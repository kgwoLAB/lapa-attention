# Standalone package implementation checklist

- [x] Inspect native-v4 host, router, executor, source closures and data paths.
- [x] Create modular SDPA/RoPE/CoPE/TAPE + LAPA core.
- [x] Separate public inputs from labels; preserve native-v4 checkpoint names.
- [x] Implement training/evaluation/config/example entry points.
- [x] Copy exact native and historical address datasets with SHA-256 manifests.
- [x] Finish documentation, notices, collaboration templates and plotting CLI.
- [x] Check original native-v4 checkpoints against migrated model outputs.
- [x] Execute eight-mode forward/backward, masks, routing and checkpoint tests.
- [x] Execute packaged data train/evaluate/plot smoke workflow.
- [x] Check operation outside the original workspace import path.

Local implementation was completed in the original build. Historical evidence
is retained locally in Git-ignored `artifacts/verification/BUILD_REPORT.md`.
Current archival preparation has a separate [release checklist](docs/release_checklist.md)
and [work log](WORK_LOG.md); the checked items above are not new publication checks.

## Before public release — user/rights-holder decisions, not implemented claims

- [x] Select Apache-2.0 for project-owned code and preserve verified upstream notices.
- [ ] Approve dataset/checkpoint redistribution and privacy scope.
- [ ] Supply and approve authors and manuscript metadata for CITATION.cff.
- [x] User authorized a sanitized initial commit/push to the specified public repository.

Publication uses a new sanitized history; the previous private history remains
local-only. See the current release checklist and work log for actual push status.
