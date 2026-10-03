# Public Investment Evidence

**CIS 509 — Analytics for Unstructured Data · Team 4**

John Wheeler, Ryan Wolff, Cameron Anthony

**Publication status:** locally prepared; the owner has confirmed permission for
public release of the included Yelp excerpts and business-level records. Read the
[public-release audit](docs/publication-audit.md) and
[data and third-party notices](DATA_AND_LICENSES.md) for scope and checks before changing repository
visibility or deploying. This repository is an academic research submission;
public access does not grant permission to redistribute its source data.

We combine historical Yelp reviews, public-project records, and Census context to
help a planner inspect area conditions and evidence around past investments.
The project asks what those observations can tell us—and what they cannot justify
about a new project or budget.

[Documentation index](docs/README.md) · [Submission reading guide](docs/SUBMISSION_GUIDE.md) · [Rubric-based review](docs/grading-review.md)

## Start here: the research and data-build notebook

**[Open the executed research walkthrough](output/jupyter-notebook/Project_Research_Walkthrough.ipynb).**

This is the primary reading path for the GitHub submission. It explains the source
data, displays the datasets, derives ZIP measures, checks project outcomes,
reproduces baseline model evaluation, interprets the results, and exports the
five JSON files consumed by Place Lab. Saved tables and charts can be read on
GitHub without running Python.

The notebook calls small, tested Python functions. It explains the analytical
choices; `src/` contains reusable implementation. The browser reads the exported
data files, not the notebook itself.

| Read in order | What it establishes |
|---|---|
| Notebook §§1–2 | Source lineage, evolution of the research question, units and coverage |
| Notebook §3 | The ZIP dataset, missingness, formulas and distributions |
| Notebook §§4–5 | Historical outcomes and unstructured-text methods |
| Notebook §§6–7 | Holdout evaluation, sensitivity and supported conclusions |
| Notebook §8 | Validated dataset exports and page data contract |
| [Source audit](docs/project-source-audit.md) | Project dates, costs, geometry and limitations |
| [Advanced text method](docs/advanced-text-method.md) | Sampling, TF-IDF/NMF, leakage controls and pending validation |

## What we found

- The current extraction scores **1,063,956 unique reviews** across **11 projects**
  in seven cities. **Ten project outcomes** meet model support rules. Reviews are
  measurements, not a million independent project training examples.
- Raw review growth can coexist with negative comparison-adjusted growth. Sun Link
  illustrates why activity counts and adjusted outcomes must be shown together.
- Learned topics often concern food and service. They cannot automatically be
  interpreted as civic satisfaction. Place-targeting rules remain provisional;
  independent human precision/recall has not been established.
- Text challengers did not improve both project- and city-held-out errors.
  The retained three-input baseline has MAE **49.33** and **45.61 reviews/$1M**, respectively.
- The baseline's advantage over a mean predictor disappears after timing exclusions.
  The useful result is an inspectable historical evidence workflow, not a validated
  recommendation of a location, project type, or budget.

Capital efficiency (CE) means **growth-adjusted excess Yelp reviews per $1 million
of nominal reported project cost over two post-opening years**. It is not revenue,
financial return, public benefit, or a causal effect. The archive and income data
are historical. Costs have inconsistent public/private scope. The displayed error
range is a historical error envelope, not a calibrated confidence interval.

## Source datasets stay outside Git

Full Yelp archives, Census downloads and intermediate data are excluded from the
repository. Readers obtain source data from the original providers when running
raw extraction. [Data setup and replication](docs/data-setup.md) documents source
links, historical versions, expected paths and the remaining raw-bootstrap limits.

We retain compact prepared research inputs and notebook-generated JSON so the
notebook and static site work from a fresh clone. CI rejects source-data paths,
common raw-download filenames, and individual files over 10 MiB.

## Run the notebook from a fresh clone

Use Python 3.12. The checked-in prepared inputs are sufficient; this workflow needs
no raw Yelp archive, API key, network data request, or sibling course directory.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r requirements-notebook.txt
.venv/bin/python -m ipykernel install --user --name cis509-project --display-name "CIS 509 Project"
.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=cis509-project output/jupyter-notebook/Project_Research_Walkthrough.ipynb
```

Alternatively open the notebook in Jupyter or VS Code, select this environment,
and use **Restart Kernel and Run All**. The notebook locates the repository from
its own directory or the repository root. The existing course workspace can use
`../.venv` instead of creating `.venv`.

Execution rebuilds the page's data and six readable CSV tables. It does **not**
rerun raw-review extraction or fit the advanced text challenger: those require the
original local corpus. The notebook labels saved results and recomputed results
separately and verifies that current evidence, model and text artifacts agree.

## Data lineage and exported datasets

```text
Yelp archive + project sources + Census inputs
                  ↓  upstream extraction / analysis in src/
checked-in historical aggregates + model artifacts
                  ↓  research notebook + tested Python transformations
ZIP / project / text / model tables → web/place-*.json
                                              ↓
                                      Place Lab browser UI
