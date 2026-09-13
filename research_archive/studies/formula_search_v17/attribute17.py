"""Learned attribute Q/K readout: opt-in, raw-input-only formula alternatives.

This module does *not* receive annotated field starts, widths, endianness,
programs or destinations. Source/axis/program probabilities are predictions
made upstream from bytes and the public ordinal query. The program bank and
its deterministic executor are the same pre-existing structural prior as
native LAPA; the executor enumerates every candidate, not an oracle program.

For alpha_s = p(source=s) and beta_sp = p(program=p | source=s), let
J_sp = alpha_s beta_sp valid_sp and M_dp = sum_s J_sp 1[E(s,p)=d].
The attribute query contains expected source-position embeddings, expected
program embeddings and separately predicted axis embeddings. Each destination
key contains its position, the incoming source-position expectation and the
incoming program/axis embeddings implied by M. Thus both Q and K are new
learned projections of structural attributes, not renamed native retrieval
projections. The discrete executor itself has no learned gradient; all weights,
attribute embeddings, projections and the optional distance kernel do.

``attr_only``: Q/K from predicted structural attributes, no hidden-content
projection in this final destination readout. The upstream encoder may still
use attention; this is not a claim of a wholly QKV-free model.
``attr_content``: concatenate task/byte hidden content to those same attributes.
``attr_distance``: attribute-only QK plus a learned-strength log execution
kernel, mixing exact route probability and a learned-bandwidth distance kernel.

END and NULL occupy the batch's final two columns; END's numeric location is
each message's observed length. NULL is a distinct categorical endpoint.
Padding is never interpreted as bytes, a destination, or an END position.
"""

import math

import torch
from torch import nn
import torch.nn.functional as F


KINDS = ("attr_only", "attr_content", "attr_distance")


