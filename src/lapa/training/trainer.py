import hashlib
import json
from pathlib import Path
import random
import time
import torch
from ..models.model import LapaModel
from ..data.dataset import NativeDataset
from ..data.collate import collate_slots
from .losses import joint_loss, LossWeights
from .checkpoint import save_checkpoint


def train(config, data_path, output_dir, *, steps=600, seed=2026090720, per_protocol=4,
          lr=.002, weight_decay=.01, device="cpu", threads=1):
    if steps < 1 or per_protocol < 1:
        raise ValueError("positive steps and per-protocol batch size required")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(threads)
    random.seed(seed)
    torch.manual_seed(seed)
    model = LapaModel(config).to(device)
    rows = NativeDataset(data_path).rows
    if max(len(r["fields"]) for r in rows) > config.slots:
        raise ValueError("configured slots cannot cover all annotated fields")
    groups = {p: [r for r in rows if r["protocol"] == p] for p in ("dns", "modbus", "tls", "smb2")}
    groups = {p: group for p, group in groups.items() if group}
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    rng = random.Random(seed)
    weights = LossWeights() if config.task == "field_discovery" else LossWeights(0, 0, 0, 1)
    curve, stream = [], hashlib.sha256()
    started = time.monotonic()
    model.train()
    for step in range(steps):
        samples = []
        for group in groups.values():
            for _ in range(per_protocol):
                row = rng.choice(group)
                count = len(row["fields"])
                if config.task == "endpoint" or rng.random() < .5 or count == config.slots:
                    if count == 0:
                        raise ValueError("endpoint sampling needs annotated positive fields")
                    slot = rng.randrange(count)
                else:
                    slot = rng.randrange(count, config.slots)
                samples.append((row, slot))
        stream.update(json.dumps([(r["message_id"], s) for r, s in samples]).encode())
        batch = collate_slots(samples, model.bank).to(device)
        optimizer.zero_grad(set_to_none=True)
        output = model(batch.inputs)
        loss, components = joint_loss(output, batch.labels, weights)
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite training loss")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        rec = {"step": step + 1, "loss": float(loss.detach()), **{k: float(v.detach()) for k, v in components.items()}}
        curve.append(rec)
        if step == 0 or (step + 1) % 100 == 0 or step + 1 == steps:
            print(json.dumps(rec), flush=True)
    metadata = {"seed": seed, "steps": steps, "seconds": time.monotonic() - started,
                "training_data_sha256": hashlib.sha256(Path(data_path).read_bytes()).hexdigest(),
                "stream_sha256": stream.hexdigest(), "torch": str(torch.__version__),
                "loss_weights": vars(weights), "training_recipe": "package_native_v4_port_not_historical_rng_replay",
                "per_protocol": per_protocol, "lr": lr, "weight_decay": weight_decay, "device": device}
    save_checkpoint(destination / "model.pt", model, metadata)
    (destination / "training_curve.json").write_text(json.dumps(curve, indent=2) + "\n")
    (destination / "run.json").write_text(json.dumps({"config": config.to_dict(), **metadata}, indent=2) + "\n")
    return model
