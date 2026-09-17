# Cross-Project Capital Efficiency and Community Voice Benchmark

**CIS 509 — Analytics for Unstructured Data** · Team 4  
**Date:** September 17, 2026  
**Empirical Source:** `docs/coursework/milestone-2-eda/study_data/capital_efficiency.csv`, `community_voice_aspects.csv`

---

## 1. Executive Summary

This benchmark evaluates the empirical performance of the Three Hypotheses formulated after the Milestone 2 EDA, centered on a 4-stage causal transmission chain:

$$\text{Public Capital Project} \;\xrightarrow{\text{crowding-in}}\; \text{Surrounding Commercial Investment} \;\xrightarrow{\text{foot traffic}}\; \text{Human Interaction} \;\xrightarrow{\text{behavioral trace}}\; \text{Review Engagement}$$

Reviews are not a direct measure of resident welfare or municipal satisfaction; **reviews are an observable digital stand-in for foot-traffic interaction and commercial engagement**. Public projects encourage general investment in surrounding areas; more people interact with the outcomes of those investments (new cafes, outdoor patios, parks); and the more people interact, the more people engage in reviews.

1. **Hypothesis 1 (Community Voice in Reviews):** Supported by keyword tagging; human audit pending. Reviews capture behavioral traces of citizens caring for and reacting to physical surroundings, streetscape conditions, pedestrian access, transit, cleanliness, and public space amenities (456,970 place-theme mentions across 3,073,181 reviews in the study panel; 14.9% overall mention rate across place themes).
2. **Hypothesis 2 (Engagement Generation / Spillover):** Supported for specific public space investments (Lafitte Greenway, Riverfront / Ascend, Dilworth Park), which stimulated substantial local commercial interaction and review volume, while contradicted for heavy fixed rail (Sun Link streetcar).
3. **Hypothesis 3 (Descriptive Capital Efficiency Across Curated Cases):** Supported as a descriptive contrast. Net engagement generated per public dollar varies by two orders of magnitude across the five investments.

> **Methodological Invariant:** With $N=5$ cases (one project per city/typology), project type is collinear with geography, cost scale, and local baseline density. These results are descriptive evaluations of specific capital outlays, not a generalizable causal regression across project classes.

---

## 2. Primary Capital Efficiency Benchmark (500m Buffer, Review Volume)

All metrics evaluate the **Main 2-Year Pre/Post Window** within a **500m Euclidean Buffer** around official project footprints, comparing nearby businesses against matched within-city control pools.

| Rank | Project | Typology & Location | Reported Cost ($M) | Matched Pairs | DiD / Pair | Net Sample Reviews | $CE_{\text{abs}}$ (Revs / $1M) | $CE_{\text{rel}}$ (Rel % / $1M) | $CE_{\text{norm}}$ (Norm % / $1M) | Support Status |
|:---:|:---|:---|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | **Lafitte Greenway** | Greenway / linear trail (New Orleans) | $9.1 | 142 | +10.59 | +1,503.0 | **+165.16** | **+3.80%** | **+4.93%** | **OK** |
| 2 | **Dilworth Park** | Civic plaza / transit hub (Philadelphia) | $55.0 | 498 | +7.50 | +3,733.0 | **+67.87** | **+0.43%** | **+0.42%** | **OK** |
| 3 | **Riverfront / Ascend** | Riverfront park / venue (Nashville) | $52.0 | 85 | +35.93 | +3,054.0 | **+58.73** | **+2.30%** | **+2.53%** | **OK** |
| 4 | **Sun Link** | Streetcar / fixed transit (Tucson) | $196.5 | 149 | −1.22 | −181.0 | **−0.92** | **−0.02%** | **−0.03%** | **OK** |
| — | **Water Works Park** | Riverfront / spring restoration (Tampa) | $7.4 | 2 | −52.50 | −105.0 | −14.19 | −6.59% | −36.38% | **FLAG (Suppressed)** |

### Metric Definitions:
- **DiD / Pair:** Mean net review increase at near businesses minus mean net increase at matched control businesses:
  $$\Delta \bar{Y}_{\text{DiD}} = (\bar{Y}_{\text{near, post}} - \bar{Y}_{\text{near, pre}}) - (\bar{Y}_{\text{ctrl, post}} - \bar{Y}_{\text{ctrl, pre}})$$
- **$CE_{\text{abs}}$ (Absolute Gain per \$1M):** Net matched reviews generated across the cohort divided by project cost:
  $$CE_{\text{abs}} = \frac{N_{\text{pairs}} \times \Delta \bar{Y}_{\text{DiD}}}{\text{Cost (\$M)}}$$
- **$CE_{\text{rel}}$ (Relative Growth per \$1M):** Relative percentage growth rate divided by project cost:
  $$CE_{\text{rel}} = \frac{\Delta E_{\text{rel}}}{\text{Cost (\$M)}}$$
