# Data dictionary and interpretation

This describes the current Place Lab exports. The primary notebook and source
manifests specify the exact inputs. JSON `null` and blank numeric CSV cells mean
unavailable or unsupported, never an inferred zero. ZIPs are string identifiers.

## Geography and periods

There are 196 displayed ZIP/ZCTA areas across five metros. Postal ZIP membership
and Census ZCTA polygons are related but not identical. Polygon area includes
water. ZIP evidence compares 2012–2014 with 2019–2021; the later window includes
COVID-19. A separate point model uses a fixed 2018–2019 sample within 500 m of a
ZIP reference point. Historical project outcomes use project-specific windows.
These three units and time definitions must remain distinct.

## Page JSON contract

| File in `web/` | Contents / consumer |
|---|---|
| `place-data.json` | Cities and business records `[longitude, latitude, reviews_2018_2019]`; point-profile calculation. Business records omit original IDs/names, but retain precise coordinates. |
| `place-map.json` | Polygon/MultiPolygon features with ZIP properties and city bounds; map rendering and hit testing. Coordinates are longitude, latitude. |
| `place-areas.json` | ZIP metrics, period definitions, support threshold, method notes and input hashes; focus heatmaps and cards. |
| `place-model.json` | Feature schema, fitted coefficients/transforms, training cases, held-out results, support rules and sensitivity; scenario model. |
| `place-history.json` | Historical near/comparison period counts, annual series, topics and sentiment; evidence charts. |
| `place-build-manifest.json` | Input/code/notebook-source/output SHA-256 hashes and coverage counts; provenance verification. The browser's main data loader reads the five files above. |

## ZIP metrics in `place-areas.json`

| Field | Meaning and unit |
|---|---|
| `business_inventory` | Yelp listings associated with the ZIP in the archive; not a current business census |
| `area_km2` | Spherical area of displayed polygons, subtracting holes |
| `early`, `late` | Period review count, weighted VADER sum and mean; mean is null when there are no reviews |
| `annual_review_density` | Later reviews ÷ 3 years ÷ km²; requires at least 100 later reviews |
| `growth_pct` | 100 × (later reviews ÷ earlier reviews − 1); each period requires at least 100 reviews |
| `sentiment_change` | Later minus earlier review-weighted VADER mean; same period threshold |
| `relative_sentiment_change` | ZIP change minus the change in the rest of its study metro; also requires 100 reviews in each rest-of-metro period |
| `access_mentions`, `access_share_pct` | Access/parking mention count and percentage of later reviews; percentage requires 100 later reviews. Includes praise and complaints. |
| `median_income`, `income_moe` | Historical nominal median household income and supplied ACS margin of error, in dollars |
| `poverty_pct` | Historical ACS poverty proportion multiplied by 100 |
| `acs_year` | ACS five-year period end: 2011 for Philadelphia/Tucson, 2012 for other metros |

The CSV `data/derived/notebook_dataset/zip_evidence.csv` uses more descriptive
column names: `annual_reviews_per_km2`, `review_growth_pct`,
`sentiment_change_vs_metro`, `access_mentions_pct`, `median_household_income`,
`income_margin_of_error`, and `acs_end_year` correspond to the JSON fields above.

## Historical projects and model outputs

Eleven projects are retained; ten meet model-fitting eligibility rules. The outcome
is growth-adjusted excess reviews per nominal reported $1M over two post years:

`CE = (near_post − near_pre × comparison_post / comparison_pre) / cost_millions`

The selected baseline uses budget, reviewed-business count and review intensity,
with log transforms, standardized inputs and ridge regression. City-held-out MAE
is 45.61 reviews/$1M; project-held-out MAE is 49.33. These are exploratory holdout
results, not external validation. The historical error envelope is not a calibrated
confidence interval. Check the model artifact for exact support ranges rather than
copying a range into UI logic.

The remaining CSV exports contain historical project outcomes/eligibility,
project text rates by band/period, learned topic terms, model comparisons, and
timing sensitivity. `*_share` is a fraction; `*_pct` is a percentage. NMF topic
weights are normalized mixtures, not mention rates. VADER, topic mentions and
area-targeted negative clauses are different measures. Independent human label
validation remains unfinished.

Source review excerpts occur in other evidence artifacts and generated evidence
pages, even though the five Place Lab JSON exports omit raw review excerpts and
original identifiers. See [data notices](../DATA_AND_LICENSES.md).
