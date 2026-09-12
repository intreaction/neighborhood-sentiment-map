"""Find specific investments and measure what happened to sentiment around them.

The pooled lag analysis is a null, which is the expected result when a handful of
real effects are averaged against thousands of quarters where nothing happened.
This does the opposite: pick individual large place-based awards landing in ZIPs
with enough reviews to measure, then read each one's own before/after.

The estimate is a difference-in-differences: the ZIP's sentiment change across the
award, minus the change over the same quarters in the rest of its metro. Netting
out the metro removes COVID and every other city-wide shock, which is what makes
a 2020 award readable at all.

    effect = (zip_post - zip_pre) - (metro_post - metro_pre)

Output: data/interim/case_studies.csv, ranked by |effect|, with the award's own
description so each row can be read as a story rather than a coefficient.
"""

import csv
import glob
import statistics
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
RAW = ROOT / "data" / "raw" / "usaspending"

csv.field_size_limit(sys.maxsize)

MIN_REVIEWS = 30
WINDOW = 6          # quarters either side
MIN_COVER = 5       # need at least this many measurable quarters on each side
MIN_AWARD = 2_000_000

# Programme families whose money plausibly changes how a place is experienced.
PLACE_CFDA = ("14.", "20.", "23.", "16.", "21.", "97.036", "97.039", "11.300",
              "10.760", "59.")

QS = [f"{y}Q{q}" for y in range(2012, 2022) for q in (1, 2, 3, 4)]
QI = {q: i for i, q in enumerate(QS)}


def quarter_of(d):
    return f"{d[:4]}Q{(int(d[5:7]) - 1) // 3 + 1}"


def load_panel():
    sent, metro_of = {}, {}
    for r in csv.DictReader(open(INTERIM / "sentiment_zip_quarter.csv")):
        if int(r["n_reviews"]) >= MIN_REVIEWS and r["quarter"] in QI:
            sent[(r["zip5"], QI[r["quarter"]])] = float(r["mean_compound"])
    for r in csv.DictReader(open(INTERIM / "awards_zip_quarter.csv")):
        metro_of[r["zip5"]] = r["metro"]
    return sent, metro_of


def metro_means(sent, metro_of):
    """Mean sentiment per metro-quarter, used as each ZIP's control group."""
    acc = defaultdict(list)
    for (z, t), v in sent.items():
        m = metro_of.get(z)
        if m:
            acc[(m, t)].append(v)
    return {k: statistics.mean(v) for k, v in acc.items()}


def load_awards(zips):
    """Large place-based transactions in the study ZIPs, with their text."""
    out = []
    for zp in sorted(glob.glob(str(RAW / "assistance_*.zip"))):
        with zipfile.ZipFile(zp) as zf:
            name = [n for n in zf.namelist() if n.endswith(".csv")][0]
            with zf.open(name) as fh:
                for row in csv.DictReader(
                        (l.decode("utf-8", "replace") for l in fh)):
                    z = (row.get("primary_place_of_performance_zip_4") or "")[:5]
                    if z not in zips:
                        continue
                    cfda = row.get("cfda_number") or ""
                    if not cfda.startswith(PLACE_CFDA):
                        continue
                    try:
                        amt = float(row.get("federal_action_obligation") or 0)
                    except ValueError:
                        continue
                    if amt < MIN_AWARD:          # deobligations are negative
                        continue
                    d = row.get("action_date") or ""
                    if len(d) < 7 or quarter_of(d) not in QI:
                        continue
                    out.append({
                        "zip": z, "q": quarter_of(d), "t": QI[quarter_of(d)],
                        "amount": amt, "cfda": cfda,
                        "program": (row.get("cfda_title") or "").strip(),
                        "agency": (row.get("awarding_agency_name") or "").strip(),
                        "recipient": (row.get("recipient_name") or "").strip(),
                        "desc": (row.get("transaction_description")
                                 or row.get("prime_award_base_transaction_description")
                                 or "").strip(),
                    })
    return out


def window_mean(series, zip_or_metro, t0, lo, hi):
    vals = [series[(zip_or_metro, t)] for t in range(t0 + lo, t0 + hi)
            if (zip_or_metro, t) in series]
    return (statistics.mean(vals), len(vals)) if vals else (None, 0)


def main():
    sent, metro_of = load_panel()
    zips = set(metro_of)
    mmean = metro_means(sent, metro_of)
    print(f"{len(sent):,} measurable ZIP-quarters across {len(zips)} ZIPs", flush=True)

    awards = load_awards(zips)
    print(f"{len(awards):,} place-based awards >= ${MIN_AWARD:,}", flush=True)

    # One ZIP-quarter can hold several awards; treat it as one event.
    events = defaultdict(lambda: {"amount": 0.0, "items": []})
    for a in awards:
        e = events[(a["zip"], a["t"])]
        e["amount"] += a["amount"]
        e["items"].append(a)

    rows = []
    for (z, t0), e in events.items():
        m = metro_of.get(z)
        if not m:
            continue
        zpre, npre = window_mean(sent, z, t0, -WINDOW, 0)
        zpost, npost = window_mean(sent, z, t0, 1, WINDOW + 1)
        if npre < MIN_COVER or npost < MIN_COVER:
            continue
        mpre, _ = window_mean(mmean, m, t0, -WINDOW, 0)
        mpost, _ = window_mean(mmean, m, t0, 1, WINDOW + 1)
        if mpre is None or mpost is None:
            continue
        did = (zpost - zpre) - (mpost - mpre)
        big = max(e["items"], key=lambda a: a["amount"])
        rows.append({
            "zip": z, "metro": m, "quarter": QS[t0],
            "amount": round(e["amount"]),
            "n_awards": len(e["items"]),
            "zip_pre": round(zpre, 4), "zip_post": round(zpost, 4),
            "zip_delta": round(zpost - zpre, 4),
            "metro_delta": round(mpost - mpre, 4),
            "did": round(did, 4),
            "q_pre": npre, "q_post": npost,
            "cfda": big["cfda"], "program": big["program"],
            "agency": big["agency"], "recipient": big["recipient"],
            "desc": big["desc"][:160],
        })

    rows.sort(key=lambda r: -abs(r["did"]))
    out = INTERIM / "case_studies.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    dids = [r["did"] for r in rows]
    print(f"{len(rows)} events with >= {MIN_COVER} measurable quarters each side")
    print(f"mean DiD {statistics.mean(dids):+.4f}  median {statistics.median(dids):+.4f}")
    print(f"positive {sum(1 for d in dids if d > 0)} / negative {sum(1 for d in dids if d < 0)}")
    print(f"-> {out}\n")

    print("Largest movements either way (DiD = ZIP change minus its metro's change):\n")
    for r in rows[:12]:
        print(f"  {r['did']:+.3f}  {r['quarter']}  ZIP {r['zip']} ({r['metro']})  "
              f"${r['amount']/1e6:,.1f}M")
        print(f"          {r['cfda']} {r['program'][:52]}")
        if r["desc"]:
            print(f"          \"{r['desc'][:88]}\"")


if __name__ == "__main__":
    main()
