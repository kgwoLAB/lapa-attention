"""Check supplied local file identities and optionally every native gold program."""
import argparse
import hashlib
import json
from pathlib import Path
import torch
from lapa.data import NativeDataset, collate_slots
from lapa.data.schema import select_program
from lapa.programs import native_bank, execute


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("artifacts/verification/assets_check.json"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "data/manifests/assets.json").read_text())
    for asset in manifest["assets"]:
        path = root / asset["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != asset["sha256"]:
            raise ValueError(f"asset mismatch: {asset['path']}")
    datasets = {split: NativeDataset(root / f"data/native_v4/{split}.jsonl") for split in ("train", "development", "evaluation")}
    seen, counts = set(), {}
    for split, dataset in datasets.items():
        ids = {r["message_id"] for r in dataset.rows}
        if seen & ids:
            raise ValueError("message ID leakage between fixed native splits")
        seen |= ids
        counts[split] = {"messages": len(dataset), "fields": sum(len(r["fields"]) for r in dataset.rows)}
    checks = 0
    if args.deep:
        torch.set_num_threads(1)
        bank = native_bank()
        for dataset in datasets.values():
            for begin in range(0, len(dataset), 8):
                rows = dataset.rows[begin:begin + 8]
                batch = collate_slots([(row, 0) for row in rows], bank)
                output = execute(bank, batch.inputs.data, batch.inputs.observed)
                storage = batch.inputs.data.shape[1]
                for i, row in enumerate(rows):
                    for field in row["fields"]:
                        source, program = field["start"], select_program(field, row["protocol"], bank)
                        target = storage + 1 if field["target"] is None else storage if field["target"] == row["byte_length"] else field["target"]
                        if not output.valid[i, source, program] or output.target[i, source, program].item() != target:
                            raise AssertionError((row["message_id"], field["relation"], source))
                        checks += 1
    result = {"status": "PASS", "assets": len(manifest["assets"]), "native_splits": counts,
              "message_ids_disjoint": True, "executor_annotation_checks": checks,
              "license_and_privacy_clearance": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
