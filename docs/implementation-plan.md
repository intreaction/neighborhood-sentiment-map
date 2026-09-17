# Implementation Plan: Community Voice, Public Investment, and Capital Efficiency

**CIS 509 — Analytics for Unstructured Data** · Team 4  
**Date:** September 17, 2026  
**Document Status:** Approved architecture guiding subsequent implementation phases.

---

## 1. Empirical Hypotheses and Analytical Foundation

### 1.1 The Causal Transmission Chain and Reformulated Hypotheses
The Milestone 2 Exploratory Data Analysis (EDA) demonstrated that customer sentiment and star ratings do not systematically track public capital expenditure ($r \approx 0.00$, failed temporal placebo test). Yelp reviews are not a survey of resident happiness or a direct measure of municipal policy approval. Rather, **reviews are an observable digital proxy for commercial and foot-traffic interaction**.

The underlying economic and behavioral mechanism follows a 4-stage transmission chain:

$$\text{Public Capital Project} \;\xrightarrow{\text{crowding-in}}\; \text{Surrounding Commercial Investment} \;\xrightarrow{\text{foot traffic}}\; \text{Human Interaction} \;\xrightarrow{\text{behavioral trace}}\; \text{Review Engagement}$$

1. **Stage 1 (Public Capital Outlay):** A public entity commits place-based capital (e.g., greenway trail, civic plaza, riverfront park, transit line).
   - *Observed Metric:* Reported project capital cost in millions ($M) from official project accounts and FTA grants.
   - *Measurement Caveat:* Headline figures conflate federal grants, municipal bonds, and private match funds; public expenditures are not reconciled to audited contractor outlays.
2. **Stage 2 (Spillover & Surrounding Investment):** The public amenity encourages private and commercial investment in the immediate catchment (adaptive reuse of buildings, new storefronts, cafes, outdoor seating, park activation).
   - *Observed Metric:* Net active reviewed business participation contrast within 500m (`business_growth.csv`).
   - *Empirical Evidence:* Mixed across projects (Lafitte +5.4%, Riverfront +0.7%, Dilworth −17.6%, Sun Link −18.7%).
3. **Stage 3 (Physical Interaction & Foot Traffic):** More people visit, walk through, recreate in, and patronize the outcomes of those public and private investments.
   - *Measurement Caveat:* **Unobserved directly** in Yelp data (no pedestrian counter or cellular mobility telemetry). Check-in counts serve as the closest observable foot-traffic proxy; the conversion of visits into Yelp reviews is a structural behavioral assumption of this research design.
4. **Stage 4 (Observable Digital Voice & Engagement):** As foot traffic and patron interactions increase, a fraction of those interacting leave behavioral traces (reviews, tips, check-ins, photos) and articulate their experience of the surrounding neighborhood conditions.
   - *Observed Metric:* Matched difference-in-differences in review volume, unique reviewer counts, check-ins, and community voice topic shares.

Under this transmission mechanism, we test three operational hypotheses (reformulated post-EDA to replace the falsified direct spending $\rightarrow$ sentiment link):

1. **Hypothesis 1 (Community Voice):** Because reviews are behavioral traces of people interacting with places, unstructured text contains substantive commentary on physical surroundings, walkability, transit, cleanliness, and public space, alongside transactional food/service evaluations.
2. **Hypothesis 2 (Engagement Generation):** Publicly funded projects catalyze general investment and foot traffic in their surrounding catchment, generating measurable net increases in active reviewed businesses and review volume relative to matched counterfactual areas.
3. **Hypothesis 3 (Capital Non-Linearity: "More Dollars ≠ More Engagement"):** Public investment can encourage local interaction, but engagement outcomes do not scale with the dollar magnitude of the capital outlay. Higher expenditure does not guarantee higher engagement per dollar or greater absolute engagement. Across our five curated cases, the most expensive project (Sun Link at $196.5M) produced the lowest engagement contrast (−1.22 reviews/pair DiD, −18.7% business expansion contrast), while the low-cost greenway (Lafitte at $9.1M) produced the highest capital efficiency (+165.16 net reviews/$M, +5.4% business expansion). With $N=5$ cases, project type is collinear with geography, cost scale, and density; this is strictly a descriptive comparison of specific capital outlays, not a generalizable causal regression across project classes.

