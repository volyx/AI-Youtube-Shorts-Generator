"""Local clipping: a single GPU-accelerated ffmpeg pass per highlight.

For each highlight we:
  1. Sample a handful of downscaled frames to find a stable crop centre
     (largest face via Haar; falls back to frame centre if OpenCV/faces absent).
  2. Cut + reframe + encode in ONE ffmpeg pass using input seeking and the
     hardware encoder (h264_videotoolbox on Apple Silicon, libx264 elsewhere).

This replaces the old three-encode path (ffmpeg cut -> OpenCV mp4v reframe ->
ffmpeg remux) plus per-frame full-resolution face detection, which was the
pipeline's dominant cost.
"""
import os
import platform
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

from ..config import (
    LAYOUT1_CAM1_CROP,
    LAYOUT1_CAM2_CROP,
    LAYOUT1_SCREEN_CROP,
    LOCAL_CROP_WORKERS,
    LOCAL_OUTPUT_DIR,
    LOCAL_VIDEO_ENCODER,
)
from . import subtitles

_FACE_SAMPLES = 10          # frames sampled across the clip for crop centring
_DETECT_WIDTH = 480         # downscale width for face detection


def _ratio(aspect_ratio: str) -> float:
    try:
        w, h = aspect_ratio.split(":")
        return float(w) / float(h)
    except (ValueError, ZeroDivisionError):
        return 9.0 / 16.0


def _probe_dims(path: str) -> Tuple[int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0:nk=1", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    w, h = out.split(",")[:2]
    return int(w), int(h)


def _video_encoder() -> List[str]:
    """Pick the encoder args. GPU (VideoToolbox) on macOS, else libx264."""
    enc = LOCAL_VIDEO_ENCODER
    if enc == "auto":
        enc = "h264_videotoolbox" if platform.system() == "Darwin" else "libx264"
    if enc == "h264_videotoolbox":
        return ["-c:v", "h264_videotoolbox", "-b:v", "8M", "-allow_sw", "1",
                "-pix_fmt", "yuv420p", "-tag:v", "avc1"]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]


