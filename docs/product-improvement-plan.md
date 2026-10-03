# Project evidence and prospective capital-efficiency tool

Planning baseline: September 25, 2026. The sections below preserve the approved plan.

## Implementation status — September 25, 2026

Implemented the canonical 11-project registry and harmonized primary outcome;
coordinate-based cohorts; targeted source/date corrections; a sourced Rail Park
Phase One footprint; full-window provisional aspect/sentiment extraction; shared-review
and business-concentration diagnostics; a deterministic annotation task set; learned
TF-IDF/bigram + NMF topic evidence; project/city-held-out model challengers; and the
new project explorer and proposal workflow. Earlier calculations remain explicitly
archived. See [advanced text methods](advanced-text-method.md),
[source audit](project-source-audit.md), and [demo walkthrough](demo-walkthrough.md).

The core extraction covers 1,063,956 unique reviews. The learned-topic layer uses
23,691 sampled nearby pre/post reviews, with 10,971 baseline reviews fitting its
descriptive representation. Ten projects meet model support; one remains withheld.
Model sample size is ten projects, not one million independent outcomes.

Still unresolved: five center proxies and historical-fidelity limits on mapped
geometry; independently human-scored aspect accuracy; inflation/common-price-year
cost sensitivity and fully reconciled public/private cost scope; current post-2022
coverage; and independent out-of-sample model confirmation. Blank annotation tasks
are prepared, not presented as completed validation. Browser QA and known testing
limits are recorded in `docs/qa/validation.md`.


## Product objective

Give a public official two connected workflows:

1. **Analyze a completed project:** understand its footprint, cost, before/after activity, comparison area, review language, and strength of evidence.
2. **Analyze a proposed project:** describe its type, cost and local baseline conditions; receive an experimental estimate of adjusted Yelp engagement per $1 million, with relevant historical projects, observed prediction errors, and a clear account of which inputs affect the estimate.

The first version measures Yelp engagement, not financial ROI or the full civic value of an investment. Keep the predictive model as a substantive product capability, with its scope and validation visible beside the result.

Use existing data first. Add targeted official public sources to resolve project geometry, opening/construction dates, cost scope and dollar years. Preserve existing work and historical coursework submissions.

## 1. Establish one project and outcome contract

- Consolidate all 11 projects into one versioned registry; eliminate the current split between nine registry records and two hardcoded model cases.
- Store stable project IDs, type/family, footprint source and quality, construction/opening milestones, baseline and outcome windows, cost source, public/private scope, price year, and eligibility reasons.
- Use one primary two-year outcome across historical pages, training and prospective outputs: `(near post reviews - near pre reviews * farther post/pre review growth) / cost in $M`.
- Retain matched-pair and other legacy results as named sensitivity analyses. Explain cohort and method changes explicitly, including cases where the sign changes; never silently replace a historical submission.
- Separate eligibility for descriptive display, model fitting, and a new-site estimate. A project can remain visible while being excluded from training.
- Record dataset versions, source hashes, extraction settings and counts in a compact manifest.

Acceptance: the same project/method/window/cost basis produces the same number everywhere; the app can trace every result to a registry record and output row. Unsupported outcomes are visibly withheld.

## 2. Improve geographic and temporal coverage

- Audit and, where sources permit, replace the six expansion center proxies with complete phase-specific alignments or polygons. Retain provisional labels for unresolved cases.
- Select businesses by coordinates and distance to the footprint, using a spatial bounding box/index rather than municipal city-name strings as a hard boundary.
- Audit overlapping projects and near/comparison cohorts. Record overlap so shared businesses and city conditions are not mistaken for independent evidence.
- Preserve Sun Link's documented full-route cohort as a reconciliation fixture; any changed cohort must have a recorded reason and old/new comparison.
- Verify phase-specific opening dates and costs, especially large phased developments. Check baseline windows against construction, not only opening.
- Flag pandemic-exposed outcomes such as Rail Park's 2019–2020 window and add a disclosed sensitivity analysis without choosing windows based on favorable results.
- Record reported nominal costs and price years. Add a documented common-price-year sensitivity where sources support it, and ensure a proposal's budget uses the same basis as the model. Do not invent missing public-only cost shares or cost years.

