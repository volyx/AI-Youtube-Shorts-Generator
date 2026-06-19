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

# LAYOUT_1 (--layout layout1): screen-share on top, two face cams side-by-side
# below, burned subtitles at the bottom. Crop boxes are "W:H:X:Y" against the
# SOURCE composite — measure once per source from a sample frame. Defaults match
# the 1920x1080 OBS layout used by the "Staff Engineer" stream.
LAYOUT1_SCREEN_CROP = os.getenv("LAYOUT1_SCREEN_CROP", "1360:800:0:140")
LAYOUT1_CAM1_CROP = os.getenv("LAYOUT1_CAM1_CROP", "560:420:1360:30")
LAYOUT1_CAM2_CROP = os.getenv("LAYOUT1_CAM2_CROP", "560:370:1360:455")

# Burned-subtitle styling (rendered with Pillow; works without libass/drawtext).
SUB_FONT = os.getenv("SUB_FONT", "/System/Library/Fonts/Supplemental/Arial Bold.ttf")
SUB_FONT_SIZE = int(os.getenv("SUB_FONT_SIZE", "50"))
SUB_Y_CENTER = int(os.getenv("SUB_Y_CENTER", "1690"))  # caption block centre, px

# Outro appended to the end of every short (empty = skip). CLI --outro overrides.
OUTRO_PATH = os.getenv("OUTRO_PATH", "").strip()


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
