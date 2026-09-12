"""Fetch ZCTA boundary polygons for the study ZIPs as GeoJSON.

Pulls only the ZCTAs we actually map (277, not 33,000), from the Census TIGERweb
REST service — so no 500 MB national shapefile and no geopandas/GDAL stack. The
service caps each response, so GEOIDs are requested in batches.

Output: data/interim/zcta_boundaries.geojson  (WGS84, ready for Leaflet/Folium)
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIPS = ROOT / "data" / "interim" / "metro_zips.txt"
OUT = ROOT / "data" / "interim" / "zcta_boundaries.geojson"

SERVICE = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
    "tigerWMS_ACS2023/MapServer/2/query"
)
BATCH = 40  # keeps the URL and the response comfortably under service limits


def fetch_batch(geoids):
    params = {
        "where": "GEOID IN (" + ",".join(f"'{g}'" for g in geoids) + ")",
        "outFields": "GEOID,NAME,AREALAND",
        "returnGeometry": "true",
        "outSR": "4326",       # WGS84 lon/lat
        "f": "geojson",
    }
    url = SERVICE + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=180) as r:
        return json.load(r)


def main():
    zips = sorted({z.strip() for z in ZIPS.read_text().split() if z.strip()})
    print(f"requesting {len(zips)} ZCTAs in batches of {BATCH}", flush=True)

    features, seen = [], set()
    for i in range(0, len(zips), BATCH):
        batch = zips[i : i + BATCH]
        try:
            fc = fetch_batch(batch)
        except urllib.error.HTTPError as e:
            print(f"  batch {i // BATCH}: HTTP {e.code} — skipped", flush=True)
            continue
        got = fc.get("features") or []
        for f in got:
            gid = (f.get("properties") or {}).get("GEOID")
            if gid and gid not in seen:
                seen.add(gid)
                features.append(f)
        print(f"  batch {i // BATCH}: {len(got)} features ({len(seen)} unique so far)", flush=True)

    OUT.write_text(
        json.dumps({"type": "FeatureCollection", "features": features})
    )
    missing = sorted(set(zips) - seen)
    print(f"\n{len(features)} polygons -> {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
    if missing:
        # ZIPs with no ZCTA are normal: PO-box-only and single-building ZIPs
        # have no tabulation area, so they can be mapped as points or dropped.
        print(f"{len(missing)} ZIPs had no ZCTA polygon: {missing}")


if __name__ == "__main__":
    main()
