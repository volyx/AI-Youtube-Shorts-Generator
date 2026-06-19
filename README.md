# AI YouTube Shorts Generator

**The open-source alternative to Opus Clip, Vidyo.ai, Klap, SubMagic, 2short.ai, and other AI clipping tools.** Drop in any long-form YouTube video and get back ranked, viral-ready 9:16 shorts — for free, with no per-clip credits, no watermarks, and full control over the highlight algorithm.

Built for creators, agencies, and developers who don't want to pay $20–$300/month or be capped on minutes processed. Runs **entirely on-device**: Whisper transcription on the Apple GPU (`mlx-whisper`), a local LLM for highlight detection, and `ffmpeg`/OpenCV for vertical cropping. No cloud keys required.

![longshorts](https://github.com/user-attachments/assets/3f5d1abf-bf3b-475f-8abf-5e253003453a)

## Why Use This Instead of Opus Clip / Vidyo.ai / Klap?

| | This repo | Opus Clip / Vidyo.ai / Klap / SubMagic |
|---|---|---|
| **Price** | Free + open source, runs on your machine | $20–$300/month subscriptions |
| **Per-clip credits** | None — process unlimited videos | Monthly minute caps, overage fees |
| **Watermarks** | Never | On free tiers |
| **Highlight algorithm** | Fully editable virality framework | Black box |
| **Output format** | Any aspect ratio, any resolution | Locked presets |
| **Batch processing** | `xargs` an entire URL list | Manual upload one-by-one |
| **JSON / API output** | Built-in (`--output-json`) | Limited or paid tier only |
| **Self-hostable** | Yes — runs on your machine or server | SaaS only, your videos sit on their servers |
| **Privacy** | Nothing leaves your machine | Your videos sit on their servers |
| **White-label / embeddable** | Yes — MIT licensed, import as Python lib | No |

## Features

- **🎬 YouTube In, Vertical Out**: Hand it any YouTube URL — get back N viral-ready 9:16 mp4s
- **💻 Fully On-Device**: `yt-dlp` download, `mlx-whisper`/`faster-whisper` transcription, a local LLM for ranking, and `ffmpeg`/`opencv` cropping — nothing leaves your machine
- **🤖 Virality-Aware Highlight Selection**: Clips ranked on hooks, emotional peaks, opinion bombs, revelation moments, conflict, quotable lines, story peaks, and practical value — not just generic "interesting"
- **📈 Score + Hook + Reason for Every Clip**: Each highlight comes with a viral score, an opening hook line, and a one-sentence explanation of why it works
- **🎤 GPU-Accelerated Whisper**: `mlx-whisper` runs on the Apple GPU (Apple Silicon); `faster-whisper` is the CPU/CUDA fallback
- **🧩 Long-Video Aware**: Videos over 30 minutes are auto-chunked with overlap so nothing gets missed
- **♻️ Smart Dedupe**: Overlapping highlights are collapsed by score so you never get two near-duplicate clips
- **🎯 Smart Vertical Crop**: `ffmpeg` + OpenCV face tracking centres the crop on the speaker
- **📱 Any Aspect Ratio**: 9:16 for TikTok/Reels/Shorts, 1:1 for square, anything else by flag
- **🧰 CLI + Python Library**: Use it from the shell or import `generate_shorts(...)` into your own pipeline
- **📦 JSON Output**: `--output-json` dumps the full result (transcript + every candidate highlight + final clip paths) for downstream automation

## Installation

### Prerequisites

- Python 3.10+ (`uv` pins 3.12 automatically — no system Python needed)
- `ffmpeg` on your PATH (`brew install ffmpeg`) — audio extraction and cropping
- A local LLM for highlight ranking — [Ollama](https://ollama.com) is the default (`ollama pull llama3.1`). Optionally use OpenAI/Gemini by setting `LLM_PROVIDER`.

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/volyx/AI-Youtube-Shorts-Generator
   cd AI-Youtube-Shorts-Generator
   ```

2. **Install dependencies with uv:**

   This is a [uv](https://docs.astral.sh/uv/) project. A single `uv sync` creates
   the `.venv` (Python pinned by `.python-version`) and installs the on-device
   pipeline deps:
   ```bash
   uv sync
   ```
   No `source .venv/bin/activate` needed — prefix commands with `uv run`.

   Optional:
   ```bash
   uv sync --group cloud-llm     # add OpenAI/Gemini SDKs for hosted LLM ranking
   ```
   Add a new dependency with `uv add <pkg>` (use `--group local` / `--group cloud-llm` to target a group).

3. **(Optional) Set up environment variables:**

   Defaults work out of the box with Ollama. Create a `.env` only to override them:
   ```bash
   LLM_PROVIDER=ollama               # ollama (default) / openai / gemini
   OLLAMA_MODEL=llama3.1
   OLLAMA_HOST=http://localhost:11434

   # Only if LLM_PROVIDER=openai or gemini:
   # OPENAI_API_KEY=your_openai_key_here
   # OPENAI_MODEL=gpt-4o-mini
   # GEMINI_API_KEY=your_gemini_key_here
   # GEMINI_MODEL=gemini-2.5-flash

   LOCAL_WHISPER_BACKEND=auto        # auto / mlx / faster-whisper
   MLX_WHISPER_MODEL=mlx-community/whisper-large-v3-turbo
   LOCAL_WHISPER_MODEL=base          # faster-whisper fallback model
   LOCAL_WHISPER_DEVICE=auto         # auto / cpu / cuda
   LOCAL_OUTPUT_DIR=output           # where rendered mp4s land
   ```

## Usage

### Single video

```bash
uv run python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Rendered shorts are written to `./output/short_01.mp4`, `short_02.mp4`, … (override with `LOCAL_OUTPUT_DIR`).

### With options

```bash
uv run python main.py "https://www.youtube.com/watch?v=VIDEO_ID" \
    --num-clips 5 \
    --aspect-ratio 9:16 \
    --output-json result.json
```

### Local file or path

Pass a `file://` URL or a direct filesystem path and skip YouTube entirely:

```bash
uv run python main.py "/Users/you/Videos/input.mp4"
uv run python main.py "file:///Users/you/Videos/input.mp4"
```

The Python API works the same way:

```python
from shorts_generator import generate_shorts

result = generate_shorts(
    "/Users/you/Videos/input.mp4",
    num_clips=5,
    aspect_ratio="9:16",
)
for short in result["shorts"]:
    print(short["score"], short["title"], short["clip_url"])
```

Transcription is cached as an `.srt` file in `LOCAL_OUTPUT_DIR` using the
video's base name. If the cache already exists and is newer than the source
file, the app reuses it instead of running Whisper again.

Downloads are also cached in `LOCAL_OUTPUT_DIR` as `source_<youtube_id>.mp4`
when the input is a YouTube URL. If that file already exists, the app skips
`yt-dlp` and reuses the cached video.

### Batch processing

Create a `urls.txt` file with one URL per line, then:

```bash
xargs -a urls.txt -I{} uv run python main.py "{}"
```

### CLI flags

| Flag | Default | Notes |
|------|---------|-------|
| `--num-clips` | `3` | How many shorts to render |
| `--aspect-ratio` | `9:16` | Any ratio; `9:16` for TikTok/Reels, `1:1` for square |
| `--format` | `720` | Source download resolution: `360` / `480` / `720` / `1080` |
| `--language` | auto | Force Whisper language code (e.g. `en`) |
| `--output-json` | — | Dump the full result (transcript + all candidates) to a file |

## How It Works

1. **Download**: `yt-dlp` fetches the source video from YouTube (local file paths are used as-is)
2. **Transcribe**: `mlx-whisper` (Apple GPU) produces a timestamped transcript; `faster-whisper` is the CPU/CUDA fallback
3. **Detect content type**: The LLM classifies the video (podcast, interview, tutorial, vlog, etc.) and density, so the prompt can be tuned per content style
4. **Long-video chunking**: Videos > 30 min are split into 20-min overlapping chunks
5. **Highlight ranking**: The LLM scans the transcript through a virality framework — hook moments, emotional peaks, opinion bombs, revelations, conflict, quotables, story peaks, practical value — and emits ranked candidates with scores 0–100
6. **Dedupe**: Overlapping candidates are collapsed by score (>50% overlap → keep the higher score)
7. **Top-N selection**: The top `--num-clips` candidates are selected
8. **Auto-crop**: Each highlight is rendered as a vertical short at the requested aspect ratio with `ffmpeg` + OpenCV face tracking

**Output**: a list of mp4 paths plus, for each clip, its title, viral score, hook sentence, and a one-line reason explaining why it should perform.

## Output

Console output looks like:

```
========================================================================
Highlights:    7 candidates → kept top 3
========================================================================

#1  score=92  124.3s → 187.6s
     title:  The one mistake that cost me $50K
     hook:   "Nobody talks about this, but it killed my first startup..."
     clip:   output/short_1.mp4

#2  score=88  ...
```

`--output-json result.json` produces:

```json
{
  "source_video_url": "...",
  "transcript": { "duration": 1873.4, "segments": [...] },
  "highlights": [ {...}, {...}, ... ],
  "shorts": [
    {
      "title": "...",
      "start_time": 124.3,
      "end_time": 187.6,
      "score": 92,
      "hook_sentence": "...",
      "virality_reason": "...",
      "clip_url": "output/short_1.mp4"
    }
  ]
}
```

(`clip_url` is the local path to the rendered mp4; the key name is kept for backward compatibility.)

## Configuration

### Highlight selection criteria
Edit `shorts_generator/highlights.py`:
- **Virality framework**: `VIRALITY_CRITERIA` — the ranked list of signals the LLM optimizes for
- **System prompt**: `HIGHLIGHT_SYSTEM_PROMPT` — duration sweet spot, hook rules, JSON schema
- **Chunk size**: `CHUNK_SIZE_SECONDS` (default 1200) — chunk length for long videos
- **Long-video threshold**: `LONG_VIDEO_THRESHOLD` (default 1800) — videos longer than this are chunked
- **Chunk overlap**: `CHUNK_OVERLAP_SECONDS` (default 60) — overlap between chunks so cross-boundary clips aren't missed

### LLM, Whisper, and cropping
Edit `shorts_generator/config.py` (or set env vars):
- `LLM_PROVIDER` — `ollama` (default), `openai`, or `gemini`
- `OLLAMA_MODEL` / `OLLAMA_HOST` — local ranking model and endpoint
- `MLX_WHISPER_MODEL` / `LOCAL_WHISPER_MODEL` — transcription model (Apple GPU / CPU fallback)
- `LOCAL_VIDEO_ENCODER` — `auto` (h264_videotoolbox on macOS / libx264 elsewhere)
- `LOCAL_CROP_WORKERS` — parallel clip renders (default 3)

Pass `--language <code>` to lock recognition to a specific language; otherwise it auto-detects.

## Project Structure

```
AI-Youtube-Shorts-Generator/
├── main.py                       CLI entry point
├── pyproject.toml                deps (`local` / `cloud-llm` groups), uv-managed
├── uv.lock                       pinned, reproducible lockfile
├── .python-version               pins the interpreter (3.12)
├── .env.example
└── shorts_generator/
    ├── config.py                 env / settings (LLM + Whisper + cropping)
    ├── highlights.py             LLM virality ranking (pluggable backend)
    ├── pipeline.py               end-to-end orchestrator
    └── local/                    on-device backends
        ├── downloader.py         yt-dlp download
        ├── transcriber.py        mlx-whisper / faster-whisper transcription
        ├── llm.py                Ollama / OpenAI / Gemini client selector
        └── clipper.py            ffmpeg cut + OpenCV vertical crop
```

## Troubleshooting

### Whisper produced no segments
The video may have no detectable speech, or it may be in a language Whisper struggles with. Try passing `--language en` (or the correct ISO-639-1 code) to skip auto-detection.

### Can't reach Ollama
Install [Ollama](https://ollama.com) and pull a model (`ollama pull llama3.1`), or set `LLM_PROVIDER=openai`/`gemini` with the corresponding API key.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.
