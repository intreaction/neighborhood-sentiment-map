# Current Place Lab verification

Recorded October 2, 2026. This describes the current desktop 2D ZIP workflow.
Earlier 3D/voice/AR checks are available in Git history and do not describe
the current product.

## Completed evidence

- Primary notebook: all 11 code cells executed. A separate copy containing only
  publishable repository files also executed using the existing Python environment;
  all five static JSON hashes matched the working repository on that platform.
- Local tests: 63 Python and 51 JavaScript tests passed.
- [GitHub Linux CI](https://github.com/intreaction/neighborhood-sentiment-map/actions/runs/37059524331)
  passed for commit `a1f26a3`: fresh dependency installation, repository audit,
  Python/JavaScript tests and UI build. One optional raw-corpus Python check is
  skipped without the ignored corpus. This is distinct from the local all-pass run.
- Linux exposed exact floating-point comparisons in two tests. Strict numerical
  tolerance resolved platform roundoff; counts, labels and hashes remain exact.
- Browser validation covered asset loading, Philadelphia/Tucson switching, ZIP
  selection, activity/decline focus changes, budget updates, panel collapse and
  populated historical/scenario charts. A sparse-ZIP selection error was found
  and corrected: an empty 500 m sample no longer hides available ZIP evidence.
- The notebook export hashes matched the static JSON files after the UI rebuild.
- Public-source exclusions and the focused credential/size scan passed. These do
  not constitute exhaustive security or licensing validation.

## Limits

The browser checks did not certify every focus, browser, assistive technology,
mobile viewport or device. There is no current voice/AR verification claim. The
raw NLP pipeline was not retrained during this check. Human label quality,
external predictive validity and a rehearsed live presentation remain unverified.

For changes after this record, rerun the relevant checks in
[maintenance](../maintenance.md) and append a dated result rather than assuming
this record covers later commits.

## Pre-publication cleanup — October 2, 2026

Removed the unused Three.js/AR implementation, its geometry adapter and five
prototype-specific tests. The current 2D map, geometry selection and street-tile
tests remain. The production bundle rebuilt successfully and all **46 remaining
JavaScript tests** passed. Historical test counts above describe their original
commits. Removed plans, demo documents and duplicate HTML are recoverable in Git
history; the research notebooks, evidence tables and presentation remain.
