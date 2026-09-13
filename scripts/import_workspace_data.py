"""Copy explicitly selected existing assets; never regenerate/re-split packets."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DECOMP = Path("openAI/packet_attention_v3m/paper/more_experiement/source_destination_decomposition")
STUDY = DECOMP / "prior_method_field_study_v2"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    records = []
    def copy(source, relative):
        source = args.workspace / source
        dest = ROOT / relative
        source_sha = digest(source)
        if dest.exists():
            if digest(dest) != source_sha:
                raise FileExistsError(f"preserve conflicting asset: {dest}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
        if digest(dest) != source_sha:
            raise ValueError("copy checksum failure")
        entry = {"path": str(relative), "source": str(source.relative_to(args.workspace)),
                 "sha256": source_sha, "bytes": dest.stat().st_size, "redistribution": "REVIEW_REQUIRED"}
        if dest.suffix == ".jsonl":
            rows = [json.loads(line) for line in dest.read_text().splitlines()]
            entry.update(messages=len(rows), fields=sum(len(r["fields"]) for r in rows),
                         protocols=dict(Counter(r["protocol"] for r in rows)))
        records.append(entry)
    for name in ("train.jsonl", "development.jsonl", "evaluation.jsonl", "config.json"):
        copy(STUDY / "results/xr_field_native_v3" / name, Path("data/native_v4") / name)
    address = DECOMP / "xroute_backbone_factorial/artifacts/v1"
    for name in ("source_manifest.json", "development_manifest.json", "terminal_manifest.json",
                 "development_tensors.pt", "terminal_tensors.pt",
                 "source_manifest.sha256", "development_manifest.sha256", "terminal_manifest.sha256",
                 "development_tensors.sha256", "terminal_tensors.sha256"):
        copy(address / name, Path("data/address_v1") / name)
    for name in ("config.json", "SUMMARY.json", "COPE_PORT_LIMITATION.md"):
        source = STUDY / "full_xroute_native_v4" / name
        if (args.workspace / source).exists():
            copy(source, Path("artifacts/reference/native_v4") / name)
    # Representative checkpoints: FIRST predeclared seed, not best performance.
    # No SDPA checkpoint is invented; no existing checkpoint is retrained.
    for backbone in ("rope", "cope", "tape"):
        for mode in ("off", "on"):
            run = f"{backbone}_{mode}_2026090720"
            source = STUDY / "full_xroute_native_v4/results" / run
            for name in ("model.pt", "metrics.json"):
                if (args.workspace / source / name).exists():
                    copy(source / name, Path("artifacts/checkpoints/legacy_native_v4") / run / name)
    manifest = {"schema": "lapa-local-assets-v1", "created_utc": datetime.now(timezone.utc).isoformat(),
                "status": "LOCAL_COPIES_NOT_CLEARED_FOR_PUBLIC_REDISTRIBUTION", "assets": records,
                "new_synthetic_protocols": False, "new_packet_mutations": False,
                "historical_counterfactual_panels": "Retained unchanged inside address_v1 terminal_tensors.pt; not new real captures.",
                "raw_pcaps_copied": False, "native_bytes": "Exact original prepared JSONL including data_hex; not just pointers or manifests."}
    target = ROOT / "data/manifests/assets.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2) + "\n")
    sources = [STUDY / "full_xroute_native_v4/model.py", STUDY / "full_xroute_native_v4/experiment.py",
               DECOMP / "xroute_backbone_factorial/model.py",
               Path("openAI/codex_phase11_comparators/position_attention.py"),
               Path("openAI/packet_attention_v3m/paper/add_experiment/lapa_ext/algebra.py"),
               Path("openAI/packet_attention_v3m/src/packet_attention_v3m/attention.py")]
    lineage = ROOT / "docs/lineage/source_hashes.json"
    lineage.parent.mkdir(parents=True, exist_ok=True)
    lineage.write_text(json.dumps({str(p): digest(args.workspace / p) for p in sources}, indent=2) + "\n")
    print(json.dumps({"files": len(records), "bytes": sum(r["bytes"] for r in records),
                      "native_splits": [r for r in records if r["path"].endswith("jsonl")]}, indent=2))


if __name__ == "__main__":
    main()
