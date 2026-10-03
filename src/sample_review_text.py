"""Create a local-only stratified Yelp text sample for the course notebook.

The sample contains full review text and is intentionally Git-ignored.
"""

import gzip
import json
import tarfile
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent.parent
BUSINESSES = ROOT / "data/raw/yelp_academic_dataset_business.json"
REVIEWS = ROOT / "Yelp JSON/yelp_dataset.tar"
OUT = ROOT / "data/derived/review_text_weak_labels.json.gz"
METROS = {("AZ", "tucson"): "Tucson", ("PA", "philadelphia"): "Philadelphia",
          ("FL", "tampa"): "TampaBay", ("TN", "nashville"): "Nashville",
          ("LA", "new orleans"): "NewOrleans"}


def build(limit_per_metro=1000, seed=509):
    if OUT.exists():
        return OUT
    business_metro = {}
    with BUSINESSES.open(encoding="utf-8") as f:
        for line in f:
            b = json.loads(line)
            metro = METROS.get((b.get("state"), (b.get("city") or "").lower()))
            if metro:
                business_metro[b["business_id"]] = metro
    rng = np.random.default_rng(seed)
    seen = defaultdict(int)
    samples = defaultdict(list)
    with tarfile.open(REVIEWS, "r|*") as tar:
        for member in tar:
            if member.name.endswith("yelp_academic_dataset_review.json"):
                for line in tar.extractfile(member):
                    r = json.loads(line)
                    metro = business_metro.get(r["business_id"])
                    if metro is None or r.get("stars") not in (1, 2, 4, 5):
                        continue
                    seen[metro] += 1
                    item = {"business_id": r["business_id"], "metro": metro,
                            "stars": r["stars"], "text": r["text"]}
                    bucket = samples[metro]
                    if len(bucket) < limit_per_metro:
                        bucket.append(item)
                    else:
                        replacement = int(rng.integers(0, seen[metro]))
                        if replacement < limit_per_metro:
                            bucket[replacement] = item
                break
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt", encoding="utf-8") as f:
        json.dump([row for metro in sorted(samples) for row in samples[metro]], f, separators=(",", ":"))
    return OUT


if __name__ == "__main__":
    print(build())
