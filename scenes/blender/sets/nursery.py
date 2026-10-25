"""The one set (brief, "The set"): a glass nursery on a low plinth in a dark, museum-like hall, with the street through
a four-pane window at the back and the shop window across the hall.

Layout (metres, Z up, the camera's push starts at -Y):
  hall        x -11..11, y -14..12, ceiling 9; a four-pane window in the back wall (+Y), a smaller one in the front
  plinth      5.6 m square, 0.4 m high, centred on the origin; the glass room stands on it
  glass room  4 m square, 2.8 m high (x, y -2..2, z 0.4..3.2); the vault door in its front (-Y) wall
  shop window in the +X wall at y 0, facing the glass room
  street      outside the back window: a hill of small houses, y 40..70

Everything is procedural. The only random process is the star scatter, seeded from config/seeds.json. Rigs expose
custom properties for the note-driven library (sr_anim), all 0-1 unless noted:
  room root  "frost" (1 = full band, 0 = clear glass)
  crib       "breath" (blanket rise), "glint" (the probe's LED through the blanket)
  chair      "rock" (-1..1, the rocking angle), "blanket_slip"
  door       "open" (0 shut .. 1 = a crack, 20 degrees: wide enough for the camera to pass the free edge)
  note       "peel" (0 flat .. 1 lifted), on the glass beside the door
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
HILL = 8.0          # the street's hill: low enough that sky silhouettes the back window's cross mullion
MOON_AT = (-18.5, 94.0, 23.3)  # in the back window's upper-left pane from inside the room (the bridge, N23-N27)
WINDOW_X = -1.0     # the back window's centre


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


FREEZE_S = json.loads((K.ROOT / "config" / "shot_anchors.json").read_text())["outro"]["freeze"]


def mat_reveal(name, role, strength, fade=0.25, dim_to=0.15, dim_fade=1.5):
    """Emitter for things that appear one piece at a time (the stars, the call graph, the town's crack, the floor
    gaps): each face carries float attributes "birth" and "dim" (song seconds); the shader compares them with the
    song time T, driven from the frame and clamped at the pen scratch (FREEZE_S: the stars freeze, N39). Before its
    birth a face is fully transparent; it fades in over `fade` s; after "dim" it fades to `dim_to` over `dim_fade` s."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()

    def attr(nm):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_type, a.attribute_name = "GEOMETRY", nm
        return a.outputs["Fac"]

    tv = nt.nodes.new("ShaderNodeValue")
    tv.name = "T"
    fc = tv.outputs[0].driver_add("default_value")
    fc.driver.type = "SCRIPTED"
    fc.driver.expression = f"min(frame / {LOOK['fps']}, {FREEZE_S})"

    def ramp(x, a, b):  # clamp((x - a) / (b - a)) built from math nodes; a, b are sockets or floats
        sub = nt.nodes.new("ShaderNodeMapRange")
        sub.clamp = True
        nt.links.new(x, sub.inputs["Value"])
        for sock, v in (("From Min", a), ("From Max", b)):
            if isinstance(v, (int, float)):
                sub.inputs[sock].default_value = v
            else:
                nt.links.new(v, sub.inputs[sock])
        return sub.outputs[0]

    def add(x, c):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = "ADD"
        nt.links.new(x, n.inputs[0])
        n.inputs[1].default_value = c
        return n.outputs[0]

    birth, dim = attr("birth"), attr("dim")
    on = ramp(tv.outputs[0], birth, add(birth, fade))
    off = ramp(tv.outputs[0], dim, add(dim, dim_fade))
    k = nt.nodes.new("ShaderNodeMapRange")  # 1 -> dim_to as off goes 0 -> 1
    nt.links.new(off, k.inputs["Value"])
    k.inputs["To Min"].default_value, k.inputs["To Max"].default_value = 1.0, dim_to
    lvl = nt.nodes.new("ShaderNodeMath")
    lvl.operation = "MULTIPLY"
    nt.links.new(on, lvl.inputs[0])
    nt.links.new(k.outputs[0], lvl.inputs[1])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = K.col(role)
    st = nt.nodes.new("ShaderNodeMath")
    st.operation = "MULTIPLY"
    nt.links.new(lvl.outputs[0], st.inputs[0])
    st.inputs[1].default_value = strength
    nt.links.new(st.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(on, mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix.outputs[0], out.inputs[0])
    m.surface_render_method = "BLENDED"
    return m


def set_times(obj, births, dims=None, per=None):
    """Write per-face "birth" and "dim" attributes. births/dims are per element; `per` maps each face to its element
    (default: one element per face)."""
    me = obj.data
    nf = len(me.polygons)
    per = per or list(range(nf))
    for nm, vals in (("birth", births), ("dim", dims)):
        a = me.attributes.get(nm) or me.attributes.new(nm, "FLOAT", "FACE")
        a.data.foreach_set("value", [float((vals[i] if vals is not None and i < len(vals) else 1e6)) for i in per])


def ribbon_mesh(name, segments, width, lift=Vector((0, 0, 0))):
    """Thin flat ribbons for line drawings (cracks, graph edges): `segments` is a list of (a, b, normal) triples.
    Returns the object and, per face, its segment index."""
    bm = bmesh.new()
    per = []
    for i, (a, b, nrm) in enumerate(segments):
        d = (b - a).normalized()
        side = d.cross(nrm).normalized() * width / 2
        bm.faces.new([bm.verts.new(v + lift) for v in (a - side, b - side, b + side, a + side)])
        per.append(i)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return K.link(bpy.data.objects.new(name, me)), per


# ---------------------------------------------------------------- primitives

def box(name, mat, loc, size, parent=None, bev=0.0, rot=(0, 0, 0)):
    o = K.mesh_obj(name, bpy.ops.mesh.primitive_cube_add, mat, parent, size=1, location=loc, rotation=rot)
    o.scale = size
    if bev:
        K.bevel(o, bev, 2)
    return o


def soft_box(name, mat, loc, size, parent=None, rot=(0, 0, 0), level=1):
    """A box with well-rounded edges, a soft stuffed shape (the maintainer's felt-doll body parts): the size goes
    into the mesh (so the rounding is even on every edge), then a wide bevel and one level of subdivision."""
    o = box(name, mat, loc, (1, 1, 1), parent, rot=rot)
    o.data.transform(Matrix.Diagonal((size[0], size[1], size[2], 1.0)))
    bv = o.modifiers.new("round", "BEVEL")
    bv.width, bv.segments, bv.limit_method = 0.42 * min(size), 4, "NONE"
    if level:
        sd = o.modifiers.new("soft", "SUBSURF")
        sd.levels = sd.render_levels = level
    K.smooth(o)
    return o


def boxes_obj(name, mat, extents):
    """One object made of several axis-aligned boxes, each given as ((x0, y0, z0), (x1, y1, z1)) in world space."""
    bm = bmesh.new()
    for a, b in extents:
        c = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2]
        m = Matrix.Translation(c) @ Matrix.Diagonal((b[0] - a[0], b[1] - a[1], b[2] - a[2], 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=m)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = K.link(bpy.data.objects.new(name, me))
    o.data.materials.append(mat)
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

def crack(name, mat, origin, length, seed, parent=None, branches=2):
    """A hairline crack in a pane (local XZ plane, Y toward the viewer): a jagged ribbon from `origin` with a couple of
    short branches. "grow" (0-1) on the returned root reveals it from its origin outward (N10's new crack)."""
    rnd = random.Random(seed)
    root = K.empty(name, origin, parent)
    K.prop(root, "grow", 1.0)
    bm = bmesh.new()

    def ribbon(p, ang, L, w):
        pts = [p]
        n = 9
        for _ in range(n):
            ang += rnd.uniform(-0.55, 0.55)
            p = p + Vector((math.cos(ang), 0, math.sin(ang))) * (L / n)
            pts.append(p)
        for a, b in zip(pts, pts[1:]):
            d = (b - a).normalized()
            nrm = Vector((-d.z, 0, d.x)) * w
            bm.faces.new([bm.verts.new(v) for v in (a - nrm, b - nrm, b + nrm, a + nrm)])
        return pts

    main = ribbon(Vector((0, 0, 0)), rnd.uniform(0, math.tau), length, 0.0022)
    for k in range(branches):
        at = main[rnd.randint(2, 7)]
        ribbon(at, rnd.uniform(0, math.tau), length * 0.35, 0.0015)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = K.link(bpy.data.objects.new(f"{name}.lines", me))
    o.parent = root
    o.data.materials.append(mat)
    o.visible_shadow = False
    K.drive(o, "scale", 0, root, "grow", "max(x, 0.001)")
    K.drive(o, "scale", 2, root, "grow", "max(x, 0.001)")
    return root


def cross_window(name, wall_y, cx, z0, size, mull, steel, facing=-1, glazed=False, backdrop=None, reflect=0.4):
    """A square window of four panes split by a heavy cross mullion: a plain sash form, never coloured, tilted or
    waved, so it stays generic (brief: no real logos). It carries the chorus's "windows" (human, C1 review: the grid
    window made the play on the word hard to stage). `facing` is the side the hall sees (-1 = its -Y face). Returns
    {"panes": [centre of each pane, upper-left first], ...}."""
    out = {}
    h = size / 2
    zc = z0 + h
    t = 0.12  # outer frame
    y = wall_y + facing * 0.12
    for k, (dx, dz, sx, sz) in enumerate(((0, h, size + t, t), (0, -h, size + t, t), (-h, 0, t, size + t),
                                          (h, 0, t, size + t))):
        box(f"{name}.frame{k}", steel, (cx + dx, y, zc + dz), (sx, 0.14, sz))
    box(f"{name}.mullion_v", steel, (cx, y, zc), (mull, 0.12, size))
    box(f"{name}.mullion_h", steel, (cx, y, zc), (size, 0.12, mull))
    box(f"{name}.sill", mat_stone(f"{name}.sill", "plinth", 0.5), (cx, y + facing * 0.12, z0 - t / 2 - 0.03),
        (size + 0.4, 0.3, 0.06))
    q = (h + mull / 2) / 2
    out["panes"] = [(cx - q, zc + q), (cx + q, zc + q), (cx - q, zc - q), (cx + q, zc - q)]
    if glazed:
        g = K.mesh_obj(f"{name}.glass", bpy.ops.mesh.primitive_plane_add, K.mat_glass(f"{name}.glass", reflect=reflect),
                       None, size=1, location=(cx, y, zc), rotation=(math.pi / 2, 0, 0))
        g.scale = (size, size, 1)
        g.visible_shadow = False
    if backdrop:
        b = box(f"{name}.backdrop", backdrop, (cx, wall_y - facing * 0.25, zc), (size, 0.02, size))
        b.visible_shadow = False
    return out


def wall_with_opening(name, mat, axis_y, x0, x1, z0, z1, H=9.0, span=(-11.0, 11.0)):
    """A hall wall at y = axis_y with one rectangular opening (x0..x1, z0..z1)."""
    a, b = span
    for nm, u0, u1 in (("l", a, x0), ("r", x1, b)):
        box(f"{name}_{nm}", mat, ((u0 + u1) / 2, axis_y, H / 2), (u1 - u0, 0.3, H))
    box(f"{name}_low", mat, ((x0 + x1) / 2, axis_y, z0 / 2), (x1 - x0, 0.3, z0))
    box(f"{name}_high", mat, ((x0 + x1) / 2, axis_y, (z1 + H) / 2), (x1 - x0, 0.3, H - z1))


def hall():
    """Dark polished floor, tall dark walls and ceiling. The back wall (+Y) holds a big four-pane window onto the
    street; the front wall (-Y), behind the camera's start, holds a smaller one with a cracked pane taped over (N09)
    and the hairline crack that appears beside the tape (N10, "grow")."""
    out = {}
    # The hall floor (80 m) with a hole the plinth's size: the cutaway passes through the plinth (hollow, see
    # plinth()), never through the hall floor, so nothing under the hall can show (human, C4 review: N18-N19).
    s_ = 2.8
    bm = bmesh.new()
    for x0, x1, y0, y1 in ((-40, 40, -40, -s_), (-40, 40, s_, 40), (-40, -s_, -s_, s_), (s_, 40, -s_, s_)):
        bm.faces.new([bm.verts.new(v) for v in ((x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0))])
    me = bpy.data.meshes.new("floor")
    bm.to_mesh(me)
    bm.free()
    fl = K.link(bpy.data.objects.new("floor", me))
    fl.data.materials.append(mat_stone("hall_floor", "floor", LOOK["materials"]["floor_roughness"]))
    wall = mat_stone("hall_wall", "hall_wall", 0.85)
    H = 9.0
    box("hall.ceiling", wall, (0, -1, H + 0.15), (22.6, 26.6, 0.3))
    box("hall.wall_l", wall, (-11.15, -1, H / 2), (0.3, 26.6, H))
    # The +X wall with the shop window's opening (y -1.8..1.8, z 0.6..3.0).
    for nm, y0, y1 in (("a", -14, -1.8), ("b", 1.8, 12)):
        box(f"hall.wall_r{nm}", wall, (11.15, (y0 + y1) / 2, H / 2), (0.3, y1 - y0, H))
    box("hall.wall_r_low", wall, (11.15, 0, 0.3), (0.3, 3.6, 0.6))
    box("hall.wall_r_high", wall, (11.15, 0, (3.0 + H) / 2), (0.3, 3.6, H - 3.0))
    steel = mat_steel("window_steel")
    # The back window: 4.4 m square, sill at 1.2 m, left of centre so the wide view sees it clear of the room.
    bx, bz, bs = WINDOW_X, 1.2, 4.4
    wall_with_opening("hall.wall_back", wall, 12.15, bx - bs / 2, bx + bs / 2, bz, bz + bs)
    # Glazed faintly since the C4 review, to carry the same taped pane as the front window (below).
    out["window_panes"] = cross_window("window", 12.15, bx, bz, bs, 0.16, steel, facing=-1, glazed=True,
                                       reflect=0.12)["panes"]
    out["window"] = (bx, 12.0, bz + bs / 2)
    # The front window, behind the camera: 2.2 m square, glazed. Since the C4 review it is seen from outside too
    # (N10: the one cut, then the move comes in through it), so there is no backdrop behind it: the night sky is a
    # far plane outside, the wall's outer face gets a faint cold fill, and from outside the hall shows through.
    fx, fz, fs = -4.0, 1.5, 2.2
    wall_with_opening("hall.wall_front", wall, -14.15, fx - fs / 2, fx + fs / 2, fz, fz + fs)
    fw = cross_window("hallwin", -14.15, fx, fz, fs, 0.1, steel, facing=1, glazed=True)
    sky = box("hallwin.sky", K.mat_emission("hallwin_glow", "sky", 0.6), (0, -45.0, 10.0), (120, 0.1, 40))
    sky.visible_shadow = False
    light("hallwin.outside_fill", "AREA", (fx, -19.5, fz + 3.5), 150.0, "sky", 4.0, target=(fx, -14.3, fz + fs / 2),
          specular=0.2)
    # The cracked pane: the upper pane at +X, seen from outside at the upper right (as in the C1 hall-window frame
    # the human picked for the cut), taped with an X on its outer face over the old crack; the new crack starts
    # beside the tape. Tape and cracks sit just outside the glass, so they read from both sides.
    tape = K.mat_matte("tape", "paper")
    tb = tape.node_tree.nodes["Principled BSDF"]
    tb.inputs["Emission Color"].default_value = K.col("paper")
    tb.inputs["Emission Strength"].default_value = 0.12  # the hall light barely reaches it; tape must read as tape
    crack_m = K.mat_emission("crack", "frost", 1.4)
    out["crack_new"] = taped_pane("hallwin", fw["panes"][1], -14.15 + 0.12, -1, 1.0, tape, crack_m)
    # Continuity (human, C4 review): the back window, the one seen from the nursery after the cut, carries the same
    # taped pane, upper right from inside, and its new crack grows with the front one's and stays.
    out["crack_new_back"] = taped_pane("window", out["window_panes"][1], 12.15 - 0.12, -1, 2.0, tape, crack_m)
    return out


def taped_pane(name, pane, glass_y, side, scale, tape, crack_m):
    """An X of tape over an old crack on one pane, and the new hairline crack beside it ("grow" on the returned root,
    0 at first). `side` is the face (-1 = the -Y side) the tape is stuck on, just off the glass at glass_y; `scale`
    sizes it to the pane (1 for the front window's 1 m panes)."""
    px, pz = pane
    y = glass_y + side * 0.006
    for k, a in enumerate((0.7, -0.7)):
        box(f"{name}.tape{k}", tape, (px, y, pz), (0.95 * scale, 0.004, 0.06 * scale), rot=(0, a, 0))
    seed = SEEDS["main"]
    yc = glass_y + side * 0.003
    crack(f"{name}.crack_old", crack_m, (px - 0.05 * scale, yc, pz - 0.03 * scale), 0.42 * scale, seed)
    new = crack(f"{name}.crack_new", crack_m, (px + 0.2 * scale, yc, pz - 0.28 * scale), 0.3 * scale, seed + 1)
    new["grow"] = 0.0
    return new


def plinth():
    """The low plinth (5.6 m square, 0.4 m) in dark stone with a steel edge band, and the slit of tungsten light
    from the basement under its front edge (N28)."""
    out = {}
    s = 2.8
    # Hollow (C4 review): a top slab (the nursery floor, "plinth": the cutaway hides only it) on four side walls
    # down to the basement's collar, so from inside, between the floors, the eye sees stone, not the hall.
    stone = mat_stone("plinth", "plinth", 0.6)
    out["plinth"] = box("plinth", stone, (0, 0, PL_H - 0.03), (2 * s, 2 * s, 0.06), bev=0.005)
    for k, (p, sz) in enumerate((((0, -s + 0.04, PL_H / 2 - 0.04), (2 * s, 0.08, PL_H + 0.08)),
                                 ((0, s - 0.04, PL_H / 2 - 0.04), (2 * s, 0.08, PL_H + 0.08)),
                                 ((-s + 0.04, 0, PL_H / 2 - 0.04), (0.08, 2 * s, PL_H + 0.08)),
                                 ((s - 0.04, 0, PL_H / 2 - 0.04), (0.08, 2 * s, PL_H + 0.08)))):
        box(f"plinth.side{k}", stone, p, sz, bev=0.005)
    steel = mat_steel("plinth_band")
    zb = PL_H - 0.025  # its top 5 mm under the stone's: level with it, the two z-fought (QC 2026-10-25)
    for k, (p, sz) in enumerate((((0, -s, zb), (2 * s + 0.02, 0.012, 0.04)),
                                 ((0, s, zb), (2 * s + 0.02, 0.012, 0.04)),
                                 ((-s, 0, zb), (0.012, 2 * s + 0.02, 0.04)),
                                 ((s, 0, zb), (0.012, 2 * s + 0.02, 0.04)))):
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
    # The door itself, on a hinge at the opening's left edge; "open" swings it inward up to 20 degrees.
    hinge = K.empty("door.hinge", (-R, y, zc), room)
    root = K.empty("door", (0, 0, 0), None)
    K.prop(root, "open", 0.0)
    K.prop(root, "note_peel", 0.0)
    K.drive(hinge, "rotation_euler", 2, root, "open", "-0.3491 * x")
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
    # The sticky note, a little crooked, on the glass beside the door (brief, section 3: "on the nursery's glass
    # door"): it reads from outside (N07) and, printed on both sides, from inside, peeling (N21); it falls at N35. It hangs
    # from its top edge (the pivot), so "peel" lifts it away from the glass.
    note = K.empty("note", (1.13, y - 0.004, 1.36), room)  # room-local: its middle at world z 1.66
    K.prop(note, "peel", 0.0)
    K.drive(note, "rotation_euler", 0, note, "peel", "1.5708 - 0.9 * x")
    note.rotation_euler = (math.pi / 2, 0.06, 0)
    out["note"] = note
    paper = K.empty("note.paper_root", (0, -0.1, 0), note)
    K.mesh_obj("note.paper", bpy.ops.mesh.primitive_plane_add, K.mat_matte("sticky", "note"), paper, size=0.2)
    K.text("note.text", "NOT FOR\nTHE PUBLIC :)", 0.036, K.mat_ink("note_ink", "shadow"), loc=(0, 0, 0.0012),
           rot=(0, 0, 0), font="InstrumentSerif-Italic.ttf", parent=paper)  # faces out
    # The same words on the back, reading the right way from inside (human, C4 review: N20-N21 must read).
    K.text("note.text_back", "NOT FOR\nTHE PUBLIC :)", 0.036, K.mat_ink("note_ink", "shadow"), loc=(0, 0, -0.0012),
           rot=(0, math.pi, 0), font="InstrumentSerif-Italic.ttf", parent=paper)
    return out


# ---------------------------------------------------------------- the nursery

def nest_z(r):
    """Crib-local height of a probe's centre (radius r) resting in the blanket's nest (crib(nest=...))."""
    return 0.455 + r + 0.001


def crib(name, loc, rot_z=0.0, parent=None, glint=True, nest=None, cover=None, quilt=None):
    """A painted crib (1.3 x 0.7 m, rails 0.95 m) with a mattress and a blanket that breathes ("breath"). Under the
    blanket's head end, the probe's green LED shows as a glint ("glint"); the probe itself is not built here (C2).
    nest = (x, y, r): a shape key "nest" (0 the plain hump .. 1) presses a cup into the blanket for a sphere of radius r
    at crib-local (x, y, nest_z(r)), the felt rising to its equator: the reveal's probe lies in it (N38) instead of
    passing through the felt (human, C4 review). cover = (x, y, r): the blanket is a mound over such a sphere, so
    the shop twin's chassis stays covered while its arms come out from under it. quilt = (x, y, r), with a nest: two
    folds of quilt lie closed over the nest, a mound hiding the sphere; "open" (0..1) turns them back, the front one
    toward the room (-Y) and the back one away, flattening as they go (the reveal, N38: the probe opens them with its
    arms; human, C4 v2 review). They pivot outside the sphere, so no fold passes through it."""
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
        # A low arched top: a disc the width of the end, flattened to rise 10 cm (local X is world Z here). 2.4 cm
        # thick inside the board's 3 cm, so its caps sit 3 mm inside the board's faces: at the same thickness they
        # lay in them and z-fought (QC 2026-10-25, the shop crib at N31).
        cyl(f"{name}.arch{sx}", paint, (sx * L / 2, 0, 0.93), W / 2, 0.024, root, rot=(0, math.pi / 2, 0),
            verts=64).scale = (0.3, 1, 1)
    box(f"{name}.mattress", K.mat_plastic(f"{name}.mattress", "felt_cream", 0.8), (0, 0, 0.38), (L - 0.06, W - 0.06, 0.12),
        root, bev=0.04)
    # The blanket: a soft slab over the mattress, its middle raised over the hidden probe at the head end; breath
    # lifts it.
    bm = bmesh.new()
    nx, ny = (78, 42) if (nest or cover) else (26, 14)  # fine enough to hug a 20 cm sphere

    def flat(u, v):
        drape = -0.07 * (abs(v - 0.5) * 2) ** 6  # the sides fall over the mattress edge
        ripple = 0.006 * math.sin(u * 23.0 + v * 7.0) * math.sin(v * 11.0)
        return 0.45 + drape + ripple

    def hump_w(u, v):
        return math.exp(-((u - 0.28) / 0.17) ** 2 - ((v - 0.5) / 0.28) ** 2)

    def xy(u, v):
        return (u - 0.5) * (L - 0.1), (v - 0.5) * (W - 0.02)

    def rest_z(u, v):
        if cover:
            # The felt drapes over the sphere and falls to the mattress in folds: ripples around the skirt, zero
            # over the top and the sphere's sides (so they never cut into it) and out on the flat blanket.
            cx, cy, r = cover
            x, y = xy(u, v)
            d = math.hypot(x - cx, y - cy)
            a = math.atan2(y - cy, x - cx)
            dome = (2 * r + 0.03) * math.exp(-(d / (1.35 * r)) ** 3)
            skirt = max(0.0, min((d - 1.05 * r) / (0.35 * r), 1.0)) * math.exp(-((d - 1.5 * r) / (0.6 * r)) ** 2)
            ph = 7 * a + 1.4 * math.sin(3 * a) + 0.5
            folds = 0.026 * skirt * math.sin(ph) * (0.7 + 0.3 * math.sin(2 * a))
            # Over the dome, raised ridges only (they lift the felt off the sphere, never into it), fading in from
            # the top and running down into the skirt's folds.
            top = max(0.0, min((d - 0.35 * r) / (0.6 * r), 1.0)) * (1.0 - skirt)
            ridges = 0.03 * top * (0.5 + 0.5 * math.sin(ph)) ** 2
            return flat(u, v) + dome + folds + ridges
        return flat(u, v) + 0.07 * hump_w(u, v)

    def nest_top(u, v):
        cx, cy, r = nest
        x, y = xy(u, v)
        d = math.hypot(x - cx, y - cy)
        c, rc = nest_z(r), r + 0.003
        if d < rc:
            return c - math.sqrt(rc * rc - d * d) - 0.004
        return flat(u, v) + (c - flat(u, v)) * math.exp(-((d - rc) / 0.07) ** 2)

    vs = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            u, v = i / nx, j / ny
            x, y = xy(u, v)
            vs[i, j] = bm.verts.new((x, y, rest_z(u, v)))
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
    # Breathing: a shape key that raises the hump 2 cm, driven by "breath". With a nest, the lift is even across the
    # nest (its centre's weight), so a probe lying in it rides the breath without the felt passing through it.
    def uv(co):
        return co.x / (L - 0.1) + 0.5, co.y / (W - 0.02) + 0.5

    def breath_w(u, v):
        if nest:
            cx, cy, r = nest
            x, y = xy(u, v)
            if math.hypot(x - cx, y - cy) < 1.6 * r:
                return hump_w(cx / (L - 0.1) + 0.5, cy / (W - 0.02) + 0.5)
        return hump_w(u, v)

    bl.shape_key_add(name="rest")
    sk = bl.shape_key_add(name="in")
    for v in sk.data:
        v.co.z += 0.02 * breath_w(*uv(v.co))
    K.drive(sk, "value", None, root, "breath", "x")
    if nest:
        K.prop(root, "nest", 0.0)
        nk = bl.shape_key_add(name="nest", from_mix=False)
        for v in nk.data:
            u, w = uv(v.co)
            v.co.z += nest_top(u, w) - rest_z(u, w)
        K.drive(nk, "value", None, root, "nest", "x")
        cx, cy, r = nest
        root["nest_breath"] = 0.02 * breath_w(cx / (L - 0.1) + 0.5, cy / (W - 0.02) + 0.5)
    out["blanket"] = bl
    glint_at = (-L / 2 + 0.07, 0.04, 0.47)  # just under the blanket's head-end lip
    if quilt:
        cx, cy, r = quilt
        K.prop(root, "open", 0.0)
        root["nest"] = 1.0  # the probe lies in its nest all along, under the quilt
        HY, H, RW = 0.15, 2 * r + 0.05, 1.6 * r  # the folds' pivots off the centre, the mound's height and width
        x0, x1 = -(L - 0.1) / 2, cx + 0.24

        def uvof(x, y):
            return x / (L - 0.1) + 0.5, y / (W - 0.02) + 0.5

        def quilt_z(x, y):
            u, v = uvof(x, y)
            d = math.hypot(x - cx, y - cy)
            return max(flat(u, v) + H * math.exp(-(d / RW) ** 4), nest_top(u, v) + 0.018)

        for side in (-1, 1):  # -1 the front fold (toward the room), 1 the back
            yh = cy + side * HY
            zh = quilt_z(cx, yh)
            hinge = K.empty(f"{name}.fold_hinge{side}", (cx, yh, zh), root)
            K.drive(hinge, "rotation_euler", 0, root, "open", f"{-side * 2.9} * x")
            K.drive(hinge, "location", 2, root, "breath", f"{zh:.4f} + {root['nest_breath']:.4f} * x")
            fb = bmesh.new()
            nx_, ny_ = 40, 16
            fv = {}
            for i in range(nx_ + 1):
                for j in range(ny_ + 1):
                    x = x0 + (x1 - x0) * i / nx_
                    y = yh + (cy - yh) * j / ny_
                    fv[i, j] = fb.verts.new((x - cx, y - yh, quilt_z(x, y) - zh))
            for i in range(nx_):
                for j in range(ny_):
                    q = (fv[i, j], fv[i + 1, j], fv[i + 1, j + 1], fv[i, j + 1])
                    fb.faces.new(q if side < 0 else q[::-1])
            bmesh.ops.solidify(fb, geom=fb.faces[:], thickness=0.015)
            fm = bpy.data.meshes.new(f"{name}.fold{side}")
            fb.to_mesh(fm)
            fb.free()
            fo = K.link(bpy.data.objects.new(f"{name}.fold{side}", fm))
            fo.parent = hinge
            fo.data.materials.append(bl.data.materials[0])
            K.smooth(fo)
            # As it turns back it lies down: its height above the pivot shrinks to 15%.
            fo.shape_key_add(name="rest")
            fk = fo.shape_key_add(name="flat")
            for v in fk.data:
                v.co.z *= 0.15
            K.drive(fk, "value", None, root, "open", "x")
        glint_at = (cx, cy - HY - 0.012, quilt_z(cx, cy - HY) - 0.012)  # under the front fold's lip
    if glint:
        # The green standby LED, seen through a fold of the blanket at the head end: a tiny emitter and a faint light.
        g = sphere(f"{name}.glint", K.mat_emission(f"{name}.glint", "standby", 30.0, root, "glint", floor=0.0),
                   glint_at, 0.006, root, 12)
        g.visible_shadow = False
        gl = light(f"{name}.glint_light", "POINT", (glint_at[0] + 0.01, glint_at[1], glint_at[2] + 0.03), 0.0,
                   "standby", 0.01, parent=root)
        gl.data.specular_factor = 0.3
        K.drive(gl.data, "energy", None, root, "glint", "0.25 * x")
    out["root"] = root
    return out


PROBE_SCALE = 3.0  # the crib probe: Sandbox Rhapsody's chassis at 3x (20 cm across), a baby's size in the crib
PROBE_AT = (-0.42, 0.0)  # crib-local: at the head end, where the blanket's hump is
PROBE_ARMS = 0.62  # the kit's arm reach that lays the folded arms forward on the blanket (N38)


def crib_probe(crib_root, name="crib_probe"):
    """The thing in the crib (brief, section 3): Sandbox Rhapsody's probe from the kit, unchanged, with the soft
    green standby LED, lying at the head end under the blanket's lip, lens toward the room (-Y). Scaled 3x: the same
    make, a baby's size; the kit's proportions, materials and rig are untouched."""
    p = K.probe(name, (0, 0, 0), led_role="standby", led=0.6, scale=PROBE_SCALE)
    p.parent = crib_root
    # In the blanket's nest (crib(nest=...)): the felt rises to its equator, its arms folded forward on the blanket
    # (brief, N38). It rides the blanket's breath, so the felt never passes through it (human, C4 review).
    r = K.PROBE_R * PROBE_SCALE
    z0 = nest_z(r)
    p.location = (PROBE_AT[0], PROBE_AT[1], z0)
    K.drive(p, "location", 2, crib_root, "breath", f"{z0:.4f} + {crib_root.get('nest_breath', 0.0):.4f} * x")
    p.rotation_euler = (0, 0, 0)
    p["arm_l"] = p["arm_r"] = PROBE_ARMS
    return {"root": p, "probe": p}


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
        # N13: each piece rises again "holding a tiny stack of tickets" (hidden until then; animate.mobile).
        stk = K.empty(f"{name}.stack_{piece}", (0, 0, -0.07), p)
        for j in range(4):
            box(f"{name}.stack_{piece}{j}", K.mat_matte(f"{name}.ticket", "paper"), (0.004 * (j % 2), 0, -0.004 * j),
                (0.05, 0.035, 0.0015), stk)
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


def projected_stars(origin, n, seed, count=1.0, reveal=False):
    """The stars on the glass (brief: "the stars are the findings"): `n` star directions from the projector, seeded,
    landing on the glass walls' and roof's inside faces as small cream glows. One mesh; each star a 5-point star
    shape, so up close they read as projected stars, not dots. `count` (0-1) keeps the first fraction (C1 shows a
    late-song wall)."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    lo, hi = Vector((-ROOM + 0.01, -ROOM + 0.01, PL_H + 0.5)), Vector((ROOM - 0.01, ROOM - 0.01, TOP - 0.01))
    placed = 0
    per = []  # face -> star index (for the birth/dim attributes)
    where = []
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
            per.append(placed)
        where.append(tuple(p))
        placed += 1
    me = bpy.data.meshes.new("stars_projected")
    bm.to_mesh(me)
    bm.free()
    o = K.link(bpy.data.objects.new("stars_projected", me))
    o.data.materials.append(mat_reveal("star_proj", "comfort", LOOK["projected_star"]) if reveal
                            else K.mat_emission("star_proj", "comfort", LOOK["projected_star"]))
    o.visible_shadow = False
    o["placed"] = placed
    o["per"] = per
    o["where"] = [c for p in where for c in p]
    if reveal:
        set_times(o, [], per=per)
    return o


def call_graph(stars_obj, seed):
    """N05 ("the branches that nobody reads"): stars on the ceiling linked into a branching tree, like a call graph.
    Each edge joins a ceiling star to its nearest earlier one; edges are thin cream ribbons just under the roof, born
    one by one (birth times set by the animation). Returns (object, per-face edge index, edge count)."""
    w = list(stars_obj["where"])
    pts = [Vector(w[i:i + 3]) for i in range(0, len(w), 3)]
    roof = [p for p in pts if p.z > TOP - 0.05]
    rnd = random.Random(seed)
    rnd.shuffle(roof)
    roof = roof[:24]
    segs = []
    for k in range(1, len(roof)):
        j = min(range(k), key=lambda i: (roof[i] - roof[k]).length)
        segs.append((roof[j], roof[k], Vector((0, 0, -1))))
    o, per = ribbon_mesh("call_graph", segs, 0.006, lift=Vector((0, 0, -0.004)))
    o.data.materials.append(mat_reveal("call_graph", "comfort", LOOK["projected_star"] * 0.6))
    o.visible_shadow = False
    set_times(o, [], per=per)
    o["per"] = per
    return o, len(segs)


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
    # Turned to show the room its comb and drum, three-quarter on to the camera's N36 approach (human, C4 v2 review:
    # it barely read as a music box), and a little bigger.
    mb = K.music_box(f"{name}.musicbox", (-0.18, -0.02, 0.825), scale=2.0, rot_z=math.pi + 0.05, parent=root)
    for o in bpy.data.objects:
        if o.name.startswith(f"{name}.musicbox.tip") or o.name == f"{name}.musicbox.knob":
            for m in o.data.materials:
                for nd in m.node_tree.nodes:
                    if nd.type == "EMISSION":
                        nd.inputs["Color"].default_value = K.col("comfort")
                    elif nd.type == "BSDF_PRINCIPLED":
                        nd.inputs["Base Color"].default_value = K.col("felt_blue")
    bpy.data.objects[f"{name}.musicbox.glow"].data.color = K.col("comfort")[:3]
    # N36: "the music box now has a coin slot; a coin drops in": a brass slot plate on the case's side (shown from
    # N36) and a coin that falls into it ("coin" 0 above .. 1 in).
    slot = K.empty(f"{name}.coinslot", (0.105, 0.0, 0.05), mb)
    K.prop(slot, "coin", 0.0)
    box(f"{name}.coinslot_plate", K.mat_metal(f"{name}.slot", "brass", 0.25), (0, 0, 0), (0.004, 0.05, 0.03), slot)
    box(f"{name}.coinslot_slit", K.mat_plastic(f"{name}.slit", "shadow", 0.5), (0.0025, 0, 0), (0.002, 0.03, 0.004), slot)
    coin = cyl(f"{name}.coin", K.mat_metal(f"{name}.coin", "brass", 0.15), (0.012, 0, 0.09), 0.011, 0.002, slot,
               rot=(0, math.pi / 2, 0), verts=24)
    K.drive(coin, "location", 2, slot, "coin", "0.09 - 0.09 * x")
    # Recolour its lacquer case from the Lab's dark blue to the nursery's pastel, so it belongs to this room.
    case = bpy.data.objects[f"{name}.musicbox.case"]
    case.data.materials[0] = mat_paint(f"{name}.mb_case", "pastel", 0.3)
    # Its lid, open on a hinge along the back edge, lined in felt: the silhouette of a music box, not a mechanism.
    lid_h = K.empty(f"{name}.mb_lid_hinge", (0, 0.056, 0.072), mb)
    lid_h.rotation_euler = (math.radians(-104), 0, 0)
    box(f"{name}.mb_lid", case.data.materials[0], (0, -0.055, 0.006), (0.17, 0.11, 0.012), lid_h, bev=0.004)
    box(f"{name}.mb_lid_lining", mat_felt(f"{name}.mb_lining", "felt_blue"), (0, -0.055, -0.0005), (0.15, 0.09, 0.002),
        lid_h)
    # A small warm key on the dresser top, so the box reads at N36.
    light(f"{name}.mb_key", "SPOT", (-0.45, -0.45, 1.35), 6.0, "comfort", 0.05, target=(-0.18, -0.02, 0.9),
          spot=(0.6, 0.4), specular=0.5, parent=root)
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
    root["marks"] = 0
    while z < 1.82:
        box(f"{name}.mark{k}", ink, (-0.03, -0.0115, z), (0.12, 0.002, 0.004), root)
        root["marks"] = k + 1
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
    c = crib("crib", (0.35, 1.05, 0), rot_z=0.0, parent=room,
             nest=(PROBE_AT[0], PROBE_AT[1], K.PROBE_R * PROBE_SCALE),
             quilt=(PROBE_AT[0], PROBE_AT[1], K.PROBE_R * PROBE_SCALE))
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
    """Outside the back window: a night sky, the moon, a hill of small houses with porch lights, and the neighbor's
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
    lights_root = K.empty("street.lights")
    out["lights"] = lights_root
    out["homes"] = []
    homes = [(-22, 46), (-13, 50), (-6, 53), (2.5, 50), (-2.0, 56), (6, 52), (13, 55), (17, 48), (25, 45), (-9, 63),
             (8.5, 65), (2, 62), (14, 61), (-15, 60),
             # More houses (human, C4 review: the town needs more lights to read when they go out).
             (-30, 50), (21, 57), (-19, 55), (-26, 62), (19, 66), (-6, 67), (27, 52), (5.5, 58.5)]
    neighbor = 4  # (-2, 56): framed by the back window from inside the room (the bridge) and from N29's wide view
    for k, (x, y) in enumerate(homes):
        g = ground(x, y)
        w, d, hh = 3.2, 2.6, 3.0 + (1.0 if k == neighbor else 0.6 * (k % 2))
        box(f"house{k}.body", wall, (x, y, g + hh / 2), (w, d, hh))
        rf = K.mesh_obj(f"house{k}.roof", bpy.ops.mesh.primitive_cone_add, roof_m, None, vertices=4,
                        radius1=w * 0.8, depth=1.4, location=(x, y, g + hh + 0.7), rotation=(0, 0, math.pi / 4))
        rf.scale = (1, d / w, 1)
        K.prop(lights_root, f"porch{k}", 1.0)  # N26: the town kills its lights, house by house
        p = sphere(f"house{k}.porch", K.mat_emission(f"porch{k}", "comfort", 22.0, lights_root, f"porch{k}", floor=0.0),
                   (x + 0.8, y - d / 2 - 0.15, g + 1.0), 0.09, None, 12)
        p.visible_shadow = False
        out["homes"].append((x, y, g))
        # Every house has a lit window or two; they go out with its porch light (N26).
        wm_k = K.mat_emission(f"house_win{k}", "comfort", 2.6, lights_root, f"porch{k}", floor=0.0)
        box(f"house{k}.win", wm_k, (x - 0.7, y - d / 2 - 0.01, g + 1.4), (0.6, 0.02, 0.5)).visible_shadow = False
        if k % 2 == 0 and k != neighbor:
            box(f"house{k}.win2", wm_k, (x + 0.7, y - d / 2 - 0.01, g + hh - 0.8), (0.5, 0.02, 0.45)).visible_shadow = False
        if k == neighbor:
            root = K.empty("neighbor", (x, y, g))
            K.prop(root, "amber", 1.0)
            wm = K.mat_emission("neighbor_win", "amber", 18.0, root, "amber", floor=0.0)
            box("neighbor.window", wm, (x + 0.6, y - d / 2 - 0.01, g + hh - 0.9), (0.7, 0.02, 0.6))
            box("neighbor.sill", mat_stone("sill_n", "house_wall", 0.6), (x + 0.6, y - d / 2 - 0.06, g + hh - 1.22),
                (0.85, 0.1, 0.05))
            # N24: the light moves along the sill (the kid up on its feet): a small amber glow, "walk" 0-1 across.
            K.prop(root, "walk", 0.0)
            walker = sphere("neighbor.walker", K.mat_emission("neighbor_walk", "amber", 40.0, root, "amber", floor=0.0),
                            (x + 0.32, y - d / 2 - 0.03, g + hh - 1.1), 0.06, None, 12)
            K.drive(walker, "location", 0, root, "walk", f"{x + 0.32} + 0.56 * x")
            walker.visible_shadow = False
            out["neighbor"] = root
            out["neighbor_window"] = Vector((x + 0.6, y - d / 2, g + hh - 0.9))
    # The road up the hill to the houses, and the fine crack that runs down it and branches under every house (N25).
    road_pts = [Vector((-1.5 + 0.06 * (yy - 30), yy, ground(-1.5 + 0.06 * (yy - 30), yy) + 0.04)) for yy in range(30, 70, 2)]
    bm = bmesh.new()
    for a, b in zip(road_pts, road_pts[1:]):
        nrm = Vector((1.6, 0, 0))
        bm.faces.new([bm.verts.new(v) for v in (a - nrm, b - nrm, b + nrm, a + nrm)])
    me = bpy.data.meshes.new("street.road")
    bm.to_mesh(me)
    bm.free()
    road = K.link(bpy.data.objects.new("street.road", me))
    road.data.materials.append(mat_stone("road", "plinth", 0.8))
    out["road_pts"] = road_pts
    out["ground"] = ground
    # A cross lane along the hill, and streetlights along both (human, C4 review: more lights, so the town reads when
    # it kills them; a subtle road). Each lamp is a head on a thin pole with a pool of light under it ("lamp<k>").
    lane = [Vector((x, 43.0, ground(x, 43.0) + 0.04)) for x in range(-32, 33, 2)]
    bm = bmesh.new()
    for a, b in zip(lane, lane[1:]):
        nrm = Vector((0, 1.2, 0))
        bm.faces.new([bm.verts.new(v) for v in (a - nrm, a + nrm, b + nrm, b - nrm)])
    me = bpy.data.meshes.new("street.lane")
    bm.to_mesh(me)
    bm.free()
    K.link(bpy.data.objects.new("street.lane", me)).data.materials.append(mat_stone("road", "plinth", 0.8))
    pole_m = mat_steel("street.pole")
    spots = [(-1.5 + 0.06 * (yy - 30) + sx * 2.3, yy) for yy, sx in ((32, 1), (37, -1), (42, 1), (48, -1), (53, 1),
                                                                     (59, -1), (64, 1), (68.5, -1))]
    spots += [(x, 43.0 + 1.8 * (1 if k % 2 else -1)) for k, x in enumerate((-29, -23, -17, -11, 7, 13, 19, 25))]
    out["lamps"] = []
    for k, (x, y) in enumerate(spots):
        g = ground(x, y)
        K.prop(lights_root, f"lamp{k}", 1.0)
        bar(f"street.pole{k}", pole_m, (x, y, g), (x, y, g + 4.2), 0.06)
        hd = sphere(f"street.lamp{k}", K.mat_emission(f"lamp{k}", "comfort", 45.0, lights_root, f"lamp{k}", floor=0.0),
                    (x, y, g + 4.25), 0.22, None, 12)
        hd.visible_shadow = False
        lt = light(f"street.lamp{k}.pool", "SPOT", (x, y, g + 4.0), 900.0, "comfort", 0.1, target=(x, y, g),
                   spot=(1.6, 0.5), specular=0.2)
        K.drive(lt.data, "energy", None, lights_root, f"lamp{k}", "900.0 * x")
        out["lamps"].append((x, y, g))
    # Far hills (N27): a second ridge behind the first, with small houses whose windows light amber one by one.
    bm = bmesh.new()
    nx = 60
    vs = []
    for i in range(nx + 1):
        x = -150 + 300 * i / nx
        h = 15 + 5 * math.sin(x * 0.03) + 3 * math.sin(x * 0.11)
        vs.append((bm.verts.new((x, 125, -1)), bm.verts.new((x, 125, h))))
    for i in range(nx):
        bm.faces.new((vs[i][0], vs[i + 1][0], vs[i + 1][1], vs[i][1]))
    me = bpy.data.meshes.new("street.far_hills")
    bm.to_mesh(me)
    bm.free()
    far = K.link(bpy.data.objects.new("street.far_hills", me))
    far.data.materials.append(mat_stone("far_hill", "hill", 0.9))
    far_root = K.empty("street.far")
    out["far"] = far_root
    rnd = random.Random(SEEDS["main"] + 7)
    out["far_n"] = 16
    for k in range(16):
        x = -60 + 120 * (k + rnd.random() * 0.6) / 16
        h = 15 + 5 * math.sin(x * 0.03) + 3 * math.sin(x * 0.11)
        K.prop(far_root, f"amber{k}", 0.0)
        wdw = box(f"far{k}.window", K.mat_emission(f"far{k}", "amber", 30.0, far_root, f"amber{k}", floor=0.0),
                  (x, 124.5, h - rnd.uniform(1.0, 3.0)), (0.9, 0.05, 0.7))
        wdw.visible_shadow = False
    return out


def shop_window():
    """Across the hall in the +X wall: a lit display window with flat fluorescent white light, an identical crib with
    a green glint under its blanket, a price tag on the rail (COMING SOON) and a small dark screen for verse 4's
    real pages. The twin probe and its mittens are built at C2 with the kit."""
    out = {}
    root = K.empty("shop", (11.0, 0, 0))
    commerce = mat_stone("shop.wall", "commerce", 0.7)
    D = 1.8
    # The box starts behind the hall wall (0.3 m thick): inside the wall its faces lay in the opening's planes and
    # flickered (human, C4 review: N31). The opening's own reveals frame it.
    X0 = 0.3
    box("shop.floor", mat_stone("shop.floor", "felt_grey", 0.6), ((X0 + D) / 2, 0, 0.55), (D - X0, 3.7, 0.1), root)
    box("shop.back", commerce, (D + 0.05, 0, 1.8), (0.1, 3.7, 2.7), root)
    box("shop.ceil", commerce, ((X0 + D) / 2, 0, 3.05), (D - X0, 3.7, 0.1), root)
    for s in (-1, 1):
        box(f"shop.side{s}", commerce, ((X0 + D) / 2, s * 1.85, 1.8), (D - X0, 0.1, 2.7), root)
    steel = mat_steel("shop.frame")
    box("shop.frame_top", steel, (0.02, 0, 3.02), (0.06, 3.7, 0.06), root)
    box("shop.frame_low", steel, (0.02, 0, 0.6), (0.06, 3.7, 0.06), root)
    glass = K.mat_glass("shop.glass", reflect=0.35)
    pg = K.mesh_obj("shop.glass", bpy.ops.mesh.primitive_plane_add, glass, root, size=1, location=(0.02, 0, 1.8),
                    rotation=(math.pi / 2, 0, math.pi / 2))
    pg.scale = (3.6, 2.4, 1)
    pg.visible_shadow = False
    c = crib("shop.crib", (0.95, 0.35, 0.6), rot_z=math.pi / 2, parent=root,
             cover=(PROBE_AT[0], PROBE_AT[1], K.PROBE_R * PROBE_SCALE))
    out["crib"] = c
    # On the rail's hall side, between the posts (human, C4 v2 review: the crib hid it at N32).
    tag = K.empty("shop.tag", (0.555, 0.33, 0.6 + 0.82), root)
    tag.rotation_euler = (math.pi / 2, 0, -math.pi / 2 + 0.1)
    K.mesh_obj("shop.tag_card", bpy.ops.mesh.primitive_plane_add, K.mat_matte("tag", "paper"), tag, size=0.2).scale = (
        1.0, 0.55, 1)
    K.text("shop.tag_text", "COMING\nSOON", 0.035, K.mat_ink("tag_ink", "shadow"), loc=(0, 0, 0.001), rot=(0, 0, 0),
           font="Inter-Medium-flat.ttf", parent=tag)
    # The display screen (dark until verse 4) on a small easel to the left: two front legs and a back leg in pale
    # wood, a ledge under the screen.
    scr = box("shop.screen", K.mat_plastic("shop.screen", "lens", 0.05), (1.3, -1.1, 1.55), (0.04, 0.9, 0.55), root,
              bev=0.01)
    easel = mat_paint("shop.easel", "wood", 0.55)
    for sy in (-1, 1):
        bar(f"shop.easel_leg{sy}", easel, (1.2, -1.1 + sy * 0.36, 0.6), (1.345, -1.1 + sy * 0.25, 1.86), 0.013, root)
    bar("shop.easel_back", easel, (1.66, -1.1, 0.6), (1.36, -1.1, 1.8), 0.012, root)
    box("shop.easel_ledge", easel, (1.275, -1.1, 1.262), (0.09, 0.84, 0.025), root, bev=0.004)
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
    """The hall's cold museum light: two dim spots from the ceiling on the plinth, a moonlight sun through the back
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
    """Faint air in the hall so the moonlight through the back window and the projector's glow read as beams."""
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


def floor_gaps():
    """N20 ("lamp light leaks up through the floor gaps"): thin tungsten slits in the nursery floor between its boards,
    lit from the basement below (reveal material: birth set by the animation)."""
    segs = [(Vector((-1.8, y, PL_H + 0.002)), Vector((1.8, y, PL_H + 0.002)), Vector((0, 0, 1)))
            for y in (-1.2, -0.6, 0.0, 0.6)]
    o, per = ribbon_mesh("floor_gaps", segs, 0.008)
    o.data.materials.append(mat_reveal("floor_gaps", "tungsten", 6.0, fade=1.2))
    o.visible_shadow = False
    set_times(o, [], per=per)
    return o


def town_crack(street_out, seed):
    """N25 ("it found the old crack under most of the net"): a fine crack runs down the road and branches under every
    house. Ribbons on the hill, faintly lit (reveal: each segment's birth set by the animation, top to bottom)."""
    ground, pts, homes = street_out["ground"], street_out["road_pts"], street_out["homes"]
    rnd = random.Random(seed)
    segs, order = [], []
    up = Vector((0, 0, 1))
    trunk = [Vector((p.x + rnd.uniform(-0.3, 0.3), p.y, p.z + 0.03)) for p in reversed(pts)]
    for a, b in zip(trunk, trunk[1:]):
        segs.append((a, b, up))
        order.append(1.0 - (b.y - 30) / 30)
    for (x, y, g) in homes:  # a branch from the nearest trunk point to under each house
        a = min(trunk, key=lambda p: (p - Vector((x, y, g))).length)
        n = 6
        prev = a
        for i in range(1, n + 1):
            f = i / n
            q = a.lerp(Vector((x, y - 1.3, g + 0.03)), f) + Vector((rnd.uniform(-0.4, 0.4), 0, 0))
            q.z = ground(q.x, q.y) + 0.03
            segs.append((prev, q, up))
            order.append(1.0 - (a.y - 30) / 30 + 0.15 * f)
            prev = q
    o, per = ribbon_mesh("town_crack", segs, 0.12)
    o.data.materials.append(mat_reveal("town_crack", "frost", 3.0, fade=0.3))
    o.visible_shadow = False
    set_times(o, [], per=per)
    o["order"] = order
    o["per"] = per
    return o


def moat():
    """N22 ("…and the moat, while we're at it, defended"): a thin ring of still water around the plinth, which
    appears there (hidden until then; the animation keys its visibility)."""
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=4.8, fill_type="NOTHING", location=(0, 0, 0.004))
    o = bpy.context.active_object
    o.name = "moat"
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.extrude_region_shrink_fatten(TRANSFORM_OT_shrink_fatten={"value": 0.7})
    bpy.ops.mesh.edge_face_add()
    bpy.ops.object.mode_set(mode="OBJECT")
    # Still water reads as reflection: Sandbox Rhapsody's glass shader (a Fresnel reflection of the procedural studio
    # environment) over a dark tint, and a faint cold rim at both edges so the ring shows against the dark floor.
    o.data.materials.append(K.mat_glass("moat", role="house", tint=0.25, reflect=0.3))
    for k, r in enumerate((4.1, 4.8)):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.008, major_segments=128, minor_segments=6,
                                         location=(0, 0, 0.006))
        e = bpy.context.active_object
        e.name = f"moat.edge{k}"
        e.data.materials.append(K.mat_emission(f"moat.edge{k}", "house", 1.2))
        e.parent = o
    return o


