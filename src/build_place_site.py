"""Copy authored Place Lab UI and fitted model to the portable web output.

Run after src/build_place_data.py, then npm run build:place for JS.
"""
import shutil
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def build():
    for source, destination in (("src/place_template.html", "web/place.html"),
                                ("src/place.css", "web/place.css"),
                                ("data/derived/project_model.json", "web/place-model.json")):
        shutil.copyfile(ROOT / source, ROOT / destination)
    evidence = json.loads((ROOT / "data/derived/project_evidence.json").read_text())
    historical = [{"id": p["id"], "project": p["project"], "opening": p["opening"],
                   "periods": {group: {period: {key: values[key] for key in ("n_reviews", "by_year", "topics", "place_discussion_share", "access_friction_share", "public_realm_complaint_share", "mean_sentiment")}
                              for period, values in p["periods"][group].items()}
                              for group in ("near", "far")}}
                  for p in evidence["projects"]]
    (ROOT / "web/place-history.json").write_text(json.dumps({"version": evidence["version"], "projects": historical}))
    print("Built Place Lab page, styles, and model artifact.")

if __name__ == "__main__":
    build()
