"""C3: inventory the Suno MIDI and validate it against the stems (ported from Sandbox Rhapsody's step 4; the method
is unchanged, the song's files come from scripts/song.py, and this song has no drums, piano model or stabs).

Suno's MIDI is a transcription, and each file holds several "instruments" (its guess at what it heard in that stem,
split into segments). A track here is one (file, program name) pair, its segments merged.

For each track:
- inventory: program, note count, note range, time span, segments;
- timing: MIDI onsets (chords merged within 30 ms) against onsets detected in the matching stem (librosa, 5.8 ms
  hop). Reports the track's constant shift, then the median, 95th-percentile and worst |offset| that remain, over
  one-to-one pairs (MIDI and stem onsets that are each other's nearest, within 120 ms);
- support: share of MIDI onsets where the stem's onset-strength envelope actually rises (its peak within -10/+60 ms
  of the shifted onset is above the 60th percentile of the surrounding 2 s). This tests that each note is real,
  which a nearest-onset hit rate can't: in dense parts (distorted guitar, piano) the detector resolves only a few
  attacks, so most correct MIDI notes have no detected onset near them;
- coverage (per stem, all its tracks together): share of the stem's detected onsets that some MIDI onset explains
  within 50 ms, i.e. how much of what is heard the MIDI holds;
- ghosts: share of MIDI notes whose onset falls where the stem is silent (below -50 dBFS RMS over the note's first
  80 ms);
- systematic lag: cross-correlation of the MIDI onset train with the stem's onset-strength envelope (±100 ms).

The onset detector itself lags a true attack, more for soft attacks. calibrate() measures that bias on synthetic
clicks, plucks and pads at known times, and it is subtracted before anything is judged. Each track's constant
shift (its median signed offset minus the detector bias) is then removed and the residual scatter judged; a shift
of more than 10 ms makes the verdict "shift" (apply it), not "usable".

Verdicts (thresholds in VERDICT below; sustained parts are judged more leniently, because onset detection on legato
strings, pads and voices is itself unreliable):
  usable      - drive animation from the MIDI as is (onsets snapped to frames);
  shift       - usable after a constant lag correction (logged);
  stem        - unusable: derive events from the stem's onsets instead (substitution logged);
  ignore      - a misattributed fragment (few notes, or mostly ghosts) that drives nothing.

Suno's MIDI for this song runs about 176 ms early in every file. scripts/event_sources.py measures that offset
(config/event_sources.json, "suno_midi_offset_s"); this script applies it to every note first, so the table judges
the notes, not the offset. Run event_sources.py first.

Usage: .venv/bin/python -I scripts/midi_inventory.py  ->  timing/midi_validation.json, timing/midi_inventory.md
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import librosa
import numpy as np
import pretty_midi

sys.path.insert(0, str(Path(__file__).resolve().parent))
import attack_times  # noqa: E402
import midi_io  # noqa: E402
from song import MIDI, STEM, STEMS  # noqa: E402

SR, HOP = 22050, 128
SUSTAINED = {"Synth Choir", "Pad 2 (warm)", "Flute"}
VERDICT = {  # (max median residual ms, max p95 residual ms, min support) for percussive/plucked vs sustained parts
    "percussive": (15.0, 60.0, 0.6),
    "sustained": (30.0, 100.0, 0.4),
}
MIN_NOTES, MAX_GHOSTS, MIN_PAIRS = 12, 0.5, 10
MIN_ISOLATED = 8         # isolated attacks needed to measure a track's own shift
OFFSET = [0.0]  # Suno's global offset (s), for the report
DEFAULT_SHIFT_MS = 10.0  # otherwise: the median of the measured pitched tracks (5.8-13.7 ms; log, C3 revision)
MIN_COVERAGE_PERCUSSIVE = 0.3  # a percussive stem whose MIDI explains less than this of its onsets: use the stem
STABS = set()


def calibrate():
    """Detector bias (ms) by attack type, from synthetic onsets at known times (seed 41)."""
    rng = np.random.default_rng(41)
    out = {}
    for kind in ("click", "pluck", "pad"):
        y = np.zeros(SR * 60)
        times = np.sort(rng.uniform(1, 59, 150))
        times = times[np.r_[True, np.diff(times) > 0.15]]
        n = int(0.3 * SR)
        tt = np.arange(n) / SR
        for t in times:
            if kind == "click":
                sig = rng.standard_normal(n) * np.exp(-tt * 60)
            elif kind == "pluck":
                sig = np.sin(2 * np.pi * 220 * tt) * np.exp(-tt * 8) * np.minimum(1, tt / 0.003)
            else:
                sig = np.sin(2 * np.pi * 330 * tt) * np.minimum(1, tt / 0.04) * np.exp(-tt * 2)
            i = int(t * SR)
            y[i:i + n] += sig[:len(y) - i]
        env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP, lag=1, max_size=3)
        on = librosa.onset.onset_detect(onset_envelope=env, sr=SR, hop_length=HOP, units="time", backtrack=False)
        out[kind] = float(np.median([on[np.argmin(abs(on - t))] - t for t in times]) * 1000)
    return out


def nearest(on, m_on):
    idx = np.searchsorted(on, m_on)
    out = []
    for t, i in zip(m_on, idx):
        cands = [on[j] for j in (i - 1, i) if 0 <= j < len(on)]
        out.append(min(cands, key=lambda c: abs(c - t)) - t if cands else np.inf)
    return np.array(out) * 1000


def mutual(on, m_on, max_ms=120):
    """Signed offsets (ms, stem minus MIDI) for one-to-one pairs: a MIDI onset and a stem onset that are each
    other's nearest, within max_ms. A quiet note the detector didn't resolve then drops out instead of borrowing a
    neighbouring hit's onset (which made dense drums and piano look 85-110 ms off at p95)."""
    if not len(on) or not len(m_on):
        return np.array([])
    i_m = np.clip(np.searchsorted(on, m_on), 1, len(on) - 1)
    near_on = np.where(np.abs(on[i_m - 1] - m_on) <= np.abs(on[i_m] - m_on), i_m - 1, i_m)
    i_s = np.clip(np.searchsorted(m_on, on), 1, len(m_on) - 1)
    near_m = np.where(np.abs(m_on[i_s - 1] - on) <= np.abs(m_on[i_s] - on), i_s - 1, i_s)
    out = []
    for k, j in enumerate(near_on):
        if near_m[j] == k and abs(on[j] - m_on[k]) * 1000 <= max_ms:
            out.append((on[j] - m_on[k]) * 1000)
    return np.array(out)


