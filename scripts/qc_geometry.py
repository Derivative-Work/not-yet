"""QC: geometry that can z-fight. Builds the animatic scene (scenes/blender/animatic.py) and, at every shot anchor,
finds triangles of different visible objects that share a plane and overlap.

  same-facing     both faces point the same way (a decal on a wall): they z-fight wherever the overlap is in view
  back-to-back    opposite faces (one object resting on another): hidden behind the top object unless it is see-through

A pair is also flagged when it is not coplanar but the gap is under what the depth buffer resolves at the nearest
camera distance seen at the anchors (dz ~ z^2 / (clip_start * 2^24), times a safety factor of 4).

Usage: blender -b --factory-startup --python scripts/qc_geometry.py -- OUT.json [--tol MM] [--shots ID ...]
  (--shots: only those anchors, e.g. to re-check a fix)
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scenes" / "blender"))
import animatic  # noqa: E402
import sr_anim as A  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = Path(argv[0])
TOL = float(argv[argv.index("--tol") + 1]) / 1000 if "--tol" in argv else 0.003  # metres: widest gap considered
N_Q, D_Q = 400, TOL  # plane bucket: normal quantised to 1/400, offset to TOL


def tris_world(o, dg):
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    if n == 0:
        ev.to_mesh_clear()
        return None
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    idx = np.empty(n * 3, np.int32)
    me.loop_triangles.foreach_get("vertices", idx)
    ev.to_mesh_clear()
    m = np.array(ev.matrix_world, np.float64)
    co = co.reshape(-1, 3).astype(np.float64) @ m[:3, :3].T + m[:3, 3]
    return co[idx.reshape(-1, 3)]


def clip_area(p, q):
    """Area of the intersection of two 2D triangles (Sutherland-Hodgman)."""
    def area(poly):
        return 0.5 * (np.dot(poly[:, 0], np.roll(poly[:, 1], -1)) - np.dot(poly[:, 1], np.roll(poly[:, 0], -1)))
    if area(q) < 0:
        q = q[::-1]
    out = list(p)
    for i in range(3):
        a, b = q[i], q[(i + 1) % 3]
        inp, out = out, []
        if not inp:
            break
        for j in range(len(inp)):
            c, d = inp[j], inp[(j + 1) % len(inp)]
            sc = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            sd = (b[0] - a[0]) * (d[1] - a[1]) - (b[1] - a[1]) * (d[0] - a[0])
            if sc >= 0:
                out.append(c)
            if (sc >= 0) != (sd >= 0):
                t = sc / (sc - sd)
                out.append(c + t * (d - c))
    return abs(area(np.array(out))) if len(out) >= 3 else 0.0


def scan(scene, cam):
    dg = bpy.context.evaluated_depsgraph_get()
    T, N, D, OB = [], [], [], []
    names = []
    for o in scene.objects:
        if o.type not in {"MESH", "CURVE", "FONT"} or o.hide_render or not o.visible_get():
            continue
        t = tris_world(o, dg)
        if t is None:
            continue
        nrm = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        ln = np.linalg.norm(nrm, axis=1)
        keep = ln > 1e-10  # 2 * area > 2e-10 m^2
        t, nrm, ln = t[keep], nrm[keep], ln[keep]
        nrm /= ln[:, None]
        T.append(t), N.append(nrm), D.append(np.einsum("ij,ij->i", nrm, t[:, 0])), OB.append(np.full(len(t), len(names)))
        names.append(o.name)
    T, N, D, OB = np.concatenate(T), np.concatenate(N), np.concatenate(D), np.concatenate(OB)
    # canonical orientation: the first clearly non-zero component positive; remember the original facing
    sgn = np.sign(np.where(np.abs(N[:, 0]) > 1e-6, N[:, 0], np.where(np.abs(N[:, 1]) > 1e-6, N[:, 1], N[:, 2])))
    Nc, Dc = N * sgn[:, None], D * sgn
    key_n = np.round(Nc * N_Q).astype(np.int64)
    key_d = np.floor(Dc / D_Q).astype(np.int64)
    buckets = defaultdict(list)
    for i, k in enumerate(map(tuple, np.column_stack([key_n, key_d]))):
        buckets[k].append(i)
    pairs = {}
    seen = set()
    for (nx, ny, nz, kd), idx in buckets.items():
        cand = list(idx)
        for dd in (1,):  # neighbour offset bucket catches pairs straddling a bucket edge
            cand += buckets.get((nx, ny, nz, kd + dd), [])
        cand = np.array(cand)
        if len(np.unique(OB[cand])) < 2:
            continue
        n0 = Nc[cand[0]]
        u = np.cross(n0, [0, 0, 1] if abs(n0[2]) < 0.9 else [1, 0, 0])
        u /= np.linalg.norm(u)
        v = np.cross(n0, u)
        P = np.stack([T[cand] @ u, T[cand] @ v], -1)  # (k, 3, 2)
        lo, hi = P.min(1), P.max(1)
        for a in range(len(cand)):
            ob = OB[cand[a]]
            m = (OB[cand] > ob) & np.all(lo <= hi[a], 1) & np.all(hi >= lo[a], 1)
            for b in np.nonzero(m)[0]:
                i, j = cand[a], cand[b]
                if (i, j) in seen or abs(Dc[i] - Dc[j]) > TOL or np.dot(Nc[i], Nc[j]) < 0.9995:
                    continue
                seen.add((i, j))
                ar = clip_area(P[a], P[b])
                if ar < 1e-7:
                    continue
                kind = "same-facing" if sgn[i] == sgn[j] else "back-to-back"
                key = (names[OB[i]], names[OB[j]], kind)
                r = pairs.setdefault(key, {"area_cm2": 0.0, "gap_mm": 1e9, "at": None})
                r["area_cm2"] += ar * 1e4
                r["gap_mm"] = min(r["gap_mm"], abs(Dc[i] - Dc[j]) * 1000)
                if r["at"] is None:
                    r["at"] = list(map(float, T[i].mean(0)))
    return pairs


scene, f_end = animatic.build([320, 180], 1)
cam = scene.camera
near = cam.data.clip_start
shots = [s for s in A.timing_map()["shots"] if s["t"] is not None and s["t"] <= animatic.animate.OUT["black"]]
if "--shots" in argv:
    want = {a for a in argv[argv.index("--shots") + 1:] if not a.startswith("--")}
    shots = [s for s in shots if s["id"] in want]
found = {}
for s in shots:
    f = min(A.frame(s["t"]) + 2, f_end)
    scene.frame_set(f)
    for key, r in scan(scene, cam).items():
        p = r["at"]
        from mathutils import Vector
        c = world_to_camera_view(scene, cam, Vector(p))
        in_view = 0 <= c.x <= 1 and 0 <= c.y <= 1 and near < c.z < cam.data.clip_end
        z = (Vector(p) - cam.matrix_world.translation).length
        resolve_mm = 4 * z * z / (near * 2 ** 24) * 1000
        g = found.setdefault("|".join(key), {"a": key[0], "b": key[1], "kind": key[2], "area_cm2": 0, "gap_mm": 1e9,
                                             "at": p, "shots_in_view": [], "min_dist_m": 1e9, "resolve_mm": 1e9})
        g["area_cm2"] = max(g["area_cm2"], round(r["area_cm2"], 3))
        g["gap_mm"] = min(g["gap_mm"], round(r["gap_mm"], 4))
        if in_view:
            g["shots_in_view"].append(s["id"])
            g["min_dist_m"] = min(g["min_dist_m"], round(z, 3))
            g["resolve_mm"] = min(g["resolve_mm"], round(resolve_mm, 4))
    print("scanned", s["id"], f, len(found), flush=True)

rows = sorted(found.values(), key=lambda g: (g["kind"] != "same-facing", not g["shots_in_view"], -g["area_cm2"]))
for g in rows:
    g["risk"] = bool(g["shots_in_view"]) and bool(g["gap_mm"] < 1e-3 or g["gap_mm"] < g["resolve_mm"])
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"clip_start": near, "tol_mm": TOL * 1000, "pairs": rows}, indent=1,
                          default=lambda x: x.item()))  # numpy scalars
print("wrote", OUT, len(rows), "pairs;", sum(g["risk"] and g["kind"] == "same-facing" for g in rows),
      "same-facing at risk in view", flush=True)
