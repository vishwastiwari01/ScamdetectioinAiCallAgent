# %% [markdown]
# # 🎤 Qwen3-TTS Voice Clone API for Honeypot
# 
# **Simple Voice Cloning with Gradio API**
# 
# This notebook:
# 1. Loads ONLY the voice clone model (memory efficient)
# 2. Creates a Gradio interface with API endpoint
# 3. Exposes public URL you can use in FastAPI
# 
# ---

# %% [code]
# ===== CELL 1: Install Packages =====
print("📦 Installing packages...")
!pip install -q git+https://github.com/QwenLM/Qwen3-TTS.git
!pip install -q transformers accelerate torchaudio gradio huggingface_hub
!pip install -q torchcodec soundfile
print("✅ Packages installed!")

# %% [code]
# ===== CELL 2: Authenticate =====
try:
    # KAGGLE
    from kaggle_secrets import UserSecretsClient
    from huggingface_hub import login
    user_secrets = UserSecretsClient()
    HF_TOKEN = user_secrets.get_secret("HF_TOKEN")
    login(token=HF_TOKEN)
    print("✅ Authenticated (Kaggle)")
except:
    # COLAB
    from google.colab import userdata
    from huggingface_hub import login
    HF_TOKEN = userdata.get("HF_TOKEN")
    login(token=HF_TOKEN)
    print("✅ Authenticated (Colab)")

# %% [code]
# ===== CELL 3: Import & Check GPU =====
import torch
import torchaudio
import numpy as np
import soundfile as sf
import tempfile
import os
import gc
import gradio as gr
from qwen_tts import Qwen3TTSModel
import base64
import io

print(f"CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"GPU Memory: {gpu_mem:.2f} GB")
    device = "cuda"
else:
    print("⚠️ No GPU - will be SLOW")
    device = "cpu"

# %% [code]
# ===== CELL 4: Load ONLY Voice Clone Model =====
print("📥 Loading Voice Clone model...")

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",  # Clone model only
    dtype=torch.float16,
    token=True,
    device_map="cuda" if torch.cuda.is_available() else "cpu",
)

print("✅ Model loaded!")
if torch.cuda.is_available():
    print(f"📊 GPU Memory: {torch.cuda.memory_allocated()/1e9:.2f} GB")

# %% [code]
# ===== CELL 5: Voice Clone Function =====

