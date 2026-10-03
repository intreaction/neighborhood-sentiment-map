"""Independent checks of the full-route Sun Link calculation."""

import csv
import unittest

from src.sun_link_corridor import COST_MILLIONS, STUDY, compute


class TestSunLinkCorridor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {(r["radius_m"], r["income_group"]): r for r in compute()}

    def test_full_route_500m_against_raw_aggregates(self):
        row = self.rows[(500, "All")]
        self.assertEqual(row["near_listings"], 717)
        self.assertEqual(row["baseline_reviewed"], 278)
        self.assertEqual(row["near_pre_reviews"], 3807)
        self.assertEqual(row["near_post_reviews"], 10943)
        self.assertEqual(row["comparison_pre_reviews"], 9957)
        self.assertEqual(row["comparison_post_reviews"], 34394)
        expected = 3807 * (34394 / 9957)
        self.assertAlmostEqual(row["expected_near_post_reviews"], expected)
        self.assertAlmostEqual(row["net_review_difference"], 10943 - expected)
        self.assertAlmostEqual(row["ce_per_million"], (10943 - expected) / COST_MILLIONS)
        self.assertAlmostEqual(row["ce_per_million"], -11.233294, places=5)
        self.assertFalse(row["low_support"])

    def test_scope_and_support(self):
        self.assertEqual(self.rows[(250, "All")]["near_listings"], 583)
        self.assertEqual(self.rows[(1000, "All")]["near_listings"], 909)
        self.assertEqual(self.rows[(500, "Lower")]["near_listings"], 631)
        self.assertTrue(self.rows[(500, "Middle")]["low_support"])
        self.assertTrue(self.rows[(500, "Higher")]["low_support"])
        with (STUDY / "capital_efficiency.csv").open(newline="") as handle:
            self.assertFalse(any(r["project"] == "Sun Link" for r in csv.DictReader(handle)))


if __name__ == "__main__":
    unittest.main()