def velvet_rope():
    """N30 ("some locks are for danger, and some are for class"): a velvet rope on two brass posts in front of the
    vault door, the second lock. Navy velvet: no red anywhere (brief). Shown from N29 on."""
    root = K.empty("rope", (0, -ROOM - 0.85, PL_H))
    brass = K.mat_metal("rope.brass", "brass", 0.15)
    for k, x in enumerate((-0.75, 0.75)):
        cyl(f"rope.post{k}", brass, (x, 0, 0.45), 0.025, 0.9, root, verts=24)
        cyl(f"rope.base{k}", brass, (x, 0, 0.02), 0.12, 0.04, root, verts=48)
        sphere(f"rope.knob{k}", brass, (x, 0, 0.92), 0.045, root, 20)
    cd = bpy.data.curves.new("rope.curve", "CURVE")
    cd.dimensions, cd.bevel_depth, cd.bevel_resolution = "3D", 0.022, 4
    sp = cd.splines.new("BEZIER")
    sp.bezier_points.add(2)
    for bp, p in zip(sp.bezier_points, ((-0.72, 0, 0.86), (0, 0, 0.62), (0.72, 0, 0.86))):
        bp.co, bp.handle_left_type, bp.handle_right_type = p, "AUTO", "AUTO"
    rope = K.link(bpy.data.objects.new("rope.velvet", cd))
    rope.parent = root
    rope.data.materials.append(mat_felt("rope.velvet", "fill"))
    return root


