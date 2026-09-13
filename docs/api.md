# Public API

`LapaConfig`: serializable architecture/profile configuration. Unsupported
causal/full-layer/alternative-bank configurations fail rather than silently
changing the method. Partial YAML model dictionaries use dataclass defaults;
there is no implicit Hydra/OmegaConf composition or external framework.

`ModelInputs(data, observed, slots)`:

- `data`: int64 `[B,L]`, values 0..255, original byte values.
- `observed`: bool `[B,L]`, nonempty contiguous prefix and right padding.
- `slots`: int64 `[B]`, fixed ordinal query ID 0..slots-1.

`LapaModel(config)(inputs, attention=None, lapa_enabled=None)` returns a dict:

| Key | Meaning |
|---|---|
| presence_logits | `[B]` field-existence logits |
| source | `[B,L]` source distribution |
| program_logits / program | `[B,L,68]` conditional program scores/probabilities |
| base / final | `[B,L+2]` destination distribution before/after route fusion |
| route | None when off; otherwise prior, sink, bias, execution and latent details |
| tape_position / cope_positions | Optional positional diagnostics |

Index L is END and L+1 is NULL **relative to batch storage length**, not an
individual shorter message. `collate_slots` remaps label indices accordingly.

`Batch` keeps `inputs`, `labels`, and metadata separate. Use `model(batch.inputs)`;
then use `joint_loss(output, batch.labels)`. Labels are rejected by forward.

`LapaAttention` is the final-logit fusion module. It accepts existing per-head
retrieval logits and an optional route log-bias; it is not a generic causal KV
cache implementation or a replacement for a full TAPE backbone.

`load_checkpoint` only accepts the versioned standalone checkpoint schema with
the matching full program-bank fingerprint. Raw native-v4 state dictionaries
require `scripts/convert_checkpoint.py` with explicit attention and on/off mode.
