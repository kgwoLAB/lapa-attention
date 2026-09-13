import argparse
from dataclasses import replace
from pathlib import Path
from lapa import LapaConfig
from lapa.training.trainer import train


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    parser.add_argument("--attention", choices=("sdpa", "rope", "cope", "tape"))
    parser.add_argument("--lapa", choices=("on", "off"))
    parser.add_argument("--data", type=Path, default=Path("data/native_v4/train.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=600)
    parser.add_argument("--seed", type=int, default=2026090720)
    parser.add_argument("--per-protocol", type=int, default=4)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()
    config = LapaConfig.from_file(args.config)
    if args.attention:
        config = replace(config, attention=args.attention)
    if args.lapa:
        config = replace(config, lapa_enabled=args.lapa == "on")
    train(config, args.data, args.output, steps=args.steps, seed=args.seed,
          per_protocol=args.per_protocol, device=args.device, threads=args.threads)


if __name__ == "__main__":
    main()
