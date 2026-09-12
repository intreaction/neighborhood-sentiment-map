"""Compute the investment-stock lag model and emit the demo page's data.

Implements the specification the analysis fleet converged on:

  kernel   w_k proportional to k^a * exp(-k/b), normalised over k = 0..48 quarters,
           with b = [P*ln((P+H)/P) - H] / ln(0.5) and a = P/b, so the continuous
           maximum sits at k = P and the tail is half the peak at k = P + H.
           For P = 0 the kernel degenerates to exp(-k*ln2/H).

  stock    S_t = sum_k w_k * log1p(max(obligations_{t-k}, 0)) / sum_{k: t-k >= 2010Q1} w_k

           That denominator is the edge correction. Without it a 48-quarter kernel
           convolved against award data starting in 2010 pads the early years with
           fabricated zeros, so the stock ramps mechanically over time in proportion
           to each ZIP's total dollars. Against a falling sentiment trend that alone
           manufactures a correlation. The page ships both versions because showing
           the artifact is the most instructive thing here.

  controls demean stock and sentiment by ZIP and by quarter, alternating sweeps.

  inference the honest unit is the ZIP (185 of them), not the ZIP-quarter (6,548),
           so significance comes from permuting whole award histories across ZIPs,
           never from an iid t on the cell count.

Output: data/interim/lag_model.json
"""

import csv
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
OUT = INTERIM / "lag_model.json"

MIN_REVIEWS = 30
AQ = [f"{y}Q{q}" for y in range(2010, 2022) for q in (1, 2, 3, 4)]   # award history
SQ = [f"{y}Q{q}" for y in range(2012, 2022) for q in (1, 2, 3, 4)]   # sentiment window
AQI = {q: i for i, q in enumerate(AQ)}
MAXLAG = len(AQ)

PEAKS = [0, 1, 2, 3, 4, 6, 8, 10]
HALVES = [2, 4, 6, 8, 12, 16]
DEFAULT_P, DEFAULT_H = 4, 8
N_PERM = 400
SEED = 20260903

CASE_ZIPS = ["19121", "37201", "33755", "70122", "33607", "37206", "19107"]


# ---------------------------------------------------------------- kernel
def kernel(P, H, n=MAXLAG):
    if P <= 0:
        w = [math.exp(-k * math.log(2) / H) for k in range(n)]
    else:
        b = (P * math.log((P + H) / P) - H) / math.log(0.5)
        a = P / b
        w = [0.0] + [math.exp(a * math.log(k) - k / b) for k in range(1, n)]
    s = sum(w)
    return [x / s for x in w] if s else w


# ---------------------------------------------------------------- data
def load():
    sent, nrev = {}, {}
    for r in csv.DictReader(open(INTERIM / "sentiment_zip_quarter.csv")):
        if r["quarter"] not in SQ:
            continue
        n = int(r["n_reviews"])
        nrev[(r["zip5"], r["quarter"])] = n
        if n >= MIN_REVIEWS:
            sent[(r["zip5"], r["quarter"])] = float(r["mean_compound"])

    obl = defaultdict(lambda: [0.0] * MAXLAG)
    metro = {}
    for r in csv.DictReader(open(INTERIM / "awards_zip_quarter.csv")):
        metro[r["zip5"]] = r["metro"]
        if r["kind"] != "place" or r["quarter"] not in AQI:
            continue
        obl[r["zip5"]][AQI[r["quarter"]]] += max(0.0, float(r["obligations"]))

    zips = sorted({z for z, _ in sent})
    for z in zips:
        obl[z]  # materialise zeros for funded-nothing ZIPs
    return sent, nrev, dict(obl), metro, zips


def stock_series(logobl, w, corrected):
    """Stock at every award-quarter index for one ZIP."""
    out = []
    for t in range(MAXLAG):
        num = 0.0
        den = 0.0
        for k in range(t + 1):
            num += w[k] * logobl[t - k]
            den += w[k]
        out.append(num / den if (corrected and den > 0) else num)
    return out


