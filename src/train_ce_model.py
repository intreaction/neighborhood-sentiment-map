"""Fit and audit a small project-level Capital Efficiency research model.

The model predicts project CE directly from pre-opening review activity,
baseline-reviewed businesses, and reported/proposed cost. No count of
businesses observed only after opening is used as a prediction feature.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/derived/ce_project_training.csv"
OUT = ROOT / "data/derived/ce_trained_model.json"
FEATURES = ("log_pre_reviews_per_active_business", "log_cost_millions", "log_baseline_reviewed")
MIN_BASELINE_REVIEWED = 20
RIDGE_ALPHA = 10.0


def feature_frame(df):
    """Values available before the proposed project opens."""
    return pd.DataFrame({
        FEATURES[0]: np.log1p(df["near_pre_reviews"] / df["near_baseline_reviewed"]),
        FEATURES[1]: np.log1p(df["cost_millions"]),
        FEATURES[2]: np.log1p(df["near_baseline_reviewed"]),
    }, index=df.index)


def load_eligible(path=DATA):
    all_projects = pd.read_csv(path)
    eligible = all_projects.loc[
        (all_projects.near_baseline_reviewed >= MIN_BASELINE_REVIEWED)
        & (all_projects.near_pre_reviews > 0)
        & (all_projects.far_pre_reviews > 0)
        & (all_projects.near_listings > 0)
        & (all_projects.cost_millions > 0)
    ].copy().reset_index(drop=True)
    return all_projects, eligible


def fit_and_evaluate(data=DATA):
    all_projects, eligible = load_eligible(data)
    X = feature_frame(eligible)
    y = eligible.ce_reviews_per_million.to_numpy()
    loo = LeaveOneOut()
    baseline = cross_val_predict(DummyRegressor(strategy="mean"), X, y, cv=loo)
    model = make_pipeline(StandardScaler(), Ridge(alpha=RIDGE_ALPHA))
    held_out = cross_val_predict(model, X, y, cv=loo)
    observed_ce = y
    baseline_ce, held_out_ce = baseline, held_out
    metrics = {
        "n_projects_total": int(len(all_projects)),
        "n_projects_trained": int(len(eligible)),
        "excluded_projects": sorted(set(all_projects.project) - set(eligible.project)),
        "mae_ce_reviews_per_million": float(mean_absolute_error(observed_ce, held_out_ce)),
        "baseline_mae_ce_reviews_per_million": float(mean_absolute_error(observed_ce, baseline_ce)),
        "sign_accuracy": float(np.mean(np.sign(held_out) == np.sign(y))),
        "baseline_sign_accuracy": float(np.mean(np.sign(baseline) == np.sign(y))),
    }
    model.fit(X, y)
    scaler, ridge = model.steps[0][1], model.steps[1][1]
    audit = []
    for row, pred, base in zip(eligible.to_dict("records"), held_out_ce, baseline_ce):
        audit.append({"project": row["project"], "city": row["city"],
                      "geometry_quality": row["geometry_quality"],
                      "observed_ce": row["ce_reviews_per_million"],
                      "held_out_ce": float(pred), "baseline_held_out_ce": float(base),
                      "absolute_error": abs(row["ce_reviews_per_million"] - pred)})
    artifact = {
        "version": "ce-project-ridge-v2",
        "training_target": "growth-adjusted excess Yelp reviews per $1M reported project cost",
        "ce_unit": "net Yelp reviews per $1M reported project cost",
        "status": "research_prototype_not_validated_for_budget_decisions",
        "feature_names": list(FEATURES),
        "feature_transform": "log1p([near_pre_reviews/near_baseline_reviewed, cost_millions, near_baseline_reviewed])",
        "feature_means": scaler.mean_.tolist(),
        "feature_scales": scaler.scale_.tolist(),
        "intercept": float(ridge.intercept_),
        "coefficients": ridge.coef_.tolist(),
        "alpha": RIDGE_ALPHA,
        "training_feature_min": X.min().tolist(),
        "training_feature_max": X.max().tolist(),
        "holdout_method": "leave-one-project-out; each test project omitted from its training fold",
        "metrics": metrics,
        "held_out_projects": audit,
        "warnings": [
            "Only 10 independent projects meet the minimum baseline support rule.",
            "Six expansion projects use a 500 m center proxy instead of a mapped project footprint.",
            "Yelp review activity is not a causal estimate of investment impact, economic return, or resident welfare.",
            "Reported project costs have mixed public and private scope; budget response is not identified.",
        ],
    }
    return artifact, model, eligible


def main():
    artifact, _, _ = fit_and_evaluate()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n")
    print(f"Wrote {OUT}")
    print(json.dumps(artifact["metrics"], indent=2))


if __name__ == "__main__":
    main()
