# Place Lab: current five-minute desktop walkthrough

Current workflow reviewed October 2, 2026. Start the server with
`python3 src/serve_place.py --port 8766`, then open the printed URL. Use
[the presenter guide](presentation/Presenter-Guide.md) for the full course talk.

1. **Question and geography (45 seconds).** Start in Philadelphia, ZIP 19123.
   Explain that the highlighted ZIP is the area being investigated. The map is
   two-dimensional; drag to pan and use zoom controls for detail. City view fits
   the city; Selected ZIP fits the chosen boundary. There is no project marker.
2. **Focus evidence (60 seconds).** Use Your focus near the top of the left panel.
   Compare activity, lower-income areas, declining activity, worsening experiences,
   and access concerns. Read the unit and period shown for each measure. Access
   counts include positive and negative mentions. Gray means limited data.
3. **Separate ZIP evidence from the model (60 seconds).** Read the large data
   value and the ZIP listing count. Explain that the model below uses a separate
   fixed 500 m reference sample, not the entire ZIP. Selecting another ZIP changes
   the highlighted area and sample; it does not estimate ZIP-wide benefits.
4. **Explore assumptions (60 seconds).** Expand Budget & proposal, change $25M to
   $50M, then restore $25M. A fitted association can change with budget; it is not
   the causal return from spending. Type affects comparable cases, not the fitted
   estimate. Unsupported inputs withhold the estimate while area evidence remains.
5. **Follow the evidence (60 seconds).** Open the full analysis below the map.
   Show historical activity, topic changes and model validation. Use the notebook
   to explain the static JSON export and distinguish saved NLP results from the
   baseline refitted during notebook execution.
6. **Close (15 seconds).** Name the next evidence needed: local investigation,
   independent labels and broader project coverage. Do not recommend a budget
   or project type from this model alone.

Map settings offers online street tiles or bundled offline ZIP boundaries. The
panel can collapse to reveal more of the map. Keep the test/demo browser on a
supported desktop viewport and rehearse before presenting. Numeric values should
be read from the current data; earlier Rail Park point values are not the same
as this ZIP reference point.
