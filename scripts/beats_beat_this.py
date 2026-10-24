"""C3: beats and downbeats from beat_this (Foscarin, Schlüter and Widmer, ISMIR 2024; CPJKU/beat_this at b95c8ab,
checkpoint "final0"), on the Suno mix and on the music box stem. The human approved it at C3 after the grid from
Suno's tempo map proved unreliable for the bars (log, C3 review).

Usage: .venv/bin/python -I scripts/beats_beat_this.py  ->  timing/beat_this.json
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import soundfile as sf
from beat_this.inference import Audio2Beats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from song import STEM, TRACK  # noqa: E402


def run(a2b, path):
    y, sr = sf.read(path, dtype="float32")
    beats, downs = a2b(y, sr)
    idx = np.searchsorted(beats, downs - 1e-6)
    return {"source": path, "beats": [round(float(b), 4) for b in beats], "downbeats": [round(float(d), 4) for d in downs],
            "beats_per_bar": dict(Counter(int(x) for x in np.diff(idx)))}


def main():
    a2b = Audio2Beats(checkpoint_path="final0", device="cpu", dbn=False)
    out = {"model": "beat_this final0 @ b95c8ab, dbn=False", "mix": run(a2b, TRACK),
           "music_box": run(a2b, STEM.format("Keyboard"))}
    Path("timing/beat_this.json").write_text(json.dumps(out) + "\n")
    for k in ("mix", "music_box"):
        r = out[k]
        b = np.array(r["beats"])
        print(f"{k:10s} beats {len(b)}  downbeats {len(r['downbeats'])}  median {60 / np.median(np.diff(b)):.1f} bpm  "
              f"beats/bar {r['beats_per_bar']}")


if __name__ == "__main__":
    main()
