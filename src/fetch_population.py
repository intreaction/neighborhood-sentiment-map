"""Fetch Census 2020 population/land area for the atlas's actual mapped ZCTAs.

Use the public Census TIGERweb Census2020 attributes (no geometry download or
API key). The count is a fixed 2020 denominator, not an annual population series.
"""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/2"


def main():
    geo = json.loads((ROOT / "data/interim/zcta_boundaries.min.geojson").read_text())
    zips = sorted({f["properties"]["zip"] for f in geo["features"]})
    records = {}
    for start in range(0, len(zips), 40):
        batch = zips[start:start + 40]
        params = {"where": "GEOID IN (" + ",".join(f"'{z}'" for z in batch) + ")",
                  "outFields": "GEOID,POP100,AREALAND", "returnGeometry": "false", "f": "json"}
        with urllib.request.urlopen(SOURCE + "/query?" + urllib.parse.urlencode(params), timeout=60) as response:
            data = json.load(response)
        if data.get("error") or data.get("exceededTransferLimit"):
            raise ValueError(data)
        for f in data["features"]:
            a = f["attributes"]
            pop = a["POP100"]
            if pop is not None and (pop < 0 or int(pop) != pop):
                raise ValueError(f"Invalid population for {a['GEOID']}")
            records[a["GEOID"]] = {"population": int(pop) if pop is not None else None,
                                   "land_m2": a["AREALAND"]}
        print(f"{len(records)} / {len(zips)} ZCTAs", flush=True)
    result = {"source": SOURCE, "population_field": "POP100", "year": 2020,
              "retrieved_at": datetime.now(timezone.utc).isoformat(),
              "geography": "Census 2020 ZCTAs; exact GEOID match to map",
              "records": records, "missing": sorted(set(zips) - set(records))}
    out = ROOT / "data/population_2020.json"
    temp = out.with_suffix(".tmp")
    temp.write_text(json.dumps(result, indent=2))
    temp.replace(out)
    print(f"Wrote {out}; {len(result['missing'])} missing, "
          f"{sum(r['population'] == 0 for r in records.values())} zero population")


if __name__ == "__main__":
    main()