def onsets_of(notes, merge=0.03):
    t = sorted(n.start for n in notes)
    out = []
    for x in t:
        if not out or x - out[-1] > merge:
            out.append(x)
    return np.array(out)


def analyse_stem(name):
    y, _ = librosa.load(STEM.format(name), sr=SR, mono=True)
    env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP, lag=1, max_size=3)
    on = librosa.onset.onset_detect(onset_envelope=env, sr=SR, hop_length=HOP, units="time", backtrack=False)
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=HOP)[0]
    db = 20 * np.log10(rms + 1e-9)
    return on, env, db


def lag_xcorr(midi_on, env, max_ms=100):
    frames = np.round(midi_on * SR / HOP).astype(int)
    frames = frames[frames < len(env)]
    e = (env - env.mean()) / (env.std() + 1e-9)
    max_lag = int(max_ms / 1000 * SR / HOP)
    scores = [(e[np.clip(frames + k, 0, len(e) - 1)].mean(), k) for k in range(-max_lag, max_lag + 1)]
    best, k = max(scores)
    return k * HOP / SR * 1000, float(best)


def attack(stem, key):
    if key == "drums":  # this song's "Percussion" stem is a vibraphone (pitched, plucked), not a kit
        return "click"
    return "pad" if key in SUSTAINED else "pluck"


