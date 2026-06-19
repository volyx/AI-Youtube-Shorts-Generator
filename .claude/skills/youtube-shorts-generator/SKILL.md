---
name: youtube-shorts-generator
description: Generate viral 9:16 YouTube Shorts (or TikTok/Reels clips) from a long-form YouTube URL or local video. Triggers on requests like "make shorts from this video", "extract viral clips from this YouTube link", "auto-clip this podcast", "find the best moments and crop vertical". Pipeline downloads the source, transcribes on-device via mlx-whisper, ranks highlights through a virality framework (hook / emotional peak / opinion bomb / revelation / conflict / quotable / story peak / practical value), dedupes overlapping candidates, and vertically auto-crops the top N as mp4s. Runs entirely on-device — no cloud keys required.
---

# YouTube Shorts Generator

End-to-end pipeline that turns one long video into N viral-ready vertical clips. Each clip ships with a viral score (0–100), an opening hook line, and a one-sentence reason it should perform.

Reference implementation: https://github.com/volyx/AI-Youtube-Shorts-Generator

## When to use this skill

- "Generate shorts from this YouTube video"
- "Find the most viral 60-second clips in this podcast"
- "Auto-crop this interview to 9:16"
- "Give me TikTok clips from this lecture"

If the user only wants transcription, summarization, or thumbnails — this is the wrong skill.

## Inputs to collect before running

Ask once, then proceed:
1. **Source** — YouTube URL (preferred) or path/URL to an mp4
2. **`num_clips`** — default 3
3. **`aspect_ratio`** — default `9:16` (also: `1:1`, `4:5`)
4. **`language`** — default auto-detect (forwarded to Whisper as ISO-639-1)
5. **Output JSON path** — optional; if set, dump full result there

If the user gave a URL and nothing else, use defaults and don't block on questions.

## Prerequisites (verify before first run)

- Python 3.10+ (`uv` pins 3.12 automatically)
- `ffmpeg` on PATH (`brew install ffmpeg`) — audio extraction and cropping
- `uv sync` (uv project — creates `.venv` + installs the on-device deps: mlx-whisper, opencv-python, yt-dlp, faster-whisper). Add `uv sync --group cloud-llm` only to rank via the OpenAI/Gemini SDKs instead of Ollama.
- Highlight ranking runs locally via Ollama (e.g. `ollama pull llama3.1`); no cloud key required.

If the repo isn't cloned yet, clone `https://github.com/volyx/AI-Youtube-Shorts-Generator` into the working directory.

## Pipeline (what to execute)

Run the eight stages in order. Each maps to a module in `shorts_generator/`.

1. **Download** (`local/downloader.py`) — pull the source video at the requested resolution (`360`/`480`/`720`/`1080`, default `720`); local file paths are used as-is.
2. **Transcribe** (`local/transcriber.py`) — `mlx-whisper` runs Whisper on-device on the Apple GPU (faster-whisper CPU fallback) and returns timestamped segments. No network, no per-minute billing.
3. **Classify content type** — LLM tags the video (podcast / interview / tutorial / vlog / lecture / monologue) and density. Tune the highlight prompt per type.
4. **Chunk if long** (`highlights.py`) — videos > `LONG_VIDEO_THRESHOLD` (1800s default) are split into `CHUNK_SIZE_SECONDS` (1200s default) windows with `CHUNK_OVERLAP_SECONDS` (60s default) overlap so cross-boundary highlights aren't missed.
5. **Rank highlights** — LLM scans each chunk through `VIRALITY_CRITERIA`:
   - **Hook moments** — strong opening line that stops the scroll
   - **Emotional peaks** — laughter, anger, vulnerability, awe
   - **Opinion bombs** — spicy, contrarian, debate-bait takes
   - **Revelation moments** — "wait, what?" reframes
   - **Conflict** — disagreement, tension, callouts
   - **Quotable lines** — tight, screenshot-worthy phrasing
   - **Story peaks** — climax of a narrative arc
   - **Practical value** — actionable insight a viewer will save
   Each candidate gets `start_time`, `end_time`, `score` 0–100, `title`, `hook_sentence`, `virality_reason`. Aim for 30–75s clips unless content dictates otherwise.
