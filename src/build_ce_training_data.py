"""Build one comparable, project-level Yelp engagement outcome per investment.

Run from the repository root with ``python3 src/build_ce_training_data.py``.
The same 500 m near and 1.5–8 km comparison bands and the same all-listing
growth-adjusted review target are used for every project. Six expansion sites
only have center-point proxies; the output marks them as such.
"""

import csv
import json
import math
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from matplotlib.path import Path as PlotPath
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT / "docs/coursework/milestone-2-eda/study_data"
OUT = ROOT / "data/derived/ce_project_training.csv"
SUN_COHORTS = ROOT / "data/derived/sun_link_full_route_cohorts.csv"
BUSINESSES = ROOT / "data/raw/yelp_academic_dataset_business.json"
REVIEWS = ROOT / "Yelp JSON/yelp_dataset.tar"

# Existing expansion coordinates are center proxies, not project footprints.
EXPANSION_CENTERS = {
    "Tampa Riverwalk": (27.9461, -82.4599),
    "Schuylkill Boardwalk": (39.9482, -75.1812),
    "The Rail Park": (39.9592, -75.1578),
    "Crescent Park": (29.9631, -90.0452),
    "Indianapolis Cultural Trail": (39.7684, -86.1581),
    "Gateway Arch Park": (38.6247, -90.1848),
}
EXTRA = {
    "Indianapolis Cultural Trail": dict(city="Indianapolis", state="IN", cost_millions=63.0,
        project_type="Urban trail", opening="2013-05-10", pre=[2010, 2011],
        post=[2014, 2015], early=[2008, 2009]),
    "Gateway Arch Park": dict(city="Saint Louis", state="MO", cost_millions=380.0,
        project_type="Civic park", opening="2015-11-20", pre=[2012, 2013],
        post=[2016, 2017], early=[2010, 2011]),
}
GEO_FILES = {
    "Lafitte": "Lafitte.geojson",
    "Sun Link": "Sun_Link.geojson",
    "Dilworth Park": "Dilworth_Park.geojson",
    "Water Works Park": "Water_Works_Park.geojson",
    "Riverfront / Ascend": "Riverfront_Ascend.geojson",
}
STATE = {"New Orleans": "LA", "Tucson": "AZ", "Philadelphia": "PA",
         "Tampa": "FL", "Nashville": "TN", "Indianapolis": "IN", "Saint Louis": "MO"}


def normalized_city(city):
    return "".join(ch for ch in (city or "").lower() if ch.isalnum())


def xy(lon, lat, lon0, lat0):
    return np.column_stack(((np.asarray(lon) - lon0) * 111_320 * math.cos(math.radians(lat0)),
                            (np.asarray(lat) - lat0) * 111_320))


def densify(points, step=10):
    chunks = []
    for a, b in zip(points[:-1], points[1:]):
        n = max(1, math.ceil(float(np.linalg.norm(b - a)) / step))
        chunks.append(a + np.linspace(0, 1, n, endpoint=False)[:, None] * (b - a))
    return np.vstack(chunks) if chunks else points


def distances(project, locations):
    """Local metre projection; sampled boundary error is below five metres."""
    center = EXPANSION_CENTERS.get(project["project"])
    if center:
        lat0, lon0 = center
        return np.linalg.norm(xy(locations[:, 0], locations[:, 1], lon0, lat0), axis=1)

    raw = json.loads((STUDY / GEO_FILES[project["project"]]).read_text())
    geom = raw.get("geometry") or raw["features"][0]["geometry"]
    if geom["type"] == "MultiLineString":
        rings = geom["coordinates"]
        polygon = False
    elif geom["type"] == "Polygon":
        rings = geom["coordinates"]
        polygon = True
    else:
        raise ValueError(geom["type"])
    coords = np.vstack([np.asarray(r) for r in rings])
    lon0, lat0 = np.mean(coords, axis=0)
    projected = [xy(np.asarray(r)[:, 0], np.asarray(r)[:, 1], lon0, lat0) for r in rings]
    outlines = []
    for r in projected:
        closed = np.vstack([r, r[0]]) if polygon and not np.array_equal(r[0], r[-1]) else r
        outlines.append(densify(closed))
    points = xy(locations[:, 0], locations[:, 1], lon0, lat0)
    nearest = cKDTree(np.vstack(outlines)).query(points, workers=-1)[0]
    if polygon:
        inside = PlotPath(projected[0]).contains_points(points)
        for hole in projected[1:]:
            inside &= ~PlotPath(hole).contains_points(points)
        nearest[inside] = 0
    return nearest


def read_projects():
    registry = json.loads((STUDY / "project_registry.json").read_text())
    projects = {p["project"]: dict(p) for p in registry}
    projects.update({k: dict(v, project=k) for k, v in EXTRA.items()})
    for p in projects.values():
        p["state"] = STATE[p["city"]]
        p["geometry_quality"] = "center_proxy" if p["project"] in EXPANSION_CENTERS else "mapped_footprint"
    return list(projects.values())


