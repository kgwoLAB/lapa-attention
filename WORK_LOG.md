# Local package build log

## 2026-09-08 — scope and extraction

User authorized a new local `lapa-attention/` package and copies of used data.
No GitHub publication or license selection was requested. Original study files
and running experiments are not modified by this build.

Implemented attention backends, shared encoder, 68-program native bank,
deterministic executor, source/program router and retrieval fusion. Preserved
native-v4 state-dict names and separated forward inputs from supervision.

## Data copy

Ran `scripts/import_workspace_data.py --workspace <WORKSPACE>`.
Copied 29 assets, 63,883,311 bytes, with source/destination SHA-256 equality.
Native splits contain 3089/522/74 messages and 12900/3200/347 fields.
Included historical DNS/x86 archives and six first-seed native checkpoints.
All copied paths are listed in `data/manifests/assets.json`.

## Model migration

Ran `scripts/check_workspace_parity.py` against six frozen native-v4 checkpoints,
12 mixed-length positive/absent slot inputs per checkpoint. All compared
presence/source/program/base/final and enabled routing tensors matched with
maximum absolute error 0. Details: `artifacts/verification/native_v4_parity.json`.
This is a finite-sample packaging check, not a new model comparison experiment.

## Portable tests

Ran `python -m unittest discover -s tests -t . -v`: 25 tests passed, including
all eight forward/backward conditions, route conservation, masking, TAPE state
transport, off-mode executor exclusion and checkpoint round trips.

## Final local verification

- Completed all eight conditions with two real-data optimizer updates each using
  `scripts/run_grid.py --steps 2 --output outputs/eight_mode_smoke`.
  These are functional smoke runs, not research performance comparisons.
- Executed the train → checkpoint load → capped evaluation → PNG/SVG/Markdown
  plotting workflow. Inspected the resulting PNG; unavailable protocols stay NA.
- `scripts/verify_assets.py --deep` verified all29 copied asset hashes, disjoint
  native message IDs, and 16,447 annotated field/program/endpoint executions.
- Converted the first-seed TAPE-on raw checkpoint without changing any tensor.
  Re-evaluated all74 messages with its original development threshold0.95:
  protocol macro F1=0.7958925750394945, exactly the original single-seed result.
  Per-protocol F1 also matches. This is not the ten-seed mean.
- Re-ran all25 portable tests after the final core changes: PASS.
- Built `outputs/final_wheels/lapa_attention-0.1.0-py3-none-any.whl` using
  local build dependencies, with no dependency downloads. Installed it to the
  task-owned `outputs/isolated_final` directory rather than modifying an existing
  Python environment. From `/tmp`, all8 modes ran while legacy workspace imports
  were explicitly prohibited. `artifacts/verification/isolated_install.json`.
- Completed README, API/data/reproduction/migration/fidelity docs, contribution
  templates, license-status notice and draft citation metadata.

The local package build is complete. Public redistribution/license/author
metadata remain explicit owner decisions. No GitHub repository, commit or push
was created. No original experiment files or running workers were modified.

After final README updates, built `outputs/release_wheel/` and confirmed all48
packaged Python files match `src/lapa/` byte-for-byte. The eight smoke runs also
share one identical minibatch-stream hash. The preserved x86_train panel loader
was exercised successfully (3000 records); no historical labels were converted
into new native-field training labels.

## 2026-09-08 — initial GitHub push preparation

Following the separate user request to push this package, verified that
the previous private repository (address withheld from this public copy) is empty
and that the current account has write access. Initialized the local `main`
branch and configured that exact URL as `origin`.

Re-ran all 25 portable unit tests successfully and checked staged whitespace.
The existing ignore rules exclude raw datasets, checkpoints, generated outputs,
build products and environment files. Source code, configurations, documentation,
data manifests and reference/verification summaries are included. A scan for
common token and private-key patterns found no matches in these included files.
License selection and dataset redistribution clearance remain pending; repository
visibility and licensing are not changed by this push workflow.

## 2026-09-13 — archive preparation (local only)

The user requested local organization for a future GitHub upload after pausing
LAPA development. This task did not authorize or perform a commit, push,
visibility change, history rewrite, or GitHub server-side archive operation.
The existing `origin` URL remains unchanged.

### Packaging and preservation

- Reorganized README, reproduction/data guidance, contribution and third-party
  notices around an archival research release. Added archive status and the
  publication checklist. Distinguished the initial standalone retrieval model
  from the v18 every-layer four-factor historical implementation, including
  their different loss contracts and limits of the scientific claims.
- Added a curated `research_archive/studies/` snapshot of v16/v17/v18: 209
  manifested files, 28,434,049 bytes; 48/93/68 files by study. It includes source
  snapshots, reports, complete aggregate summaries, figures and tables, not
  raw traffic, weights, per-packet arrays or private run directories.
- Recorded original/exported SHA-256 and transformations in the manifest.
  Replaced 2,359 workstation-path occurrences in derived copies only. All
  three reconstructed summaries equal their path-sanitized originals; numerical
  values were neither dropped nor rounded. Large JSON is losslessly split.
  Of the exported assets, 120 are byte-exact copies, including 15 existing PDFs.
- Left original study directories and `src/lapa/` unchanged. The preliminary
  export layout was retained recoverably in ignored
  `outputs/research_archive_pre_layout/`; it is not an upload candidate.
- Kept all raw data, checkpoints and local validation reports on disk. Removed
  only eight already-tracked local-only reference/verification/manifest files
  from the Git index with `git rm --cached`; all eight still match HEAD bytes.
  Their removals are staged, while the new and edited publication files are not.
  This does not remove those assets from existing Git history.