6. **Dedupe** — collapse overlaps. Rule: if two candidates overlap > 50%, keep the higher score, drop the other.
7. **Top-N selection** — sort surviving candidates by score, take `num_clips`.
8. **Compose vertical (LAYOUT_1)** — render each highlight as a 1080×1920 9:16 clip using **LAYOUT_1**:
   - **Top 50%** — the **screen-share** panel (slides / terminal / charts), cropped from the source composite and scaled to full width.
   - **Bottom 50%** — the **two face cams side-by-side** (`hstack`), with **burned-in subtitles** from the transcript across the bottom band.

   One GPU-accelerated `ffmpeg` pass per clip (input-seek cut + crop/scale/`hstack`/`vstack` + `h264_videotoolbox`), rendered in parallel (`LOCAL_CROP_WORKERS`). Subtitles: if this `ffmpeg` lacks libass/`drawtext` (common on Homebrew builds), render each cue to a transparent PNG with Pillow and overlay it with `enable='between(t,a,b)'`; otherwise burn an offset `.srt`/`.ass`. The source composite regions (screen panel, each cam) must be measured once per source layout from a sample frame.

## Invocation

CLI (the standard path):

```bash
uv run python main.py "<YOUTUBE_URL>" \
    --num-clips 5 \
    --aspect-ratio 9:16 \
    --output-json result.json
```

Python API (when embedding in another pipeline):

```python
from shorts_generator import generate_shorts

result = generate_shorts(
    "<URL>",
    num_clips=5,
    aspect_ratio="9:16",
)
for short in result["shorts"]:
    print(short["score"], short["title"], short["clip_url"])
```

Batch mode — `urls.txt` with one URL per line:

```bash
xargs -a urls.txt -I{} uv run python main.py "{}"
```

## CLI flags reference

| Flag | Default | Notes |
|------|---------|-------|
| `--num-clips` | `3` | How many shorts to render |
| `--aspect-ratio` | `9:16` | `9:16` for TikTok/Reels, `1:1` square, anything else by flag |
| `--format` | `720` | Source download resolution |
| `--language` | auto | Whisper language code (e.g. `en`) |
| `--output-json` | — | Dump full result (transcript + all candidates + clip URLs) |

## Output schema

```json
{
  "source_video_url": "...",
  "transcript": { "duration": 1873.4, "segments": [...] },
  "highlights": [ /* every candidate, before top-N cut */ ],
  "shorts": [
    {
      "title": "The one mistake that cost me $50K",
      "start_time": 124.3,
      "end_time": 187.6,
      "score": 92,
      "hook_sentence": "Nobody talks about this, but it killed my first startup...",
      "virality_reason": "Opens with a number + regret, peaks on a contrarian lesson",
      "clip_url": "output/short_1.mp4"
    }
  ]
}
```

`clip_url` is the local path to the rendered mp4 (the key name is kept for backward compatibility). When reporting back to the user, surface for each clip: rank, score, time range, title, hook, and clip path. Skip the raw transcript unless asked.

## Tunable knobs

- `shorts_generator/highlights.py`
  - `VIRALITY_CRITERIA` — reorder or extend signals
  - `HIGHLIGHT_SYSTEM_PROMPT` — duration sweet spot, hook rules, JSON schema
  - `CHUNK_SIZE_SECONDS` — 1200s default
  - `LONG_VIDEO_THRESHOLD` — 1800s default
  - `CHUNK_OVERLAP_SECONDS` — 60s default
- `shorts_generator/config.py` (or env vars)
  - `LLM_PROVIDER` — `ollama` (default), `openai`, or `gemini`
  - `MLX_WHISPER_MODEL` / `LOCAL_WHISPER_MODEL` — transcription model
  - `LOCAL_CROP_WORKERS` — parallel clip renders (default 3)

## Whisper transcription

Audio is transcribed on-device by `mlx-whisper` (Apple GPU via MLX; faster-whisper CPU fallback) — no network, no per-minute billing. The CLI passes `--language` straight through; leave it empty for auto-detection, or pass an ISO-639-1 code (e.g. `en`) to lock it.

## Failure modes — handle, don't paper over

- **Whisper produced no segments** — likely no detectable speech or a hard language. Retry with `--language <code>` (correct ISO-639-1) before declaring failure.
- **No local LLM for ranking** — ranking goes through Ollama if configured, otherwise the agent scores highlights from the transcript against the 8 virality criteria. No cloud key required. (If `LLM_PROVIDER=openai`/`gemini` and the key is missing, surface the exact error; never fabricate a key.)
- **Highlight ranker returned <`num_clips`** — return what survived dedupe with a note; don't pad with low-score filler.

## Done criteria

The skill is done when:
1. `result["shorts"]` has up to `num_clips` entries, each with a rendered `clip_url` (local mp4 path).
2. The user has been shown the ranked list (score, time range, title, hook, path).
3. If `--output-json` was set, the file exists and parses.

If any clip file is missing, re-run just the crop stage for that highlight rather than re-running the whole pipeline.
