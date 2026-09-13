# Final EDA rubric and validation review

Prepared September 12, 2026. Assignment: [CIS 509 Milestone 2](https://canvas.asu.edu/courses/264495/assignments/7537751). This is a completion check, not an instructor grade or teammate approval.

| Requirement | Evidence in final notebook |
|---|---|
| Team information | Section 1 lists Public Investment Map Team, Team 4, all three names and ASURITE IDs. |
| Project overview (10%) | Section 2 names the customer and decision (district and economic-development organisations choosing public-space investments), then connects local public investment to business engagement and review experience, with three exploratory expectations. |
| Data sources (10%) | Section 3 links Yelp, Census, GIS and project accounts; explains selection, time windows, geometry and non-comparable cost scope. |
| Description/statistics (25%) | Section 4 reports record counts at four units of observation, variable types, a missingness summary, text lengths, the 6,966-word vocabulary and distributions. Figures 1–4 show project geography, study windows, sample attrition and text diagnostics. Section 5 tables report missingness in full and matched-control support. |
| Quality/suitability (20%) | Section 5 covers sparse samples, missing context, geometry/ZIP limitations, user selection, composition, shared controls, confounding and missing cost/population denominators. |
| Preliminary exploration (25%) | Section 6 compares five projects, engagement versus experience, local income groups, radius/weighting sensitivities, embedding categories and all-business Sun Link coverage. Figures 5–10 communicate these findings and changes in reviewed-business counts. |
| Proposed AI solution (10%) | Section 7 specifies sentiment/topic validation, baseline models, exposure verification, improved study design, an auditable comparison tool, and the open-source Python stack (scikit-learn, NLTK, spaCy, Hugging Face). |
| Generative AI use | Section 8 discloses Codex and Claude assistance and the team's responsibility to verify/explain the work. Reproduction details follow in Appendix A. |
| Deliverable formats | Executed `ProjectEDA_Team4.ipynb` and matching self-contained `ProjectEDA_Team4.html`. |

## Technical checks completed

- All 12 notebook code cells execute without error and generate ten plotted outputs.
- Required aggregate files have matching SHA-256 hashes. Notebook metadata embeds 39 prepared inputs.
- A clean directory containing only the submitted notebook restored those inputs and regenerated ten PNG/SVG figures.
- Assertions verify all five projects, 2,004,265 extracted reviews, 704,025 selected pre/post records, 97,896 nearby text records and 28,233 reviews in the five-case topic sample.
- Growth and experience contrasts are recomputed from prepared summaries and checked against saved values. VADER diagnostics are calculated from the star-by-label counts.
- Figure helper code embedded in the notebook matches the accompanying Python module.
- All ten figures were visually inspected; title spacing and topic labels were adjusted for readability. HTML narrative visibility and embedded figure rendering were checked in a browser. Images have descriptive alternative text.

## Interpretation retained in the submission

- Positive review activity is not proof of visits, resident involvement, revenue, welfare or business creation.
- Water Works has only two primary matched pairs; primary estimates are suppressed rather than presented as supported results.
- Income groups are within-city ZIP terciles, not individual or nationally comparable income groups.
- Sentiment and activity use different eligible business cohorts. The inclusive Sun Link extension is pooled/unmatched and includes business-composition changes.
- Topic labels are provisional; whole-review stars are not aspect ratings. Sampling, coverage and small category cells are disclosed.
- Five cases and unreconciled cost/population denominators cannot identify a causal project-type effect, cost threshold, or spending per resident by income group.
- No significance claims, independent-pair confidence intervals, causal placebo claims or unverified photo/visit measures are presented.

## Repository integration

The five-project submission was pushed as a single commit, `63a4c0f` on `eda/milestone-2-review`, built directly on `2d3fdf0` from `origin/main`. Cameron's `analysis/` files are retained unchanged. Earlier local pilot history is not in the pushed branch; it remains in the assignment's local Work folder.

`e0b8f8c` on `eda/rubric-alignment` then renumbered the notebook so its eight sections map one-to-one onto the rubric, added the customer framing to Section 2, the record/missingness/text-statistics summary to Section 4 and the named toolkit stack to Section 7, and moved reproduction notes to Appendix A. Those edits are markdown only: on re-execution, every computed output value and all ten figures are byte-identical to `63a4c0f`. The team confirmed `eda/rubric-alignment` as the version going forward.

## Map and business-activity extension

The report adds a national locator map with five local footprint/buffer panels, plus an unmatched comparison of reviewed-business counts near each project. The new count decompositions and relative growth calculations are checked in the notebook. The original matched analyses remain unchanged. More reviewed businesses is explicitly distinguished from verified business openings.
