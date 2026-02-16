"""
OPENROUTER AI INTEGRATION - ENHANCED WITH HONEYPOT AGENT SKILL
Uses Llama 3.1 70B with proper female persona and engagement tactics
"""

import requests
import json
import random
from typing import Dict, List, Optional

# Import enhanced system prompt and persona config
from enhanced_honeypot_agent import ENHANCED_SYSTEM_PROMPT, PERSONA_CONFIG, detect_scam_type, IntelligenceExtractor, SCAM_PATTERNS

class OpenRouterPersonaAgent:
    """AI-Powered Persona using OpenRouter's Llama 3.1 70B with Honeypot Agent Skill"""
    
    def __init__(self, api_key: str, persona_config: Dict):
        self.persona = persona_config
        self.api_key = api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "meta-llama/llama-3.1-70b-instruct"
        self.system_prompt = ENHANCED_SYSTEM_PROMPT
        self.intel_extractor = IntelligenceExtractor()
        
        print(f"✅ OpenRouter initialized with Enhanced Honeypot Agent")
        print(f"   Persona: {persona_config.get('name', 'Unknown')} ({persona_config.get('gender', 'unspecified')})")
    
    def generate_response(self, scam_analysis: Dict, conversation_history: List[Dict], current_message: str) -> str:
        """Generate AI response using honeypot agent tactics with retry logic"""
        
        # Detect scam type for better context
        scam_type = detect_scam_type(current_message)
        
        # Build context - last 5 messages
        context = ""
        for msg in conversation_history[-5:]:
            sender = "SCAMMER" if msg['sender'] == 'scammer' else "YOU"
            context += f"{sender}: {msg['message']}\n"
        
        # Add intelligence context if we've captured anything
        intel = self.intel_extractor.extract_all(current_message)
        intel_note = ""
        if intel:
            intel_note = f"\n💡 INTELLIGENCE DETECTED: {', '.join([f'{k}: {v}' for k, v in intel.items()])}"
            intel_note += "\nMake them REPEAT these details slowly to confirm!"
        
        # Scam type hint
        scam_hint = ""
        if scam_type != "unknown":
            scam_hint = f"\n🎯 SCAM TYPE DETECTED: {scam_type.upper()}"
            if scam_type in SCAM_PATTERNS:
                example_responses = SCAM_PATTERNS[scam_type]["response_hooks"]
                scam_hint += f"\n   Consider using: {example_responses[0]}"
        
        # Full prompt
        user_prompt = f"""RECENT CONVERSATION:
{context}

SCAMMER'S LATEST MESSAGE: "{current_message}"{scam_hint}{intel_note}

YOUR TASK: Respond as Mrs. Kavita (FEMALE homemaker, 52 years old).

CRITICAL REMINDERS:
1. Use FEMININE Hindi: "kar rahi hoon" (NOT "kar raha hoon")
2. Keep response SHORT (2-3 sentences maximum)
3. Sound worried/confused but cooperative
4. If they gave UPI ID/account/phone: Make them repeat it slowly
5. Deploy time delays: "Ek minute...", "App open ho raha hai..."
6. Ask clarifying questions to waste time
7. Match their language (English vs Hinglish)

RESPOND NOW as Mrs. Kavita:"""
        
        # Retry logic - try 3 times with different timeout strategies
        for attempt in range(3):
            try:
                timeout = 15 if attempt == 0 else (10 if attempt == 1 else 8)
                
                response = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.85,
                        "max_tokens": 150
                    },
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result['choices'][0]['message']['content'].strip()
                    # Clean up any quotes or artifacts
                    ai_response = ai_response.strip('"').strip("'").strip()
                    return ai_response
                else:
                    print(f"⚠️ OpenRouter error {response.status_code} (attempt {attempt + 1}/3)")
                    if attempt < 2:
                        continue
                    return self._fallback_response(scam_analysis, current_message)
                    
            except Exception as e:
                print(f"⚠️ OpenRouter exception (attempt {attempt + 1}/3): {e}")
                if attempt < 2:
                    continue
                return self._fallback_response(scam_analysis, current_message)
    
    def _fallback_response(self, scam_analysis: Dict, current_message: str) -> str:
        """Fallback if API fails - use pattern-based responses"""
        scam_type = detect_scam_type(current_message)
        
        if scam_type != "unknown" and scam_type in SCAM_PATTERNS:
            return random.choice(SCAM_PATTERNS[scam_type]["response_hooks"])
        
        # Generic fallback responses (FEMININE Hindi!)
        generic_responses = [
            "Ek minute rukiye... mujhe theek se samajh nahi aa raha.",
            "Haan ji, main kar rahi hoon... bas app khul nahi raha.",
            "Aap phir se batayiye, main dhyan se sun rahi hoon.",
            "Theek hai ji, par ye safe hai na? Mujhe tension ho raha hai.",
            "Main try kar rahi hoon... network thoda slow hai aaj."
        ]
        
        return random.choice(generic_responses)
    
    def reset_context(self):
        pass


