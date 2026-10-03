# Architecture

Place Lab is a static research application. Python prepares and validates data;
the browser reads JSON and computes an exploratory scenario locally. There is no
application database, inference service or API key required to view the site.

## Research and build flow

```text
Local source archives and historical course extracts (ignored by Git)
  → upstream Python extraction / NLP / model builders
  → prepared input snapshots + historical evidence/model artifacts
  → executed research notebook → five static JSON files + CSV tables + manifest
  → browser ZIP map, evidence cards and scenario charts
```

The [notebook](../output/jupyter-notebook/Project_Research_Walkthrough.ipynb) imports
`src/place_pipeline.py`: `load_inputs` verifies snapshot hashes and evidence/model
compatibility; `derive_areas` recomputes ZIP measures; `build_payloads` assembles the
five page inputs; `validate_payloads` checks geography, totals and missing-value
rules; `export_payloads` writes files and a provenance manifest.

All payloads are validated before writing. Each JSON file is replaced atomically,
but the complete five-file export is not a single filesystem transaction. Finish
and verify a build before serving or publishing it. The manifest hashes notebook
source cells separately from saved outputs to avoid self-reference.

`prepare_place_inputs.py` is an explicit upstream snapshot refresh. It depends on
local intermediate files and existing extraction outputs. It is not part of the
normal fresh-clone notebook run. The notebook refits the baseline regression;
it displays saved advanced-text evaluation rather than retraining NMF from counts.

## Browser modules

| Module | Responsibility |
|---|---|
| `src/place_app.js` | Load five assets, maintain proposal state, wire controls and update views |
| `src/place_map.js`, `place_map_math.mjs` | Canvas 2D rendering, projection, bounds, fitting and interaction |
| `src/place_street_tiles.mjs` | Online street-tile loading and offline fallback |
| `src/place_area_math.mjs`, `place_area_ui.js` | ZIP selection, stable interior reference points, focus values and colors |
| `src/place_core.cjs` | 500 m profiles, proposal validation and optional point-selection helpers |
| `src/project_model_math.js` | Browser-side model calculation and support checks |
| `src/place_charts.js`, `place_chart_components.tsx` | React/Recharts evidence and scenario charts |
| `src/place_tools.cjs` | Optional browser tool adapter using the same application calculations |

The human map workflow selects a ZIP polygon without moving a visible marker.
Its fixed interior reference point supplies a separate 500 m model sample. A ZIP
can retain area evidence even when its point sample cannot support an estimate.
Project type changes comparable ordering, not the fitted regression's inputs.

The retired Three.js/AR prototype and its dependency have been removed. The
current canvas map does not require WebGL, Three.js or an AR device.

## Build and hosting boundaries

`src/build_place_site.py` copies the HTML/CSS sources into `web/` without changing
data. `npm run build:place` bundles JavaScript and chart CSS. `web/` contains prepared
static assets for local hosting or GitHub Pages. Do not edit generated bundles by
hand. UI-only builds do not execute the notebook.

`src/serve_place.py` serves only `web/` on loopback, restricts request origin/host,
and exposes no API endpoints. Street tiles require a network connection; bundled
ZIP geometry works offline. The archived population/ACS values are not live feeds.
The browser needs HTTP hosting to fetch JSON; opening HTML with `file://` is not
the supported launch path. See [maintenance](maintenance.md) for commands and failures.
