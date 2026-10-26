"""C4 animatic (brief: "the whole camera move in grey-box at final timing, every anchor hit, low-res"): the full set,
every device keyed from the timing data (animate.py), the one continuous camera move (camera_path.py), rendered with
Eevee at low resolution and few samples.

Modes:
  --anchors   one still per shot anchor (N02..N40) -> <out>/anchor_<ID>.png, for the contact sheet
  --times     stills at the given song seconds -> <out>/t_<seconds>.png (review frames)
  default     every --step'th frame from --from to --to (song seconds; default the whole move, to N40's black)
              -> <out>/f_<frame>.png (frame numbers are the song's, at the video's fps)

Usage: blender -b --factory-startup --python scenes/blender/animatic.py -- --out DIR [--profile NAME] [--size W H]
       [--samples N] [--step K] [--from S] [--to S] [--resume] [--anchors | --times S ...]
--size and --samples override the profile's; with neither, 640x360 at 8 samples.
"""
import argparse
import json
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

PROFILES = json.loads((HERE.parents[1] / "config" / "render_profiles.json").read_text())


def build(size, samples, mb_steps=1, bake=True):
    """The whole animatic scene, ready to render; returns (scene, f_end). Also imported by scripts/qc_geometry.py.
    bake=False leaves the simulations unbaked (for tuning them)."""
    t_start = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = K.setup_render(bpy.context.scene, size[0], size[1], samples, mb_steps)
    scene.eevee.use_volumetric_shadows = True
    scene.eevee.volumetric_tile_size = "8"
    S = nursery.build(reveal=True)
    S["probe"] = nursery.crib_probe(S["crib"]["root"])
    births = animate.all_(S)
    f_end = A.frame(animate.OUT["black"])
    camera_path.build(K, bpy, 0, f_end)
    # The cutaway through the plinth (brief, N14-N15 and N19): while the eye passes the floor's layers (z -0.15..0.55),
    # the layers it would pass through are hidden (the nursery floor slab, the rug, the basement's ceiling), so the
    # frame opens from the nursery straight into the basement. The plinth is hollow and its sides stay, so nothing
    # outside it shows on the way (human, C4 review).
    CUT = ["plinth", "nursery.rug", "base.ceiling", "floor_gaps"]
    inside = [f for f in range(f_end + 1) if -0.15 <= camera_path.pose(f / A.FPS)[0].z <= 0.55]
    spans = []
    for f in inside:
        if spans and f == spans[-1][1] + 1:
            spans[-1][1] = f
        else:
            spans.append([f, f])
    for nm in CUT:
        o = bpy.data.objects[nm]
        pts = [(0, 0.0, "CONSTANT")]
        for f0, f1 in spans:
            pts += [(f0 - 1, 1.0, "CONSTANT"), (f1 + 2, 0.0, "CONSTANT")]
        A.write_keys(o, "hide_render", pts, interp="CONSTANT")
    print("cutaway frames:", [(a / A.FPS, b / A.FPS) for a, b in spans], flush=True)
    K.bloom(scene)
    K.rebind_drivers()
    K.refresh()
    scene.frame_start, scene.frame_end = 0, f_end
    # Bake the simulations (the quilt's cloth, from N38), so any frame renders right, in any order.
    if bake:
        t = time.time()
        with bpy.context.temp_override(scene=scene):
            bpy.ops.ptcache.bake_all(bake=True)
        print(f"baked the cloth in {time.time() - t:.0f} s", flush=True)
    print(f"built in {time.time() - t_start:.0f} s; {len(bpy.data.objects)} objects; stars born "
          f"{sum(b < 1e5 for b in births)}; frames 0..{f_end}", flush=True)
    bad = K.invalid_drivers()
    if bad:
        print("INVALID DRIVERS:", bad[:20], flush=True)
    return scene, f_end


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--profile", choices=[k for k in PROFILES if not k.startswith("_")],
                    help="size, samples and motion-blur steps from config/render_profiles.json")
    ap.add_argument("--size", nargs=2, type=int)
    ap.add_argument("--samples", type=int)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--from", dest="t0", type=float, default=0.0)
    ap.add_argument("--to", dest="t1", type=float, default=None)
    ap.add_argument("--anchors", action="store_true")
    ap.add_argument("--times", nargs="+", type=float)
    ap.add_argument("--resume", action="store_true",
                    help="keep frames already in --out (and claim each with a placeholder), so runs resume and share")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
    prof = PROFILES[args.profile] if args.profile else {"size": [640, 360], "samples": 8}
    scene, f_end = build(args.size or prof["size"], args.samples or prof["samples"], prof.get("motion_blur_steps", 1))
    black = animate.OUT["black"]

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    if args.times:
        for t in args.times:
            scene.frame_set(min(A.frame(t), f_end))
            scene.render.filepath = str(out / f"t_{t:07.2f}.png")
            bpy.ops.render.render(write_still=True)
            print("still", t, flush=True)
    elif args.anchors:
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
        scene.render.use_overwrite = not args.resume
        scene.render.use_placeholder = args.resume
        t = time.time()
        bpy.ops.render.render(animation=True)
        n = len(range(f0, f1 + 1, args.step))
        print(f"rendered {n} frames in {time.time() - t:.0f} s ({(time.time() - t) / max(n, 1):.2f} s/frame)", flush=True)
