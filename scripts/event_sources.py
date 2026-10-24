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

Crosstalk (human, C3 review: "significant crosstalk"). Suno separates its stems from a finished mix, so the music
box leaks into every other stem, and both transcriptions hear the leak: before this filter, 69-86% of the other
stems' events had a same-pitch-class event in the music box within 30 ms. Each event is tested by energy: the
constant-Q magnitude at its pitch (+-1 semitone bin, first 100 ms) in its own stem against the same measure in
every other stem (Vocals included as a source of bleed). If another stem is more than BLEED_DB louder there, the
event is bleed and is dropped, with one exception: where the louder stem is Vocals, the event is dropped only if its
attack is also soft (10-90% rise over VOICE_RISE_MS at its pitch in its own stem), as a leaked voice's is; a plucked
attack is the instrument's own, however loud the singer is over it (C3 score: a level rule alone emptied the music box
under the bridge's vocal; the voice-dropped notes' median rise was 52 ms against 32 ms for the kept ones). A real unison (two instruments on one note) shows comparable energy in both stems
and survives. Then duplicates: the same note (same pitch, onsets within 30 ms) left in two stems at comparable level
(C3 score: the "celesta" doubled the music box note for note in the intro) is kept only in the stem where it is
louder, unless the two are within UNISON_DB (a deliberate unison), so one sound never drives two machines. The
before/after coincidence matrix is in timing/event_sources.md.

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
BLEED_DB = 10.0
UNISON_DB = 3.0
VOICE_RISE_MS = 25.0
RISE_HOP = 64
BLEED_FROM = list(STEMS) + ["Vocals"]
CQT_HOP, CQT_MIDI0 = 256, 24  # CQT bins are semitones from C1 (MIDI 24)
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


_cqt = {}


def cqt_db(stem):
    """Constant-Q magnitude in dB (absolute reference, so stems compare), semitone bins from C1, 7 octaves."""
    if stem not in _cqt:
        y, _ = librosa.load(STEM.format(stem), sr=SR, mono=True)
        C = np.abs(librosa.cqt(y, sr=SR, hop_length=CQT_HOP, fmin=librosa.midi_to_hz(CQT_MIDI0), n_bins=84,
                               bins_per_octave=12))
        _cqt[stem] = 20 * np.log10(C + 1e-9)
    return _cqt[stem]


def level_at(stem, t, pitch):
    C = cqt_db(stem)
    b = int(pitch) - CQT_MIDI0
    if b < 0 or b >= C.shape[0]:
        return -200.0
    f0, f1 = int(t * SR / CQT_HOP), int((t + 0.1) * SR / CQT_HOP) + 1
    return float(C[max(0, b - 1):b + 2, f0:f1].max(initial=-200.0))


_fine = {}


def rise_ms(stem, t, pitch):
    """10-90% rise time (ms) of the stem's constant-Q magnitude at `pitch` around onset t; NaN if no clear rise."""
    if stem not in _fine:
        y, _ = librosa.load(STEM.format(stem), sr=SR, mono=True)
        _fine[stem] = np.abs(librosa.cqt(y, sr=SR, hop_length=RISE_HOP, fmin=librosa.midi_to_hz(CQT_MIDI0), n_bins=84,
                                          bins_per_octave=12))
    C = _fine[stem]
    b, f = int(pitch) - CQT_MIDI0, int(t * SR / RISE_HOP)
    if b < 0 or b >= C.shape[0] or f < 20:
        return float("nan")
    w = C[max(0, b - 1):b + 2, f - 20:f + 30].max(0)
    pk = int(np.argmax(w[10:])) + 10
    base, top = float(np.median(w[:8])), float(w[pk])
    if top < 2 * base:
        return float("nan")
    i10 = int(np.argmax(w[:pk + 1] > base + 0.1 * (top - base)))
    i90 = int(np.argmax(w[:pk + 1] > base + 0.9 * (top - base)))
    return (i90 - i10) * RISE_HOP / SR * 1000


def bleed_filter(stem, events):
    keep, dropped = [], 0
    for e in events:
        own = level_at(stem, e["t"], e["pitch"])
        lv = {o: level_at(o, e["t"], e["pitch"]) for o in BLEED_FROM if o != stem}
        src = max(lv, key=lv.get)
        bleed = lv[src] - own > BLEED_DB
        if bleed and src == "Vocals":
            r = rise_ms(stem, e["t"], e["pitch"])
            bleed = not (r == r and r <= VOICE_RISE_MS)  # a sharp (plucked) attack is the instrument's own
        if bleed:
            dropped += 1
        else:
            keep.append(e)
    return keep, dropped


