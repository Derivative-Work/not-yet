"""Shared kit (brief, "Sets → Shared kit"): Python-built assets reused in every set.

Everything here is procedural and deterministic: no random calls, so a rebuild gives the same geometry. Colors come
from config/look.json (written from style/style_spec.md), never hard-coded in a set.

Units are metres. Rigs expose a few named custom properties that the note-driven animation library (step 7) keys:
  probe:  "led" (0–1 LED intensity), "arm_l" / "arm_r" (0–1 reach)
  blade:  "vent" (0 = louvres closed, 1 = open)
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[3]
LOOK = json.loads((ROOT / "config" / "look.json").read_text())


# ---------------------------------------------------------------- colour and materials

def lin(hexstr, a=1.0):
    """sRGB hex -> linear RGBA, as Blender's colour sockets expect."""
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    h = hexstr.lstrip("#")
    return (ch(int(h[0:2], 16)), ch(int(h[2:4], 16)), ch(int(h[4:6], 16)), a)


def col(role):
    return lin(LOOK["palette"][role])


def _principled(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes["Principled BSDF"]


def mat_plastic(name, role, rough=None):
    """Glossy plastic: the Animusic default surface (spec, 'Materials')."""
    m, b = _principled(name)
    b.inputs["Base Color"].default_value = col(role)
    b.inputs["Roughness"].default_value = LOOK["materials"]["plastic_roughness"] if rough is None else rough
    b.inputs["Coat Weight"].default_value = LOOK["materials"]["plastic_coat"]
    b.inputs["Coat Roughness"].default_value = 0.03
    return m


def mat_matte(name, role):
    """Matte, no coat, no specular: signs, cards and lettering that must never pick up the room's highlights and
    wash out (glossy ones did, in the lit sets; human, C4 v4: "all rendered text for contrast")."""
    m, b = _principled(name)
    b.inputs["Base Color"].default_value = col(role)
    b.inputs["Roughness"].default_value = 0.95
    b.inputs["Specular IOR Level"].default_value = 0.0
    return m


def mat_ink(name, role="shadow"):
    """Printed or painted lettering: matte, and text() sets it a little heavier."""
    m = mat_matte(name, role)
    m["ink"] = True
    return m


def mat_chrome(name, role="chrome"):
    m, b = _principled(name)
    b.inputs["Base Color"].default_value = col(role)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = LOOK["materials"]["chrome_roughness"]
    return m


def mat_metal(name, role, rough):
    m, b = _principled(name)
    b.inputs["Base Color"].default_value = col(role)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    return m


def mat_glass(name, role="glass", tint=0.94, reflect=0.7):
    """Thin clear glass: tinted transparency plus a Fresnel-weighted reflection of a procedural studio environment.

    The environment is computed in the shader from the reflection vector: the world's violet horizon band, a dark
    floor below, a soft warm key glow high front-left and a cool strip high behind. It is noise-free and
    deterministic, and reads like the environment-mapped glass of Animusic's era.
    Tried and rejected (log, step 3):
      - raytraced refraction: Eevee refracts one layer only, and the cube's panes stack;
      - dithered transparency: grain, and it darkens and smears what's behind;
      - a glossy BSDF on the sphere light probe: the probe's capture is noisy, which showed as speckle across every
        pane, and its influence edge drew a ring on the floor."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()

    def node(kind, **inputs):
        n = nt.nodes.new(kind)
        for k, v in inputs.items():
            n.inputs[k].default_value = v
        return n

    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Reflection"], sep.inputs[0])
    # Vertical gradient: floor (dark) -> horizon band -> zenith.
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.42, col("floor")
    els[1].position, els[1].color = 0.56, col("void")
    mid = els.new(0.5)
    mid.color = col("horizon")
    mapz = node("ShaderNodeMapRange", **{"From Min": -1.0, "From Max": 1.0})
    nt.links.new(sep.outputs["Z"], mapz.inputs["Value"])
    nt.links.new(mapz.outputs[0], ramp.inputs[0])
    env = ramp.outputs[0]
    # Soft light glows: smooth spots around the key and rim directions.
    for role, d, size, gain in (("key", Vector((-0.55, -0.8, 0.75)), 0.3, 4.0),
                                ("rim", Vector((0.0, 1.0, 0.45)), 0.2, 2.5)):
        dot = nt.nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        dot.inputs[1].default_value = d.normalized()
        nt.links.new(tc.outputs["Reflection"], dot.inputs[0])
        spot = node("ShaderNodeMapRange", **{"From Min": 1.0 - size, "From Max": 1.0, "To Min": 0.0, "To Max": gain})
        spot.interpolation_type = "SMOOTHSTEP"
        nt.links.new(dot.outputs["Value"], spot.inputs["Value"])
        add = nt.nodes.new("ShaderNodeMix")
        add.data_type = "RGBA"
        add.blend_type = "ADD"
        add.inputs["B"].default_value = col(role)
        nt.links.new(spot.outputs[0], add.inputs["Factor"])
        nt.links.new(env, add.inputs["A"])
        env = add.outputs["Result"]
    # Reflection is added on top of the transmission (not mixed in), so the dark parts of the environment don't
    # darken what's behind the glass; only the bright bands and glows show.
    fr = node("ShaderNodeFresnel", IOR=1.5)
    k = node("ShaderNodeMath")
    k.operation = "MULTIPLY"
    k.inputs[1].default_value = reflect
    nt.links.new(fr.outputs[0], k.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(env, em.inputs["Color"])
    nt.links.new(k.outputs[0], em.inputs["Strength"])
    c = col(role)
    tr = node("ShaderNodeBsdfTransparent", Color=(c[0] * tint, c[1] * tint, c[2] * tint, 1))
    mix = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], mix.inputs[0])
    nt.links.new(em.outputs[0], mix.inputs[1])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix.outputs[0], out.inputs[0])
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = False
    return m


def mat_acrylic(name, role, alpha=0.35, emit=0.0):
    """Translucent tinted acrylic, optionally glowing from inside (LED housings, pellets)."""
    m, b = _principled(name)
    b.inputs["Base Color"].default_value = col(role)
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Emission Color"].default_value = col(role)
    b.inputs["Emission Strength"].default_value = emit
    m.surface_render_method = "BLENDED"
    return m


def mat_emission(name, role, strength, prop_owner=None, prop=None, floor=0.04):
    """Emitter whose strength can be driven by a custom property on `prop_owner` (0–1 scales `strength`, above an
    idle `floor`)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = col(role)
    e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    if prop_owner is not None:
        fc = e.inputs["Strength"].driver_add("default_value")
        d = fc.driver
        d.type = "SCRIPTED"
        v = d.variables.new()
        v.name = "x"
        v.targets[0].id_type = "OBJECT"
        v.targets[0].id = prop_owner
        v.targets[0].data_path = f'["{prop}"]'
        d.expression = f"{strength} * ({floor} + {1 - floor} * x)"
    return m


def mat_glow_fade(name, role, strength, prop_owner, prop):
    """Emitter that fades to clear: `prop_owner[prop]` (0-1) mixes it from fully transparent to full strength, so
    at 0 it vanishes instead of turning into a dark solid (the voice rings)."""
    m = mat_emission(name, role, strength, prop_owner, prop, floor=0.0)
    nt = m.node_tree
    e = next(n for n in nt.nodes if n.type == "EMISSION")
    o = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(e.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs[0])
    drive(mix.inputs[0], "default_value", None, prop_owner, prop, "min(1.0, 3.0 * x)")
    m.surface_render_method = "BLENDED"
    return m


def mat_mirror_floor(name="floor"):
    """Black mirror floor (spec, 'Background'): near-black, low roughness, reflections fade with distance."""
    m, b = _principled(name)
    b.inputs["Base Color"].default_value = col("floor")
    b.inputs["Roughness"].default_value = LOOK["materials"]["floor_roughness"]
    b.inputs["Specular IOR Level"].default_value = 0.5
    return m


# ---------------------------------------------------------------- helpers

def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def mesh_obj(name, mesh_op, mat=None, parent=None, **kw):
    if mesh_op == bpy.ops.mesh.primitive_torus_add:  # Blender's 48x12 default faceted rings in 4K close-ups (C5)
        kw.setdefault("major_segments", 96)
        kw.setdefault("minor_segments", 16)
    mesh_op(**kw)
    o = bpy.context.active_object
    o.name = name
    if mat:
        o.data.materials.append(mat)
    if parent:
        o.parent = parent
    return o


def bevel(o, width, segments=3):
    md = o.modifiers.new("bevel", "BEVEL")
    md.width = width
    md.segments = segments
    md.limit_method = "ANGLE"
    return o


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def smooth_by_angle(angle_deg=35.0):
    """Shade every flat-shaded mesh smooth, keeping edges sharper than `angle_deg` hard: curved parts (cylinders,
    spheres, tori, lathes) read round while boxes, bevels' flats and hex sections keep their edges. Run once a set is
    built (C5: flat-shaded curved parts, e.g. the freezer's doorway frame, read as low-poly at 4K)."""
    n = 0
    for me in {o.data for o in bpy.data.objects if o.type == "MESH"}:
        if me.polygons and not all(p.use_smooth for p in me.polygons):
            me.shade_smooth()
            me.set_sharp_from_angle(angle=math.radians(angle_deg))
            n += 1
    return n


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    link(e)
    if parent:
        e.parent = parent
    return e


def prop(o, key, value, lo=0.0, hi=1.0):
    o[key] = value
    o.id_properties_ui(key).update(min=lo, max=hi)


def drive(target, path, index, owner, key, expr):
    """target.path[index] = expr(x), x = owner[key]."""
    fc = target.driver_add(path, index) if index is not None else target.driver_add(path)
    d = fc.driver
    d.type = "SCRIPTED"
    v = d.variables.new()
    v.name = "x"
    v.targets[0].id_type = "OBJECT"
    v.targets[0].id = owner
    v.targets[0].data_path = f'["{key}"]'
    d.expression = expr


def refresh():
    """Re-evaluate rig drivers after custom properties were set directly (not keyed): assigning obj["vent"] doesn't
    tag the depsgraph, so the driven slats/arms/LEDs would render at their old values."""
    for o in bpy.data.objects:
        if o.keys():
            o.update_tag()
    for m in bpy.data.materials:  # emission strengths driven by the same properties
        if m.node_tree and m.node_tree.animation_data:
            m.node_tree.update_tag()
    # A driver flagged invalid (e.g. evaluated once before its target existed) is skipped until cleared; clear every
    # flag so each is retried (sub-agent report, set G: drivers made in build() silently never evaluated).
    for idb in _driven_ids():
        ad = idb.animation_data
        for fc in (ad.drivers if ad else []):
            fc.driver.is_valid = True
    bpy.context.view_layer.update()


def _driven_ids():
    return list(bpy.data.objects) + list(bpy.data.lights) + [m.node_tree for m in bpy.data.materials if m.node_tree]


def rebind_drivers():
    """Remake every single-variable kit driver (drive(), mat_emission) after the set is keyed. Some drivers made while
    building never evaluate: Blender fails them each time and writes 0 to the channel (C4 v2: set G's kill buttons sank
    into the tower's body; found by the set G sub-agent). The same driver made after the keys exist works."""
    n = 0
    for idb in _driven_ids():
        ad = idb.animation_data
        for fc in list(ad.drivers if ad else []):
            d = fc.driver
            if fc.data_path.startswith("constraints") or len(d.variables) != 1 or d.variables[0].name != "x":
                continue
            tgt = d.variables[0].targets[0]
            path, idx, owner, key, expr = fc.data_path, fc.array_index, tgt.id, tgt.data_path[2:-2], d.expression
            arr = hasattr(idb.path_resolve(path), "__len__")
            idb.driver_remove(path, idx) if arr else idb.driver_remove(path)
            drive(idb, path, idx if arr else None, owner, key, expr)
            n += 1
    return n


def invalid_drivers():
    """Drivers Blender flags invalid after evaluating the current frame (should be none)."""
    bpy.context.view_layer.update()
    return [(idb.name, fc.data_path, fc.array_index) for idb in _driven_ids()
            for fc in (idb.animation_data.drivers if idb.animation_data else []) if not fc.driver.is_valid]


# ---------------------------------------------------------------- render setup

def setup_render(scene, width, height, samples):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.fps = LOOK["fps"]
    ee = scene.eevee
    ee.taa_render_samples = samples
    ee.use_raytracing = True
    ee.ray_tracing_options.resolution_scale = "1"
    ee.ray_tracing_options.screen_trace_quality = 1.0
    ee.use_shadows = True
    ee.shadow_pool_size = "2048"  # MB; the 512 default overflows at 4K ("Shadow buffer full", missing shadows)
    ee.fast_gi_method = "GLOBAL_ILLUMINATION"
    ee.gi_cubemap_resolution = LOOK["probe_resolution"]  # see spec, Lighting
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = LOOK["agx_look"]
    scene.view_settings.exposure = LOOK["exposure"]
    scene.world = void_world()
    return scene


def void_world():
    """The surround (spec, 'Background'): not black. A vertical gradient from the floor-level horizon glow up to a
    deep violet-black zenith. The stars are a separate dome (star_dome) so reflections and light probes never see
    them: in the world shader they were baked into the reflection probe and sparkled as grain on the glass."""
    world = bpy.data.worlds.new("void")
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = col("horizon")
    ramp.color_ramp.elements[1].position = 0.35
    ramp.color_ramp.elements[1].color = col("void")
    nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(ramp.outputs[0], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    o = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], o.inputs[0])
    return world


