# Three-minute demo runbook

> This runbook covers the historical evidence/profile-model demo. For the current ZIP explorer use [Place Lab walkthrough](place-demo-walkthrough.md).

Use the prepared site; do not rebuild the data or models during the presentation.
The demo needs an available Python 3 installation and a browser. It uses only
Python's standard library and the existing `web/` files. No internet, API key,
raw Yelp archive, or analysis-package installation is needed to present.

## Start before the audience arrives

1. In Finder, double-click **`start-demo.command`** at the repository root.
   It opens the Dilworth Park project in the default browser. Keep its Terminal window open.
2. Use a desktop browser window at least 1,280 pixels wide. Close unrelated tabs and
   turn off notifications before presenting.
3. Open **Use as a proposal example →** once to check the proposal loads, then use
   **Explore projects** and select **Dilworth Park · Philadelphia** to reset the starting view.
4. Keep the saved screenshots below available in a separate window as a fallback.

Terminal alternative, from the repository:

```sh
./start-demo.command
```

The launcher resolves its own location, so an absolute path to it also works from
another directory. It binds only to `127.0.0.1`. If port 8765 is occupied, it selects
a free port and prints the actual URL; it does not reuse or kill an existing server.
Use the URL it prints instead of assuming the port number. Press **Control-C** in
that launcher Terminal after the demo to stop only this demo server.

## Exact three-minute route

| Time | Click / action | Say or show |
|---|---|---|
| 0:00–0:25 | Start at **Dilworth Park · Philadelphia**. Point to **Observed capital efficiency** and the nearby/comparison counts. | “We study how online review activity changed near public investments. Dilworth has about **+60.0 growth-adjusted reviews per $1M**. The raw counts and expected count make that calculation inspectable.” |
| 0:25–1:00 | Scroll past **The place being measured** to **Learned patterns in review language**. Open **Text richness, examples & how this was fitted** briefly. | “We extracted over a million reviews. TF-IDF word and phrase features feed five learned NMF topics; these terms and pre/post mixtures are actual model outputs. Topic diversity and lexical measures add structure. These often describe food and service, so we do not relabel them as civic satisfaction.” |
| 1:00–1:55 | Return to the top. Click **Use as a proposal example →**. Change **Reported capital cost · $M** from **55** to **80**, then click **Reset profile**. | “An official can start with a historical example, then use a measured baseline for a proposal. Changing a supported input updates the estimate. This is a fitted association, not the causal return from spending more.” |
| 1:55–2:35 | Point to the error span, **Advanced text was tested**, and timing-sensitivity box. Open **Compare the models tested**. | “We tested rule-based and learned-text challengers with entire projects and cities held out. Advanced text did not beat the simpler baseline, so we kept the baseline. The timing checks also show the model's advantage is fragile.” |
| 2:35–2:50 | Click **Export analysis ↓** once. | “The record preserves inputs, provenance, model version, result, and limitations. This supports evidence review and scenarios; it is not financial ROI or a budget recommendation.” |
| 2:50–3:00, if time | Click **Explore projects** and select **Water Works Park · Tampa**. | “Insufficient baseline support produces a withheld result instead of an unsupported number.” |

This live segment fits inside the thirteen-minute presentation. The preceding slide already explains Sun Link’s raw review growth and negative adjusted CE. Keep JSON import, additional projects, and the area atlas for questions. They are
working features, but they distract from the three-minute story. Historical presets
are demonstrations, not current measurements for a new location.

## If the live demo is interrupted

- **Browser did not open:** paste the exact URL printed in the launcher Terminal.
- **Page no longer loads:** check that the launcher Terminal remains open. Restart
  `start-demo.command` and use its newly printed URL. Do not stop unrelated servers.
- **Browser failure or presentation time is short:** return to the presentation deck and its captured product screens, or show the saved screenshots and continue the
  interpretation above. Screenshots document the validated product, not live results.

Saved, visually checked fallback images:

- [Advanced text — desktop](qa/advanced-text-desktop.png): learned-topic patterns and coverage.
- [Advanced text — mobile](qa/advanced-text-mobile.png): narrow-screen topic presentation.
- [Proposal — mobile](qa/proposal-mobile.png): estimate, historical error span, and limitations.

See [validation notes](qa/validation.md) for the exact browser checks and limits.
The [presenter guide](presentation/Presenter-Guide.md) covers questions and discussion.

## Presenter smoke check

This starts an ephemeral loopback server, fetches all three product pages, and stops
its own server. It never opens a browser:

```sh
./start-demo.command --smoke-test --port 0
```

A successful run prints `PASS: index, project explorer, and proposal page served on loopback.`
This checks delivery; the visual and interaction validation is recorded separately.

Verified CLI behavior: startup from a different working directory; all three product
pages returning HTTP 200 with cache disabled; an occupied preferred port being
skipped; and the original occupied listener still accepting connections afterward.
The smoke checks do not open a browser or alter the site.
