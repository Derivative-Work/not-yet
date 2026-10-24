"""Note-driven animation library (pre-production step 7): event lists -> keyframes on the kit's rigs.

Clock: frame f shows song time f / FPS (scene frame_start = 0). Every contact lands on the frame nearest its event
(worst-case 8.3 ms at 60 fps). Everything is procedural: re-running a set after a timing fix rewrites its keys, and
nothing is keyed by hand.

Rig types (config/instrument_map.json "rig"); timings from the style spec, part 2, "Making machines play themselves"
(retuned after the human's look at the first test: "not obvious enough ... happening too fast or are not large
enough"; the first values were 6/12/4 frames):
  key_press  - down 4 frames before the onset, held for the note (at least 12 frames), up over 12 frames
  striker    - wind-up from 14 frames before (height by velocity), accelerating into contact on the onset frame,
               held 2 frames, rebound and settle over 28 frames
  bell       - damped swing starting on the onset, decaying over the note (at least 45 frames)
  led_pulse  - full on the onset, exponential decay (tau = 0.4 x note length, at least 12 frames)
  hit_flash  - a light burst on the struck part: full on contact, gone over 18 frames
When notes crowd, wind-ups shrink and settles are cut short so every contact still lands (_merge).
  envelope   - follows a stem envelope (timing/envelopes/*.npy, already smoothed over 3 frames)
  stepper    - a counter: +1 per event, easing in over 6 frames to land on the onset with a 6% overshoot that
               settles over 8 frames (turnstiles, odometers, split-flaps, dials)
  continuous - a value moved linearly between two times
  pellet     - an object riding a curve, launched early so it arrives on the onset; the launch time is solved back from
               the path length at a constant speed, with at least 12 frames of flight

Event loading and filters are plain Python + numpy, usable outside Blender; the rig functions need bpy.
"""
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FPS = json.loads((ROOT / "config" / "look.json").read_text())["fps"]
SOURCES = json.loads((ROOT / "config" / "instrument_map.json").read_text())["sources"]
_TM = None


def timing_map():
    global _TM
    if _TM is None:
        _TM = json.loads((ROOT / "timing" / "timing_map.json").read_text())
    return _TM


def frame(t):
    return int(round(t * FPS))


# ---------------------------------------------------------------- events

def events(key):
    """Events of a source as dicts with at least t (s), end (s), vel (0-127); pitch / piece where the source has them.
    Words come back as events with the word in 'w'; beats with 'beat' (index) and 'down' (downbeat)."""
    src = SOURCES[key]
    if src["kind"] in ("notes", "hits"):
        ev = json.loads((ROOT / src["file"]).read_text())["events"]
        out = []
        for e in ev:
            d = dict(e)
            d.setdefault("end", d["t"] + 0.1)
            d.setdefault("vel", int(127 * d.get("strength", 0.8)))
            out.append(d)
        return sorted(out, key=lambda e: e["t"])
    tm = timing_map()
    if src["kind"] == "words":
        return [{"t": w["start"], "end": w["end"], "vel": 100, "w": w["w"], "line": ln["text"], "role": ln["role"]}
                for ln in tm["lines"] for w in ln["words"]]
    if src["kind"] == "beats":
        down = set(tm["downbeat_beats"])
        b = tm["beats"]
        return [{"t": t, "end": b[i + 1] if i + 1 < len(b) else t + 0.4, "vel": 110 if i in down else 80, "beat": i,
                 "down": i in down} for i, t in enumerate(b)]
    raise ValueError(f"{key} is an envelope; use envelope()")


def envelope(key):
    """Per-frame 0-1 envelope of a stem (scripts/stem_envelopes.py)."""
    stem = Path(SOURCES[key]["stem"]).stem.split("(")[1].rstrip(")")
    return np.load(ROOT / "timing" / "envelopes" / f"{stem.lower().replace(' ', '_')}.npy")


# Filters: small composable predicates, so set builders say exactly what drives what.
def between(evs, t0, t1):
    return [e for e in evs if t0 <= e["t"] < t1]


def pitch_range(evs, lo=0, hi=128):
    return [e for e in evs if lo <= e.get("pitch", 0) < hi]


def pieces(evs, *names):
    return [e for e in evs if e.get("piece") in names]


