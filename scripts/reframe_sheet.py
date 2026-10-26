"""A sheet for setting a vertical short's reframe (config/reframe.json): frames across the short's span, each with
its 9:16 window drawn as the current keys place it, labelled with the song time.

Usage: .venv/bin/python -I scripts/reframe_sheet.py <short id> <frames dir> <out.jpg> [--every S]
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CUES = json.loads((ROOT / "overlays/cues.json").read_text())
KEYS = json.loads((ROOT / "config/reframe.json").read_text())
FPS = json.loads((ROOT / "timing/timing_map.json").read_text())["fps"]


def cx_at(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if t < b:
            return va + (vb - va) * (t - a) / (b - a)
    return keys[-1][1]


def main():
    sid, frames, out = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    every = float(sys.argv[sys.argv.index("--every") + 1]) if "--every" in sys.argv else 2.0
    sh = next(s for s in CUES["shorts"] if s["id"] == sid)
    black = json.loads((ROOT / "timing/timing_map.json").read_text())["outro"]["black"]
    ts, t = [], sh["from"]
    while t < min(sh["to"], black):
        ts.append(t)
        t += every
    tw, th = 480, 270
    cols = 5
    sheet = Image.new("RGB", (cols * tw, -(-len(ts) // cols) * (th + 18)), (20, 20, 24))
    d = ImageDraw.Draw(sheet)
    for k, t in enumerate(ts):
        im = Image.open(frames / f"f_{round(t * FPS):04d}.png").convert("RGB").resize((tw, th))
        x0, y0 = (k % cols) * tw, (k // cols) * (th + 18)
        sheet.paste(im, (x0, y0))
        w = th * 9 / 16
        c = min(max(cx_at(KEYS[sid], t) * tw, w / 2), tw - w / 2)
        d.rectangle([x0 + c - w / 2, y0, x0 + c + w / 2, y0 + th - 1], outline=(95, 227, 154), width=2)
        for i in range(1, 10):  # tenths of the width, to read keys off
            d.line([x0 + i * tw / 10, y0 + th - 6, x0 + i * tw / 10, y0 + th - 1], fill=(200, 200, 200))
        d.text((x0 + 4, y0 + th + 2), f"{t:.1f} s  cx {cx_at(KEYS[sid], t):.2f}", fill=(220, 220, 220))
    sheet.save(out, quality=88)
    print(out, len(ts), "frames")


if __name__ == "__main__":
    main()
