#!/usr/bin/env python3
"""Synthesise an original, royalty-free upbeat background track (no samples).

Usage: python3 music.py out.wav SECONDS [--bpm 118] [--key 0] [--seed 1]
Needs numpy + scipy.
"""
import argparse
import wave

import numpy as np
from scipy.signal import butter, lfilter

SR = 44100


def note_hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def env(n, a=0.005, d=0.1, s=0.0, r=0.05, hold=None):
    """Simple ADSR envelope of n samples."""
    t = np.arange(n) / SR
    hold = hold if hold is not None else n / SR
    e = np.where(t < a, t / a, 1.0)
    dec = np.exp(-(t - a) / max(d, 1e-4)) * (1 - s) + s
    e = np.where(t >= a, dec, e)
    rel = np.clip(1 - (t - hold) / r, 0, 1)
    return e * np.where(t > hold, rel, 1.0)


def lp(x, hz, order=2):
    b, a = butter(order, min(hz / (SR / 2), 0.99), "low")
    return lfilter(b, a, x)


def hp(x, hz, order=2):
    b, a = butter(order, hz / (SR / 2), "high")
    return lfilter(b, a, x)


def saw(f, n, detune=0.0, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f * (1 + detune) + phase) % 1) - 1


def add(buf, sig, start):
    s = int(start * SR)
    if s >= len(buf):
        return
    e = min(len(buf), s + len(sig))
    buf[s:e] += sig[: e - s]


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 50 + 110 * np.exp(-t * 35)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) * 1.0


def clap(rng):
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    bursts = sum(np.exp(-np.clip(t - d, 0, None) * 60) * (t >= d) for d in (0, 0.01, 0.02))
    return hp(lp(noise, 6000), 900) * (bursts * 0.4 + np.exp(-t * 18)) * 0.35


def hat(rng, open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000) * np.exp(-t * (18 if open_ else 80)) * 0.18


def build(seconds, bpm=118, key=0, seed=1):
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    bar = 4 * beat
    n = int(seconds * SR) + SR
    L = np.zeros(n)
    R = np.zeros(n)
    drums = np.zeros(n)
    bassb = np.zeros(n)

    # I - V - vi - IV in C (+key)
    prog = [(48, [60, 64, 67, 72]), (43, [59, 62, 67, 71]),
            (45, [60, 64, 69, 72]), (41, [60, 65, 69, 72])]
    melody_bank = [
        [72, None, 76, 79, 76, None, 74, 72],
        [71, None, 74, 79, 74, None, 72, 71],
        [72, None, 76, 81, 79, None, 76, 74],
        [72, None, 77, 81, 77, None, 76, 72],
    ]
    K, C, HC, HO = kick(), clap(rng), hat(rng), hat(rng, True)
    nbars = int(np.ceil(seconds / bar))
    sidechain = np.ones(n)

    for b in range(nbars):
        t0 = b * bar
        root, chord = prog[b % 4]
        intro = b < 2
        # drums
        for q in range(4):
            tq = t0 + q * beat
            if not intro or q in (0, 2):
                add(drums, K, tq)
                s = int(tq * SR)
                m = min(n - s, int(beat * SR))
                if m > 0:
                    tt = np.arange(m) / SR
                    sidechain[s:s + m] = np.minimum(sidechain[s:s + m], 1 - 0.55 * np.exp(-tt * 9))
            if not intro and q in (1, 3):
                add(drums, C, tq)
            add(drums, HO if (q % 2 == 1 and not intro) else HC, tq + beat / 2)
            if not intro:
                add(drums, HC * 0.5, tq + beat * 0.75)
        # bass: off-beat 8ths
        for e8 in range(8):
            if e8 % 2 == 0 and not intro:
                continue
            if intro and e8 % 2 == 0:
                continue
            f = note_hz(root + key - 12 * (0 if root < 45 else 1))
            m = int(beat / 2 * SR)
            sig = saw(f, m) * 0.6 + np.sin(2 * np.pi * f * np.arange(m) / SR) * 0.6
            add(bassb, lp(sig, 380) * env(m, d=0.12, s=0.3, hold=beat * 0.4, r=0.03) * 0.5, t0 + e8 * beat / 2)
        # pad chords
        m = int(bar * SR)
        pad = np.zeros(m)
        for nt in chord:
            f = note_hz(nt + key - 12)
            pad += saw(f, m, 0.004, rng.random()) + saw(f, m, -0.004, rng.random())
        cutoff = 900 if intro else 2200
        pad = lp(pad, cutoff) * env(m, a=0.08, d=1.0, s=0.7, hold=bar - 0.1, r=0.1) * 0.06
        add(L, pad, t0)
        add(R, np.roll(pad, 300), t0)
        # pluck melody (from bar 2)
        if not intro:
            mel = melody_bank[b % 4]
            for i, nt in enumerate(mel):
                if nt is None:
                    continue
                f = note_hz(nt + key)
                mm = int(beat * 0.9 * SR)
                sig = (saw(f, mm) + 0.5 * saw(f * 2, mm, 0.003))
                sig = lp(sig, 3200) * env(mm, a=0.002, d=0.18, s=0.0) * 0.11
                tt = t0 + i * beat / 2
                add(L, sig, tt)
                add(R, sig * 0.8, tt + 0.012)
                # echo
                add(L, sig * 0.3, tt + beat * 0.75)
                add(R, sig * 0.35, tt + beat * 0.75 + 0.01)

    music_l = (L + bassb) * sidechain + drums
    music_r = (R + bassb) * sidechain + drums
    out = np.stack([music_l, music_r], 1)[: int(seconds * SR)]
    # fades
    fi, fo = int(0.3 * SR), int(2.0 * SR)
    out[:fi] *= np.linspace(0, 1, fi)[:, None]
    out[-fo:] *= np.linspace(1, 0, fo)[:, None]
    out /= np.max(np.abs(out)) + 1e-9
    return np.tanh(out * 1.2) * 0.85


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("seconds", type=float)
    ap.add_argument("--bpm", type=float, default=118)
    ap.add_argument("--key", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    x = build(a.seconds, a.bpm, a.key, a.seed)
    pcm = (x * 32767).astype("<i2")
    with wave.open(a.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    main()
