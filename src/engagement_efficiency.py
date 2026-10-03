"""Compute engagement and capital efficiency metrics across the five study projects.

Calculates:
  1. Net absolute review gain per $1M (CE_abs)
  2. Relative growth rate per $1M (CE_rel)
  3. Baseline-normalized efficiency rate (CE_norm)
  4. Active business expansion per $1M (CE_biz)

Enforces strict support rules:
  - Any matched cohort with pairs < 20 is flagged as low_support=True and
    suppressed from primary ranking.
  - Reports both absolute count and relative percentage metrics to prevent
    distortion from high urban density or tiny baselines.

Usage:
  python3 src/engagement_efficiency.py [--output PATH]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
STUDY_DATA = ROOT / "docs" / "coursework" / "milestone-2-eda" / "study_data"


def load_data(data_dir: Path):
    registry_path = data_dir / "project_registry.json"
    engagement_path = data_dir / "engagement.csv"
    business_growth_path = data_dir / "business_growth.csv"

    if not registry_path.exists() or not engagement_path.exists() or not business_growth_path.exists():
        raise FileNotFoundError(f"Missing required input files in {data_dir}")

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    eng = pd.read_csv(engagement_path)
    bg = pd.read_csv(business_growth_path)
    reg_df = pd.DataFrame(registry)

    return reg_df, eng, bg


def compute_capital_efficiency(reg_df: pd.DataFrame, eng: pd.DataFrame, bg: pd.DataFrame, data_dir: Path = STUDY_DATA) -> pd.DataFrame:
    """Compute matched engagement efficiency and business participation efficiency."""
    rows = []

    # Filter to Main window
    main_eng = eng[eng["window"] == "Main"].copy()

    # Pre-index business growth near & farther
    bg_near = bg[bg["area"] == "Near"].set_index("project")
    bg_far = bg[bg["area"] == "Farther"].set_index("project")

    for _, reg_row in reg_df.iterrows():
        proj = reg_row["project"]
        # The historical Sun Link matched extract covered only a restricted
        # subset of the corridor. Current analysis uses the full-route cohort
        # in sun_link_corridor_efficiency.csv instead.
        if proj == "Sun Link":
            continue
        cost = float(reg_row["cost_millions"])
        city = reg_row["city"]
        ptype = reg_row["project_type"]

        # Business growth stats for 500m
        has_bg = proj in bg_near.index and proj in bg_far.index
        if has_bg:
            bn = bg_near.loc[proj]
            bf = bg_far.loc[proj]
            n_pre_biz = float(bn["baseline_active"])
            n_post_biz = float(bn["post_active"])
            delta_n_biz = n_post_biz - n_pre_biz
            far_growth_rate = float(bf["growth_pct"]) / 100.0
            counterfactual_n_biz = n_pre_biz * (1.0 + far_growth_rate)
            net_biz_gain = delta_n_biz - (counterfactual_n_biz - n_pre_biz)
            ce_biz = net_biz_gain / cost
            bg_rel_growth = float(bn["relative_growth_pct"])
        else:
            n_pre_biz = np.nan
            n_post_biz = np.nan
            net_biz_gain = np.nan
            ce_biz = np.nan
            bg_rel_growth = np.nan

        # Match with engagement rows
        proj_eng = main_eng[main_eng["project"] == proj]

        for _, e_row in proj_eng.iterrows():
            radius = int(e_row["radius_m"])
            income_grp = e_row["income_group"]
            metric = e_row["metric"]
            pairs = int(e_row["pairs"])
            distinct_ctrls = int(e_row["distinct_controls"])
            low_support = bool(e_row["low_support"]) or (pairs < 20)

            near_pre = float(e_row["near_pre"])
            near_post = float(e_row["near_post"])
            ctrl_pre = float(e_row["control_pre"])
            ctrl_post = float(e_row["control_post"])

            delta_near = near_post - near_pre
            delta_ctrl = ctrl_post - ctrl_pre
            did_per_pair = delta_near - delta_ctrl

            total_baseline_volume = near_pre * pairs
            total_post_volume = near_post * pairs
            net_volume_gain = did_per_pair * pairs

            rel_growth_pct = float(e_row["relative_growth_pct"]) if pd.notna(e_row["relative_growth_pct"]) else np.nan

            # Capital efficiency formulas
            ce_abs = net_volume_gain / cost
            ce_rel = rel_growth_pct / cost if pd.notna(rel_growth_pct) else np.nan

            if total_baseline_volume > 0:
                ce_norm_pct = (net_volume_gain / (total_baseline_volume * cost)) * 100.0
            else:
                ce_norm_pct = np.nan

            rows.append({
                "project": proj,
                "comparison_method": "matched_pairs",
                "city": city,
                "project_type": ptype,
                "cost_millions": cost,
                "radius_m": radius,
                "income_group": income_grp,
                "metric": metric,
                "pairs": pairs,
                "distinct_controls": distinct_ctrls,
                "low_support": low_support,
                "near_pre_mean": round(near_pre, 3),
                "near_post_mean": round(near_post, 3),
                "control_pre_mean": round(ctrl_pre, 3),
                "control_post_mean": round(ctrl_post, 3),
                "did_per_pair": round(did_per_pair, 3),
                "total_baseline_near_vol": round(total_baseline_volume, 1),
                "total_post_near_vol": round(total_post_volume, 1),
                "net_volume_gain": round(net_volume_gain, 1),
                "relative_growth_pct": round(rel_growth_pct, 2) if pd.notna(rel_growth_pct) else np.nan,
                "ce_abs_per_million": round(ce_abs, 2),
                "ce_rel_pct_per_million": round(ce_rel, 4) if pd.notna(ce_rel) else np.nan,
                "ce_norm_pct_per_million": round(ce_norm_pct, 4) if pd.notna(ce_norm_pct) else np.nan,
                # Business participation (active reviewed listings at 500m)
                "biz_500m_pre": int(n_pre_biz) if pd.notna(n_pre_biz) else None,
                "biz_500m_post": int(n_post_biz) if pd.notna(n_post_biz) else None,
                "biz_500m_net_gain": round(net_biz_gain, 2) if pd.notna(net_biz_gain) else np.nan,
                "biz_500m_rel_growth_pct": round(bg_rel_growth, 2) if pd.notna(bg_rel_growth) else np.nan,
                "ce_biz_per_million": round(ce_biz, 3) if pd.notna(ce_biz) else np.nan,
            })
    # Append expansion projects from expansion_projects_metrics.csv if present
    exp_path = data_dir / "expansion_projects_metrics.csv"
    if exp_path.exists():
        exp_df = pd.read_csv(exp_path)
        for _, er in exp_df.iterrows():
            cost_val = float(er["cost_millions"])
            pairs_val = int(er["pairs"])
            near_post_val = float(er["near_post_mean"])
            ce_rel_val = float(er["ce_rel_pct_per_million"])
            rows.append({
                "project": er["project"],
                "comparison_method": "cohort_mean",
                "city": er["city"],
                "project_type": er["project_type"],
                "cost_millions": cost_val,
                "radius_m": 500,
                "income_group": "All",
                "metric": "reviews",
                "pairs": pairs_val,
                "distinct_controls": np.nan,
                "low_support": bool(er["low_support"]),
                "near_pre_mean": float(er["near_pre_mean"]),
                "near_post_mean": near_post_val,
                "control_pre_mean": float(er["control_pre_mean"]),
                "control_post_mean": float(er["control_post_mean"]),
                "did_per_pair": float(er["did_per_pair"]),
                "total_baseline_near_vol": float(er["total_baseline_near_vol"]),
                "total_post_near_vol": round(near_post_val * pairs_val, 1),
                "net_volume_gain": float(er["net_volume_gain"]),
                "relative_growth_pct": round(ce_rel_val * cost_val, 2),
                "ce_abs_per_million": float(er["ce_abs_per_million"]),
                "ce_rel_pct_per_million": ce_rel_val,
                "ce_norm_pct_per_million": float(er["ce_norm_pct_per_million"]),
                "biz_500m_pre": int(er["biz_500m_pre"]) if pd.notna(er.get("biz_500m_pre")) else None,
                "biz_500m_post": int(er["biz_500m_post"]) if pd.notna(er.get("biz_500m_post")) else None,
                "biz_500m_net_gain": float(er["biz_500m_net_gain"]) if pd.notna(er.get("biz_500m_net_gain")) else np.nan,
                "biz_500m_rel_growth_pct": float(er["biz_500m_rel_growth_pct"]) if pd.notna(er.get("biz_500m_rel_growth_pct")) else np.nan,
                "ce_biz_per_million": float(er["ce_biz_per_million"]) if pd.notna(er.get("ce_biz_per_million")) else np.nan,
            })

    return pd.DataFrame(rows)
def extract_expansion_candidates(reg_df: pd.DataFrame, data_dir: Path) -> pd.DataFrame:
    """Extract candidate expansion projects and summarize their catchment density."""
    is_candidate = reg_df["funding_note"].fillna("").str.contains("Candidate status")
    candidates = reg_df[is_candidate].copy()
    rows = []
    for _, r in candidates.iterrows():
        pre_str = f"{r['pre'][0]}-{r['pre'][1]}" if isinstance(r.get('pre'), list) else ""
        post_str = f"{r['post'][0]}-{r['post'][1]}" if isinstance(r.get('post'), list) else ""
        rows.append({
            "project": r["project"],
            "city": r["city"],
            "project_type": r["project_type"],
            "cost_millions": r["cost_millions"],
            "opening_milestone": r["opening"],
            "pre_window": pre_str,
            "post_window": post_str,
            "geometry_note": r["geometry_note"],
            "funding_source": r.get("source", ""),
            "status": "Candidate pending full matching extraction",
        })
    cand_df = pd.DataFrame(rows)
    cand_path = data_dir / "expansion_candidates.csv"
    cand_df.to_csv(cand_path, index=False)
    return cand_df



def print_summary_benchmark(df: pd.DataFrame):
    """Print 500m descriptive comparisons with method and support visible."""
    primary = df[(df["radius_m"] == 500) & (df["metric"] == "reviews") & (df["income_group"] == "All")].copy()
    primary["method_order"] = primary["comparison_method"].map({"matched_pairs": 0, "cohort_mean": 1})
    primary = primary.sort_values(by=["method_order", "low_support", "ce_abs_per_million"], ascending=[True, True, False])

    print("\n" + "=" * 105)
    print("DESCRIPTIVE CAPITAL EFFICIENCY: 500m Buffer, Review Volume (Main 2-Year Window)")
    print("=" * 105)
    header = (
        f"{'Project':<28} {'Method':<14} {'Cost ($M)':>10} {'Sample':>6} "
        f"{'DiD/Pair':>9} {'Net Vol':>9} {'CE_abs':>9} {'CE_rel':>9} {'CE_norm':>9} {'Support':>8}"
    )
    print(header)
    print("-" * 105)

    for _, r in primary.iterrows():
        supp_str = "FLAG" if r["low_support"] else "OK"
        did_str = "—" if r["low_support"] else f"{r['did_per_pair']:+.2f}"
        net_str = "—" if r["low_support"] else f"{r['net_volume_gain']:+.1f}"
        ce_abs_str = "—" if r["low_support"] else f"{r['ce_abs_per_million']:+.2f}"
        ce_rel_str = "—" if r["low_support"] else f"{r['ce_rel_pct_per_million']:+.2f}%" if pd.notna(r["ce_rel_pct_per_million"]) else "N/A"
        ce_norm_str = "—" if r["low_support"] else f"{r['ce_norm_pct_per_million']:+.2f}%" if pd.notna(r["ce_norm_pct_per_million"]) else "N/A"
        method = "Matched pairs" if r["comparison_method"] == "matched_pairs" else "Cohort mean"
        print(
            f"{r['project']:<28} {method:<14} {r['cost_millions']:>10.1f} {r['pairs']:>6} "
            f"{did_str:>9} {net_str:>9} {ce_abs_str:>9} "
            f"{ce_rel_str:>9} {ce_norm_str:>9} {supp_str:>8}"
        )
    print("=" * 105)
    print("Notes:")
    print("  CE_abs   = Descriptive net reviews per reported $1M project cost (Net Vol / Cost)")
    print("  CE_rel   = Relative Review Growth Rate per $1M Invested (Rel Growth % / Cost)")
    print("  CE_norm  = Baseline-Normalized Net Volume Generated per $1M Invested (Net Vol / [Baseline Vol * Cost] * 100)")
    print("  Sample   = Matched pairs for original cases; baseline nearby businesses for cohort-mean expansions.")
    print("  Support  = Difference and efficiency estimates suppressed when sample size is below 20.")
    print("=" * 105 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Calculate engagement and capital efficiency.")
    parser.add_argument("--data-dir", type=Path, default=STUDY_DATA, help="Path to study data directory.")
    parser.add_argument("--output", type=Path, default=STUDY_DATA / "capital_efficiency.csv", help="Output CSV path.")
    args = parser.parse_args()

    reg_df, eng, bg = load_data(args.data_dir)
    res = compute_capital_efficiency(reg_df, eng, bg, args.data_dir)
    cand_df = extract_expansion_candidates(reg_df, args.data_dir)
    print(f"Wrote {len(cand_df)} expansion candidates to {args.data_dir / 'expansion_candidates.csv'}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(args.output, index=False)
    print(f"Wrote {len(res)} capital efficiency records to {args.output}")

    print_summary_benchmark(res)


if __name__ == "__main__":
    main()
