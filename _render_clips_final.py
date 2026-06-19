"""Render the ranked highlights as 9:16: shared screen on top, both cams below, burned subs.

No-libass ffmpeg here, so subtitles are rendered to transparent PNGs with PIL and
overlaid with enable=between(t,a,b) — the proven approach for this source video.

Run with uv:
    uv run python _render_clips_final.py            # all clips
    uv run python _render_clips_final.py 1           # just clip 1
"""
import json
import os
import subprocess
import sys
import time

from PIL import Image, ImageDraw, ImageFont

SRC = "/Users/volyx/Movies/2026-05-21 19-12-30.mov"
OUT_DIR = "/Users/volyx/Movies/2026-05-21 19-12-30/shorts_screen_subs"
TRANSCRIPT = "/Users/volyx/Movies/2026-05-21 19-12-30/transcript.json"
PNG_DIR = "/Users/volyx/Movies/2026-05-21 19-12-30/_subpng"
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

W, H = 1080, 1920
Y_CENTER = 1690        # caption block centre (empty band under the cams)
FSIZE = 50
MAXW = 960
font = ImageFont.truetype(FONT, FSIZE)

# Agent-ranked top 10 highlights: (num, start, end, score, title, hook).
CLIPS = [
    (1, 3504.5, 3540.1, 92, "Why devs trash AI coding: fear of losing their jobs",
     "Это боязнь потерять работу и желание сохранить статус-кво программистов."),
    (2, 5856.5, 5902.5, 90, "A DB built with Claude only 3x slower than DuckDB",
     "Раньше это было 12 секунд, теперь GpointDB отрабатывает за 183 миллисекунды."),
    (3, 7472.2, 7514.6, 89, "Spec-driven development is BS",
     "Спек-дривен-девелопмент — это какая-то чушь, там нет никакого driven-development."),
    (4, 6058.3, 6091.0, 88, "The agent researched me and built my landing page",
     "Мой OpenClaw агент провёл ресерч меня как автора и вставил ссылки в лендос."),
    (5, 6431.5, 6491.1, 87, "The human is the bottleneck between software and Claude",
     "Ты начинаешь быть узким местом — этот человек между софтом и Клодом не работает."),
    (6, 6863.0, 6911.1, 86, "My autonomous agent has its own VM and GitHub account",
     "OpenClaw — автономный агент: отдельная виртуалка, отдельный GitHub аккаунт, только PR-ы."),
    (7, 3105.5, 3153.0, 85, "Claude estimates in human-days because it trained on humans",
     "Один шаг займёт 3-5 дней — он оценивает как человек, потому что обучался на людях."),
    (8, 1325.8, 1363.1, 84, "The prompt is the only thing that matters",
     "The prompt — это единственный промпт, который реально имеет значение."),
    (9, 2331.9, 2360.6, 83, "With Claude, writing your own tooling is a no-brainer",
     "Когда есть такая мощь, как Клод, писать свой тулинг — сам Бог велел."),
    (10, 7296.0, 7337.2, 82, "Claude pushed me to Caddy — wait, was that an ad?",
     "Клод сам предложил Caddy вместо nginx. А может, это реклама была?"),
]

# Screen fit-width on top, both cams filled below, subtitle band at the bottom.
# Crops tuned for this 1920x1080 OBS composite.
BASE = (
    "[0:v]crop=1360:800:0:140,scale=1080:636,setsar=1[top];"
    "[0:v]crop=560:420:1360:30,scale=-2:820,crop=540:820,setsar=1[c1];"
    "[0:v]crop=560:370:1360:455,scale=-2:820,crop=540:820,setsar=1[c2];"
    "[c1][c2]hstack=inputs=2[cams];"
    "[top][cams]vstack=inputs=2[stack];"
    "[stack]pad=1080:1920:0:0:black[base]"
)


def wrap(text, d):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= MAXW or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
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
    maxw = max(d.textlength(ln, font=font) for ln in lines)
    bx0, bx1 = (W - maxw) / 2 - 30, (W + maxw) / 2 + 30
    d.rounded_rectangle([bx0, y - 18, bx1, y + block + 10], radius=24, fill=(0, 0, 0, 150))
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((W - w) / 2, y), ln, font=font, fill=(255, 255, 255, 255),
               stroke_width=5, stroke_fill=(0, 0, 0, 255))
        y += lh
    img.save(path)


def cues_for(segments, start, end):
    out = []
    for s in segments:
        if s["end"] <= start or s["start"] >= end:
            continue
        a = max(s["start"], start) - start
        b = min(s["end"], end) - start
        if b > a:
            out.append((a, b, s["text"].strip().replace("\n", " ")))
    return out


def render(num, start, end, segments):
    dur = end - start
    cues = cues_for(segments, start, end)
    pdir = os.path.join(PNG_DIR, f"clip_{num:02d}")
    os.makedirs(pdir, exist_ok=True)
    pngs = []
    for i, (a, b, txt) in enumerate(cues):
        p = os.path.join(pdir, f"cue_{i:03d}.png")
        render_png(txt, p)
        pngs.append((p, a, b))

    inputs = ["-ss", f"{start}", "-t", f"{dur}", "-i", SRC]
    for p, _, _ in pngs:
        inputs += ["-loop", "1", "-i", p]

    fg, cur = BASE, "base"
    for i, (_, a, b) in enumerate(pngs, start=1):
        nxt = f"o{i}"
        fg += f";[{cur}][{i}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[{nxt}]"
        cur = nxt

    out = os.path.join(OUT_DIR, f"short_{num:02d}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", fg,
           "-map", f"[{cur}]", "-map", "0:a", "-t", f"{dur}",
           "-c:v", "h264_videotoolbox", "-b:v", "8M", "-allow_sw", "1", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", out]
    t0 = time.time()
    subprocess.run(cmd, check=True)
    print(f"short_{num:02d}.mp4  ({dur:.1f}s, {len(pngs)} cues, {time.time()-t0:.0f}s) -> {out}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    segments = json.load(open(TRANSCRIPT))["segments"]
    only = [int(x) for x in sys.argv[1:]] or [c[0] for c in CLIPS]
    shorts = []
    for num, start, end, score, title, hook in CLIPS:
        if num not in only:
            continue
        render(num, start, end, segments)
        shorts.append({
            "rank": num, "score": score, "title": title, "hook_sentence": hook,
            "start_time": start, "end_time": end, "duration": round(end - start, 1),
            "clip_url": os.path.join(OUT_DIR, f"short_{num:02d}.mp4"),
        })
    with open(os.path.join(OUT_DIR, "ranking.json"), "w") as f:
        json.dump(shorts, f, ensure_ascii=False, indent=2)
    print("ALL DONE")


if __name__ == "__main__":
    main()