def basement():
    """The basement (brief: "directly under the glass room, reached by a cutaway through the plinth: a low room, one
    desk lamp, a laptop and a paper avalanche of printed tickets"). Below the hall floor: x, y -2.4..2.4, z -2.8..0.
    The maintainer is seen from behind, no face (N16). A jar of peanuts, a donation jar with three coins (N15), sheets
    that glow faintly cream among grey ones (N17), a mail slot in the ceiling whose flap clatters on the beat (N18).
    Returns its rigs."""
    out = {}
    Z0, Z1, W = -2.8, -0.02, 2.4
    wall = mat_stone("base.wall", "house_wall", 0.9)
    box("base.floor", mat_stone("base.floor", "plinth", 0.8), (0, 0, Z0 - 0.05), (2 * W, 2 * W, 0.1))
    for k, (p, sz) in enumerate((((0, W, (Z0 + Z1) / 2), (2 * W, 0.1, Z1 - Z0)), ((0, -W, (Z0 + Z1) / 2), (2 * W, 0.1, Z1 - Z0)),
                                 ((W, 0, (Z0 + Z1) / 2), (0.1, 2 * W, Z1 - Z0)), ((-W, 0, (Z0 + Z1) / 2), (0.1, 2 * W, Z1 - Z0)))):
        box(f"base.wall{k}", wall, p, sz)
    # The ceiling slab, with the mail slot's opening cut through it (x 0.2 +- 0.21, y 1.6 +- 0.065).
    hx0, hx1, hy0, hy1 = -0.01, 0.41, 1.535, 1.665
    zc = Z1 - 0.03
    boxes_obj("base.ceiling", mat_stone("base.ceil", "plinth", 0.9),
              [((-W, -W, zc - 0.02), (W, hy0, zc + 0.02)), ((-W, hy1, zc - 0.02), (W, W, zc + 0.02)),
               ((-W, hy0, zc - 0.02), (hx0, hy1, zc + 0.02)), ((hx1, hy0, zc - 0.02), (W, hy1, zc + 0.02))])
    # The collar: closes the ring between the basement's walls and the plinth's sides at the hall floor's level.
    # Its top 4 mm under the hall floor's and its ends 1 cm inside the plinth's sides: flush, they z-fought (QC
    # 2026-10-25).
    for k, (p, sz) in enumerate((((0, 2.6, -0.032), (5.58, 0.42, 0.056)), ((0, -2.6, -0.032), (5.58, 0.42, 0.056)),
                                 ((2.6, 0, -0.032), (0.42, 5.58, 0.056)), ((-2.6, 0, -0.032), (0.42, 5.58, 0.056)))):
        box(f"base.collar{k}", wall, p, sz)
    # The desk, its lamp, the laptop.
    wood = mat_paint("base.desk", "wood", 0.6)
    dz = Z0 + 0.75
    box("base.desk_top", wood, (0.5, 1.3, dz), (1.5, 0.75, 0.04), bev=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"base.desk_leg{sx}{sy}", wood, (0.5 + sx * 0.7, 1.3 + sy * 0.33, Z0 + 0.37), (0.04, 0.04, 0.74))
    metal = K.mat_metal("base.lamp", "steel", 0.4)
    cyl("base.lamp_foot", metal, (1.05, 1.5, dz + 0.03), 0.07, 0.02, verts=32)
    bar("base.lamp_arm", metal, (1.05, 1.5, dz + 0.04), (0.85, 1.35, dz + 0.42), 0.008)
    shade = K.mesh_obj("base.lamp_shade", bpy.ops.mesh.primitive_cone_add, metal, None, vertices=32, radius1=0.09,
                       radius2=0.03, depth=0.12, location=(0.82, 1.32, dz + 0.4), rotation=(0.5, -0.3, 0))
    K.smooth(shade)
    sphere("base.bulb", K.mat_emission("base.bulb", "tungsten", 40.0), (0.81, 1.31, dz + 0.36), 0.02, None, 12)
    out["lamp"] = light("base.lamp_light", "SPOT", (0.81, 1.31, dz + 0.37), 220.0, "tungsten", 0.03,
                        target=(0.55, 1.2, dz), spot=(1.9, 0.6))
    light("base.lamp_spill", "POINT", (0.8, 1.3, dz + 0.5), 25.0, "tungsten", 0.2, specular=0.1)
    light("base.fill", "AREA", (0, -1.0, Z1 - 0.2), 30.0, "tungsten", 2.0, target=(0.4, 1.0, Z0), specular=0.1)
    # The laptop: a base with a keyboard well, keys and a trackpad, a hinge, and a lid whose display is the lit page
    # below (the lid itself is dark plastic; the page carries the screen's light).
    shell = K.mat_plastic("base.laptop", "lab_dark", 0.4)
    bz = dz + 0.0275  # the base's top face
    box("base.laptop_base", shell, (0.35, 1.15, dz + 0.03), (0.34, 0.24, 0.015), bev=0.004)
    keys_ext = []
    for row in range(4):
        for col in range(12):
            x0, y0 = 0.35 - 0.141 + col * 0.0236, 1.215 - row * 0.0225
            keys_ext.append(((x0, y0 - 0.0185, bz), (x0 + 0.02, y0, bz + 0.003)))
    keys_ext.append(((0.35 - 0.075, 1.215 - 4 * 0.0225 - 0.0185, bz), (0.35 + 0.075, 1.215 - 4 * 0.0225, bz + 0.003)))
    boxes_obj("base.laptop_keys", K.mat_plastic("base.keys", "shadow", 0.5), keys_ext)
    box("base.laptop_pad", K.mat_plastic("base.pad", "plinth", 0.3), (0.35, 1.062, bz + 0.0005), (0.1, 0.05, 0.001))
    cyl("base.laptop_hinge", shell, (0.35, 1.262, dz + 0.042), 0.008, 0.3, rot=(0, math.pi / 2, 0), verts=16)
    scr = box("base.laptop_screen", shell, (0.35, 1.28, dz + 0.15), (0.33, 0.01, 0.22), bev=0.003)
    scr.rotation_euler = (-0.2, 0, 0)
    # The page on the laptop (human, C4 v3 review: "something about warnings or CVEs"): a security advisory feed, a
    # thousand new warnings, a few critical, mostly noise (N17's line). The real bugs are the ones the words allude to
    # (human, C4 v3 review): PHP2Shell, CVE-2026-109618 and CVE-2026-109619 (the bridge's "old crack under most of the
    # net"; critical, per the PHP advisories), and Mythos's 27-year-old OpenBSD SACK bug (verse 1), which has no CVE:
    # OpenBSD fixed it as 7.8 errata 025. The rest is noise, with no IDs made up. Ink on a lit page, just in front of
    # the screen, on a pivot with the screen's tilt so the text keeps its proportions.
    pg = K.empty("base.laptop_page", (0.35, 1.28 - 0.0065 * math.cos(0.2), dz + 0.15 - 0.0065 * math.sin(0.2)))
    pg.rotation_euler = (-0.2, 0, 0)
    K.mesh_obj("base.page", bpy.ops.mesh.primitive_plane_add, K.mat_emission("base.page", "commerce", 1.1), pg, size=1,
               rotation=(math.pi / 2, 0, 0)).scale = (0.31, 0.2, 1)
    K.mesh_obj("base.page_bar", bpy.ops.mesh.primitive_plane_add, K.mat_emission("base.page_bar", "amber", 1.6), pg,
               size=1, location=(0, -0.0004, 0.082), rotation=(math.pi / 2, 0, 0)).scale = (0.31, 0.036, 1)
    ink = K.mat_ink("base.page_ink", "shadow")
    mono = "JetBrainsMono-SemiBold-flat.ttf"
    K.text("base.page_title", "SECURITY ADVISORIES", 0.019, ink, loc=(-0.145, -0.0008, 0.082), font=mono,
           align="LEFT", parent=pg)
    K.text("base.page_count", "1,024 new warnings  ·  2 critical", 0.0115, ink, loc=(-0.145, -0.0008, 0.052),
           align="LEFT", parent=pg)
    rows = (("CVE-2026-109618", "CRITICAL"), ("WARNING", "unused var"), ("OpenBSD errata 025", "27 years old"),
            ("AI report", "unverified"), ("CVE-2026-109619", "CRITICAL"), ("WARNING", "deprecated"),
            ("AI report", "duplicate"), ("AI report", "???"))
    for k, (a, b) in enumerate(rows):
        z = 0.03 - k * 0.0165
        # The rows in Inter: the mono's dotted zero reads as an 8 at 720p ("2826").
        K.text(f"base.page_id{k}", a, 0.0125, ink, loc=(-0.145, -0.0008, z), align="LEFT", parent=pg)
        K.text(f"base.page_sev{k}", b, 0.0125, ink, loc=(0.145, -0.0008, z), align="RIGHT", parent=pg)
        if b == "CRITICAL":
            K.mesh_obj(f"base.page_hi{k}", bpy.ops.mesh.primitive_plane_add,
                       K.mat_emission(f"base.page_hi{k}", "amber", 1.3), pg, size=1,
                       location=(0.115, -0.0005, z), rotation=(math.pi / 2, 0, 0)).scale = (0.072, 0.014, 1)
    # The jar of peanuts and the donation jar with three coins.
    jar = K.mat_acrylic("base.jar", "glass", alpha=0.25)
    cyl("base.peanut_jar", jar, (-0.05, 1.45, dz + 0.08), 0.05, 0.14, verts=24)
    rnd = random.Random(SEEDS["main"] + 3)
    nut = mat_paint("base.nut", "felt_cream", 0.7)
    for k in range(14):
        sphere(f"base.nut{k}", nut, (-0.05 + rnd.uniform(-0.03, 0.03), 1.45 + rnd.uniform(-0.03, 0.03),
                                     dz + 0.03 + rnd.uniform(0, 0.08)), 0.012, None, 8)
    cyl("base.tip_jar", jar, (-0.2, 1.5, dz + 0.07), 0.045, 0.12, verts=24)
    K.text("base.tip_label", "DONATIONS", 0.018, K.mat_ink("base.tip_ink", "shadow"), loc=(-0.2, 1.454, dz + 0.08),
           rot=(math.pi / 2, 0, 0))
    coin = K.mat_metal("base.coin", "brass", 0.2)
    for k in range(3):  # stacked on the desk top (dz + 0.02), half a millimetre apart (QC 2026-10-25: two were
        # buried in the desk and the third's face z-fought with it)
        cyl(f"base.coin{k}", coin, (-0.2 + 0.012 * (k - 1), 1.5, dz + 0.0215 + 0.0025 * k), 0.012, 0.002, verts=16)
    # The maintainer, from behind, hunched over the laptop in a hoodie: a felt doll like the nursery's toys (soft
    # rounded parts), on a wooden chair. "breath" lifts the torso, shoulders, head and upper arms a little; the
    # forearms and hands rest on the keyboard and stay put (the elbow joints hide the seam).
    m_root = K.empty("maintainer", (0.37, 0.55, Z0))
    K.prop(m_root, "breath", 0.0)
    cloth = mat_felt("base.cloth", "felt_grey")
    jeans = mat_felt("base.jeans", "fill")
    hair = mat_paint("base.hair", "pencil", 0.8)
    skin = mat_felt("base.skin", "felt_cream")
    shoe = K.mat_plastic("base.shoe", "shadow", 0.6)
    # The chair: seat, four legs, two back posts with a top rail and a lower rail.
    box("base.chair_seat", wood, (0, 0, 0.45), (0.44, 0.44, 0.04), m_root, bev=0.008)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f"base.chair_leg{sx}{sy}", wood, (sx * 0.19, sy * 0.19, 0.215), 0.016, 0.43, m_root, verts=12)
        cyl(f"base.chair_post{sx}", wood, (sx * 0.19, -0.2, 0.7), 0.017, 0.46, m_root, verts=12)
    box("base.chair_back", wood, (0, -0.2, 0.86), (0.42, 0.03, 0.12), m_root, bev=0.008)
    box("base.chair_rail", wood, (0, -0.2, 0.62), (0.4, 0.025, 0.04), m_root, bev=0.005)
    # Torso local: origin over the seat (world z = Z0 + 0.5); +Y toward the desk.
    torso = K.empty("maintainer.torso", (0, 0.02, 0.5), m_root)
    K.drive(torso, "location", 2, m_root, "breath", "0.5 + 0.012 * x")
    soft_box("maintainer.hips", jeans, (0, 0.02, 0.05), (0.36, 0.3, 0.15), torso)
    soft_box("maintainer.body", cloth, (0, 0.06, 0.3), (0.42, 0.27, 0.52), torso, rot=(-0.25, 0, 0))
    # The hood, down: a soft bunch of fabric lying on the upper back, below the neck.
    hood = sphere("maintainer.hood", cloth, (0, 0.03, 0.53), 0.09, torso, 24)
    hood.scale, hood.rotation_euler = (1.45, 0.55, 0.75), (-0.5, 0, 0)
    cyl("maintainer.neck", skin, (0, 0.14, 0.6), 0.05, 0.07, torso, rot=(-0.5, 0, 0), verts=16)
    sphere("maintainer.head", hair, (0, 0.2, 0.685), 0.105, torso, 32).scale = (0.9, 1.0, 1.08)
    for sx in (-1, 1):
        sphere(f"maintainer.ear{sx}", skin, (sx * 0.094, 0.21, 0.675), 0.022, torso, 12).scale = (0.5, 1.0, 1.25)
    # Arms: shoulder -> elbow on the torso (breathing); elbow -> wrist -> hand on the root (still, on the keys).
    # Root local = torso local + (0, 0.02, 0.5).
    for sx in (-1, 1):
        sh, el = (sx * 0.17, 0.1, 0.47), (sx * 0.22, 0.22, 0.33)
        sphere(f"maintainer.shoulder{sx}", cloth, sh, 0.05, torso, 16)
        bar(f"maintainer.arm{sx}", cloth, sh, el, 0.046, torso, verts=16)
        el_r = (el[0], el[1] + 0.02, el[2] + 0.5)
        wr = (sx * 0.1, 0.54, 0.825)
        sphere(f"maintainer.elbow{sx}", cloth, el_r, 0.045, m_root, 16)
        bar(f"maintainer.forearm{sx}", cloth, el_r, wr, 0.036, m_root, verts=16)
        sphere(f"maintainer.cuff{sx}", cloth, wr, 0.037, m_root, 16).scale = (1.0, 0.6, 1.0)
        sphere(f"maintainer.hand{sx}", skin, (sx * 0.085, 0.585, 0.796), 0.034, m_root, 16).scale = (1.0, 1.35, 0.45)
        # Legs under the desk: thigh forward along the seat, shin down, a shoe.
        kn = (sx * 0.1, 0.34, 0.53)
        bar(f"maintainer.thigh{sx}", jeans, (sx * 0.09, 0.07, 0.55), kn, 0.068, m_root, verts=16)
        sphere(f"maintainer.knee{sx}", jeans, kn, 0.066, m_root, 16)
        bar(f"maintainer.shin{sx}", jeans, kn, (sx * 0.11, 0.4, 0.09), 0.052, m_root, verts=16)
        soft_box(f"maintainer.shoe{sx}", shoe, (sx * 0.11, 0.45, 0.04), (0.1, 0.24, 0.08), m_root)
    out["maintainer"] = m_root
    # The paper avalanche: drifts of printed tickets across the desk and floor, reaching the desk edge (N16).
    grey = K.mat_matte("base.paper", "paper")
    rnd = random.Random(SEEDS["main"] + 4)
    out["sheets_glow"] = []
    glow = K.empty("base.glow")
    K.prop(glow, "glow", 0.0)
    for k in range(220):
        r = rnd.random() ** 0.6
        a = rnd.uniform(0, math.tau)
        x, y = -0.8 + 1.4 * r * math.cos(a), 1.6 - 1.2 * r * abs(math.sin(a))
        z = Z0 + 0.01 + 0.35 * (1 - r) * rnd.random() if rnd.random() < 0.7 else dz + 0.03 + 0.12 * rnd.random()
        if z > dz and -0.15 < x < 0.85 and 0.7 < y < 1.6:  # keep the laptop's screen clear (N17's feed)
            z = Z0 + 0.01 + 0.35 * (1 - r) * rnd.random()
        lit = k % 17 == 0
        mat = K.mat_emission(f"base.sheet_glow{k}", "comfort", 1.5, glow, "glow", floor=0.0) if lit else grey
        sh = box(f"base.sheet{k}", mat, (x, y, z), (0.21, 0.297, 0.001), rot=(rnd.uniform(-0.3, 0.3),
                 rnd.uniform(-0.3, 0.3), rnd.uniform(0, math.tau)))
        if lit:
            out["sheets_glow"].append(sh)
    out["glow"] = glow
    # The mail slot in the ceiling: a lit opening, a frame and a flap on a hinge ("flap" 0 shut .. 1 swung down).
    # Folded tickets push through it, crease first, and drop to the desk (human, C4 review: the flat sheets of the
    # first version didn't read as coming through the slot).
    slot = K.empty("mailslot", (0.2, 1.6, Z1 - 0.06))  # just below the ceiling slab (its underside is Z1 - 0.05)
    K.prop(slot, "flap", 0.0)
    brass = K.mat_metal("mailslot.brass", "brass", 0.3)
    SW, SD = 0.42, 0.13  # the opening
    for k, (p, sz) in enumerate((((0, SD / 2 + 0.02, 0), (SW + 0.08, 0.04, 0.02)), ((0, -SD / 2 - 0.02, 0), (SW + 0.08, 0.04, 0.02)),
                                 ((SW / 2 + 0.02, 0, 0), (0.04, SD, 0.02)), ((-SW / 2 - 0.02, 0, 0), (0.04, SD, 0.02)))):
        box(f"mailslot.frame{k}", brass, p, sz, slot)
    # The chute above the opening, lit by the hall: its far end glows cold, so the slot reads as a way through.
    chute = mat_stone("mailslot.chute", "plinth", 0.9)
    for sy in (-1, 1):
        box(f"mailslot.chute{sy}", chute, (0, sy * (SD / 2 + 0.005), 0.06), (SW, 0.01, 0.1), slot)
    glow = box("mailslot.glow", K.mat_emission("mailslot.glow", "house", 6.0), (0, 0, 0.11), (SW, SD, 0.005), slot)
    glow.visible_shadow = False
    hinge = K.empty("mailslot.hinge", (0, SD / 2, -0.012), slot)
    K.drive(hinge, "rotation_euler", 0, slot, "flap", "-1.1 * x")
    box("mailslot.flap", K.mat_metal("mailslot.flap", "brass", 0.3), (0, -SD / 2, 0), (SW - 0.01, SD, 0.004), hinge)
    # The hall's cold light falls through the slot (N18 looks up at it; the ceiling is otherwise unlit).
    light("mailslot.light", "AREA", (0.2, 1.6, Z1 - 0.08), 30.0, "house", 0.3, target=(0.3, 1.3, Z0), specular=0.3)
    light("mailslot.beam", "SPOT", (0.2, 1.6, Z1 - 0.02), 120.0, "house", 0.05, target=(0.15, 1.45, Z0),
          spot=(0.55, 0.3), specular=0.3)  # a shaft through the basement's haze, lighting the tickets as they drop
    light("mailslot.ceiling", "POINT", (0.4, 1.3, Z1 - 0.6), 20.0, "tungsten", 0.3, specular=0.0)
    # Folded tickets the slot drops on the beat (N18): "drop<k>" 0 up in the chute .. 0.25 through the opening
    # (crease first) .. 1 on the desk (animate.basement).
    paper = K.mat_matte("mailslot.sheet", "paper")
    fall = (Z1 - 0.06) - (dz + 0.03)
    out["mailslot_n"] = 8
    for k in range(8):
        K.prop(slot, f"drop{k}", 0.0)
        f = K.empty(f"mailslot.fold{k}", (0, 0, 0), slot)
        for side in (-1, 1):  # two halves in a tent, the crease at the bottom
            half = K.empty(f"mailslot.fold{k}.h{side}", (0, 0, 0), f)
            half.rotation_euler = (side * 0.35, 0, 0)
            box(f"mailslot.fold{k}.p{side}", paper, (0, 0, 0.05), (0.2, 0.001, 0.1), half)
        dx, dy = 0.12 * ((k * 5) % 7 - 3) / 3, -0.1 - 0.03 * (k % 4)
        K.drive(f, "location", 2, slot, f"drop{k}",
                f"0.1 * (1 - min(x * 4, 1)) - {fall:.3f} * (max(x - 0.25, 0) / 0.75) ** 2")
        K.drive(f, "location", 0, slot, f"drop{k}", f"{dx:.3f} * max(x - 0.25, 0) / 0.75")
        K.drive(f, "location", 1, slot, f"drop{k}", f"{dy:.3f} * max(x - 0.25, 0) / 0.75")
        K.drive(f, "rotation_euler", 0, slot, f"drop{k}", f"{1.2 + 0.3 * k:.2f} * max(x - 0.25, 0) / 0.75")
        K.drive(f, "rotation_euler", 2, slot, f"drop{k}", f"{0.4 * ((k % 3) - 1):.2f} * max(x - 0.25, 0) / 0.75")
        K.drive(f, "scale", 0, slot, f"drop{k}", "1.0 if x > 0.01 else 0.001")
    out["mailslot"] = slot
    return out


