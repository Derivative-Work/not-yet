"""C2 review sheet: Sandbox Rhapsody's probe (its own C1 close-up, re-rendered from that repo) beside this video's
import of it, as a 2x2 grid with a caption on each frame.
Usage: .venv/bin/python -I scripts/c2_sheet.py <out.jpg> <frame.png> <caption> [<frame.png> <caption>]...
"""
import json
import sys

from PIL import Image, ImageDraw, ImageFont

PAD, LABEL, COLS = 16, 30, 2


def main():
    out, rest = sys.argv[1], sys.argv[2:]
    pairs = list(zip(rest[::2], rest[1::2]))
    look = json.load(open("config/look.json"))
    font = ImageFont.truetype("assets/fonts/Inter-Medium-flat.ttf", 20)
    ims = [Image.open(f).convert("RGB") for f, _ in pairs]
    fw, fh = ims[0].size
    rows = (len(ims) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * fw + (COLS + 1) * PAD, rows * (fh + LABEL + PAD) + PAD), look["palette"]["void"])
    d = ImageDraw.Draw(sheet)
    for k, (im, (_, cap)) in enumerate(zip(ims, pairs)):
        x, y = PAD + (k % COLS) * (fw + PAD), PAD + (k // COLS) * (fh + LABEL + PAD)
        d.text((x, y + 2), cap, fill=look["palette"]["paper"], font=font)
        sheet.paste(im.resize((fw, fh)), (x, y + LABEL))
    sheet.save(out, quality=92)


if __name__ == "__main__":
    main()
