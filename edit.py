#!/usr/bin/env python3
"""Cut the raw property walkthrough into a ~60s TikTok video with
bilingual (BM + 中文) subtitles, highlight cards and a location tag.

Usage: python3 edit.py input.mov output.mp4 [zh|ms]
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import style as S

SPEED = 1.05  # slight speed-up, not noticeable, gets us under 60s

LOCATION = "Bandar Rimbayu, Selangor"  # from the clip's GPS (+2.9599, +101.5518)
TITLE = "双层半独立洋房 · 马来保留地"
TITLE_MS = "Semi-D 2 Tingkat · Malay Reserve"

# (source_start, source_end) in seconds of the raw clip
SEGMENTS = [
    (0.0, 6.95),    # frontage, 40ft wide, big porch
    (7.2, 15.1),    # build-up 29 x 32
    (15.5, 18.5),   # showroom
    (19.6, 21.2),   # memang cantik
    (23.0, 26.5),   # ground-floor room + store
    (32.7, 38.0),   # bathroom, toilet, kitchen
    (39.1, 47.8),   # semi-D, land behind & side
    (49.1, 51.8),   # side 10ft
    (62.4, 65.6),   # SPC flooring
    (70.3, 73.6),   # family hall
    (76.0, 78.5),   # room 2
    (84.9, 93.6),   # room 3 + summary 4R4B
    (94.0, 96.2),   # master room
    (104.4, 107.5), # master bathroom
]

# (source_start, source_end, malay, chinese)
SUBS = [
    (0.0, 3.2, "Rumah ini lebar 40 kaki.", "这间房子土地宽40尺"),
    (3.3, 6.95, "Sudah ada rumah contoh, porch depan memang besar.", "已有样板屋，前面门廊非常大"),
    (7.3, 10.0, "Build-up rumah 29 kaki,", "建筑面积：宽29尺"),
    (10.6, 15.1, "panjangnya 32 kaki.", "长32尺"),
    (15.6, 18.5, "Ini showroom dia.", "这是样板屋"),
    (19.6, 21.2, "Memang cantik!", "真的很漂亮！"),
    (23.2, 26.5, "Bawah ada satu bilik dan stor.", "楼下有一间房 + 储藏室"),
    (32.8, 34.3, "Bilik air.", "浴室"),
    (34.4, 36.0, "Tandas.", "厕所"),
    (36.1, 38.0, "Ini kitchen dia.", "这是厨房"),
    (39.2, 42.0, "Ini rumah semi-D.", "这是半独立式洋房"),
    (42.3, 46.2, "Belakang rumah ada tanah, tepi pun ada tanah.", "屋后有地，旁边也有地"),
    (46.2, 47.8, "Belakang 10 kaki.", "后面10尺"),
    (49.1, 51.8, "Tepi pula ada 10 kaki tanah.", "侧边还有10尺地"),
    (62.5, 65.6, "Lantai SPC disediakan.", "配SPC地板"),
    (70.4, 73.6, "Atas ada satu family hall.", "楼上有家庭厅"),
    (76.1, 78.5, "Bilik kedua, tandas sendiri.", "第二间房，独立厕所"),
    (85.0, 87.0, "Bilik ketiga pun ada tandas sendiri.", "第三间房也有独立厕所"),
    (87.0, 90.3, "Jadi rumah ini 4 bilik, 4 tandas,", "所以这是 4房4厕"),
    (90.3, 93.6, "double storey semi-D.", "双层半独立式洋房"),
    (94.1, 96.2, "Okey, master room.", "主人房"),
    (104.5, 107.5, "Master room ada tandas sendiri.", "主人房有独立浴室"),
]

# Highlight cards: (source_start, source_end, text)
HIGHLIGHTS = [
    (2.8, 6.95, "土地宽 40尺\\N超大门廊"),
    (7.2, 15.1, "建筑面积\\N29尺 × 32尺"),
    (15.5, 21.2, "样板屋"),
    (23.0, 26.5, "楼下有睡房\\N+ 储藏室"),
    (32.7, 38.0, "楼下浴室 + 厨房"),
    (39.1, 51.8, "后院 10尺\\N侧边 10尺\\N额外土地！"),
    (62.4, 65.6, "SPC 地板"),
    (70.3, 73.6, "楼上家庭厅"),
    (76.0, 87.0, "每间房都有\\N独立厕所"),
    (87.0, 93.6, "4房 4厕"),
    (94.0, 107.5, "主人房\\N+ 独立浴室"),
]

# Malay-only version (Malay Reserve land: buyers are Malay / Bumiputera)
HIGHLIGHTS_MS = [
    (2.8, 6.95, "Tanah lebar 40 kaki\\NPorch besar"),
    (7.2, 15.1, "Keluasan binaan\\N29' × 32'"),
    (15.5, 21.2, "Rumah contoh\\Ndah siap"),
    (23.0, 26.5, "Bilik di bawah\\N+ stor"),
    (32.7, 38.0, "Bilik air + dapur"),
    (39.1, 51.8, "Tanah lebih!\\NBelakang 10'\\NTepi 10'"),
    (62.4, 65.6, "Lantai SPC"),
    (70.3, 73.6, "Family hall\\Ndi atas"),
    (76.0, 87.0, "Setiap bilik ada\\Nbilik air sendiri"),
    (87.0, 93.6, "4 Bilik\\N4 Bilik Air"),
    (94.0, 107.5, "Master room\\N+ bilik air"),
]

HOOK_END = 2.8  # source seconds the opening hook stays up


def src_to_out(t):
    """Map a source timestamp to output timestamp (after cuts + speed)."""
    acc = 0.0
    for s, e in SEGMENTS:
        if t < s:
            return acc / SPEED
        if t <= e:
            return (acc + t - s) / SPEED
        acc += e - s
    return acc / SPEED


def build_ass(total, lang="zh"):
    malay = lang == "ms"
    Z = (lambda x: x) if malay else S.zh
    ev = []
    end_start = total - 3.0
    hook_end = src_to_out(HOOK_END)

    # opening hook
    ev.append(S.price(0, hook_end, "SEMI-D", y=700))
    ev.append(S.big(0, hook_end, Z("2 Tingkat · Malay Reserve" if malay else "双层半独立 · 马来保留地"), 860, extra="\\fs60"))
    ev.append(S.big(0, hook_end, Z("4 Bilik · 4 Bilik Air" if malay else "4房 4厕 · 40尺宽地"), 960, extra=f"\\fs60\\1c{S.YELLOW}"))

    title = TITLE_MS if malay else TITLE
    loc = "Lokasi: " if malay else S.zh("位置 ") + "Lokasi: "
    ev.append(f"Dialogue: 2,{S.ts(hook_end)},{S.ts(end_start)},Title,,0,0,0,,{{\\frz-1}}{Z(title)}")
    ev.append(f"Dialogue: 2,{S.ts(hook_end)},{S.ts(end_start)},Loc,,0,0,0,,{loc}{LOCATION}")

    for s, e, ms, zh in SUBS:
        a, b = src_to_out(s), min(src_to_out(e), end_start)
        if b > a:
            text = ms if malay else f"{S.zh(zh)}\\N{{\\fs46\\bord4\\c{S.YELLOW}}}{ms}"
            ev.append(f"Dialogue: 1,{S.ts(a)},{S.ts(b)},Sub,,0,0,0,,{text}")

    for i, (s, e, txt) in enumerate(HIGHLIGHTS_MS if malay else HIGHLIGHTS):
        a, b = src_to_out(s), min(src_to_out(e), end_start)
        if b > a:
            ev.append(S.card(a, b, Z(txt), i))

    # end card
    ev.append(S.dim(end_start, total))
    ev.append(S.price(end_start, total, "SEMI-D", y=640))
    lines = (["Tanah Rizab Melayu", "4 Bilik · 4 Bilik Air", "Tanah lebar 40 kaki"] if malay
             else [S.zh("马来保留地"), S.zh("4房4厕 · 40尺宽地"), S.zh("后院+侧边额外土地")])
    for k, line in enumerate(lines):
        ev.append(S.big(end_start, total, line, 820 + k * 90))
    cta = "DM untuk info & lawatan!" if malay else S.zh("私信了解更多") + " / DM untuk info"
    ev.append(S.big(end_start, total, cta, 1140, layer=6,
                    extra=f"\\fs58\\1c{S.BLACK}\\3c{S.YELLOW}\\bord18\\shad0\\t(300,600,\\fscx106\\fscy106)\\t(600,900,\\fscx100\\fscy100)"))
    ev.append(S.big(end_start, total, f"{loc}{LOCATION}", 1260, extra="\\fs42"))
    return S.HEADER + "\n".join(ev) + "\n"


def main():
    src, out = sys.argv[1], sys.argv[2]
    lang = sys.argv[3] if len(sys.argv) > 3 else "zh"  # "zh" (中文+BM) or "ms" (BM only)
    total = sum(e - s for s, e in SEGMENTS) / SPEED
    tmp = Path(tempfile.mkdtemp())
    ass = tmp / "subs.ass"
    ass.write_text(build_ass(total, lang), encoding="utf-8")

    parts, labels = [], ""
    fade = 0.06
    for i, (s, e) in enumerate(SEGMENTS):
        d = e - s
        parts.append(
            f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,"
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1[v{i}]"
        )
        parts.append(
            f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d={fade},afade=t=out:st={d - fade:.3f}:d={fade}[a{i}]"
        )
        labels += f"[v{i}][a{i}]"
    n = len(SEGMENTS)
    parts.append(f"{labels}concat=n={n}:v=1:a=1[vc][ac]")
    parts.append(
        f"[vc]setpts=PTS/{SPEED},eq=saturation=1.12:contrast=1.04,"
        f"ass={ass}:fontsdir={S.FONTS_DIR}[vo]"
    )
    parts.append(f"[ac]atempo={SPEED},loudnorm=I=-14:TP=-1.5:LRA=11[ao]")
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-stats", "-i", src,
        "-filter_complex", ";".join(parts),
        "-map", "[vo]", "-map", "[ao]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart", out,
    ]
    print(f"Output length ≈ {total:.1f}s")
    subprocess.run(cmd, check=True)
    Path(out).with_suffix(".ass").write_text(ass.read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    main()
