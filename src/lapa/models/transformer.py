# TAPE position-stream transport adapted through the local compact model lineage.
# Preserved upstream TAPE/models/llama/adape.py attribution:
# Copyright 2022 EleutherAI and the HuggingFace Inc. team. All rights reserved.
# TAPE additions: Copyright (c) 2024 Jiajun Zhu (MIT).
# Apache-2.0 terms and the TAPE MIT notice are retained in LICENSES/.
# Modified for LAPA: bidirectional support masks and a compact post-LayerNorm host.
# This is not the upstream full model; see THIRD_PARTY_NOTICES.md.
# Publication attribution comments added 2026-09-13; executable code unchanged.
import torch
from torch import nn
from ..attention.base import split_heads
from ..attention.factory import make_attention
from ..attention.masks import masked_softmax
from ..attention.tape import PositionHeadTransform, TAPEPositionMLP


class FeedForward(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.input = nn.Linear(cfg.dim, cfg.ff_dim)
        self.activation = nn.GELU()
        self.output = nn.Linear(cfg.ff_dim, cfg.dim)

    def forward(self, hidden):
        return self.output(self.activation(self.input(hidden)))


class SharedSelfAttention(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.heads = cfg.heads
        self.query = nn.Linear(cfg.dim, cfg.dim)
        self.key = nn.Linear(cfg.dim, cfg.dim)
        self.value = nn.Linear(cfg.dim, cfg.dim)
        self.output = nn.Linear(cfg.dim, cfg.dim)

    def forward(self, hidden, backbone, allowed, gate_allowed, position, cope):
        q, k, v = [split_heads(layer(hidden), self.heads) for layer in (self.query, self.key, self.value)]
        scores, _ = make_attention(backbone).logits(q, k, state=position, cope=cope, gate_allowed=gate_allowed)
        weights = masked_softmax(scores, allowed)
        attended = torch.matmul(weights, v).transpose(1, 2).reshape_as(hidden)
        position_attended = tuple(torch.matmul(weights, stream) for stream in position) if backbone == "tape" else None
        return self.output(attended), position_attended


class EncoderBlock(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.attention = SharedSelfAttention(cfg)
        self.attention_norm = nn.LayerNorm(cfg.dim)
        self.feed_forward = FeedForward(cfg)
        self.output_norm = nn.LayerNorm(cfg.dim)
        self.tape_transform = PositionHeadTransform(cfg.heads)
        self.tape_mlp = TAPEPositionMLP(cfg.dim, cfg.heads, cfg.position_size)

    def forward(self, hidden, backbone, support, allowed, gate_allowed, position, cope):
        attended, position_attended = self.attention(hidden, backbone, allowed, gate_allowed, position, cope)
        hidden = self.attention_norm(hidden + attended) * support.unsqueeze(-1).to(hidden.dtype)
        pmask = support[:, None, :, None].to(hidden.dtype)
        if backbone == "tape":
            position = tuple((old + self.tape_transform(delta)) * pmask for old, delta in zip(position, position_attended))
        ff = self.feed_forward(hidden)
        if backbone == "tape":
            delta = self.tape_mlp(ff, position)
            position = tuple((old + update) * pmask for old, update in zip(position, delta))
        hidden = self.output_norm(hidden + ff) * support.unsqueeze(-1).to(hidden.dtype)
        return hidden, position