def tickets():
    """Printed tickets: the stacks the mobile's pieces carry away (N13), the one that falls through the floor (N14,
    "fall" 0 at the mobile .. 1 on the basement desk), and the drift that piles against the glass (N29-N37,
    "drift" 0 .. 1 scales the pile)."""
    out = {}
    paper = K.mat_matte("ticket.paper", "paper")
    fall = K.empty("ticket.fall")
    t = box("ticket.fall.card", paper, (0, 0, 0), (0.11, 0.15, 0.001), fall)
    t.visible_shadow = False
    out["fall"] = fall
    pile = K.empty("ticket.pile", (0, -ROOM - 0.12, PL_H))
    K.prop(pile, "drift", 0.0)
    rnd = random.Random(SEEDS["main"] + 5)
    for k in range(60):
        x = rnd.uniform(-1.9, 1.9)
        if abs(x) < 1.0 and rnd.random() < 0.7:
            x = math.copysign(1.0 + rnd.random() * 0.9, x)
        box(f"ticket.pile{k}", paper, (x, -rnd.uniform(0, 0.25), rnd.uniform(0, 0.12)),
            (0.11, 0.15, 0.001), pile, rot=(rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(0, math.tau)))
    for i in range(3):
        K.drive(pile, "scale", i, pile, "drift", "max(0.001, x)")
    out["pile"] = pile
    return out


