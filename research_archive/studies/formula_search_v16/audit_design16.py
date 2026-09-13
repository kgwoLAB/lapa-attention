"""Independent, read-only data/design audit; never reads prediction metrics.

``audit(data_by_split)`` accepts merged native rows keyed by train,
development, evaluation. With no argument it verifies and loads the canonical
clean/gold files against the frozen v15 contract. The command-line entry point
creates DESIGN_AUDIT.json exactly once; it does not train or select a model.
"""
from collections import Counter
from itertools import combinations
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parent
WORKSPACE = next(p for p in ROOT.parents if (p / "lapa-attention/src/lapa").is_dir())
sys.path.insert(0, str(WORKSPACE / "lapa-attention/src"))
from lapa.data.schema import select_program, validate_record
from lapa.programs.bank import native_bank

PROTOCOLS = ("dns", "modbus", "tls", "smb2")
SPLITS = ("train", "development", "evaluation")
DEV_LIMIT = 32


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def target_kind(row, field):
    if field["target"] is None:
        return "NULL"
    return "END" if field["target"] == row["byte_length"] else "INTERIOR"


def selected_development(rows):
    """Selection is solely by raw hash, with message ID as deterministic tie."""
    return {
        protocol: sorted((r for r in rows if r["protocol"] == protocol),
                         key=lambda r: (r["raw_sha256"], r["message_id"]))[:DEV_LIMIT]
        for protocol in PROTOCOLS
    }


def canonical_data():
    frozen = json.loads((STUDY / "three_to_one_v15/DATA_CONTRACT.json").read_text())
    data, inputs = {}, {}
    for split in SPLITS:
        paths = {kind: STUDY / f"baseline_extension_v7/data/{kind}/{split}.jsonl"
                 for kind in ("clean", "gold")}
        for path in paths.values():
            digest = sha(path)
            assert digest == frozen["inputs"][str(path)], str(path)
            inputs[str(path)] = digest
        clean, gold = (read_rows(paths[kind]) for kind in ("clean", "gold"))
        lookup = {r["message_id"]: r for r in clean}
        assert len(lookup) == len(clean) == len(gold)
        merged = []
        for row in gold:
            raw = lookup[row["message_id"]]
            assert set(raw) == {"message_id", "data_hex", "byte_length", "raw_sha256"}
            assert raw["raw_sha256"] == row["raw_sha256"]
            assert raw["byte_length"] == row["byte_length"]
            merged.append(dict(row, data_hex=raw["data_hex"]))
        data[split] = merged
    return data, inputs


def describe(rows, bank):
    strata = Counter()
    operators = Counter()
    slots = Counter()
    axes = {axis: Counter() for axis in bank.axis_names}
    for row in rows:
        ordered = sorted(row["fields"], key=lambda f: (f["start"], f["end"], f["semantic"]))
        for slot, field in enumerate(ordered):
            strata[(row["protocol"], field["relation"], target_kind(row, field))] += 1
            program_id = select_program(field, row["protocol"], bank)
            operators[program_id] += 1
            slots[slot] += 1
            for axis, value in bank.programs[program_id].axis_values().items():
                axes[axis][value] += 1
    return {
        "messages": len(rows),
        "fields": sum(strata.values()),
        "protocol_messages": dict(sorted(Counter(r["protocol"] for r in rows).items())),
        "strata": [dict(protocol=p, relation=r, target_kind=k, n_fields=n)
                   for (p, r, k), n in sorted(strata.items())],
        "operator_positive_labels": {str(k): v for k, v in sorted(operators.items())},
        "axis_positive_labels": {axis: dict(sorted(counts.items())) for axis, counts in axes.items()},
        "positive_ordinal_slot_fields": {str(k): v for k, v in sorted(slots.items())},
    }


def overlap(left, right):
    return {
        key: sorted({r[key] for r in left} & {r[key] for r in right})
        for key in ("raw_sha256", "group_id", "capture_sha256")
    }


