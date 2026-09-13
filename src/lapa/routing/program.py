from torch import nn


def make_axis_heads(dim, bank):
    return nn.ModuleDict({a: nn.Linear(dim, len(v)) for a, v in bank.axis_vocabulary().items()})


def program_logits(hidden, bank, heads, axis_ids):
    logits = hidden.new_zeros(*hidden.shape[:2], len(bank))
    for axis in bank.axis_names:
        logits = logits + heads[axis](hidden).index_select(-1, axis_ids[axis])
    return logits
