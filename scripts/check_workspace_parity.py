"""Optional one-time migration check against the source workspace.

Not imported by the installed package or normal tests; no training or version
search. Compares the same frozen six representative checkpoint tensors.
"""
import argparse
import importlib
import json
from pathlib import Path
import sys
import torch
from lapa import LapaModel, LapaConfig
from lapa.data.dataset import NativeDataset
from lapa.data.collate import collate_slots


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    sys.path.insert(0, str(args.workspace.resolve()))
    legacy = importlib.import_module("openAI.packet_attention_v3m.paper.more_experiement.source_destination_decomposition.prior_method_field_study_v2.full_xroute_native_v4.model")
    root = Path(__file__).resolve().parents[1]
    dataset = NativeDataset(root / "data/native_v4/evaluation.jsonl")
    selected = [next(r for r in dataset.rows if r["protocol"] == p) for p in ("dns", "modbus", "tls", "smb2")]
    records = []
    for backbone in ("rope", "cope", "tape"):
        for mode in ("off", "on"):
            run = f"{backbone}_{mode}_2026090720"
            state = torch.load(root / "artifacts/checkpoints/legacy_native_v4" / run / "model.pt", map_location="cpu", weights_only=True)
            old = legacy.FullXRouteNative().eval()
            old.load_state_dict(state, strict=True)
            new = LapaModel(LapaConfig(attention=backbone, lapa_enabled=mode == "on")).eval()
            new.load_state_dict(state, strict=True)
            errors = {}
            # Mixed lengths, multiple positive and absent fixed slots.
            samples = [(r, slot) for r in selected for slot in (0, 1, 63)]
            batch = collate_slots(samples, new.bank)
            with torch.no_grad():
                a = old(batch.inputs.data, batch.inputs.observed, batch.inputs.slots, backbone, mode == "on")
                b = new(batch.inputs)
            for key in ("presence_logits", "source", "program_logits", "program", "base", "final"):
                errors[key] = float((a[key] - b[key]).abs().max())
                torch.testing.assert_close(a[key], b[key], atol=2e-6, rtol=2e-6)
            if mode == "on":
                for key in ("prior", "bias", "real", "sink", "top", "wellformed"):
                    errors["route_" + key] = float((a["route"][key] - b["route"][key]).abs().max())
                    torch.testing.assert_close(a["route"][key], b["route"][key], atol=2e-6, rtol=2e-6)
            records.append({"condition": run, "samples": len(samples), "max_abs_error": errors})
    result = {"status": "PASS", "scope": "six frozen checkpoint native forward comparisons; not re-training or full-paper fidelity", "conditions": records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
