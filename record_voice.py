"""
record_voice.py - Simple Voice Recorder
Records your voice for cloning
"""

import pyaudio
import wave
import time

def record_voice(duration: int = 15, output: str = "my_voice.wav"):
    """Record voice sample"""
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              🎤 VOICE RECORDER 🎤                            ║
╚══════════════════════════════════════════════════════════════╝

Recording {duration} seconds for voice cloning.

READ THIS SCRIPT (as elderly woman):
────────────────────────────────────────────────────────────────
"Namaste beta, this is Mrs. Kavita speaking. I am calling 
about my electricity bill. Can you help me please? My phone 
is not working. One minute, let me check. Yes yes, I am here. 
Thank you beta, you are very kind."
────────────────────────────────────────────────────────────────

Tips:
• Speak slowly
• Use elderly tone
• Add hesitations
• Say 'beta', 'ji', 'achha'

Press ENTER when ready...
    """)
    
    input()
    
    print("\n🔴 RECORDING IN 3... 2... 1...\n")
    time.sleep(1)
    
    # Setup
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024
    )
    
    print(f"🔴 RECORDING! ({duration}s)\n")
    
    frames = []
    
    # Record
    for i in range(0, int(16000 / 1024 * duration)):
        data = stream.read(1024)
        frames.append(data)
        
        if i % 15 == 0:
            elapsed = i * 1024 / 16000
            remaining = duration - elapsed
            print(f"⏺️  {elapsed:.1f}s / {duration}s (Remaining: {remaining:.1f}s)", end='\r')
    
    print(f"\n\n✅ Recording complete!")
    
    # Cleanup
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # Save
    wf = wave.open(output, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    print(f"💾 Saved: {output}")
    print(f"📊 Size: {len(frames) * 1024 / 1024:.1f} MB")
    
    return output


if __name__ == "__main__":
    record_voice(15, "my_voice.wav")