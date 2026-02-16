"""
ENHANCED FULL HONEYPOT SYSTEM
With Time-Wasted Metric, Persona Mirroring, and Psychological Fatigue
"""

import sqlite3
import re
from datetime import datetime
from typing import Dict, List, Optional
import random

# ============================================================================
# PERSONA CONFIGURATION
# ============================================================================

PERSONA_CONFIG = {
    "name": "Mrs. Kavita",
    "age": 65,
    "location": "Mumbai",
    "occupation": "Retired Teacher"
}

# Persona types based on scammer behavior
PERSONA_TYPES = {
    "confused_elderly": {
        "responses": [
            "Beta, ek baar aur boliye? Samajh nahi aaya.",
            "My phone is old, network problem. Can you repeat?",
            "I am not understanding properly. Please say again slowly."
        ]
    },
    "eager_victim": {
        "responses": [
            "Yes sir, I want to do it! What should I do first?",
            "Okay, I am ready! Tell me the steps please.",
            "I am worried beta, please help me fix this quickly!"
        ]
    },
    "technical_struggler": {
        "responses": [
            "App is not opening sir. Showing some error.",
            "My phone is hanging. Wait let me restart.",
            "This OTP screen is not coming. What to do?"
        ]
    }
}

SCAM_SCENARIOS = {
    "banking_otp": [
        "Your SBI account has been blocked. Please share OTP to verify."
    ]
}

# ============================================================================
# DATABASE WITH ENHANCED METRICS
# ============================================================================

