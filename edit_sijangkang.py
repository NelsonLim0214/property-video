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

import style as S

LOCATION = "Sijangkang, Kuala Langat"
TITLE = "Teres 1 Tingkat · 20' × 70'"
PRICE_BAR = "RM399K NETT · Freehold"

# (source_start, source_end, highlight card text or None)
SEGMENTS = [
    (0.0, 5.5, None),                       # neighbourhood (hook card below)
    (6.5, 14.0, "Tanah 20' × 70'\\NPorch luas"),
    (15.5, 21.0, "Ruang tamu\\Nluas"),
    (25.0, 29.5, "Bilik tidur"),
    (31.0, 33.8, "Bilik air"),
    (35.0, 39.5, "Bilik tidur"),
    (42.0, 44.8, "Bilik air kedua"),
    (46.0, 50.0, "Dapur luas"),
    (51.0, 54.5, "Bilik tidur"),
    (56.0, 58.8, "Tingkap besar\\NRumah terang"),
    (59.0, 61.5, "Sinki +\\Npintu belakang"),
    (63.5, 69.8, "Laman belakang"),
]

def build_ass(total, starts):
    end_start = total - 3.5
    hook_end = starts[1]
    ev = [
        # opening hook over the street shot
        S.dim(0, hook_end),
        S.price(0, hook_end, "RM399K", y=600),
        f"Dialogue: 6,{S.ts(0.25)},{S.ts(hook_end)},Bar,,0,0,0,,{{\\an5\\pos(540,860)}}{S.bounce()}NETT · FREEHOLD",
        S.big(0.5, hook_end, "Malay Reserve", 1020, extra=f"\\1c{S.YELLOW}"),
        S.big(0.7, hook_end, "Teres 1 Tingkat", 1150),
        S.big(0.7, hook_end, "Sijangkang", 1280),
        # persistent labels
        f"Dialogue: 2,{S.ts(hook_end)},{S.ts(end_start)},Title,,0,0,0,,{TITLE}",
        f"Dialogue: 2,{S.ts(hook_end)},{S.ts(end_start)},Loc,,0,0,0,,Lokasi: {LOCATION}",
        f"Dialogue: 2,{S.ts(hook_end)},{S.ts(end_start)},Bar,,0,0,0,,{PRICE_BAR}",
    ]
    k = 0
    for (s, e, txt), a in zip(SEGMENTS, starts):
        b = min(a + e - s, end_start)
        if txt and b > a:
            ev.append(S.card(a, b, txt, k))
            k += 1
    # end card
    ev += [
        S.dim(end_start, total),
        S.price(end_start, total, "RM399K", y=480),
        S.big(end_start, total, "NETT · FREEHOLD", 700, extra=f"\\1c{S.YELLOW}"),
        S.big(end_start, total, "Malay Reserve", 830, extra="\\fs100"),
        S.big(end_start, total, "Teres 1 Tingkat", 950, extra="\\fs100"),
        S.big(end_start, total, "20' × 70'", 1070, extra="\\fs100"),
        S.big(end_start, total, "Sijangkang, Selangor", 1190, extra="\\fs100"),
        S.big(end_start, total, "DM untuk info & lawatan!", 1350, layer=6,
              extra=f"\\fs80\\1c{S.BLACK}\\3c{S.YELLOW}\\bord20\\shad0"),
    ]
    return S.HEADER + "\n".join(ev) + "\n"


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
    parts.append(f"[vc]eq=saturation=1.15:contrast=1.05:brightness=0.01,ass={ass}:fontsdir={S.FONTS_DIR}[vo]")
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