- **$CE_{\text{norm}}$ (Baseline-Normalized Efficiency):** Net review generation scaled by pre-existing near volume and cost:
  $$CE_{\text{norm}} = \frac{N_{\text{pairs}} \times \Delta \bar{Y}_{\text{DiD}}}{\left(\sum_{i \in \mathcal{N}} Y_{i, \text{pre}}\right) \times \text{Cost (\$M)}} \times 100$$
- **Support Invariant:** Water Works Park has only 2 primary matched pairs ($N < 20$); its ratio metrics explode misleadingly and are suppressed from ranking comparisons.

---

## 3. Commercial Business Participation Benchmark (500m Buffer)

Evaluates all active reviewed listings on Yelp within 500m regardless of baseline review thresholds, comparing near growth against farther-area (1.5–8 km) city growth.

| Project | Reported Cost ($M) | Total Listings | Baseline Active | Post Active | Raw Growth % | Farther Area Growth % | Rel. Business Growth % | Net Counterfactual Businesses Added | $CE_{\text{biz}}$ (Net Biz / $1M) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Lafitte Greenway** | $9.1 | 436 | 244 | 343 | +40.6% | +33.4% | **+5.39%** | +17.5 | **+1.93** |
| **Riverfront / Ascend** | $52.0 | 308 | 123 | 202 | +64.2% | +63.2% | **+0.65%** | +1.3 | **+0.03** |
| **Water Works Park** | $7.4 | 75 | 6 | 21 | +250.0% | +106.9% | **+69.17%** | +8.6 | **+1.16\*** |
| **Sun Link** | $196.5 | 717 | 278 | 470 | +69.1% | +108.0% | **−18.73%** | −108.3 | **−0.55** |
| **Dilworth Park** | $55.0 | 1,697 | 856 | 1,160 | +35.5% | +64.5% | **−17.63%** | −248.3 | **−4.51** |

*\*Note: Water Works Park shows large business growth (+250%), but starts from a tiny baseline of 6 businesses.*

### Key Insights:
1. **Lafitte Greenway** is the only project with positive matched engagement *and* positive relative business expansion ($CE_{\text{biz}} = +1.93$ active businesses added per \$1M).
2. **Dilworth Park and Sun Link** saw substantial absolute increases in reviewed businesses (+304 and +192 listings), but grew significantly *slower* than their surrounding metro areas (−17.6% and −18.7% relative contrast).

---

## 4. Distance Sensitivity Analysis

How capital efficiency behaves across 250m, 500m, and 1,000m buffers:

| Project | Radius | Pairs | DiD / Pair | Net Sample Reviews | $CE_{\text{abs}}$ (Revs / $1M) | $CE_{\text{norm}}$ (% / $1M) | Support |
|:---|---:|---:|---:|---:|---:|---:|:---:|
| **Lafitte** | 250m | 40 | +19.68 | +787.0 | +86.48 | +8.96% | OK |
| | 500m | 142 | +10.59 | +1,503.0 | +165.16 | +4.93% | OK |
| | 1,000m | 641 | +23.26 | +14,907.0 | +1,638.13 | +6.36% | OK |
| **Dilworth Park** | 250m | 95 | −1.27 | −121.0 | −2.20 | −0.07% | OK |
| | 500m | 498 | +7.50 | +3,733.0 | +67.87 | +0.42% | OK |
| | 1,000m | 1,013 | +6.39 | +6,475.0 | +117.73 | +0.34% | OK |
| **Riverfront / Ascend** | 250m | 21 | +44.48 | +934.0 | +17.96 | +3.25% | OK |
| | 500m | 85 | +35.93 | +3,054.0 | +58.73 | +2.53% | OK |
| | 1,000m | 154 | +12.55 | +1,933.0 | +37.17 | +1.00% | OK |
| **Sun Link** | 250m | 130 | −1.36 | −177.0 | −0.90 | −0.03% | OK |
| | 500m | 149 | −1.22 | −181.0 | −0.92 | −0.03% | OK |
| | 1,000m | 176 | −0.92 | −161.0 | −0.82 | −0.02% | OK |
| **Water Works Park** | 250m | 1 | −59.00 | −59.0 | −7.97 | −56.95% | FLAG |
| | 500m | 2 | −52.50 | −105.0 | −14.19 | −36.38% | FLAG |
| | 1,000m | 23 | −26.83 | −617.0 | −83.38 | −22.18% | OK |

*\*Note: Net Sample Reviews and $CE$ metrics are computed from unrounded floating-point differences (e.g., Sun Link 1,000m raw DiD is −0.91477, yielding $-0.91477 \times 176 = -161.0$, rather than the rounded displayed −0.92).*

