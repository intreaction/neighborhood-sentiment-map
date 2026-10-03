# Atlas exploration: definitions and reproduction

The map remains the entry point. Its quarterly slider stays inside the map card.
Scrolling continues into funding timing, review language and a ZIP comparison table.
City, review quarter, review theme and coverage threshold are shared across sections.
Selecting a ZIP changes its details, history and review breakdown; the scatterplot
and correlation still compare all eligible mapped ZIPs in the selected city.

The default map depicts project Capital Efficiency (CE): a review difference
per $1 million of reported project cost. Four project badges use matched business
samples. Sun Link uses all 717 Yelp listings along its 500 m route corridor and
adjusts for review growth in a farther 1.5–8 km Tucson area. Its unmatched result
is not directly comparable with the matched badges. Green is positive, orange is
negative, and gray means insufficient support or no estimate. The default 500-meter, all-income
view can be changed with radius and income selectors that also update the benchmark
table. CE uses a fixed pre/post comparison and is pinned at the end of the project
post window on the timeline. The quarter slider changes the ZIP colors, which
show quarterly Yelp review counts on a logarithmic scale. Review-theme filtering
changes ZIP colors, not CE. Reported costs may mix public and private funding.
Expansion projects use unmatched cohorts and are excluded from this map layer.

The ZIP review-growth view measures quarterly Yelp review counts relative to the
same quarter one year earlier: `100 × (N_t / N_(t−4) − 1)`. Both counts must meet
the current minimum (30 reviews by default). The companion count view uses a fixed
logarithmic color scale. Review count is a proxy for online activity, not visits or
spending. The ZIP color summarizes an entire area, while project outlines mark the
five documented footprints. The project comparison below uses nearby businesses
(500 meters by default) and a separate comparison group; ZIP color is not that local
estimate.

## Capital Efficiency Studio

`web/model.html` is a separate, self-contained capital-efficiency page linked from
the map. It includes a trained research estimate from ten supported projects and
shows leave-one-project-out error; the estimate is not reliable enough to choose
a budget or site. The executed [final report](coursework/final-project/Final_Submission_Report.ipynb)
documents the project EDA and training method. Its observed-reference scenario
is described below.
It loads four matched project references from `capital_efficiency.csv` and
recomputes the full-route Sun Link reference from `sun_scopes.csv` and its
coverage inputs (`sun_link_corridor_efficiency.csv` records the same output). For the
selected type, radius and income group, it multiplies the observed review
difference per business or route listing by the user-entered catchment count.
Dividing by proposed cost in $ millions gives scenario CE in net reviews per $1M.
Sun Link requires a count of all Yelp listings along the proposed route and uses
an unmatched, growth-adjusted contrast.

Target city and ZIP provide contextual population and all-ZIP Yelp business totals.
They do not numerically adjust the score: a whole-ZIP listing count cannot stand
in for a 250–1,000 m project catchment, and the five cases cannot identify an
independent location effect. The user must supply a catchment business count.
Rows with inadequate baseline support, missing differences, or invalid inputs
produce no score. The radius comparison holds proposed cost and business count
fixed while changing the reference radius; it is sensitivity, not an uncertainty
interval. This page is an illustrative reference-case calculation, not a validated
prediction or financial return estimate.

Build and verify it with:

```sh
../.venv/bin/python src/build_model_page.py
node --test tests/model_math.test.cjs
../.venv/bin/python -m unittest discover -s tests -p 'test_model_page.py'
```

## Funding timing

For review quarter `t`, lag `L` and window length `W`, funding is the sum of signed
net obligations from `t − L − W + 1` through `t − L`, inclusive. A lag of zero
includes the review quarter. The UI labels the exact funding dates and outcome date.
Example: reviews in 2021Q4, lag 4, window 4 → funding in 2020Q1–2020Q4.

The default outcome is percent change in review count from `t − 4` to `t`. Both quarters
must meet the review threshold. The alternative is `log(1 + reviews in t)`, with
the current quarter meeting the same threshold. The review-growth map always compares
the same quarter one year earlier, independent of the funding window. The top funding
chart shows original transaction timing;
the lag lab provides the explicit earlier funding comparison.

The scatterplot has one observation per mapped ZIP in the chosen city at `t`, with
equal dot size and equal statistical weight. Pearson correlation uses signed-log
funding (`sign(x) * log(1 + abs(x))`) and the chosen engagement outcome. It is a
cross-sectional description without controls, significance claims or causal inference.
Negative obligations remain negative. A constant variable or fewer than three
eligible observations produces an unavailable correlation, never a fabricated zero.

Every lag from 0 to 12 quarters is shown with a fixed −1 to +1 vertical scale. This
sensitivity chart uses the intersection of eligible ZIPs across all 13 lags, so
changes in cohort do not masquerade as changes in the lag relationship. It does not
select an optimal lag. Its cohort may be smaller than the scatterplot's.

The explorer embeds funding for 2012–2021. A window starting before 2012 is unavailable.
Zeros within this range mean zero net obligations in the existing selected extract,
not a verified absence of investment. Source classification and geographic exposure
remain inherited limitations; this update does not rebuild the funding pipeline.

## Review themes

`src/build_review_topics.py` streams the original Yelp review archive and applies
six overlapping, case-insensitive keyword rules: access/parking, surroundings,
cleanliness, price/value, service and food/products. Exact rules and explanatory
labels are stored with the output. This is mention detection, not a trained classifier.

