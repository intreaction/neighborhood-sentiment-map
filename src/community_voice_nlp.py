"""Community Voice Aspect Extractor and Text Diagnostics.

Distinguishes Community Voice (neighborhood, walkability, transit, surroundings,
cleanliness, public space) from Commercial Transaction commentary (food,
drink, service, price).

Computes:
  - Community Voice Share (CVS)
  - Aspect-level mention rates (pre vs. post)
  - Evaluation diagnostics (precision, recall, F1) on calibration benchmarks
  - Tagged qualitative excerpts for the exploration interface

Usage:
  python3 src/community_voice_nlp.py [--output PATH]
"""
import argparse
import json
from pathlib import Path
import re
from typing import Dict, List, Set, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
STUDY_DATA = ROOT / "docs" / "coursework" / "milestone-2-eda" / "study_data"
INTERIM_DATA = ROOT / "data" / "interim"

# Aspect vocabulary patterns
ASPECT_PATTERNS = {
    # Community Voice / Place Aspects
    "access_transit": {
        "group": "community",
        "label": "Access & Transit",
        "terms": (
            r"\b(?:walk|walkable|walkability|walking|sidewalks?|pedestrian|"
            r"bike|biking|bikes?|bicycle|bike rack|bike path|trail|greenway|"
            r"transit|streetcar|train|subway|bus|bus stop|metro|"
            r"parking|parked|garage|valet|wheelchair|accessible|accessibility)\b"
        ),
    },
    "surroundings_safety": {
        "group": "community",
        "label": "Surroundings & Safety",
        "terms": (
            r"\b(?:neighborhood|neighbourhood|surroundings|street|block|district|area|"
            r"street lighting|lighting|streetlights?|potholes?|graffiti|"
            r"safe|safety|unsafe|sketchy|dangerous|crime|revitalization|development|construction)\b"
        ),
    },
    "cleanliness_public_space": {
        "group": "community",
        "label": "Cleanliness & Public Space",
        "terms": (
            r"\b(?:park|plaza|square|green space|waterfront|riverfront|outdoor seating|patio|"
            r"trees|landscaping|scenery|public space|fountain|monument|"
            r"clean|cleanliness|dirty|filthy|litter|trash|garbage|debris|upkeep|maintenance)\b"
        ),
    },
    # Commercial / Transactional Aspects
    "food_drinks": {
        "group": "commercial",
        "label": "Food & Products",
        "terms": (
            r"\b(?:food|meal|meals|dish|dishes|menu|taste|tasty|delicious|flavor|"
            r"chicken|pizza|burger|burgers|salad|sandwich|sandwiches|tacos?|burritos?|"
            r"pasta|fries|steak|seafood|sushi|desserts?|breakfast|lunch|dinner|"
            r"drinks?|cocktail|cocktails|beer|beers|wine|coffee|tea|beverage)\b"
        ),
    },
    "service_staff": {
        "group": "commercial",
        "label": "Service & Staff",
        "terms": (
            r"\b(?:service|staff|server|servers|waiter|waiters|waitress|cashier|"
            r"employee|employees|bartender|management|customer service|rude|friendly|attentive)\b"
        ),
    },
    "price_value": {
        "group": "commercial",
        "label": "Price & Value",
        "terms": (
            r"\b(?:price|prices|pricing|expensive|overpriced|affordable|cheap|"
            r"value|worth|cost|costly|bill|check|deal|discount)\b"
        ),
    },
}

COMPILED_PATTERNS = {
    name: re.compile(spec["terms"], re.IGNORECASE)
    for name, spec in ASPECT_PATTERNS.items()
}

# Calibration Benchmark for Unit Diagnostics
CALIBRATION_BENCHMARKS: List[Tuple[str, Set[str], Set[str]]] = [
    # (text, expected_community_aspects, expected_commercial_aspects)
    (
        "The new greenway path makes walking to this café safe and pleasant.",
        {"access_transit", "surroundings_safety"},
        set(),
    ),
    (
        "Construction and lack of street lighting make this neighborhood sketchy at night.",
        {"surroundings_safety"},
        set(),
    ),
    (
        "The park across the street is clean, and the outdoor patio has beautiful landscaping.",
        {"cleanliness_public_space"},
        set(),
    ),
    (
        "The streetcar stop is right outside, but finding parking is difficult.",
        {"access_transit"},
        set(),
    ),
    (
        "Our server was incredibly rude and the burger was salty and overpriced.",
        set(),
        {"food_drinks", "service_staff", "price_value"},
    ),
    (
        "Great cocktails and friendly bartenders, but prices are a bit high.",
        set(),
        {"food_drinks", "service_staff", "price_value"},
    ),
    (
        "Delicious pizza, but the sidewalk outside had trash and litter everywhere.",
        {"cleanliness_public_space"},
        {"food_drinks"},
    ),
    (
        "A wonderful local spot in our neighborhood with friendly staff and cheap beers.",
        {"surroundings_safety"},
        {"food_drinks", "service_staff", "price_value"},
    ),
]


def classify_text(text: str) -> Dict[str, bool]:
    """Return dictionary of aspect presence booleans."""
    return {
        name: bool(pattern.search(text))
        for name, pattern in COMPILED_PATTERNS.items()
    }


