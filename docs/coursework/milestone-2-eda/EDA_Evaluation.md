# Project EDA evaluation

**Artifact reviewed:** `ProjectEDA_Team4.ipynb` and its HTML export  
**Review date:** September 5, 2026  
**Evaluator:** OpenAI Codex, applying the assignment's published rubric  
**Estimated score:** **9.7 / 10 (97%)**  
**Readiness:** Technically ready; complete the team/content-owner review before submission.

This is a rubric-based estimate, not an instructor grade. The notebook was also checked mechanically: all 11 code cells have execution counts and saved outputs, and there are no recorded error outputs.

## Rubric score

| Rubric area | Weight | Estimated credit | Evaluation |
|---|---:|---:|---|
| Project overview | 10% | 10% | Clear business audience, decision problem, analytical question, and appropriately limited claim. The distinction between business-review sentiment and community well-being is especially strong. |
| Data sources | 10% | 10% | Identifies Yelp, USASpending, and Census sources; explains collection, filtering, time window, geography, and important exclusions; includes source links. |
| Data description and summary statistics | 25% | 24% | Strong unit-of-analysis discipline, field/type table, record and feature counts, missingness checks, distribution summaries, text statistics, regional coverage, and reproducible figures. A small deduction reflects density: reviewers may need more signposting to distinguish the headline statistics from supporting diagnostics. |
| Data quality and suitability | 20% | 20% | Excellent. Treats ZIP/ZCTA mismatch, self-selection, historical boundaries, sparse cells, award geography, nominal dollars, dependence, and VADER validity as analytical limitations rather than footnotes. |
| Preliminary exploration | 25% | 24% | Multiple relevant analyses connect directly to feasibility: rating/sentiment disagreement, time and volume patterns, funding concentration, candidate program language, and matched ZIP-quarter coverage. The association is correctly labeled descriptive. A small deduction reflects that the matched analysis is intentionally preliminary and does not yet include sensitivity views by region, program type, or time lag. |
| Proposed AI solution | 10% | 10% | Specific next-stage methods, evaluation measures, leakage controls, geographic validation, and interface implications. The plan follows directly from the EDA findings. |

## What is strongest

1. **The analysis tells one story.** It moves from the business question to data feasibility, measurement risk, preliminary relationships, and a defensible next-stage plan.
2. **Claims are calibrated.** The notebook never turns a descriptive correlation into a causal result and explicitly explains why a weak/null relationship could still be informative.
3. **The data audit is unusually credible.** Row reconciliation, duplicate checks, signed obligations, cache signatures, missingness, sampling rules, and units of analysis make the work inspectable.
4. **The proposed AI work is testable.** It names baselines and evaluation measures rather than merely proposing "use AI."
5. **AI use is disclosed clearly.** The disclosure says what Codex did and reserves interpretation and verification responsibility for the team.

## Remaining checks before submission

- [ ] Ryan Wolff and Cameron Anthony review the central findings and confirm they can explain the analysis and code.
- [ ] Confirm the data-source selection and any earlier team AI use so the disclosure is complete.
- [ ] Confirm that `ProjectEDA_Team4.ipynb` and `ProjectEDA_Team4.html` are the only two files uploaded.
- [ ] Open the final HTML independently and visually inspect all seven figures and tables.
- [ ] Verify that the team wants the current cautious framing; do not strengthen the causal language.
- [ ] Consider adding each teammate's ASURITE only if the instructor expects identifiers for every member. The published instructions require team ID and names, which are already present.

## Optional refinements

These are polish, not blockers:

- Add a one-sentence "headline result" immediately before the preliminary-exploration subsections so a fast reviewer sees the main feasibility conclusion early.
- Add one compact regional sensitivity table (matched share and descriptive correlation by region) only if it can be explained without crowding the notebook. Do not add it merely to increase analysis volume.
- Tighten a few long methodology paragraphs if the team wants a shorter read; preserve the caveats and provenance details.

## Bottom line

The notebook fully addresses the published requirements and is stronger than a typical milestone EDA. Its only material prerequisite is human team review. The work should be submitted as a feasibility analysis, not as evidence that federal assistance caused changes in local business sentiment.
