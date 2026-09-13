"""Outer-target-isolated promotion and two-objective formula selection.

Only source-pair training runs and inner development metrics are consumed.
The held-out outer protocol is excluded from every scored evidence row.
Complete-run artifact hashes are checked before metrics are used. No final
test predictions, test labels, or historical v16 metrics are read here.
"""

import argparse

from common17 import (
    ATTRIBUTE_VARIANTS, PROTOCOLS, REFINE_SEEDS, ROOT, SCREEN_SEEDS, STEPS,
    VARIANTS, canonical_backbone, itertools, job_folder, json, log, math,
    now, read, sha, statistics, verify_choice_file, verify_contract,
    verify_run, write,
)


SCORE_NAMES = ("balanced_p", "balanced_log_gain")
VARIANT_ORDER = {variant: index for index, variant in enumerate(VARIANTS)}
PROMOTED_COUNT = 4


class _EvidenceReader:
    """Verify each reused checkpoint once during a single sealed-stage call."""

    def __init__(self, phase):
        assert phase in ("screen", "refine")
        self.phase = phase
        self.seeds = SCREEN_SEEDS if phase == "screen" else REFINE_SEEDS
        self.verified = {}

    def read(self, outer_target, sources, validation, variant, seed):
        assert outer_target in PROTOCOLS
        assert sources == [p for p in PROTOCOLS if p in sources]
        assert len(sources) == len(set(sources)) == 2
        assert outer_target not in sources and validation != outer_target
        assert validation not in sources and validation in PROTOCOLS
        assert set(sources + [validation]) == set(PROTOCOLS) - {outer_target}
        assert seed in self.seeds and variant in VARIANTS
        job = dict(phase=self.phase, sources=sources, variant=variant, seed=seed,
                   backbone=canonical_backbone(variant, "tape"), target=None)
        folder = job_folder(job)
        if folder not in self.verified:
            complete = verify_run(folder)
            for key in ("phase", "sources", "variant", "seed", "backbone", "target"):
                assert complete[key] == job[key], (folder, key, complete.get(key), job[key])
            assert complete["steps"] == STEPS[self.phase], folder
            self.verified[folder] = complete
        complete = self.verified[folder]
        relative = f"validation/{validation}/METRICS.json"
        assert relative in complete["files"], (folder, relative)
        path = folder / relative
        digest = sha(path)
        assert digest == complete["files"][relative], path
        metrics = read(path)
        assert set(metrics["by_protocol"]) == {validation}, path
        assert metrics["overall"]["n_fields"] > 0, path
        scores = {key: float(metrics["overall"][key]) for key in SCORE_NAMES}
        assert all(math.isfinite(value) for value in scores.values()), path
        assert 0 <= scores["balanced_p"] <= 1, path
        # The hash verifier may read other completed validation artifacts for
        # integrity, but their scores never enter this target's selection.
        return dict(sources=list(sources), validation=validation, seed=seed,
                    path=str(path), sha256=digest, **scores)


def _candidate_rows(target, variants, reader):
    sources = [p for p in PROTOCOLS if p != target]
    assert len(variants) == len(set(variants)) and all(v in VARIANTS for v in variants)
    candidates = []
    for variant in variants:
        evidence = []
        for pair in itertools.combinations(sources, 2):
            validation = next(p for p in sources if p not in pair)
            for seed in reader.seeds:
                evidence.append(reader.read(target, list(pair), validation, variant, seed))
        assert len(evidence) == 3 * len(reader.seeds)
        assert {row["validation"] for row in evidence} == set(sources)
        assert all(sum(e["validation"] == p for e in evidence) == len(reader.seeds)
                   for p in sources)
        candidates.append(dict(
            variant=variant,
            scores={key: statistics.mean(e[key] for e in evidence) for key in SCORE_NAMES},
            evidence=evidence,
        ))
    return sources, candidates


def _rankings(candidates):
    """Higher scores win; every exact tie follows the fixed variant order."""
    assert candidates and len({row["variant"] for row in candidates}) == len(candidates)
    by_metric = {
        key: sorted(candidates, key=lambda row: (-row["scores"][key], VARIANT_ORDER[row["variant"]]))
        for key in SCORE_NAMES
    }
    ranks = {
        key: {row["variant"]: rank for rank, row in enumerate(order)}
        for key, order in by_metric.items()
    }
    summed = sorted(candidates, key=lambda row: (
        sum(ranks[key][row["variant"]] for key in SCORE_NAMES),
        VARIANT_ORDER[row["variant"]],
    ))
    return by_metric, ranks, summed


def _promotion_order(candidates):
    """Exactly four distinct variants, including hybrid and an attribute path."""
    assert {row["variant"] for row in candidates} == set(VARIANTS)
    ranked, ranks, summed = _rankings(candidates)
    best_attribute = next(row["variant"] for row in summed if row["variant"] in ATTRIBUTE_VARIANTS)
    roles = dict(
        mandatory_reference="hybrid",
        balanced_p_winner=ranked["balanced_p"][0]["variant"],
        balanced_log_gain_winner=ranked["balanced_log_gain"][0]["variant"],
        attribute_rank_sum_winner=best_attribute,
    )
    promoted = list(dict.fromkeys(roles.values()))
    for row in summed:
        if len(promoted) == PROMOTED_COUNT:
            break
        if row["variant"] not in promoted:
            promoted.append(row["variant"])
    assert len(promoted) == len(set(promoted)) == PROMOTED_COUNT
    assert "hybrid" in promoted and set(promoted) & set(ATTRIBUTE_VARIANTS)
    assert all(variant in promoted for variant in roles.values())
    return promoted, roles, ranks


