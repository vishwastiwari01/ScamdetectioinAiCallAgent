"""
OPTIMIZED FASTAPI VOICE HONEYPOT - REDUCED LATENCY VERSION
Faster responses, better text handling, retry logic for OpenRouter
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict
import requests
import base64
import io
import speech_recognition as sr
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from openrouter_integration import AIEnhancedOrchestrator, load_api_key

app = FastAPI(title="Enhanced Voice Honeypot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=4)

# ============================================================================
# CONFIGURATION
# ============================================================================

SARVAM_API_KEY = "sk_wzeate0h_sAXDre0emvaKK1FczN8l1BvJ"
SARVAM_API_URL = "https://api.sarvam.ai/text-to-speech/stream"
USE_TTS = True

# ============================================================================
# FALLBACK TTS (Google)
# ============================================================================

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

class FallbackTTSAgent:
    def synthesize(self, text: str) -> bytes:
        if not GTTS_AVAILABLE:
            return None
        try:
            tts = gTTS(text=text, lang='en', tld='co.in')
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            return audio_bytes.read()
        except:
            return None

# ============================================================================
# OPTIMIZED SARVAM AI TTS WITH SHORTER TIMEOUT
# ============================================================================

class SarvamTTSAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = SARVAM_API_URL
        self.fallback = FallbackTTSAgent() if GTTS_AVAILABLE else None
        print("✅ Sarvam AI TTS initialized (optimized)")
    
    def synthesize(self, text: str) -> Optional[bytes]:
        has_hindi = any(ord(char) > 2304 and ord(char) < 2432 for char in text)
        target_language = "hi-IN" if has_hindi else "en-IN"
        
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "target_language_code": target_language,
            "speaker": "shreya",
            "model": "bulbul:v3",
            "pace": 1.15,  # Slightly faster
            "speech_sample_rate": 8000,
            "output_audio_codec": "mp3",
            "enable_preprocessing": True
        }
        
        try:
            # Reduced timeout from 10 to 5 seconds
            with requests.post(self.api_url, headers=headers, json=payload, stream=True, timeout=5) as response:
                response.raise_for_status()
                audio_data = b''
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        audio_data += chunk
                return audio_data
        except Exception as e:
            print(f"⚠️ Sarvam TTS failed: {e}, using fallback")
            if self.fallback:
                return self.fallback.synthesize(text)
            return None

# ============================================================================
# SPEECH RECOGNITION
# ============================================================================

class STTAgent:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = False
        print("✅ Speech Recognition initialized")
    
    def transcribe(self, audio_bytes: bytes) -> str:
        """Convert audio to text with robust error handling"""
        
        # Quick validation
        if len(audio_bytes) < 100:
            print("⚠️ Audio too short (< 100 bytes)")
            return ""
        
        print(f"🎤 Processing {len(audio_bytes)} bytes of audio")
        
        try:
            from pydub import AudioSegment
            
            # Try multiple audio formats
            audio = None
            errors = []
            
            # Try 1: As WebM (most common from browser)
            try:
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
                print("✅ Loaded as WebM")
            except Exception as e:
                errors.append(f"WebM: {str(e)[:50]}")
            
            # Try 2: As Opus
            if not audio:
                try:
                    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="opus")
                    print("✅ Loaded as Opus")
                except Exception as e:
                    errors.append(f"Opus: {str(e)[:50]}")
            
            # Try 3: Let pydub auto-detect
            if not audio:
                try:
                    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
                    print("✅ Loaded with auto-detect")
                except Exception as e:
                    errors.append(f"Auto: {str(e)[:50]}")
            
            # Try 4: As WAV directly
            if not audio:
                try:
                    audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
                    print("✅ Loaded as WAV")
                except Exception as e:
                    errors.append(f"WAV: {str(e)[:50]}")
            
            # If all failed, give up
            if not audio:
                print(f"❌ All format attempts failed:")
                for err in errors:
                    print(f"   - {err}")
                return ""
            
            # Convert to standard format
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_frame_rate(16000)  # 16kHz
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Export to WAV
            wav_io = io.BytesIO()
            audio.export(wav_io, format='wav')
            wav_io.seek(0)
            
            # Use speech recognition
            with sr.AudioFile(wav_io) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio_data = self.recognizer.record(source)
            
            # Recognize
            text = self.recognizer.recognize_google(audio_data, language='en-IN')
            print(f"✅ Transcribed: '{text}'")
            return text
                
        except ImportError:
            print("⚠️ pydub not available")
            return ""
        except sr.UnknownValueError:
            print("⚠️ No clear speech detected")
            return ""
        except sr.RequestError as e:
            print(f"⚠️ Google API error: {e}")
            return ""
        except Exception as e:
            print(f"⚠️ STT error: {type(e).__name__}: {str(e)[:100]}")
            return ""

# ============================================================================
# ENHANCED VOICE MANAGER - OPTIMIZED
# ============================================================================

class EnhancedVoiceManager:
    def __init__(self):
        self.sessions = {}
        openrouter_key = load_api_key()
        self.orchestrator = AIEnhancedOrchestrator(openrouter_key)
        self.tts = SarvamTTSAgent(SARVAM_API_KEY) if USE_TTS else None
        self.stt = STTAgent()
        print("✅ Enhanced Voice Manager initialized (optimized)")
    
    def start_call(self, call_id: str, mode: str = "voice") -> Dict:
        # Use orchestrator's start_session method
        session_id = self.orchestrator.start_session(handoff=True)
        
        self.sessions[call_id] = {
            'session_id': session_id,
            'started_at': datetime.now(),
            'turns': 0,
            'mode': mode,
            'first_response': True  # Track first response
        }
        
        # DIFFERENT BEHAVIOR FOR TEXT VS VOICE
        if mode == "text":
            # Text mode: Send greeting immediately
            greeting_text = "Namaste ji! Main Mrs. Kavita bol rahi hoon."
            greeting_audio = None
        else:
            # Voice mode: Silent at first - wait for scammer to speak
            greeting_text = "Hello?"  # Very short initial greeting
            greeting_audio = self.tts.synthesize(greeting_text) if self.tts else None
        
        return {
            'session_id': session_id,
            'greeting_text': greeting_text,
            'greeting_audio_b64': base64.b64encode(greeting_audio).decode() if greeting_audio else None,
            'tts_enabled': greeting_audio is not None,
            'mode': mode
        }
    
    def process_text(self, call_id: str, text: str) -> Dict:
        if call_id not in self.sessions:
            return {'error': 'Call not found'}
        
        session_id = self.sessions[call_id]['session_id']
        
        # Process with retry logic (max 2 attempts)
        result = None
        for attempt in range(2):
            try:
                result = self.orchestrator.handle_message(text, session_id, sender="scammer_voice")
                if result and result.get('response'):
                    break
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                if attempt == 1:  # Last attempt
                    # Use fallback response
                    result = {
                        'response': 'Ek minute... network thoda slow hai. Aap phir se boliye?',
                        'analysis': {'threat_level': 0},
                        'extracted_intelligence': {},
                        'psychological_fatigue_score': 0
                    }
        
        response_text = result.get('response', '')
        if not response_text:
            return {'error': 'Could not generate response'}
        
        intelligence = result.get('extracted_intelligence', {})
        
        # NO AUDIO FOR TEXT MODE
        self.sessions[call_id]['turns'] += 1
        
        return {
            'response_text': response_text,
            'response_audio_b64': None,
            'intelligence': intelligence,
            'threat_level': result.get('analysis', {}).get('threat_level', 0),
            'psychological_fatigue_score': result.get('psychological_fatigue_score', 0),
            'scammer_persona': result.get('analysis', {}).get('scammer_persona', 'unknown'),
            'tts_enabled': False
        }
    
    async def process_audio_async(self, call_id: str, audio_bytes: bytes) -> Dict:
        """Async version with parallel processing"""
        if call_id not in self.sessions:
            return {'error': 'Call not found'}
        
        # Run STT in thread pool
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(executor, self.stt.transcribe, audio_bytes)
        
        if not transcript:
            # If STT fails, return helpful message
            return {
                'error': 'no_speech_detected',
                'transcript': '',
                'response_text': 'Hello? I cannot hear you properly. Can you speak louder?',
                'response_audio_b64': None,
                'intelligence': {},
                'threat_level': 0,
                'psychological_fatigue_score': 0,
                'scammer_persona': 'unknown',
                'tts_enabled': False
            }
        
        session_id = self.sessions[call_id]['session_id']
        
        print(f"📝 Transcribed: {transcript}")
        
        # Process text with retry
        result = None
        for attempt in range(2):
            try:
                result = await loop.run_in_executor(
                    executor,
                    self.orchestrator.handle_message,
                    transcript, session_id, "scammer_voice"
                )
                if result and result.get('response'):
                    break
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                if attempt == 1:
                    result = {
                        'response': 'Haan ji... aap kya keh rahe the? Network problem hai.',
                        'analysis': {'threat_level': 0},
                        'extracted_intelligence': {},
                        'psychological_fatigue_score': 0
                    }
        
        response_text = result.get('response', '')
        
        # Generate TTS in parallel
        response_audio = None
        if response_text and self.tts:
            response_audio = await loop.run_in_executor(executor, self.tts.synthesize, response_text)
        
        intelligence = result.get('extracted_intelligence', {})
        self.sessions[call_id]['turns'] += 1
        
        return {
            'transcript': transcript,
            'response_text': response_text,
            'response_audio_b64': base64.b64encode(response_audio).decode() if response_audio else None,
            'intelligence': intelligence,
            'threat_level': result.get('analysis', {}).get('threat_level', 0),
            'psychological_fatigue_score': result.get('psychological_fatigue_score', 0),
            'scammer_persona': result.get('analysis', {}).get('scammer_persona', 'unknown'),
            'tts_enabled': response_audio is not None
        }
    
    def get_session_report(self, call_id: str) -> Dict:
        if call_id not in self.sessions:
            return {'error': 'Call not found'}
        session_id = self.sessions[call_id]['session_id']
        from full_honeypot_system import HoneypotDatabase
        db = HoneypotDatabase()
        return db.get_session_report(session_id)

manager = EnhancedVoiceManager()

# ============================================================================
# ENDPOINTS - OPTIMIZED
# ============================================================================

class CallRequest(BaseModel):
    call_id: str
    mode: Optional[str] = "voice"  # "voice" or "text"

class TextRequest(BaseModel):
    call_id: str
    text: str

@app.post("/call/start")
async def start_call(request: CallRequest):
    return manager.start_call(request.call_id, request.mode)

@app.post("/call/text")
async def process_text(request: TextRequest):
    """Fast text processing - no TTS"""
    return manager.process_text(request.call_id, request.text)

@app.post("/call/audio")
async def process_audio(call_id: str, audio: UploadFile = File(...)):
    """Optimized audio processing with async"""
    audio_bytes = await audio.read()
    return await manager.process_audio_async(call_id, audio_bytes)

@app.get("/call/report/{call_id}")
async def get_report(call_id: str):
    report = manager.get_session_report(call_id)
    if 'error' in report:
        return JSONResponse(content=report, status_code=404)
    return JSONResponse(content=report, headers={"Content-Disposition": f"attachment; filename=honeypot_report_{call_id}.json"})

@app.get("/health")
async def health():
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'sessions': len(manager.sessions),
        'tts_enabled': USE_TTS
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Enhanced Voice Honeypot (Optimized)")
    print("📍 Text mode: Fast responses, no audio")
    print("📍 Voice mode: Full TTS with audio")
    uvicorn.run(app, host="0.0.0.0", port=8000)