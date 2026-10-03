# Product validation — September 25, 2026

> Historical evidence/model verification; not a current Place Lab test report. See [current QA](place-lab.md).

Tested the generated static site in the Codex in-app browser through a loopback
HTTP server. This records observed checks, not a claim of universal browser support.

## Browser workflows verified

- All 11 historical proposal presets load. Ten produce supported estimates;
  Water Works Park is withheld for weak baseline/out-of-domain support.
- Project dropdown updates raw counts, outcome, geometry, sources, language and
  deep links. Browser Back restores the previous selection. Direct project URLs work.
- Positive Lafitte, negative Sun Link, and suppressed Water Works outcomes are
  distinguishable and use the same primary measure.
- Changing Dilworth's cost from $55M to $80M updates the estimate. Zero cost withholds
  it; Reset restores the complete historical profile and cost.
- A project-type filter returns the matching historical case and does not change
  the fitted estimate. Keyboard Tab reaches the proposal action with visible focus.
- Valid local JSON import populates inputs and metadata. Invalid fractional units
  are rejected with a visible error while retaining the prior valid profile.
- Export produces `public-investment-analysis.json` with inputs, metadata, version IDs,
  support status and results. The downloaded file was read and its estimate checked
  against the actual fitted coefficients; it matched. The browser automation download
  event timed out, but the saved file verified successful delivery.
- Disclosure controls expose excerpts, model comparisons and text methods. Mobile
  jump links reach the estimate section.
- Atlas city selection, keyboard quarter changes and zoom controls work. The atlas
  defaults to review counts and labels prior CE methods as legacy.
- No browser console errors were observed in these checks.

## Visual and responsive checks

Screenshots were visually inspected on desktop and mobile. The explorer, proposal
form, unsupported state, learned topics, footprint figure and mobile result remain
readable. Measured document width matched viewport width at 320, 360, 390, 768,
1280 and 1440 CSS pixels. Native controls have associated labels; important result
and import/export messages use status/live regions. This is not a full accessibility
conformance audit.

Artifacts:

- `advanced-text-desktop.png`: complete learned-topic comparison at desktop width.
- `advanced-text-mobile.png`: narrow-screen topic section and coverage.
- `proposal-mobile.png`: estimate, error span and interpretation on mobile.

A visual issue found during validation—the atlas banner inheriting flex layout and
splitting prose into fragments—was corrected and rebuilt. Preset decimal precision,
complete reset, Back navigation, source labels and duplicate error prose were also
checked or corrected during implementation.

## Limits of these checks

Direct `file://` navigation was blocked by the browser tool's URL policy; no workaround
was attempted. The HTTP-served pages were tested, and static contract checks verify
embedded assets without external scripts/styles. Direct-file behavior is not certified.
Native 200% browser zoom, touch-device hardware, screen readers, Safari and Firefox
were not tested. Raw text accuracy has not been independently human-validated.

## Automated checks

Run the reproducible suite:

```sh
../.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.cjs
```

Coverage includes primary-outcome arithmetic, exact Sun Link fixture reconciliation,
shared-review joins, target/negation semantics, deterministic advanced sampling,
baseline-only vocabulary fitting, held-out text exclusion, Python/JavaScript numeric
parity, model support guards, portable builds, profile validation and every preset.
Final run: **47 Python tests passed**, **three Node test files passed**, and
`git diff --check` passed. The final model artifact is `project-ce-v2`; evidence is
`project-evidence-v1`; descriptive learned text is `tfidf-bigram-nmf5-v1`.

The final topic-enabled sample profile was downloaded and successfully reimported
in the browser with its exact predictive topic-basis ID. Final proposal layouts
were rechecked at 320, 390, 768 and 1440 pixels after the advanced build.
