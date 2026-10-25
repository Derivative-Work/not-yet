"""Pick draft settings on a new box: render a few song times at 1280x720 under several (samples, motion-blur steps)
pairs and time each, building the animatic scene once.

Usage: blender -b --factory-startup --python scripts/qc_mbtest.py -- OUT_DIR T1 [T2 ...]
  -> OUT_DIR/s<samples>_m<steps>_t<seconds>.png, timings on stdout
"""
import sys
import time
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scenes" / "blender"))
import animatic  # noqa: E402
import sr_anim as A  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
out, times = Path(argv[0]), [float(t) for t in argv[1:]]
out.mkdir(parents=True, exist_ok=True)
scene, f_end = animatic.build([1280, 720], 8)
for samples, steps in [(8, 1), (16, 1), (32, 1), (32, 2), (64, 1), (64, 4)]:
    scene.eevee.taa_render_samples, scene.eevee.motion_blur_steps = samples, steps
    for t in times:
        scene.frame_set(min(A.frame(t), f_end))
        scene.render.filepath = str(out / f"s{samples:02d}_m{steps}_t{t:07.2f}.png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"MB samples={samples} steps={steps} t={t}: {time.time() - t0:.2f} s", flush=True)
