"""Extract review counts and compute business participation & capital efficiency
for expanded projects (Tier 1 & Tier 2).

Projects:
  Tier 1 (Within 5 study metros):
    - Tampa Riverwalk (Tampa, FL)
    - Schuylkill Banks Boardwalk (Philadelphia, PA)
    - The Rail Park Phase 1 (Philadelphia, PA)
    - Crescent Park (New Orleans, LA)
  Tier 2 (New metros in Yelp dataset):
    - Indianapolis Cultural Trail (Indianapolis, IN)
    - Gateway Arch Park / CityArchRiver (Saint Louis, MO)

Streams yelp_academic_dataset_review.json from Yelp JSON/yelp_dataset.tar in a single pass.
Outputs:
  - docs/coursework/milestone-2-eda/study_data/expansion_projects_metrics.csv
"""
import json
import math
import os
import tarfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
STUDY_DATA = ROOT / "docs" / "coursework" / "milestone-2-eda" / "study_data"
TAR_PATH = ROOT / "Yelp JSON" / "yelp_dataset.tar"
BIZ_PATH = ROOT / "data" / "raw" / "yelp_academic_dataset_business.json"

PROJECTS = {
    "Tampa Riverwalk": {
        "coords": (27.9461, -82.4599),
        "state": "FL",
        "city": "Tampa",
        "project_type": "Waterfront trail / linear promenade",
        "cost_millions": 32.0,
        "opening": "2015-03-27",
        "pre": [2012, 2013],
        "post": [2016, 2017],
        "tier": "Tier 1",
    },
    "Schuylkill Boardwalk": {
        "coords": (39.9482, -75.1812),
        "state": "PA",
        "city": "Philadelphia",
        "project_type": "Over-water boardwalk / linear trail",
        "cost_millions": 18.0,
        "opening": "2014-10-02",
        "pre": [2011, 2012],
        "post": [2015, 2016],
        "tier": "Tier 1",
    },
    "The Rail Park": {
        "coords": (39.9592, -75.1578),
        "state": "PA",
        "city": "Philadelphia",
        "project_type": "Elevated viaduct linear greenway",
        "cost_millions": 10.3,
        "opening": "2018-06-14",
        "pre": [2015, 2016],
        "post": [2019, 2020],
        "tier": "Tier 1",
    },
    "Crescent Park": {
        "coords": (29.9631, -90.0452),
        "state": "LA",
        "city": "New Orleans",
        "project_type": "Linear riverfront park",
        "cost_millions": 31.2,
        "opening": "2014-07-01",
        "pre": [2011, 2012],
        "post": [2015, 2016],
        "tier": "Tier 1",
    },
    "Indianapolis Cultural Trail": {
        "coords": (39.7684, -86.1581),
        "state": "IN",
        "city": "Indianapolis",
        "project_type": "8-mile urban bicycle / pedestrian greenway",
        "cost_millions": 63.0,
        "opening": "2013-05-10",
        "pre": [2010, 2011],
        "post": [2014, 2015],
        "tier": "Tier 2",
    },
    "Gateway Arch Park": {
        "coords": (38.6247, -90.1848),
        "state": "MO",
        "city": "Saint Louis",
        "project_type": "Civic park & highway lid",
        "cost_millions": 380.0,
        "opening": "2015-11-20",
        "pre": [2012, 2013],
        "post": [2016, 2017],
        "tier": "Tier 2",
    },
}


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def identify_cohorts():
    """Identify near and farther businesses for each candidate project."""
    biz_map = {}  # bid -> list of (project_name, area, distance_m)
    with open(BIZ_PATH, "r", encoding="utf-8") as f:
        for line in f:
            b = json.loads(line)
            lat, lon = b.get("latitude"), b.get("longitude")
            if lat is None or lon is None:
                continue
            state = b.get("state", "")
            bcity = (b.get("city") or "").lower()
            bid = b["business_id"]

            for pname, spec in PROJECTS.items():
                if state == spec["state"]:
                    d = haversine(lat, lon, spec["coords"][0], spec["coords"][1])
                    if d <= 500:
                        biz_map.setdefault(bid, []).append((pname, "Near", d))
                    elif 1500 < d <= 8000:
                        if spec["city"].lower() in bcity or bcity in spec["city"].lower() or state in ["IN", "MO"]:
                            biz_map.setdefault(bid, []).append((pname, "Farther", d))
    return biz_map


