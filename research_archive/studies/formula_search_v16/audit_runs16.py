"""Independent artifact audit. No training, tuning, or frozen-code changes.

Only this audit's own output is written. Repeat runs preserve earlier audit
snapshots before replacing INDEPENDENT_AUDIT.json. Incomplete model folders are
reported as pending rather than interpreted as zero-valued results.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import statistics
import time

import numpy as np

ROOT = Path(__file__).resolve().parent
PROTOCOLS = ("dns", "modbus", "tls", "smb2")
CLEAN_KEYS = {"message_id", "data_hex", "byte_length", "raw_sha256"}


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def close(a, b):
    assert math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-11), (a, b)


def balanced_gain(records):
    groups = defaultdict(list)
    for row in records:
        groups[row["relation"], row["target_kind"]].append(math.log(row["byte_length"] + 2) - row["nll"])
    return statistics.mean(statistics.mean(values) for values in groups.values())


def stream_evidence(train, sources, seed, steps):
    """Independent replay of frozen protocol/positive/negative sampling recipe."""
    rng = random.Random(seed)
    groups = {protocol: [r for r in train if r["protocol"] == protocol] for protocol in sources}
    stream = hashlib.sha256()
    exposure = Counter()
    for _ in range(steps):
        batch = []
        for j in range(16):
            row = rng.choice(groups[rng.choice(sources)])
            count = len(row["fields"])
            slot = rng.randrange(count) if j < 8 else rng.randrange(count, 64)
            batch.append((row["message_id"], slot))
            exposure[row["protocol"]] += 1
        rng.shuffle(batch)
        stream.update(json.dumps(batch).encode())
    return stream.hexdigest(), dict(exposure)


def distribution(array, shape):
    assert array.shape == shape, (array.shape, shape)
    assert np.isfinite(array).all() and (array >= 0).all()
    np.testing.assert_allclose(array.sum(-1), 1, atol=5e-6, rtol=0)


def main():
    started = time.monotonic()
    code, data = read(ROOT / "CODE_CONTRACT.json"), read(ROOT / "DATA_CONTRACT.json")
    code_hash, data_hash = digest(ROOT / "CODE_CONTRACT.json"), digest(ROOT / "DATA_CONTRACT.json")
    verified = {}

    def verify_file(path, expected):
        path = Path(path).resolve()
        if path not in verified:
            verified[path] = digest(path)
        assert verified[path] == expected, str(path)

    for path, expected in code["files"].items():
        verify_file(path, expected)
    for path, expected in data["files"].items():
        verify_file(ROOT / path, expected)
    assert data["plan_sha256"] == digest(ROOT / "PLAN.md")
    design = read(ROOT / "DESIGN_AUDIT.json")
    for protocol in PROTOCOLS:
        assert data["development_ids"][protocol] == design["development_selection"]["protocols"][protocol]["message_ids"]
    canonical = {split: rows(ROOT / f"data/gold/{split}.jsonl") for split in ("train", "development", "evaluation")}
    clean = {split: {r["message_id"]: r for r in rows(ROOT / f"data/clean/{split}.jsonl")}
             for split in canonical}
    for split in canonical:
        for protocol in PROTOCOLS:
            assert set(data["protocol_ids"][split][protocol]) == {r["message_id"] for r in canonical[split] if r["protocol"] == protocol}
        assert all(set(r) == CLEAN_KEYS for r in clean[split].values())

    snapshots, pending, run_checks = [], [], []
    for pair in itertools.combinations(PROTOCOLS, 2):
        for seed in code["search_seeds"]:
            for variant in code["variants"]:
                folder = ROOT / "search" / "_".join(pair) / f"{variant}_{seed}"
                snapshots.append((folder, "search", list(pair), None, seed, variant, code["search_steps"]))
    assert len(snapshots) == 72
    selection = read(ROOT / "SELECTION.json") if (ROOT / "SELECTION.json").exists() else None
    if selection:
        assert selection["code_contract_sha256"] == code_hash
        assert selection["plan_sha256"] == digest(ROOT / "PLAN.md")
        assert set(selection["choices"]) == set(PROTOCOLS)
        for target in PROTOCOLS:
            choice = selection["choices"][target]
            for seed in code["final_seeds"]:
                for variant in dict.fromkeys(("off", "hybrid", choice["selected"])):
                    folder = ROOT / "final" / target / f"{variant}_{seed}"
                    snapshots.append((folder, "final", choice["sources"], target, seed, variant, code["final_steps"]))

    streams = {}
    probability_archives = prediction_seals = diagnostics_checked = 0
    completed = {}
    for index, (folder, phase, sources, target, seed, variant, steps) in enumerate(snapshots, 1):
        if not (folder / "COMPLETE.json").exists():
            pending.append(str(folder.relative_to(ROOT)))
            continue
        complete, meta = read(folder / "COMPLETE.json"), read(folder / "TRAINING.json")
        assert complete["code_contract_sha256"] == meta["code_contract_sha256"] == code_hash
        assert meta["data_contract_sha256"] == data_hash
        for key, expected in (("phase", phase), ("sources", sources), ("target", target), ("seed", seed), ("variant", variant), ("steps", steps)):
            assert complete[key] == meta[key] == expected, (folder, key)
        assert sources == [p for p in PROTOCOLS if p in sources]
        assert len(sources) == (2 if phase == "search" else 3)
        assert target not in sources
        assert not meta["target_protocol_training"] and not meta["pretrained_checkpoint_used"]
        for name, expected in complete["files"].items():
            path = (folder / name).resolve()
            assert folder in path.parents
            verify_file(path, expected)
        key = (tuple(sources), seed, steps)
        if key not in streams:
            streams[key] = stream_evidence(canonical["train"], sources, seed, steps)
        stream, exposure = streams[key]
        assert meta["stream_sha256"] == stream and meta["source_sample_counts"] == exposure
        curve = read(folder / "curve.json")
        losses = {"endpoint"} if variant == "off" else {"presence", "source", "program", "endpoint"}
        assert set(meta["loss_keys"]) == losses and len(curve) == steps
        for step, row in enumerate(curve, 1):
            assert row["step"] == step and set(row) == losses | {"step", "loss", "grad_norm"}
            assert all(math.isfinite(float(value)) for value in row.values())
            close(row["loss"], sum(row[name] for name in losses)) if variant == "off" else None
        assert meta["endpoint_qk"] == (variant in ("off", "hybrid"))
        assert meta["encoder_qkv"] == (variant != "cnn_joint")
        if variant == "off":
            assert meta["auxiliary_unchanged"]
            assert not any(name.startswith(("host.router.", "presence.")) for name in meta["active_parameter_names"])
        else:
            for prefix in ("host.router.source_score.", "host.router.axis_heads.", "presence."):
                assert any(name.startswith(prefix) for name in meta["active_parameter_names"])
        if variant not in ("off", "hybrid"):
            assert not any("retrieval_query" in name or "retrieval_key" in name or "special_endpoints" in name for name in meta["active_parameter_names"])
        if variant == "cnn_joint":
            assert not any(".attention." in name for name in meta["active_parameter_names"])
        if phase == "final":
            assert meta["selection_sha256"] == digest(ROOT / "SELECTION.json")

        for seal_path in sorted(folder.rglob("PREDICTION_SEAL.json")):
            seal = read(seal_path)
            prediction_seals += 1
            assert seal["gold_read"] is False and seal["protocol_id_input"] is False
            assert seal["slots"] == 64 and set(seal["input_keys"]) == CLEAN_KEYS
            assert seal["variant"] == variant
            is_final_test = phase == "final" and seal_path.parent.name == "evaluation"
            split = "evaluation" if is_final_test else "development"
            included_protocols = [target] if is_final_test else [seal_path.parent.name] if phase == "search" else sources
            if phase == "search":
                assert included_protocols[0] not in sources
            expected_ids = {mid for p in included_protocols for mid in
                            (data["protocol_ids"][split][p] if is_final_test else data["development_ids"][p])}
            assert set(seal["input_ids"]) == expected_ids
            assert len(seal["input_ids"]) == len(set(seal["input_ids"]))
            assert seal["input_hashes"] == [clean[split][mid]["raw_sha256"] for mid in seal["input_ids"]]
            for name, expected in seal["files"].items():
                path = seal_path.parent / name
                verify_file(path, expected)
                if path.suffix != ".npz":
                    continue
                probability_archives += 1
                row = clean[split][path.stem]
                with np.load(path, allow_pickle=False) as archive:
                    for name in ("base", "final", "route"):
                        if name in archive:
                            distribution(archive[name], (64, row["byte_length"] + 2))
                    distribution(archive["source"], (64, row["byte_length"]))
                    distribution(archive["program_at_predicted_source"], (64, len(design["program_bank"]["programs"])))
                    if variant == "off":
                        assert np.array_equal(archive["base"], archive["final"])
            metrics_path = seal_path.parent / "METRICS.json"
            if metrics_path.exists():
                measured = read(metrics_path)
                details = rows(seal_path.parent / "diagnostics.jsonl")
                diagnostics_checked += len(details)
                assert set(measured["by_protocol"]) == set(included_protocols)
                assert measured["prediction_seal_sha256"] == digest(seal_path)
                assert measured["diagnostics_sha256"] == digest(seal_path.parent / "diagnostics.jsonl")
                close(measured["overall"]["balanced_log_gain"], balanced_gain(details))
                for detail in details:
                    assert detail["message_id"] in expected_ids
                    assert detail["protocol"] in included_protocols
                    close(detail["nll"], -math.log(max(detail["p_true"], 1e-30)))
                if is_final_test:
                    stage = rows(folder / "STAGES.jsonl")
                    lookup = {(r["message_id"], r["slot"]): r for r in stage}
                    assert len(lookup) == len(stage) == len(details)
                    for detail in details:
                        stage_row = lookup[detail["message_id"], detail["slot"]]
                        assert stage_row["inputs_gold_free"] is True
                        assert abs(stage_row["final_p"] - detail["p_true"]) <= 1e-6
        completed[str(folder)] = meta
        run_checks.append(dict(phase=phase, folder=str(folder.relative_to(ROOT)), variant=variant,
                               target=target, sources=sources, seed=seed, steps=steps,
                               complete_sha256=digest(folder / "COMPLETE.json")))
        if index % 12 == 0:
            print(json.dumps(dict(audited=len(run_checks), snapshot_total=len(snapshots), seconds=time.monotonic() - started)), flush=True)

    selection_evidence = 0
    if selection:
        for target, choice in selection["choices"].items():
            sources = [p for p in PROTOCOLS if p != target]
            assert choice["sources"] == sources and choice["target_development_used"] is False and choice["target_evaluation_used"] is False
            assert {r["variant"] for r in choice["ranked"]} == set(code["variants"])
            for row in choice["ranked"]:
                expected = {(tuple(pair), next(p for p in sources if p not in pair), seed)
                            for pair in itertools.combinations(sources, 2) for seed in code["search_seeds"]}
                actual = {(tuple(e["pair"]), e["validation"], e["seed"]) for e in row["evidence"]}
                assert actual == expected and len(row["evidence"]) == len(expected) == 6
                for evidence in row["evidence"]:
                    selection_evidence += 1
                    assert target not in evidence["pair"] and evidence["validation"] != target
                    path = ROOT / "search" / "_".join(evidence["pair"]) / f"{row['variant']}_{evidence['seed']}" / "validation" / evidence["validation"] / "METRICS.json"
                    assert str(path) == evidence["path"]
                    verify_file(path, evidence["sha256"])
                    close(evidence["score"], read(path)["overall"]["balanced_log_gain"])
                close(row["score"], statistics.mean(e["score"] for e in row["evidence"]))
            ranked = sorted(choice["ranked"], key=lambda r: (-r["score"], code["variants"].index(r["variant"])))
            assert ranked == choice["ranked"] and choice["selected"] == ranked[0]["variant"]

    paired_initializations = []
    for target in PROTOCOLS:
        for seed in code["final_seeds"]:
            pair = [completed.get(str(ROOT / "final" / target / f"{variant}_{seed}")) for variant in ("off", "hybrid")]
            if all(pair):
                assert pair[0]["initial_sha256"] == pair[1]["initial_sha256"]
                assert pair[0]["stream_sha256"] == pair[1]["stream_sha256"]
                paired_initializations.append(dict(target=target, seed=seed))
    old = read(ROOT.parent / "three_to_one_v15/CODE_CONTRACT.json")
    package_files = {name: value for name, value in old["files"].items() if "/lapa-attention/src/lapa/" in name}
    for name, expected in package_files.items():
        verify_file(name, expected)
    result = dict(status="PASS_COMPLETE" if not pending and selection else "PASS_COMPLETED_SUBSET",
                  time=datetime.now(timezone.utc).isoformat(), seconds=time.monotonic() - started,
                  audit_source_sha256=digest(__file__), code_contract_sha256=code_hash, data_contract_sha256=data_hash,
                  no_training_or_formula_changes=True, pending=pending,
                  search_models=sum(r["phase"] == "search" for r in run_checks),
                  final_models=sum(r["phase"] == "final" for r in run_checks),
                  training_steps=sum(r["steps"] for r in run_checks), deterministic_streams_replayed=len(streams),
                  file_hashes_verified=len(verified), probability_archives_verified=probability_archives,
                  prediction_seals_verified=prediction_seals, endpoint_diagnostics_verified=diagnostics_checked,
                  outer_excluded_selection_evidence=selection_evidence,
                  off_hybrid_paired_initializations=paired_initializations,
                  packaged_lapa_unchanged_files=len(package_files), runs=run_checks,
                  selected={p: r["selected"] for p, r in selection["choices"].items()} if selection else None,
                  uncertainty_note="Integrity and protocol-exclusion checks do not remove historical-test exposure, smallcohort/seed uncertainty, or shared train/dev captures.")
    output = ROOT / "INDEPENDENT_AUDIT.json"
    if output.exists():
        archive = ROOT / "audit_snapshots" / ("INDEPENDENT_AUDIT_" + digest(output)[:16] + ".json")
        archive.parent.mkdir(exist_ok=True)
        if not archive.exists():
            with archive.open("xb") as stream:
                stream.write(output.read_bytes())
    temporary = ROOT / "INDEPENDENT_AUDIT.json.tmp"
    with temporary.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    temporary.replace(output)
    print(json.dumps({k: v for k, v in result.items() if k not in ("runs", "off_hybrid_paired_initializations")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
