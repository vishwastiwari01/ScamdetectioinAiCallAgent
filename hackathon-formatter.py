"""
HACKATHON SUBMISSION FORMATTER
Formats honeypot data for competition requirements
Simulates Mock Scammer API interaction
"""

import json
import requests
from typing import List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ============================================================================
# MOCK SCAMMER API SIMULATOR
# ============================================================================

class MockScammerAPI:
    """
    Simulates the hackathon's Mock Scammer API
    In production, replace with actual API endpoint
    """
    
    SCAM_SCENARIOS = [
        {
            "id": "scam_001",
            "type": "tech_support",
            "messages": [
                "Hello sir, this is calling from Microsoft. Your computer has virus.",
                "We need remote access to fix. Please install TeamViewer.",
                "Payment of ₹5000 required for virus removal. Send to support@techhelp.com"
            ]
        },
        {
            "id": "scam_002",
            "type": "bank_kyc",
            "messages": [
                "Dear customer, your HDFC KYC is pending. Update immediately.",
                "Your account will be blocked in 24 hours if not updated.",
                "Pay ₹500 KYC charges to 9876543210@paytm to reactivate."
            ]
        },
        {
            "id": "scam_003",
            "type": "refund_fraud",
            "messages": [
                "Congratulations! You have electricity bill refund of ₹2500.",
                "To claim, provide your UPI ID for refund transfer.",
                "Also pay processing fee of ₹100 to refund@electricity.com"
            ]
        },
        {
            "id": "scam_004",
            "type": "job_scam",
            "messages": [
                "Hi, we have work from home job for you. ₹30000 per month.",
                "Just pay ₹1500 registration fee to join.",
                "Send to jobs@workfromhome.in via UPI immediately."
            ]
        },
        {
            "id": "scam_005",
            "type": "investment_fraud",
            "messages": [
                "Invest in crypto! 500% returns guaranteed in 30 days.",
                "Minimum investment ₹10000. No risk, all profit!",
                "Transfer to investor@cryptoking.com to start earning."
            ]
        }
    ]
    
    @staticmethod
    def get_random_scam() -> Dict:
        """Get random scam scenario"""
        import random
        return random.choice(MockScammerAPI.SCAM_SCENARIOS)
    
    @staticmethod
    def get_next_message(scam_id: str, turn: int) -> str:
        """Get next scammer message"""
        for scam in MockScammerAPI.SCAM_SCENARIOS:
            if scam['id'] == scam_id:
                messages = scam['messages']
                if turn < len(messages):
                    return messages[turn]
                else:
                    # Repeat last message with urgency
                    return f"Sir/Madam, please respond! {messages[-1]}"
        return None

# ============================================================================
# HACKATHON SUBMISSION FORMATTER
# ============================================================================

