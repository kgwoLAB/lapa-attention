"""Aggregate only a completed formula grid; never select using final results.

Every interval is a Student-t interval across the three fixed training seeds.
It is not a confidence interval over packets, captures, or new protocols.
Selected denotes an outer-fold-specific source-only selection procedure, not a
single globally selected architecture. Search and final outcomes stay separate.
"""
from collections import defaultdict
import itertools
import math
from pathlib import Path
import statistics

from common16 import (ROOT, PROTOCOLS, VARIANTS, SEARCH_SEEDS, FINAL_SEEDS,
                      SEARCH_STEPS, FINAL_STEPS, PAIRS, load_data, metric,
                      now, read, rows, sha, verify_contract, write)


ROLES = ('off', 'hybrid', 'selected')
T95_DF2 = 4.302652729911275
ENDPOINT_METRICS = ('p_true', 'hit1', 'nll', 'balanced_log_gain', 'base_p',
                    'base_nll', 'source_p', 'source_hit1', 'route_p')
STAGE_METRICS = ('source_p', 'program_p', 'program_hit1', 'route_p', 'route_real_p',
                 'final_p', 'route_source_p', 'route_program_p', 'route_valid_mass', 'route_sink')


def stats(seed_values):
    """Three-seed mean, sample SD, and un-clipped two-sided 95% t interval."""
    assert {int(seed) for seed in seed_values} == set(FINAL_SEEDS)
    values = {str(seed): float(seed_values[str(seed)] if str(seed) in seed_values else seed_values[seed])
              for seed in FINAL_SEEDS}
    assert all(math.isfinite(value) for value in values.values())
    mean, std = statistics.mean(values.values()), statistics.stdev(values.values())
    margin = T95_DF2*std/math.sqrt(len(values))
    return dict(mean=mean, std=std, ci95=[mean-margin, mean+margin],
                seed_values=values, n_seeds=len(values), interval='Student t, df=2; not clipped')


def maybe_stats(values):
    if all(value is None for value in values.values()):
        return None
    assert all(value is not None for value in values.values()), 'Do not silently drop missing seed values'
    return stats(values)


def mean_nullable(records, key):
    values = [record.get(key) for record in records]
    assert values
    if all(value is None for value in values):
        return None
    assert all(value is not None and math.isfinite(float(value)) for value in values), key
    return statistics.mean(values)


def identity(record):
    return record['message_id'], record['slot']


def _sealed_run(folder, phase, variant, seed, sources, target=None):
    complete = read(folder/'COMPLETE.json')
    assert complete['phase'] == phase and complete['variant'] == variant
    assert complete['seed'] == seed and complete['sources'] == list(sources) and complete['target'] == target
    assert complete['code_contract_sha256'] == sha(ROOT/'CODE_CONTRACT.json')
    expected_steps = SEARCH_STEPS if phase == 'search' else FINAL_STEPS
    assert complete['steps'] == expected_steps
    verified = 0
    for name, digest in complete['files'].items():
        path = (folder/name).resolve()
        assert folder.resolve() in path.parents and sha(path) == digest, path
        verified += 1
    training = read(folder/'TRAINING.json')
    for key, value in dict(phase=phase, variant=variant, seed=seed, sources=list(sources),
                           target=target, steps=expected_steps).items():
        assert training[key] == value, (folder, key)
    assert training['target_protocol_training'] is False and training['pretrained_checkpoint_used'] is False
    assert set(training['source_sample_counts']) == set(sources)
    assert sum(training['source_sample_counts'].values()) == expected_steps*16
    assert training['code_contract_sha256'] == sha(ROOT/'CODE_CONTRACT.json')
    assert training['data_contract_sha256'] == sha(ROOT/'DATA_CONTRACT.json')
    assert set(training['loss_keys']) == ({'endpoint'} if variant == 'off' else {'presence', 'source', 'program', 'endpoint'})
    expected_program = ('mean_five_axis_ce' if variant in ('route_axis', 'route_joint', 'cnn_joint') else
                        None if variant == 'off' else 'valid_bank_ce')
    assert training['program_loss'] == expected_program
    assert training['endpoint_qk'] == (variant in ('off', 'hybrid'))
    assert training['encoder_qkv'] == (variant != 'cnn_joint')
    if variant == 'off':
        assert training['auxiliary_unchanged'] is True
        assert not any(name.startswith(('host.router.', 'presence.')) for name in training['active_parameter_names'])
    if phase == 'final':
        assert target not in sources
        assert training['selection_sha256'] == sha(ROOT/'SELECTION.json')
    curve = read(folder/'curve.json')
    assert len(curve) == expected_steps and [r['step'] for r in curve] == list(range(1, expected_steps+1))
    for row in curve:
        assert set(row) == {'step', 'loss', 'grad_norm'} | set(training['loss_keys'])
        assert all(math.isfinite(value) for value in row.values())
        assert abs(row['loss']-sum(row[key] for key in training['loss_keys'])) <= 2e-5*max(1., abs(row['loss']))
    return dict(folder=str(folder), complete_sha256=sha(folder/'COMPLETE.json'),
                verified_files=verified, metadata=training)