def scan_reviews(biz_map):
    """Scan Yelp reviews from tar in a single streaming pass and aggregate per business-year."""
    # (project_name, area, bid, year) -> review_count
    biz_year_counts = defaultdict(int)
    total_scanned = 0
    matched_reviews = 0

    print("Opening tar archive for single-pass review streaming...", flush=True)
    with tarfile.open(TAR_PATH, "r|*") as tar:
        for mem in tar:
            if mem.name.endswith("yelp_academic_dataset_review.json"):
                f = tar.extractfile(mem)
                for line in f:
                    total_scanned += 1
                    if total_scanned % 1000000 == 0:
                        print(f"  Scanned {total_scanned:,} reviews... ({matched_reviews:,} matched)", flush=True)
                    # Quick check: does the line contain any matched business_id?
                    # Faster: json load
                    r = json.loads(line)
                    bid = r.get("business_id")
                    if bid in biz_map:
                        yr_str = r.get("date", "")[:4]
                        if yr_str.isdigit():
                            yr = int(yr_str)
                            for pname, area, _ in biz_map[bid]:
                                biz_year_counts[(pname, area, bid, yr)] += 1
                                matched_reviews += 1
                break

    print(f"Done streaming: {total_scanned:,} total reviews scanned; {matched_reviews:,} assigned to study cohorts.")
    return biz_year_counts


