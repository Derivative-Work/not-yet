"""Extract a Suno clip's metadata and lyrics from a page fetched by scripts/fetch_suno.mjs.

Writes <dir>/clip.json (id, title, style tags as Suno stored them, model, duration, created_at, sliders) and
<dir>/lyrics.txt (the lyrics as submitted, from the page text). Usage: suno_meta.py <fetch dir>
"""
import json
import re
import sys
from pathlib import Path

KEYS = ["id", "title", "tags", "display_tags", "model_name", "major_model_version", "duration", "created_at", "type",
        "make_instrumental", "is_remix", "control_sliders", "handle"]


def main(d):
    d = Path(d)
    h = (d / "page.html").read_text()
    i = h.find('\\"major_model_version\\"')
    seg = h[max(0, i - 8000):i + 8000].encode().decode("unicode_escape", errors="ignore")
    clip = {}
    for k in KEYS:
        m = re.search(r'"' + k + r'":("(?:[^"\\]|\\.)*"|\{[^{}]*\}|[-0-9.]+|true|false|null)', seg)
        if m:
            clip[k] = json.loads(m.group(1))
    (d / "clip.json").write_text(json.dumps(clip, indent=1, ensure_ascii=False) + "\n")
    t = (d / "page.txt").read_text()
    # The lyrics run from the first section tag to the last line, "Goodnight.".
    a, b = t.find("[Verse 1]"), t.rfind("Goodnight.")
    (d / "lyrics.txt").write_text(t[a:b + len("Goodnight.")] + "\n")
    print(d.name, clip.get("id"), clip.get("duration"))


if __name__ == "__main__":
    for d in sys.argv[1:]:
        main(d)
