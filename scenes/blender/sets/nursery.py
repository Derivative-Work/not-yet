"""The one set (brief, "The set"): a glass nursery on a low plinth in a dark, museum-like hall, with the street through
a tall window at the back and the shop window across the hall.

Layout (metres, Z up, the camera's push starts at -Y):
  hall        x -11..11, y -14..12, ceiling 9; tall window in the back wall (+Y) at x 0
  plinth      5.6 m square, 0.4 m high, centred on the origin; the glass room stands on it
  glass room  4 m square, 2.8 m high (x, y -2..2, z 0.4..3.2); the vault door in its front (-Y) wall
  shop window in the +X wall at y 0, facing the glass room
  street      outside the tall window: a hill of small houses, y 40..70

Everything is procedural. The only random process is the star scatter, seeded from config/seeds.json. Rigs expose
custom properties for the note-driven library (sr_anim), all 0-1 unless noted:
  room root  "frost" (1 = full band, 0 = clear glass)
  crib       "breath" (blanket rise), "glint" (the probe's LED through the blanket)
  chair      "rock" (-1..1, the rocking angle), "blanket_slip"
  door       "open" (0 shut .. 1 = a crack, 12 degrees), "note_peel"
  mobile     "turn" (revolutions), "lower" (per piece: "lower_bank", "lower_globe", "lower_cloud", "lower_flag")
  stars      "count" (0..1 of the full scatter shown)
  neighbor   "amber" (the upstairs window)
"""
import json
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import sr_kit as K

LOOK = K.LOOK
SEEDS = json.loads((K.ROOT / "config" / "seeds.json").read_text())
PL_H = 0.4          # plinth height: the nursery floor
ROOM = 2.0          # glass room half-width
ROOM_H = 2.8        # glass room height
TOP = PL_H + ROOM_H
HILL = 21.0         # the street's hill height behind the window: high enough to show above the glass room
MOON_AT = (19.0, 92.0, 25.0)  # in the tall window from the wide camera


# ---------------------------------------------------------------- materials (this video's surfaces)

def mat_paint(name, role, rough=None):
    """Painted wood or metal: no coat, mid roughness (the crib, the door's pastel)."""
    m, b = K._principled(name)
    b.inputs["Base Color"].default_value = K.col(role)
    b.inputs["Roughness"].default_value = LOOK["materials"]["paint_roughness"] if rough is None else rough
    return m


def mat_felt(name, role):
    """Felt and blanket wool: fully rough with sheen, so edges catch a soft halo of the night-light."""
    m, b = K._principled(name)
    b.inputs["Base Color"].default_value = K.col(role)
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Specular IOR Level"].default_value = 0.2
    b.inputs["Sheen Weight"].default_value = LOOK["materials"]["felt_sheen"]
    b.inputs["Sheen Tint"].default_value = K.col("comfort")
    return m


def mat_steel(name="steel"):
    return K.mat_metal(name, "steel", LOOK["materials"]["steel_roughness"])


def mat_stone(name, role, rough):
    m, b = K._principled(name)
    b.inputs["Base Color"].default_value = K.col(role)
    b.inputs["Roughness"].default_value = rough
    return m


def mat_frost(name, owner):
    """Frost on the inside of the glass's bottom edge: white crystalline speckle whose height and coverage follow
    `owner["frost"]` (1 = the full band, 0 = clear). Blended, with a faint self-glow so it reads in the dark hall."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])  # the strip is a plane: its local Y runs 0 (bottom) to 1 (top)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 38.0
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.7
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    # coverage where height < frost + jitter: v = frost + 0.25 (noise - 0.5) - height, a ragged edge that climbs
    # the strip as frost goes 0 -> 1
    lim = nt.nodes.new("ShaderNodeMath")
    lim.operation = "MULTIPLY_ADD"
    lim.inputs[1].default_value = 0.25
    nt.links.new(noise.outputs["Fac"], lim.inputs[0])
    lim.inputs[2].default_value = -0.125
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    nt.links.new(lim.outputs[0], sub.inputs[0])
    nt.links.new(sep.outputs["Y"], sub.inputs[1])
    fr = nt.nodes.new("ShaderNodeValue")
    fr.name = "frost"
    K.drive(fr.outputs[0], "default_value", None, owner, "frost", "x")
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(sub.outputs[0], add.inputs[0])
    nt.links.new(fr.outputs[0], add.inputs[1])
    off = nt.nodes.new("ShaderNodeMath")
    off.operation = "SUBTRACT"
    nt.links.new(add.outputs[0], off.inputs[0])
    off.inputs[1].default_value = 0.0
    cov = nt.nodes.new("ShaderNodeMapRange")
    cov.inputs["From Min"].default_value = 0.0
    cov.inputs["From Max"].default_value = 0.08
    cov.inputs["To Max"].default_value = 0.85
    nt.links.new(off.outputs[0], cov.inputs["Value"])
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = K.col("frost")
    b.inputs["Roughness"].default_value = 0.55
    b.inputs["Emission Color"].default_value = K.col("frost")
    b.inputs["Emission Strength"].default_value = 0.08
    nt.links.new(cov.outputs[0], b.inputs["Alpha"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(b.outputs[0], out.inputs[0])
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = False
    return m


# ---------------------------------------------------------------- primitives

def box(name, mat, loc, size, parent=None, bev=0.0, rot=(0, 0, 0)):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cube_add, mat, parent, size=1, location=loc, rotation=rot)
    o.scale = size
    if bev:
        K.bevel(o, bev, 2)
    return o


def cyl(name, mat, loc, r, depth, parent=None, rot=(0, 0, 0), verts=32, smooth=True):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cylinder_add, mat, parent, radius=r, depth=depth, vertices=verts,
                   location=loc, rotation=rot)
    if smooth:
        K.smooth(o)
    return o


def sphere(name, mat, loc, r, parent=None, segs=24):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_uv_sphere_add, mat, parent, radius=r, segments=segs,
                   ring_count=segs // 2, location=loc)
    K.smooth(o)
    return o


def torus(name, mat, loc, R, r, parent=None, rot=(0, 0, 0)):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_torus_add, mat, parent, major_radius=R, minor_radius=r, location=loc,
                   rotation=rot)
    K.smooth(o)
    return o


def bar(name, mat, a, b, r, parent=None, verts=12):
    """A round rod from a to b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    o = cyl(name, mat, (a + b) / 2, r, d.length, parent, verts=verts)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return o