def _prediction(folder, expected_ids):
    seal = read(folder/'PREDICTION_SEAL.json')
    assert seal['gold_read'] is False and seal['protocol_id_input'] is False
    assert set(seal['input_ids']) == set(expected_ids) and len(seal['input_ids']) == len(expected_ids)
    assert seal['slots'] == 64
    for name, digest in seal['files'].items():
        path = (folder/name).resolve()
        assert path.parent == folder.resolve() and sha(path) == digest
    results = read(folder/'METRICS.json')
    assert results['prediction_seal_sha256'] == sha(folder/'PREDICTION_SEAL.json')
    assert results['diagnostics_sha256'] == sha(folder/'diagnostics.jsonl')
    records = rows(folder/'diagnostics.jsonl')
    recomputed = metric(records)
    assert results['overall'] == recomputed
    assert len({identity(r) for r in records}) == len(records)
    return records, seal, results


def summarize_cohort(per_seed, stages, predicate=lambda r: True):
    chosen = {seed: [record for record in records if predicate(record)] for seed, records in per_seed.items()}
    keys = [{identity(record) for record in records} for records in chosen.values()]
    assert keys and keys[0] and all(key == keys[0] for key in keys)
    result = dict(n_fields=len(keys[0]), n_predictions=len(keys[0])*len(FINAL_SEEDS), metrics={}, stages={})
    for name in ENDPOINT_METRICS:
        values = {seed: metric(records)['balanced_log_gain'] if name == 'balanced_log_gain' else mean_nullable(records, name)
                  for seed, records in chosen.items()}
        result['metrics'][name] = maybe_stats(values)
    for name in STAGE_METRICS:
        values = {seed: mean_nullable([row for row in stages[seed] if identity(row) in keys[0]], name)
                  for seed in FINAL_SEEDS}
        result['stages'][name] = maybe_stats(values)
    first = chosen[FINAL_SEEDS[0]]
    result['n_messages'] = len({row['message_id'] for row in first})
    result['target_kind_counts'] = {kind: sum(row['target_kind'] == kind for row in first)
                                    for kind in sorted({row['target_kind'] for row in first})}
    return result


