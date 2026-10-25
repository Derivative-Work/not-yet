"""QC: temporal flicker in a rendered frame sequence (z-fighting, shadow acne, light-probe or GI pops, fireflies).

a and c are warped onto b with optical flow (DIS), so camera motion cancels; what is left between the three frames should
change smoothly. A pixel that jumps at b against both neighbours (same sign of b-a' and b-c', a' ~ c') is a pop. Where
the flow can't match (disocclusions, the edge of the frame) the forward and backward warps disagree and the pixel is
skipped. Pops are kept in blobs of at least
MIN_AREA pixels, so single-pixel noise drops out, and then grouped into runs of consecutive frames. A long run in one
place is the z-fighting signature; a one-frame run is a pop. Note-driven lights (LEDs, stars, the shop flicker) also
pop by design: the crops are for a human-eye pass, not a verdict.

Usage: .venv/bin/python -I scripts/qc_flicker.py <frames dir> <out dir> [--thr 0.06] [--top 40]
  -> <out>/flicker.csv (per frame), <out>/runs.json, <out>/run_<k>.png (a | b | c crops, the pop mask in red)
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

MIN_AREA = 6


def load(p):
    im = cv2.imread(str(p), cv2.IMREAD_COLOR)
    return im.astype(np.float32) / 255.0


DIS = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)


def warp_to(b, x):
    """x warped onto b, and a validity mask from the forward-backward flow check."""
    gb, gx = (cv2.cvtColor((im * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY) for im in (b, x))
    fw = DIS.calc(gb, gx, None)
    bw = DIS.calc(gx, gb, None)
    h, w = gb.shape
    gy_, gx_ = np.mgrid[0:h, 0:w].astype(np.float32)
    mx, my = gx_ + fw[..., 0], gy_ + fw[..., 1]
    out = cv2.remap(x, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    back = cv2.remap(bw, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    err = np.linalg.norm(fw + back, axis=2)
    ok = (err < 0.5) & (mx >= 1) & (mx < w - 1) & (my >= 1) & (my < h - 1)
    return out, ok


def pops(a, b, c, thr):
    """Pop strength map and the mask of pops (thr) for the middle frame b."""
    wa, oka = warp_to(b, a)
    wc, okc = warp_to(b, c)
    d1, d2 = b - wa, b - wc
    pop = np.where(np.sign(d1) == np.sign(d2), np.minimum(np.abs(d1), np.abs(d2)), 0).max(2)
    pop[~(oka & okc)] = 0
    back = np.abs(wa - wc).max(2)
    return pop, (pop > thr) & (back < 0.5 * pop)


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    thr = float(sys.argv[sys.argv.index("--thr") + 1]) if "--thr" in sys.argv else 0.06
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 40
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(src.glob("f_*.png"), key=lambda p: int(p.stem[2:]))
    fr = [int(p.stem[2:]) for p in files]
    rows, events = [], []
    a, b = load(files[0]), load(files[1])
    for k in range(2, len(files)):
        c = load(files[k])
        m = pops(a, b, c, thr)[1].astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        blobs = [(st[i, 4], st[i, :4]) for i in range(1, n) if st[i, 4] >= MIN_AREA]
        area = sum(x[0] for x in blobs)
        rows.append((fr[k - 1], area, len(blobs)))
        for ar, (x, y, w, h) in blobs:
            events.append({"frame": fr[k - 1], "area": int(ar), "box": [int(x), int(y), int(w), int(h)]})
        a, b = b, c
        if k % 500 == 0:
            print(k, "/", len(files), flush=True)
    with open(out / "flicker.csv", "w") as f:
        f.write("frame,pop_px,blobs\n")
        f.writelines(f"{r[0]},{r[1]},{r[2]}\n" for r in rows)
    # runs: blobs whose boxes overlap (grown by 8 px) in frames no more than 2 samples apart
    step = fr[1] - fr[0]
    runs = []
    for e in sorted(events, key=lambda e: e["frame"]):
        x, y, w, h = e["box"]
        for r in runs:
            X, Y, W, H = r["box"]
            if e["frame"] - r["last"] <= 2 * step and x < X + W + 8 and X < x + w + 8 and y < Y + H + 8 and Y < y + h + 8:
                r["box"] = [min(x, X), min(y, Y), max(x + w, X + W) - min(x, X), max(y + h, Y + H) - min(y, Y)]
                r["last"], r["n"], r["area"] = e["frame"], r["n"] + 1, r["area"] + e["area"]
                r["peak"] = max(r["peak"], (e["area"], e["frame"]))
                break
        else:
            runs.append({"first": e["frame"], "last": e["frame"], "n": 1, "area": e["area"], "box": list(e["box"]),
                         "peak": (e["area"], e["frame"])})
    runs.sort(key=lambda r: -r["area"])
    by_frame = dict(zip(fr, files))
    for i, r in enumerate(runs[:top]):
        f = r["peak"][1]
        j = fr.index(f)
        x, y, w, h = r["box"]
        pad = 24
        x0, y0 = max(x - pad, 0), max(y - pad, 0)
        x1, y1 = x + w + pad, y + h + pad
        full = [load(by_frame[fr[j + o]]) for o in (-1, 0, 1)]
        pop = pops(*full, thr)[1][y0:y1, x0:x1]
        trip = [im[y0:y1, x0:x1] for im in full]
        mark = trip[1].copy()
        mark[pop] = (0, 0, 1)
        strip = np.concatenate(trip + [mark], 1)
        scale = max(1, int(220 / max(strip.shape[0], 1)))
        strip = cv2.resize(strip, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        cv2.imwrite(str(out / f"run_{i:02d}.png"), (strip * 255).astype(np.uint8))
        r["crop"] = f"run_{i:02d}.png"
    (out / "runs.json").write_text(json.dumps({"thr": thr, "step": step, "runs": runs}, indent=1))
    print(len(events), "blobs;", len(runs), "runs; top:", [(r["first"], r["last"], r["n"], r["area"]) for r in runs[:10]])


if __name__ == "__main__":
    main()
