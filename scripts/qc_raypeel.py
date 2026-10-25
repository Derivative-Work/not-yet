"""QC: z-fighting between any surfaces, curved ones included (qc_geometry.py only compares flat triangles). Builds the
animatic scene and casts rays from the camera through a grid of pixels, peeling through every surface. A pixel is
flagged where the first surface it sees and the next front-facing surface of a different object are closer than the
depth buffer resolves at that distance (dz ~ z^2 / (clip_start * 2^24), times 4) or than 0.2 mm.

  scan       every --every s of the move (default 1), a --grid W H of rays (default 160 90) -> OUT.json, pairs ranked
  --pixel    one frame and pixel of a W x H render: every surface along that ray, for diagnosis

Usage: blender -b --factory-startup --python scripts/qc_raypeel.py -- OUT.json [--every S] [--grid W H]
       blender -b --factory-startup --python scripts/qc_raypeel.py -- --pixel FRAME X Y W H [X Y ...]
"""
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scenes" / "blender"))
sys.path.insert(0, str(ROOT / "scripts"))
import animatic  # noqa: E402
import sr_anim as A  # noqa: E402
from qc_raypeel_lib import fights, peel, ray_dir  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]


scene, f_end = animatic.build([320, 180], 1)
cam = scene.camera
near = cam.data.clip_start

if argv[0] == "--pixel":
    f, rest = int(argv[1]), argv[2:]
    W, H = int(rest[2]), int(rest[3])
    pts = [(int(rest[0]), int(rest[1]))] + [(int(rest[i]), int(rest[i + 1])) for i in range(4, len(rest), 2)]
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    org = cam.matrix_world.translation.copy()
    for x, y in pts:
        hits = peel(scene, dg, org, ray_dir(scene, cam, (x + 0.5) / W, 1 - (y + 0.5) / H), 10)
        print(f"PIXEL {x},{y} @ {f}:")
        for nm, z, front in hits:
            print(f"   {z:9.5f} m  {'front' if front else 'back '}  {nm}")
        print("   fight:", fights(hits, near), flush=True)
    sys.exit(0)

OUT = Path(argv[0])
every = float(argv[argv.index("--every") + 1]) if "--every" in argv else 1.0
gw, gh = (int(argv[argv.index("--grid") + 1]), int(argv[argv.index("--grid") + 2])) if "--grid" in argv else (160, 90)
pairs = {}
f = 0
while f <= f_end:
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    org = cam.matrix_world.translation.copy()
    n = 0
    for j in range(gh):
        for i in range(gw):
            r = fights(peel(scene, dg, org, ray_dir(scene, cam, (i + 0.5) / gw, 1 - (j + 0.5) / gh)), near)
            if r:
                a, b, z, gap = r
                k = "|".join(sorted((a, b)))
                p = pairs.setdefault(k, {"a": a, "b": b, "rays": 0, "frames": {}, "min_gap_mm": 1e9, "z_m": z})
                p["rays"] += 1
                p["frames"][f] = p["frames"].get(f, 0) + 1
                p["min_gap_mm"] = min(p["min_gap_mm"], round(gap * 1000, 4))
                n += 1
    print(f"frame {f} ({f / A.FPS:.1f} s): {n} fighting rays", flush=True)
    f += max(1, round(every * A.FPS))

rows = sorted(pairs.values(), key=lambda p: -p["rays"])
for p in rows:
    fr = sorted(p["frames"])
    p["seconds"] = [round(fr[0] / A.FPS, 1), round(fr[-1] / A.FPS, 1)]
    p["peak_frame"] = max(p["frames"], key=p["frames"].get)
    p["frames"] = len(fr)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"clip_start": near, "grid": [gw, gh], "every_s": every, "pairs": rows}, indent=1))
print("wrote", OUT, len(rows), "pairs", flush=True)
