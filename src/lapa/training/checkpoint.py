from pathlib import Path
import torch
from ..config import LapaConfig
from ..models.model import LapaModel

SCHEMA = "lapa-native-v4-port-v1"


def save_checkpoint(path, model, metadata=None):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema": SCHEMA, "config": model.config.to_dict(), "bank_fingerprint": model.bank.fingerprint,
               "state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()}, "metadata": metadata or {}}
    torch.save(payload, path)


def load_checkpoint(path, device="cpu"):
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if payload.get("schema") != SCHEMA:
        raise ValueError("not a packaged checkpoint; use explicit legacy conversion")
    model = LapaModel(LapaConfig(**payload["config"]))
    if payload.get("bank_fingerprint") != model.bank.fingerprint:
        raise ValueError("program ordering/configuration mismatch")
    model.load_state_dict(payload["state_dict"], strict=True)
    return model.to(device), payload.get("metadata", {})
