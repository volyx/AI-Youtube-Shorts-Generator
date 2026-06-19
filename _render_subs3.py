import os, re, subprocess, sys, time
from PIL import Image, ImageDraw, ImageFont

SRC = "/Users/volyx/Movies/2026-05-21 19-12-30.mov"
OUTDIR = "output/shorts2_split"
PNGDIR = "output/subs2/png"
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
os.makedirs(OUTDIR, exist_ok=True)

W, H = 1080, 1920
Y_CENTER = 1690                      # caption block centre (black band under faces)
FSIZE = 50
MAXW = 960
font = ImageFont.truetype(FONT, FSIZE)

clips = [
    (1, 598.0, 636.0),
    (2, 778.0, 808.0),
    (3, 2325.0, 2348.0),
    (4, 1326.0, 1352.0),
    (5, 825.0, 862.0),
]

def parse_srt(p):
    cues = []
    for b in re.split(r"\n\s*\n", open(p, encoding="utf-8").read().strip()):
        ls = [x for x in b.splitlines() if x.strip()]
        if len(ls) < 2 or "-->" not in ls[1]:
            continue
        a, bb = [t.strip() for t in ls[1].split("-->")]
        cues.append((srt_t(a), srt_t(bb), " ".join(ls[2:])))
    return cues

def srt_t(s):
    h, m, rest = s.split(":"); sec, ms = rest.split(",")
    return int(h)*3600 + int(m)*60 + int(sec) + int(ms)/1000

def wrap(text, d):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= MAXW or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def render_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lines = wrap(text, d)
    lh = FSIZE + 16
    block = lh * len(lines)
    y = Y_CENTER - block // 2
    maxw = max(d.textlength(ln, font=font) for ln in lines)
    bx0, bx1 = (W - maxw) / 2 - 30, (W + maxw) / 2 + 30
    d.rounded_rectangle([bx0, y - 18, bx1, y + block + 10], radius=24, fill=(0, 0, 0, 150))
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((W - w) / 2, y), ln, font=font, fill=(255, 255, 255, 255),
               stroke_width=5, stroke_fill=(0, 0, 0, 255))
        y += lh
    img.save(path)

# slide fit-width on top, both cams filled below, subtitle band at the bottom
BASE = (
    "[0:v]crop=1360:800:0:140,scale=1080:636,setsar=1[top];"
    "[0:v]crop=560:420:1360:30,scale=-2:820,crop=540:820,setsar=1[c1];"
    "[0:v]crop=560:370:1360:455,scale=-2:820,crop=540:820,setsar=1[c2];"
    "[c1][c2]hstack=inputs=2[cams];"
    "[top][cams]vstack=inputs=2[stack];"
    "[stack]pad=1080:1920:0:0:black[base]"
)

only = [int(x) for x in sys.argv[1:]] or [c[0] for c in clips]
for n, start, end in clips:
    if n not in only:
        continue
    dur = end - start
    cues = parse_srt(f"output/subs2/clip_{n:02d}.srt")
    pdir = f"{PNGDIR}/clip_{n:02d}"; os.makedirs(pdir, exist_ok=True)
    pngs = []
    for i, (a, b, txt) in enumerate(cues):
        p = f"{pdir}/cue_{i:03d}.png"; render_png(txt, p); pngs.append((p, a, b))
    inputs = ["-ss", f"{start}", "-t", f"{dur}", "-i", SRC]
    for p, _, _ in pngs:
        inputs += ["-loop", "1", "-i", p]
    fg, cur = BASE, "base"
    for i, (_, a, b) in enumerate(pngs, start=1):
        nxt = f"o{i}"
        fg += f";[{cur}][{i}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[{nxt}]"; cur = nxt
    out = f"{OUTDIR}/short_{n:02d}.mp4"
    t0 = time.time()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", fg,
           "-map", f"[{cur}]", "-map", "0:a", "-t", f"{dur}",
           "-c:v", "h264_videotoolbox", "-b:v", "8M", "-allow_sw", "1", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"#{n} {'ok' if r.returncode==0 else 'FAIL: '+r.stderr[-600:]} -> {out} ({len(pngs)} cues, {time.time()-t0:.0f}s)")
