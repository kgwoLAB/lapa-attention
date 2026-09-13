"""Post-grid audit and aggregation; never promotes or reselects a formula.

The final role hierarchy is final[target].by_backbone[backbone].roles[role].
CNN/GRU champions alias their single canonical 'none' run across backbone
panels; these aliases are never counted as independent trained models.
All intervals quantify variation over the three fixed training seeds only.
"""
import math
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np

from common17 import (
    ROOT, PROTOCOLS, BACKBONES, FINAL_SEEDS, SCREEN_SEEDS, REFINE_SEEDS,
    STEPS, VARIANTS, NO_BACKBONE, canonical_backbone, phase_jobs, job_folder,
    now, read, rows, sha, write, load_data, metric, ev,
    verify_contract, verify_choice_file, verify_run,
)


ROLES = ('off', 'hybrid', 'p_champion', 'nll_champion')
T95_DF2 = 4.302652729911275
METRICS = ('p_true', 'hit1', 'nll', 'balanced_p', 'balanced_log_gain',
           'base_p', 'base_nll', 'source_p', 'source_hit1', 'route_p')
STAGES = ('source_p', 'program_p', 'program_hit1', 'route_p', 'route_real_p',
          'final_p', 'route_source_p', 'route_program_p', 'route_valid_mass', 'route_sink')
GROUPS = (('by_semantic', 'semantic'), ('by_relation', 'relation'), ('by_target_kind', 'target_kind'))
CONTRASTS = (
    ('p_champion_minus_hybrid', 'p_champion', 'hybrid'),
    ('nll_champion_minus_hybrid', 'nll_champion', 'hybrid'),
    ('p_champion_minus_off', 'p_champion', 'off'),
    ('nll_champion_minus_off', 'nll_champion', 'off'),
    ('hybrid_minus_off', 'hybrid', 'off'),
)


def stats(seed_values):
    assert {int(seed) for seed in seed_values} == set(FINAL_SEEDS)
    values = {str(seed): float(seed_values.get(seed, seed_values.get(str(seed)))) for seed in FINAL_SEEDS}
    assert all(math.isfinite(value) for value in values.values())
    mean, std = statistics.mean(values.values()), statistics.stdev(values.values())
    margin = T95_DF2 * std / math.sqrt(len(values))
    return dict(mean=mean, std=std, ci95=[mean-margin, mean+margin], seed_values=values,
                n_seeds=len(values), interval='Student t, df=2; un-clipped; training-seed variation only')


def maybe_stats(seed_values):
    if all(value is None for value in seed_values.values()):
        return None
    assert all(value is not None for value in seed_values.values()), 'Missing seeds must not be silently dropped'
    return stats(seed_values)


def mean_nullable(records, key):
    values = [record.get(key) for record in records]
    assert values
    if all(value is None for value in values):
        return None
    assert all(value is not None and math.isfinite(float(value)) for value in values), key
    return statistics.mean(values)


def identity(record):
    return record['message_id'], record['slot']


def _expected_fields(gold):
    return {(row['message_id'], slot): (row, field)
            for row in gold for slot, field in enumerate(row['fields'])}


def _verify_record_mapping(records, gold):
    expected = _expected_fields(gold)
    assert len(records) == len(expected) and {identity(r) for r in records} == set(expected)
    for record in records:
        row, field = expected[identity(record)]
        n = row['byte_length']
        target = n+1 if field['target'] is None else field['target']
        for key, value in dict(protocol=row['protocol'], semantic=field['semantic'], relation=field['relation'],
                               source=field['start'], field_end=field['end'], byte_length=n, target=target,
                               target_kind='NULL' if target == n+1 else 'END' if target == n else 'INTERIOR').items():
            assert record[key] == value, (identity(record), key, record[key], value)


