"""C6 final assembly: the main video, the two vertical shorts and the thumbnail, from the rendered frames, the overlay
tracks (overlays/render.mjs) and the audio (config/audio.json: the post-filtered master and the pen scratch).

- main (3840x2160): the frames fade up from black over the first 2 s and cut to black at N40 (as the animatic); black
  under the music box's tail and the cards; the overlay (captions, N41 to N44, the human's note) over everything.
  Audio: the master with the pen scratch on top, then the instrumental card bounce (config/audio.json "cards").
- short:<id> (1080x1920): the short's span (overlays/cues.json "shorts"), a 9:16 window of the frame whose centre
  follows config/reframe.json, scaled; its overlay; the master over the span. The windows short fades picture and
  music out together over its last 2.5 s (brief); both fade up over 0.4 s.
- thumbnail: the N29 frame (brief) at config/release.json thumbnail_t, 1920x1080 JPEG.
Encoded with NVENC HEVC (BT.709, tagged), AAC 320k.

Usage: .venv/bin/python -I scripts/assemble.py main|short:<id>|thumbnail [--frames DIR] [--overlay FILE] [--out FILE]
  --frames: default renders/c5/frames (a draft run can point at renders/c4/frames_v11: 720p frames scale up)
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TM = json.loads((ROOT / "timing/timing_map.json").read_text())
CUES = json.loads((ROOT / "overlays/cues.json").read_text())
AUD = json.loads((ROOT / "config/audio.json").read_text())
REFRAME = json.loads((ROOT / "config/reframe.json").read_text())
FPS = TM["fps"]
BLACK = TM["outro"]["black"]
SHOT = {s["id"]: s["t"] for s in TM["shots"]}
ENC = ["-c:v", "hevc_nvenc", "-preset", "p7", "-tune", "hq", "-rc", "vbr", "-b:v", "{br}", "-maxrate", "{mr}",
       "-bufsize", "{mr}", "-profile:v", "main", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
       "-color_trc", "bt709", "-colorspace", "bt709", "-tag:v", "hvc1", "-c:a", "aac", "-b:a", "320k",
       "-movflags", "+faststart",
       # The PNGs carry an sRGB tag that reached the stream's transfer (iec61966-2-1); set BT.709 in the bitstream.
       "-bsf:v", "hevc_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1"]
# RGB to YUV: format=yuv420p converts with the BT.709 matrix the output is tagged with (checked: Y within 0.1 of the
# BT.709 value from the source PNG; an explicit scale=out_color_matrix=bt709 here came out 1.6 darker).
YUV = "format=yuv420p"


def enc(br, mr):
    return [a.format(br=br, mr=mr) for a in ENC]


def audio_graph(i_master, i_sfx, t0, dur, fade_out=0.0, sound=None):
    """The master with the pen scratch mixed on top, from song t0 for dur seconds, padded with silence; with sound,
    only its first sound seconds (fading out over fade_out before then), silence after."""
    sound = dur if sound is None else sound
    sfx = AUD["sfx"][0]
    ms = int(round((sfx["at_s"] - t0) * 1000))
    g = (f"[{i_master}:a]atrim=start={t0},asetpts=PTS-STARTPTS,aresample=48000[m];")
    if 0 <= ms < dur * 1000:
        g += (f"[{i_sfx}:a]aresample=48000,volume={sfx['gain_db']}dB,pan=stereo|c0=0.95*c0|c1=c0,"
              f"adelay={ms}|{ms}[s];[m][s]amix=inputs=2:duration=first:normalize=0[mx];")
    else:
        g += "[m]anull[mx];"
    g += f"[mx]apad,atrim=end={sound}"
    if fade_out:
        g += f",afade=t=out:st={sound - fade_out}:d={fade_out}"
    return g + f",apad,atrim=end={dur}[a]"


def piecewise(keys, t0):
    """An ffmpeg expression in t (seconds from the short's start) for keys [[song s, value], ...]: linear, held."""
    keys = [(s - t0, v) for s, v in keys]
    expr = f"{keys[-1][1]}"
    for (a, va), (b, vb) in reversed(list(zip(keys, keys[1:]))):
        expr = f"if(lt(t,{b}),{va}+({vb}-{va})*(t-{a})/{b - a},{expr})"
    return f"if(lt(t,{keys[0][0]}),{keys[0][1]},{expr})"


def frames_input(frames, start=0):
    return ["-framerate", str(FPS), "-start_number", str(start), "-i", str(Path(frames) / "f_%04d.png")]


def main_video(a):
    end = CUES["end"]
    ov = a.overlay or "renders/overlays/overlay_main.mkv"
    out = a.out or "deliverables/not_yet_main.mp4"
    vf = (f"[0:v]scale=3840:2160:flags=lanczos,fade=t=in:st=0:d=2,trim=end={BLACK},setpts=PTS-STARTPTS,"
          f"tpad=stop_mode=add:stop_duration={end - BLACK}:color=black,format=rgba[bg];"
          f"[1:v]format=rgba[ov];[bg][ov]overlay=eof_action=pass,{YUV}[v];")
    # Under the cards, the instrumental bounce (config/audio.json "cards"), mixed in at its video time.
    cards = AUD["cards"]
    ms = int(round(cards["at_s"] * 1000))
    ag = audio_graph(2, 3, 0.0, end).replace("[a]", "[song]")
    ag += (f";[4:a]aresample=48000,adelay={ms}|{ms},apad,atrim=end={end}[cards];"
           f"[song][cards]amix=inputs=2:duration=first:normalize=0[a]")
    cmd = (["ffmpeg", "-v", "error", "-y"] + frames_input(a.frames) + ["-i", ov, "-i", AUD["master"], "-i",
           AUD["sfx"][0]["file"], "-i", cards["file"], "-filter_complex", vf + ag, "-map", "[v]", "-map", "[a]",
           "-t", f"{end}", "-r", str(FPS)] + enc("70M", "120M") + [out])
    run(cmd, out)


def short_video(a, sid):
    sh = next(s for s in CUES["shorts"] if s["id"] == sid)
    f0 = round(sh["from"] * FPS)  # start on a frame: picture and audio from the same instant
    t0, dur = f0 / FPS, sh["to"] - f0 / FPS
    content = sh.get("content_to", sh["to"]) - t0  # then black and silence under the human's note
    ov = a.overlay or f"renders/overlays/overlay_short_{sid}.mkv"
    out = a.out or f"deliverables/not_yet_short_{sid}.mp4"
    fade = 2.5 if sid == "windows" else 0.0
    vis = max(0.0, min(content, BLACK - t0))  # picture until N40's black or the content's end, black after
    cx = piecewise(REFRAME[sid], t0)
    vf = (f"[0:v]trim=end={vis},setpts=PTS-STARTPTS,scale=-2:2160:flags=lanczos,"
          f"crop=w=1215:h=2160:x='max(0,min(iw-1215,({cx})*iw-607.5))':y=0,scale=1080:1920:flags=lanczos,"
          f"tpad=stop_mode=add:stop_duration={dur - vis + 0.1}:color=black,fade=t=in:st=0:d=0.4")
    if fade:
        vf += f",fade=t=out:st={content - fade}:d={fade}"
    vf += f",format=rgba[bg];[1:v]format=rgba[ov];[bg][ov]overlay=eof_action=pass,{YUV}[v];"
    cmd = (["ffmpeg", "-v", "error", "-y"] + frames_input(a.frames, f0) + ["-i", ov, "-i", AUD["master"],
           "-i", AUD["sfx"][0]["file"], "-filter_complex", vf + audio_graph(2, 3, t0, dur, fade_out=fade, sound=content),
           "-map", "[v]", "-map", "[a]", "-t", f"{dur}", "-r", str(FPS)] + enc("30M", "50M") + [out])
    run(cmd, out)


def thumbnail(a):
    f = round(json.loads((ROOT / "config/release.json").read_text())["thumbnail_t"] * FPS)
    out = a.out or "deliverables/not_yet_thumbnail.jpg"
    src = Path(a.frames) / f"f_{f:04d}.png"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", "scale=1920:1080:flags=lanczos", "-q:v", "2", out], out)


def run(cmd, out):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    if Path(out).exists():
        raise SystemExit(f"{out} exists: archive it first (never overwrite an asset)")
    subprocess.run(cmd, check=True, cwd=ROOT)
    print(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what")
    ap.add_argument("--frames", default="renders/c5/frames")
    ap.add_argument("--overlay")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.what == "main":
        main_video(a)
    elif a.what.startswith("short:"):
        short_video(a, a.what[6:])
    elif a.what == "thumbnail":
        thumbnail(a)
    else:
        raise SystemExit(f"unknown target {a.what}")


if __name__ == "__main__":
    main()
