"""C4 animatic (brief: "the whole camera move in grey-box at final timing, every anchor hit, low-res"): the full set,
every device keyed from the timing data (animate.py), the one continuous camera move (camera_path.py), rendered with
Eevee at low resolution and few samples.

Modes:
  --anchors   one still per shot anchor (N02..N40) -> <out>/anchor_<ID>.png, for the contact sheet
  default     every --step'th frame from --from to --to (song seconds; default the whole move, to N40's black)
              -> <out>/f_<frame>.png (frame numbers are the song's, at the video's fps)

Usage: blender -b --factory-startup --python scenes/blender/animatic.py -- --out DIR [--size W H] [--samples N]
       [--step K] [--from S] [--to S] [--anchors]
"""
import argparse
import sys
import time
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE / "sets"), str(HERE)]
import animate  # noqa: E402
import camera_path  # noqa: E402
import nursery  # noqa: E402
import sr_anim as A  # noqa: E402
import sr_kit as K  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--size", nargs=2, type=int, default=[640, 360])
ap.add_argument("--samples", type=int, default=8)
ap.add_argument("--step", type=int, default=1)
ap.add_argument("--from", dest="t0", type=float, default=0.0)
ap.add_argument("--to", dest="t1", type=float, default=None)
ap.add_argument("--anchors", action="store_true")
args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])

t_start = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = K.setup_render(bpy.context.scene, args.size[0], args.size[1], args.samples)
scene.eevee.use_volumetric_shadows = True
scene.eevee.volumetric_tile_size = "8"
S = nursery.build(reveal=True)
S["probe"] = nursery.crib_probe(S["crib"]["root"])
births = animate.all_(S)
black = animate.OUT["black"]
f_end = A.frame(black)
cam = camera_path.build(K, bpy, 0, f_end)
K.bloom(scene)
K.rebind_drivers()
K.refresh()
scene.frame_start, scene.frame_end = 0, f_end
print(f"built in {time.time() - t_start:.0f} s; {len(bpy.data.objects)} objects; stars born "
      f"{sum(b < 1e5 for b in births)}; frames 0..{f_end}", flush=True)
bad = K.invalid_drivers()
if bad:
    print("INVALID DRIVERS:", bad[:20], flush=True)

out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
scene.render.image_settings.file_format = "PNG"
if args.anchors:
    shots = [s for s in A.timing_map()["shots"] if s["t"] is not None and s["t"] <= black]
    for s in shots:
        f = min(A.frame(s["t"]) + 2, f_end)
        scene.frame_set(f)
        scene.render.filepath = str(out / f"anchor_{s['id']}.png")
        bpy.ops.render.render(write_still=True)
        print("anchor", s["id"], f, flush=True)
else:
    f0 = A.frame(args.t0)
    f1 = min(A.frame(args.t1), f_end) if args.t1 is not None else f_end
    scene.frame_start, scene.frame_end, scene.frame_step = f0, f1, args.step
    scene.render.filepath = str(out / "f_")
    t = time.time()
    bpy.ops.render.render(animation=True)
    n = len(range(f0, f1 + 1, args.step))
    print(f"rendered {n} frames in {time.time() - t:.0f} s ({(time.time() - t) / max(n, 1):.2f} s/frame)", flush=True)
