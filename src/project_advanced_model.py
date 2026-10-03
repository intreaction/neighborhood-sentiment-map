"""Fold-isolated TF-IDF/NMF features for the project CE challenger.

The descriptive topic model elsewhere in the product is not used here. Every
validation fold learns its own vocabulary, IDF and topics from training reviews.
"""
import hashlib
import json
import re

import numpy as np
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

CAP = 500
SEED = 42
TOPICS = 5
FIELDS = [f"topic_{i + 1}" for i in range(TOPICS)] + ["topic_diversity", "review_length_log", "lexical_diversity"]
TOKEN = re.compile(r"\b[a-zA-Z]{2,}\b")


def summarize_audit(details):
    audit = details["fold_audit"]
    details["imputation_summary"] = {
        "folds_with_imputed_training_projects": sum(bool(f["training_projects_with_text_imputed"]) for f in audit),
        "total_folds": len(audit),
        "imputed_project_fold_memberships": sum(len(f["training_projects_with_text_imputed"]) for f in audit),
        "heldout_review_overlap_total": sum(f["shared_review_overlap"] for f in audit),
    }
    details["parameters"] = {"ngram_range": [1, 2], "max_features": 8000, "min_df": 2,
        "max_df": .95, "stop_words": "english", "sublinear_tf": True, "strip_accents": "unicode",
        "nmf_components": TOPICS, "nmf_init": "nndsvda", "nmf_max_iter": 500, "random_state": SEED}
    return details


def select_sample(corpus, project_ids):
    by_project = {pid: [] for pid in project_ids}
    for record in corpus["records"]:
        if not record.get("text", "").strip():
            continue
        for pid, band, period in record["memberships"]:
            if pid in by_project and band == "near" and period == "pre":
                by_project[pid].append(record)
    for pid, records in by_project.items():
        unique = {r["review_id"]: r for r in records}
        by_project[pid] = sorted(unique.values(), key=lambda r: hashlib.sha256(r["review_id"].encode()).hexdigest())[:CAP]
        if not by_project[pid]:
            raise ValueError("No baseline advanced-text reviews for " + pid)
    return by_project


def blocked_record(record, held_ids, held_cities, city_for_project):
    for pid, band, period in record.get("all_memberships", record["memberships"]):
        if held_cities and city_for_project.get(pid) in held_cities:
            return True
        if pid in held_ids:
            return True
    return False


def fit_basis(records):
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=8000,
        min_df=2, max_df=.95, stop_words="english", sublinear_tf=True, strip_accents="unicode")
    matrix = vectorizer.fit_transform([r["text"] for r in records])
    nmf = NMF(n_components=TOPICS, init="nndsvda", random_state=SEED, max_iter=500)
    nmf.fit(matrix)
    return vectorizer, nmf


def aggregate_features(records, vectorizer, nmf):
    if not records:
        raise ValueError("Shared-review exclusions left a project without training text")
    weights = nmf.transform(vectorizer.transform([r["text"] for r in records]))
    totals = weights.sum(axis=1)
    probabilities = weights / np.where(totals > 0, totals, 1)[:, None]
    mixture = probabilities.mean(axis=0)
    if mixture.sum() > 0:
        mixture /= mixture.sum()
    positive = mixture[mixture > 0]
    entropy = float(-np.sum(positive * np.log(positive)) / np.log(TOPICS))
    tokens = [TOKEN.findall(r["text"].lower()) for r in records]
    length = float(np.mean([np.log1p(len(t)) for t in tokens]))
    diversity = float(np.mean([len(set(t)) / max(1, len(t)) for t in tokens]))
    return {**{f"topic_{i+1}": float(mixture[i]) for i in range(TOPICS)},
            "topic_diversity": entropy, "review_length_log": length, "lexical_diversity": diversity}


