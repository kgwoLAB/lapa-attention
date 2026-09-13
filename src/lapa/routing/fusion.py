import torch


def route_prior(real, support, epsilon):
    real = real * support.to(real.dtype)
    sink = (1 - real.sum(-1)).clamp_min(0)
    uniform = support.to(real.dtype) / support.sum(-1, keepdim=True)
    prior = (1 - epsilon) * (real + sink[:, None] * uniform) + epsilon * uniform
    bias = (prior.clamp_min(1e-30).log() - uniform.clamp_min(1e-30).log()).masked_fill(~support, 0)
    return {"real": real, "sink": sink, "prior": prior, "uniform": uniform, "bias": bias}
