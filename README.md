# neighborhood-sentiment-map

**CIS 509 — Analytics for Unstructured Data** · Fall 2026 · Canvas course `264495` (Xiao Liu)

Public investment (USASpending) vs Yelp review sentiment, rendered as a web map.

**Team 4** — John Wheeler, Ryan Wolff, Cameron Anthony

## Where things live

This is the course's **final project**, so it sits at the course root rather than under
`Work/`. Course material is mirrored at `../Mirror/` (read-only, regenerated) and lab
drafts live in `../Work/<Canvas assignment title>/`. This repo holds the course-project
code and durable project docs — not the weekly lab write-ups.

CIS 509 has its own `.venv` at the course-folder level; use it for this course's Python.

## Map application

Open `web/index.html` directly, or serve `web/` locally. The page is self-contained:
SVG geography, review sentiment and funding data are embedded, with no external
map tiles, JavaScript libraries or font requests.

- Choose one of the five cities, then click a ZIP polygon or use the Area selector.
- The quarterly slider and play/pause control sit directly beneath the map, inside
  the map card. They synchronize the map, selected-area statistics and both charts.
- Switch between sentiment, year-over-year sentiment change and signed funding.
  The optional funding circles show positive net obligations at area centers, not
  verified project locations. Negative adjustments remain in the funding view/chart.
- The selected ZIP's sentiment history is compared with its city's review-weighted
  history. Click either chart to select a quarter; drag to pan or use the zoom
  buttons / Ctrl+scroll to zoom. Ordinary scrolling moves through the page. On narrow screens, details and charts stack below the map.
- Hatching flags unavailable sentiment/comparisons; annual change needs both the
  current quarter and the same quarter one year earlier to meet the chosen review
  threshold (30 by default; adjustable from 10 to 200).

Scroll below the map for:

- A funding timing lab with 0–12-quarter lags, 1–8-quarter funding windows, review
  coverage controls, a linked ZIP scatterplot and a fixed-cohort view of all lags.
- Six overlapping review themes, review-rating distributions and sampled excerpts.
  Choosing a theme filters sentiment throughout the map and analysis.
- Census 2020 population, a dollars-per-resident map, population normalization in
  the lag lab, and a five-region population/funding/sentiment table. The population
  denominator is a fixed 2020 snapshot; the default minimum is 500 residents.
- A sortable ZIP comparison table and CSV preview with save/copy options.

Text tags cover all 3,073,181 study reviews, with 2,390,974 matching at least one
rule. They are exploratory keyword mentions, not validated aspect classifications.
See `docs/atlas-exploration.md` for definitions, provenance and limitations.

Edit `src/map_template.html` and `src/exploration.{html,css,js}`. To build the
review-tag aggregates once and regenerate the page:

```sh
../.venv/bin/python src/build_review_topics.py  # stream raw text; reuse reconciled scores
../.venv/bin/python src/build_map_page.py
```

This UI uses the existing quarterly funding panel. It does not reconcile the older
transaction builder, reclassify awards or validate the lag model's causal claims.
The interface describes recorded obligations and review sentiment, with geographic
and source limitations available in its data notes.

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
../.venv/bin/python src/build_map_page.py          # -> web/index.html   (the map)

../.venv/bin/python src/lag_analysis.py            # naive lag cross-correlation (null)
../.venv/bin/python src/case_studies.py            # per-award difference-in-differences
../.venv/bin/python src/build_lag_model.py         # 48-kernel surface + permutation + bootstrap
../.venv/bin/python src/build_lag_page.py          # -> web/lag.html     (the demo)
```

`build_lag_model.py` is the slow one (~6 min): 48 kernels x 5 control regimes, plus a
400-draw permutation null and a 300-draw ZIP-clustered bootstrap.

### Headline result

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
