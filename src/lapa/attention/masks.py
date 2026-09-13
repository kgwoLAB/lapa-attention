import torch


def masked_softmax(logits, mask, dim=-1):
    if mask.dtype != torch.bool:
        raise TypeError("boolean mask required")
    safe = logits.masked_fill(~mask, torch.finfo(logits.dtype).min)
    prob = torch.softmax(safe, dim=dim) * mask.to(logits.dtype)
    norm = prob.sum(dim=dim, keepdim=True)
    return torch.where(mask.any(dim=dim, keepdim=True), prob / norm.clamp_min(torch.finfo(prob.dtype).tiny), torch.zeros_like(prob))


def allowed_mask(observed, causal=False):
    allowed = observed[:, None, :, None] & observed[:, None, None, :]
    if causal:
        length = observed.shape[1]
        allowed = allowed & torch.ones(length, length, device=observed.device, dtype=torch.bool).tril()
    return allowed
