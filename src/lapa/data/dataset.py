import json
from pathlib import Path
from torch.utils.data import Dataset
from .schema import validate_record


class NativeDataset(Dataset):
    def __init__(self, path, protocol=None):
        self.path = Path(path)
        self.rows = []
        for line in self.path.read_text().splitlines():
            row = validate_record(json.loads(line))
            if protocol is None or row["protocol"] == protocol:
                row["fields"] = sorted(row["fields"], key=lambda f: (f["start"], f["end"], f["semantic"]))
                self.rows.append(row)
        if not self.rows:
            raise ValueError("empty selected dataset")
        if len({r["message_id"] for r in self.rows}) != len(self.rows):
            raise ValueError("duplicate message IDs")

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        return self.rows[index]
