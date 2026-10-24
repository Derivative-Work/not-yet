"""C3 timing preview: everything in timing/ drawn against the master audio, for checking sync by ear.

960x540 at the video's fps. A lane per animation-driving track scrolls right to left past a "now" line in the
centre (3 s visible each side): a dot per note, flashing as it crosses. Top: section, bar.beat (3/4; a bar that is not
3 beats is marked), shot ID (it flashes at its anchor), the beat square (downbeats bright). Bottom: the line being
sung, each word lighting at its aligned start; a strip for the vocal envelope (breaths will brighten the projector).
Ported from Sandbox Rhapsody; this video's colour roles, no opera roles.

Usage: .venv/bin/python -I scripts/c3_preview.py [start_s end_s]  ->  renders/c3/c3_preview.mp4
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

TM = json.loads(Path("timing/timing_map.json").read_text())
LOOK = json.loads(Path("config/look.json").read_text())
P = LOOK["palette"]
FPS = TM["fps"]
W, H = 960, 540
SPAN = 3.0  # seconds visible each side of the now line
NOW_X = W // 2
OUT = Path("renders/c3")
FONT = "assets/fonts/Inter[opsz,wght].ttf"
MONO = "assets/fonts/JetBrainsMono[wght].ttf"
AUDIO = "audio/track/Sleep, Little Secret.wav"  # the Suno mix (the mastered track comes later)

LANES = [  # (label, file, colour role)
    ("music box", "timing/events/keyboard.json", "comfort"),
    ("celesta", "timing/events/percussion.json", "frost"),
    ("strings", "timing/events/strings.json", "felt_blue"),
    ("e.piano/pad", "timing/events/guitar.json", "rim"),
    ("bass", "timing/events/bass.json", "tungsten"),
    ("words", "timing/timing_map.json:words", "paper"),
]
VOCAL_ENV = "timing/envelopes/vocals.npy"


def rgb(role, k=1.0):
    h = P[role].lstrip("#")
    return tuple(int(int(h[i:i + 2], 16) * k) for i in (0, 2, 4))


def load_lane(spec):
    if spec.endswith(":words"):
        return np.array(sorted(w["start"] for ln in TM["lines"] for w in ln["words"]))
    path, _, pitches = spec.partition(":")
    ev = json.loads(Path(path).read_text())["events"]
    keep = set(int(p) for p in pitches.split(",")) if pitches else None
    return np.array(sorted(e["t"] for e in ev if keep is None or e.get("pitch") in keep))


def main():
    t0, t1 = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) >= 3 else (0.0, TM["duration_s"])
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / ("c3_preview.mp4" if len(sys.argv) < 3 else f"c3_preview_{t0:.0f}-{t1:.0f}.mp4")
    lanes = [(lab, load_lane(f), col) for lab, f, col in LANES]
    beats = np.array(TM["beats"])
    down = set(TM["downbeat_beats"])
    bars = TM["bars"]
    shots = [s for s in TM["shots"] if s["t"] is not None]
    env = np.load(VOCAL_ENV)
    lines = TM["lines"]
    f_lab, f_cap, f_role, f_big = (ImageFont.truetype(MONO, 13), ImageFont.truetype(FONT, 26),
                                   ImageFont.truetype(FONT, 15), ImageFont.truetype(MONO, 18))
    top, lane_h = 84, 40
    bg = Image.new("RGB", (W, H), rgb("void"))
    d0 = ImageDraw.Draw(bg)
    for k, (lab, _, col) in enumerate(lanes):
        y = top + k * lane_h
        d0.text((8, y + 3), lab, font=f_lab, fill=rgb(col, 0.8))
        d0.line([(120, y + lane_h // 2), (W - 8, y + lane_h // 2)], fill=rgb("horizon"), width=1)
    d0.line([(NOW_X, top - 6), (NOW_X, top + len(lanes) * lane_h + 4)], fill=rgb("paper", 0.6), width=1)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", AUDIO, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-shortest", str(out)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(int(round(t0 * FPS)), int(round(t1 * FPS))):
        t = f / FPS
        im = bg.copy()
        d = ImageDraw.Draw(im)
        px = lambda x: NOW_X + (x - t) / SPAN * (NOW_X - 124)  # noqa: E731
        # Beat ticks across the lanes, downbeats brighter.
        bi = np.searchsorted(beats, [t - SPAN, t + SPAN])
        for i in range(bi[0], bi[1]):
            x = px(beats[i])
            d.line([(x, top - 4), (x, top + len(lanes) * lane_h)], fill=rgb("horizon", 1.6 if i in down else 0.9))
        for k, (_, ev, col) in enumerate(lanes):
            y = top + k * lane_h + lane_h // 2
            a, b = np.searchsorted(ev, [t - SPAN, t + SPAN])
            for e in ev[a:b]:
                x = px(e)
                age = t - e
                hot = 0 <= age < 0.12
                r = 7 if hot else 3
                d.ellipse([x - r, y - r, x + r, y + r], fill=rgb(col, 1.0 if hot or age < 0 else 0.45))
        # Header: section, bar.beat, shot, beat square.
        sec = next(s for s in reversed(TM["sections"]) if s["start"] <= t + 1e-6)
        bar = next((b for b in reversed(bars) if b["start"] <= t + 1e-6), bars[0])
        bnum = int(np.searchsorted(beats, t + 1e-6)) - 1
        beat_in_bar = bnum - bar["beat"] + 1
        shot = next((s for s in reversed(shots) if s["t"] <= t + 1e-6), shots[0])
        d.text((10, 10), f"{sec['name']}", font=f_big, fill=rgb("paper"))
        odd = f"  ({bar['beats']}-beat bar)" if bar["beats"] != 3 else ""
        d.text((10, 34), f"bar {bar['n']}.{beat_in_bar}{odd}  {bar['bpm'] or 0:.0f} bpm  t={t:7.2f}s  f={f}", font=f_lab,
               fill=rgb("tungsten") if odd else rgb("paper", 0.7))
        flash = 0 <= t - shot["t"] < 0.25
        tag = shot["id"] + (" (prov.)" if shot.get("provisional") else "")
        d.rectangle([W - 250, 8, W - 60, 40], fill=rgb("standby") if flash else rgb("void"), outline=rgb("standby"))
        d.text((W - 242, 14), tag, font=f_big, fill=rgb("void") if flash else rgb("standby"))
        if bnum >= 0 and t - beats[bnum] < 0.1:
            d.rectangle([W - 48, 8, W - 16, 40], fill=rgb("comfort") if bnum in down else rgb("steel"))
        # Vocal envelope strip (breaths and phrases), under the lanes.
        ey = top + len(lanes) * lane_h + 14
        v = float(env[min(f, len(env) - 1)])
        d.rectangle([124, ey, 124 + int(v * (W - 140)), ey + 6], fill=rgb("comfort", 0.8))
        d.text((8, ey - 4), "vocal env", font=f_lab, fill=rgb("comfort", 0.7))
        # The provisional outro edit: the music cut at the pen scratch.
        o = TM["outro"]
        if o["pen_scratch"] <= t < o["black"]:
            d.text((W // 2 - 150, 52), "PROPOSED: music cut, pen scratch", font=f_lab, fill=rgb("tungsten"))
        elif o["black"] <= t < o["crt"]:
            d.text((W // 2 - 60, 52), "BLACK (N40)", font=f_lab, fill=rgb("tungsten"))
        # Caption: the line being sung (or the next within 1.5 s), words lighting at their start.
        cur = [ln for ln in lines if ln["start"] - 1.5 <= t <= ln["end"] + 0.6]
        y = H - 40 - 34 * (len(cur) - 1)
        for ln in cur[-3:]:
            x = 40
            for w in ln["words"]:
                lit = t >= w["start"]
                d.text((x, y), w["w"], font=f_cap, fill=rgb("comfort") if lit else rgb("paper", 0.45))
                x += d.textlength(w["w"] + " ", font=f_cap)
            y += 34
        ff.stdin.write(im.tobytes())
    ff.stdin.close()
    ff.wait()
    print(out)


if __name__ == "__main__":
    main()
