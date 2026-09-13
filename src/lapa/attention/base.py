import math
import torch


class AttentionBackend:
    """Parameter-free dispatcher; shared learned CoPE state lives in the encoder."""
    def logits(self, query, key, *, state=None, cope=None, gate_allowed=None):
        return torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(query.shape[-1]), None


def split_heads(value, heads):
    b, length, dim = value.shape
    return value.view(b, length, heads, dim // heads).transpose(1, 2)