def _summarize_role(run_data):
    per_seed = {seed: data['records'] for seed, data in run_data.items()}
    stages = {seed: data['stages'] for seed, data in run_data.items()}
    result = summarize_cohort(per_seed, stages)
    first = per_seed[FINAL_SEEDS[0]]
    for label, key in (('by_semantic', 'semantic'), ('by_relation', 'relation'), ('by_target_kind', 'target_kind')):
        result[label] = {value: summarize_cohort(per_seed, stages, lambda row, value=value, key=key: row[key] == value)
                         for value in sorted({row[key] for row in first})}
    result['by_semantic_target_kind'] = {
        semantic+'|'+kind: summarize_cohort(per_seed, stages,
            lambda row, semantic=semantic, kind=kind: row['semantic'] == semantic and row['target_kind'] == kind)
        for semantic, kind in sorted({(row['semantic'], row['target_kind']) for row in first})}
    if first[0]['protocol'] == 'dns':
        result['dns_slot_groups'] = {name: summarize_cohort(per_seed, stages, predicate)
            for name, predicate in (('slot_lt4', lambda row: row['slot'] < 4),
                                    ('slot_ge4', lambda row: row['slot'] >= 4))
            if any(predicate(row) for row in first)}
    else:
        result['dns_slot_groups'] = {}
    fields = {seed: data['field_metrics'] for seed, data in run_data.items()}
    if fields[FINAL_SEEDS[0]]['off_field_head_untrained']:
        assert all(data['off_field_head_untrained'] and data['all'] is None for data in fields.values())
        result['field_f1'] = None
        result['field_f1_status'] = 'NOT_TRAINED: Off has endpoint loss only; do not report zero F1'
    else:
        result['field_f1'] = dict(all=stats({seed: data['all']['f1'] for seed, data in fields.items()}),
            by_semantic={semantic: maybe_stats({seed: data['by_semantic'][semantic]['f1'] for seed, data in fields.items()})
                         for semantic in result['by_semantic']},
            raw_seed_counts={str(seed): data for seed, data in fields.items()})
        result['field_f1_status'] = 'source-development threshold; exact typed span multiset F1'
    result['base_kind'] = run_data[FINAL_SEEDS[0]]['seal']['base_kind']
    assert all(data['seal']['base_kind'] == result['base_kind'] for data in run_data.values())
    result['runs'] = {str(seed): data['run'] for seed, data in run_data.items()}
    return result


def _difference(selected, reference):
    assert selected['n_fields'] == reference['n_fields']
    gains = {}
    for output, metric_name, sign in (('p_true_gain', 'p_true', 1), ('hit1_gain', 'hit1', 1),
                                      ('nll_gain', 'nll', -1), ('balanced_log_gain_gain', 'balanced_log_gain', 1)):
        a, b = selected['metrics'][metric_name]['seed_values'], reference['metrics'][metric_name]['seed_values']
        gains[output] = stats({seed: sign*(a[str(seed)]-b[str(seed)]) for seed in FINAL_SEEDS})
    return dict(n_fields=selected['n_fields'], gains=gains,
                direction='positive favors selected; NLL gain = reference NLL - selected NLL',
                paired=True)


def _compare(selected, reference):
    result = _difference(selected, reference)
    for grouping in ('by_semantic', 'by_relation', 'by_target_kind', 'by_semantic_target_kind', 'dns_slot_groups'):
        result[grouping] = {key: _difference(node, reference[grouping][key]) for key, node in selected[grouping].items()}
    return result


def _sanity(records):
    result = dict(n_fields=len(records), models={})
    for name in ('always_end', 'always_null', 'uniform'):
        predictions = []
        for record in records:
            n, target = record['byte_length'], record['target']
            probability = 1/(n+2) if name == 'uniform' else float(target == n+(name == 'always_null'))
            argmax = 0 if name == 'uniform' else n+int(name == 'always_null')
            predictions.append(dict(record, p_true=probability, nll=-math.log(max(probability, 1e-30)),
                                    hit1=int(target == argmax)))
        result['models'][name] = metric(predictions)
        result['models'][name]['expected_sampled_hit'] = statistics.mean(row['p_true'] for row in predictions)
    result['uniform_hit_rule'] = 'deterministic argmax ties choose byte index 0; expected sampled Hit@1 equals p_true'
    result['zero_probability_nll'] = '-log(max(p,1e-30)); not a learned model and not a smoothed output'
    return result


def sanity_groups(records):
    result = _sanity(records)
    for name, key in (('by_semantic', 'semantic'), ('by_relation', 'relation'), ('by_target_kind', 'target_kind')):
        result[name] = {value: _sanity([row for row in records if row[key] == value])
                        for value in sorted({row[key] for row in records})}
    return result


def macro_summary(final, semantic=None):
    result = dict(weighting='equal four target protocols; per protocol field mean (or balanced log gain)', roles={})
    for role in ROLES:
        nodes = [final[target]['roles'][role] if semantic is None else final[target]['roles'][role]['by_semantic'][semantic]
                 for target in PROTOCOLS]
        metrics = {}
        for name in ENDPOINT_METRICS:
            if all(node['metrics'][name] is None for node in nodes):
                metrics[name] = None
                continue
            assert all(node['metrics'][name] is not None for node in nodes)
            metrics[name] = stats({seed: statistics.mean(node['metrics'][name]['seed_values'][str(seed)] for node in nodes)
                                   for seed in FINAL_SEEDS})
        result['roles'][role] = dict(metrics=metrics, n_fields=sum(node['n_fields'] for node in nodes))
    result['comparisons'] = {name: _difference(result['roles']['selected'], result['roles'][reference])
                             for name, reference in (('selected_minus_hybrid', 'hybrid'), ('selected_minus_off', 'off'))}
    return result


