"""C2 test frames: Sandbox Rhapsody's probe, imported from the kit unchanged (sr_kit.probe), in this set's lighting
with the green standby LED (brief, checkpoint C2).

  reveal   N38: the push arrives over the crib rail; the probe lies at the head end under the blanket, lens iris
           open, LED lit, arms folded on the blanket, rim light on the sphere
  glint    before N38: the same crib from further back, the chassis hidden (brief: hidden until N38), only the green
           glint at the blanket's lip
  match    the probe alone on the dresser top at Sandbox Rhapsody's C1 close-up framing and pose, for a side-by-side
           with renders/c2/sr_reference_close.png

Usage: blender -b --factory-startup --python scenes/blender/c2_test_frame.py -- <out.png> [width height samples [reveal|glint|match]]
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
w, h, samples = (int(a) for a in args[1:4]) if len(args) >= 4 else (1280, 720, 64)
framing = args[4] if len(args) >= 5 else "reveal"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = K.setup_render(bpy.context.scene, w, h, samples)
scene.eevee.use_volumetric_shadows = True
scene.eevee.volumetric_tile_size = "4"
S = nursery.build(star_count=1.0 if framing != "glint" else 0.6)
S["root"]["frost"] = 0.0 if framing == "reveal" else 0.5  # by the outro the glass is clear (brief)
S["street_neighbor"]["amber"] = 1.0

crib = S["crib"]["root"]
P = S["probe"] = nursery.crib_probe(crib)
probe = P["probe"]
bpy.context.view_layer.update()  # matrix_world is stale until the depsgraph runs
crib_w = crib.matrix_world.copy()


def hide_tree(o):
    """hide_render on an empty doesn't hide its children; the chassis is many parts."""
    o.hide_render = True
    for c in o.children_recursive:
        c.hide_render = True

if framing == "reveal":
    probe["led"], probe["sing"] = 1.0, 0.55  # the iris widens out of the glint
    probe["arm_l"] = probe["arm_r"] = 0.4     # forearms out and resting on the blanket, as folded hands (brief)
    probe.location.z += 0.02                  # a little more of the sphere above the felt, so the arms clear it
    crib["glint"] = 0.0
    at = probe.matrix_world.translation.copy()
    K.reflection_probe(center=at, radius=0.35)
    nursery.light("reveal.rim", "AREA", at + Vector((-0.5, 0.55, 0.45)), 14.0, "rim", 0.25, target=at, specular=0.8)
    eye = at + Vector((0.2, -0.5, 0.8))  # over the near rail (its top is 1.35 m), looking down into the crib
    K.camera("cam", eye, at + Vector((0.0, 0.0, -0.03)), lens=50, dof_fstop=2.8, focus=(eye - at).length)
elif framing == "glint":
    hide_tree(P["root"])  # the chassis stays hidden until N38, glint only
    crib["glint"] = 1.0
    at = crib_w @ Vector((-0.5, 0.0, 0.5))
    eye = at + Vector((0.55, -1.45, 0.75))
    K.camera("cam", eye, at, lens=45, dof_fstop=4.0, focus=(eye - at).length)
else:  # match: the probe on the dresser top, posed and framed as Sandbox Rhapsody's C1 close-up
    hide_tree(P["root"])
    for nm in ("dresser.musicbox", "dresser.monitor"):  # clear the dresser top for the probe
        hide_tree(bpy.data.objects[nm])
    m = K.probe("match_probe", (0, 0, 0), led_role="standby")
    top = bpy.data.objects["dresser.top"].matrix_world.translation
    m.location = top + Vector((0.0, 0.0, 0.0125 + K.PROBE_R))
    m.rotation_euler = (0, 0, math.radians(-22))  # Sandbox Rhapsody's C1 pose and camera offsets, exactly
    m["led"], m["arm_l"], m["arm_r"] = 1.0, 0.2, 0.9
    K.reflection_probe(center=m.location, radius=0.2)
    at = m.location.copy()
    eye = at + Vector((-0.42, -0.82, 0.0))
    K.camera("cam", eye, at + Vector((0.14, 0.2, -0.07)), lens=45, dof_fstop=3.2, focus=(eye - at).length)

K.bloom(scene)
K.rebind_drivers()
K.refresh()
bad = K.invalid_drivers()
if bad:
    print("INVALID DRIVERS:", bad)
scene.render.filepath = out_path
scene.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
