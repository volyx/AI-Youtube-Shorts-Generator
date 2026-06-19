import json, os, subprocess, sys, time

SRC = "/Users/volyx/Movies/2026-06-08 19-14-31.mov"
OUTDIR = "output/shorts_subs"
os.makedirs(OUTDIR, exist_ok=True)

clips = [
    (1, 3560.0, 3624.0),
    (2, 1251.0, 1330.0),
    (3, 2479.0, 2519.0),
    (4, 2566.0, 2606.0),
    (5, 3421.0, 3457.0),
]

STYLE = (
    "FontName=Helvetica,FontSize=46,Bold=1,"
    "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
    "BorderStyle=1,Outline=3,Shadow=1,Alignment=2,"
    "MarginV=240,MarginL=60,MarginR=60"
)

def filtergraph(srt):
    return (
        "[0:v]crop=1290:740:15:140,scale=1080:620,setsar=1[scr];"
        "[0:v]crop=560:385:1360:105,scale=-2:620,crop=540:620,setsar=1[c1];"
        "[0:v]crop=560:360:1360:573,scale=-2:620,crop=540:620,setsar=1[c2];"
        "[c1][c2]hstack=inputs=2[cams];"
        "[scr][cams]vstack=inputs=2[top];"
        "[top]pad=1080:1920:0:0:black[pad];"
        f"[pad]subtitles=f={srt}:force_style='{STYLE}'[v]"
    )

only = [int(x) for x in sys.argv[1:]] or [c[0] for c in clips]

for n, start, dur_end in clips:
    if n not in only:
        continue
    dur = dur_end - start
    srt = f"output/subs/clip_{n:02d}.srt"
    out = f"{OUTDIR}/short_{n:02d}.mp4"
    t0 = time.time()
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{start}", "-t", f"{dur}", "-i", SRC,
        "-filter_complex", filtergraph(srt),
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        out,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"#{n} FAILED:\n{r.stderr[-1500:]}")
    else:
        print(f"#{n} ok -> {out} ({time.time()-t0:.0f}s)")
