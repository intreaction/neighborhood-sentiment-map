# Place Lab: five-minute single-user demo

Browser rehearsal: September 26, 2026. Direct controls, budget updates, support
withholding, comparable navigation, text evidence, orbiting and AR fallback were
exercised. The app reported a completed USDZ export; the automation's download
event wait timed out, so that event was not independently confirmed in this pass.
No browser console errors were recorded. Physical AR is not verified.

## Start

Run `python3 src/serve_place.py --port 8766` and open
`http://127.0.0.1:8766/place.html`, or double-click `start-place.command`.
The app runs entirely in the browser; no API backend is needed.

## 1. The question — 30 seconds

“An official chooses a place, a project type and an estimated budget. We measure
the surrounding business activity and compare that proposal with historical
public projects.”

Begin near The Rail Park with a $25M civic plaza. Show the 500 m orange study ring,
business dots and location controls. These are ZIP geometries, not 3D buildings.
City view shows the metro; drag to orbit, then Focus location returns to the study
area. The current archive is historical, not a current business census.

## 2. Measured inputs — 45 seconds

Click View analysis. Point out 180 archive inventory businesses, 124 with baseline
reviews, and 2,613 reviews in 2018–2019: 21.1 reviews per reviewed business.
The estimate is 41.2 growth-adjusted excess Yelp reviews per $1M over two post years.
This point scenario differs from the historical Rail Park footprint and outcome.

## 3. Change an assumption — 45 seconds

Change the budget to 50. The estimate updates to 34.8; the measured neighborhood
counts stay the same. Open Uncertainty & assumptions: the historical error envelope
is -68.0 to 137.7, with city-holdout MAE 45.6. It is not a confidence interval.

“This is an exploratory activity association. It does not establish financial ROI
or the causal return from spending more.”

## 4. Show the boundary — 30 seconds

Choose Dilworth Park from Location shortcut. The point profile has 968 reviewed
businesses, above the observed model range of 28–859. The estimate is withheld.
This is different from inspecting Dilworth's historical observed outcome.

## 5. Open the unstructured evidence — 90 seconds

Reset scenario, then select Civic park. The estimate stays 41.2; the comparable
list changes and includes Gateway Arch Park. Project type affects comparables,
not the fitted numerical estimate. Open that comparable.

Show Learned patterns in review language and expand Text richness, examples & how
this was fitted. Explain TF-IDF terms/word pairs, five NMF topics, topic diversity,
lexical diversity and negation frequency. Show the separate provisional sentiment
and place-topic signals below. These describe nearby business reviews, not direct
measurements of residents' experiences of the capital project.

“We evaluated text features as predictive challengers. The selected model retains
budget, business count and review intensity. The richer text remains evidence to
inspect; we do not claim it improved the selected model.”

## 6. Put the analysis in the room — 60 seconds

Use the Place Lab navigation link to return to the opening scenario.
On a tested, compatible WebXR device: choose Place in your room, find a horizontal
surface, tap to place, and walk around the map. Inspect the label and select another
location. Demonstrate Reposition map and Exit AR. Device testing is required before
promising this portion live; do not substitute desktop orbiting for tracking proof.

On the desktop rehearsal, the AR button correctly reports unsupported placement.
iPhone AR snapshot generates a USDZ export. Quick Look displays a snapshot; editing
the analysis requires returning to the page and exporting again.

Close with: “The goal is a spatial planning aid that connects a proposed investment
to its surrounding evidence, while making uncertainty and data coverage visible.”
