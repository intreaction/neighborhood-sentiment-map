# Documentation index

The primary research narrative is the [executed notebook](../output/jupyter-notebook/Project_Research_Walkthrough.ipynb).
The root [README](../README.md) is the installation and execution entry point.

| Reader / question | Start here |
|---|---|
| Instructor: what should I assess? | [Submission guide](SUBMISSION_GUIDE.md), [rubric review](grading-review.md) |
| Researcher: where do measurements come from? | [Data dictionary](data-dictionary.md), [source audit](project-source-audit.md), [NLP method](advanced-text-method.md) |
| Reproducer: how do I obtain source data? | [Data setup](data-setup.md); distinguish prepared-data execution from raw extraction |
| Developer: how does the application work? | [Architecture](architecture.md), [maintenance](maintenance.md), [contributing](../CONTRIBUTING.md) |
| Presenter: how do I demonstrate it? | [Current Place Lab walkthrough](place-demo-walkthrough.md), [13-minute presenter guide](presentation/Presenter-Guide.md) |
| Reviewer: what has actually been tested? | [Current QA record](qa/place-lab.md) |
| Publisher: what may be included? | [Data notices](../DATA_AND_LICENSES.md), [publication audit](publication-audit.md) |

## Current versus historical material

The current interface is the desktop 2D ZIP explorer at `web/place.html`. Historical
project evidence (`projects.html` / `index.html`) and the profile model (`model.html`)
are supporting views. Their [demo runbook](demo-runbook.md) describes that separate
workflow, not the ZIP explorer.

`coursework/` preserves prior course submissions; the [September engagement study](history/engagement-model-study-2026-09.ipynb)
is archived in `history/` and is not the primary current notebook.
`atlas-exploration.md` and `capital-efficiency-benchmark.md` describe earlier
research definitions. Do not combine their coefficients with the current model.

Retired 3D/AR plans, prototype code, old demos and redundant documentation were
removed from the current tree before publication. They remain recoverable from
Git history (before this cleanup, commit `a69bdcb`). The current QA record describes
what was tested; older claims do not establish current device support.

Update active guides when behavior changes. Preserve analytical evidence where
it explains conclusions; use Git history for superseded implementation plans.
