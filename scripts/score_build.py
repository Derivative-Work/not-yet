"""Build a readable score of the timing data, for the C3 check (human, C3: "a score is best, like it generated for
that step"). Ported from Sandbox Rhapsody's score_build.py.

Parts, from config/event_sources.json: Vocals (the aligned words, each a note at its aligned start, pitched from
Suno's vocal MIDI with its offset applied), Music box, Strings and E-piano/pad (the Guitar stem) each on
two staves split at middle C (Strings and E-piano: lowest 3 notes of each chord shown), Celesta, Bass (lowest line). Every event is placed on the measured
beat grid (timing/timing_map.json, one beat = one quarter) at eighth-note resolution (at about 150 bpm the
arrangement moves in eighths; sixteenths only added clutter), in the song's own bars, 3/4 with the odd 2/4 or 4/4 bar
the meter found. Key signatures come from music21's key analysis of each section (all G minor, except the final
chorus in E-flat major).

Usage: .venv/bin/python -I scripts/score_build.py  ->  cache/score/score.musicxml
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from music21 import chord, clef, instrument, key, layout, meter, metadata, note, pitch, stream, tempo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import midi_io  # noqa: E402
from song import MIDI  # noqa: E402

TM = json.loads(Path("timing/timing_map.json").read_text())
SRC = json.loads(Path("config/event_sources.json").read_text())
BEATS = np.array(TM["beats"])
Q = 0.5
OUT = Path("cache/score")
BARS_PER_SYSTEM = 4


def qpos(t):
    i = int(np.clip(np.searchsorted(BEATS, t) - 1, 0, len(BEATS) - 2))
    return i + (t - BEATS[i]) / (BEATS[i + 1] - BEATS[i])


def qz(x):
    return round(x / Q) * Q


def events(stem, lo=None, hi=None):
    ev = json.loads(Path(SRC[stem]["events"]).read_text())["events"]
    return [e for e in ev if (lo is None or e["pitch"] >= lo) and (hi is None or e["pitch"] < hi)
            and e["t"] < TM["duration_s"]]


def mono(evs, top=True):
    by = defaultdict(list)
    for e in evs:
        by[qz(qpos(e["t"]))].append(e)
    on = sorted(by)
    out = []
    for k, q in enumerate(on):
        e = (max if top else min)(by[q], key=lambda x: x["pitch"])
        end = min(qz(qpos(e["end"])), on[k + 1] if k + 1 < len(on) else 1e9)
        out.append((q, max(Q, end - q), [e]))
    return out


def lowest(n):
    def f(items):
        return [(q, d, sorted(evs, key=lambda e: e["pitch"])[:n]) for q, d, evs in items]
    return f


def poly(evs):
    by = defaultdict(list)
    for e in evs:
        by[qz(qpos(e["t"]))].append(e)
    on = sorted(by)
    out = []
    for k, q in enumerate(on):
        end = max(qz(qpos(e["end"])) for e in by[q])
        end = min(end, on[k + 1] if k + 1 < len(on) else 1e9)
        out.append((q, max(Q, end - q), by[q]))
    return out


def section_keys():
    """music21 key analysis (Krumhansl) of the pitched events in each section."""
    ev = [e for s in ("keyboard", "bass", "guitar", "strings") for e in events(s)]
    secs = TM["sections"]
    out = []
    for i, sec in enumerate(secs):
        a, b = sec["start"], secs[i + 1]["start"] if i + 1 < len(secs) else 1e9
        st = stream.Stream()
        for e in ev:
            if a <= e["t"] < b:
                st.append(note.Note(e["pitch"], quarterLength=1))
        out.append((sec["start"], st.analyze("key") if len(st) else key.Key("g")))
    return out


KEYS = section_keys()


def key_at(t):
    return next(k for s, k in reversed(KEYS) if s <= t + 1e-6)


def spell(midi, k):
    p = pitch.Pitch(midi=midi)
    cands = [c for c in (p, p.getHigherEnharmonic(), p.getLowerEnharmonic()) if c is not None and abs(c.alter) <= 1]
    scale = {x.name for x in k.pitches}
    if k.mode == "minor":
        scale.add(k.pitchFromDegree(7).transpose("A1").name)
    for c in cands:
        if c.name in scale:
            return c
    want = -1 if k.sharps < 0 else 1
    for c in cands:
        if c.alter == want:
            return c
    return p


def key_signatures(part):
    last = None
    for s, k in KEYS:
        if last is None or k.sharps != last:
            b = min(TM["bars"], key=lambda b: abs(b["start"] - s)) if s > 0 else None
            part.insert(b["beat"] if b else 0, key.KeySignature(k.sharps))
            last = k.sharps


def time_signatures(part):
    first = TM["bars"][0]["beat"]
    if first:
        part.insert(0, meter.TimeSignature(f"{first}/4"))  # pickup beats before the first downbeat
    last = None
    for b in TM["bars"]:
        if b["beats"] != last:
            part.insert(b["beat"], meter.TimeSignature(f"{b['beats']}/4"))
            last = b["beats"]


def build_part(name, inst, cl, items, lyrics=None):
    p = stream.Part()
    p.partName = name
    p.insert(0, inst)
    p.insert(0, cl)
    time_signatures(p)
    key_signatures(p)
    for q, dur, evs in items:
        k = key_at(evs[0]["t"])
        pitches = [spell(m, k) for m in sorted({e["pitch"] for e in evs})]
        el = note.Note(pitches[0]) if len(pitches) == 1 else chord.Chord(pitches)
        el.quarterLength = dur
        if lyrics and q in lyrics:
            el.lyric = lyrics[q]
        p.insert(q, el)
    end = TM["bars"][-1]["beat"] + TM["bars"][-1]["beats"]
    last = max((q + d for q, d, _ in items), default=0)
    if last < end:
        p.insert(last, note.Rest(quarterLength=end - last))
    p = p.makeMeasures()
    first = TM["bars"][0]["beat"]
    for k, m in enumerate(p.getElementsByClass("Measure")):
        m.number = k if first else k + 1  # score bars match timing_map bars (a pickup is bar 0)
    p.makeTies(inPlace=True)
    p.makeRests(fillGaps=True, inPlace=True)
    for m in p.getElementsByClass("Measure"):
        m.makeAccidentals(searchKeySignatureByContext=True, cautionaryPitchClass=False,
                          cautionaryNotImmediateRepeat=False, overrideStatus=True, inPlace=True)
    return p


def vocal_line():
    """Each aligned word starts a note at its aligned start; its pitch is Suno's vocal MIDI sounding then (offset
    applied), else the nearest; a pitch change inside the word adds a lyric-less note (a melisma)."""
    off = SRC["suno_midi_offset_s"]["value"]
    vm = sorted(({"t": n.start + off, "end": n.end + off, "pitch": n.pitch}
                 for i in midi_io.load(MIDI.format("Vocals")).instruments if i.name == "Synth Choir" for n in i.notes),
                key=lambda e: e["t"])
    vt = np.array([e["t"] for e in vm])

    def pitch_at(t):
        sounding = [e for e in vm if e["t"] - 0.08 <= t < e["end"]]
        if sounding:
            return max(sounding, key=lambda e: e["pitch"])["pitch"]
        return vm[int(np.argmin(np.abs(vt - t)))]["pitch"]

    words = sorted((w for ln in TM["lines"] for w in ln["words"]), key=lambda w: w["start"])
    items, lyr = [], {}
    for k, w in enumerate(words):
        q0, q_end = qz(qpos(w["start"])), qz(qpos(w["end"]))
        if k + 1 < len(words):
            q_end = min(q_end, qz(qpos(words[k + 1]["start"])))
        if items and q0 < items[-1][0] + items[-1][1]:
            prev = items[-1]
            items[-1] = (prev[0], max(Q, q0 - prev[0]), prev[2])
            if q0 <= prev[0]:
                q0 = prev[0] + Q
        q_end = max(q_end, q0 + Q)
        marks = sorted(set(m for m in [q0] + [qz(qpos(e["t"])) for e in vm if w["start"] + 0.06 < e["t"] < w["end"] - 0.06]
                           if q0 <= m < q_end))
        last_pitch = None
        for j, m in enumerate(marks):
            m_end = marks[j + 1] if j + 1 < len(marks) else q_end
            t_m = w["start"] if j == 0 else next(e["t"] for e in vm if qz(qpos(e["t"])) == m)
            pt = pitch_at(t_m + 0.04)
            if pt == last_pitch and items:
                q_prev, _, ev_prev = items[-1]
                items[-1] = (q_prev, m_end - q_prev, ev_prev)
                continue
            items.append((m, m_end - m, [{"pitch": pt, "t": w["start"]}]))
            last_pitch = pt
        lyr[q0] = w["w"]
    return items, lyr


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    voc, lyr = vocal_line()
    parts = [
        build_part("Vocals", instrument.Vocalist(), clef.TrebleClef(), voc, lyrics=lyr),
        build_part("Music box", instrument.Celesta(), clef.TrebleClef(), poly(events("keyboard", lo=60))),
        build_part("Music box (low)", instrument.Celesta(), clef.BassClef(), poly(events("keyboard", hi=60))),
        build_part("Celesta", instrument.Vibraphone(), clef.TrebleClef(), poly(events("percussion"))),
        build_part("Strings", instrument.Violin(), clef.TrebleClef(), lowest(3)(poly(events("strings", lo=60)))),
        build_part("Strings (low)", instrument.Violoncello(), clef.BassClef(), lowest(3)(poly(events("strings", hi=60)))),
        build_part("E-piano / pad", instrument.ElectricPiano(), clef.TrebleClef(), lowest(3)(poly(events("guitar", lo=60)))),
        build_part("E-piano / pad (low)", instrument.ElectricPiano(), clef.BassClef(), lowest(3)(poly(events("guitar", hi=60)))),
        build_part("Bass", instrument.AcousticBass(), clef.Bass8vbClef(), mono(events("bass"), top=False)),
    ]
    sc = stream.Score()
    sc.metadata = metadata.Metadata(title="Not Yet (timing check)")
    for p in parts:
        sc.insert(0, p)
    for p in parts:
        for k, m in enumerate(p.getElementsByClass("Measure")):
            if k and k % BARS_PER_SYSTEM == 0:
                m.insert(0, layout.PageLayout(isNew=True))
                m.insert(0, layout.SystemLayout(isNew=True))
    sc.parts[0].getElementsByClass("Measure")[0].insert(0, tempo.MetronomeMark(number=60))
    sc.write("musicxml", fp=str(OUT / "score.musicxml"))
    print("measures", len(parts[0].getElementsByClass("Measure")), "keys", [(round(s, 1), str(k)) for s, k in KEYS])


if __name__ == "__main__":
    main()