class HackathonSubmission:
    """Formats data according to hackathon requirements"""
    
    @staticmethod
    def format_intelligence(
        session_id: str,
        scam_type: str,
        intelligence_items: List[Dict],
        conversation_log: List[Dict]
    ) -> Dict:
        """
        Format extracted intelligence for submission
        
        Required JSON structure:
        {
            "session_id": "...",
            "scam_type": "...",
            "threat_level": 1-10,
            "extracted_data": {
                "upi_ids": [...],
                "bank_accounts": [...],
                "phone_numbers": [...],
                "email_addresses": [...],
                "phishing_links": [...]
            },
            "conversation_summary": {...},
            "timestamp": "..."
        }
        """
        
        # Categorize intelligence
        extracted_data = {
            "upi_ids": [],
            "bank_accounts": [],
            "phone_numbers": [],
            "email_addresses": [],
            "phishing_links": [],
            "other": []
        }
        
        for item in intelligence_items:
            data_type = item.get('data_type', 'unknown')
            value = item.get('value')
            confidence = item.get('confidence', 0.0)
            
            entry = {
                "value": value,
                "confidence": confidence,
                "extracted_at": item.get('created_at', datetime.now().isoformat())
            }
            
            if data_type == 'upi_id':
                extracted_data['upi_ids'].append(entry)
            elif data_type == 'bank_account':
                extracted_data['bank_accounts'].append(entry)
            elif data_type == 'phone':
                extracted_data['phone_numbers'].append(entry)
            elif data_type == 'email':
                extracted_data['email_addresses'].append(entry)
            elif data_type == 'url':
                extracted_data['phishing_links'].append(entry)
            else:
                extracted_data['other'].append(entry)
        
        # Calculate threat level
        threat_level = HackathonSubmission._calculate_threat_level(
            scam_type,
            intelligence_items
        )
        
        # Summarize conversation
        conversation_summary = {
            "total_turns": len(conversation_log),
            "duration_seconds": HackathonSubmission._calculate_duration(conversation_log),
            "scammer_messages": [
                msg['message'] for msg in conversation_log 
                if msg.get('sender') == 'scammer_voice' or msg.get('sender') == 'scammer'
            ],
            "honeypot_responses": [
                msg['message'] for msg in conversation_log 
                if msg.get('sender') == 'honeypot'
            ]
        }
        
        return {
            "session_id": session_id,
            "scam_type": scam_type,
            "threat_level": threat_level,
            "extracted_data": extracted_data,
            "conversation_summary": conversation_summary,
            "timestamp": datetime.now().isoformat(),
            "intelligence_quality_score": HackathonSubmission._calculate_quality_score(extracted_data)
        }
    
    @staticmethod
    def _calculate_threat_level(scam_type: str, intelligence: List[Dict]) -> int:
        """Calculate threat level 1-10"""
        
        base_threats = {
            'tech_support': 7,
            'bank_kyc': 9,
            'refund_fraud': 6,
            'job_scam': 5,
            'investment_fraud': 8,
            'unknown': 5
        }
        
        base = base_threats.get(scam_type, 5)
        
        # Increase if payment info captured
        has_payment = any(
            item.get('data_type') in ['upi_id', 'bank_account'] 
            for item in intelligence
        )
        
        if has_payment:
            base = min(10, base + 2)
        
        return base
    
    @staticmethod
    def _calculate_duration(conversation_log: List[Dict]) -> int:
        """Calculate conversation duration in seconds"""
        
        if len(conversation_log) < 2:
            return 0
        
        try:
            first = datetime.fromisoformat(conversation_log[0]['created_at'])
            last = datetime.fromisoformat(conversation_log[-1]['created_at'])
            return int((last - first).total_seconds())
        except:
            # Fallback: estimate 30 seconds per turn
            return len(conversation_log) * 30
    
    @staticmethod
    def _calculate_quality_score(extracted_data: Dict) -> float:
        """
        Calculate intelligence quality score (0-100)
        Based on quantity and diversity of captured data
        """
        
        score = 0.0
        
        # Points for each category
        if extracted_data['upi_ids']:
            score += 30
        if extracted_data['bank_accounts']:
            score += 25
        if extracted_data['phone_numbers']:
            score += 15
        if extracted_data['email_addresses']:
            score += 15
        if extracted_data['phishing_links']:
            score += 15
        
        # Bonus for high confidence
        all_items = (
            extracted_data['upi_ids'] +
            extracted_data['bank_accounts'] +
            extracted_data['phone_numbers'] +
            extracted_data['email_addresses'] +
            extracted_data['phishing_links']
        )
        
        if all_items:
            avg_confidence = sum(item['confidence'] for item in all_items) / len(all_items)
            score *= (0.5 + 0.5 * avg_confidence)  # Adjust by confidence
        
        return min(100.0, score)

# ============================================================================
# FASTAPI ENDPOINTS FOR HACKATHON
# ============================================================================

app = FastAPI(title="Hackathon Submission API")

class ScammerMessage(BaseModel):
    message: str
    scam_id: Optional[str] = None

class IntelligenceResponse(BaseModel):
    session_id: str
    response: str
    extracted_intelligence: List[Dict]
    should_continue: bool

@app.post("/hackathon/simulate-scam")
async def simulate_scam_interaction(message: ScammerMessage):
    """
    Simulate interaction with Mock Scammer API
    Returns AI response and extracted intelligence
    """
    
    from fastapi_voice_honeypot import call_manager
    
    # Create new session if not exists
    call_id = message.scam_id or f"hackathon_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    if call_id not in call_manager.active_calls:
        call_manager.create_session(call_id)
    
    session_id = call_manager.active_calls[call_id]['session_id']
    
    # Process scammer message
    result = await call_manager.intelligence_agent.process(
        message.message,
        session_id
    )
    
    return {
        "session_id": session_id,
        "scammer_message": message.message,
        "honeypot_response": result['response_text'],
        "extracted_intelligence": result['intelligence'],
        "threat_level": result['threat_level'],
        "should_continue": result['should_continue']
    }

