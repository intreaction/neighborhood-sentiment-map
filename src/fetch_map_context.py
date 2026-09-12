"""Fetch water, roads and county outlines so the choropleth reads as a place.

A published Artifact cannot load basemap tiles (the CSP blocks external images),
so context has to ship as vector geometry inside the page. These come from the
same Census TIGERweb service as the ZCTAs, clipped to each metro's bounding box:
without the bay, Tampa is unreadable; without the Mississippi, so is New Orleans.

Output: data/interim/map_context.geojson  — features tagged {kind: water|road|county}
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
BOUNDARIES = INTERIM / "zcta_boundaries.min.geojson"
METRO_ZIPS = INTERIM / "metro_zips.json"
OUT = INTERIM / "map_context.geojson"

BASE = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb"
LAYERS = [
    # (kind, service, layer id, min area in sq deg to keep, cap)
    ("water", "Hydro", 1, 2e-5, 900),
    ("road", "Transportation", 2, 0, 700),      # primary roads
    ("road2", "Transportation", 3, 0, 900),     # secondary: interstates + US highways
    ("county", "State_County", 1, 0, 200),
]
PRECISION = 4
PAD = 0.12  # degrees of slack around each metro


def bboxes():
    gj = json.loads(BOUNDARIES.read_text())
    metro_of = {z: m for m, zs in json.loads(METRO_ZIPS.read_text()).items() for z in zs}
    acc = {}
    for f in gj["features"]:
        m = metro_of.get(f["properties"]["zip"])
        if not m:
            continue
        polys = (
            [f["geometry"]["coordinates"]]
            if f["geometry"]["type"] == "Polygon"
            else f["geometry"]["coordinates"]
        )
        for poly in polys:
            for ring in poly:
                for x, y in ring:
                    b = acc.setdefault(m, [x, y, x, y])
                    b[0], b[1] = min(b[0], x), min(b[1], y)
                    b[2], b[3] = max(b[2], x), max(b[3], y)
    return {m: (b[0] - PAD, b[1] - PAD, b[2] + PAD, b[3] + PAD) for m, b in acc.items()}


def query(service, layer, bbox, cap):
    params = {
        "geometry": ",".join(f"{v:.5f}" for v in bbox),
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "NAME",
        "returnGeometry": "true",
        "outSR": "4326",
        "resultRecordCount": str(cap),
        "where": "NAME IS NOT NULL",  # `1=1` is WAF-rejected
        "f": "geojson",
    }
    url = f"{BASE}/{service}/MapServer/{layer}/query?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=240) as r:
        return json.load(r)


def ring_area(ring):
    a = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def geom_area(g):
    if g["type"] == "Polygon":
        return ring_area(g["coordinates"][0]) if g["coordinates"] else 0
    if g["type"] == "MultiPolygon":
        return sum(ring_area(p[0]) for p in g["coordinates"] if p)
    return 0


def round_geom(coords, depth):
    if depth == 1:
        return [[round(x, PRECISION), round(y, PRECISION)] for x, y in coords]
    return [round_geom(c, depth - 1) for c in coords]


DEPTH = {"Polygon": 2, "MultiPolygon": 3, "LineString": 1, "MultiLineString": 2}


def main():
    boxes = bboxes()
    print(f"{len(boxes)} metro bounding boxes", flush=True)
    out = []
    for kind, service, layer, min_area, cap in LAYERS:
        got = 0
        for metro, bbox in boxes.items():
            try:
                fc = query(service, layer, bbox, cap)
            except urllib.error.HTTPError as e:
                print(f"  {kind}/{metro}: HTTP {e.code}", flush=True)
                continue
            except Exception as e:
                print(f"  {kind}/{metro}: {type(e).__name__}", flush=True)
                continue
            for f in fc.get("features") or []:
                g = f.get("geometry") or {}
                d = DEPTH.get(g.get("type"))
                if not d:
                    continue
                if min_area and geom_area(g) < min_area:
                    continue
                g["coordinates"] = round_geom(g["coordinates"], d)
                out.append({
                    "type": "Feature",
                    "geometry": g,
                    "properties": {
                        "kind": "road" if kind == "road2" else kind,
                        "metro": metro,
                        "name": (f.get("properties") or {}).get("NAME") or "",
                    },
                })
                got += 1
        print(f"  {kind}: {got} features", flush=True)

    OUT.write_text(json.dumps(
        {"type": "FeatureCollection", "features": out}, separators=(",", ":")))
    kinds = {}
    for f in out:
        kinds[f["properties"]["kind"]] = kinds.get(f["properties"]["kind"], 0) + 1
    print(f"\n{len(out)} features {kinds} -> {OUT} ({OUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
