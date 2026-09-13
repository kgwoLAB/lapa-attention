# Upstream license evidence and scope

Verified against the public upstream repositories on 2026-09-13. These license
copies preserve third-party terms; they do not transfer ownership, license
datasets or weights, or assert that every file in this project came from an
upstream repository. The project-wide license applies subject to the component
scope in `../THIRD_PARTY_NOTICES.md`.

## TAPE

- Official repository: <https://github.com/VITA-Group/TAPE>.
- Verified commit: `466d9e61e57dd19e2fe23fcec295ee323561f6fd`.
- Root license: **MIT**, copied verbatim to `TAPE-MIT.txt` from
  <https://github.com/VITA-Group/TAPE/blob/466d9e61e57dd19e2fe23fcec295ee323561f6fd/LICENSE>.
- License Git blob: `1200382a6db3f4d3ac628c9b7981a4b91d4a9ada`.
- Exact root copyright notice: `Copyright (c) 2024 Jiajun Zhu`.

The local ancestor `openAI/codex_phase11_comparators/position_attention.py`
describes `TAPEPositionMLP` as a compact port of VITA-Group `PELayer`. The
upstream implementation is in
<https://github.com/VITA-Group/TAPE/blob/466d9e61e57dd19e2fe23fcec295ee323561f6fd/models/llama/adape.py>.
That file also retains an **Apache-2.0** header and this exact copyright notice:

> Copyright 2022 EleutherAI and the HuggingFace Inc. team. All rights reserved.

Its upstream attribution explains that the code is based on EleutherAI's
GPT-NeoX library and the GPT-NeoX and OPT implementations in the HuggingFace
library, modified for architectural differences in the Meta AI model. This
file-level notice is not replaced by the repository's root MIT license. The
Apache-2.0 terms are included in `RoFormer-Apache-2.0.txt`; they are the same
standard license referenced by the TAPE file header.

The applicable compact local components are `src/lapa/attention/tape.py`, the
shared rotary helpers in `src/lapa/attention/rope.py`, and the TAPE
position-stream transport in `src/lapa/models/transformer.py`. The package is
not a copy of TAPE's full LLaMA model. Local changes include compact module
interfaces, bidirectional support masks, down-projection zero initialization,
full head mixing instead of the upstream literal row-sum transform, and
integration into the local post-LayerNorm host. These files carry attribution
and modification comments. Their publication headers change source bytes,
not executable statements or numerical behavior.

The reviewed TAPE tree has no separate `NOTICE` file. Its README credits BiPE
and LongLoRA; no independent copy of those full codebases, TAPE's arithmetic
submodule, tokenizer, or pretrained weights is included by this notice bundle.

## RoFormer / RoPE method reference

- Official repository: <https://github.com/ZhuiyiTechnology/roformer>.
- Verified commit: `dfc678ad506fc527ba17ead8db23cbe4d947a9b4`.
- License: **Apache-2.0**, copied verbatim to `RoFormer-Apache-2.0.txt` from
  <https://github.com/ZhuiyiTechnology/roformer/blob/dfc678ad506fc527ba17ead8db23cbe4d947a9b4/LICENSE>.
- License Git blob: `d645695673349e3947e8e5ae42332d0ac3164cd7`.
- Method: Su et al., *RoFormer: Enhanced Transformer with Rotary Position
  Embedding*, <https://arxiv.org/abs/2104.09864>.

The local implementation is a small PyTorch rotary operator using a half-split
representation shared with the TAPE lineage. The RoFormer repository shows
interleaved Keras-style pseudocode; this review did not establish a direct copy
from that repository. Its license is retained as verified reference material,
not as a claim that a mathematical method itself is subject to that license.
The reviewed RoFormer tree has no separate `NOTICE` file. The unfilled
copyright fields in its standard license appendix are upstream boilerplate,
not a declaration of this project's copyright holder.

## CoPE method attribution; no guessed repository license

Golovneva et al., *Contextual Position Encoding: Learning to Count What's
Important*, <https://arxiv.org/abs/2405.18719>, describes the equations and
Appendix-B computational pattern followed by the local `ExactCoPE` ancestor.
The compact package uses a shared head-dimension/position table, an `einsum`
projection, fractional-position interpolation, and explicit bidirectional
gate masks; it is not the paper's complete causal model.

The public GitHub API returned HTTP 404 for both `facebookresearch/CoPE` and
`facebookresearch/contextual_position_encoding` during this review. No separate
official CoPE repository software license was verified, so no Meta MIT,
Apache, or other license is fabricated here. The paper's arXiv display license
is not treated as a software license grant. This entry documents the method
and observed local lineage; it does not assert clean-room authorship or legal
clearance for copied paper code.