def evaluate_advanced(rows, evidence, corpus, project_splits, city_splits, base_fields, base_transform, alpha):
    city_for_project = {p["id"]: p["city"] for p in evidence["projects"]}
    sample = select_sample(corpus, [r["id"] for r in rows])
    y = np.array([r["observed_ce"] for r in rows])
    results = {}
    audit = []
    for mode, splits in (("project", project_splits), ("city", city_splits)):
        predictions = np.zeros(len(rows))
        for train, test in splits:
            held_ids = {rows[i]["id"] for i in test}
            held_cities = {rows[i]["city"] for i in test} if mode == "city" else set()
            allowed = {rows[i]["id"]: [r for r in sample[rows[i]["id"]]
                if not blocked_record(r, held_ids, held_cities, city_for_project)] for i in train}
            fit_records = {r["review_id"]: r for records in allowed.values() for r in records}
            test_review_ids = {r["review_id"] for i in test for r in sample[rows[i]["id"]]}
            overlap = set(fit_records) & test_review_ids
            if overlap:
                raise AssertionError("Held-out text leaked into unsupervised training")
            ordered = sorted(fit_records.values(), key=lambda r: r["review_id"])
            vectorizer, nmf = fit_basis(ordered)
            def features(i, records):
                if not records:
                    return base_transform(rows[i]["inputs"], base_fields) + [float("nan")] * len(FIELDS)
                advanced = aggregate_features(records, vectorizer, nmf)
                return base_transform(rows[i]["inputs"], base_fields) + [advanced[k] for k in FIELDS]
            X_train = np.array([features(i, allowed[rows[i]["id"]]) for i in train])
            X_test = np.array([features(i, sample[rows[i]["id"]]) for i in test])
            ridge = make_pipeline(SimpleImputer(strategy="mean"), StandardScaler(), Ridge(alpha=alpha))
            ridge.fit(X_train, y[train])
            predictions[test] = ridge.predict(X_test)
            audit.append({"mode": mode, "held_out_projects": sorted(held_ids),
                "held_out_cities": sorted(held_cities), "training_unique_reviews": len(ordered),
                "held_out_unique_reviews": len(test_review_ids), "shared_review_overlap": len(overlap),
                "excluded_training_review_memberships": sum(len(sample[rows[i]["id"]]) - len(allowed[rows[i]["id"]]) for i in train),
                "training_projects_with_text_imputed": [rows[i]["id"] for i in train if not allowed[rows[i]["id"]]],
                "training_vocabulary_size": len(vectorizer.vocabulary_), "nmf_iterations": nmf.n_iter_,
                "training_review_id_sha256": hashlib.sha256("\n".join(sorted(fit_records)).encode()).hexdigest()})
        results[mode] = predictions
    all_records = {r["review_id"]: r for records in sample.values() for r in records}
    vectorizer, nmf = fit_basis(sorted(all_records.values(), key=lambda r: r["review_id"]))
    vocabulary = vectorizer.get_feature_names_out()
    encoder = {"vocabulary": vocabulary.tolist(), "idf": vectorizer.idf_.tolist(), "components": nmf.components_.tolist()}
    basis_version = "ce-nmf5-" + hashlib.sha256(json.dumps(encoder, separators=(",", ":")).encode()).hexdigest()[:16]
    project_features = {pid: aggregate_features(records, vectorizer, nmf) for pid, records in sample.items()}
    topics = [{"id": f"topic_{i+1}", "label": " / ".join(vocabulary[np.argsort(component)[-3:][::-1]]),
               "terms": vocabulary[np.argsort(component)[-12:][::-1]].tolist()} for i, component in enumerate(nmf.components_)]
    details = {"basis_version": basis_version, "representation_id": basis_version, "topics": topics,
        "method": "TF-IDF unigrams/bigrams (8,000 terms maximum) and five NMF topics; normalized per-review topic mixtures aggregated by project, normalized topic entropy, mean log token count and lexical diversity.",
        "validation": "Vocabulary, IDF, NMF, scaling and ridge fitted inside every held-out fold. Every review with any held-out-project membership is excluded from both unsupervised fitting and training-project aggregation; city folds exclude all records with memberships in the held-out city.",
        "topic_diversity_definition": "Normalized Shannon entropy of the project-aggregated topic mixture, not mean review entropy. Reviews with no basis vocabulary do not contribute topic mass.",
        "lexical_diversity_caveat": "Mean per-review type/token ratio depends strongly on length; mean log review length enters the same challenger, but this does not make it a civic-quality measure.",
        "sampling": {"maximum_reviews_per_project": CAP, "selection": "lowest SHA256(review_id), near/pre only", "seed": SEED,
                     "unique_reviews": len(all_records), "project_reviews": {pid: len(rs) for pid, rs in sample.items()}},
        "corpus_metadata": corpus.get("metadata"), "fold_audit": audit,
        "input_contract": "Proposal topic values must be generated with this exact basis_version, not the descriptive topic basis. Global descriptive topics are never used for holdout evaluation.",
        "empty_training_text": "Strict shared-review exclusions can remove all sampled text for a training project. Its advanced fields are then imputed from the means of other training projects inside that fold, retaining the same train/test project rows for every candidate.",
        "interpretation": "Learned topics describe recurring review vocabulary, often food or service. They are not validated civic themes or causal project effects.",
        "timing_sensitivity": "Advanced text has project/city holdouts; reduced-case timing sensitivities are not evaluated for this candidate."}
    return project_features, results, summarize_audit(details), (vectorizer, nmf)
