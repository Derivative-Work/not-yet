"""The pen scratch at N39 ("…or the moment the contract is signed."), synthesised in code: a signature in four
strokes, each band-passed noise (paper friction, 1.8-7 kHz) under an envelope that follows the pen's speed, plus
sparse fibre clicks; a short tap at the end (the full stop). Seeded (config/seeds.json, "pen_scratch"); no recorded
sound is used.

Placement (human, C3): on top of the existing audio, which is not edited or silenced. config/audio.json records where
it goes; the final mix applies it to the mastered track.

Usage: .venv/bin/python -I scripts/pen_scratch.py  ->  audio/sfx/pen_scratch.wav, config/audio.json
"""
import json
from pathlib import Path

import numpy as np
import scipy.signal as sg
import soundfile as sf

SR = 48000
STROKES = [(0.00, 0.34), (0.40, 0.28), (0.74, 0.22), (1.02, 0.30)]  # (start s, length s): a written name
TAP = 1.42
GAIN_DB = -14.0  # peak level of the effect itself; set against the outro's music box at C5 by ear


def main():
    seeds = json.loads(Path("config/seeds.json").read_text())
    rng = np.random.default_rng(seeds["main"])
    n = int((TAP + 0.2) * SR)
    y = np.zeros(n)
    b, a = sg.butter(4, [1800, 7000], btype="band", fs=SR)
    for t0, L in STROKES:
        m = int(L * SR)
        tt = np.linspace(0, 1, m)
        speed = np.sin(np.pi * tt) ** 0.6 * (0.75 + 0.25 * np.sin(2 * np.pi * rng.uniform(2, 5) * tt))
        grain = sg.lfilter(b, a, rng.standard_normal(m))
        clicks = (rng.random(m) < 0.0015) * rng.uniform(0.5, 1.0, m)
        stroke = grain * speed + sg.lfilter(b, a, clicks) * 3.0 * speed
        i = int(t0 * SR)
        y[i:i + m] += stroke
    # The full stop: a short tap of the pen.
    m = int(0.03 * SR)
    tap = sg.lfilter(b, a, rng.standard_normal(m)) * np.exp(-np.linspace(0, 8, m))
    y[int(TAP * SR):int(TAP * SR) + m] += tap * 1.5
    y *= 10 ** (GAIN_DB / 20) / (np.abs(y).max() + 1e-9)
    st = np.stack([y * 0.95, y], 1)  # a little right of centre: the pen is off screen
    Path("audio/sfx").mkdir(parents=True, exist_ok=True)
    sf.write("audio/sfx/pen_scratch.wav", st, SR, subtype="PCM_24")
    tm = json.loads(Path("timing/timing_map.json").read_text())
    cfg = {"_doc": "Audio for the edit (scripts/pen_scratch.py, the human's C3 choices). The track itself is not edited.",
           "track": "audio/track/Sleep, Little Secret.wav",
           "master": None,
           "sfx": [{"file": "audio/sfx/pen_scratch.wav", "at_s": tm["outro"]["pen_scratch"], "gain_db": 0.0,
                    "why": "N39: the waiver's pen, off screen, on top of the existing audio"}]}
    Path("config/audio.json").write_text(json.dumps(cfg, indent=1) + "\n")
    print("pen scratch", round(len(y) / SR, 2), "s at", cfg["sfx"][0]["at_s"], "s")


if __name__ == "__main__":
    main()
