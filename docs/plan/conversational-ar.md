# Place Lab: public-project analysis with optional AI tools

Implemented prototype: September 26, 2026. AI voice was removed September 30, 2026.
The current 2D interface runs entirely in the browser. Physical AR still requires
device validation. This is an extension of the existing
evidence product, not a new validated forecasting model.

## Product flow

The current scope is **single-user spatial analysis**. Place one map on a surface
in the room, walk around it, and inspect the selected neighborhood and its data.
Multiplayer, room presence, avatars and shared spatial anchors are deferred. No
multiplayer framework or room backend is needed for this milestone. A native app
is a possible device-specific path, not a prerequisite for the supported WebXR demo.

Select a point on the map, choose a project type, and enter an estimated budget.
These direct controls are the primary interface. No AI account, microphone, command
parser or model-provider connection is required. Optional browser integrations use the same validated proposal controls.
The app measures a 500 m neighborhood, counts Yelp-listed businesses and businesses
with baseline reviews, then runs the existing capital-efficiency model. Browser tools can update the same proposal state as the map and form controls.
Computed results always come from the deterministic model.

The opening example is a $25M plaza near The Rail Park in Philadelphia. Its point
profile has 124 reviewed businesses, 180 archive inventory businesses and 2,613
reviews in 2018–2019. The selected model returns about 41.2 excess reviews per $1M
over two post years. This is a new retrospective point scenario, not the original
Rail Park project's historical footprint or observed outcome.

## Run it

From the repository root:

```sh
python3 src/serve_place.py --port 8766
```

Open `http://127.0.0.1:8766/place.html`. The checked-in web assets work without npm,
raw Yelp files or external map services. The static page also works through the
existing demo server or any static hosting service.

## Optional LLM tools

The page registers three native WebMCP tools where the browser supports the API:
`inspect_place_catalog`, `inspect_proposal`, and `update_proposal`. All calls use the
same validated state and deterministic model as the human controls. They do not
start a microphone, connect a paid provider, publish anything or navigate away.

Other browser integrations can use the documented local adapter:

```javascript
await window.placeLab.call("inspect_place_catalog", {});
await window.placeLab.call("update_proposal", {cost_millions: 50});
await window.placeLab.call("inspect_proposal", {});
```

Catalog/inspection are read-only. Returned values are detached JSON; mutating them
does not change the live scenario. Invalid edits leave the previous scenario intact.
Semantic form labels and stable element IDs remain available for agents without
WebMCP. Registration is optional and failures do not block the human interface.
See [Chrome WebMCP documentation](https://developer.chrome.com/docs/ai/agents).

## AR paths

**Interactive WebXR:** the same Three.js scene and proposal state can be placed on
a detected horizontal surface. A runtime capability check gates session startup.
Where DOM overlays are supported, direct proposal controls remain available over AR;
otherwise the browser's AR exit returns to the page. The map has a shared analysis
label between desktop and AR so the proposal remains visible in the scene. After
placement, the user can physically move around the map while the device tracks its
viewpoint. Select, reposition and exit are implemented; physical tracking and label
readability from different sides require hardware testing.

For a compatible Android device, Chrome USB port forwarding can expose the local
server as `http://localhost:8766` on the device in a secure context. Preserve that
same port for the server's origin check. Merely opening a laptop LAN IP over HTTP
does not satisfy WebXR's secure-context requirement. No public tunnel was created.

**iPhone/iPad AR Quick Look:** export a USDZ snapshot of the current city and proposal,
then tap the prepared AR link on a supported device. This is a snapshot viewer.
Live conversation, selection changes and model updates remain in the web page;
export again after changing a proposal. Desktop browsers can download the USDZ.

**Desktop/fallback:** orbitable 3D, clickable geographic selection, landmarks,
coordinate inputs and the existing 2D atlas. A missing WebGL/AR capability does not
disable the location/profile/model controls.

## Data and model contract

- Five atlas metros, 196 ZIP geometries. No invented street or building geometry.
- Full raw archive scan: 6,990,280 reviews; 1,813,646 fall in 2018–2019.
- Published location index: 72,575 coordinate/count records across buffered metro
  regions. No raw review text, business names or source business/review IDs.
- Each record includes zero or more reviews in the same fixed two-year baseline.
- Metro record bounds include a 1 km buffer so a 500 m selection near the supported
  region's edge retains its neighbors. Points outside selection bounds are unavailable.
- Baseline business count and reviews/business are measured over a point radius.
  Historical training cases may use extended footprints; this remains a limitation.
- The selected three-input model, support checks and error envelope are reused
  without retraining. Project type reorders comparable evidence only.
- “Capital efficiency” is **two-post-year growth-adjusted excess Yelp reviews per
  $1M nominal reported cost**, never annual activity, financial ROI or a causal effect.
- Text sentiment and learned topics remain in the linked evidence library. We did
  not claim newly measured place-specific sentiment for arbitrary map locations.

## Files and rebuild

```sh
# Requires the local Yelp archive and prepared geographic boundaries:
../.venv/bin/python src/build_place_data.py
# UI/model assets:
python3 src/build_place_site.py
npm ci
npm run build:place
```

`place_core.cjs` owns deterministic location measurements, state validation and
model calls. `place_app.js` connects the UI, map and optional browser tools. `place_scene.js` owns
Three.js/WebXR/USDZ; `place_geometry.mjs` owns projections and polygon conversion.
`serve_place.py` serves the static assets for local demos.

## Next acceptance gate

1. Choose the actual demo device and validate surface placement in the presentation
   room. Walk around the map, approach it and step back; check placement stability
   and readable business counts, budget, estimate and its two-year outcome label.
2. On interactive WebXR, select another map location and change the budget using
   ordinary controls. Confirm the in-scene data updates without AI or a microphone.
   Validate repositioning, exit and returning to the same proposal on the page.
3. On iPhone/iPad Quick Look, validate walking around the exported map and reading
   its labels. Explicitly demonstrate that changing analysis requires returning to
   the page and exporting again; live in-AR editing is not provided by this path.
4. Measure frame rate and verify labels from multiple viewing directions. Treat
   tiny or reversed labels as defects to resolve before calling the AR demo ready.
   Rehearse the desktop fallback. These hardware checks are still outstanding.
5. Expand geography/current business coverage and historical training cases before
   representing the prototype as an operational budgeting tool.

## Implementation references

- [Three.js ARButton](https://threejs.org/docs/pages/ARButton.html)
- [Google WebXR requirements](https://developers.google.com/ar/develop/webxr/requirements)
- [Apple AR Quick Look](https://developer.apple.com/quick-look-gallery/)