def _verify_prediction(folder, gold, numeric=False):
    seal = ev._verify_seal(folder)
    expected_hashes = {r['message_id']: r['raw_sha256'] for r in gold}
    assert dict(zip(seal['input_ids'], seal['input_hashes'])) == expected_hashes
    assert seal['slots'] == 64
    records = rows(folder/'diagnostics.jsonl')
    _verify_record_mapping(records, gold)
    stored = read(folder/'METRICS.json')
    assert stored['prediction_seal_sha256'] == sha(folder/'PREDICTION_SEAL.json')
    assert stored['diagnostics_sha256'] == sha(folder/'diagnostics.jsonl')
    assert stored['overall'] == metric(records)
    grouped = defaultdict(list)
    for record in records:
        grouped[record['protocol']].append(record)
    assert stored['by_protocol'] == {p: metric(group) for p, group in grouped.items()}
    if numeric:
        by_message = defaultdict(list)
        for record in records:
            by_message[record['message_id']].append(record)
        for message_id, group in by_message.items():
            n = group[0]['byte_length']
            with np.load(folder/(message_id+'.npz'), allow_pickle=False) as values:
                for key in ('base', 'final'):
                    ev._check_probabilities(values[key], (64, n+2))
                ev._check_probabilities(values['source'], (64, n))
                for record in group:
                    slot, target, source = record['slot'], record['target'], record['source']
                    p = float(values['final'][slot, target])
                    assert record['p_true'] == p and record['final_p'] == p
                    assert record['hit1'] == int(values['final'][slot].argmax() == target)
                    assert record['nll'] == -math.log(max(p, 1e-30))
                    assert record['base_p'] == float(values['base'][slot, target])
                    assert record['source_p'] == float(values['source'][slot, source])
    return records, seal, stored


def _sealed_run(job):
    folder = job_folder(job)
    complete = verify_run(folder)
    assert all(complete[key] == value for key, value in job.items())
    assert complete['steps'] == STEPS[job['phase']]
    for name in complete['files']:
        assert folder.resolve() in (folder/name).resolve().parents
    training = read(folder/'TRAINING.json')
    assert all(training[key] == value for key, value in job.items())
    assert training['steps'] == STEPS[job['phase']]
    assert training['target_protocol_training'] is False and training['pretrained_checkpoint_used'] is False
    assert training['code_contract_sha256'] == sha(ROOT/'CODE_CONTRACT.json')
    assert training['data_contract_sha256'] == sha(ROOT/'DATA_CONTRACT.json')
    assert set(training['source_sample_counts']) == set(job['sources'])
    assert sum(training['source_sample_counts'].values()) == training['steps'] * 16
    off = job['variant'] == 'off'
    assert set(training['loss_keys']) == ({'endpoint'} if off else {'presence', 'source', 'program', 'endpoint'})
    if off:
        assert training['loss_weights'] == {'endpoint': 1.0}
        assert training['auxiliary_unchanged'] is True
        assert training['initial_auxiliary_sha256'] == training['final_auxiliary_sha256']
        assert not any(name.startswith(('host.router.', 'presence.', 'attribute.', 'mix_gate.'))
                       for name in training['active_parameter_names'])
    else:
        auxiliary_weight = .25 if job['variant'] == 'aux_small' else 4. if job['variant'] == 'aux_large' else 1.
        assert training['loss_weights'] == dict(endpoint=1., presence=auxiliary_weight,
                                                 source=auxiliary_weight, program=auxiliary_weight)
    if job['phase'] == 'final':
        assert job['target'] not in job['sources']
        assert training['selection_sha256'] == sha(ROOT/'SELECTION.json')
    curve = read(folder/'curve.json')
    assert len(curve) == training['steps']
    for step, row in enumerate(curve, 1):
        assert row['step'] == step
        assert set(row) == {'step', 'loss', 'grad_norm'} | set(training['loss_keys'])
        assert all(math.isfinite(value) for value in row.values())
        assert abs(row['loss'] - sum(row[key] for key in training['loss_keys'])) <= 2e-5 * max(1., abs(row['loss']))
    return dict(folder=str(folder), job=job, complete_sha256=sha(folder/'COMPLETE.json'),
                verified_files=len(complete['files']), metadata=training)


def cohort(per_seed, stages, predicate=lambda row: True, auxiliary_trained=True):
    chosen = {seed: [row for row in records if predicate(row)] for seed, records in per_seed.items()}
    keys = [{identity(row) for row in records} for records in chosen.values()]
    assert keys[0] and all(group == keys[0] for group in keys)
    result = dict(n_fields=len(keys[0]), n_predictions=len(keys[0])*len(FINAL_SEEDS), metrics={}, stages={})
    derived = {seed: metric(records) for seed, records in chosen.items()}
    for name in METRICS:
        if not auxiliary_trained and name in ('source_p', 'source_hit1', 'route_p'):
            result['metrics'][name] = None
        else:
            values = {seed: derived[seed][name] if name in ('balanced_p', 'balanced_log_gain') else mean_nullable(records, name)
                      for seed, records in chosen.items()}
            result['metrics'][name] = maybe_stats(values)
    for name in STAGES:
        if not auxiliary_trained and name != 'final_p':
            result['stages'][name] = None
        else:
            values = {seed: mean_nullable([row for row in stages[seed] if identity(row) in keys[0]], name) for seed in FINAL_SEEDS}
            result['stages'][name] = maybe_stats(values)
    first = chosen[FINAL_SEEDS[0]]
    result['n_messages'] = len({row['message_id'] for row in first})
    result['target_kind_counts'] = {kind: sum(row['target_kind'] == kind for row in first)
                                    for kind in sorted({row['target_kind'] for row in first})}
    return result