def shop_twin(shop):
    """Verse 4's twin in the shop crib (brief: "an identical crib, a green glint under a blanket", "mittens over two
    thin arms; a waiver on a clipboard, its pen on a string"): the chassis stays under the blanket (hidden until N38
    everywhere, brief): it is the kit's probe at the crib probe's scale, lying under a mound of blanket (crib(cover=...)),
    its two arms reaching out from under the felt along the blanket in felt mittens (human, C4 review: the first
    version's loose wires read as disconnected from any body). Only the glint, the arms and the clipboard show. Also
    the price tag's second face (AVAILABLE, from N36) and the display screen's placeholder for the real pages (N33,
    N34: composited at C5)."""
    out = {}
    c = shop["crib"]["root"]
    tw = K.probe("twin", (0, 0, 0), led_role="standby", led=0.6, scale=PROBE_SCALE)
    tw.parent = c
    tw.location = (PROBE_AT[0], PROBE_AT[1], nest_z(K.PROBE_R * PROBE_SCALE))
    tw.rotation_euler = (0, 0, math.pi / 2)  # lens and reach toward the crib's foot: in profile from the hall
    tw["arm_l"] = tw["arm_r"] = 1.0
    mitt = mat_felt("twin.mitten", "felt_cream")
    r = K.PROBE_R
    for side in ("l", "r"):
        elbow = bpy.data.objects[f"twin.elbow_{side}"]
        sphere(f"twin.mitten_{side}", mitt, (0, 0, -r * 0.88), r * 0.32, elbow, 16).scale = (1.0, 0.8, 1.5)
        for k in (-1, 1):
            bpy.data.objects[f"twin.finger_{side}{k}"].hide_render = True  # inside the mitten
    out["probe"] = tw
    # The clipboard lies on the blanket just past the mittens, as if held out to them (human, C4 v3 review: it stood
    # against the headboard and passed through it); it rides the blanket's breath there.
    clip = K.empty("twin.clipboard", (-0.02, 0.0, 0.0), c)
    clip.rotation_euler = (0, 0, math.pi)  # the waiver reads from the hall
    K.drive(clip, "location", 2, c, "breath", "0.478 + 0.004*x")
    box("twin.board", mat_paint("twin.board", "wood", 0.6), (0, 0, 0), (0.22, 0.3, 0.006), clip)
    box("twin.waiver", K.mat_matte("twin.waiver", "paper"), (0, 0, 0.004), (0.2, 0.27, 0.001), clip)
    K.text("twin.waiver_text", "WAIVER", 0.03, K.mat_ink("twin.ink", "shadow"), loc=(0, 0.09, 0.006), rot=(0, 0, 0),
           parent=clip)
    for k in range(6):
        box(f"twin.line{k}", K.mat_matte("twin.lines", "steel"), (0, 0.04 - k * 0.03, 0.006), (0.15, 0.003, 0.0005), clip)
    bar("twin.pen", K.mat_plastic("twin.pen", "shadow", 0.3), (0.06, -0.12, 0.01), (0.12, -0.02, 0.01), 0.004, clip)
    bar("twin.string", K.mat_matte("twin.string", "felt_grey"), (0.1, 0.15, 0.004), (0.12, -0.02, 0.01), 0.001, clip)
    tag2 = K.text("shop.tag_text2", "AVAILABLE", 0.03, K.mat_ink("tag_ink2", "shadow"), loc=(0, 0, 0.001),
                  rot=(0, 0, 0), font="Inter-Medium-flat.ttf", parent=bpy.data.objects["shop.tag"])
    out["tag_soon"], out["tag_available"] = bpy.data.objects["shop.tag_text"], tag2
    scr = shop["screen"]
    ph = K.empty("shop.screen_ph", scr.matrix_world.translation + Vector((-0.025, 0, 0)))
    K.prop(ph, "page", 0.0)
    pl = K.mesh_obj("shop.screen_page", bpy.ops.mesh.primitive_plane_add,
                    K.mat_emission("shop.page", "commerce", 2.0, ph, "page", floor=0.0), ph, size=1,
                    rotation=(math.pi / 2, 0, -math.pi / 2))
    pl.scale = (0.86, 0.5, 1)
    K.text("shop.screen_label", "[ real page, composited at C5 ]", 0.03, K.mat_ink("shop.ph_ink", "shadow"),
           loc=(-0.002, 0, 0), rot=(math.pi / 2, 0, -math.pi / 2), parent=ph)
    out["screen_ph"] = ph
    return out


def build(star_count=1.0, reveal=False):
    """The whole set; returns a dict of named rigs for the shot scripts."""
    S = {}
    S.update(hall())
    S.update(plinth())
    S.update(glass_room())
    S.update(nursery(S["root"]))
    S["stars"] = projected_stars(S["projector_pt"], 320, SEEDS["main"], star_count, reveal=reveal)
    st = street()
    S.update({f"street_{k}": v for k, v in st.items()})
    shop = shop_window()
    S.update({f"shop_{k}": v for k, v in shop.items()})
    if reveal:  # the C4+ additions: everything that appears, falls or lights during the song
        S["call_graph"], S["call_graph_n"] = call_graph(S["stars"], SEEDS["main"] + 1)
        S["floor_gaps"] = floor_gaps()
        S["town_crack"] = town_crack(st, SEEDS["main"] + 2)
        S["moat"] = moat()
        S["rope"] = velvet_rope()
        S.update({f"base_{k}": v for k, v in basement().items()})
        S.update({f"ticket_{k}": v for k, v in tickets().items()})
        S.update({f"twin_{k}": v for k, v in shop_twin(shop).items()})
    S.update(hall_lights())
    if LOOK.get("haze_density"):
        S["haze"] = haze(LOOK["haze_density"])
    return S
