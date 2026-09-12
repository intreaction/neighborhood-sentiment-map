"""Shrink the ZCTA GeoJSON so a timeline slider can redraw it smoothly.

TIGER polygons carry survey-grade vertex density — far more than a ZIP-level
choropleth needs. This applies Ramer-Douglas-Peucker per ring and rounds
coordinates, which is enough to cut the payload by roughly an order of magnitude
with no visible change at metro zoom. Implemented directly so the project needs
no shapely/GDAL stack.

Output: data/interim/zcta_boundaries.min.geojson
"""

import json
import sys
from pathlib import Path

# RDP recurses once per retained vertex; dense TIGER rings exceed the default.
sys.setrecursionlimit(100_000)

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "interim" / "zcta_boundaries.geojson"
OUT = ROOT / "data" / "interim" / "zcta_boundaries.min.geojson"

TOLERANCE = 0.0004  # degrees, ~40 m — well below ZIP-polygon scale
PRECISION = 5


def _perp_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def rdp(points, tol):
    if len(points) < 3:
        return points
    dmax, idx = 0.0, 0
    for i in range(1, len(points) - 1):
        d = _perp_dist(points[i], points[0], points[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax <= tol:
        return [points[0], points[-1]]
    return rdp(points[: idx + 1], tol)[:-1] + rdp(points[idx:], tol)


def simplify_ring(ring, tol):
    # A ring must stay closed and keep at least 4 points to remain a polygon.
    out = rdp(ring, tol)
    if len(out) < 4:
        out = ring[:: max(1, len(ring) // 8)]
    if out[0] != out[-1]:
        out.append(out[0])
    return [[round(x, PRECISION), round(y, PRECISION)] for x, y in out]


def walk(coords, depth):
    """Recurse to ring level (depth 2 = Polygon, 3 = MultiPolygon)."""
    if depth == 1:
        return simplify_ring(coords, TOLERANCE)
    return [walk(c, depth - 1) for c in coords]


def main():
    gj = json.loads(SRC.read_text())
    before = after = 0
    feats = []
    for f in gj["features"]:
        g = f.get("geometry") or {}
        t = g.get("type")
        if t == "Polygon":
            depth = 2
        elif t == "MultiPolygon":
            depth = 3
        else:
            continue
        before += len(json.dumps(g["coordinates"]))
        g["coordinates"] = walk(g["coordinates"], depth)
        after += len(json.dumps(g["coordinates"]))
        p = f.get("properties") or {}
        f["properties"] = {"zip": p.get("GEOID")}  # drop unused attributes
        feats.append(f)

    OUT.write_text(
        json.dumps({"type": "FeatureCollection", "features": feats},
                   separators=(",", ":"))
    )
    print(f"{len(feats)} polygons")
    print(f"coordinate payload: {before / 1e6:.2f} MB -> {after / 1e6:.2f} MB")
    print(f"file: {SRC.stat().st_size / 1e6:.2f} MB -> {OUT.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
