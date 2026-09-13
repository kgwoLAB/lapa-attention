from collections import defaultdict
import hashlib
import json
from pathlib import Path
import torch
from ..data.collate import collate_slots
from ..data.dataset import NativeDataset
from ..models.heads.field import decode_field
from .metrics import field_counts, field_metrics
from .diagnostics import positive_diagnostics


@torch.no_grad()
def evaluate(model, data_path, output_dir, *, threshold=.5, slots_per_batch=16, max_messages=None):
    if not 0 <= threshold <= 1 or slots_per_batch < 1 or (max_messages is not None and max_messages < 1):
        raise ValueError("invalid threshold or batch size")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=False)
    dataset = NativeDataset(data_path)
    rows = dataset.rows if max_messages is None else dataset.rows[:max_messages]
    if not rows:
        raise ValueError("no evaluation rows")
    if max(len(r["fields"]) for r in rows) > model.config.slots:
        raise ValueError("configured slots cannot cover the declared evaluation fields")
    model.eval()
    device = next(model.parameters()).device
    counts, diagnostics = defaultdict(lambda: [0, 0, 0]), defaultdict(list)
    predictions = []
    for record in rows:
        chosen, diag = [], []
        # No oracle field count is used to select inference queries.
        for begin in range(0, model.config.slots, slots_per_batch):
            slots = range(begin, min(begin + slots_per_batch, model.config.slots))
            batch = collate_slots([(record, s) for s in slots], model.bank).to(device)
            output = model(batch.inputs)
            for i in range(len(batch.inputs.slots)):
                field = decode_field(output, i, model.bank, threshold)
                if field is not None:
                    chosen.append({"slot": int(batch.inputs.slots[i]), **field})
            diag += positive_diagnostics(output, batch.labels)
        predictions.append({"message_id": record["message_id"], "protocol": record["protocol"], "fields": chosen})
        diagnostics[record["protocol"]] += diag
    # Persist decoded predictions before the ground-truth field comparison.
    pred_path = destination / "predictions.jsonl"
    pred_path.write_text("".join(json.dumps(p) + "\n" for p in predictions))
    for record, pred in zip(rows, predictions):
        c = field_counts(record["fields"], pred["fields"])
        counts[record["protocol"]] = [a + b for a, b in zip(counts[record["protocol"]], c)]
    protocols = {}
    for protocol, c in counts.items():
        d = diagnostics[protocol]
        protocols[protocol] = {**field_metrics(c), "positive_queries": len(d),
                               "endpoint_nll": sum(x["nll"] for x in d) / len(d) if d else None,
                               "endpoint_hit1": sum(x["hit1"] for x in d) / len(d) if d else None}
    all_four = set(protocols) == {"dns", "modbus", "tls", "smb2"}
    result = {"status": "COMPLETE_SELECTED_COHORT", "config": model.config.to_dict(), "threshold": threshold,
              "messages": len(rows), "fields": sum(len(r["fields"]) for r in rows), "protocols": protocols,
              "protocol_macro_field_f1": sum(p["f1"] for p in protocols.values()) / 4 if all_four else None,
              "protocol_macro_endpoint_nll": sum(p["endpoint_nll"] for p in protocols.values()) / 4 if all_four else None,
              "pooled": field_metrics([sum(c[i] for c in counts.values()) for i in range(3)]),
              "prediction_sha256": hashlib.sha256(pred_path.read_bytes()).hexdigest(),
              "data_sha256": hashlib.sha256(Path(data_path).read_bytes()).hexdigest(),
              "partial_selection": max_messages is not None and len(rows) < len(dataset),
              "presence_head_supervised": model.config.task == "field_discovery",
              "field_score_role": "primary" if model.config.task == "field_discovery" else "untrained_presence_head_diagnostic_only",
              "interpretation": "fixed supplied cohort; not new independent protocol generalization"}
    (destination / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    (destination / "diagnostics.json").write_text(json.dumps(dict(diagnostics), indent=2) + "\n")
    return result
