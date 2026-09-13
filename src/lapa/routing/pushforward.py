import torch


def pushforward(targets, contributions, length):
    """Stable segmented sum; no nondeterministic CUDA scatter-add."""
    batch = contributions.shape[0]
    offsets = torch.arange(batch, device=targets.device)[:, None, None] * length
    keys = (targets + offsets).reshape(-1)
    values = contributions.reshape(-1)
    order = torch.argsort(keys, stable=True)
    sorted_keys, sorted_values = keys[order], values[order]
    unique, counts = torch.unique_consecutive(sorted_keys, return_counts=True)
    sums = torch.segment_reduce(sorted_values, "sum", lengths=counts)
    return values.new_zeros(batch * length).index_copy(0, unique, sums).view(batch, length)
