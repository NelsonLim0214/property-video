"""Render animated text overlays for the property ad and composite onto the video.

Usage: python3 make_overlay.py SRC.mp4 OUT.mp4 FONT_DIR
"""
import math
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC, OUT, FONT_DIR = sys.argv[1], sys.argv[2], sys.argv[3]
MUSIC = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "--preview" else None
W, H = 1080, 1920
FPS_NUM, FPS_DEN = 30000, 1001
FPS = FPS_NUM / FPS_DEN
DURATION = 69.87
NFRAMES = int(DURATION * FPS)

HEAVY = f"{FONT_DIR}/archivo-black/package/files/archivo-black-latin-400-normal.woff"
BOLD = f"{FONT_DIR}/montserrat/package/files/montserrat-latin-800-normal.woff"
BLACK = f"{FONT_DIR}/montserrat/package/files/montserrat-latin-900-normal.woff"

NAVY = (16, 32, 64, 255)
RED = (235, 59, 59, 255)
YELLOW = (255, 200, 40, 255)
WHITE = (255, 255, 255, 255)
GREEN = (37, 211, 102, 255)


def font(path, size):
    return ImageFont.truetype(path, size)


def shadowed(img, offset=(0, 10), blur=14, opacity=110):
    """Add a soft drop shadow around an RGBA element."""
    pad = blur * 3
    out = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    a = img.split()[3].point(lambda v: v * opacity // 255)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 255))
    sh.putalpha(a)
    out.paste(sh, (pad + offset[0], pad + offset[1]), sh)
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(img, (pad, pad))
    return out


def text_size(f, s, stroke=0):
    b = f.getbbox(s, stroke_width=stroke)
    return b[2] - b[0], b[3] - b[1], b


def pill(text, f, fg, bg, padx=40, pady=22, border=None, bw=6):
    tw, th, b = text_size(f, text)
    w, h = tw + padx * 2, th + pady * 2
    img = Image.new("RGBA", (w + bw * 2, h + bw * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if border:
        d.rounded_rectangle((0, 0, w + bw * 2 - 1, h + bw * 2 - 1), radius=(h + bw * 2) // 2, fill=border)
    d.rounded_rectangle((bw, bw, bw + w - 1, bw + h - 1), radius=h // 2, fill=bg)
    d.text((bw + padx - b[0], bw + pady - b[1]), text, font=f, fill=fg)
    return shadowed(img)


def pin_icon(size, color):
    img = Image.new("RGBA", (size, int(size * 1.35)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = size // 2
    d.ellipse((0, 0, size - 1, size - 1), fill=color)
    d.polygon([(size * 0.12, r * 1.3), (size * 0.88, r * 1.3), (r, img.height - 1)], fill=color)
    hr = size * 0.2
    d.ellipse((r - hr, r - hr, r + hr, r + hr), fill=WHITE)
    return img


def location_card(lines, sizes, colors, max_w=960):
    """White card with red border + red pin, like the reference style."""
    rendered = []
    for text, sz, col in zip(lines, sizes, colors):
        f = font(HEAVY, sz)
        while text_size(f, text)[0] > max_w - 260 and sz > 30:
            sz -= 2
            f = font(HEAVY, sz)
        rendered.append((text, f, col))
    gap = 6
    heights = [text_size(f, t)[1] for t, f, _ in rendered]
    widths = [text_size(f, t)[0] for t, f, _ in rendered]
    tw, th = max(widths), sum(heights) + gap * (len(rendered) - 1)
    pin = pin_icon(96, RED)
    padx, pady, bw = 44, 38, 7
    w = pin.width + 30 + tw + padx * 2
    h = max(th, pin.height) + pady * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=34, fill=RED)
    d.rounded_rectangle((bw, bw, w - 1 - bw, h - 1 - bw), radius=28, fill=WHITE)
    img.alpha_composite(pin, (padx, (h - pin.height) // 2))
    x0 = padx + pin.width + 30
    y = (h - th) // 2
    for (t, f, col), hh, ww in zip(rendered, heights, widths):
        b = f.getbbox(t)
        d.text((x0 + (tw - ww) // 2 - b[0], y - b[1]), t, font=f, fill=col)
        y += hh + gap
    return shadowed(img)


def price_sticker(scale=1.0):
    """Big tilted price: 'HANYA' tag + RM399K in yellow with navy outline + FREEHOLD ribbon."""
    f_small = font(BLACK, int(46 * scale))
    f_big = font(HEAVY, int(190 * scale))
    f_rib = font(HEAVY, int(58 * scale))
    st = int(14 * scale)
    bw, bh, bb = text_size(f_big, "RM399K", st)
    rib = pill("FREEHOLD", f_rib, WHITE, RED, padx=int(40 * scale), pady=int(16 * scale),
               border=WHITE, bw=int(6 * scale))
    tag = pill("HANYA", f_small, NAVY, WHITE, padx=int(28 * scale), pady=int(12 * scale))
    w = max(bw, rib.width) + 40
    h = tag.height + bh + rib.height - int(40 * scale)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.alpha_composite(tag, (int(30 * scale), 0))
    ty = tag.height - int(30 * scale)
    txt = Image.new("RGBA", (w, bh + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    # hard offset shadow then outlined text = "sticker" look
    d.text(((w - bw) // 2 - bb[0] + int(10 * scale), 20 - bb[1] + int(12 * scale)), "RM399K",
           font=f_big, fill=NAVY, stroke_width=st, stroke_fill=NAVY)
    d.text(((w - bw) // 2 - bb[0], 20 - bb[1]), "RM399K", font=f_big, fill=YELLOW,
           stroke_width=st, stroke_fill=NAVY)
    img.alpha_composite(txt, (0, ty - 20))
    img.alpha_composite(rib, ((w - rib.width) // 2 + int(60 * scale), ty + bh - int(30 * scale)))
    return img.rotate(4, resample=Image.BICUBIC, expand=True)


def spec_bar():
    """Bottom bar: three spec chips."""
    f_v = font(HEAVY, 54)
    f_l = font(BLACK, 28)
    items = [("20'x70'", "KELUASAN TANAH"), ("4 BILIK", "TIDUR"), ("2 BILIK AIR", "TANDAS")]
    cells = []
    for v, l in items:
        vw, vh, vb = text_size(f_v, v)
        lw, lh, lb = text_size(f_l, l)
        cw = max(vw, lw) + 44
        ch = vh + lh + 70
        c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        d = ImageDraw.Draw(c)
        d.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=26, fill=NAVY)
        d.rounded_rectangle((0, ch - 12, cw - 1, ch - 1), radius=6, fill=YELLOW)
        d.text(((cw - vw) // 2 - vb[0], 22 - vb[1]), v, font=f_v, fill=WHITE)
        d.text(((cw - lw) // 2 - lb[0], 22 + vh + 12 - lb[1]), l, font=f_l, fill=YELLOW)
        cells.append(c)
    gap = 16
    total = sum(c.width for c in cells) + gap * (len(cells) - 1)
    scale = min(1.0, 1000 / total)
    if scale < 1:
        cells = [c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS) for c in cells]
        total = sum(c.width for c in cells) + gap * (len(cells) - 1)
    hh = max(c.height for c in cells)
    img = Image.new("RGBA", (total, hh), (0, 0, 0, 0))
    x = 0
    for c in cells:
        img.alpha_composite(c, (x, 0))
        x += c.width + gap
    return shadowed(img)


def room_label(text):
    f = font(HEAVY, 78)
    tw, th, b = text_size(f, text, 10)
    img = Image.new("RGBA", (tw + 40, th + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((20 - b[0], 20 - b[1]), text, font=f, fill=YELLOW, stroke_width=10, stroke_fill=NAVY)
    return shadowed(img, offset=(0, 6), blur=10, opacity=140)


def phone_icon(size, bg, fg):
    img = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    S = size * 4
    d.ellipse((0, 0, S - 1, S - 1), fill=bg)
    # handset: thick arc with rounded ends
    w = int(S * 0.13)
    box = (S * 0.22, S * 0.22, S * 0.78, S * 0.78)
    d.arc(box, 100, 260, fill=fg, width=w)
    import math as _m
    cx, cy, r = S / 2, S / 2, (box[2] - box[0]) / 2 - w / 2
    for ang in (100, 260):
        x, y = cx + r * _m.cos(_m.radians(ang)), cy + r * _m.sin(_m.radians(ang))
        e = w * 0.95
        d.ellipse((x - e, y - e, x + e, y + e), fill=fg)
    img = img.rotate(-45, resample=Image.BICUBIC)
    return img.resize((size, size), Image.LANCZOS)


def phone_card():
    f_l = font(BLACK, 40)
    f_n = font(HEAVY, 92)
    l, n = "HUBUNGI NELSON", "019-8149687"
    lw, lh, lb = text_size(f_l, l)
    nw, nh, nb = text_size(f_n, n)
    ic = phone_icon(130, GREEN, WHITE)
    tw = max(lw, nw)
    padx, pady, bw = 40, 30, 7
    w = padx * 2 + ic.width + 28 + tw
    h = pady * 2 + max(ic.height, lh + 14 + nh)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=34, fill=GREEN)
    d.rounded_rectangle((bw, bw, w - 1 - bw, h - 1 - bw), radius=28, fill=WHITE)
    img.alpha_composite(ic, (padx, (h - ic.height) // 2))
    x0 = padx + ic.width + 28
    y0 = (h - (lh + 14 + nh)) // 2
    d.text((x0 + (tw - lw) // 2 - lb[0], y0 - lb[1]), l, font=f_l, fill=NAVY)
    d.text((x0 + (tw - nw) // 2 - nb[0], y0 + lh + 14 - nb[1]), n, font=f_n, fill=RED)
    return shadowed(img)


def phone_pill():
    f = font(HEAVY, 44)
    t = "NELSON  019-8149687"
    tw, th, b = text_size(f, t)
    ic = phone_icon(th + 24, WHITE, GREEN)
    padx, pady, bw = 22, 16, 6
    w = padx * 2 + ic.width + 16 + tw + 10
    h = pady * 2 + max(ic.height, th)
    img = Image.new("RGBA", (w + bw * 2, h + bw * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w + bw * 2 - 1, h + bw * 2 - 1), radius=(h + bw * 2) // 2, fill=WHITE)
    d.rounded_rectangle((bw, bw, bw + w - 1, bw + h - 1), radius=h // 2, fill=GREEN)
    img.alpha_composite(ic, (bw + padx, bw + (h - ic.height) // 2))
    d.text((bw + padx + ic.width + 16 - b[0], bw + (h - th) // 2 - b[1]), t, font=f, fill=WHITE)
    return shadowed(img)


# ---------- elements ----------
tag_top = pill("PROJEK BARU · RUMAH SIAP", font(HEAVY, 46), NAVY, YELLOW, padx=44, pady=22)
loc_big = location_card(["SIJANGKANG", "TELOK PANGLIMA GARANG"], [104, 64], [NAVY, RED])
sub_pill = pill("Rumah Teres Setingkat · Freehold", font(BOLD, 42), WHITE, NAVY, padx=36, pady=18)
price_big = price_sticker(1.0)
price_small = price_sticker(0.65)
loc_small = location_card(["SIJANGKANG", "TELOK PANGLIMA GARANG"], [62, 40], [NAVY, RED], max_w=760)
specs = spec_bar()
DKGREEN = (0, 120, 70, 255)
mr_big = pill("MALAY RESERVED", font(HEAVY, 56), YELLOW, DKGREEN, padx=44, pady=24, border=YELLOW, bw=7)
mr_small = pill("MALAY RESERVED", font(HEAVY, 36), YELLOW, DKGREEN, padx=26, pady=16, border=YELLOW, bw=5)
cta_top = pill("JANGAN LEPASKAN!", font(HEAVY, 60), WHITE, RED, padx=48, pady=24, border=WHITE)
phone_big = phone_card()
phone_small = phone_pill()
cta_main = pill("PM / WHATSAPP UNTUK VIEWING", font(HEAVY, 44), WHITE, GREEN, padx=40, pady=26,
                border=WHITE)
cta_price = price_sticker(0.85)

rooms = [
    (2.0, 14.5, "DEPAN RUMAH"),
    (14.5, 25.5, "RUANG TAMU LUAS"),
    (25.5, 30.5, "BILIK TIDUR"),
    (30.5, 34.0, "BILIK AIR"),
    (40.5, 45.5, "BILIK AIR 2"),
    (45.5, 49.5, "RUANG MAKAN"),
    (49.5, 56.5, "BILIK TIDUR"),
    (56.5, 63.5, "DAPUR"),
]
room_imgs = {t: room_label(t) for _, _, t in rooms}

INTRO_END = 5.0
CTA_START = 63.5


# ---------- animation helpers ----------
def ease_back(x):
    x = max(0.0, min(1.0, x))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def window(t, start, end, fin=0.35, fout=0.25):
    """Returns (scale, alpha) for an element visible in [start, end) with pop-in / fade-out."""
    if t < start or t >= end:
        return None
    p = (t - start) / fin
    s = ease_back(p) if p < 1 else 1.0
    a = min(1.0, p * 2)
    if end - t < fout:
        a *= (end - t) / fout
        s *= 0.9 + 0.1 * (end - t) / fout
    return max(s, 0.01), max(0.0, min(1.0, a))


def place(frame, img, cx, cy, sa, wobble=0.0):
    if sa is None:
        return
    s, a = sa
    if a <= 0:
        return
    s *= 1 + wobble
    im = img
    if abs(s - 1) > 1e-3:
        im = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BILINEAR)
    if a < 1:
        im = im.copy()
        im.putalpha(im.split()[3].point(lambda v: int(v * a)))
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def render(t):
    fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pulse = 0.03 * math.sin(t * 2 * math.pi * 1.2)
    # intro hero stack (mirrors the reference layout)
    place(fr, tag_top, W / 2, 330, window(t, 0.0, INTRO_END))
    place(fr, loc_big, W / 2, 520, window(t, 0.15, INTRO_END))
    place(fr, sub_pill, W / 2, 720, window(t, 0.35, INTRO_END))
    place(fr, mr_big, W / 2, 1320, window(t, 1.2, INTRO_END))
    place(fr, price_big, W / 2, 1060, window(t, 0.8, INTRO_END, fin=0.45), pulse if t > 1.3 else 0)
    # persistent info during walkthrough
    place(fr, loc_small, W / 2, 230, window(t, INTRO_END, CTA_START))
    place(fr, price_small, 330, 460, window(t, INTRO_END + 0.1, CTA_START), pulse * 0.6)
    place(fr, mr_small, 835, 545, window(t, INTRO_END + 0.2, CTA_START))
    place(fr, specs, W / 2, 1640, window(t, 0.6, CTA_START))
    place(fr, phone_small, W / 2, 1790, window(t, 0.9, CTA_START))
    for st, en, txt in rooms:
        place(fr, room_imgs[txt], W / 2, 1440, window(t, max(st, INTRO_END - 0.5 if st < INTRO_END else st), en))
    # ending CTA
    place(fr, loc_small, W / 2, 330, window(t, CTA_START, 99))
    place(fr, cta_top, W / 2, 560, window(t, CTA_START + 0.1, 99))
    place(fr, cta_price, W / 2, 820, window(t, CTA_START + 0.3, 99), pulse)
    place(fr, mr_big, W / 2, 1040, window(t, CTA_START + 0.4, 99))
    place(fr, specs, W / 2, 1195, window(t, CTA_START + 0.5, 99))
    place(fr, cta_main, W / 2, 1370, window(t, CTA_START + 0.7, 99))
    place(fr, phone_big, W / 2, 1580, window(t, CTA_START + 0.9, 99), pulse * 0.7)
    return fr


if __name__ == "__main__":
    if len(sys.argv) > 4 and sys.argv[4] == "--preview":
        for ts in [float(x) for x in sys.argv[5:]]:
            render(ts).save(f"preview_{ts:05.1f}.png")
        sys.exit(0)
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-stats",
        "-i", SRC,
        *(["-i", MUSIC] if MUSIC else []),
        "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", f"{FPS_NUM}/{FPS_DEN}", "-i", "pipe:0",
        "-filter_complex",
        "[0:v]scale=1080:1920:flags=lanczos,setsar=1,eq=saturation=1.12:contrast=1.04[bg];"
        f"[bg][{2 if MUSIC else 1}:v]overlay=0:0:format=auto:shortest=1,format=yuv420p[v]"
        + (";[0:a]volume=0.6[o];[1:a]volume=0.55[m];[o][m]amix=inputs=2:duration=first:normalize=0,"
           "alimiter=limit=0.95[a]" if MUSIC else ""),
        "-map", "[v]", "-map", "[a]" if MUSIC else "0:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT,
    ]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(NFRAMES):
        p.stdin.write(render(i / FPS).tobytes())
    p.stdin.close()
    sys.exit(p.wait())
