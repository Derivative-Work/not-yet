"""Everything that moves in the set, keyed from the timing map and the note events (C4). Nothing is keyed by hand:
re-running after a timing fix rewrites every key. Times are song seconds; frames come from sr_anim.frame().

What drives what (brief, "Running devices", shot list and texture pass; config/instrument_map.json):
  music box     comb: every music-box note (sr_anim.comb); drum turns steadily; coin drops in at N36
  stars         born on the music box's melody (top line), a planned number per section (human, C3), none on a key
                word; two dim at N08, one at N20 (the fix from the basement), a few more later; frozen at the pen
                scratch (the reveal material's clock is clamped there)
  call graph    N05: its edges are born on melody notes across L03
  rocking chair rocks on every bar (forward on the downbeat, back mid-bar), stops dead at the pen scratch
  mobile        a small step on each downbeat; pieces lower on their nouns (N12: bank, browser, cloud; the flag on
                "week"), rise again (N13) with ticket stacks; stops at the pen scratch
  blanket       breathes (crib); the chair's blanket slips each chorus and falls at the pen scratch
  door          opens a crack as the camera arrives (N11)
  sticky note   peels a corner at N07, further at N21, falls early in N35 (once the camera is back from the shop)
  frost         thins over the song; gone by N37
  night-light   clicks on at N04 (before "twenty-seven-year", never on it)
  moon          the moonlight clock: the back window's patch creeps from the window's base (N02) to the crib (N38)
  growth chart  marks appear by N05, more by N22, the last near the top by N37
  hall window   whole until the cut to it (N10), where it is taped over an old crack; the new hairline crack grows on
                "never", on the front window and the back one, and stays
  ticket        falls from the mobile through the floor to the basement desk (N14); from then on tickets flutter down
                in gusts onto the drift against the glass, a small drift by N29, a snowbank by N37; some slide
                down it when the next gust lands
  basement      lamp on; the maintainer breathes; a few sheets glow (N17); the flap clatters on each beat of N18
                and folded tickets push through the slot on every other beat, dropping to the desk;
                the floor gaps glow from N20
  neighbor      flickers once at N20; lights on "light" (N23); the glow walks the sill (N24)
  town          the crack runs down the road (N25); porch lights, house windows and streetlights go out house by
                house, lamp by lamp, most return (N26); the far
                hills' windows light amber (N27)
  moat          appears at N22: the floor over its channel dissolves on "moat"
  velvet rope   in front of the door from N29
  shop          tag COMING SOON until N36, then AVAILABLE; the screen lights for the real pages (N33, N34)
  probe         under the quilt's two folds until N38, when its arms push them open; its glint widens as the iris
                opens; the crib's glint goes out as it does
"""
import json
import math
import random

import bpy
import numpy as np

import sr_anim as A
import sr_kit as K

TM = A.timing_map()
FPS = A.FPS
SHOT = {s["id"]: s["t"] for s in TM["shots"] if s["t"] is not None}
LINES = {ln["id"]: ln for ln in TM["lines"]}
OUT = TM["outro"]
FREEZE = OUT["freeze"]
DUR = TM["duration_s"]
KEY_WORDS = ("twenty-seven-year", "class.", "mittens", "contract")  # texture pass: nothing moves on these


def word(line_id, text):
    """Start time of the first word in a line that starts with `text`."""
    return next(w["start"] for w in LINES[line_id]["words"] if w["w"].lower().startswith(text.lower()))


def key_words():
    return [(w["start"] - 0.25, w["end"] + 0.25) for ln in TM["lines"] for w in ln["words"]
            if w["w"].lower().strip(",.;:?…") in [k.strip(".") for k in KEY_WORDS]]


def on_key_word(t, spans):
    return any(a <= t <= b for a, b in spans)


def keys(owner, prop, pts, interp="BEZIER"):
    """pts: [(t s, value[, interp])] -> keys on owner[prop]."""
    return A.write_keys(owner, A.prop_path(prop), [(A.frame(t), v, *rest) for t, v, *rest in pts], interp=interp)