### 1.2 Grounding in EDA Evidence

| Project | Typology | Reported Cost ($M) | Relative Review Growth (500m) | Relative Business Growth (500m) | Baseline Local Income Contrast |
|---|---|---:|---:|---:|---|
| **Lafitte Greenway** (New Orleans) | Greenway / linear park | $9.1 | +34.5% (Main) / +26.3% (Lower band) | +5.4% | Robust positive growth concentrated in lower-income ZIPs (+26.3%). |
| **Riverfront / Ascend** (Nashville) | Riverfront park / venue | $52.0 | +64.2% (Unmatched) / +59.7% (Lower band) | +0.7% | High activity growth, but matched citywide growth leaves business participation flat (+0.7%). |
| **Dilworth Park** (Philadelphia) | Civic plaza / transit hub | $55.0 | +23.7% (All) / −4.1% (250m) | −17.6% | Sensitive to radius; driven by top 5% busiest establishments (contrast drops to +5.8% without them). |
| **Water Works Park** (Tampa) | Riverfront / spring restoration | $7.4 | Suppressed at 500m (2 pairs) / −44.8% at 1km | +69.2% (Raw) | Severe baseline sparsity (only 2 matched pairs); percentage contrasts uninterpretable without support indicators. |
| **Sun Link** (Tucson) | Streetcar / fixed transit | $196.5 | −3.4% (All) / −6.5% (Lower band) | −18.7% | Highest cost by 3.5x, yet shows negative relative engagement and lagging business participation. |

---

## 2. Mathematical Formulations and Estimands

### 2.1 Engagement Metrics Vector ($E$)
For a given business $i$ in period $p \in \{\text{pre}, \text{post}\}$:
$$E_{i, p} = \big[ Y_{i, p}^{\text{reviews}}, \; Y_{i, p}^{\text{reviewers}}, \; Y_{i, p}^{\text{checkins}}, \; Y_{i, p}^{\text{tips}} \big]$$

At the cohort/area level:
$$N_{p}^{\text{active}} = \sum_{i \in \mathcal{B}} \mathbb{I}(Y_{i, p}^{\text{reviews}} \ge 1)$$

### 2.2 Relative Engagement Growth ($\Delta E$)
For near cohort $\mathcal{N}$ and matched comparison cohort $\mathcal{C}$:
$$\text{Growth}_{\mathcal{N}} = \frac{\bar{Y}_{\mathcal{N}, \text{post}}}{\bar{Y}_{\mathcal{N}, \text{pre}}} - 1, \quad \text{Growth}_{\mathcal{C}} = \frac{\bar{Y}_{\mathcal{C}, \text{post}}}{\bar{Y}_{\mathcal{C}, \text{pre}}} - 1$$

$$\Delta E_{\text{rel}} = \left( \frac{\bar{Y}_{\mathcal{N}, \text{post}} / \bar{Y}_{\mathcal{N}, \text{pre}}}{\bar{Y}_{\mathcal{C}, \text{post}} / \bar{Y}_{\mathcal{C}, \text{pre}}} - 1 \right) \times 100$$

Alongside log-transformed contrast to mitigate extreme skew:
$$\Delta E_{\log} = \frac{1}{|\mathcal{P}|} \sum_{(i, j) \in \mathcal{P}} \left[ \big(\ln(1 + Y_{i, \text{post}}) - \ln(1 + Y_{i, \text{pre}})\big) - \big(\ln(1 + Y_{j, \text{post}}) - \ln(1 + Y_{j, \text{pre}})\big) \right]$$

### 2.3 Capital Efficiency Estimands ($CE$)
Because absolute review gains are inflated by dense baselines (e.g., Center City Philadelphia) while percentage gains are inflated by sparse baselines (e.g., Water Works Park), we designate a **single primary ranking metric** ($CE_{\text{abs}}$) alongside secondary context columns ($CE_{\text{rel}}$, $CE_{\text{norm}}$, $CE_{\text{biz}}$):

