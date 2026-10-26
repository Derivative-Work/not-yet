"""C4 animatic (brief: "the whole camera move in grey-box at final timing, every anchor hit, low-res"): the full set,
every device keyed from the timing data (animate.py), the one continuous camera move (camera_path.py), rendered with
Eevee at low resolution and few samples.

Modes:
  --anchors   one still per shot anchor (N02..N40) -> <out>/anchor_<ID>.png, for the contact sheet
  --times     stills at the given song seconds -> <out>/t_<seconds>.png (review frames)
  default     every --step'th frame from --from to --to (song seconds; default the whole move, to N40's black)
              -> <out>/f_<frame>.png (frame numbers are the song's, at the video's fps)

Usage: blender -b --factory-startup --python scenes/blender/animatic.py -- --out DIR [--profile NAME] [--size W H]
       [--samples N] [--step K] [--from S] [--to S] [--resume] [--cloth-cache DIR] [--anchors | --times S ...]
--size and --samples override the profile's; with neither, 640x360 at 8 samples.
"""
import argparse
import json
import math
import struct
import sys
import time
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE / "sets"), str(HERE)]
import animate  # noqa: E402
import camera_path  # noqa: E402
import nursery  # noqa: E402
import sr_anim as A  # noqa: E402
import sr_kit as K  # noqa: E402

PROFILES = json.loads((HERE.parents[1] / "config" / "render_profiles.json").read_text())


def write_pc2(path, frames):
    """Vertex positions per frame (a list of flat float32 arrays) as a PC2 point cache, for a Mesh Cache modifier."""
    n = len(frames[0]) // 3
    with open(path, "wb") as f:
        f.write(struct.pack("<12siiffi", b"POINTCACHE2\0", 1, n, 0.0, 1.0, len(frames)))
        for co in frames:
            f.write(co.tobytes())


def cloth_from_cache(scene, cache_dir):
    """The cloth simulations through a shared point cache (C5): Blender's cloth does not repeat from run to run (the
    blanket's folds at N39-N40 differ between two runs of the same code), so the final render's separate runs (the
    windows span, the rest, a resume, the anchors) would each fold it differently. The first run bakes and writes each
    cloth's result before its later modifiers (thickness, subdivision) to <cache_dir>/<object>.pc2; every run then
    swaps the Cloth modifier for a Mesh Cache reading that file, so all of them show the same blanket."""
    cache_dir = Path(cache_dir)
    cloth = [(o, m) for o in scene.objects if o.type == "MESH" for m in o.modifiers if m.type == "CLOTH"]
    files = {o.name: cache_dir / f"{o.name}.pc2" for o, _ in cloth}
    if not all(f.exists() for f in files.values()):
        cache_dir.mkdir(parents=True, exist_ok=True)
        t = time.time()
        with bpy.context.temp_override(scene=scene):
            bpy.ops.ptcache.bake_all(bake=True)
        later = [(mm, mm.show_viewport) for o, m in cloth for mm in o.modifiers[list(o.modifiers).index(m) + 1:]]
        for mm, _ in later:
            mm.show_viewport = False
        f0 = min(m.point_cache.frame_start for _, m in cloth)
        f1 = max(m.point_cache.frame_end for _, m in cloth)
        frames = {o.name: [] for o, _ in cloth}
        for f in range(f0, f1 + 1):
            scene.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            for o, _ in cloth:
                me = o.evaluated_get(dg).data
                co = np.empty(len(me.vertices) * 3, np.float32)
                me.vertices.foreach_get("co", co)
                frames[o.name].append(co)
        for mm, shown in later:
            mm.show_viewport = shown
        for name, fr in frames.items():
            tmp = files[name].with_suffix(".pc2.part")
            write_pc2(tmp, fr)
            tmp.rename(files[name])
        (cache_dir / "frames.json").write_text(json.dumps({"first": f0, "last": f1}))
        print(f"baked the cloth and wrote {len(files)} point caches in {time.time() - t:.0f} s", flush=True)
    f0 = json.loads((cache_dir / "frames.json").read_text())["first"]
    for o, m in cloth:
        i = list(o.modifiers).index(m)
        o.modifiers.remove(m)
        mc = o.modifiers.new("cloth_cache", "MESH_CACHE")
        mc.cache_format, mc.filepath = "PC2", str(files[o.name].resolve())
        mc.frame_start, mc.interpolation, mc.deform_mode = f0, "LINEAR", "OVERWRITE"
        o.modifiers.move(len(o.modifiers) - 1, i)
    print(f"cloth from the point caches in {cache_dir}", flush=True)


def build(size, samples, mb_steps=1, bake=True, cloth_cache=None):
    """The whole animatic scene, ready to render; returns (scene, f_end). Also imported by scripts/qc_geometry.py.
    bake=False leaves the simulations unbaked (for tuning them); cloth_cache shares one bake between runs."""
    t_start = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = K.setup_render(bpy.context.scene, size[0], size[1], samples, mb_steps)
    scene.eevee.use_volumetric_shadows = True
    scene.eevee.volumetric_tile_size = "8"
    S = nursery.build(reveal=True)
    S["probe"] = nursery.crib_probe(S["crib"]["root"])
    births = animate.all_(S)
    # Flat-shaded curved parts read as low-poly (human, C4 v11 review), as Sandbox Rhapsody found at its C5: the kit's
    # smooth_by_angle, except the blanket and its colliders, whose normals steer the single-sided collisions (smoothing
    # them refolded the approved blanket).
    sim = {o.data for o in bpy.data.objects
           if o.type == "MESH" and any(m.type in ("CLOTH", "COLLISION") for m in o.modifiers)}
    n = 0
    for me in {o.data for o in bpy.data.objects if o.type == "MESH"} - sim:
        if me.polygons and not all(p.use_smooth for p in me.polygons):
            me.shade_smooth()
            me.set_sharp_from_angle(angle=math.radians(35.0))
            n += 1
    print(f"smooth by angle: {n} meshes ({len(sim)} simulation meshes left as they were)")
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
    if bake and cloth_cache:
        cloth_from_cache(scene, cloth_cache)
    elif bake:
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
    ap.add_argument("--cloth-cache", help="share one cloth bake between runs (point caches in this directory)")
    ap.add_argument("--resume", action="store_true",
                    help="keep frames already in --out (and claim each with a placeholder), so runs resume and share")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
    prof = PROFILES[args.profile] if args.profile else {"size": [640, 360], "samples": 8}
    scene, f_end = build(args.size or prof["size"], args.samples or prof["samples"], prof.get("motion_blur_steps", 1),
                         cloth_cache=args.cloth_cache)
    # Shadow maps follow screen resolution: at 4K the room asked for more shadow pages than Eevee updates in one go
    # ("Shadow buffer full", 9,838 / 8,192, with the kit's 2 GB pool). Half scale at 4K is still finer than 720p's.
    scene.eevee.shadow_resolution_scale = prof.get("shadow_resolution_scale", 1.0)
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
