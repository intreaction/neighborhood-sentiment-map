"""Fetch the orientation layer: state borders, place labels, metro extents.

Solves two things the choropleth alone can't. First, comparability across zoom —
state outlines and a locator inset mean you always know where you are. Second,
recognition — a ZCTA is an abstraction; "Ybor City" or "Germantown" is a place.

Place labels ship as points rendered in HTML rather than as a MapLibre symbol
layer, because `text-field` fetches SDF glyphs from an external URL and the
Artifact CSP blocks that.

Outputs (data/interim/):
    states.geojson        all US state outlines, simplified
    place_labels.json     [{name, lon, lat, rank, metro}] for the study metros
    metro_extents.json    per-metro bounds for the flyto buttons and inset
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.setrecursionlimit(100_000)

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
BOUNDARIES = INTERIM / "zcta_boundaries.min.geojson"
METRO_ZIPS = INTERIM / "metro_zips.json"

BASE = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb"
PAD = 0.12


PRECISION = 4


def _perp(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def rdp(pts, tol):
    if len(pts) < 3:
        return pts
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = _perp(pts[i], pts[0], pts[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax <= tol:
        return [pts[0], pts[-1]]
    return rdp(pts[: idx + 1], tol)[:-1] + rdp(pts[idx:], tol)


def simplify(coords, depth, tol, closed=True):
    if depth == 1:
        out = rdp(coords, tol)
        if closed:
            if len(out) < 4:
                out = coords[:: max(1, len(coords) // 8)]
            if out[0] != out[-1]:
                out.append(out[0])
        return [[round(x, PRECISION), round(y, PRECISION)] for x, y in out]
    return [simplify(c, depth - 1, tol, closed) for c in coords]


DEPTH = {"Polygon": 2, "MultiPolygon": 3, "LineString": 1, "MultiLineString": 2}


def get(url):
    with urllib.request.urlopen(url, timeout=300) as r:
        return json.load(r)


def query(service, layer, params):
    # `where=1=1` is rejected by the Census WAF as injection-shaped; this is equivalent.
    p = {"returnGeometry": "true", "outSR": "4326",
         "where": "NAME IS NOT NULL", "f": "geojson", **params}
    return get(f"{BASE}/{service}/MapServer/{layer}/query?" + urllib.parse.urlencode(p))


def metro_extents():
    gj = json.loads(BOUNDARIES.read_text())
    metro_of = {z: m for m, zs in json.loads(METRO_ZIPS.read_text()).items() for z in zs}
    acc = {}
    for f in gj["features"]:
        m = metro_of.get(f["properties"]["zip"])
        if not m:
            continue
        polys = ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon"
                 else f["geometry"]["coordinates"])
        for poly in polys:
            for ring in poly:
                for x, y in ring:
                    b = acc.setdefault(m, [x, y, x, y])
                    b[0], b[1] = min(b[0], x), min(b[1], y)
                    b[2], b[3] = max(b[2], x), max(b[3], y)
    return acc


def centroid(g):
    """Area-weighted centroid of the largest ring — good enough for a label anchor."""
    rings = ([g["coordinates"][0]] if g["type"] == "Polygon"
             else [p[0] for p in g["coordinates"] if p])
    best, ba = None, -1
    for r in rings:
        a = 0.0
        for i in range(len(r) - 1):
            a += r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1]
        a = abs(a) / 2
        if a > ba:
            ba, best = a, r
    if not best:
        return None, 0
    n = len(best)
    return [sum(p[0] for p in best) / n, sum(p[1] for p in best) / n], ba


def main():
    ext = metro_extents()
    (INTERIM / "metro_extents.json").write_text(json.dumps(
        {m: [round(v, 4) for v in b] for m, b in ext.items()}))
    print(f"metro extents: {len(ext)}", flush=True)

    # ---- states ---------------------------------------------------------
    # Full-resolution state geometry is ~650 KB each, and the Census gateway
    # rejects any response over a few MB — so page in small batches and
    # simplify each batch before it accumulates.
    feats = []
    PAGE = 8
    for offset in range(0, 64, PAGE):
        try:
            fc = query("State_County", 0, {
                "outFields": "NAME,STUSAB",
                "resultRecordCount": str(PAGE),
                "resultOffset": str(offset),
            })
        except urllib.error.HTTPError as e:
            print(f"  states offset {offset}: HTTP {e.code}", flush=True)
            continue
        batch = fc.get("features") or []
        if not batch:
            break
        for f in batch:
            g = f.get("geometry") or {}
            d = DEPTH.get(g.get("type"))
            if not d:
                continue
            g["coordinates"] = simplify(g["coordinates"], d, 0.02)
            pr = f.get("properties") or {}
            feats.append({"type": "Feature", "geometry": g,
                          "properties": {"name": pr.get("NAME"), "ab": pr.get("STUSAB")}})
        print(f"  states offset {offset}: +{len(batch)} ({len(feats)} total)", flush=True)
    out = INTERIM / "states.geojson"
    out.write_text(json.dumps({"type": "FeatureCollection", "features": feats},
                              separators=(",", ":")))
    print(f"states: {len(feats)} -> {out.name} ({out.stat().st_size / 1e6:.2f} MB)", flush=True)

    # ---- place labels inside each metro ---------------------------------
    # Only the study metros get labels; at national zoom the metro bubbles carry
    # their own names, so out-of-scope cities would be pure clutter.
    labels = []
    for metro, b in ext.items():
        bbox = (b[0] - PAD, b[1] - PAD, b[2] + PAD, b[3] + PAD)
        try:
            fc = query("Places_CouSub_ConCity_SubMCD", 4, {
                "geometry": ",".join(f"{v:.5f}" for v in bbox),
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "NAME",
                "resultRecordCount": "400",
            })
        except urllib.error.HTTPError as e:
            print(f"  places/{metro}: HTTP {e.code}", flush=True)
            continue
        got = []
        for f in fc.get("features") or []:
            g = f.get("geometry") or {}
            if g.get("type") not in ("Polygon", "MultiPolygon"):
                continue
            c, area = centroid(g)
            if not c:
                continue
            nm = (f.get("properties") or {}).get("NAME") or ""
            if not nm:
                continue
            got.append((area, nm, c))
        got.sort(reverse=True, key=lambda t: t[0])
        for rank, (_a, nm, c) in enumerate(got[:26], start=1):
            labels.append({"name": nm, "lon": round(c[0], 4), "lat": round(c[1], 4),
                           "rank": rank, "metro": metro})
        print(f"  places/{metro}: {min(len(got),26)} labels", flush=True)

    lp = INTERIM / "place_labels.json"
    lp.write_text(json.dumps(labels, separators=(",", ":")))
    print(f"\nplace labels: {len(labels)} -> {lp.name} ({lp.stat().st_size / 1e3:.0f} KB)")


if __name__ == "__main__":
    main()
