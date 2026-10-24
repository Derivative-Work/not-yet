"""C3: choose, per pitched stem, whether Suno's MIDI or the Basic Pitch re-transcription drives its machines, and export
the chosen notes as animation events. Records the choice in config/event_sources.json.

Both sources are measured against the same reference: onsets detected in the stem with a locally normalised onset
envelope (each point divided by the +-2 s maximum, so quiet passages register; Sandbox Rhapsody found the global
default detector blind to them). Per source:
  coverage - share of the stem's detected onsets a note explains within 50 ms (how much of what is heard it holds)
  support  - share of its notes where the stem's onset envelope rises within -10/+40 ms (is each note real)
  ghosts   - share of its notes starting more than 30 dB below the stem's loud level (95th-percentile RMS)
A third candidate, "union", is Suno's notes plus Basic Pitch's where Suno has no onset within 50 ms and the stem's
onset envelope rises (Sandbox Rhapsody's piano: the precise source, filled in by the other). The candidate with the
highest coverage wins unless its support is more than 0.1 below the best support; within 2 points of the best
coverage, the one with the higher support wins.

Suno's MIDI for this song runs about 190 ms early in every file (C3: cross-correlated with Basic Pitch and with the
stems' onsets). Its offset is measured per stem as the shift that maximises coverage of the stem's detected onsets
(+-400 ms, 1 ms steps), and the median over the stems is applied to all Suno notes, and to its tempo map
(scripts/timing_map.py), before anything is compared.

Export (methods from Sandbox Rhapsody's events_from_transcriptions.py): ghosts dropped; a constant shift to the
physical attacks of isolated notes (scripts/attack_times.py); notes within 60 ms grouped into one chord timed at the
nearest detected onset (within 80 ms); events kept only where the stem is playing (within 26 dB of its loud level in
the 0.3 s after the event).

Usage: .venv/bin/python -I scripts/event_sources.py  ->  timing/events/<stem>.json, config/event_sources.json,
       timing/event_sources.md
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np
from scipy.ndimage import maximum_filter1d

sys.path.insert(0, str(Path(__file__).resolve().parent))
import attack_times  # noqa: E402
import midi_io  # noqa: E402
from song import MIDI, STEM  # noqa: E402

SR, HOP = 22050, 128
STEMS = {"Keyboard": "music box comb", "Percussion": "celesta (star births)", "Strings": "pizzicato strings, flute",
         "Guitar": "electric piano, pad", "Bass": "bass"}
GHOST_DB, ACTIVE_DB, MIN_AMP = 30.0, 26.0, 0.12
DET_LAG, SNAP, CHORD = 0.012, 0.08, 0.06


def stem_analysis(path):
    y, _ = librosa.load(path, sr=SR, mono=True)
    env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP, lag=1, max_size=3)
    envn = env / (maximum_filter1d(env, size=int(4.0 * SR / HOP)) + 1e-6)
    det = librosa.onset.onset_detect(onset_envelope=envn, sr=SR, hop_length=HOP, units="time", delta=0.05,
                                     normalize=False) - DET_LAG
    db = 20 * np.log10(librosa.feature.rms(y=y, frame_length=1024, hop_length=HOP)[0] + 1e-9)
    return {"envn": envn, "det": det, "db": db, "loud": float(np.percentile(db, 95))}


def frame(t):
    return int(t * SR / HOP)


def metrics(notes, A):
    t = np.array(sorted(n["t"] for n in notes))
    det = A["det"]
    cov = float(np.mean([np.min(np.abs(t - d)) <= 0.05 for d in det])) if len(t) and len(det) else 0.0
    env, w = A["envn"], int(1.0 * SR / HOP)
    sup = []
    for x in t:
        f = frame(x)
        lo, hi = max(0, f - 1), min(len(env), f + frame(0.04) + 1)
        local = env[max(0, f - w):min(len(env), f + w)]
        sup.append(lo < hi and env[lo:hi].max() > np.percentile(local, 60))
    db = A["db"]
    ghosts = [db[frame(x):frame(x + 0.08) + 1].max(initial=-200) < A["loud"] - GHOST_DB for x in t]
    return {"notes": len(t), "coverage": round(cov, 3), "support": round(float(np.mean(sup)) if sup else 0, 3),
            "ghosts": round(float(np.mean(ghosts)) if ghosts else 0, 3)}


def suno_notes(stem, offset=0.0):
    pm = midi_io.load(MIDI.format(stem))
    return [{"t": float(n.start) + offset, "end": float(n.end) + offset, "pitch": int(n.pitch), "vel": int(n.velocity),
             "program": i.name} for i in pm.instruments for n in i.notes]


def best_offset(t, det, span=0.4):
    """The shift (s) of note onsets `t` that maximises coverage of detected onsets `det` within 30 ms."""
    t = np.sort(t)
    best = (-1, 0.0)
    for off in np.arange(-span, span + 1e-9, 0.001):
        x = t + off
        i = np.clip(np.searchsorted(x, det), 1, len(x) - 1)
        d = np.minimum(np.abs(x[i] - det), np.abs(x[i - 1] - det))
        best = max(best, (float(np.mean(d <= 0.03)), float(off)))
    return best[1], best[0]


def bp_notes(stem):
    return json.loads(Path(f"timing/transcriptions/{stem.lower()}.json").read_text())["notes"]


def supported(t, A):
    env, w, f = A["envn"], int(1.0 * SR / HOP), frame(t)
    lo, hi = max(0, f - 1), min(len(env), f + frame(0.04) + 1)
    return lo < hi and env[lo:hi].max() > np.percentile(env[max(0, f - w):min(len(env), f + w)], 60)


def union(suno, bp, A):
    st = np.array(sorted(n["t"] for n in suno))
    fill = [{**n, "source": "basic_pitch"} for n in bp
            if np.min(np.abs(st - n["t"])) >= 0.05 and n["vel"] / 127 >= MIN_AMP and supported(n["t"], A)]
    return sorted([{**n, "source": "suno"} for n in suno] + fill, key=lambda n: (n["t"], n["pitch"]))


def export(stem, notes, A, source):
    path = STEM.format(stem)
    db = A["db"]
    keep = [n for n in notes if db[frame(n["t"]):frame(n["t"] + 0.08) + 1].max(initial=-200) >= A["loud"] - GHOST_DB
            and (n.get("source", source) == "suno" or n["vel"] / 127 >= MIN_AMP)]
    t = np.unique(np.round([n["t"] for n in keep], 3))
    att = attack_times.attack_offsets(path, attack_times.isolated(t)) * 1000
    att = att[~np.isnan(att)]
    shift = float(np.median(att)) if len(att) >= 8 else 0.0
    ev = sorted(({**n, "t": n["t"] + shift / 1000, "end": n["end"] + shift / 1000} for n in keep),
                key=lambda n: (n["t"], n["pitch"]))
    # Chords: one strike per group, at the detected onset nearest its first note.
    groups = []
    for n in ev:
        if groups and n["t"] - groups[-1][0]["t"] < CHORD:
            groups[-1].append(n)
        else:
            groups.append([n])
    det, out = A["det"], []
    for g in groups:
        t0 = g[0]["t"]
        k = int(np.argmin(np.abs(det - t0))) if len(det) else -1
        tt = float(det[k]) if k >= 0 and abs(det[k] - t0) <= SNAP else t0
        out += [{**n, "t": round(tt, 4), "end": round(max(n["end"], tt + 0.05), 4)} for n in g]
    active = [e for e in out if db[frame(e["t"]):frame(e["t"] + 0.3) + 1].max(initial=-200) >= A["loud"] - ACTIVE_DB]
    return {"stem": stem, "source": source, "shift_ms": round(shift, 1), "shift_from": f"{len(att)} isolated attacks",
            "dropped_ghosts": len(notes) - len(keep), "dropped_inactive": len(out) - len(active), "events": active}


def main():
    Path("timing/events").mkdir(parents=True, exist_ok=True)
    sources = {"_doc": "Which event file drives each instrument's machines (C3). Written by scripts/event_sources.py; "
                       "the measurements are in timing/event_sources.md.",
               "vocals": {"events": "timing/timing_map.json lines/words", "why": "forced alignment of the as-sung lyrics"}}
    L = ["# Event sources", "", "C3. Generated by `scripts/event_sources.py` (method in its docstring). Per stem: Suno's "
         "MIDI against Basic Pitch, measured on the same detected onsets.", "",
         "| Stem | Drives | Source | Notes | Coverage | Support | Ghosts | Chosen | Shift (ms) | Events |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    analyses = {stem: stem_analysis(STEM.format(stem)) for stem in STEMS}
    offs = {stem: best_offset([n["t"] for n in suno_notes(stem)], A["det"]) for stem, A in analyses.items()}
    suno_off = float(np.median([o for o, _ in offs.values()]))
    sources["suno_midi_offset_s"] = {"value": round(suno_off, 3), "per_stem": {k: round(o, 3) for k, (o, _) in offs.items()},
                                     "why": "Suno's MIDI runs early against its stems; the median is applied to every "
                                            "Suno note and to its tempo map"}
    L.insert(4, f"Suno's MIDI offset, measured per stem against detected onsets: "
                f"{', '.join(f'{k} {o * 1000:+.0f} ms' for k, (o, _) in offs.items())}; applied: {suno_off * 1000:+.0f} ms.")
    L.insert(5, "")
    print("suno offsets:", {k: round(o, 3) for k, (o, _) in offs.items()}, "->", round(suno_off, 3))
    for stem, role in STEMS.items():
        A = analyses[stem]
        cand = {"suno": suno_notes(stem, suno_off), "basic_pitch": bp_notes(stem)}
        cand["union"] = union(cand["suno"], cand["basic_pitch"], A)
        m = {k: metrics(v, A) for k, v in cand.items()}
        top_sup = max(v["support"] for v in m.values())
        ok = [k for k in m if m[k]["support"] >= top_sup - 0.1]
        top_cov = max(m[k]["coverage"] for k in ok)
        # Within 2 points of the best coverage, the more reliable source wins: a visible pluck on a note that
        # isn't there is worse than one fewer pluck.
        win = max((k for k in ok if m[k]["coverage"] >= top_cov - 0.02), key=lambda k: m[k]["support"])
        data = export(stem, cand[win], A, win)
        slug = f"timing/events/{stem.lower()}.json"
        Path(slug).write_text(json.dumps(data) + "\n")
        sources[stem.lower()] = {"events": slug, "drives": role, "source": win,
                                 "why": f"coverage {m[win]['coverage']:.2f} (suno {m['suno']['coverage']:.2f}, basic-pitch "
                                        f"{m['basic_pitch']['coverage']:.2f}, union {m['union']['coverage']:.2f}); "
                                        f"shift {data['shift_ms']:+.1f} ms; {data['dropped_ghosts']} ghosts and "
                                        f"{data['dropped_inactive']} inactive-section events dropped"}
        for k in ("suno", "basic_pitch", "union"):
            ch = k == win
            L.append(f"| {stem} | {role} | {k} | {m[k]['notes']} | {m[k]['coverage']:.2f} | {m[k]['support']:.2f} | "
                     f"{m[k]['ghosts']:.2f} | {'**yes**' if ch else ''} | {data['shift_ms'] if ch else ''} | "
                     f"{len(data['events']) if ch else ''} |")
        print(f"{stem:10s} detected {len(A['det']):4d}  suno {m['suno']}  bp {m['basic_pitch']}  union {m['union']}  -> {win}, "
              f"{len(data['events'])} events, shift {data['shift_ms']} ms")
    Path("config/event_sources.json").write_text(json.dumps(sources, indent=1) + "\n")
    Path("timing/event_sources.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
