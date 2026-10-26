#!/usr/bin/env bash
# C5: the final render on the RTX 5090 box (config/render_profiles.json "final": 3840x2160, 64 samples, motion blur).
# The windows short's span renders first (brief: its C5 frames go ahead of the rest, before Patch Tuesday), then the
# whole move; both runs share renders/c5/frames and skip frames already there (animatic.py --resume), so a stopped run
# picks up where it left off. Then the anchor stills for the C5 contact sheet. The cloth is baked once, by the first
# run, into renders/c5/cloth and read back by every run (animatic.py --cloth-cache): it does not repeat between bakes.
#
# Usage: scripts/render_final.sh [windows|all|anchors]   (default: all three in order)
set -euo pipefail
cd "$(dirname "$0")/.."
out=renders/c5
mkdir -p "$out/frames" "$out/logs"
what=${1:-everything}
# A stopped run leaves an empty placeholder for the frame it was on; clear those so they render again.
find "$out/frames" -name 'f_*.png' -size 0 -delete
read -r W0 W1 < <(.venv/bin/python -I -c "import json; s=[x for x in json.load(open('overlays/cues.json'))['shorts'] if x['id']=='windows'][0]; print(s['from'] - 0.5, s['to'] + 0.5)")
blend() {  # blender args -> log
  local log=$1; shift
  blender -b --factory-startup --python scenes/blender/animatic.py -- --profile final --cloth-cache "$out/cloth" "$@" \
    > "$out/logs/$log.log" 2>&1
  grep -h "rendered\|anchor N40" "$out/logs/$log.log" || true
}
if [[ $what == windows || $what == everything ]]; then
  blend windows --out "$out/frames" --from "$W0" --to "$W1" --resume
fi
if [[ $what == all || $what == everything ]]; then
  blend all --out "$out/frames" --resume
fi
if [[ $what == anchors || $what == everything ]]; then
  blend anchors --out "$out/anchors" --anchors
  .venv/bin/python -I scripts/contact_sheet.py "$out/anchors" "$out/c5_anchor_sheet.jpg" 6
fi
ls "$out/frames" | wc -l
