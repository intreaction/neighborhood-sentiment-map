"""Build portable project evidence and proposal pages from versioned artifacts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def embedded_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

def build():
    evidence = json.loads((ROOT / "data/derived/project_evidence.json").read_text())
    for project in evidence["projects"]:
        geometry = project.get("geometry", {})
        if geometry.get("path"):
            raw = json.loads((ROOT / geometry["path"]).read_text())
            project["display_geometry"] = raw.get("geometry") or raw["features"][0]["geometry"]
        elif geometry.get("kind") == "center_proxy":
            project["display_geometry"] = {"type": "Point", "coordinates": [geometry["longitude"], geometry["latitude"]]}
    model = json.loads((ROOT / "data/derived/project_model.json").read_text())
    advanced_path = ROOT / "data/derived/advanced_text.json"
    advanced = json.loads(advanced_path.read_text())
    template = (ROOT / "src/evidence_template.html").read_text()
    css = (ROOT / "src/evidence.css").read_text()
    app = (ROOT / "src/evidence.js").read_text()
    math = (ROOT / "src/project_model_math.js").read_text()
    for page, title in (("projects", "Project evidence"), ("model", "Analyze a proposal")):
        html = template.replace("__TITLE__", title).replace("__PAGE__", page)
        html = html.replace("__CSS__", css).replace("__DATA__", embedded_json(evidence)).replace("__MODEL__", embedded_json(model)).replace("__ADVANCED__", embedded_json(advanced)).replace("__MATH__", math).replace("__APP__", app)
        (ROOT / "web" / f"{page}.html").write_text(html)
    return len(evidence["projects"])

if __name__ == "__main__":
    print(f"Built project evidence and proposal pages for {build()} projects")
