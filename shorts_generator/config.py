import os

from dotenv import load_dotenv

load_dotenv()

# Highlight-ranking LLM. Defaults to a local Ollama model so no cloud key is
# needed. Set LLM_PROVIDER=openai|gemini to use a hosted model instead.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

# Transcription backend: "auto" picks mlx-whisper on Apple Silicon (GPU), else
# falls back to faster-whisper (CPU). Force with "mlx" / "faster-whisper".
LOCAL_WHISPER_BACKEND = os.getenv("LOCAL_WHISPER_BACKEND", "auto").strip().lower()
# mlx-whisper model (Apple GPU). large-v3-turbo is faster AND more accurate than base.
MLX_WHISPER_MODEL = os.getenv("MLX_WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo")
# faster-whisper model (CPU/CUDA fallback).
LOCAL_WHISPER_MODEL = os.getenv("LOCAL_WHISPER_MODEL", "base")
LOCAL_WHISPER_DEVICE = os.getenv("LOCAL_WHISPER_DEVICE", "auto")  # auto / cpu / cuda
LOCAL_OUTPUT_DIR = os.getenv("LOCAL_OUTPUT_DIR", "output")

# Clipping/encoding. "auto" uses the Apple GPU (h264_videotoolbox) on macOS,
# libx264 elsewhere. LOCAL_CROP_WORKERS renders clips in parallel.
LOCAL_VIDEO_ENCODER = os.getenv("LOCAL_VIDEO_ENCODER", "auto")
LOCAL_CROP_WORKERS = int(os.getenv("LOCAL_CROP_WORKERS", "3"))


def require_openai_key() -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Highlight ranking needs an OpenAI key when "
            "LLM_PROVIDER=openai. Add it to your .env or export it, or switch "
            "LLM_PROVIDER back to ollama."
        )
    return OPENAI_API_KEY


def require_gemini_key() -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Highlight ranking needs a Gemini key when "
            "LLM_PROVIDER=gemini. Add it to your .env or export it, or switch "
            "LLM_PROVIDER back to ollama."
        )
    return GEMINI_API_KEY
