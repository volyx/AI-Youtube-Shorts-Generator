"""End-to-end orchestrator.

Fully on-device: yt-dlp + mlx-whisper (Apple GPU) + local LLM (Ollama by
default) + ffmpeg/opencv. No cloud keys required. LLM_PROVIDER selects
ollama/openai/gemini for the highlight-ranking step.
"""
from typing import Dict, List, Optional

from .highlights import get_highlights


def generate_shorts(
    youtube_url: str,
    num_clips: int = 3,
    aspect_ratio: str = "9:16",
    download_format: str = "720",
    language: Optional[str] = None,
    layout: str = "crop",
    subs: bool = True,
    outro: Optional[str] = None,
) -> Dict:
    """Run the full pipeline and return a structured result.

    Args:
        youtube_url: source URL, file:// URL, or local path.
        num_clips: how many shorts to render.
        aspect_ratio: e.g. "9:16", "1:1" (used by layout="crop").
        download_format: source resolution ("360" / "480" / "720" / "1080").
        language: ISO-639-1 to force Whisper language detection.
        layout: "crop" (generic speaker-centred crop) or "layout1"
            (screen-share on top, two cams + burned subtitles below).
        subs: burn transcript subtitles (layout1 only).
        outro: path to an outro mp4 to append to every short (None = skip;
            defaults to config.OUTRO_PATH when called via the CLI).

    Returns:
        {
          "source_video_url": str,   # local path
          "transcript": {...},
          "highlights": [...],       # all candidates ranked
          "shorts": [...],           # top `num_clips` with local clip path
        }
    """
    from .local.clipper import compose_layout1_highlights, crop_highlights_local
    from .local.downloader import download_youtube_local
    from .local.llm import call_local_llm
    from .local.outro import append_outro
    from .local.transcriber import transcribe_local

    source_path = download_youtube_local(youtube_url, fmt=download_format)

    transcript = transcribe_local(source_path, language=language)
    if not transcript["segments"]:
        raise RuntimeError(
            "Whisper produced no segments. The video may have no detectable speech."
        )

    highlights_result = get_highlights(transcript, num_clips=num_clips, llm_fn=call_local_llm)
    all_highlights: List[Dict] = highlights_result.get("highlights", [])
    if not all_highlights:
        raise RuntimeError("Highlight generator returned zero clips.")

    top = sorted(all_highlights, key=lambda h: int(h.get("score", 0)), reverse=True)[:num_clips]
    print(f"[pipeline] rendering {len(top)} of {len(all_highlights)} candidates "
          f"(layout={layout})", flush=True)

    if layout == "layout1":
        shorts = compose_layout1_highlights(
            source_path, top, segments=transcript["segments"] if subs else None)
    else:
        shorts = crop_highlights_local(source_path, top, aspect_ratio=aspect_ratio)

    if outro:
        import os
        for s in shorts:
            clip = s.get("clip_url")
            if clip:
                tmp = clip + ".outro.mp4"
                append_outro(clip, outro, tmp)
                os.replace(tmp, clip)

    return {
        "source_video_url": source_path,
        "transcript": transcript,
        "highlights": all_highlights,
        "shorts": shorts,
    }
