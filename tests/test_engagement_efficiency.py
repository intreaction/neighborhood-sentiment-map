"""Unit tests for engagement and capital efficiency calculations."""
from pathlib import Path
import unittest

from src.engagement_efficiency import load_data, compute_capital_efficiency

ROOT = Path(__file__).resolve().parent.parent
STUDY_DATA = ROOT / "docs" / "coursework" / "milestone-2-eda" / "study_data"


class TestEngagementEfficiency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg_df, cls.eng, cls.bg = load_data(STUDY_DATA)
        cls.results = compute_capital_efficiency(cls.reg_df, cls.eng, cls.bg)

    def test_row_count_and_projects(self):
        self.assertGreater(len(self.results), 0)
        projects = set(self.results["project"])
        self.assertEqual(projects, {"Lafitte", "Sun Link", "Dilworth Park", "Water Works Park", "Riverfront / Ascend"})

    def test_water_works_low_support_flag(self):
        ww = self.results[(self.results["project"] == "Water Works Park") & (self.results["radius_m"] == 500)]
        self.assertTrue((ww["low_support"] == True).all(), "Water Works Park at 500m must be flagged as low_support")

    def test_lafitte_primary_metrics(self):
        lafitte = self.results[
            (self.results["project"] == "Lafitte") &
            (self.results["radius_m"] == 500) &
            (self.results["metric"] == "reviews") &
            (self.results["income_group"] == "All")
        ].iloc[0]

        # DiD = delta_near - delta_ctrl
        delta_near = lafitte["near_post_mean"] - lafitte["near_pre_mean"]
        delta_ctrl = lafitte["control_post_mean"] - lafitte["control_pre_mean"]
        expected_did = delta_near - delta_ctrl
        self.assertAlmostEqual(lafitte["did_per_pair"], expected_did, places=2)

        # CE_abs = net_vol / cost
        expected_ce_abs = lafitte["net_volume_gain"] / lafitte["cost_millions"]
        self.assertAlmostEqual(lafitte["ce_abs_per_million"], expected_ce_abs, places=1)
        self.assertGreater(lafitte["ce_abs_per_million"], 100.0)

    def test_sun_link_cost_and_efficiency(self):
        sl = self.results[
            (self.results["project"] == "Sun Link") &
            (self.results["radius_m"] == 500) &
            (self.results["metric"] == "reviews") &
            (self.results["income_group"] == "All")
        ].iloc[0]

        self.assertEqual(sl["cost_millions"], 196.5)
        # Sun link had negative matched contrast
        self.assertLess(sl["ce_abs_per_million"], 0)

    def test_independent_external_anchors(self):
        # Independent anchor 1: Lafitte 500m/All/Main matches engagement.csv raw values
        lafitte = self.results[
            (self.results["project"] == "Lafitte") &
            (self.results["radius_m"] == 500) &
            (self.results["metric"] == "reviews") &
            (self.results["income_group"] == "All")
        ].iloc[0]
        self.assertEqual(lafitte["pairs"], 142)
        self.assertAlmostEqual(lafitte["near_pre_mean"], 23.613, places=2)
        self.assertAlmostEqual(lafitte["near_post_mean"], 38.993, places=2)
        self.assertAlmostEqual(lafitte["control_pre_mean"], 21.085, places=2)
        self.assertAlmostEqual(lafitte["control_post_mean"], 25.880, places=2)
        self.assertAlmostEqual(lafitte["relative_growth_pct"], 34.54, places=1)
        self.assertAlmostEqual(lafitte["net_volume_gain"], 1503.0, places=0)
        self.assertAlmostEqual(lafitte["ce_abs_per_million"], 165.16, places=1)

        # Independent anchor 2: Lafitte CE_biz matches business_growth.csv net gain
        self.assertAlmostEqual(lafitte["biz_500m_net_gain"], 17.53, places=1)
        self.assertAlmostEqual(lafitte["ce_biz_per_million"], 1.926, places=2)

        # Independent anchor 3: Water Works Park at 1,000m has pairs=23 and low_support=False
        ww_1000 = self.results[
            (self.results["project"] == "Water Works Park") &
            (self.results["radius_m"] == 1000) &
            (self.results["metric"] == "reviews") &
            (self.results["income_group"] == "All")
        ].iloc[0]
        self.assertEqual(ww_1000["pairs"], 23)
        self.assertFalse(ww_1000["low_support"])


if __name__ == "__main__":
    unittest.main()
