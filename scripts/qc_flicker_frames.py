"""QC companion to qc_flicker.py: for the frames with the most popping pixels (one per window of --gap frames), a
panel of a | b | c | b with the pop mask in red, for a human-eye pass.

Usage: PYTHONPATH=scripts .venv/bin/python scripts/qc_flicker_frames.py <frames dir> <qc dir with flicker.csv> [--n 16] [--gap 60]
  -> <qc dir>/top_<frame>.png
"""
import sys
from pathlib import Path

import cv2
import numpy as np

from qc_flicker import pops


def main():
    src, qc = Path(sys.argv[1]), Path(sys.argv[2])
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 16
    gap = int(sys.argv[sys.argv.index("--gap") + 1]) if "--gap" in sys.argv else 60
    rows = [tuple(map(int, l.split(","))) for l in (qc / "flicker.csv").read_text().splitlines()[1:]]
    step = rows[1][0] - rows[0][0]
    picked = []
    for f, px, _ in sorted(rows, key=lambda r: -r[1]):
        if all(abs(f - p) > gap for p, _ in picked):
            picked.append((f, px))
        if len(picked) == n:
            break
    for f, px in sorted(picked):
        a, b, c = (cv2.imread(str(src / f"f_{g:04d}.png")).astype(np.float32) / 255 for g in (f - step, f, f + step))
        m = pops(a, b, c, 0.06)[1]
        mark = b.copy()
        mark[m] = (0, 0, 1)
        top = np.concatenate([a, b], 1)
        bot = np.concatenate([c, mark], 1)
        cv2.imwrite(str(qc / f"top_{f:04d}.png"), (np.concatenate([top, bot], 0) * 255).astype(np.uint8))
        print(f"frame {f} ({f / 30:.2f} s): {px} px", flush=True)


if __name__ == "__main__":
    main()
