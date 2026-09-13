"""Attention-free, shared-ordinal locators for the v17 formula search.

This is an isolated research implementation, not a replacement for LAPA's
released ByteEncoder.  The public ordinal slot remains an input, but there is
no independently learned embedding per slot.  One MLP maps analytic ordinal
features to a query vector for every slot.  Neither locator uses a Q/K/V
projection, an attention distribution, a protocol ID, a field count, or gold
field attributes.  The native byte embedding, layer norms, task vector and
router are reused; all other native encoder/retrieval modules are omitted.

``make_encoder(native_host, cfg, kind)(inputs)`` returns ``[B, L + 1, D]``:
the first token is a pooled task representation and the rest represent bytes.
Observed masks must describe a nonempty contiguous prefix, as in LAPA's
public ModelInputs contract.  Positions and slots are normalized by observed
message length or fixed configuration constants, never padded batch length.
"""

import math

import torch
from torch import nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence


KINDS = ("cnn_shared", "recurrent_shared")


class SharedSlotQuery(nn.Module):
    """A shared smooth query function, rather than a trainable slot-ID table.

    Features are normalized ordinal, normalized log ordinal, and sine/cosine
    at four fixed frequencies.  The normalization uses cfg.slots, not the
    number of annotated fields or the largest slot encountered in training.
    No clipping or remapping to observed training slots is performed.
    """

    feature_count = 10

    def __init__(self, cfg):
        super().__init__()
        self.slot_scale = float(max(cfg.slots - 1, 1))
        self.slot_period = float(max(cfg.slots, 1))
        self.mlp = nn.Sequential(
            nn.Linear(self.feature_count, cfg.dim),
            nn.GELU(),
            nn.Linear(cfg.dim, cfg.dim),
        )

    def features(self, slots, dtype):
        ordinal = slots.to(dtype)
        linear = ordinal / self.slot_scale
        logarithmic = torch.log1p(ordinal) / math.log1p(self.slot_scale)
        frequencies = torch.tensor((1.0, 2.0, 4.0, 8.0), device=slots.device, dtype=dtype)
        phase = ordinal[:, None] * frequencies[None] * (2.0 * math.pi / self.slot_period)
        return torch.cat((linear[:, None], logarithmic[:, None], phase.sin(), phase.cos()), -1)

    def forward(self, slots):
        return self.mlp(self.features(slots, self.mlp[0].weight.dtype))


class MaskedConvBlock(nn.Module):
    """Dilated depthwise mixing with masked per-token residual updates."""

    def __init__(self, dim, ff_dim, dilation):
        super().__init__()
        self.depthwise = nn.Conv1d(dim, dim, 3, padding=dilation, dilation=dilation, groups=dim)
        self.channel = nn.Linear(dim, dim)
        self.norm = nn.LayerNorm(dim)
        self.ff = nn.Sequential(nn.Linear(dim, ff_dim), nn.GELU(), nn.Linear(ff_dim, dim))
        self.ff_norm = nn.LayerNorm(dim)

    def forward(self, hidden, observed):
        mask = observed.unsqueeze(-1).to(hidden.dtype)
        mixed = self.depthwise((hidden * mask).transpose(1, 2)).transpose(1, 2)
        hidden = self.norm(hidden + self.channel(F.gelu(mixed))) * mask
        return self.ff_norm(hidden + self.ff(hidden)) * mask