def support(env, m_on):
    """Share of onsets where the onset envelope peaks above its local 60th percentile (2 s window)."""
    ok = []
    w = int(1.0 * SR / HOP)
    for t in m_on:
        f = int(t * SR / HOP)
        lo, hi = max(0, f - 2), min(len(env), f + int(0.06 * SR / HOP) + 1)
        if lo >= hi:
            continue
        local = env[max(0, f - w):min(len(env), f + w)]
        ok.append(env[lo:hi].max() > np.percentile(local, 60))
    return float(np.mean(ok)) if ok else 0.0


def main():
    off = json.loads(Path("config/event_sources.json").read_text())["suno_midi_offset_s"]["value"]
    bias = calibrate()
    print("detector bias (ms):", {k: round(v, 1) for k, v in bias.items()})
    rows, coverage, pending = [], {}, {}
    for stem in STEMS:
        on, env, db = analyse_stem(stem)
        pm = midi_io.load(MIDI.format(stem))
        for inst in pm.instruments:  # Suno's global offset (docstring)
            for n in inst.notes:
                n.start += off
                n.end += off
        groups = defaultdict(list)
        for inst in pm.instruments:
            groups["drums" if inst.is_drum else inst.name].append(inst)
        shifted_all = {}
        for key, insts in groups.items():
            notes = [n for i in insts for n in i.notes]
            m_on = onsets_of(notes)
            b = bias[attack(stem, key)]
            # Shift: from physical attacks of isolated notes (scripts/attack_times.py), not onset-detector peaks,
            # which lag real drum and piano attacks by 13-20 ms more than the synthetic calibration suggests.
            others = np.sort([n.start for i in pm.instruments for n in i.notes])
            iso = [t for t in attack_times.isolated(m_on) if not np.any((t - others > 1e-6) & (t - others < 0.15))]
            att = attack_times.attack_offsets(STEM.format(stem), iso) * 1000
            att = att[~np.isnan(att)]
            if len(att) >= MIN_ISOLATED:
                shift, shift_src = float(np.median(att)), f"attack ({len(att)} isolated notes)"
            else:
                shift, shift_src = DEFAULT_SHIFT_MS, f"default ({len(att)} isolated notes)"
            shifted = m_on + shift / 1000
            raw = mutual(on, m_on)
            matched = raw - np.median(raw) if len(raw) else raw   # timing scatter around the track's own offset
            sup = support(env, shifted)
            ghost = float(np.mean([db[min(len(db) - 1, int(n.start * SR / HOP)):
                                      min(len(db), int((n.start + 0.08) * SR / HOP) + 1)].max() < -50 for n in notes]))
            lag, lag_score = lag_xcorr(m_on, env)
            kind = "sustained" if key in SUSTAINED else "percussive"
            med_abs = float(np.median(np.abs(matched))) if len(matched) else float("inf")
            p95 = float(np.percentile(np.abs(matched), 95)) if len(matched) else float("inf")
            max_med, max_p95, min_sup = VERDICT[kind]
            misattributed = key == "drums" and stem in ("Vocals", "Backing Vocals")  # consonants read as hits
            if len(notes) < MIN_NOTES or ghost > MAX_GHOSTS or len(matched) < MIN_PAIRS or misattributed:
                verdict = "ignore"
            elif med_abs <= max_med and p95 <= max_p95 and sup >= min_sup:
                verdict = "shift" if abs(shift) > 5 else "usable"
            else:
                verdict = "stem"
            if verdict != "ignore":
                shifted_all[key] = shifted
            if verdict in ("usable", "shift"):
                # Corrected events: shift applied, ghost notes (onset in stem silence) dropped, so no visible hit
                # ever lands where nothing sounds.
                ev = []
                for n in sorted(notes, key=lambda n: (n.start, n.pitch)):
                    f0 = min(len(db) - 1, int(n.start * SR / HOP))
                    if db[f0:min(len(db), int((n.start + 0.08) * SR / HOP) + 1)].max() < -50:
                        continue
                    ev.append({"t": round(n.start + shift / 1000, 4), "end": round(n.end + shift / 1000, 4),
                               "pitch": n.pitch, "vel": n.velocity})
                slug = f"{stem}__{key}".lower().replace(" ", "_").replace("(", "").replace(")", "")
                pending[slug] = (len(rows), {"stem": stem, "track": key, "shift_ms": round(shift, 1),
                                             "dropped_ghosts": len(notes) - len(ev), "events": ev})
            pitches = [n.pitch for n in notes]
            rows.append({
                "stem": stem, "track": key, "kind": kind, "attack": attack(stem, key),
                "program": None if key == "drums" else int(insts[0].program),
                "segments": len(insts), "notes": len(notes), "onsets": int(len(m_on)),
                "low": pretty_midi.note_number_to_name(min(pitches)), "high": pretty_midi.note_number_to_name(max(pitches)),
                "first_s": round(min(n.start for n in notes), 2), "last_s": round(max(n.end for n in notes), 2),
                "detector_bias_ms": round(b, 1), "shift_ms": round(shift, 1), "shift_source": shift_src,
                "median_abs_ms": round(med_abs, 1) if np.isfinite(med_abs) else None,
                "p95_abs_ms": round(p95, 1) if np.isfinite(p95) else None,
                "worst_abs_ms": round(float(np.max(np.abs(matched))), 1) if len(matched) else None,
                "pairs": int(len(matched)), "support": round(sup, 3), "ghost_share": round(ghost, 3),
                "xcorr_lag_ms": round(lag, 1), "xcorr_score": round(lag_score, 2), "verdict": verdict,
            })
            r = rows[-1]
            print(f"{stem:14s} {key:24s} n={r['notes']:4d} shift={r['shift_ms']:6.1f} med={r['median_abs_ms']} "
                  f"p95={r['p95_abs_ms']} worst={r['worst_abs_ms']} support={r['support']} ghost={r['ghost_share']} "
                  f"-> {verdict}")
        allon = np.sort(np.concatenate(list(shifted_all.values()))) if shifted_all else np.array([])
        cov = float(np.mean(np.abs(nearest(allon, on)) <= 50)) if len(allon) and len(on) else 0.0
        coverage[stem] = {"stem_onsets": int(len(on)), "covered_50ms": round(cov, 3)}
        print(f"{stem:14s} coverage of stem onsets by its MIDI: {cov:.2f} ({len(on)} onsets)")
        # Stem substitution: a percussive stem (clicks) whose MIDI holds too little of what is heard drives its
        # machines from its own detected onsets instead, bias-corrected, with onset strength as velocity.
        if (attack(stem, "") == "click" or stem in STABS) and cov < MIN_COVERAGE_PERCUSSIVE:
            b_stem = bias["pad"] if stem in STABS else bias["click"]
            for r in rows:
                if r["stem"] == stem and r["verdict"] != "ignore":
                    r["verdict"] = "stem"
            strength = env[np.clip((on * SR / HOP).astype(int), 0, len(env) - 1)]
            # Each detected onset moves back to its physical attack (the detector peaks after it); where no clear
            # attack is found, the detector bias plus the measured extra lag on real attacks (13 ms) is removed.
            att = attack_times.attack_offsets(STEM.format(stem), on, before=0.08, after=0.02, quiet=0.5)
            ev = [{"t": round(float(t + a) if not np.isnan(a) else float(t - (b_stem + 13) / 1000), 4),
                   "strength": round(float(x / strength.max()), 3)} for t, x, a in zip(on, strength, att)]
            Path("timing/stem_events").mkdir(exist_ok=True)
            Path(f"timing/stem_events/{stem.lower().replace(' ', '_')}.json").write_text(json.dumps(
                {"stem": STEM.format(stem), "timing": "physical attack (scripts/attack_times.py)", "events": ev},
                indent=0) + "\n")
            print(f"{stem:14s} -> stem substitution: {len(ev)} events in timing/stem_events/")
    # Event files only for tracks still driven by their MIDI once stem substitutions are decided.
    Path("timing/events").mkdir(exist_ok=True)
    for slug, (i, data) in pending.items():
        if rows[i]["verdict"] in ("usable", "shift"):
            Path(f"timing/events/{slug}.json").write_text(json.dumps(data) + "\n")
    Path("timing/midi_validation.json").write_text(json.dumps(
        {"detector_bias_ms": bias, "verdict_thresholds": VERDICT, "coverage": coverage, "tracks": rows}, indent=1) + "\n")
    OFFSET[0] = off
    write_report(bias, coverage, rows)