1. **Primary Headline Metric: Absolute Matched Gain per \$1M Capital Outlay ($CE_{\text{abs}}$):**
   Measures net reviewer traffic added to the matched business sample per million dollars invested:
   $$CE_{\text{abs}} = \frac{\sum_{i \in \mathcal{N}} (Y_{i, \text{post}} - Y_{i, \text{pre}}) - \sum_{j \in \mathcal{C}} (Y_{j, \text{post}} - Y_{j, \text{pre}})}{\text{Cost (\$M)}} = \frac{|\mathcal{P}| \times \Delta \bar{Y}_{\text{DiD}}}{\text{Cost (\$M)}}$$

2. **Relative Growth Rate per \$1M Capital Outlay ($CE_{\text{rel}}$):**
   Measures the net percentage acceleration of nearby activity relative to control trend per million dollars:
   $$CE_{\text{rel}} = \frac{\Delta E_{\text{rel}}}{\text{Cost (\$M)}}$$

3. **Baseline-Normalized Capital Efficiency ($CE_{\text{norm}}$):**
   Normalizes net absolute review generation by the pre-existing baseline review volume of the near cohort:
   $$CE_{\text{norm}} = \frac{|\mathcal{P}| \times \Delta \bar{Y}_{\text{DiD}}}{\left(\sum_{i \in \mathcal{N}} Y_{i, \text{pre}}\right) \times \text{Cost (\$M)}} \times 100 = \frac{\Delta E_{\text{net}}}{\text{Baseline Volume} \times \text{Cost (\$M)}} \times 100$$

4. **Active Business Expansion per \$1M Capital Outlay ($CE_{\text{biz}}$):**
   Measures net reviewed business participation on Yelp within the 500m catchment per million dollars:
   $$CE_{\text{biz}} = \frac{\Delta N_{\mathcal{N}}^{\text{active}} - \left(N_{\mathcal{N}, \text{pre}}^{\text{active}} \times \text{Growth}_{\mathcal{C}}^{\text{biz}}\right)}{\text{Cost (\$M)}}$$

5. **Support and Display Invariant:**
   Ratios with $N_{\text{pairs}} < 20$ (specifically Water Works Park primary 500m with $N=2$) MUST be marked `low_support = True` and suppressed from ranking comparisons. No ratio may be presented without its underlying baseline counts.

### 2.4 Community Voice Share ($CVS$)
To test Hypothesis 1, text is partitioned into Community Aspects ($\mathcal{A}_{\text{community}}$) vs. Transactional Aspects ($\mathcal{A}_{\text{commercial}}$):
- $\mathcal{A}_{\text{community}}$: Surroundings & Streetscape, Accessibility & Transit, Walkability & Bikeability, Cleanliness & Public Safety.
- $\mathcal{A}_{\text{commercial}}$: Food & Taste, Service & Speed, Product Quality, Price & Value.

For review $r \in \mathcal{R}$:
$$CVS = \frac{\sum_{r \in \mathcal{R}} \mathbb{I}(\exists a \in \mathcal{A}_{\text{community}} \text{ in } r)}{|\mathcal{R}|}$$
$$\Delta CVS = CVS_{\text{near, post}} - CVS_{\text{near, pre}} - \big(CVS_{\text{ctrl, post}} - CVS_{\text{ctrl, pre}}\big)$$

---

## 3. Architecture and Component Design

```mermaid
flowchart TD
    A[Yelp & Spatial Extracts] --> B[src/engagement_efficiency.py]
    A --> C[src/community_voice_nlp.py]
    P[study_data/project_registry.json] --> B
    P --> C
    B --> D[study_data/capital_efficiency.csv]
    C --> E[study_data/community_voice_aspects.csv]
    D --> F[src/build_map_page.py]
    E --> F
    F --> G[web/index.html & exploration.js]
```

### 3.1 Data Contracts & Storage
1. **`study_data/project_registry.json` (Source of Truth):**
   - Project metadata, historical opening dates, official geometries, reported capital costs, coordinate reference systems (EPSG), and ACS baseline years.
