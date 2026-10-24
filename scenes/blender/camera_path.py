"""The one continuous camera move, N02 to N40 (brief: "N03 to N38 are one continuous camera move with no cuts: the IDs
mark where the move must be at each anchor").

KEYS are poses (eye, target, lens) at times given as a shot ID (its anchor in timing/timing_map.json) plus an optional
offset in seconds. The eye and the target each run on a centripetal Catmull-Rom spline through their keys,
parameterised by time, and are baked once per frame (linear between frames), so the move never stops or eases at a
key: velocity is continuous through every anchor. Lens is interpolated the same way. Speed is reported by
speed_profile() for the log; the brief's "constant speed" can't hold exactly, because the itinerary mixes close
details with crossings of the hall, so the path is drawn to keep speed changes gradual.

Coordinates: metres, world space (the room is centred on the origin; nursery floor z 0.4; basement z -2.8..0; the
shop window at x 11). The camera passes the vault door's 20-degree crack three times (N11, after N27, before N36): in
through the opening right of centre, then past the door's free edge.
"""
import json
import math
from pathlib import Path

from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
TM = json.loads((ROOT / "timing" / "timing_map.json").read_text())
FPS = TM["fps"]
ANCHOR = {s["id"]: s["t"] for s in TM["shots"] if s["t"] is not None}

PROBE = (-0.07, 1.05, 0.93)       # the crib probe's centre (nursery.crib_probe)
NOTE = (1.13, -2.08, 1.66)        # the sticky note on the glass beside the door
MBOX = (1.62, -0.03, 1.33)        # the music box on the dresser
SHOP_CRIB = (11.9, 0.35, 1.15)
SCREEN = (12.28, -1.1, 1.55)
NEIGHBOR = (-1.4, 54.7, 7.9)

# (anchor, offset s, eye, target, lens mm)
KEYS = [
    ("N02", 0.0, (-1.6, -13.2, 1.9), (0.0, 0.0, 1.7), 35),
    ("N03", 0.0, (-1.45, -12.1, 1.88), (0.0, 0.0, 1.7), 35),
    ("N04", 0.0, (-1.05, -10.0, 1.82), (0.2, 0.5, 1.9), 35),     # the night-light clicks on, first stars
    ("N05", 0.0, (-0.6, -7.9, 1.76), (0.2, 0.4, 2.7), 35),       # the call graph on the ceiling
    ("N06", 0.0, (-0.15, -6.0, 1.7), (0.3, 0.0, 1.05), 35),      # a slight tilt toward the floor
    ("N07", 0.0, (1.55, -3.55, 1.64), NOTE, 40),                 # at the door: the sticky note
    ("N08", 0.0, (1.75, -3.2, 1.6), (0.4, 0.6, 1.5), 36),        # through the glass: two stars dim
    ("N09", 0.0, (1.55, -3.15, 1.6), (0.6, 0.6, 1.5), 36),       # the taped hall window in the glass (C5: reflection)
    ("N10", 0.0, (1.2, -3.1, 1.58), (0.3, 0.6, 1.45), 36),       # a new hairline crack beside the tape
    ("N11", -5.0, (0.85, -3.0, 1.55), (0.5, -1.0, 1.55), 34),
    ("N11", 0.5, (0.6, -1.95, 1.55), (0.9, -0.6, 1.6), 32),      # through the opening, right of centre
    ("N11", 2.5, (0.98, -1.3, 1.58), (0.4, 0.5, 1.8), 30),       # past the door's free edge
    ("N12", 0.0, (0.95, -0.45, 1.5), (0.15, 1.05, 2.0), 30),     # the mobile's pieces lower to peer in
    ("N13", 0.0, (0.75, 0.05, 1.55), (0.2, 1.05, 1.95), 30),     # they rise with tickets
    ("N14", 0.0, (0.65, 0.2, 1.45), (0.45, 0.95, 1.55), 32),     # follow one ticket down
    ("N14", 2.7, (0.6, 0.3, 0.9), (0.5, 0.65, 0.42), 30),
    ("N15", 0.0, (-0.7, -0.6, -1.55), (0.4, 1.3, -2.05), 28),    # the basement: lamp, peanuts, donation jar
    ("N16", 0.0, (0.05, -0.75, -1.8), (0.45, 0.9, -2.05), 30),   # the maintainer from behind
    ("N17", 0.0, (0.95, 0.15, -1.75), (0.2, 1.45, -2.1), 32),    # a few sheets glow cream
    ("N18", 0.0, (0.95, 0.2, -1.9), (0.25, 1.5, -0.95), 26),     # the mail slot in the ceiling, the desk below
    ("N18", 3.4, (0.8, 0.3, -1.4), (0.3, 1.3, -0.5), 30),
    ("N19", 0.0, (0.5, -0.3, 1.25), (0.2, 0.8, 1.05), 30),       # back up into the nursery
    ("N20", 0.0, (-0.25, -0.35, 1.3), (-0.7, -1.25, 0.42), 30),  # lamp light through the floor gaps
    ("N21", 0.0, (0.6, -1.25, 1.62), NOTE, 34),                  # the note from inside, peeling further
    ("N22", 2.0, (1.2, -1.55, 1.75), (3.4, -3.8, 0.0), 30),      # a glimpse outside: the moat (it appears on "moat")
    ("N23", 0.0, (0.6, -0.6, 1.7), (-1.0, 12.0, 3.4), 32),       # turn toward the back window
    ("N24", 0.0, (0.35, -0.2, 1.72), NEIGHBOR, 45),              # the amber light moves along the sill
    ("N25", 0.0, (0.25, 0.1, 1.74), (-1.5, 45.0, 4.5), 50),      # the crack down the road
    ("N26", 0.0, (0.15, 0.35, 1.75), (-1.0, 42.0, 5.5), 42),     # porch lights go out
    ("N27", 0.0, (0.35, -1.2, 1.75), (-1.0, 70.0, 10.0), 32),    # pull back: amber windows on the far hills
    ("N27", 2.4, (0.62, -2.0, 1.5), (0.9, -4.0, 0.6), 32),       # out through the crack
    ("N28", 0.0, (0.95, -4.0, 0.75), (0.3, -2.82, 0.05), 35),    # the tungsten slit under the plinth
    ("N29", 0.0, (-0.3, -6.1, 2.75), (0.0, 0.0, 2.0), 28),       # wide: the glass room in the hall
    ("N30", 0.0, (0.5, -4.8, 1.45), (0.0, -2.2, 1.3), 35),       # two locks: the dial and the velvet rope
    ("N31", 0.0, (4.6, -2.7, 1.5), SHOP_CRIB, 34),               # across the hall to the shop window
    ("N32", 0.0, (10.25, 0.05, 1.45), (11.6, 0.35, 1.18), 50),   # mittens, the waiver
    ("N33", 0.0, (9.2, -0.55, 1.58), SCREEN, 45),                # the real model page
    ("N34", 0.0, (9.45, -0.75, 1.57), SCREEN, 50),               # the audits
    ("N35", 0.0, (2.9, -3.15, 1.62), NOTE, 40),                  # the note falls
    ("N35", 3.3, (0.6, -2.3, 1.52), (0.9, -0.8, 1.5), 32),
    ("N35", 4.6, (0.98, -1.4, 1.55), (1.4, 0.0, 1.35), 32),
    ("N36", 0.0, (1.15, -0.55, 1.45), MBOX, 40),                 # the music box's coin slot
    ("N37", 0.0, (0.75, -0.45, 1.65), (-0.4, 1.2, 2.6), 24),     # walls crowded with stars, frost gone
    ("N38", 0.0, (0.2, 0.42, 1.7), PROBE, 45),                   # the push reaches the crib: the reveal
    ("N39", 0.0, (0.14, 0.52, 1.62), PROBE, 50),
    ("N40", 0.0, (0.11, 0.58, 1.56), PROBE, 55),
    ("N40", 2.0, (0.1, 0.6, 1.54), PROBE, 56),
]