def read_businesses(projects):
    cities = {(p["state"], normalized_city(p["city"])) for p in projects}
    by_city = defaultdict(list)
    sun_ids = {row["business_id"] for row in csv.DictReader(SUN_COHORTS.open(newline=""))}
    sun_businesses = {}
    with BUSINESSES.open(encoding="utf-8") as handle:
        for line in handle:
            b = json.loads(line)
            if b["business_id"] in sun_ids:
                sun_businesses[b["business_id"]] = b
            key = (b.get("state"), normalized_city(b.get("city")))
            if key[1] == "stlouis":
                key = (key[0], "saintlouis")
            if key in cities and isinstance(b.get("latitude"), (int, float)) and isinstance(b.get("longitude"), (int, float)):
                by_city[key].append(b)
    assert len(sun_businesses) == len(sun_ids), "Sun Link cohort IDs must resolve in Yelp business data"
    return by_city, sun_businesses


def cohorts(projects, by_city, sun_businesses):
    assignment = defaultdict(list)
    inventories = {}
    for project in projects:
        name = project["project"]
        if name == "Sun Link":
            inventory = {"near": [], "far": []}
            for row in csv.DictReader(SUN_COHORTS.open(newline="")):
                inventory[row["band"]].append(sun_businesses[row["business_id"]])
                assignment[row["business_id"]].append((name, row["band"]))
            assert len(inventory["near"]) == 717 and len(inventory["far"]) == 4151
            inventories[name] = inventory
            print("Sun Link: 717 near; 4151 comparison (full route inventory)", flush=True)
            continue
        businesses = by_city[(project["state"], normalized_city(project["city"]))]
        locations = np.array([(b["longitude"], b["latitude"]) for b in businesses])
        d = distances(project, locations)
        inventory = {"near": [], "far": []}
        for b, distance in zip(businesses, d):
            band = "near" if distance <= 500 else "far" if 1500 < distance <= 8000 else None
            if band:
                assignment[b["business_id"]].append((name, band))
                inventory[band].append(b)
        inventories[name] = inventory
        print(f'{name}: {len(inventory["near"])} near; {len(inventory["far"])} comparison ({project["geometry_quality"]})', flush=True)
    return assignment, inventories


def review_counts(assignments, projects):
    years = {p["project"]: set(p["pre"] + p["post"] + p["early"]) for p in projects}
    totals = Counter()
    business_counts = Counter()
    scanned = 0
    with tarfile.open(REVIEWS, "r|*") as tar:
        for member in tar:
            if member.name.endswith("yelp_academic_dataset_review.json"):
                for line in tar.extractfile(member):
                    scanned += 1
                    review = json.loads(line)
                    bid = review["business_id"]
                    if bid not in assignments:
                        continue
                    year = int(review["date"][:4])
                    for name, band in assignments[bid]:
                        if year in years[name]:
                            totals[(name, band, year)] += 1
                            business_counts[(name, band, bid, year)] += 1
                    if scanned % 1_000_000 == 0:
                        print(f"Scanned {scanned:,} reviews", flush=True)
                break
    print(f"Scanned {scanned:,} Yelp reviews total", flush=True)
    return totals, business_counts


def make_rows(projects, inventories, totals, business_counts):
    rows = []
    for p in projects:
        name = p["project"]
        def total(band, period):
            return sum(totals[(name, band, y)] for y in p[period])
        near_pre, near_post = total("near", "pre"), total("near", "post")
        far_pre, far_post = total("far", "pre"), total("far", "post")
        near_early, far_early = total("near", "early"), total("far", "early")
        near = inventories[name]["near"]
        far = inventories[name]["far"]
        baseline_reviewed = sum(any(business_counts[(name, "near", b["business_id"], y)] for y in p["pre"]) for b in near)
        food = sum(any(term in (b.get("categories") or "").lower() for term in ("restaurants", "food", "bars", "coffee")) for b in near)
        ratio = far_post / far_pre if far_pre else float("nan")
        net = near_post - near_pre * ratio if far_pre else float("nan")
        rows.append(dict(project=name, city=p["city"], state=p["state"], project_type=p["project_type"],
                         geometry_quality=p["geometry_quality"], cost_millions=p["cost_millions"],
                         opening=p["opening"], pre_years="/".join(map(str, p["pre"])),
                         post_years="/".join(map(str, p["post"])), near_listings=len(near), far_listings=len(far),
                         near_baseline_reviewed=baseline_reviewed, near_food_share=food / len(near) if near else float("nan"),
                         near_early_reviews=near_early, far_early_reviews=far_early,
                         near_pre_reviews=near_pre, far_pre_reviews=far_pre,
                         near_post_reviews=near_post, far_post_reviews=far_post,
                         far_growth_factor=ratio, expected_near_post=near_pre * ratio,
                         net_review_difference=net, ce_reviews_per_million=net / float(p["cost_millions"])))
    return rows


def main():
    projects = read_projects()
    by_city, sun_businesses = read_businesses(projects)
    assignments, inventories = cohorts(projects, by_city, sun_businesses)
    totals, business_counts = review_counts(assignments, projects)
    rows = make_rows(projects, inventories, totals, business_counts)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT} ({len(rows)} projects)")


if __name__ == "__main__":
    main()
