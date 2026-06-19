"""Re-render the ranked highlights as 9:16 with shared screen + presenter cam + burned subs.

Layout (1080x1920):
  - top:    shared-screen panel (left region of the OBS composite), 1080x810
  - middle: presenter webcam (top-right cam), 760 wide, centred
  - bottom: burned Russian subtitles from the cached transcript

Run with uv:
    uv run python _make_clips_screen_subs.py
"""
import json
import os
import subprocess

SRC = "/Users/volyx/Movies/2026-05-21 19-12-30.mov"
OUT_DIR = "/Users/volyx/Movies/2026-05-21 19-12-30/shorts_screen_subs"
TRANSCRIPT = "/Users/volyx/Movies/2026-05-21 19-12-30/transcript.json"

# Source composite regions (1920x1080 OBS layout), measured from sample frames.
SCREEN_CROP = "crop=1338:1004:6:38"      # left main panel (slides / terminal / tables / chat)
CAM_CROP = "crop=464:261:1452:6"         # top-right presenter webcam (Sasha)

CLIPS = [
    (1, 3504.5, 3540.1),
    (2, 5856.5, 5902.5),
    (3, 7472.2, 7514.6),
]

# ASS style baked into the file — avoids escaping force_style on the filter CLI.
ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,58,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,4,2,2,70,70,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ts(sec: float) -> str:
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    cs = (sec - int(sec))
    s = int(sec % 60)
    return f"{h:d}:{m:02d}:{s:02d}.{int(round(cs * 100)):02d}"


def write_clip_ass(segments, start, end, path):
    idx = 0
    events = []
    for seg in segments:
        if seg["end"] <= start or seg["start"] >= end:
            continue
        a = max(seg["start"], start) - start
        b = min(seg["end"], end) - start
        if b <= a:
            continue
        idx += 1
        text = seg["text"].strip().replace("\n", " ")
        events.append(f"Dialogue: 0,{_ts(a)},{_ts(b)},Default,,0,0,0,,{text}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER + "\n".join(events) + "\n")
    return idx


def render(num, start, end, segments):
    dur = end - start
    ass = f"/tmp/_clipsub_{num}.ass"
    n = write_clip_ass(segments, start, end, ass)
    out = os.path.join(OUT_DIR, f"short_{num:02d}.mp4")

    filter_complex = (
        f"[0:v]{SCREEN_CROP},scale=1080:810,setsar=1[scr];"
        f"[0:v]{CAM_CROP},scale=760:-2,setsar=1[cam];"
        f"color=c=#0b1a2b:s=1080x1920[bg];"
        f"[bg][scr]overlay=0:70[t1];"
        f"[t1][cam]overlay=(W-w)/2:920[t2];"
        f"[t2]subtitles={ass}[v]"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{start}", "-i", SRC, "-t", f"{dur}",
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "0:a",
        "-r", "30",
        "-c:v", "h264_videotoolbox", "-b:v", "8M", "-allow_sw", "1", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        out,
    ]
    subprocess.run(cmd, check=True)
    print(f"short_{num:02d}.mp4  ({dur:.1f}s, {n} subs) -> {out}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    segments = json.load(open(TRANSCRIPT))["segments"]
    for num, start, end in CLIPS:
        render(num, start, end, segments)
    print("ALL DONE")


if __name__ == "__main__":
    main()
