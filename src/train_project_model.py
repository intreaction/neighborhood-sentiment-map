"""Predefined project-level CE models with project and city holdouts.

Consumes the same evidence artifact displayed by the product. Historical legacy
models are intentionally untouched. No post-period measurement enters X.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import LeaveOneGroupOut, LeaveOneOut, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from project_advanced_model import FIELDS as ADVANCED, evaluate_advanced

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/derived/project_evidence.json"
OUT = ROOT / "data/derived/project_model.json"
ALPHA = 10.0
BASE = ["pre_reviews_per_business", "cost_millions", "baseline_reviewed"]
TEXT = ["place_share", "access_negative_share", "publicrealm_negative_share"]
CANDIDATES = {"baseline": BASE, "text": BASE + TEXT,
              "trend": BASE + ["early_relative_trend"], "advanced_text": BASE + ADVANCED}
DEFINITIONS = {
    "pre_reviews_per_business": dict(label="Baseline reviews per reviewed business", unit="reviews over two baseline years", transform="log1p"),
    "cost_millions": dict(label="Reported or proposed capital cost", unit="$ million, nominal reported basis", transform="log1p"),
    "baseline_reviewed": dict(label="Businesses with baseline reviews", unit="businesses within 500 m", transform="log1p"),
    "place_share": dict(label="Place-discussion share", unit="fraction of baseline reviews", transform="identity"),
    "access_negative_share": dict(label="Access-friction share", unit="fraction of baseline reviews", transform="identity"),
    "publicrealm_negative_share": dict(label="Public-realm complaint share", unit="fraction of baseline reviews", transform="identity"),
    "early_relative_trend": dict(label="Baseline relative activity trend", unit="near minus farther log growth, early to pre", transform="identity"),
}
DEFINITIONS.update({name: dict(label=f"Learned review topic {i+1}", unit="fraction in fitted topic basis", transform="identity") for i, name in enumerate(ADVANCED[:5])})
DEFINITIONS.update({
    "topic_diversity": dict(label="Learned topic diversity", unit="normalized entropy of project topic mixture", transform="identity"),
    "review_length_log": dict(label="Mean log review length", unit="mean log(1 + word tokens)", transform="identity"),
    "lexical_diversity": dict(label="Mean lexical diversity", unit="unique words / total words per review; length-dependent", transform="identity"),
})


def inputs_for(project):
    f = project["features"]
    periods = project["periods"]
    near, far = periods["near"], periods["far"]
    def n(band, period):
        return float(band[period]["n_reviews"])
    return {
        "cost_millions": float(project["cost_millions"]),
        "baseline_reviewed": float(f["near_baseline_reviewed"]),
        "pre_reviews_per_business": float(f["baseline_review_intensity"]),
        "place_share": float(f["place_discussion_share"]),
        "access_negative_share": float(f["access_friction_share"]),
        "publicrealm_negative_share": float(f["public_realm_complaint_share"]),
        "early_relative_trend": math.log((n(near, "pre") + 1) / (n(near, "early") + 1))
            - math.log((n(far, "pre") + 1) / (n(far, "early") + 1)),
    }


def transform(inputs, names):
    return [math.log1p(inputs[n]) if DEFINITIONS[n]["transform"] == "log1p" else inputs[n] for n in names]


def metrics(y, predictions):
    errors = np.abs(y - predictions)
    return {"n": len(y), "mae": float(mean_absolute_error(y, predictions)),
            "median_absolute_error": float(np.median(errors)),
            "max_absolute_error": float(np.max(errors)),
            "sign_accuracy": float(np.mean(np.sign(y) == np.sign(predictions)))}


def sensitivity(rows, exclude_terms):
    keep = [r for r in rows if not any(term in r["project"].lower() for term in exclude_terms)]
    excluded = [r["project"] for r in rows if r not in keep]
    result = {"excluded": excluded, "n_projects": len(keep), "n_cities": len({r["city"] for r in keep})}
    if len(keep) < 4 or result["n_cities"] < 3:
        return dict(result, status="insufficient_support")
    y = np.array([r["observed_ce"] for r in keep])
    groups = [r["city"] for r in keep]
    cvp = list(LeaveOneOut().split(y))
    cvc = list(LeaveOneGroupOut().split(y, groups=groups))
    result["candidates"] = {}
    for name, names in CANDIDATES.items():
        if name == "advanced_text":
            continue  # No globally fitted topic features in reduced-case validation.
        X = np.array([transform(r["inputs"], names) for r in keep])
        fitted = make_pipeline(StandardScaler(), Ridge(alpha=ALPHA))
        result["candidates"][name] = {
            "project_metrics": metrics(y, cross_val_predict(fitted, X, y, cv=cvp)),
            "city_metrics": metrics(y, cross_val_predict(fitted, X, y, cv=cvc)),
        }
    result["mean_baseline"] = {
        "project_metrics": metrics(y, cross_val_predict(DummyRegressor(), np.zeros((len(y), 1)), y, cv=cvp)),
        "city_metrics": metrics(y, cross_val_predict(DummyRegressor(), np.zeros((len(y), 1)), y, cv=cvc)),
    }
    return dict(result, status="exploratory_sensitivity_not_model_selection")


def fit_artifact(evidence, include_advanced=True):
    rows, excluded = [], []
    for p in evidence["projects"]:
        reason = p["primary"].get("reason")
        if not p["primary"]["eligible"]:
            excluded.append({"id": p["id"], "project": p["project"], "reason": reason or "Insufficient outcome support"})
            continue
        try:
            inputs = inputs_for(p)
            target = float(p["primary"]["ce_reviews_per_million"])
            if not all(math.isfinite(v) for v in [target, *inputs.values()]):
                raise ValueError("Non-finite measurements")
            if inputs["baseline_reviewed"] < 20 or inputs["cost_millions"] <= 0:
                raise ValueError("Insufficient baseline or invalid cost")
            if inputs["pre_reviews_per_business"] <= 0 or any(not 0 <= inputs[k] <= 1 for k in TEXT):
                raise ValueError("Invalid baseline review intensity or text fraction")
        except (KeyError, TypeError, ValueError) as exc:
            excluded.append({"id": p["id"], "project": p["project"], "reason": "Incomplete common evaluation features: " + str(exc)})
            continue
        rows.append({"id": p["id"], "project": p["project"], "city": p["city"],
                     "project_type": p["project_type"], "geometry_quality": p.get("geometry_quality", p.get("geometry", {}).get("kind")),
                     "cost_millions": inputs["cost_millions"], "inputs": inputs, "observed_ce": target})
    if len(rows) < 4 or len({r["city"] for r in rows}) < 3:
        raise ValueError("Need at least four complete projects across three cities for predefined validation")
    y = np.array([r["observed_ce"] for r in rows])
    groups = np.array([r["city"] for r in rows])
    project_splits = list(LeaveOneOut().split(y))
    city_splits = list(LeaveOneGroupOut().split(y, groups=groups))
    dummy_X = np.zeros((len(y), 1))
    mean_project = cross_val_predict(DummyRegressor(), dummy_X, y, cv=project_splits)
    mean_city = cross_val_predict(DummyRegressor(), dummy_X, y, cv=city_splits)
    advanced_details = None
    if include_advanced:
        from build_advanced_text import load_corpus
        import joblib
        from threadpoolctl import threadpool_limits
        with threadpool_limits(limits=1):
            advanced_features, advanced_predictions, advanced_details, encoder = evaluate_advanced(
                rows, evidence, load_corpus(), project_splits, city_splits, BASE, transform, ALPHA)
        for row in rows:
            row["inputs"].update(advanced_features[row["id"]])
            row["inputs"]["topic_basis_version"] = advanced_details["basis_version"]
        for topic in advanced_details["topics"]:
            DEFINITIONS[topic["id"]]["label"] = "Predictive topic: " + topic["label"]
        encoder_path = ROOT / "data/interim/project_evidence/model_text_basis.joblib"
        joblib.dump({"basis_version": advanced_details["basis_version"], "vectorizer": encoder[0], "nmf": encoder[1]}, encoder_path)
        advanced_details["local_encoder_path"] = str(encoder_path.relative_to(ROOT))
    candidates = {}
    for name, names in CANDIDATES.items():
        if name == "advanced_text" and not include_advanced:
            continue
        X = np.array([transform(r["inputs"], names) for r in rows])
        model = make_pipeline(StandardScaler(), Ridge(alpha=ALPHA))
        project_predictions = advanced_predictions["project"] if name == "advanced_text" else cross_val_predict(model, X, y, cv=project_splits)
        city_predictions = advanced_predictions["city"] if name == "advanced_text" else cross_val_predict(model, X, y, cv=city_splits)
        model.fit(X, y)
        scaler, ridge = model.steps[0][1], model.steps[1][1]
        z = scaler.transform(X)
        distances = np.sqrt(np.mean((z[:, None, :] - z[None, :, :]) ** 2, axis=2))
        np.fill_diagonal(distances, np.inf)
        # The most isolated training case establishes the combination boundary.
        # This is an empirical support check, not a statistical confidence region.
        threshold = float(np.max(np.min(distances, axis=1)))
        candidates[name] = {
            "feature_names": names, "feature_means": scaler.mean_.tolist(),
            "feature_scales": scaler.scale_.tolist(), "coefficients": ridge.coef_.tolist(),
            "intercept": float(ridge.intercept_), "alpha": ALPHA,
            "project_metrics": metrics(y, project_predictions), "city_metrics": metrics(y, city_predictions),
            "similarity_threshold": threshold,
            "empirical_error_radius": float(np.max(np.abs(y - city_predictions))),
            "held_out": [{"id": r["id"], "project": r["project"], "city": r["city"],
                "observed_ce": float(y[i]), "project_prediction": float(project_predictions[i]),
                "city_prediction": float(city_predictions[i]),
                "project_absolute_error": float(abs(y[i] - project_predictions[i])),
                "city_absolute_error": float(abs(y[i] - city_predictions[i]))}
                for i, r in enumerate(rows)],
            "parity_cases": [{"id": r["id"], "inputs": r["inputs"], "ce": float(pred)}
                             for r, pred in zip(rows, model.predict(X))],
        }
    base = candidates["baseline"]
    if include_advanced:
        advanced_better = all(candidates["advanced_text"][kind]["mae"] < base[kind]["mae"] for kind in ("project_metrics", "city_metrics"))
        advanced_details["promotion"] = {"improves_both_primary_holdouts": advanced_better,
            "eligible_for_default": False,
            "reason": "Timing sensitivities pending" if advanced_better else "Does not improve both primary holdouts; retain the better baseline"}
        if not advanced_better:
            advanced_details["timing_sensitivity"] = "Not run: advanced text did not improve both primary held-out comparisons, so it was not considered for default promotion."
    qualifying = [name for name in ("text", "trend") if all(
        candidates[name][metric]["mae"] < base[metric]["mae"] for metric in ("project_metrics", "city_metrics"))]
    selected = min(qualifying, key=lambda n: (candidates[n]["city_metrics"]["mae"], len(CANDIDATES[n]))) if qualifying else "baseline"
    schema = {name: dict(definition, min=min(r["inputs"][name] for r in rows),
                        max=max(r["inputs"][name] for r in rows), required=name in CANDIDATES[selected])
              for name, definition in DEFINITIONS.items() if name in rows[0]["inputs"]}
    return {
        "version": "project-ce-v2", "status": "exploratory_retrospective_model",
        "target": "Two-post-year growth-adjusted excess Yelp reviews per $1M nominal reported project cost",
        "selected_model": selected, "feature_schema": schema, "candidates": candidates,
        "selection_policy": "Predefined ridge alpha=10 and baseline/text/trend feature sets. A challenger qualifies only if MAE improves on the current three-input model in both project and city holdouts; choose the lowest city MAE among qualifying challengers, else baseline. Advanced TF-IDF/NMF text is an additional exploratory challenger with fold-isolated preprocessing; it is not eligible for default promotion until reduced-case timing sensitivities are also evaluated. This exploratory model choice reuses validation data and is not independent confirmation.",
        "advanced_text": advanced_details,
        "mean_baseline": {"project_metrics": metrics(y, mean_project), "city_metrics": metrics(y, mean_city),
            "held_out": [{"id": r["id"], "project": r["project"], "city": r["city"],
                "observed_ce": float(y[i]), "project_prediction": float(mean_project[i]),
                "city_prediction": float(mean_city[i]),
                "project_absolute_error": float(abs(y[i] - mean_project[i])),
                "city_absolute_error": float(abs(y[i] - mean_city[i]))} for i, r in enumerate(rows)]},
        "training_rows": rows, "excluded_projects": excluded,
        "sensitivities": {
            "exclude_pandemic_post_windows": sensitivity(rows, ["rail park", "gateway arch"]),
            "exclude_pandemic_and_construction_overlap": sensitivity(rows, ["rail park", "gateway arch", "indianapolis"]),
        },
        "n_projects": len(rows), "n_cities": len(set(groups)),
        "validation": {"project": "Leave one entire project out", "city": "Leave all projects in the same city out", "scaling": "Fit only on training fold", "hyperparameter_search": False},
        "uncertainty": "The displayed empirical error range uses the maximum absolute city-holdout error, symmetrically around the estimate. It is a historical error envelope, not a confidence or prediction interval and has no guaranteed coverage.",
        "conditions": ["Review activity measures online participation, not revenue, public benefit, or causal investment returns.",
            "Project type filters comparable evidence only; it does not change the fitted prediction.",
            "Costs remain nominal reported amounts with mixed historical scope and dollar years; present-day budget comparisons are provisional until costs are reconciled.",
            "The archive describes historic conditions. A new proposal requires measured catchment inputs or explicitly declared assumptions.",
            "Text signals are transparent clause-level rule measurements, not validated resident sentiment.",
            "Some baseline years overlap construction; baseline means before opening, not always before intervention. Pandemic-window and construction-overlap exclusions are reported as sensitivities.",
            "Shared cities and catchments reduce independence; city holdouts are a stronger stress test, not proof of transferability."],
        "provenance": {"evidence_version": evidence.get("version"), "evidence_method": evidence.get("method"),
            "input_period": "Only early and pre periods", "radius_m": 500,
            "text_denominator": "All near-area baseline reviews; each review counts at most once per share. A negative topic clause counts only when its target is the area.",
            "text_candidates": TEXT, "target_source": "project_evidence.projects[].primary.ce_reviews_per_million"},
    }


def main():
    raw = DATA.read_bytes()
    artifact = fit_artifact(json.loads(raw))
    artifact["provenance"]["evidence_sha256"] = hashlib.sha256(raw).hexdigest()
    temporary = OUT.with_suffix(".tmp")
    temporary.write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n")
    temporary.replace(OUT)
    print(json.dumps({"selected": artifact["selected_model"], "n": artifact["n_projects"],
                      "results": {k: {"project_mae": v["project_metrics"]["mae"], "city_mae": v["city_metrics"]["mae"]} for k, v in artifact["candidates"].items()}}, indent=2))


if __name__ == "__main__":
    main()
