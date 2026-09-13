import torch
from torch import nn
from ..config import LapaConfig
from ..types import ModelInputs
from ..programs.bank import native_bank
from .byte_encoder import ByteEncoder
from .heads.field import FieldPresence
from .heads.endpoint import SpecialEndpoints
from .lapa_attention import LapaAttention


class LapaModel(nn.Module):
    def __init__(self, config=None):
        super().__init__()
        self.config = config or LapaConfig()
        self.bank = native_bank()
        self.host = ByteEncoder(self.config, self.bank)
        self.presence = FieldPresence(self.config.dim)
        self.special_endpoints = SpecialEndpoints(self.config.dim, self.config.heads)
        self.fusion = LapaAttention()

    def _validate(self, inputs):
        if not isinstance(inputs, ModelInputs):
            raise TypeError("forward accepts ModelInputs only; pass batch.inputs, never labels")
        data, observed, slots = inputs.data, inputs.observed, inputs.slots
        if data.ndim != 2 or data.dtype != torch.long or observed.shape != data.shape or observed.dtype != torch.bool:
            raise ValueError("data must be int64 [B,L], observed bool [B,L]")
        if len({data.device, observed.device, slots.device}) != 1:
            raise ValueError("input devices must match")
        if data.shape[0] < 1 or not 1 <= data.shape[1] <= self.config.max_length or bool(((data < 0) | (data > 255)).any()):
            raise ValueError("invalid byte values or sequence length")
        lengths = observed.sum(-1)
        if not bool((lengths > 0).all()) or not torch.equal(observed, torch.arange(data.shape[1], device=data.device)[None, :] < lengths[:, None]):
            raise ValueError("complete nonempty native messages with right padding required")
        if slots.dtype != torch.long or slots.shape != (len(data),) or bool(((slots < 0) | (slots >= self.config.slots)).any()):
            raise ValueError("invalid fixed slot ID")

    def forward(self, inputs, *, attention=None, lapa_enabled=None):
        self._validate(inputs)
        backbone = attention or self.config.attention
        enabled = self.config.lapa_enabled if lapa_enabled is None else bool(lapa_enabled)
        hidden, host_logits, position, cope_positions = self.host(inputs, backbone)
        task, raw = hidden[:, 0], hidden[:, 1:]
        special = self.special_endpoints(task).view(len(task), self.config.heads, 2)
        logits = torch.cat((host_logits, special), -1)
        support = torch.cat((inputs.observed, torch.ones(len(task), 2, device=task.device, dtype=torch.bool)), -1)
        latent = self.host.router.latents(raw, inputs.observed)
        route = self.host.router.route(inputs, task, raw, latent, self.config.epsilon) if enabled else None
        base, final = self.fusion(logits, support, None if route is None else route["bias"], self.config.prior_strength)
        return {"presence_logits": self.presence(task).squeeze(-1), **latent, "base": base, "final": final,
                "route": route, "enabled": enabled, "observed": inputs.observed,
                "attention": backbone, "tape_position": position, "cope_positions": cope_positions}
