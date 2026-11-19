"""Render a cut of a 1080x1920 clip with PNG graphic overlays + ASS subtitles.

Overlay spec: Layer(img, x, y, t0, t1) — img is a PIL RGBA image placed with
its top-left at (x, y) (x=None centres it), visible t0..t1 (output seconds),
with a short fade in/out.
"""
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

FONTS_DIR = str(Path(__file__).parent / "fonts")
FADE = 0.22


@dataclass
class Layer:
    img: object
    y: int
    t0: float
    t1: float
    x: int = None


def dim_layer(t0, t1, alpha=150):
    from PIL import Image
    return Layer(Image.new("RGBA", (1080, 1920), (0, 0, 0, alpha)), 0, t0, t1, 0)


def render(src, out, segments, layers, ass_text=None, speed=1.0, keep_audio=True):
    tmp = Path(tempfile.mkdtemp())
    total = sum(e - s for s, e in segments) / speed
    inputs = ["-i", src]
    parts, labels = [], ""
    for i, (s, e) in enumerate(segments):
        d = e - s
        parts.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,fps=30,setsar=1[v{i}]")
        if keep_audio:
            parts.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,"
                         f"afade=t=in:d=0.06,afade=t=out:st={d - 0.06:.3f}:d=0.06[a{i}]")
            labels += f"[v{i}][a{i}]"
        else:
            labels += f"[v{i}]"
    n = len(segments)
    if keep_audio:
        parts.append(f"{labels}concat=n={n}:v=1:a=1[vc][ac]")
        parts.append(f"[ac]atempo={speed}[aout]")
    else:
        parts.append(f"{labels}concat=n={n}:v=1:a=0[vc]")
    parts.append(f"[vc]setpts=PTS/{speed},eq=saturation=1.12:contrast=1.04[b0]")

    cur = "b0"
    for k, L in enumerate(layers):
        p = tmp / f"l{k}.png"
        L.img.save(p)
        idx = k + 1
        inputs += ["-loop", "1", "-framerate", "30", "-t", f"{total:.3f}", "-i", str(p)]
        x = L.x if L.x is not None else (1080 - L.img.size[0]) // 2
        fo = max(L.t1 - FADE, L.t0)
        parts.append(f"[{idx}:v]format=rgba,fade=t=in:st={L.t0:.3f}:d={FADE}:alpha=1,"
                     f"fade=t=out:st={fo:.3f}:d={FADE}:alpha=1[f{k}]")
        parts.append(f"[{cur}][f{k}]overlay=x={x}:y={L.y}:enable='between(t,{L.t0:.3f},{L.t1:.3f})'[o{k}]")
        cur = f"o{k}"
    if ass_text:
        ass = tmp / "subs.ass"
        ass.write_text(ass_text, encoding="utf-8")
        parts.append(f"[{cur}]ass={ass}:fontsdir={FONTS_DIR}[vout]")
    else:
        parts.append(f"[{cur}]null[vout]")

    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(parts),
           "-map", "[vout]"]
    if keep_audio:
        cmd += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "-ar", "44100"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-t", f"{total:.3f}", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    if ass_text:
        Path(out).with_suffix(".ass").write_text(ass_text, encoding="utf-8")
    return total
