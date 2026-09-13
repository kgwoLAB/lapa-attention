import torch
from torch import nn
from ..attention.masks import masked_softmax
from ..programs.executor import execute
from .source import SourceLocator
from .program import make_axis_heads, program_logits
from .pushforward import pushforward
from .fusion import route_prior


class XRouteRouter(nn.Module):
    def __init__(self, dim, bank):
        super().__init__()
        self.bank = bank
        self.axis_names = bank.axis_names
        self.source_score = SourceLocator(dim)
        self.axis_heads = make_axis_heads(dim, bank)
        for axis, ids in bank.axis_ids().items():
            self.register_buffer(f"axis_ids_{axis}", ids)
        widths = sorted({p.width for p in bank.programs})
        self.register_buffer("program_width_ids", torch.tensor([widths.index(p.width) for p in bank.programs]))
        self.wellformed_width_score = nn.Linear(dim, len(widths))
        self.top_head = nn.Sequential(nn.Linear(2 * dim + 2, dim), nn.GELU(), nn.Linear(dim, 3))
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
        for head in [self.source_score, *self.axis_heads.values(), self.wellformed_width_score]:
            nn.init.normal_(head.weight, std=1e-3)
        nn.init.zeros_(self.top_head[-1].weight)
        with torch.no_grad():
            self.top_head[-1].bias.copy_(torch.tensor((.70, .15, .15)).log())

    def latents(self, raw, observed):
        logits, source = self.source_score.probabilities(raw, observed)
        ids = {a: getattr(self, f"axis_ids_{a}") for a in self.axis_names}
        plogits = program_logits(raw, self.bank, self.axis_heads, ids)
        prob = masked_softmax(plogits, observed[:, :, None].expand_as(plogits))
        return {"source_logits": logits, "source": source, "program_logits": plogits, "program": prob}

    def route(self, inputs, task, raw, latent, epsilon):
        execution = execute(self.bank, inputs.data, inputs.observed)
        source, program = latent["source"], latent["program"]
        wellformed = torch.sigmoid(self.wellformed_width_score(raw).index_select(-1, self.program_width_ids))
        wellformed = wellformed * execution.candidate_mask.to(source.dtype)
        selected = torch.einsum("bl,bld->bd", source, raw)
        masked = latent["source_logits"].masked_fill(~inputs.observed, torch.finfo(source.dtype).min)
        maximum = masked.max(-1, keepdim=True).values
        lme = torch.logsumexp(masked, -1, keepdim=True) - inputs.observed.sum(-1, keepdim=True).to(source.dtype).log()
        top = torch.softmax(self.top_head(torch.cat((task, selected, maximum, lme), -1)), -1)
        joint = source[:, :, None] * program
        contribution = top[:, 2, None, None] * joint * wellformed * execution.valid.to(source.dtype)
        length = inputs.data.shape[1]
        real = pushforward(execution.target, contribution, length + 2)
        support = torch.cat((inputs.observed, torch.ones(len(source), 2, dtype=torch.bool, device=source.device)), -1)
        return {"source": source, "program": program, "joint": joint, "wellformed": wellformed,
                "top": top, "execution": execution, **route_prior(real, support, epsilon)}