def summarize_role(run_data, variant, backbone):
    per_seed = {seed: result['records'] for seed, result in run_data.items()}
    stages = {seed: result['stages'] for seed, result in run_data.items()}
    trained = variant != 'off'
    result = cohort(per_seed, stages, auxiliary_trained=trained)
    first = per_seed[FINAL_SEEDS[0]]
    for name, key in GROUPS:
        result[name] = {value: cohort(per_seed, stages, lambda row, k=key, v=value: row[k] == v, trained)
                        for value in sorted({row[key] for row in first})}
    result['by_semantic_target_kind'] = {
        semantic+'|'+kind: cohort(per_seed, stages,
            lambda row, s=semantic, k=kind: row['semantic'] == s and row['target_kind'] == k, trained)
        for semantic, kind in sorted({(row['semantic'], row['target_kind']) for row in first})}
    result['dns_slot_groups'] = {}
    if first[0]['protocol'] == 'dns':
        for name, pred in (('slot_lt4', lambda row: row['slot'] < 4), ('slot_ge4', lambda row: row['slot'] >= 4)):
            if any(pred(row) for row in first):
                result['dns_slot_groups'][name] = cohort(per_seed, stages, pred, trained)
    fields = {seed: data['field_metrics'] for seed, data in run_data.items()}
    if not trained:
        assert all(data['off_field_head_untrained'] and data['all'] is None for data in fields.values())
        result['field_f1'] = None
        result['field_f1_status'] = 'NOT_TRAINED: Off endpoint loss only; auxiliary metrics are not reported as zeros'
    else:
        result['field_f1'] = dict(all=stats({seed: data['all']['f1'] for seed, data in fields.items()}),
            by_semantic={semantic: maybe_stats({seed: data['by_semantic'][semantic]['f1'] for seed, data in fields.items()})
                         for semantic in result['by_semantic']},
            raw_seed_counts={str(seed): data for seed, data in fields.items()})
        result['field_f1_status'] = 'source-development threshold; exact typed-span multiset F1'
    result.update(formula=variant, variant=variant, actual_backbone=backbone,
                  base_kind=run_data[FINAL_SEEDS[0]]['seal']['base_kind'],
                  encoder_kind=run_data[FINAL_SEEDS[0]]['seal']['encoder_kind'],
                  runs={str(seed): data['run'] for seed, data in run_data.items()})
    return result


def difference(candidate, reference):
    assert candidate['n_fields'] == reference['n_fields']
    gains = {}
    for name, key, sign in (('p_true_gain', 'p_true', 1), ('hit1_gain', 'hit1', 1), ('nll_gain', 'nll', -1),
                           ('balanced_p_gain', 'balanced_p', 1), ('balanced_log_gain_gain', 'balanced_log_gain', 1)):
        a, b = candidate['metrics'][key]['seed_values'], reference['metrics'][key]['seed_values']
        gains[name] = stats({seed: sign*(a[str(seed)]-b[str(seed)]) for seed in FINAL_SEEDS})
    result = dict(n_fields=candidate['n_fields'], gains=gains, paired=True,
                  direction='positive favors candidate; NLL gain = reference NLL - candidate NLL')
    if 'field_f1' in candidate and candidate['field_f1'] is not None and reference['field_f1'] is not None:
        a, b = candidate['field_f1']['all']['seed_values'], reference['field_f1']['all']['seed_values']
        result['field_f1_gain'] = stats({seed: a[str(seed)]-b[str(seed)] for seed in FINAL_SEEDS})
    else:
        result['field_f1_gain'] = None
    return result


def compare(candidate, reference):
    result = difference(candidate, reference)
    for group in [name for name, _ in GROUPS] + ['by_semantic_target_kind', 'dns_slot_groups']:
        result[group] = {key: difference(node, reference[group][key]) for key, node in candidate[group].items()}
    return result


