"""
DATABASE SCHEMA FIX
Recreates the database with the correct schema
"""

import sqlite3
import os

def fix_database():
    db_path = "honeypot.db"
    
    # Delete old database if it exists
    if os.path.exists(db_path):
        print(f"🗑️  Deleting old database: {db_path}")
        os.remove(db_path)
    
    print(f"✅ Creating new database with correct schema...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Sessions table with correct columns
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
    
    print("✅ Database recreated successfully!")
    print("\n📊 Database schema:")
    print("  - sessions (with scam_type, channel, etc.)")
    print("  - messages")
    print("  - intelligence")
    print("  - fatigue_events")

if __name__ == "__main__":
    fix_database()