def star_dome(radius=150.0):
    """Sparse, faint starfield on an inverted sphere seen by camera rays only. About 12% of Voronoi cells hold a
    star, at random brightness, above the horizon. Deterministic (procedural, no seed)."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=64, ring_count=32, location=(0, 0, 0))
    o = bpy.context.active_object
    o.name = "star_dome"
    m = bpy.data.materials.new("stars")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 220.0
    nt.links.new(tc.outputs["Normal"], vor.inputs["Vector"])
    sepc = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(vor.outputs["Color"], sepc.inputs[0])
    sepn = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Normal"], sepn.inputs[0])

    def math(op, a, b):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    star = math("LESS_THAN", vor.outputs["Distance"], 0.06)
    keep = math("GREATER_THAN", sepc.outputs["Red"], 0.88)
    above = math("LESS_THAN", sepn.outputs["Z"], -0.04)  # inverted sphere: inward normals, so the sky has Z < 0
    v = math("MULTIPLY", math("MULTIPLY", math("MULTIPLY", star, keep), sepc.outputs["Green"]), above)
    v = math("MULTIPLY", v, LOOK["stars"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(v, em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(math("GREATER_THAN", v, 0.0), mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix.outputs[0], out.inputs[0])
    m.surface_render_method = "BLENDED"
    o.data.materials.append(m)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode="OBJECT")
    o.visible_glossy = o.visible_diffuse = o.visible_shadow = o.visible_transmission = False
    o.hide_probe_sphere = o.hide_probe_volume = o.hide_probe_plane = True
    return o


def reflection_cards(center=(0, 0, 0.6), radius=7.0):
    """Large soft emissive cards that the camera never sees directly (ray visibility off) but chrome, glass and the
    floor reflect: Animusic's chrome reads because it mirrors bright shapes, not the dark surround."""
    out = []
    c = Vector(center)
    C = LOOK["cards"]
    for name, d, role, strength, size in (("card_warm", (-0.7, -0.6, 0.5), "key", C["warm"], (6, 3)),
                                          ("card_cool", (0.8, 0.5, 0.35), "fill", C["cool"], (8, 2)),
                                          ("card_top", (0.0, 0.0, 1.0), "rim", C["top"], (5, 5))):
        bpy.ops.mesh.primitive_plane_add(size=1, location=c + Vector(d).normalized() * radius)
        o = bpy.context.active_object
        o.name = name
        o.scale = (size[0], size[1], 1)
        o.rotation_euler = (c - o.location).to_track_quat("Z", "Y").to_euler()
        o.data.materials.append(mat_emission(name, role, strength))
        o.visible_camera = False
        o.visible_shadow = False
        out.append(o)
    return out


