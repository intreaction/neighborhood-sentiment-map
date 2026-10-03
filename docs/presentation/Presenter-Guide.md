# Project overview — presenter guide

[Open the Google Slides deck](https://docs.google.com/presentation/d/1sg0G4LGOqI1nrnQCK6E-p9zHme1tHvJlLT3XWMzv2ME/edit) · [CIS 509 Group folder](https://drive.google.com/drive/folders/1VNB4BIbkiL1KiISKPGbI3SAH_ryArrsc)

The presentation follows the course's Final Project Deliverables – Grading Rubric.
It has 15 slides and a planned duration of 13:05, including a 90-second demo.
The rubric recommends approximately 12–15 minutes. Assign speakers and rehearse;
the timing below is a plan, not a measured delivery.

| Slides | Rubric coverage | Weight |
|---|---|---|
| 2 | Planning problem, intended user, motivation for Yelp | 15% |
| 3–5, 7 | Sources, preparation, coverage, missingness, overlap, text patterns | 10% |
| 5–6, 9 | Geographic design, NLP choices, baseline-only fitting, held-out evaluation | 25% |
| 7–11, 15 | NLP findings, adjusted outcome, model comparison, sensitivity, planning use | 25% |
| Throughout | Clear narrative and visuals; delivery requires rehearsal | 10% |
| 12 plus repository | Notebook, reusable modules, tests and reproducibility limits | 15% |

These are the full project's rubric weights. The presentation communicates the
research across those categories; presentation and communication alone is 10%.
Speaker notes contain method justification and sources. Five NMF topics remain an
exploratory choice, and human text-label validation is unfinished.

| Slide | Topic | Target time |
|---|---|---|
| 1 | Project and team | 0:00–0:30 |
| 2 | Planning problem and research question | 0:30–1:20 |
| 3 | Data sources and scope | 1:20–2:00 |
| 4 | Data preparation and coverage | 2:00–3:00 |
| 5 | Geographic units and time windows | 3:00–3:50 |
| 6 | NLP methods and rationale | 3:50–5:05 |
| 7 | Actual learned topic terms | 5:05–6:05 |
| 8 | Sun Link comparison-adjusted outcome | 6:05–7:05 |
| 9 | Predictive model evaluation | 7:05–8:05 |
| 10 | Timing sensitivity | 8:05–8:55 |
| 11 | Planning implications and next evidence requests | 8:55–10:00 |
| 12 | Notebook, code structure and static data exports | 10:00–10:40 |
| 13 | Map screenshot | 10:40–11:05 |
| 14 | Live demonstration | 11:05–12:35 |
| 15 | Findings and remaining work | 12:35–13:05 |

## Live demonstration

Start `python3 src/serve_place.py --port 8766` before presenting and open
`http://127.0.0.1:8766/place.html`.

1. Choose Philadelphia. Switch between activity and access concerns; explain the
   legend, historical dates and limited-data color.
2. Select ZIP 19123. Distinguish whole-ZIP evidence from the fixed 500 m model sample.
3. Open Budget & proposal, change the budget once, and inspect uncertainty,
   historical evidence and comparable projects. Export the scenario if time permits.

Keep the demo to 90 seconds. Use slide 13 as the fallback if the browser fails. Do not debug during the talk.
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

Checked all 161 visible editable text runs across 15 slides using their Google
Slides text and background colors, with the WCAG relative-luminance calculation.
The chosen target is 4.5:1 for all text, including large text. The final minimum
is 5.24:1. Fixed black slide numbers on the two dark slides (previously 1.81:1),
darkened brown callouts (previously 3.36:1), and strengthened small captions.
The deck was rendered and visually checked, including browser inspection.

This does not certify every pixel of the embedded app screenshot. Its map labels
are small and sit on variable backgrounds; use the live demo for those details.
Reference: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
