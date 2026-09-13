from dataclasses import dataclass, fields
import torch


@dataclass
class ModelInputs:
    """Only public byte inputs. No protocol, source, program or target labels."""
    data: torch.Tensor
    observed: torch.Tensor
    slots: torch.Tensor

    def to(self, device):
        return ModelInputs(**{f.name: getattr(self, f.name).to(device) for f in fields(self)})


@dataclass
class Supervision:
    present: torch.Tensor
    sources: torch.Tensor
    programs: torch.Tensor
    targets: torch.Tensor

    def to(self, device):
        return Supervision(**{f.name: getattr(self, f.name).to(device) for f in fields(self)})


@dataclass
class Batch:
    inputs: ModelInputs
    labels: Supervision
    metadata: list

    def to(self, device):
        return Batch(self.inputs.to(device), self.labels.to(device), self.metadata)


@dataclass
class Execution:
    target: torch.Tensor
    valid: torch.Tensor
    candidate_mask: torch.Tensor
    decoded: torch.Tensor
    null: torch.Tensor