def _crop_origin(
    source_path: str, start: float, end: float,
    src_w: int, src_h: int, crop_w: int, crop_h: int,
) -> Tuple[int, int]:
    """Sample a few frames to centre the crop on the speaker; else frame centre."""
    cx, cy = src_w // 2, src_h // 2
    try:
        import cv2  # type: ignore
    except ImportError:
        return _clamp_origin(cx, cy, src_w, src_h, crop_w, crop_h)

    cap = cv2.VideoCapture(source_path)
    if not cap.isOpened():
        return _clamp_origin(cx, cy, src_w, src_h, crop_w, crop_h)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    scale = src_w / _DETECT_WIDTH if src_w > _DETECT_WIDTH else 1.0
    centers = []
    dur = max(0.0, end - start)
    for i in range(_FACE_SAMPLES):
        t = start + dur * (i + 0.5) / _FACE_SAMPLES
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, frame = cap.read()
        if not ok:
            continue
        small = cv2.resize(frame, (_DETECT_WIDTH, int(src_h / scale))) if scale != 1.0 else frame
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(24, 24))
        if len(faces):
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            centers.append(((x + w / 2) * scale, (y + h / 2) * scale))
    cap.release()
    if centers:
        centers.sort(key=lambda c: c[0])
        cx, cy = centers[len(centers) // 2]          # median by x
    return _clamp_origin(int(cx), int(cy), src_w, src_h, crop_w, crop_h)


def _clamp_origin(cx, cy, src_w, src_h, crop_w, crop_h) -> Tuple[int, int]:
    x0 = max(0, min(src_w - crop_w, cx - crop_w // 2))
    y0 = max(0, min(src_h - crop_h, cy - crop_h // 2))
    return x0 - (x0 % 2), y0 - (y0 % 2)


def crop_clip_local(
    source_path: str, start_time: float, end_time: float,
    aspect_ratio: str, out_path: str,
) -> str:
    """Cut + reframe + encode one highlight in a single ffmpeg pass."""
    src_w, src_h = _probe_dims(source_path)
    target = _ratio(aspect_ratio)
    if target < src_w / src_h:
        crop_h, crop_w = src_h, int(src_h * target)
    else:
        crop_w, crop_h = src_w, int(src_w / target)
    crop_w = max(2, crop_w - (crop_w % 2))
    crop_h = max(2, crop_h - (crop_h % 2))

    x0, y0 = _crop_origin(source_path, start_time, end_time, src_w, src_h, crop_w, crop_h)
    dur = max(0.0, end_time - start_time)

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{start_time:.3f}", "-i", source_path, "-t", f"{dur:.3f}",
        "-vf", f"crop={crop_w}:{crop_h}:{x0}:{y0}",
        *_video_encoder(),
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
        out_path,
    ]
    subprocess.run(cmd, check=True)
    return out_path


def compose_layout1_clip(
    source_path: str, start_time: float, end_time: float, out_path: str,
    segments: Optional[List[Dict]] = None,
) -> str:
    """Render one highlight as LAYOUT_1: screen-share on top, two cams below,
    burned subtitles at the bottom. One ffmpeg pass (plus PNG cue overlays)."""
    dur = max(0.0, end_time - start_time)
    base = (
        f"[0:v]crop={LAYOUT1_SCREEN_CROP},scale=1080:636,setsar=1[top];"
        f"[0:v]crop={LAYOUT1_CAM1_CROP},scale=-2:820,crop=540:820,setsar=1[c1];"
        f"[0:v]crop={LAYOUT1_CAM2_CROP},scale=-2:820,crop=540:820,setsar=1[c2];"
        "[c1][c2]hstack=inputs=2[cams];"
        "[top][cams]vstack=inputs=2[stack];"
        "[stack]pad=1080:1920:0:0:black[base]"
    )
    # -ss/-t BEFORE -i limits the source decode to the clip window; otherwise the
    # trailing -t would attach to the first PNG input and ffmpeg decodes the whole
    # rest of the source.
    inputs = ["-ss", f"{start_time:.3f}", "-t", f"{dur:.3f}", "-i", source_path]
    fg, last = base, "base"
    if segments:
        cues = subtitles.cues_for(segments, start_time, end_time)
        if cues:
            pngs = subtitles.render_cue_pngs(cues, f"{out_path}.subpng")
            sub_fg, sub_inputs, last = subtitles.overlay_chain("base", pngs, dur, first_input_index=1)
            fg += sub_fg
            inputs += sub_inputs

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", *inputs,
        "-filter_complex", fg, "-map", f"[{last}]", "-map", "0:a",
        "-t", f"{dur:.3f}",               # cap output duration to the clip window
        *_video_encoder(), "-c:a", "aac", "-b:a", "160k",
        out_path,
    ]
    subprocess.run(cmd, check=True)
    return out_path


def _render_highlights(source_path, highlights, out_dir, render_one) -> List[Dict]:
    """Shared parallel driver for the per-clip renderers."""
    out_dir = out_dir or LOCAL_OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    results: List[Dict] = [None] * len(highlights)  # type: ignore
    workers = max(1, min(LOCAL_CROP_WORKERS, len(highlights)))

    def _one(i: int, h: Dict) -> Dict:
        out_path = os.path.join(out_dir, f"short_{i + 1:02d}.mp4")
        try:
            render_one(i, h, out_path)
            return {**h, "clip_url": out_path}
        except Exception as e:
            return {**h, "clip_url": None, "error": str(e)}

    print(f"[clip/local] rendering {len(highlights)} clips on {workers} workers "
          f"({_video_encoder()[1]})", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(_one, i, h): i for i, h in enumerate(highlights)}
        for fut in as_completed(futs):
            i = futs[fut]
            results[i] = fut.result()
            tag = "ok" if results[i].get("clip_url") else f"FAILED {results[i].get('error')}"
            print(f"[clip/local] {i + 1}/{len(highlights)} {tag}", flush=True)
    return results


def crop_highlights_local(
    source_path: str, highlights: List[Dict],
    aspect_ratio: str = "9:16", out_dir: Optional[str] = None,
) -> List[Dict]:
    """Generic single-cam vertical crop (speaker-centred) for each highlight."""
    def render(i, h, out_path):
        crop_clip_local(source_path, float(h["start_time"]), float(h["end_time"]),
                        aspect_ratio, out_path)
    return _render_highlights(source_path, highlights, out_dir, render)


def compose_layout1_highlights(
    source_path: str, highlights: List[Dict],
    out_dir: Optional[str] = None, segments: Optional[List[Dict]] = None,
) -> List[Dict]:
    """LAYOUT_1 (screen + two cams + subtitles) for each highlight."""
    def render(i, h, out_path):
        compose_layout1_clip(source_path, float(h["start_time"]), float(h["end_time"]),
                             out_path, segments=segments)
    return _render_highlights(source_path, highlights, out_dir, render)
