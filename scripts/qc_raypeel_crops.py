"""QC companion to qc_raypeel.py: for its top pairs, render the peak frame and the next at a profile's size, crop
around the rays where the pair fights (marked in the second crop), and note whether the two surfaces share a material
(a fight between identical shading can't be seen). One sheet per pair, for a human-eye pass.

Usage: blender -b --factory-startup --python scripts/qc_raypeel_crops.py -- RAYPEEL.json OUT_DIR [--top N]
       [--profile NAME]
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scenes" / "blender"))
sys.path.insert(0, str(ROOT / "scripts"))
import animatic  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = Path(argv[0]), Path(argv[1])
top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 25
prof = animatic.PROFILES[argv[argv.index("--profile") + 1] if "--profile" in argv else "draft720"]
out.mkdir(parents=True, exist_ok=True)
rp = json.loads(src.read_text())
gw, gh = rp["grid"]

scene, f_end = animatic.build(prof["size"], prof["samples"], prof.get("motion_blur_steps", 1))
import qc_raypeel_lib as R  # noqa: E402  (peel, fights, ray_dir: shared with qc_raypeel.py)

W, H = prof["size"]
near = scene.camera.data.clip_start


def mats(name):
    o = bpy.data.objects[name]
    return sorted({s.material.name for s in o.material_slots if s.material})


def load(path):
    im = bpy.data.images.load(str(path))
    w, h = im.size
    px = np.array(im.pixels[:], np.float32).reshape(h, w, 4)[::-1, :, :3]
    bpy.data.images.remove(im)
    return px


report = []
for k, p in enumerate(rp["pairs"][:top]):
    f = p["peak_frame"]
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    org = scene.camera.matrix_world.translation.copy()
    pts = []
    for j in range(gh):
        for i in range(gw):
            r = R.fights(R.peel(scene, dg, org, R.ray_dir(scene, scene.camera, (i + 0.5) / gw, 1 - (j + 0.5) / gh)),
                         near)
            if r and {r[0], r[1]} == {p["a"], p["b"]}:
                pts.append(((i + 0.5) / gw * W, (j + 0.5) / gh * H))
    ims = []
    for g in (f, min(f + 1, f_end)):
        scene.frame_set(g)
        scene.render.filepath = str(out / f"pair{k:02d}_{g}.png")
        bpy.ops.render.render(write_still=True)
        ims.append(load(out / f"pair{k:02d}_{g}.png"))
    if pts:
        xs, ys = np.array(pts).T
        cx, cy = np.median(xs), np.median(ys)
    else:
        cx, cy = W / 2, H / 2
    half = 60
    x0, y0 = int(np.clip(cx - half, 0, W - 2 * half)), int(np.clip(cy - half, 0, H - 2 * half))
    crops = [im[y0:y0 + 2 * half, x0:x0 + 2 * half].copy() for im in ims]
    for x, y in pts:
        xi, yi = int(x) - x0, int(y) - y0
        if 0 <= xi < 2 * half and 0 <= yi < 2 * half:
            crops[1][max(yi - 1, 0):yi + 2, max(xi - 1, 0):xi + 2] = (1, 0, 0)
    diff = np.clip(np.abs(crops[0] - ims[1][y0:y0 + 2 * half, x0:x0 + 2 * half]) * 4, 0, 1)
    sheet = np.concatenate(crops + [diff], 1).repeat(3, 0).repeat(3, 1)
    img = bpy.data.images.new(f"pair{k}", sheet.shape[1], sheet.shape[0])
    img.pixels = np.concatenate([sheet[::-1], np.ones(sheet.shape[:2] + (1,), np.float32)], 2).ravel()
    img.filepath_raw = str(out / f"pair{k:02d}_sheet.png")
    img.file_format = "PNG"
    img.save()
    same = mats(p["a"]) == mats(p["b"])
    report.append({"k": k, "a": p["a"], "b": p["b"], "frame": f, "rays_here": len(pts), "mats_a": mats(p["a"]),
                   "mats_b": mats(p["b"]), "same_material": same, "crop_xy": [x0, y0]})
    print(f"PAIR {k:02d} {p['a']} | {p['b']} f{f} rays {len(pts)} same_material={same} "
          f"{mats(p['a'])} {mats(p['b'])}", flush=True)
(out / "pairs.json").write_text(json.dumps(report, indent=1))
