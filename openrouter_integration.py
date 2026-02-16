"""
OPENROUTER AI INTEGRATION - GUVI HACKATHON VERSION
Combines your existing honeypot agent with GUVI API requirements

Features:
- Your enhanced honeypot agent with female persona
- GUVI-compatible intelligence extraction
- Multi-turn engagement up to 10 turns
- Fallback template responses
- Both standalone and GUVI API modes
"""

import requests
import json
import random
import re
import os
from typing import Dict, List, Optional
from datetime import datetime

# Try to import your enhanced system (for standalone mode)
try:
    from enhanced_honeypot_agent import (
        ENHANCED_SYSTEM_PROMPT, PERSONA_CONFIG, detect_scam_type, 
        IntelligenceExtractor as EnhancedExtractor, SCAM_PATTERNS
    )
    ENHANCED_MODE = True
except ImportError:
    ENHANCED_MODE = False
    print("⚠️ Running in GUVI-only mode (enhanced_honeypot_agent not found)")


class UnifiedIntelligenceExtractor:
    """
    Unified intelligence extractor that works with both:
    - Your existing honeypot system
    - GUVI hackathon requirements
    """
    
    def __init__(self):
        # GUVI-required intelligence types
        self.intelligence_types = {
            'upi_ids': [],
            'phone_numbers': [],
            'bank_accounts': [],
            'phishing_links': [],
            'email_addresses': [],
            'suspicious_keywords': []
        }
    
    def extract_all(self, text: str, session_id: str = None) -> List[Dict]:
        """
        Extract intelligence in GUVI format
        
        Returns: List[Dict] with format:
        [
            {'data_type': 'upi_id', 'value': 'scammer@paytm', 'confidence': 0.95},
            {'data_type': 'phone_number', 'value': '9876543210', 'confidence': 0.9},
            ...
        ]
        """
        intelligence = []
        
        if not text:
            return intelligence
        
        # Extract UPI IDs (comprehensive pattern)
        upi_pattern = r'\b[\w\.-]+@(?:paytm|phonepe|googlepay|amazonpay|bhim|ybl|axl|icici|sbi|hdfc|oksbi|okaxis|okhdfcbank|okicici|ibl|airtel|fbl|axisgo|fakebank|fakeupi|[\w]+)\b'
        for match in re.finditer(upi_pattern, text, re.IGNORECASE):
            upi = match.group().lower()
            if upi not in [i['value'] for i in intelligence if i['data_type'] == 'upi_id']:
                intelligence.append({
                    'data_type': 'upi_id',
                    'value': upi,
                    'confidence': 0.95
                })
        
        # Extract phone numbers (Indian format)
        phone_patterns = [
            r'\+91[-\s]?[6-9]\d{9}',  # +91-9876543210
            r'\b[6-9]\d{9}\b'          # 9876543210
        ]
        
        for pattern in phone_patterns:
            for match in re.finditer(pattern, text):
                phone = match.group().replace('+91', '').replace('-', '').replace(' ', '').strip()
                if phone and phone not in [i['value'] for i in intelligence if i['data_type'] == 'phone_number']:
                    intelligence.append({
                        'data_type': 'phone_number',
                        'value': phone,
                        'confidence': 0.9
                    })
        
        # Extract URLs (phishing links)
        url_pattern = r'http[s]?://(?:[a-zA-Z0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        for match in re.finditer(url_pattern, text):
            url = match.group()
            if url not in [i['value'] for i in intelligence if i['data_type'] == 'phishing_link']:
                intelligence.append({
                    'data_type': 'phishing_link',
                    'value': url,
                    'confidence': 1.0
                })
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            email = match.group().lower()
            # Exclude UPI IDs from email list
            if not any(provider in email for provider in ['paytm', 'phonepe', 'googlepay', 'bhim', 'ybl']):
                if email not in [i['value'] for i in intelligence if i['data_type'] == 'email_address']:
                    intelligence.append({
                        'data_type': 'email_address',
                        'value': email,
                        'confidence': 0.85
                    })
        
        # Extract bank account numbers (10-18 digits, excluding phone numbers)
        account_pattern = r'\b\d{10,18}\b'
        for match in re.finditer(account_pattern, text):
            value = match.group()
            # Exclude 10-digit numbers (likely phone numbers)
            if len(value) != 10:
                if value not in [i['value'] for i in intelligence if i['data_type'] == 'bank_account']:
                    intelligence.append({
                        'data_type': 'bank_account',
                        'value': value,
                        'confidence': 0.7
                    })
        
        return intelligence