def path_keys(owner, path, pts, index=0, interp="BEZIER"):
    return A.write_keys(owner, path, [(A.frame(t), v, *rest) for t, v, *rest in pts], index=index, interp=interp)


def visible(obj, t_on=None, t_off=None, recursive=True):
    """Key hide_render (and hide_viewport): hidden before t_on, shown until t_off."""
    objs = [obj] + (list(obj.children_recursive) if recursive else [])
    for o in objs:
        pts = [(0.0, 1.0 if t_on is not None and t_on > 0 else 0.0, "CONSTANT")]
        if t_on is not None and t_on > 0:
            pts.append((t_on, 0.0, "CONSTANT"))
        if t_off is not None:
            pts.append((t_off, 1.0, "CONSTANT"))
        path_keys(o, "hide_render", pts, interp="CONSTANT")


def melody():
    return A.top_line(A.events("music_box"))


# ---------------------------------------------------------------- the devices

def music_box(S):
    box = S["dresser_musicbox"]
    evs = A.events("music_box")
    lo, hi = min(e["pitch"] for e in evs), max(e["pitch"] for e in evs)
    A.comb(box, evs, lo=lo, hi=hi)
    # The kit declares "drum" as 0..1 (one turn), and Blender clamps an animated property to its range: the drum
    # turned once in the first 6 s and then stood still (human, C4 v9 review: "doesn't appear to be rotating").
    box.id_properties_ui("drum").update(max=DUR / 6.0 + 1.0)
    keys(box, "drum", [(0.0, 0.0, "LINEAR"), (DUR, DUR / 6.0, "LINEAR")])  # one turn every 6 s
    # A pin on the drum for every note, meeting its tooth as it plays (the tooth as A.comb picks it).
    import nursery
    nursery.drum_pins(box, [(int(min(max(round((e["pitch"] - lo) / (hi - lo) * 17), 0), 17)), e["t"]) for e in evs],
                      6.0, A.FPS)
    slot = bpy.data.objects["dresser.coinslot"]
    t = SHOT["N36"] + 1.6  # the camera settles on the slot at N36 + 1.2
    visible(slot, SHOT["N35"])
    keys(slot, "coin", [(0.0, 0.0, "CONSTANT"), (t, 0.0), (t + 0.45, 1.0)])


STAR_PLAN = [  # (section start shot, until shot, cumulative stars by its end)
    ("N04", "N07", 24), ("N07", "N11", 80), ("N11", "N19", 130), ("N19", "N23", 200), ("N23", "N31", 230),
    ("N31", "N35", 250), ("N35", "N38", 320),
]


def stars(S):
    obj = S["stars"]
    n = int(obj["placed"])
    per = list(obj["per"])
    mel = [e["t"] for e in melody()]
    spans = key_words()
    births, done = [], 0
    first_ok = word("L02", "ghosts")  # after "twenty-seven-year"
    for a, b, total in STAR_PLAN:
        t0, t1 = max(SHOT[a], first_ok if a == "N04" else 0), SHOT[b]
        cand = [t for t in mel if t0 <= t < t1 and not on_key_word(t, spans)]
        want = min(total, n) - done
        if want <= 0 or not cand:
            continue
        pick = [cand[int(i * len(cand) / want)] for i in range(min(want, len(cand)))]
        births += pick
        done += len(pick)
    births += [1e6] * (n - len(births))
    # Dims: two at N08, one at N20 (the basement's fix), and one per later chorus: only a few ever dim.
    dims = [1e6] * n
    for k, t in ((3, SHOT["N08"] + 1.2), (9, SHOT["N08"] + 2.6), (40, SHOT["N20"] + 1.5), (101, SHOT["N35"] + 2.0)):
        if k < n:
            dims[k] = t
    import nursery
    nursery.set_times(obj, births, dims, per=per)
    return births


def call_graph(S):
    obj, n = S["call_graph"], S["call_graph_n"]
    mel = [e["t"] for e in melody() if LINES["L03"]["start"] <= e["t"] <= LINES["L03"]["end"] + 1.0]
    births = [mel[int(i * len(mel) / n)] if mel else LINES["L03"]["start"] for i in range(n)]
    import nursery
    nursery.set_times(obj, births, per=list(obj["per"]))


