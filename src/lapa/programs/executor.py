"""Parameter-free native-v4 execution. END/NULL are distinct from neutral sink."""
import torch
from .schema import BASES
from .decode import decode
from ..types import Execution


def execute(bank, data, observed):
    batch, length = data.shape
    lengths = observed.sum(-1)[:, None, None]
    cache = {(p.width, p.endian): None for p in bank.programs}
    for w, e in cache:
        cache[w, e] = decode(data, observed, w, e)
    raw = torch.stack([cache[p.width, p.endian][0] for p in bank.programs], -1)
    complete = torch.stack([cache[p.width, p.endian][1] for p in bank.programs], -1)
    def vector(fn):
        return torch.tensor([fn(p) for p in bank.programs], dtype=torch.long, device=data.device)[None, None, :]
    width = vector(lambda p: p.width)
    base = vector(lambda p: BASES.index(p.base))
    value = (raw & vector(lambda p: p.mask if p.mask is not None else -1)) >> vector(lambda p: p.shift)
    span = vector(lambda p: 1 << (8 * p.width))
    value = torch.where(vector(lambda p: int(p.signed)).bool() & (value >= span // 2), value - span, value)
    value = value * vector(lambda p: p.scale) + vector(lambda p: p.bias)
    pos = torch.arange(length, device=data.device)[None, :, None]
    companion_pos = pos + torch.where(base == 4, -width, torch.where(base == 5, width, 0))
    inside = (companion_pos >= 0) & (companion_pos < length)
    index = companion_pos.clamp(0, length - 1).expand(batch, -1, -1)
    companion = raw.gather(1, index)
    companion_complete = complete.gather(1, index) & inside
    complete = complete & ((base < 4) | companion_complete)
    null = ((base == 4) & (value == 0)) | ((base == 5) & (companion == 0))
    target = torch.where(base == 0, value, torch.where(base == 1, pos + width + value,
             torch.where(base == 2, pos - value, torch.where(base == 3, pos + value,
             torch.where(base == 4, companion + value, value)))))
    guard_ok = (raw & vector(lambda p: p.guard_mask)) == vector(lambda p: p.guard_value)
    exclusive_end = ((base == 1) & ~vector(lambda p: int(p.signed)).bool()) | (base == 4)
    valid = complete & guard_ok & (null | ((target >= 0) & ((target < lengths) | (exclusive_end & (target == lengths)))))
    output = torch.where(null, torch.full_like(target, length + 1), torch.where(target == lengths, torch.full_like(target, length), target))
    output = torch.where(valid, output, torch.zeros_like(output))
    return Execution(output, valid, observed[:, :, None].expand_as(valid), value, null & valid)
