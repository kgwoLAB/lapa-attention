# Workspace extraction map

| Original research component | Standalone location |
|---|---|
| `full_xroute_native_v4/model.py::FullXRouteNative` | `models/model.py::LapaModel` |
| `NativeRouter` / `_XRouteRouter` | `routing/{source,program,router}.py` |
| `execute_native`, adjacent programs | `programs/{schema,bank,decode,executor}.py` |
| `_SharedSelfAttention` / `_EncoderBlock` | `models/transformer.py`, `attention/` |
| `_encode`, `_retrieval_logits` | `models/byte_encoder.py` |
| `position_attention.py` | `attention/{rope,cope,tape}.py` |
| Native-v4 joint loss and fixed slots | `training/losses.py`, `data/collate.py` |
| Native field evaluator | `evaluation/`, `models/heads/field.py` |

The public package has no `openAI.*` import, author-workstation dependency,
or `paper/` runtime dependency. Existing model parameter names are retained for
strict state-dict conversion. Constructors now use validated configuration
instead of module-level hidden-dimension constants.

`scripts/import_workspace_data.py --workspace ...` is an optional one-time asset
import utility. `scripts/check_workspace_parity.py --workspace ... --output ...`
is an optional one-time migration check. Neither is called by normal training,
evaluation, examples, unit tests or installed-package imports.

This extraction does not modify or move the original study files, checkpoints,
running jobs, dataset splits or reports. There is no new git repository/remote
creation or external publication in this local build.
