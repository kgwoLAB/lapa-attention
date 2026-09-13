"""Raw-only, execution-aware residual scores for the existing program logits.

This module is an opt-in v17 formula component, not a new protocol parser.
The caller supplies the deterministic execution of the common program bank.
No field annotations, protocol identity, or target labels enter this scorer.
"""

import math

import torch
from torch import nn


class ExecutionFeatureScore(nn.Module):
    """Return ``delta_logits[B, L, P]`` from raw context and executable rules.

    A program has a *sum of factorized attribute embeddings*, rather than an
    independent learned program-ID embedding. Source context, task context,
    attributes and bounded numeric execution features are projected additively
    into 16 channels, followed by a small nonlinear scalar scoring head. Thus
    no concatenation of three full ``B x L x P x dim`` contexts is allocated.

    Numeric features use each message's observed length, never batch padding.
    The executor represents END/NULL using the padded batch length; END is
    converted back to the observed message length before numeric features are
    formed, and NULL is represented separately, not as a numeric destination.
    Invalid executor targets are similarly not interpreted as real byte zero.

    The final linear layer starts at zero, so adding this residual initially
    preserves the unmodified program logits. Earlier scorer layers begin
    receiving gradients once the scalar head has left zero. ``latent`` is
    accepted for the shared formula API but not read: this component provides
    new raw/execution evidence, not a duplicate of existing program scores.
    """

    hidden_dim = 16
    numeric_feature_names = (
        "source_over_length",
        "remaining_over_length",
        "field_end_over_length",
        "width_over_length",
        "width_over_four",
        "signed_log_decoded_over_log_length",
        "clipped_decoded_over_length",
        "valid_nonnull_target_over_length",
        "valid_nonnull_displacement_over_length",
        "valid",
        "null",
        "end",
        "candidate_mask",
    )

    def __init__(self, dim, bank):
        super().__init__()
        if dim <= 0:
            raise ValueError("context dimension must be positive")
        self.dim = int(dim)
        self.program_count = len(bank.programs)
        self.bank_fingerprint = bank.fingerprint
        self.axis_names = tuple(bank.axis_names)
        vocabulary, axis_ids = bank.axis_vocabulary(), bank.axis_ids()
        self.attributes = nn.ModuleDict(
            {axis: nn.Embedding(len(vocabulary[axis]), self.hidden_dim)
             for axis in self.axis_names}
        )
        for axis, ids in axis_ids.items():
            self.register_buffer(f"attribute_ids_{axis}", ids.clone())
        self.register_buffer(
            "program_widths",
            torch.tensor([program.width for program in bank.programs], dtype=torch.float32),
        )
        self.source_projection = nn.Linear(dim, self.hidden_dim, bias=False)
        self.task_projection = nn.Linear(dim, self.hidden_dim, bias=False)
        self.numeric_projection = nn.Parameter(
            torch.empty(len(self.numeric_feature_names), self.hidden_dim)
        )
        self.scorer = nn.Sequential(
            nn.LayerNorm(self.hidden_dim),
            nn.Linear(self.hidden_dim, self.hidden_dim),
            nn.GELU(),
            nn.Linear(self.hidden_dim, 1),
        )
        for embedding in self.attributes.values():
            nn.init.normal_(embedding.weight, mean=0.0, std=0.1)
        nn.init.xavier_uniform_(self.numeric_projection)
        nn.init.zeros_(self.scorer[-1].weight)
        nn.init.zeros_(self.scorer[-1].bias)

    def _features(self, inputs, execution, dtype):
        """Return scalar tensors broadcastable to B x L x P, all bounded."""
        batch, padded_length = inputs.data.shape
        lengths = inputs.observed.sum(-1).to(dtype)[:, None, None].clamp_min(1)
        source = torch.arange(padded_length, device=inputs.data.device, dtype=dtype)[None, :, None]
        width = self.program_widths.to(dtype)[None, None, :]
        # The native decoder returns a provisional integer even for an
        # incomplete field. That integer can depend on padding/clamped reads,
        # so expose decoded-value features only for fully observed reads.
        complete_read = (source + width <= lengths) & inputs.observed[:, :, None]
        value = torch.where(complete_read, execution.decoded.to(dtype),
                            torch.zeros_like(execution.decoded, dtype=dtype))
        valid = execution.valid
        null = execution.null & valid
        end = valid & ~null & (execution.target == padded_length)
        nonnull = valid & ~null
        # Only the executor's discrete target is used. Huge decoded integers
        # never pass through a floating-point comparison to determine validity.
        target = torch.where(end, lengths, execution.target.to(dtype))
        target = torch.where(nonnull, target, torch.zeros_like(target))
        signed_log = value.sign() * torch.log1p(value.abs()) / torch.log1p(lengths)
        return (
            (source / lengths).clamp(0, 1),
            ((lengths - source) / lengths).clamp(0, 1),
            ((source + width) / lengths).clamp(0, 4),
            (width / lengths).clamp(0, 4),
            width / 4.0,
            signed_log.clamp(-4, 4),
            (value / lengths).clamp(-4, 4),
            (target / lengths).clamp(0, 1),
            torch.where(nonnull, (target - source) / lengths, torch.zeros_like(target)).clamp(-1, 1),
            valid.to(dtype),
            null.to(dtype),
            end.to(dtype),
            execution.candidate_mask.to(dtype),
        )

    def forward(self, inputs, raw, task, latent, execution):
        """Consume only ModelInputs, hidden states and deterministic execution."""
        del latent
        if inputs.data.ndim != 2 or inputs.observed.shape != inputs.data.shape:
            raise ValueError("data and observed must have matching B x L shape")
        batch, length = inputs.data.shape
        if raw.shape != (batch, length, self.dim) or task.shape != (batch, self.dim):
            raise ValueError("raw/task shapes do not match scorer context dimension")
        expected = (batch, length, self.program_count)
        if any(getattr(execution, name).shape != expected
               for name in ("target", "valid", "candidate_mask", "decoded", "null")):
            raise ValueError("execution shape does not match the fixed program bank")
        if not inputs.observed.any(-1).all():
            raise ValueError("each message must contain at least one observed byte")
        program = sum(
            self.attributes[axis](getattr(self, f"attribute_ids_{axis}"))
            for axis in self.axis_names
        ) / math.sqrt(len(self.axis_names))
        hidden = (
            self.source_projection(raw)[:, :, None, :]
            + self.task_projection(task)[:, None, None, :]
            + program[None, None, :, :]
        )
        # Scalar-feature projections avoid concatenating replicated raw/task/
        # attribute contexts, and avoid an additional dense 13-feature stack.
        for feature, weights in zip(self._features(inputs, execution, hidden.dtype), self.numeric_projection):
            hidden = hidden + feature[..., None] * weights
        delta = self.scorer(hidden).squeeze(-1)
        return delta.masked_fill(~inputs.observed[:, :, None], 0.0)
