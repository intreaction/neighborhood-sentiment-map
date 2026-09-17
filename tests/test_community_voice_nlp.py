"""Unit tests for community voice aspect extraction."""
import unittest

from src.community_voice_nlp import analyze_review_aspects, run_diagnostics


class TestCommunityVoiceNLP(unittest.TestCase):
    def test_pure_commercial_review(self):
        text = "The pasta was delicious and our server was super attentive. Great prices!"
        res = analyze_review_aspects(text)
        self.assertFalse(res["has_community_voice"])
        self.assertTrue(res["has_commercial_voice"])
        self.assertIn("food_drinks", res["commercial_aspects"])
        self.assertIn("service_staff", res["commercial_aspects"])
        self.assertIn("price_value", res["commercial_aspects"])

    def test_pure_community_review(self):
        text = "The new greenway path makes walking and biking to work safe and pleasant."
        res = analyze_review_aspects(text)
        self.assertTrue(res["has_community_voice"])
        self.assertFalse(res["has_commercial_voice"])
        self.assertIn("access_transit", res["community_aspects"])
        self.assertIn("surroundings_safety", res["community_aspects"])

    def test_mixed_review(self):
        text = "Good tacos, but the street construction makes parking a nightmare."
        res = analyze_review_aspects(text)
        self.assertTrue(res["has_community_voice"])
        self.assertTrue(res["has_commercial_voice"])
        self.assertIn("access_transit", res["community_aspects"])
        self.assertIn("surroundings_safety", res["community_aspects"])
        self.assertIn("food_drinks", res["commercial_aspects"])

    def test_calibration_diagnostics(self):
        diag = run_diagnostics()
        self.assertGreaterEqual(diag["community_voice_f1"], 0.90)
        self.assertGreaterEqual(diag["aspect_level_f1"], 0.80)


if __name__ == "__main__":
    unittest.main()
