"""Build the self-contained capital-efficiency scenario page from tracked benchmark data."""

import csv
import json
from pathlib import Path
from sun_link_corridor import compute as compute_sun_link_corridor

ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT / "docs" / "coursework" / "milestone-2-eda" / "study_data"
OUT = ROOT / "web" / "reference.html"
PROJECTS = ("Dilworth Park", "Lafitte", "Riverfront / Ascend", "Sun Link", "Water Works Park")
CITY_LABELS = {
    "Philadelphia": "Philadelphia", "NewOrleans": "New Orleans",
    "Nashville": "Nashville", "Tucson": "Tucson", "TampaBay": "Tampa Bay",
}
METRO_FOR_CITY = {label: key for key, label in CITY_LABELS.items()}
METRO_FOR_CITY["Tampa"] = "TampaBay"


def number(value):
    return float(value) if value not in (None, "") else None


def main():
    registry = {r["project"]: r for r in json.loads((STUDY / "project_registry.json").read_text())}
    with (STUDY / "capital_efficiency.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    with (STUDY / "experience.csv").open(newline="") as f:
        experience = list(csv.DictReader(f))
    with (STUDY / "topic_prevalence.csv").open(newline="") as f:
        topics = list(csv.DictReader(f))
    with (STUDY / "business_growth.csv").open(newline="") as f:
        business_growth = list(csv.DictReader(f))
    trained_model = json.loads((ROOT / "data" / "derived" / "ce_trained_model.json").read_text())
    with (ROOT / "data" / "derived" / "ce_project_training.csv").open(newline="") as f:
        trained_projects = {
            r["project"]: {"listings": int(r["near_listings"]),
                           "baseline_reviewed": int(r["near_baseline_reviewed"]),
                           "pre_reviews_per_active": float(r["near_pre_reviews"]) / int(r["near_baseline_reviewed"]),
                           "geometry_quality": r["geometry_quality"]}
            for r in csv.DictReader(f)
        }
    with (STUDY / "sun_coverage.csv").open(newline="") as f:
        sun_link_coverage = {
            int(r["radius_m"]): {"listed": int(r["listed_businesses"]),
                                  "baseline": int(r["baseline_reviewed"]),
                                  "post": int(r["post_reviewed"])}
            for r in csv.DictReader(f)
        }
    analogues = []
    for name in PROJECTS:
        project = registry[name]
        measures = []
        for row in rows:
            if row["project"] != name or row["comparison_method"] != "matched_pairs" or row["metric"] != "reviews":
                continue
            measures.append({
                "radius": int(row["radius_m"]), "income": row["income_group"],
                "pairs": int(row["pairs"]), "low_support": row["low_support"] == "True",
                "did_per_pair": number(row["did_per_pair"]),
                "near_pre_mean": number(row["near_pre_mean"]),
                "near_post_mean": number(row["near_post_mean"]),
                "control_pre_mean": number(row["control_pre_mean"]),
                "control_post_mean": number(row["control_post_mean"]),
                "observed_ce": number(row["ce_abs_per_million"]),
                "observed_net_reviews": number(row["net_volume_gain"]),
            })
        sentiment = [{"radius": int(r["radius_m"]), "income": r["income_group"],
                      "pairs": int(r["pairs"]), "contrast": number(r["contrast"]),
                      "low_support": r["low_support"] == "True"}
                     for r in experience if name != "Sun Link" and r["project"] == name
                     and r["metric"] == "compound"]
        local_identity = [r for r in topics if r["project"] == name and
                          name != "Sun Link" and
                          r["category"] == "Location/local identity (mixed)"]
        topic_shift = None
        if len(local_identity) == 4:
            share = {(r["area"], r["period"]): number(r["prevalence_pct"])
                     for r in local_identity}
            if all(key in share for key in (("near", "pre"), ("near", "post"),
                                             ("comparison", "pre"), ("comparison", "post"))):
                topic_shift = (share[("near", "post")] - share[("near", "pre")]
                               - share[("comparison", "post")] + share[("comparison", "pre")])
        growth = {r["area"]: r for r in business_growth if r["project"] == name}
        participation = None
        if "Near" in growth and "Farther" in growth:
            near, farther = growth["Near"], growth["Farther"]
            baseline = int(near["baseline_active"])
            post = int(near["post_active"])
            farther_baseline = int(farther["baseline_active"])
            farther_post = int(farther["post_active"])
            participation = {
                "baseline": baseline, "post": post,
                "listings": int(near["listings"]),
                "low_support": baseline < 20 or farther_baseline < 20,
                "net": post - baseline * farther_post / farther_baseline,
                "ce": (post - baseline * farther_post / farther_baseline)
                      / number(project["cost_millions"]),
            }
        analogues.append({
            "name": name, "type": project["project_type"], "city": project["city"],
            "metro": METRO_FOR_CITY[project["city"]],
            "cost_millions": number(project["cost_millions"]),
            "opening": project["opening"], "rows": measures,
            "sentiment_rows": sentiment, "topic_shift_pp": topic_shift,
            "participation": participation,
            "route_coverage": sun_link_coverage if name == "Sun Link" else None,
            "corridor_rows": [
                {"radius": r["radius_m"], "income": r["income_group"],
                 "pairs": r["near_listings"], "low_support": r["low_support"],
                 "did_per_pair": r["net_per_listing"],
                 "observed_ce": r["ce_per_million"],
                 "observed_net_reviews": r["net_review_difference"],
                 "baseline_reviewed": r["baseline_reviewed"],
                 "raw_review_gain": r["raw_review_gain"],
                 "near_pre_reviews": r["near_pre_reviews"],
                 "near_post_reviews": r["near_post_reviews"],
                 "comparison_growth_pct": r["comparison_growth_pct"]}
                for r in compute_sun_link_corridor(STUDY) if name == "Sun Link"
            ],
        })

    metro_zips = json.loads((ROOT / "data" / "interim" / "metro_zips.json").read_text())
    metro_of = {zip5: city for city, zips in metro_zips.items() for zip5 in zips}
    geometry = json.loads((ROOT / "data" / "interim" / "zcta_boundaries.min.geojson").read_text())
    mapped = {f["properties"]["zip"] for f in geometry["features"]}
    with (ROOT / "data" / "interim" / "yelp_zip_summary.csv").open(newline="") as f:
        summary = {r["zip"]: r for r in csv.DictReader(f)}
    population = json.loads((ROOT / "data" / "population_2020.json").read_text())["records"]
    areas = []
    for zip5 in sorted(mapped & metro_of.keys()):
        city = metro_of[zip5]
        areas.append({
            "zip": zip5, "city": city, "businesses_zip": int(summary.get(zip5, {}).get("businesses", 0)),
            "reviews_zip": int(summary.get(zip5, {}).get("review_count", 0)),
            "population": population.get(zip5, {}).get("population"),
        })
    payload = {"analogues": analogues, "areas": areas, "cities": CITY_LABELS,
               "trained_model": trained_model, "trained_projects": trained_projects}
    page = (ROOT / "src" / "model_template.html").read_text()
    page = page.replace("__MODEL_DATA__", json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c"))
    page = page.replace("__MODEL_MATH__", (ROOT / "src" / "model_math.js").read_text())
    OUT.write_text(page)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} KB; {len(analogues)} project references; {len(areas)} mapped ZIP areas)")


if __name__ == "__main__":
    main()
