"""PIL-drawn TikTok graphics: rounded pills, location card with pin,
big price headline, divider. Each function returns an RGBA image that is
overlaid on the video (see compose.py).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = Path(__file__).parent / "fonts"
INTER_BLACK = str(FONTS / "Inter-900.ttf")
INTER_XB = str(FONTS / "Inter-800.ttf")
CJK_BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"

NAVY = (20, 33, 61)
RED = (230, 57, 70)
YELLOW = (255, 201, 60)
GREEN = (52, 199, 89)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

TRACK = -0.02  # letter spacing, fraction of font size (tight, like the refs)


def _has_cjk(s):
    return any("　" <= c <= "鿿" or "＀" <= c <= "￯" for c in s)


def font(size, text="", weight="black"):
    if _has_cjk(text):
        return ImageFont.truetype(CJK_BLACK, size, index=2)  # index 2 = SC
    return ImageFont.truetype(INTER_BLACK if weight == "black" else INTER_XB, size)


def text_size(text, size, weight="black"):
    f = font(size, text, weight)
    track = 0 if _has_cjk(text) else TRACK * size
    w = sum(f.getlength(c) for c in text) + track * max(len(text) - 1, 0)
    asc, desc = f.getmetrics()
    return w, asc, desc


def draw_text(d, xy, text, size, fill, weight="black"):
    """Draw text with tight tracking; xy = top-left of the em box."""
    f = font(size, text, weight)
    track = 0 if _has_cjk(text) else TRACK * size
    x, y = xy
    if _has_cjk(text):
        d.text((x, y), text, font=f, fill=fill)
        return
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + track


def _shadow(img, radius=14, offset=(0, 8), alpha=150):
    """Return img with a soft drop shadow underneath (canvas grows)."""
    pad = radius * 3
    W, H = img.size[0] + 2 * pad, img.size[1] + 2 * pad
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = img.split()[3].point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 255))
    sh.putalpha(a)
    base.paste(sh, (pad + offset[0], pad + offset[1]), sh)
    base = base.filter(ImageFilter.GaussianBlur(radius))
    base.alpha_composite(img, (pad, pad))
    base.info["pad"] = pad
    return base


def pill(text, size=56, bg=YELLOW, fg=NAVY, pad=(40, 22), radius=None, border=None,
         lines_gap=0.15, shadow=True):
    """Rounded box with one or more centred lines (split on \\n)."""
    lines = text.split("\n")
    metrics = [text_size(l, size) for l in lines]
    lh = int(size * 1.18)
    w = int(max(m[0] for m in metrics)) + 2 * pad[0]
    h = lh * len(lines) + int(size * lines_gap) * (len(lines) - 1) + 2 * pad[1]
    r = radius if radius is not None else min(h // 2, int(size * 0.9))
    bw = border[1] if border else 0
    img = Image.new("RGBA", (w + 2 * bw, h + 2 * bw), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if border:
        d.rounded_rectangle([0, 0, w + 2 * bw - 1, h + 2 * bw - 1], r + bw, fill=border[0])
    d.rounded_rectangle([bw, bw, bw + w - 1, bw + h - 1], r, fill=bg)
    y = bw + pad[1]
    for l, (lw, asc, desc) in zip(lines, metrics):
        # vertically centre glyphs in the line box
        top = y + (lh - (asc + desc)) // 2 + int(size * 0.02)
        draw_text(d, (bw + (w - lw) / 2, top), l, size, fg)
        y += lh + int(size * lines_gap)
    return _shadow(img) if shadow else img


def pin_icon(h, color=RED):
    w = int(h * 0.72)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = w // 2
    d.ellipse([0, 0, w - 1, w - 1], fill=color)
    d.polygon([(w * 0.12, r * 1.35), (w * 0.88, r * 1.35), (w / 2, h - 1)], fill=color)
    ir = int(r * 0.42)
    d.ellipse([r - ir, r - ir, r + ir, r + ir], fill=WHITE)
    return img


def location_card(line1, line2, size1=104, size2=118, c1=NAVY, c2=RED, max_w=900):
    """White rounded card, red border, pin icon, two big uppercase lines."""
    w1, a1, d1 = text_size(line1, size1)
    w2, a2, d2 = text_size(line2, size2)
    # shrink to fit
    pin_h = int((size1 + size2) * 0.62)
    pin_w = int(pin_h * 0.72)
    gap = 34
    inner = max(w1, w2) + pin_w + gap
    s = min(1.0, (max_w - 2 * 50) / inner)
    if s < 1:
        return location_card(line1, line2, int(size1 * s), int(size2 * s), c1, c2, max_w)
    pad_x, pad_y, bw = 50, 30, 9
    lh1, lh2 = int(size1 * 1.08), int(size2 * 1.08)
    W = int(inner) + 2 * pad_x + 2 * bw
    H = lh1 + lh2 + 2 * pad_y + 2 * bw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], 42, fill=RED)
    d.rounded_rectangle([bw, bw, W - 1 - bw, H - 1 - bw], 34, fill=WHITE)
    pin = pin_icon(pin_h)
    img.alpha_composite(pin, (bw + pad_x, (H - pin_h) // 2))
    tx0 = bw + pad_x + pin_w + gap
    tw = W - tx0 - pad_x - bw
    y = bw + pad_y
    draw_text(d, (tx0 + (tw - w1) / 2, y + (lh1 - a1 - d1) // 2), line1, size1, c1)
    y += lh1
    draw_text(d, (tx0 + (tw - w2) / 2, y + (lh2 - a2 - d2) // 2), line2, size2, c2)
    return _shadow(img, radius=16, alpha=170)


def headline(text, size, color=WHITE, max_w=960):
    """Free-standing big text with a soft dark shadow (for dimmed frames)."""
    w, asc, desc = text_size(text, size)
    if w > max_w:
        return headline(text, int(size * max_w / w), color, max_w)
    img = Image.new("RGBA", (int(w) + 8, asc + desc + 8), (0, 0, 0, 0))
    draw_text(ImageDraw.Draw(img), (4, 4), text, size, color)
    return _shadow(img, radius=12, offset=(0, 6), alpha=200)


def divider(width=640, h=14, color=GREEN):
    img = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, width - 1, h - 1], h // 2, fill=color)
    return _shadow(img, radius=8, offset=(0, 4), alpha=120)


def loc_pill(text, size=46):
    """Small white pill with a red pin, for the persistent top label."""
    tw, asc, desc = text_size(text, size)
    pin_h = int(size * 1.05)
    pin_w = int(pin_h * 0.72)
    pad_x, pad_y, gap = 30, 16, 14
    lh = int(size * 1.18)
    W = int(tw) + pin_w + gap + 2 * pad_x
    H = lh + 2 * pad_y
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], H // 2, fill=WHITE)
    img.alpha_composite(pin_icon(pin_h), (pad_x, (H - pin_h) // 2))
    draw_text(d, (pad_x + pin_w + gap, pad_y + (lh - asc - desc) // 2), text, size, NAVY)
    return _shadow(img, radius=10, alpha=140)


def stack(elems, top, t0, t1, gap=26, stagger=0.12, Layer=None):
    """Place images vertically (visible boxes `gap` apart) from `top`.
    elems: list of images or (image, extra_gap_before). Returns Layers."""
    out, y = [], top
    for i, e in enumerate(elems):
        img, extra = (e if isinstance(e, tuple) else (e, 0))
        pad = img.info.get("pad", 0)
        y += extra
        out.append(Layer(img, y - pad, t0 + i * stagger, t1))
        y += img.size[1] - 2 * pad + gap
    return out
