# Baseline fidelity

| Option | What this release actually implements |
|---|---|
| sdpa | Ordinary scaled QK self-attention/retrieval with no added positional mechanism |
| rope | Half-split rotary operator from the existing matched host |
| cope | Existing compact bidirectional adaptation, fractional interpolation, shared learned table |
| tape | Existing compact down-zero position MLP + full head mixing + evolving cos/sin streams |

RoPE is an operator implementation, not a pretrained RoFormer model. CoPE is not
an equation-identical causal CoPE model. TAPE is not the official complete Llama
release. Retaining learned position-state transport does not erase those limits.
The inherited CoPE repeated-byte/source-symmetry and hardware-sensitive argmax
limitations still apply.

The package preserves the native-v4 learned tensors and forward interface
semantics for the three historical backbones; `artifacts/verification/` records
the concrete migration checks. A finite-sample matching check does not prove
equivalence for every device/input/dtype or every original published model.

SDPA uses the same model and native bank, but there is no historical native-v4
SDPA score or checkpoint to import. Eight-mode functional tests are not eight
completed research experiments. Default model initialization need not replay the
legacy discarded-router RNG sequence; historical training trajectory identity
is not claimed.
