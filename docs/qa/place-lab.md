# Place Lab verification — September 26, 2026

Update September 30, 2026: AI voice transport and API endpoints were removed.
The local launcher now serves static files only. Counts below describe the earlier
verification pass; the mocked voice tests were retired. The static build succeeded,
28 Node checks passed for profiles, models, maps and browser tools, and four local
HTTP checks passed for assets, request restrictions and removed API endpoints.

The primary workflow uses the map and ordinary controls. No provider connection or microphone permission is needed.

## Automated checks

- 61 Python tests passed, including the existing project/model suite, new complete-
  archive location profiles and nine mocked local voice-server tests.
- 25 Node test entries passed across legacy math, place profiles/commands, all 196
  real ZIP geometries, optional agent adapters and mocked voice transport.
- The browser bundle builds with pinned local Three.js/esbuild dependencies.
- Provider tests use mock responses; they make no paid API requests.

## Browser checks completed

Tested the served app in the Codex in-app browser, with no OpenAI API key configured.

- The Rail Park opening profile displays 124 baseline-reviewed businesses, 2,613
  reviews, 21.1 reviews/business and 41.2 excess reviews/$1M for a $25M proposal.
- A direct budget edit to $50M immediately changes the estimate to 34.8. The
  browser check caught a delayed-update problem; the input handler was corrected.
- Map click changes the geographic selection and recounts businesses (one tested
  point at displayed 39.9572, -75.1529 returned 251 reviewed businesses).
- Selecting Dilworth shows 968 reviewed businesses and withholds the estimate
  because the model's observed business-count support ends at 859.
- Sun Link and Tampa Riverwalk change cities and profiles correctly. Tampa
  Riverwalk at $32M shows 164 businesses and an estimate of 55.1.
- Nashville and New Orleans city switching rebuilds their real map geometry.
- Changing type updates comparable ordering, while preserving numerical prediction.
- Invalid zero budget reports that it was not applied and that results retain the
  last valid budget; Reset restores the default proposal.
- JSON scenario export and USDZ AR export both complete through browser controls.
- Unsupported live WebXR displays a fallback message and preserves the desktop UI.
- The optional command panel supports budget edits and evidence questions.
- Native WebMCP tools were discovered by the actual browser. `inspect_proposal`
  returned the measured state; `update_proposal` changed the visible budget to $30M
  and type to Civic park, producing the same model result (about 39.5).
- Visual inspection at desktop and 390 px mobile width: map, landmark labels,
  500 m ring, controls, count cards, estimate, comparables and explanations render.
- Widths 320, 390, 768 and 1280 px reported no horizontal overflow.
- Opening/closing the assistant revealed a canvas sizing feedback issue. A fixed
  CSS viewport corrected it; measured scene height stayed 390 px before, during and
  after toggling the panel, with no horizontal overflow.
- No browser console errors were reported during the final manual/export checks.

## Limits of this verification

- No physical AR device was supplied. Surface detection, placement stability,
  touch behavior on an actual phone, AR overlay usability and device FPS remain
  unverified. Desktop viewport resizing is not a substitute for those tests.
- USDZ generation/download was tested, not Apple Quick Look rendering on hardware.
- Live speech, actual model access, provider billing and simultaneous voice/AR were
  not tested because the server API key is absent. Mocked transport tests cover
  transcripts, tools, permission failures, cleanup, mute and autoplay recovery.
- No claim of screen-reader, Safari or Firefox certification is made.
- These tests establish implementation behavior, not external predictive validity.

See [the implementation guide](../plan/conversational-ar.md) for the data contract,
launch instructions, optional LLM tools and the remaining device validation gate.
