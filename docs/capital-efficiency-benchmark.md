# Capital Efficiency and Community Voice Benchmark

**CIS 509 — Analytics for Unstructured Data · Team 4**
**Updated:** September 24, 2026

## What the score measures

Capital Efficiency (CE) is a descriptive difference in Yelp review activity divided by reported project cost in $ millions. Reviews reflect online participation, not visits, revenue, resident welfare, or a causal effect of construction. Reported costs may mix public and private funding.

The five original projects do not share one estimation method. Lafitte Greenway, Dilworth Park, Riverfront / Ascend, and Water Works Park use matched nearby businesses. Sun Link uses every Yelp listing along its full streetcar route, compared with an unmatched farther Tucson area. **The two methods must not be ranked as though their scores had the same interpretation.** The six additional candidate projects use unmatched cohort means and form a third methodological group.

## Four matched project samples

For matched projects, the review difference per nearby business is its pre/post change minus that of its matched control. Matched-sample CE equals that difference times the number of matched nearby businesses, divided by reported project cost. The numerator covers the matched sample, not every establishment around the footprint.

| Project | Cost ($M) | Matched businesses at 500 m | Review difference / business | Net sample reviews | CE (reviews / $1M) | Support |
|---|---:|---:|---:|---:|---:|---|
| Lafitte Greenway | 9.1 | 142 | +10.59 | +1,503 | +165.16 | Adequate |
| Dilworth Park | 55.0 | 498 | +7.50 | +3,733 | +67.87 | Adequate |
| Riverfront / Ascend | 52.0 | 85 | +35.93 | +3,054 | +58.73 | Adequate |
| Water Works Park | 7.4 | 2 | −52.50 | −105 | Suppressed | Inadequate at 500 m |

The matched rows come from `study_data/engagement.csv` and are recalculated by `src/engagement_efficiency.py` into `study_data/capital_efficiency.csv`. Water Works is displayed without a 500 m CE because two pairs cannot support a stable ratio.

## Sun Link: full-route recalculation

Sun Link is a 3.9-mile streetcar route through central Tucson districts ([operator route information](https://sunlinkstreetcar.com/)). The 500 m catchment includes **717 Yelp listings**, including listings with no baseline reviews. The comparison inventory contains 4,151 listings 1.5–8 km from the route. The pre period is 2010–2011 and the post period is 2015–2016.

The active score uses the farther area's proportional review growth as a descriptive counterfactual for the same corridor baseline:

$$\text{Expected corridor post reviews} = \text{Corridor pre reviews}\times\frac{\text{Farther post reviews}}{\text{Farther pre reviews}}$$
$$\text{Corridor CE} = \frac{\text{Observed corridor post reviews}-\text{Expected corridor post reviews}}{\text{Reported cost in \$M}}$$

At 500 m, corridor reviews increased **3,807 → 10,943** (+187.4%). Farther-area reviews increased **9,957 → 34,394** (+245.4%). Applying that comparison growth factor to the corridor baseline gives **13,150.3 expected** post reviews. The difference is **−2,207.3 reviews**, or **−11.23 reviews per $1M** of the $196.5M reported project cost. The raw corridor increase was **+7,136 reviews**. The negative adjusted value means corridor review growth was slower than the farther area, not that review counts fell.

| Distance from full route | Yelp listings | Corridor pre → post reviews | Growth-adjusted difference | CE (reviews / $1M) |
|---|---:|---:|---:|---:|
| 250 m | 583 | 3,263 → 9,395 | −1,876.2 | −9.55 |
| 500 m | 717 | 3,807 → 10,943 | −2,207.3 | −11.23 |
| 1,000 m | 909 | 4,342 → 12,548 | −2,450.4 | −12.47 |

The result is robustly negative across these three radius choices and a location-flag exclusion check. The 500 m lower-income subgroup has 631 listings and 248 baseline-reviewed listings; its adjusted difference is −2,338.2 reviews (−11.90 per $1M). Middle and higher-income subgroup estimates are withheld for inadequate baseline support. Subgroups at 250 and 1,000 m have not been calculated.

This is **unmatched**. The farther inventory differs from the corridor in baseline business mix, geography, and review intensity. Inclusion of listings first reviewed after opening also mixes activity at existing businesses with changing Yelp coverage. Neither the growth adjustment nor the CE ratio identifies a causal effect or financial return. Source aggregates are `study_data/sun_scopes.csv`, `sun_coverage.csv`, and `sun_income.csv`; `src/sun_link_corridor.py` writes the reproducible `sun_link_corridor_efficiency.csv` output.

## Business participation and review language

The full-route inventory had 278 businesses with at least one baseline review and 470 with at least one post-period review. This is growth in *reviewed listings*, not a verified count of new or surviving businesses. The farther-area comparison also grew, so Sun Link's relative reviewed-business growth was −18.73% despite the positive absolute increase. `study_data/business_growth.csv` records the five projects' participation contrasts.

The review text panel tags access and parking, surroundings and safety, and cleanliness and public space alongside commercial themes. Across the study panel, 456,970 reviews mention at least one place theme. These are rule-based mentions, not validated measures of resident sentiment toward investment. The app keeps review engagement and sentiment separate.

## Scenario studio and further modeling

The Capital Efficiency Studio uses each project's observed difference as a transparent reference case. It now lets a user change cost, count, and both near and comparison review trends. For matched references, scenario CE is `businesses × (near review change/business − comparison review change/business) ÷ proposed cost ($M)`. Sun Link retains its separate proportional method: `route listings × observed baseline reviews/listing × (assumed corridor growth − assumed farther growth) ÷ proposed cost ($M)`. The inputs initialize from observed reference changes and can be reset; a break-even control equates the two trends. These editable assumptions are not fitted coefficients or learned project effects.

The studio also displays an observed 500 m reviewed-listing participation contrast, matched whole-review VADER contrasts, and a sampled location/identity topic-share shift where supported. Listing participation uses all source-area Yelp listings and a farther-area growth comparison, a different cohort from matched review CE. The topic shift comes from baseline-trained Word2Vec embeddings and MiniBatchKMeans clustering, with mixed category meaning and unequal sampling fractions (`study_data/embedding_audit.json`). These companion outcomes do not change CE. Sun Link's earlier restricted text cohort is excluded from the active studio. Target ZIP data provide context but do not supply a measured 250–1,000 m catchment. The studio withholds unsupported subgroups and labels each method.

Five heterogeneous original projects cannot identify separate effects of project type, cost, city, baseline density, and income. The six expansion cases currently use a different comparison design. A fitted cross-project model requires harmonized cohorts, more independent projects, and validation that leaves entire projects out. Until then, scores are illustrative descriptive comparisons.
