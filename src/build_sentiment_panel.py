"""Extract the five-metro reviews and score sentiment into quarterly panels.

One streaming pass over the 5.3 GB review file (never extracted to disk): keep
reviews whose business sits in one of the 277 study ZIPs, score each with VADER,
and roll up to ZIP-quarter and metro-quarter.

VADER is the Lab 2 method and needs no model download, which makes it the right
baseline for Milestone 2. Per-review scores are written out so the panel can be
re-aggregated (monthly, by category, by rating) without re-reading the tar, and
so a transformer model can be swapped in later without redoing extraction.

Outputs (data/interim/):
    reviews_5metro.csv            one row per review: zip, metro, date, stars, compound
    sentiment_zip_quarter.csv     zip x quarter: n, mean compound, mean stars, %negative
    sentiment_metro_quarter.csv   metro x quarter: same, for the graphs

Add --with-text to also emit reviews_5metro_text.jsonl.gz for later topic modeling.
"""

import argparse
import csv
import gzip
import json
import tarfile
from collections import defaultdict
from pathlib import Path

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

ROOT = Path(__file__).resolve().parent.parent
TAR = ROOT / "Yelp JSON" / "yelp_dataset.tar"
BUSINESS = ROOT / "data" / "raw" / "yelp_academic_dataset_business.json"
METRO_ZIPS = ROOT / "data" / "interim" / "metro_zips.json"
INTERIM = ROOT / "data" / "interim"
MEMBER = "yelp_academic_dataset_review.json"

# Reviews thin out before 2012 and stop 2022-01-19; the panel covers full quarters.
START_YEAR, END_YEAR = 2012, 2021
NEG_THRESHOLD = -0.05  # VADER's conventional negative cutoff


def quarter_of(date_str):
    y, m = date_str[:4], int(date_str[5:7])
    return f"{y}Q{(m - 1) // 3 + 1}"


def load_business_index():
    """business_id -> (zip, metro) for businesses in the study ZIPs."""
    zip_metro = {
        z: metro for metro, zs in json.loads(METRO_ZIPS.read_text()).items() for z in zs
    }
    idx = {}
    with open(BUSINESS) as f:
        for line in f:
            b = json.loads(line)
            z = (b.get("postal_code") or "").strip()
            m = zip_metro.get(z)
            if m:
                idx[b["business_id"]] = (z, m, b.get("is_open"), b.get("categories") or "")
    return idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-text", action="store_true",
                    help="also write review text for later topic modeling")
    args = ap.parse_args()

    biz = load_business_index()
    print(f"{len(biz):,} businesses in the 5 metros", flush=True)

    va = SentimentIntensityAnalyzer()
    INTERIM.mkdir(parents=True, exist_ok=True)

    # zip-quarter and metro-quarter accumulators: [n, sum_compound, sum_stars, n_neg]
    zq = defaultdict(lambda: [0, 0.0, 0, 0])
    mq = defaultdict(lambda: [0, 0.0, 0, 0])

    out = open(INTERIM / "reviews_5metro.csv", "w", newline="")
    w = csv.writer(out)
    w.writerow(["zip5", "metro", "date", "quarter", "stars", "compound", "is_open"])

    tw = None
    if args.with_text:
        tw = gzip.open(INTERIM / "reviews_5metro_text.jsonl.gz", "wt")

    scanned = kept = 0
    with tarfile.open(TAR) as tf:
        fh = tf.extractfile(MEMBER)
        for line in fh:
            scanned += 1
            if scanned % 1_000_000 == 0:
                print(f"  {scanned:,} scanned, {kept:,} kept", flush=True)
            try:
                r = json.loads(line)
            except ValueError:
                continue
            hit = biz.get(r.get("business_id"))
            if not hit:
                continue
            date = r.get("date") or ""
            year = date[:4]
            if not (str(START_YEAR) <= year <= str(END_YEAR)):
                continue
            z, metro, is_open, _cats = hit
            q = quarter_of(date)
            text = r.get("text") or ""
            comp = va.polarity_scores(text)["compound"]
            stars = int(r.get("stars") or 0)
            kept += 1

            w.writerow([z, metro, date[:10], q, stars, f"{comp:.4f}", is_open])
            if tw:
                tw.write(json.dumps({"business_id": r["business_id"], "zip5": z,
                                     "metro": metro, "quarter": q, "stars": stars,
                                     "compound": round(comp, 4), "text": text}) + "\n")

            neg = 1 if comp <= NEG_THRESHOLD else 0
            for acc, key in ((zq, (z, q)), (mq, (metro, q))):
                c = acc[key]
                c[0] += 1
                c[1] += comp
                c[2] += stars
                c[3] += neg

    out.close()
    if tw:
        tw.close()

    def dump(path, acc, key_names):
        with open(path, "w", newline="") as f:
            ww = csv.writer(f)
            ww.writerow([*key_names, "n_reviews", "mean_compound", "mean_stars", "pct_negative"])
            for key, (n, sc, ss, nn) in sorted(acc.items()):
                ww.writerow([*key, n, f"{sc / n:.4f}", f"{ss / n:.3f}", f"{100 * nn / n:.1f}"])
        print(f"  {len(acc):,} rows -> {path.name}")

    print(f"\n{scanned:,} reviews scanned, {kept:,} kept ({START_YEAR}-{END_YEAR}, 5 metros)")
    dump(INTERIM / "sentiment_zip_quarter.csv", zq, ["zip5", "quarter"])
    dump(INTERIM / "sentiment_metro_quarter.csv", mq, ["metro", "quarter"])


if __name__ == "__main__":
    main()
