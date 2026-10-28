"""The video's thumbnail (human, 2026-10-28: "the probe at the blanket reveal, with text that hints at the video"). It
replaces the N28 frame, which the brief asked for and which underperformed on YouTube. Like Sandbox Rhapsody's
thumbnail, it's a treated frame with text set over it; option B of three (human, R1).

The frame is N38 at frame 6662 (222.07 s): the blanket is mid-fall and arcs over the probe like a hood, the lens ring
is lit, and both arms show. It's cropped 3360 x 1890 from (0, 40) at 4K, which puts the probe right of centre and
leaves room for the text on the left. A vignette centred on the probe (down to 40% at the edges) turns the bright
room toward night, and the probe's green light gets a soft glow (screen blend). The headline is set in Inter Black
and the line under it in Oooh Baby (the caption face), each in white with a blurred drop shadow.

Usage: .venv/bin/python -I scripts/thumbnail.py  ->  deliverables/not_yet_thumbnail.jpg
"""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FRAME = 6662                 # N38: the blanket falling off the probe
CROP = (0, 40, 3360)         # x0, y0, width at 3840x2160; height is width * 9/16
CENTRE = (0.57, 0.5)         # the vignette's centre, on the probe (fraction of the crop)
GREEN = np.array([0.25, 1.0, 0.6], np.float32)
FONTS = ROOT / "assets/fonts"
TEXT = [  # font, size, weight, text, position (1920x1080), colour
    ("Inter[opsz,wght].ttf", 128, 900, "TOO DANGEROUS", (64, 46), (255, 250, 240)),
    ("Inter[opsz,wght].ttf", 128, 900, "TO RELEASE", (64, 182), (255, 250, 240)),
    ("OoohBaby-Regular.ttf", 112, None, "so we sang it to sleep", (70, 330), (255, 245, 225)),
]
OUT = ROOT / "deliverables/not_yet_thumbnail.jpg"


def plate():
    a = cv2.imread(str(ROOT / f"renders/c5/frames/f_{FRAME:04d}.png"))[..., ::-1].astype(np.float32) / 255
    x0, y0, w = CROP
    a = a[y0:y0 + w * 9 // 16, x0:x0 + w]
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - CENTRE[0] * w) / w) ** 2 + ((yy - CENTRE[1] * h) / h) ** 2)
    v = np.clip(1.05 - 1.5 * r, 0.4, 1.0)
    g = a[..., 1] - np.maximum(a[..., 0], a[..., 2])  # how green: the probe's light
    glow = cv2.GaussianBlur(np.clip(g * 4, 0, 1), (0, 0), 40)[..., None] * GREEN
    out = a * v[..., None] * 0.92
    out = 1 - (1 - out) * (1 - 0.55 * glow)  # screen
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).resize((1920, 1080), Image.LANCZOS)


def font(name, size, wght):
    f = ImageFont.truetype(str(FONTS / name), size)
    if wght:
        f.set_variation_by_axes([32, wght])  # Inter: opsz, wght
    return f


def shadowed(img, xy, txt, f, fill):
    sh = Image.new("L", img.size, 0)
    ImageDraw.Draw(sh).text((xy[0], xy[1] + 6), txt, font=f, fill=235)
    img.paste((0, 0, 0), mask=sh.filter(ImageFilter.GaussianBlur(16)))
    ImageDraw.Draw(img).text(xy, txt, font=f, fill=fill)


def main():
    if OUT.exists():
        raise SystemExit(f"{OUT} exists: archive it first (never overwrite an asset)")
    img = plate()
    for name, size, wght, txt, xy, fill in TEXT:
        shadowed(img, xy, txt, font(name, size, wght), fill)
    img.save(OUT, quality=92)
    print(OUT.relative_to(ROOT), "(1920x1080)")


if __name__ == "__main__":
    main()
