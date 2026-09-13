import torch


def decode(data, observed, width, endian):
    batch, length = data.shape
    result = torch.zeros(batch, length, dtype=torch.long, device=data.device)
    complete = torch.ones_like(observed)
    pos = torch.arange(length, device=data.device)
    for offset in range(width):
        index = pos + offset
        safe = index.clamp_max(length - 1)
        complete = complete & (index < length)[None, :] & observed.index_select(1, safe)
        exponent = width - 1 - offset if endian == "big" else offset
        result = result + data.index_select(1, safe) * (256 ** exponent)
    return result, complete