class SharedOrdinalEncoder(nn.Module):
    """Common raw-byte and shared-slot conditioning for attention-free models."""

    def __init__(self, native_host, cfg):
        super().__init__()
        self.cfg = cfg
        for name in ("byte_embedding", "embedding_norm", "readout", "router"):
            setattr(self, name, getattr(native_host, name))
        self.task_query = native_host.task_query
        self.slot_query = SharedSlotQuery(cfg)
        self.position_projection = nn.Linear(8, cfg.dim, bias=False)
        self.slot_projection = nn.Linear(cfg.dim, cfg.dim, bias=False)
        self.task_readout = nn.Sequential(
            nn.Linear(2 * cfg.dim, cfg.dim), nn.GELU(), nn.LayerNorm(cfg.dim)
        )

    def _inputs(self, inputs):
        data, observed = inputs.data, inputs.observed
        token_ids = torch.where(observed, data, torch.full_like(data, 256))
        embedded = self.byte_embedding(token_ids)
        mask = observed.unsqueeze(-1).to(embedded.dtype)
        lengths = observed.sum(-1, keepdim=True).to(embedded.dtype)
        # clamp_min protects arithmetic; callers retain the nonempty-prefix
        # input contract and GRU checks it explicitly before packing.
        safe_lengths = lengths.clamp_min(1)
        pos = torch.arange(data.shape[1], device=data.device, dtype=embedded.dtype)[None].expand_as(data)
        log_length = (torch.log1p(lengths) / math.log1p(self.cfg.max_length)).expand_as(pos)
        features = torch.stack(
            (
                pos / self.cfg.max_length,
                pos / safe_lengths,
                (lengths - pos) / safe_lengths,
                log_length,
                torch.sin(pos * (2 * math.pi / 16)),
                torch.cos(pos * (2 * math.pi / 16)),
                torch.sin(pos * (2 * math.pi / 64)),
                torch.cos(pos * (2 * math.pi / 64)),
            ),
            -1,
        )
        query = self.task_query[None] + self.slot_query(inputs.slots)
        raw = F.gelu(
            self.embedding_norm(embedded + self.position_projection(features) + self.slot_projection(query)[:, None])
        ) * mask
        return raw, query, safe_lengths, mask

    def _output(self, raw, query, lengths, mask):
        raw = self.readout(raw) * mask
        pooled = raw.sum(1) / lengths
        task = self.task_readout(torch.cat((query, pooled), -1))
        return torch.cat((task[:, None], raw), 1)

    def parameter_counts(self):
        """Explicit counts; router is retained but called by the outer model."""
        router_ids = {id(p) for p in self.router.parameters()}
        encoder = sum(p.numel() for p in self.parameters() if id(p) not in router_ids)
        router = sum(p.numel() for p in self.router.parameters())
        return {
            "encoder_excluding_router": encoder,
            "retained_router": router,
            "total": encoder + router,
            "slot_query": sum(p.numel() for p in self.slot_query.parameters()),
            "independent_slot_embeddings": 0,
        }


class SharedCNNEncoder(SharedOrdinalEncoder):
    """Three masked dilated blocks; no convolution crosses a padding boundary."""

    kind = "cnn_shared"

    def __init__(self, native_host, cfg):
        super().__init__(native_host, cfg)
        self.blocks = nn.ModuleList([MaskedConvBlock(cfg.dim, cfg.ff_dim, d) for d in (1, 2, 4)])

    def forward(self, inputs):
        raw, query, lengths, mask = self._inputs(inputs)
        for block in self.blocks:
            raw = block(raw, inputs.observed)
        return self._output(raw, query, lengths, mask)


class SharedRecurrentEncoder(SharedOrdinalEncoder):
    """Bidirectional GRU; packed sequences prevent reading right padding.

    There are cfg.layers recurrent layers with dropout disabled, matching the
    deterministic native encoder setup.  Unlike a causal deployment model,
    this sees both directions of the observed message, just as the native
    bidirectional Transformer does.  It does not attend over tokens.
    """

    kind = "recurrent_shared"

    def __init__(self, native_host, cfg):
        super().__init__(native_host, cfg)
        hidden_size = (cfg.dim + 1) // 2
        self.recurrent = nn.GRU(
            cfg.dim, hidden_size, num_layers=cfg.layers, batch_first=True, bidirectional=True, dropout=0.0
        )
        self.recurrent_projection = (
            nn.Identity() if 2 * hidden_size == cfg.dim else nn.Linear(2 * hidden_size, cfg.dim)
        )
        self.recurrent_norm = nn.LayerNorm(cfg.dim)
        self.ff = nn.Sequential(nn.Linear(cfg.dim, cfg.ff_dim), nn.GELU(), nn.Linear(cfg.ff_dim, cfg.dim))
        self.ff_norm = nn.LayerNorm(cfg.dim)

    def forward(self, inputs):
        raw, query, lengths, mask = self._inputs(inputs)
        sequence_lengths = inputs.observed.sum(-1).to(device="cpu", dtype=torch.long)
        if bool((sequence_lengths < 1).any()):
            raise ValueError("recurrent_shared requires at least one observed byte per message")
        packed = pack_padded_sequence(raw, sequence_lengths, batch_first=True, enforce_sorted=False)
        packed_output, _ = self.recurrent(packed)
        recurrent, _ = pad_packed_sequence(packed_output, batch_first=True, total_length=raw.shape[1])
        raw = self.recurrent_norm(raw + self.recurrent_projection(recurrent)) * mask
        raw = self.ff_norm(raw + self.ff(raw)) * mask
        return self._output(raw, query, lengths, mask)


def make_encoder(native_host, cfg, kind):
    """Build an attention-free shared-ordinal encoder without changing host.

    Reused modules are shared by reference; callers normally replace their
    native host with the result.  Do not optimize both hosts independently.
    The encoder keeps ``.router`` for the outer LAPA route computation.
    """
    if kind == "cnn_shared":
        return SharedCNNEncoder(native_host, cfg)
    if kind == "recurrent_shared":
        return SharedRecurrentEncoder(native_host, cfg)
    raise ValueError(f"unknown shared-ordinal encoder {kind!r}; expected one of {KINDS}")
