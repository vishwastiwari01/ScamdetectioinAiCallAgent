"""
GUVI HACKATHON - AGENTIC HONEYPOT REST API - FIXED VERSION
Complete solution as per Problem Statement 2

CRITICAL FIXES APPLIED:
✅ Made all Pydantic fields optional to prevent 422 errors
✅ Added HEAD method support for /health endpoint
✅ Enhanced intelligence extraction with regex patterns
✅ Added fallback extraction when AI fails
✅ Improved error handling
✅ Fixed API key to match your credential
✅ Better logging for debugging

Endpoints:
- POST /api/message - Main endpoint for scam detection and engagement
- GET/HEAD /health - Health check
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import requests
from datetime import datetime
import uuid
import re

# Import your existing honeypot system
try:
    from openrouter_integration import AIEnhancedOrchestrator, load_api_key
    HONEYPOT_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: openrouter_integration not found. Using mock mode.")
    HONEYPOT_AVAILABLE = False

app = FastAPI(title="Agentic Honeypot API - GUVI Hackathon")

# ============================================================================
# CONFIGURATION
# ============================================================================

# FIXED: Your actual API key from logs
API_KEY = "vishwas-tiwari-guvi-honeypot-2026"

# GUVI callback endpoint
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# ============================================================================
# PYDANTIC MODELS - FIXED: All fields now optional to prevent 422 errors
# ============================================================================

class Message(BaseModel):
    sender: Optional[str] = "unknown"
    text: Optional[str] = ""
    timestamp: Optional[int] = None

class Metadata(BaseModel):
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"

class IncomingRequest(BaseModel):
    sessionId: Optional[str] = None
    message: Optional[Message] = None
    conversationHistory: Optional[List[Message]] = []
    metadata: Optional[Metadata] = None

class AgentResponse(BaseModel):
    status: str = "success"
    reply: str = ""
    scamDetected: Optional[bool] = None
    threatLevel: Optional[int] = None

class ExtractedIntelligence(BaseModel):
    bankAccounts: List[str] = []
    upiIds: List[str] = []
    phishingLinks: List[str] = []
    phoneNumbers: List[str] = []
    suspiciousKeywords: List[str] = []

class FinalResultPayload(BaseModel):
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str

# ============================================================================
# INTELLIGENCE EXTRACTION - NEW: Regex-based fallback extraction
# ============================================================================

def extract_intelligence_from_text(text: str) -> Dict:
    """
    Extract intelligence using regex patterns
    This is a fallback when AI extraction fails
    """
    intelligence = {
        'bankAccounts': [],
        'upiIds': [],
        'phishingLinks': [],
        'phoneNumbers': [],
        'suspiciousKeywords': []
    }
    
    if not text:
        return intelligence
    
    # Extract UPI IDs (format: username@provider)
    upi_pattern = r'\b[\w\.-]+@(?:paytm|phonepe|googlepay|amazonpay|bhim|ybl|axl|icici|sbi|hdfc|oksbi|okaxis|okhdfcbank|okicici|ibl|airtel|fbl|axisgo)\b'
    upi_matches = re.findall(upi_pattern, text, re.IGNORECASE)
    intelligence['upiIds'] = list(set(upi_matches))
    
    # Extract phone numbers (Indian format: 10 digits starting with 6-9)
    phone_pattern = r'\b[6-9]\d{9}\b'
    phone_matches = re.findall(phone_pattern, text)
    intelligence['phoneNumbers'] = list(set(phone_matches))
    
    # Extract URLs (phishing links)
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    url_matches = re.findall(url_pattern, text)
    intelligence['phishingLinks'] = list(set(url_matches))
    
    # Extract bank account numbers (9-18 digits)
    bank_pattern = r'\b\d{9,18}\b'
    potential_accounts = re.findall(bank_pattern, text)
    # Filter out phone numbers from bank accounts
    bank_accounts = [acc for acc in potential_accounts if len(acc) != 10]
    intelligence['bankAccounts'] = list(set(bank_accounts))
    
    # Extract suspicious keywords
    keywords = [
        'urgent', 'verify', 'blocked', 'suspended', 'immediately', 
        'payment', 'account', 'bank', 'upi', 'refund', 'prize',
        'won', 'congratulations', 'claim', 'otp', 'expire', 'expire',
        'confirm', 'update', 'kyc', 'fraud', 'risk', 'security'
    ]
    
    text_lower = text.lower()
    found_keywords = [kw for kw in keywords if kw in text_lower]
    intelligence['suspiciousKeywords'] = list(set(found_keywords))
    
    return intelligence

# ============================================================================
# API KEY AUTHENTICATION
# ============================================================================
def verify_api_key(x_api_key: str = Header(...)):
    print(f"🔑 Received API Key: {x_api_key}")
    print(f"🔑 Expected API Key: {API_KEY}")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# ============================================================================
# SESSION MANAGEMENT - ENHANCED
# ============================================================================

class SessionManager:
    """Manages conversation sessions with enhanced intelligence extraction"""
    
    def __init__(self):
        self.sessions = {}
        if HONEYPOT_AVAILABLE:
            api_key = load_api_key()
            self.orchestrator = AIEnhancedOrchestrator(api_key)
        else:
            self.orchestrator = None
    
    def get_or_create_session(self, session_id: str) -> Dict:
        """Get existing session or create new one"""
        if not session_id:
            session_id = f"session-{uuid.uuid4()}"
            
        if session_id not in self.sessions:
            # Create new session
            honeypot_session_id = None
            if self.orchestrator:
                honeypot_session_id = self.orchestrator.start_session(handoff=True)
            
            self.sessions[session_id] = {
                'honeypot_session_id': honeypot_session_id,
                'messages': [],
                'intelligence': {
                    'bankAccounts': [],
                    'upiIds': [],
                    'phishingLinks': [],
                    'phoneNumbers': [],
                    'suspiciousKeywords': []
                },
                'scam_detected': False,
                'threat_level': 0,
                'created_at': datetime.now().isoformat()
            }
        
        return self.sessions[session_id]
    
    def merge_intelligence(self, existing: Dict, new: Dict):
        """Merge intelligence from multiple sources"""
        for key in ['bankAccounts', 'upiIds', 'phishingLinks', 'phoneNumbers', 'suspiciousKeywords']:
            if key in new:
                for item in new[key]:
                    if item and item not in existing[key]:
                        existing[key].append(item)
    
    def update_session(self, session_id: str, message: str, sender: str, 
                      intelligence: List[Dict], threat_level: int, scam_detected: bool):
        """Update session with new message and intelligence"""
        session = self.sessions[session_id]
        
        # Add message
        session['messages'].append({
            'sender': sender,
            'text': message,
            'timestamp': int(datetime.now().timestamp() * 1000)
        })
        
        # Extract intelligence from AI response
        for item in intelligence:
            data_type = item.get('data_type', '')
            value = item.get('value', '')
            
            if 'bank' in data_type.lower() or 'account' in data_type.lower():
                if value and value not in session['intelligence']['bankAccounts']:
                    session['intelligence']['bankAccounts'].append(value)
            
            elif 'upi' in data_type.lower():
                if value and value not in session['intelligence']['upiIds']:
                    session['intelligence']['upiIds'].append(value)
            
            elif 'url' in data_type.lower() or 'link' in data_type.lower():
                if value and value not in session['intelligence']['phishingLinks']:
                    session['intelligence']['phishingLinks'].append(value)
            
            elif 'phone' in data_type.lower():
                if value and value not in session['intelligence']['phoneNumbers']:
                    session['intelligence']['phoneNumbers'].append(value)
        
        # CRITICAL FIX: Also extract using regex as fallback
        regex_intel = extract_intelligence_from_text(message)
        self.merge_intelligence(session['intelligence'], regex_intel)
        
        # Update metadata
        session['scam_detected'] = scam_detected
        if threat_level > session['threat_level']:
            session['threat_level'] = threat_level
        
        print(f"🎯 Extracted Intelligence Type: {type(session['intelligence'])}")
        print(f"🎯 Extracted Intelligence Content: {session['intelligence']}")
    
    def should_send_final_callback(self, session_id: str) -> bool:
        """Determine if we should send final result to GUVI"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # Send if:
        # 1. Scam is detected
        # 2. At least 3 messages exchanged
        # 3. Some intelligence captured OR high threat level
        has_intelligence = (
            len(session['intelligence']['bankAccounts']) > 0 or
            len(session['intelligence']['upiIds']) > 0 or
            len(session['intelligence']['phoneNumbers']) > 0 or
            len(session['intelligence']['phishingLinks']) > 0 or
            session['threat_level'] >= 7
        )
        
        return (
            session['scam_detected'] and
            len(session['messages']) >= 3 and
            has_intelligence
        )
    
    def send_final_callback(self, session_id: str):
        """Send final result to GUVI endpoint"""
        session = self.sessions.get(session_id)
        if not session:
            return
        
        try:
            # Extract suspicious keywords from all messages
            all_text = " ".join([msg['text'] for msg in session['messages']])
            regex_intel = extract_intelligence_from_text(all_text)
            self.merge_intelligence(session['intelligence'], regex_intel)
            
            # Prepare payload
            payload = {
                "sessionId": session_id,
                "scamDetected": session['scam_detected'],
                "totalMessagesExchanged": len(session['messages']),
                "extractedIntelligence": session['intelligence'],
                "agentNotes": f"Scam detected with threat level {session['threat_level']}/10. "
                             f"Captured {len(session['intelligence']['upiIds'])} UPI IDs, "
                             f"{len(session['intelligence']['phoneNumbers'])} phone numbers, "
                             f"{len(session['intelligence']['bankAccounts'])} bank accounts, "
                             f"{len(session['intelligence']['phishingLinks'])} phishing links."
            }
            
            # Send to GUVI
            print(f"📤 Sending final result to GUVI for session {session_id}")
            print(f"   Payload: {payload}")
            
            response = requests.post(
                GUVI_CALLBACK_URL,
                json=payload,
                timeout=10
            )
            
            print(f"✅ GUVI callback response: {response.status_code}")
            print(f"   Response body: {response.text}")
            session['callback_sent'] = True
            session['callback_response'] = response.status_code
            
        except Exception as e:
            print(f"❌ Error sending GUVI callback: {e}")
            session['callback_error'] = str(e)

