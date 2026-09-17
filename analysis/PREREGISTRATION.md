# Pre-registration: does public investment move low-price businesses more?

**Project:** neighborhood-sentiment-map · CIS 509 Team 4
**Written:** 2026-09-11, before any segmented analysis has been run
**Status at time of writing:** the only results computed are the pooled specification
curve in `spec_curve_results.csv` (648 specifications + 486 placebo). No analysis
has been run on any business segment. This document is committed to establish that
ordering.

---

## 1. Why we are pre-registering this

Our Milestone 2 analysis found a matched-quarter correlation of r = 0.077 between
federal assistance and review sentiment. The specification curve showed that number
ranges from −0.20 to +0.26 across defensible analytic choices, and the placebo family
— funding dated *after* the sentiment it supposedly explains — reproduces the real
result (paired difference −0.0041; the real specification beats its own placebo in
43.8% of pairs). We treat the pooled hypothesis as falsified under this measurement
design.

Segmenting the data is the most likely way we would resurrect that dead hypothesis as
a false positive. Five segments across 648 specifications is over three thousand
chances to find something. So the contrast, the predicted direction, and the decision
rule are fixed here, in advance.

## 2. Hypothesis

**H1.** Place-based federal investment is associated with a larger improvement in
review sentiment for low-price, neighborhood-serving businesses than for mid-price
businesses.

**Mechanism.** Streetscape, transit and housing investment changes walk-in
accessibility and the quality of the immediate local catchment. Yelp price-tier-1
businesses draw disproportionately on walking and local trade; tier-2 businesses draw
more on deliberate trips. If public investment affects business experience through
the street, it should bind more tightly on tier 1.

**Predicted sign, stated before observation:** the tier-1 effect exceeds the tier-2
effect. Δ > 0 as defined in §5.

This prediction is falsifiable in three distinct ways: Δ ≤ 0, Δ indistinguishable
from zero, or tier 1 failing to beat its own placebo.

## 3. Why price tier and not business type

The mechanically obvious contrast — foot-traffic businesses versus destination
businesses (auto, medical, professional services) — **cannot be tested on Yelp data**
and we are recording that finding here rather than discovering it later:

| Segment | Reviews (study states, 2012–2021) | Share | Reviews/business | ZIP-quarter cells ≥10 reviews |
|---|---:|---:|---:|---:|
| Foot-traffic | 49,913 | 83.2% | 13.4 | 1,316 |
| Other | 7,214 | 12.0% | 5.0 | — |
| Destination | 2,843 | 4.7% | 2.9 | **0** |

The comparison arm is empty, not merely small. Price tier is 95.7% populated among
foot-traffic businesses and splits them into two well-populated groups (tier 1:
1,208 businesses; tier 2: 1,378). Tiers 3–4 (128 businesses) are too thin and are
excluded in advance.

## 4. Data and construction

Required inputs, **not yet in hand at time of writing**:

- Review-level sentiment with `business_id` (`reviews_5metro.csv`, or rebuilt from the
  Yelp Open Dataset)
- Business categories and the `RestaurantsPriceRange2` attribute
  (`yelp_academic_dataset_business.json`)
- Assistance transactions 2012–2021 and `metro_zips.json` — already in hand

Construction:

1. Restrict to foot-traffic businesses (categories containing Restaurants, Bars,
   Cafes, Coffee & Tea, Nightlife, Shopping, Bakeries, Breakfast & Brunch).
2. Assign each business price tier 1 or 2; drop tiers 3–4 and missing.
3. Build a separate ZIP-quarter sentiment panel **per tier**, requiring the review
   threshold to be met *within* that tier.
4. Join assistance exactly as in `spec_curve.py`, unchanged.

## 5. Estimand and primary specification

For a given specification *s* and tier *t*, define the **placebo-corrected gap**

```
gap(s, t) = r_real(s, t) − r_placebo(s, t)
```

where `r_placebo` uses funding dated after the sentiment (negative lag), as already
implemented. The estimand is

```
Δ(s) = gap(s, tier 1) − gap(s, tier 2)
```

**Primary specification, fixed now:**

| Choice | Value | Reason |
|---|---|---|
| Exposure | place-based CFDA set | the only exposure with a street-level mechanism |
| Amount | gross positive obligations | de-obligations are accounting events, not investment |
| Threshold | ≥30 reviews within tier | matches the Milestone 2 panel |
| Variation | within-ZIP | the only variation that speaks to change, not place |
| Window | 2012–2021 | full |
| Lag | **averaged over 0, 1, 2, 4 quarters** | pre-commits us to not select a lag after seeing results |

The remaining grid from `spec_curve.py` is **robustness, not confirmation**.

**Uncertainty.** 95% confidence interval on Δ by bootstrap over ZIPs (clustered,
because ZIP-quarters repeat within a ZIP), 1,000 resamples, `seed = 509`.

## 6. Decision rule

Fixed in advance. We report whichever of these the data produces.

**Support for H1** requires *all three*:
1. The bootstrap 95% CI for Δ in the primary specification excludes zero, and Δ > 0.
2. Tier 1 beats its own placebo: gap(primary, tier 1) > 0.
3. The sign of Δ holds in at least two-thirds of the robustness grid.

**Refutation** if Δ ≤ 0, or the CI includes zero, or tier 1 does not beat its placebo.
Condition 2 is decisive on its own: if tier 1 cannot beat funding dated after the
fact, no difference between tiers can be causal, regardless of Δ.

**Inconclusive — reported as such, not as a null** — if either arm has fewer than 500
ZIP-quarter cells after the within-tier threshold. Underpowered is not the same as
absent, and we will not present it as absent.

## 7. What we report regardless of outcome

The full specification curve for both tiers, both placebo families, the Δ
distribution, and cell counts per arm. The pre-registered primary result is reported
first, whatever it says.

Any further segmentation — cuisine, chain status, tiers 3–4, region — is **exploratory**,
will be labeled exploratory, and will not be reported as confirmatory evidence for H1.

## 8. Known threats to this test

1. **Price tier is a snapshot, not history.** The attribute reflects the dataset
   snapshot, not the business's tier in 2014. Same limitation as `is_open`. We will
   report it as a measurement caveat and cannot correct it.
2. **Tier missingness may be geographic.** 4.3% of foot-traffic businesses lack a
   tier. We will report the missingness rate by ZIP and check it is not differential
   across high- and low-funding ZIPs.
3. **Categories overlap.** A business can be both Shopping and Restaurants; the
   foot-traffic filter is inclusive by design.
4. **Composition change.** Tier mix within a ZIP can shift over time through entry and
   exit, which within-ZIP differencing does not remove.
5. **Exposure is still place-of-performance ZIP,** with all the limitations recorded in
   the Milestone 2 notebook. This test changes the outcome side, not the exposure side.

## 9. Authorship and AI use

Written by Team 4 with Anthropic's Claude, which computed the segment feasibility
figures in §3 from the public Yelp sample and drafted this document. The hypothesis,
the predicted direction, and the decision rule are the team's to defend. No segmented
result existed when this was committed.