Acceptance: each project has a coverage audit showing near/far businesses, reviewed businesses, reviews by year, missing coordinates/text, geometry quality, timing and cost limitations. Source changes regenerate downstream results consistently.

## 3. Extract project-level evidence from Yelp text

The local archive contains the review text needed for all existing project cities and older baseline years. The current ZIP text panel covers only 2012–2021 and five metros; it cannot supply all model baselines. The small weak-label notebook sample is not a substitute for project-level extraction.

- Stream the archive once against the versioned cohort membership index; keep reusable, local-only review/sentence evidence and compact aggregate outputs.
- Cover early baseline, baseline and post windows for all 11 projects, near and comparison areas. Deduplicate review processing when a review belongs to multiple project cohorts.
- Extract whole-review sentiment, multi-label topics, text target (business interior/service versus street/neighborhood/public amenity), and topic-specific negative/positive/mixed or uncertain sentiment.
- Begin with interpretable themes: access/transit/parking/walking, safety, outdoor cleanliness/maintenance/public space, price/value, food/products, and service. Keep ambiguous classifications explicit.
- Produce review-weighted and business-balanced summaries, support counts, missingness, and evidence excerpts. Use business-balanced and near/far contrasts to check whether one high-volume business dominates.
- Candidate model features: baseline sentiment; place-discussion share; access-friction share; public-realm complaint share; pre-intervention trends. Keep post-period text in historical evaluation outputs, outside prospective inputs.
- Provide a stratified annotation set spanning projects, periods, rare topics, negation and business-versus-neighborhood ambiguity. Include random noncandidate reviews as well as keyword candidates so missed mentions can be measured. Separate examples used to refine rules from held-out examples used to assess them, with businesses separated between these sets.
- Report precision/recall and support by label when independently reviewed labels exist. Synthetic examples and agent-generated labels are development checks, not a human validation claim. If human review is pending, label the features provisional and continue the rest of the work.

Acceptance: every retained review joins by ID to the right project/cohort/date; all baseline windows are covered; aggregate review counts reconcile with the outcome pipeline; missing text is not interpreted as neutral sentiment or no complaints. Raw text remains local and excluded from public artifacts except appropriate short evidence excerpts.

## 4. Build and evaluate a text-enriched model

- Preserve the current three-input ridge model and mean-only comparator as reproducible baselines.
- Predefine a small set of challengers: existing baseline, baseline plus pre-period trend, and baseline plus a small set of text features. Do not feed every extracted field into ten project rows.
- Consider coarse project-family information for reference selection and as a regularized challenger only where support permits. Show counts by family. A single transit case cannot establish a reliable transit-specific coefficient.
- Use project-held-out evaluation with all learned preprocessing inside folds. Add leave-city-out and overlap-aware stress checks for shared geography.
- If tuning is needed, keep tuning inside training folds; retain all challenger results rather than reporting only the winner.
- Report per-project predictions/errors, mean and median absolute error, direction accuracy, and comparison with the existing baseline. Show geometry, timing and cost sensitivity alongside model performance.
- Display observed held-out error and sensitivity ranges honestly. Do not relabel mean absolute error as a confidence interval; introduce a predictive interval only with an explicit method and coverage assessment.
- Check similarity to observed combinations of inputs as well as individual feature ranges; three individually supported values can still describe an unfamiliar proposal.
- Promote additional features only when the evaluation justifies their use. Keep a simpler model available if text enrichment does not improve transfer.

Acceptance: no post-intervention input leakage; held-out projects do not train their own preprocessing; Python training and browser inference agree; the final model artifact contains feature definitions, supported input domains, data version and all validation results.

## 5. Rebuild the site around two clear workflows

Preserve the civic/editorial typography, restrained palette, and cartographic identity. Improve hierarchy and legibility rather than adding decorative complexity.

### Historical projects