class HoneypotDatabase:
    """SQLite database with time-wasted and fatigue tracking"""
    
    def __init__(self, db_path: str = "honeypot.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                scam_type TEXT,
                channel TEXT,
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                time_wasted_seconds INTEGER DEFAULT 0,
                psychological_fatigue_score INTEGER DEFAULT 0,
                scammer_persona_type TEXT,
                handoff_mode INTEGER DEFAULT 0
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                sender TEXT,
                message TEXT,
                timestamp TIMESTAMP,
                response_delay_seconds REAL
            )
        """)
        
        # Intelligence table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS intelligence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                intel_type TEXT,
                value TEXT,
                extracted_at TIMESTAMP
            )
        """)
        
        # Fatigue events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fatigue_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                event_type TEXT,
                timestamp TIMESTAMP,
                fatigue_contribution INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_session(self, session_id: str, scam_type: str, channel: str, handoff: bool = False):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (session_id, scam_type, channel, started_at, handoff_mode) VALUES (?, ?, ?, ?, ?)",
            (session_id, scam_type, channel, datetime.now(), 1 if handoff else 0)
        )
        conn.commit()
        conn.close()
    
    def save_message(self, session_id: str, sender: str, message: str, delay_seconds: float = 0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, sender, message, timestamp, response_delay_seconds) VALUES (?, ?, ?, ?, ?)",
            (session_id, sender, message, datetime.now(), delay_seconds)
        )
        conn.commit()
        conn.close()
    
    def save_intelligence(self, session_id: str, intel_type: str, value: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO intelligence (session_id, intel_type, value, extracted_at) VALUES (?, ?, ?, ?)",
            (session_id, intel_type, value, datetime.now())
        )
        conn.commit()
        conn.close()
    
    def add_fatigue_event(self, session_id: str, event_type: str, contribution: int = 1):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO fatigue_events (session_id, event_type, timestamp, fatigue_contribution) VALUES (?, ?, ?, ?)",
            (session_id, event_type, datetime.now(), contribution)
        )
        conn.commit()
        conn.close()
    
    def update_fatigue_score(self, session_id: str, score: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET psychological_fatigue_score = ? WHERE session_id = ?",
            (score, session_id)
        )
        conn.commit()
        conn.close()
    
    def update_time_wasted(self, session_id: str):
        """Calculate and update time wasted"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT started_at FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            started_at = datetime.fromisoformat(row[0])
            time_wasted = int((datetime.now() - started_at).total_seconds())
            cursor.execute(
                "UPDATE sessions SET time_wasted_seconds = ? WHERE session_id = ?",
                (time_wasted, session_id)
            )
        conn.commit()
        conn.close()
    
    def update_persona_type(self, session_id: str, persona_type: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET scammer_persona_type = ? WHERE session_id = ?",
            (persona_type, session_id)
        )
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT sender, message FROM messages WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        messages = [{"sender": row[0], "message": row[1]} for row in cursor.fetchall()]
        conn.close()
        return messages
    
    def get_session_report(self, session_id: str) -> Dict:
        """Generate complete session report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Session data
        cursor.execute(
            "SELECT scam_type, started_at, time_wasted_seconds, psychological_fatigue_score, scammer_persona_type FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        session_row = cursor.fetchone()
        
        # Messages
        cursor.execute(
            "SELECT sender, message, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        messages = [{"sender": row[0], "message": row[1], "timestamp": row[2]} for row in cursor.fetchall()]
        
        # Intelligence
        cursor.execute(
            "SELECT intel_type, value FROM intelligence WHERE session_id = ?",
            (session_id,)
        )
        intelligence = [{"type": row[0], "value": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        if session_row:
            return {
                "session_id": session_id,
                "scam_type": session_row[0],
                "started_at": session_row[1],
                "time_wasted_seconds": session_row[2],
                "time_wasted_formatted": f"{session_row[2] // 60}m {session_row[2] % 60}s",
                "psychological_fatigue_score": session_row[3],
                "scammer_persona_type": session_row[4],
                "total_messages": len(messages),
                "messages": messages,
                "intelligence_extracted": intelligence
            }
        return {}

# ============================================================================
# SCAM ANALYZER WITH PERSONA DETECTION
# ============================================================================

class ScamAnalyzer:
    """Analyzes messages AND detects scammer personality - ENHANCED THREAT DETECTION"""
    
    def __init__(self):
        self.scam_patterns = {
            "banking": ["account", "bank", "otp", "verify", "blocked", "kyc", "atm", "debit", "credit"],
            "payment": ["pay", "send", "upi", "paytm", "transfer", "phonepe", "gpay", "payment"],
            "urgent": ["urgent", "immediately", "now", "quick", "jaldi", "abhi"],
            "threat": ["blocked", "suspended", "action", "police", "arrest", "legal", "court"],
            "remote": ["anydesk", "teamviewer", "remote", "access", "install app", "download"],
            "refund": ["refund", "cashback", "wrong payment", "return money"]
        }
        
        self.urgency_keywords = ["urgent", "immediately", "now", "jaldi", "abhi"]
        self.polite_indicators = ["sir", "madam", "please", "kindly"]
        self.aggressive_indicators = ["must", "have to", "will be", "shall be"]
    
    def detect_scammer_persona(self, message: str) -> str:
        message_lower = message.lower()
        
        urgency = sum(1 for kw in self.urgency_keywords if kw in message_lower)
        polite = sum(1 for kw in self.polite_indicators if kw in message_lower)
        aggressive = sum(1 for kw in self.aggressive_indicators if kw in message_lower)
        
        if aggressive >= 2 or urgency >= 2:
            return "aggressive"
        elif polite >= 2:
            return "polite"
        else:
            return "neutral"
    
    def analyze(self, message: str) -> Dict:
        message_lower = message.lower()
        
        scam_scores = {}
        total_score = 0
        
        for scam_type, keywords in self.scam_patterns.items():
            score = sum(2 for kw in keywords if kw in message_lower)  # 2 points per keyword
            scam_scores[scam_type] = score
            total_score += score
        
        primary_scam_type = max(scam_scores, key=scam_scores.get) if max(scam_scores.values()) > 0 else "unknown"
        
        # MORE AGGRESSIVE threat level calculation
        threat_level = min(10, total_score)
        
        # Boost threat level if multiple indicators present
        has_payment_request = any(kw in message_lower for kw in ["pay", "send", "upi", "paytm", "transfer"])
        has_urgency = any(kw in message_lower for kw in self.urgency_keywords)
        has_threat = any(kw in message_lower for kw in ["block", "suspend", "arrest", "police"])
        has_number = bool(re.search(r'\d{4,}', message))  # Any number with 4+ digits
        
        # BOOST THREAT LEVEL
        if has_payment_request:
            threat_level += 3
        if has_urgency:
            threat_level += 2
        if has_threat:
            threat_level += 2
        if has_number:
            threat_level += 1
        
        # Cap at 10
        threat_level = min(10, max(3, threat_level))  # Minimum 3, maximum 10
        
        scammer_persona = self.detect_scammer_persona(message)
        should_engage = threat_level >= 1 or has_payment_request or len(message) > 5
        
        return {
            "primary_scam_type": primary_scam_type,
            "threat_level": threat_level,
            "has_payment_request": has_payment_request,
            "urgency": has_urgency,
            "should_engage": should_engage,
            "scam_scores": scam_scores,
            "scammer_persona": scammer_persona
        }

# ============================================================================
# PSYCHOLOGICAL FATIGUE TRACKER
# ============================================================================

class PsychologicalFatigueTracker:
    """Tracks psychological fatigue"""
    
    def __init__(self, db: HoneypotDatabase):
        self.db = db
        self.fatigue_weights = {
            "repetition_request": 2,
            "clarification_needed": 2,
            "technical_error": 3,
            "delay_tactic": 2,
            "wrong_information": 4
        }
    
    def add_event(self, session_id: str, event_type: str):
        weight = self.fatigue_weights.get(event_type, 1)
        self.db.add_fatigue_event(session_id, event_type, weight)
    
    def calculate_score(self, session_id: str) -> int:
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT SUM(fatigue_contribution) FROM fatigue_events WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        total = row[0] if row[0] else 0
        score = min(100, int(total * 5))
        self.db.update_fatigue_score(session_id, score)
        return score

# ============================================================================
# INTELLIGENCE EXTRACTOR
# ============================================================================

class IntelligenceExtractor:
    """Extracts intelligence - ENHANCED VERSION"""
    
    def __init__(self, db: HoneypotDatabase):
        self.db = db
        # More aggressive patterns
        self.upi_pattern = r'\b[a-zA-Z0-9._-]+@[a-zA-Z]+\b'
        self.phone_pattern = r'\b(?:\+91[\s-]?)?[6-9]\d{9}\b'
        self.account_pattern = r'\b\d{9,18}\b'
        self.url_pattern = r'https?://[^\s]+'
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.amount_pattern = r'[₹₨]\s*\d+|rs\.?\s*\d+|\d+\s*rupees?'
        self.ifsc_pattern = r'\b[A-Z]{4}0[A-Z0-9]{6}\b'
        self.app_name_pattern = r'\b(anydesk|teamviewer|quicksupport|remotpc|chrome\s*remote)\b'
        self.name_pattern = r'\b(?:my\s+name\s+is|i\s+am|this\s+is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
    
    def extract_all(self, message: str, session_id: str) -> Dict:
        extracted = {}
        message_lower = message.lower()
        
        # UPI IDs
        upi_ids = re.findall(self.upi_pattern, message)
        if upi_ids:
            extracted['upi_ids'] = upi_ids
            for upi in upi_ids:
                self.db.save_intelligence(session_id, 'upi_id', upi)
                print(f"🎯 Captured UPI ID: {upi}")
        
        # Phone numbers
        phones = re.findall(self.phone_pattern, message)
        if phones:
            extracted['phone_numbers'] = phones
            for phone in phones:
                self.db.save_intelligence(session_id, 'phone', phone)
                print(f"🎯 Captured Phone: {phone}")
        
        # Bank accounts
        accounts = [acc for acc in re.findall(self.account_pattern, message) if len(acc) >= 10]
        if accounts:
            extracted['bank_accounts'] = accounts
            for acc in accounts:
                self.db.save_intelligence(session_id, 'bank_account', acc)
                print(f"🎯 Captured Account: {acc}")
        
        # URLs
        urls = re.findall(self.url_pattern, message)
        if urls:
            extracted['phishing_links'] = urls
            for url in urls:
                self.db.save_intelligence(session_id, 'phishing_url', url)
                print(f"🎯 Captured URL: {url}")
        
        # Email addresses
        emails = re.findall(self.email_pattern, message)
        if emails:
            extracted['email_addresses'] = emails
            for email in emails:
                self.db.save_intelligence(session_id, 'email', email)
                print(f"🎯 Captured Email: {email}")
        
        # Amounts mentioned
        amounts = re.findall(self.amount_pattern, message_lower)
        if amounts:
            extracted['amounts'] = amounts
            for amt in amounts:
                self.db.save_intelligence(session_id, 'amount', amt)
                print(f"🎯 Captured Amount: {amt}")
        
        # IFSC codes
        ifsc = re.findall(self.ifsc_pattern, message.upper())
        if ifsc:
            extracted['ifsc_codes'] = ifsc
            for code in ifsc:
                self.db.save_intelligence(session_id, 'ifsc', code)
                print(f"🎯 Captured IFSC: {code}")
        
        # Remote access app names
        apps = re.findall(self.app_name_pattern, message_lower)
        if apps:
            extracted['remote_apps'] = apps
            for app in apps:
                self.db.save_intelligence(session_id, 'remote_app', app)
                print(f"🎯 Captured App: {app}")
        
        # Scammer name
        names = re.findall(self.name_pattern, message)
        if names:
            extracted['scammer_names'] = names
            for name in names:
                self.db.save_intelligence(session_id, 'scammer_name', name)
                print(f"🎯 Captured Name: {name}")
        
        # Keywords that indicate scam intent (even without specific data)
        scam_keywords = {
            'bank': ['bank', 'account', 'atm', 'debit', 'credit'],
            'payment': ['pay', 'send', 'transfer', 'payment', 'transaction'],
            'verification': ['verify', 'confirm', 'otp', 'code', 'pin'],
            'urgency': ['urgent', 'immediately', 'now', 'quick', 'hurry'],
            'threat': ['block', 'suspend', 'close', 'expire', 'arrest', 'police', 'legal']
        }
        
        for category, keywords in scam_keywords.items():
            if any(kw in message_lower for kw in keywords):
                self.db.save_intelligence(session_id, f'keyword_{category}', message[:100])
        
        return extracted

# ============================================================================
# PERSONA AGENT
# ============================================================================

class PersonaAgent:
    """Persona with mirroring"""
    
    def __init__(self, persona_config: Dict):
        self.persona = persona_config
    
    def select_response(self, scammer_persona: str) -> str:
        # Mirror opposite behavior
        if scammer_persona == "aggressive":
            persona_type = "confused_elderly"
        elif scammer_persona == "polite":
            persona_type = "eager_victim"
        else:
            persona_type = "technical_struggler"
        
        return random.choice(PERSONA_TYPES[persona_type]["responses"])
    
    def generate_response(self, scam_analysis: Dict, conversation_history: List[Dict], turn_count: int) -> str:
        scammer_persona = scam_analysis.get('scammer_persona', 'neutral')
        return self.select_response(scammer_persona)