"""The camera move, N02 to N40 (brief: "N03 to N38 are one continuous camera move with no cuts: the IDs mark where the
move must be at each anchor"), with the one cut the human added at C4 review: right before "windows are never quite
mended" (N10) it cuts to the taped, cracked hall window seen from outside, then comes in through the window and pans
slowly around the set to the door, with no second cut (log/human_interventions.md, an EXCEPTION).

KEYS are poses (eye, target, lens) at times given as a shot ID (its anchor in timing/timing_map.json) plus an optional
offset in seconds. The eye and the target each run on a centripetal Catmull-Rom spline through their keys,
parameterised by time, and are baked once per frame (linear between frames), so the move never stops or eases at a
key: velocity is continuous through every anchor. CUT splits KEYS into two splines: the one before it ends on its last
key at the cut, the one after starts on its first; build() keys the jump so it never interpolates across it. Lens is interpolated the same way. Speed is reported by
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
MBOX = (1.64, -0.03, 1.3)         # the music box on the dresser (its mechanism)
SHOP_CRIB = (11.9, 0.35, 1.15)
SCREEN = (12.28, -1.1, 1.55)
NEIGHBOR = (-1.4, 54.7, 7.9)

# (anchor, offset s, eye, target, lens mm)
CUT = ("N10", 0.03)  # 52.00 s: on the beat, after "...and", right before "windows are never quite mended"

KEYS = [
    ("N02", 0.0, (-1.6, -13.2, 1.9), (0.0, 0.0, 1.7), 35),
    ("N03", 0.0, (-1.45, -12.1, 1.88), (0.0, 0.0, 1.7), 35),
    ("N04", 0.0, (-1.05, -10.0, 1.82), (0.2, 0.5, 1.9), 35),     # the night-light clicks on, first stars
    ("N05", 0.0, (-0.6, -7.9, 1.76), (0.2, 0.4, 2.7), 35),       # the call graph on the ceiling
    ("N06", 0.0, (-0.15, -6.0, 1.7), (0.3, 0.0, 1.05), 35),      # a slight tilt toward the floor
    ("N07", 0.0, (1.55, -3.55, 1.64), NOTE, 40),                 # at the door: the sticky note
    ("N08", 0.0, (1.75, -3.2, 1.6), (0.4, 0.6, 1.5), 36),        # through the glass: two stars dim
    ("N09", 0.0, (1.55, -3.15, 1.6), (0.6, 0.6, 1.5), 36),       # the taped hall window in the glass (C5: reflection)
    ("N10", 0.03, (1.4, -3.13, 1.59), (0.5, 0.6, 1.48), 36),     # -- the cut --
    ("N10", 0.03, (-4.0, -19.0, 2.6), (-4.0, -14.1, 2.6), 40),   # outside: the taped pane, the new crack on "never"
    ("N10", 3.5, (-4.1, -17.6, 2.5), (-4.15, -14.1, 2.48), 39),
    ("N10", 4.8, (-4.4, -15.8, 2.18), (-4.5, -11.0, 2.12), 36),
    ("N10", 6.0, (-4.53, -14.03, 2.07), (-4.4, -9.5, 2.0), 35),  # through the lower-left pane
    ("N10", 8.2, (-4.0, -10.6, 2.05), (-1.0, -1.0, 1.8), 32),    # the slow pan around the set
    ("N10", 10.9, (-2.6, -6.6, 1.9), (0.0, 0.0, 1.6), 32),
    ("N10", 12.85, (-0.6, -4.2, 1.7), (0.4, -1.2, 1.55), 34),
    ("N11", 1.0, (0.85, -3.0, 1.55), (0.5, -1.0, 1.55), 34),
    ("N11", 2.6, (0.6, -1.95, 1.55), (0.9, -0.6, 1.6), 32),      # through the opening, right of centre
    ("N11", 3.8, (0.98, -1.3, 1.58), (0.4, 0.5, 1.8), 30),       # past the door's free edge
    ("N12", 0.0, (0.95, -0.45, 1.5), (0.15, 1.05, 2.0), 30),     # the mobile's pieces lower to peer in
    ("N13", 0.0, (0.75, 0.05, 1.55), (0.2, 1.05, 1.95), 30),     # they rise with tickets
    ("N14", 0.0, (0.65, 0.2, 1.45), (0.45, 0.95, 1.55), 32),     # follow one ticket down
    ("N14", 2.7, (0.6, 0.3, 0.9), (0.5, 0.65, 0.42), 30),
    ("N15", 0.0, (-0.7, -0.6, -1.55), (0.4, 1.3, -2.05), 28),    # the basement: lamp, peanuts, donation jar
    ("N16", 0.0, (0.05, -0.75, -1.8), (0.45, 0.9, -2.05), 30),   # the maintainer from behind
    ("N17", 0.0, (0.92, 0.66, -1.6), (0.35, 1.28, -1.93), 36),   # a few sheets glow cream; over the shoulder, the
    ("N17", 3.2, (0.86, 0.78, -1.62), (0.35, 1.28, -1.92), 40),  # laptop's advisory feed (human, C4 v3 review)
    ("N18", 0.0, (0.42, 1.2, -1.15), (0.2, 1.58, -0.1), 30),    # the mail slot in the ceiling, tickets dropping
    ("N18", 3.4, (0.8, 0.3, -1.4), (0.3, 1.3, -0.5), 30),
    ("N19", -2.6, (0.62, 0.0, 0.2), (0.25, 1.0, 1.9), 28),       # through the plinth looking up, at the crib and mobile
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
    ("N32", 0.0, (10.75, 0.05, 1.85), (11.95, 0.16, 1.22), 52),  # over the rail: the mittens, the waiver
    # The screen fills most of the frame and holds to the end of N34's bar (human, C4 review: closer, longer).
    ("N33", 0.0, (10.75, -1.02, 1.55), SCREEN, 42),              # the real model page
    ("N33", 3.0, (10.88, -1.09, 1.55), SCREEN, 45),
    ("N34", 0.0, (10.93, -1.1, 1.55), SCREEN, 46),               # the audits
    ("N34", 5.8, (10.9, -1.13, 1.555), SCREEN, 46),
    ("N35", 0.8, (4.6, -4.6, 1.65), NOTE, 50),                   # the note falls (animate: N35 + 1.2), clear of
    ("N35", 3.6, (2.4, -3.9, 1.62), NOTE, 42),                   # the open door's edge
    ("N35", 5.4, (0.6, -2.3, 1.52), (0.9, -0.8, 1.5), 32),
    ("N35", 6.3, (0.98, -1.4, 1.55), (1.4, 0.0, 1.35), 32),
    # The music box, close and held into N37 (human, C4 v2 review): its comb, drum and lid, the coin slot on its side.
    ("N36", 1.2, (1.1, -0.64, 1.8), MBOX, 40),                   # the coin slot (animate: coin at N36 + 1.6)
    ("N36", 3.5, (1.08, -0.66, 1.78), MBOX, 42),
    ("N37", 1.8, (1.05, -0.68, 1.78), MBOX, 43),
    ("N37", 4.2, (0.75, -0.45, 1.65), (-0.4, 1.2, 2.6), 24),     # walls crowded with stars, frost gone
    # The push reaches the crib, high enough to look down past the rail (human, C4 v2 review): the reveal.
    ("N38", 0.0, (0.2, 0.42, 1.98), PROBE, 45),
    ("N39", 0.0, (0.14, 0.55, 1.92), PROBE, 50),
    ("N40", 0.0, (0.11, 0.62, 1.86), PROBE, 55),
    ("N40", 2.0, (0.1, 0.64, 1.84), PROBE, 56),
]


def key_times():
    return [ANCHOR[a] + off for a, off, *_ in KEYS]


def cut_t():
    return ANCHOR[CUT[0]] + CUT[1]


def _segment(t):
    """(times, keys) of the spline that holds t: before the cut, or from the cut on."""
    ts, tc = key_times(), cut_t()
    i = next(k for k, x in enumerate(ts) if abs(x - tc) < 1e-9 and k + 1 < len(ts) and abs(ts[k + 1] - tc) < 1e-9)
    return (ts[:i + 1], KEYS[:i + 1]) if t < tc else (ts[i + 1:], KEYS[i + 1:])


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
    ts, keys = _segment(t)
    eye = catmull(ts, [Vector(k[2]) for k in keys], t)
    tgt = catmull(ts, [Vector(k[3]) for k in keys], t)
    lens = catmull(ts, [Vector((k[4], 0, 0)) for k in keys], t).x
    return eye, tgt, lens


def speed_profile(step=0.5):
    """(t, m/s) samples of the eye's speed, and the shot whose anchor precedes each."""
    out = []
    t, end = 0.0, key_times()[-1]
    prev = pose(0.0)[0]
    while t < end:
        t += step
        e = pose(t)[0]
        if not (t - step < cut_t() <= t):  # the cut is not a speed
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
    # The cut: the last frame before it holds until half a frame before the cut, where the new shot's first pose is
    # keyed, so nothing (a motion-blur sample included) interpolates across it.
    fcut = math.ceil(cut_t() * FPS - 1e-6)
    if f0 < fcut <= f1:
        eye, t, lens = pose(fcut / FPS)
        cam.location, tgt.location, cd.lens = eye, t, lens
        for ob, path in ((cam, "location"), (tgt, "location"), (cd, "lens")):
            ob.keyframe_insert(path, frame=fcut - 0.5)
    for ob in (cam, tgt, cd):
        ad = ob.animation_data
        if ad and ad.action:
            for fc in _fcurves(ad):
                for kp in fc.keyframe_points:
                    held = f0 < fcut <= f1 and fcut - 1.01 < kp.co.x < fcut - 0.01
                    kp.interpolation = "CONSTANT" if held else "LINEAR"
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