def _header(phase, rule, reader):
    return dict(
        time=now(), phase=phase, rule=rule,
        plan_sha256=sha(ROOT / "PLAN.md"),
        code_contract_sha256=sha(ROOT / "CODE_CONTRACT.json"),
        data_contract_sha256=sha(ROOT / "DATA_CONTRACT.json"),
        scored_phase=reader.phase, seeds=list(reader.seeds),
        steps_per_run=STEPS[reader.phase],
        verified_unique_runs=len(reader.verified),
        scores=list(SCORE_NAMES),
        inner_weighting="equal three inner validation protocols and equal seeds; "
                        "within protocol equal nonempty relation x target-kind strata",
        tie_break="fixed common17.VARIANTS order",
        search_backbone="tape for attention variants; none for CNN/GRU variants",
        final_backbones_tuned_separately=False,
        outer_target_development_used=False,
        outer_target_evaluation_used=False,
    )


def promote():
    """Verify screen results, write PROMOTION.json once, return its full payload."""
    verify_contract()
    reader = _EvidenceReader("screen")
    choices = {}
    for target in PROTOCOLS:
        sources, candidates = _candidate_rows(target, VARIANTS, reader)
        promoted, roles, ranks = _promotion_order(candidates)
        choices[target] = dict(
            sources=sources, candidates=candidates, promoted=promoted,
            promotion_roles=roles, metric_ranks=ranks,
            outer_target_development_used=False,
            outer_target_evaluation_used=False,
        )
    payload = _header(
        "promotion",
        "Exactly four distinct: hybrid, best balanced_p, best balanced_log_gain, "
        "best attribute variant by global p-rank plus log-gain-rank sum; "
        "deduplicate and fill remaining places by that same rank sum. "
        "Attribute eligibility is fixed by common17.ATTRIBUTE_VARIANTS.",
        reader,
    )
    payload.update(choices=choices, candidate_order=list(VARIANTS),
                   attribute_candidates=list(ATTRIBUTE_VARIANTS), promoted_count=PROMOTED_COUNT)
    write(ROOT / "PROMOTION.json", payload)
    log("SCREEN_PROMOTION_SEALED", promoted={p: r["promoted"] for p, r in choices.items()})
    return payload


def select():
    """Write independent p/NLL champions using only promoted refine candidates."""
    verify_contract()
    promotion = verify_choice_file("PROMOTION.json")
    assert set(promotion["choices"]) == set(PROTOCOLS)
    assert promotion["candidate_order"] == list(VARIANTS)
    assert promotion["attribute_candidates"] == list(ATTRIBUTE_VARIANTS)
    reader = _EvidenceReader("refine")
    choices = {}
    for target in PROTOCOLS:
        prior = promotion["choices"][target]
        expected_promoted, _, _ = _promotion_order(prior["candidates"])
        assert prior["promoted"] == expected_promoted, target
        sources, candidates = _candidate_rows(target, prior["promoted"], reader)
        assert sources == prior["sources"]
        ranked, ranks, _ = _rankings(candidates)
        choices[target] = dict(
            sources=sources, candidates=candidates, promoted=prior["promoted"],
            p_champion=ranked["balanced_p"][0]["variant"],
            nll_champion=ranked["balanced_log_gain"][0]["variant"],
            metric_ranks=ranks,
            outer_target_development_used=False,
            outer_target_evaluation_used=False,
        )
    payload = _header(
        "selection",
        "Select p_champion by maximal balanced_p and nll_champion independently "
        "by maximal balanced_log_gain over exactly the four promoted candidates. "
        "The uniform log reference is candidate-independent, so maximal "
        "balanced_log_gain is equivalent to minimal equally stratified NLL. "
        "No post-test rescue or substitution is allowed.",
        reader,
    )
    payload.update(choices=choices, promotion_sha256=sha(ROOT / "PROMOTION.json"))
    write(ROOT / "SELECTION.json", payload)
    log("REFINE_SELECTION_SEALED", selected={
        p: {key: row[key] for key in ("p_champion", "nll_champion")}
        for p, row in choices.items()
    })
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=("promote", "select"))
    parser.add_argument("--phase", choices=("promote", "select"))
    args = parser.parse_args()
    action = args.phase or args.action
    if action is None or (args.phase and args.action and args.phase != args.action):
        parser.error("specify exactly one consistent action: promote or select")
    result = promote() if action == "promote" else select()
    display = {
        p: {key: value for key, value in choice.items()
            if key in ("promoted", "p_champion", "nll_champion")}
        for p, choice in result["choices"].items()
    }
    print(json.dumps(dict(phase=action, choices=display), indent=2))