@app.post("/hackathon/get-submission/{session_id}")
async def get_hackathon_submission(session_id: str):
    """
    Get formatted submission for hackathon
    Returns JSON in required format
    """
    
    from fastapi_voice_honeypot import call_manager
    
    # Get session data from database
    try:
        db = call_manager.orchestrator.db
        
        # Get conversation history
        import sqlite3
        conn = sqlite3.connect("honeypot.db")
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute(
            "SELECT scenario_type FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        result = cursor.fetchone()
        scam_type = result[0] if result else "unknown"
        
        # Get conversation log
        cursor.execute(
            """
            SELECT sender, message, created_at 
            FROM messages 
            WHERE session_id = ? 
            ORDER BY created_at
            """,
            (session_id,)
        )
        
        conversation_log = []
        for row in cursor.fetchall():
            conversation_log.append({
                'sender': row[0],
                'message': row[1],
                'created_at': row[2]
            })
        
        # Get intelligence
        cursor.execute(
            """
            SELECT data_type, value, confidence, created_at
            FROM intelligence
            WHERE session_id = ?
            """,
            (session_id,)
        )
        
        intelligence_items = []
        for row in cursor.fetchall():
            intelligence_items.append({
                'data_type': row[0],
                'value': row[1],
                'confidence': row[2],
                'created_at': row[3]
            })
        
        conn.close()
        
        # Format for submission
        submission = HackathonSubmission.format_intelligence(
            session_id,
            scam_type,
            intelligence_items,
            conversation_log
        )
        
        return submission
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hackathon/export-all")
async def export_all_sessions():
    """
    Export all sessions in hackathon format
    For bulk submission
    """
    
    from fastapi_voice_honeypot import call_manager
    
    try:
        db = call_manager.orchestrator.db
        
        import sqlite3
        conn = sqlite3.connect("honeypot.db")
        cursor = conn.cursor()
        
        # Get all sessions
        cursor.execute("SELECT session_id FROM sessions")
        session_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Format each session
        submissions = []
        for session_id in session_ids:
            try:
                submission = await get_hackathon_submission(session_id)
                submissions.append(submission)
            except:
                continue
        
        return {
            "total_sessions": len(submissions),
            "submissions": submissions,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hackathon/run-full-scenario")
async def run_full_scenario(scam_type: str = "random"):
    """
    Run complete scam scenario from start to finish
    Simulates full Mock Scammer API interaction
    Returns complete submission
    """
    
    from fastapi_voice_honeypot import call_manager
    
    # Get scam scenario
    if scam_type == "random":
        scenario = MockScammerAPI.get_random_scam()
    else:
        scenario = next(
            (s for s in MockScammerAPI.SCAM_SCENARIOS if s['type'] == scam_type),
            MockScammerAPI.SCAM_SCENARIOS[0]
        )
    
    # Create session
    call_id = f"scenario_{scenario['id']}_{datetime.now().strftime('%H%M%S')}"
    session_id = call_manager.create_session(call_id)
    
    # Run conversation
    responses = []
    
    for turn, scammer_msg in enumerate(scenario['messages']):
        # Process message
        result = await call_manager.intelligence_agent.process(
            scammer_msg,
            session_id
        )
        
        responses.append({
            'turn': turn + 1,
            'scammer': scammer_msg,
            'honeypot': result['response_text'],
            'intelligence': result['intelligence']
        })
        
        # Stop if AI decides to end
        if not result['should_continue']:
            break
    
    # Get final submission
    submission = await get_hackathon_submission(session_id)
    
    submission['conversation_flow'] = responses
    
    return submission

# ============================================================================
# MAIN - Run Hackathon Tests
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         🏆 HACKATHON SUBMISSION API 🏆                       ║
║    Agentic Honeypot for Scam Detection & Intelligence       ║
╚═══════════════════════════════════════════════════════════════╝

Endpoints:
  POST /hackathon/simulate-scam
    → Single message interaction
  
  POST /hackathon/run-full-scenario
    → Complete scam scenario
  
  GET  /hackathon/get-submission/{session_id}
    → Formatted submission for session
  
  GET  /hackathon/export-all
    → All sessions in submission format

Running on: http://localhost:8001
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
