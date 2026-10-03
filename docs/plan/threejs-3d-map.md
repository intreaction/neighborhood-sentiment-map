# Tomorrow: a Three.js map worth demoing

Planned session: September 26, 2026. This is the original implementation plan.

The subsequent product direction prioritizes location selection, project type and
budget through direct controls, with optional LLM tools and AR. See the implemented
[Place Lab plan](conversational-ar.md). Its schematic ZIP extrusion is not the
quarterly review-height layer proposed below; timeline work remains deferred.

## Goal

Give the demo a memorable opening: an angled, interactive city landscape where
review activity rises above neighborhoods, project footprints stand out, and a
click leads into the project's text evidence and proposal analysis.

The visual should feel like a small city model on a table, using our cream, dark
green and ochre palette. Smooth camera motion and clear selection should provide
the polish. The map's height will represent review activity, with an explicit legend.

**Finish line:** a working Philadelphia scene, then the other four existing atlas
cities, with selection, quarter controls, a reliable reset, and a direct route to
the current project analysis. Capture a short demo sequence and update the deck.

## Current foundation

- `src/build_map_page.py` creates `web/atlas.html` with embedded geometry and data.
- `src/map_template.html` renders the current SVG scene and links ZIP selection,
  city selection, quarterly data, review lenses and charts.
- The atlas has 196 mapped ZCTAs across five metros and 40 quarters (2012–2021).
- `data/project_registry.json` and `data/derived/project_evidence.json` describe
  11 projects across seven cities. These records own the current project outcomes.
- The current project and proposal pages already work. The demo launcher serves
  local assets and can support an additional page and bundled JavaScript.

The seven-city project library and five-city atlas have different coverage. The
first 3D pass uses the existing atlas metros. We will keep every project available
in the library without inventing missing ZIP maps for the other two cities.

## Visual and interaction decisions

| Element | First implementation |
|---|---|
| Camera | Angled perspective with a restrained opening move and a fixed home view |
| Geography | Extruded ZIP polygons, flat water/context geometry, subtle directional lighting |
| Height | Current-quarter review count using a documented `log1p` scale |
| Scale | Fixed across quarters and cities in the displayed dataset; slider movement must not rescale the whole scene |
| Color | Restrained activity shading, selected outline and explicit low-coverage styling |
| Projects | Canonical mapped footprints or clearly marked proxy centers, with project names on selection |
| Navigation | Orbit, pan and bounded zoom; visible Reset view and Top view controls |
| Selection | Hover identifies a ZIP; click selects it and updates the HTML inspector |
| Project action | Select a project, inspect its outcome, then open the existing project/proposal page |
| Text evidence | Project panel links to learned topics and place-specific signals; existing ZIP review lenses remain explicitly separate |
| Motion | Animate transitions briefly; respect reduced motion; avoid a permanently spinning map |
| Mobile | Keep page scrolling usable; offer deliberate map interaction and a clear 2D fallback |

The scene is an extruded data map. Its columns are not building heights or terrain.
Project CE stays attached to the project record rather than being painted across
entire ZIPs. A timeline change updates quarterly review activity; it does not
recalculate a historical project's fixed-window outcome.

## Build sequence

### 1. Lock the data and demo path — 45 minutes

- Start with Philadelphia and Dilworth Park.
- Define a reusable atlas payload and stable IDs for ZIPs, cities and projects.
- Preserve the current atlas output while exposing its geometry/quarter data to
  the 3D builder. Add a small canonical-project adapter instead of carrying forward
  the legacy map's CE lookup.
- Record a few known ZIP/quarter values and project outcomes as parity fixtures.
- Choose a fixed height scale and publish its units in the legend.

**Checkpoint:** the new payload reproduces the selected ZIP values and Dilworth
outcome before any camera or mesh work.

### 2. Build the first city scene — 90 minutes

- Add a pinned Three.js dependency and a minimal local bundling step with a lockfile.
  Bundle dependencies into `web/`; the demo must not depend on a CDN.
- Add `src/atlas_3d.js`, `src/atlas_3d.css` and a 3D template/builder that outputs
  `web/atlas-3d.html` and a local JavaScript bundle.
- Project longitude/latitude into local meter coordinates around a city origin.
- Convert Polygon and MultiPolygon features into shapes, preserving holes and
  disconnected pieces. Build non-beveled extrusions and cache geometry.
- Keep geography on one ground plane, with height on a separate vertical axis.
- Add camera, lighting, water/context shapes and a default Philadelphia view.

**Checkpoint:** Philadelphia renders correctly, with no filled-in rivers or holes,
flipped geography, or height that users could mistake for real buildings.

### 3. Make it a usable map — 90 minutes

