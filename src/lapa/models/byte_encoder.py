import torch
from torch import nn
from .transformer import EncoderBlock
from ..attention.base import split_heads
from ..attention.cope import CoPEPosition
from ..attention.factory import make_attention
from ..attention.rope import rope_state
from ..attention.masks import allowed_mask
from ..routing.router import XRouteRouter


class ByteEncoder(nn.Module):
    """Native-v4 host. All positional tensors remain allocated across modes."""
    def __init__(self, cfg, bank):
        super().__init__()
        self.cfg = cfg
        self.byte_embedding = nn.Embedding(257, cfg.dim)
        self.query_id_embedding = nn.Embedding(256, cfg.dim)
        self.version_embedding = nn.Embedding(256, cfg.dim)
        self.task_query = nn.Parameter(torch.empty(cfg.dim))
        nn.init.normal_(self.task_query, std=.02)
        self.embedding_norm = nn.LayerNorm(cfg.dim)
        self.blocks = nn.ModuleList([EncoderBlock(cfg) for _ in range(cfg.layers)])
        self.readout = nn.LayerNorm(cfg.dim)
        self.cope = CoPEPosition(cfg.dim // cfg.heads, cfg.max_length + 1)
        self.retrieval_query = nn.Linear(cfg.dim, cfg.dim, bias=False)
        self.retrieval_key = nn.Linear(cfg.dim, cfg.dim, bias=False)
        self.router = XRouteRouter(cfg.dim, bank)

    def forward(self, inputs, backbone):
        data, observed = inputs.data, inputs.observed
        token_ids = torch.where(observed, data, torch.full_like(data, 256))
        raw = self.byte_embedding(token_ids) * observed.unsqueeze(-1)
        task = self.task_query.unsqueeze(0).expand(len(data), -1) + self.query_id_embedding(inputs.slots) + self.version_embedding(torch.zeros_like(inputs.slots))
        hidden = torch.cat((task.unsqueeze(1), raw), 1)
        support = torch.cat((torch.ones(len(data), 1, device=data.device, dtype=torch.bool), observed), 1)
        hidden = self.embedding_norm(hidden) * support.unsqueeze(-1)
        allowed = allowed_mask(support)
        raw_support = support.clone()
        raw_support[:, 0] = False
        gate_allowed = support[:, None, :, None] & raw_support[:, None, None, :]
        position = rope_state(len(data), self.cfg.heads, torch.arange(-1, data.shape[1], device=data.device),
                              self.cfg.dim // self.cfg.heads, hidden.dtype, data.device)
        position = tuple(stream * support[:, None, :, None].to(hidden.dtype) for stream in position)
        for block in self.blocks:
            hidden, position = block(hidden, backbone, support, allowed, gate_allowed, position, self.cope)
        hidden = self.readout(hidden) * support.unsqueeze(-1)
        q = split_heads(self.retrieval_query(hidden[:, :1]), self.cfg.heads)
        k = split_heads(self.retrieval_key(hidden[:, 1:]), self.cfg.heads)
        logits, cope_positions = make_attention(backbone).logits(q, k, state=position, cope=self.cope, gate_allowed=observed[:, None, None, :])
        logits = logits.squeeze(-2).masked_fill(~observed[:, None, :], torch.finfo(hidden.dtype).min)
        return hidden, logits, position if backbone == "tape" else None, cope_positions
