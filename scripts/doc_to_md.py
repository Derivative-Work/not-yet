"""Convert a Claude Docs prose read (the tool's JSON result, saved to a file) to Markdown.

Usage: doc_to_md.py <read_result.json> <out.md>
"""
import html
import json
import re
import sys
import xml.etree.ElementTree as ET


def inline(el):
    out = []
    for c in el:
        if c.tag == "text":
            out.append(text_run(c))
        elif c.tag == "date":
            out.append(c.get("value"))
        elif c.tag == "mention":
            out.append("@" + (c.get("name") or c.get("user") or ""))
    return "".join(out)


def text_run(t):
    s = t.text or ""
    for c in t:
        inner = "".join(c.itertext())
        if c.tag == "bold":
            s += f"**{inner}**"
        elif c.tag == "code":
            s += f"`{inner}`"
        elif c.tag == "link":
            s += f"[{inner}]({c.get('href')})"
        else:
            s += inner
        s += c.tail or ""
    return s


def block(el, depth=0):
    if el.tag == "paragraph":
        h = el.get("heading")
        s = inline(el)
        return ("#" * int(h) + " " + s) if h else s
    if el.tag == "codeBlock":
        return f"```{el.get('language') or ''}\n" + "".join(el.itertext()).rstrip("\n") + "\n```"
    if el.tag == "list":
        kind, lines = el.get("kind"), []
        for i, li in enumerate(el.findall("listItem"), 1):
            mark = {"ordered": f"{i}.", "check": "- [x]" if li.get("checked") == "true" else "- [ ]"}.get(kind, "-")
            parts = [block(c, depth + 1) for c in li]
            first, rest = parts[0], parts[1:]
            lines.append("    " * depth + f"{mark} {first}")
            lines += [p for p in rest]
        return "\n".join(lines)
    if el.tag == "table":
        rows = []
        for r in el.findall("row"):
            rows.append(["<br>".join(inline(p) for p in c.findall("paragraph")).replace("|", "\\|") for c in r.findall("cell")])
        out = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join("---" for _ in rows[0]) + " |"]
        out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        return "\n".join(out)
    return ""


def main(src, dst):
    d = json.load(open(src))
    x = d["data"]["xml"] if "data" in d else d["xml"]
    root = ET.fromstring(x)
    md = "\n\n".join(b for b in (block(c) for c in root) if b is not None)
    open(dst, "w").write(md + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:3])
