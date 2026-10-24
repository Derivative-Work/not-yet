"""C3 timing preview, as a score (human, C3: "an actual score would be even easier for me to read").

Ported from Sandbox Rhapsody. 1920x1080 at the video's fps, with the Suno mix. The current system of the score
(scripts/score_build.py, engraved by scripts/score_render.py) fills the middle; a cursor moves through it on the
beat grid, and each note lights while it sounds, so held notes and note-offs are visible. Header: section,
bar.beat (a bar that is not 3 beats is marked), tempo, shot ID (flashes at its anchor), beat square (bright on
downbeats), and the proposed outro edit. Footer: the line being sung, words lighting as they start.

Score position <-> song time: Verovio's timemap gives each note's on/off in quarters from the start (the score has
one quarter per beat and starts at beat 0), and the beat grid (timing/timing_map.json) turns quarters into seconds.

Usage: .venv/bin/python -I scripts/c3_score_preview.py [start_s end_s]  ->  renders/c3/c3_score_preview.mp4
"""
import io
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_render  # noqa: E402

TM = json.loads(Path("timing/timing_map.json").read_text())
P = json.loads(Path("config/look.json").read_text())["palette"]
FPS, W, H = TM["fps"], 1920, 1080
BEATS = np.array(TM["beats"])
SCORE_W, SCORE_TOP = 1880, 96
AUDIO = "audio/track/Sleep, Little Secret.wav"
FONT, MONO = "assets/fonts/Inter[opsz,wght].ttf", "assets/fonts/JetBrainsMono[wght].ttf"
SVGNS = "{http://www.w3.org/2000/svg}"
HI = "standby"  # cursor and lit notes: the preview's highlight colour


def rgb(role, a=255):
    h = P[role].lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def qpos(t):
    i = int(np.clip(np.searchsorted(BEATS, t) - 1, 0, len(BEATS) - 2))
    return i + (t - BEATS[i]) / (BEATS[i + 1] - BEATS[i])


def page_geometry(svg):
    """Pixel positions of every note and rest head on a page rendered SCORE_W wide: {id: (x, y)}."""
    root = ET.fromstring(svg)
    outer_w = float(root.get("viewBox").split()[2])
    inner = root.find(f"{SVGNS}svg")
    inner_w = float(inner.get("viewBox").split()[2])
    margin = inner.find(f".//{SVGNS}g[@class='page-margin']")
    mx, my = (float(v) for v in re.findall(r"[-\d.]+", margin.get("transform"))[:2])
    k = outer_w / inner_w * SCORE_W / outer_w
    pos = {}
    for g in inner.iter(f"{SVGNS}g"):
        cls = g.get("class") or ""
        if cls not in ("note", "rest"):
            continue
        use = next((u for u in g.iter(f"{SVGNS}use")), None)
        if use is None:
            continue
        x, y = (float(v) for v in re.findall(r"[-\d.]+", use.get("transform"))[:2])
        pos[g.get("id")] = ((x + mx + 90) * k, (y + my) * k)  # +90 inner units: notehead centre, not its left edge
    return pos


