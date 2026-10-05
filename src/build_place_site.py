"""Build Place Lab, its findings and methodology pages; data exports belong to the research notebook.

Run output/jupyter-notebook/Project_Research_Walkthrough.ipynb to rebuild data,
then run this script and npm run build:place to rebuild the browser interface.
The only data this script writes is findings-data.json, copied verbatim from
derived artifacts (text-validation metrics and learned topic terms).
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REDIRECT = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Public Investment Map</title>
<meta http-equiv="refresh" content="0; url=place.html"><link rel="canonical" href="place.html"></head>
<body><p><a href="place.html">Open Place Lab</a></p></body></html>
"""


def build():
    for source, destination in (("src/place_template.html", "web/place.html"),
                                ("src/place.css", "web/place.css"),
                                ("src/methods_template.html", "web/methods.html"),
                                ("src/findings_template.html", "web/findings.html")):
        shutil.copyfile(ROOT / source, ROOT / destination)
    advanced = json.loads((ROOT / "data/derived/advanced_text.json").read_text())
    findings = {"text_validation": json.loads((ROOT / "data/derived/text_validation/metrics.json").read_text()),
                "topics": [{"id": t["id"], "top_terms": t["top_terms"]} for t in advanced["topics"]]}
    (ROOT / "web/findings-data.json").write_text(json.dumps(findings, separators=(",", ":")))
    # The site root opens Place Lab, the primary deliverable.
    (ROOT / "web/index.html").write_text(REDIRECT)
    print("Built Place Lab, findings and methodology pages. Notebook data files are unchanged.")


if __name__ == "__main__":
    build()