def audit(data_by_split=None):
    inputs = {}
    if data_by_split is None:
        data_by_split, inputs = canonical_data()
    assert set(data_by_split) == set(SPLITS)
    for split, rows in data_by_split.items():
        assert {r["protocol"] for r in rows} == set(PROTOCOLS)
        assert len({r["message_id"] for r in rows}) == len(rows), split
        for row in rows:
            validate_record(row)
            assert 0 < len(row["fields"]) < 64

    bank = native_bank()
    split_overlaps = {}
    for a, b in combinations(SPLITS, 2):
        shared = overlap(data_by_split[a], data_by_split[b])
        assert not shared["raw_sha256"] and not shared["group_id"], (a, b, shared)
        # Existing train/development captures overlap. Never claim otherwise.
        if "evaluation" in (a, b):
            assert not shared["capture_sha256"], (a, b, shared)
        split_overlaps[f"{a}/{b}"] = {
            "counts": {key: len(values) for key, values in shared.items()},
            "shared_values": shared,
        }

    chosen_dev = selected_development(data_by_split["development"])
    folds = {}
    for target in PROTOCOLS:
        sources = [p for p in PROTOCOLS if p != target]
        fit = [r for r in data_by_split["train"] if r["protocol"] in sources]
        target_eval = [r for r in data_by_split["evaluation"] if r["protocol"] == target]
        source_description, target_description = (describe(rows, bank) for rows in (fit, target_eval))
        available_slots = set(source_description["positive_ordinal_slot_fields"])
        unexposed_slots = {
            slot: count for slot, count in target_description["positive_ordinal_slot_fields"].items()
            if slot not in available_slots
        }
        operator_exposure = []
        for program_id, count in target_description["operator_positive_labels"].items():
            program = bank.programs[int(program_id)]
            operator_exposure.append({
                "program_id": int(program_id), "program": program.to_dict(),
                "evaluation_fields": count,
                "source_train_same_program_fields": source_description["operator_positive_labels"].get(program_id, 0),
                "source_train_axis_value_fields": {
                    axis: source_description["axis_positive_labels"][axis].get(value, 0)
                    for axis, value in program.axis_values().items()
                },
            })
        inner_folds = []
        for validation in sources:
            train_protocols = [p for p in sources if p != validation]
            inner_train = [r for r in data_by_split["train"] if r["protocol"] in train_protocols]
            inner_dev = chosen_dev[validation]
            shared = overlap(inner_train, inner_dev)
            assert not shared["raw_sha256"] and not shared["group_id"]
            assert target not in train_protocols + [validation]
            inner_folds.append({
                "train_protocols": train_protocols, "validation_protocol": validation,
                "validation_messages": len(inner_dev),
                "overlap_counts": {key: len(values) for key, values in shared.items()},
                "target_protocol_in_training_or_selection": False,
            })
        final_overlap = overlap(fit + [r for p in sources for r in chosen_dev[p]], target_eval)
        assert all(not value for value in final_overlap.values())
        folds[target] = {
            "sources": sources, "source_training": source_description,
            "evaluation": target_description, "operator_exposure": operator_exposure,
            "target_positive_slots_without_source_positive_labels": unexposed_slots,
            "target_fields_at_unexposed_positive_slots": sum(unexposed_slots.values()),
            "slot_note": "Unexposed positive slots remain eligible for negative presence sampling; no positive endpoint/source/program supervision.",
            "inner_folds": inner_folds,
            "final_fit_evaluation_overlap_counts": {key: len(values) for key, values in final_overlap.items()},
        }

    return {
        "audit_version": 1,
        "status": "PASS_WITH_DOCUMENTED_LIMITATIONS",
        "reads_prediction_metrics": False,
        "uses_evaluation_labels_for_candidate_selection": False,
        "canonical_input_sha256": inputs,
        "audit_source_sha256": sha(__file__),
        "real_capture_data_only": True,
        "historically_inspected_evaluation": True,
        "split_overlaps": split_overlaps,
        "split_descriptions": {split: describe(rows, bank) for split, rows in data_by_split.items()},
        "development_selection": {
            "criterion": "First32 perprotocol by(raw_sha256,message_id); no label/score-dependent subsampling",
            "protocols": {
                p: {"message_ids": [r["message_id"] for r in rows],
                    "raw_sha256": [r["raw_sha256"] for r in rows],
                    "description": describe(rows, bank)} for p, rows in chosen_dev.items()
            },
        },
        "program_bank": dict(fingerprint=bank.fingerprint, **bank.manifest()),
        "outer_folds": folds,
        "selection_metric": {
            "per_field": "log(byte_length+2) + log(max(p_true,1e-30))",
            "within_protocol": "Equal-weight mean of nonempty relation x target_kind stratum means",
            "outer_fold": "Equal-weight mean of the three inner validation protocol scores, then search seeds",
            "direction": "larger_is_better",
            "note": "Uniform-relative gain changes cross-protocol scaling, but has identical candidate ranking to negativeNLL on identical examples and weights.",
        },
        "limitations": [
            "Canonical train/development have2 shared capture hashes; they are raw/group-disjoint, not capture-disjoint.",
            "Inner DNS/TLS held-out-protocol validation can share a capture with its other-protocol training set.",
            "Final evaluation is raw/group/capture-disjoint but historically inspected; exploratory, not newblind confirmation.",
            "Modbus/TLS length targets are allEND; END-only accuracy does not demonstrate address arithmetic.",
            "OuterDNS has119/266 evaluation fields in ordinalslots without source-positive training labels.",
            "A known shared operator bank is a structuralprior; goldprogram selection is training-label construction only.",
            "DNS maskedpointer andSMB2 compoundlittle-endian operators have zero positive labels when their protocol is heldout.",
            "Programheads already factor width/endian/sign/base/mask; three newfactor names alone are not an architecture novelty.",
            "Endpoint scores assume ordinal query slots; they do not establish successful unknown-field discovery.",
            "Perouter selected formula may differ; cannot call a global formula targetblind by pooling allprotocol devlabels.",
            "Three final seeds quantify a small training-seed sample; they are not independent captures or robust population uncertainty.",
        ],
    }


if __name__ == "__main__":
    result = audit()
    output = ROOT / "DESIGN_AUDIT.json"
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "output": str(output),
                      "split_overlap_counts": {key: value["counts"] for key, value in result["split_overlaps"].items()},
                      "unexposed_positive_slot_fields": {p: fold["target_fields_at_unexposed_positive_slots"] for p, fold in result["outer_folds"].items()}}, indent=2))
