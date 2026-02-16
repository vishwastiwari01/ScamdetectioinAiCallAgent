
"""
AI HONEYPOT GUI v2.0 - Complete Working Version
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import sqlite3
import threading
import time
import json
import os
from datetime import datetime

try:
    import pyperclip
except:
    pyperclip = None

try:
    import winsound
except:
    winsound = None

from full_honeypot_system import SCAM_SCENARIOS, ScamType

try:
    from openrouter_integration import AIEnhancedOrchestrator, load_api_key
    USE_AI = True
except:
    from full_honeypot_system import HoneypotOrchestrator
    USE_AI = False

THEMES = {
    "dark": {
        'bg': '#1a1a2e', 'fg': '#eee', 'accent': '#e94560',
        'success': '#16213e', 'warning': '#f39c12', 'card': '#0f3460',
        'chat_bg': '#0a0a0a', 'chat_fg': '#00ff00'
    },
    "matrix": {
        'bg': '#000000', 'fg': '#00ff00', 'accent': '#00ff00',
        'success': '#003300', 'warning': '#00ff00', 'card': '#001100',
        'chat_bg': '#000000', 'chat_fg': '#00ff00'
    }
}

class HoneypotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🍯 AI Honeypot v2.0")
        self.root.geometry("1400x900")
        
        # Initialize
        if USE_AI:
            try:
                api_key = load_api_key()
                self.orchestrator = AIEnhancedOrchestrator(api_key) if api_key else HoneypotOrchestrator()
                self.ai_enabled = bool(api_key)
            except:
                from full_honeypot_system import HoneypotOrchestrator
                self.orchestrator = HoneypotOrchestrator()
                self.ai_enabled = False
        else:
            from full_honeypot_system import HoneypotOrchestrator
            self.orchestrator = HoneypotOrchestrator()
            self.ai_enabled = False
        
        self.current_session = None
        self.auto_play = False
        self.session_start_time = None
        self.current_theme = "dark"
        self.colors = THEMES[self.current_theme]
        
        self.root.configure(bg=self.colors['bg'])
        self.setup_shortcuts()
        self.setup_ui()
        self.start_timer()
    
    def setup_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self.start_session())
        self.root.bind('<Control-v>', lambda e: self.start_voice_call())
    
    def setup_ui(self):
        # Top bar
        top = tk.Frame(self.root, bg=self.colors['bg'])
        top.pack(fill='x', padx=10, pady=10)
        
        ai_text = " 🤖 AI" if self.ai_enabled else ""
        tk.Label(top, text=f"🍯 AI HONEYPOT v2.0{ai_text}",
                font=('Arial', 24, 'bold'), bg=self.colors['bg'],
                fg=self.colors['accent']).pack(side='left')
        
        self.timer = tk.Label(top, text="⏱️ 00:00:00",
                             font=('Arial', 12, 'bold'),
                             bg=self.colors['bg'], fg=self.colors['warning'])
        self.timer.pack(side='right')
        
        # Main container
        main = tk.Frame(self.root, bg=self.colors['bg'])
        main.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel
        left = tk.Frame(main, bg=self.colors['card'], width=300)
        left.pack(side='left', fill='both', padx=(0,5))
        
        tk.Label(left, text="⚙️ CONTROLS", font=('Arial', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['fg']).pack(pady=10)
        
        # Session info
        self.session_label = tk.Label(left, text="No session",
                                     bg=self.colors['card'], fg='#95a5a6')
        self.session_label.pack(pady=5)
        
        # Buttons
        btn_frame = tk.Frame(left, bg=self.colors['card'])
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        self.start_btn = tk.Button(btn_frame, text="▶ START (Ctrl+N)",
                                   command=self.start_session,
                                   bg=self.colors['accent'], fg='white',
                                   font=('Arial', 10, 'bold'), relief='flat')
        self.start_btn.pack(fill='x', pady=5)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹ STOP",
                                  command=self.stop_session,
                                  bg='#7f8c8d', fg='white',
                                  font=('Arial', 10), relief='flat', state='disabled')
        self.stop_btn.pack(fill='x', pady=5)
        
        # Voice section
        voice_frame = tk.LabelFrame(left, text="🎤 VOICE",
                                   bg=self.colors['card'], fg=self.colors['fg'])
        voice_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Button(voice_frame, text="🎤 Record", command=self.record_voice,
                 bg=self.colors['accent'], fg='white', relief='flat').pack(fill='x', padx=5, pady=3)
        
        tk.Button(voice_frame, text="📞 Call (Ctrl+V)", command=self.start_voice_call,
                 bg='#27ae60', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat').pack(fill='x', padx=5, pady=3)
        
        voice_status = "✅ Ready" if os.path.exists("my_voice.wav") else "⚠️ No sample"
        self.voice_label = tk.Label(voice_frame, text=voice_status,
                                   bg=self.colors['card'], fg=self.colors['fg'],
                                   font=('Arial', 8))
        self.voice_label.pack(pady=3)
        
        # Center - chat
        center = tk.Frame(main, bg=self.colors['card'])
        center.pack(side='left', fill='both', expand=True, padx=5)
        
        tk.Label(center, text="💬 CONVERSATION", font=('Arial', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['fg']).pack(pady=10)
        
        self.chat = scrolledtext.ScrolledText(center, wrap=tk.WORD,
                                             font=('Consolas', 11),
                                             bg=self.colors['chat_bg'],
                                             fg=self.colors['chat_fg'])
        self.chat.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.chat.tag_config('scammer', foreground='#e74c3c', font=('Consolas', 11, 'bold'))
        self.chat.tag_config('honeypot', foreground='#3498db', font=('Consolas', 11, 'bold'))
        self.chat.tag_config('system', foreground='#95a5a6', font=('Consolas', 10, 'italic'))
        
        # Input
        input_frame = tk.Frame(center, bg=self.colors['card'])
        input_frame.pack(fill='x', padx=10, pady=10)
        
        self.input = tk.Text(input_frame, height=3, font=('Arial', 11),
                           bg='#2c3e50', fg='white')
        self.input.pack(side='left', fill='both', expand=True, padx=(0,5))
        self.input.bind('<Return>', lambda e: self.send_message() or "break")
        
        tk.Button(input_frame, text="📤\nSEND", command=self.send_message,
                 bg=self.colors['accent'], fg='white',
                 font=('Arial', 10, 'bold'), relief='flat', width=8).pack(side='right')
        
        # Right - intel
        right = tk.Frame(main, bg=self.colors['card'], width=300)
        right.pack(side='right', fill='both', padx=(5,0))
        
        tk.Label(right, text="🎯 INTELLIGENCE", font=('Arial', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['fg']).pack(pady=10)
        
        self.intel = scrolledtext.ScrolledText(right, wrap=tk.WORD,
                                              font=('Courier', 10),
                                              bg='#0a0a0a', fg='#f39c12')
        self.intel.pack(fill='both', expand=True, padx=10, pady=5)
    
    def start_session(self):
        self.current_session = self.orchestrator.start_session(handoff=True)
        self.add_msg("🟢 Session started", 'system')
        self.session_label.config(text=f"Session: {self.current_session}", fg='#2ecc71')
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.session_start_time = time.time()
    
    def stop_session(self):
        self.add_msg("🔴 Session stopped", 'system')
        self.current_session = None
        self.session_start_time = None
        self.session_label.config(text="No session", fg='#95a5a6')
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
    
    def send_message(self):
        if not self.current_session:
            messagebox.showwarning("No Session", "Start a session first!")
            return
        
        msg = self.input.get("1.0", "end-1c").strip()
        if not msg:
            return
        
        self.input.delete("1.0", "end")
        self.add_msg("SCAMMER", msg, 'scammer')
        
        def process():
            result = self.orchestrator.handle_message(msg, self.current_session)
            self.root.after(0, lambda: self.handle_response(result))
        
        threading.Thread(target=process, daemon=True).start()
    
    def handle_response(self, result):
        if result.get('engaged'):
            self.add_msg("MRS. KAVITA", result['response'], 'honeypot')
            
            if result.get('extracted_intelligence'):
                self.intel.insert('end', "\n🎯 NEW:\n", 'header')
                for dtype, values in result['extracted_intelligence'].items():
                    for v in values:
                        self.intel.insert('end', f"{dtype}: {v}\n")
                self.intel.see('end')
    
    def add_msg(self, sender, msg, tag=''):
        ts = datetime.now().strftime("%H:%M:%S")
        self.chat.insert('end', f"\n[{ts}] ", 'system')
        if tag:
            self.chat.insert('end', f"{sender}:\n", tag)
        self.chat.insert('end', f"{msg}\n")
        self.chat.see('end')
    
    def record_voice(self):
        try:
            from voice_call_agent import VoiceSampleRecorder
            
            if not messagebox.askyesno("Record", "Record 15 seconds?"):
                return
            
            rec_win = tk.Toplevel(self.root)
            rec_win.title("🎤 Recording")
            rec_win.geometry("400x300")
            rec_win.configure(bg=self.colors['bg'])
            
            tk.Label(rec_win, text="🎤 RECORDING", font=('Arial', 16, 'bold'),
                    bg=self.colors['bg'], fg=self.colors['accent']).pack(pady=20)
            
            status = tk.Label(rec_win, text="Ready", font=('Arial', 12),
                            bg=self.colors['bg'], fg=self.colors['warning'])
            status.pack(pady=10)
            
            def rec():
                try:
                    recorder = VoiceSampleRecorder()
                    for i in range(3, 0, -1):
                        rec_win.after(0, lambda c=i: status.config(text=f"Starting {c}..."))
                        time.sleep(1)
                    
                    rec_win.after(0, lambda: status.config(text="🔴 RECORDING!", fg='#e74c3c'))
                    output = recorder.record_sample(15)
                    recorder.cleanup()
                    
                    rec_win.after(0, lambda: messagebox.showinfo("Done", f"Saved: {output}"))
                    rec_win.after(500, rec_win.destroy)
                    self.voice_label.config(text="✅ Ready")
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            
            threading.Thread(target=rec, daemon=True).start()
            
        except:
            messagebox.showerror("Error", "voice_call_agent.py missing!")
    
    def start_voice_call(self):
        try:
            from voice_call_agent import VoiceAgent
            
            voice_sample = "my_voice.wav" if os.path.exists("my_voice.wav") else None
            
            if not voice_sample:
                if not messagebox.askyesno("No Sample", "Use default voice?"):
                    return
            
            if not self.current_session:
                self.start_session()
            
            call_win = tk.Toplevel(self.root)
            call_win.title("📞 Voice Call")
            call_win.geometry("600x500")
            call_win.configure(bg=self.colors['bg'])
            
            tk.Label(call_win, text="📞 CALL ACTIVE", font=('Arial', 18, 'bold'),
                    bg=self.colors['bg'], fg=self.colors['accent']).pack(pady=20)
            
            status_label = tk.Label(call_win, text="Starting...",
                                   font=('Arial', 12), bg=self.colors['bg'])
            status_label.pack(pady=10)
            
            transcript = scrolledtext.ScrolledText(call_win, height=15,
                                                  bg=self.colors['chat_bg'],
                                                  fg=self.colors['chat_fg'])
            transcript.pack(fill='both', expand=True, padx=20, pady=10)
            
            agent = [None]
            
            def end():
                if agent[0]:
                    agent[0].call_active = False
                call_win.destroy()
            
            tk.Button(call_win, text="📞 END", command=end,
                     bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                     relief='flat', width=15).pack(pady=10)
            
            def run():
                try:
                    agent[0] = VoiceAgent(self.orchestrator, voice_sample)
                    status_label.config(text="🎤 Listening...")
                    transcript.insert('end', "[SYSTEM] Call started\n\n")
                    
                    turn = 0
                    while agent[0].call_active and turn < 20:
                        speech = agent[0].listen(15)
                        if not speech:
                            continue
                        
                        transcript.insert('end', f"SCAMMER: {speech}\n\n")
                        
                        if "end call" in speech.lower():
                            break
                        
                        result = self.orchestrator.handle_message(speech, self.current_session)
                        if result.get("engaged"):
                            resp = result["response"]
                            agent[0].speak(resp)
                            transcript.insert('end', f"MRS. KAVITA: {resp}\n\n")
                            turn += 1
                        
                        time.sleep(0.5)
                    
                    status_label.config(text="📞 Ended")
                except Exception as e:
                    status_label.config(text=f"Error: {e}")
                finally:
                    if agent[0]:
                        agent[0].cleanup()
            
            threading.Thread(target=run, daemon=True).start()
            
        except:
            messagebox.showerror("Error", "voice_call_agent.py missing!")
    
    def start_timer(self):
        if self.session_start_time:
            elapsed = int(time.time() - self.session_start_time)
            h, m, s = elapsed//3600, (elapsed%3600)//60, elapsed%60
            self.timer.config(text=f"⏱️ {h:02d}:{m:02d}:{s:02d}")
        self.root.after(1000, self.start_timer)

def main():
    root = tk.Tk()
    app = HoneypotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

