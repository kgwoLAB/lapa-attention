import torch
from lapa import LapaConfig, LapaModel, ModelInputs, Supervision

torch.set_num_threads(1)


def setup(attention="rope", enabled=True):
    torch.manual_seed(19)
    cfg = LapaConfig(attention=attention, lapa_enabled=enabled, dim=16, heads=2, layers=1, ff_dim=32, max_length=64, slots=8)
    model = LapaModel(cfg)
    data = torch.arange(24).repeat(2, 1).long()
    observed = torch.ones_like(data, dtype=torch.bool)
    observed[1, 16:] = False
    inputs = ModelInputs(data, observed, torch.tensor([0, 7]))
    labels = Supervision(torch.tensor([True, False]), torch.tensor([0, 0]), torch.tensor([1, 0]), torch.tensor([1, 0]))
    return model, inputs, labels