def _text(path, content):
    path = Path(path).resolve()
    assert ROOT in path.parents and not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        handle.write(content)


def fmt(statistic):
    if statistic is None:
        return 'N/A'
    return f"{statistic['mean']:.4f} [{statistic['ci95'][0]:.4f}, {statistic['ci95'][1]:.4f}]"


def latex(value):
    text = str(value)
    for a, b in (('\\', r'\textbackslash{}'), ('&', r'\&'), ('%', r'\%'), ('_', r'\_'), ('#', r'\#')):
        text = text.replace(a, b)
    return text


def _latex_table(headers, body):
    alignment = 'l'*len(headers)
    return ('% Generated from sealed formula_search_v16 results; three-seed t95 intervals, df=2.\n'
            '\\begin{tabular}{'+alignment+'}\n\\hline\n'+
            ' & '.join(latex(header) for header in headers)+r' \\'+'\n\\hline\n'+
            '\n'.join(' & '.join(latex(cell) for cell in row)+r' \\' for row in body)+
            '\n\\hline\n\\end{tabular}\n')


def write_tables(summary):
    lines = ['# Formula search v16: sealed numerical tables', '',
             'These are exploratory, historically inspected real-capture evaluations, not a fresh confirmatory test.', '',
             'Values are means [95% Student-t CI] across three fixed training seeds (df=2). '
             'Intervals are not clipped and quantify seed variation only, not packet/capture/protocol uncertainty. '
             'Selected is independently chosen inside each outer fold using source protocols only; it is not one global best formula.', '',
             '## Source-only selection', '', '| Held-out target | Source protocols | Selected formula | Inner balanced log gain |',
             '|---|---|---|---:|']
    selection_body = []
    for target in PROTOCOLS:
        choice = summary['selection']['choices'][target]
        row = [target.upper(), ', '.join(choice['sources']), choice['selected'], f"{choice['ranked'][0]['score']:.6f}"]
        selection_body.append(row)
        lines.append('| '+' | '.join(row)+' |')
    lines += ['', '### All candidate search scores (not final test scores)', '',
              '| Outer target excluded | Candidate | Source-only inner balanced log gain | Selected |',
              '|---|---|---:|---|']
    for target in PROTOCOLS:
        choice = summary['selection']['choices'][target]
        for candidate in choice['ranked']:
            lines.append('| '+' | '.join([target.upper(), candidate['variant'], f"{candidate['score']:.6f}",
                'yes' if candidate['variant'] == choice['selected'] else 'no'])+' |')
    lines += ['', '## Final endpoint probabilities by protocol and semantic', '',
              'N is the number of unique annotated fields per seed, not three times that number. '
              'The Off field head is untrained; its field F1 must not be interpreted as zero.', '',
              '| Protocol | Semantic | N | Role (formula) | p(target) [95% CI] | Hit@1 [95% CI] | NLL [95% CI] |',
              '|---|---|---:|---|---:|---:|---:|']
    semantic_body, relation_body, paired_body, stage_body, kind_body = [], [], [], [], []
    for target in PROTOCOLS:
        result = summary['final'][target]
        for semantic in result['roles']['off']['by_semantic']:
            for role in ROLES:
                node = result['roles'][role]['by_semantic'][semantic]
                row = [target.upper(), semantic, str(node['n_fields']), role+' ('+result['roles'][role]['variant']+')',
                       fmt(node['metrics']['p_true']), fmt(node['metrics']['hit1']), fmt(node['metrics']['nll'])]
                semantic_body.append(row)
                lines.append('| '+' | '.join(row)+' |')
    lines += ['', '## Paired final gains by protocol and semantic', '',
              'Positive gains favor Selected. NLL gain is reference minus Selected; probability gain is Selected minus reference.', '',
              '| Protocol | Semantic | Reference | Δp(target) [95% CI] | NLL gain [95% CI] |',
              '|---|---|---|---:|---:|']
    for target in PROTOCOLS:
        for reference in ('hybrid', 'off'):
            comparison = summary['final'][target]['comparisons']['selected_minus_'+reference]
            for semantic, node in comparison['by_semantic'].items():
                row = [target.upper(), semantic, reference, fmt(node['gains']['p_true_gain']), fmt(node['gains']['nll_gain'])]
                paired_body.append(row)
                lines.append('| '+' | '.join(row)+' |')
    lines += ['', '## Equal-protocol macro', '',
              '| Cohort | Role | p(target) [95% CI] | Hit@1 [95% CI] | NLL [95% CI] | Balanced log gain [95% CI] |',
              '|---|---|---:|---:|---:|---:|']
    for cohort, result in summary['macro'].items():
        for role, node in result['roles'].items():
            lines.append('| '+' | '.join([cohort, role, *(fmt(node['metrics'][key]) for key in ('p_true', 'hit1', 'nll', 'balanced_log_gain'))])+' |')
    lines += ['', '## Relation detail', '',
              '| Protocol | Relation | N | Role | p(target) [95% CI] | Hit@1 [95% CI] | NLL [95% CI] |',
              '|---|---|---:|---|---:|---:|---:|']
    for target in PROTOCOLS:
        for relation in summary['final'][target]['roles']['off']['by_relation']:
            for role in ROLES:
                node = summary['final'][target]['roles'][role]['by_relation'][relation]
                row = [target.upper(), relation, str(node['n_fields']), role, fmt(node['metrics']['p_true']), fmt(node['metrics']['hit1']), fmt(node['metrics']['nll'])]
                relation_body.append(row)
                lines.append('| '+' | '.join(row)+' |')
    lines += ['', '## Target-kind detail', '',
              'END and NULL are distinct valid output classes. INTERIOR is a byte destination. '
              'Absent fields are not relabeled NULL, and no abstention is folded into NULL.', '',
              '| Protocol | Target kind | N | Role | p(target) [95% CI] | Hit@1 [95% CI] | NLL [95% CI] |',
              '|---|---|---:|---|---:|---:|---:|']
    for target in PROTOCOLS:
        for kind in summary['final'][target]['roles']['off']['by_target_kind']:
            for role in ROLES:
                node = summary['final'][target]['roles'][role]['by_target_kind'][kind]
                row = [target.upper(), kind, str(node['n_fields']), role, fmt(node['metrics']['p_true']),
                       fmt(node['metrics']['hit1']), fmt(node['metrics']['nll'])]
                kind_body.append(row)
                lines.append('| '+' | '.join(row)+' |')
    lines += ['', '## Stage diagnostics (all annotated fields per protocol)', '',
              'Source and Program are pre-validity heads. Program is conditioned on the true source only by '
              'post-forward indexing. Route is the destination prior after execution and smoothing. '
              'The separately stored route_source_p / route_program_p are validity-normalized posterior quantities.', '',
              '| Protocol | Role | Source p | Program p given true source | Route p | Final p |',
              '|---|---|---:|---:|---:|---:|']
    for target in PROTOCOLS:
        for role in ROLES:
            node = summary['final'][target]['roles'][role]
            row = [target.upper(), role, *(fmt(node['stages'][key]) for key in ('source_p', 'program_p', 'route_p', 'final_p'))]
            stage_body.append(row)
            lines.append('| '+' | '.join(row)+' |')
    lines += ['', '## DNS positive-slot exposure', '',
              'For DNS held out, non-DNS source training has positive fields only in slots 0–3. '
              'Slots ≥4 still receive negative-presence examples; this is unseen positive-supervision position, not an entirely untrained slot embedding.', '',
              '| Slot group | N | Role | p(target) [95% CI] | NLL [95% CI] |', '|---|---:|---|---:|---:|']
    for role in ROLES:
        for name, node in summary['final']['dns']['roles'][role]['dns_slot_groups'].items():
            lines.append('| '+' | '.join([name, str(node['n_fields']), role, fmt(node['metrics']['p_true']), fmt(node['metrics']['nll'])])+' |')
    lines += ['', '## Field F1 (separate task)', '',
              '| Protocol | Role | Typed field F1 [95% CI] |', '|---|---|---:|']
    for target in PROTOCOLS:
        for role in ROLES:
            node = summary['final'][target]['roles'][role]
            lines.append('| '+' | '.join([target.upper(), role, 'Not trained' if node['field_f1'] is None else fmt(node['field_f1']['all'])])+' |')
    lines += ['', '## Deterministic sanity references', '',
              'These are not prior-paper models. Uniform Hit@1 uses deterministic argmax tie-breaking at byte index 0; '
              'its expected sampled Hit@1 equals p(target). Zero-probability NLL uses the same 1e-30 reporting floor.', '',
              '| Protocol | Semantic | N | Reference | p(target) | Hit@1 | NLL |', '|---|---|---:|---|---:|---:|---:|']
    for target in PROTOCOLS:
        for semantic, node in summary['final'][target]['sanity']['by_semantic'].items():
            for name, result in node['models'].items():
                lines.append('| '+' | '.join([target.upper(), semantic, str(node['n_fields']), name,
                    f"{result['p_true']:.6f}", f"{result['hit1']:.6f}", f"{result['nll']:.6f}"])+' |')
    lines += ['', '## Audit and interpretation boundaries', '',
              f"- Verified {summary['audit']['search_models']} search models and {summary['audit']['final_models']} unique final models.",
              '- All final runs use 600 steps and the same protocol-balanced sample stream for paired seeds.',
              '- Off uses endpoint NLL only; On variants use four unit-weight losses. Axis variants replace bank CE with mean axis CE.',
              '- Original Off/Hybrid share complete initial states; all selected variants preserve shared tensor initialization (smoke-test evidence).',
              '- Route-only base_p is a uniform reference, never a learned QK result. CNN-joint has no encoder QKV; other route variants still use a Transformer encoder.',
              '- Formula choices are source-only and outer-fold-specific. Final target outcomes never re-rank those choices.',
              '- Selected versus Hybrid can change normalization and program loss as well as final QK removal; this contrast alone is not an isolated causal proof that QKV is harmful.',
              '- Full seed values, target-kind slices, paired intervals, raw F1 counts, and seal hashes are preserved in SUMMARY.json.',
              '- No untrained, stale, or unsupported prior-paper baseline is silently assigned a zero or inserted into this comparison.', '']
    _text(ROOT/'TABLES.md', '\n'.join(lines))
    for name, headers, body in (
        ('selection', ('Held-out target', 'Sources', 'Selected formula', 'Inner score'), selection_body),
        ('endpoint_by_semantic', ('Protocol', 'Semantic', 'N', 'Role (formula)', 'p(target) [95% CI]', 'Hit@1 [95% CI]', 'NLL [95% CI]'), semantic_body),
        ('endpoint_by_relation', ('Protocol', 'Relation', 'N', 'Role', 'p(target) [95% CI]', 'Hit@1 [95% CI]', 'NLL [95% CI]'), relation_body),
        ('endpoint_by_target_kind', ('Protocol', 'Target kind', 'N', 'Role', 'p(target) [95% CI]', 'Hit@1 [95% CI]', 'NLL [95% CI]'), kind_body),
        ('paired_gains', ('Protocol', 'Semantic', 'Reference', 'Probability gain [95% CI]', 'NLL gain [95% CI]'), paired_body),
        ('stages', ('Protocol', 'Role', 'Source p', 'Program p | true source', 'Route p', 'Final p'), stage_body)):
        _text(ROOT/f'tables/{name}.tex', _latex_table(headers, body))


