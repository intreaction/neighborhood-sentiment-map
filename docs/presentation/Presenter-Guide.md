# Public Investment Evidence: presenter guide

Working format: a thirteen-minute course presentation, including a three-minute live demo,
with three appendix slides for questions. Audience and timing can be revised when
confirmed. The presentation uses the site's cream/green visual style and current
project artifacts, rather than the archived coursework calculations.

## Goal and key points

**Goal:** show how a public official can inspect historical project evidence and
explore a proposed project using measured local conditions, with the uncertainty
visible alongside the estimate.

**Opening thesis:** “We turn historical public investments and unstructured Yelp
reviews into inspectable evidence, then let an official test a proposed project
using an explicitly experimental capital-efficiency estimate.”

The audience should remember four points:

1. **This is a connected product.** The historical explorer explains each project;
   the proposal tool turns local baseline measurements into an inspectable scenario.
2. **Unstructured data is central.** Target-aware sentiment and topic rules identify
   candidate place issues. TF-IDF word/phrase features and NMF reveal learned themes,
   with topic diversity and lexical features providing additional structure.
3. **The measure is specific and traceable.** Capital efficiency means adjusted
   Yelp reviews per $1M of reported project cost. Raw counts and a farther-area
   growth comparison explain the result.
4. **The evaluation is part of the contribution.** Advanced text did not improve
   forecast accuracy on ten project outcomes. We show that result, retain the
   simpler default, and expose timing sensitivity and unsupported inputs.

**Closing ask:** pilot the workflow with one public official and a documented local
proposal. Use the pilot to identify evidence gaps, then expand project coverage and
independent validation before relying on the forecast for budget decisions.

## Timing and emphasis

| Slide | Time | Purpose |
|---|---|---|
| 1. Public Investment Evidence | 0:00–0:45 | Establish the question and product |
| 2. Goal | 0:45–1:45 | Name the planning decision and limits of the proxy |
| 3. Data coverage | 1:45–3:00 | Explain cleaning, missingness and why reviews are not independent project outcomes |
| 4. Place-specific text | 3:00–4:15 | Explain sentiment, topic and target; distinguish an example from validation |
| 5. Learned topics | 4:15–5:30 | Explain TF-IDF/NMF, frozen baseline topics and food/service dominance |
| 6. Sun Link | 5:30–6:30 | Explain raw growth versus comparison-adjusted activity |
| 7. Model comparison | 6:30–7:45 | Explain both holdouts, shared-review exclusion and the negative NLP result |
| 8. Live demo | 7:45–10:45 | Demonstrate historical evidence and a ZIP-level exploration |
| 9. Evidence limits | 10:45–12:00 | Explain sensitivity and what additional evidence a decision needs |
| 10. Closing | 12:00–13:00 | State present value and the next validation steps |
| 11–13. Appendix | Questions only | Model details and browser-failure fallback |

The rubric recommends approximately 12–15 minutes. This is a rehearsal plan,
not a measured delivery time. Rehearse with a timer and adjust to actual speakers.

For three presenters, a natural handoff is slides 1–4, slides 5–7, and the live demo
plus closing. Assign names during rehearsal. One person should operate the browser
throughout the demo.

## Three-minute live demo

Use [the historical demo runbook](../demo-runbook.md) for the evidence view.
For the current ZIP interface, start `python3 src/serve_place.py --port 8766` and
open `/place.html`. Keep the server running. The ZIP demo supplements the older
proposal screenshot already embedded in slide 8; it is not pictured in that slide.

- First minute: show Dilworth Park's historical outcome and learned terms. Explain
  that food/service topics are not automatically civic satisfaction.
- Second minute: open Place Lab, select Philadelphia ZIP 19123, and switch focus
  from activity to access. Explain the actual units and that mentions include
  praise and complaints. Use the map to form a question for local investigation.
- Third minute: open budget/proposal controls and show the fixed 500 m model
  sample, historical error range and support rules. Separate ZIP evidence from a
  project benefit forecast. Close with the notebook and its static-data export.

