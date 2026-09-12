# Final EDA rubric and validation review

Prepared September 12, 2026. Assignment: [CIS 509 Milestone 2](https://canvas.asu.edu/courses/264495/assignments/7537751). This is a completion check, not an instructor grade or teammate approval.

| Requirement | Evidence in final notebook |
|---|---|
| Team information | Title block includes Team 4, all three names and ASURITE IDs. |
| Project overview (10%) | Section 1 connects local public investment to business engagement and review experience, with three exploratory expectations. |
| Data sources (10%) | Section 2 links Yelp, Census, GIS and project accounts; explains selection, time windows, geometry and non-comparable cost scope. |
| Description/statistics (25%) | Section 3 reports counts, variable types, text lengths, vocabulary size and distributions. Figures 1–3 show study windows, sample attrition and text diagnostics. Section 4 tables report missingness and matched-control support. |
| Quality/suitability (20%) | Section 4 covers sparse samples, missing context, geometry/ZIP limitations, user selection, composition, shared controls, confounding and missing cost/population denominators. |
| Preliminary exploration (25%) | Section 5 compares five projects, engagement versus experience, local income groups, radius/weighting sensitivities, embedding categories and all-business Sun Link coverage. Figures 4–8 communicate these findings. |
| Proposed AI solution (10%) | Section 6 specifies sentiment/topic validation, baseline models, exposure verification, improved study design and an auditable comparison tool. |
| Generative AI use | Final Section 8 discloses Codex and Claude assistance and the team's responsibility to verify/explain the work. |
| Deliverable formats | Executed `ProjectEDA_Team4.ipynb` and matching self-contained `ProjectEDA_Team4.html`. |

## Technical checks completed

- All 10 notebook code cells execute without error and generate eight plotted outputs.
- Required aggregate files have matching SHA-256 hashes. Notebook metadata embeds 36 prepared inputs.
- A clean directory containing only the submitted notebook restored those inputs and regenerated eight PNG/SVG figures.
- Assertions verify all five projects, 2,004,265 extracted reviews, 704,025 selected pre/post records, 97,896 nearby text records and 28,233 reviews in the five-case topic sample.
- Growth and experience contrasts are recomputed from prepared summaries and checked against saved values. VADER diagnostics are calculated from the star-by-label counts.
- Figure helper code embedded in the notebook matches the accompanying Python module.
- All eight figures were visually inspected; title spacing and topic labels were adjusted for readability. HTML narrative visibility and embedded figure rendering were checked in a browser. Images have descriptive alternative text.

## Interpretation retained in the submission

- Positive review activity is not proof of visits, resident involvement, revenue, welfare or business creation.
- Water Works has only two primary matched pairs; primary estimates are suppressed rather than presented as supported results.
- Income groups are within-city ZIP terciles, not individual or nationally comparable income groups.
- Sentiment and activity use different eligible business cohorts. The inclusive Sun Link extension is pooled/unmatched and includes business-composition changes.
- Topic labels are provisional; whole-review stars are not aspect ratings. Sampling, coverage and small category cells are disclosed.
- Five cases and unreconciled cost/population denominators cannot identify a causal project-type effect, cost threshold, or spending per resident by income group.
- No significance claims, independent-pair confidence intervals, causal placebo claims or unverified photo/visit measures are presented.

## Repository integration

The work is on `eda/five-project-submission`. Cameron's incoming `origin/main` history through `2d3fdf0` was merged with the pre-existing local history through `df9aece`, without rebasing or amending either. The submission revision is a separate commit after that merge. Cameron's `analysis/` files are retained unchanged. Nothing has been pushed or submitted.
