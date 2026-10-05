"""Score the clause rules and VADER against labelled review text.

Labels come from the 731-item annotation sample (data/interim/project_evidence).
The current labels are AGENT labels (Claude Opus, blind to rule and VADER output)
pending human recheck; they are not independent human validation. Candidate and
stratified frames are enriched for keyword hits, so their rates are not population
prevalence. Only the random-review frame can estimate how much the keyword screen misses.
"""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from project_text import ANY, analyze_text

AGENT_REVIEWER = {'reviewer_type': 'agent', 'reviewer_id': 'claude-opus-5-5'}
TOPICS = ['walking_accessibility', 'transit', 'parking', 'safety', 'cleanliness_maintenance',
          'public_space', 'construction', 'food_service_value', 'neighborhood']
CLAUSE_FRAMES = ('candidate_clause', 'stratified_project_period_topic')
LABEL_FIELDS = ('label_target', 'label_topics', 'label_polarity', 'confidence')


def review_key(review_id):
    return hashlib.sha256(review_id.encode()).hexdigest()[:16]


def wilson(k, n, z=1.96):
    """95% Wilson score interval; None when there is no support."""
    if not n:
        return None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, centre - half), min(1.0, centre + half)]


def binary_scores(pairs):
    """pairs: (gold, predicted) booleans. Precision/recall with support and intervals."""
    pairs = [(bool(g), bool(p)) for g, p in pairs]
    tp = sum(g and p for g, p in pairs)
    fp = sum(p and not g for g, p in pairs)
    fn = sum(g and not p for g, p in pairs)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else None
    return {'n': len(pairs), 'tp': tp, 'fp': fp, 'fn': fn, 'precision': precision, 'recall': recall, 'f1': f1,
            'precision_ci': wilson(tp, tp + fp), 'recall_ci': wilson(tp, tp + fn)}


def vader_label(compound):
    return 'positive' if compound >= .05 else 'negative' if compound <= -.05 else 'neutral'


def rule_view(text):
    """Collapse the rule engine's clause evidence into one target, polarity and topic set."""
    result = analyze_text(text)
    evidence = result['evidence']
    targets = {e['target'] for e in evidence}
    target = 'none' if not evidence else 'area' if 'area' in targets else 'business' if targets == {'business'} else 'unclear'
    return {'target': target,
            'negative_area': any(e['target'] == 'area' and e['polarity'] == 'negative' for e in evidence),
            'topics': {e['topic'] for e in evidence},
            'place': result['place'],
            'screen_hit': bool(ANY.search(text)),
            'vader': vader_label(result['compound'])}


def merge(rows, labels):
    """Attach labels to sample rows by position; every row must be labelled exactly once."""
    by_item = {l['item']: l for l in labels}
    if sorted(by_item) != list(range(len(rows))):
        raise ValueError('Labels must cover every annotation item exactly once.')
    return [{**row, **{k: by_item[i][k] for k in LABEL_FIELDS}, 'place_spans': by_item[i].get('place_spans', []),
             'notes': by_item[i].get('notes', ''), **AGENT_REVIEWER} for i, row in enumerate(rows)]


def evaluate(records):
    clauses = [r for r in records if r['sampling_frame'] in CLAUSE_FRAMES]
    reviews = [r for r in records if r['sampling_frame'] == 'random_review']
    views = {id(r): rule_view(r['text']) for r in records}
    decided = [r for r in clauses if r['label_target'] != 'unclear']
    gold_area = lambda r: r['label_target'] in ('area', 'mixed')
    gold_negative_area = lambda r: gold_area(r) and r['label_polarity'] in ('negative', 'mixed')

    by_frame = {frame: binary_scores([(gold_area(r), views[id(r)]['target'] == 'area') for r in decided if r['sampling_frame'] == frame])
                for frame in CLAUSE_FRAMES}
    polar = [r for r in clauses if r['label_polarity'] in ('positive', 'negative', 'neutral')]
    confusion = Counter((r['label_polarity'], views[id(r)]['vader']) for r in polar)
    per_class = {}
    for c in ('positive', 'negative', 'neutral'):
        per_class[c] = binary_scores([(r['label_polarity'] == c, views[id(r)]['vader'] == c) for r in polar])
    f1s = [s['f1'] or 0 for s in per_class.values()]
    topics = {t: binary_scores([(t in r['label_topics'], t in views[id(r)]['topics']) for r in clauses]) for t in TOPICS}
    place_reviews = [r for r in reviews if r['label_target'] != 'none']
    return {
        'labels': {**AGENT_REVIEWER, 'status': 'Agent labels pending human recheck; not independent human validation.',
                   'n_items': len(records), 'n_clauses': len(clauses), 'n_random_reviews': len(reviews),
                   'confidence': dict(Counter(r['confidence'] for r in records)),
                   'clause_targets': dict(Counter(r['label_target'] for r in clauses)),
                   'clause_polarity': dict(Counter(r['label_polarity'] for r in clauses))},
        'area_target': {**binary_scores([(gold_area(r), views[id(r)]['target'] == 'area') for r in decided]),
                        'by_frame': by_frame, 'excluded_unclear': len(clauses) - len(decided)},
        'negative_area': binary_scores([(gold_negative_area(r), views[id(r)]['negative_area']) for r in decided]),
        'vader_polarity': {'n': len(polar), 'accuracy': sum(r['label_polarity'] == views[id(r)]['vader'] for r in polar) / len(polar) if polar else None,
                           'macro_f1': sum(f1s) / 3, 'per_class': per_class,
                           'confusion': [{'label': g, 'vader': p, 'n': n} for (g, p), n in sorted(confusion.items())]},
        'topics': topics,
        'random_reviews': {'n': len(reviews), 'with_place_mention': len(place_reviews),
                           'place_rate_ci': wilson(len(place_reviews), len(reviews)),
                           'keyword_screen': binary_scores([(r['label_target'] != 'none', views[id(r)]['screen_hit']) for r in reviews]),
                           'area_rules': binary_scores([(r['label_target'] in ('area', 'mixed'), views[id(r)]['place']) for r in reviews])}
    }