def light(name, kind, loc, power, role, size=0.1, target=None, spot=None, specular=1.0, parent=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = power
    ld.color = K.col(role)[:3]
    ld.specular_factor = specular
    if kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = size
    elif kind == "AREA":
        ld.size = size
    elif kind == "SUN":
        ld.angle = size
    if spot:
        ld.spot_size, ld.spot_blend = spot
    o = K.link(bpy.data.objects.new(name, ld))
    o.location = loc
    if target is not None:
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if parent:
        o.parent = parent
    return o


# ---------------------------------------------------------------- the hall

def hall():
    """Dark polished floor, tall dark walls and ceiling; the tall window in the back wall (an opening with
    mullions, no glass), a hall window behind the camera with a taped crack (N09, seen in reflection)."""
    out = {}
    K.floor(size=80.0).data.materials[0] = mat_stone("hall_floor", "floor", LOOK["materials"]["floor_roughness"])
    wall = mat_stone("hall_wall", "hall_wall", 0.85)
    H = 9.0
    box("hall.ceiling", wall, (0, -1, H + 0.15), (22.6, 26.6, 0.3))
    box("hall.wall_l", wall, (-11.15, -1, H / 2), (0.3, 26.6, H))
    box("hall.wall_front", wall, (0, -14.15, H / 2), (22.6, 0.3, H))
    # The +X wall with the shop window's opening (y -1.8..1.8, z 0.6..3.0).
    for nm, y0, y1 in (("a", -14, -1.8), ("b", 1.8, 12)):
        box(f"hall.wall_r{nm}", wall, (11.15, (y0 + y1) / 2, H / 2), (0.3, y1 - y0, H))
    box("hall.wall_r_low", wall, (11.15, 0, 0.3), (0.3, 3.6, 0.6))
    box("hall.wall_r_high", wall, (11.15, 0, (3.0 + H) / 2), (0.3, 3.6, H - 3.0))
    # The back wall with the tall window (x -1.6..1.6, z 0.6..7.6).
    wx, z0, z1 = 1.6, 0.6, 7.6
    for nm, x0, x1 in (("l", -11, -wx), ("r", wx, 11)):
        box(f"hall.wall_back_{nm}", wall, ((x0 + x1) / 2, 12.15, H / 2), (x1 - x0, 0.3, H))
    box("hall.wall_back_low", wall, (0, 12.15, z0 / 2), (2 * wx, 0.3, z0))
    box("hall.wall_back_high", wall, (0, 12.15, (z1 + H) / 2), (2 * wx, 0.3, H - z1))
    steel = mat_steel("window_steel")
    for k in range(5):  # mullions: 4 columns ...
        x = -wx + k * (2 * wx / 4)
        box(f"window.mullion{k}", steel, (x, 12.02, (z0 + z1) / 2), (0.05, 0.08, z1 - z0))
    for k in range(9):  # ... and 8 rows of panes
        z = z0 + k * ((z1 - z0) / 8)
        box(f"window.transom{k}", steel, (0, 12.02, z), (2 * wx, 0.08, 0.04))
    box("window.sill", mat_stone("sill", "plinth", 0.5), (0, 11.9, z0 - 0.03), (2 * wx + 0.3, 0.4, 0.06))
    # A hall window in the front wall, behind the camera, its cracked pane taped over (N09/N10 reflections).
    hw = (-4.0, -13.98)
    for k in range(3):
        box(f"hallwin.mullion{k}", steel, (hw[0] - 0.8 + k * 0.8, hw[1], 3.0), (0.04, 0.06, 3.0))
    for k in range(4):
        box(f"hallwin.transom{k}", steel, (hw[0], hw[1], 1.5 + k * 1.0), (1.6, 0.06, 0.04))
    pane = box("hallwin.glow", K.mat_emission("hallwin_glow", "sky", 0.6), (hw[0], hw[1] - 0.04, 3.0), (1.6, 0.01, 3.0))
    pane.visible_shadow = False
    tape = K.mat_matte("tape", "paper")
    for k, a in enumerate((0.6, -0.6)):  # an X of tape over one pane
        box(f"hallwin.tape{k}", tape, (hw[0] + 0.4, hw[1] + 0.035, 3.5), (0.62, 0.004, 0.05), rot=(0, a, 0))
    out["window"] = (0.0, 12.0, (z0 + z1) / 2)
    return out


def plinth():
    """The low plinth (5.6 m square, 0.4 m) in dark stone with a steel edge band, and the slit of tungsten light
    from the basement under its front edge (N28)."""
    out = {}
    s = 2.8
    out["plinth"] = box("plinth", mat_stone("plinth", "plinth", 0.6), (0, 0, PL_H / 2), (2 * s, 2 * s, PL_H), bev=0.01)
    steel = mat_steel("plinth_band")
    for k, (p, sz) in enumerate((((0, -s, PL_H - 0.02), (2 * s + 0.02, 0.012, 0.04)),
                                 ((0, s, PL_H - 0.02), (2 * s + 0.02, 0.012, 0.04)),
                                 ((-s, 0, PL_H - 0.02), (0.012, 2 * s + 0.02, 0.04)),
                                 ((s, 0, PL_H - 0.02), (0.012, 2 * s + 0.02, 0.04)))):
        box(f"plinth.band{k}", steel, p, sz)
    slit = box("plinth.slit", K.mat_emission("tungsten_slit", "tungsten", LOOK["lights"]["tungsten_slit"]),
               (0.3, -s - 0.004, 0.035), (1.6, 0.004, 0.012))
    slit.visible_shadow = False
    out["slit"] = slit
    return out


# ---------------------------------------------------------------- the glass room

def glass_room():
    """Clear glass walls and ceiling on a thin steel frame (mullions every metre), frost along the inside bottom
    edge, the round vault door in the front wall. Returns {"root", "door", "note", ...}."""
    out = {}
    root = K.empty("room", (0, 0, PL_H))
    K.prop(root, "frost", 1.0)
    out["root"] = root
    glass = K.mat_glass("room.glass", reflect=0.55)
    frost = mat_frost("room.frost", root)
    steel = mat_steel("room.steel")
    t = 0.035
    # Walls: each a pane per metre, so the frame has visible verticals (parallax for the arcing push).
    for side, (axis, sign) in {"front": ("y", -1), "back": ("y", 1), "left": ("x", -1), "right": ("x", 1)}.items():
        for k in range(4):
            u = -ROOM + 0.5 + k
            if side == "front" and k in (1, 2):
                continue  # the door's bay
            if axis == "y":
                loc, rot = (u, sign * ROOM, ROOM_H / 2), (math.pi / 2, 0, 0)
            else:
                loc, rot = (sign * ROOM, u, ROOM_H / 2), (math.pi / 2, 0, math.pi / 2)
            pn = K.mesh_obj(f"room.pane_{side}{k}", bpy.ops.mesh.primitive_plane_add, glass, root, size=1,
                            location=loc, rotation=rot)
            pn.scale = (1.0, ROOM_H, 1)
            # Frost strip on the inside face, 0.45 m high at full frost.
            inward = Vector((0, -sign * 0.006, 0)) if axis == "y" else Vector((-sign * 0.006, 0, 0))
            fl = Vector((loc[0], loc[1], 0.225)) + inward
            fs = K.mesh_obj(f"room.frost_{side}{k}", bpy.ops.mesh.primitive_plane_add, frost, root, size=1,
                            location=fl, rotation=rot)
            fs.scale = (1.0, 0.45, 1)
            fs.visible_shadow = False
    roof = K.mesh_obj("room.roof", bpy.ops.mesh.primitive_plane_add, glass, root, size=2 * ROOM,
                      location=(0, 0, ROOM_H))
    roof.visible_shadow = False
    for o in root.children:
        if o.name.startswith("room.pane"):
            o.visible_shadow = False  # clear glass casts no shadow (the moonlight crosses it)
    # Frame: corner posts, top and bottom rails, mullions between panes, roof ribs.
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"room.post{sx}{sy}", steel, (sx * ROOM, sy * ROOM, ROOM_H / 2), (t * 1.6, t * 1.6, ROOM_H), root)
    for k, (p, s) in enumerate((((0, -ROOM, 0), (2 * ROOM, t, t * 1.4)), ((0, ROOM, 0), (2 * ROOM, t, t * 1.4)),
                                ((-ROOM, 0, 0), (t, 2 * ROOM, t * 1.4)), ((ROOM, 0, 0), (t, 2 * ROOM, t * 1.4)))):
        box(f"room.sill{k}", steel, (p[0], p[1], 0.02), s, root)
        box(f"room.head{k}", steel, (p[0], p[1], ROOM_H), s, root)
    for k in range(1, 4):
        u = -ROOM + k
        for side, p in (("back", (u, ROOM)), ("left", (-ROOM, u)), ("right", (ROOM, u))):
            box(f"room.mullion_{side}{k}", steel, (p[0], p[1], ROOM_H / 2), (t, t, ROOM_H), root)
        box(f"room.rib_x{k}", steel, (u, 0, ROOM_H), (t * 0.8, 2 * ROOM, t * 0.8), root)
        box(f"room.rib_y{k}", steel, (0, u, ROOM_H), (2 * ROOM, t * 0.8, t * 0.8), root)
    out.update(vault_door(root))
    return out


