import torch
from torch import nn
from .base import AttentionBackend


class CoPEPosition(nn.Module):
    """Fractional-position interpolation; bidirectional native-v4 compact port."""
    def __init__(self, head_dim, npos_max):
        super().__init__()
        self.npos_max = npos_max
        self.position = nn.Parameter(torch.zeros(head_dim, npos_max))

    def forward(self, query, gate_logits):
        gates = torch.sigmoid(gate_logits)
        positions = gates.flip(-1).cumsum(dim=-1).flip(-1).clamp(max=self.npos_max - 1)
        lower, upper = positions.floor().long(), positions.ceil().long()
        weight = positions - lower.to(positions.dtype)
        integer = torch.einsum("bhqd,dp->bhqp", query, self.position)
        bias = integer.gather(-1, lower) * (1 - weight) + integer.gather(-1, upper) * weight
        return bias, positions


class CoPEBackend(AttentionBackend):
    def logits(self, query, key, *, state=None, cope=None, gate_allowed=None):
        if cope is None or gate_allowed is None:
            raise ValueError("CoPE requires shared position table and explicit gate mask")
        scores, _ = super().logits(query, key)
        gate_scores = scores.masked_fill(~gate_allowed, torch.finfo(scores.dtype).min)
        bias, positions = cope(query, gate_scores)
        return scores + bias, positions.masked_fill(~gate_allowed, 0)