---

## 5. Local Income Tercile Distribution (Equity Analysis)

Capital efficiency broken down by within-city baseline income terciles (500m buffer):

| Project | Income Band | Pairs | DiD / Pair | $CE_{\text{abs}}$ (Revs / $1M) | $CE_{\text{norm}}$ (% / $1M) | Support |
|:---|:---|---:|---:|---:|---:|:---:|
| **Lafitte** | Lower | 108 | +9.54 | **+113.19** | **+4.30%** | OK |
| | Middle | 32 | +13.59 | **+47.80** | **+7.38%** | OK |
| | Higher | 2 | +19.00 | +4.18 | +5.72% | FLAG |
| **Dilworth Park** | Lower | 1 | +5.00 | +0.09 | +0.43% | FLAG |
| | Middle | 171 | +21.02 | **+65.35** | **+1.04%** | OK |
| | Higher | 326 | +0.41 | **+2.44** | **+0.02%** | OK |
| **Riverfront / Ascend** | Lower | 25 | +37.80 | **+18.17** | **+1.79%** | OK |
| | Middle | 2 | +61.50 | +2.37 | +2.60% | FLAG |
| | Higher | 58 | +34.24 | **+38.19** | **+3.14%** | OK |
| **Sun Link** | Lower | 140 | −1.99 | **−1.41** | **−0.04%** | OK |
| | Middle | 9 | +10.78 | +0.49 | +0.47% | FLAG |
| | Higher | 0 | — | — | — | — |
| **Water Works Park** | Higher | 2 | −52.50 | −14.19 | −36.38% | FLAG |

### Key Equity Findings:
1. **Lafitte Greenway delivered its largest absolute volume gain in lower-income neighborhoods:** 108 of its 142 pairs are in the lower-income band, generating $+113.19$ net reviews/\$1M.
2. **Dilworth Park gains were heavily concentrated in middle-income ZIPs:** 171 pairs generated $+65.35$ net reviews/\$1M, while 326 higher-income pairs had virtually zero DiD gain ($+0.41$ reviews/pair).
3. **Sun Link streetcar underperformed in lower-income areas:** In the lower-income band (140 pairs), review volume lagged matched controls by $-1.99$ reviews/pair ($CE_{\text{abs}} = -1.41$).

---

## 6. Community Voice NLP Discourse Analysis

### 6.1 Full-Corpus Panel Prevalence (3,073,181 Reviews, 277 ZIPs)
Across all reconciled reviews in the 2012–2021 panel (`data/interim/review_topics.json`):
- **Total reviews scanned:** 3,073,181
- **Tagged with $\ge 1$ theme:** 2,390,974 (77.8%)
- **Place / Community Voice Mentions (456,970 total mentions):**
  - **Cleanliness:** 263,660 mentions (**8.6%** of all reviews)
  - **Access & Parking:** 119,671 mentions (**3.9%** of all reviews)
  - **Surroundings & Safety:** 73,639 mentions (**2.4%** of all reviews)
- **Commercial / Transactional Mentions:**
  - **Food & Products:** 1,661,743 mentions (**54.1%** of all reviews)
  - **Service & Staff:** 1,410,605 mentions (**45.9%** of all reviews)
  - **Price & Value:** 491,493 mentions (**16.0%** of all reviews)

Commercial evaluation is the primary driver of reviews, but place-based conditions appear in hundreds of thousands of reviews across the study metros.

### 6.2 Seeded Qualitative Reservoir (1,794 Excerpts)
The offline exploration interface embeds 1,794 short excerpts sampled into a seeded reservoir (2 excerpts per city, year, theme, and polarity cell):
- **Sample Mention Rate:** **52.1%** of sampled excerpts contain $\ge 1$ community voice aspect.
- *Methodological Note:* This 52.1% figure is an artifact of the balanced reservoir design, which deliberately samples equally across themes to ensure qualitative visibility. It is directional and qualitative, not a population prevalence rate.
- Breakdown within the qualitative sample:
  - Surroundings & Neighborhood Safety: 23.4%
  - Access, Walkability & Transit: 20.8%
  - Cleanliness & Public Space Amenities: 19.0%

### 6.3 Representative Community Voice Excerpts:
- *Positive Access / Public Space:* "The greenway trail right outside makes walking over after work so easy and pleasant."
- *Negative Access / Construction:* "Street construction and torn up sidewalks made parking and walking in the rain impossible."
- *Cleanliness & Surroundings:* "Outdoor patio sits right on the park with clean landscaping and great city views."

*Status:* Supported by keyword tagging and rule-based mention detection. The synthetic benchmark sentences in `tests/test_community_voice_nlp.py` verify parser mechanics; formal human audit across stratified review lengths and star ratings remains pending.
