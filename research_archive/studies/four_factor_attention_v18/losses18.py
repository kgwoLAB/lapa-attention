"""Four objective groups, with explicit width/endian/base factor supervision."""
import torch
from torch.nn import functional as F


def loss(output, labels):
    pos = labels['present'].bool()
    assert pos.any()
    presence_parts = [F.softplus(-output['presence_logits'][pos]).mean()]
    if (~pos).any(): presence_parts.append(F.softplus(output['presence_logits'][~pos]).mean())
    presence = torch.stack(presence_parts).mean()
    source = -output['source'][pos].gather(1,labels['source'][pos,None]).clamp_min(1e-30).log().mean()
    endpoint = -output['final'][pos].gather(1,labels['target'][pos,None]).clamp_min(1e-30).log().mean()
    per_example = []
    rows = torch.arange(int(pos.sum()),device=pos.device)
    for axis in ('width','endian','base'):
        distribution = output[axis][pos][rows,labels['source'][pos]]
        values = -distribution.gather(1,labels[axis][pos,None]).squeeze(-1).clamp_min(1e-30).log()
        # For a single byte, both endians execute identically; marginalize
        # this indistinguishable label instead of inventing a distinction.
        if axis == 'endian': values = values*(labels['width'][pos]!=0)
        per_example.append(values)
    attributes = sum(per_example).mean()
    parts = dict(presence=presence,source=source,attributes=attributes,endpoint=endpoint)
    return sum(parts.values()),parts