class OpenRouterPersonaAgent:
    """
    AI-Powered Persona using OpenRouter with your existing honeypot agent
    ENHANCED for GUVI hackathon compatibility
    """
    
    def __init__(self, api_key: str, persona_config: Dict = None):
        self.api_key = api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "meta-llama/llama-3.1-70b-instruct"
        
        # Use your persona config if available, else default
        if persona_config:
            self.persona = persona_config
        else:
            self.persona = {
                'name': 'Mrs. Kavita Sharma',
                'gender': 'female',
                'age': 52,
                'occupation': 'homemaker',
                'language': 'hinglish'
            }
        
        # Use your system prompt if available
        if ENHANCED_MODE:
            self.system_prompt = ENHANCED_SYSTEM_PROMPT
        else:
            self.system_prompt = self._get_default_system_prompt()
        
        self.intel_extractor = UnifiedIntelligenceExtractor()
        
        print(f"✅ OpenRouter initialized")
        print(f"   Persona: {self.persona.get('name', 'Unknown')} ({self.persona.get('gender', 'unspecified')})")
    
    def _get_default_system_prompt(self) -> str:
        """Default system prompt if enhanced_honeypot_agent not available"""
        return """You are Mrs. Kavita Sharma, a 52-year-old Indian homemaker.

CRITICAL RULES FOR RESPONDING:
1. You are FEMALE - use FEMININE Hindi: "kar rahi hoon" NOT "kar raha hoon"
2. Act worried, confused, but cooperative with scammers
3. Keep responses SHORT (2-3 sentences, 10-25 words)
4. Use natural Indian English/Hinglish patterns
5. Show emotions: worry, confusion, hesitation
6. Ask questions to extract MORE information
7. Use delays: "Ek minute...", "App open ho raha hai..."
8. NEVER reveal you're AI or automated

ENGAGEMENT TACTICS:
- Ask for clarification to waste time
- Pretend to have technical difficulties
- Show willingness to help but hesitate at critical moments
- If they give UPI/phone/account: make them repeat it slowly

Match the scammer's language style (English vs Hinglish)."""
    
    def generate_response(self, scam_analysis: Dict, conversation_history: List[Dict], current_message: str, turn_count: int = 1) -> str:
        """
        Generate AI response using honeypot tactics
        
        Compatible with both:
        - Your existing system (if scam_analysis has all fields)
        - GUVI requirements (minimal scam_analysis)
        """
        
        # Detect scam type
        if ENHANCED_MODE:
            scam_type = detect_scam_type(current_message)
        else:
            scam_type = self._simple_scam_detection(current_message)
        
        # Build context from conversation history
        context = ""
        for msg in conversation_history[-5:]:  # Last 5 messages
            sender = "SCAMMER" if msg.get('sender') == 'scammer' else "YOU"
            text = msg.get('message') or msg.get('text', '')
            context += f"{sender}: {text}\n"
        
        # Extract intelligence for context
        intel = self.intel_extractor.extract_all(current_message)
        intel_note = ""
        if intel:
            intel_items = [f"{i['data_type']}: {i['value']}" for i in intel[:3]]
            intel_note = f"\n💡 INTELLIGENCE DETECTED: {', '.join(intel_items)}"
            intel_note += "\nMake them REPEAT these details to confirm!"
        
        # Scam type hint
        scam_hint = ""
        if scam_type != "unknown":
            scam_hint = f"\n🎯 SCAM TYPE: {scam_type.upper()}"
            if ENHANCED_MODE and scam_type in SCAM_PATTERNS:
                example = SCAM_PATTERNS[scam_type]["response_hooks"][0]
                scam_hint += f"\n   Example: {example}"
        
        # Turn-based guidance
        turn_guidance = self._get_turn_guidance(turn_count, scam_type)
        
        # Full user prompt
        user_prompt = f"""RECENT CONVERSATION:
{context}

SCAMMER'S LATEST MESSAGE: "{current_message}"{scam_hint}{intel_note}

TURN {turn_count}/10{turn_guidance}

YOUR TASK: Respond as {self.persona['name']} ({self.persona['gender'].upper()} {self.persona['occupation']}, {self.persona['age']} years old).

CRITICAL REMINDERS:
1. Use FEMININE language if female
2. Keep response SHORT (2-3 sentences max)
3. Sound worried/confused but cooperative
4. Ask questions to extract more info
5. Deploy time delays when appropriate
6. Match their language (English/Hinglish)

RESPOND NOW as {self.persona['name']}:"""
        
        # Try API with retry logic
        for attempt in range(3):
            try:
                timeout = 15 if attempt == 0 else (10 if attempt == 1 else 8)
                
                response = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/vishwastiwari01/ScamdetectioinAiCallAgent",
                        "X-Title": "GUVI Hackathon Honeypot"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.85,
                        "max_tokens": 150,
                        "top_p": 0.95
                    },
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result['choices'][0]['message']['content'].strip()
                    # Clean up response
                    ai_response = ai_response.strip('"').strip("'").strip()
                    
                    # Ensure not too long
                    if len(ai_response) > 200:
                        ai_response = ai_response[:200].rsplit('.', 1)[0] + '.'
                    
                    print(f"✅ OpenRouter API success (turn {turn_count})")
                    return ai_response
                else:
                    print(f"⚠️ OpenRouter error {response.status_code} (attempt {attempt + 1}/3)")
                    if attempt == 2:
                        return self._fallback_response(scam_type, turn_count, current_message)
            
            except Exception as e:
                print(f"⚠️ OpenRouter exception (attempt {attempt + 1}/3): {e}")
                if attempt == 2:
                    return self._fallback_response(scam_type, turn_count, current_message)
        
        return self._fallback_response(scam_type, turn_count, current_message)
    
    def _simple_scam_detection(self, message: str) -> str:
        """Simple scam detection when enhanced_honeypot_agent not available"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['bank', 'account', 'otp', 'blocked', 'suspended']):
            return 'bank_fraud'
        elif any(word in message_lower for word in ['upi', 'paytm', 'phonepe', 'cashback', 'prize', 'won']):
            return 'upi_fraud'
        elif any(word in message_lower for word in ['http', 'click', 'link', 'offer', 'deal']):
            return 'phishing'
        else:
            return 'unknown'
    
    def _get_turn_guidance(self, turn: int, scam_type: str) -> str:
        """Get guidance based on turn number"""
        if turn <= 3:
            return "\n   Strategy: Show initial concern/excitement, ask basic questions"
        elif turn <= 6:
            return "\n   Strategy: Request more details, express worry/interest"
        else:
            return "\n   Strategy: Act more hesitant, ask for verification, show doubt"
    
    def _fallback_response(self, scam_type: str, turn_count: int, message: str) -> str:
        """
        Fallback template responses when API fails
        Uses your existing patterns if available
        """
        
        # Try using your enhanced patterns first
        if ENHANCED_MODE and scam_type in SCAM_PATTERNS:
            responses = SCAM_PATTERNS[scam_type]["response_hooks"]
            return random.choice(responses)
        
        # Fallback to built-in templates
        templates = {
            'bank_fraud': [
                "Oh no! My account is blocked? What should I do sir?",
                "I'm very worried. How can I verify this?",
                "Should I share my OTP? Is this the bank?",
                "Let me check my bank app first... ek minute.",
                "What number should I call to confirm?",
                "Sir please help, I don't want my account blocked!",
                "Can you send verification link?",
                "I have the OTP ready. Where to send?",
                "This is urgent? Should I go to bank branch?",
                "Okay I will do as you say. What next?"
            ],
            'upi_fraud': [
                "Really? I won cashback? Thank you so much!",
                "How do I claim this reward sir?",
                "Which UPI ID should I send to?",
                "Is this really from Paytm official?",
                "Do I need to pay anything to claim?",
                "Amazing! What details you need?",
                "Can I get in bank account instead?",
                "How long is this valid sir?",
                "Should I download any app?",
                "Okay sending details. Please confirm."
            ],
            'phishing': [
                "iPhone for Rs 999? This is amazing!",
                "Let me click link... wait is it safe?",
                "How do I know this is genuine?",
                "Can you send COD? I'm not sure...",
                "What if I don't get the product?",
                "This seems too good. Are you sure?",
                "Should I share card details?",
                "Offer expires soon? Let me think...",
                "Can I call customer care first?",
                "Okay I will try. What after that?"
            ],
            'unknown': [
                "Sorry, I don't understand clearly.",
                "What do you need from me exactly?",
                "Can you explain again?",
                "Who is this? Which company?",
                "How did you get my number?",
                "Is this some kind of offer?",
                "Please send more details."
            ]
        }
        
        responses = templates.get(scam_type, templates['unknown'])
        
        # Prefer sequential responses but add randomness
        if turn_count <= len(responses):
            if random.random() < 0.8:
                return responses[turn_count - 1]
        
        return random.choice(responses)
    
    def reset_context(self):
        """Reset conversation context"""
        pass


class AIEnhancedOrchestrator:
    """
    Unified orchestrator that works with:
    1. Your existing full_honeypot_system.py (standalone mode)
    2. GUVI hackathon API requirements (API mode)
    """
    
    def __init__(self, openrouter_api_key: Optional[str] = None):
        self.use_ai = False
        self.standalone_mode = False
        
        # Try to use your existing system
        try:
            from full_honeypot_system import (
                HoneypotDatabase, ScamAnalyzer, 
                PersonaAgent, PERSONA_CONFIG, SCAM_SCENARIOS
            )
            
            self.db = HoneypotDatabase()
            self.analyzer = ScamAnalyzer()
            self.scenarios = SCAM_SCENARIOS
            self.standalone_mode = True
            persona_config = PERSONA_CONFIG
            print("✅ Full honeypot system loaded (standalone mode)")
        
        except ImportError:
            # GUVI API mode - minimal dependencies
            self.db = None
            self.analyzer = SimpleScamAnalyzer()
            self.scenarios = {}
            persona_config = None
            print("✅ Running in GUVI API mode")
        
        # Initialize intelligence extractor
        self.extractor = UnifiedIntelligenceExtractor()
        
        # Initialize AI persona
        if openrouter_api_key:
            try:
                self.persona = OpenRouterPersonaAgent(openrouter_api_key, persona_config)
                self.use_ai = True
                print("✅ AI mode enabled with OpenRouter!")
            except Exception as e:
                print(f"⚠️ AI init failed: {e}")
                self.use_ai = False
        
        self.active_sessions = {}
    
    def start_session(self, scenario_name: Optional[str] = None, handoff: bool = False) -> str:
        """Start a new session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        self.active_sessions[session_id] = {
            "turn_count": 0,
            "messages": [],
            "intelligence": [],
            "scam_type": "unknown"
        }
        
        # Initialize in database if available
        if self.db and self.standalone_mode:
            if scenario_name and scenario_name in self.scenarios:
                messages = self.scenarios[scenario_name]
                scam_type = self._guess_scam_type(messages[0]) if messages else "unknown"
            else:
                scam_type = "unknown"
            
            self.db.create_session(session_id, scam_type, "text", handoff)
        
        return session_id
    
    def _guess_scam_type(self, message: str) -> str:
        """Guess scam type from message"""
        analysis = self.analyzer.analyze(message)
        return analysis.get("primary_scam_type", "unknown")
    
    def handle_message(self, message: str, session_id: str, sender: str = "scammer") -> Dict:
        """
        Handle incoming message - works with both modes
        
        Returns unified response format for GUVI API
        """
        import time
        start_time = time.time()
        
        # Get or create session
        if session_id not in self.active_sessions:
            session_id = self.start_session()
        
        session = self.active_sessions[session_id]
        
        # Increment turn count
        session['turn_count'] += 1
        turn_count = session['turn_count']
        
        # Save message to history
        session['messages'].append({
            'sender': sender,
            'text': message,
            'message': message,  # Compatibility with both formats
            'timestamp': datetime.now().isoformat()
        })
        
        # Save to database if available
        if self.db and self.standalone_mode:
            self.db.save_message(session_id, sender, message)
        
        # Extract intelligence
        extracted = self.extractor.extract_all(message, session_id)
        session['intelligence'].extend(extracted)
        
        # Analyze threat
        analysis = self.analyzer.analyze(message)
        
        # Update scam type
        if analysis.get('primary_scam_type', 'unknown') != 'unknown':
            session['scam_type'] = analysis['primary_scam_type']
        
        # Decide engagement (threat level >= 5)
        threat_level = analysis.get('threat_level', 0)
        should_engage = analysis.get('should_engage', threat_level >= 5)
        
        if not should_engage:
            response = "Thank you for your message."
            engaged = False
        else:
            # Generate AI response
            if self.use_ai:
                response = self.persona.generate_response(
                    analysis, 
                    session['messages'], 
                    message,
                    turn_count
                )
            else:
                response = self._template_response(session['scam_type'], turn_count)
            
            engaged = True
        
        # Save response
        session['messages'].append({
            'sender': 'honeypot',
            'text': response,
            'message': response,
            'timestamp': datetime.now().isoformat()
        })
        
        if self.db and self.standalone_mode:
            delay = time.time() - start_time
            self.db.save_message(session_id, "honeypot", response, delay)
            self.db.update_time_wasted(session_id)
        
        # Return unified format
        return {
            "engaged": engaged,
            "session_id": session_id,
            "response": response,
            "analysis": analysis,
            "extracted_intelligence": extracted,
            "turn_count": turn_count,
            "ai_powered": self.use_ai
        }
    
    def _template_response(self, scam_type: str, turn: int) -> str:
        """Simple template response"""
        templates = {
            'bank_fraud': ["Oh no! What should I do?", "I'm worried about my account.", "Should I go to bank?"],
            'upi_fraud': ["Really? I won prize?", "How to claim this?", "Which UPI to use?"],
            'phishing': ["Is this real?", "The link is safe?", "How do I know it's genuine?"],
            'unknown': ["I don't understand.", "What do you mean?", "Please explain."]
        }
        
        responses = templates.get(scam_type, templates['unknown'])
        return responses[min(turn - 1, len(responses) - 1)]


