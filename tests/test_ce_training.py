"""Guard the final CE model against cohort regression and future-input leakage."""

import csv
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from train_ce_model import fit_and_evaluate  # noqa: E402


class TestCeTraining(unittest.TestCase):
    def test_full_sun_route_and_pre_opening_features(self):
        with (ROOT / "data/derived/sun_link_full_route_cohorts.csv").open(newline="") as f:
            cohorts = Counter(row["band"] for row in csv.DictReader(f))
        self.assertEqual(cohorts, {"near": 717, "far": 4151})
        artifact, _, eligible = fit_and_evaluate()
        saved = json.loads((ROOT / "data/derived/ce_trained_model.json").read_text())
        self.assertEqual(artifact["feature_names"], [
            "log_pre_reviews_per_active_business", "log_cost_millions", "log_baseline_reviewed"
        ])
        self.assertNotIn("near_listings", artifact["feature_transform"])
        self.assertEqual(len(eligible), 10)
        self.assertEqual(saved["metrics"], artifact["metrics"])
        self.assertEqual(saved["metrics"]["excluded_projects"], ["Water Works Park"])


if __name__ == "__main__":
    unittest.main()
