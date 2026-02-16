"""
GUVI HACKATHON - AGENTIC HONEYPOT REST API
Complete solution as per Problem Statement 2

Endpoints:
- POST /api/message - Main endpoint for scam detection and engagement
- GET /health - Health check
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
from datetime import datetime
import uuid

# Import your existing honeypot system
from openrouter_integration import AIEnhancedOrchestrator, load_api_key

app = FastAPI(title="Agentic Honeypot API - GUVI Hackathon")

# ============================================================================
# CONFIGURATION
# ============================================================================

# Your API key for authentication (change this!)
API_KEY = "guvi-hackaton-honeypot-12345"  # Update this!

# GUVI callback endpoint
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# ============================================================================
# PYDANTIC MODELS (As per problem statement)
# ============================================================================

class Message(BaseModel):
    sender: str  # "scammer" or "user"
    text: str
    timestamp: int

class Metadata(BaseModel):
    channel: str = "SMS"
    language: str = "English"
    locale: str = "IN"

class IncomingRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = []
    metadata: Optional[Metadata] = None

class AgentResponse(BaseModel):
    status: str  # "success" or "error"
    reply: str  # AI-generated response
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
# API KEY AUTHENTICATION
# ============================================================================
def verify_api_key(x_api_key: str = Header(...)):
    print("Received API Key:", x_api_key)
    print("Expected API Key:", API_KEY)
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class SessionManager:
    """Manages conversation sessions"""
    
    def __init__(self):
        self.sessions = {}
        api_key = load_api_key()
        self.orchestrator = AIEnhancedOrchestrator(api_key)
    
    def get_or_create_session(self, session_id: str) -> Dict:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            # Create new session
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
    
    def update_session(self, session_id: str, message: str, sender: str, 
                      intelligence: Dict, threat_level: int, scam_detected: bool):
        """Update session with new message and intelligence"""
        session = self.sessions[session_id]
        
        # Add message
        session['messages'].append({
            'sender': sender,
            'text': message,
            'timestamp': int(datetime.now().timestamp() * 1000)
        })
        
        # Update intelligence - intelligence is a Dict not List
        if isinstance(intelligence, dict):
            # Handle UPI IDs
            if 'upi_ids' in intelligence:
                for upi in intelligence['upi_ids']:
                    if upi not in session['intelligence']['upiIds']:
                        session['intelligence']['upiIds'].append(upi)
            
            # Handle phone numbers
            if 'phone_numbers' in intelligence:
                for phone in intelligence['phone_numbers']:
                    if phone not in session['intelligence']['phoneNumbers']:
                        session['intelligence']['phoneNumbers'].append(phone)
            
            # Handle bank accounts
            if 'bank_accounts' in intelligence:
                for acc in intelligence['bank_accounts']:
                    if acc not in session['intelligence']['bankAccounts']:
                        session['intelligence']['bankAccounts'].append(acc)
            
            # Handle phishing links
            if 'phishing_links' in intelligence:
                for url in intelligence['phishing_links']:
                    if url not in session['intelligence']['phishingLinks']:
                        session['intelligence']['phishingLinks'].append(url)
        
        # Update metadata
        session['scam_detected'] = scam_detected
        if threat_level > session['threat_level']:
            session['threat_level'] = threat_level
    
    def should_send_final_callback(self, session_id: str) -> bool:
        """Determine if we should send final result to GUVI"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # Send if:
        # 1. Scam is detected
        # 2. At least 3 messages exchanged
        # 3. Some intelligence captured
        return (
            session['scam_detected'] and
            len(session['messages']) >= 3 and
            (len(session['intelligence']['bankAccounts']) > 0 or
             len(session['intelligence']['upiIds']) > 0 or
             len(session['intelligence']['phoneNumbers']) > 0)
        )
    
    def send_final_callback(self, session_id: str):
        """Send final result to GUVI endpoint"""
        session = self.sessions.get(session_id)
        if not session:
            return
        
        try:
            # Extract suspicious keywords from messages
            suspicious_keywords = []
            keywords = ['urgent', 'verify', 'blocked', 'suspended', 'immediately', 
                       'payment', 'account', 'bank', 'upi', 'refund']
            
            for msg in session['messages']:
                text_lower = msg['text'].lower()
                for keyword in keywords:
                    if keyword in text_lower and keyword not in suspicious_keywords:
                        suspicious_keywords.append(keyword)
            
            session['intelligence']['suspiciousKeywords'] = suspicious_keywords
            
            # Prepare payload
            payload = {
                "sessionId": session_id,
                "scamDetected": session['scam_detected'],
                "totalMessagesExchanged": len(session['messages']),
                "extractedIntelligence": session['intelligence'],
                "agentNotes": f"Scam detected with threat level {session['threat_level']}/10. "
                             f"Captured {len(session['intelligence']['upiIds'])} UPI IDs, "
                             f"{len(session['intelligence']['phoneNumbers'])} phone numbers, "
                             f"{len(session['intelligence']['bankAccounts'])} bank accounts."
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
            session['callback_sent'] = True
            session['callback_response'] = response.status_code
            
        except Exception as e:
            print(f"❌ Error sending GUVI callback: {e}")
            session['callback_error'] = str(e)

# Initialize session manager
session_manager = SessionManager()

# ============================================================================
# MAIN API ENDPOINT
# ============================================================================

@app.post("/api/message", response_model=AgentResponse)
async def handle_message(
    request: IncomingRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Main endpoint for scam detection and engagement
    
    This endpoint:
    1. Receives a message from suspected scammer
    2. Detects scam intent
    3. Activates AI Agent if scam detected
    4. Returns AI-generated response
    5. Sends final callback to GUVI when appropriate
    """
    
    try:
        print(f"\n{'='*60}")
        print(f"📨 Received message for session: {request.sessionId}")
        print(f"   Sender: {request.message.sender}")
        print(f"   Text: {request.message.text}")
        print(f"{'='*60}\n")
        
        # Get or create session
        session = session_manager.get_or_create_session(request.sessionId)
        honeypot_session_id = session['honeypot_session_id']
        
        # Process message through AI honeypot
        result = session_manager.orchestrator.handle_message(
            request.message.text,
            honeypot_session_id,
            sender=request.message.sender
        )
        
        # Check if scam detected
        scam_detected = result.get('engaged', False)
        threat_level = result['analysis'].get('threat_level', 0)
        
        if not scam_detected:
            # Low threat - not engaging
            return AgentResponse(
                status="success",
                reply="Thank you for your message.",
                scamDetected=False,
                threatLevel=threat_level
            )
        
        # Extract intelligence
        intelligence = result.get('extracted_intelligence', [])
        
        # Update session
        session_manager.update_session(
            request.sessionId,
            request.message.text,
            request.message.sender,
            intelligence,
            threat_level,
            scam_detected
        )
        
        # Add AI response to session
        ai_response = result['response']
        session_manager.update_session(
            request.sessionId,
            ai_response,
            "user",  # Our AI agent responds as "user"
            [],
            threat_level,
            scam_detected
        )
        
        # Check if we should send final callback to GUVI
        if session_manager.should_send_final_callback(request.sessionId):
            session_manager.send_final_callback(request.sessionId)
        
        print(f"✅ Response generated")
        print(f"   Scam Detected: {scam_detected}")
        print(f"   Threat Level: {threat_level}/10")
        print(f"   AI Response: {ai_response[:50]}...")
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
        
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ADDITIONAL ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Agentic Honeypot API",
        "active_sessions": len(session_manager.sessions),
        "timestamp": datetime.now().isoformat()
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
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║        🍯 GUVI HACKATHON - AGENTIC HONEYPOT API 🍯          ║
╚═══════════════════════════════════════════════════════════════╝

Problem Statement 2: Agentic Honey-Pot for Scam Detection

Features:
  ✅ REST API with API key authentication
  ✅ Scam detection & multi-turn engagement
  ✅ Intelligence extraction (UPI, phone, bank accounts)
  ✅ Automatic callback to GUVI endpoint
  ✅ Session management
  ✅ Human-like AI responses

Endpoints:
  POST /api/message          - Main scam detection endpoint
  GET  /health               - Health check
  GET  /api/session/:id      - Get session info
  POST /api/session/:id/finalize - Manual callback trigger

Authentication:
  Header: x-api-key: {API_KEY}

Server starting on: http://localhost:8000

⚠️  IMPORTANT:
   Update API_KEY in the code (line 26)
   OpenRouter API key should be in honeypot_config.json

📖 API Documentation: http://localhost:8000/docs
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)