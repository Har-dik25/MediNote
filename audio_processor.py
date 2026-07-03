import warnings
# Suppress huggingface warnings for cleaner output
warnings.filterwarnings("ignore")

try:
    from transformers import pipeline
except ImportError:
    pipeline = None

# We use a very small model by default to ensure it runs on standard laptops without GPU easily.
# In a real production setup, we might use "openai/whisper-small" or "openai/whisper-base".
MODEL_NAME = "openai/whisper-tiny"

def process_audio(audio_path: str) -> str:
    """
    Transcribes an audio file using local Whisper model via HuggingFace transformers.
    Zero-cost implementation.
    """
    if pipeline is None:
        return "[Mock Transcription] Patient presents with mild headache and fever for 3 days. Prescribed paracetamol. Need to check interactions if taking other meds."
    
    try:
        transcriber = pipeline("automatic-speech-recognition", model=MODEL_NAME)
        result = transcriber(audio_path)
        return result.get("text", "")
    except Exception as e:
        print(f"Error in transcription: {e}")
        return f"[Error in transcription fallback] Could not process audio: {str(e)}"
