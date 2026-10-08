# Place Lab — pipeline walkthrough

[Open the Google Slides walkthrough](https://docs.google.com/presentation/d/1sg0G4LGOqI1nrnQCK6E-p9zHme1tHvJlLT3XWMzv2ME/edit#slide=id.n04_data)

Updated October 8, 2026. This analysis follows the implementation and saved evidence;
it does not report a new extraction, model fit or test run.

The walkthrough occupies slides 5–13 of the main presentation. It explains one
stage at a time with examples, actual counts, formulas and evaluation results.
The activity and sentiment findings on slides 14–15 follow model evaluation so the audience can see what that stage produces.

## Two paths with different units

| Path | Unit and scope | What it produces |
|---|---|---|
| Area evidence | Review records joined to business ZIPs; 196 displayed ZCTAs across five metros | Activity, access mentions, historical ACS context, sentiment and timeline measures |
| Historical project evidence | Businesses assigned to project distance bands and project-specific windows; 11 projects in seven cities | Nearby/comparison outcomes, extracted text, and ten eligible model outcomes |

The 1,063,956 distinct scored reviews belong to the project-window corpus. They are
not the review denominator for every ZIP measure. Shared reviews can contribute to
multiple project memberships after being scored once. Review counts do not increase
the number of independent project outcomes.

## Slide-by-slide analysis

Slide 6 provides the pipeline graph. Each subsequent pipeline slide has a
right-hand “Technical choices” box defining the methods used at that step.

### Slide 5: 01 — Prepare sources at ZIP and project scales

Start with Yelp business and review records, historical Census ACS estimates, ZCTA boundaries, and audited project dates, geometry and reported costs. Join reviews to businesses by business_id. The ZIP analysis retains 2012–2021 reviews in study ZIPs, then aggregates by ZIP/quarter; the project analysis assigns businesses to distance cohorts and each project’s early/pre/post year windows.

Typical nearby distance is at most 500 m; comparison is over 1.5 to 8 km. Sun Link uses its fixed full-route cohort fixture. Score each distinct project review once and retain multiple memberships: 1,063,956 distinct reviews, 1,420,312 memberships, 292,924 shared across projects.

The map covers 196 ZCTAs in five metros; project evidence covers 11 projects in seven cities. These are different populations. Census income/poverty estimates are historical, not reviewer characteristics.

ZIP and ZCTA are not identical. Source: build_sentiment_panel.py, project_registry.py, build_project_evidence.py; notebook §§1–2.

### Slide 7: 02 — Split a review; assign topic, target and polarity

Walk through the illustrative review sentence. Split at punctuation and conjunctions such as but, however and although. Match the nine versioned topic vocabularies.

Assign business, area or unclear from explicit business/outdoor context; transit and public walking infrastructure can imply an area target. Score the whole review and each selected clause with VADER; clause polarity also checks complaint expressions and explicit negation. A topic mention is not necessarily a negative area complaint.

Aggregate review flags once even when multiple clauses match. The displayed sentence is illustrative, not an attributed source quote. Rules are deployed in project evidence; map access mentions come from separate overlapping whole-review keyword rules.

Source: project_text.py and build_review_topics.py; notebook §5.3.

### Slide 8: 03a — BERTopic on 413 extracted place excerpts

This is the notebook’s executed BERTopic analysis on 413 published rule-selected area excerpts, not the full review corpus. all-MiniLM-L6-v2 produces 384-dimensional vectors; UMAP uses five reduced dimensions and HDBSCAN minimum cluster size eight. c-TF-IDF identifies characteristic terms. Seven selected clusters are displayed; about one-third of excerpts remain unclustered and the chart is not exhaustive. Since the rules selected the excerpts, these counts cannot estimate issue prevalence among all reviews or residents. Source: review_nlp.py fit_bertopic; notebook §5.4.

### Slide 9: 03b — Stable sampling and baseline TF-IDF/NMF topics

A separate descriptive analysis samples nearby pre/post reviews: 23,691 unique selected reviews from 136,807 eligible, with at most 1,200 per project/period by stable SHA256 review-ID rank; shared selections are deduplicated. TF-IDF uses unigrams and bigrams, English stop words, sublinear term frequency, min_df 2, max_df .95 and up to 8,000 features. Five NMF topics are fitted only to 10,971 sampled nearby baseline reviews; post reviews are projected through the frozen vocabulary and basis.

Show actual top terms, which often describe food, service and products. We do not rename them as verified civic issues. Topic mixtures are model weights, not calibrated mention rates.

Prediction uses a separately fitted text basis inside each holdout, not this descriptive full-baseline artifact. Source: advanced_text.json and build_advanced_text.py; docs/advanced-text-method.md.

### Slide 10: 04 — Human label review and business-grouped classifier evaluation

Claude Opus annotated 731 items blind to rule output: 200 random reviews, 200 candidate clauses and 331 project/period/topic-enriched clauses. The team confirmed humans checked the labels and found them satisfactory. No additional independent reviewer counts or adjudication metrics are claimed.

The chart uses the 514-clause, five-fold business-grouped benchmark: rules find 12 of 73 negative area clauses; MiniLM embeddings with balanced logistic regression find 51 of 73. Precision is 41.8%, with 71 false positives, so better recall does not imply a ready complaint measure. Businesses never appear in both training and held-out data within a fold.

This classifier has not been applied to replace the full deployed corpus rules. Source: text_validation.py and metrics.json embedding_benchmark.

### Slide 11: 05 — Denominators, weighted sentiment and ZIP measures

Join the independently prepared sentiment and access aggregates to ZCTA display geometry and historical ACS context. Fixed windows are 2012–2014 and 2019–2021. Compute sentiment from score sums divided by review counts, not unweighted quarterly averages.

Activity density equals review count divided by three years and polygon km² including water. Access share is access/parking mention reviews divided by all late-period reviews, including praise and complaints. ZIP 19134 gives 56/1,702×100=3.29%.

Relative sentiment subtracts the change in the rest of the study metro, excluding the selected ZIP. Require 100 reviews in every required three-year period; unsupported measures remain null. The browser timeline can use other date selections: monthly review sums and quarterly access counts, with thresholds 100 for year-or-longer windows and 50 for shorter ones.

Historical ACS vintages are 2007–2011 or 2008–2012; not current conditions. Source: build_place_areas.py and place_pipeline.py.

### Slide 12: 06 — Expected vs observed activity around Sun Link

Construct project-specific historical outcomes with fixed near/comparison cohorts and predefined two-year windows. Sun Link near pre=3,807, near post=10,943, comparison pre=9,957, comparison post=34,394. Expected near post=3,807×34,394/9,957≈13,150.

Observed is about 17% below expected. The project-model target divides the observed-minus-expected difference by reported cost in $M. Eligibility requires at least 20 nearby baseline reviewed businesses and positive nearby/comparison baseline review counts and cost.

Ten of eleven projects qualify. For sentiment, subtract the comparison’s before/after change from the nearby change. Neither calculation isolates causal project effects; comparison trends, overlapping cohorts, construction and pandemic timing remain limitations.

Source: build_project_evidence.py primary_outcome; notebook §4.

### Slide 13: 07 — Project/city holdouts and timing sensitivity

The independent model unit is a project, not a review: ten eligible outcomes in seven cities. Three baseline inputs are log1p project cost, reviewed-business count and reviews/business. Ridge alpha is fixed at 10 and scaling is learned inside training folds.

Evaluate leave-one-project-out and leave-one-city-out against a mean predictor. The chart shows city-held-out MAE, lower is better. Advanced TF-IDF/NMF challengers refit inside each fold and remove held-out/shared review IDs; training-only imputation handles excluded text.

Text challengers do not improve both holdouts. Timing sensitivity without 2020 windows gives ridge MAE 60.3 versus mean 59.5, reversing its advantage. This remains an exploratory historical model, not a validated forecast or public-budget recommendation.

The site’s separate 500 m business-location sample is not a ZIP-wide impact estimate. Source: train_project_model.py, project_advanced_model.py and project_model.json.

### Export stage: validate six payloads and record provenance

This implementation reference is retained here; the separate export slide was
removed from the current Google Slides deck.

Separate upstream rebuilds from normal notebook execution. prepare_place_inputs.py refreshes eight frozen aggregate inputs explicitly and records hashes. The notebook loads those inputs, verifies hashes and evidence/model/text build compatibility, recomputes ZIP measures and baseline evaluation, and assembles six payloads. validate_payloads checks matching city/ZIP coverage, profile totals, access denominators, timeline reconciliation, null semantics and finite JSON values. Validate all payloads before export; replace each file atomically and write place-build-manifest.json with input/code/notebook-source/output hashes.

The six-file export is not one filesystem transaction. Browser UI reads the static files and uses shared calculations for maps, tables and assistant tools; viewing the page does not run Python or retrain models. Raw review text/IDs stay local; public evidence may contain selected short excerpts.

Fresh-clone notebook execution uses prepared aggregates and saved advanced-text evaluations, not a raw-archive rebuild. Source: place_pipeline.py and prepare_place_inputs.py; notebook §8.

## Source reading order

1. [Research notebook](../../output/jupyter-notebook/Project_Research_Walkthrough.ipynb), §§1–8.
2. [ZIP review extraction](../../src/build_sentiment_panel.py) and [whole-review keyword counts](../../src/build_review_topics.py).
3. [Project cohort registry](../../src/project_registry.py), [project evidence builder](../../src/build_project_evidence.py) and [clause rules](../../src/project_text.py).
4. [Executed excerpt methods](../../src/review_nlp.py), [label evaluation](../../src/text_validation.py) and [saved validation metrics](../../data/derived/text_validation/metrics.json).
5. [Sampled TF-IDF/NMF builder](../../src/build_advanced_text.py) and [saved topic artifact](../../data/derived/advanced_text.json).
6. [ZIP measure calculations](../../src/build_place_areas.py), [model evaluation](../../src/train_project_model.py) and [fold-specific text challenger](../../src/project_advanced_model.py).
7. [Input snapshot preparation](../../src/prepare_place_inputs.py), [notebook data contract](../../src/place_pipeline.py) and [export manifest](../../web/place-build-manifest.json).

## What the process establishes

The work produces traceable historical evidence that can guide further investigation.
Human reviewers checked the AI-generated labels and found them satisfactory, as
confirmed by the team. That review does not remove the measured false positives,
limited project sample, historical data vintages or observational comparison limits.
The deployed rules, descriptive topics and predictive challengers answer different
questions; none establishes a current need, causal benefit or reliable forecast alone.
