"""Generate the interactive map page with all data inlined.

One self-contained, offline HTML file with SVG cartography, linked quarterly
charts and a selected-ZIP inspector. Edit map_template.html for the interface.
Run after the sentiment, award and geometry panels have been prepared.
"""

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from sun_link_corridor import compute as compute_sun_link_corridor, table_rows as sun_link_table_rows

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "web" / "atlas.html"

BOUNDARIES = INTERIM / "zcta_boundaries.min.geojson"
CONTEXT = INTERIM / "map_context.min.geojson"
STATES = INTERIM / "states.geojson"
LABELS = INTERIM / "place_labels.json"
EXTENTS = INTERIM / "metro_extents.json"
SENT_ZQ = INTERIM / "sentiment_zip_quarter.csv"
SENT_MQ = INTERIM / "sentiment_metro_quarter.csv"
AWARDS = INTERIM / "awards_zip_quarter.csv"
METRO_ZIPS = INTERIM / "metro_zips.json"
EVENTS = ROOT / "data" / "events.json"

STUDY_DATA = ROOT / "docs" / "coursework" / "milestone-2-eda" / "study_data"
MIN_REVIEWS = 30

PROJECT_FOOTPRINTS = {
    "Lafitte": ("Lafitte.geojson", "NewOrleans"),
    "Sun Link": ("Sun_Link.geojson", "Tucson"),
    "Dilworth Park": ("Dilworth_Park.geojson", "Philadelphia"),
    "Water Works Park": ("Water_Works_Park.geojson", "TampaBay"),
    "Riverfront / Ascend": ("Riverfront_Ascend.geojson", "Nashville"),
}

METRO_LABEL = {
    "Philadelphia": ("Philadelphia", "191", "PA"),
    "TampaBay": ("Tampa Bay", "336 / 337", "FL"),
    "NewOrleans": ("New Orleans", "701", "LA"),
    "Nashville": ("Nashville", "372", "TN"),
    "Tucson": ("Tucson", "857", "AZ"),
}


def quarters(start=2012, end=2021):
    return [f"{y}Q{q}" for y in range(start, end + 1) for q in (1, 2, 3, 4)]


def read_csv(path):
    if not path.exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def load_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def load_project_footprints():
    registry = {r["project"]: r for r in load_json(STUDY_DATA / "project_registry.json", [])}
    projects = []
    for name, (filename, metro) in PROJECT_FOOTPRINTS.items():
        source = load_json(STUDY_DATA / filename, None)
        if source is None or name not in registry:
            continue
        feature = source["features"][0] if source["type"] == "FeatureCollection" else source
        geometry = feature["geometry"]
        points = []

        def visit(value):
            if value and isinstance(value[0], (int, float)):
                points.append(value)
            else:
                for item in value:
                    visit(item)

        visit(geometry["coordinates"])
        if not points:
            continue
        center = [(min(p[0] for p in points) + max(p[0] for p in points)) / 2,
                  (min(p[1] for p in points) + max(p[1] for p in points)) / 2]
        projects.append({"name": name, "metro": metro, "opening": registry[name]["opening"],
                         "pre": registry[name]["pre"], "post": registry[name]["post"],
                         "geometry": geometry, "center": center})
    return projects


