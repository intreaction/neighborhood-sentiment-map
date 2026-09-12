"""Derive the ZIP universe for the study from the Yelp business file.

Every downstream pull (USASpending awards, TIGER/ZCTA boundaries) is scoped to
the ZIPs where Yelp actually has businesses, so this runs first. Canadian
postal codes in the Yelp data (Alberta) are dropped — USASpending is US-only.
"""

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUSINESS = ROOT / "data" / "raw" / "yelp_academic_dataset_business.json"
OUT = ROOT / "data" / "interim" / "yelp_zips.txt"
SUMMARY = ROOT / "data" / "interim" / "yelp_zip_summary.csv"

US_ZIP = re.compile(r"\d{5}")


def main():
    businesses = Counter()
    reviews = Counter()
    total = 0
    with open(BUSINESS) as f:
        for line in f:
            b = json.loads(line)
            total += 1
            z = (b.get("postal_code") or "").strip()
            if US_ZIP.fullmatch(z):
                businesses[z] += 1
                reviews[z] += b.get("review_count", 0)

    zips = sorted(businesses)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(zips) + "\n")

    with open(SUMMARY, "w") as f:
        f.write("zip,businesses,review_count\n")
        for z in sorted(zips, key=lambda z: -reviews[z]):
            f.write(f"{z},{businesses[z]},{reviews[z]}\n")

    print(f"{total:,} businesses read")
    print(f"{len(zips):,} US ZIPs -> {OUT}")
    print(f"{sum(businesses.values()):,} businesses, {sum(reviews.values()):,} reviews in scope")


if __name__ == "__main__":
    main()