def chair(S):
    ch = S["chair"]
    bars = [b["start"] for b in TM["bars"] if b["start"] < FREEZE]
    pts = [(0.0, 0.0)]
    for i, t in enumerate(bars):
        nxt = bars[i + 1] if i + 1 < len(bars) else t + 1.2
        pts += [(t, 1.0), ((t + nxt) / 2, -0.8)]
    pts += [(FREEZE, pts[-1][1] * 0.3), (FREEZE + 0.12, 0.0, "CONSTANT")]  # stops dead on the pen scratch
    keys(ch, "rock", [p for p in pts if p[0] <= FREEZE + 0.12])
    choruses = [SHOT[x] for x in ("N07", "N19", "N35")]
    keys(ch, "blanket_slip", [(0.0, 0.2)] + [(t, 0.2 + 0.25 * (k + 1)) for k, t in enumerate(choruses)]
         + [(FREEZE, 0.95), (FREEZE + 0.5, 3.5)])  # falls when the chair stops


def mobile(S):
    mb = S["mobile"]
    down = [b["start"] for b in TM["bars"] if b["start"] < FREEZE]
    A.stepper(mb, "turn", [{"t": t} for t in down], pre=6, settle=10, overshoot=0.08)
    # stepper counts +1 per downbeat; scale it to a small step per bar through a driver on the hub instead of the
    # raw count: the hub turns 6.2832 * turn, so convert: 1/24 of a turn per bar.
    hub = bpy.data.objects["mobile.hub"]
    hub.driver_remove("rotation_euler", 2)
    K.drive(hub, "rotation_euler", 2, mb, "turn", "6.2832 * x / 24")
    nouns = {"bank": word("L10", "bank"), "globe": word("L10", "browser"), "cloud": word("L10", "cloud"),
             "flag": word("L10", "week")}
    rise = word("L11", "tiptoe")
    for piece, t in nouns.items():
        keys(mb, f"lower_{piece}", [(0.0, 0.0), (t - 0.3, 0.0), (t + 0.5, 1.0), (rise - 0.2, 1.0), (rise + 1.2, 0.0)])
    for piece in nouns:  # ticket stacks appear in the pieces' hold as they rise (N13)
        stack = bpy.data.objects.get(f"mobile.stack_{piece}")
        if stack:
            visible(stack, rise - 0.2)


def blanket(S):
    cr = S["crib"]["root"]
    pts, t = [], 0.0
    while t < DUR:
        pts += [(t, 0.2), (t + 1.7, 0.9)]
        t += 3.6
    keys(cr, "breath", pts)


def door_and_note(S):
    keys(S["door"], "open", [(0.0, 0.0), (SHOT["N11"] - 3.0, 0.0), (SHOT["N11"] - 0.5, 1.0)])
    note = S["note"]
    t07, t21, t35 = SHOT["N07"] + 0.8, SHOT["N21"] + 0.6, SHOT["N35"] + 1.2  # N35: the camera is back by then
    keys(note, "peel", [(0.0, 0.0), (t07, 0.0), (t07 + 0.8, 0.18), (t21, 0.18), (t21 + 1.0, 0.45), (t35, 0.5),
                        (t35 + 0.4, 0.95)])
    # The fall (N35): the note drops from the glass to the plinth, turning.
    z0 = note.location.z
    path_keys(note, "location", [(0.0, z0, "CONSTANT"), (t35 + 0.3, z0), (t35 + 2.4, 0.02)], index=2)
    path_keys(note, "location", [(0.0, note.location.y, "CONSTANT"), (t35 + 0.3, note.location.y),
                                 (t35 + 2.4, note.location.y - 0.35)], index=1)
    path_keys(note, "rotation_euler", [(0.0, 0.06, "CONSTANT"), (t35 + 0.3, 0.06), (t35 + 2.4, 1.4)], index=1)