def clone_voice(
    reference_audio,  # Gradio audio input
    reference_text,   # What was said in reference
    target_text,      # What you want to say
    language="Auto"
):
    """
    Clone voice from reference audio and generate new speech
    
    Args:
        reference_audio: tuple (sample_rate, audio_data) from Gradio
        reference_text: str - transcript of reference audio
        target_text: str - text to synthesize
        language: str - language code or "Auto"
    
    Returns:
        str: path to generated audio file
    """
    
    try:
        # Handle Gradio audio input
        if reference_audio is None:
            return None
        
        # Gradio returns (sample_rate, numpy_array)
        ref_sr, ref_audio = reference_audio
        
        # Convert to mono if stereo
        if len(ref_audio.shape) > 1:
            ref_audio = ref_audio.mean(axis=1)
        
        # Normalize to float32 in range [-1, 1]
        if ref_audio.dtype == np.int16:
            ref_audio = ref_audio.astype(np.float32) / 32768.0
        elif ref_audio.dtype == np.int32:
            ref_audio = ref_audio.astype(np.float32) / 2147483648.0
        
        # Set language
        lang = None if language == "Auto" else language
        
        # Generate cloned voice
        print(f"🎤 Cloning voice...")
        print(f"   Reference: {len(ref_audio)/ref_sr:.2f}s audio")
        print(f"   Target: {target_text[:50]}...")
        
        wavs, sr = model.generate_voice_clone(
            text=target_text,
            language=lang,
            ref_audio=(ref_audio, ref_sr),  # Tuple format
            ref_text=reference_text,
            x_vector_only_mode=False,  # Use transcript for better quality
        )
        
        # Save to temp file
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        sf.write(output_path, wavs[0], sr)
        
        print(f"✅ Generated: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

# %% [code]
# ===== CELL 6: API Function (for FastAPI) =====

def clone_voice_api(
    reference_audio_b64: str,  # Base64 encoded audio
    reference_text: str,
    target_text: str,
    language: str = "Auto"
):
    """
    API version that accepts base64 audio
    This is what your FastAPI will call
    
    Returns:
        dict with base64 encoded audio
    """
    
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(reference_audio_b64)
        
        # Load audio from bytes
        audio_io = io.BytesIO(audio_bytes)
        ref_audio, ref_sr = torchaudio.load(audio_io)
        
        # Convert to numpy
        ref_audio = ref_audio.squeeze().numpy()
        
        # Set language
        lang = None if language == "Auto" else language
        
        # Generate
        wavs, sr = model.generate_voice_clone(
            text=target_text,
            language=lang,
            ref_audio=(ref_audio, ref_sr),
            ref_text=reference_text,
            x_vector_only_mode=False,
        )
        
        # Convert to WAV bytes
        wav_io = io.BytesIO()
        sf.write(wav_io, wavs[0], sr, format='WAV')
        wav_bytes = wav_io.getvalue()
        
        # Return as base64
        return {
            "audio_b64": base64.b64encode(wav_bytes).decode('utf-8'),
            "sample_rate": sr,
            "status": "success"
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

# %% [code]
# ===== CELL 7: Gradio Interface with API =====

LANGUAGES = ["Auto", "English", "Chinese", "Hindi", "Japanese", "Korean"]

# Create interface
with gr.Blocks(title="Voice Clone API") as demo:
    gr.Markdown("# 🎤 Voice Clone API for AI Honeypot")
    gr.Markdown("**Clone your voice and use it in FastAPI**")
    
    with gr.Row():
        with gr.Column():
            # Reference audio upload
            ref_audio = gr.Audio(
                label="📁 Upload Your Voice Sample (3-15 seconds)",
                type="numpy"
            )
            
            # Reference transcript
            ref_text = gr.Textbox(
                label="📝 What did you say in the audio?",
                placeholder="Type the exact transcript...",
                lines=3,
                value=""
            )
            
        with gr.Column():
            # Target text
            target_text = gr.Textbox(
                label="🎯 What should I say? (in your cloned voice)",
                placeholder="Type what you want to generate...",
                lines=3,
                value="Hello beta, this is calling. Can you help me with my electricity bill?"
            )
            
            # Language
            language = gr.Dropdown(
                choices=LANGUAGES,
                value="Auto",
                label="🌍 Language"
            )
            
            # Generate button
            generate_btn = gr.Button("🎵 Clone Voice & Generate", variant="primary")
    
    # Output
    output_audio = gr.Audio(label="🔊 Generated Audio", type="filepath")
    
    # Connect function
    generate_btn.click(
        clone_voice,
        inputs=[ref_audio, ref_text, target_text, language],
        outputs=output_audio
    )
    
    # Usage instructions
    gr.Markdown("""
    ---
    ### 📖 How to Use
    
    **1. Record Your Voice Sample:**
    - Record 5-15 seconds of clear speech
    - Act as the elderly persona you want
    - No background noise
    - Save as WAV or MP3
    
    **2. Upload & Transcribe:**
    - Upload the audio file
    - Type EXACTLY what you said (important for quality!)
    
    **3. Generate:**
    - Type what you want the AI to say
    - Click generate
    - Your cloned voice will speak the new text!
    
    ---
    ### 🔗 API Usage (for FastAPI)
    
    This interface exposes an API endpoint at:
    ```
    https://YOUR-URL.gradio.live/api/predict
    ```
    
    **Python Example:**
    ```python
    import requests
    import base64
    
    # Read your voice sample
    with open("my_voice.wav", "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()
    
    # Call API
    response = requests.post(
        "https://YOUR-URL.gradio.live/api/predict",
        json={
            "data": [
                audio_b64,           # Reference audio (base64)
                "Hello, testing",    # Reference text
                "Hello beta!",       # Target text
                "Auto"               # Language
            ]
        }
    )
    
    result = response.json()
    output_audio_b64 = result['data'][0]
    ```
    
    ---
    ### 💡 Tips
    - **Better Quality:** Always provide the transcript
    - **Speed:** 3-10 seconds on T4 GPU
    - **Best Results:** Clear audio, accurate transcript, native language
    """)

# Launch with API enabled
print("\n🚀 Launching Gradio with API...")
demo.launch(
    share=True,      # Creates public URL
    debug=True,
    server_name="0.0.0.0",
    server_port=7860
)

print("""
╔═══════════════════════════════════════════════════════════════╗
║             🎤 VOICE CLONE API IS LIVE! 🎤                   ║
╚═══════════════════════════════════════════════════════════════╝

✅ Your Gradio interface is running!

📡 PUBLIC URL: https://xxxxxxxxxxxx.gradio.live
🔗 API ENDPOINT: https://xxxxxxxxxxxx.gradio.live/api/predict

Copy the public URL above and use it in your FastAPI config!

The interface will stay active while this notebook runs.
For 24/7 availability, keep the notebook running or deploy to HF Spaces.
""")