def dedupe(E):
    """Winner-take-all across stems for identical notes (docstring). E: {stem: events}; returns new dict, counts."""
    tagged = sorted(((e["t"], st, k, e["pitch"]) for st, ev in E.items() for k, e in enumerate(ev)))
    drop = {st: set() for st in E}
    for i, (t, st, k, p) in enumerate(tagged):
        j = i + 1
        while j < len(tagged) and tagged[j][0] - t < 0.03:
            t2, st2, k2, p2 = tagged[j]
            if st2 != st and p2 == p and k not in drop[st] and k2 not in drop[st2]:
                la, lb = level_at(st, t, p), level_at(st2, t2, p2)
                if abs(la - lb) > UNISON_DB:
                    if la < lb:
                        drop[st].add(k)
                    else:
                        drop[st2].add(k2)
            j += 1
    return {st: [e for k, e in enumerate(ev) if k not in drop[st]] for st, ev in E.items()}, \
        {st: len(d) for st, d in drop.items()}


def coincidence(E):
    """Share of A's events with a same-pitch-class event in B within 30 ms."""
    out = {}
    for a in E:
        for b in E:
            if a == b:
                continue
            tb = np.array([e["t"] for e in E[b]])
            pb = np.array([e["pitch"] for e in E[b]])
            hit = sum(bool(np.any((pb[np.abs(tb - e["t"]) < 0.03] % 12) == e["pitch"] % 12)) for e in E[a])
            out[a, b] = hit / max(1, len(E[a]))
    return out


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
    clean, n_bleed = bleed_filter(stem, active)
    return {"stem": stem, "source": source, "shift_ms": round(shift, 1), "shift_from": f"{len(att)} isolated attacks",
            "dropped_ghosts": len(notes) - len(keep), "dropped_inactive": len(out) - len(active),
            "dropped_bleed": n_bleed, "bleed_db": BLEED_DB, "events": clean, "_before_bleed": active}


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
    before, after = {}, {}
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
        before[stem], after[stem] = data.pop("_before_bleed"), data["events"]
        slug = f"timing/events/{stem.lower()}.json"
        Path(slug).write_text(json.dumps(data) + "\n")
        sources[stem.lower()] = {"events": slug, "drives": role, "source": win,
                                 "why": f"coverage {m[win]['coverage']:.2f} (suno {m['suno']['coverage']:.2f}, basic-pitch "
                                        f"{m['basic_pitch']['coverage']:.2f}, union {m['union']['coverage']:.2f}); "
                                        f"shift {data['shift_ms']:+.1f} ms; {data['dropped_ghosts']} ghosts and "
                                        f"{data['dropped_inactive']} inactive-section events and {data['dropped_bleed']} "
                                        f"bleed events dropped"}
        for k in ("suno", "basic_pitch", "union"):
            ch = k == win
            L.append(f"| {stem} | {role} | {k} | {m[k]['notes']} | {m[k]['coverage']:.2f} | {m[k]['support']:.2f} | "
                     f"{m[k]['ghosts']:.2f} | {'**yes**' if ch else ''} | {data['shift_ms'] if ch else ''} | "
                     f"{len(data['events']) if ch else ''} |")
        print(f"{stem:10s} detected {len(A['det']):4d}  suno {m['suno']}  bp {m['basic_pitch']}  union {m['union']}  -> {win}, "
              f"{len(data['events'])} events, shift {data['shift_ms']} ms")
    after, dup = dedupe(after)
    for stem in STEMS:
        slug = f"timing/events/{stem.lower()}.json"
        data = json.loads(Path(slug).read_text())
        data["events"], data["dropped_duplicate"] = after[stem], dup[stem]
        Path(slug).write_text(json.dumps(data) + "\n")
        sources[stem.lower()]["why"] += f"; {dup[stem]} duplicates of a louder stem's notes dropped"
        print(f"{stem:10s} duplicates dropped {dup[stem]:4d}, events {len(after[stem])}")
    cb, ca = coincidence(before), coincidence(after)
    names = list(STEMS)
    L += ["", f"Crosstalk: share of each row stem's events with a same-pitch-class event in the column stem within 30 ms, "
          f"before / after the bleed filter ({BLEED_DB:.0f} dB) and the duplicate rule.", "",
          "| | " + " | ".join(names) + " |", "| --- |" + " --- |" * len(names)]
    for a in names:
        L.append(f"| {a} | " + " | ".join("—" if a == b else f"{cb[a, b]:.2f} / {ca[a, b]:.2f}" for b in names) + " |")
        print(f"{a:10s} bleed dropped {len(before[a]) - len(after[a]):4d}; vs music box {cb.get((a, 'Keyboard'), 0):.2f} -> "
              f"{ca.get((a, 'Keyboard'), 0):.2f}")
    Path("config/event_sources.json").write_text(json.dumps(sources, indent=1) + "\n")
    Path("timing/event_sources.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
