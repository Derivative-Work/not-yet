"""Physical attack times: where a note's sound actually starts in its stem.

For each onset, take the stem's amplitude envelope (Hilbert, 1 ms smoothing) in a window around it; the attack is
the first sample above baseline + 20% of the rise to the window's peak, where baseline is the median of the 30 ms
before the window and the peak must be at least 3x the baseline (a clear attack). This is the reference for
shifting a transcription onto the audio. It replaced onset-envelope peaks, which lag real drum and piano attacks
by about 13-20 ms more than they lag synthetic test onsets, and so had made every shift too large (log, step 5
C3 revision).
"""
import numpy as np
import scipy.signal as sg
import soundfile as sf

_cache = {}


def envelope(stem_path):
    if stem_path not in _cache:
        y, sr = sf.read(stem_path)
        y = y.mean(1) if y.ndim > 1 else y
        env = np.abs(sg.hilbert(y))
        k = int(sr * 0.001)
        env = sg.filtfilt(np.ones(k) / k, 1, env)
        _cache[stem_path] = (env, sr)
    return _cache[stem_path]


def isolated(onsets, gap=0.15):
    """Onsets with no other onset in the preceding `gap` seconds: in dense parts a window around a note otherwise
    catches the previous note's decay or another note's attack."""
    o = np.sort(np.asarray(onsets))
    keep = np.r_[True, np.diff(o) >= gap]
    return o[keep]


def attack_offsets(stem_path, onsets, before=0.06, after=0.08, quiet=0.15):
    """Signed offsets (s) from each onset to the stem's physical attack near it; NaN where no clear attack (peak
    under 3x baseline, or baseline above `quiet` x peak, i.e. the note doesn't start from near-silence)."""
    env, sr = envelope(stem_path)
    out = []
    for t in onsets:
        a, b = int((t - before) * sr), int((t + after) * sr)
        if a < int(0.03 * sr) or b >= len(env):
            out.append(np.nan)
            continue
        w = env[a:b]
        pk = int(np.argmax(w))
        base = float(np.median(env[a - int(0.03 * sr):a]))
        if w[pk] < 3 * base + 1e-4 or base > quiet * w[pk]:
            out.append(np.nan)
            continue
        k = np.where(w[:pk + 1] > base + 0.2 * (w[pk] - base))[0]
        out.append((a + k[0]) / sr - t if len(k) else np.nan)
    return np.array(out)
