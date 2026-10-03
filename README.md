# neighborhood-sentiment-map

**CIS 509 — Analytics for Unstructured Data** · Fall 2026 · Canvas course `264495` (Xiao Liu)

An evidence explorer and experimental proposal tool for public investments, combining
project outcomes with unstructured Yelp review analysis.

**Team 4** — John Wheeler, Ryan Wolff, Cameron Anthony

## Where things live

This is the course's **final project**, so it sits at the course root rather than under
`Work/`. Course material is mirrored at `../Mirror/` (read-only, regenerated) and lab
drafts live in `../Work/<Canvas assignment title>/`. This repo holds the course-project
code and durable project docs — not the weekly lab write-ups.

CIS 509 has its own `.venv` at the course-folder level; use it for this course's Python.

## Presenting the demo

Double-click [`start-demo.command`](start-demo.command) to open the prepared local
site. It selects a free loopback port and needs only Python 3, the bundled `web/`
files and a browser. Keep the launcher Terminal open while presenting.

- [Editable presentation](docs/presentation/Public-Investment-Evidence.pptx): ten main slides, three backup slides, and speaker notes.
- [PDF viewing copy](output/pdf/Public-Investment-Evidence.pdf).
- [Presenter guide](docs/presentation/Presenter-Guide.md): ten-minute story, key points and anticipated questions.
- [Three-minute demo runbook](docs/demo-runbook.md): exact clicks and fallback plan.

New prototype: **Place Lab**, a location-to-proposal tool with direct controls and
an interactive 2D map. Placement is limited to covered regions with at least one
business with 2018–2019 reviews within 500 m. Double-click [`start-place.command`](start-place.command), or
run `python3 src/serve_place.py --port 8766`, then open
`http://127.0.0.1:8766/place.html`. Map selection, project type, budget, actual nearby-business profiles and estimates
run in the browser without an API backend. Optional browser tools use the same validated controls. See the
[implementation and demo guide](docs/plan/conversational-ar.md).

Original development plan: [Three.js 3D map](docs/plan/threejs-3d-map.md).

## Current product

