"""Verification tests for the compiled offline web/index.html page."""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "web" / "index.html"


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
        self.assertIn('id="capital-efficiency"', self.html)
        self.assertIn('id="efficiencyRows"', self.html)
        self.assertIn('id="effRadius"', self.html)
        self.assertIn('id="effIncome"', self.html)
        self.assertIn('02 / Capital Efficiency', self.html)
        self.assertIn('03 / Funding &amp; timing', self.html)
        self.assertIn('04 / Inside the reviews', self.html)
        self.assertIn('05 / Compare places', self.html)

    def test_embedded_data_payload(self):
        marker = "const D="
        idx = self.html.find(marker)
        self.assertNotEqual(idx, -1, "Could not locate embedded D payload in web/index.html")
        payload_str = self.html[idx + len(marker):]
        payload, _ = json.JSONDecoder().raw_decode(payload_str)

        self.assertIn("capitalEfficiency", payload)
        ce_rows = payload["capitalEfficiency"]
        self.assertEqual(len(ce_rows), 200)

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
        self.assertIsNotNone(match, "Could not find <script> tag in web/index.html")
        script = match.group(1)

        tmp_js = Path("/tmp/test_web_index_extracted.js")
        tmp_js.write_text(script, encoding="utf-8")
        res = subprocess.run(["node", "--check", str(tmp_js)], capture_output=True, text=True, check=False)
        self.assertEqual(res.returncode, 0, f"Node syntax error in web/index.html: {res.stderr}")


if __name__ == "__main__":
    unittest.main()
