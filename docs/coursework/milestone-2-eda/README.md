# CIS 509 · Team 4 EDA submission

John Wheeler (`jwheele4`), Ryan Wolff (`rwwolff`), Cameron Anthony (`cantho19`). Prepared September 12, 2026 for Milestone 2, due September 13 at 11:59 PM MST.

## Required assignment files

- `ProjectEDA_Team4.ipynb`: executed notebook with analysis, explanations, all figure code and embedded aggregate inputs.
- `ProjectEDA_Team4.html`: reading version with eight embedded figures, source links and expandable supporting tables.

The report covers Lafitte Greenway, Sun Link, Dilworth Park, Water Works Park and Riverfront Park / Ascend. It compares engagement, stars, VADER, embedding categories and baseline local income, with project type and reported cost as descriptive context. The Sun Link extension includes all 717 Yelp listings within 500 m of the full route, including listings without baseline reviews.

Engagement grows faster near some projects, but sentiment and ratings do not improve consistently. Five heterogeneous cases cannot establish causation, a spending threshold, or an income-specific spending effect. Water Works remains visible as an insufficient-support case (two primary matched pairs).

## Reproduce the submitted results

Use Python 3.11 or 3.12 with `pandas`, `numpy`, `matplotlib`, `nbformat`, `nbclient`, `nbconvert` and `ipykernel`. With uv installed:

```sh
uv run --with pandas --with numpy --with matplotlib --with nbformat --with nbclient --with nbconvert --with ipykernel python render_submission.py
```

Alternatively, install those dependencies in a Jupyter environment, open the notebook from this directory and run all cells. Keep its submitted filename. If `study_data/` is missing, the notebook restores 36 compact inputs from its own metadata. It verifies their SHA-256 hashes, recomputes growth/sentiment contrasts and VADER diagnostics, and redraws all figures. No external data download is required for this stage.

`eda_visuals.py` mirrors the notebook's embedded figure code. When editing figures, update both copies. `figures/` contains PNG and SVG versions for reuse. The HTML does not need these external images.

## Preparation scope and provenance

These deliverables reproduce the displayed analysis from prepared aggregates. Raw Yelp extraction, geospatial selection, Census linkage, sentiment scoring, business matching and embedding training are upstream stages. They are not re-executed by the submission notebook. No raw review text or reviewer IDs are included in this package.

The original scripts and audits are retained in the assignment's local Work directory under `Five Project Study`, `Sun Link Full Corridor`, `Pilot Lafitte`, `Pilot Sun Link`, `Engagement Pilot` and `Embedding Categories`. The aggregate manifest in `study_data/provenance.json` records preparation source paths and input hashes; those local paths document provenance rather than portable dependencies. The five-project preparation applies the reconstructed, frozen two-city baseline embedding model to added cities. The full Sun Link topic extension processes every qualifying pre/post corridor review. Source links, geography limitations, matching choices, sample counts and distinctions between pooled and matched comparisons are documented in the notebook.

The prior broad federal-assistance analysis and Cameron's specification, timing and site-selection work remain in repository history and `analysis/`. The revised submission adopts the focus on exposure quality, robustness and a majority-class sentiment baseline, while narrowing the assignment narrative to the five documented projects. Earlier exploration-heavy notebook versions are retained in the Work folder's `_prior_draft/`.

## Validation and handoff

`EDA_Evaluation.md` maps the final notebook to the assignment rubric and records checks. All 10 code cells execute without errors; a clean-directory check using only the notebook restored all inputs and regenerated eight figures. The HTML was checked in a browser, including narrative visibility and figure layout. Human understanding/review remains the team's responsibility, as stated in the AI disclosure. The files have not been submitted to Canvas.

## Writing review

The report follows [Cursor's Unslop guidance](https://github.com/cursor/plugins/blob/main/pstack/skills/unslop/SKILL.md), accessed September 12, 2026. The editing pass splits dense sentences, removes repetitive labels and replaces generic conclusions with project findings. Statistical qualifications, numeric notation and the assignment sections remain. The calculations, aggregate inputs and source links are unchanged.
