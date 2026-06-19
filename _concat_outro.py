"""Crossfade each short into the outro clip.

Replaces the old _concat_outro.sh / _concat2.sh. Run with uv:

    uv run python _concat_outro.py                       # libx264, output/shorts_split -> output/shorts_final
    uv run python _concat_outro.py --encoder videotoolbox \
        --in-dir output/shorts2_split --out-dir output/shorts2_final
"""
import argparse
import os
import subprocess

XFADE = 0.35  # crossfade duration, seconds
OUTRO = "output/outro.mp4"

ENCODERS = {
    "libx264": ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p"],
    "videotoolbox": ["-c:v", "h264_videotoolbox", "-b:v", "8M", "-allow_sw", "1", "-pix_fmt", "yuv420p"],
}


def probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def concat_one(in_path: str, out_path: str, video_args: list[str]) -> float:
    dur = probe_duration(in_path)
    off = dur - XFADE
    filter_complex = (
        "[0:v]fps=30,format=yuv420p,setsar=1,settb=AVTB[v0];"
        "[1:v]fps=30,format=yuv420p,setsar=1,settb=AVTB[v1];"
        f"[v0][v1]xfade=transition=fadeblack:duration={XFADE}:offset={off:.3f}[v];"
        "[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a0];"
        "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a1];"
        f"[a0][a1]acrossfade=d={XFADE}:c1=tri:c2=tri[a]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", in_path, "-i", OUTRO,
         "-filter_complex", filter_complex, "-map", "[v]", "-map", "[a]",
         *video_args, "-c:a", "aac", "-b:a", "160k", out_path],
        check=True,
    )
    return off


def main() -> int:
    parser = argparse.ArgumentParser(description="Crossfade shorts into the outro clip")
    parser.add_argument("--in-dir", default="output/shorts_split", help="dir of input short_NN.mp4")
    parser.add_argument("--out-dir", default="output/shorts_final", help="dir for output short_NN.mp4")
    parser.add_argument("--encoder", choices=list(ENCODERS), default="libx264")
    parser.add_argument("--clips", default="01,02,03,04,05", help="comma-separated NN ids")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    video_args = ENCODERS[args.encoder]
    for n in args.clips.split(","):
        n = n.strip()
        in_path = os.path.join(args.in_dir, f"short_{n}.mp4")
        out_path = os.path.join(args.out_dir, f"short_{n}.mp4")
        off = concat_one(in_path, out_path, video_args)
        print(f"done short_{n} (offset={off:.3f})")
    print("ALL DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