- Made three examples default to fixed numerical API-smoke inputs, with
  explicit optional `--data` access to local data. These untrained forward
  demonstrations are not synthetic-protocol experiments or accuracy results.
- Added a fail-closed snapshot exporter/verifier, a strict split-JSON reader,
  a current-candidate release checker and regression tests. CI now checks the
  archive hashes and current candidate policy before installing the package.

### Checks actually performed

Using the existing local Python environment and CPU (PyTorch 2.13.0+cu130):

- `PYTHONPATH=src python -m unittest discover -s tests -t . -v`: 72 tests passed.
- Three default examples plus three explicit local-data examples passed.
- `python scripts/prepare_research_archive.py --verify`: all 209 records passed.
  All 194 unique original source hashes and three summary reconstructions also
  matched; manifest-generated records do not pretend to have source files.
- `python scripts/verify_assets.py --output
  outputs/archive_release_20260913/local_assets_check.json`: 29 local asset
  hashes and split checks passed. This run did **not** repeat `--deep` annotation
  execution checks; the September 8 deep-check result above is historical.
- The original v17/v18 frozen package contracts passed without changing
  `src/lapa`; all 738 files in the original v18 final-artifact manifest retained
  their hashes. No experiment was retrained or rescored for this cleanup.
- Built the final wheel offline with `pip wheel --no-deps --no-build-isolation`
  into `outputs/archive_release_20260913/final_wheels/`. All 48 packaged Python
  files equal `src/lapa/`; metadata includes the current README. No raw data,
  weights or research snapshots are bundled into the wheel.
  SHA-256: `229859a2c063749943cf22f43b98b4a303cf288124f0ebfcb31fe976f18a68a3`.
- Installed that wheel without dependencies into the task-owned
  `outputs/archive_release_20260913/final_installed/`. From outside the source
  tree, `scripts/check_installed.py` passed all eight backbone × Off/On modes
  with legacy workspace imports prohibited and explicit approved local data.
  Existing environments and checkpoints were not overwritten.
- Reviewed 48 modern relative document/image links. Fixed one example-summary
  path and stale language implying that a public clone includes raw datasets.
- `python scripts/check_release.py --report`: 319 current tracked/untracked
  nonignored candidate files, no findings; `technical_ready=true` but
  `release_approved=false`. `git diff --check` passed.

### Remaining owner decisions

The license remains pending rights-holder selection. Third-party redistribution,
author/citation details and any public-release approval still need owner review.
The automated scanner is limited to current candidates and heuristic UTF-8
content checks; it is not a full privacy/security audit and does not scan Git
history. The eight index exclusions leave historical copies in old commits.
No local originals were deleted, and no remote publication action was taken.

## 2026-09-13 — licensed, privacy-reviewed publication

The user subsequently requested publication to
`https://github.com/kgwoLAB/lapa-attention.git`, then explicitly asked to select
a license and remove sensitive information. The earlier pending-license and
no-push records above describe the preceding preparation stage, not a refusal
or the current license. The target was verified as empty, public and writable.

- Selected Apache-2.0 for project-controlled contributions. Retained complete,
  upstream-verified TAPE MIT and Apache-2.0 texts, pinned provenance, copyright
  notices and a root NOTICE. CoPE software-license uncertainty is explicitly
  documented; no nonexistent Meta license or clean-room clearance is claimed.
- Added attribution/modification comments to three position-related Python
  files only. All 48 Python modules have identical executable ASTs to the local
  pre-license backup. Original study files were not edited. Frozen historical
  package hashes must not be asserted as hashes of the newly annotated files.
- Removed the previous private-repository address from public documentation.
  The chosen public commit identity uses a GitHub noreply address, not the
  configured personal email. Private Git history must not be a parent of the
  new public initial commit.
- Audited candidate text for credentials, emails, internal IP/MAC addresses,
  local paths and authenticated URLs. Preserved legitimate copyright names,
  method citations, aggregate numerical results and provenance fingerprints.
- Separately inspected all 29 PNG chunk/metadata structures, 29 SVG XML/metadata
  files, and 15 PDFs with 41 pages. PDF text, metadata, string objects and
  decompressed non-image streams had no detected private identifiers; no
  attachments, annotations, forms or active actions were found. PNG metadata
  was generic Matplotlib/dpi; no EXIF or trailing payload. These bounded checks
  are not a guarantee that every possible secret or visual identifier is absent.
- Regenerated archive notices under the selected license; all 209 export hashes
  pass. The exporter still verifies exact reconstruction of all three sanitized
  summaries without numerical rounding/removal. Original figures remain
  byte-identical, and the prior public-export version is backed up locally.
- Strengthened the release checker and its regression tests. All 84 unit tests
  passed; all three default examples passed. The final wheel contains all 48
  source modules and five license/notice files byte-identical to the worktree,
  without raw data or weights. Isolated installation passed all eight modes.
  Wheel SHA-256:
  `fba1e2fc800b19cefe02e2c50ba70c31062021015eaa76cbdac4daa9e44b22e2`.
- Added a CPU-only Torch install step to GitHub CI. Remote CI is checked
  separately from the local test results; no fresh research training is run.

Publication backups and local verification reports are under ignored
`outputs/publication_20260913/`. The original data, checkpoints and former
repository history are retained locally, not deleted or included in the new
public object database. No old remote repository or visibility is changed.
Actual commit/push completion is recorded after remote verification below.

Initial staging also exposed Matplotlib-generated trailing spaces in the 29
unchanged SVG assets. A narrowly scoped `.gitattributes` whitespace exception
preserves their byte-exact archive hashes; source/document whitespace checks
remain enabled. The preserved v17 DATA_LIMITATIONS report also has a narrow
blank-at-EOF exception. No historical asset was edited to suppress these
formatting-only warnings.
