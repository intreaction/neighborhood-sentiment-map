"""Meaningful invariants for project model provenance, leakage and validation."""
import copy
import hashlib
import json
import sys
import unittest
from numeric_assertions import assert_numeric_tree
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from train_project_model import DATA, OUT, fit_artifact, inputs_for
from project_advanced_model import blocked_record, select_sample


class ProjectModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(DATA.read_text())
        cls.model = json.loads(OUT.read_text())

    def test_artifact_matches_real_evidence(self):
        self.assertEqual(self.model["provenance"]["evidence_sha256"], hashlib.sha256(DATA.read_bytes()).hexdigest())
        evidence = {p["id"]: p for p in self.evidence["projects"]}
        for row in self.model["training_rows"]:
            p = evidence[row["id"]]
            self.assertTrue(p["primary"]["eligible"])
            self.assertEqual(row["observed_ce"], p["primary"]["ce_reviews_per_million"])
            for key, value in inputs_for(p).items():
                self.assertEqual(row["inputs"][key], value)

    def test_post_period_does_not_change_features(self):
        p = next(p for p in self.evidence["projects"] if p["primary"]["eligible"])
        changed = copy.deepcopy(p)
        for band in ("near", "far"):
            changed["periods"][band]["post"] = {"n_reviews": 987654321, "negative_share": 0.999}
        changed["primary"]["ce_reviews_per_million"] = -54321
        self.assertEqual(inputs_for(p), inputs_for(changed))

    def test_predefined_candidates_common_rows_and_reproducible(self):
        rebuilt = fit_artifact(self.evidence, include_advanced=False)
        self.assertEqual(rebuilt["selected_model"], self.model["selected_model"])
        for key, candidate in rebuilt["candidates"].items():
            for field in ("coefficients", "intercept", "project_metrics", "city_metrics"):
                assert_numeric_tree(self, candidate[field], self.model["candidates"][key][field], f"{key}.{field}")
        names = set(self.model["candidates"])
        self.assertEqual(names, {"baseline", "text", "trend", "advanced_text"})
        for candidate in self.model["candidates"].values():
            self.assertEqual(len(candidate["held_out"]), self.model["n_projects"])
            self.assertNotEqual([r["project_prediction"] for r in candidate["held_out"]],
                                [r["ce"] for r in candidate["parity_cases"]])
            self.assertTrue(all("post" not in field for field in candidate["feature_names"]))
            errors = [r["city_absolute_error"] for r in candidate["held_out"]]
            self.assertAlmostEqual(candidate["city_metrics"]["mae"], float(np.mean(errors)))
            self.assertEqual(candidate["empirical_error_radius"], max(errors))

    def test_selected_challenger_improves_both_holdouts(self):
        selected = self.model["selected_model"]
        if selected != "baseline":
            for kind in ("city_metrics", "project_metrics"):
                self.assertLess(self.model["candidates"][selected][kind]["mae"],
                                self.model["candidates"]["baseline"][kind]["mae"])
        required = {k for k, v in self.model["feature_schema"].items() if v["required"]}
        self.assertEqual(required, set(self.model["candidates"][selected]["feature_names"]))

    def test_shared_city_holdout_and_timing_sensitivities_present(self):
        self.assertLess(self.model["n_cities"], self.model["n_projects"])
        result = self.model["sensitivities"]["exclude_pandemic_and_construction_overlap"]
        self.assertTrue(any("Indianapolis" in p for p in result["excluded"]))
        self.assertTrue(any("Rail Park" in p for p in result["excluded"]))
        self.assertTrue(any("Gateway" in p for p in result["excluded"]))

    def test_advanced_fold_fit_excludes_shared_and_future_text(self):
        info = self.model["advanced_text"]
        self.assertEqual(len(info["fold_audit"]), self.model["n_projects"] + self.model["n_cities"])
        self.assertTrue(all(f["shared_review_overlap"] == 0 for f in info["fold_audit"]))
        self.assertTrue(any(f["excluded_training_review_memberships"] > 0 for f in info["fold_audit"]))
        self.assertTrue(all(n <= 500 for n in info["sampling"]["project_reviews"].values()))
        example = {"review_id": "shared", "business_id": "b", "text": "Great walking access", "memberships": [["train", "near", "pre"]],
                   "all_memberships": [["train", "near", "pre"], ["held", "far", "post"]]}
        self.assertTrue(blocked_record(example, {"held"}, set(), {}))
        self.assertTrue(blocked_record(example, set(), {"City"}, {"held": "City"}))
        self.assertFalse(blocked_record(example, {"other"}, set(), {}))
        post = dict(example, review_id="post-only", memberships=[["train", "near", "post"]])
        sample = select_sample({"records": [example, post]}, ["train"])
        self.assertEqual([r["review_id"] for r in sample["train"]], ["shared"])
        self.assertEqual(info["representation_id"], info["basis_version"])
        for row in self.model["training_rows"]:
            self.assertEqual(row["inputs"]["topic_basis_version"], info["basis_version"])
            self.assertAlmostEqual(sum(row["inputs"][f"topic_{i}"] for i in range(1, 6)), 1)


if __name__ == "__main__":
    unittest.main()