def demean(vals, keys, idx, sweeps=2):
    v = dict(zip(keys, vals))
    for _ in range(sweeps):
        for axis in (0, 1):
            g = defaultdict(list)
            for k, x in v.items():
                g[k[axis]].append(x)
            m = {kk: statistics.mean(xs) for kk, xs in g.items()}
            v = {k: x - m[k[axis]] for k, x in v.items()}
    return v


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def fit(sent, logobl_by_zip, zips, P, H, corrected=True, fe="both", assign=None):
    """Correlation between investment stock and sentiment under a control regime."""
    w = kernel(P, H)
    stocks = {}
    for z in zips:
        src = assign[z] if assign else z
        stocks[z] = stock_series(logobl_by_zip[src], w, corrected)

    keys, xs, ys = [], [], []
    for (z, q), sv in sent.items():
        t = AQI.get(q)
        if t is None or z not in stocks:
            continue
        keys.append((z, q))
        xs.append(stocks[z][t])
        ys.append(sv)
    if len(xs) < 10:
        return 0.0, len(xs)

    if fe == "none":
        return pearson(xs, ys), len(xs)
    sweeps = 2
    if fe == "both":
        dx = demean(xs, keys, None, sweeps)
        dy = demean(ys, keys, None, sweeps)
    else:
        axis = 0 if fe == "zip" else 1
        gx, gy = defaultdict(list), defaultdict(list)
        for k, x, y in zip(keys, xs, ys):
            gx[k[axis]].append(x)
            gy[k[axis]].append(y)
        mx = {k: statistics.mean(v) for k, v in gx.items()}
        my = {k: statistics.mean(v) for k, v in gy.items()}
        dx = {k: x - mx[k[axis]] for k, x in zip(keys, xs)}
        dy = {k: y - my[k[axis]] for k, y in zip(keys, ys)}
    order = list(dx)
    return pearson([dx[k] for k in order], [dy[k] for k in order]), len(xs)


