from torch import nn


class SpecialEndpoints(nn.Linear):
    """Two task-head logits per head: END and NULL; not neutral sink."""
    def __init__(self, dim, heads):
        super().__init__(dim, heads * 2)
