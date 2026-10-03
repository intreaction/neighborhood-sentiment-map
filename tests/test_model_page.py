"""Verification of the compiled, offline capital-efficiency scenario page."""

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "web" / "reference.html"


class TestModelPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = MODEL.read_text(encoding="utf-8")

    def test_page_and_reference_data(self):
        self.assertLess(MODEL.stat().st_size, 100_000)
        self.assertNotIn('src="https://', self.html)
        for element in ('id="projectType"', 'id="capital"', 'id="city"', 'id="zip"',
                        'id="businesses"', 'id="radius"', 'id="income"', 'id="score"',
                        'id="nearChange"', 'id="comparisonChange"', 'id="sentimentContrast"',
                        'id="participationCe"', 'id="trainedScore"', 'id="modelActive"',
                        'id="modelIntensity"'):
            self.assertTrue(element in self.html, f"Missing scenario control: {element}")
        start = self.html.index("const DATA=") + len("const DATA=")
        payload, _ = json.JSONDecoder().raw_decode(self.html[start:])
        self.assertEqual(len(payload["analogues"]), 5)
        self.assertEqual(len(payload["areas"]), 196)
        self.assertEqual(payload["trained_model"]["metrics"]["n_projects_trained"], 10)
        self.assertEqual(payload["trained_projects"]["Sun Link"]["listings"], 717)
        self.assertIn("Water Works Park", payload["trained_model"]["metrics"]["excluded_projects"])
        self.assertEqual({p["name"] for p in payload["analogues"]}, {
            "Dilworth Park", "Lafitte", "Riverfront / Ascend", "Sun Link", "Water Works Park"
        })
        dilworth = next(p for p in payload["analogues"] if p["name"] == "Dilworth Park")
        row = next(r for r in dilworth["rows"] if r["radius"] == 500 and r["income"] == "All")
        self.assertEqual(row["pairs"], 498)
        self.assertAlmostEqual(row["did_per_pair"], 7.496)
        self.assertAlmostEqual(row["observed_ce"], 67.87)
        self.assertAlmostEqual(
            row["near_post_mean"] - row["near_pre_mean"]
            - row["control_post_mean"] + row["control_pre_mean"],
            row["did_per_pair"], places=5,
        )
        sentiment = next(r for r in dilworth["sentiment_rows"] if r["radius"] == 500 and r["income"] == "All")
        self.assertEqual(sentiment["pairs"], 248)
        self.assertAlmostEqual(sentiment["contrast"], -0.0299972997214248)
        self.assertIsNotNone(dilworth["topic_shift_pp"])
        self.assertEqual(dilworth["participation"]["baseline"], 856)
        self.assertEqual(dilworth["participation"]["post"], 1160)
        self.assertAlmostEqual(dilworth["participation"]["ce"], -4.514, places=2)
        water = next(p for p in payload["analogues"] if p["name"] == "Water Works Park")
        water_row = next(r for r in water["rows"] if r["radius"] == 500 and r["income"] == "All")
        self.assertTrue(water_row["low_support"])
        self.assertTrue(water["participation"]["low_support"])
        sun_link = next(p for p in payload["analogues"] if p["name"] == "Sun Link")
        self.assertEqual(sun_link["route_coverage"]["500"]["listed"], 717)
        self.assertEqual(sun_link["route_coverage"]["250"]["listed"], 583)
        self.assertEqual(sun_link["route_coverage"]["1000"]["listed"], 909)
        self.assertEqual(sun_link["rows"], [])
        sun_row = next(r for r in sun_link["corridor_rows"] if r["radius"] == 500 and r["income"] == "All")
        self.assertEqual(sun_row["pairs"], 717)
        self.assertAlmostEqual(sun_row["observed_ce"], -11.233294, places=5)
        self.assertIn('id="routeCoverage"', self.html)
        self.assertIn("full-route baseline", self.html)
        self.assertEqual(sun_link["sentiment_rows"], [])
        self.assertIsNone(sun_link["topic_shift_pp"])
        self.assertIn("scenarioScoreWithAssumptions", self.html)

    def test_inline_script_syntax(self):
        match = re.search(r"<script>(.*?)</script>", self.html, re.DOTALL)
        self.assertIsNotNone(match)
        with tempfile.TemporaryDirectory() as temp_dir:
            script = Path(temp_dir) / "model.js"
            script.write_text(match.group(1), encoding="utf-8")
            check = subprocess.run(["node", "--check", str(script)], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)


if __name__ == "__main__":
    unittest.main()
