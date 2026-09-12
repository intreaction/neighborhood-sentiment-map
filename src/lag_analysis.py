"""Does investment lead sentiment, and by how long?

Cross-correlates place-based obligations in a ZIP-quarter against that ZIP's
review sentiment k quarters later, for k = -4 .. +8.

Two controls do the real work here:

  ZIP demeaning     removes fixed differences between neighbourhoods (a rich ZIP
                    is both better-reviewed and better-funded; that is not a lag).
  Quarter demeaning removes shocks common to every ZIP. Without it COVID alone
                    manufactures a correlation at whatever lag separates the
                    2020 sentiment collapse from the 2020-21 relief surge.

Negative lags are the falsification test: investment cannot be caused by future
sentiment, so a peak at k<0 means the design is picking up trend, not effect.
"""

import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
MIN_REVIEWS = 30
LAGS = range(-4, 9)


def quarters(start=2012, end=2021):
    return [f"{y}Q{q}" for y in range(start, end + 1) for q in (1, 2, 3, 4)]


def pearson(xs, ys):
    n = len(xs)
    if n < 10:
        return None, n
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return None, n
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
    return r, n


def tstat(r, n):
    if r is None or abs(r) >= 1:
        return None
    return r * math.sqrt(max(n - 2, 1)) / math.sqrt(max(1e-12, 1 - r * r))


def demean(cells, key_index):
    """Subtract the mean of each group defined by key_index (0=zip, 1=quarter)."""
    groups = defaultdict(list)
    for k in cells:
        groups[k[key_index]].append(cells[k])
    means = {g: statistics.mean(v) for g, v in groups.items()}
    return {k: v - means[k[key_index]] for k, v in cells.items()}


def main():
    QS = quarters()
    qi = {q: i for i, q in enumerate(QS)}

    sent = {}
    with open(INTERIM / "sentiment_zip_quarter.csv") as f:
        for r in csv.DictReader(f):
            if int(r["n_reviews"]) < MIN_REVIEWS or r["quarter"] not in qi:
                continue
            sent[(r["zip5"], qi[r["quarter"]])] = float(r["mean_compound"])

    inv = defaultdict(float)
    with open(INTERIM / "awards_zip_quarter.csv") as f:
        for r in csv.DictReader(f):
            if r["kind"] != "place" or r["quarter"] not in qi:
                continue
            inv[(r["zip5"], qi[r["quarter"]])] += float(r["obligations"])

    # Only ZIP-quarters where sentiment is measurable; obligations of zero are
    # real observations (no award that quarter), so they stay in.
    cells_inv = {k: math.log1p(max(0.0, inv.get(k, 0.0))) for k in sent}
    cells_sen = dict(sent)

    for _ in range(2):  # alternate until both margins are swept out
        cells_inv = demean(demean(cells_inv, 0), 1)
        cells_sen = demean(demean(cells_sen, 0), 1)

    zips = sorted({z for z, _ in sent})
    print(f"{len(sent):,} ZIP-quarter cells, {len(zips)} ZIPs, "
          f"sentiment >= {MIN_REVIEWS} reviews")
    print("investment = log1p(place-based obligations), both series demeaned "
          "by ZIP and by quarter\n")
    print(f"{'lag':>5} {'r':>8} {'t':>7} {'n':>7}   {'':<24}")
    best = (0, 0.0)
    rows = []
    for k in LAGS:
        xs, ys = [], []
        for (z, t), xv in cells_inv.items():
            yv = cells_sen.get((z, t + k))
            if yv is None:
                continue
            xs.append(xv)
            ys.append(yv)
        r, n = pearson(xs, ys)
        if r is None:
            continue
        t_ = tstat(r, n)
        rows.append((k, r, t_, n))
        if abs(r) > abs(best[1]):
            best = (k, r)
        bar_n = int(round(abs(r) * 400))
        bar = ("+" if r > 0 else "-") * min(bar_n, 24)
        flag = "  <-- |t|>2" if t_ and abs(t_) > 2 else ""
        print(f"{k:>+5} {r:>+8.4f} {t_:>7.2f} {n:>7,}   {bar}{flag}")

    print(f"\nstrongest |r| at lag {best[0]:+d} (r = {best[1]:+.4f})")
    pos = [r for k, r, _, _ in rows if k > 0]
    neg = [r for k, r, _, _ in rows if k < 0]
    if pos and neg:
        print(f"mean r, future sentiment (k>0): {statistics.mean(pos):+.4f}")
        print(f"mean r, past sentiment  (k<0): {statistics.mean(neg):+.4f}   "
              "(placebo - should be ~0 if the lag is real)")


if __name__ == "__main__":
    main()