class AttributeDestination(nn.Module):
    """Return ``(logits[B, heads, L+2], diagnostics)`` without gold inputs.

    ``latent`` must provide source[B,L] and program[B,L,P] probabilities;
    ``axis_logits`` maps all bank.axis_names to predicted [B,L,A] logits;
    ``execution`` is the native executor's Execution object for the same bytes.
    The caller normalizes logits over observed bytes plus END/NULL, averages
    heads according to the existing evaluator, and chooses losses separately.
    """

    def __init__(self, dim, bank, heads, max_length):
        super().__init__()
        if dim <= 0 or heads <= 0 or dim % heads or max_length <= 0:
            raise ValueError("dim must be divisible by heads; all sizes must be positive")
        self.dim = dim
        self.heads = heads
        self.head_dim = dim // heads
        self.max_length = max_length
        self.axis_names = tuple(bank.axis_names)
        self.program_count = len(bank)
        self.bank_fingerprint = bank.fingerprint
        self.embedding_dim = max(4, self.head_dim)
        vocab = bank.axis_vocabulary()
        self.program_embedding = nn.Embedding(len(bank), self.embedding_dim)
        self.axis_embeddings = nn.ModuleDict({
            axis: nn.Embedding(len(vocab[axis]), self.embedding_dim)
            for axis in self.axis_names
        })
        for axis, ids in bank.axis_ids().items():
            self.register_buffer("program_axis_" + axis, ids)

        self.source_embedding = nn.Sequential(
            nn.Linear(8, self.embedding_dim, bias=False), nn.Tanh())
        descriptor_dim = self.embedding_dim * (len(self.axis_names) + 1)
        # Query: source embedding + axis/program embeddings + four scalars.
        query_dim = self.embedding_dim + descriptor_dim + 4
        # Key: incoming source/program/axes + destination features + four scalars.
        key_dim = self.embedding_dim + descriptor_dim + 10 + 4
        self.query_attributes = nn.Sequential(
            nn.LayerNorm(query_dim), nn.Linear(query_dim, dim, bias=False))
        self.key_attributes = nn.Sequential(
            nn.LayerNorm(key_dim), nn.Linear(key_dim, dim, bias=False))
        self.query_with_content = nn.Sequential(
            nn.LayerNorm(query_dim + dim), nn.Linear(query_dim + dim, dim, bias=False))
        self.key_with_content = nn.Sequential(
            nn.LayerNorm(key_dim + dim), nn.Linear(key_dim + dim, dim, bias=False))
        self.special_content = nn.Parameter(torch.empty(2, dim))
        nn.init.normal_(self.special_content, std=dim ** -0.5)
        # softplus values initially: bandwidth=2 bytes, strength=1.
        self.kernel_log_bandwidth = nn.Parameter(torch.tensor(math.log(math.expm1(2.0))))
        self.kernel_log_strength = nn.Parameter(torch.tensor(math.log(math.expm1(1.0))))

    def _position_features(self, positions, lengths):
        lengths = lengths.clamp_min(1)
        relative = positions / lengths
        return torch.stack((
            positions / self.max_length,
            relative,
            (lengths - positions) / lengths,
            torch.log1p(lengths).expand_as(positions) / math.log1p(self.max_length),
            torch.sin(positions * (2 * math.pi / 16)),
            torch.cos(positions * (2 * math.pi / 16)),
            torch.sin(positions * (2 * math.pi / 64)),
            torch.cos(positions * (2 * math.pi / 64)),
        ), dim=-1)

    def _distance_kernel(self, route, destination_positions, support):
        """Column-normalized location kernel, preserving NULL categorically."""
        tau = F.softplus(self.kernel_log_bandwidth).clamp(0.25, 32.0)
        delta = destination_positions[:, :, None] - destination_positions[:, None, :]
        weights = torch.exp(-0.5 * (delta / tau).square())
        # Index -1 is NULL; no numeric distance may move mass to/from NULL.
        byte_or_end = support.clone()
        byte_or_end[:, -1] = False
        same_kind = byte_or_end[:, :, None] & byte_or_end[:, None, :]
        same_kind[:, -1, -1] = True
        weights = weights * same_kind.to(weights.dtype)
        weights = weights / weights.sum(dim=1, keepdim=True).clamp_min(1e-12)
        smoothed = torch.bmm(weights, route.unsqueeze(-1)).squeeze(-1)
        return 0.75 * route + 0.25 * smoothed, tau

    def forward(self, inputs, raw, task, latent, axis_logits, execution, kind):
        if kind not in KINDS:
            raise ValueError(f"unknown attribute readout kind: {kind}")
        batch, length, dim = raw.shape
        if dim != self.dim or task.shape != (batch, dim):
            raise ValueError("raw/task dimensions differ from configured hidden size")
        source = latent["source"]
        program = latent["program"]
        if source.shape != (batch, length) or program.shape != (batch, length, self.program_count):
            raise ValueError("source/program predictions differ from input/bank dimensions")
        if set(axis_logits) != set(self.axis_names):
            raise ValueError("every existing program-bank axis must be supplied")
        if execution.target.shape != program.shape or execution.valid.shape != program.shape:
            raise ValueError("execution and predicted program candidates must align")

        observed = inputs.observed
        support = torch.cat((observed, torch.ones(batch, 2, dtype=torch.bool, device=raw.device)), dim=-1)
        dtype = raw.dtype
        lengths = observed.sum(-1, keepdim=True).to(dtype)
        positions = torch.arange(length, device=raw.device, dtype=dtype)[None].expand(batch, -1)
        source = source * observed.to(source.dtype)
        source = source / source.sum(-1, keepdim=True).clamp_min(1e-12)
        program = program * observed[:, :, None].to(program.dtype)
        position_features = self._position_features(positions, lengths)
        source_embedding = self.source_embedding(position_features) * observed[:, :, None]

        # Q sees separately predicted axes, including base, endian, width,
        # sign and mask, not their labels or the true program's decomposition.
        expected_program = torch.einsum("bl,blp,pd->bd", source, program, self.program_embedding.weight)
        predicted_axes = []
        program_descriptors = [self.program_embedding.weight]
        for axis in self.axis_names:
            probabilities = torch.softmax(axis_logits[axis], dim=-1)
            predicted_axes.append(torch.einsum(
                "bl,bla,ad->bd", source, probabilities, self.axis_embeddings[axis].weight))
            ids = getattr(self, "program_axis_" + axis)
            program_descriptors.append(self.axis_embeddings[axis](ids))
        query_descriptor = torch.cat([expected_program, *predicted_axes], dim=-1)
        program_descriptors = torch.cat(program_descriptors, dim=-1)
        selected_source_embedding = torch.einsum("bl,bld->bd", source, source_embedding)

        joint = source[:, :, None] * program * execution.valid.to(dtype)
        # M[d,p] retains the *joint* source/program relationship. It does not
        # replace it with independent unconditional program and source modes.
        incoming_program = torch.zeros(batch, self.program_count, length + 2,
                                       dtype=dtype, device=raw.device)
        incoming_program = incoming_program.scatter_add(
            2, execution.target.transpose(1, 2), joint.transpose(1, 2)).transpose(1, 2)
        incoming_mass = incoming_program.sum(-1)
        valid_mass = incoming_mass.sum(-1)
        incoming_descriptor = torch.matmul(incoming_program, program_descriptors)
        incoming_descriptor = incoming_descriptor / incoming_mass[:, :, None].clamp_min(1e-12)
        weighted_source = joint[:, :, :, None] * source_embedding[:, :, None, :]
        incoming_source = torch.zeros(batch, length + 2, self.embedding_dim, dtype=dtype, device=raw.device)
        incoming_source = incoming_source.scatter_add(
            1, execution.target.reshape(batch, -1, 1).expand(-1, -1, self.embedding_dim),
            weighted_source.reshape(batch, -1, self.embedding_dim))
        incoming_source = incoming_source / incoming_mass[:, :, None].clamp_min(1e-12)

        source_entropy = -(source * source.clamp_min(1e-12).log()).sum(-1)
        source_entropy = source_entropy / torch.log(lengths.squeeze(-1).clamp_min(2))
        program_entropy = -(program * program.clamp_min(1e-12).log()).sum(-1)
        program_entropy = (source * program_entropy).sum(-1) / math.log(max(2, self.program_count))
        query_scalars = torch.stack((source.max(-1).values, source_entropy,
                                     program_entropy, valid_mass), dim=-1)
        query_features = torch.cat((selected_source_embedding, query_descriptor, query_scalars), dim=-1)

        # END uses the actual observed message length, not the batch-pad index.
        # NULL's numerical features are cleared and a separate type bit is set.
        destination_positions = torch.cat((positions, lengths, torch.zeros_like(lengths)), dim=-1)
        destination_features = self._position_features(destination_positions, lengths)
        destination_features[:, -1] = 0
        kinds = torch.zeros(batch, length + 2, 2, dtype=dtype, device=raw.device)
        kinds[:, -2, 0] = 1
        kinds[:, -1, 1] = 1
        destination_features = torch.cat((destination_features, kinds), dim=-1)
        source_here = torch.cat((source, torch.zeros(batch, 2, dtype=dtype, device=raw.device)), dim=-1)
        key_scalars = torch.stack((incoming_mass, torch.log1p(incoming_mass * lengths),
                                   source_here, valid_mass[:, None].expand(-1, length + 2)), dim=-1)
        key_features = torch.cat((incoming_source, incoming_descriptor,
                                  destination_features, key_scalars), dim=-1)

        if kind == "attr_content":
            content = torch.cat((raw, self.special_content[None].expand(batch, -1, -1)), dim=1)
            query = self.query_with_content(torch.cat((query_features, task), dim=-1))
            key = self.key_with_content(torch.cat((key_features, content), dim=-1))
        else:
            query = self.query_attributes(query_features)
            key = self.key_attributes(key_features)
        query = query.reshape(batch, self.heads, self.head_dim)
        key = key.reshape(batch, length + 2, self.heads, self.head_dim).transpose(1, 2)
        logits = torch.einsum("bhd,bhnd->bhn", query, key) / math.sqrt(self.head_dim)

        uniform = support.to(dtype) / support.sum(-1, keepdim=True)
        route = torch.where(valid_mass[:, None] > 0,
                            incoming_mass / valid_mass[:, None].clamp_min(1e-12), uniform)
        diagnostics = {"attribute_kind": kind, "predicted_attribute_inputs_only": True,
                       "native_retrieval_qk_used": False,
                       "hidden_content_in_final_qk": kind == "attr_content",
                       "valid_mass": valid_mass, "attribute_route": route,
                       "attribute_query_norm": query.norm(dim=-1),
                       "source_entropy": source_entropy, "program_entropy": program_entropy}
        if kind == "attr_distance":
            kernel, bandwidth = self._distance_kernel(route, destination_positions, support)
            # Strictly positive support smoothing is part of the declared
            # readout, not a fabricated posterior for a deterministic baseline.
            kernel = 0.98 * kernel + 0.02 * uniform
            strength = F.softplus(self.kernel_log_strength)
            logits = logits + strength * kernel.clamp_min(1e-12).log()[:, None]
            diagnostics.update({"execution_kernel": kernel, "kernel_bandwidth": bandwidth,
                                "kernel_strength": strength})
        logits = logits.masked_fill(~support[:, None], torch.finfo(logits.dtype).min)
        return logits, diagnostics
