# Public-release audit

Audit date: 2026-10-02. **Status: locally prepared for public release; publication not performed.**
GitHub reports `intreaction/neighborhood-sentiment-map` as **PRIVATE**. No visibility
change, push, deployment, deletion of research evidence, or history rewrite was
performed. This describes the audit-time state. The reviewed preparation was subsequently
committed and pushed on October 2; publication/visibility changes were not performed.

## Permission confirmation

On 2026-10-02, the repository owner confirmed that permission is held in response
to the specific question about public release of the review excerpts and
business-level map data. This audit relies on that confirmation; the underlying
agreement was not independently inspected. Retain permission evidence privately.
The research data remains subject to its source terms and is not offered under an
open-data license.

## Findings and disposition

| Priority | Finding | Evidence and disposition |
|---|---|---|
| Resolved by owner confirmation | Source review excerpts are distributed | `data/derived/project_evidence.json` contains 413 excerpt records; `data/derived/advanced_text.json` contains 15 topic excerpts. Generated `web/index.html` and `web/projects.html` embed evidence. Builders can regenerate excerpts. Retained under the owner-confirmed permission. Hashed review keys and excerpt content remain part of the research release, including historical commits. |
| Resolved by owner confirmation | Business-level records are distributed | `web/place-data.json` and `data/derived/place_inputs/baseline_profiles.json` contain 72,575 coordinate/count records, not solely ZIP summaries. Original IDs are absent, but locations remain precise. Retained under the owner-confirmed permission, preserving the point model and reproducible notebook. |
| Owner confirmed; not independently verified | Data agreement/approval | The archive is labeled January 2022. The official agreement examined is dated July 7, 2023; it is not proof of which agreement was accepted. See DATA_AND_LICENSES.md for the source and publication provisions. The owner confirmed permission for the identified public-release scope; keep the underlying agreement/approval privately. |
| Important | History retains prior material | The local refs contain 46 commits and 439 unique file blobs. A clean latest commit does not remove earlier excerpts or machine paths. The data is retained under confirmed permission. Personal machine prefixes in older commits were disclosed in this audit; no credentials matched the focused scan. History rewriting was not required or performed for these prefixes. |
| Important | No project-wide code license selected | Public GitHub access and permission to reuse are different. Contributor agreement is needed before assigning a code license. Third-party data/content must remain excluded from any blanket code license. Public viewing itself does not require selecting an open-source license. |
| Important | Team attribution and older coursework remain | README credits three contributors. Earlier HTML/notebooks, slides and screenshots remain part of the submission history. Team attribution was preserved; the owner requested preparation for public release. The earlier notebook is labeled prior analysis; it is not the current primary notebook. |

The 428 excerpts are record counts, not a claim of 428 unique source reviews.
Removing excerpts requires updating their builders, generated pages, evidence
hash references, model artifacts and notebook outputs together. Simply deleting
JSON keys would break provenance checks. No removal was performed because the owner confirmed permission.
An aggregate-only release also needs a deliberate replacement for business-level
point calculations; rounding coordinates alone does not settle data rights.

## Work completed

- Added `DATA_AND_LICENSES.md` with source-specific rights and attribution notes.
- Corrected README's overly broad statement about raw text: archives are absent,
  but excerpts and business-level records are present elsewhere.
- Added `CONTRIBUTING.md` with data, build and verification practices.
- Strengthened `.gitignore` for environment variants, private keys, local agent
  settings and common review-label files. Ignore rules do not remove tracked files.
- Replaced personal `/Users/.../Documents/...` prefixes with `COURSE_WORKSPACE`
  in five saved artifacts: the prior final notebook and HTML, Milestone 2 notebook
  and provenance JSON, and `web/report.html`. Historical source lineage is retained.
- Added the read-only `scripts/audit_public_repo.py` check. It scans tracked plus
  non-ignored untracked files; `--history` scans unique reachable blobs from local
  refs. Office XML is inspected inside ZIP packages. Matches report locations,
  never credential values.
- Added a read-only-permission CI workflow for the focused scan, Python/JS tests,
  dependency install and UI build. CI subsequently passed on GitHub for commit `a1f26a3`; see [current QA](qa/place-lab.md).
- Made Pages deployment manual to keep publication deliberate. This local workflow
  change does not remove or change any already deployed website.

## Verification evidence and limits

| Check | Result |
|---|---|
| GitHub repository visibility | Private, read via GitHub CLI |
| Focused credentials / forbidden-file scan | Zero findings in the candidate working tree and 439 unique historical blobs |
| Tracked raw archive / raw-data path scan | No matching archive/raw-data paths found in reachable local history |
| npm production dependency audit | Zero known vulnerabilities returned by npm |
| Application regression suite | 63 Python tests and 51 JavaScript tests passed before this documentation/CI preparation |
| Primary notebook and site data | 11 executed code cells; five output hashes verified in the prior validation |
| File sizes | Largest candidate file approximately 3.42 MiB; no large archive required for prepared-data notebook execution |
| Presentation core metadata | Exporter metadata only; no personal machine path found in inspected core properties |

The focused scanner recognizes selected common token and private-key formats. It
is not an exhaustive secret scanner or legal/privacy approval. It does not inspect
remote-only refs, GitHub issues/releases/actions logs, compressed PDF text, image
pixels, arbitrary passwords, all metadata, or every dependency vulnerability.
Python dependency advisory scanning was not performed. The historical scan covers
local refs without fetching additional remote branches. Public-release review
must account for these limits and any permission evidence held outside Git.

## Publication handoff

1. Review and commit the prepared working tree, including the notebook, static
   JSON outputs, source changes and publication documentation. The audit did not
   commit or push existing work.
2. Run `python3 scripts/audit_public_repo.py --history` before future releases;
   inspect any newly introduced datasets and verify permission still covers them.
3. GitHub CI should pass after the changes are pushed. Choose a code license if
   open-source reuse is intended; leaving it unlicensed does not prevent public
   viewing, but does not grant general reuse rights.
4. Change repository visibility only on the owner's explicit publication request.
   Pages deployment is a separate manual action. This audit did not establish
   current public access to any existing Pages deployment.

## Source-data exclusion policy (2026-10-02)

The owner requested that large Yelp/Census source datasets remain outside Git.
Raw archives and intermediate files were already excluded; the policy now also
covers external/download folders, raw Yelp filenames anywhere in the repository,
and Census shapefile downloads. The publication check rejects individual files
over 10 MiB. Compact prepared inputs and static outputs remain versioned so the
notebook and site remain usable. See [data setup](data-setup.md) for acquisition
and reproduction details, including limits of the legacy raw-data bootstrap.
