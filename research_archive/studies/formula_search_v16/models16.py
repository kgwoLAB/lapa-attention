"""Isolated, opt-in endpoint-formula ablations; the released LAPA is unchanged.

All learned decisions consume ModelInputs (bytes, observed mask, ordinal slot)
only. The fixed native-v4 executor/bank is shared by every routed formula.
``source``/``program`` retain the legacy pre-validity heads for matched losses
and field decoding. The actual route posterior is separately reported.
"""
import math

import torch
from torch import nn
import torch.nn.functional as F

from lapa import LapaConfig, LapaModel
from lapa.attention.masks import allowed_mask, masked_softmax
from lapa.attention.rope import rope_state
from lapa.programs.executor import execute
from lapa.routing.fusion import route_prior
from lapa.routing.pushforward import pushforward


VARIANTS = ("off", "hybrid", "route_sink", "route_direct", "route_axis", "route_joint", "cnn_joint")
SEARCH_VARIANTS = tuple(v for v in VARIANTS if v != "off")


class MaskedConvBlock(nn.Module):
    """Dilated local mixing, with no Q/K/V projections or attention weights."""
    def __init__(self, dim, ff_dim, dilation):
        super().__init__()
        self.depthwise = nn.Conv1d(dim, dim, 3, padding=dilation, dilation=dilation, groups=dim)
        self.channel = nn.Linear(dim, dim)
        self.norm = nn.LayerNorm(dim)
        self.ff = nn.Sequential(nn.Linear(dim, ff_dim), nn.GELU(), nn.Linear(ff_dim, dim))
        self.ff_norm = nn.LayerNorm(dim)

    def forward(self, hidden, observed):
        mask = observed.unsqueeze(-1).to(hidden.dtype)
        mixed = self.depthwise((hidden * mask).transpose(1, 2)).transpose(1, 2)
        hidden = self.norm(hidden + self.channel(F.gelu(mixed))) * mask
        return self.ff_norm(hidden + self.ff(hidden)) * mask


class CNNEncoder(nn.Module):
    """Slot-conditioned byte CNN, reusing initial embeddings/router tensors.

    Position features use observed message length or a fixed max-length scale,
    never the padded batch length. Invalid positions are cleared after every
    layer, so extra right padding cannot leak through dilated convolutions.
    """
    def __init__(self, host, cfg):
        super().__init__()
        self.cfg = cfg
        for name in ("byte_embedding", "query_id_embedding", "version_embedding", "embedding_norm", "readout", "router"):
            setattr(self, name, getattr(host, name))
        self.task_query = host.task_query
        self.position_projection = nn.Linear(8, cfg.dim, bias=False)
        self.slot_projection = nn.Linear(cfg.dim, cfg.dim, bias=False)
        self.blocks = nn.ModuleList([MaskedConvBlock(cfg.dim, cfg.ff_dim, d) for d in (1, 2, 4)])
        self.task_readout = nn.Sequential(nn.Linear(2 * cfg.dim, cfg.dim), nn.GELU(), nn.LayerNorm(cfg.dim))

    def forward(self, inputs):
        data, observed = inputs.data, inputs.observed
        token_ids = torch.where(observed, data, torch.full_like(data, 256))
        raw = self.byte_embedding(token_ids)
        dtype = raw.dtype
        mask = observed.unsqueeze(-1).to(dtype)
        lengths = observed.sum(-1, keepdim=True).to(dtype)
        pos = torch.arange(data.shape[1], device=data.device, dtype=dtype)[None].expand_as(data)
        log_length = (torch.log1p(lengths) / math.log1p(self.cfg.max_length)).expand_as(pos)
        features = torch.stack((pos / self.cfg.max_length, pos / lengths, (lengths - pos) / lengths,
                                log_length, torch.sin(pos * (2 * math.pi / 16)), torch.cos(pos * (2 * math.pi / 16)),
                                torch.sin(pos * (2 * math.pi / 64)), torch.cos(pos * (2 * math.pi / 64))), -1)
        query = self.task_query[None] + self.query_id_embedding(inputs.slots) + self.version_embedding(torch.zeros_like(inputs.slots))
        raw = F.gelu(self.embedding_norm(raw + self.position_projection(features) + self.slot_projection(query)[:, None])) * mask
        for block in self.blocks:
            raw = block(raw, observed)
        raw = self.readout(raw) * mask
        pooled = raw.sum(1) / lengths
        task = self.task_readout(torch.cat((query, pooled), -1))
        return torch.cat((task[:, None], raw), 1)


