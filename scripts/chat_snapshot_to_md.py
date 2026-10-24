"""Convert a claude.ai chat_snapshots JSON (from scripts/fetch_share.mjs) into a readable markdown transcript.

Usage: python3 scripts/chat_snapshot_to_md.py <snapshot.json> <share url> > out.md
"""
import json
import sys


def render_tool_use(block):
    label = block.get("message") or block["name"]
    inp = block.get("input")
    if block["name"] == "web_search" and inp:
        return f"> *[{label}: \"{inp.get('query', '')}\"]*"
    return f"> *[{label}]*"


def main():
    path, url = sys.argv[1], sys.argv[2]
    snap = json.load(open(path, encoding="utf-8"))
    out = [
        f"# Planning chat: {snap['snapshot_name']}",
        "",
        f"Source: {url} (snapshot taken {snap['created_at']}). Raw snapshot: `planning_chat.json`.",
        "Tool calls are shown as one-line placeholders; tool results are omitted (they are in the raw JSON).",
        "",
    ]
    for m in snap["chat_messages"]:
        speaker = "User" if m["sender"] == "human" else "Claude"
        out += ["---", "", f"## {m['index'] + 1}. {speaker} ({m['created_at']})", ""]
        for block in m["content"]:
            if block["type"] == "text" and block.get("text", "").strip():
                out += [block["text"].strip(), ""]
            elif block["type"] == "tool_use":
                out += [render_tool_use(block), ""]
    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    main()
