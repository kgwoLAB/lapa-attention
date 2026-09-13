"""Inputs shared by untrained API examples; no benchmark data are fabricated."""

import argparse
from pathlib import Path

import torch
from lapa import ModelInputs
from lapa.data.collate import collate_slots
from lapa.data.dataset import NativeDataset


def sample_inputs(model):
    parser = argparse.ArgumentParser(
        description="Untrained API smoke demonstration, not an accuracy experiment."
    )
    parser.add_argument(
        "--data", type=Path,
        help="Optional locally approved NativeDataset JSONL; omitted by default.",
    )
    parser.add_argument("--index", type=int, default=0, help="Dataset row index (default: 0).")
    args = parser.parse_args()
    if args.index < 0:
        parser.error("--index must be nonnegative")
    if args.data is None:
        if args.index != 0:
            parser.error("--index requires --data")
        # Fixed integers only: no protocol semantics, labels, or performance claim.
        data = torch.arange(16, dtype=torch.long).unsqueeze(0)
        inputs = ModelInputs(
            data=data,
            observed=torch.ones_like(data, dtype=torch.bool),
            slots=torch.tensor([0], dtype=torch.long),
        )
        return inputs, "fixed numeric tensor; not a protocol or benchmark"
    try:
        dataset = NativeDataset(args.data)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if args.index >= len(dataset):
        parser.error(f"--index must be less than {len(dataset)}")
    # Labels stay outside the forward call and are not scored in these examples.
    inputs = collate_slots([(dataset[args.index], 0)], model.bank).inputs
    return inputs, "user-supplied local dataset; no accuracy evaluation"
