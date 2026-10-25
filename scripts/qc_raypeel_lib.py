"""Ray helpers shared by qc_raypeel.py and qc_raypeel_crops.py."""


def ray_dir(scene, cam, u, v):
    """World-space ray direction through normalised image coords u, v (0..1, v up)."""
    fr = cam.data.view_frame(scene=scene)  # tr, br, bl, tl in camera space
    tl, tr, bl = fr[3], fr[0], fr[2]
    p = tl + (tr - tl) * u + (bl - tl) * (1 - v)
    m = cam.matrix_world
    return (m.to_3x3() @ p).normalized()


def peel(scene, dg, origin, d, max_hits=6):
    hits = []
    o = origin.copy()
    travelled = 0.0
    for _ in range(max_hits * 3):
        ok, loc, nrm, _, ob, _ = scene.ray_cast(dg, o, d, distance=900.0)
        if not ok:
            break
        travelled += (loc - o).length
        o = loc + d * 1e-6
        travelled += 1e-6
        if ob.original.hide_render:
            continue
        hits.append((ob.original.name, travelled, nrm.dot(d) < 0))
        if len(hits) >= max_hits:
            break
    return hits


def fights(hits, near):
    """(a, b, z, gap) when the first visible surface has a front-facing surface of another object right behind it."""
    if not hits or not hits[0][2]:
        return None
    a, z, _ = hits[0]
    lim = max(4 * z * z / (near * 2 ** 24), 0.0002)
    for b, zb, front in hits[1:]:
        if zb - z > lim:
            break
        if b != a and front:
            return a, b, z, zb - z
    return None
