# Project overview — presenter guide

[Open the Google Slides deck](https://docs.google.com/presentation/d/1sg0G4LGOqI1nrnQCK6E-p9zHme1tHvJlLT3XWMzv2ME/edit) · [CIS 509 Group folder](https://drive.google.com/drive/folders/1VNB4BIbkiL1KiISKPGbI3SAH_ryArrsc)

The presentation follows the course's Final Project Deliverables – Grading Rubric.
It has 20 slides and a planned duration of 13:20, including a 60-second demo.
The rubric recommends approximately 12–15 minutes. Assign speakers and rehearse;
the timing below is a plan, not a measured delivery.

| Slides | Rubric coverage | Weight |
|---|---|---|
| 2, 7–11, 18 | Planning problem, focus questions and proposed uses | 15% |
| 3–4, 7–11, 14 | Sources, preparation, coverage and observed patterns | 10% |
| 7–13, 16 | Focus calculations, NLP choices and held-out evaluation | 25% |
| 7–11, 14–18, 20 | Worked ZIP examples, model findings and planning implications | 25% |
| Throughout | Clear narrative and visuals; delivery requires rehearsal | 10% |
| 5 plus repository | Notebook, reusable modules, tests and reproducibility | 15% |

These are the full project's rubric weights. The focus section is the center of
the talk. Notes provide detailed formulas and sources for questions; do not read
them verbatim. Five NMF topics remain exploratory and human label validation is
unfinished. The deck does not imply the heatmaps forecast project effects.

| Slide | Topic | Target time |
|---|---|---|
| 1 | Project and team | 0:00–0:20 |
| 2 | Planning problem | 0:20–1:00 |
| 3 | Data sources | 1:00–1:30 |
| 4 | Preparation and coverage | 1:30–2:10 |
| 5 | Notebook and static exports | 2:10–2:40 |
| 6 | Current map | 2:40–3:05 |
| 7 | Reach active business areas | 3:05–3:50 |
| 8 | Support lower-income areas | 3:50–4:40 |
| 9 | Explore declining activity | 4:40–5:25 |
| 10 | Explore worsening experiences | 5:25–6:20 |
| 11 | Investigate access concerns | 6:20–7:10 |
| 12 | Geographic units | 7:10–7:40 |
| 13 | NLP methods | 7:40–8:35 |
| 14 | Learned topic terms | 8:35–9:10 |
| 15 | Sun Link outcome | 9:10–9:55 |
| 16 | Model evaluation | 9:55–10:40 |
| 17 | Timing sensitivity | 10:40–11:15 |
| 18 | Planning implications | 11:15–11:55 |
| 19 | Demonstration | 11:55–12:55 |
| 20 | Conclusions | 12:55–13:20 |

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

1. Choose Philadelphia. Switch between activity and access concerns; explain the
   legend, historical dates and limited-data color.
2. Select ZIP 19134. Distinguish whole-ZIP evidence from the fixed 500 m model sample.
3. Switch to ZIP 19123 for a supported model example. Open Budget & proposal, change the budget once, and inspect uncertainty,
   historical evidence and comparable projects. Skip export during the timed demo.

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
