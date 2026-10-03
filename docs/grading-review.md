# Rubric-based project review

Reviewed 2026-10-02. **Prior estimated score: 84.5/100.** This is a repository-based
assessment, not an instructor grade. No course letter-grade scale was supplied.
Live presentation delivery and engagement cannot be graded from stored files.
The presentation was subsequently revised against the rubric; the estimate below
has not been recalculated or increased on that basis.

The source is the course's **Final Project Deliverables – Grading Rubric**
(`139228374-Final Project Deliverables - Grading Rubric.pdf`, supplied in the local
course materials). It requires slides plus Python notebook(s) or a GitHub code
link, recommends approximately 12–15 minutes, and assigns the six weights below.
The rubric defines 9–10 as Excellent, 7–8 as Good, 5–6 as Satisfactory, and 0–4 as
Needs Improvement. Half-points below are reviewer estimates between those bands.

## Score and evidence

| Category | Weight | Score /10 | Weighted points | Assessment |
|---|---:|---:|---:|---|
| Business problem definition | 15% | 9 | 13.5 | Clear public-planning audience and Yelp-based question; distinguishes historical investigation from causal investment recommendations. The project is original and motivated. |
| Exploratory data analysis | 10% | 8.5 | 8.5 | Coverage, missingness, denominators, ZIP distributions and project comparisons are visible. Earlier coursework adds text diagnostics. The primary path could show more cleaning examples, review-length/star distributions and coverage bias directly. |
| Methodology | 25% | 8 | 20 | VADER, target-aware clause rules, TF-IDF/NMF and fold-isolated challenger evaluation are appropriate and explained. Shared reviews are excluded from representation training. Independent annotation and topic-quality evaluation remain incomplete; five-topic selection has limited comparative justification. |
| Results and business insights | 25% | 8.5 | 21.25 | Raw versus adjusted growth, food/service dominance, negative predictive NLP results and timing sensitivity are interpreted honestly. More explicit examples of how a planner changes an investigation or evidence request would strengthen the business connection. |
| Presentation and communication | 10% | 8 | 8 | Prior deck assessment. The current 15-slide deck adds data preparation, actual NMF terms and planning implications, with current ZIP/notebook coverage. Delivery is unobserved. |
| Code clarity and quality | 15% | 8.5 | 12.75 | Executed primary notebook, modular transformations, hashes, static JSON contract and meaningful tests. Legacy/current entry points and compressed older modules add reading cost. Prepared-data reproduction is stronger than full raw-source replication. |
| **Total** | **100%** | | **84.5** | Strong submission, with the largest remaining opportunity in validating and interpreting the NLP contribution. |

Calculation: sum of `(category score / 10) × category weight`. A reasonable
reviewer range is roughly 81–88, depending on how heavily unfinished text
validation and live delivery affect the methodology and presentation scores.
A failed predictive challenger is not itself a grading failure: appropriate
methods, valid evaluation and thoughtful interpretation matter more than a
positive result. A small project sample is a limitation, not evidence of bad code.

## What was reviewed

- [Primary executed notebook](../output/jupyter-notebook/Project_Research_Walkthrough.ipynb):
  24 cells, 11 executed code cells; source lineage, coverage, ZIP derivation,
  outcome reconstruction, saved NLP results, actual baseline refitting, sensitivity,
  conclusions and static JSON export.
- [NLP method](advanced-text-method.md), `src/project_text.py`,
  `src/community_voice_nlp.py`, `src/build_advanced_text.py` and
  `src/project_advanced_model.py`: reviewed method documentation and implementation,
  including train-only representation fitting and held-out review exclusion.
- [Project source audit](project-source-audit.md), prepared input manifests,
  `src/place_pipeline.py`, and the current model/evidence artifacts.