def frost_light_moon(S):
    keys(S["root"], "frost", [(0.0, 1.0, "LINEAR"), (SHOT["N03"], 1.0, "LINEAR"), (SHOT["N37"], 0.0, "LINEAR")])
    lamp = bpy.data.objects["projector.lamp"].data
    t = LINES["L02"]["start"] - 0.15
    path_keys(lamp, "energy", [(0.0, 0.0, "CONSTANT"), (t, lamp.energy, "CONSTANT")], interp="CONSTANT")
    moon = S["moon"]
    # The patch moves as the moon's elevation falls: steep at N02 (patch at the window's base), shallow by N38.
    import mathutils
    def rot(elev_deg):
        d = mathutils.Vector((0, -math.cos(math.radians(elev_deg)), -math.sin(math.radians(elev_deg))))
        return d.to_track_quat("-Z", "Y").to_euler()
    for i in range(3):
        path_keys(moon, "rotation_euler", [(0.0, rot(58)[i], "LINEAR"), (SHOT["N38"], rot(16)[i], "LINEAR")], index=i)


def growth_chart(S):
    g = S["growth"]
    n = int(g["marks"])
    marks = [bpy.data.objects[f"growth.mark{k}"] for k in range(n)]
    # The lowest third is there from the start (seen at N05); the middle third appears by N22, the last by N37.
    for k, mk in enumerate(marks):
        if k >= int(n * 0.7):
            visible(mk, SHOT["N37"] - 4.0)
        elif k >= int(n * 0.35):
            visible(mk, SHOT["N22"] - 4.0)


def hall_window(S):
    for c in (S["crack_new"], S["crack_new_back"]):  # the back window keeps the same state (continuity)
        keys(c, "grow", [(0.0, 0.0), (word("L08", "never") - 0.1, 0.0), (word("L08", "never") + 1.4, 1.0)])
    # Whole until the line: the tape and the old crack appear on the cut to the window ("...and" | "windows are
    # never quite mended", N10), so no broken window gives the line away before it (human, C4 v9 review).
    import camera_path
    cut = SHOT[camera_path.CUT[0]] + camera_path.CUT[1]
    for name in ("hallwin", "window"):
        for part in ("tape0", "tape1", "crack_old"):
            visible(bpy.data.objects[f"{name}.{part}"], cut)


def ticket(S):
    fall = S["ticket_fall"]
    t0, t1, t2, t3 = SHOT["N14"] - 0.4, SHOT["N14"] + 2.7, SHOT["N15"] - 0.8, SHOT["N15"] + 0.3
    p = [(t0, (0.45, 1.0, 1.88)), (t1, (0.5, 0.62, 0.42)), (t2, (0.6, 0.9, -1.6)), (t3, (0.76, 1.12, -2.028))]  # flat on the desk, clear of the screen
    for i in range(3):
        path_keys(fall, "location", [(0.0, p[0][1][i], "CONSTANT")] + [(t, xyz[i]) for t, xyz in p], index=i)
    for i, w in enumerate((2 * math.pi / 3, 0.0, 2.2)):  # x ends a whole turn: lying flat
        path_keys(fall, "rotation_euler", [(t0, 0.0), (t3, w * 3)], index=i)
    visible(fall, t0, SHOT["N19"])
    drift(S["ticket_pile"])


