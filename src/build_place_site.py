"""Build only Place Lab HTML/CSS; data exports belong to the research notebook.

Run output/jupyter-notebook/Project_Research_Walkthrough.ipynb to rebuild data,
then run this script and npm run build:place to rebuild the browser interface.
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build():
    for source, destination in (("src/place_template.html", "web/place.html"),
                                ("src/place.css", "web/place.css")):
        shutil.copyfile(ROOT / source, ROOT / destination)
    print("Built Place Lab HTML and styles. Data files are unchanged.")


if __name__ == "__main__":
    build()
