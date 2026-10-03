# Source data and local replication

## What belongs in Git

Commit code, notebooks, compact study outputs, source/version manifests, and the
static files needed to view the site. Do not commit full Yelp or Census source
collections, downloaded shapefiles, raw review records, or intermediate caches.
Store downloads in `data/raw/`, `data/external/`, `data/downloads/`, or the existing
`Yelp JSON/` archive directory; all are ignored. `data/interim/` is also ignored.

The publication check rejects these source paths and common raw-source filenames,
even if force-added, and rejects individual files larger than 10 MiB. CI runs this
check. `.gitignore` prevents ordinary accidental additions; CI does not prevent a
local commit or a push by itself. Run `python3 scripts/audit_public_repo.py` before
committing. Do not use Git LFS to redistribute the source archives.

The compact notebook snapshots and static JSON are intentionally retained. The
largest prepared data input is approximately 1.8 MiB. They let readers reproduce
the notebook transformations and inspect the application without downloading the
full corpus. They are derived research inputs, not a replacement for the source
archive. The data permission confirmed by the owner still applies to them.

## Obtain source data

| Source | Obtain from | Version / local destination |
|---|---|---|
| Yelp business and review archive | [Yelp Open Dataset](https://www.yelp.com/dataset), following its access and agreement process | This research used the January 2022 archive. Save the tar archive at `Yelp JSON/yelp_dataset.tar`; put its business JSON at `data/raw/yelp_academic_dataset_business.json`. Review builders stream the review member from the archive. |
| Census ZCTA polygons | Census TIGERweb through `src/fetch_zcta_boundaries.py` | Script requests only study ZIPs from the ACS2023 service and writes `data/interim/zcta_boundaries.geojson`; `src/simplify_boundaries.py` creates the reduced geometry. |
| Census population | `src/fetch_population.py` queries Census2020 TIGERweb | Uses 2020 population and land area for mapped ZCTAs; produces the small `data/population_2020.json` research extract. |
| ACS income / poverty context | [Census ACS five-year data](https://www.census.gov/data/developers/data-sets/acs-5year.html) | Retained course extracts use 2007–2011 for Philadelphia/Tucson and 2008–2012 for the other metros. Prepared values are in `data/derived/place_area_income.csv` and `data/derived/place_inputs/income.csv`. |

Yelp is publicly obtainable subject to its dataset terms, not unrestricted public
domain data. We do not provide an automated downloader that accepts those terms
on another person's behalf. Availability of the exact January 2022 archive at
the current download page has not been established. A current archive can support
a new analysis, but cannot be assumed to reproduce the historical counts exactly.

Census's ACS API documentation currently requires an API key for API queries.
Keep any key in a local environment variable, never in a notebook output or Git.
The repository's TIGERweb scripts use a separate service. Source service versions,
missing ZCTAs, and availability can change; record versions and hashes when
refreshing data.

## Two levels of reproduction

**Prepared-data reproduction:** follow the README's notebook execution command.
This is the supported fresh-clone workflow, needs no source download, and exports
the five static app JSON files from versioned study inputs.

**Raw-source replication:** obtain the matching archive and the required study
configuration before running extraction. The repository includes builders for
ZIP inventory (`build_zip_universe.py`), VADER panels
(`build_sentiment_panel.py --with-text`), topics (`build_review_topics.py`),
project evidence (`build_project_evidence.py`), learned text
(`build_advanced_text.py`) and the model (`train_project_model.py`).

This older pipeline is not yet a single-command bootstrap from public downloads:
metro membership/extents and historical ACS preparation originated in the course
workspace. Prepared metro membership and geometry are retained in
`data/derived/place_inputs/`; they must be restored to the formats expected by
upstream builders when doing a raw rebuild. The historical ACS acquisition and
cleaning process is not fully automated in this repository. Do not claim a fresh
raw-source run is identical merely because the notebook executes successfully.

After upstream inputs have been rebuilt, `build_place_data.py` creates profiles
and map geometry; `prepare_place_inputs.py` freezes the notebook input snapshots.
Then rerun the research notebook and the test suite. Review the generated manifest
and differences before replacing the checked-in research outputs. Full source
extraction is computationally expensive and is not part of ordinary CI.
