"""Rule checks and optional reconciliation against locally generated aggregates."""
import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from build_review_topics import classify


class ReviewTopicsTest(unittest.TestCase):
    def test_overlapping_topics(self):
        self.assertEqual(set(classify("Dirty bathrooms and expensive food.")), {"cleanliness", "value", "product"})

    def test_word_boundaries_and_case(self):
        self.assertIn("access", classify("PARKING was easy."))
        self.assertNotIn("access", classify("A sparkling place."))

    def test_mentions_do_not_assert_polarity(self):
        self.assertIn("cleanliness", classify("The bathroom was spotless and clean."))
        self.assertIn("cleanliness", classify("The bathroom was filthy."))

    @unittest.skipUnless((ROOT / "data/interim/review_topics.json").exists(), "Local review panel is not built")
    def test_aggregate_reconciliation(self):
        data = json.loads((ROOT / "data/interim/review_topics.json").read_text())
        with (ROOT / "data/interim/sentiment_zip_quarter.csv").open() as f:
            expected = {(r["zip5"], r["quarter"]): int(r["n_reviews"]) for r in csv.DictReader(f)}
        observed = {}
        for z, quarters in data["panel"].items():
            for q, cell in quarters.items():
                n = sum(cell["stars"])
                observed[z, q] = n
                for count, score, negative in cell["topics"].values():
                    self.assertTrue(0 <= negative <= count <= n)
                    self.assertLessEqual(abs(score), count + .0001)
        self.assertEqual(observed, expected)
        self.assertEqual(sum(observed.values()), data["nReviews"])
        for e in data["examples"]:
            self.assertIn(e["topic"], classify(e["text"]))


if __name__ == "__main__":
    unittest.main()
