"""Normalize the raw USASpending downloads into a slim transaction table.

The bulk-download CSVs carry ~112 (assistance) / ~280 (contract) columns and run
to hundreds of MB. This streams them, keeps only the fields the project needs,
harmonizes the assistance and contract schemas onto one set of names, and writes:

    data/interim/award_transactions.csv  one row per transaction
    data/interim/zip_year_awards.csv     obligations rolled up to ZIP x year

The description fields are kept verbatim — classifying them into place-based vs.
institutional investment is the text-analytics step, done downstream.
"""

import csv
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "usaspending"
INTERIM = ROOT / "data" / "interim"
ZIP_FILE = INTERIM / "yelp_zips.txt"

csv.field_size_limit(sys.maxsize)

# target name -> (assistance column, contract column)
FIELD_MAP = {
    "award_key": ("assistance_award_unique_key", "contract_award_unique_key"),
    "award_id": ("award_id_fain", "award_id_piid"),
    "action_date": ("action_date", "action_date"),
    "obligation": ("federal_action_obligation", "federal_action_obligation"),
    "awarding_agency": ("awarding_agency_name", "awarding_agency_name"),
    "awarding_sub_agency": ("awarding_sub_agency_name", "awarding_sub_agency_name"),
    "recipient_name": ("recipient_name", "recipient_name"),
    "pop_zip4": (
        "primary_place_of_performance_zip_4",
        "primary_place_of_performance_zip_4",
    ),
    "pop_city": (
        "primary_place_of_performance_city_name",
        "primary_place_of_performance_city_name",
    ),
    "pop_state": (
        "primary_place_of_performance_state_name",
        "primary_place_of_performance_state_name",
    ),
    # program taxonomy: CFDA for assistance, NAICS/PSC for contracts
    "program_code": ("cfda_number", "naics_code"),
    "program_title": ("cfda_title", "naics_description"),
    "psc_description": (None, "product_or_service_code_description"),
    "description": ("transaction_description", "transaction_description"),
    "base_description": (
        "prime_award_base_transaction_description",
        "prime_award_base_transaction_description",
    ),
}

OUT_COLUMNS = ["group", "zip5", "year", *FIELD_MAP]
ZIP5 = re.compile(r"(\d{5})")


def zip5_of(value):
    m = ZIP5.match((value or "").strip())
    return m.group(1) if m else ""


def iter_rows(zip_path, group):
    """Yield harmonized dicts from every CSV member of one downloaded zip."""
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            if not member.lower().endswith(".csv"):
                continue
            with zf.open(member) as fh:
                reader = csv.DictReader(
                    (line.decode("utf-8", "replace") for line in fh)
                )
                idx = 0 if group == "assistance" else 1
                cols = {
                    target: src[idx]
                    for target, src in FIELD_MAP.items()
                    if src[idx] and src[idx] in (reader.fieldnames or [])
                }
                # only flag fields this group is supposed to have
                expected = {t for t, src in FIELD_MAP.items() if src[idx]}
                missing = expected - set(cols)
                if missing:
                    print(f"  {zip_path.name}/{member}: no column for {sorted(missing)}")
                for row in reader:
                    out = {t: (row.get(c) or "").strip() for t, c in cols.items()}
                    out["group"] = group
                    out["zip5"] = zip5_of(out.get("pop_zip4"))
                    out["year"] = (out.get("action_date") or "")[:4]
                    yield out


def main():
    keep = set(ZIP_FILE.read_text().split())
    INTERIM.mkdir(parents=True, exist_ok=True)
    out_path = INTERIM / "award_transactions.csv"
    panel = defaultdict(lambda: [0, 0.0])  # (zip, year, group) -> [n, dollars]

    kept = dropped = 0
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for zip_path in sorted(RAW.glob("*.zip")):
            group = zip_path.name.split("_")[0]
            n0 = kept
            for row in iter_rows(zip_path, group):
                if row["zip5"] not in keep:
                    dropped += 1
                    continue
                writer.writerow(row)
                kept += 1
                try:
                    amt = float(row.get("obligation") or 0)
                except ValueError:
                    amt = 0.0
                cell = panel[(row["zip5"], row["year"], group)]
                cell[0] += 1
                cell[1] += amt
            print(f"{zip_path.name}: {kept - n0:,} rows kept", flush=True)

    with open(INTERIM / "zip_year_awards.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["zip5", "year", "group", "n_transactions", "obligations"])
        for (z, y, g), (n, amt) in sorted(panel.items()):
            w.writerow([z, y, g, n, f"{amt:.2f}"])

    print(f"\n{kept:,} transactions written -> {out_path}")
    print(f"{dropped:,} dropped (place of performance outside the Yelp ZIP universe)")
    print(f"{len(panel):,} ZIP x year x group cells -> zip_year_awards.csv")


if __name__ == "__main__":
    main()
