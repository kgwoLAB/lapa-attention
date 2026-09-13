# LAPA Research Archive

This **public GitHub snapshot** preserves implementations and both successful
and unsuccessful experiments. Project-controlled contributions use Apache-2.0;
this is not a new experiment. See the
[project status](../docs/archive_status.md) for the decision to pause development
and the interpretation of the results.

## Archive layout

```text
research_archive/
├── README.md
├── MANIFEST.json
└── studies/
    ├── formula_search_v16/
    ├── formula_search_v17/
    └── four_factor_attention_v18/
```

| Study | Documents | Scope |
| --- | --- | --- |
| v16 | [Report](studies/formula_search_v16/REPORT.md), [tables](studies/formula_search_v16/TABLES.md) | Initial formula comparison |
| v17 | [Report](studies/formula_search_v17/REPORT.md), [tables](studies/formula_search_v17/TABLES.md) | Expanded formula search and fixed selection procedure |
| v18 | [Report](studies/four_factor_attention_v18/REPORT.md), [tables](studies/four_factor_attention_v18/TABLES.md), [formulas](studies/four_factor_attention_v18/FORMULAS.md) | Direct Source/Width/Endian/Base attention; QK-free, V-retained |

Each directory preserves historical Python source, designs, work logs, reports,
aggregate JSON, existing LaTeX tables, and Matplotlib figures.
[MANIFEST.json](MANIFEST.json) lists all included source assets.
Historical study records retain their original language; this English guide
does not replace or modify their archived contents.

v18 trained 24 new models for 600 updates each under a three-protocol-to-one
evaluation design and reused 96 historical controls under matched conditions.
These are not 120 newly trained models. Models reused across studies must not
be counted as independent experiments by summing version totals.

## Differences between originals and public copies

- Original research directories, raw data, checkpoints, predictions, and failure
  records were not changed.
- Raw payload/JSONL/PCAP files, tensors/weights, per-packet NPZ files, run
  directories, full contracts, and original audit JSON are not included.
- Personal absolute paths in research code, documentation, and JSON were
  replaced with `WORKSPACE` or `USER_HOME` placeholders. Documentation carries
  notices identifying these as distribution copies.
- Numerical values were neither rounded nor removed. Large JSON is split into
  parts of at most 4 MiB each. An `$archive_ref` is a reference to another
  preserved JSON file, not an omission.
- Assets eligible for direct copying, including figures and tables, are
  byte-identical to their originals. Existing PDFs were copied, not regenerated
  or edited.
- The manifest records each original workspace-relative location and SHA-256,
  exported SHA-256, and transformation type. Generated notices explicitly have
  no corresponding source file.

`MANIFEST.json` seals the 209 exporter-generated files. This guide was authored
separately and is outside that list. Historical documents or code retaining
original contract hashes **do not claim that the current public copies pass
those original contracts**.

## Verification and reading aggregate results

From the repository root, verification uses standard Python and does not
require raw data or PyTorch:

```bash
python scripts/prepare_research_archive.py --verify
```

Use the helper below to read either split or unsplit summaries:

```python
from scripts.read_archive_summary import read_summary

summary = read_summary(
    "research_archive/studies/four_factor_attention_v18/SUMMARY.json"
)
score = summary["methods"]["four_factor_sink"]["overall_protocol_macro"]["metrics"]["p_true"]
print(score["mean"], score["ci95"])
```

For v17, pass
`research_archive/studies/formula_search_v17/SUMMARY.json` to the same helper
to reconstruct the complete structure. At export time, each of the three
reconstructed summaries was checked for exact equality to its original summary
after path substitution only. Verifying public file hashes is different from
rescoring experiments using private predictions and ground truth.

## Execution scope and access requirements

**The historical training scripts are not portable runners that reproduce the
experiments from a public clone alone.** They require the original workspace,
frozen contracts, private splits, and earlier models. Do not arbitrarily restore
paths or disable hash checks and claim to have reproduced the original runs.
Use the [root README](../README.md) examples to check the standalone package.

Project-controlled code and documentation use [Apache-2.0](../LICENSE), subject
to the preserved [third-party notices](../THIRD_PARTY_NOTICES.md).
Dataset and weight redistribution requires separate approval. Obtain any
required private assets through an authorized collaboration channel.
See the [release checklist](../docs/release_checklist.md).

New results belong in a separate experiment lineage, without overwriting
originals. The exporter refuses to regenerate into an existing output directory;
`--verify` does not modify files.
