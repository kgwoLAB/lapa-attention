from torch import nn
from ..attention.masks import masked_softmax


class LapaAttention(nn.Module):
    """Fuse a route density ratio into already computed backbone logits.

    This retrieval operator returns distributions, not fictitious values for
    END/NULL. The encoder's ordinary self-attention has its own V tensors.
    """
    def forward(self, logits, support, route_bias=None, strength=1.0):
        base = masked_softmax(logits, support[:, None, :]).mean(1)
        if route_bias is None or strength == 0:
            return base, base
        final = masked_softmax(logits + strength * route_bias[:, None, :], support[:, None, :]).mean(1)
        return base, final