- The prior PowerPoint/PDF reviewed for this assessment has been retired. Its
  replacement is the [15-slide Google Slides course presentation](https://docs.google.com/presentation/d/1sg0G4LGOqI1nrnQCK6E-p9zHme1tHvJlLT3XWMzv2ME/edit), rebuilt on
  October 2, 2026 with the ZIP workflow, data pipeline and current findings.
  The replacement was rendered and visually checked; delivery remains ungraded.
- [Presenter guide](presentation/Presenter-Guide.md), README, data acquisition
  documentation, CI configuration and repository publication checks.
- Clean-copy execution: copied only tracked/non-ignored candidate files into a
  temporary directory, then executed all 11 notebook code cells using the existing
  Python environment. All five exported JSON hashes matched. This verifies file
  independence from the local raw corpus, not a fresh dependency installation.
- Current test suite: **63 Python and 51 JavaScript tests passed** during this review.
  Source-data exclusion and focused publication checks passed. Tests support
  implementation correctness; they do not establish scientific validity.

## Deliverable compliance

| Requirement | Status |
|---|---|
| Presentation slides | Native Google Slides in CIS 509 Group; visual review completed |
| Python notebook(s) or GitHub repository | Present; the new executed walkthrough is the primary entry point |
| Clean, documented implementation | Substantially met; reusable functions and tests support the notebook |
| Clear connection between problem, NLP and business interpretation | Present, with room for more concrete decision examples |
| Approximately 12–15 minutes | Presenter guide updated to a 13-minute plan; timed rehearsal still needed |
| Accessible submission | GitHub repository is public; verify instructor access to the separate Google Slides deck |

Raw datasets do not need to be checked in under the supplied rubric. Compact
research results and documented acquisition are appropriate. The exact archive
version matters; do not present a fresh prepared-data run as a full raw rebuild.
See [data setup](data-setup.md).

## Highest-value improvements remaining

1. **Validate the NLP labels independently.** Have human reviewers annotate a
   documented held-out sample with written topic/target/polarity definitions.
   Report sample construction, agreement, per-class precision/recall and error
   examples. The existing 731 blank-label tasks and semantic unit tests are not
   completed independent validation. Do not fill this gap with model-generated
   labels presented as human labels.
2. **Make the business implications concrete.** Add two or three short cases that
   connect an observed text measure to a planning question, a next evidence request,
   and a decision the measure cannot support. For example, access mentions can
   justify a targeted accessibility review, not a budget recommendation.
3. **Strengthen the text EDA and model justification.** Show representative errors,
   text length and star distributions in the primary notebook; compare a small,
   predeclared set of topic counts or justify five topics based on interpretability
   and stability. Keep descriptive quality separate from predictive performance.
4. **Complete raw-source bootstrapping.** Automate historical ACS preparation and
   restoration of study configuration. Keep public downloads outside Git. The
   prepared-data notebook already works without the raw corpus; this is the
   separate upstream reproducibility gap.
5. **Rehearse and refresh the demo evidence.** Use the updated 13-minute guide,
   use the current ZIP demonstration and notebook-to-JSON explanation. Do not infer an excellent delivery score from slide design.

These changes could improve the score, but no point increase is guaranteed.
They remain outstanding; this review does not claim to have performed human
annotation, raw-corpus retraining, an independent test-set evaluation, or rehearsal.

## Cross-platform check

The first GitHub Linux run exposed exact-equality assertions on regenerated
floating-point values. They differed only at numerical roundoff scale from macOS.
The comparisons now use relative tolerance 1e-9 and absolute tolerance 1e-10 for
floats while keeping structural fields, integer counts and provenance hashes exact.
Research values and model selection were not changed.

## Repository updates made during this review

Added this grading assessment and a submission reading guide, linked them from
README, and aligned the presenter guide with the rubric's recommended timing and
current ZIP/notebook workflow. Existing earlier research is retained and explicitly
identified as history. The latest notebook, map, data-policy and publication
preparation work is included in the repository update; large source datasets stay
excluded. No scientific results were altered to improve the apparent grade.
