"""Execute installed wheel outside the source tree, rejecting legacy imports."""
import argparse
import importlib.abc
import json
from pathlib import Path
import sys


class NoLegacyImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "openAI" or fullname.startswith("openAI.") or fullname.startswith("packet_attention_v3m"):
            raise ImportError("legacy workspace imports prohibited in standalone check")
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    site = args.site.resolve()
    sys.path.insert(0, str(site))
    sys.meta_path.insert(0, NoLegacyImports())
    import torch
    import lapa
    from lapa.data import NativeDataset, collate_slots
    torch.set_num_threads(1)
    if not Path(lapa.__file__).resolve().is_relative_to(site):
        raise AssertionError("import did not come from isolated wheel installation")
    model = lapa.LapaModel().eval()
    row = NativeDataset(args.data)[0]
    inputs = collate_slots([(row, 0)], model.bank).inputs
    conditions = []
    with torch.no_grad():
        for attention in ("sdpa", "rope", "cope", "tape"):
            for enabled in (False, True):
                output = model(inputs, attention=attention, lapa_enabled=enabled)
                torch.testing.assert_close(output["final"].sum(-1), torch.ones(1))
                conditions.append(f"{attention}_{'on' if enabled else 'off'}")
    result = {"status": "PASS", "cwd": str(Path.cwd()), "package_path": str(Path(lapa.__file__).resolve()),
              "version": lapa.__version__, "conditions": conditions, "legacy_imports": False,
              "torch": str(torch.__version__)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