def main():
    assert (ROOT/'GRID_COMPLETE.json').exists(), 'Do not aggregate incomplete or running experiments'
    verify_contract()
    grid, selection = read(ROOT/'GRID_COMPLETE.json'), read(ROOT/'SELECTION.json')
    assert grid['selection_sha256'] == sha(ROOT/'SELECTION.json')
    assert selection['code_contract_sha256'] == sha(ROOT/'CODE_CONTRACT.json')
    assert selection['plan_sha256'] == sha(ROOT/'PLAN.md')
    search_runs, search_results, stream_by_pair_seed = [], [], {}
    for pair in PAIRS:
        for seed in SEARCH_SEEDS:
            for variant in VARIANTS:
                folder = ROOT/'search'/'_'.join(pair)/f'{variant}_{seed}'
                run = _sealed_run(folder, 'search', variant, seed, pair)
                key = pair, seed
                stream = run['metadata']['stream_sha256']
                assert stream_by_pair_seed.setdefault(key, stream) == stream
                search_runs.append(run)
                for validation in PROTOCOLS:
                    if validation in pair:
                        continue
                    gold = load_data('development', [validation], limited=True)
                    records, seal, results = _prediction(folder/'validation'/validation, [r['message_id'] for r in gold])
                    assert {r['protocol'] for r in records} == {validation}
                    search_results.append(dict(sources=list(pair), validation=validation, variant=variant, seed=seed,
                        metrics=results['overall'], base_kind=seal['base_kind'], path=str(folder/'validation'/validation/'METRICS.json')))
    assert len(search_runs) == grid['search_models'] == len(PAIRS)*len(SEARCH_SEEDS)*len(VARIANTS)
    lookup = {(tuple(r['sources']), r['validation'], r['variant'], r['seed']): r for r in search_results}
    for target, choice in selection['choices'].items():
        assert choice['sources'] == [p for p in PROTOCOLS if p != target]
        assert choice['target_development_used'] is False and choice['target_evaluation_used'] is False
        assert {r['variant'] for r in choice['ranked']} == set(VARIANTS)
        for ranked in choice['ranked']:
            expected = {(pair, next(p for p in choice['sources'] if p not in pair), seed)
                        for pair in itertools.combinations(choice['sources'], 2) for seed in SEARCH_SEEDS}
            actual = {(tuple(r['pair']), r['validation'], r['seed']) for r in ranked['evidence']}
            assert actual == expected and len(ranked['evidence']) == 6
            for evidence in ranked['evidence']:
                assert target not in evidence['pair'] and evidence['validation'] != target
                assert sha(evidence['path']) == evidence['sha256']
                matched = lookup[(tuple(evidence['pair']), evidence['validation'], ranked['variant'], evidence['seed'])]
                assert evidence['path'] == matched['path']
                assert evidence['score'] == matched['metrics']['balanced_log_gain']
            assert ranked['score'] == statistics.mean(r['score'] for r in ranked['evidence'])
        ordered = sorted(choice['ranked'], key=lambda r: (-r['score'], VARIANTS.index(r['variant'])))
        assert choice['ranked'] == ordered and choice['selected'] == ordered[0]['variant']
    final, final_runs, field_count = {}, [], 0
    for target in PROTOCOLS:
        choice = selection['choices'][target]
        gold = load_data('evaluation', [target])
        expected_ids = [r['message_id'] for r in gold]
        expected_fields = {(row['message_id'], slot): (field, row) for row in gold for slot, field in enumerate(row['fields'])}
        by_variant, streams, initial = {}, {}, {}
        for variant in dict.fromkeys(('off', 'hybrid', choice['selected'])):
            run_data = {}
            for seed in FINAL_SEEDS:
                folder = ROOT/'final'/target/f'{variant}_{seed}'
                run = _sealed_run(folder, 'final', variant, seed, choice['sources'], target)
                final_runs.append(run)
                assert streams.setdefault(seed, run['metadata']['stream_sha256']) == run['metadata']['stream_sha256']
                if variant in ('off', 'hybrid'):
                    assert initial.setdefault(seed, run['metadata']['initial_sha256']) == run['metadata']['initial_sha256']
                records, seal, results = _prediction(folder/'evaluation', expected_ids)
                assert {identity(r) for r in records} == set(expected_fields)
                for record in records:
                    field, row = expected_fields[identity(record)]
                    assert record['protocol'] == target and record['relation'] == field['relation'] and record['semantic'] == field['semantic']
                    assert record['source'] == field['start'] and record['byte_length'] == row['byte_length']
                    assert record['target'] == (row['byte_length']+1 if field['target'] is None else field['target'])
                stages = rows(folder/'STAGES.jsonl')
                assert {identity(r) for r in stages} == set(expected_fields) and len(stages) == len(records)
                stage_lookup = {identity(r): r for r in stages}
                for record in records:
                    stage = stage_lookup[identity(record)]
                    assert stage['inputs_gold_free'] is True
                    assert abs(record['p_true']-stage['final_p']) < 1e-6
                    assert abs(record['source_p']-stage['source_p']) < 1e-6
                if variant != 'off':
                    threshold = read(folder/'THRESHOLD.json')
                    assert threshold['sources'] == choice['sources']
                    best = max(threshold['sweep'], key=lambda r: (r['macro_f1'], r['threshold']))
                    assert threshold['threshold'] == best['threshold']
                run_data[seed] = dict(run=run, records=records, stages=stages, seal=seal,
                                      field_metrics=read(folder/'FIELD_METRICS.json'))
            by_variant[variant] = _summarize_role(run_data)
        roles = {}
        for role, variant in (('off', 'off'), ('hybrid', 'hybrid'), ('selected', choice['selected'])):
            roles[role] = dict(by_variant[variant], variant=variant,
                               alias_of='hybrid' if role == 'selected' and variant == 'hybrid' else None)
        records = rows(ROOT/'final'/target/f'off_{FINAL_SEEDS[0]}'/'evaluation/diagnostics.jsonl')
        final[target] = dict(sources=choice['sources'], selected_variant=choice['selected'], roles=roles,
            comparisons={name: _compare(roles['selected'], roles[reference])
                         for name, reference in (('selected_minus_hybrid', 'hybrid'), ('selected_minus_off', 'off'))},
            sanity=sanity_groups(records), n_messages=len(gold), n_fields=len(expected_fields))
        field_count += len(expected_fields)
    assert len(final_runs) == grid['final_models']
    positive_dns_sources = {slot for row in load_data('train', [p for p in PROTOCOLS if p != 'dns']) for slot in range(len(row['fields']))}
    assert positive_dns_sources == {0, 1, 2, 3}
    summary = dict(schema='lapa-formula-search-v16-summary-1', time=now(),
        definitions=dict(final_seeds=list(FINAL_SEEDS), search_seeds=list(SEARCH_SEEDS), t95_df2=T95_DF2,
            ci='un-clipped Student t over training-seed means only; not packet/capture/protocol sampling uncertainty',
            selected='independent source-only selected formula per held-out protocol; not one globally best architecture',
            balanced_log_gain='equal relation x target-kind strata mean of log(byte_length+2) - NLL, within protocol',
            positive_dns_source_slots=sorted(positive_dns_sources), historical_test_previously_inspected=True,
            scope='four existing real protocols, TAPE anchor plus explicit QKV-free CNN; no synthetic protocols'),
        audit=dict(status='PASS', search_models=len(search_runs), final_models=len(final_runs),
            search_validation_results=len(search_results), final_fields=field_count,
            final_endpoint_predictions=field_count*len(FINAL_SEEDS)*len(ROLES),
            endpoint_predictions_note='role-counted; selected=hybrid aliases reuse identical sealed predictions',
            complete_files_verified=sum(r['verified_files'] for r in search_runs+final_runs),
            code_contract_sha256=sha(ROOT/'CODE_CONTRACT.json'), data_contract_sha256=sha(ROOT/'DATA_CONTRACT.json'),
            grid_complete_sha256=sha(ROOT/'GRID_COMPLETE.json'), selection_sha256=sha(ROOT/'SELECTION.json'),
            paired_sample_streams=True, off_auxiliary_unchanged=True, final_target_training=False,
            search_steps=SEARCH_STEPS, final_steps=FINAL_STEPS, stale_paper_baselines_inserted=False),
        selection=selection, search=dict(runs=search_runs, validation_results=search_results,
            interpretation='All search results retained for transparency; each outer fold uses only its six target-free evidence items per variant'),
        final=final, macro=dict(all_fields=macro_summary(final), length=macro_summary(final, 'LENGTH')))
    write(ROOT/'SUMMARY.json', summary)
    write_tables(summary)
    print(f"PASS: {len(search_runs)} search models, {len(final_runs)} final models, {field_count} unique final fields")


if __name__ == '__main__':
    main()