def vault_door(room):
    """Sandbox Rhapsody's bank-vault door (set G's freezer door: chrome rim, locking bolts, handwheel, combination
    dial), scaled to a doorway and repainted pastel; the dial is left as it was (brief). It fills the front wall's
    two middle bays, set in a pastel steel surround, hinged on its left edge. The sticky note NOT FOR THE PUBLIC :)
    is on its face, in Sandbox Rhapsody's handwriting font."""
    out = {}
    pastel = mat_paint("door.pastel", "pastel", 0.42)
    chrome = K.mat_chrome("door.chrome")
    steel = mat_steel("door.steel")
    y = -ROOM
    # Surround: a 2 m x 2.8 m panel with a round opening, built as a frame of boxes around a disc-shaped hole.
    R = 0.92
    zc = 1.12
    # The bay around the door stays glass (a solid surround hid the nursery, C1 draft): glass head and kick panels
    # and four glass spandrels between the square bay and the round opening, on steel stiles.
    surround_m = K.mat_glass("door.surround_glass", reflect=0.55)
    box("door.stile_l", steel, (-1.0, y, ROOM_H / 2), (0.035, 0.035, ROOM_H), room)
    box("door.stile_r", steel, (1.0, y, ROOM_H / 2), (0.035, 0.035, ROOM_H), room)
    for nm, z0, z1 in (("head", zc + R + 0.05, ROOM_H), ("kick", 0.0, zc - R - 0.05)):
        pn = K.mesh_obj(f"door.{nm}", bpy.ops.mesh.primitive_plane_add, surround_m, room, size=1,
                        location=(0, y, (z0 + z1) / 2), rotation=(math.pi / 2, 0, 0))
        pn.scale = (2.0, z1 - z0, 1)
        pn.visible_shadow = False
    # Spandrels: the four corners between the square bay and the round opening, as filled quarter-panels.
    bm = bmesh.new()
    n = 24
    for qx, qz in ((-1, 1), (1, 1), (-1, -1), (1, -1)):
        pts = [Vector((qx * (R + 0.05), 0, qz * (R + 0.05)))]
        for i in range(n + 1):
            a = (math.pi / 2) * i / n
            pts.append(Vector((qx * math.cos(a) * R, 0, qz * math.sin(a) * R)))
        vs = [bm.verts.new(p) for p in pts]
        bm.faces.new(vs)
    me = bpy.data.meshes.new("door.spandrels")
    bm.to_mesh(me)
    bm.free()
    sp = K.link(bpy.data.objects.new("door.spandrels", me))
    sp.parent, sp.location = room, (0, y, zc)
    sp.data.materials.append(surround_m)
    sp.visible_shadow = False
    # The door's heavy round frame, painted with the door; a chrome bead on its face.
    torus("door.frame_ring", pastel, (0, y, zc), R + 0.04, 0.055, room, rot=(math.pi / 2, 0, 0))
    torus("door.frame_bead", chrome, (0, y - 0.05, zc), R + 0.04, 0.012, room, rot=(math.pi / 2, 0, 0))
    # The door itself, on a hinge at the opening's left edge; "open" swings it inward up to 12 degrees.
    hinge = K.empty("door.hinge", (-R, y, zc), room)
    root = K.empty("door", (0, 0, 0), None)
    K.prop(root, "open", 0.0)
    K.prop(root, "note_peel", 0.0)
    K.drive(hinge, "rotation_euler", 2, root, "open", "-0.2094 * x")
    out["door"] = root
    slab = cyl("door.slab", pastel, (R, 0, 0), R - 0.01, 0.16, hinge, rot=(math.pi / 2, 0, 0), verts=128)
    torus("door.rim", chrome, (R, -0.08, 0), R - 0.03, 0.03, hinge, rot=(math.pi / 2, 0, 0))
    for k in range(10):  # locking bolts round the rim
        a = k * math.tau / 10
        cyl(f"door.bolt{k}", chrome, (R + math.cos(a) * (R - 0.1), -0.085, math.sin(a) * (R - 0.1)), 0.035, 0.03,
            hinge, rot=(math.pi / 2, 0, 0), verts=24)
    # The handwheel, repainted with the door: hub and four spokes, ring.
    hub = (R + 0.18, -0.12, -0.05)
    torus("door.wheel", pastel, hub, 0.2, 0.018, hinge, rot=(math.pi / 2, 0, 0))
    cyl("door.wheel_hub", pastel, hub, 0.04, 0.06, hinge, rot=(math.pi / 2, 0, 0))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        bar(f"door.spoke{k}", pastel, hub, (hub[0] + math.cos(a) * 0.2, hub[1], hub[2] + math.sin(a) * 0.2), 0.012,
            hinge)
    # The combination dial, untouched: black face, chrome ring, white graduations, chrome knob.
    dial = K.empty("door.dial", (R - 0.28, -0.085, 0.26), hinge)
    cyl("door.dial_face", K.mat_plastic("dial", "shadow", 0.3), (0, -0.006, 0), 0.11, 0.02, dial,
        rot=(math.pi / 2, 0, 0), verts=64)
    torus("door.dial_ring", chrome, (0, -0.016, 0), 0.113, 0.01, dial, rot=(math.pi / 2, 0, 0))
    tick = K.mat_matte("dial_tick", "paper")
    for k in range(24):
        a = k * math.tau / 24
        tk = box(f"door.dial_tick{k}", tick, (math.cos(a) * 0.088, -0.0175, math.sin(a) * 0.088),
                 (0.003, 0.002, 0.014 if k % 6 else 0.024), dial)
        tk.rotation_euler = (0, -a + math.pi / 2, 0)
    cyl("door.dial_knob", chrome, (0, -0.03, 0), 0.04, 0.03, dial, rot=(math.pi / 2, 0, 0), verts=32)
    # The sticky note, a little crooked, at adult eye height on the door's face.
    note = K.empty("door.note", (R + 0.34, -0.085, 0.16), hinge)
    note.rotation_euler = (math.pi / 2, 0.06, 0)
    out["note"] = note
    K.mesh_obj("door.note_paper", bpy.ops.mesh.primitive_plane_add, K.mat_matte("sticky", "note"), note, size=0.2,
               rotation=(0, 0, 0)).scale = (1, 1, 1)
    K.text("door.note_text", "NOT FOR\nTHE PUBLIC :)", 0.036, K.mat_ink("note_ink", "shadow"), loc=(0, 0, 0.0008),
           rot=(0, 0, 0), font="InstrumentSerif-Italic.ttf", parent=note)
    return out