def write_report(bias, coverage, rows):
    L = ["# MIDI inventory and validation", "",
         "Pre-production step 4. Generated by `scripts/midi_inventory.py` (numbers in `timing/midi_validation.json`); "
         "the method is in that script's docstring. A track is one (file, program) pair with its segments merged. "
         "Offsets are in ms. The shift is how early the MIDI runs against the physical attack in the stem (positive = "
         "early; scripts/attack_times.py, isolated notes only); the timing columns are the scatter of one-to-one "
         "detector pairs around the track's own offset.", "",
         f"Suno's global MIDI offset applied to every note first: {OFFSET[0] * 1000:+.0f} ms "
         "(`scripts/event_sources.py`).", "",
         f"Detector bias removed first (synthetic onsets): clicks {bias['click']:.1f} ms, plucks {bias['pluck']:.1f} ms, "
         f"pads {bias['pad']:.1f} ms.", "",
         "| Stem file | Track (Suno's program) | Notes | Range | Span (s) | Shift | Median | p95 | Worst | Pairs | "
         "Support | Ghosts | Verdict |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    fmt = lambda v, f="{}": "—" if v is None else f.format(v)  # noqa: E731
    for r in rows:
        L.append(f"| {r['stem']} | {r['track']} | {r['notes']} | {r['low']}–{r['high']} | {r['first_s']}–{r['last_s']} | "
                 f"{r['shift_ms']:+.1f} | {fmt(r['median_abs_ms'])} | {fmt(r['p95_abs_ms'])} | {fmt(r['worst_abs_ms'])} | "
                 f"{fmt(r['pairs'])} | {fmt(r['support'], '{:.2f}')} | {fmt(r['ghost_share'], '{:.2f}')} | "
                 f"**{r['verdict']}** |")
    L += ["", "Coverage: the share of each stem's detected onsets that its MIDI tracks explain within 50 ms.", "",
          "| Stem | Detected onsets | Covered |", "| --- | --- | --- |"]
    for k, v in coverage.items():
        L.append(f"| {k} | {v['stem_onsets']} | {v['covered_50ms']:.2f} |")
    L += ["", "Rules applied by the script:",
          "- **shift**: the track's constant offset to the physical attack is applied when events are exported "
          "(`timing/events/`).",
          "- **ghosts** (onset in stem silence below −50 dBFS) are dropped from the exported events; the counts are in "
          "each event file.",
          "- **stem**: a percussive stem whose MIDI explains under 30% of its detected onsets drives its machines from "
          "the stem's own onsets (`timing/stem_events/`).",
          "- **ignore**: fragments too small or too ghostly to validate.",
          "- Whether Suno's MIDI or a Basic Pitch re-transcription drives each instrument is decided after both are "
          "measured (`scripts/event_sources.py`, `config/event_sources.json`)."]
    Path("timing/midi_inventory.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
