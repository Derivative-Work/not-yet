#!/usr/bin/env bash
# Regenerate MANIFEST.sha256 for every published large file (git-ignored, not inspiration, not regenerable).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
# reference/stills is not published (other creators' frames); reference/stills.tsv (in git) lists each one's
# source video and time instead (scripts/stills_index.py).
dirs=(audio renders takes transcripts archive deliverables)
existing=()
for d in "${dirs[@]}"; do [ -d "$d" ] && existing+=("$d"); done
# Frame sequences (plates, overlay frames, assembled sequences) are never archived (brief): they regenerate from
# the logged commands, so they stay out of the manifest. Any directory named plates*/overlay* (plates_superseded_*,
# overlay_v_scene, ...), ovl, plate_seq, or frames* (C5's full-quality sequences, and superseded ones set aside).
find "${existing[@]}" -type f -not -regex '.*/\(plates[^/]*\|overlay[^/]*\|ovl\|plate_seq\|frames[^/]*\)/.*' -print0 \
  | while IFS= read -r -d '' f; do git check-ignore -q "$f" && printf '%s\0' "$f"; done \
  | sort -z | xargs -0 -r sha256sum > MANIFEST.sha256
echo "$(wc -l < MANIFEST.sha256) files in MANIFEST.sha256"