# ---------------------------------------------------------------- the nursery

def crib(name, loc, rot_z=0.0, parent=None, glint=True):
    """A painted crib (1.3 x 0.7 m, rails 0.95 m) with a mattress and a blanket that breathes ("breath"). Under the
    blanket's head end, the probe's green LED shows as a glint ("glint"); the probe itself is not built here (C2)."""
    out = {}
    root = K.empty(name, loc, parent)
    root.rotation_euler = (0, 0, rot_z)
    K.prop(root, "breath", 0.5)
    K.prop(root, "glint", 0.6)
    paint = mat_paint(f"{name}.paint", "crib", 0.5)
    L, W, Hr = 1.3, 0.7, 0.95
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = box(f"{name}.post{sx}{sy}", paint, (sx * L / 2, sy * W / 2, Hr / 2 + 0.03), (0.05, 0.05, Hr + 0.06),
                    root, bev=0.008)
            sphere(f"{name}.finial{sx}{sy}", paint, (sx * L / 2, sy * W / 2, Hr + 0.08), 0.03, root, 16)
    for sy in (-1, 1):  # long sides: top rail, bottom rail, slats
        box(f"{name}.rail_top{sy}", paint, (0, sy * W / 2, Hr - 0.02), (L, 0.04, 0.04), root, bev=0.006)
        box(f"{name}.rail_low{sy}", paint, (0, sy * W / 2, 0.3), (L, 0.04, 0.04), root, bev=0.006)
        for k in range(15):
            x = -L / 2 + (k + 1) * L / 16
            cyl(f"{name}.slat{sy}_{k}", paint, (x, sy * W / 2, (0.3 + Hr - 0.02) / 2), 0.011, Hr - 0.32, root,
                verts=10)
    for sx in (-1, 1):  # ends: solid headboard/footboard panels with an arched top
        box(f"{name}.end{sx}", paint, (sx * L / 2, 0, 0.62), (0.03, W, 0.62), root, bev=0.008)
        # A low arched top: a disc the width of the end, flattened to rise 10 cm (local X is world Z here).
        cyl(f"{name}.arch{sx}", paint, (sx * L / 2, 0, 0.93), W / 2, 0.03, root, rot=(0, math.pi / 2, 0),
            verts=64).scale = (0.3, 1, 1)
    box(f"{name}.mattress", K.mat_plastic(f"{name}.mattress", "felt_cream", 0.8), (0, 0, 0.38), (L - 0.06, W - 0.06, 0.12),
        root, bev=0.04)
    # The blanket: a soft slab over the mattress, its middle raised over the hidden probe at the head end; breath
    # lifts it.
    bm = bmesh.new()
    nx, ny = 26, 14
    vs = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            u, v = i / nx, j / ny
            x, y = (u - 0.5) * (L - 0.1), (v - 0.5) * (W - 0.02)
            hump = math.exp(-((u - 0.28) / 0.17) ** 2 - ((v - 0.5) / 0.28) ** 2)
            drape = -0.07 * (abs(v - 0.5) * 2) ** 6  # the sides fall over the mattress edge
            ripple = 0.006 * math.sin(u * 23.0 + v * 7.0) * math.sin(v * 11.0)
            vs[i, j] = bm.verts.new((x, y, 0.45 + 0.07 * hump + drape + ripple))
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.015)
    me = bpy.data.meshes.new(f"{name}.blanket")
    bm.to_mesh(me)
    bm.free()
    bl = K.link(bpy.data.objects.new(f"{name}.blanket", me))
    bl.parent = root
    bl.data.materials.append(mat_felt(f"{name}.blanket", "felt_blue"))
    K.smooth(bl)
    # Breathing: a shape key that raises the hump 2 cm, driven by "breath".
    bl.shape_key_add(name="rest")
    sk = bl.shape_key_add(name="in")
    for v in sk.data:
        x, y = v.co.x / (L - 0.1) + 0.5, v.co.y / (W - 0.02) + 0.5
        v.co.z += 0.02 * math.exp(-((x - 0.28) / 0.17) ** 2 - ((y - 0.5) / 0.28) ** 2)
    K.drive(sk, "value", None, root, "breath", "x")
    out["blanket"] = bl
    if glint:
        # The green standby LED, seen through a fold of the blanket at the head end: a tiny emitter and a faint light.
        g = sphere(f"{name}.glint", K.mat_emission(f"{name}.glint", "standby", 30.0, root, "glint", floor=0.0),
                   (-L / 2 + 0.07, 0.04, 0.47), 0.006, root, 12)  # just under the blanket's head-end lip
        g.visible_shadow = False
        gl = light(f"{name}.glint_light", "POINT", (-L / 2 + 0.08, 0.04, 0.5), 0.0, "standby", 0.01, parent=root)
        gl.data.specular_factor = 0.3
        K.drive(gl.data, "energy", None, root, "glint", "0.25 * x")
    out["root"] = root
    return out