def sanity(records):
    result = dict(n_fields=len(records), models={})
    for name in ('always_end', 'always_null', 'uniform'):
        predictions = []
        for row in records:
            n, target = row['byte_length'], row['target']
            p = 1/(n+2) if name == 'uniform' else float(target == n+int(name == 'always_null'))
            argmax = 0 if name == 'uniform' else n+int(name == 'always_null')
            predictions.append(dict(row, p_true=p, nll=-math.log(max(p, 1e-30)), hit1=int(target == argmax)))
        result['models'][name] = dict(metric(predictions), expected_sampled_hit=statistics.mean(r['p_true'] for r in predictions))
    result['uniform_hit_rule'] = 'deterministic argmax ties choose byte 0; expected sampled hit equals p_true'
    return result


def sanity_groups(records):
    result = sanity(records)
    for name, key in GROUPS:
        result[name] = {value: sanity([row for row in records if row[key] == value])
                        for value in sorted({row[key] for row in records})}
    return result


def macro_summary(final, backbone, semantic=None):
    result = dict(weighting='equal four held-out target protocols; field-mean metrics within each protocol', roles={})
    for role in ROLES:
        all_nodes = [final[target]['by_backbone'][backbone]['roles'][role] for target in PROTOCOLS]
        nodes = all_nodes if semantic is None else [node['by_semantic'][semantic] for node in all_nodes]
        metrics, stages = {}, {}
        for name in METRICS:
            if all(node['metrics'][name] is None for node in nodes):
                metrics[name] = None
            else:
                assert all(node['metrics'][name] is not None for node in nodes)
                metrics[name] = stats({seed: statistics.mean(node['metrics'][name]['seed_values'][str(seed)] for node in nodes)
                                       for seed in FINAL_SEEDS})
        for name in STAGES:
            if all(node['stages'][name] is None for node in nodes):
                stages[name] = None
            elif all(node['stages'][name] is not None for node in nodes):
                stages[name] = stats({seed: statistics.mean(node['stages'][name]['seed_values'][str(seed)] for node in nodes)
                                     for seed in FINAL_SEEDS})
            else:
                # Native hybrid and direct-route champions expose different
                # posterior diagnostics. Do not average only supported targets.
                stages[name] = None
        field_f1 = None
        if all(node['field_f1'] is not None for node in all_nodes):
            field_f1 = dict(all=stats({seed: statistics.mean(
                (node['field_f1']['all'] if semantic is None else node['field_f1']['by_semantic'][semantic])['seed_values'][str(seed)]
                for node in all_nodes) for seed in FINAL_SEEDS}))
        result['roles'][role] = dict(metrics=metrics, stages=stages, field_f1=field_f1,
                                    n_fields=sum(node['n_fields'] for node in nodes), n_protocols=4,
                                    formulas={target: final[target]['by_backbone'][backbone]['roles'][role]['formula'] for target in PROTOCOLS})
    result['comparisons'] = {name: difference(result['roles'][candidate], result['roles'][reference])
                             for name, candidate, reference in CONTRASTS}
    return result


def _verify_candidates(payload, phase_results, phase):
    lookup = {(tuple(row['sources']), row['validation'], row['variant'], row['seed']): row for row in phase_results}
    for target, choice in payload['choices'].items():
        assert choice['outer_target_development_used'] is False and choice['outer_target_evaluation_used'] is False
        for candidate in choice['candidates']:
            for evidence in candidate['evidence']:
                assert target not in evidence['sources'] and target != evidence['validation']
                row = lookup[(tuple(evidence['sources']), evidence['validation'], candidate['variant'], evidence['seed'])]
                assert row['path'] == evidence['path'] and sha(row['path']) == evidence['sha256']
                for key in ('balanced_p', 'balanced_log_gain'):
                    assert evidence[key] == row['metrics'][key]
            assert candidate['scores'] == {key: statistics.mean(e[key] for e in candidate['evidence'])
                                            for key in ('balanced_p', 'balanced_log_gain')}
        if phase == 'refine':
            for role, key in (('p_champion', 'balanced_p'), ('nll_champion', 'balanced_log_gain')):
                best = min(choice['candidates'], key=lambda row: (-row['scores'][key], VARIANTS.index(row['variant'])))
                assert choice[role] == best['variant']


