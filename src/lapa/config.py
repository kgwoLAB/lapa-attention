"""Serializable configuration. No workspace path or implicit model download."""
from dataclasses import asdict, dataclass
from pathlib import Path
import json
import math


@dataclass(frozen=True)
class LapaConfig:
    attention: str = "rope"
    lapa_enabled: bool = True
    task: str = "field_discovery"
    dim: int = 32
    heads: int = 4
    layers: int = 2
    ff_dim: int = 64
    position_size: int = 16
    max_length: int = 1024
    slots: int = 64
    epsilon: float = 0.02
    prior_strength: float = 1.0
    program_bank: str = "native_v4"
    implementation: str = "native_v4_compact"
    injection: str = "retrieval"
    causal: bool = False

    def __post_init__(self):
        if self.attention not in ("sdpa", "rope", "cope", "tape"):
            raise ValueError("attention must be sdpa, rope, cope or tape")
        if self.task not in ("endpoint", "field_discovery"):
            raise ValueError("unknown task")
        if min(self.dim, self.heads, self.layers, self.ff_dim, self.position_size, self.max_length, self.slots) < 1:
            raise ValueError("dimensions must be positive")
        if self.dim % self.heads or (self.dim // self.heads) % 2:
            raise ValueError("dim must be divisible by heads, with even head dimension")
        if self.slots > 256 or not 0 < self.epsilon < 1:
            raise ValueError("slots <= 256 and 0 < epsilon < 1 required")
        if self.prior_strength < 0 or not math.isfinite(self.prior_strength):
            raise ValueError("prior_strength must be finite and nonnegative")
        if self.program_bank != "native_v4" or self.implementation != "native_v4_compact":
            raise ValueError("this release supports the native_v4 bank/compact profile")
        if self.injection != "retrieval" or self.causal:
            raise ValueError("v0.1 uses bidirectional encoding and final retrieval fusion; no causal/full-layer claim")

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_file(cls, path):
        import yaml
        path = Path(path)
        data = json.loads(path.read_text()) if path.suffix == ".json" else yaml.safe_load(path.read_text())
        return cls(**data.get("model", data))