def mobile(name, loc, parent=None):
    """The crib mobile: an arm up from the crib's back, a cross of two rods, four felt pieces on threads: a bank's
    columns, a globe, a cloud and the tiny flag (Sandbox Rhapsody's prize; its swallowtail shape, recoloured, since
    amber here belongs to the neighbor's window). "turn" spins the cross; "lower_<piece>" drops a piece 25 cm."""
    root = K.empty(name, loc, parent)
    K.prop(root, "turn", 0.0, hi=100.0)
    hub = K.empty(f"{name}.hub", (0, 0, 0), root)
    K.drive(hub, "rotation_euler", 2, root, "turn", "6.2832 * x")
    rod = mat_paint(f"{name}.rod", "crib", 0.4)
    thread = K.mat_matte(f"{name}.thread", "felt_grey")
    sphere(f"{name}.hubball", rod, (0, 0, 0), 0.02, hub, 16)
    pieces = {}
    for k, piece in enumerate(("bank", "globe", "cloud", "flag")):
        a = k * math.pi / 2
        end = Vector((math.cos(a) * 0.28, math.sin(a) * 0.28, -0.03))
        bar(f"{name}.arm{k}", rod, (0, 0, 0), end, 0.006, hub, verts=8)
        K.prop(root, f"lower_{piece}", 0.0)
        hang = K.empty(f"{name}.hang_{piece}", end, hub)
        K.drive(hang, "location", 2, root, f"lower_{piece}", "-0.03 - 0.25 * x")
        L = 0.22 + 0.04 * (k % 2)
        cyl(f"{name}.thread{k}", thread, (0, 0, -L / 2), 0.0015, L, hang, verts=6, smooth=False)
        p = K.empty(f"{name}.{piece}", (0, 0, -L - 0.05), hang)
        pieces[piece] = p
    felt_c, felt_b, felt_g = (mat_felt(f"{name}.felt_c", "felt_cream"), mat_felt(f"{name}.felt_b", "felt_blue"),
                              mat_felt(f"{name}.felt_g", "felt_grey"))
    # A bank: stepped base, four columns, a pediment.
    b = pieces["bank"]
    box(f"{name}.bank_base", felt_g, (0, 0, -0.035), (0.11, 0.05, 0.015), b, bev=0.004)
    for i in range(4):
        cyl(f"{name}.bank_col{i}", felt_c, (-0.039 + i * 0.026, 0, 0), 0.007, 0.06, b, verts=12)
    box(f"{name}.bank_lintel", felt_g, (0, 0, 0.036), (0.11, 0.05, 0.012), b, bev=0.003)
    ped = K.mesh_obj(f"{name}.bank_ped", bpy.ops.mesh.primitive_cone_add, felt_c, b, vertices=3, radius1=0.065,
                     depth=0.05, location=(0, 0, 0.055), rotation=(math.pi / 2, 0, 0))
    ped.scale = (1, 0.42, 1)
    # A globe: blue sphere, cream meridian ring and stand.
    g = pieces["globe"]
    sphere(f"{name}.globe", felt_b, (0, 0, 0), 0.045, g)
    torus(f"{name}.globe_ring", felt_c, (0, 0, 0), 0.052, 0.004, g, rot=(0.4, 0, 0))
    # A cloud: merged soft spheres.
    c = pieces["cloud"]
    for i, (x, z, r) in enumerate(((-0.04, 0, 0.03), (0, 0.012, 0.04), (0.042, 0, 0.032), (0.012, -0.012, 0.03))):
        sphere(f"{name}.cloud{i}", felt_c, (x, 0, z), r, c, 16).scale = (1, 0.7, 1)
    # The flag: Sandbox Rhapsody's swallowtail pennant on its pole with a ball finial, in felt.
    f = pieces["flag"]
    cyl(f"{name}.flag_pole", rod, (0, 0, 0), 0.003, 0.12, f, verts=8)
    sphere(f"{name}.flag_ball", rod, (0, 0, 0.062), 0.006, f, 12)
    bm = bmesh.new()
    pts = [(0, 0, 0.055), (0.07, 0, 0.045), (0.05, 0, 0.03), (0.07, 0, 0.015), (0, 0, 0.01)]
    bm.faces.new([bm.verts.new(p) for p in pts])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.004)
    me = bpy.data.meshes.new(f"{name}.flag")
    bm.to_mesh(me)
    bm.free()
    fl = K.link(bpy.data.objects.new(f"{name}.flag", me))
    fl.parent = f
    fl.data.materials.append(felt_b)
    return root


def rocking_chair(name, loc, rot_z=0.0, parent=None):
    """An empty rocking chair in plain wood; "rock" (-1..1) tips it on its rockers about 7 degrees; a knitted
    blanket hangs over its arm ("blanket_slip" draws it down)."""
    root = K.empty(name, loc, parent)
    root.rotation_euler = (0, 0, rot_z)
    K.prop(root, "rock", 0.0, lo=-1.0, hi=1.0)
    K.prop(root, "blanket_slip", 0.2)
    piv = K.empty(f"{name}.pivot", (0, 0, 0), root)
    K.drive(piv, "rotation_euler", 0, root, "rock", "0.12 * x")
    wood = mat_paint(f"{name}.wood", "wood", 0.5)
    # Rockers: arcs of a 1.1 m radius circle under each side.
    for sx in (-1, 1):
        bm = bmesh.new()
        R, n = 1.1, 24
        prof = []
        for i in range(n + 1):
            a = -0.42 + 0.84 * i / n
            prof.append(Vector((sx * 0.24, math.sin(a) * R, R - math.cos(a) * R + 0.02)))
        ring = []
        for p in prof:
            ring.append([bm.verts.new(p + Vector(d)) for d in ((-0.015, 0, -0.02), (0.015, 0, -0.02),
                                                                (0.015, 0, 0.02), (-0.015, 0, 0.02))])
        for i in range(n):
            for j in range(4):
                bm.faces.new((ring[i][j], ring[i][(j + 1) % 4], ring[i + 1][(j + 1) % 4], ring[i + 1][j]))
        bm.faces.new(ring[0][::-1])
        bm.faces.new(ring[-1])
        me = bpy.data.meshes.new(f"{name}.rocker{sx}")
        bm.to_mesh(me)
        bm.free()
        o = K.link(bpy.data.objects.new(f"{name}.rocker{sx}", me))
        o.parent = piv
        o.data.materials.append(wood)
    for sx in (-1, 1):  # legs and arms
        for sy in (-0.18, 0.2):
            bar(f"{name}.leg{sx}{sy}", wood, (sx * 0.24, sy, 0.05), (sx * 0.23, sy, 0.45), 0.018, piv)
        bar(f"{name}.arm{sx}", wood, (sx * 0.25, -0.22, 0.66), (sx * 0.25, 0.22, 0.66), 0.02, piv)
        bar(f"{name}.armpost{sx}", wood, (sx * 0.25, -0.18, 0.45), (sx * 0.25, -0.2, 0.66), 0.016, piv)
        bar(f"{name}.backpost{sx}", wood, (sx * 0.22, 0.22, 0.45), (sx * 0.2, 0.34, 1.12), 0.02, piv)
    box(f"{name}.seat", wood, (0, 0.01, 0.46), (0.5, 0.46, 0.035), piv, bev=0.01)
    bar(f"{name}.crest", wood, (-0.21, 0.34, 1.12), (0.21, 0.34, 1.12), 0.025, piv)
    for k in range(5):  # back spindles
        x = -0.14 + k * 0.07
        bar(f"{name}.spindle{k}", wood, (x, 0.23, 0.48), (x * 0.95, 0.335, 1.1), 0.009, piv, verts=8)
    # A knitted blanket over the right arm: a folded strip.
    bm = bmesh.new()
    n = 18
    rows = []
    for i in range(n + 1):
        s = i / n
        if s <= 0.35:  # over the top of the arm, from the seat side
            x, z = 0.25 - (0.35 - s) * 0.6, 0.69
        else:  # hanging down the outside
            x, z = 0.285, 0.67 - 0.42 * ((s - 0.35) / 0.65) ** 1.3
        rows.append([bm.verts.new((x, y, z)) for y in (-0.15, -0.05, 0.05, 0.15)])
    for i in range(n):
        for j in range(3):
            bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.012)
    me = bpy.data.meshes.new(f"{name}.blanket")
    bm.to_mesh(me)
    bm.free()
    bo = K.link(bpy.data.objects.new(f"{name}.blanket", me))
    bo.parent = piv
    bo.data.materials.append(mat_felt(f"{name}.blanket", "felt_cream"))
    K.smooth(bo)
    K.drive(bo, "location", 2, root, "blanket_slip", "-0.12 * x")
    return root