def export(records, metrics, derived_dir):
    """Write text-free labels (hashed keys) and metrics for the repository."""
    out = Path(derived_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / 'agent_labels.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['review_key', 'sampling_frame', 'stratum_project', 'stratum_period', 'label_target', 'label_topics', 'label_polarity', 'confidence', 'reviewer_type', 'reviewer_id'])
        for r in records:
            w.writerow([review_key(r['review_id']), r['sampling_frame'], r.get('stratum_project', ''), r.get('stratum_period', ''), r['label_target'],
                        '|'.join(r['label_topics']), r['label_polarity'], r['confidence'], r['reviewer_type'], r['reviewer_id']])
    (out / 'metrics.json').write_text(json.dumps(metrics, indent=1))


def embedding_benchmark(records, encode, folds=5, seed=0):
    """Logistic regression on sentence embeddings, cross-validated by business.

    `encode` maps a list of texts to an embedding matrix (all-MiniLM-L6-v2 in the
    notebook). Folds group by business_id so one business never sits on both sides.
    The same items are scored for the rules and VADER, so the comparison is paired.
    """
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupKFold, cross_val_predict

    clauses = [r for r in records if r['sampling_frame'] in CLAUSE_FRAMES and r['label_target'] != 'unclear']
    X = np.asarray(encode([r['text'] for r in clauses]))
    groups = [r['business_id'] for r in clauses]
    views = [rule_view(r['text']) for r in clauses]
    cv = GroupKFold(n_splits=folds)

    def fit_predict(y, idx=None):
        idx = list(range(len(clauses))) if idx is None else idx
        model = LogisticRegression(max_iter=2000, class_weight='balanced', random_state=seed)
        return cross_val_predict(model, X[idx], np.asarray(y), groups=[groups[i] for i in idx], cv=cv)

    area = [r['label_target'] in ('area', 'mixed') for r in clauses]
    negative = [a and r['label_polarity'] in ('negative', 'mixed') for a, r in zip(area, clauses)]
    polar = [i for i, r in enumerate(clauses) if r['label_polarity'] in ('positive', 'negative', 'neutral')]
    gold_pol = [clauses[i]['label_polarity'] for i in polar]
    pred_pol = fit_predict(gold_pol, polar)

    def macro(gold, pred):
        scores = [binary_scores([(g == c, p == c) for g, p in zip(gold, pred)])['f1'] or 0 for c in ('positive', 'negative', 'neutral')]
        return sum(scores) / 3

    return {
        'n_clauses': len(clauses), 'folds': folds, 'grouping': 'business_id',
        'area_target': {'rules': binary_scores(list(zip(area, [v['target'] == 'area' for v in views]))),
                        'embedding_lr': binary_scores(list(zip(area, fit_predict(area))))},
        'negative_area': {'rules': binary_scores(list(zip(negative, [v['negative_area'] for v in views]))),
                          'embedding_lr': binary_scores(list(zip(negative, fit_predict(negative))))},
        'polarity': {'n': len(polar),
                     'vader': {'accuracy': sum(g == views[i]['vader'] for g, i in zip(gold_pol, polar)) / len(polar), 'macro_f1': macro(gold_pol, [views[i]['vader'] for i in polar])},
                     'embedding_lr': {'accuracy': float(np.mean([g == p for g, p in zip(gold_pol, pred_pol)])), 'macro_f1': float(macro(gold_pol, list(pred_pol)))}}
    }
