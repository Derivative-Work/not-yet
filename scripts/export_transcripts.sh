#!/usr/bin/env bash
# Export this project's Claude Code session transcripts into transcripts/claude-code/ (brief: session transcripts are
# large files, out of git, hashed in MANIFEST.sha256 and published in the GitHub Release). Verbatim copies of
# ~/.claude/projects/<project>/: each session's .jsonl plus its side directory (offloaded tool results, subagents).
# A transcript is append-only while its session runs, so a later export may replace an earlier snapshot only if the
# old file is an exact prefix of the new one; anything else is refused (never overwrite an asset).
# Usage: scripts/export_transcripts.sh   (run from the repo root, on each machine that ran sessions)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
src="$HOME/.claude/projects/$(pwd | sed 's|[^A-Za-z0-9]|-|g')"
dst=transcripts/claude-code
[ -d "$src" ] || { echo "no Claude Code sessions for this path: $src"; exit 1; }
mkdir -p "$dst"
for f in "$src"/*.jsonl; do
  id=$(basename "$f" .jsonl)
  out="$dst/$id.jsonl"
  if [ -e "$out" ] && ! cmp -s "$out" "$f"; then
    n=$(stat -c %s "$out")
    if ! cmp -s -n "$n" "$out" "$f"; then echo "REFUSED: $out is not a prefix of $f"; exit 1; fi
  fi
  cp "$f" "$out"
  if [ -d "$src/$id" ]; then mkdir -p "$dst/$id"; cp -r "$src/$id/." "$dst/$id/"; fi
  cmp -s "$f" "$out" && echo "$id: $(wc -l < "$out") lines, $(du -h "$out" | cut -f1)"
done
scripts/manifest.sh