def compute_metrics(biz_map, biz_year_counts):
    """Compute business participation, review DiD, and capital efficiency across all projects."""
    results = []

    for pname, spec in PROJECTS.items():
        pre_years = set(spec["pre"])
        post_years = set(spec["post"])
        cost = spec["cost_millions"]

        # Collect all businesses in Near and Farther
        near_bids = {bid for bid, lst in biz_map.items() if any(p == pname and a == "Near" for p, a, _ in lst)}
        far_bids = {bid for bid, lst in biz_map.items() if any(p == pname and a == "Farther" for p, a, _ in lst)}

        def tally_cohort(bids):
            pre_counts = {}
            post_counts = {}
            for b in bids:
                pr = sum(biz_year_counts.get((pname, "Near" if b in near_bids else "Farther", b, y), 0) for y in pre_years)
                po = sum(biz_year_counts.get((pname, "Near" if b in near_bids else "Farther", b, y), 0) for y in post_years)
                pre_counts[b] = pr
                post_counts[b] = po
            return pre_counts, post_counts

        near_pre_c, near_post_c = tally_cohort(near_bids)
        far_pre_c, far_post_c = tally_cohort(far_bids)

        # Business growth stats
        n_listings = len(near_bids)
        n_base_active = sum(1 for c in near_pre_c.values() if c > 0)
        n_post_active = sum(1 for c in near_post_c.values() if c > 0)
        n_active_both = sum(1 for b in near_bids if near_pre_c[b] > 0 and near_post_c[b] > 0)
        n_post_only = sum(1 for b in near_bids if near_pre_c[b] == 0 and near_post_c[b] > 0)
        n_base_only = sum(1 for b in near_bids if near_pre_c[b] > 0 and near_post_c[b] == 0)

        far_base_active = sum(1 for c in far_pre_c.values() if c > 0)
        far_post_active = sum(1 for c in far_post_c.values() if c > 0)

        near_biz_growth_pct = ((n_post_active / n_base_active) - 1.0) * 100.0 if n_base_active > 0 else 0.0
        far_biz_growth_pct = ((far_post_active / far_base_active) - 1.0) * 100.0 if far_base_active > 0 else 0.0
        rel_biz_growth_pct = (((n_post_active / n_base_active) / (far_post_active / far_base_active)) - 1.0) * 100.0 if (n_base_active > 0 and far_base_active > 0 and far_post_active > 0) else 0.0

        counterfactual_n_biz = n_base_active * (1.0 + far_biz_growth_pct / 100.0)
        net_biz_added = (n_post_active - n_base_active) - (counterfactual_n_biz - n_base_active)
        ce_biz = net_biz_added / cost

        # Engagement review stats (among baseline active businesses)
        # DiD on baseline active businesses
        near_base_bids = [b for b in near_bids if near_pre_c[b] > 0]
        far_base_bids = [b for b in far_bids if far_pre_c[b] > 0]

        mean_near_pre = sum(near_pre_c[b] for b in near_base_bids) / len(near_base_bids) if near_base_bids else 0.0
        mean_near_post = sum(near_post_c[b] for b in near_base_bids) / len(near_base_bids) if near_base_bids else 0.0

        mean_far_pre = sum(far_pre_c[b] for b in far_base_bids) / len(far_base_bids) if far_base_bids else 0.0
        mean_far_post = sum(far_post_c[b] for b in far_base_bids) / len(far_base_bids) if far_base_bids else 0.0

        delta_near = mean_near_post - mean_near_pre
        delta_far = mean_far_post - mean_far_pre
        did_per_biz = delta_near - delta_far

        pairs = len(near_base_bids)
        low_support = pairs < 20

        total_base_vol = mean_near_pre * pairs
        net_vol_gain = did_per_biz * pairs

        ce_abs = net_vol_gain / cost
        rel_rev_growth_pct = (((mean_near_post / mean_near_pre) / (mean_far_post / mean_far_pre)) - 1.0) * 100.0 if (mean_near_pre > 0 and mean_far_pre > 0 and mean_far_post > 0) else 0.0
        ce_rel = rel_rev_growth_pct / cost
        ce_norm = (net_vol_gain / (total_base_vol * cost)) * 100.0 if (total_base_vol > 0 and cost > 0) else 0.0

        results.append({
            "project": pname,
            "tier": spec["tier"],
            "city": spec["city"],
            "state": spec["state"],
            "project_type": spec["project_type"],
            "cost_millions": cost,
            "opening": spec["opening"],
            "pre_years": f"{spec['pre'][0]}-{spec['pre'][1]}",
            "post_years": f"{spec['post'][0]}-{spec['post'][1]}",
            "pairs": pairs,
            "low_support": low_support,
            "near_pre_mean": round(mean_near_pre, 2),
            "near_post_mean": round(mean_near_post, 2),
            "control_pre_mean": round(mean_far_pre, 2),
            "control_post_mean": round(mean_far_post, 2),
            "did_per_pair": round(did_per_biz, 2),
            "total_baseline_near_vol": round(total_base_vol, 1),
            "net_volume_gain": round(net_vol_gain, 1),
            "ce_abs_per_million": round(ce_abs, 2),
            "ce_rel_pct_per_million": round(ce_rel, 4),
            "ce_norm_pct_per_million": round(ce_norm, 4),
            # Business growth
            "listings_500m": n_listings,
            "biz_500m_pre": n_base_active,
            "biz_500m_post": n_post_active,
            "biz_500m_net_gain": round(net_biz_added, 2),
            "biz_500m_growth_pct": round(near_biz_growth_pct, 2),
            "biz_500m_rel_growth_pct": round(rel_biz_growth_pct, 2),
            "ce_biz_per_million": round(ce_biz, 3),
        })

    return pd.DataFrame(results)


def main():
    print("Step 1: Identifying business cohorts for Tier 1 & Tier 2 candidate projects...")
    biz_map = identify_cohorts()
    print(f"Mapped {len(biz_map):,} unique businesses to project buffer zones.")

    print("\nStep 2: Streaming reviews from yelp_dataset.tar...")
    biz_year_counts = scan_reviews(biz_map)

    print("\nStep 3: Computing business growth and capital efficiency...")
    df = compute_metrics(biz_map, biz_year_counts)

    out_path = STUDY_DATA / "expansion_projects_metrics.csv"
    df.to_csv(out_path, index=False)
    print(f"\nWrote results to {out_path}:\n")
    print(df[["project", "tier", "cost_millions", "pairs", "did_per_pair", "ce_abs_per_million", "biz_500m_pre", "biz_500m_post", "ce_biz_per_million", "low_support"]].to_string(index=False))


if __name__ == "__main__":
    main()
