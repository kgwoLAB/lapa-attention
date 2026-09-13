# Data contracts

## Native field records

Locally retained `data/native_v4/{train,development,evaluation}.jsonl` files are
unchanged copies; they are Git-ignored and are not included in a GitHub clone.
Each line includes message_id, protocol, raw_sha256, data_hex, capture_sha256,
group_id, capture_id, byte_length and fields. Fields have start, end (exclusive),
semantic, relation, value and target. A null target means NULL, an integer equal
to byte_length means END. The raw hexadecimal bytes are included, not fetched.

The loader validates byte lengths, hashes and annotation bounds and orders
fields by `(start, end, semantic)` as in native-v4. That ordering assigns the
training ordinal labels. Inference evaluates all fixed slots, not a supplied
number of gold fields. Protocol/field annotations are used by the data layer
and evaluator, not by the model forward.

## Historical address archive

The existing DNS/x86 development/terminal tensors retain `row`, `labels` and
per-row provenance records, query IDs, view starts, original B3 program IDs,
and the original splits. `torch.load(..., weights_only=True)` loads them.
`lapa.data.adapters.x86.load_panel` provides direct natural-panel access.

These archives are NOT silently converted into native-v4 field records. The
older task has different query/coordinate/supervision contracts. The current
training CLI consumes native field JSONL; exact historical address-study replay
is outside this release. These data remain local-only and Git-ignored;
collaborators need separately approved access and redistribution clearance.

The terminal archive includes previously generated pointer/displacement edits
and length-scaling windows. They remain identified in the original manifests;
they are not relabeled as newly collected natural traffic. No new edited packets
or synthetic protocols are created by this repository.
