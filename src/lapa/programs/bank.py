from dataclasses import dataclass
import hashlib
import json
import torch
from .schema import Program, BASES


@dataclass(frozen=True)
class ProgramBank:
    programs: tuple
    name: str = "native_v4"
    axis_names: tuple = ("width", "endian", "sign", "base", "mask")

    def __post_init__(self):
        if not self.programs or len(set(self.programs)) != len(self.programs):
            raise ValueError("program bank must be nonempty and unique")

    def __len__(self):
        return len(self.programs)

    def axis_vocabulary(self):
        return {a: tuple(dict.fromkeys(p.axis_values()[a] for p in self.programs)) for a in self.axis_names}

    def axis_ids(self):
        vocabulary = self.axis_vocabulary()
        return {a: torch.tensor([vocabulary[a].index(p.axis_values()[a]) for p in self.programs], dtype=torch.long) for a in self.axis_names}

    def manifest(self):
        return {"name": self.name, "programs": [p.to_dict() for p in self.programs], "axis_names": list(self.axis_names)}

    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.manifest(), sort_keys=True).encode()).hexdigest()


def native_bank():
    # Preserve the exact historical B3 order, followed by the eight native-v4
    # adjacent operations. These IDs are part of the checkpoint contract.
    programs = [Program(w, e, b, signed=s) for w in (1, 2, 3, 4)
                for e in (("big",) if w == 1 else ("big", "little"))
                for s in (False, True) for b in BASES[:4]]
    programs += [Program(2, e, b, mask=0x3fff, guard_mask=0xc000, guard_value=0xc000)
                 for e in ("big", "little") for b in ("packet_absolute", "field_start_forward")]
    programs += [Program(w, e, b) for w in (2, 4) for e in ("big", "little") for b in BASES[4:]]
    return ProgramBank(tuple(programs))
