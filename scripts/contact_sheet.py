"""Contact sheet of shot-anchor stills (C4 animatic, C5 renders): a grid with each shot's ID and its lyric line.

Usage: .venv/bin/python -I scripts/contact_sheet.py <dir with anchor_<ID>.png> <out.jpg> [columns]
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PAD, LABEL = 10, 44


def main():
    src, out = Path(sys.argv[1]), sys.argv[2]
    cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    tm = json.loads(Path("timing/timing_map.json").read_text())
    shots = [s for s in tm["shots"] if (src / f"anchor_{s['id']}.png").exists()]
    pal = json.loads(Path("config/look.json").read_text())["palette"]
    f_id = ImageFont.truetype("assets/fonts/JetBrainsMono-SemiBold-flat.ttf", 16)
    f_ln = ImageFont.truetype("assets/fonts/Inter-Medium-flat.ttf", 13)
    im0 = Image.open(src / f"anchor_{shots[0]['id']}.png")
    w, h = im0.size
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (w + PAD) + PAD, rows * (h + LABEL + PAD) + PAD), pal["void"])
    d = ImageDraw.Draw(sheet)
    for k, s in enumerate(shots):
        x, y = PAD + (k % cols) * (w + PAD), PAD + (k // cols) * (h + LABEL + PAD)
        sheet.paste(Image.open(src / f"anchor_{s['id']}.png").convert("RGB"), (x, y))
        d.text((x, y + h + 4), f"{s['id']}  {s['t']:.1f} s", font=f_id, fill=pal["standby"])
        line = s.get("line", s.get("anchor", ""))
        d.text((x, y + h + 24), line[:78], font=f_ln, fill=pal["paper"])
    sheet.save(out, quality=88)
    print(out, len(shots), "stills")


if __name__ == "__main__":
    main()
