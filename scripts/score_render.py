"""Engrave cache/score/score.musicxml with Verovio, one system per page, and patch what the MusicXML import gets
wrong. (Ported from Sandbox Rhapsody; this score has no drum staff, so its key-signature patch is gone.)

Used by scripts/c3_score_preview.py; run alone to write page PNGs for a look:
  .venv/bin/python -I scripts/score_render.py [page ...]  ->  cache/score/page_<n>.png
"""
import sys
from pathlib import Path

import cairosvg
import verovio

OPTS = {"pageWidth": 3600, "pageHeight": 1500, "scale": 45, "breaks": "encoded", "adjustPageHeight": True,
        "header": "none", "footer": "none", "svgViewBox": True, "lyricSize": 5.0}


def toolkit():
    tk = verovio.toolkit()
    tk.setOptions(OPTS)
    tk.loadFile("cache/score/score.musicxml")
    return tk


if __name__ == "__main__":
    tk = toolkit()
    print("pages", tk.getPageCount())
    for pg in [int(a) for a in sys.argv[1:]] or [1]:
        cairosvg.svg2png(bytestring=tk.renderToSVG(pg).encode(), write_to=str(Path(f"cache/score/page_{pg}.png")),
                         output_width=1800, background_color="white")