def reflection_probe(center=(0, 0, 0.6), radius=0.6):
    """Sphere light probe for close-ups of chrome (the probe rig, rails): lets them reflect the off-screen cards and
    set. Keep it small and centred on the hero: its capture is noisy at large scale and its influence edge shows in
    the mirror floor (log, step 3). Glass doesn't use it (see mat_glass)."""
    bpy.ops.object.lightprobe_add(type="SPHERE", location=center)
    o = bpy.context.active_object
    o.data.influence_distance = radius
    return o


def area_light(name, loc, target, power, size, role="key", shape="RECTANGLE", size_y=None, specular=1.0):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = power
    ld.specular_factor = specular
    ld.shape = shape
    ld.size = size
    ld.size_y = size_y or size
    ld.color = col(role)[:3]
    o = link(bpy.data.objects.new(name, ld))
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def studio_lights(center=(0, 0, 0.6), radius=6.0, scale=1.0):
    """Soft key from front-left above, strong cool rim pair from behind, faint fill (spec, 'Lighting')."""
    L = LOOK["lights"]
    c = Vector(center)
    out = [
        area_light("key", c + Vector((-0.55, -0.8, 0.75)) * radius, c, L["key"] * scale, radius * 0.5, "key",
                   shape="ELLIPSE", specular=L["key_specular"]),
        area_light("fill", c + Vector((0.9, -0.5, 0.2)) * radius, c, L["fill"] * scale, radius * 0.6, "fill"),
        # Rims light edges through diffuse grazing; full specular made them a bright halo in the mirror floor and a
        # white strip in the glass.
        area_light("rim_l", c + Vector((-0.8, 0.9, 0.45)) * radius, c, L["rim"] * scale, radius * 0.18, "rim",
                   size_y=radius * 0.6, specular=L["rim_specular"]),
        area_light("rim_r", c + Vector((0.85, 0.85, 0.5)) * radius, c, L["rim"] * scale, radius * 0.18, "rim",
                   size_y=radius * 0.6, specular=L["rim_specular"]),
    ]
    return out


