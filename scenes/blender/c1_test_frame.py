"""C1 test frames: the glass room in the hall in this video's look (brief, checkpoint C1).

Builds the whole set (scenes/blender/sets/nursery.py) posed as a late-song still (walls crowded with stars, frost
half gone, the neighbor's window lit) and frames it:
  wide   the N29 / thumbnail view: the glass room glowing in the dark hall, the back window (four panes: the moon in one, the amber window in another)
         on the hill behind it
  hallwin  the front wall's four-pane window straight on, the taped pane and the new crack (N09/N10's subject)
  close  outside the vault door at N07: the sticky note, the dial, and the nursery through the glass (crib, mobile,
         projector, chair), for the materials (glass, frost, felt, steel)
Deterministic: the star scatter reads its seed from config/seeds.json.

Usage: blender -b --factory-startup --python scenes/blender/c1_test_frame.py -- <out.png> [width height samples [wide|close|hallwin]]
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE / "sets")]
import nursery  # noqa: E402
import sr_kit as K  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
out_path = args[0]
w, h, samples = (int(a) for a in args[1:4]) if len(args) >= 4 else (1280, 720, 32)
framing = args[4] if len(args) >= 5 else "wide"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = K.setup_render(bpy.context.scene, w, h, samples)
scene.eevee.use_volumetric_shadows = True
scene.eevee.volumetric_tile_size = "4"
S = nursery.build(star_count=0.85)

# A late-song still: frost mostly gone, the mobile mid-turn, the chair tipped back, the blanket mid-breath.
S["root"]["frost"] = 0.45
S["mobile"]["turn"] = 0.13
S["chair"]["rock"] = 0.6
S["crib"]["root"]["breath"] = 0.7
S["crib"]["root"]["glint"] = 0.7
S["door"]["open"] = 0.0
S["street_neighbor"]["amber"] = 1.0

if framing == "wide":
    # Low three-quarter from front left, far enough left that the back window sits clear of the room.
    eye = Vector((-6.0, -8.2, 1.5))
    target = Vector((0.3, 1.0, 2.3))
    K.camera("cam", eye, target, lens=27, dof_fstop=8.0, focus=(eye - Vector((0, 0, 1.6))).length)
elif framing == "hallwin":
    # Straight on at the front wall's four-pane window, the new crack half grown (N10's "never quite mended").
    S["crack_new"]["grow"] = 0.6
    eye = Vector((-4.0, -9.0, 2.6))
    K.camera("cam", eye, Vector((-4.0, -14.0, 2.6)), lens=40, dof_fstop=8.0, focus=5.0)
else:
    # Outside the front wall, right of the door: the note in focus at left, the nursery through the glass at right.
    eye = Vector((1.85, -4.3, 1.6))
    target = Vector((0.55, -0.6, 1.15))
    K.camera("cam", eye, target, lens=35, dof_fstop=5.6, focus=(eye - Vector((0.34, -2.1, 1.28))).length)

K.bloom(scene)
K.rebind_drivers()
K.refresh()
bad = K.invalid_drivers()
if bad:
    print("INVALID DRIVERS:", bad)
print("stars placed:", S["stars"]["placed"], "objects:", len(bpy.data.objects))
scene.render.filepath = out_path
scene.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