def star_projector(name, loc, parent=None):
    """A star-projector night-light on a little round table: a cream dome pierced with star holes, glowing from
    inside, on a turned wooden base. The light inside is the nursery's warm night-light."""
    root = K.empty(name, loc, parent)
    wood = mat_paint(f"{name}.wood", "crib", 0.5)
    cyl(f"{name}.table_top", wood, (0, 0, 0.55), 0.24, 0.03, root, verts=64)
    cyl(f"{name}.table_leg", wood, (0, 0, 0.28), 0.03, 0.52, root, verts=16)
    cyl(f"{name}.table_foot", wood, (0, 0, 0.02), 0.16, 0.03, root, verts=48)
    cyl(f"{name}.base", K.mat_plastic(f"{name}.base", "felt_blue", 0.35), (0, 0, 0.6), 0.075, 0.06, root, verts=48)
    dome = K.mesh_obj(f"{name}.dome", bpy.ops.mesh.primitive_uv_sphere_add,
                      K.mat_acrylic(f"{name}.dome", "comfort", alpha=0.6, emit=2.5), root, radius=0.075, segments=40,
                      ring_count=20, location=(0, 0, 0.63))
    K.smooth(dome)
    dome.visible_shadow = False
    lamp = light(f"{name}.lamp", "POINT", (0, 0, 0.66), LOOK["lights"]["night_light"], "comfort", 0.04, parent=root)
    lamp.data.use_soft_falloff = True
    return root, Vector(loc) + Vector((0, 0, 0.66))


def projected_stars(origin, n, seed, count=1.0):
    """The stars on the glass (brief: "the stars are the findings"): `n` star directions from the projector, seeded,
    landing on the glass walls' and roof's inside faces as small cream glows. One mesh; each star a 5-point star
    shape, so up close they read as projected stars, not dots. `count` (0-1) keeps the first fraction (C1 shows a
    late-song wall)."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    lo, hi = Vector((-ROOM + 0.01, -ROOM + 0.01, PL_H + 0.5)), Vector((ROOM - 0.01, ROOM - 0.01, TOP - 0.01))
    placed = 0
    for i in range(n):
        # Directions: uniform over the sphere, upper half favoured (the dome's holes face up and out).
        z = rnd.uniform(-0.25, 1.0)
        a = rnd.uniform(0, math.tau)
        d = Vector((math.cos(a) * math.sqrt(1 - z * z), math.sin(a) * math.sqrt(1 - z * z), z))
        size = 0.012 + 0.03 * rnd.random() ** 2.5
        if i >= n * count:
            continue
        # First wall hit from the projector.
        ts = []
        for ax in range(3):
            if abs(d[ax]) > 1e-6:
                for bound in (lo[ax], hi[ax]):
                    t = (bound - origin[ax]) / d[ax]
                    if t > 0:
                        ts.append((t, ax, 1 if bound == hi[ax] else -1))
        t, ax, side = min(ts)
        p = origin + d * t
        if p.z < PL_H + 0.5:
            continue
        # Normal pointing into the room.
        nrm = Vector((0, 0, 0))
        nrm[ax] = -side
        p = p + nrm * 0.008
        # Stretch with obliquity: a projected star smears along the wall away from the projector.
        cosang = abs(d.dot(nrm))
        rot = nrm.to_track_quat("Z", "Y").to_matrix()
        verts = []
        for k in range(10):
            ang = k * math.pi / 5 + i
            rr = size if k % 2 == 0 else size * 0.42
            v = Vector((math.cos(ang) * rr, math.sin(ang) * rr, 0))
            verts.append(bm.verts.new(p + rot @ v))
        c = bm.verts.new(p)
        for k in range(10):
            bm.faces.new((c, verts[k], verts[(k + 1) % 10]))
        placed += 1
    me = bpy.data.meshes.new("stars_projected")
    bm.to_mesh(me)
    bm.free()
    o = K.link(bpy.data.objects.new("stars_projected", me))
    o.data.materials.append(K.mat_emission("star_proj", "comfort", LOOK["projected_star"]))
    o.visible_shadow = False
    o["placed"] = placed
    return o


def dresser(name, loc, rot_z=0.0, parent=None):
    """A low painted dresser against the right glass wall, holding the music box (Sandbox Rhapsody's, its glowing
    comb tips recoloured from amber to cream) and the baby monitor's camera, aimed at the crib."""
    root = K.empty(name, loc, parent)
    root.rotation_euler = (0, 0, rot_z)
    paint = mat_paint(f"{name}.paint", "crib", 0.5)
    box(f"{name}.body", paint, (0, 0, 0.42), (0.95, 0.46, 0.76), root, bev=0.012)
    for k in range(3):
        box(f"{name}.drawer{k}", mat_paint(f"{name}.drawer", "felt_cream", 0.5), (0, -0.233, 0.17 + k * 0.24),
            (0.88, 0.01, 0.2), root, bev=0.006)
        sphere(f"{name}.knob{k}", K.mat_chrome(f"{name}.knob"), (0, -0.245, 0.17 + k * 0.24), 0.014, root, 12)
    box(f"{name}.top", paint, (0, 0, 0.81), (1.0, 0.5, 0.025), root, bev=0.008)
    mb = K.music_box(f"{name}.musicbox", (-0.18, -0.02, 0.825), scale=1.6, rot_z=0.15, parent=root)
    for o in bpy.data.objects:
        if o.name.startswith(f"{name}.musicbox.tip") or o.name == f"{name}.musicbox.knob":
            for m in o.data.materials:
                for nd in m.node_tree.nodes:
                    if nd.type == "EMISSION":
                        nd.inputs["Color"].default_value = K.col("comfort")
                    elif nd.type == "BSDF_PRINCIPLED":
                        nd.inputs["Base Color"].default_value = K.col("felt_blue")
    bpy.data.objects[f"{name}.musicbox.glow"].data.color = K.col("comfort")[:3]
    # Recolour its lacquer case from the Lab's dark blue to the nursery's pastel, so it belongs to this room.
    case = bpy.data.objects[f"{name}.musicbox.case"]
    case.data.materials[0] = mat_paint(f"{name}.mb_case", "pastel", 0.3)
    # The baby monitor camera: a small rounded unit on a stand, a lens, a green standby pip.
    mon = K.empty(f"{name}.monitor", (0.3, 0.02, 0.825), root)
    mon.rotation_euler = (0, 0, 2.3)
    white = K.mat_plastic(f"{name}.mon", "paper", 0.25)
    cyl(f"{name}.mon_foot", white, (0, 0, 0.01), 0.04, 0.02, mon, verts=24)
    cyl(f"{name}.mon_neck", white, (0, 0, 0.06), 0.008, 0.08, mon, verts=12)
    sphere(f"{name}.mon_head", white, (0, 0, 0.12), 0.04, mon).scale = (1, 0.8, 0.85)
    cyl(f"{name}.mon_lens", K.mat_plastic(f"{name}.mon_lens", "lens", 0.05), (0, -0.032, 0.122), 0.014, 0.01, mon,
        rot=(math.pi / 2, 0, 0), verts=24)
    sphere(f"{name}.mon_pip", K.mat_emission(f"{name}.mon_pip", "standby", 12.0), (0.022, -0.03, 0.15), 0.003, mon, 8)
    return {"root": root, "musicbox": mb, "monitor": mon}