def drift(pile):
    """The drift against the glass (brief: "from N14 on, a few tickets keep drifting through the hall. A small drift
    has formed against the base of the glass by N29 and is a snowbank by N37"; human, C4 v7 review: it should fall,
    especially as more arrive). Tickets come in gusts, a fifth of them by N29 and faster after, each fluttering down
    from above the room: it sways and rocks, spins slowly, and lands curled (shape key "air") before it lies down
    on the pile. Most then slide straight into place; about a third touch down on their perch upslope and stay
    there until the next gust lands near them and knocks them down."""
    rnd = random.Random(json.loads((K.ROOT / "config" / "seeds.json").read_text())["main"] + 6)
    tickets = sorted((o for o in pile.children if "rest" in o), key=lambda o: int(o.name[len("ticket.pile"):]))
    n, gusts = len(tickets), int(pile["gusts"])
    t0, t29, t37 = SHOT["N14"] + 4.0, SHOT["N29"], SHOT["N37"] - 1.5
    before = [0] * gusts  # tickets in earlier gusts
    for o in tickets:
        for g in range(o["gust"] + 1, gusts):
            before[g] += 1

    def when(u):  # share of the drift landed -> time: a fifth by N29, then the rest, faster
        return t0 + (t29 - t0) * u / 0.2 if u < 0.2 else t29 + (t37 - t29) * (u - 0.2) / 0.8

    spacing = [when((before[g + 1] if g + 1 < gusts else n) / n) - when(before[g] / n) for g in range(gusts)]
    gust_t = [when(before[g] / n) + rnd.uniform(-0.3, 0.3) * spacing[g] for g in range(gusts)]
    gust_x = {}
    land, last = {}, 0.0
    for o in tickets:  # touch-down times follow the order they were laid in
        g = o["gust"]
        t = max(gust_t[g] + rnd.uniform(0.0, 1.4), last + 0.05)
        land[o.name], last = t, t
        gust_x.setdefault(g, []).append(o["rest"][0])
    gust_x = {g: sum(xs) / len(xs) for g, xs in gust_x.items()}
    for o in tickets:
        g, ta = o["gust"], land[o.name]
        x, y, ang = o["rest"]
        dx, dy, lift = o["perch"]
        # Perched until the next gust that lands within 60 cm, if it comes within 25 s; else it slides right away.
        ts = ta + rnd.uniform(0.05, 0.25)
        if rnd.random() < 0.35 and dy + abs(dx) > 0.03:
            nxt = [h for h in range(g + 1, gusts) if abs(gust_x.get(h, 9) - x) < 0.6 and 1.0 < gust_t[h] - ta < 25.0]
            if nxt:
                ts = max(ts, gust_t[nxt[0]] + 0.5 + rnd.uniform(0.0, 0.3))
        dur = rnd.uniform(4.5, 6.0)  # paper falls at about 0.8 m/s from 4.2 m over the plinth
        z0 = 4.2
        A_, P, ph = rnd.uniform(0.12, 0.25), rnd.uniform(1.2, 2.0), rnd.uniform(0, math.tau)
        rock, spin = rnd.uniform(0.35, 0.7), rnd.uniform(-3.0, 3.0)
        pts = {c: [] for c in ("x", "y", "z", "rx", "ry", "rz")}
        steps = int(dur / 0.2)
        for i in range(steps + 1):
            f = i / steps
            tau = f * dur
            env = 1.0 - (max(0.0, f - 0.7) / 0.3) ** 2 if f > 0.7 else 1.0  # sway dies out in the last 30%
            w = math.tau * tau / P
            t = ta - dur + tau
            pts["x"].append((t, x + dx + A_ * math.sin(w + ph) * env))
            # Away from the glass while it sways, gliding in as it settles.
            pts["y"].append((t, y + dy + (0.05 * math.sin(0.7 * w + ph) - 0.16) * env))
            pts["z"].append((t, lift + (z0 - lift) * (1 - f) + 0.03 * math.sin(2 * w) * env))
            pts["rx"].append((t, rock * math.sin(w + ph + math.pi / 2) * env))
            pts["ry"].append((t, 0.6 * rock * math.sin(0.8 * w + ph) * env))
            pts["rz"].append((t, ang + spin * (1 - min(1.0, f / 0.85)) ** 2))
        slide = ts + rnd.uniform(0.35, 0.7)
        for i, (c, end) in enumerate((("x", x), ("y", y), ("z", 0.0))):
            # then it rests on the perch until ts and slides home
            path_keys(o, "location", [(-1.0, pts[c][0][1], "CONSTANT")] + pts[c] +
                      [(ts, pts[c][-1][1]), (slide, end)], index=i)
        for i, c in enumerate(("rx", "ry", "rz")):
            path_keys(o, "rotation_euler", [(-1.0, pts[c][0][1], "CONSTANT")] + pts[c], index=i)
        path_keys(o.data.shape_keys, 'key_blocks["air"].value', [(0.0, 1.0, "CONSTANT"), (ta - 0.15, 1.0), (ta + 0.25, 0.0)])
        visible(o, ta - dur)