def main():
    sent, nrev, obl, metro, zips = load()
    logobl = {z: [math.log1p(v) for v in obl[z]] for z in obl}
    print(f"{len(sent):,} measurable ZIP-quarters, {len(zips)} ZIPs, "
          f"{sum(1 for z in zips if sum(obl[z]) > 0)} of them funded", flush=True)

    surface = []
    for P in PEAKS:
        for H in HALVES:
            rc, n = fit(sent, logobl, zips, P, H, corrected=True)
            rp, _ = fit(sent, logobl, zips, P, H, corrected=False)
            # every control regime at every knob position, so the page's
            # fixed-effects toggle stays honest wherever the user drags to
            rn, _ = fit(sent, logobl, zips, P, H, True, "none")
            rz, _ = fit(sent, logobl, zips, P, H, True, "zip")
            rq, _ = fit(sent, logobl, zips, P, H, True, "quarter")
            surface.append({"P": P, "H": H, "r": round(rc, 5),
                            "r_padded": round(rp, 5), "n": n,
                            "r_none": round(rn, 5), "r_zip": round(rz, 5),
                            "r_quarter": round(rq, 5)})
    best = max(surface, key=lambda c: abs(c["r"]))
    worst_pad = max(surface, key=lambda c: abs(c["r_padded"]))
    print(f"corrected: max |r| = {best['r']:+.4f} at P={best['P']} H={best['H']}")
    print(f"padded   : max |r| = {worst_pad['r_padded']:+.4f} "
          f"at P={worst_pad['P']} H={worst_pad['H']}", flush=True)

    fes = {}
    for mode in ("none", "zip", "quarter", "both"):
        r, n = fit(sent, logobl, zips, DEFAULT_P, DEFAULT_H, True, mode)
        fes[mode] = round(r, 5)
        print(f"  FE={mode:<8} r={r:+.4f}", flush=True)

    # Permutation: hand each ZIP's whole award history to a different ZIP.
    rng = random.Random(SEED)
    maxes, at_default = [], []
    funded = [z for z in zips]
    for i in range(N_PERM):
        shuf = funded[:]
        rng.shuffle(shuf)
        assign = dict(zip(funded, shuf))
        rd, _ = fit(sent, logobl, zips, DEFAULT_P, DEFAULT_H, True, "both", assign)
        at_default.append(rd)
        cells = [fit(sent, logobl, zips, P, H, True, "both", assign)[0]
                 for P in (0, 4, 10) for H in (2, 8, 16)]
        maxes.append(max(abs(c) for c in cells))
        if (i + 1) % 50 == 0:
            print(f"  permutation {i+1}/{N_PERM}", flush=True)

    maxes.sort()
    at_abs = sorted(abs(v) for v in at_default)
    perm = {
        "n": N_PERM,
        "null_sd_default": round(statistics.pstdev(at_default), 5),
        "null_max_median": round(maxes[len(maxes) // 2], 5),
        "null_max_p95": round(maxes[int(0.95 * (len(maxes) - 1))], 5),
        "p_family": round(sum(1 for m in maxes if m >= abs(best["r"])) / len(maxes), 3),
        "p_default": round(sum(1 for v in at_abs if v >= abs(fes["both"])) / len(at_abs), 3),
    }
    print(f"permutation: null max median {perm['null_max_median']:.4f}, "
          f"family-wise p = {perm['p_family']}", flush=True)

    # ZIP-clustered bootstrap for a defensible interval at the default cell.
    zlist = list(zips)
    boot = []
    for _ in range(300):
        draw = [zlist[rng.randrange(len(zlist))] for _ in zlist]
        sub, seen = {}, defaultdict(int)
        for z in draw:
            seen[z] += 1
            tag = f"{z}#{seen[z]}"
            for q in SQ:
                if (z, q) in sent:
                    sub[(tag, q)] = sent[(z, q)]
        lo = {f"{z}#{i+1}": logobl[z] for z in zlist for i in range(seen[z])}
        if len(sub) > 100:
            r, _ = fit(sub, lo, list(lo), DEFAULT_P, DEFAULT_H, True, "both")
            boot.append(r)
    boot.sort()
    ci = [round(boot[int(0.025 * (len(boot) - 1))], 4),
          round(boot[int(0.975 * (len(boot) - 1))], 4)] if boot else [None, None]
    print(f"clustered 95% CI at default: {ci}", flush=True)

    # Per-case series so the page can build the stacking animation live.
    msent = defaultdict(lambda: defaultdict(list))
    for (z, q), v in sent.items():
        m = metro.get(z)
        if m:
            msent[m][q].append(v)
    cases = []
    for z in CASE_ZIPS:
        if z not in obl:
            continue
        m = metro.get(z, "")
        cases.append({
            "zip": z, "metro": m,
            "awards": [round(v) for v in obl[z]],
            "sent": [round(sent[(z, q)], 4) if (z, q) in sent else None for q in SQ],
            "n": [nrev.get((z, q), 0) for q in SQ],
            "metroSent": [round(statistics.mean(msent[m][q]), 4) if msent[m].get(q) else None
                          for q in SQ],
            "total": round(sum(obl[z])),
            "quarters_funded": sum(1 for v in obl[z] if v > 0),
        })

    payload = {
        "awardQuarters": AQ, "sentQuarters": SQ,
        "peaks": PEAKS, "halves": HALVES,
        "default": {"P": DEFAULT_P, "H": DEFAULT_H},
        "surface": surface, "fe": fes, "perm": perm, "clusteredCI": ci,
        "best": best, "paddedWorst": worst_pad,
        "cases": cases,
        "nCells": len(sent), "nZips": len(zips),
        "minDetectable": 0.09,
    }
    OUT.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"\nwrote {OUT} ({OUT.stat().st_size/1e3:.0f} KB)")


if __name__ == "__main__":
    main()