def encoder_without_retrieval(host, inputs, backbone):
    """Exact native ByteEncoder through its readout, omitting final QK entirely."""
    data, observed = inputs.data, inputs.observed
    token_ids = torch.where(observed, data, torch.full_like(data, 256))
    raw = host.byte_embedding(token_ids) * observed.unsqueeze(-1)
    task = host.task_query.unsqueeze(0).expand(len(data), -1) + host.query_id_embedding(inputs.slots) + host.version_embedding(torch.zeros_like(inputs.slots))
    hidden = torch.cat((task.unsqueeze(1), raw), 1)
    support = torch.cat((torch.ones(len(data), 1, device=data.device, dtype=torch.bool), observed), 1)
    hidden = host.embedding_norm(hidden) * support.unsqueeze(-1)
    allowed = allowed_mask(support)
    raw_support = support.clone()
    raw_support[:, 0] = False
    gate_allowed = support[:, None, :, None] & raw_support[:, None, None, :]
    position = rope_state(len(data), host.cfg.heads, torch.arange(-1, data.shape[1], device=data.device),
                          host.cfg.dim // host.cfg.heads, hidden.dtype, data.device)
    position = tuple(stream * support[:, None, :, None].to(hidden.dtype) for stream in position)
    for block in host.blocks:
        hidden, position = block(hidden, backbone, support, allowed, gate_allowed, position, host.cope)
    hidden = host.readout(hidden) * support.unsqueeze(-1)
    return hidden, position if backbone == "tape" else None


class FormulaModel(LapaModel):
    """FormulaModel(variant, backbone='tape') -> legacy-compatible output dict.

    off/hybrid are exact existing-model forwards, with extra diagnostic keys.
    route_sink retains the old learned gates and neutral sink but no final QK.
    route_direct/route_axis normalize alpha(s)*beta(p|s)*valid(s,p).
    route_joint/cnn_joint normalize exp(source_logit(s)+program_logit(s,p))
    over valid pairs, without the per-source program partition function.
    All new route distributions are smoothed using config.epsilon; an empty
    valid set falls back to uniform, never to the distinct NULL endpoint.

    route_axis has the same forward as route_direct; the caller supplies its
    explicit axis-averaged program loss. No losses or labels are used here.
    """
    def __init__(self, variant, backbone="tape"):
        if variant not in VARIANTS:
            raise ValueError(f"unknown formula variant: {variant}")
        super().__init__(LapaConfig(attention=backbone, lapa_enabled=variant != "off"))
        self.variant = variant
        if variant not in ("off", "hybrid"):
            # Initialization occurs in precisely the native order before any
            # deletions, preserving every shared initial tensor for a seed.
            del self.host.retrieval_query
            del self.host.retrieval_key
            del self.special_endpoints
            del self.fusion
        if variant not in ("off", "hybrid", "route_sink"):
            del self.host.router.top_head
            del self.host.router.wellformed_width_score
            del self.host.router.program_width_ids
        if variant == "cnn_joint":
            self.host = CNNEncoder(self.host, self.config)

    def _normalized_route(self, inputs, latent, support):
        execution = execute(self.bank, inputs.data, inputs.observed)
        source_logits, program_logits = latent["source_logits"], latent["program_logits"]
        if self.variant in ("route_joint", "cnn_joint"):
            scores = source_logits[:, :, None] + program_logits
        else:
            masked_source = source_logits.masked_fill(~inputs.observed, torch.finfo(source_logits.dtype).min)
            scores = F.log_softmax(masked_source, -1)[:, :, None] + F.log_softmax(program_logits, -1)
        valid = execution.valid
        joint = masked_softmax(scores.flatten(1), valid.flatten(1)).reshape_as(scores)
        real = pushforward(execution.target, joint, inputs.data.shape[1] + 2)
        source_marginal = joint.sum(-1)
        conditional = torch.where(source_marginal[:, :, None] > 0,
                                  joint / source_marginal[:, :, None].clamp_min(torch.finfo(joint.dtype).tiny),
                                  torch.zeros_like(joint))
        unconditioned = latent["source"][:, :, None] * latent["program"]
        return {"source": latent["source"], "program": latent["program"], "joint": joint,
                "unconditioned_joint": unconditioned, "source_marginal": source_marginal,
                "program_conditional": conditional, "valid_mass": (unconditioned * valid).sum((1, 2)),
                "has_valid_pair": valid.flatten(1).any(-1), "execution": execution,
                "normalization": "global_joint_energy" if self.variant in ("route_joint", "cnn_joint") else "conditional_joint_valid",
                **route_prior(real, support, self.config.epsilon)}

    def forward(self, inputs, *, attention=None, lapa_enabled=None):
        self._validate(inputs)
        backbone = attention or self.config.attention
        if lapa_enabled is not None and bool(lapa_enabled) != (self.variant != "off"):
            raise ValueError("formula variants are fixed; construct off or hybrid for a different mode")
        cope_positions = position = None
        host_logits = None
        if self.variant in ("off", "hybrid"):
            hidden, host_logits, position, cope_positions = self.host(inputs, backbone)
        elif self.variant == "cnn_joint":
            if attention is not None:
                raise ValueError("cnn_joint has no attention backbone to override")
            hidden = self.host(inputs)
        else:
            hidden, position = encoder_without_retrieval(self.host, inputs, backbone)
        task, raw = hidden[:, 0], hidden[:, 1:]
        support = torch.cat((inputs.observed, torch.ones(len(task), 2, device=task.device, dtype=torch.bool)), -1)
        uniform = support.to(raw.dtype) / support.sum(-1, keepdim=True)
        latent = self.host.router.latents(raw, inputs.observed)
        axis_logits = {axis: head(raw) for axis, head in self.host.router.axis_heads.items()}
        if self.variant in ("off", "hybrid"):
            special = self.special_endpoints(task).view(len(task), self.config.heads, 2)
            logits = torch.cat((host_logits, special), -1)
            route = self.host.router.route(inputs, task, raw, latent, self.config.epsilon) if self.variant == "hybrid" else None
            base, final = self.fusion(logits, support, None if route is None else route["bias"], self.config.prior_strength)
        elif self.variant == "route_sink":
            route = self.host.router.route(inputs, task, raw, latent, self.config.epsilon)
            base, final = uniform, route["prior"]
        else:
            route = self._normalized_route(inputs, latent, support)
            base, final = uniform, route["prior"]
        return {"presence_logits": self.presence(task).squeeze(-1), **latent, "axis_logits": axis_logits,
                "base": base, "final": final, "route": route, "enabled": self.variant != "off",
                "observed": inputs.observed, "attention": "none_cnn" if self.variant == "cnn_joint" else backbone,
                "tape_position": position, "cope_positions": cope_positions, "variant": self.variant,
                "base_available": self.variant in ("off", "hybrid"),
                "base_kind": "retrieval_qk" if self.variant in ("off", "hybrid") else "uniform_reference_no_qk",
                "encoder_kind": "cnn_no_qkv" if self.variant == "cnn_joint" else "transformer_qkv"}
