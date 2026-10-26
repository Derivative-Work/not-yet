"""The captions as SRT files (brief, deliverables: "burned-in captions plus a separate SRT file"): one per line, timed
as the burned-in captions (overlays/cues.json), for the main video and each vertical short (times from its start).
Lines are the sung text (timing map), so the SRT matches what is heard and shown.

Usage: .venv/bin/python -I scripts/make_srt.py [OUT_DIR=deliverables]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CUES = json.loads((ROOT / "overlays/cues.json").read_text())
TEXT = {ln["id"]: ln["text"] for ln in json.loads((ROOT / "timing/timing_map.json").read_text())["lines"]}


def stamp(t):
    ms = int(round(max(t, 0.0) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def srt(t0=0.0, t1=1e9):
    out = []
    for c in CUES["captions"]:
        on, off = max(c["on"], t0), min(c["off"], t1)
        if off - on < 0.3:
            continue
        out.append(f"{len(out) + 1}\n{stamp(on - t0)} --> {stamp(off - t0)}\n{TEXT[c['id']]}\n")
    return "\n".join(out)


def main():
    d = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "deliverables")
    d.mkdir(parents=True, exist_ok=True)
    files = {"not_yet.srt": srt()}
    for s in CUES["shorts"]:
        files[f"not_yet_short_{s['id']}.srt"] = srt(s["from"], s["to"])
    for name, body in files.items():
        (d / name).write_text(body)
        print(d / name, body.count("-->"), "captions")


if __name__ == "__main__":
    main()
