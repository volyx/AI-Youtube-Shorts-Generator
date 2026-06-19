"""Burn transcript subtitles without libass.

Many ffmpeg builds (notably Homebrew's default) ship without the `subtitles`
or `drawtext` filters. So instead of an `.srt`/`.ass` burn we render each cue to
a transparent PNG with Pillow and overlay it via `enable='between(t,a,b)'`.

`cues_for()` slices transcript segments to a clip window (relative timing),
`render_cue_pngs()` rasterises them, and `overlay_chain()` builds the ffmpeg
filter fragment + the extra `-loop 1 -i png` inputs.
"""
import os
from typing import Dict, List, Tuple

from ..config import SUB_FONT, SUB_FONT_SIZE, SUB_Y_CENTER

Cue = Tuple[float, float, str]            # (start, end, text), clip-relative seconds
Png = Tuple[str, float, float]            # (png_path, start, end)


def cues_for(segments: List[Dict], start: float, end: float) -> List[Cue]:
    """Segments overlapping [start, end), re-timed relative to the clip start."""
    out: List[Cue] = []
    for s in segments:
        if s["end"] <= start or s["start"] >= end:
            continue
        a = max(s["start"], start) - start
        b = min(s["end"], end) - start
        if b > a:
            out.append((a, b, s["text"].strip().replace("\n", " ")))
    return out


def _wrap(text: str, draw, font, maxw: int) -> List[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_cue_pngs(
    cues: List[Cue], out_dir: str,
    canvas: Tuple[int, int] = (1080, 1920), maxw: int = 960,
) -> List[Png]:
    """Rasterise each cue to a transparent PNG; return [(path, start, end)]."""
    from PIL import Image, ImageDraw, ImageFont

    os.makedirs(out_dir, exist_ok=True)
    W, H = canvas
    font = ImageFont.truetype(SUB_FONT, SUB_FONT_SIZE)
    lh = SUB_FONT_SIZE + 16
    pngs: List[Png] = []
    for i, (a, b, text) in enumerate(cues):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        lines = _wrap(text, d, font, maxw)
        block = lh * len(lines)
        y = SUB_Y_CENTER - block // 2
        tw = max(d.textlength(ln, font=font) for ln in lines)
        d.rounded_rectangle(
            [(W - tw) / 2 - 30, y - 18, (W + tw) / 2 + 30, y + block + 10],
            radius=24, fill=(0, 0, 0, 150),
        )
        for ln in lines:
            w = d.textlength(ln, font=font)
            d.text(((W - w) / 2, y), ln, font=font, fill=(255, 255, 255, 255),
                   stroke_width=5, stroke_fill=(0, 0, 0, 255))
            y += lh
        path = os.path.join(out_dir, f"cue_{i:03d}.png")
        img.save(path)
        pngs.append((path, a, b))
    return pngs


def overlay_chain(base_label: str, pngs: List[Png], clip_dur: float, first_input_index: int = 1):
    """Return (filter_fragment, [-loop 1 -t dur -i png ...] inputs, final_label).

    `first_input_index` is the ffmpeg input index of the first PNG (i.e. how many
    real inputs precede it). Each looped image input is bounded with `-t clip_dur`
    so ffmpeg doesn't hold an infinite stream open (which can spike memory). PNGs
    are overlaid in order, each gated by its cue window.
    """
    inputs: List[str] = []
    fg, cur = "", base_label
    for n, (path, a, b) in enumerate(pngs):
        inputs += ["-loop", "1", "-t", f"{clip_dur:.3f}", "-i", path]
        idx = first_input_index + n
        nxt = f"s{n}"
        fg += f";[{cur}][{idx}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[{nxt}]"
        cur = nxt
    return fg, inputs, cur