def basement(S):
    m = S["base_maintainer"]
    pts, t = [], 0.0
    while t < DUR:
        pts += [(t, 0.0), (t + 2.0, 1.0)]
        t += 4.2
    keys(m, "breath", pts)
    keys(S["base_glow"], "glow", [(0.0, 0.0), (SHOT["N17"] - 0.3, 0.0), (SHOT["N17"] + 1.0, 1.0)])
    beats = [b for b in TM["beats"] if SHOT["N18"] <= b < LINES["L16"]["end"] + 0.2]
    # Between clatters the flap hangs a little ajar (0.2), so the lit chute shows through it.
    per = [[(A.frame(b) - 2, 0.2, "BEZIER"), (A.frame(b), 1.0, "BEZIER", True), (A.frame(b) + 6, 0.2, "BEZIER")]
           for b in beats]
    A.write_keys(S["base_mailslot"], A.prop_path("flap"), A._merge(per))
    # A folded ticket on every other clatter: it slides down the chute, through the opening as the flap swings
    # (0.25 at the beat), and drops to the desk (the drop's own curve is in the driver; keyed linear in time).
    for k, bt in enumerate(beats[::2][:int(S["base_mailslot_n"])]):
        keys(S["base_mailslot"], f"drop{k}", [(0.0, 0.0, "CONSTANT"), (bt - 0.3, 0.0, "LINEAR"), (bt, 0.25, "LINEAR"),
                                             (bt + 0.65, 1.0, "LINEAR")])
    import nursery
    nursery.set_times(S["floor_gaps"], [SHOT["N20"]] * 4)


def neighbor_and_town(S):
    nb = S["street_neighbor"]
    t20 = SHOT["N20"] + 1.6
    on = word("L21", "light")
    keys(nb, "amber", [(0.0, 0.0, "CONSTANT"), (t20, 0.7, "CONSTANT"), (t20 + 0.12, 0.0, "CONSTANT"),
                       (on - 0.1, 0.0), (on + 0.5, 1.0)], interp="CONSTANT")
    keys(nb, "walk", [(0.0, 0.0), (SHOT["N24"], 0.0), (LINES["L22"]["end"], 1.0)])
    crack = S["town_crack"]
    order = list(crack["order"])
    t0, t1 = word("L23", "found"), LINES["L23"]["end"]
    import nursery
    nursery.set_times(crack, [t0 + (t1 - t0) * min(1.0, max(0.0, o)) for o in order], per=list(crack["per"]))
    lights = S["street_lights"]
    homes = S["street_homes"]
    rnd = random.Random(json.loads((K.ROOT / "config" / "seeds.json").read_text())["main"])
    t_off = word("L24", "killed")
    stay_dark = {1, 6, 11}
    for k in range(len(homes)):
        a = t_off + 0.18 * k
        b = LINES["L24"]["end"] + rnd.uniform(0.3, 2.0)
        pts = [(0.0, 1.0, "CONSTANT"), (a, 0.0, "CONSTANT")]
        if k not in stay_dark:
            pts.append((b, 1.0, "CONSTANT"))
        keys(lights, f"porch{k}", pts, interp="CONSTANT")
    # The streetlights go out down the hill as the houses do; two stay dark.
    lamps = S["street_lamps"]
    for k in range(len(lamps)):
        a = t_off + 0.1 + 0.12 * k
        b = LINES["L24"]["end"] + rnd.uniform(0.2, 1.6)
        pts = [(0.0, 1.0, "CONSTANT"), (a, 0.0, "CONSTANT")]
        if k not in (2, 9):
            pts.append((b, 1.0, "CONSTANT"))
        keys(lights, f"lamp{k}", pts, interp="CONSTANT")
    far = S["street_far"]
    t_will = word("L25", "others")
    for k in range(int(S["street_far_n"])):
        t = t_will + 0.22 * k + rnd.uniform(0, 0.15)
        keys(far, f"amber{k}", [(0.0, 0.0, "CONSTANT"), (t, 1.0, "CONSTANT")], interp="CONSTANT")