def analyze_review_aspects(text: str) -> Dict:
    """Analyze a single review for community vs. commercial voice."""
    aspects = classify_text(text)
    comm_hits = [
        name for name, hit in aspects.items()
        if hit and ASPECT_PATTERNS[name]["group"] == "community"
    ]
    comm_commercial = [
        name for name, hit in aspects.items()
        if hit and ASPECT_PATTERNS[name]["group"] == "commercial"
    ]

    return {
        "has_community_voice": len(comm_hits) > 0,
        "has_commercial_voice": len(comm_commercial) > 0,
        "community_aspects": comm_hits,
        "commercial_aspects": comm_commercial,
        "aspect_flags": aspects,
    }


def run_diagnostics() -> Dict[str, float]:
    """Evaluate classifier performance against calibration set."""
    tp_comm, fp_comm, fn_comm = 0, 0, 0
    tp_comm_any, fp_comm_any, fn_comm_any = 0, 0, 0

    for text, exp_comm, _ in CALIBRATION_BENCHMARKS:
        res = analyze_review_aspects(text)
        detected_comm = set(res["community_aspects"])

        # Any-community detection
        exp_any = len(exp_comm) > 0
        det_any = res["has_community_voice"]
        if exp_any and det_any:
            tp_comm_any += 1
        elif not exp_any and det_any:
            fp_comm_any += 1
        elif exp_any and not det_any:
            fn_comm_any += 1

        # Aspect-level detection
        for a in exp_comm:
            if a in detected_comm:
                tp_comm += 1
            else:
                fn_comm += 1
        for a in detected_comm:
            if a not in exp_comm:
                fp_comm += 1

    prec_any = tp_comm_any / (tp_comm_any + fp_comm_any) if (tp_comm_any + fp_comm_any) > 0 else 1.0
    rec_any = tp_comm_any / (tp_comm_any + fn_comm_any) if (tp_comm_any + fn_comm_any) > 0 else 1.0
    f1_any = 2 * (prec_any * rec_any) / (prec_any + rec_any) if (prec_any + rec_any) > 0 else 0.0

    prec_aspect = tp_comm / (tp_comm + fp_comm) if (tp_comm + fp_comm) > 0 else 1.0
    rec_aspect = tp_comm / (tp_comm + fn_comm) if (tp_comm + fn_comm) > 0 else 1.0
    f1_aspect = 2 * (prec_aspect * rec_aspect) / (prec_aspect + rec_aspect) if (prec_aspect + rec_aspect) > 0 else 0.0

    return {
        "community_voice_precision": round(prec_any, 3),
        "community_voice_recall": round(rec_any, 3),
        "community_voice_f1": round(f1_any, 3),
        "aspect_level_precision": round(prec_aspect, 3),
        "aspect_level_recall": round(rec_aspect, 3),
        "aspect_level_f1": round(f1_aspect, 3),
    }


def process_review_examples(examples_path: Path, output_path: Path) -> pd.DataFrame:
    """Classify real review examples and emit structured community voice dataset."""
    if not examples_path.exists():
        raise FileNotFoundError(f"Missing review examples at {examples_path}")

    with open(examples_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_examples = data.get("examples", [])
    records = []

    for ex in raw_examples:
        text = ex.get("text", "")
        analysis = analyze_review_aspects(text)

        records.append({
            "zip": ex.get("zip"),
            "metro": ex.get("metro"),
            "quarter": ex.get("quarter"),
            "polarity": ex.get("polarity"),
            "compound": ex.get("compound"),
            "stars": ex.get("stars"),
            "text": text,
            "has_community_voice": analysis["has_community_voice"],
            "has_commercial_voice": analysis["has_commercial_voice"],
            "community_aspects": "|".join(analysis["community_aspects"]),
            "commercial_aspects": "|".join(analysis["commercial_aspects"]),
            "access_transit": analysis["aspect_flags"]["access_transit"],
            "surroundings_safety": analysis["aspect_flags"]["surroundings_safety"],
            "cleanliness_public_space": analysis["aspect_flags"]["cleanliness_public_space"],
            "food_drinks": analysis["aspect_flags"]["food_drinks"],
            "service_staff": analysis["aspect_flags"]["service_staff"],
            "price_value": analysis["aspect_flags"]["price_value"],
        })

    df = pd.DataFrame(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


def main():
    parser = argparse.ArgumentParser(description="Process community voice aspects and evaluate diagnostics.")
    parser.add_argument("--examples", type=Path, default=INTERIM_DATA / "review_topics.json", help="Path to review topics JSON.")
    parser.add_argument("--output", type=Path, default=STUDY_DATA / "community_voice_aspects.csv", help="Output path for classified review aspects.")
    args = parser.parse_args()

    print("Running Community Voice classifier diagnostics...")
    diag = run_diagnostics()
    print("Diagnostics on Calibration Benchmark:")
    for k, v in diag.items():
        print(f"  {k}: {v}")

    print(f"\nProcessing real review excerpts from {args.examples}...")
    df = process_review_examples(args.examples, args.output)
    print(f"Wrote {len(df):,} tagged review records to {args.output}")

    # Summary statistics
    comm_share = df["has_community_voice"].mean() * 100.0
    print(f"\nOverall Community Voice Share: {comm_share:.1f}% of reviews mention neighborhood/public aspects.")
    print("Breakdown by Community Aspect:")
    for col in ["access_transit", "surroundings_safety", "cleanliness_public_space"]:
        pct = df[col].mean() * 100.0
        print(f"  {col:<26}: {pct:>5.1f}%")

    print("\nBreakdown by Commercial Aspect:")
    for col in ["food_drinks", "service_staff", "price_value"]:
        pct = df[col].mean() * 100.0
        print(f"  {col:<26}: {pct:>5.1f}%")


if __name__ == "__main__":
    main()
