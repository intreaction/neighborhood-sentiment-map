# Maintenance and troubleshooting

Run commands from the repository root. Follow [README](../README.md) to create a
Python 3.12 environment and install pinned requirements. Use that environment's
`python`/`jupyter`; do not assume a sibling course environment exists.

## Choose the correct rebuild

| Change | Required action |
|---|---|
| ZIP formulas or prepared evidence | Run the primary notebook; inspect exported CSVs and all five JSON files/manifests |
| Raw archive/extraction | Follow [data setup](data-setup.md); regenerate dependent evidence/model/text artifacts and refresh prepared snapshots before running the notebook |
| HTML or map CSS | `python src/build_place_site.py` |
| Browser JS or chart styling | `npm ci` then `npm run build:place` |
| Documentation only | Check links, commands and current/historical status; no data rebuild needed |

Do not bypass a hash mismatch by editing a hash to match an unexplained file.
Trace the changed source and rebuild its dependents. Keep the primary notebook's
saved outputs, CSV exports, JSON outputs and manifest in the same reviewed change.
CSV bytes are preserved by `.gitattributes` because input hashes cover exact bytes.
Cross-platform scientific calculations may differ at numerical roundoff scale;
tests use strict float tolerances while counts, structure and hashes stay exact.

## Verify

```sh
python scripts/audit_public_repo.py
python scripts/check_docs.py
python -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.cjs tests/*.test.mjs
```

The document checker checks local inline Markdown file targets in active guides;
it does not verify external URLs, heading anchors, HTML or notebook links.
For publication, also run the audit with `--history`. Source archives and files
over 10 MiB must remain out of Git. One raw-corpus-dependent Python test is skipped
on a fresh checkout without that corpus; this is not a full NLP retraining check.
CI installs dependencies and runs the checks/build on Linux.

For an interface change, launch `python src/serve_place.py --port 8766` and follow
[the walkthrough](place-demo-walkthrough.md). Verify a city/ZIP change, each affected
focus, budget edits and support messages. Check the browser console and visually
inspect the map. Desktop is the current design target; no mobile/AR certification
is implied. Commit generated web assets with their source changes.

## Common issues

| Symptom | Check / resolution |
|---|---|
| Blank page or missing JSON | Serve `web/` through the provided HTTP server. Confirm notebook exports exist and inspect failed asset requests. |
| Input hash mismatch | Find the intended upstream change; refresh snapshots explicitly, then rerun the notebook. Do not hand-edit manifests. |
| Model/evidence versions disagree | Rebuild text/model artifacts against the same evidence before exporting. |
| Estimate withheld | Read the support explanation. ZIP evidence can still be shown; do not force a numerical prediction. |
| Gray heatmap area | A required measure is missing or below its review threshold. Zero and missing are different. |
| Street tiles fail | Select **ZIP boundaries · offline** under map settings. Network tiles are optional. |
| Port 8766 is occupied | Use the URL printed by the launcher, which selects a free port. |
| Notebook kernel cannot start | Select the installed project kernel. Sandboxed runners must permit local kernel communication. |

## Release

Review the exact commit, CI result, data permission and instructor access. Pushes
do not deploy Pages automatically; `.github/workflows/pages.yml` is manually
triggered. Repository visibility and Pages deployment are separate decisions.
Never use production deployment as a substitute for checking a local build.