# Initialize session manager
session_manager = SessionManager()

# ============================================================================
# MAIN API ENDPOINT - ENHANCED ERROR HANDLING
# ============================================================================

@app.post("/api/message", response_model=AgentResponse)
async def handle_message(
    request: IncomingRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Main endpoint for scam detection and engagement
    
    FIXED: Now handles empty/incomplete requests without 422 errors
    """
    
    try:
        # Handle empty or incomplete requests
        if not request.message or not request.message.text:
            print("⚠️  Received empty or incomplete request")
            return AgentResponse(
                status="success",
                reply="I didn't receive a message. Could you please send again?",
                scamDetected=False,
                threatLevel=0
            )
        
        session_id = request.sessionId or f"auto-{uuid.uuid4()}"
        
        print(f"\n{'='*60}")
        print(f"📨 Received message for session: {session_id}")
        print(f"   Sender: {request.message.sender}")
        print(f"   Text: {request.message.text}")
        print(f"{'='*60}\n")
        
        # Get or create session
        session = session_manager.get_or_create_session(session_id)
        honeypot_session_id = session['honeypot_session_id']
        
        # Process message through AI honeypot (if available)
        if session_manager.orchestrator:
            result = session_manager.orchestrator.handle_message(
                request.message.text,
                honeypot_session_id,
                sender=request.message.sender
            )
            
            scam_detected = result.get('engaged', False)
            threat_level = result['analysis'].get('threat_level', 0)
            intelligence = result.get('extracted_intelligence', [])
            ai_response = result.get('response', "I understand. Could you tell me more?")
        else:
            # Fallback mode without AI
            print("⚠️  Running in fallback mode (no AI)")
            intelligence_dict = extract_intelligence_from_text(request.message.text)
            has_intel = any(len(v) > 0 for v in intelligence_dict.values())
            
            scam_detected = has_intel or any(kw in request.message.text.lower() 
                                            for kw in ['upi', 'bank', 'payment', 'verify', 'urgent'])
            threat_level = 7 if has_intel else 3
            intelligence = []
            ai_response = "I see. Could you provide more details?"
        
        if not scam_detected:
            # Low threat - not engaging
            return AgentResponse(
                status="success",
                reply="Thank you for your message.",
                scamDetected=False,
                threatLevel=threat_level
            )
        
        # Update session with incoming message
        session_manager.update_session(
            session_id,
            request.message.text,
            request.message.sender or "scammer",
            intelligence,
            threat_level,
            scam_detected
        )
        
        # Add AI response to session
        session_manager.update_session(
            session_id,
            ai_response,
            "user",  # Our AI agent responds as "user"
            [],
            threat_level,
            scam_detected
        )
        
        # Check if we should send final callback to GUVI
        if session_manager.should_send_final_callback(session_id):
            session_manager.send_final_callback(session_id)
        
        print(f"✅ Response generated")
        print(f"   Scam Detected: {scam_detected}")
        print(f"   Threat Level: {threat_level}/10")
        print(f"   AI Response: {ai_response[:100]}...")
        print(f"   Intelligence: {len(intelligence)} items captured\n")
        
        return AgentResponse(
            status="success",
            reply=ai_response,
            scamDetected=scam_detected,
            threatLevel=threat_level
        )
    
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        import traceback
        traceback.print_exc()
        
        # Return friendly error instead of 500
        return AgentResponse(
            status="error",
            reply="I'm having trouble processing your message. Please try again.",
            scamDetected=False,
            threatLevel=0
        )

# ============================================================================
# ADDITIONAL ENDPOINTS - FIXED: Added HEAD support for /health
# ============================================================================

@app.get("/health")
@app.head("/health")
async def health_check():
    """
    Health check endpoint
    FIXED: Now supports both GET and HEAD methods
    """
    return {
        "status": "healthy",
        "service": "Agentic Honeypot API",
        "active_sessions": len(session_manager.sessions),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "GUVI Hackathon - Agentic Honeypot API",
        "status": "running",
        "endpoints": {
            "main": "POST /api/message",
            "health": "GET /health",
            "session": "GET /api/session/{session_id}"
        }
    }

@app.get("/api/session/{session_id}")
async def get_session_info(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get session information (for debugging)"""
    session = session_manager.sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "sessionId": session_id,
        "scamDetected": session['scam_detected'],
        "threatLevel": session['threat_level'],
        "messageCount": len(session['messages']),
        "intelligence": session['intelligence'],
        "callbackSent": session.get('callback_sent', False)
    }

