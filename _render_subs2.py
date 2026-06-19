import os, re, subprocess, sys, time
from PIL import Image, ImageDraw, ImageFont

SRC = "/Users/volyx/Movies/2026-06-08 19-14-31.mov"
OUTDIR = "output/shorts_split"
PNGDIR = "output/subs/png"
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
os.makedirs(OUTDIR, exist_ok=True)

W, H = 1080, 1920
Y_CENTER = 1770                       # caption block center (lower third, over the faces)
FSIZE = 50
MAXW = 960                            # text wrap width (60px margins)
font = ImageFont.truetype(FONT, FSIZE)

clips = [
    (1, 3560.0, 3624.0),
    (2, 1251.0, 1330.0),
    (3, 2479.0, 2519.0),
    (4, 2566.0, 2606.0),
    (5, 3421.0, 3457.0),
]

def parse_srt(path):
    cues, blocks = [], re.split(r"\n\s*\n", open(path, encoding="utf-8").read().strip())
    for b in blocks:
        ls = [x for x in b.splitlines() if x.strip()]
        if len(ls) < 2 or "-->" not in ls[1]:
            continue
        a, bb = [t.strip() for t in ls[1].split("-->")]
        cues.append((srt_t(a), srt_t(bb), " ".join(ls[2:])))
    return cues

def srt_t(s):
    h, m, rest = s.split(":")
    sec, ms = rest.split(",")
    return int(h)*3600 + int(m)*60 + int(sec) + int(ms)/1000

def wrap(text, draw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= MAXW or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines

def render_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lines = wrap(text, d)
    lh = FSIZE + 16
    block = lh * len(lines)
    y = Y_CENTER - block // 2
    # translucent backing box so captions stay legible over the faces
    maxw = max(d.textlength(ln, font=font) for ln in lines)
    bx0, bx1 = (W - maxw) / 2 - 30, (W + maxw) / 2 + 30
    d.rounded_rectangle([bx0, y - 18, bx1, y + block + 10], radius=24, fill=(0, 0, 0, 150))
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((W - w) / 2, y), ln, font=font, fill=(255, 255, 255, 255),
               stroke_width=5, stroke_fill=(0, 0, 0, 255))
        y += lh
    img.save(path)

# Top 66% (1080x1280): shared screen, zoomed to fill width then centered.
# Bottom 33% (1080x640): both webcams side by side, filled to height.
BASE = (
    "[0:v]crop=1290:740:15:140,scale=-2:920,crop=1080:920,setsar=1,pad=1080:1280:0:180:black[top];"
    "[0:v]crop=560:385:1360:105,scale=-2:640,crop=540:640,setsar=1[c1];"
    "[0:v]crop=560:360:1360:573,scale=-2:640,crop=540:640,setsar=1[c2];"
    "[c1][c2]hstack=inputs=2[cams];"
    "[top][cams]vstack=inputs=2[base]"
)

only = [int(x) for x in sys.argv[1:]] or [c[0] for c in clips]

for n, start, end in clips:
    if n not in only:
        continue
    dur = end - start
    cues = parse_srt(f"output/subs/clip_{n:02d}.srt")
    pdir = f"{PNGDIR}/clip_{n:02d}"; os.makedirs(pdir, exist_ok=True)
    pngs = []
    for i, (a, b, txt) in enumerate(cues):
        p = f"{pdir}/cue_{i:03d}.png"
        render_png(txt, p); pngs.append((p, a, b))

    inputs = ["-ss", f"{start}", "-t", f"{dur}", "-i", SRC]
    for p, _, _ in pngs:
        inputs += ["-loop", "1", "-i", p]

    fg = BASE
    cur = "base"
    for i, (_, a, b) in enumerate(pngs, start=1):
        nxt = f"o{i}"
        fg += f";[{cur}][{i}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[{nxt}]"
        cur = nxt

    out = f"{OUTDIR}/short_{n:02d}.mp4"
    t0 = time.time()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs,
           "-filter_complex", fg, "-map", f"[{cur}]", "-map", "0:a",
           "-t", f"{dur}", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"#{n} FAILED ({len(pngs)} cues):\n{r.stderr[-1500:]}")
    else:
        print(f"#{n} ok -> {out} ({len(pngs)} cues, {time.time()-t0:.0f}s)")
