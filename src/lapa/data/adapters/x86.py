"""Read preserved address-study panels without converting them into field F1.

Historical query IDs, view starts and B3 programs remain in the archive. This
loader does NOT claim they are equivalent to native-v4 ordinal field queries.
"""
import torch


def load_panel(path, panel="x86_train"):
    archive = torch.load(path, map_location="cpu", weights_only=True)
    panels = archive.get("panels", archive)
    if panel not in panels or not isinstance(panels[panel], dict) or "row" not in panels[panel]:
        raise ValueError("choose a stored natural panel, e.g. x86_train or x86_binary_heldout")
    return panels[panel]