- A project index covers all 11 records, with explicit verified/provisional coverage rather than a five-project map implying complete coverage.
- Each project gets a consistent detail view: overview and sources; mapped footprint/catchment; primary CE and its calculation; raw near/far before/after counts; review-language changes; sensitivity; evidence quality.
- Use one primary metric, explicit units and windows. Put alternative definitions behind a labeled comparison rather than making users reconcile simultaneous headline scores.
- Keep the broader ZIP funding/timing map as supporting exploration, separate from project outcome evidence.
- Give each project a stable link and a clear path to use its conditions as a proposal example.

### Proposed projects

- A short staged form: project type and budget; location/footprint and baseline data; review inputs; results.
- Support clearly labeled historical example profiles and a documented local-data import/manual-input path for a real proposal. Show source, observation period, catchment and completeness for each profile. A ZIP selection alone must not claim to supply a measured project catchment.
- Keep historical 2022-archive demonstrations distinct from current local evidence. Do not silently assign old city averages to a current proposal.
- A result shows estimated adjusted Yelp reviews per $1M, corresponding adjusted review count, time horizon, evidence support, model error and comparable projects. Explain how type affects reference selection or prediction and disclose unsupported type effects.
- Put editable hypothetical growth assumptions in an advanced scenario view, clearly separate from the fitted estimate.
- Every visible control either changes the calculation, changes an explicitly labeled reference/context, or is disabled with a reason. Provide precise field validation and supported ranges.
- Reset restores all inputs and outputs; changing an example never leaves an accidental hybrid of its baseline data and another project's cost/count.
- Preserve a proposal through shareable local state or export, with input provenance and model version. No server upload of local review data is required for the initial import workflow.

Acceptance: a user can identify the primary estimate, units, time period, evidence source and limits without reading a methodology appendix; a historical example can be reproduced exactly; incomplete real-proposal inputs yield a useful explanation rather than a fabricated estimate.

## 6. Visual and usability validation

Run these checks on the implemented app, fix defects, and repeat affected checks. Existing math and generated-markup tests do not replace browser interaction tests.

- Desktop at 1440×900 and 1280×720, tablet at 768×1024, mobile at 390×844 and 360×800, plus a 320 px width stress check and 200% zoom.
- Inspect screenshots of project index/details, proposal inputs/results, missing-data and error states, expanded methods, and export views.
- Check long forms and sticky panels, horizontal overflow, readable body/help text, table handling, labels, focus visibility, color contrast, and non-color evidence/status cues.
- Keyboard-only path through selecting a project, completing a proposal, correcting an invalid field, resetting, and exporting; dialogs must return focus correctly.
- Touch scrolling must remain possible around the map. Interaction help must match actual zoom/pan behavior.
- Browser tasks: all projects load; controls have their advertised effects; timeline versus fixed project outcome is clear; filters synchronize; reset fully restores state; invalid/sparse/out-of-domain cases behave correctly; back/deep links preserve expected context; reports and exports match displayed values.
- Check runtime errors and self-contained/offline behavior for the delivered demo. Test actual export/download behavior, not just the presence of buttons.
- Record screenshots and completed scenarios in a QA report. Agent/browser checks demonstrate interaction correctness; do not call them human user research. Provide a short task script for the team to rehearse.

## Delivery sequence and ownership

1. **Data agent:** registry/coverage audit, targeted source repairs, cohort construction and text extraction.
2. **Model agent:** feature/outcome contract, baseline reproduction, challengers, evaluation and browser inference contract.
3. **Site agent:** historical/proposal workflows and responsive components using agreed data contracts; do not fabricate data while extraction runs.
4. **Primary agent:** integrate changes, resolve shared-file dependencies, run visual/browser checks, verify claims and prepare the demo handoff.

Agree on the registry and feature schema before parallel implementation. Give each agent separate file ownership and integrate at each milestone. Preserve the current uncommitted work.

First milestone: one audited registry, one harmonized project table, and full baseline text-coverage statistics. Second: evaluated text-enriched model and proposal input contract. Third: integrated project/proposal site. Final: verified demo build, reproducible commands/dependencies, QA evidence, and a short demonstration script.

Do not add more projects merely to increase row count. Evaluate expansion after repairing the existing 11 cases. More review rows improve text measurement; they do not create more independent project outcomes.