2. **`study_data/capital_efficiency.csv`:**
   - Pre-computed $CE_{\text{reviews}}$, $CE_{\text{biz}}$, $\Delta E_{\text{rel}}$, $\Delta E_{\log}$, sample sizes, pair counts, and support flags across buffer radii (250m, 500m, 1000m) and income tiers.
3. **`study_data/community_voice_aspects.csv`:**
   - Aspect prevalence, aspect-specific sentiment distributions, sentence-level excerpts, and pre/post shifts for community vs. transactional terms.

### 3.2 Computational Modules (`src/`)
- **`src/engagement_efficiency.py`:**
  - Ingests `engagement.csv`, `business_growth.csv`, and `project_registry.json`.
  - Calculates point estimates, standard errors (clustered by business pair), and capital efficiency indices.
  - Emits `study_data/capital_efficiency.csv` and summary markdown tables.
- **`src/community_voice_nlp.py`:**
  - Implements rule-based and supervised aspect classifiers (integrating BERT/deep-learning representations aligned with CIS 509 Lab 3/4).
  - Validates negative recall and precision against a stratified audit sample of 500 reviews.
  - Extracts place-based discourse shifts before and after project completion.
- **`src/build_map_page.py` & `src/exploration.js`:**
  - Refactors front-end interface:
    1. Replaces ZCTA gross dollar explorer with **Project Capital Efficiency Benchmark**.
    2. Adds **Typology Comparison Matrix** (Greenway vs Plaza vs Transit vs Riverfront).
    3. Integrates **Community Voice Inspector** showing exact review excerpts where citizens discuss the public space.
    4. Enforces visual support guards (graying out or hatching under-supported estimates like Water Works Park).

### 3.3 Prospective Planning Tool: Reference-Case Scenario Explorer
To assist policymakers planning future capital investments without making unconstrained statistical claims, the system implements a **Reference-Case Scenario Explorer**:

1. **Methodological Framing (Adopted RCF Spirit):**
   Supervised machine learning cannot be trained on $N=5$ retrospective case studies (zero degrees of freedom; catastrophic overfitting). Instead, we adopt the principles of Reference Class Forecasting (Kahneman & Flyvbjerg): evaluating proposed investments against the empirical distributions of observed past projects rather than unconstrained regressions. Because our reference class contains 5 cases ($N=1$ per typology), outputs are presented strictly as **illustrative scenario ranges**, never point-estimate predictions.

2. **Single-Case Sourced Bounds (Derived from Distance Sensitivities):**
   Each typology maps to a single empirical reference project, displaying its $N=1$ evidentiary weight directly in the UI. Rather than fabricated symmetric error bands, scenario bounds reflect the project's actual observed sensitivity across radii (250m, 500m, 1,000m):
   - **Linear Greenway ($N=1$, Lafitte):** DiD $+10.59$ to $+23.26$ reviews/pair (500m: $+10.59$, 250m: $+19.68$, 1000m: $+23.26$). Consistently positive.
   - **Civic Plaza / Transit Hub ($N=1$, Dilworth):** DiD **$-1.27$ to $+7.50$** reviews/pair (250m immediate footprint: **$-1.27$**, 500m catchment: $+7.50$, 1000m: $+6.39$). Highlights footprint sign-flip and radius sensitivity.
   - **Riverfront Event Park ($N=1$, Riverfront / Ascend):** DiD $+12.55$ to $+44.48$ reviews/pair (1000m: $+12.55$, 500m: $+35.93$, 250m: $+44.48$). Concentrated near core.
   - **Fixed-Rail Transit ($N=1$, Sun Link):** DiD $-1.36$ to $-0.92$ reviews/pair (250m: $-1.36$, 500m: $-1.22$, 1000m: $-0.92$). Consistently negative relative to matched controls.

3. **Scenario Formulation:**
   For proposed budget $C$ (\$M) and target ZCTA with baseline active businesses $N_{\text{biz}}$:
   $$\widehat{\Delta \text{Reviews}} = \big[ N_{\text{biz}} \times \Delta \bar{Y}_{\text{low}}, \; N_{\text{biz}} \times \Delta \bar{Y}_{\text{high}} \big]$$
   $$\widehat{CE}_{\text{abs}} = \left[ \frac{N_{\text{biz}} \times \Delta \bar{Y}_{\text{low}}}{C}, \; \frac{N_{\text{biz}} \times \Delta \bar{Y}_{\text{high}}}{C} \right]$$

