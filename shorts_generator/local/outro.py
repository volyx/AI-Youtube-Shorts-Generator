"""Append an outro clip to the end of a short.

Uses the concat filter with normalized video/audio so an outro with different
fps / SAR / channel count joins cleanly. Re-encodes (concat demuxer would need
identical codecs/params, which outros rarely match).
"""
import subprocess
from typing import List

from .clipper import _video_encoder

_FILTER = (
    "[0:v]fps=30,scale=1080:1920,setsar=1,format=yuv420p,settb=AVTB[v0];"
    "[1:v]fps=30,scale=1080:1920,setsar=1,format=yuv420p,settb=AVTB[v1];"
    "[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a0];"
    "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a1];"
    "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
)


def append_outro(clip_path: str, outro_path: str, out_path: str) -> str:
    """Concat `outro_path` onto the end of `clip_path` -> `out_path`."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", clip_path, "-i", outro_path,
        "-filter_complex", _FILTER, "-map", "[v]", "-map", "[a]",
        *_video_encoder(), "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
        out_path,
    ]
    subprocess.run(cmd, check=True)
    return out_path
