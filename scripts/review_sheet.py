"""A labelled grid of review stills (animatic.py --times): each tile captioned with its file's song time.

Usage: .venv/bin/python -I scripts/review_sheet.py <out.jpg> <cols> <png> [<png> ...]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def main():
    out, cols, paths = sys.argv[1], int(sys.argv[2]), [Path(p) for p in sys.argv[3:]]
    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = ims[0].size
    sheet = Image.new("RGB", (w * cols, h * ((len(ims) + cols - 1) // cols)))
    for k, (p, im) in enumerate(zip(paths, ims)):
        ImageDraw.Draw(im).text((6, 4), p.stem.replace("t_", "").lstrip("0") + " s", fill=(255, 230, 0))
        sheet.paste(im, ((k % cols) * w, (k // cols) * h))
    sheet.save(out, quality=85)
    print(out)


if __name__ == "__main__":
    main()