def top_line(evs, merge=0.03):
    """The highest note of each onset (a melody line out of chords)."""
    out = []
    for e in sorted(evs, key=lambda e: (e["t"], -e.get("pitch", 0))):
        if out and e["t"] - out[-1]["t"] < merge:
            continue
        out.append(e)
    return out


def in_line(evs, text):
    """Events inside the sung line whose text starts with `text` (its first to last word)."""
    ln = next(x for x in timing_map()["lines"] if x["text"].startswith(text))
    return between(evs, ln["start"] - 0.05, ln["end"] + 0.05)


def words_starting(prefix):
    return [e for e in events("words") if e["w"].lower().strip(".,!?…").startswith(prefix.lower())]


def section(name):
    s = next(x for x in timing_map()["sections"] if x["name"] == name)
    return s["start"], s["end"]


def strikes(evs, min_gap=0.03):
    """One event per strike time (chords and simultaneous kit pieces collapse), loudest kept."""
    out = []
    for e in sorted(evs, key=lambda e: e["t"]):
        if out and e["t"] - out[-1]["t"] < min_gap:
            if e["vel"] > out[-1]["vel"]:
                out[-1] = e
            continue
        out.append(e)
    return out


# ---------------------------------------------------------------- keyframe writing

def _fcurve(owner, path, index=0):
    """F-curve on owner's action for data path (custom props as '["name"]'), created if needed (Blender 4.4+/5
    layered actions: Action.fcurve_ensure_for_datablock)."""
    import bpy
    if owner.animation_data is None:
        owner.animation_data_create()
    act = owner.animation_data.action
    if act is None:
        act = bpy.data.actions.new(f"{owner.name}.act")
        owner.animation_data.action = act
    return act.fcurve_ensure_for_datablock(owner, path, index=index)


def write_keys(owner, path, keys, index=0, interp="BEZIER"):
    """Replace the F-curve's keys with `keys`: [(frame, value[, interpolation])], frames ascending. Bulk-set for
    speed (a 323 s piano part is thousands of keys)."""
    fc = _fcurve(owner, path, index)
    fc.keyframe_points.clear()
    keys = sorted(keys, key=lambda k: k[0])
    # Drop exact duplicate frames, keeping the last value written for a frame.
    dedup = {}
    for k in keys:
        dedup[float(k[0])] = k
    keys = [dedup[f] for f in sorted(dedup)]
    fc.keyframe_points.add(len(keys))
    co = np.empty(2 * len(keys), dtype=np.float32)
    co[0::2] = [k[0] for k in keys]
    co[1::2] = [k[1] for k in keys]
    fc.keyframe_points.foreach_set("co", co)
    lookup = {"BEZIER": 0, "LINEAR": 1, "CONSTANT": 2}
    ip = [k[2] if len(k) > 2 else interp for k in keys]
    for kp, i in zip(fc.keyframe_points, ip):
        kp.interpolation = i
        kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
    fc.update()
    return fc


def prop_path(name):
    return f'["{name}"]'


# ---------------------------------------------------------------- rigs (value curves on a custom property)

def key_press(owner, prop, evs, depth=1.0, pre=4, release=12, min_hold=12):
    per = []
    for e in evs:
        f0, f1 = frame(e["t"]), max(frame(e["end"]), frame(e["t"]) + min_hold)
        per.append([(f0 - pre, 0.0), (f0, depth * (0.6 + 0.4 * e["vel"] / 127), "LINEAR", True), (f1, depth * 0.85),
                    (f1 + release, 0.0)])
    return write_keys(owner, prop_path(prop), _merge(per), interp="BEZIER")


