"""Shared TikTok text styling (ASS subtitles) for all property videos.

Latin text: Baloo 2 ExtraBold (./fonts). Chinese: Noto Sans CJK SC Black
(apt: fonts-noto-cjk-extra). No rotation; simple fade + gentle scale-in.
"""
import os
from pathlib import Path

FONTS_DIR = str(Path(__file__).parent / "fonts")

LATIN = os.environ.get("VIDEO_FONT", "Baloo 2 ExtraBold")
PRICE_FONT = os.environ.get("VIDEO_PRICE_FONT", LATIN)
ZH = "Noto Sans CJK SC Black"

# ASS colours are &HAABBGGRR
YELLOW = "&H000AD6FF"
RED = "&H004639E6"
TEAL = "&H00A0D606"
WHITE = "&H00FFFFFF"
BLACK = "&H00000000"

HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,{LATIN},80,{WHITE},{WHITE},{RED},&H64000000,0,0,0,0,100,100,0,0,3,18,5,8,60,120,160,1
Style: Loc,{LATIN},58,{WHITE},{WHITE},{BLACK},&H80000000,0,0,0,0,100,100,0,0,1,5,3,8,60,120,290,1
Style: Hi,{LATIN},124,{BLACK},{BLACK},{YELLOW},&H78000000,0,0,0,0,100,100,0,0,3,22,8,8,60,120,560,1
Style: Sub,{LATIN},84,{WHITE},{WHITE},{BLACK},&H96000000,0,0,0,0,100,100,0,0,1,7,4,2,60,120,400,1
Style: Price,{PRICE_FONT},340,{YELLOW},{YELLOW},{BLACK},{RED},0,0,0,0,100,100,0,0,1,12,10,5,40,100,0,1
Style: Big,{LATIN},112,{WHITE},{WHITE},{BLACK},&H96000000,0,0,0,0,100,100,0,0,1,8,5,5,50,100,0,1
Style: Bar,{LATIN},100,{WHITE},{WHITE},{RED},&H64000000,0,0,0,0,100,100,0,0,3,20,6,2,60,120,380,1
Style: Dim,{LATIN},10,{BLACK},{BLACK},{BLACK},{BLACK},0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# rotating card colours: (box, text)
CARD_COLOURS = [(YELLOW, BLACK), (WHITE, BLACK), (TEAL, BLACK), (RED, WHITE)]


def ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def bounce(rot=0):
    """Clean entrance: fade in and scale 90% -> 100%. (rot ignored: no tilting.)"""
    return "{\\fad(150,150)\\fscx90\\fscy90\\t(0,180,\\fscx100\\fscy100)}"


def zh(text):
    """Wrap Chinese text in the CJK font."""
    return f"{{\\fn{ZH}}}{text}{{\\fn{LATIN}}}"


def card(start, end, text, i):
    box, fg = CARD_COLOURS[i % len(CARD_COLOURS)]
    return (f"Dialogue: 3,{ts(start)},{ts(end)},Hi,,0,0,0,,"
            f"{bounce()}{{\\3c{box}\\1c{fg}}}{text}")


def dim(start, end):
    """Darken the whole frame (for the hook / end card)."""
    return (f"Dialogue: 4,{ts(start)},{ts(end)},Dim,,0,0,0,,"
            f"{{\\fad(200,0)\\pos(0,0)\\1a&H70&\\p1}}m 0 0 l 1080 0 1080 1920 0 1920{{\\p0}}")


def price(start, end, text, y=700):
    return (f"Dialogue: 6,{ts(start)},{ts(end)},Price,,0,0,0,,"
            f"{{\\pos(540,{y})}}{bounce()}{text}")


def big(start, end, text, y, layer=5, extra=""):
    return (f"Dialogue: {layer},{ts(start)},{ts(end)},Big,,0,0,0,,"
            f"{{\\pos(540,{y})\\fad(250,0){extra}}}{text}")
