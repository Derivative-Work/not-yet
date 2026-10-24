"""C3: the beat grid and the bars (downbeats) for a 3/4 song whose tempo breathes.

Beats: Suno's MIDI tempo map (identical in every file, about one tempo event per beat: a beat track), moved by
Suno's global MIDI offset (config/event_sources.json) and then by the median offset of the music box's onsets to
their nearest beat (within 80 ms), so the grid sits on what is heard.

Bars: the song is in 3/4, but Suno's grid drops or adds beats where the tempo breathes (the bridge falls to about
100 bpm), so a fixed "every third beat" drifts out of phase (C3: the accented phase moves window to window). The
downbeats are chosen by dynamic programming over the grid: each beat scores the onset strength of the stems that
mark bars (music box, bass, guitar; each normalised by its own 95th percentile) plus the sung word starts within
60 ms; a bar of 3 beats costs nothing, 2 or 4 beats cost PENALTY, anything else is not allowed. The best path
maximises downbeat score minus penalties.

Usage: .venv/bin/python -I scripts/meter.py  ->  config/meter.json, timing/beats.json
"""
import json
import sys
from collections import Counter
from pathlib import Path

import librosa
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import midi_io  # noqa: E402
from song import MIDI, STEM  # noqa: E402

SR, HOP = 22050, 256
BAR_STEMS = {"Keyboard": 1.0, "Bass": 1.0, "Guitar": 0.7}
WORD_WEIGHT = 0.8
PENALTY = {3: 0.0, 2: 1.6, 4: 1.6}


def beat_grid():
    off = json.loads(Path("config/event_sources.json").read_text())["suno_midi_offset_s"]["value"]
    beats = midi_io.load(MIDI.format("Keyboard")).get_beats() + off
    kb = np.array([e["t"] for e in json.loads(Path("timing/events/keyboard.json").read_text())["events"]])
    i = np.clip(np.searchsorted(beats, kb), 1, len(beats) - 1)
    near = np.where(np.abs(beats[i] - kb) < np.abs(beats[i - 1] - kb), beats[i], beats[i - 1])
    d = kb - near
    fine = float(np.median(d[np.abs(d) < 0.08]))
    return beats + fine, off, fine


def scores(beats):
    s = np.zeros(len(beats))
    for stem, wgt in BAR_STEMS.items():
        y, _ = librosa.load(STEM.format(stem), sr=SR, mono=True)
        env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
        f = np.clip((beats * SR / HOP).astype(int), 0, len(env) - 1)
        v = np.array([env[max(0, k - 2):k + 3].max() for k in f])
        s += wgt * v / (np.percentile(v, 95) + 1e-9)
    words = [w["start"] for ln in json.loads(Path("timing/words.json").read_text())["lines"] for w in ln["words"]]
    w = np.array(words)
    s += WORD_WEIGHT * np.array([np.any(np.abs(w - b) < 0.06) for b in beats])
    return s


def best_bars(s):
    n = len(s)
    best = np.full(n, -np.inf)
    prev = np.full(n, -1)
    for k in range(min(4, n)):  # the first downbeat may fall on any of the first four beats
        best[k] = s[k]
    for k in range(n):
        for L, pen in PENALTY.items():
            j = k - L
            if j >= 0 and best[j] > -np.inf and best[j] + s[k] - pen > best[k]:
                best[k], prev[k] = best[j] + s[k] - pen, j
    k = int(np.argmax(best[-4:])) + n - 4
    path = []
    while k >= 0:
        path.append(k)
        k = prev[k]
    return path[::-1]


def main():
    beats, off, fine = beat_grid()
    s = scores(beats)
    down = best_bars(s)
    lens = np.diff(down)
    odd = [{"bar": i + 1, "beat": int(down[i]), "t": round(float(beats[down[i]]), 3), "beats": int(L)}
           for i, L in enumerate(lens) if L != 3]
    Path("timing/beats.json").write_text(json.dumps({
        "beats": [round(float(b), 4) for b in beats], "downbeat_beats": [int(d) for d in down]}) + "\n")
    Path("config/meter.json").write_text(json.dumps({
        "_doc": "Bars for 3/4 (scripts/meter.py): downbeats chosen by dynamic programming over Suno's beat grid. "
                "Bars that are not 3 beats are listed with their times for the ear check.",
        "suno_offset_s": off, "grid_fine_shift_s": round(fine, 4), "beats": len(beats), "bars": len(down),
        "bar_lengths": dict(Counter(int(x) for x in lens)), "irregular_bars": odd}, indent=1) + "\n")
    print(f"grid: Suno offset {off * 1000:+.0f} ms, fine {fine * 1000:+.1f} ms; {len(beats)} beats, {len(down)} bars; "
          f"lengths {dict(Counter(int(x) for x in lens))}")
    for o in odd:
        print("  irregular", o)


if __name__ == "__main__":
    main()
