"""C1 review sheet: the test frames (wide, close, and any more), side by side, above a strip of the six colour-role swatches with their hex values.

There are no reference videos in this project (the look follows the brief and Sandbox Rhapsody's spec), so unlike
Sandbox Rhapsody's sheet this one holds only this video's own frames.
Usage: .venv/bin/python -I scripts/c1_sheet.py <title> <frame.png>... <out.jpg>
"""
import json
import sys

from PIL import Image, ImageDraw, ImageFont

PAD, LABEL = 16, 30
ROLES = [("house", "The house and its glass"), ("comfort", "Comfort"), ("standby", "The crib probe"),
         ("amber", "Another house's child"), ("tungsten", "The maintainer"), ("commerce", "Commerce")]


def main():
    title, frames, out = sys.argv[1], sys.argv[2:-1], sys.argv[-1]
    look = json.load(open("config/look.json"))
    font = ImageFont.truetype("assets/fonts/Inter-Medium-flat.ttf", 20)
    mono = ImageFont.truetype("assets/fonts/JetBrainsMono-SemiBold-flat.ttf", 18)
    ims = [Image.open(f).convert("RGB") for f in frames]
    fw, fh = ims[0].size
    if len(ims) > 2:  # keep the sheet about two frames wide
        fw, fh = fw * 2 // len(ims), fh * 2 // len(ims)
        ims = [im.resize((fw, fh), Image.LANCZOS) for im in ims]
    sw_h = 120
    W = len(ims) * fw + (len(ims) + 1) * PAD
    H = PAD + LABEL + fh + PAD + LABEL + sw_h + PAD
    sheet = Image.new("RGB", (W, H), look["palette"]["void"])
    d = ImageDraw.Draw(sheet)
    d.text((PAD, PAD + 2), title, fill=look["palette"]["paper"], font=font)
    for k, im in enumerate(ims):
        sheet.paste(im, (PAD + k * (fw + PAD), PAD + LABEL))
    y = PAD + LABEL + fh + PAD
    d.text((PAD, y + 2), "Colour roles (config/look.json)", fill=look["palette"]["paper"], font=font)
    y += LABEL
    cw = (W - PAD * (len(ROLES) + 1)) // len(ROLES)
    for k, (key, label) in enumerate(ROLES):
        x = PAD + k * (cw + PAD)
        hexv = look["palette"][key]
        d.rectangle((x, y, x + cw, y + 64), fill=hexv)
        d.text((x, y + 70), label, fill=look["palette"]["paper"], font=font)
        d.text((x, y + 94), f"{key} {hexv}", fill="#8a93a3", font=mono)
    sheet.save(out, quality=92)


if __name__ == "__main__":
    main()
