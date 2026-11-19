#!/usr/bin/env python3
"""Single-storey terrace, Sijangkang — ~52s TikTok cut (Malay text, no voice-over).

Raw clip has no speech; story told with graphics. Audio muted (music added
afterwards with add_music.sh).

Usage: python3 edit_sijangkang.py proxy_1080x1920.mov output.mp4
"""
import sys

import graphics as G
from compose import Layer, dim_layer, render

# (source_start, source_end, highlight card text or None)
SEGMENTS = [
    (0.0, 5.5, None),                       # neighbourhood — hook
    (6.5, 14.0, "Tanah 20' × 70'\nPorch luas"),
    (15.5, 21.0, "Ruang tamu luas"),
    (25.0, 29.5, "Bilik tidur"),
    (31.0, 33.8, "Bilik air"),
    (35.0, 39.5, "Bilik tidur"),
    (42.0, 44.8, "Bilik air kedua"),
    (46.0, 50.0, "Dapur luas"),
    (51.0, 54.5, "Bilik tidur"),
    (56.0, 58.8, "Tingkap besar\nRumah terang"),
    (59.0, 61.5, "Sinki +\npintu belakang"),
    (63.5, 69.8, "Laman belakang"),
]

CARD_STYLES = [
    dict(bg=G.NAVY, fg=G.WHITE),
    dict(bg=G.YELLOW, fg=G.NAVY),
    dict(bg=G.WHITE, fg=G.NAVY, border=(G.RED, 8)),
]


def build_layers(starts, total):
    hook_end = starts[1]
    end_start = total - 3.6
    L = []
    # ---- hook ----
    L.append(dim_layer(0, hook_end, 140))
    L += G.stack([
        G.pill("RUMAH SIAP · MALAY RESERVE", 50, G.YELLOW, G.NAVY),
        G.location_card("SIJANGKANG", "KUALA LANGAT"),
        G.pill("Rumah Teres Setingkat · 20' × 70'", 50, G.NAVY, G.WHITE),
        (G.headline("HARGA NETT", 88), 40),
        G.headline("RM399K", 270, G.GREEN),
        G.divider(620),
        G.headline("4 BILIK · 2 BILIK AIR", 84),
    ], top=230, t0=0, t1=hook_end, gap=22, Layer=Layer)

    # ---- persistent labels ----
    top_pill = G.loc_pill("Sijangkang, Kuala Langat", 48)
    L.append(Layer(top_pill, 160 - top_pill.info["pad"], hook_end, end_start))
    info = G.pill("4 Bilik · 2 Bilik Air · Freehold", 50, G.YELLOW, G.NAVY)
    price = G.pill("RM399K NETT", 84, G.GREEN, G.WHITE, pad=(48, 20))
    L += G.stack([info, price], top=1290, t0=hook_end, t1=end_start, gap=18, stagger=0, Layer=Layer)

    # ---- per-scene highlight cards ----
    k = 0
    for (s, e, txt), a in zip(SEGMENTS, starts):
        if not txt:
            continue
        b = min(a + e - s, end_start)
        img = G.pill(txt, 96, pad=(54, 26), **CARD_STYLES[k % len(CARD_STYLES)])
        L.append(Layer(img, 330 - img.info["pad"], a, b))
        k += 1

    # ---- end card ----
    L.append(dim_layer(end_start, total, 165))
    L += G.stack([
        G.headline("RUMAH TERES SETINGKAT", 70),
        G.headline("RM399K", 270, G.GREEN),
        G.divider(620),
        G.headline("NETT · FREEHOLD", 84),
        G.headline("4 BILIK · 2 BILIK AIR", 76, G.YELLOW),
        (G.pill("DM UNTUK LAWATAN!", 64, G.YELLOW, G.NAVY, pad=(50, 22)), 30),
        G.loc_pill("Sijangkang, Kuala Langat", 46),
    ], top=420, t0=end_start, t1=total, gap=24, Layer=Layer)
    return L


def main():
    src, out = sys.argv[1], sys.argv[2]
    starts, acc = [], 0.0
    for s, e, _ in SEGMENTS:
        starts.append(acc)
        acc += e - s
    layers = build_layers(starts, acc)
    total = render(src, out, [(s, e) for s, e, _ in SEGMENTS], layers, keep_audio=False)
    print(f"Output length ≈ {total:.1f}s")


if __name__ == "__main__":
    main()
