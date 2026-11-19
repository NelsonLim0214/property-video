#!/usr/bin/env python3
"""Cut the raw property walkthrough into a ~60s TikTok video with
bilingual (BM + 中文) subtitles, highlight cards and a location tag.

Usage: python3 edit.py input.mov output.mp4 [zh|ms]
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import re

import graphics as G
from compose import Layer, dim_layer, render

SPEED = 1.05  # slight speed-up, not noticeable, gets us under 60s

LOCATION = "Bandar Rimbayu, Selangor"  # guessed from GPS (+2.9599, +101.5518) — CONFIRM
LOC1, LOC2 = "BANDAR RIMBAYU", "SELANGOR"
TITLE = "双层半独立 · 马来保留地"
TITLE_MS = "Semi-D · Malay Reserve"

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

# Highlight cards: (source_start, source_end, text). The first scene is the hook.
HIGHLIGHTS = [
    (7.2, 15.1, "建筑面积\n29尺 × 32尺"),
    (15.5, 21.2, "样板屋"),
    (23.0, 26.5, "楼下有睡房\n+ 储藏室"),
    (32.7, 38.0, "楼下浴室 + 厨房"),
    (39.1, 51.8, "后院 10尺\n侧边 10尺\n额外土地！"),
    (62.4, 65.6, "SPC 地板"),
    (70.3, 73.6, "楼上家庭厅"),
    (76.0, 87.0, "每间房都有\n独立厕所"),
    (87.0, 93.6, "4房 4厕"),
    (94.0, 107.5, "主人房\n+ 独立浴室"),
]

# Malay-only version (Malay Reserve land: buyers are Malay / Bumiputera)
HIGHLIGHTS_MS = [
    (7.2, 15.1, "Keluasan binaan\n29' × 32'"),
    (15.5, 21.2, "Rumah contoh\ndah siap"),
    (23.0, 26.5, "Bilik di bawah\n+ stor"),
    (32.7, 38.0, "Bilik air + dapur"),
    (39.1, 51.8, "Tanah lebih!\nBelakang 10'\nTepi 10'"),
    (62.4, 65.6, "Lantai SPC"),
    (70.3, 73.6, "Family hall\ndi atas"),
    (76.0, 87.0, "Setiap bilik ada\nbilik air sendiri"),
    (87.0, 93.6, "4 Bilik\n4 Bilik Air"),
    (94.0, 107.5, "Master room\n+ bilik air"),
]

HOOK_END = 6.95  # source seconds: hook covers the first scene

CARD_STYLES = [
    dict(bg=G.NAVY, fg=G.WHITE),
    dict(bg=G.YELLOW, fg=G.NAVY),
    dict(bg=G.WHITE, fg=G.NAVY, border=(G.RED, 8)),
]

YEL = "&H003CC9FF"
KEY_MS = re.compile(r"(\d+|kaki|semi-D|SPC|porch|tanah|bilik|tandas|master room|family hall|"
                    r"showroom|cantik|kitchen|stor|double storey)", re.I)
KEY_ZH = re.compile(r"(\d+尺?|\d+[房厕]|样板屋|门廊|储藏室|厨房|浴室|厕所|地板|家庭厅|主人房|半独立式洋房|有地)")


def hl(text, rx):
    return rx.sub(lambda m: f"{{\\c{YEL}}}{m.group(0)}{{\\c&H00FFFFFF&}}", text)


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter Black,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,-1,0,1,7,3,2,70,110,400,1
Style: SubZH,Noto Sans CJK SC Black,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,7,3,2,70,110,400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


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


def build_ass(total, malay):
    end_start = total - 3.0
    ev = []
    for s, e, ms, zh in SUBS:
        a, b = src_to_out(s), min(src_to_out(e), end_start)
        if b <= a:
            continue
        if malay:
            ev.append(f"Dialogue: 1,{G_ts(a)},{G_ts(b)},Sub,,0,0,0,,{hl(ms, KEY_MS)}")
        else:
            ev.append(f"Dialogue: 1,{G_ts(a)},{G_ts(b)},SubZH,,0,0,0,,"
                      f"{hl(zh, KEY_ZH)}\\N{{\\fnInter Black\\fs52\\bord5\\c&H00E0E0E0&}}{ms}")
    return ASS_HEAD + "\n".join(ev) + "\n"


def G_ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def build_layers(total, malay):
    hook_end = src_to_out(HOOK_END)
    end_start = total - 3.0
    L = [dim_layer(0, hook_end, 130)]
    if malay:
        hook = [G.pill("RUMAH CONTOH SIAP · MALAY RESERVE", 46, G.YELLOW, G.NAVY),
                G.location_card(LOC1, LOC2),
                G.pill("Semi-D 2 Tingkat", 54, G.NAVY, G.WHITE),
                (G.headline("TANAH LEBAR", 84), 36),
                G.headline("40 KAKI", 250, G.GREEN),
                G.divider(620),
                G.headline("4 BILIK · 4 BILIK AIR", 80)]
    else:
        hook = [G.pill("样板屋已建好 · 马来保留地", 50, G.YELLOW, G.NAVY),
                G.location_card(LOC1, LOC2),
                G.pill("双层半独立洋房", 56, G.NAVY, G.WHITE),
                (G.headline("土地宽", 76), 24),
                G.headline("40尺", 190, G.GREEN),
                G.divider(560),
                G.headline("4房 · 4厕", 72)]
    L += G.stack(hook, top=210, t0=0, t1=hook_end, gap=20, Layer=Layer)

    top_pill = G.loc_pill(LOCATION, 48)
    L.append(Layer(top_pill, 160 - top_pill.info["pad"], hook_end, end_start))
    info = G.pill("4 Bilik · 4 Bilik Air · Malay Reserve" if malay else "4房4厕 · 马来保留地",
                  48, G.GREEN, G.WHITE)
    L.append(Layer(info, 1215 - info.info["pad"], hook_end, end_start))

    for k, (s, e, txt) in enumerate(HIGHLIGHTS_MS if malay else HIGHLIGHTS):
        a, b = src_to_out(s), min(src_to_out(e), end_start)
        if b > a:
            img = G.pill(txt, 96, pad=(54, 26), **CARD_STYLES[k % len(CARD_STYLES)])
            L.append(Layer(img, 330 - img.info["pad"], a, b))

    L.append(dim_layer(end_start, total, 165))
    if malay:
        end = [G.headline("SEMI-D 2 TINGKAT", 76),
               G.headline("TANAH 40'", 240, G.GREEN),
               G.divider(620),
               G.headline("4 BILIK · 4 BILIK AIR", 80),
               G.headline("TANAH LEBIH BELAKANG & TEPI", 56, G.YELLOW),
               (G.pill("DM UNTUK LAWATAN!", 64, G.YELLOW, G.NAVY, pad=(50, 22)), 30),
               G.loc_pill(LOCATION, 46)]
    else:
        end = [G.headline("双层半独立洋房", 76),
               G.headline("40尺宽地", 220, G.GREEN),
               G.divider(620),
               G.headline("4房 · 4厕 · 马来保留地", 72),
               G.headline("后院 + 侧边额外土地", 62, G.YELLOW),
               (G.pill("私信了解更多", 64, G.YELLOW, G.NAVY, pad=(50, 22)), 30),
               G.loc_pill(LOCATION, 46)]
    L += G.stack(end, top=420, t0=end_start, t1=total, gap=24, Layer=Layer)
    return L


def main():
    src, out = sys.argv[1], sys.argv[2]
    malay = (sys.argv[3] if len(sys.argv) > 3 else "zh") == "ms"
    total = sum(e - s for s, e in SEGMENTS) / SPEED
    total = render(src, out, SEGMENTS, build_layers(total, malay), build_ass(total, malay), speed=SPEED)
    print(f"Output length ≈ {total:.1f}s")


if __name__ == "__main__":
    main()