def striker(owner, prop, evs, wind=14, settle=28):
    """0 = rest; negative = wound up; 1 = contact. Wind-up height scales with velocity. The fall from the top of the
    wind-up into contact is linear (fast), so the strike reads as a strike; the rebound overshoots, then settles."""
    per = []
    for e in evs:
        f0 = frame(e["t"])
        h = 0.5 + 0.5 * e["vel"] / 127
        per.append([(f0 - wind, 0.0), (f0 - wind // 3, -h, "LINEAR"), (f0, 1.0, "CONSTANT", True), (f0 + 2, 1.0),
                    (f0 + 8, -0.3 * h), (f0 + 16, 0.1 * h), (f0 + settle, 0.0)])
    return write_keys(owner, prop_path(prop), _merge(per))


def bell(owner, prop, evs, min_len=45, cycles_per_s=2.0):
    per = []
    for e in evs:
        f0 = frame(e["t"])
        n = max(min_len, frame(e["end"]) - f0)
        amp = 0.7 + 0.3 * e["vel"] / 127
        ks = [(f0 + k, amp * math.exp(-3 * k / n) * math.sin(2 * math.pi * cycles_per_s * k / FPS), "LINEAR", k == 0)
              for k in range(0, n + 1, 2)]
        per.append(ks + [(f0 + n + 2, 0.0)])
    return write_keys(owner, prop_path(prop), _merge(per), interp="LINEAR")


def led_pulse(owner, prop, evs, floor=0.04, min_tau=12):
    per = []
    for e in evs:
        f0 = frame(e["t"])
        n = max(1, frame(e["end"]) - f0)
        tau = max(min_tau, 0.4 * n)
        peak = 0.75 + 0.25 * e["vel"] / 127
        ks = [(f0 - 1, floor, "LINEAR")]
        ks += [(f0 + k, floor + (peak - floor) * math.exp(-k / tau), "LINEAR", k == 0)
               for k in (0, 1, 2, 4, 8, 12, 16, 24, 32, 48, 64) if k <= 4 * tau]
        per.append(ks + [(f0 + int(4 * tau) + 1, floor, "LINEAR")])
    return write_keys(owner, prop_path(prop), _merge(per), interp="LINEAR")


def hit_flash(owner, prop, evs, length=18):
    per = []
    for e in evs:
        f0 = frame(e["t"])
        per.append([(f0 - 1, 0.0, "LINEAR"), (f0, 1.0, "LINEAR", True), (f0 + 3, 0.7, "LINEAR"),
                    (f0 + length // 2, 0.2, "LINEAR"), (f0 + length, 0.0, "LINEAR")])
    return write_keys(owner, prop_path(prop), _merge(per), interp="LINEAR")


def envelope_rig(owner, prop, env, f0=0, f1=None, step=2, gain=1.0, offset=0.0):
    f1 = len(env) if f1 is None else min(f1, len(env))
    keys = [(f, offset + gain * float(env[f])) for f in range(f0, f1, step)]
    return write_keys(owner, prop_path(prop), keys, interp="LINEAR")


def stepper(owner, prop, evs, pre=10, settle=16, overshoot=0.15, start=0.0):
    per, v = [[(0, start, "CONSTANT")]], start
    for e in evs:
        f0 = frame(e["t"])
        per.append([(f0 - pre, v, "BEZIER"), (f0, v + 1 + overshoot, "BEZIER", True), (f0 + settle, v + 1, "BEZIER")])
        v += 1
    return write_keys(owner, prop_path(prop), _merge(per))


def continuous(owner, prop, t0, t1, v0, v1, interp="LINEAR"):
    return write_keys(owner, prop_path(prop), [(frame(t0), v0), (frame(t1), v1)], interp=interp)


def _merge(per_event, contact_value=None):
    """Concatenate per-event key lists in time order. Each list may mark its contact key (a 4th element True).
    When notes crowd: the previous note's keys after the next note's first key are dropped, but never its contact;
    the next note's keys at or before the previous contact are dropped, but never its own contact. So every contact
    lands, a wind-up shrinks to fit, and a settle is cut short (fast repeated notes stay readable)."""
    out, last_contact = [], -10 ** 9
    for keys in sorted(per_event, key=lambda ks: ks[0][0] if ks else 0):
        if not keys:
            continue
        keys = [k for k in keys if (len(k) > 3 and k[3]) or k[0] > last_contact]
        if not keys:
            continue
        start = keys[0][0]
        while out and out[-1][0] >= start and not (len(out[-1]) > 3 and out[-1][3]):
            out.pop()
        keys = [k for k in keys if not out or k[0] > out[-1][0]]
        out += keys
        for k in keys:
            if len(k) > 3 and k[3]:
                last_contact = k[0]
    return [k[:3] if len(k) > 3 else k for k in out]


# ---------------------------------------------------------------- pellets

def launch_times(evs, path_len, speed, min_flight_frames=30):
    """(launch frame, arrival frame) per event: arrival exactly on the onset frame; the launch is solved back from
    the path length at `speed` (m/s), with at least `min_flight_frames` of flight so every arc is seen."""
    out = []
    for e in evs:
        fa = frame(e["t"])
        flight = max(min_flight_frames, int(math.ceil(path_len / speed * FPS)))
        out.append((fa - flight, fa))
    return out


def pellets(curve_obj, evs, speed, make_pellet, path_len=None, keep_after=6):
    """One pellet per event riding `curve_obj`, arriving on the onset. `make_pellet(i)` returns a new object.
    Uses a Follow Path constraint with keyed offset_factor (0 -> 1); the pellet is hidden before launch and
    `keep_after` frames after arrival (its 'hit' flash belongs to the instrument)."""
    import bpy
    if path_len is None:
        path_len = curve_length(curve_obj)
    objs = []
    for i, (fl, fa) in enumerate(launch_times(evs, path_len, speed)):
        p = make_pellet(i)
        c = p.constraints.new("FOLLOW_PATH")
        c.target = curve_obj
        curve_obj.data.use_path = True  # Follow Path does nothing without it (the pellets sat still until C4 v5)
        c.use_fixed_location = True
        c.use_curve_follow = True
        write_keys(p, f'constraints["{c.name}"].offset_factor', [(fl, 0.0, "LINEAR"), (fa, 1.0, "LINEAR")],
                   interp="LINEAR")
        write_keys(p, "hide_render", [(fl - 1, 1, "CONSTANT"), (fl, 0, "CONSTANT"), (fa + keep_after, 1, "CONSTANT")],
                   interp="CONSTANT")
        objs.append(p)
    return objs


def curve_length(curve_obj):
    """Approximate world-space length of a curve object (sampled from its evaluated mesh)."""
    import bpy
    dg = bpy.context.evaluated_depsgraph_get()
    me = curve_obj.evaluated_get(dg).to_mesh()
    pts = [curve_obj.matrix_world @ v.co for v in me.vertices]
    curve_obj.evaluated_get(dg).to_mesh_clear()
    return sum((pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)) if len(pts) > 1 else 1.0


def sing_curve(t0, t1, roles=("lead",), line_ids=None, attack=6, release=12, accent=0.12, accent_len=10):
    """Per-frame 0-1 "voice": the vocal stem's level inside the singer's lines, lifted by its sung words.
    - Stem: (env - 0.45) / 0.5, clipped, only inside the singer's lines (the stem has every voice). It holds long
      notes, which the aligned words often end early (human, C4 v2: "not holding out for long words").
    - Words (timing map): 0.55-1.0 with the stem's level while sung, and a word's hold continues while the stem stays
      up, until the next word. Without them the compressed stem (0.5-0.93 while singing) barely moves (C4 v1).
    - A fresh word adds a small accent; it opens over `attack` frames and closes over `release` (v2's 3/6 frames and
      0.3 accent read as jerky looking up on each word)."""
    env = envelope("vocal_env")
    n = frame(timing_map()["duration_s"]) + 1
    e = np.zeros(n)
    e[:len(env)] = env[:n]
    stem = np.clip((e - 0.45) / 0.5, 0, 1)
    inline = np.zeros(n, bool)
    target = np.zeros(n)
    acc = np.zeros(n)
    for li in timing_map()["lines"]:
        if (line_ids is None and li["role"] not in roles) or (line_ids is not None and li["id"] not in line_ids):
            continue
        if li["end"] < t0 - 1 or li["start"] > t1 + 1:
            continue
        inline[max(0, frame(li["start"]) - 3):min(n, frame(li["end"]) + 30)] = True
        ws = li["words"]
        for k, w in enumerate(ws):
            a = frame(w["start"])
            b = max(frame(w["end"]), a + 6)
            nxt = frame(ws[k + 1]["start"]) if k + 1 < len(ws) else min(n, b + 120)
            while b < nxt and stem[b] > 0.3:  # held past the aligned word's end
                b += 1
            target[a:b] = np.maximum(target[a:b], 0.55 + 0.45 * stem[a:b])
            kk = np.arange(min(accent_len, n - a))
            acc[a:a + len(kk)] = np.maximum(acc[a:a + len(kk)], accent * (1 - kk / accent_len))
    target = np.maximum(target, stem * inline)
    out = np.zeros(n)
    v = 0.0
    for f in range(n):
        tgt = target[f]
        v += (tgt - v) / (attack if tgt > v else release)
        out[f] = v
    return np.clip(out + acc, 0, 1)


def sing(owner, t0, t1, prop="sing", **kw):
    """Key a probe's "sing" (sr_kit.probe) from sing_curve over [t0, t1] s, and its voice rings: one per sung word."""
    if "wave0" in owner:
        voice_rings(owner, t0, t1, roles=kw.get("roles", ("lead",)), line_ids=kw.get("line_ids"))
    return envelope_rig(owner, prop, sing_curve(t0, t1, **kw), frame(t0 - 1), frame(t1 + 1), step=1)


def voice_rings(owner, t0, t1, roles=("lead",), line_ids=None, life=36):
    """Key a probe's voice rings (sr_kit.probe, "wave<k>"/"wave_a<k>"): on each word the singer starts in [t0, t1] s,
    the next free ring leaves the lens, widening (phase 0 -> 1, eased out) and fading over `life` frames. Brightness
    follows the stem, so a belted word rings brighter. A word that finds every ring still in flight goes without."""
    env = envelope("vocal_env")
    nring = sum(1 for k in owner.keys() if k.startswith("wave_a"))
    free = [-10 ** 9] * nring
    keys = [([(0, 0.0)], [(0, 0.0)]) for _ in range(nring)]
    for li in timing_map()["lines"]:
        if (line_ids is None and li["role"] not in roles) or (line_ids is not None and li["id"] not in line_ids):
            continue
        for w in li["words"]:
            if not t0 <= w["start"] <= t1:
                continue
            a = frame(w["start"])
            k = min(range(nring), key=lambda j: free[j])
            if free[k] > a:
                continue
            amp = float(np.clip(0.55 + 0.9 * (env[min(a + 3, len(env) - 1)] - 0.5), 0.45, 1.0))
            ph, br = keys[k]
            ph += [(a - 1, 0.0), (a, 0.02), (a + life // 3, 0.7), (a + life, 1.0), (a + life + 1, 0.0)]
            br += [(a - 1, 0.0), (a + 1, amp), (a + life // 3, 0.55 * amp), (a + life, 0.0)]
            free[k] = a + life + 2
    for k, (ph, br) in enumerate(keys):
        write_keys(owner, prop_path(f"wave{k}"), ph, interp="LINEAR")
        write_keys(owner, prop_path(f"wave_a{k}"), br, interp="LINEAR")


def comb(box, evs, lo=36, hi=96, cut_at=None, step=1):
    """A music box (sr_kit.music_box) plays notes: pitch picks one of its 18 teeth (lo..hi spread across the comb,
    low on the left); a tooth snaps up and lights on its note's onset frame, rings down like a struck string while the
    note is held (fast transient, then about 6 dB/s, matching the ending's release) and lets go over 12 frames at the
    note's end. Overlapping notes on a tooth take the louder. cut_at (s) stops everything dead (the SIGTERM)."""
    n = frame(timing_map()["duration_s"]) + 1
    vals = np.zeros((18, n))
    stop = frame(cut_at) if cut_at is not None else n
    for e in evs:
        k = int(np.clip(round((e["pitch"] - lo) / (hi - lo) * 17), 0, 17))
        a = frame(e["t"])
        b = min(max(frame(e["end"]), a + 8), stop)
        f = np.arange(a, min(b + 12, stop, n))
        dt = (f - a) / FPS
        v = 0.3 * 10 ** (-6 * dt / 20) + 0.7 * np.exp(-dt * FPS / 20)
        v = np.where(f < b, v, v * np.clip(1 - (f - b) / 12, 0, 1))
        vals[k, f] = np.maximum(vals[k, f], v)
    lo_f = max(0, min((frame(e["t"]) for e in evs), default=0) - 2)
    hi_f = min(n, max((frame(e["end"]) for e in evs), default=0) + 14, stop + 1)
    for k in range(18):
        if vals[k].any():
            envelope_rig(box, f"tooth{k}", vals[k], lo_f, hi_f, step=step)
    envelope_rig(box, "glow", vals.max(axis=0), lo_f, hi_f, step=step)
