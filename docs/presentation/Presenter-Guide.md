# Place Lab — presenter guide

[Open the Google Slides deck](https://docs.google.com/presentation/d/1sg0G4LGOqI1nrnQCK6E-p9zHme1tHvJlLT3XWMzv2ME/edit) · [CIS 509 Group folder](https://drive.google.com/drive/folders/1VNB4BIbkiL1KiISKPGbI3SAH_ryArrsc)

Updated October 8, 2026. The current deck has **21 slides: 16 story slides and five supporting slides**.
Supporting slides are currently interleaved at positions 16–17 and 19–21.
The main talk answers two questions: **What problem are we solving? How do we solve it?**
It follows a planner from a need for local evidence through text analysis and historical
comparisons to an explorable tool. The presentation selects evidence that carries this
story; the notebook and appendix hold the technical detail.

The planned story content is **12:55**, including a **1:30 demonstration**. Allow
25 seconds for transitions to target **13:20**. Supporting slides are optional;
these are pacing targets that still need rehearsal.

## Main talk

| Slide | Story and evidence | Target time |
|---|---|---|
| 1 | Place Lab | 0:00–0:20 |
| 2 | Better area data helps identify local needs | 0:20–0:55 |
| 3 | Procurement takes time. Public data can inform decisions earlier. | 0:55–1:45 |
| 4 | Only about 3 in 10 reviews mention the surrounding place | 1:45–2:25 |
| 5 | Join each source at the scale it actually describes | 2:25–3:20 |
| 6 | From historical data to explorable local evidence | 3:20–3:40 |
| 7 | Split the review before deciding what it describes | 3:40–4:45 |
| 8 | BERTopic groups recurring language in place excerpts | 4:45–5:30 |
| 9 | A second topic model checks what the wider text contains | 5:30–6:20 |
| 10 | Validate labels, then compare the rules with BERT | 6:20–7:10 |
| 11 | Turn review counts and scores into area measures | 7:10–8:10 |
| 12 | Compare nearby change with the surrounding trend | 8:10–9:15 |
| 13 | Test the model on entire held-out projects and cities | 9:15–10:15 |
| 14 | Past projects show a mixed picture of review activity | 10:15–10:50 |
| 15 | Sentiment changes were modest across the past projects | 10:50–11:25 |
| 18 | From a planning question to an area worth investigating | 11:25–12:55 |

Use slides 5–13 for the process walkthrough. The [pipeline analysis](Pipeline-Walkthrough.md)
provides the detailed explanation and code links for each stage. State the question,
point to the evidence, and explain what it changes for the planner. Sources, evaluation
details and interpretation boundaries are also in the Google Slides speaker notes.

## Opening and conclusion

**Opening:** Our project hypothesis is that public officials, investment developers and
investors need area-specific data to identify local needs. Place Lab supports this
investigation. Access to additional data and analysis can depend on procurement. Existing
public data can support early investigation, helping officials refine their questions
and narrow the scope of a subsequent request. Place Lab applies that idea to local
conditions and past public projects.

**Solution:** Align historical sources, extract place meaning, compare local changes
with surrounding changes, and make the evidence explorable in Place Lab.

**Conclusion:** Explore before procurement, refine the question and narrow the request.
These are proposed planning uses; deployment benefits and procurement time savings
have not been measured. The historical evidence does not establish causal effects or
support reliable new-project forecasts.

## Live demonstration

Open [Place Lab](https://intreaction.github.io/neighborhood-sentiment-map/place.html)
before presenting. For a local fallback, run `python3 src/serve_place.py --port 8766`
and open `http://127.0.0.1:8766/place.html`.

1. Choose Philadelphia and search for ZIP **19134**. Select the **access** map layer.
2. Show **56 of 1,702 reviews = 3.3% access mentions**, alongside the **49.0% historical
   poverty estimate**. Explain that mentions include praise and complaints; this is a
   question worth investigating, not proof of an access deficit.
3. Choose **Trail / greenway** and **The Rail Park** in the past-project section.
   Compare business engagement with sentiment and open a definition or reliability warning.
4. Return to the opening question: the planner can now choose what to investigate
   through an on-site visit, resident outreach or an accessibility audit.

Keep the demonstration to 1:30. Slide 18 is the screenshot fallback.
Do not debug during the talk. Assistant navigation is optional appendix material,
not a required part of the main demonstration.

## Evidence behind the procurement opening

- [NYC MOCS FY2026 Citywide Indicators Report](https://www.nyc.gov/site/mocs/resources/citywide-indicator-reports.page): median end-to-end cycle times of **282 days** for competitive sealed bids and **527 days** for competitive sealed proposals. These are citywide contract categories, not measured delays specific to data purchases or studies.
- [Federal Data Strategy](https://strategy.data.gov/practices/), practices 1, 4 and 33: identify data needs, use data to guide decisions, and promote open access.
- [FAR 12.202](https://www.acquisition.gov/far/12.202): market research informs the description of need, solicitation and contract. This is federal procurement guidance, not a rule governing NYC.

The proposal that Place Lab can help narrow a later request is our application of
these principles. The sources do not establish a measured time saving for this tool.
Yelp is publicly obtainable under dataset terms; Census data are open government data.

## Evidence behind the main graphs

| Slide | Evidence and interpretation |
|---|---|
| 4 | `data/derived/text_validation/metrics.json`: 61 of 200 randomly sampled reviews mention the place (30.5%; 95% interval approximately 25–37%). Claude Opus labels were checked by human reviewers and found satisfactory, as confirmed by the team. |
| 8 | Seven displayed BERTopic clusters among 413 place excerpts: 84 parking; 22 neighborhood/night; 19 parks/water; 13 walking/distance; 12 streetcar; 9 construction/noise; 9 trash. About one-third are unclustered; displayed clusters are not exhaustive or population prevalence. The text-method sequence is shown separately from the cluster result. |
| 10 | Business-grouped five-fold evaluation on 514 clauses: rules recover 12 of 73 negative area clauses (16.4%); MiniLM plus logistic regression recovers 51 of 73 (69.9%). Classifier precision is 41.8%, and human reviewers have checked the labels and found them satisfactory, as confirmed by the team. This benchmark has not replaced all deployed rule-based measures. |
| 12 | Sun Link nearby reviews: 3,807 before, 10,943 after. Comparison ring: 9,957 before, 34,394 after. Expected nearby count: 3,807 × 34,394 ÷ 9,957 ≈ 13,150; actual is about 17% lower. |
| 14–15 | Current historical project evidence: ten eligible outcomes. Five have positive comparison-adjusted review growth; seven have positive adjusted sentiment change. Every absolute sentiment change is below 0.1. |
| 18 | `web/place-areas.json`: ZIP 19134, 2019–21 reviews; ACS 2007–11 poverty estimate. Historical context describes the area, not the reviewers. |

## Supporting slides

| Position | Content |
|---|---|
| 16 | Uneven review growth across metros |
| 17 | ZIP activity, sentiment and poverty correlations |
| 19 | Sources and AI-use disclosure |
| 20 | NLP methods and course connections |
| 21 | Clause-rule examples and errors |

Use these selectively during the talk or for questions. The current deck order
comes from the live Google Slides presentation; repository documentation does not
restore slides removed in the editor. Reproduction evidence remains in the notebook
and repository even though that slide is no longer in this deck.

## Interpretation boundaries

- Yelp activity is not visits, revenue, public benefit or financial ROI.
- Business-review sentiment is not direct resident satisfaction.
- Historical comparisons do not isolate causal project effects.
- Ten eligible project outcomes remain a small sample despite the review corpus size.
- Humans reviewed the AI-generated labels and found them satisfactory; the BERT benchmark still produces false positives.
- The topic analysis is exploratory; cluster counts do not describe the whole corpus.
- Review and income data are historical; Place Lab cannot describe current conditions.
- The prediction advantage disappears after timing exclusions; the tool does not forecast.

## Rubric coverage and submission

The instructor requests slides and Python notebook files or a GitHub repository link,
with approximately 12–15 minutes recommended. The rubric emphasizes connecting the
business problem, technical approach and insights.

| Rubric category | Where it is communicated |
|---|---|
| Business problem | Slides 2–4 and the planning scenario |
| EDA | Slides 4–5, 14–17 and the notebook |
| Methodology | Slides 5–13, 20–21 and the notebook |
| Results and business insights | Slides 10, 12–15, 18 |
| Presentation and communication | Two-question story, graphs, examples and demonstration; delivery needs rehearsal |
| Code clarity and quality | Submitted notebook/repository and the pipeline walkthrough |

The shared-folder Google Slides deck is the presentation source of truth. Verify
instructor access. Export a PDF or PowerPoint only if the submission system needs one.

## Visual review

The October 6 pipeline revision was read back from Google Slides and rendered for visual
review. It uses the existing Georgia/Nunito Sans typography and cream/forest-green
palette, larger main-slide labels, native editable charts, and fitted product screenshots.
The structural issue checker reported no issues. The 25-slide output was rendered
and inspected, with worked examples and separate stages instead of a flowchart.
All slides were inspected. Embedded UI labels remain small; use the live demonstration
for detail. This edit does not constitute a new pixel-level contrast certification.
