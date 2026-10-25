"""QC: find what makes a spot flicker. Renders a pair of consecutive frames under variations (shadow jitter on every
light, shadow resolution x2, ray tracing off, no shadows) and reports how much the crop changes between the two frames
under each; the variation that stops the change names the cause.

Usage: blender -b --factory-startup --python scripts/qc_flicker_cause.py -- OUT_DIR FRAME X0 Y0 X1 Y1 [--profile NAME]
  (crop in pixels of the profile's size; default draft720)
"""
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scenes" / "blender"))
import animatic  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
out, f = Path(argv[0]), int(argv[1])
x0, y0, x1, y1 = map(int, argv[2:6])
prof = animatic.PROFILES[argv[argv.index("--profile") + 1] if "--profile" in argv else "draft720"]
out.mkdir(parents=True, exist_ok=True)
scene, _ = animatic.build(prof["size"], prof["samples"], prof.get("motion_blur_steps", 1))
lights = [o.data for o in scene.objects if o.type == "LIGHT"]


def crop(path):
    im = bpy.data.images.load(str(path))
    w, h = im.size
    px = np.array(im.pixels[:], np.float32).reshape(h, w, 4)[::-1, :, :3]  # top row first
    bpy.data.images.remove(im)
    return px[y0:y1, x0:x1]


def jitter(on):
    for ld in lights:
        ld.use_shadow_jitter = on


def shadow_scale(s):
    scene.eevee.shadow_resolution_scale = s


def raytrace(on):
    scene.eevee.use_raytracing = on


def shadows(on):
    for ld in lights:
        ld.use_shadow = on


VARIANTS = [("as-is", lambda: None, lambda: None),
            ("shadow jitter", lambda: jitter(True), lambda: jitter(False)),
            ("shadow res x2", lambda: shadow_scale(2.0), lambda: shadow_scale(1.0)),
            ("no ray tracing", lambda: raytrace(False), lambda: raytrace(True)),
            ("no shadows", lambda: shadows(False), lambda: shadows(True))]
for name, on, off in VARIANTS:
    on()
    crops = []
    for g in (f, f + 1):
        scene.frame_set(g)
        p = out / f"{name.replace(' ', '_')}_{g}.png"
        scene.render.filepath = str(p)
        bpy.ops.render.render(write_still=True)
        crops.append(crop(p))
    off()
    d = np.abs(crops[0] - crops[1])
    print(f"CAUSE {name:15s} mean |f - f+1| in crop = {d.mean():.4f}  p99 = {np.percentile(d, 99):.4f}", flush=True)
