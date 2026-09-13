from torch import nn
from ..attention.masks import masked_softmax


class SourceLocator(nn.Linear):
    def __init__(self, dim):
        super().__init__(dim, 1)

    def probabilities(self, hidden, observed):
        logits = self(hidden).squeeze(-1)
        return logits, masked_softmax(logits, observed)