Live site: [Public Investment Map](https://intreaction.github.io/neighborhood-sentiment-map/)
and [Place Lab](https://intreaction.github.io/neighborhood-sentiment-map/place.html).
GitHub Actions publishes the prepared `web/` directory when its files change on
`main`. The **Deploy GitHub Pages** workflow can also be run manually. Only the
static web files are published; raw data and local Python launchers are not needed
by visitors. After changing Place Lab sources, run `python3 src/build_place_site.py`
and `npm run build:place`, then commit the updated `web/` files.

Open `web/index.html`, or serve `web/` with `python -m http.server 8765 --directory web`.
The original self-contained pages use embedded data, SVG, CSS and JavaScript.
Place Lab uses a local 2D canvas map, bundled shadcn/Recharts graphs and JSON assets and must be served over
HTTP. Neither UI needs external fonts or map tiles. Local profile imports remain
in the browser. The prepared web assets can be hosted on a static site service such as GitHub Pages.

- **Explore projects** (`index.html` / `projects.html`): 11 historical projects in
  seven cities, one harmonized outcome, near/comparison counts, footprint diagrams,
  text topics, sentiment, excerpts, source notes and coverage limitations.
- **Analyze a proposal** (`model.html`): start with a historical example or enter/import
  a measured baseline profile; change cost and local activity, inspect comparables,
  export inputs and the resulting estimate. Unsupported inputs withhold the estimate.
  Missing provenance is labeled an assumption-only scenario.
- **Area atlas** (`atlas.html`): the earlier five-city ZIP map, review themes,
  funding lag exploration and population context. Its optional Legacy CE layer uses
  different methods and is preserved for comparison, not mixed into primary outcomes.
- **Place Lab** (`place.html`): pick a point, choose type and budget, count businesses
  within 500 m and run the existing model. A fixed 2018–2019 baseline covers five
  metros. Placement requires nearby baseline-reviewed businesses. Optional browser tools are
  available through the browser adapter.
- **Archived reference calculator** (`reference.html`) and **earlier coursework report**
  (`report.html`) retain prior research results and their original definitions.

Capital efficiency here means **growth-adjusted excess Yelp reviews per $1 million
of reported project cost**, over two post-opening years. It is an online-activity
proxy, not financial return, public benefit, or a causal effect. Costs are nominal
reported totals with inconsistent public/private scope; the January 2022 Yelp archive
cannot describe current conditions.

### Coverage and model evidence

The project extraction scored **1,063,956 unique reviews**, yielding 1,420,312
project/period memberships. Overlapping catchments share 292,924 reviews. Ten of 11
projects meet baseline support requirements; Water Works Park remains visible with
its outcome withheld. Six projects have mapped footprints and five use explicit
center proxies. Mapped geometry is not necessarily a verified historical footprint.

Text extraction records topic, whole-review sentiment, place versus business target,
and provisional clause-level polarity for parking, transit, walking/accessibility,
public space, safety, construction, cleanliness/maintenance, neighborhood and
food/service/value. Pre-opening place discussion, access friction and public-realm
complaints form model challenger features. Rule labels remain provisional: the
local annotation task is prepared, but no independent human accuracy estimate exists.

The advanced text layer learns **TF-IDF unigram/bigram features and five NMF topics**
from baseline review language. It uses 23,691 sampled nearby baseline/post reviews
(10,971 unique baseline reviews fit the descriptive topic basis), then exposes
pre/post topic mixtures, normalized topic entropy, lexical diversity, review length
and negation frequency. The prediction challenger refits its text representation
inside every held-out fold, using a separate versioned basis. See
[advanced text methods](docs/advanced-text-method.md) for sampling, leakage controls
and interpretation. These learned topics often reflect food and service language;
they are not automatically civic-satisfaction labels.

On the refreshed common ten-project sample, the three-input baseline (reported cost,
baseline reviewed businesses, reviews per reviewed business) has project-held-out MAE
49.33 and city-held-out MAE 45.61 reviews/$1M. Rule-text, early-trend and learned-text challengers did not
improve both errors, so the baseline remains selected. Its advantage over a mean-only
comparator disappears when timing-sensitive cases are excluded. The displayed error
envelope is historical error, not a calibrated confidence interval. This is a research
prototype for exploring assumptions and evidence, not a validated budget recommender.

### Rebuild the current product

Python dependencies are pinned in `requirements.txt`; this workspace uses `../.venv`.
The raw Yelp archive and business file are required for extraction, but the checked-in
aggregate evidence/model artifacts suffice to rebuild the site.

```sh
../.venv/bin/python src/build_project_evidence.py --workers 4
../.venv/bin/python src/build_advanced_text.py
../.venv/bin/python src/train_project_model.py
../.venv/bin/python src/build_evidence_site.py
```

The extractor reuses a versioned local cache under ignored `data/interim/project_evidence/`.
Use `--rebuild-cache` when required. `src/fetch_project_geometry.py` refreshes the
sourced Rail Park footprint with provenance; it requires network access. See
[the source audit](docs/project-source-audit.md) and
[implementation plan](docs/product-improvement-plan.md),
[browser/test validation](docs/qa/validation.md), and
[demo walkthrough](docs/demo-walkthrough.md).

```sh
../.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.cjs
```

Legacy outputs remain reproducible with `src/build_map_page.py` (`atlas.html`) and
`src/build_model_page.py` (`reference.html`). Their earlier aggregate inputs and
pipelines are documented in [atlas exploration](docs/atlas-exploration.md).

## Data pipeline

Raw data is gitignored. Regenerate it from scratch with:

```
../.venv/bin/python src/build_zip_universe.py    # Yelp business file -> 1,202 US ZIPs
../.venv/bin/python src/fetch_usaspending.py     # one bulk download per year x award group
../.venv/bin/python src/build_award_panel.py     # -> slim transactions + ZIP-year panel
```

| Path | What |
|---|---|
| `Yelp JSON/yelp_dataset.tar` | Yelp Open Dataset v4 (Jan 2022), 150,346 businesses / 6.99M reviews. Not redistributable — see the ToS PDF beside it. |
| `data/raw/yelp_academic_dataset_business.json` | extracted from the tar |
| `data/raw/usaspending/*.zip` | bulk-download CSVs, one per year x award group |
| `data/interim/yelp_zips.txt` | the 1,202-ZIP study universe |
| `data/interim/award_transactions.csv` | harmonized assistance + contract transactions |
| `data/interim/zip_year_awards.csv` | obligations rolled up to ZIP x year |

### Notes on the USASpending pull

- The bulk-download API caps each request at **one year** of action dates, so the
  fetcher issues one request per year. All 1,202 ZIP filters go in a single request.
- Rows are **transactions**, not awards — each modification is its own row with its
  own `action_date`, which is what a time series needs.
- Place of performance ZIP is the **administering entity's** ZIP, not where the money
  was physically spent. Statewide formula programs book to one office address.
- Group programs on `cfda_number`, never `cfda_title` — the titles are inconsistently
  truncated in the source (`MEDICAL ASSISTANCE PROGRAM (MEDICAID)` vs
  `MEDICAL ASSISTANCE PROGRAM`).

## Analysis pipeline

```
../.venv/bin/python src/build_sentiment_panel.py   # 3.07M reviews -> VADER, ZIP-quarter panel
../.venv/bin/python src/fetch_map_context.py       # water, roads, county outlines
../.venv/bin/python src/simplify_context.py        # 8.07 MB -> 0.37 MB
../.venv/bin/python src/fetch_map_furniture.py     # state borders, place labels, metro extents
../.venv/bin/python src/build_map_page.py          # -> web/atlas.html   (historical ZIP context)

../.venv/bin/python src/lag_analysis.py            # naive lag cross-correlation (null)
../.venv/bin/python src/case_studies.py            # per-award difference-in-differences
../.venv/bin/python src/build_lag_model.py         # 48-kernel surface + permutation + bootstrap
../.venv/bin/python src/build_lag_page.py          # -> web/lag.html     (earlier research explorer)
```

`build_lag_model.py` is the slow one (~6 min): 48 kernels x 5 control regimes, plus a
400-draw permutation null and a 300-draw ZIP-clustered bootstrap.

### Earlier ZIP-funding research result

No weighting of twelve years of place-based obligations correlates detectably with
ZIP-quarter review sentiment once ZIP and quarter fixed effects are applied. Best of
48 kernels is |r| = 0.0115; shuffling award histories across ZIPs beats it 94% of the
time; the ZIP-clustered 95% CI at the default kernel is -0.054 to +0.059. Five
independent specifications and 256 event studies agree.

Two ways the analysis manufactures a false positive, both reproducible in `web/lag.html`:

| Trap | Reads | Corrected |
|---|---|---|
| No fixed effects (cross-sectional density confound) | +0.151 | +0.004 |
| Kernel padded with fabricated pre-2010 zeros | +0.039 | -0.003 |

The design is blind below about \|r\| = 0.09 with honest clustered errors, so this is
"not detectable", never "no effect".

### USASpending inventory

| Group | Location filter | Years | Files |
|---|---|---|---|
| `assistance_*` | place of performance | 2010-2021 + Jan 2022 | 13 |
| `assistance_recipient_*` | recipient | 2019-2021 + Jan 2022 | 4 |
| `loans_*` (PPP, EIDL) | recipient | 2019-2021 + Jan 2022 | 4 |
| `contracts_*` | place of performance | 2010-2013 only | 4 |

633 MB total. PPP and EIDL are recorded at the **recipient's** address, not place of
performance - filtering PPP on place of performance returns 4 loans where recipient
location returns 13,215 across five test ZIPs. Contracts 2014-2021 were deliberately
skipped: in these ZIPs 75% of contract dollars are defense procurement and only ~7% is
construction.