- Add constrained OrbitControls and camera reset/top-view controls.
- Add raycast selection with drag-versus-click handling.
- Keep labels, controls, tooltips and the inspector in accessible HTML.
- Link ZIP selector, quarter slider and supported review lenses to scene updates.
- Update heights without recreating every mesh on every frame.
- Retain selection while changing quarters; move the camera only when requested.
- Add project selection and canonical links to the current evidence/proposal pages.

**Checkpoint:** a user can find Dilworth, change quarter, inspect a ZIP, and open
project evidence without learning complicated 3D navigation.

### 4. Add the presentation polish — 60 minutes

- Tune restrained lighting, edges and selected-project emphasis.
- Add a short camera transition to a selected project, cancellable by interaction.
- Add a modest height transition when the quarter changes.
- Use a clear legend and short first-use instructions.
- Extend to Tampa Bay, New Orleans, Nashville and Tucson using the same renderer.
- Preserve city/ZIP/quarter in navigation state where applicable.
- Add a visible 2D link and a graceful message/fallback if WebGL is unavailable.

**Checkpoint:** the scene adds an immediate visual hook and still leads naturally
to the analytical product.

### 5. Validate, repair, and package — 90 minutes

- Compare selected ZIP/quarter counts with the existing 2D atlas.
- Check holes, multipart geometry, project positions, sparse coverage and empty data.
- Test all five cities, repeated city switching, timeline changes, reset and project links.
- Test keyboard access through HTML controls, zoom limits, reduced motion and page scroll.
- Inspect desktop and mobile screenshots, including labels near viewport edges.
- Measure frame timing on the actual demo laptop. Aim for smooth interaction, with
  at least 30 FPS during orbit on the target machine; cap pixel ratio if needed.
- Dispose of scene resources when switching cities. Check for growing memory or
  duplicate event handlers after repeated switching.
- Verify the site after disconnecting external network access, using its local server.
- Run existing project/model tests and targeted geometry/selection checks.
- Save new screenshots, update the presentation's demo slide, and rehearse the route.

**Checkpoint:** a reproducible local demo with a working fallback and no regressions
in the existing project/proposal workflows.

## Work allocation

If using the same parallel-agent setup:

- **Geometry/data agent:** shared payload, projection, polygon holes/multipart
  conversion, canonical project adapter and numerical parity checks.
- **Scene agent:** Three.js renderer, camera, picking, resource cleanup and animation.
- **Primary agent:** HTML controls and evidence integration, final styling, browser
  verification, performance check, presentation assets and demo rehearsal.

Agree on the payload and selection-event contract first. Keep file ownership clear
so parallel work does not rewrite the same rendering or template files.

## Scope control

Priority order:

1. One city with correct geometry, compelling camera framing and reliable selection.
2. Project evidence links and the timeline.
3. The remaining existing atlas cities.
4. Visual polish and presentation screenshots.

Leave photorealistic buildings, terrain tiles, new geographic data collection,
WebGPU, custom shaders and animated particles for another pass. Avoid adding a
React migration to this task. Defer live model-output geometry until its meaning
and uncertainty have a clear visual design.

If polygon conversion or browser performance consumes the time budget, ship a
polished Philadelphia pilot with a 2D fallback and label the coverage clearly.
Do not spend the final hour adding effects before the demo route works.

## Acceptance checklist

- [ ] Local build and launch work without external asset requests.
- [ ] Philadelphia is immediately recognizable and pleasant to navigate.
- [ ] ZIP geometry, holes and project positions are correct.
- [ ] Height legend and fixed scale explain the data mapping.
- [ ] Selected values match the existing atlas and canonical project evidence.
- [ ] Timeline, ZIP selector, project links and Reset view work together.
- [ ] Other atlas cities work, or the first-city scope is explicit.
- [ ] Keyboard users can reach equivalent information through HTML controls.
- [ ] Mobile scrolling and reduced-motion behavior are usable.
- [ ] WebGL failure and the 2D fallback are understandable.
- [ ] Target-laptop performance passes the agreed demo check.
- [ ] Screenshots and the presentation reflect the actual finished scene.

## Tomorrow's opening demo

Start with the angled Philadelphia landscape. Select Dilworth and move the camera
closer. Scrub a few quarters to show review activity changing. Open its project
analysis, inspect the learned text topics, then carry the profile into the proposal
tool. The 3D scene supplies the visual hook; the evidence and scenario workflow
supply the substance.

## Implementation references

Official Three.js documentation, checked while drafting this plan:

- [Creating a scene](https://threejs.org/manual/pages/creating-a-scene.html)
- [ExtrudeGeometry](https://threejs.org/docs/pages/ExtrudeGeometry.html)
- [OrbitControls](https://threejs.org/docs/pages/OrbitControls.html)
- [Responsive design](https://threejs.org/manual/pages/responsive.html)