```

| Location | Role |
|---|---|
| `data/derived/place_inputs/` | Frozen, prepared page inputs; manifest records upstream origins and SHA-256 hashes |
| `data/derived/project_evidence.json` | Current historical project counts, text measures, source notes and outcomes |
| `data/derived/advanced_text.json` | Saved descriptive TF-IDF/NMF results and coverage |
| `data/derived/project_model.json` | Current fitted model, holdouts and sensitivities |
| [ZIP evidence CSV](data/derived/notebook_dataset/zip_evidence.csv) | All 196 mapped areas, activity/sentiment/access and ACS fields |
| [Historical projects CSV](data/derived/notebook_dataset/historical_projects.csv) | All 11 projects, raw outcome components, eligibility and exclusion reasons |
| [Project text CSV](data/derived/notebook_dataset/project_text_results.csv) | Near/comparison, period-specific sentiment and text rates |
| [Learned topic terms](data/derived/notebook_dataset/learned_topic_terms.csv) | Five descriptive topic vocabularies |
| [Model comparison](data/derived/notebook_dataset/model_comparison.csv) | Mean predictor and four candidate evaluations |
| [Timing sensitivity](data/derived/notebook_dataset/timing_sensitivity.csv) | How exclusions change the baseline comparison |
| `web/place-build-manifest.json` | Notebook-source, code, source-artifact and output hashes |

Prepared inputs are **derived datasets, not original raw data**. The business
profiles and boundaries were frozen from the previous published extraction;
subsequent notebook runs read those inputs rather than their own `web/` outputs.
The access snapshot retains counts and denominators, without review excerpts.
Full raw Yelp archives and original review/user identifiers remain outside Git.
Other evidence artifacts and generated pages contain short review excerpts and
hashed review keys; the map inputs contain business-level coordinates and counts.
These are tracked separately in the publication audit. CSV ZIP identifiers should
be read as strings; blank numeric values mean unavailable/unsupported, not zero.
Column units and time windows are explained in the notebook's relevant sections.

The map's ZIP dataset compares **2012–2014 with 2019–2021**. Its optional point
model uses a separate **2018–2019, 500 m sample** at a fixed interior reference
point. That sample is not a ZIP-wide impact estimate. ACS estimates are 2007–2011
for Philadelphia/Tucson and 2008–2012 for other study metros. ZCTA polygons include
water, and the later review window includes COVID-19. Access mentions include
praise and complaints.

## Run the application

```sh
python3 src/serve_place.py --port 8766
```

Open [Place Lab locally](http://127.0.0.1:8766/place.html), or double-click
`start-place.command`. The prepared `web/` files run without Python analysis at
view time. Street tiles require internet; **ZIP boundaries · offline** uses bundled
geometry. A single floating panel contains city, ZIP, focus, proposal settings,
legend and evidence. ZIP selection highlights the boundary; there is no project
marker or automatic relocation to another area.

Other views provide supporting evidence:

- `projects.html` / `index.html`: historical project evidence and learned topics.
- `model.html`: historical-profile proposal scenarios and model comparisons.
- `atlas.html`, `lag.html`, `reference.html`, `report.html`: earlier research views;
  their definitions/results must not be mixed with the current model.

UI-only builds are deliberately separate from data builds:

```sh
python3 src/build_place_site.py
npm ci
npm run build:place
```

These commands rebuild HTML/CSS/JavaScript without overwriting notebook-exported
data. GitHub Pages serves the committed `web/` directory. A local edit is not a
published update until committed and deployed. Pages deployment is manual so publication remains deliberate. Configured repository site:
[Public Investment Map](https://intreaction.github.io/neighborhood-sentiment-map/).

## Upstream rebuilds and research history

The original raw archive is `Yelp JSON/yelp_dataset.tar`; business JSON is under
`data/raw/`. These files are not distributed with this repository. Original
extraction is intentionally separate from the grader-friendly prepared-data run.

| Stage | Main implementation | Interpretation / audit |
|---|---|---|
| Earlier ZIP funding and sentiment study | `build_sentiment_panel.py`, `fetch_usaspending.py`, `build_lag_model.py` | [Atlas exploration](docs/atlas-exploration.md), [preregistration](analysis/PREREGISTRATION.md) |
| Named-project cohorts and text extraction | `project_registry.py`, `build_project_evidence.py`, `project_text.py` | [Source audit](docs/project-source-audit.md) |
| Learned text and model comparison | `build_advanced_text.py`, `project_advanced_model.py`, `train_project_model.py` | [Text method](docs/advanced-text-method.md) |
| Prepared local profiles and geometry | `build_place_data.py` | Full archive counts, fixed 2018–2019 baseline |
| Snapshot refresh | `prepare_place_inputs.py` | Explicit refresh after upstream rebuilding; requires local intermediate files |
| Page data transformation/export | `place_pipeline.py`, `build_place_areas.py`, research notebook | Hash checks, denominator checks and missing-data rules |

All implementation names in the table are under `src/`. Raw rebuilds need the
original corpus and upstream intermediate files; the notebook does not download
or regenerate them. Rebuilding the historical pipeline uses:

```sh
python src/build_project_evidence.py --workers 4
python src/build_advanced_text.py
python src/train_project_model.py
python src/build_evidence_site.py
```

Refresh baseline profile snapshots only after running `build_place_data.py` and
the required ZIP analysis stages. Then run `prepare_place_inputs.py` and rerun the
notebook. Snapshot hashes make this refresh explicit rather than silent.

The earlier [historical engagement notebook](docs/history/engagement-model-study-2026-09.ipynb)
is retained as a **prior analysis** using `ce-project-ridge-v2`. Its results are not
the current submission's model. The primary notebook above uses `project-ce-v2`.

## Verification and presentation

```sh
python -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.cjs tests/*.test.mjs
```

Tests cover outcome arithmetic, deterministic sampling, leakage checks,
Python/JavaScript model parity, geographic selection, support rules, data exports
and the local server. Server tests need permission to bind localhost.

- [Presentation slides](docs/presentation/Public-Investment-Evidence.pptx)
- [PDF slides](output/pdf/Public-Investment-Evidence.pdf)
- [Presenter guide](docs/presentation/Presenter-Guide.md)
- [Source/model browser validation](docs/qa/validation.md)

The presentation currently demonstrates the historical-project workflow; Place
Lab adds ZIP exploration. Independent human label validation remains unfinished.
OpenAI Codex assisted with code, analysis checks, debugging, visuals and drafting;
the team remains responsible for the submitted work and its interpretation.
