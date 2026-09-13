# LAPA Research Archive Status

Status: **development paused / research archive**.
Further development of the current research direction is paused while the
implementation, experiment history, and negative results are preserved.
This is neither a finding that every possible LAPA design is impossible nor a
claim that GitHub's `Archived` setting has been enabled. Repository creation,
publication, pushing, and server-side archiving are separate operations that
require their own authorization.

## Evidence behind the decision

The final evidence is in the
[v18 report](../research_archive/studies/four_factor_attention_v18/REPORT.md) and
[full-precision summary](../research_archive/studies/four_factor_attention_v18/SUMMARY.json).
Two formulas directly construct attention in every encoder layer and the final
readout from Source, Width, Endian, and Base distributions. Q/K similarity was
removed, while learned V, residual connections, FFNs, and fixed address-operation
rules were retained.

Using real DNS, Modbus, TLS, and SMB2 data, the study trained on three protocols
and evaluated on the remaining one. Two formulas × four targets × three seeds
produced **24 newly trained models**, each trained for 600 updates.
The **96 existing RoPE/CoPE/TAPE/SDPA × Off/Hybrid controls were reused, not
retrained**. The comparison uses the same 74 messages and 347 evaluation fields.

The following protocol-macro results first average fields within each protocol,
then weight the four protocols equally, and finally average the three seeds.
`p(target)` is probability assigned to the correct destination, not field
discovery F1 or packet accuracy.

| Method | Mean p(target) ↑ | Mean NLL (nat) ↓ | Hit@1 ↑ |
| --- | ---: | ---: | ---: |
| RoPE + LAPA Hybrid | 0.420837 | 3.063246 | 0.534492 |
| CoPE + LAPA Hybrid | 0.456255 | 3.525861 | 0.509848 |
| TAPE + LAPA Hybrid | 0.436009 | 3.035284 | 0.487448 |
| SDPA + LAPA Hybrid | 0.414544 | 3.509370 | 0.432749 |
| Four-factor Direct | 0.295720 | 3.847661 | 0.373162 |
| Four-factor Sink | 0.311763 | 3.419171 | 0.430911 |

Both new formulas have lower mean correct-destination probability than all four
Hybrid controls. Sink has lower NLL than CoPE/SDPA Hybrid but higher NLL than
RoPE/TAPE Hybrid, so the result is not uniform inferiority on every metric.
Field-micro correct-destination probability, which weights all 347 fields
equally, is 0.041878 for Direct and 0.052515 for Sink. DNS accounts for 266 fields,
so macro and micro averages answer different questions.

Higher DNS pointer endpoint probability did not establish success through the
correct semantic route. Annotated true-source probability was 0.000216 for
Direct and 0.000243 for Sink. Across Sink's 36 pointer fields × three seeds =
108 predictions, the analysis established a lower bound: **at least 98.057% of
the total probability mass assigned to correct destinations came from sources
other than the annotated source**. This is not a 98.057% packet error rate,
nor does it mean that 108 independent packets were observed. This Sink-specific
bound does not identify a particular alternative source/base or establish the
cause of Direct's behavior.

Both new formulas had Hit@1 = 0 on the 25 DNS RDLENGTH fields. All four SMB2
subrelations also had Hit@1 = 0. These are prediction failures from completed
models, not zeros inserted because training or evaluation was interrupted.
The negative results and the limits of their interpretation are preserved.

The earlier [v17 report](../research_archive/studies/formula_search_v17/REPORT.md)
also found insufficient evidence from a 400-model search to replace the
general-purpose default formula. Some probability improvements coexisted with
worse overall NLL, while source/program selection remained difficult.
The final v18 results likewise did not justify replacing the default package
with the new architecture.

## What these results do not establish

- Results use a fixed 600-update budget, three training seeds, and a small
  historical evaluation set. They do not establish fully converged best-case
  performance or generalization to new captures/protocols. Seed confidence
  intervals do not measure uncertainty over the capture population.
- The new models use 42 legal combinations, whereas the Hybrid controls use
  68 programs. Auxiliary losses, parameterization, and parameter counts also
  differ. The comparison does not isolate the causal effect of removing Q/K,
  prove that Q/K is universally necessary, or rule out every LAPA design.
- The DNS pointer mask/guard and SMB2 adjacent-field rules are fixed prior
  knowledge. The study does not claim unsupervised discovery of operation
  semantics.
- All Modbus/TLS evaluation destinations are END. High endpoint probability
  alone does not establish an understanding of length operations.
  v18 did not compute field discovery F1.
- Positive training coverage of operators/slots and the number of captures are
  limited. Nevertheless, DNS RDLENGTH failures cannot all be attributed to
  operations absent from training.

## Preservation and public distribution scope

The public bundle is limited to the lightweight materials below. Following the
user's publication and license-selection request, project-owned code and
documentation use Apache-2.0 while third-party notices are preserved.
Raw datasets and weights are outside the public release scope.

| Category | Preservation and distribution policy |
| --- | --- |
| `src/`, `configs/`, `scripts/`, `examples/`, `tests/` | Retain the compact package, interfaces, and verification code. Do not describe this as a package port of the complete v18 study |
| `research_archive/studies/formula_search_v16/` | Preserve selected reports, summaries, figures, and code snapshots from the earlier formula search |
| `research_archive/studies/formula_search_v17/` | Preserve selected reports, summaries, figures, and code snapshots from the architecture search |
| `research_archive/studies/four_factor_attention_v18/` | Preserve selected reports, summaries, figures, and code snapshots from the final four-factor study |
| Raw data, payloads, PCAP files, and tensors | Retained locally; not uploaded in this public bundle |
| Checkpoints, weights, training runs, and per-packet predictions/diagnostics | Retained locally; not distributed as if they were lightweight aggregates |
| Full-path workspace contracts and original manifests | Retained locally because they can contain absolute paths and private asset references; public inventories use relative paths and reviewed metadata |

Research code snapshots are **historical records that depend on their original
workspace**. A public clone without the original data, sibling research modules,
contracts, and execution environment is not guaranteed to reproduce complete
training runs. Matching selected file hashes does not establish full
reproducibility or grant permission to publish private source assets.
Some raw outputs referenced by the snapshots are absent because of this scope
restriction.

The compact package in `src/` follows the documented
[baseline fidelity](baseline_fidelity.md) and [reproduction scope](reproduction.md).
Unit-level functionality, smoke training on approved local data, and full
historical experiment reproduction are distinct levels of verification.
PASS entries in historical reports and checklists describe checks performed at
that time; they are not new verification or publication approval for this bundle.

## Access, licensing, and conditions for resuming

[LICENSE](../LICENSE) is Apache-2.0. It applies to project-owned contributions;
it neither licenses raw data/weight redistribution nor replaces third-party
terms. Follow the [third-party notices](../THIRD_PARTY_NOTICES.md) and
[data guide](../data/README.md). Only attribution comments were added to three
position-related modules for publication. Their executable code is unchanged,
but their file hashes differ from historical frozen contracts. Do not claim
that the current package passes those original file-hash contracts.

Researchers needing private source assets must explain the scope and purpose
to the owner and obtain a rights/privacy-reviewed bundle through an authorized
channel. Access or a response is not guaranteed. Missing assets must not be
supplied through an unreviewed public push or force-add. The
[release checklist](release_checklist.md) records checks associated with
separately authorized publication.

If work resumes, use a separate experiment lineage rather than overwriting
failed results. Necessary follow-up conditions include separating source
localization from factor selection under matched operator support and losses,
and preregistering new capture/protocol evaluation and test-reuse policies.
These are proposed conditions, not completed experiments or a promise of
continued development.
