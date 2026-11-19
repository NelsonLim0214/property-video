"""Shared TikTok text styling (ASS subtitles) for all property videos.

Fonts: Anton (price), Poppins Black / ExtraBold (Latin text) from ./fonts,
Noto Sans CJK SC Black for Chinese (apt: fonts-noto-cjk-extra).
"""
from pathlib import Path

FONTS_DIR = str(Path(__file__).parent / "fonts")

# ASS colours are &HAABBGGRR
YELLOW = "&H000AD6FF"
RED = "&H004639E6"
TEAL = "&H00A0D606"
WHITE = "&H00FFFFFF"
BLACK = "&H00000000"

ZH = "Noto Sans CJK SC Black"

HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Poppins Black,54,{WHITE},{WHITE},{RED},&H64000000,0,0,0,0,100,100,1,0,3,16,5,8,60,140,170,1
Style: Loc,Poppins ExtraBold,40,{WHITE},{WHITE},{BLACK},&H80000000,0,0,0,0,100,100,0,0,1,4,3,8,60,140,280,1
Style: Hi,Poppins Black,80,{BLACK},{BLACK},{YELLOW},&H78000000,0,0,0,0,100,100,0,0,3,20,8,8,70,140,560,1
Style: Sub,Poppins ExtraBold,62,{WHITE},{WHITE},{BLACK},&H96000000,0,0,0,0,100,100,0,0,1,6,4,2,70,140,420,1
Style: Price,Anton,250,{YELLOW},{YELLOW},{BLACK},{RED},0,0,0,0,100,100,2,0,1,10,10,5,40,100,0,1
Style: Big,Poppins Black,74,{WHITE},{WHITE},{BLACK},&H96000000,0,0,0,0,100,100,0,0,1,7,5,5,60,120,0,1
Style: Bar,Anton,74,{WHITE},{WHITE},{RED},&H64000000,0,0,0,0,100,100,2,0,3,18,6,2,60,140,400,1
Style: Dim,Poppins Black,10,{BLACK},{BLACK},{BLACK},{BLACK},0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# rotating card colours: (box, text)
CARD_COLOURS = [(YELLOW, BLACK), (WHITE, BLACK), (TEAL, BLACK), (RED, WHITE)]


def ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def bounce(rot=0):
    """Pop-in: grow from 30% to 115% then settle at 100%, with a small tilt."""
    return (f"{{\\fad(80,150)\\frz{rot}\\fscx30\\fscy30"
            f"\\t(0,160,\\fscx115\\fscy115)\\t(160,280,\\fscx100\\fscy100)}}")


def zh(text):
    """Wrap Chinese text in the CJK font."""
    return f"{{\\fn{ZH}}}{text}{{\\fnPoppins Black}}"


def check(text):
    """Bullet line with a coloured check mark (glyph from DejaVu)."""
    return f"{{\\fnDejaVu Sans\\b1}}✔{{\\b0\\fnPoppins Black}} {text}"


def card(start, end, text, i):
    box, fg = CARD_COLOURS[i % len(CARD_COLOURS)]
    rot = (-3, 2, -2, 3)[i % 4]
    return (f"Dialogue: 3,{ts(start)},{ts(end)},Hi,,0,0,0,,"
            f"{bounce(rot)}{{\\3c{box}\\1c{fg}}}{text}")


def dim(start, end):
    """Darken the whole frame (for the hook / end card)."""
    return (f"Dialogue: 4,{ts(start)},{ts(end)},Dim,,0,0,0,,"
            f"{{\\fad(200,0)\\pos(0,0)\\1a&H70&\\p1}}m 0 0 l 1080 0 1080 1920 0 1920{{\\p0}}")


def price(start, end, text, y=760):
    return (f"Dialogue: 6,{ts(start)},{ts(end)},Price,,0,0,0,,"
            f"{{\\pos(540,{y})}}{bounce(-4)}{text}")


def big(start, end, text, y, layer=5, extra=""):
    return (f"Dialogue: {layer},{ts(start)},{ts(end)},Big,,0,0,0,,"
            f"{{\\pos(540,{y})\\fad(250,0){extra}}}{text}")