Every eligible review is reconciled in sequence with the existing per-review score
file using ZIP, metro, date, quarter and star rating. A mismatch or extra score
record aborts the build. Existing rounded VADER compound scores are reused; no
external model or service is called. The completed build reconciled 3,073,181 reviews;
2,390,974 matched one or more rules.

Aggregates preserve review count, sum of compound score and negative count for each
ZIP/quarter/theme, plus all-review star histograms. Theme sentiment is the mean
whole-review sentiment among matching reviews. It is not sentiment toward the
matched aspect. Topic shares use all reviews in the selected ZIP or city and quarter
as the denominator, regardless of the active theme. Shares can total over 100%.
City theme means include study ZIPs with no mapped polygon.

The source means for all reviews remain available below 30 reviews so the UI can
apply its 10–200 review threshold consistently. The default remains 30, and the
engagement map uses that threshold for growth and count coverage.
A minimum count is a coverage filter, not an uncertainty interval.

For qualitative inspection, a seeded reservoir (`20260908`) retains up to two
240-character excerpts per city/year/theme/whole-review-polarity group. There are
1,794 stored excerpts. The UI shows up to one per polarity, explicitly citywide and
from the entire selected year, even when a ZIP is selected. This balanced sample
illustrates language; it cannot estimate prevalence. Reviewer identities are omitted,
HTML is escaped, and excerpt content is inserted with `textContent`.

Human validation remains necessary. Examples can describe interiors instead of
neighborhoods, and a positive full review can contain a negative parking remark.
The next step is a labeled evaluation set across cities and years, theme-level
precision/recall, and comparison with a supervised text model.

## Build and verification

```sh
../.venv/bin/python src/build_review_topics.py
../.venv/bin/python src/build_map_page.py
node tests/analysis_math.test.cjs
../.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

The HTML remains self-contained and offline. Aggregates and excerpts are embedded;
the generated page is approximately 3.6 MB. Raw and intermediate data remain ignored
by Git. Interface templates live in `src/map_template.html` and
`src/exploration.{html,css,js}`; pure numerical functions live in `src/analysis_math.js`.

Checks cover funding date alignment, unavailable history, signed amounts, outcome
baselines, degenerate correlations, keyword boundaries and overlapping tags. When
the local data are present, every generated ZIP-quarter review count is reconciled
with the existing panel, and every sample excerpt must contain its theme's terms.
Earlier browser checks covered linked selection, sliders, missing-history states,
themes, table sorting, CSV preview and responsive layout for the sentiment version.
The engagement revision has numerical and generated-page checks but has not had a
fresh automated browser pass. The earlier Tucson access-theme correlation applies
to the previous sentiment outcome and should not be read as an engagement result.

CSV export includes every mapped ZIP in the city, including excluded observations,
with window dates, lag, theme, review threshold and exclusion status. Numeric
engagement values are serialized to at most six decimal places. Preview/copy remains
available when an embedded browser does not support saving a Blob download.

## Population-normalized funding

`src/fetch_population.py` queries Census TIGERweb's public Census2020 ZCTA layer
for `GEOID`, `POP100` and `AREALAND`. The compact source snapshot is tracked at
`data/population_2020.json`, with retrieval timestamp and source URL. All 196 mapped
ZCTAs matched; six have zero population. This is an exact identifier join to the
mapped areas, not a postal ZIP-to-city allocation.

The `$ / resident` map shows current-quarter net obligations divided by the fixed
2020 population. The funding-basis selector in the lag lab changes its scatterplot,
correlation and all-lag sensitivity view to net obligations in the chosen funding
window divided by that same population. The original funding timeline and total
obligations inspector remain dollar totals. Population and current-quarter rates
are also shown in the inspector; their covered-area scope is labeled.

Population must be positive and meet the configurable minimum (500 residents by
default, range 0–5,000). Zero, missing and below-minimum counts produce unavailable
rates, not zero or infinity. The cutoff affects per-resident comparisons, map and
regional population summaries, and can change their cohorts. Total-dollar comparisons
remain available without a population requirement.

The five-region population table and selected-area cards use the same covered
ZCTAs for both funding and population. Regional rates are the ratio of summed
funding to summed population. Regional review growth uses aggregate counts among covered
ZCTAs meeting the selected threshold in both compared quarters. These study
regions are not municipal or official metro populations. They may exclude small,
unmapped or sparsely reviewed areas.

The denominator is held fixed across the 2012–2021 timeline. This comparison does
not estimate historical population, adjust dollars for inflation, control for local
need or validate funding benefit footprints. An administering-office location may
have few residents while serving an entire region; even positive small denominators
can generate extreme rates. Future annual estimates require consistent geography
and explicit boundary-vintage reconciliation.

Rebuild population (network needed) and page:

```sh
../.venv/bin/python src/fetch_population.py
../.venv/bin/python src/build_map_page.py
```

Numerical checks cover zero/missing denominators, negative obligations, valid zero
funding and inclusive population thresholds. An independent calculation reproduced
Tucson's default window (2020Q1–Q4) on 31 covered ZCTAs: 905,196 residents and
$96.06 per resident. Browser checks verified that ZCTA 85721 (zero population)
remains unavailable and hatched, while 85701 (5,132 residents) displays $5,964.16
per resident for that funding window.