def aggregate():
    assert (ROOT/'GRID_COMPLETE.json').exists(), 'Cannot aggregate while grid is incomplete'
    verify_contract()
    grid = read(ROOT/'GRID_COMPLETE.json')
    promotion, selection = verify_choice_file('PROMOTION.json'), verify_choice_file('SELECTION.json')
    assert grid['code_contract_sha256'] == sha(ROOT/'CODE_CONTRACT.json')
    assert grid['promotion_sha256'] == sha(ROOT/'PROMOTION.json')
    assert grid['selection_sha256'] == sha(ROOT/'SELECTION.json')
    all_runs, searches, stream_hashes, initial_reference = [], {}, {}, {}

    def audit_paired(run):
        job, meta = run['job'], run['metadata']
        key = (job['phase'], tuple(job['sources']), job['seed'])
        assert stream_hashes.setdefault(key, meta['stream_sha256']) == meta['stream_sha256']
        # Every native shared tensor is initialized before candidate-specific
        # modules are constructed. Compare tensor hashes, not incompatible
        # complete state hashes across architectures.
        tensor_map = meta['initial_tensor_sha256']
        reference = initial_reference.setdefault(key, tensor_map)
        shared = {name for name in reference.keys() & tensor_map.keys()
                  if name.startswith(('host.', 'presence.', 'special_endpoints.'))}
        if job['variant'] in NO_BACKBONE:
            # CNN blocks deliberately reuse a generic '.blocks' container
            # name, not Transformer weights; equal names alone are not proof
            # these architecturally different parameters are shared tensors.
            shared = {name for name in shared if not name.startswith('host.blocks.')}
        for name in shared:
            assert reference[name] == tensor_map[name], (key, job['variant'], name)

    for phase, payload in (('screen', promotion), ('refine', selection)):
        runs, results = [], []
        for job in phase_jobs(phase):
            run = _sealed_run(job)
            audit_paired(run)
            runs.append(run)
            folder = job_folder(job)
            for validation in PROTOCOLS:
                if validation in job['sources']:
                    continue
                gold = load_data('development', [validation], limited=True)
                records, seal, measured = _verify_prediction(folder/'validation'/validation, gold)
                results.append(dict(sources=job['sources'], validation=validation, variant=job['variant'],
                                    backbone=job['backbone'], seed=job['seed'], metrics=measured['overall'],
                                    base_kind=seal['base_kind'], path=str(folder/'validation'/validation/'METRICS.json')))
        assert len(runs) == grid[phase+'_models']
        _verify_candidates(payload, results, phase)
        searches[phase] = dict(runs=runs, validation_results=results,
                              outer_candidates={target: choice['candidates'] for target, choice in payload['choices'].items()},
                              interpretation='Both excluded-protocol results retained; each outer target uses only target-free source-pair evidence')
        all_runs.extend(runs)

    final_runs, raw_final = [], {}
    for job in phase_jobs('final'):
        run = _sealed_run(job)
        audit_paired(run)
        final_runs.append(run)
        folder, target = job_folder(job), job['target']
        gold = load_data('evaluation', [target])
        records, seal, measured = _verify_prediction(folder/'evaluation', gold, numeric=True)
        stage = rows(folder/'STAGES.jsonl')
        _verify_record_mapping(stage, gold)
        stage_lookup = {identity(row): row for row in stage}
        for record in records:
            row = stage_lookup[identity(record)]
            assert row['inputs_gold_free'] is True
            for a, b in (('p_true', 'final_p'), ('source_p', 'source_p')):
                assert abs(record[a]-row[b]) < 1e-6
        field_metrics = read(folder/'FIELD_METRICS.json')
        if job['variant'] != 'off':
            ev._verify_seal(folder/'development')
            source_gold = load_data('development', job['sources'], limited=True)
            source_candidates = rows(folder/'development/candidates.jsonl')
            threshold = read(folder/'THRESHOLD.json')
            assert threshold == ev.choose_threshold(source_candidates, source_gold, job['sources'])
            assert field_metrics['threshold'] == threshold['threshold']
            predictions = ev.selected(rows(folder/'evaluation/candidates.jsonl'), threshold['threshold'])
            assert rows(folder/'FIELDS.jsonl') == predictions
            assert field_metrics['all'] == ev.field_f1(gold, predictions)
            assert field_metrics['by_semantic'] == {semantic: ev.field_f1(gold, predictions, semantic=semantic)
                                                     for semantic in ('LENGTH', 'OFFSET', 'POINTER')}
        key = target, job['backbone'], job['variant']
        raw_final.setdefault(key, {})[job['seed']] = dict(run=run, records=records, stages=stage,
                                                        seal=seal, field_metrics=field_metrics)
    assert len(final_runs) == grid['final_models']
    all_runs.extend(final_runs)
    final = {}
    for target in PROTOCOLS:
        choice = selection['choices'][target]
        final[target] = dict(sources=choice['sources'], p_champion=choice['p_champion'],
                             nll_champion=choice['nll_champion'], by_backbone={})
        summarized = {}
        for backbone in BACKBONES:
            roles, aliases = {}, {}
            for role in ROLES:
                variant = role if role in ('off', 'hybrid') else choice[role]
                actual_backbone = canonical_backbone(variant, backbone)
                key = target, actual_backbone, variant
                if key not in summarized:
                    summarized[key] = summarize_role(raw_final[key], variant, actual_backbone)
                roles[role] = dict(summarized[key], role=role,
                                  alias_of=aliases.get(key), shared_across_backbones=actual_backbone == 'none')
                aliases.setdefault(key, role)
            final[target]['by_backbone'][backbone] = dict(roles=roles,
                comparisons={name: compare(roles[candidate], roles[reference]) for name, candidate, reference in CONTRASTS})
        first = raw_final[(target, BACKBONES[0], 'off')][FINAL_SEEDS[0]]['records']
        final[target].update(n_fields=len(first), n_messages=len({row['message_id'] for row in first}), sanity=sanity_groups(first))
    unique_predictions = sum(len(result['records']) for results in raw_final.values() for result in results.values())
    assert grid['total_models'] == len(all_runs)
    summary = dict(
        schema='lapa-formula-search-v17-summary-1', time=now(),
        definitions=dict(roles=list(ROLES), backbones=list(BACKBONES), final_seeds=list(FINAL_SEEDS),
            screen_seeds=list(SCREEN_SEEDS), refine_seeds=list(REFINE_SEEDS), steps=STEPS, t95_df2=T95_DF2,
            ci='un-clipped Student t, df=2, across training-seed means only; not capture or protocol sampling uncertainty',
            p_champion='per-outer-fold source-only balanced p champion; selected with TAPE anchor, not retuned per backbone',
            nll_champion='per-outer-fold source-only balanced log gain champion, equivalent to minimum stratified NLL',
            balanced_p='equal nonempty relation x target-kind strata within each protocol',
            balanced_log_gain='equal relation x target-kind strata of log(byte_length+2) - NLL',
            no_backbone='CNN/GRU canonical none runs are reused across four display panels, not independent replicas',
            endpoint_support='byte positions, END=n, NULL=n+1; no ABSTAIN or absent-field conflation',
            missing='null is unsupported/untrained/absent; measured exact zero remains numeric zero',
            historical_test_previously_inspected=True, synthetic_protocols_used=False,
            scope='30 candidate formulas screened; promoted subset refined; frozen champions evaluated on four attention backbones'),
        audit=dict(status='PASS', **{key: grid[key] for key in ('screen_models', 'refine_models', 'final_models', 'total_models')},
            final_fields=sum(result['n_fields'] for result in final.values()), unique_final_endpoint_predictions=unique_predictions,
            complete_files_verified=sum(run['verified_files'] for run in all_runs),
            paired_sample_streams=True, shared_native_initial_tensors_verified=True, off_auxiliary_unchanged=True,
            target_training=False, stale_paper_baselines_inserted=False,
            code_contract_sha256=sha(ROOT/'CODE_CONTRACT.json'), data_contract_sha256=sha(ROOT/'DATA_CONTRACT.json'),
            promotion_sha256=sha(ROOT/'PROMOTION.json'), selection_sha256=sha(ROOT/'SELECTION.json'),
            grid_complete_sha256=sha(ROOT/'GRID_COMPLETE.json'), aggregation_code_sha256=sha(__file__)),
        promotion=promotion, selection=selection, screen=searches['screen'], refine=searches['refine'], final=final,
        macro=dict(by_backbone={backbone: dict(all_fields=macro_summary(final, backbone),
                                               length=macro_summary(final, backbone, 'LENGTH')) for backbone in BACKBONES}),
    )
    write(ROOT/'SUMMARY.json', summary)
    write_tables(summary)
    print(f"PASS: {grid['screen_models']} screen, {grid['refine_models']} refine, {grid['final_models']} final unique models", flush=True)
    return summary