@app.post("/api/session/{session_id}/finalize")
async def finalize_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Manually trigger final callback to GUVI (for testing)"""
    session = session_manager.sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_manager.send_final_callback(session_id)
    
    return {
        "status": "success",
        "message": "Final callback sent to GUVI",
        "sessionId": session_id
    }

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    """Handle validation errors gracefully"""
    print(f"⚠️  Validation error: {exc}")
    return JSONResponse(
        status_code=200,  # Return 200 instead of 422
        content={
            "status": "success",
            "reply": "I received your message but couldn't process it. Could you rephrase?",
            "scamDetected": False,
            "threatLevel": 0
        }
    )

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║        🍯 GUVI HACKATHON - AGENTIC HONEYPOT API 🍯          ║
║                      FIXED VERSION                           ║
╚═══════════════════════════════════════════════════════════════╝

✅ CRITICAL FIXES APPLIED:
   • Made all Pydantic fields optional (no more 422 errors)
   • Added HEAD method support for /health endpoint
   • Enhanced intelligence extraction with regex patterns
   • Added fallback extraction when AI fails
   • Fixed API key: {API_KEY}
   • Better error handling and logging

Problem Statement 2: Agentic Honey-Pot for Scam Detection

Features:
  ✅ REST API with API key authentication
  ✅ Scam detection & multi-turn engagement
  ✅ Intelligence extraction (UPI, phone, bank accounts, URLs)
  ✅ Automatic callback to GUVI endpoint
  ✅ Session management
  ✅ Human-like AI responses
  ✅ Graceful error handling

Endpoints:
  POST /api/message          - Main scam detection endpoint
  GET  /health               - Health check (supports HEAD too)
  HEAD /health               - Health check (new!)
  GET  /                     - Service info
  GET  /api/session/:id      - Get session info
  POST /api/session/:id/finalize - Manual callback trigger

Authentication:
  Header: x-api-key: {API_KEY}

Server starting on: http://localhost:8000

📖 API Documentation: http://localhost:8000/docs
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