class SimpleScamAnalyzer:
    """Simple analyzer when full_honeypot_system not available"""
    
    def analyze(self, message: str) -> Dict:
        """Basic scam analysis"""
        message_lower = message.lower()
        
        # Calculate threat level
        high_threat = ['urgent', 'blocked', 'suspended', 'otp', 'immediately', 'compromised']
        medium_threat = ['won', 'prize', 'cashback', 'claim', 'reward', 'verify']
        
        high_count = sum(1 for word in high_threat if word in message_lower)
        medium_count = sum(1 for word in medium_threat if word in message_lower)
        
        threat_level = min(10, (high_count * 3) + (medium_count * 2))
        
        # Detect scam type
        if any(word in message_lower for word in ['bank', 'account', 'otp']):
            scam_type = 'bank_fraud'
        elif any(word in message_lower for word in ['upi', 'paytm', 'prize', 'won']):
            scam_type = 'upi_fraud'
        elif 'http' in message_lower:
            scam_type = 'phishing'
        else:
            scam_type = 'unknown'
        
        return {
            'threat_level': threat_level,
            'primary_scam_type': scam_type,
            'should_engage': threat_level >= 5
        }


# API Key Management

def save_api_key(api_key: str):
    """Save API key to config file"""
    config = {"openrouter_api_key": api_key}
    with open("honeypot_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("✅ API key saved to honeypot_config.json")

def load_api_key() -> Optional[str]:
    """Load API key from config or environment"""
    # Try config file first
    try:
        with open("honeypot_config.json", "r") as f:
            key = json.load(f).get("openrouter_api_key")
            if key:
                print("✅ API key loaded from config file")
                return key
    except:
        pass
    
    # Try environment variable
    key = os.environ.get('OPENROUTER_API_KEY', '')
    if key:
        print("✅ API key loaded from environment")
        return key
    
    print("⚠️ No API key found")
    return None

def setup_openrouter_api():
    """Interactive setup"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║          🚀 OPENROUTER SETUP (FREE LLAMA 3.1 70B) 🚀        ║
╚═══════════════════════════════════════════════════════════════╝

Get your FREE API key: https://openrouter.ai/keys

1. Sign in (or create account)
2. Click "Create Key"
3. Copy the key (starts with "sk-or-")
    """)
    
    existing = load_api_key()
    if existing:
        print(f"Found existing key: {existing[:15]}...")
        if input("Use existing key? (y/n): ").lower() == 'y':
            return existing
    
    key = input("\nPaste your OpenRouter API key: ").strip()
    if key:
        save_api_key(key)
        return key
    return None