class AIEnhancedOrchestrator:
    """Orchestrator using OpenRouter - FIXED IMPORTS"""
    
    def __init__(self, openrouter_api_key: Optional[str] = None):
        # FIXED: Import from full_honeypot_system.py instead of aihoneypot_gui.py
        from full_honeypot_system import (
            HoneypotDatabase, ScamAnalyzer, IntelligenceExtractor,
            PersonaAgent, PERSONA_CONFIG, SCAM_SCENARIOS
        )
        
        self.db = HoneypotDatabase()
        self.analyzer = ScamAnalyzer()
        self.extractor = IntelligenceExtractor(self.db)
        self.scenarios = SCAM_SCENARIOS
        self.use_ai = False
        
        if openrouter_api_key:
            try:
                self.persona = OpenRouterPersonaAgent(openrouter_api_key, PERSONA_CONFIG)
                self.use_ai = True
                print("✅ AI mode enabled!")
            except Exception as e:
                print(f"⚠️ AI init failed: {e}")
                self.persona = PersonaAgent(PERSONA_CONFIG)
        else:
            self.persona = PersonaAgent(PERSONA_CONFIG)
        
        self.active_sessions = {}
    
    def start_session(self, scenario_name: Optional[str] = None, handoff: bool = False) -> str:
        from datetime import datetime
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if scenario_name and scenario_name in self.scenarios:
            messages = self.scenarios[scenario_name]
            scam_type = self._guess_scam_type(messages[0])
        else:
            messages = []
            scam_type = "unknown"
        
        self.active_sessions[session_id] = {
            "turn_count": 0,
            "scenario_messages": messages,
            "current_scenario_index": 0
        }
        
        self.db.create_session(session_id, scam_type, "text", handoff)
        
        if self.use_ai:
            self.persona.reset_context()
        
        return session_id
    
    def _guess_scam_type(self, message: str) -> str:
        analysis = self.analyzer.analyze(message)
        return analysis["primary_scam_type"]
    
    def handle_message(self, message: str, session_id: str, sender: str = "scammer") -> Dict:
        import time
        start_time = time.time()
        
        self.db.save_message(session_id, sender, message)
        
        extracted = self.extractor.extract_all(message, session_id)
        analysis = self.analyzer.analyze(message)
        
        # Update scammer persona type
        if 'scammer_persona' in analysis:
            self.db.update_persona_type(session_id, analysis['scammer_persona'])
        
        if not analysis['should_engage']:
            return {"engaged": False}
        
        history = self.db.get_conversation_history(session_id)
        turn_count = self.active_sessions[session_id]["turn_count"] + 1
        self.active_sessions[session_id]["turn_count"] = turn_count
        
        # Add random fatigue events
        if turn_count % 3 == 0:
            from full_honeypot_system import PsychologicalFatigueTracker
            fatigue_tracker = PsychologicalFatigueTracker(self.db)
            fatigue_tracker.add_event(session_id, "delay_tactic")
        
        # Call the right function based on AI vs Template
        if self.use_ai:
            response = self.persona.generate_response(analysis, history, message)
        else:
            response = self.persona.generate_response(analysis, history, turn_count)
        
        # Calculate response delay
        delay = time.time() - start_time
        self.db.save_message(session_id, "honeypot", response, delay)
        
        # Update time wasted
        self.db.update_time_wasted(session_id)
        
        # Calculate fatigue score
        from full_honeypot_system import PsychologicalFatigueTracker
        fatigue_tracker = PsychologicalFatigueTracker(self.db)
        fatigue_score = fatigue_tracker.calculate_score(session_id)
        
        return {
            "engaged": True,
            "session_id": session_id,
            "response": response,
            "analysis": analysis,
            "extracted_intelligence": extracted,
            "turn_count": turn_count,
            "ai_powered": self.use_ai,
            "psychological_fatigue_score": fatigue_score,
            "response_delay_seconds": round(delay, 2)
        }
    
    def get_next_scenario_message(self, session_id: str) -> Optional[str]:
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            return None
        
        messages = session_data["scenario_messages"]
        index = session_data["current_scenario_index"]
        
        if index < len(messages):
            self.active_sessions[session_id]["current_scenario_index"] = index + 1
            return messages[index]
        return None


def save_api_key(api_key: str):
    config = {"openrouter_api_key": api_key}
    with open("honeypot_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("✅ API key saved!")

def load_api_key() -> Optional[str]:
    try:
        with open("honeypot_config.json", "r") as f:
            return json.load(f).get("openrouter_api_key")
    except:
        return None

def setup_openrouter_api():
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
        print(f"Found key: {existing[:10]}...")
        if input("Use existing? (y/n): ").lower() == 'y':
            return existing
    
    key = input("\nPaste API key: ").strip()
    if key:
        save_api_key(key)
        return key
    return None


if __name__ == "__main__":
    key = setup_openrouter_api()
    
    if key:
        print("\n🧪 Testing OpenRouter...")
        
        try:
            orch = AIEnhancedOrchestrator(key)
            sid = orch.start_session(handoff=True)
            
            result = orch.handle_message("Pay ₹5000 to 9876@paytm now!", sid)
            
            if result['engaged']:
                print(f"\n✅ SUCCESS!")
                print(f"Response: {result['response']}")
                
                if result.get('ai_powered'):
                    print("\n🤖 AI is working!")
                else:
                    print("\n⚠️ Using templates (AI failed)")
        except Exception as e:
            print(f"\n❌ Test failed: {e}")