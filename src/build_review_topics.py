"""Tag all study reviews with transparent, overlapping keyword themes.

Stream raw reviews in the same order as build_sentiment_panel.py and reconcile
each retained row against its existing score by ZIP, metro, date, quarter and
stars. Fail closed on any mismatch; do not silently attach scores to other text.
These rules measure mentions, not aspect sentiment or validated classifications.
Only compact aggregates and seeded short excerpt samples enter the offline map.
"""
import csv
import json
import random
import re
import tarfile
from collections import defaultdict
from pathlib import Path

from build_sentiment_panel import load_business_index, quarter_of, TAR, MEMBER

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
TOPICS = {
    "access": {"label": "Access & parking", "terms": r"\b(?:parking|parked|walkable|walkability|sidewalks?|transit|bus stop|bike racks?|wheelchair|accessible|accessibility)\b", "hint": "Parking, sidewalks, transit, walkability and accessibility."},
    "surroundings": {"label": "Surroundings", "terms": r"\b(?:neighborhood|neighbourhood|surroundings|street lighting|street lights|construction|potholes?|graffiti|unsafe|safety)\b", "hint": "Neighborhoods, construction, street conditions and safety mentions."},
    "cleanliness": {"label": "Cleanliness", "terms": r"\b(?:clean|cleanliness|dirty|filthy|sanitary|unsanitary|litter|trash|garbage|restrooms?|bathrooms?)\b", "hint": "Cleanliness, trash, bathrooms and related conditions."},
    "value": {"label": "Price & value", "terms": r"\b(?:prices?|pricing|expensive|overpriced|affordable|cheap|value|worth the money|costly)\b", "hint": "Prices, affordability and value for money."},
    "service": {"label": "Service", "terms": r"\b(?:service|staff|servers?|waiters?|waitress(?:es)?|cashiers?|employees?|customer service)\b", "hint": "Staff, servers, employees and customer service."},
    "product": {"label": "Food & products", "terms": r"\b(?:food|meal|meals|dish|dishes|menu|taste|tasty|delicious|flavor|flavour|products?|merchandise)\b", "hint": "Food, meals, taste and products; all business types are retained."},
}


def classify(text):
    return [key for key, pattern in PATTERNS.items() if pattern.search(text)]


PATTERNS = {key: re.compile(t["terms"], re.I) for key, t in TOPICS.items()}


def main():
    biz = load_business_index()
    # Each topic cell is [review count, sum of compound, negative count].
    cells = defaultdict(lambda: defaultdict(lambda: [0, 0.0, 0]))
    stars = defaultdict(lambda: [0] * 5)
    samples, seen = defaultdict(list), defaultdict(int)
    rng = random.Random(20260908)
    n = tagged = 0
    with open(INTERIM / "reviews_5metro.csv") as scored, tarfile.open(TAR) as tf:
        scores = csv.DictReader(scored)
        for line in tf.extractfile(MEMBER):
            r = json.loads(line)
            hit = biz.get(r.get("business_id"))
            date = r.get("date", "")
            if not hit or not "2012" <= date[:4] <= "2021":
                continue
            z, metro, *_ = hit
            q = quarter_of(date)
            old = next(scores, None)
            expected = (z, metro, date[:10], q, int(r["stars"]))
            actual = None if old is None else (old["zip5"], old["metro"], old["date"], old["quarter"], int(old["stars"]))
            if actual != expected:
                raise ValueError(f"Review/score order mismatch at eligible row {n}: {actual} != {expected}")
            comp = float(old["compound"])
            text = r.get("text") or ""
            topics = classify(text)
            n += 1
            tagged += bool(topics)
            stars[(z, q)][int(r["stars"]) - 1] += 1
            for topic in topics:
                cell = cells[(z, q)][topic]
                cell[0] += 1
                cell[1] += comp
                cell[2] += comp <= -.05
                # Two examples per city/year/topic/polarity, selected by reservoir.
                polarity = "negative" if comp <= -.05 else "positive" if comp >= .05 else "neutral"
                key = (metro, date[:4], topic, polarity)
                seen[key] += 1
                bucket = samples[key]
                slot = len(bucket) if len(bucket) < 2 else rng.randrange(seen[key])
                if slot < 2:
                    match = PATTERNS[topic].search(text)
                    start = max(0, match.start() - 65)
                    excerpt = ("…" if start else "") + re.sub(r"\s+", " ", text[start:start + 240]).strip() + ("…" if start + 240 < len(text) else "")
                    example = {"zip": z, "metro": metro, "quarter": q, "topic": topic, "polarity": polarity, "compound": comp, "stars": int(r["stars"]), "text": excerpt}
                    if slot == len(bucket):
                        bucket.append(example)
                    else:
                        bucket[slot] = example
            if n % 500_000 == 0:
                print(f"{n:,} reviews reconciled and tagged", flush=True)
        if next(scores, None) is not None:
            raise ValueError("Extra rows remain in the score file")

    panel = {}
    for (z, q), histogram in stars.items():
        zi = panel.setdefault(z, {})
        zi[q] = {"stars": histogram, "topics": {t: [c[0], round(c[1], 4), c[2]] for t, c in cells[(z, q)].items()}}
    out = {"method": "Overlapping keyword rules on all study reviews; whole-review VADER scores, not aspect sentiment.", "nReviews": n, "nTagged": tagged, "seed": 20260908, "topics": TOPICS, "panel": panel, "examples": [r for bucket in samples.values() for r in bucket]}
    target = INTERIM / "review_topics.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(out, separators=(",", ":")))
    temp.replace(target)
    print(f"{n:,} reviews · {tagged:,} with ≥1 tag · {len(out['examples']):,} excerpts → {target}", flush=True)


if __name__ == "__main__":
    main()
