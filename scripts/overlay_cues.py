"""Build overlays/cues.json, the 2D overlay's timeline (overlays/overlay.html), from the timing map, the shop screen's
times (overlays/screen.json), the cards (overlays/cards.json) and the release values (config/release.json).

- captions: each lyric line with its words (style spec, "Captions"); verse 4 in the lighter weight
- checks: N34's check marks beside the caption, one as each auditor's flag is marked on the shop screen
- label: the opening `AI-generated satire` label
- crt: N41, the line opening (after the audio ends)
- facts: N42, one card at a time, each held for its length
- bookend: N43, the real audit log scrolling, then its last line held
- end_card: N44, one line at a time
- note: the human's closing note (human, C6), after the end card; each short ends on it too, after its own content
- shorts: the two vertical cuts' spans (brief, "Vertical cut" and "Second vertical cut")

Usage: .venv/bin/python -I scripts/overlay_cues.py [--draft]   (--draft: allow a null repo URL, shown as a placeholder)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TM = json.loads((ROOT / "timing/timing_map.json").read_text())
SCREEN = json.loads((ROOT / "overlays/screen.json").read_text())
CARDS = json.loads((ROOT / "overlays/cards.json").read_text())
REL = json.loads((ROOT / "config/release.json").read_text())
SHOT = {s["id"]: s["t"] for s in TM["shots"]}
OUT = TM["outro"]
LEAD, TAIL = 0.4, 0.6  # a caption shows from just before its first word to just after its last
# Words whose first letter flickers between two forms while the line is up (human, C6: "on the "windows are never quite
# mended", make the "w" flicker between capital W and lowercase"). The SRT keeps the sung text.
FLICKER = {("L08", "windows"): ["windows", "Windows"]}


def at(ref):
    return SHOT[ref[0]] + ref[1]


def captions():
    lines = TM["lines"]
    caps = []
    for k, ln in enumerate(lines):
        on, off = ln["start"] - LEAD, ln["end"] + TAIL
        if k + 1 < len(lines):
            off = min(off, lines[k + 1]["start"] - LEAD)
        caps.append({"id": ln["id"], "on": round(on, 3), "off": round(off, 3),
                     "thin": ln["section"].startswith("Verse 4"),
                     "words": [{"w": w["w"], "t": w["start"], "e": w["end"],
                                **({"flicker": FLICKER[ln["id"], w["w"]]} if (ln["id"], w["w"]) in FLICKER else {})}
                               for w in ln["words"]]})
    return caps


def card_hold(text):
    """Seconds a card stays up: about 3.3 words a second plus time to find it, 4 to 8.5 s."""
    return min(8.5, max(4.0, 2.0 + len(text.split()) / 3.3))


def excerpt(sec):
    s = (ROOT / sec["file"]).read_text()
    i, j = s.index(sec["from"]), s.index(sec["to"])
    return s[i:j].strip()


def short_cut(sid, t0, content_to, label, label_s, note_s, doc):
    """A vertical cut's span in song time: its content to content_to, then black with the human's note (song times
    past content_to are the short's own, not the song's: the overlay draws the note there instead of the song's cues)."""
    on = content_to + 0.8
    sh = {"id": sid, "from": t0, "content_to": round(content_to, 3), "to": round(on + note_s + 0.5, 3),
          "note_on": round(on, 3), "note_off": round(on + note_s, 3), "label": label, "doc": doc}
    if label_s:
        sh["label_s"] = label_s
    return sh


def main():
    draft = "--draft" in sys.argv
    if not CARDS["facts_checked"]:
        sys.exit("facts_checked is false: run and log the source check first")
    repo = REL["repo_url"]
    if repo is None and not draft:
        sys.exit("config/release.json repo_url is null: the end card needs it (or pass --draft)")
    n_int = sum(1 for ln in (ROOT / "log/human_interventions.md").read_text().splitlines() if ln.startswith("## "))
    t = OUT["fact_card"] + 0.4
    facts = []
    for f in CARDS["facts"]:
        hold = card_hold(f["text"])
        facts.append({**f, "on": round(t, 3), "off": round(t + hold, 3)})
        t += hold + 0.6
    bk = CARDS["bookend"]
    book = {"on": round(t + 0.4, 3), "scroll_s": 30.0, "last_s": 4.5, "last": bk["last"],
            "sections": [{"title": s["title"], "md": excerpt(s)} for s in bk["sections"]]}
    book["off"] = round(book["on"] + book["scroll_s"] + book["last_s"], 3)
    t = book["off"] + 1.0
    fill = {"interventions": str(n_int), "repo_url": repo or "[repo URL]"}
    lines = [re.sub(r"\{(\w+)\}", lambda m: fill[m.group(1)], s) for s in CARDS["end_card"]]
    step = 1.5
    end_card = {"on": round(t, 3), "step": step, "lines": lines}
    end_card["off"] = round(t + step * len(lines) + 6.0, 3)
    hn = CARDS["human_note"]
    note_s = card_hold(" ".join(hn["lines"]))
    note = {"on": round(end_card["off"] + 1.6, 3), "from": hn["from"], "lines": hn["lines"]}
    note["off"] = round(note["on"] + note_s, 3)
    checks = [round(at(a["from"]) + a["mark_at"] + a["mark_s"] * 0.5, 3) for a in SCREEN["audits"]]
    cues = {
        "_doc": "Generated by scripts/overlay_cues.py; do not edit.",
        "fps": TM["fps"],
        "end": round(note["off"] + 0.5, 3),
        "song_black": OUT["black"],
        "palette": {"comfort": "#ffe3b0", "paper": "#efe8da", "white": "#f1f4ee", "steel": "#8d97a6",
                    "frost": "#dfe9f7", "void": "#04060b"},
        "label": CARDS["label"],
        "captions": captions(),
        "checks": {"line": TM["lines"][[ln["id"] for ln in TM["lines"]].index("L32")]["id"], "at": checks},
        "crt": {"on": OUT["crt"], "off": OUT["fact_card"]},
        "facts": facts,
        "bookend": book,
        "end_card": end_card,
        "note": note,
        "shorts": [
            short_cut("bridge", SHOT["N23"] - 0.5, facts[-1]["off"] + 0.6, None, None, note_s,
                      "the bridge through the CRT line (N23 to N41), then the fact card, then the human's note"),
            short_cut("windows", 34.6, 64.7, CARDS["label"]["text"], [0.3, 4.0], note_s,
                      "Chorus 1, N07 to just before N11; opens with the label; no fact card; ends on the human's note"),
        ],
        "repo_url_missing": repo is None,
    }
    (ROOT / "overlays/cues.json").write_text(json.dumps(cues, indent=1, ensure_ascii=False) + "\n")
    print(f"cues: {len(cues['captions'])} captions, {len(facts)} facts {facts[0]['on']}..{facts[-1]['off']} s, "
          f"bookend {book['on']}..{book['off']} s, end card {end_card['on']}..{end_card['off']} s, "
          f"note {note['on']}..{note['off']} s, end {cues['end']} s; "
          f"interventions {n_int}" + ("; REPO URL MISSING (draft)" if repo is None else ""))


if __name__ == "__main__":
    main()
