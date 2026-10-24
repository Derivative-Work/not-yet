"""Per-frame envelopes of the stems for the animation library (vents, LEDs, the amp): RMS over each video frame
(30 fps -> 1600 samples at 48 kHz), in dB below the stem's loud level (99th percentile), mapped to 0-1 over
FLOOR_DB..0 dB, then smoothed over 3 frames (style spec). Blender reads them with numpy (no audio libraries there).

Usage: .venv/bin/python -I scripts/stem_envelopes.py  ->  timing/envelopes/<stem>.npy (float32, one value per frame)
"""
import json
from pathlib import Path

import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from song import STEM, STEMS  # noqa: E402

FPS = json.loads(Path("config/look.json").read_text())["fps"]
FLOOR_DB = -36.0


def main():
    out = Path("timing/envelopes")
    out.mkdir(parents=True, exist_ok=True)
    for s in STEMS:
        y, sr = sf.read(STEM.format(s))
        y = y.mean(1) if y.ndim > 1 else y
        hop = sr // FPS
        n = len(y) // hop
        rms = np.sqrt((y[:n * hop].reshape(n, hop) ** 2).mean(1))
        db = 20 * np.log10(rms + 1e-9)
        db -= np.percentile(db, 99)
        v = np.clip((db - FLOOR_DB) / -FLOOR_DB, 0, 1)
        v = np.convolve(v, np.ones(3) / 3, mode="same").astype(np.float32)
        np.save(out / f"{s.lower().replace(' ', '_')}.npy", v)
        print(s, n, "frames", f"mean {v.mean():.2f}")


if __name__ == "__main__":
    main()
