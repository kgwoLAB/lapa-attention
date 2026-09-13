from torch import nn


class FieldPresence(nn.Linear):
    def __init__(self, dim):
        super().__init__(dim, 1)


def decode_field(output, row, bank, threshold=.5):
    """Decode the same source/program/endpoint decision as native-v4."""
    if output["presence_logits"][row].sigmoid().item() < threshold:
        return None
    source = output["source"][row].argmax().item()
    program_id = output["program"][row, source].argmax().item()
    program = bank.programs[program_id]
    length = int(output["observed"][row].sum())
    if source + program.width > length or program.semantic == "OTHER":
        return None
    target = output["final"][row].argmax().item()
    storage = output["observed"].shape[1]
    target = "END" if target == storage else "NULL" if target == storage + 1 else target
    return {"start": source, "end": source + program.width, "semantic": program.semantic,
            "target": target, "program_id": program_id}
