"""Append the channel outro to the end of each subtitled short.

Uses the concat filter with normalized video/audio so the mono 48k outro joins
cleanly onto the stereo shorts. Run with uv:

    uv run python _append_outro.py
"""
import os
import subprocess

BASE = "/Users/volyx/Movies/2026-05-21 19-12-30"
IN_DIR = os.path.join(BASE, "shorts_screen_subs")
OUT_DIR = os.path.join(BASE, "shorts_final")
OUTRO = "/Users/volyx/.claude/skills/youtube-shorts/outro.mp4"

CLIPS = [f"short_{n:02d}.mp4" for n in range(1, 11)]

FILTER = (
    "[0:v]fps=30,scale=1080:1920,setsar=1,format=yuv420p,settb=AVTB[v0];"
    "[1:v]fps=30,scale=1080:1920,setsar=1,format=yuv420p,settb=AVTB[v1];"
    "[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a0];"
    "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a1];"
    "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for name in CLIPS:
        src = os.path.join(IN_DIR, name)
        out = os.path.join(OUT_DIR, name)
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", src, "-i", OUTRO,
            "-filter_complex", FILTER,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "h264_videotoolbox", "-b:v", "8M", "-allow_sw", "1", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", out,
        ]
        subprocess.run(cmd, check=True)
        dur = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", out],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        print(f"{name}  -> {out}  ({float(dur):.1f}s)")
    print("ALL DONE")


if __name__ == "__main__":
    main()
