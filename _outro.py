import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FPS, DUR = 30, 3.0
NF = int(FPS * DUR)
FRAMES = "output/outro_frames"
os.makedirs(FRAMES, exist_ok=True)

BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
f_title = ImageFont.truetype(BOLD, 92)
f_sub = ImageFont.truetype(REG, 46)
f_btn = ImageFont.truetype(BOLD, 44)

CREAM = (243, 241, 230, 255)
GRAY = (176, 186, 198, 255)
TG = (38, 162, 224, 255)        # telegram blue
YT = (220, 30, 30, 255)         # youtube red

TITLE = "Стафф Инженер"
SUB = "подписывайтесь на еженедельный стаф"
TG_LINK = "t.me/staff_engineers"
YT_LINK = "youtube.com/@StaffPodcast"

LOGO_CY, LOGO_D = 560, 420
TITLE_CY = 990
SUB_CY = 1115
TG_CY = 1290
YT_CY = 1420

def smoothstep(e0, e1, t):
    if e1 <= e0:
        return 1.0 if t >= e1 else 0.0
    x = max(0.0, min(1.0, (t - e0) / (e1 - e0)))
    return x * x * (3 - 2 * x)

def ease_out_back(p):
    s = 1.70158
    p -= 1
    return 1 + (s + 1) * p**3 + s * p**2

def make_bg():
    bg = Image.new("RGB", (W, H))
    px = bg.load()
    top, bot = (12, 26, 43), (5, 11, 20)
    for y in range(H):
        k = y / H
        row = tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3))
        for x in range(W):
            px[x, y] = row
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    for r, a in [(360, 38), (260, 30), (170, 26)]:
        gd.ellipse([540 - r, LOGO_CY - r, 540 + r, LOGO_CY + r], fill=a)
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    bg = Image.composite(Image.new("RGB", (W, H), (60, 130, 180)), bg, glow)
    return bg.convert("RGBA")

def make_logo():
    src = Image.open("output/channels4_profile.jpg").convert("RGBA").resize((LOGO_D, LOGO_D))
    mask = Image.new("L", (LOGO_D, LOGO_D), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, LOGO_D, LOGO_D], radius=70, fill=255)
    logo = Image.new("RGBA", (LOGO_D, LOGO_D), (0, 0, 0, 0))
    logo.paste(src, (0, 0), mask)
    ImageDraw.Draw(logo).rounded_rectangle([1, 1, LOGO_D - 2, LOGO_D - 2], radius=70,
                                           outline=(243, 241, 230, 150), width=3)
    return logo

def tg_icon(d, bx, by, s):
    """Telegram-style paper plane in an s x s box at (bx,by)."""
    A = (bx + 0.04 * s, by + 0.52 * s)
    B = (bx + 0.96 * s, by + 0.07 * s)
    C = (bx + 0.43 * s, by + 0.60 * s)
    Dn = (bx + 0.56 * s, by + 0.96 * s)
    d.polygon([A, B, C], fill=(255, 255, 255, 255))
    d.polygon([C, B, Dn], fill=(255, 255, 255, 210))

def yt_icon(d, bx, by, s):
    """White rounded badge with a red play triangle (YouTube)."""
    bw, bh = s * 1.4, s
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=s * 0.28, fill=(255, 255, 255, 255))
    tx = bx + bw * 0.40
    d.polygon([(tx, by + bh * 0.28), (tx, by + bh * 0.72),
               (bx + bw * 0.66, by + bh * 0.5)], fill=YT)

def text_layer(fn):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fn(ImageDraw.Draw(img))
    return img

def draw_title(d):
    w = d.textlength(TITLE, font=f_title)
    d.text(((W - w) / 2, TITLE_CY - 50), TITLE, font=f_title, fill=CREAM,
           stroke_width=2, stroke_fill=(0, 0, 0, 120))

def wrap(text, font, maxw, d):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = wd
    if cur: lines.append(cur)
    return lines

def draw_sub(d):
    lines = wrap(SUB, f_sub, 940, d)
    lh, y = 58, SUB_CY - (58 * len(lines)) // 2
    for ln in lines:
        w = d.textlength(ln, font=f_sub)
        d.text(((W - w) / 2, y), ln, font=f_sub, fill=GRAY)
        y += lh

def button_layer(cy, text, bg, icon, icon_kind):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tw = d.textlength(text, font=f_btn)
    isz = 46
    gap = 22
    pad = 46
    bw = pad + isz + gap + tw + pad
    bh = 96
    x0 = (W - bw) / 2
    y0 = cy - bh / 2
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=48, fill=bg)
    iy = cy - isz / 2
    if icon_kind == "tg":
        tg_icon(d, x0 + pad, iy, isz)
    else:
        yt_icon(d, x0 + pad, iy + isz * 0.12, isz)
    d.text((x0 + pad + isz + gap, cy - 30), text, font=f_btn, fill=(255, 255, 255, 255))
    return img

def faded(layer, a):
    if a >= 1.0:
        return layer
    r, g, b, al = layer.split()
    return Image.merge("RGBA", (r, g, b, al.point(lambda p: int(p * a))))

BG = make_bg()
LOGO = make_logo()
L_TITLE = text_layer(draw_title)
L_SUB = text_layer(draw_sub)
L_TG = button_layer(TG_CY, TG_LINK, TG, None, "tg")
L_YT = button_layer(YT_CY, YT_LINK, YT, None, "yt")

for i in range(NF):
    t = i / FPS
    fo = 1.0 - smoothstep(2.3, 3.0, t)         # global fade away
    frame = BG.copy()

    p = max(0.0, min(1.0, t / 0.6))
    s = 0.6 + 0.4 * ease_out_back(p)
    a_logo = smoothstep(0.0, 0.45, t) * fo
    d = max(2, int(LOGO_D * s))
    frame.alpha_composite(faded(LOGO.resize((d, d)), a_logo), (540 - d // 2, LOGO_CY - d // 2))

    a_t = smoothstep(0.35, 0.85, t) * fo
    if a_t > 0:
        dy = int((1 - smoothstep(0.35, 0.85, t)) * 26)
        frame.alpha_composite(faded(L_TITLE, a_t), (0, dy))

    a_s = smoothstep(0.6, 1.05, t) * fo
    if a_s > 0:
        frame.alpha_composite(faded(L_SUB, a_s), (0, 0))

    a_tg = smoothstep(0.85, 1.25, t) * fo
    if a_tg > 0:
        frame.alpha_composite(faded(L_TG, a_tg), (0, 0))

    a_yt = smoothstep(1.05, 1.45, t) * fo
    if a_yt > 0:
        frame.alpha_composite(faded(L_YT, a_yt), (0, 0))

    frame.convert("RGB").save(f"{FRAMES}/f_{i:04d}.png")

print(f"rendered {NF} frames -> {FRAMES}")
