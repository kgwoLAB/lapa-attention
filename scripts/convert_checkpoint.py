"""Explicit native-v4 state-dict conversion; no guessed partial loading."""
import argparse
from pathlib import Path
import hashlib
import torch
from lapa import LapaConfig, LapaModel
from lapa.training.checkpoint import save_checkpoint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--attention", choices=("rope", "cope", "tape"), required=True)
    parser.add_argument("--lapa", choices=("on", "off"), required=True)
    args = parser.parse_args()
    state = torch.load(args.input, map_location="cpu", weights_only=True)
    model = LapaModel(LapaConfig(attention=args.attention, lapa_enabled=args.lapa == "on"))
    # Existing full_xroute_native_v4 names are deliberately preserved.
    model.load_state_dict(state, strict=True)
    save_checkpoint(args.output, model, {"origin": "full_xroute_native_v4",
                    "source_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
                    "weights_changed": False, "legacy_filename": args.input.name})
    print(args.output)


if __name__ == "__main__":
    main()
