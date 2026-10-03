"""Recalculate Sun Link engagement over every Yelp listing along its route.

This is a growth-adjusted, unmatched area comparison. It uses the existing
full-route near inventory and the 1.5–8 km Tucson comparison inventory, not
the earlier restricted matched extract. It must not be pooled with matched CE rows.
"""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT / "docs" / "coursework" / "milestone-2-eda" / "study_data"
OUT = STUDY / "sun_link_corridor_efficiency.csv"
COST_MILLIONS = 196.5
MIN_BASELINE_REVIEWED = 20


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def calculate_row(source, radius_m, income_group, baseline_reviewed):
    near_listings = int(source["near_businesses"])
    comparison_listings = int(source["comparison_businesses"])
    near_pre = float(source["near_pre"])
    near_post = float(source["near_post"])
    comparison_pre = float(source["comparison_pre"])
    comparison_post = float(source["comparison_post"])
    supported = (near_listings >= 20 and comparison_listings >= 20
                 and baseline_reviewed >= MIN_BASELINE_REVIEWED
                 and near_pre > 0 and comparison_pre > 0)
    growth_factor = comparison_post / comparison_pre if comparison_pre > 0 else None
    expected_post = near_pre * growth_factor if growth_factor is not None else None
    net = near_post - expected_post if expected_post is not None else None
    return {
        "project": "Sun Link",
        "comparison_method": "unmatched_growth_adjusted_corridor",
        "radius_m": radius_m,
        "income_group": income_group,
        "near_listings": near_listings,
        "baseline_reviewed": baseline_reviewed,
        "comparison_listings": comparison_listings,
        "near_pre_reviews": near_pre,
        "near_post_reviews": near_post,
        "comparison_pre_reviews": comparison_pre,
        "comparison_post_reviews": comparison_post,
        "expected_near_post_reviews": expected_post,
        "raw_review_gain": near_post - near_pre,
        "net_review_difference": net,
        "net_per_listing": net / near_listings if net is not None else None,
        "ce_per_million": net / COST_MILLIONS if net is not None else None,
        "near_growth_pct": 100 * (near_post / near_pre - 1) if near_pre > 0 else None,
        "comparison_growth_pct": 100 * (growth_factor - 1) if growth_factor is not None else None,
        "low_support": not supported,
    }


def compute(data_dir=STUDY):
    coverage = {int(r["radius_m"]): r for r in read_rows(data_dir / "sun_coverage.csv")}
    income_support = {r["income_group"]: r for r in read_rows(data_dir / "sun_income_support.csv")}
    results = []
    for source in read_rows(data_dir / "sun_scopes.csv"):
        if (source["radius_m"] in {"250", "500", "1000"}
                and source["scope"] == "All listed businesses"
                and source["metric"] == "reviews" and source["period"] == "post"):
            radius = int(source["radius_m"])
            results.append(calculate_row(source, radius, "All", int(coverage[radius]["baseline_reviewed"])))
    for source in read_rows(data_dir / "sun_income.csv"):
        if source["dimension"] == "income_group" and source["metric"] == "reviews":
            income = source["group"]
            results.append(calculate_row(source, 500, income, int(income_support[income]["baseline_reviewed"])))
    return sorted(results, key=lambda row: (row["radius_m"], row["income_group"] != "All", row["income_group"]))


def table_rows(rows):
    """Shape corridor results for the app comparison table without calling them pairs."""
    shaped = []
    for row in rows:
        near = row["near_listings"]
        baseline = row["near_pre_reviews"]
        relative = (100 * ((row["near_post_reviews"] / baseline) /
                           (row["comparison_post_reviews"] / row["comparison_pre_reviews"]) - 1)
                    if baseline > 0 and row["comparison_pre_reviews"] > 0 else None)
        shaped.append({
            "project": "Sun Link", "comparison_method": row["comparison_method"],
            "city": "Tucson", "project_type": "Streetcar / transit",
            "cost_millions": COST_MILLIONS, "radius_m": row["radius_m"],
            "income_group": row["income_group"], "metric": "reviews",
            "pairs": near, "low_support": row["low_support"],
            "did_per_pair": row["net_per_listing"],
            "net_volume_gain": row["net_review_difference"],
            "ce_abs_per_million": row["ce_per_million"],
            "ce_rel_pct_per_million": relative / COST_MILLIONS if relative is not None else None,
            "ce_norm_pct_per_million": 100 * row["net_review_difference"] / (baseline * COST_MILLIONS) if baseline > 0 else None,
        })
    return shaped


def main():
    rows = compute()
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} full-corridor comparisons)")


if __name__ == "__main__":
    main()