def floor(size=200.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    o = bpy.context.active_object
    o.name = "floor"
    o.data.materials.append(mat_mirror_floor())
    return o


def camera(name, loc, target, lens=35.0, dof_fstop=None, focus=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.01, 500
    o = link(bpy.data.objects.new(name, cd))
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if dof_fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = dof_fstop
        cd.dof.focus_distance = focus or (Vector(target) - Vector(loc)).length
    bpy.context.scene.camera = o
    return o


# ---------------------------------------------------------------- probe rig

PROBE_R = 0.034  # tennis-ball size (brief, "The agents")
VOICE_RINGS = 3  # rings in flight at once per singing probe (sr_anim.sing)


def voice_rings(name, owner, parent, r, led_role="amber", at=(0, 0, 0), strength=40.0, thick=0.03):
    """Voice rings: on each sung word a glowing ring leaves `at` along the parent's -Y, widening and fading as it
    travels out (sr_anim.voice_rings keys `owner`'s "wave<k>", the ring's phase, and "wave_a<k>", its brightness).
    They read where a singing probe is small in frame or turned away, and from a singer's POV (human, C5 set A: the
    singing in S07/S08 "too subtle"). `r` sets the size (a probe's radius); `thick`, the tube's share of it."""
    for k in range(VOICE_RINGS):
        prop(owner, f"wave{k}", 0.0)
        prop(owner, f"wave_a{k}", 0.0)
        ring = mesh_obj(f"{name}.wave{k}", bpy.ops.mesh.primitive_torus_add, mat_glow_fade(f"{name}.wave{k}", led_role,
                        strength, owner, f"wave_a{k}"), parent, major_radius=r * 0.52, minor_radius=r * thick,
                        major_segments=64, minor_segments=8, location=at, rotation=(math.pi / 2, 0, 0))
        smooth(ring)
        ring.visible_shadow = False
        for i in range(3):  # hidden (scale 0) until its first word
            drive(ring, "scale", i, owner, f"wave{k}", "(0.9 + 3.0 * x) if x > 0 else 0")
        drive(ring, "location", 1, owner, f"wave{k}", f"{at[1]} - {r * 3.0} * x")


def pov_voice(name, cam, r=0.08, led_role="amber"):
    """A singer's voice seen from its own lens: voice rings leaving the camera `cam` along its view (a POV shot),
    thin and dimmer than a probe's, since they pass close to the lens and widen out past the frame's edges.
    Returns the empty that carries the "wave" properties (key it with sr_anim.voice_rings)."""
    top = empty(name, (0, 0, 0), cam)
    top.rotation_euler = (math.pi / 2, 0, 0)  # local -Y along the camera's -Z (its view)
    voice_rings(name, top, top, r, led_role, (0, -r * 2.0, 0), strength=10.0, thick=0.008)
    return top


def probe(name="probe", loc=(0, 0, 0), led_role="amber", led=1.0, scale=1.0):
    """Polished sphere, one lens, one status LED, two thin manipulator arms. Faces -Y (lens forward).
    "sing" (0-1, sr_anim.sing) is its voice: the body lifts and tilts its lens up, the iris opens and a halo round the
    lens lights (human, C4: the protagonist's singing, an LED alone, was "too subtle")."""
    r = PROBE_R
    top = empty(name, loc)
    top.scale = (scale,) * 3
    prop(top, "led", led)
    prop(top, "arm_l", 0.2)
    prop(top, "arm_r", 0.2)
    prop(top, "sing", 0.0)
    root = empty(f"{name}.body", (0, 0, 0), top)  # every part hangs here, so singing moves the whole probe
    drive(root, "location", 2, top, "sing", f"{r * 0.3} * x")
    drive(root, "rotation_euler", 0, top, "sing", "-0.16 * x")  # lens (-Y) tips up a little (0.38 nodded, C4 v2)

    shell = mesh_obj(f"{name}.shell", bpy.ops.mesh.primitive_uv_sphere_add, mat_chrome(f"{name}.chrome", "probe"),
                     root, radius=r, segments=48, ring_count=24, location=(0, 0, 0))
    smooth(shell)
    # Lens: a dark glass bulge in a chrome bezel, facing -Y.
    bezel = mesh_obj(f"{name}.bezel", bpy.ops.mesh.primitive_torus_add, mat_chrome(f"{name}.bezel", "chrome"), root,
                     major_radius=r * 0.42, minor_radius=r * 0.07, location=(0, -r * 0.9, r * 0.05),
                     rotation=(math.pi / 2, 0, 0))
    smooth(bezel)
    lens = mesh_obj(f"{name}.lens", bpy.ops.mesh.primitive_uv_sphere_add, mat_plastic(f"{name}.lens", "lens", 0.02),
                    root, radius=r * 0.4, segments=32, ring_count=16, location=(0, -r * 0.78, r * 0.05))
    lens.scale = (1, 0.55, 1)
    smooth(lens)
    iris = mesh_obj(f"{name}.iris", bpy.ops.mesh.primitive_circle_add, mat_emission(f"{name}.iris", led_role, 6.0, top, "led"),
                    root, radius=r * 0.16, vertices=32, fill_type="NGON", location=(0, -r * 1.0, r * 0.05),
                    rotation=(math.pi / 2, 0, 0))
    for i in (0, 1):
        drive(iris, "scale", i, top, "sing", "1 + 1.3 * x")
    halo = mesh_obj(f"{name}.halo", bpy.ops.mesh.primitive_torus_add,
                    mat_emission(f"{name}.halo", led_role, 30.0, top, "sing"), root, major_radius=r * 0.52,
                    minor_radius=r * 0.035, location=(0, -r * 0.86, r * 0.05), rotation=(math.pi / 2, 0, 0))
    smooth(halo)
    voice_rings(name, top, root, r, led_role, (0, -r * 0.9, r * 0.05))
    # Status LED on top, in a small acrylic dome.
    ledo = mesh_obj(f"{name}.led", bpy.ops.mesh.primitive_uv_sphere_add,
                    mat_emission(f"{name}.led", led_role, 40.0, top, "led"), root, radius=r * 0.13, segments=16,
                    ring_count=8, location=(0, -r * 0.1, r * 0.97))
    smooth(ledo)
    # Arms: two-segment thin chrome rods from the equator, with a tiny pincer.
    for side, sx in (("l", -1), ("r", 1)):
        shoulder = empty(f"{name}.shoulder_{side}", (sx * r * 0.92, 0, -r * 0.1), root)
        upper = mesh_obj(f"{name}.upper_{side}", bpy.ops.mesh.primitive_cylinder_add, mat_chrome(f"{name}.arm", "chrome"),
                         shoulder, radius=r * 0.045, depth=r * 1.1, vertices=12, location=(0, 0, -r * 0.55))
        elbow = empty(f"{name}.elbow_{side}", (0, 0, -r * 1.1), shoulder)
        fore = mesh_obj(f"{name}.fore_{side}", bpy.ops.mesh.primitive_cylinder_add, mat_chrome(f"{name}.arm", "chrome"),
                        elbow, radius=r * 0.035, depth=r * 0.9, vertices=12, location=(0, 0, -r * 0.45))
        joint = mesh_obj(f"{name}.joint_{side}", bpy.ops.mesh.primitive_uv_sphere_add, mat_chrome(f"{name}.arm", "chrome"),
                         elbow, radius=r * 0.07, segments=12, ring_count=8, location=(0, 0, 0))
        for k in (-1, 1):
            f = mesh_obj(f"{name}.finger_{side}{k}", bpy.ops.mesh.primitive_cube_add, mat_chrome(f"{name}.arm", "chrome"),
                         elbow, size=1, location=(k * r * 0.05, 0, -r * 0.95))
            f.scale = (r * 0.025, r * 0.05, r * 0.16)
        # Reach 0 = arm folded along the body, 1 = stretched forward.
        drive(shoulder, "rotation_euler", 0, top, f"arm_{side}", "-0.25 - 1.25 * x")
        drive(shoulder, "rotation_euler", 1, top, f"arm_{side}", f"{sx} * (0.35 - 0.2 * x)")
        drive(elbow, "rotation_euler", 0, top, f"arm_{side}", "-1.1 + 0.95 * x")
    return top


# ---------------------------------------------------------------- server blade

def blade(name="blade", loc=(0, 0, 0), rot_z=0.0, width=0.48, height=0.09, depth=0.62, slats=9):
    """A 2U server blade: glossy pale chassis, chrome handles, a louvred front grille whose slats open with "vent",
    and a row of status LEDs. Front faces -Y."""
    root = empty(name, loc)
    root.rotation_euler = (0, 0, rot_z)
    prop(root, "vent", 0.0)
    prop(root, "led", 0.5)

    body = mesh_obj(f"{name}.body", bpy.ops.mesh.primitive_cube_add, mat_plastic(f"{name}.body", "lab"), root,
                    size=1, location=(0, 0, height / 2))
    body.scale = (width, depth, height)
    bevel(body, 0.006)
    # Chrome face plate, a recessed dark grille well in it, the glow behind, the louvres in front.
    face = mesh_obj(f"{name}.face", bpy.ops.mesh.primitive_cube_add, mat_chrome(f"{name}.face", "chrome"), root,
                    size=1, location=(0, -depth / 2 - 0.002, height / 2))
    face.scale = (width * 0.98, 0.004, height * 0.94)
    bevel(face, 0.002, 2)
    gw, gh = width * 0.8, height * 0.82
    well = mesh_obj(f"{name}.well", bpy.ops.mesh.primitive_cube_add, mat_plastic(f"{name}.well", "shadow", 0.4), root,
                    size=1, location=(-width * 0.07, -depth / 2 - 0.0035, height / 2))
    well.scale = (gw, 0.004, gh)
    glow = mesh_obj(f"{name}.glow", bpy.ops.mesh.primitive_plane_add,
                    mat_emission(f"{name}.glow", "lab_glow", LOOK["vent_glow"], root, "vent"), root, size=1,
                    location=(-width * 0.07, -depth / 2 - 0.006, height / 2), rotation=(math.pi / 2, 0, 0))
    glow.scale = (gw * 0.97, gh * 0.9, 1)
    slat_h = gh / slats
    for i in range(slats):
        z = height / 2 - gh / 2 + slat_h * (i + 0.5)
        pivot = empty(f"{name}.slat_pivot{i}", (-width * 0.07, -depth / 2 - 0.009, z), root)
        s = mesh_obj(f"{name}.slat{i}", bpy.ops.mesh.primitive_cube_add, mat_plastic(f"{name}.slat", "lab_dark", 0.1), pivot,
                     size=1, location=(0, 0, 0))
        s.scale = (gw, slat_h * 0.98, 0.0015)
        s.rotation_euler = (math.pi / 2, 0, 0)
        # vent 0: slats vertical (closed); 1: rotated 80° front-edge-down (open). Cameras mostly look down on the
        # blades, so slats tilted this way line up with the view and the glow shows through.
        drive(pivot, "rotation_euler", 0, root, "vent", "-1.4 * x")
    # Handles.
    for sx in (-1, 1):
        h = mesh_obj(f"{name}.handle{sx}", bpy.ops.mesh.primitive_torus_add, mat_chrome(f"{name}.handle", "chrome"), root,
                     major_radius=height * 0.28, minor_radius=0.004, location=(sx * width * 0.46, -depth / 2 - 0.009,
                                                                               height / 2),
                     rotation=(0, math.pi / 2, 0))
        h.scale = (1, 0.5, 1)
    # Status LEDs right of the grille.
    for i in range(3):
        mesh_obj(f"{name}.ledrow{i}", bpy.ops.mesh.primitive_uv_sphere_add,
                 mat_emission(f"{name}.ledrow{i}", "amber" if i == 0 else "lab_glow", 12.0, root, "led"), root,
                 radius=0.0045, segments=12, ring_count=6,
                 location=(width * 0.36 + i * 0.016, -depth / 2 - 0.005, height * 0.5))
    return root


# ---------------------------------------------------------------- the sandbox cube

def glass_cube(name="sandbox", size=2.0, loc=(0, 0, 0)):
    """Glass cube with thin chrome edge frame, standing on the floor. Returns the root empty."""
    root = empty(name, loc)
    glass = mat_glass(f"{name}.glass")
    half = size / 2
    panes = {"front": ((0, -half, half), (math.pi / 2, 0, 0)), "back": ((0, half, half), (math.pi / 2, 0, 0)),
             "left": ((-half, 0, half), (math.pi / 2, 0, math.pi / 2)),
             "right": ((half, 0, half), (math.pi / 2, 0, math.pi / 2)), "top": ((0, 0, size), (0, 0, 0))}
    for side, (p, r) in panes.items():
        mesh_obj(f"{name}.pane_{side}", bpy.ops.mesh.primitive_plane_add, glass, root, size=size, location=p,
                 rotation=r)
    # Edge frame: 12 thin chrome bars.
    t = 0.018
    half = size / 2
    edges = []
    for a in (-1, 1):
        for b in (-1, 1):
            edges += [((0, a * half, half + b * half), (size + t, t, t)),
                      ((a * half, 0, half + b * half), (t, size + t, t)),
                      ((a * half, b * half, half), (t, t, size + t))]
    for i, (p, s) in enumerate(edges):
        e = mesh_obj(f"{name}.edge{i}", bpy.ops.mesh.primitive_cube_add, mat_chrome(f"{name}.edge", "chrome"), root,
                     size=1, location=p)
        e.scale = s
        bevel(e, t * 0.3, 2)
    return root


# ---------------------------------------------------------------- text, glow, set dressing

FONTS = ROOT / "assets" / "fonts"


def text(name, body, size, mat, loc=(0, 0, 0), rot=(math.pi / 2, 0, 0), font="Inter-Medium-flat.ttf", extrude=0.0,
         align="CENTER", parent=None):
    """A text object (signs, notes, decals, displays): crisp at any resolution, never a painted texture."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.font = bpy.data.fonts.load(str(FONTS / font), check_existing=True)
    o = link(bpy.data.objects.new(name, cu))
    o.location, o.rotation_euler = loc, rot
    o.data.materials.append(mat)
    if mat.get("ink"):
        cu.offset = size * 0.04  # heavier than the font's regular weight, so strokes hold up against glare
    if parent:
        o.parent = parent
    return o


def bloom(scene, threshold=None, size=None, mix=None):
    """Compositor bloom so emitters (vent glow, LEDs, pellets, tubes) carry light into the frame, as Animusic's
    glows do. Eevee Next has no bloom of its own."""
    B = LOOK["bloom"]
    nt = bpy.data.node_groups.new("comp", "CompositorNodeTree")  # Blender 5: the compositor is a node group
    scene.compositing_node_group = nt
    rl = nt.nodes.new("CompositorNodeRLayers")
    g = nt.nodes.new("CompositorNodeGlare")
    g.inputs["Type"].default_value = "Bloom"  # Blender 5: glare settings are sockets
    g.inputs["Threshold"].default_value = threshold or B["threshold"]
    g.inputs["Size"].default_value = size or B["size"]
    g.inputs["Strength"].default_value = mix or B["strength"]
    nt.links.new(rl.outputs["Image"], g.inputs["Image"])
    nt.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    out = nt.nodes.new("NodeGroupOutput")
    nt.links.new(g.outputs["Image"], out.inputs[0])
    return g


def music_box(name="musicbox", loc=(0, 0, 0), scale=1.0, rot_z=0.0, parent=None):
    """A wind-up music box mechanism with its lid off: dark lacquer case, brass pinned drum on a copper axle, a
    steel comb whose teeth the pins pluck, a crank. "drum" (0–1) is the drum's turn; the comb teeth carry the
    note-driven pluck in step 7. Front faces -Y."""
    root = empty(name, loc, parent)
    root.scale = (scale,) * 3
    root.rotation_euler = (0, 0, rot_z)
    prop(root, "drum", 0.0)
    case = mesh_obj(f"{name}.case", bpy.ops.mesh.primitive_cube_add, mat_plastic(f"{name}.case", "lab_dark", 0.15),
                    root, size=1, location=(0, 0, 0.035))
    case.scale = (0.17, 0.11, 0.07)
    bevel(case, 0.006)
    deck = mesh_obj(f"{name}.deck", bpy.ops.mesh.primitive_cube_add, mat_metal(f"{name}.deck", "brass", 0.2), root,
                    size=1, location=(0, 0, 0.071))
    deck.scale = (0.16, 0.10, 0.003)
    axle = empty(f"{name}.axle", (0, 0.018, 0.098), root)
    drive(axle, "rotation_euler", 0, root, "drum", "6.2832 * x")
    drum = mesh_obj(f"{name}.drum", bpy.ops.mesh.primitive_cylinder_add, mat_metal(f"{name}.drum", "brass", 0.1),
                    axle, radius=0.02, depth=0.11, vertices=48, rotation=(0, math.pi / 2, 0))
    smooth(drum)
    pin_mat = mat_chrome(f"{name}.pin")
    for i in range(60):  # pins in a fixed scatter (golden angle), no random calls
        a = i * 2.39996
        x = -0.05 + (i * 0.618 % 1.0) * 0.1
        mesh_obj(f"{name}.pin{i}", bpy.ops.mesh.primitive_cylinder_add, pin_mat, axle, radius=0.0012, depth=0.006,
                 vertices=6, location=(x, math.sin(a) * 0.022, math.cos(a) * 0.022),
                 rotation=(-a, 0, 0))  # points radially out of the drum
    # Teeth, low (left) to high: each hinges at the comb base; "tooth<k>" (0-1, sr_anim.comb) lifts its tip and
    # lights it, so every plucked note shows (human, C4: the piano at the end couldn't be seen).
    comb_m = mat_chrome(f"{name}.comb")
    for k in range(18):
        L = 0.05 - k * 0.0012
        prop(root, f"tooth{k}", 0.0)
        hinge = empty(f"{name}.hinge{k}", (-0.051 + k * 0.006, -0.051, 0.084), root)
        drive(hinge, "rotation_euler", 0, root, f"tooth{k}", "0.3 * x")
        t = mesh_obj(f"{name}.tooth{k}", bpy.ops.mesh.primitive_cube_add, comb_m, hinge, size=1,
                     location=(0, L / 2, 0))
        t.scale = (0.0042, L, 0.0015)
        tip = mesh_obj(f"{name}.tip{k}", bpy.ops.mesh.primitive_cube_add,
                       mat_emission(f"{name}.tip{k}", "amber", 60.0, root, f"tooth{k}", floor=0.0), hinge, size=1,
                       location=(0, L * 0.8, 0.0012))
        tip.scale = (0.0044, L * 0.4, 0.001)
    # A warm pool of light over the comb, following the loudest ringing tooth ("glow", keyed by sr_anim.comb).
    prop(root, "glow", 0.0)
    ld = bpy.data.lights.new(f"{name}.glow", "POINT")
    ld.color, ld.shadow_soft_size, ld.energy = col("amber")[:3], 0.02, 0.0
    ld.specular_factor = 0.0  # its hot spot in the brass deck read as a blown-out bulb (set I close-up)
    lo = link(bpy.data.objects.new(f"{name}.glow", ld))
    lo.parent, lo.location = root, (0, -0.02, 0.13)
    drive(ld, "energy", None, root, "glow", f"{1.4 * scale * scale:.3f} * x")  # 8 W at scale 2.4 (6x blew out)
    comb_base = mesh_obj(f"{name}.combbase", bpy.ops.mesh.primitive_cube_add, mat_chrome(f"{name}.comb"), root, size=1,
                         location=(0, -0.055, 0.082))
    comb_base.scale = (0.115, 0.018, 0.008)
    for k, (x, y) in enumerate(((-0.07, 0.018), (0.07, 0.018))):
        mesh_obj(f"{name}.bearing{k}", bpy.ops.mesh.primitive_cube_add, mat_metal(f"{name}.bear", "copper", 0.15), root,
                 size=0.012, location=(x, y, 0.09))
    crank = mesh_obj(f"{name}.crank", bpy.ops.mesh.primitive_cylinder_add, mat_metal(f"{name}.crank", "copper", 0.15),
                     root, radius=0.003, depth=0.04, location=(0.1, 0.018, 0.098), rotation=(0, math.pi / 2, 0))
    knob = mesh_obj(f"{name}.knob", bpy.ops.mesh.primitive_uv_sphere_add, mat_plastic(f"{name}.knob", "amber", 0.1),
                    root, radius=0.006, location=(0.12, 0.018, 0.115))
    return root


def locked_box(name, loc, rot_z=0.0, mat_case=None, mat_band=None, parent=None):
    """A small closed music box with a brass band and a clasp that has no keyhole (the wall of 198)."""
    root = empty(name, loc, parent)
    root.rotation_euler = (0, 0, rot_z)
    c = mesh_obj(f"{name}.case", bpy.ops.mesh.primitive_cube_add, mat_case, root, size=1, location=(0, 0, 0.032))
    c.scale = (0.1, 0.07, 0.064)
    bevel(c, 0.004, 2)
    lid = mesh_obj(f"{name}.lid", bpy.ops.mesh.primitive_cube_add, mat_case, root, size=1, location=(0, 0, 0.068))
    lid.scale = (0.104, 0.074, 0.01)
    bevel(lid, 0.003, 2)
    band = mesh_obj(f"{name}.band", bpy.ops.mesh.primitive_cube_add, mat_band, root, size=1, location=(0, -0.0352, 0.045))
    band.scale = (0.104, 0.002, 0.008)
    clasp = mesh_obj(f"{name}.clasp", bpy.ops.mesh.primitive_cube_add, mat_band, root, size=1, location=(0, -0.037, 0.05))
    clasp.scale = (0.016, 0.004, 0.022)
    bevel(clasp, 0.002, 2)
    return root


def security_camera(name, loc, parent=None, body_role="lab", scale=1.0):
    """A CCTV camera: a ceiling plate with screws and a mount arm down from `loc` to a pan head (`{name}.yaw`, turns
    about Z) and a tilt joint (`{name}.tilt`, turns about X), carrying a rounded box housing with a darker rear cap,
    a sun hood with side skirts, a lens barrel ending in a chrome ring round a dark lens, a red tally light, and a
    cable looping from the housing's back into the arm (C5 placeholder pass: the housing was a stretched cube). The
    lens looks along the tilt joint's local -Y. Returns (root, yaw, tilt)."""
    s = scale

    def block(nm, mat, par, at, dims, bev, segs=4):
        o = mesh_obj(f"{name}.{nm}", bpy.ops.mesh.primitive_cube_add, mat, par, size=1, location=at)
        o.data.transform(Matrix.Diagonal((*dims, 1.0)))  # sized in the mesh, so the bevel stays round
        bevel(o, bev, segs)
        return smooth(o)

    root = empty(name, loc, parent)
    plastic = mat_plastic(f"{name}.housing", body_role, 0.3)
    dark = mat_plastic(f"{name}.dark", "lab_dark", 0.4)
    chrome = mat_chrome(f"{name}.chrome")
    plate = mesh_obj(f"{name}.plate", bpy.ops.mesh.primitive_cylinder_add, dark, root, radius=0.055 * s,
                     depth=0.012 * s, vertices=32, location=(0, 0, -0.006 * s))
    bevel(plate, 0.003 * s, 2)
    smooth(plate)
    for k in range(3):
        a = k * math.tau / 3 + 0.5
        smooth(mesh_obj(f"{name}.screw{k}", bpy.ops.mesh.primitive_cylinder_add, chrome, root, radius=0.007 * s,
                        depth=0.004 * s, vertices=16, location=(math.cos(a) * 0.04 * s, math.sin(a) * 0.04 * s,
                                                                 -0.013 * s)))
    arm = mesh_obj(f"{name}.arm", bpy.ops.mesh.primitive_cylinder_add, chrome, root, radius=0.018 * s,
                   depth=0.16 * s, vertices=24, location=(0, 0, -0.08 * s))
    smooth(arm)
    yaw = empty(f"{name}.yaw", (0, 0, -0.17 * s), root)
    smooth(mesh_obj(f"{name}.knuckle", bpy.ops.mesh.primitive_uv_sphere_add, chrome, yaw, radius=0.03 * s,
                    segments=24, ring_count=12))
    tilt = empty(f"{name}.tilt", (0, 0, -0.03 * s), yaw)
    block("body", plastic, tilt, (0, -0.1 * s, -0.04 * s), (0.12 * s, 0.28 * s, 0.11 * s), 0.025 * s)
    block("cap", dark, tilt, (0, 0.045 * s, -0.04 * s), (0.124 * s, 0.025 * s, 0.114 * s), 0.02 * s)
    for k in range(3):  # cooling grooves along each side
        for sx in (-1, 1):
            block(f"groove{k}{sx}", dark, tilt, (sx * 0.061 * s, -0.1 * s, -0.065 * s + k * 0.022 * s),
                  (0.004 * s, 0.18 * s, 0.006 * s), 0.0015 * s, 2)
    block("hood", plastic, tilt, (0, -0.14 * s, 0.026 * s), (0.16 * s, 0.38 * s, 0.012 * s), 0.005 * s)
    for sx in (-1, 1):  # the hood's side skirts
        block(f"skirt{sx}", plastic, tilt, (sx * 0.074 * s, -0.24 * s, 0.002 * s), (0.008 * s, 0.17 * s, 0.045 * s),
              0.003 * s, 2)
    barrel = mesh_obj(f"{name}.barrel", bpy.ops.mesh.primitive_cylinder_add, dark, tilt, radius=0.045 * s,
                      depth=0.04 * s, vertices=48, location=(0, -0.255 * s, -0.04 * s), rotation=(math.pi / 2, 0, 0))
    bevel(barrel, 0.004 * s, 2)
    smooth(barrel)
    ring = mesh_obj(f"{name}.ring", bpy.ops.mesh.primitive_torus_add, chrome, tilt, major_radius=0.043 * s,
                    minor_radius=0.007 * s, major_segments=48, minor_segments=12, location=(0, -0.276 * s, -0.04 * s),
                    rotation=(math.pi / 2, 0, 0))
    smooth(ring)
    lens = mesh_obj(f"{name}.lens", bpy.ops.mesh.primitive_uv_sphere_add, mat_plastic(f"{name}.lens", "lens", 0.02),
                    tilt, radius=0.036 * s, segments=32, ring_count=16, location=(0, -0.272 * s, -0.04 * s))
    lens.scale = (1, 0.4, 1)
    smooth(lens)
    smooth(mesh_obj(f"{name}.tally", bpy.ops.mesh.primitive_uv_sphere_add, mat_emission(f"{name}.tally", "alarm", 30.0),
                    tilt, radius=0.008 * s, segments=16, ring_count=8, location=(0.04 * s, -0.242 * s, 0.006 * s)))
    cable = bpy.data.curves.new(f"{name}.cable", "CURVE")  # a loop from the housing's back up into the arm
    cable.dimensions, cable.bevel_depth, cable.bevel_resolution = "3D", 0.006 * s, 3
    sp = cable.splines.new("BEZIER")
    sp.bezier_points.add(1)
    for bp, co, h in zip(sp.bezier_points, ((0, 0.06 * s, -0.03 * s), (0, 0.015 * s, 0.03 * s)),
                         ((0, 0.05 * s, 0), (0, 0, -0.05 * s))):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "FREE"
        bp.handle_right = Vector(co) + Vector(h)
        bp.handle_left = Vector(co) - Vector(h)
    co = link(bpy.data.objects.new(f"{name}.cable", cable))
    co.data.materials.append(dark)
    co.parent = tilt
    return root, yaw, tilt


def turnstile(name="grader", loc=(0, 0, 0), rot_z=0.0):
    """The grader: a chrome turnstile post with three arms ("spin" counts clicks: each +1 is a third of a turn, driven
    by sr_anim.stepper), a slot plate
    with a flag-shaped cut-out, and a bell on a bracket. Anything flag-shaped clicks through; it never checks how."""
    root = empty(name, loc)
    root.rotation_euler = (0, 0, rot_z)
    prop(root, "spin", 0.0, lo=0.0, hi=10000.0)
    prop(root, "bell", 0.0, lo=-1.0, hi=1.0)
    post = mesh_obj(f"{name}.post", bpy.ops.mesh.primitive_cylinder_add, mat_chrome(f"{name}.post"), root, radius=0.06,
                    depth=0.9, vertices=48, location=(0, 0, 0.45))
    smooth(post)
    cap = mesh_obj(f"{name}.cap", bpy.ops.mesh.primitive_uv_sphere_add, mat_plastic(f"{name}.cap", "lab"), root,
                   radius=0.075, location=(0, 0, 0.9))
    cap.scale = (1, 1, 0.5)
    smooth(cap)
    hub = empty(f"{name}.hub", (0, 0, 0.72), root)
    drive(hub, "rotation_euler", 2, root, "spin", "2.0944 * x")
    for k in range(3):
        a = k * math.tau / 3
        arm = mesh_obj(f"{name}.arm{k}", bpy.ops.mesh.primitive_cylinder_add, mat_chrome(f"{name}.arm"), hub,
                       radius=0.018, depth=0.42, vertices=24,
                       location=(math.cos(a) * 0.24, math.sin(a) * 0.24, -0.06),
                       rotation=(0, math.pi / 2 + 0.25, a))
        smooth(arm)
        tip = mesh_obj(f"{name}.tip{k}", bpy.ops.mesh.primitive_uv_sphere_add, mat_plastic(f"{name}.tip", "lab_glow", 0.1),
                       hub, radius=0.026, location=(math.cos(a) * 0.45, math.sin(a) * 0.45, -0.115))
        smooth(tip)
    # Slot plate on the post's front with a flag-shaped emissive cut-out (pole + pennant).
    plate = mesh_obj(f"{name}.plate", bpy.ops.mesh.primitive_cube_add, mat_plastic(f"{name}.plate", "lab_dark", 0.2),
                     root, size=1, location=(0, -0.075, 0.55))
    plate.scale = (0.11, 0.012, 0.16)
    bevel(plate, 0.004, 2)
    slot = mat_emission(f"{name}.slot", "lab_glow", 6.0)
    pole = mesh_obj(f"{name}.slot_pole", bpy.ops.mesh.primitive_cube_add, slot, root, size=1, location=(-0.025, -0.082, 0.55))
    pole.scale = (0.008, 0.002, 0.12)
    bpy.ops.mesh.primitive_plane_add(size=1)
    pen = bpy.context.active_object
    pen.name = f"{name}.slot_flag"
    me = pen.data
    me.vertices[0].co, me.vertices[1].co, me.vertices[2].co, me.vertices[3].co = \
        (0, 0, 0), (0.06, 0, -0.022), (0, 0, -0.045), (0, 0, -0.045)
    pen.parent = root
    pen.location = (-0.021, -0.0825, 0.605)
    pen.data.materials.append(slot)
    # Bell on a bracket; "bell" is its swing.
    arm = mesh_obj(f"{name}.bracket", bpy.ops.mesh.primitive_cylinder_add, mat_chrome(f"{name}.bracket"), root,
                   radius=0.008, depth=0.22, location=(0.11, 0, 0.86), rotation=(0, math.pi / 2, 0))
    hinge = empty(f"{name}.bell_hinge", (0.2, 0, 0.86), root)
    drive(hinge, "rotation_euler", 1, root, "bell", "0.5 * x")
    bell = mesh_obj(f"{name}.bell", bpy.ops.mesh.primitive_cone_add, mat_metal(f"{name}.bell", "brass", 0.1), hinge,
                    radius1=0.06, radius2=0.025, depth=0.08, vertices=48, location=(0, 0, -0.05))
    smooth(bell)
    return root


def decal(name, body, loc, rot, size, peel=0.0, parent=None):
    """A vinyl decal: white film with letters, one corner peeling ("peel" 0–1). The film is a subdivided plane whose
    top-right corner curls away from the glass along a quarter-cylinder; the letters ride the film."""
    root = empty(name, loc, parent)
    root.rotation_euler = rot
    w, h = size
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=10, size=1)
    film = bpy.context.active_object
    film.name = f"{name}.film"
    film.scale = (w, h, 1)
    bpy.ops.object.transform_apply(scale=True)
    film.parent = root
    # Opaque film and heavy letters: it has to read in a wide shot (a translucent film with regular-weight red
    # letters didn't; human, C1 v2).
    film.data.materials.append(mat_matte(f"{name}.film", "decal_film"))  # off-white and matte, so it doesn't bloom or glare
    t = text(f"{name}.text", body, h * 0.7, mat_ink(f"{name}.ink", "decal_ink"), loc=(0, 0, 0.0008), rot=(0, 0, 0),
             font="Inter-Medium-flat.ttf", parent=root)
    t.data.space_character = 1.05
    t.data.offset = h * 0.008  # embolden a little (Inter loads at its default weight); more fills the A's crossbar
    # Curl the top-right corner: a fold line cuts the corner diagonally; film beyond it rolls up off the glass
    # (+Z, toward the viewer) around a cylinder of radius R, then continues straight along the tangent. The letters
    # stay flat: the peel is confined to the corner, past the last letter.
    n = Vector((w, h * 1.6, 0)).normalized()          # in-plane direction across the fold, toward the corner
    corner = Vector((w / 2, h / 2, 0))
    d0 = corner.dot(n) - (0.12 + 0.25 * peel) * h * 1.9  # fold line sits this far in from the corner
    R = 0.06 * h
    theta = peel * 2.4                                  # radians of roll at full peel
    for v in film.data.vertices:
        p = Vector((v.co.x, v.co.y, 0))
        d = p.dot(n) - d0
        if d <= 0 or peel <= 0:
            continue
        base = p - n * d
        arc = R * theta
        if d <= arc:
            phi = d / R
            along, up = R * math.sin(phi), R * (1 - math.cos(phi))
        else:
            along = R * math.sin(theta) + (d - arc) * math.cos(theta)
            up = R * (1 - math.cos(theta)) + (d - arc) * math.sin(theta)
        q = base + n * along
        v.co = (q.x, q.y, up)
    return root


def floor_ring(name="floor_ring", radius=1.8, width=0.03, loc=(0, 0, 0.001)):
    """The bass ring (brief, motion rules): a thin emissive ring on the floor. "pulse" (0–1) is driven by bass notes."""
    root = empty(name, loc)
    prop(root, "pulse", 0.15)
    mesh_obj(f"{name}.ring", bpy.ops.mesh.primitive_torus_add,
             mat_emission(f"{name}.ring", "lab_glow", LOOK["floor_ring"], root, "pulse"), root,
             major_radius=radius, minor_radius=width, major_segments=128, minor_segments=8)
    bpy.context.active_object.scale = (1, 1, 0.1)
    return root


def mallet_pad(name, loc=(0, 0, 0), rot_z=0.0, pad_role="lab", pad_r=0.12, arm_len=0.34, glow_role="amber"):
    """A struck pad with its mallet: the big, readable strike (human, step 7: motion "not obvious enough").
    "strike" (sr_anim.striker): 0 rest, arm raised 40 deg; -1 wound up to 70 deg; 1 contact (arm level on the pad).
    "flash" (sr_anim.hit_flash): the pad's rim lights and the pad squashes 25% on contact."""
    root = empty(name, loc)
    root.rotation_euler = (0, 0, rot_z)
    prop(root, "strike", 0.0, lo=-1.0, hi=1.0)
    prop(root, "flash", 0.0)
    stand = mesh_obj(f"{name}.stand", bpy.ops.mesh.primitive_cylinder_add, mat_chrome(f"{name}.stand"), root,
                     radius=0.012, depth=0.18, location=(0, 0, 0.09))
    pad_root = empty(f"{name}.pad_root", (0, 0, 0.18), root)
    drive(pad_root, "scale", 2, root, "flash", "1 - 0.25 * x")
    pad = mesh_obj(f"{name}.pad", bpy.ops.mesh.primitive_cylinder_add, mat_plastic(f"{name}.pad", pad_role, 0.1),
                   pad_root, radius=pad_r, depth=0.035, vertices=64, location=(0, 0, 0.0175))
    bevel(pad, 0.006)
    rim = mesh_obj(f"{name}.rim", bpy.ops.mesh.primitive_torus_add,
                   mat_emission(f"{name}.rim", glow_role, 60.0, root, "flash"), pad_root,
                   major_radius=pad_r, minor_radius=0.01, location=(0, 0, 0.036))
    # The pad's face glows too on the hit (a dark pad, so the flash is the contrast).
    face = mesh_obj(f"{name}.face", bpy.ops.mesh.primitive_circle_add,
                    mat_emission(f"{name}.face", glow_role, 8.0, root, "flash"), pad_root, radius=pad_r * 0.85,
                    vertices=48, fill_type="NGON", location=(0, 0, 0.0362))
    # Mallet: a pivot behind the pad, an arm reaching over its centre, a ball head.
    pivot = empty(f"{name}.pivot", (0, arm_len, 0.18 + 0.075), root)
    drive(pivot, "rotation_euler", 0, root, "strike", "-(0.698 - 0.698 * max(x, 0) - 0.524 * min(x, 0))")  # +X lowers an arm along -Y
    post = mesh_obj(f"{name}.post", bpy.ops.mesh.primitive_cylinder_add, mat_chrome(f"{name}.post"), root,
                    radius=0.01, depth=0.255, location=(0, arm_len, 0.1275))
    arm = mesh_obj(f"{name}.arm", bpy.ops.mesh.primitive_cylinder_add, mat_chrome(f"{name}.arm"), pivot,
                   radius=0.008, depth=arm_len, location=(0, -arm_len / 2, 0), rotation=(math.pi / 2, 0, 0))
    head = mesh_obj(f"{name}.head", bpy.ops.mesh.primitive_uv_sphere_add, mat_plastic(f"{name}.head", "brass", 0.15),
                    pivot, radius=0.035, location=(0, -arm_len, -0.02))
    smooth(head)
    return root


def pellet_mesh(name, mat, r=0.015, stretch=2.6):
    """A glowing pellet with a stretched tail, oriented along its path by Follow Path (curve follow)."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=16, ring_count=8)
    o = bpy.context.active_object
    o.name = name
    o.scale = (stretch, 1, 1)
    o.data.materials.append(mat)
    return o


def camera_move(name, keys, fps=None):
    """A camera flying through `keys` = [(time s, eye xyz, target xyz, lens mm), ...], tracking a target empty,
    eased in and out (Bezier keys, auto-clamped handles): Animusic's long smooth moves (style spec, camera).
    Returns the camera object; it becomes the scene camera."""
    import bpy
    fps = fps or LOOK["fps"]
    tgt = empty(f"{name}.target")
    cd = bpy.data.cameras.new(name)
    cd.sensor_fit = "HORIZONTAL"  # the horizontal field holds at any frame shape: a square render for the
    # vertical cut (S30-S65) has the 16:9 framing as its centre band
    cd.clip_start, cd.clip_end = 0.01, 800
    cam = link(bpy.data.objects.new(name, cd))
    c = cam.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
    for t, eye, target, lens in keys:
        f = round(t * fps)
        cam.location, tgt.location, cd.lens = eye, target, lens
        cam.keyframe_insert("location", frame=f)
        tgt.keyframe_insert("location", frame=f)
        cd.keyframe_insert("lens", frame=f)
    bpy.context.scene.camera = cam
    return cam
