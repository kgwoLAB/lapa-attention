from dataclasses import dataclass
import torch
import torch.nn.functional as F


@dataclass(frozen=True)
class LossWeights:
    presence: float = 1.0
    source: float = 1.0
    program: float = 1.0
    endpoint: float = 1.0


def joint_loss(output, labels, weights=None):
    weights = weights or LossWeights()
    pos = labels.present.bool()
    pieces = []
    if pos.any():
        pieces.append(F.softplus(-output["presence_logits"][pos]).mean())
    if (~pos).any():
        pieces.append(F.softplus(output["presence_logits"][~pos]).mean())
    losses = {"presence": torch.stack(pieces).mean()}
    if pos.any():
        sources, programs, targets = labels.sources[pos], labels.programs[pos], labels.targets[pos]
        losses["source"] = -output["source"][pos].gather(1, sources[:, None]).clamp_min(1e-30).log().mean()
        selected = output["program_logits"][pos][torch.arange(len(sources), device=sources.device), sources]
        losses["program"] = F.cross_entropy(selected, programs)
        losses["endpoint"] = -output["final"][pos].gather(1, targets[:, None]).clamp_min(1e-30).log().mean()
    total = sum(getattr(weights, key) * value for key, value in losses.items())
    return total, losses
