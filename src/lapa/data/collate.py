import torch
from ..types import ModelInputs, Supervision, Batch
from .schema import select_program


def collate_slots(samples, bank):
    """samples: (native record, public fixed slot ID) pairs.

    Labels are separated before the model is called. Batch padding changes
    END/NULL output indices, but never changes the packet's native bytes.
    """
    if not samples:
        raise ValueError("empty batch")
    length = max(row["byte_length"] for row, _ in samples)
    data = torch.zeros(len(samples), length, dtype=torch.long)
    observed = torch.zeros_like(data, dtype=torch.bool)
    labels = {k: [] for k in ("present", "sources", "programs", "targets")}
    slots, metadata = [], []
    for i, (row, slot) in enumerate(samples):
        raw = bytes.fromhex(row["data_hex"])
        n = len(raw)
        data[i, :n] = torch.tensor(list(raw), dtype=torch.long)
        observed[i, :n] = True
        slots.append(slot)
        yes = slot < len(row["fields"])
        labels["present"].append(yes)
        if yes:
            field = row["fields"][slot]
            source, program = field["start"], select_program(field, row["protocol"], bank)
            target = length + 1 if field["target"] is None else length if field["target"] == n else field["target"]
        else:
            source = program = target = 0
        for key, value in (("sources", source), ("programs", program), ("targets", target)):
            labels[key].append(value)
        metadata.append({"message_id": row["message_id"], "protocol": row["protocol"], "slot": slot})
    supervision = Supervision(**{k: torch.tensor(v, dtype=torch.bool if k == "present" else torch.long) for k, v in labels.items()})
    return Batch(ModelInputs(data, observed, torch.tensor(slots, dtype=torch.long)), supervision, metadata)
