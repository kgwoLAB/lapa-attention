# Shared rotary helpers from the local compact RoPE/TAPE lineage.
# Preserved upstream TAPE/models/llama/adape.py attribution:
# Copyright 2022 EleutherAI and the HuggingFace Inc. team. All rights reserved.
# TAPE additions: Copyright (c) 2024 Jiajun Zhu (MIT).
# Apache-2.0 terms and the TAPE MIT notice are retained in LICENSES/.
# Modified for LAPA: compact half-split rotary state and retrieval-length handling.
# This is an operator, not the upstream full model; see THIRD_PARTY_NOTICES.md.
# Publication attribution comments added 2026-09-13; executable code unchanged.
import torch
from .base import AttentionBackend


def rotate_half(value):
    first, second = value.chunk(2, dim=-1)
    return torch.cat((-second, first), dim=-1)


def rope_state(batch, heads, positions, head_dim, dtype, device):
    inverse = 1.0 / (10000.0 ** (torch.arange(0, head_dim, 2, device=device, dtype=torch.float32) / head_dim))
    angle = positions.to(device=device, dtype=torch.float32)[:, None] * inverse[None, :]
    doubled = torch.cat((angle, angle), dim=-1)
    return tuple(x[None, None].expand(batch, heads, -1, -1).to(dtype) for x in (doubled.cos(), doubled.sin()))


class RoPEBackend(AttentionBackend):
    def logits(self, query, key, *, state=None, cope=None, gate_allowed=None):
        if state is None:
            raise ValueError("RoPE/TAPE position state is required")
        cos, sin = state
        if query.shape[-2] == key.shape[-2] == cos.shape[-2]:
            qc, qs, kc, ks = cos, sin, cos, sin
        elif query.shape[-2] == 1 and key.shape[-2] + 1 == cos.shape[-2]:
            qc, qs, kc, ks = cos[:, :, :1], sin[:, :, :1], cos[:, :, 1:], sin[:, :, 1:]
        else:
            raise ValueError("unsupported position/query/key lengths")
        q = query * qc + rotate_half(query) * qs
        k = key * kc + rotate_half(key) * ks
        return super().logits(q, k)
