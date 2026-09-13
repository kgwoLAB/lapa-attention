from .base import AttentionBackend


class SDPABackend(AttentionBackend):
    """Explicit scaled QK logits for inspectable additive route fusion."""