def moat_rope_shop(S):
    # The lid of hall floor over the moat's cut dissolves on "moat" (human, C4 v7 review: the moat read as a placeholder).
    t = word("L20", "moat")
    visible(S["moat"], t - 0.3)
    keys(S["moat"], "appear", [(0.0, 0.0, "CONSTANT"), (t - 0.3, 0.0), (t + 1.2, 1.0)])
    visible(S["moat"]["lid"], None, t + 1.3)
    visible(S["rope"], SHOT["N29"] - 2.0)
    visible(S["twin_tag_soon"], None, SHOT["N36"], recursive=False)
    visible(S["twin_tag_available"], SHOT["N36"], recursive=False)
    keys(S["twin_screen_ph"], "page", [(0.0, 0.0, "CONSTANT"), (SHOT["N33"] - 0.5, 0.0), (SHOT["N33"], 1.0),
                                        (SHOT["N35"], 1.0), (SHOT["N35"] + 1.0, 0.0)])


def probe(S):
    """The reveal (N38; human, C4 v2 review: it appeared out of thin air): the probe lies in its nest under the quilt
    all along. Its arms reach out from under the folds and push them open, front and back, then lie forward on the
    blanket; the iris opens (sing) as the glint under the fold goes out."""
    import nursery
    p = S["probe"]["probe"]
    cr = S["crib"]["root"]
    t = SHOT["N38"]
    for arm in ("arm_l", "arm_r"):
        keys(p, arm, [(0.0, 0.0, "CONSTANT"), (t - 0.7, 0.0), (t + 0.4, 1.0), (t + 1.7, nursery.PROBE_ARMS)])
    keys(cr, "open", [(0.0, 0.0, "CONSTANT"), (t - 0.4, 0.0), (t + 1.0, 1.0)])
    keys(p, "led", [(0.0, 0.0, "CONSTANT"), (t - 0.5, 0.3), (t + 1.0, 1.0)])
    keys(p, "sing", [(0.0, 0.0, "CONSTANT"), (t + 0.4, 0.0), (t + 2.0, 0.55)])
    keys(cr, "glint", [(0.0, 0.6, "CONSTANT"), (t - 0.6, 0.7), (t + 0.3, 0.0)])
    # Out, the glint's bead is a black dot, no longer hidden under the fold's lip once the fold falls away.
    visible(bpy.data.objects[f"{cr.name}.glint"], None, t + 0.35)
    # Two thirds of the way over (open about 0.4), the folds turn to cloth, each held at the middle of its lip,
    # which the hinge's turn carries on over (human, C4 v7 review: opened, they kept the mound's shape round the
    # probe; C4 v8 review: held by one point each, not a bar). Any earlier and the arms, still coming out from under
    # them, snagged and balled them up.
    folds = S["crib"]["folds"]
    # The crib and the probe's shell only: not the glint, nor the probe's sound waves, halo, iris and lens, which
    # pulse with the song, nor its arms, whose overlapping parts it caught between; on them the front fold never came
    # to rest (human, C4 v8 review: it flickered as if blown downward). The arms lie on top of it.
    skip = set(folds) | {o for o in cr.children_recursive
                         if any(k in o.name for k in ("glint", ".wave", ".halo", ".iris", ".lens", ".led", ".bezel",
                                                      ".upper", ".fore", ".joint", ".finger"))}
    colliders = [o for o in cr.children_recursive if o.type == "MESH" and o not in skip]
    # They have fallen and settled by N38 + 3.5 s; the simulation stops there and holds its last frame (resting on
    # the breathing blanket, the cloth never quite comes to rest).
    nursery.quilt_cloth(folds, colliders, A.frame(t + 0.15), A.frame(t + 3.5))


def all_(S):
    """Run every device; returns the star births (for the log)."""
    music_box(S)
    births = stars(S)
    call_graph(S)
    chair(S)
    mobile(S)
    blanket(S)
    door_and_note(S)
    frost_light_moon(S)
    growth_chart(S)
    hall_window(S)
    ticket(S)
    basement(S)
    neighbor_and_town(S)
    moat_rope_shop(S)
    probe(S)
    return births