def main():
    QS = quarters()
    qi = {q: i for i, q in enumerate(QS)}
    N = len(QS)

    gj = json.loads(BOUNDARIES.read_text())
    metro_of = {z: m for m, zs in json.loads(METRO_ZIPS.read_text()).items() for z in zs}

    sent = defaultdict(lambda: [None] * N)
    nrev = defaultdict(lambda: [0] * N)
    pctneg = defaultdict(lambda: [None] * N)
    good = []
    for r in read_csv(SENT_ZQ):
        i = qi.get(r["quarter"])
        if i is None:
            continue
        n = int(r["n_reviews"])
        nrev[r["zip5"]][i] = n
        v = float(r["mean_compound"])
        # Keep the observed means so the explorer can apply its chosen threshold.
        # Only the fixed all-review color scale uses the default 30-review rule.
        sent[r["zip5"]][i] = round(v, 4)
        pctneg[r["zip5"]][i] = float(r["pct_negative"])
        if n >= MIN_REVIEWS:
            good.append(v)

    # Sentiment is overwhelmingly positive (VADER on reviews), so an absolute
    # -1..+1 ramp would paint every ZIP the same. Diverge about the median and
    # clip the arms at p5/p95 so the map shows relative standing, which is the
    # thing that actually varies.
    good.sort()
    med = statistics.median(good) if good else 0.6
    p5 = good[int(0.05 * (len(good) - 1))] if good else 0.3
    p95 = good[int(0.95 * (len(good) - 1))] if good else 0.8

    inv = defaultdict(lambda: [0.0] * N)
    for r in read_csv(AWARDS):
        if r["kind"] != "place":
            continue
        i = qi.get(r["quarter"])
        if i is None:
            continue
        inv[r["zip5"]][i] += float(r["obligations"])

    feats = []
    for f in gj["features"]:
        z = f["properties"]["zip"]
        m = metro_of.get(z)
        if not m:
            continue
        f["properties"] = {
            "zip": z, "metro": m,
            "s": sent.get(z, [None] * N),
            "n": nrev.get(z, [0] * N),
            "g": pctneg.get(z, [None] * N),
            "i": [round(v) for v in inv.get(z, [0.0] * N)],
        }
        feats.append(f)
    gj["features"] = feats

    series = {}
    for r in read_csv(SENT_MQ):
        i = qi.get(r["quarter"])
        if i is None:
            continue
        d = series.setdefault(r["metro"], {"sent": [None] * N, "n": [0] * N,
                                          "inv": [0.0] * N, "neg": [None] * N})
        d["sent"][i] = round(float(r["mean_compound"]), 4)
        d["n"][i] = int(r["n_reviews"])
        d["neg"][i] = float(r["pct_negative"])
    for r in read_csv(AWARDS):
        if r["kind"] != "place":
            continue
        i = qi.get(r["quarter"])
        if i is None:
            continue
        d = series.setdefault(r["metro"], {"sent": [None] * N, "n": [0] * N,
                                          "inv": [0.0] * N, "neg": [None] * N})
        d["inv"][i] += float(r["obligations"])
    for d in series.values():
        d["inv"] = [round(v) for v in d["inv"]]

    sun_link_rows = compute_sun_link_corridor(STUDY_DATA)
    payload = {
        "quarters": QS,
        "metros": {k: {"label": v[0], "zip3": v[1], "st": v[2]}
                   for k, v in METRO_LABEL.items()},
        "series": series,
        "events": load_json(EVENTS, []),
        "labels": load_json(LABELS, []),
        "extents": load_json(EXTENTS, {}),
        "minReviews": MIN_REVIEWS,
        "studyZipCounts": {m: sum(v == m for v in metro_of.values()) for m in METRO_LABEL},
        "sentScale": {"mid": round(med, 4), "lo": round(p5, 4), "hi": round(p95, 4)},
        "nReviews": sum(sum(v) for v in nrev.values()),
        "zipMetro": metro_of,
        "population": load_json(ROOT / "data" / "population_2020.json", {"records": {}}),
        "capitalEfficiency": read_csv(STUDY_DATA / "capital_efficiency.csv") + sun_link_table_rows(sun_link_rows),
        "sunLinkCoverage": {r["radius_m"]: r for r in read_csv(STUDY_DATA / "sun_coverage.csv")},
        "sunLinkCorridor": sun_link_rows,
        "projectFootprints": load_project_footprints(),
        "engagementScale": {"growthLow": -50, "growthHigh": 100,
                             "countHigh": sorted(n for counts in nrev.values() for n in counts)[int(.95 * (sum(map(len, nrev.values())) - 1))]},
    }

    html = (TEMPLATE
            .replace("__EXPLORATION_CSS__", (ROOT / "src" / "exploration.css").read_text())
            .replace("__EXPLORATION__", (ROOT / "src" / "exploration.html").read_text())
            .replace("__ANALYSIS__", (ROOT / "src" / "exploration.js").read_text())
            .replace("__ANALYSIS_MATH__", (ROOT / "src" / "analysis_math.js").read_text())
            .replace("__REVIEWS__", (INTERIM / "review_topics.json").read_text().replace("<", "\\u003c") if (INTERIM / "review_topics.json").exists() else "null")
            .replace("__DATA__", json.dumps(payload, separators=(",", ":")))
            .replace("__GEO__", json.dumps(gj, separators=(",", ":")))
            .replace("__CTX__", CONTEXT.read_text() if CONTEXT.exists()
                     else '{"type":"FeatureCollection","features":[]}')
            .replace("__STATES__", STATES.read_text() if STATES.exists()
                     else '{"type":"FeatureCollection","features":[]}'))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(f"{len(feats)} ZCTAs · {N} quarters · {len(payload['events'])} events "
          f"· {len(payload['labels'])} labels")
    print(f"sentiment scale: {p5:.3f} / {med:.3f} / {p95:.3f}")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.2f} MB)")


TEMPLATE = (ROOT / "src" / "map_template.html").read_text()


if __name__ == "__main__":
    main()
