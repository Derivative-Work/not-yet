"""Assemble the C4 animatic: rendered frames + the track (its post-filtered master when config/audio.json has one) with the pen scratch on top (config/audio.json) + burned-in
review captions (ASS via libass): each lyric line with its words lighting as sung (karaoke timing from the aligned
words), the shot ID top right, the N02 label, and placeholders for the 2D outro shots built at C5 (N41 CRT line,
N42 fact card, N43 bookend, N44 end card). The picture fades up from black over N02's first 2 s, cuts to black at N40,
and stays black under the music box's tail.

Frames may be every k'th frame (blender --step k): they play at fps / k, so timing is exact and motion is coarser.

Usage: .venv/bin/python -I scripts/animatic_assemble.py <frames dir> <step> <out.mp4>
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TM = json.loads(Path("timing/timing_map.json").read_text())
AUD = json.loads(Path("config/audio.json").read_text())
FPS = TM["fps"]
OUT = TM["outro"]


def ts(t):
    h, r = divmod(max(t, 0.0), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ass(w, h):
    L = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}", "",
         "[V4+ Styles]",
         "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
         "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
         "MarginR, MarginV, Encoding",
         # Karaoke: SecondaryColour before a word is sung, PrimaryColour after (cream, the comfort role).
         "Style: Cap,Inter,22,&H00B0E3FF,&H80B0B0B0,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,1.2,0,2,20,20,18,1",
         "Style: Id,JetBrains Mono,14,&H009AE35F,&H009AE35F,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,1,0,9,10,10,8,1",
         "Style: Card,Inter,20,&H00F1F4EE,&H00F1F4EE,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,30,30,30,1",
         "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for ln in TM["lines"]:
        a, b = ln["start"] - 0.4, ln["end"] + 0.6
        parts, t = [], a
        for wd in ln["words"]:
            parts.append(f"{{\\k{max(0, int(round((wd['start'] - t) * 100)))}}}")
            parts.append(wd["w"] + " ")
            t = wd["start"]
        L.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{''.join(parts)}")
    shots = [s for s in TM["shots"] if s["t"] is not None]
    for k, s in enumerate(shots):
        end = shots[k + 1]["t"] if k + 1 < len(shots) else s["t"] + 6
        L.append(f"Dialogue: 1,{ts(s['t'])},{ts(end)},Id,,0,0,0,,{s['id']}")
    L.append(f"Dialogue: 2,{ts(1.0)},{ts(8.0)},Card,,0,0,0,,{{\\an5\\fad(800,800)}}AI-generated satire")
    L.append(f"Dialogue: 2,{ts(OUT['crt'])},{ts(OUT['fact_card'])},Card,,0,0,0,,N41: CRT line opens (2D, C5)")
    L.append(f"Dialogue: 2,{ts(OUT['fact_card'])},{ts(OUT['fact_card'] + 4)},Card,,0,0,0,,N42-N44: fact card, "
             f"audit-log bookend, end card (2D, C5)")
    return "\n".join(L) + "\n"


def main():
    frames, step, out = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    pngs = sorted(frames.glob("f_*.png"))
    from PIL import Image
    w, h = Image.open(pngs[0]).size
    end = OUT["fact_card"] + 4.0
    with tempfile.TemporaryDirectory() as td:
        sub = Path(td) / "c4.ass"
        sub.write_text(ass(w, h))
        sfx = AUD["sfx"][0]
        ms = int(round(sfx["at_s"] * 1000))
        fade_out = OUT["black"]
        vf = (f"fade=t=in:st=0:d=2,trim=end={fade_out},setpts=PTS-STARTPTS,tpad=stop_mode=add:stop_duration="
              f"{end - fade_out}:color=black,ass={sub}:fontsdir=assets/fonts")
        cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", f"{FPS / step}", "-pattern_type", "glob",
               "-i", str(frames / "f_*.png"), "-i", AUD["master"] or AUD["track"], "-i", sfx["file"],
               "-filter_complex",
               f"[0:v]{vf}[v];[2:a]aresample=48000,volume={sfx['gain_db']}dB,pan=stereo|c0=0.95*c0|c1=c0,"
               f"adelay={ms}|{ms}[s];[1:a][s]amix=inputs=2:duration=first:normalize=0,apad[a]",
               "-map", "[v]", "-map", "[a]", "-t", f"{end}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
               "-pix_fmt", "yuv420p", "-r", f"{FPS}", "-c:a", "aac", "-b:a", "160k", out]
        subprocess.run(cmd, check=True)
    print(out)


if __name__ == "__main__":
    main()
