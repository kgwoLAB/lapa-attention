# Source attribution and license scope

Project-controlled LAPA code and associated documentation are released under
[Apache-2.0](LICENSE), following the user's explicit license-selection and
publication request on 2026-09-13. This does not transfer ownership or replace
third-party terms. Retained attribution is in [NOTICE](NOTICE), and verified
upstream texts and pinned sources are in [LICENSES](LICENSES/README.md).

This is an extraction/refactoring of an existing research workspace, not a
claim that every implementation was authored from scratch. Original local
source fingerprints remain in [source_hashes.json](docs/lineage/source_hashes.json).

| Component | Source / scope | Distribution treatment |
| --- | --- | --- |
| LAPA routing, address execution and compact model integration | Local research implementation | Project-controlled contributions: Apache-2.0 |
| SDPA | Local scaled dot-product implementation; PyTorch dependency | Project code: Apache-2.0; PyTorch is not vendored |
| RoPE | [RoFormer](https://github.com/ZhuiyiTechnology/roformer) method; local half-split PyTorch operator | Direct copying from RoFormer was not established. Its verified Apache-2.0 text is retained as a reference; TAPE-lineage notices are also preserved |
| TAPE | Compact adaptation of [VITA-Group/TAPE](https://github.com/VITA-Group/TAPE) position path | Upstream MIT copyright plus the Apache-2.0 file-level notice are retained; modified files carry prominent notices |
| CoPE | Local bidirectional equation/Appendix-B adaptation of [Contextual Position Encoding](https://arxiv.org/html/2405.18719v1) | No official Meta repository or software license was verified. No upstream code repository is vendored, and a paper citation is not claimed as a software-license grant |
| PyTorch / PyYAML / Matplotlib | Installed dependencies | Not vendored; their own licenses apply |
| Original traffic, binary windows and weights | Separately retained local research assets | Not distributed or licensed by this release |

## Modification and reproduction boundaries

`src/lapa/attention/rope.py`, `src/lapa/attention/tape.py`, and
`src/lapa/models/transformer.py` retain attribution and modification notices.
The publication step added comments only: executable statements and tensors
were not changed. Consequently, their file hashes differ from pre-publication
frozen package fingerprints; this is not a new model experiment. The backup of
the prior package and original experiment directories remain local-only.

`research_archive/studies/` contains selected historical code, reports, aggregate
results and figures. Its manifest records original/exported hashes and path
substitutions. Historical pass checks certify the original experiment only,
not the present package, a full replay, or third-party legal clearance.

The CoPE method reference establishes the computational source, not blanket
copyright permission for copying its paper listing or any unavailable code.
This release grants rights only to project-controlled expression; externally
owned material remains subject to its owners' rights. Do not describe this
bounded source review as a complete legal audit or a clean-room certification.

## Publication privacy boundary

Raw packet bytes, datasets, checkpoints, per-packet predictions, local reference
and verification bundles, original asset manifests and previous Git history
are excluded from the new public initial snapshot. A private local backup
preserves the original history; no old private remote is modified.

Do not remove legitimate upstream copyright attribution as if it were a secret.
Data or weights require a separate provenance/privacy review before any later
distribution. They must not be force-added to work around the release policy.
