"""Verification tests for the compiled offline web/atlas.html page."""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "web" / "atlas.html"


class TestWebIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not INDEX_HTML.exists():
            raise FileNotFoundError(f"{INDEX_HTML} does not exist. Run python3 src/build_map_page.py first.")
        cls.html = INDEX_HTML.read_text(encoding="utf-8")

    def test_file_size_under_budget(self):
        # Must be self-contained and offline, under 4.0 MB budget
        size_mb = INDEX_HTML.stat().st_size / 1e6
        self.assertLess(size_mb, 4.0, f"File size {size_mb:.2f} MB exceeds 4.0 MB budget")

    def test_dom_elements_present(self):
        for label in (
            'data-m="ce" aria-pressed="false">Legacy CE</button>',
            'CE = matched net review gain ÷ reported project cost in $ millions.',
            'data-m="g" aria-pressed="false">Review growth</button>',
            'data-m="n" aria-pressed="true">Review count</button>',
            'id="ceMapRadius"', 'id="ceMapIncome"', 'id="ceProjectValue"',
            'ZIP color = quarterly review count; project badge = CE from its post window.',
            'id="projectTimeline"', 'id="projectCePin"',
        ):
            self.assertTrue(label in self.html, f"Missing CE map element: {label}")
        self.assertIn('id="capital-efficiency"', self.html)
        self.assertIn('id="efficiencyRows"', self.html)
        self.assertIn('id="effRadius"', self.html)
        self.assertIn('id="effIncome"', self.html)
        self.assertEqual(self.html.count('class="ce-column-help"'), 10)
        self.assertIn('id="ceColumnHelp"', self.html)
        self.assertIn('function initializeCeColumnHelp()', self.html)
        self.assertIn('Net Reviews ÷ reported project cost', self.html)
        self.assertIn('href="model.html"', self.html)
        self.assertIn('Open the proposal tool', self.html)
        self.assertNotIn('id="scenBudget"', self.html)
        self.assertIn('02 / Earlier CE methods', self.html)
        self.assertIn('03 / Funding &amp; timing', self.html)
        self.assertIn('04 / Inside the reviews', self.html)
        self.assertIn('05 / Compare places', self.html)

    def test_embedded_data_payload(self):
        marker = "const D="
        idx = self.html.find(marker)
        self.assertNotEqual(idx, -1, "Could not locate embedded D payload in web/atlas.html")
        payload_str = self.html[idx + len(marker):]
        payload, _ = json.JSONDecoder().raw_decode(payload_str)

        self.assertIn("capitalEfficiency", payload)
        self.assertEqual(payload["engagementScale"]["growthLow"], -50)
        self.assertEqual(payload["engagementScale"]["growthHigh"], 100)
        footprints = payload["projectFootprints"]
        self.assertEqual(len(footprints), 5)
        self.assertEqual({f["name"] for f in footprints}, {
            "Lafitte", "Sun Link", "Dilworth Park", "Water Works Park", "Riverfront / Ascend"
        })
        self.assertTrue(all(f["geometry"]["coordinates"] and len(f["center"]) == 2 for f in footprints))
        self.assertTrue(all(len(f["pre"]) == 2 and len(f["post"]) == 2 for f in footprints))
        geo_start = self.html.index(", GEO=") + len(", GEO=")
        geometry, _ = json.JSONDecoder().raw_decode(self.html[geo_start:])
        philly = [f["properties"]["n"] for f in geometry["features"]
                  if f["properties"]["metro"] == "Philadelphia"]
        self.assertGreater(sum(counts[19] != counts[20] for counts in philly), 10,
                           "The CE map's quarterly engagement background needs changing counts")
        ce_rows = payload["capitalEfficiency"]
        self.assertGreaterEqual(len(ce_rows), 170)
        self.assertEqual({r["comparison_method"] for r in ce_rows}, {"matched_pairs", "cohort_mean", "unmatched_growth_adjusted_corridor"})
        self.assertEqual(payload["sunLinkCoverage"]["500"]["listed_businesses"], "717")
        self.assertFalse(any(r["project"] == "Sun Link" and r["comparison_method"] == "matched_pairs" for r in ce_rows))
        corridor = next(r for r in payload["sunLinkCorridor"] if r["radius_m"] == 500 and r["income_group"] == "All")
        self.assertAlmostEqual(corridor["ce_per_million"], -11.233294, places=5)

        def project_score(name):
            row = next(r for r in ce_rows if r["project"] == name and
                       r["comparison_method"] == "matched_pairs" and r["metric"] == "reviews" and
                       r["income_group"] == "All" and r["radius_m"] == "500")
            return row

        self.assertAlmostEqual(float(project_score("Dilworth Park")["ce_abs_per_million"]), 67.87)
        self.assertEqual(project_score("Water Works Park")["low_support"], "True")
        self.assertEqual(int(project_score("Water Works Park")["pairs"]), 2)

        # Check Lafitte 500m row
        lafitte_500 = [
            r for r in ce_rows
            if r["project"] == "Lafitte" and str(r["radius_m"]) == "500" and r["metric"] == "reviews" and r["income_group"] == "All"
        ]
        self.assertEqual(len(lafitte_500), 1)
        self.assertAlmostEqual(float(lafitte_500[0]["ce_abs_per_million"]), 165.16, places=1)
    def test_inlined_javascript_syntax(self):
        # Extract script content
        match = re.search(r"<script>(.*?)</script>", self.html, re.DOTALL)
        self.assertIsNotNone(match, "Could not find <script> tag in web/atlas.html")
        script = match.group(1)

        tmp_js = Path("/tmp/test_web_index_extracted.js")
        tmp_js.write_text(script, encoding="utf-8")
        res = subprocess.run(["node", "--check", str(tmp_js)], capture_output=True, text=True, check=False)
        self.assertEqual(res.returncode, 0, f"Node syntax error in web/atlas.html: {res.stderr}")


if __name__ == "__main__":
    unittest.main()
