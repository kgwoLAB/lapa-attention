import argparse
from pathlib import Path
import json
import torch
from lapa.training.checkpoint import load_checkpoint
from lapa.evaluation.evaluator import evaluate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=Path("data/native_v4/evaluation.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=.5, help="Fixed a priori or selected on development, never evaluation")
    parser.add_argument("--max-messages", type=int)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()
    torch.set_num_threads(args.threads)
    model, metadata = load_checkpoint(args.checkpoint, args.device)
    result = evaluate(model, args.data, args.output, threshold=args.threshold, max_messages=args.max_messages)
    result["checkpoint_metadata"] = metadata
    (args.output / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
