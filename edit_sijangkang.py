#!/usr/bin/env python3
"""Single-storey terrace, Sijangkang — ~52s TikTok cut (Malay text, no voice-over).

The raw clip has no speech, so the story is told with on-screen text.
Original audio is only wind/hiss, so it is muted: add a TikTok sound in-app.

Usage: python3 edit_sijangkang.py proxy_1080x1920.mov output.mp4
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from edit import ts

LOCATION = "Sijangkang, Kuala Langat, Selangor"
TITLE = "Teres 1 Tingkat · Sijangkang"
PRICE_BAR = "RM399K NETT · Freehold · 20' × 70'"

# (source_start, source_end, highlight card text or None)
SEGMENTS = [
    (0.0, 5.5, None),                       # neighbourhood (hook card below)
    (6.5, 14.0, "Saiz tanah 20' × 70'\\NPorch luas"),
    (15.5, 21.0, "Ruang tamu luas"),
    (25.0, 29.5, "Bilik tidur"),
    (31.0, 33.8, "Bilik air"),
    (35.0, 39.5, "Bilik tidur"),
    (42.0, 44.8, "Bilik air kedua"),
    (46.0, 50.0, "Dapur luas"),
    (51.0, 54.5, "Bilik tidur"),
    (56.0, 58.8, "Tingkap besar · terang"),
    (59.0, 61.5, "Sinki + pintu belakang"),
    (63.5, 69.8, "Laman belakang"),
]

HOOK = "{\\fs120\\c&H00D7FF&}RM399K NETT{\\r}\\NFreehold · Malay Reserve\\N" + LOCATION.split(",")[0]
END_CARD = (
    "{\\fs96\\c&H00D7FF&}RM399K NETT{\\r}\\NFreehold · Malay Reserve\\N20' × 70' · Teres 1 Tingkat\\N"
    "Sijangkang, Selangor\\N\\N{\\fs60}DM untuk info & lawatan!"
)


def build_ass(total, starts):
    font = "WenQuanYi Zen Hei"
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hi,{font},76,&H00000000,&H00000000,&H0000D7FF,&H0000D7FF,1,0,0,0,100,100,0,0,3,18,0,8,80,140,600,1
Style: Hook,{font},70,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,1,0,0,0,100,100,0,0,3,26,0,5,80,140,0,1
Style: Title,{font},56,&H00FFFFFF,&H00FFFFFF,&H002A2AD0,&H002A2AD0,1,0,0,0,100,100,0,0,3,14,0,8,60,140,190,1
Style: Loc,{font},44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,4,1,8,60,140,300,1
Style: Bar,{font},58,&H00FFFFFF,&H00FFFFFF,&H002A2AD0,&H002A2AD0,1,0,0,0,100,100,0,0,3,16,0,2,60,140,430,1
Style: End,{font},72,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB0000000,1,0,0,0,100,100,0,0,3,30,0,5,80,140,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    pop = "{\\fad(120,120)\\t(0,150,\\fscx108\\fscy108)\\t(150,300,\\fscx100\\fscy100)}"
    end_start = total - 3.5
    hook_end = starts[1]
    ev = [
        f"Dialogue: 4,{ts(0)},{ts(hook_end)},Hook,,0,0,0,,{pop}{HOOK}",
        f"Dialogue: 2,{ts(hook_end)},{ts(end_start)},Title,,0,0,0,,{TITLE}",
        f"Dialogue: 2,{ts(hook_end)},{ts(end_start)},Loc,,0,0,0,,Lokasi: {LOCATION}",
        f"Dialogue: 2,{ts(hook_end)},{ts(end_start)},Bar,,0,0,0,,{PRICE_BAR}",
    ]
    for (s, e, txt), a in zip(SEGMENTS, starts):
        b = min(a + e - s, end_start)
        if txt and b > a:
            ev.append(f"Dialogue: 3,{ts(a)},{ts(b)},Hi,,0,0,0,,{pop}{txt}")
    ev.append(f"Dialogue: 5,{ts(end_start)},{ts(total)},End,,0,0,0,,{{\\fad(250,0)}}{END_CARD}")
    return head + "\n".join(ev) + "\n"


def main():
    src, out = sys.argv[1], sys.argv[2]
    starts, acc = [], 0.0
    for s, e, _ in SEGMENTS:
        starts.append(acc)
        acc += e - s
    total = acc
    ass = Path(tempfile.mkdtemp()) / "subs.ass"
    ass.write_text(build_ass(total, starts), encoding="utf-8")

    parts, labels = [], ""
    for i, (s, e, _) in enumerate(SEGMENTS):
        parts.append(
            f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,"
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1[v{i}]"
        )
        labels += f"[v{i}]"
    parts.append(f"{labels}concat=n={len(SEGMENTS)}:v=1:a=0[vc]")
    parts.append(f"[vc]eq=saturation=1.15:contrast=1.05:brightness=0.01,ass={ass}[vo]")
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", src,
        "-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=44100:cl=stereo",
        "-filter_complex", ";".join(parts),
        "-map", "[vo]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", "-shortest", out,
    ]
    print(f"Output length ≈ {total:.1f}s")
    subprocess.run(cmd, check=True)
    Path(out).with_suffix(".ass").write_text(ass.read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    main()
