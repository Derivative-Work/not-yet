"""C3: the timing map, the clock every later step reads (brief: "exact frames come from the timing map").

Joins the beat grid and bars (scripts/meter.py), the aligned words (scripts/align_words.py) and the shot anchors
into timing/timing_map.json, plus a readable timing/timing_map.md. Times are seconds of the Suno mix; frames are
at the style spec's fps (config/look.json).

Shot anchors (brief, "Shot list"): N03..N40 are lines L01..L38 in sung order (Nk = line k-2); N02 opens on the music
box alone at 0 s. N03..N38 are positions of one continuous camera move, not cuts: each anchor is the time the
move must reach its mark, at the line's first word, with the nearest downbeat recorded for focus pulls (texture
pass: on downbeats only). The only cuts are N40 (black), N41 (the CRT line), N42 (fact card), N43 (bookend) and
N44 (end card).

The outro (human, C3: "just add the pen scratch on top of what's existing"): the audio is not edited. The pen scratch
sounds just after "signed" (N39); the chair stops and the stars freeze there, but the music box keeps turning, since it
is still heard. Black follows "Goodnight." (N40), and the music box plays out in the dark. The CRT line opens in the
silence after the audio ends (N41: "Silence"), then the fact card.

Usage: .venv/bin/python -I scripts/timing_map.py  ->  timing/timing_map.json, timing/timing_map.md,
       config/shot_anchors.json
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf

LOOK = json.loads(Path("config/look.json").read_text())
FPS = LOOK["fps"]
TRACK = "audio/track/Sleep, Little Secret.wav"
SILENCE = 0.8      # s of silence after the audio ends before the CRT line opens (N41)
CRT_LEN = 1.0      # s for the CRT line to open into the fact card (N42)


def fr(t):
    return int(round(t * FPS))


def main():
    B = json.loads(Path("timing/beats.json").read_text())
    beats, down = np.array(B["beats"]), B["downbeat_beats"]
    lines = json.loads(Path("timing/words.json").read_text())["lines"]
    dur = sf.info(TRACK).duration
    bars = []
    for i, k in enumerate(down):
        end_b = down[i + 1] if i + 1 < len(down) else len(beats)
        span = beats[min(end_b, len(beats) - 1)] - beats[k] if end_b < len(beats) else (beats[-1] - beats[k]) + 0.42
        nb = end_b - k
        bars.append({"n": i + 1, "beat": int(k), "start": round(float(beats[k]), 4), "beats": int(nb),
                     "bpm": round(60 * nb / span, 1) if span > 0 else None, "frame": fr(beats[k])})
    dts = np.array([b["start"] for b in bars])

    def downbeat_near(t):
        return float(dts[np.argmin(np.abs(dts - t))])

    # Sections: the intro (music box alone), then each lyric section from its first line's start.
    sections = [{"name": "Intro", "start": 0.0}]
    for ln in lines:
        if ln["section"] != (sections[-1].get("lyric") if len(sections) > 1 else None):
            sections.append({"name": ln["section"].split(",")[0] if ln["section"] != "Chorus, variant" else "Chorus 2",
                             "lyric": ln["section"], "start": ln["start"]})
    for s in sections:
        s["frame"] = fr(s["start"])
    for ln in lines:
        ln["start_frame"], ln["end_frame"] = fr(ln["start"]), fr(ln["end"])
        for w in ln["words"]:
            w["start_frame"], w["end_frame"] = fr(w["start"]), fr(w["end"])
    # Shots.
    shots = [{"id": "N02", "anchor": "music box alone", "t": 0.0, "kind": "open"}]
    for k, ln in enumerate(lines):
        nid = f"N{k + 3:02d}"
        shots.append({"id": nid, "anchor": ln["id"], "line": ln["text"], "t": ln["start"],
                      "downbeat": round(downbeat_near(ln["start"]), 4),
                      "kind": "mark" if k + 3 <= 38 else ("outro" if k + 3 == 39 else "cut")})
    signed = lines[-2]["end"]          # L37, "...is signed."
    good = lines[-1]                   # L38, "Goodnight."
    outro = {"pen_scratch": round(signed + 0.05, 3), "freeze": round(signed + 0.05, 3),
             "goodnight": [good["start"], good["end"]], "black": round(good["end"] + 0.4, 3)}
    outro["crt"] = round(dur + SILENCE, 3)
    outro["fact_card"] = round(outro["crt"] + CRT_LEN, 3)
    for s in shots:
        if s["id"] == "N40":
            s.update({"t": outro["black"], "kind": "cut", "note": "black after Goodnight.; the music box plays out"})
        if s["id"] == "N39":
            s["note"] = f"pen scratch {outro['pen_scratch']} s over the existing audio; chair stops, stars freeze"
    shots += [{"id": "N41", "anchor": "after the audio ends", "t": outro["crt"], "kind": "cut"},
              {"id": "N42", "anchor": "fact card", "t": outro["fact_card"], "kind": "cut"},
              {"id": "N43", "anchor": "closing bookend", "t": None, "kind": "cut"},
              {"id": "N44", "anchor": "end card", "t": None, "kind": "cut"}]
    for s in shots:
        s["frame"] = fr(s["t"]) if s["t"] is not None else None
    Path("config/shot_anchors.json").write_text(json.dumps({
        "_doc": "Shot anchors (scripts/timing_map.py): Nk is line L(k-2); outro as approved at C3.",
        "rule": "N03..N40 = L01..L38", "outro": outro}, indent=1) + "\n")
    tm = {"fps": FPS, "duration_s": round(dur, 3), "duration_frames": fr(dur), "audio": TRACK,
          "meter": "3/4", "beats": B["beats"], "downbeat_beats": down, "bars": bars, "sections": sections,
          "lines": lines, "shots": shots, "outro": outro}
    Path("timing/timing_map.json").write_text(json.dumps(tm) + "\n")
    L = ["# Timing map", "", f"C3. Generated by `scripts/timing_map.py` from `timing/beats.json`, `config/meter.json` and "
         f"`timing/words.json`. {FPS} fps; {dur:.2f} s ({fr(dur)} frames); 3/4, {len(bars)} bars.", "",
         "## Sections", "", "| Section | Start (s) | Frame |", "| --- | --- | --- |"]
    L += [f"| {s['name']} | {s['start']:.2f} | {s['frame']} |" for s in sections]
    L += ["", "## Shots", "", "| ID | Anchor | Line | t (s) | Frame | Nearest downbeat (s) | Note |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for s in shots:
        t = "" if s["t"] is None else f"{s['t']:.2f}"
        L.append(f"| {s['id']} | {s['anchor']} | {s.get('line', '')} | {t} | "
                 f"{'' if s['frame'] is None else s['frame']} | {s.get('downbeat', '')} | "
                 f"{s.get('note', '')} |")
    irregular = [b for b in bars if b["beats"] != 3]
    L += ["", "## Bars that are not 3 beats (for the ear check)", "", "| Bar | Start (s) | Beats |", "| --- | --- | --- |"]
    L += [f"| {b['n']} | {b['start']:.2f} | {b['beats']} |" for b in irregular]
    L += ["", "## Words with low alignment confidence (score < 0.3)", ""]
    L += [f"- {ln['id']} {w['w']} at {w['start']:.2f} s (score {w['score']})" for ln in lines for w in ln["words"]
          if w["score"] < 0.3]
    Path("timing/timing_map.md").write_text("\n".join(L) + "\n")
    print(f"{len(bars)} bars, {len(lines)} lines, {len(shots)} shots; outro {outro}")


if __name__ == "__main__":
    main()