4. **Over-Capitalization Risk Warning:**
   Compares proposed capital expenditure against the commercial carrying capacity of the local catchment. Flags an alert if proposed cost per baseline business exceeds empirical thresholds, preventing over-capitalization in sparse corridors (the "Sun Link trap").

---

## 4. Threats to Validity and Risk Controls

| Risk / Threat | Observed in EDA | Control / Mitigation Strategy |
|---|---|---|
| **Under-supported Baselines** | Water Works Park had only 2 baseline matched pairs; raw % changes spike deceptively (+250%). | Hard minimum support threshold ($N_{\text{pairs}} \ge 20$). Display raw counts alongside rates; suppress ratio contrasts below threshold with explicit visual flags. |
| **Skew and Top-5% Outliers** | Dilworth Park growth is dominated by high-volume Center City restaurants; contrast drops from +23.7% to +5.8% without them. | Report log-transformed contrasts ($\Delta E_{\log}$) alongside raw arithmetic sums; compute Winsorized and trimmed bounds. |
| **Yelp Population vs. Business Openings** | An increase in active Yelp listings does not guarantee new business births (could be Yelp platform adoption). | Strictly define metric as *reviewed business participation on Yelp*, not *business formation*. |
| **Unreconciled Cost Scopes** | Headline costs conflate public grants with private match funding (e.g. Dilworth $55M mixed, Sun Link $196.5M FTA+local). | Document source ledgers in registry; run sensitivity against public-only funding shares. |
| **Confounding with Wider Metro Growth** | Nashville review volume grew citywide across 2012–2017. | All primary engagement and efficiency indices MUST be difference-in-differences against matched local control pools. |
| **Scenario Extrapolation Overreach** | Applying a single project's observed DiD spread to a hypothetical corridor assumes transferable commercial elasticity. | Strictly label tool as an illustrative *Scenario Explorer* based on $N=5$ cases; display source project $N=1$ badge and report ranges, never point forecasts. |

---

## 5. Implementation Roadmap and Verification Plan

### Phase 1: Capital Efficiency Engine (`src/engagement_efficiency.py`)
- **Objective:** Implement reproducible capital efficiency calculations across all 5 study cases.
- **Deliverables:**
  - `src/engagement_efficiency.py` script.
  - `study_data/capital_efficiency.csv`.
  - CLI reporting tool producing tabular benchmarks.
- **Verification:** Unit tests confirming mathematical identities, handle zero denominators, and match baseline EDA figures.

### Phase 2: Community Voice NLP Engine (`src/community_voice_nlp.py`)
- **Objective:** Separate community/amenity voice from commercial service commentary.
- **Deliverables:**
  - Multi-label aspect tagger for `community_voice` vs. `commercial_voice`.
  - Sentence extraction module gathering qualitative evidence for the web UI.
  - Accuracy and negative-recall validation suite.
- **Verification:** Precision and recall checked against human-labeled calibration set; test suite passing.

### Phase 3: Web Visualization & Map Refactor (`src/build_map_page.py`, `exploration.js`)
- **Objective:** Deliver interactive exploration of project efficiency, catchments, and community discourse.
- **Deliverables:**
  - Updated `web/index.html` featuring project locator, efficiency rankings, and voice excerpts.
  - Self-contained, offline-renderable build artifact ($\le 4$ MB).
- **Verification:** Headless browser / syntax check; verified offline rendering; zero broken assets.

### Phase 4: Final Synthesis & Coursework Artifacts
- **Objective:** Produce final notebook and presentation materials meeting CIS 509 final requirements.
- **Deliverables:**
  - End-to-end reproducible Jupyter Notebook incorporating the Public Investment Efficiency Score (PIES) and Scenario Estimator.
  - Final slide deck structure summarizing the Three Hypotheses, 4-stage transmission mechanism, PIES policy scorecard, and municipal capital allocation recommendations.
