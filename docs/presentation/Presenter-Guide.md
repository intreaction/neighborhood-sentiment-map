# Project overview — presenter guide

[Open the Google Slides deck](https://docs.google.com/presentation/d/1sg0G4LGOqI1nrnQCK6E-p9zHme1tHvJlLT3XWMzv2ME/edit) · [CIS 509 Group folder](https://drive.google.com/drive/folders/1VNB4BIbkiL1KiISKPGbI3SAH_ryArrsc)

The presentation follows the course's Final Project Deliverables – Grading Rubric.
It has 21 presentation slides plus two source appendix slides. The planned talk
is 14:35, including a 60-second demo; the appendix is for questions.
The rubric recommends approximately 12–15 minutes. Assign speakers and rehearse;
the timing below is a plan, not a measured delivery.

| Slides | Rubric coverage | Weight |
|---|---|---|
| 2–4, 8–12, 19 | Planning problem, focus questions and proposed uses | 15% |
| 4–5, 8–12, 15 | Sources, preparation, coverage and observed patterns | 10% |
| 8–14, 17 | Focus calculations, NLP choices and held-out evaluation | 25% |
| 8–12, 15–19, 21 | Worked ZIP examples, model findings and planning implications | 25% |
| Throughout | Clear narrative and visuals; delivery requires rehearsal | 10% |
| 6 plus repository | Notebook, reusable modules, tests and reproducibility | 15% |

These are the full project's rubric weights. The focus section is the center of
the talk. Notes provide detailed formulas and sources for questions; do not read
them verbatim. Five NMF topics remain exploratory and human label validation is
unfinished. The deck does not imply the heatmaps forecast project effects.

| Slide | Topic | Target time |
|---|---|---|
| 1 | Project and team | 0:00–0:30 |
| 2 | NYC: Yelp reveals missing reports | 0:30–1:15 |
| 3 | NYC: procurement timelines | 1:15–2:00 |
| 4 | Public data retrieval and preparation | 2:00–2:45 |
| 5 | Preparation and coverage | 2:45–3:25 |
| 6 | Notebook and static exports | 3:25–3:55 |
| 7 | Current map | 3:55–4:20 |
| 8 | Reach active business areas | 4:20–5:05 |
| 9 | Support lower-income areas | 5:05–5:55 |
| 10 | Explore declining activity | 5:55–6:40 |
| 11 | Explore worsening experiences | 6:40–7:35 |
| 12 | Investigate access concerns | 7:35–8:25 |
| 13 | Geographic units | 8:25–8:55 |
| 14 | NLP methods | 8:55–9:50 |
| 15 | Learned topic terms | 9:50–10:25 |
| 16 | Sun Link outcome | 10:25–11:10 |
| 17 | Model evaluation | 11:10–11:55 |
| 18 | Timing sensitivity | 11:55–12:30 |
| 19 | Planning implications | 12:30–13:10 |
| 20 | Demonstration | 13:10–14:10 |
| 21 | Conclusions | 14:10–14:35 |

Appendix A1 links the opening evidence; Appendix A2 links datasets, source audits,
text methods and model results. Both are outside the timed talk.

## Focus data lineage

All worked examples use ZIP 19134 and the current `web/place-areas.json` export.
The notebook calls `src/build_place_areas.py` to derive these measures from the
prepared inputs in `data/derived/place_inputs/`.

| Focus | Prepared source | Calculation / example |
|---|---|---|
| Activity | `sentiment_zip_quarter.csv`, `map_geometry.json` | 1,702 reviews ÷ 3 years ÷ 9.7004 km² = 58.5 per km²/year |
| Income / poverty | `income.csv` | ACS 2007–2011: median household income $24,048 (MOE $1,889); poverty 49.0% |
| Declining activity | `sentiment_zip_quarter.csv` | 100 × (1,702 ÷ 1,012 − 1) = +68.2%; this ZIP grew |
| Worsening experiences | `sentiment_zip_quarter.csv`, `metro_zips.json` | ZIP sentiment change +0.017 minus rest-of-metro change −0.072 = +0.089 relative improvement |
| Access concerns | `access_quarters.json` | 56 keyword-matching reviews ÷ 1,702 total × 100 = 3.3% |

Review windows are 2012–2014 and 2019–2021. ACS uses 2007–2011 in Philadelphia
and Tucson, 2008–2012 elsewhere. Income is historical, not a reviewer attribute.
Access includes praise and complaints. “No heatmap” turns the overlay off; it is
not a sixth analytical focus. Limited data is not zero.

## Live demonstration

Start `python3 src/serve_place.py --port 8766` before presenting and open
`http://127.0.0.1:8766/place.html`.

1. Choose Philadelphia. Switch between business engagement and access concerns;
   explain the legend, historical dates and limited-data colour.
2. Type 19134 in the ZIP search. Scroll to the ZIP profile table and click one
   underlined term to show a definition.
3. In "What happened around similar past projects?", choose Trail / greenway, click
   The Rail Park, and switch the chart tabs from Business engagement to Sentiment.
   Point out the low-reliability badge on the negative-comment columns.

**Agent segment (about 30 seconds).** Place Lab's twelve agent tools let a voice or chat
assistant drive the page (Methodology § 10). If no assistant is connected, run the same
calls from the browser console; each one scrolls, highlights and shows a caption:

```js
await placeLab.call("show_on_map", {city: "Philly", zip: "19134", focus: "access"})
await placeLab.call("navigate", {direction: "down"})          // ZIP profile
await placeLab.call("navigate", {direction: "right"})         // next measure; map follows
await placeLab.call("move_to_neighbor", {direction: "north"}) // ZIP next door
await placeLab.call("show_past_projects", {project_id: "the-rail-park", chart: "sentiment"})
```

Say what makes it trustworthy: the tools use the same code as the tables, change only
the view, and never forecast.

Keep the demo to 60 seconds. Use slide 6 as the fallback if the browser fails. Do not debug during the talk.
The older [historical-project demo](../demo-runbook.md) remains an optional deeper
workflow; it is not the primary sequence for this deck.

## Interpretation boundaries

- Review activity is not revenue, visits, welfare or financial ROI.
- Heatmap focuses are descriptive; the model does not forecast improvement in them.
- Ten eligible project outcomes remain a small prediction sample despite the
  much larger review corpus.
- Learned text did not improve held-out prediction. Timing exclusions weaken the
  simpler model's advantage over a mean predictor.
- Rule labels still need independent human validation. The notebook rebuilds
  published outputs from prepared inputs; raw-source replication requires acquisition.

## Submission

Verify instructor access to the deck and rehearse timing. Export a PDF or PowerPoint
from Google Slides only if the course submission system requires an attachment.
The shared-folder deck is the presentation source of truth.

## Contrast check (2026-10-02)

The original check covered all 161 visible editable text runs across 15 slides using their Google
Slides text and background colors, with the WCAG relative-luminance calculation.
The chosen target is 4.5:1 for all text, including large text. The final minimum
is 5.24:1. Fixed black slide numbers on the two dark slides (previously 1.81:1),
darkened brown callouts (previously 3.36:1), and strengthened small captions.
The deck was rendered and visually checked, including browser inspection.

This does not certify every pixel of the embedded app screenshot. Its map labels
are small and sit on variable backgrounds; use the live demo for those details.
Reference: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html

The expanded focus deck preserves that palette. Its five new slides use the same
text styles; all 20 rendered slides were checked after the expansion.


## Opening evidence and chart sources

The opening distinguishes the value of existing data from the work needed to use it.
The project is a prototype intended to support investigation; deployment savings
and improvements in public decisions have not been measured.

- **NYC Yelp pilot (2012–2013):** among 468 reviews consistent with recent or
  potentially recent illness, 15 also corresponded to reports to 311. The other
  chart bar is derived as 468 − 15 = 453. Expert review and follow-up identified
  three previously unreported outbreaks. This is review-text screening followed
  by investigation, not an automated diagnosis. [Harrison et al., CDC MMWR (2014)](https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6320a1.htm).
- **NYC procurement (FY2026):** median cycle times were 282 days for competitive
  sealed bids and 527 for competitive sealed proposals. Both bars start at zero.
  These are citywide contract categories, not data-only or consultant-only
  purchases, and are not estimates of time saved by our app.
  [NYC MOCS Citywide Indicators Report](https://www.nyc.gov/site/mocs/resources/citywide-indicator-reports.page).
- **Our retrieval workflow:** Census tables and geographic vintages, Yelp archive
  joins, and separate project records must be aligned and checked. See
  [data setup](../data-setup.md) and [project source audit](../project-source-audit.md).
  Yelp is publicly obtainable subject to dataset terms, not unrestricted open data.