def main():
    t0, t1 = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) >= 3 else (0.0, TM["duration_s"])
    out = Path("renders/c3") / ("c3_score_preview.mp4" if len(sys.argv) < 3 else f"c3_score_preview_{t0:.0f}-{t1:.0f}.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    tk = score_render.toolkit()
    on_q, off_q = {}, {}
    for e in tk.renderToTimemap({"includeRests": True}):
        for i in e.get("on", []):
            on_q[i] = e["qstamp"]
        for i in e.get("off", []):
            off_q[i] = e["qstamp"]
    pages = []
    for pg in range(1, tk.getPageCount() + 1):
        svg = tk.renderToSVG(pg)
        pos = page_geometry(svg)
        png = cairosvg.svg2png(bytestring=svg.encode(), output_width=SCORE_W, background_color="#f6f3ec")
        img = Image.open(io.BytesIO(png)).convert("RGB")
        notes = [(i, xy, on_q[i], off_q.get(i, on_q[i])) for i, xy in pos.items() if i in on_q]
        # Cursor track: one x per onset time on this page (the leftmost head at that onset).
        track = {}
        for i, (x, y), q0, _ in notes:
            track[q0] = min(track.get(q0, 1e9), x)
        qs = np.array(sorted(track))
        pages.append({"img": img, "notes": notes, "q": qs, "x": np.array([track[q] for q in qs]),
                      "q0": float(qs.min()), "rests": {i for i in pos if i not in on_q}})
    starts = np.array([p["q0"] for p in pages])
    fonts = {"big": ImageFont.truetype(MONO, 30), "small": ImageFont.truetype(MONO, 20),
             "cap": ImageFont.truetype(FONT, 44), "role": ImageFont.truetype(FONT, 26)}
    shots = [s for s in TM["shots"] if s["t"] is not None]
    down = set(TM["downbeat_beats"])
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", AUDIO, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-shortest", str(out)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(int(round(t0 * FPS)), int(round(t1 * FPS))):
        t = f / FPS
        q = qpos(t)
        pg = pages[int(np.clip(np.searchsorted(starts, q + 1e-9) - 1, 0, len(pages) - 1))]
        frame = Image.new("RGB", (W, H), rgb("void")[:3])
        frame.paste(pg["img"], ((W - SCORE_W) // 2, SCORE_TOP))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        ox = (W - SCORE_W) // 2
        for _, (x, y), q0, q1 in pg["notes"]:
            if q0 <= q < max(q1, q0 + 0.25):
                d.ellipse([ox + x - 13, SCORE_TOP + y - 13, ox + x + 13, SCORE_TOP + y + 13], fill=rgb(HI, 120),
                          outline=rgb(HI, 255), width=2)
        if len(pg["q"]) > 1:
            cx = float(np.interp(q, pg["q"], pg["x"]))
            d.line([(ox + cx, SCORE_TOP + 6), (ox + cx, SCORE_TOP + pg["img"].height - 6)], fill=rgb(HI, 200),
                   width=3)
        frame.paste(ov, (0, 0), ov)
        dd = ImageDraw.Draw(frame)
        sec = next(s for s in reversed(TM["sections"]) if s["start"] <= t + 1e-6)
        bar = next((b for b in reversed(TM["bars"]) if b["start"] <= t + 1e-6), TM["bars"][0])
        bnum = int(np.searchsorted(BEATS, t + 1e-6)) - 1
        dd.text((24, 18), sec["name"], font=fonts["big"], fill=rgb("paper")[:3])
        odd = f"   ({bar['beats']}-beat bar)" if bar["beats"] != 3 else ""
        dd.text((24, 58), f"bar {bar['n']}.{bnum - bar['beat'] + 1}{odd}   {bar['bpm'] or 0:.0f} bpm   {t:6.2f} s",
                font=fonts["small"], fill=rgb("tungsten")[:3] if odd else rgb("paper", 180)[:3])
        shot = next((s for s in reversed(shots) if s["t"] <= t + 1e-6), shots[0])
        flash = 0 <= t - shot["t"] < 0.25
        tag = shot["id"] + (" (provisional)" if shot.get("provisional") else "")
        dd.rectangle([W - 470, 16, W - 90, 66], fill=rgb(HI)[:3] if flash else rgb("void")[:3], outline=rgb(HI)[:3],
                     width=2)
        dd.text((W - 455, 22), tag, font=fonts["big"], fill=rgb("void")[:3] if flash else rgb(HI)[:3])
        if bnum >= 0 and t - BEATS[bnum] < 0.1:
            dd.rectangle([W - 70, 16, W - 20, 66], fill=rgb("comfort" if bnum in down else "steel")[:3])
        o = TM["outro"]
        if o["pen_scratch"] <= t < o["black"]:
            dd.text((W // 2 - 260, 30), "PROPOSED EDIT: music cut, pen scratch", font=fonts["small"], fill=rgb("tungsten")[:3])
        elif o["black"] <= t < o["crt"]:
            dd.text((W // 2 - 90, 30), "BLACK (N40)", font=fonts["small"], fill=rgb("tungsten")[:3])
        cur = [ln for ln in TM["lines"] if ln["start"] - 1.2 <= t <= ln["end"] + 0.5][-2:]
        y = H - 70 - 58 * (len(cur) - 1)
        for ln in cur:
            x = 40
            for w in ln["words"]:
                dd.text((x, y), w["w"], font=fonts["cap"], fill=rgb("comfort")[:3] if t >= w["start"] else rgb("steel")[:3])
                x += dd.textlength(w["w"] + " ", font=fonts["cap"])
            y += 58
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    ff.wait()
    print(out)


if __name__ == "__main__":
    main()