def key_times():
    return [ANCHOR[a] + off for a, off, *_ in KEYS]


def catmull(ts, ps, t, alpha=0.5):
    """Centripetal Catmull-Rom through points ps (Vectors) at times ts, evaluated at t (clamped)."""
    n = len(ts)
    if t <= ts[0]:
        return ps[0].copy()
    if t >= ts[-1]:
        return ps[-1].copy()
    i = max(k for k in range(n - 1) if ts[k] <= t)
    p0, p1, p2, p3 = ps[max(0, i - 1)], ps[i], ps[i + 1], ps[min(n - 1, i + 2)]
    u = (t - ts[i]) / (ts[i + 1] - ts[i])
    # Barry-Goldman pyramid on knot spacing |dp|^alpha, mapped onto the time segment by u.
    def tj(ti, a, b):
        return ti + max((b - a).length, 1e-4) ** alpha
    t0 = 0.0
    t1 = tj(t0, p0, p1)
    t2 = tj(t1, p1, p2)
    t3 = tj(t2, p2, p3)
    tt = t1 + u * (t2 - t1)
    def lerp(a, b, ta, tb):
        return a * ((tb - tt) / (tb - ta)) + b * ((tt - ta) / (tb - ta)) if tb != ta else a
    a1, a2, a3 = lerp(p0, p1, t0, t1), lerp(p1, p2, t1, t2), lerp(p2, p3, t2, t3)
    b1, b2 = lerp(a1, a2, t0, t2), lerp(a2, a3, t1, t3)
    return lerp(b1, b2, t1, t2)


def pose(t):
    ts = key_times()
    eye = catmull(ts, [Vector(k[2]) for k in KEYS], t)
    tgt = catmull(ts, [Vector(k[3]) for k in KEYS], t)
    lens = catmull(ts, [Vector((k[4], 0, 0)) for k in KEYS], t).x
    return eye, tgt, lens


def speed_profile(step=0.5):
    """(t, m/s) samples of the eye's speed, and the shot whose anchor precedes each."""
    out = []
    t, end = 0.0, key_times()[-1]
    prev = pose(0.0)[0]
    while t < end:
        t += step
        e = pose(t)[0]
        out.append((round(t, 2), round((e - prev).length / step, 3)))
        prev = e
    return out


def build(K, bpy, f0, f1):
    """Bake the move onto a camera (tracking a target empty) for frames f0..f1. Returns the camera."""
    tgt = K.empty("cam.target")
    cd = bpy.data.cameras.new("cam")
    cd.sensor_fit = "HORIZONTAL"
    cd.clip_start, cd.clip_end = 0.02, 800
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = 5.6
    cd.dof.focus_object = tgt
    cam = K.link(bpy.data.objects.new("cam", cd))
    c = cam.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
    for f in range(f0, f1 + 1):
        eye, t, lens = pose(f / FPS)
        cam.location, tgt.location, cd.lens = eye, t, lens
        cam.keyframe_insert("location", frame=f)
        tgt.keyframe_insert("location", frame=f)
        cd.keyframe_insert("lens", frame=f)
    for ob in (cam, tgt, cd):
        ad = ob.animation_data
        if ad and ad.action:
            for fc in _fcurves(ad):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
    bpy.context.scene.camera = cam
    return cam


def _fcurves(ad):
    act = ad.action
    if hasattr(act, "fcurves") and len(act.fcurves):
        return act.fcurves
    out = []  # Blender 5 layered actions
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                out += list(bag.fcurves)
    return out
