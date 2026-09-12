"""Retrieve USASpending prime award transactions for the Yelp ZIP universe.

The USASpending bulk-download API caps each request at one year of action dates,
so we issue one request per year and let the server generate the CSV. Requests
are resumable: a year whose zip is already on disk is skipped.

Usage:
    python src/fetch_usaspending.py                    # 2010-2021 + Jan 2022
    python src/fetch_usaspending.py --years 2015 2016
    python src/fetch_usaspending.py --award-group assistance
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.usaspending.gov/api/v2"
ROOT = Path(__file__).resolve().parent.parent
ZIP_FILE = ROOT / "data" / "interim" / "yelp_zips.txt"
OUT_DIR = ROOT / "data" / "raw" / "usaspending"

# Assistance and contract transactions carry different column sets, so they are
# fetched as separate downloads rather than one mixed request.
AWARD_GROUPS = {
    "assistance": ["02", "03", "04", "05"],  # grants, direct payments-as-grants
    "contracts": ["A", "B", "C", "D"],
    "loans": ["07", "08"],  # PPP and EIDL live here
}

# Which location field a group should be filtered on. Infrastructure spending is
# recorded where the work happens; business relief (PPP, EIDL) is recorded at the
# recipient's own address — filtering PPP on place of performance returns almost
# nothing (4 loans vs 13,215 across five test ZIPs).
LOCATION_FILTERS = {
    "place_of_performance": "place_of_performance_locations",
    "recipient": "recipient_locations",
}
DEFAULT_LOCATION = {
    "assistance": "place_of_performance",
    "contracts": "place_of_performance",
    "loans": "recipient",
}

# Yelp reviews in the Open Dataset run through 2022-01-19.
DEFAULT_YEARS = list(range(2010, 2022))
TAIL = ("2022-01-01", "2022-01-31")


def post(path, payload, timeout=300):
    req = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def load_zips():
    if not ZIP_FILE.exists():
        sys.exit(f"missing {ZIP_FILE} — run src/build_zip_universe.py first")
    return [ln.strip() for ln in ZIP_FILE.read_text().splitlines() if ln.strip()]


def request_download(zips, award_types, start, end, location):
    payload = {
        "filters": {
            "prime_award_types": award_types,
            "date_type": "action_date",
            "date_range": {"start_date": start, "end_date": end},
            LOCATION_FILTERS[location]: [{"country": "USA", "zip": z} for z in zips],
        },
        "columns": [],
        "file_format": "csv",
    }
    return post("/bulk_download/awards/", payload)


def poll(file_name, label, interval=10, max_wait=3600):
    url = API + "/download/status?file_name=" + urllib.parse.quote(file_name)
    waited = 0
    while waited < max_wait:
        time.sleep(interval)
        waited += interval
        try:
            s = json.load(urllib.request.urlopen(url, timeout=120))
        except urllib.error.HTTPError as e:
            print(f"  [{label}] status HTTP {e.code}, retrying", flush=True)
            continue
        status = s.get("status")
        print(
            f"  [{label}] {status}"
            f" rows={s.get('total_rows')}"
            f" size={s.get('total_size')}KB"
            f" t={s.get('seconds_elapsed')}s",
            flush=True,
        )
        if status == "finished":
            return s
        if status == "failed":
            raise RuntimeError(f"{label}: generation failed — {s.get('message')}")
    raise TimeoutError(f"{label}: still running after {max_wait}s")


def download(file_url, dest):
    tmp = dest.with_suffix(".part")
    with urllib.request.urlopen(file_url, timeout=1800) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    tmp.rename(dest)
    return dest.stat().st_size


QUARTERS = [("01-01", "03-31"), ("04-01", "06-30"), ("07-01", "09-30"), ("10-01", "12-31")]


def quarters_of(year):
    return [(f"{year}-{a}", f"{year}-{b}", f"{year}Q{i}") for i, (a, b) in enumerate(QUARTERS, 1)]


def fetch(zips, group, start, end, label, location, allow_split=True):
    suffix = "" if location == DEFAULT_LOCATION.get(group) else f"_{location}"
    dest = OUT_DIR / f"{group}{suffix}_{label}.zip"
    if dest.exists():
        print(f"[{group} {label}] already have {dest.name}, skipping", flush=True)
        return dest
    print(f"[{group} {label}] requesting {start}..{end}", flush=True)
    try:
        d = request_download(zips, AWARD_GROUPS[group], start, end, location)
        status = poll(d["file_name"], f"{group} {label}")
    except (RuntimeError, TimeoutError) as e:
        # High-volume years (COVID relief, IIJA) blow up server-side generation.
        # Split the year into quarters and retry each independently.
        if not (allow_split and len(label) == 4 and label.isdigit()):
            raise
        print(f"[{group} {label}] {e} — retrying as quarters", flush=True)
        got = [
            fetch(zips, group, s, e2, lb, location, allow_split=False)
            for s, e2, lb in quarters_of(int(label))
        ]
        return [g for g in got if g]
    if not status.get("total_rows"):
        print(f"[{group} {label}] no rows, skipping download", flush=True)
        return None
    size = download(status.get("file_url") or d["file_url"], dest)
    print(f"[{group} {label}] saved {dest.name} ({size / 1e6:.1f} MB)", flush=True)
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="*", type=int, default=DEFAULT_YEARS)
    ap.add_argument(
        "--award-group", choices=[*AWARD_GROUPS, "all"], default="all"
    )
    ap.add_argument(
        "--location", choices=[*LOCATION_FILTERS],
        help="override the default location filter for the chosen group(s)",
    )
    ap.add_argument("--no-tail", action="store_true", help="skip the Jan-2022 stub")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zips = load_zips()
    groups = list(AWARD_GROUPS) if args.award_group == "all" else [args.award_group]
    print(f"{len(zips)} ZIPs · groups={groups} · years={args.years}", flush=True)

    periods = [(f"{y}-01-01", f"{y}-12-31", str(y)) for y in args.years]
    if not args.no_tail:
        periods.append((*TAIL, "2022-01"))

    for group in groups:
        location = args.location or DEFAULT_LOCATION[group]
        print(f"--- {group}: filtering on {LOCATION_FILTERS[location]}", flush=True)
        for start, end, label in periods:
            try:
                fetch(zips, group, start, end, label, location)
            except Exception as e:  # keep going; the run is resumable
                print(f"[{group} {label}] ERROR {type(e).__name__}: {e}", flush=True)


if __name__ == "__main__":
    main()