Avoid new imports or arbitrary locations during the live demo. Rehearse the values
against the committed dataset before presenting. The following historical-model
values remain useful if the team chooses the older scenario flow instead.

Recorded values to rehearse:

- Dilworth historical observed CE: **+60.0 reviews/$1M**.
- Dilworth fitted historical profile at $55M: **+56.7 reviews/$1M**.
- Same profile at $80M: **+53.2 reviews/$1M**.
- Water Works: **seven baseline-reviewed businesses**, so its estimate is withheld.

Observed outcomes and fitted predictions are different numbers. Increasing cost
in the form changes a fitted association; it does not measure the causal return
from spending more.

If the browser fails, stop after 15 seconds and use slide 8's proposal capture and
slide 12's learned-topic capture. Continue the explanation rather than debug live.

## Anticipated questions

**Why call this capital efficiency?**  
We define a narrow engagement-per-cost proxy so projects can be compared on one
measure. It does not capture financial returns or comprehensive civic value.

**Does Yelp represent residents?**  
It represents participating reviewers and listed businesses in a historical archive.
We do not infer residency or treat these reviews as a representative public survey.

**What makes the text analysis advanced?**  
We learn an 8,000-term TF-IDF vocabulary of unigrams and bigrams and five NMF topics.
Topic mixtures, normalized entropy and lexical features become measurable dimensions.
For predictive evaluation, vocabulary, IDF and topics are refitted inside each fold.

**Why keep advanced text if prediction did not improve?**  
It exposes what people discuss, separates business language from place evidence,
and produces a reproducible modeling comparison. More reviews do not create more
independent project outcomes. The negative result is informative.

**How do you prevent leakage?**  
Only baseline conditions enter the predictor. Each held-out fold learns the text
representation from training reviews and excludes reviews shared with held-out
projects. All 17 folds have zero held-out review-ID overlap in text training. Two
folds need training-only mean imputation after strict overlap exclusions. Predictive
and descriptive topic bases have different identifiers.

**Can an official choose a project type and estimate its effect?**  
Type currently filters comparable evidence. The fitted model uses local baseline
conditions and cost, and does not identify a type-specific effect. Broader project
coverage is needed before making that stronger claim.

**Why use a simpler default?**  
On the same ten outcomes, city-held-out MAE is 45.61 for the baseline and 46.67 for
learned text. Both project- and city-held-out tests must improve before replacing
the baseline. None of the challengers met that test.

**Is the baseline ready to recommend a budget?**  
No. Its advantage over a mean predictor disappears after timing exclusions. The
historical error envelope is wide, geography includes five proxies, and costs have
mixed nominal scope. The working value is evidence inspection and scenario analysis.

**How would you improve it next?**  
Acquire more projects and current local data, verify phase-specific footprints and
costs, obtain independent human labels for the place signals, and evaluate on new
projects outside model selection. Pilot the workflow alongside this work.

## Claims to avoid

- “We trained the CE model on a million independent examples.” The model has ten
  project outcomes; a million reviews support the text and activity measurements.
- “Negative CE means the project failed.” Sun Link grew in raw review volume while
  trailing its farther-area comparison.
- “The topic model measures civic satisfaction.” Its learned terms often concern
  food and service. Topic weights are mixtures, not literal mention shares.
- “The error span is a 95% confidence interval.” It is a historical error envelope.
- “Advanced NLP improved our forecast.” It did not improve the two held-out checks.
- “We verified classifier accuracy.” Human accuracy evaluation remains pending.

## Files and evidence

- [Editable presentation](Public-Investment-Evidence.pptx)
- [PDF viewing copy](../../output/pdf/Public-Investment-Evidence.pdf)
- [Demo runbook](../demo-runbook.md)
- [Advanced text methods](../advanced-text-method.md)
- [Source audit](../project-source-audit.md)
- [Browser validation](../qa/validation.md)

Slides include source paths in their notes. The source of truth is the current
`data/derived/project_evidence.json`, `advanced_text.json` and `project_model.json`.
The presentation does not claim that the archived coursework report uses these
new outcomes or methods.