# Testing
if __name__ == "__main__":
    print("🧪 Testing Merged OpenRouter Integration\n")
    
    key = setup_openrouter_api()
    
    if key:
        print("\n" + "="*60)
        print("Testing with GUVI test scenarios...")
        print("="*60)
        
        orch = AIEnhancedOrchestrator(key)
        
        test_scenarios = [
            ("Bank Fraud", "URGENT: Your SBI account has been compromised. Share your account number and OTP immediately!"),
            ("UPI Fraud", "Congratulations! You won Rs 5000 cashback from Paytm. Verify your UPI: scammer@paytm"),
            ("Phishing", "iPhone 15 Pro at Rs 999! Click: http://fake-amazon.com Deal expires in 10 min!")
        ]
        
        for name, msg in test_scenarios:
            print(f"\n{'─'*60}")
            print(f"📧 {name}")
            print(f"   Message: {msg[:60]}...")
            
            sid = orch.start_session(handoff=True)
            result = orch.handle_message(msg, sid)
            
            if result['engaged']:
                print(f"✅ Engaged: YES")
                print(f"🤖 AI Response: {result['response']}")
                print(f"📊 Threat: {result['analysis']['threat_level']}/10")
                print(f"🔍 Intel: {len(result['extracted_intelligence'])} items")
                
                for intel in result['extracted_intelligence']:
                    print(f"   - {intel['data_type']}: {intel['value']}")
            else:
                print(f"⚠️ Not engaged (low threat)")
    else:
        print("\n❌ No API key provided. Exiting.")
