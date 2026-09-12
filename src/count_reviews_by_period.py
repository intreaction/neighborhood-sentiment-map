"""Count Yelp reviews by year and by ZIP-year, streaming from the 4 GB tar.

review.json is 5.3 GB, so it is never extracted to disk — tarfile streams it and
we keep only the two fields needed to size a study window: date and business_id
(mapped to ZIP via the business file).

Writes data/interim/review_counts_by_zip_year.csv and prints a year summary.
"""

import json
import re
import tarfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAR = ROOT / "Yelp JSON" / "yelp_dataset.tar"
BUSINESS = ROOT / "data" / "raw" / "yelp_academic_dataset_business.json"
OUT = ROOT / "data" / "interim" / "review_counts_by_zip_year.csv"

US_ZIP = re.compile(r"\d{5}")
MEMBER = "yelp_academic_dataset_review.json"


def business_zips():
    z = {}
    with open(BUSINESS) as f:
        for line in f:
            b = json.loads(line)
            pc = (b.get("postal_code") or "").strip()
            if US_ZIP.fullmatch(pc):
                z[b["business_id"]] = pc
    return z


def main():
    bz = business_zips()
    print(f"{len(bz):,} businesses with US ZIPs", flush=True)

    by_year = Counter()
    by_zip_year = Counter()
    n = skipped = 0

    with tarfile.open(TAR) as tf:
        fh = tf.extractfile(MEMBER)
        for line in fh:
            n += 1
            if n % 1_000_000 == 0:
                print(f"  {n:,} reviews scanned", flush=True)
            try:
                r = json.loads(line)
            except ValueError:
                continue
            z = bz.get(r.get("business_id"))
            if not z:
                skipped += 1
                continue
            year = (r.get("date") or "")[:4]
            by_year[year] += 1
            by_zip_year[(z, year)] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        f.write("zip5,year,reviews\n")
        for (z, y), c in sorted(by_zip_year.items()):
            f.write(f"{z},{y},{c}\n")

    print(f"\n{n:,} reviews total, {skipped:,} outside the US ZIP universe")
    print("\nreviews by year (US ZIPs only):")
    for y in sorted(by_year):
        print(f"  {y}  {by_year[y]:>9,}")

    # how many ZIPs clear useful thresholds in the COVID window
    print("\nCOVID window density (2019-2021):")
    win = Counter()
    for (z, y), c in by_zip_year.items():
        if y in ("2019", "2020", "2021"):
            win[z] += c
    counts = sorted(win.values(), reverse=True)
    print(f"  ZIPs with any reviews: {len(counts):,}")
    for t in (100, 250, 500, 1000, 2500):
        print(f"  ZIPs with >={t}: {sum(1 for c in counts if c >= t):,}")


if __name__ == "__main__":
    main()