def growth_chart(name, loc, rot_z=0.0, parent=None):
    """A wooden growth-chart board leaning on the back glass: pencil marks spaced wider as they climb, crowded at
    the top, no labels (texture pass). `marks` heights are cumulative; C1 shows the late-song set."""
    root = K.empty(name, loc, parent)
    root.rotation_euler = (0.06, 0, rot_z)
    board = mat_paint(f"{name}.board", "felt_cream", 0.6)
    box(f"{name}.board", board, (0, 0, 0.95), (0.22, 0.02, 1.9), root, bev=0.006)
    ink = K.mat_matte(f"{name}.pencil", "pencil")
    for k in range(10):
        box(f"{name}.tick{k}", ink, (0.08, -0.011, 0.2 + k * 0.17), (0.05, 0.002, 0.006), root)
    # Marks: gaps grow, then crowd at the very top.
    z, gap, k = 0.35, 0.04, 0
    while z < 1.82:
        box(f"{name}.mark{k}", ink, (-0.03, -0.0115, z), (0.12, 0.002, 0.004), root)
        z += gap
        gap = gap * 1.35 if z < 1.55 else max(0.012, gap * 0.45)
        k += 1
    return root


def rug(name, loc, r, parent=None):
    o = cyl(name, mat_felt(name, "rug"), loc, r, 0.012, parent, verts=96)
    o.scale = (1, 0.8, 1)
    return o


def nursery(room):
    """Everything inside the glass room. Room-local coordinates (z 0 = the nursery floor)."""
    out = {}
    rug("nursery.rug", (0, 0.2, 0.006), 1.35, room)
    c = crib("crib", (0.35, 1.05, 0), rot_z=0.0, parent=room)
    out["crib"] = c
    out["mobile"] = mobile("mobile", (0.35 - 0.2, 1.05, 1.72), room)
    # The mobile's arm: up from the crib's back rail, over to the mobile.
    paint = mat_paint("mobile.arm", "crib", 0.4)
    bar("mobile.mast", paint, (0.35 - 0.62, 1.05 + 0.36, 0.95), (0.35 - 0.62, 1.05 + 0.36, 1.82), 0.012, room)
    bar("mobile.boom", paint, (0.35 - 0.62, 1.05 + 0.36, 1.82), (0.35 - 0.2, 1.05, 1.76), 0.01, room)
    proj, proj_pt = star_projector("projector", (-1.25, 1.2, 0), room)
    out["projector"] = proj
    out["projector_pt"] = Vector((proj_pt.x, proj_pt.y, proj_pt.z + PL_H))
    out["chair"] = rocking_chair("chair", (-1.15, -0.85, 0), rot_z=math.radians(-150), parent=room)
    out.update({f"dresser_{k}": v for k, v in dresser("dresser", (1.62, 0.15, 0), rot_z=math.pi / 2, parent=room).items()})
    out["growth"] = growth_chart("growth", (-0.6, 1.93, 0), parent=room)
    # The nursery's low fill: soft cream from above the crib, so the room reads from outside without the hall's
    # blue taking over (the night-light alone left the crib a silhouette).
    light("nursery.fill", "AREA", (0, 0.4, ROOM_H - 0.15), LOOK["lights"]["nursery_fill"], "comfort", 2.4,
          target=(0, 0.4, 0), specular=0.2, parent=room)
    return out


# ---------------------------------------------------------------- the street and the shop window

def street():
    """Outside the tall window: a night sky, the moon, a hill of small houses with porch lights, and the neighbor's
    upstairs window (amber, "amber" 0-1). The hill rises from y 30 to 70, so through the window it fills the lower
    two-thirds."""
    out = {}
    sky = K.mesh_obj("street.sky", bpy.ops.mesh.primitive_plane_add, None, None, size=1, location=(0, 95, 25),
                     rotation=(math.pi / 2, 0, 0))
    sky.scale = (260, 90, 1)
    m = bpy.data.materials.new("sky")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.35, K.col("sky")
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.75, K.col("void")
    nt.links.new(sep.outputs["Y"], ramp.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 2.5
    nt.links.new(ramp.outputs[0], em.inputs["Color"])
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], o.inputs[0])
    sky.data.materials.append(m)
    sky.visible_shadow = False
    moon = sphere("street.moon", K.mat_emission("moon", "moon", 6.0), MOON_AT, 2.0, None, 32)
    moon.visible_shadow = False
    # The hill: a broad ridge, highest behind the window, falling away to the sides.
    bm = bmesh.new()
    nx, ny = 60, 20
    vs = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = -90 + 180 * i / nx
            y = 28 + 45 * j / ny
            h = HILL * math.exp(-(x / 45) ** 2) * (j / ny) ** 0.8 + 1.5 * math.sin(x * 0.09) * (j / ny)
            vs[i, j] = bm.verts.new((x, y, h - 0.5))
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
    me = bpy.data.meshes.new("street.hill")
    bm.to_mesh(me)
    bm.free()
    hill = K.link(bpy.data.objects.new("street.hill", me))
    hill.data.materials.append(mat_stone("hill", "hill", 0.9))

    def ground(x, y):
        j = (y - 28) / 45
        return HILL * math.exp(-(x / 45) ** 2) * max(j, 0) ** 0.8 + 1.5 * math.sin(x * 0.09) * max(j, 0) - 0.5

    # Houses: a row climbing the hill, each a box with a gabled roof, a porch light and a couple of windows.
    wall = mat_stone("house_wall", "house_wall", 0.8)
    roof_m = mat_stone("house_roof", "hill", 0.7)
    porch = K.mat_emission("porch", "comfort", 22.0)
    win_dim = K.mat_emission("house_win", "comfort", 1.2)
    homes = [(-22, 46), (-13, 50), (-5, 53), (1.5, 50), (13.1, 56), (7, 53), (17, 48), (25, 45), (-9, 63),
             (8.5, 65), (2, 62), (14, 61), (-1.5, 59)]
    neighbor = 4  # (13.1, 56): framed by the tall window from the wide C1 camera
    for k, (x, y) in enumerate(homes):
        g = ground(x, y)
        w, d, hh = 3.2, 2.6, 3.0 + (1.6 if k == neighbor else 0.6 * (k % 2))
        box(f"house{k}.body", wall, (x, y, g + hh / 2), (w, d, hh))
        rf = K.mesh_obj(f"house{k}.roof", bpy.ops.mesh.primitive_cone_add, roof_m, None, vertices=4,
                        radius1=w * 0.8, depth=1.4, location=(x, y, g + hh + 0.7), rotation=(0, 0, math.pi / 4))
        rf.scale = (1, d / w, 1)
        p = sphere(f"house{k}.porch", porch, (x + 0.8, y - d / 2 - 0.15, g + 1.0), 0.09, None, 12)
        p.visible_shadow = False
        if k % 3 == 1:
            box(f"house{k}.win", win_dim, (x - 0.7, y - d / 2 - 0.01, g + 1.4), (0.6, 0.02, 0.5))
        if k == neighbor:
            root = K.empty("neighbor", (x, y, g))
            K.prop(root, "amber", 1.0)
            wm = K.mat_emission("neighbor_win", "amber", 18.0, root, "amber", floor=0.0)
            box("neighbor.window", wm, (x + 0.6, y - d / 2 - 0.01, g + hh - 0.9), (0.7, 0.02, 0.6))
            box("neighbor.sill", mat_stone("sill_n", "house_wall", 0.6), (x + 0.6, y - d / 2 - 0.06, g + hh - 1.22),
                (0.85, 0.1, 0.05))
            out["neighbor"] = root
    return out


