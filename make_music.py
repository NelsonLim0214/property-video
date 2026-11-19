"""Synthesize an original, royalty-free upbeat background track (no samples used).

Usage: python3 make_music.py OUT.wav [seconds]
"""
import sys
import wave

import numpy as np

SR = 44100
OUT = sys.argv[1]
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 70.0
BPM = 118
BEAT = 60 / BPM
N = int(DUR * SR)
rng = np.random.default_rng(7)

L = np.zeros(N)
R = np.zeros(N)


def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * (1 - pan) if pan > 0 else sig
    R[i:i + len(sig)] += sig * (1 + pan) if pan < 0 else sig


def env(n, a=0.005, d=0.2):
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e


def kick():
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    f = 50 + 110 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)


def hat(d=0.04):
    n = int(0.12 * SR)
    x = rng.standard_normal(n)
    x = np.diff(x, prepend=0)  # crude high-pass
    return x * env(n, 0.001, d) * 0.35


def clap():
    n = int(0.3 * SR)
    x = rng.standard_normal(n)
    x = x - np.convolve(x, np.ones(8) / 8, "same")
    e = env(n, 0.001, 0.09)
    for k in (0.01, 0.02):
        e[int(k * SR):] += 0.6 * env(n - int(k * SR), 0.001, 0.02)
    return x * e * 0.5


def note_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def saw(f, n):
    t = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(1, 12):
        s += np.sin(2 * np.pi * f * k * t) / k
    return s


def pluck(m, dur=0.35):
    n = int(dur * SR)
    s = saw(note_hz(m), n) + saw(note_hz(m) * 1.004, n)
    return s * env(n, 0.003, 0.12) * 0.12


def bass(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note_hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    e = np.minimum(1, t / 0.005) * np.minimum(1, (dur - t) / 0.02)
    return s * e * 0.35


def pad(chord, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * note_hz(m) * t) + 0.5 * np.sin(2 * np.pi * note_hz(m) * 1.003 * t)
            for m in chord)
    e = np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.4)
    return s * e * 0.04


# I - V - vi - IV in D major
prog = [
    (50, [62, 66, 69]),  # D
    (45, [61, 64, 69]),  # A
    (47, [62, 66, 71]),  # Bm
    (43, [62, 67, 71]),  # G
]
arp = [0, 1, 2, 1, 2, 0, 1, 2]

bar = 4 * BEAT
nbars = int(DUR / bar) + 1
for b in range(nbars):
    t0 = b * bar
    root, chord = prog[b % 4]
    intro = b < 2
    add(pad(chord + [chord[0] + 12], bar), t0, 1.0)
    for beat in range(4):
        tb = t0 + beat * BEAT
        if not intro:
            add(kick(), tb, 0.9)
            if beat in (1, 3):
                add(clap(), tb, 0.6)
        add(hat(), tb + BEAT / 2, 0.8 if not intro else 0.4, pan=0.2)
        if not intro:
            add(hat(0.015), tb + BEAT / 4, 0.35, pan=-0.2)
            add(hat(0.015), tb + 3 * BEAT / 4, 0.35, pan=-0.2)
            # offbeat bass, house style
            add(bass(root, BEAT / 2 * 0.9), tb + BEAT / 2)
    for k in range(8):
        m = chord[arp[k]] + 12
        add(pluck(m), t0 + k * BEAT / 2, 1.0, pan=0.3 if k % 2 else -0.3)

mix = np.stack([L, R], axis=1)
# fade in / out
fi, fo = int(0.5 * SR), int(3.0 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
# soft clip + normalise
mix = np.tanh(mix * 1.2)
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.89
pcm = (mix * 32767).astype(np.int16)
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