def fmt(value):
    return 'N/A' if value is None else f"{value['mean']:.4f} [{value['ci95'][0]:.4f}, {value['ci95'][1]:.4f}]"


def _text(path, content):
    path = Path(path).resolve()
    assert ROOT in path.parents and not path.exists(), path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        handle.write(content)


def _latex(value):
    conversion = {'&': r'\&', '%': r'\%', '_': r'\_', '#': r'\#', '{': r'\{', '}': r'\}'}
    return ''.join(conversion.get(char, char) for char in str(value))


def _table(headers, body):
    return ('% v17 sealed results. Seed t95 intervals (df=2), not protocol-sampling intervals.\n'
            '\\begin{tabular}{'+'l'*len(headers)+'}\n\\hline\n'+
            ' & '.join(_latex(value) for value in headers)+r' \\'+'\n\\hline\n'+
            '\n'.join(' & '.join(_latex(value) for value in row)+r' \\' for row in body)+
            '\n\\hline\n\\end{tabular}\n')


def write_tables(summary):
    lines = ['# Formula search v17: audited numerical tables', '',
        'Exploratory, historically inspected real captures; not a fresh confirmatory test. No synthetic protocols.', '',
        'Final values are means [un-clipped 95% Student-t CI, df=2] across three fixed training seeds. '
        'Intervals quantify seed variation, not uncertainty over packets, captures, or unseen protocols. '
        'Champions are selected independently within each outer fold using source protocols only; selection is anchored to TAPE, not retuned per backbone.', '',
        'CNN/GRU rows labeled `none` reuse the same sealed runs in each backbone panel. Identical role aliases are not additional experiments. '
        'N/A denotes an absent or untrained quantity; measured zero remains zero. Off auxiliary heads and field F1 are not trained.', '']
    tables = []

    def add(name, title, headers, body, note=None):
        lines.extend(['## '+title, ''])
        if note:
            lines.extend([note, ''])
        lines.extend(['| '+' | '.join(headers)+' |', '| '+' | '.join('---' for _ in headers)+' |'])
        lines.extend('| '+' | '.join(str(value) for value in row)+' |' for row in body)
        lines.append('')
        tables.append((name, headers, body))

    body = []
    for target in PROTOCOLS:
        choice = summary['selection']['choices'][target]
        body.append([target.upper(), ', '.join(choice['sources']), choice['p_champion'], choice['nll_champion'], ', '.join(choice['promoted'])])
    add('selection', 'Frozen source-only choices', ['Target excluded', 'Sources', 'p champion', 'NLL champion', 'Promoted formulas'], body)
    for phase in ('screen', 'refine'):
        body = []
        for target, candidates in summary[phase]['outer_candidates'].items():
            for candidate in candidates:
                body.append([target.upper(), candidate['variant'], f"{candidate['scores']['balanced_p']:.6f}",
                             f"{candidate['scores']['balanced_log_gain']:.6f}", str(len(candidate['evidence']))])
        add(phase+'_candidate_scores', phase.title()+' candidate scores — not final test results',
            ['Outer target excluded', 'Formula', 'Balanced p', 'Balanced log gain', 'Evidence cells'], body)
        raw = [[','.join(row['sources']), row['validation'], row['backbone'], row['variant'], str(row['seed']),
                f"{row['metrics']['p_true']:.6f}", f"{row['metrics']['balanced_p']:.6f}",
                f"{row['metrics']['nll']:.6f}", f"{row['metrics']['balanced_log_gain']:.6f}"]
               for row in summary[phase]['validation_results']]
        add(phase+'_all_validation', phase.title()+' complete validation matrix',
            ['Sources', 'Validation', 'Backbone', 'Formula', 'Seed', 'p(target)', 'Balanced p', 'NLL', 'Balanced log gain'], raw,
            'Both excluded protocols are retained for transparency; only outer-target-free evidence enters each choice.')

    for group, title in (('all', 'protocol'), ('by_semantic', 'semantic'), ('by_relation', 'relation'), ('by_target_kind', 'target kind')):
        body = []
        for target in PROTOCOLS:
            for backbone in BACKBONES:
                for role, result in summary['final'][target]['by_backbone'][backbone]['roles'].items():
                    cohorts = {'ALL': result} if group == 'all' else result[group]
                    for label, node in cohorts.items():
                        body.append([target.upper(), backbone, label, str(node['n_fields']), role, result['formula'],
                                     result['actual_backbone'], *(fmt(node['metrics'][key]) for key in ('p_true', 'hit1', 'nll'))])
        add('endpoint_'+group, 'Final endpoint metrics by '+title,
            ['Target', 'Panel backbone', 'Cohort', 'N', 'Role', 'Formula', 'Actual backbone', 'p(target) [95% CI]', 'Hit@1 [95% CI]', 'NLL [95% CI]'], body)
    body = []
    for target in PROTOCOLS:
        for backbone in BACKBONES:
            for contrast, node in summary['final'][target]['by_backbone'][backbone]['comparisons'].items():
                for label, cohort_node in dict(ALL=node, **node['by_semantic']).items():
                    body.append([target.upper(), backbone, label, contrast,
                                 *(fmt(cohort_node['gains'][key]) for key in ('p_true_gain', 'hit1_gain', 'nll_gain'))])
    add('paired_gains', 'Paired gains', ['Target', 'Backbone', 'Cohort', 'Contrast', 'p gain [95% CI]', 'Hit@1 gain [95% CI]', 'NLL gain [95% CI]'], body,
        'Positive favors the first role. NLL gain is reference NLL minus candidate NLL; other gains are candidate minus reference.')
    body = []
    for backbone, groups in summary['macro']['by_backbone'].items():
        for cohort_name, group in groups.items():
            for role, node in group['roles'].items():
                body.append([backbone, cohort_name, role, *(fmt(node['metrics'][key]) for key in ('p_true', 'hit1', 'nll', 'balanced_p', 'balanced_log_gain'))])
    add('macro', 'Equal-four-protocol macro', ['Backbone', 'Cohort', 'Role', 'p [95% CI]', 'Hit@1 [95% CI]', 'NLL [95% CI]', 'Balanced p [95% CI]', 'Balanced log gain [95% CI]'], body)
    body, field_body = [], []
    for target in PROTOCOLS:
        for backbone in BACKBONES:
            for role, result in summary['final'][target]['by_backbone'][backbone]['roles'].items():
                body.append([target.upper(), backbone, role, result['formula'],
                             *(fmt(result['stages'][key]) for key in ('source_p', 'program_p', 'route_p', 'final_p'))])
                field_body.append([target.upper(), backbone, role, result['formula'],
                                   'N/A (not trained)' if result['field_f1'] is None else fmt(result['field_f1']['all'])])
    add('stages', 'Stage decomposition', ['Target', 'Backbone', 'Role', 'Formula', 'Source p', 'Program p given true source', 'Route p', 'Final p'], body,
        'True source is used only for post-forward indexing. Source/program are pre-validity heads; route is the executed and smoothed destination prior.')
    add('field_f1', 'Typed exact-field F1 — a separate task', ['Target', 'Backbone', 'Role', 'Formula', 'Field F1 [95% CI]'], field_body)
    body = []
    for target in PROTOCOLS:
        for semantic, result in summary['final'][target]['sanity']['by_semantic'].items():
            for name, values in result['models'].items():
                body.append([target.upper(), semantic, str(result['n_fields']), name,
                             *(f"{values[key]:.6f}" for key in ('p_true', 'hit1', 'nll'))])
    add('sanity', 'Deterministic sanity references', ['Target', 'Semantic', 'N', 'Reference', 'p(target)', 'Hit@1', 'NLL'], body,
        'These are not prior-paper models. Uniform argmax ties choose index 0; expected sampled Hit@1 equals p(target). Zero-probability NLL is reported with a 1e-30 floor.')
    audit = summary['audit']
    lines += ['## Audit boundaries', '',
        f"- Verified {audit['screen_models']} screen, {audit['refine_models']} refine, and {audit['final_models']} unique final models.",
        f"- Recomputed mappings and final probabilities for {audit['unique_final_endpoint_predictions']} unique run-field predictions.",
        '- Same-seed protocol-balanced training streams and native shared initial tensors were matched.',
        '- All On variants retain four nonzero losses; aux_small/aux_large explicitly change auxiliary weights.',
        '- Probability-selected and NLL-selected roles can disagree; final results do not alter either choice.',
        '- A winning formula is best only under its precommitted selection objective and budget, not universally optimal.',
        '- No historical prior-paper baseline is inserted as if retrained in this new architecture experiment.', '']
    _text(ROOT/'TABLES.md', '\n'.join(lines))
    for name, headers, body in tables:
        _text(ROOT/'tables'/f'{name}.tex', _table(headers, body))


if __name__ == '__main__':
    aggregate()