def shop_window():
    """Across the hall in the +X wall: a lit display window with flat fluorescent white light, an identical crib with
    a green glint under its blanket, a price tag on the rail (COMING SOON) and a small dark screen for verse 4's
    real pages. The twin probe and its mittens are built at C2 with the kit."""
    out = {}
    root = K.empty("shop", (11.0, 0, 0))
    commerce = mat_stone("shop.wall", "commerce", 0.7)
    D = 1.8
    box("shop.floor", mat_stone("shop.floor", "felt_grey", 0.6), (D / 2, 0, 0.55), (D, 3.6, 0.1), root)
    box("shop.back", commerce, (D + 0.05, 0, 1.8), (0.1, 3.6, 2.6), root)
    box("shop.ceil", commerce, (D / 2, 0, 3.05), (D, 3.6, 0.1), root)
    for s in (-1, 1):
        box(f"shop.side{s}", commerce, (D / 2, s * 1.85, 1.8), (D, 0.1, 2.6), root)
    steel = mat_steel("shop.frame")
    box("shop.frame_top", steel, (0.02, 0, 3.02), (0.06, 3.7, 0.06), root)
    box("shop.frame_low", steel, (0.02, 0, 0.6), (0.06, 3.7, 0.06), root)
    glass = K.mat_glass("shop.glass", reflect=0.35)
    pg = K.mesh_obj("shop.glass", bpy.ops.mesh.primitive_plane_add, glass, root, size=1, location=(0.02, 0, 1.8),
                    rotation=(math.pi / 2, 0, math.pi / 2))
    pg.scale = (3.6, 2.4, 1)
    pg.visible_shadow = False
    c = crib("shop.crib", (0.95, 0.35, 0.6), rot_z=math.pi / 2, parent=root)
    out["crib"] = c
    tag = K.empty("shop.tag", (0.6, 0.35 - 0.6, 0.6 + 0.8), root)
    tag.rotation_euler = (math.pi / 2, 0, -math.pi / 2 + 0.1)
    K.mesh_obj("shop.tag_card", bpy.ops.mesh.primitive_plane_add, K.mat_matte("tag", "paper"), tag, size=0.2).scale = (
        1.0, 0.55, 1)
    K.text("shop.tag_text", "COMING\nSOON", 0.035, K.mat_ink("tag_ink", "shadow"), loc=(0, 0, 0.001), rot=(0, 0, 0),
           font="Inter-Medium-flat.ttf", parent=tag)
    # The display screen (dark until verse 4) on a small easel to the left.
    scr = box("shop.screen", K.mat_plastic("shop.screen", "lens", 0.05), (1.3, -1.1, 1.55), (0.04, 0.9, 0.55), root,
              bev=0.01)
    out["screen"] = scr
    for k in range(3):  # fluorescent tubes in the ceiling
        tube = cyl(f"shop.tube{k}", K.mat_emission("shop.tube", "commerce", 6.0), (0.4 + k * 0.55, 0, 2.97), 0.02,
                   3.2, root, rot=(math.pi / 2, 0, 0), verts=12)
        tube.visible_shadow = False
    light("shop.light", "AREA", (11.0 + D / 2, 0, 2.9), LOOK["lights"]["shop"], "commerce", 1.6, target=(11.0 + D / 2, 0, 0),
          specular=0.4)
    # The receiver of the baby monitor, on the display floor (texture pass: someone else is listening).
    rx = K.empty("shop.receiver", (0.5, -0.5, 0.6), root)
    white = K.mat_plastic("shop.receiver", "paper", 0.3)
    box("shop.receiver_body", white, (0, 0, 0.06), (0.05, 0.08, 0.12), rx, bev=0.012)
    box("shop.receiver_screen", K.mat_emission("shop.rx_screen", "fill", 2.0), (-0.026, 0, 0.075), (0.002, 0.06, 0.05),
        rx)
    out["root"] = root
    return out


# ---------------------------------------------------------------- lighting and air

def hall_lights():
    """The hall's cold museum light: two dim spots from the ceiling on the plinth, a moonlight sun through the tall
    window (it lays the window's patch on the floor: the moonlight clock), faint cool rims behind the glass room so
    its frame reads against the dark."""
    L = LOOK["lights"]
    out = {}
    for k, (x, y) in enumerate(((-3.5, -4.0), (3.0, 3.0))):
        light(f"hall.spot{k}", "SPOT", (x, y, 8.6), L["hall_spot"], "key", 0.3, target=(0, 0, PL_H), spot=(0.55, 0.6),
              specular=0.5)
    # Moon: low, from behind the window, so its patch starts near the window's base (N02) and creeps forward.
    moon = light("hall.moon", "SUN", (0, 30, 20), L["moon"], "moon", 0.01, target=(0, 6.0, 0))
    out["moon"] = moon
    # A faint front light on the vault door, so its pastel reads as pastel, not as the hall's navy.
    light("hall.door_key", "AREA", (0.6, -6.5, 2.6), L["door_key"], "moon", 2.0, target=(0, -ROOM, 1.5), specular=0.3)
    for k, (x, y) in enumerate(((-4.0, 5.5), (4.5, 5.0))):
        light(f"hall.rim{k}", "AREA", (x, y, 3.2), 300, "rim", 1.2, target=(0, 0, 1.6), specular=0.25)
    return out


def haze(density):
    """Faint air in the hall so the moonlight through the tall window and the projector's glow read as beams."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1, 4.5))
    o = bpy.context.active_object
    o.name = "hall.haze"
    o.scale = (22, 26, 9)
    m = bpy.data.materials.new("haze")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = density
    v.inputs["Color"].default_value = K.col("frost")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(v.outputs[0], out.inputs["Volume"])
    o.data.materials.append(m)
    o.visible_shadow = False
    return o


def build(star_count=1.0):
    """The whole set; returns a dict of named rigs for the shot scripts."""
    S = {}
    S.update(hall())
    S.update(plinth())
    S.update(glass_room())
    S.update(nursery(S["root"]))
    S["stars"] = projected_stars(S["projector_pt"], 320, SEEDS["main"], star_count)
    S.update({f"street_{k}": v for k, v in street().items()})
    S.update({f"shop_{k}": v for k, v in shop_window().items()})
    S.update(hall_lights())
    if LOOK.get("haze_density"):
        S["haze"] = haze(LOOK["haze_density"])
    return S
