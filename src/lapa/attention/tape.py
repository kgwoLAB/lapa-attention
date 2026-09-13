# Compact adaptation of TAPE PELayer through the local position_attention.py.
# Preserved upstream TAPE/models/llama/adape.py attribution:
# Copyright 2022 EleutherAI and the HuggingFace Inc. team. All rights reserved.
# TAPE additions: Copyright (c) 2024 Jiajun Zhu (MIT).
# Apache-2.0 terms and the TAPE MIT notice are retained in LICENSES/.
# Modified for LAPA: compact interfaces, down-zero initialization and full head mix.
# This is not the upstream full model; see THIRD_PARTY_NOTICES.md.
# Publication attribution comments added 2026-09-13; executable code unchanged.
"""Existing paper-intended down-zero/full-head-mix TAPE compact port."""
import torch
from torch import nn
from .rope import RoPEBackend


class TAPEBackend(RoPEBackend):
    """Consumes evolving position streams; encoder performs their transport."""


class PositionHeadTransform(nn.Module):
    def __init__(self, heads):
        super().__init__()
        self.weight = nn.Parameter(torch.zeros(heads, heads))

    def forward(self, value):
        return torch.einsum("bhld,oh->bold", value, self.weight)


class TAPEPositionMLP(nn.Module):
    def __init__(self, dim, heads, position_size):
        super().__init__()
        self.up = nn.Linear(heads, position_size, bias=False)
        self.content = nn.Linear(dim, position_size, bias=False)
        self.down = nn.Linear(position_size, heads, bias=False)
        self.activation = nn.SiLU()
        for layer in (self.up, self.content, self.down):
            nn.init.normal_(layer.weight, mean=0, std=.02)
        nn.init.zeros_(self.down.weight)

    def forward(self, content, position):
        gate = self.activation(self.content(content)).transpose(1, 2).unsqueeze(-1)
        return tuple(torch.einsum("bpld,hp->bhld", torch.einsum("bhld,ph->bpld", x, self.up.weight) * gate, self.down.weight) for x in position)
