import argparse
from pathlib import Path
import yaml
from lapa import LapaConfig
from lapa.training.trainer import train


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/experiments/backbone_grid.yaml"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int)
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    for seed in cfg["seeds"]:
        for attention in cfg["attention"]:
            for enabled in cfg["lapa_enabled"]:
                name = f"{attention}_{'on' if enabled else 'off'}_{seed}"
                model = LapaConfig(attention=attention, lapa_enabled=enabled)
                train(model, cfg["data"], args.output / name, steps=args.steps or cfg["steps"], seed=seed)


if __name__ == "__main__":
    main()
