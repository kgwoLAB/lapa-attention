"""Independent, read-only recomputation of completed v18 evidence.

Does not import the trainer/evaluator/aggregator for reference calculations.
Only the audit JSON is written; no inference, fitting, selection, or repair.
Saved head-mean valid execution mass is checked as a scalar, not incorrectly
reconstructed from products of head-mean factor probabilities.
"""
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics

import numpy as np
import torch

from common18 import ROOT, V17, PROTOCOLS, SEEDS, MODES, STEPS, load_data, now, read, sha, write, verify_contract, previous
from executor18 import FourFactorExecutor
from model18 import FourFactorModel, FourFactorRoute, SourceFactor
from lapa.data.schema import select_program
from lapa.programs.bank import native_bank


CLEAN_KEYS = {'message_id', 'data_hex', 'byte_length', 'raw_sha256'}
FACTORS = ('source', 'width', 'endian', 'base')
LOSS_KEYS = ('presence', 'source', 'attributes', 'endpoint')
METRIC_KEYS = ('p_true', 'nll', 'hit1', 'source_p', 'width_p', 'endian_p', 'base_p', 'valid_mass')
DEFAULT_CONFIG = dict(dim=32, heads=4, layers=2, ff_dim=64, max_length=1024, slots=64)


def equal(actual, expected, where='root'):
    """Recursively compare all keys, not a selection of favorable metrics."""
    if isinstance(expected, dict):
        assert isinstance(actual, dict) and set(actual) == set(expected), (where, set(actual), set(expected))
        for key in expected:
            equal(actual[key], expected[key], where+'.'+str(key))
    elif isinstance(expected, (list, tuple)):
        assert isinstance(actual, (list, tuple)) and len(actual) == len(expected), where
        for index, (left, right) in enumerate(zip(actual, expected)):
            equal(left, right, where+f'[{index}]')
    elif isinstance(expected, float):
        assert isinstance(actual, (int, float)) and math.isfinite(actual), (where, actual)
        assert math.isclose(actual, expected, abs_tol=1e-11, rel_tol=1e-10), (where, actual, expected)
    else:
        assert actual == expected, (where, actual, expected)


def json_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def state_digest(state):
    digest = hashlib.sha256()
    for name, tensor in sorted(state.items()):
        tensor = tensor.detach().cpu().contiguous()
        digest.update(name.encode())
        digest.update(str(tuple(tensor.shape)).encode())
        digest.update(str(tensor.dtype).encode())
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def file_manifest(folder, manifest):
    folder = Path(folder).resolve()
    assert manifest
    for name, expected in manifest.items():
        path = (folder/name).resolve()
        assert folder in path.parents and path.is_file(), (folder, name)
        assert sha(path) == expected, path
    return len(manifest)


def expected_jobs():
    return [dict(target=target, sources=[p for p in PROTOCOLS if p != target], mode=mode, seed=seed)
            for target in PROTOCOLS for mode in MODES for seed in SEEDS]


def job_key(job):
    return job['target'], job['mode'], job['seed']


def replay_stream(data, sources, seed):
    """Reimplement the fixed 8-positive/8-negative sampler using local RNG."""
    rng = random.Random(seed)
    groups = {p: [row for row in data if row['protocol'] == p] for p in sources}
    assert set(groups) == set(sources) and all(groups.values())
    digest, counts, positive_counts, negative_counts = hashlib.sha256(), Counter(), Counter(), Counter()
    for _ in range(STEPS):
        samples = []
        for index in range(16):
            row = rng.choice(groups[rng.choice(sources)])
            fields = len(row['fields'])
            assert 0 < fields < 64
            slot = rng.randrange(fields) if index < 8 else rng.randrange(fields, 64)
            samples.append((row, slot))
        rng.shuffle(samples)
        digest.update(json.dumps([(r['message_id'], s) for r, s in samples]).encode())
        for row, slot in samples:
            counts[row['protocol']] += 1
            (positive_counts if slot < len(row['fields']) else negative_counts)[row['protocol']] += 1
    assert sum(counts.values()) == STEPS*16
    assert sum(positive_counts.values()) == sum(negative_counts.values()) == STEPS*8
    return dict(stream_sha256=digest.hexdigest(), source_sample_counts=dict(counts),
                positive_draws=dict(positive_counts), negative_presence_only_draws=dict(negative_counts))


def verify_checkpoint(folder, metadata):
    config = dict(DEFAULT_CONFIG, mode=metadata['mode'])
    equal(metadata['config'], config, 'training.config')
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(metadata['seed'])
        model = FourFactorModel(**config)
    assert state_digest(model.state_dict()) == metadata['initial_sha256'], (folder, 'initialization')
    checkpoint = torch.load(folder/'model.pt', map_location='cpu', weights_only=True)
    assert set(checkpoint) == {'schema', 'config', 'state_dict', 'metadata'}
    assert checkpoint['schema'] == 'four-factor-attention-v18'
    equal(checkpoint['config'], config, 'checkpoint.config')
    equal(checkpoint['metadata'], metadata, 'checkpoint.metadata')
    model.load_state_dict(checkpoint['state_dict'], strict=True)
    assert state_digest(model.state_dict()) == metadata['final_sha256']
    assert all(torch.isfinite(value).all() for value in model.state_dict().values())
    parameters = dict(model.named_parameters())
    assert sum(value.numel() for value in parameters.values()) == metadata['parameters'] == 31041
    active = set(metadata['active_parameters'])
    assert len(active) == len(metadata['active_parameters']) and active == set(parameters)
    forbidden = {'q', 'k', 'qkv', 'query', 'key', 'query_proj', 'key_proj', 'q_proj', 'k_proj',
                 'in_proj', 'program', 'program_head', 'sign', 'mask'}
    for name in parameters:
        assert not (set(re.split(r'[.]+', name.lower())) & forbidden), name
    assert not any(isinstance(module, torch.nn.MultiheadAttention) for module in model.modules())
    assert len(model.blocks) == config['layers']
    routes = [(f'blocks.{i}.routing', block.routing) for i, block in enumerate(model.blocks)] + [('readout', model.readout)]
    for prefix, route in routes:
        assert isinstance(route, FourFactorRoute)
        assert set(dict(route.named_children())) == {factor+'_factor' for factor in FACTORS}
        assert route.mode == metadata['mode'] and route.epsilon == .02
        assert isinstance(route.source_factor, SourceFactor)
        assert set(dict(route.source_factor.named_children())) == {'receiver', 'origin', 'relative', 'energy'}
        for factor, classes in [('width', 4), ('endian', 2), ('base', 7)]:
            layer = getattr(route, factor+'_factor')
            assert isinstance(layer, torch.nn.Linear) and layer.out_features == config['heads']*classes
        assert all(prefix+'.'+name in active for name, _ in route.named_parameters())
    for index, block in enumerate(model.blocks):
        for name in ('value', 'output'):
            assert isinstance(getattr(block, name), torch.nn.Linear)
            assert f'blocks.{index}.{name}.weight' in active
    assert sum(parameter.numel() for parameter in model.executor.parameters()) == 0
    assert model.executor.fingerprint == metadata['executor_fingerprint']
    return dict(parameters=metadata['parameters'], active_parameters=len(active), factor_modules=len(routes)*4,
                encoder_layers=len(model.blocks), initial_sha256=metadata['initial_sha256'], final_sha256=metadata['final_sha256'],
                exact_cpu_initialization_recreated=True, strict_cpu_checkpoint_loaded=True,
                no_learned_qk_program_sign_mask_heads=True, value_projections_retained=True)


def probability(array, shape, normalized=True):
    assert array.shape == shape, (array.shape, shape)
    assert np.isfinite(array).all() and (array >= 0).all() and (array <= 1+1e-5).all()
    if normalized:
        np.testing.assert_allclose(array.sum(-1), 1., atol=1e-5, rtol=1e-5)


def identity(row, field, slot):
    n = row['byte_length']
    target = n+1 if field['target'] is None else field['target']
    assert isinstance(target, int) and 0 <= target <= n+1
    return dict(message_id=row['message_id'], slot=slot, protocol=row['protocol'], semantic=field['semantic'],
                relation=field['relation'], source=int(field['start']), field_end=int(field['end']),
                target=target, byte_length=n, target_kind='NULL' if target == n+1 else 'END' if target == n else 'INTERIOR')


def new_metric(records):
    return dict(n_fields=len(records), **{name: statistics.mean(r[name] for r in records) for name in METRIC_KEYS})


def control_metric(records):
    groups = defaultdict(list)
    for record in records:
        groups[(record['relation'], record['target_kind'])].append(record)
    strata = {relation+'|'+kind: dict(n=len(group), p_true=statistics.mean(r['p_true'] for r in group),
              log_gain=statistics.mean(math.log(r['byte_length']+2)-r['nll'] for r in group))
              for (relation, kind), group in groups.items()}
    return dict(n_fields=len(records), **{name: statistics.mean(r[name] for r in records) for name in ('p_true', 'nll', 'hit1')},
                balanced_p=statistics.mean(g['p_true'] for g in strata.values()),
                balanced_log_gain=statistics.mean(g['log_gain'] for g in strata.values()), strata=strata)


def verify_evaluation(folder, clean, gold, config=None, variant=None):
    new = config is not None
    seal_path = folder/'PREDICTION_SEAL.json'
    seal = read(seal_path)
    assert seal['gold_read'] is False and seal['protocol_id_input'] is False
    assert seal['slots'] == 64 and seal['batch_size'] == (8 if new else 16)
    equal(seal['input_keys'], sorted(CLEAN_KEYS))
    equal(seal['input_ids'], [r['message_id'] for r in clean])
    equal(seal['input_hashes'], [r['raw_sha256'] for r in clean])
    assert len(set(seal['input_ids'])) == len(clean) == len(gold)
    assert set(seal['files']) == {r['message_id']+'.npz' for r in clean} | (set() if new else {'candidates.jsonl'})
    hashes = file_manifest(folder, seal['files'])
    if new:
        equal(seal['byte_lengths'], [r['byte_length'] for r in clean])
        equal(seal['config'], config)
        assert seal['presence_not_multiplied_into_endpoint_probability'] is True
        assert seal['executor_fingerprint'] == FourFactorExecutor().fingerprint
    else:
        assert seal['variant'] == variant and seal['enabled'] == (variant != 'off')
    raw_by_id = {r['message_id']: r for r in clean}
    bank, recomputed = native_bank(), []
    for row in gold:
        raw = raw_by_id[row['message_id']]
        assert set(raw) == CLEAN_KEYS
        assert len(bytes.fromhex(raw['data_hex'])) == raw['byte_length'] == row['byte_length']
        assert hashlib.sha256(bytes.fromhex(raw['data_hex'])).hexdigest() == row['raw_sha256'] == raw['raw_sha256']
        n = row['byte_length']
        with np.load(folder/(row['message_id']+'.npz'), allow_pickle=False) as values:
            expected_keys = {'final', 'source', 'width', 'endian', 'base', 'presence', 'valid_mass'} if new else {
                'final', 'source', 'base', 'presence', 'predicted_source', 'program_at_predicted_source'} | ({'route'} if variant != 'off' else set())
            assert set(values) == expected_keys
            probability(values['final'], (64, n+2))
            probability(values['source'], (64, n))
            probability(values['presence'], (64,), normalized=False)
            if new:
                for name, classes in [('width', 4), ('endian', 2), ('base', 7)]:
                    probability(values[name], (64, n, classes))
                probability(values['valid_mass'], (64,), normalized=False)
            else:
                probability(values['base'], (64, n+2))
                probability(values['program_at_predicted_source'], (64, len(bank.programs)))
                assert values['predicted_source'].shape == (64,)
                np.testing.assert_array_equal(values['predicted_source'], values['source'].argmax(-1))
                if variant == 'off':
                    np.testing.assert_array_equal(values['base'], values['final'])
                else:
                    probability(values['route'], (64, n+2))
            fields = sorted(row['fields'], key=lambda f: (f['start'], f['end'], f['semantic']))
            assert len(fields) <= 64
            for slot, field in enumerate(fields):
                result = identity(row, field, slot)
                target, source = result['target'], result['source']
                assert 0 <= source < result['field_end'] <= n
                p = float(values['final'][slot, target])
                result.update(p_true=p, nll=-math.log(max(p, 1e-30)), hit1=int(values['final'][slot].argmax() == target),
                              source_p=float(values['source'][slot, source]))
                if new:
                    axes = FourFactorExecutor.native_to_axes(select_program(field, row['protocol'], bank), bank)
                    for name, axis in zip(('width', 'endian', 'base'), axes):
                        result[name+'_id'] = axis
                        result[name+'_p'] = float(values[name][slot, source, axis])
                    result['valid_mass'] = float(values['valid_mass'][slot])
                else:
                    base_p = float(values['base'][slot, target])
                    result.update(final_p=p, base_p=base_p, base_nll=-math.log(max(base_p, 1e-30)),
                                  source_hit1=int(values['predicted_source'][slot] == source), base_kind=seal['base_kind'],
                                  route_p=float(values['route'][slot, target]) if 'route' in values else None)
                recomputed.append(result)
    equal(json_rows(folder/'diagnostics.jsonl'), recomputed, str(folder/'diagnostics.jsonl'))
    metrics = read(folder/'METRICS.json')
    assert metrics['prediction_seal_sha256'] == sha(seal_path)
    assert metrics['diagnostics_sha256'] == sha(folder/'diagnostics.jsonl')
    assert metrics['endpoint_fields_only'] is True
    calculate = new_metric if new else control_metric
    expected = dict(overall=calculate(recomputed))
    for column in (('protocol', 'semantic', 'relation', 'target_kind') if new else ('protocol',)):
        grouped = defaultdict(list)
        for record in recomputed:
            grouped[record[column]].append(record)
        expected['by_'+column] = {key: calculate(group) for key, group in grouped.items()}
    assert {key for key in metrics if key == 'overall' or key.startswith('by_')} == set(expected)
    for name, value in expected.items():
        equal(metrics[name], value, str(folder/'METRICS.json')+'.'+name)
    if new:
        assert metrics['field_f1_computed'] is False and metrics['gold_used_for_post_seal_indexing_only'] is True
        assert metrics['nll_probability_floor'] == 1e-30
        equal(metrics['config'], config)
        assert metrics['executor_fingerprint'] == seal['executor_fingerprint']
        assert metrics['valid_mass_condition'] == seal['valid_mass_storage']
    else:
        assert metrics['field_f1_not_in_endpoint_metric'] is True
    identities = [{k: r[k] for k in identity_keys()} for r in recomputed]
    return dict(messages=len(clean), positive_fields=len(recomputed), all_slot_predictions=len(clean)*64,
                seal_file_hashes=hashes, npz_archives=len(clean), grouped_metric_cells=len(expected),
                gold_identity_sha256=hashlib.sha256(json.dumps(identities, sort_keys=True).encode()).hexdigest(),
                prediction_seal_sha256=sha(seal_path), metrics_sha256=sha(folder/'METRICS.json'))


def identity_keys():
    return ('message_id', 'slot', 'protocol', 'semantic', 'relation', 'source', 'field_end', 'target', 'byte_length', 'target_kind')


def verify_mechanism_bounds():
    """Independently check optional, explicitly post-hoc sink-only bounds."""
    path = ROOT/'MECHANISM_DIAGNOSIS.json'
    if not path.exists():
        return dict(status='NOT_PRESENT', required_for_primary_audit=False)
    document = read(path)
    assert document['status'] == 'POST_HOC_ANALYTIC_BOUND' and document['mode'] == 'sink'
    assert document['epsilon'] == .02 and document['not_applied_to_direct'] is True
    assert document['not_a_new_metric_for_selection'] is True and document['head_mean_bounds_exact'] is True
    assert document['source_sha256'] == sha(ROOT/'diagnose18.py')
    groups = defaultdict(list)
    for target in PROTOCOLS:
        for seed in SEEDS:
            folder = ROOT/'runs'/target/f'sink__{seed}'
            complete = read(folder/'COMPLETE.json')
            diagnostics = folder/'evaluation/diagnostics.jsonl'
            assert sha(diagnostics) == complete['files']['evaluation/diagnostics.jsonl']
            for record in json_rows(diagnostics):
                # E_h[.98 sum_a p(s*,a) 1{execute(s*,a)=y}]
                # <= .98 E_h[p(s*)]; head correlations do not break the bound.
                neutral = (1-.98*record['valid_mass'])/(record['byte_length']+2)
                upper = .98*record['source_p']
                lower = max(0., record['p_true']-neutral-upper)
                assert neutral >= 0 and upper >= 0 and 0 <= lower <= record['p_true']
                assert record['p_true']+1e-6 >= neutral, 'Sink neutral floor violated'
                value = dict(p_true=record['p_true'], neutral_p=neutral,
                             true_source_p_upper_bound=upper, other_source_p_lower_bound=lower)
                for name in ('semantic', 'relation'):
                    groups[record['protocol']+'|'+record[name]].append(value)
    expected = {}
    for name, records in groups.items():
        means = {key: statistics.mean(r[key] for r in records) for key in records[0]}
        means['other_source_fraction_of_total_correct_mass_lower_bound'] = means['other_source_p_lower_bound']/means['p_true']
        means['n_field_seed_pairs'] = len(records)
        expected[name] = means
    equal(document['groups'], expected, 'MECHANISM_DIAGNOSIS.groups')
    return dict(status='PASS', groups_checked=len(groups), mechanism_diagnosis_sha256=sha(path),
                diagnosis_code_sha256=document['source_sha256'],
                statement='Lower bound is a fraction of pooled correct-target probability mass, not a fraction of packets, errors, or successful parses.',
                dns_pointer=expected['dns|DNS pointer'])


def main():
    assert (ROOT/'GRID_COMPLETE.json').is_file(), 'Refuse partial-grid audit'
    torch.set_num_threads(2)
    verify_contract()
    contract, grid = read(ROOT/'CONTRACT.json'), read(ROOT/'GRID_COMPLETE.json')
    jobs = expected_jobs()
    equal(contract['jobs'], jobs, 'contract.jobs')
    assert len(jobs) == grid['models'] == 24 and grid['steps'] == contract['total_updates'] == 14400
    assert contract['steps_per_model'] == STEPS == 600
    assert grid['contract_sha256'] == sha(ROOT/'CONTRACT.json')
    assert len(grid['jobs']) == len(jobs)
    assert {job_key(job) for job in grid['jobs']} == {job_key(job) for job in jobs}
    for job in grid['jobs']:
        assert job in jobs
    for filename, digest in contract['smoke_files'].items():
        assert sha(filename) == digest
        smoke = read(filename)
        assert smoke['status'] == 'PASS' and smoke['standard_qk_attention_calls_forbidden']
        assert smoke['every_encoder_and_readout_uses_four_factors']
        assert not smoke['evaluation_read'] and not smoke['development_read']
    clean = {p: load_data('evaluation', [p], clean=True) for p in PROTOCOLS}
    gold = {p: load_data('evaluation', [p]) for p in PROTOCOLS}
    streams = {}
    for target in PROTOCOLS:
        sources = [p for p in PROTOCOLS if p != target]
        train = load_data('train', sources)
        assert {r['protocol'] for r in train} == set(sources) and all(r['protocol'] != target for r in train)
        assert not ({r['raw_sha256'] for r in train} & {r['raw_sha256'] for r in gold[target]})
        for seed in SEEDS:
            streams[(target, seed)] = replay_stream(train, sources, seed)
    new_runs, controls, identities, totals, direct_sink = {}, {}, {}, Counter(), {}
    expected_controls = {str(V17/'final'/job['target']/f'{backbone}__{variant}__{job["seed"]}')
                         for job in jobs for backbone in ('rope', 'cope', 'tape', 'sdpa') for variant in ('off', 'hybrid')}
    assert set(contract['controls']) == expected_controls and len(expected_controls) == 96
    for job in jobs:
        folder = ROOT/'runs'/job['target']/f'{job["mode"]}__{job["seed"]}'
        complete, metadata = read(folder/'COMPLETE.json'), read(folder/'TRAINING.json')
        for document in (complete, metadata):
            for key, expected in job.items():
                equal(document[key], expected)
            assert document['steps'] == STEPS and document['contract_sha256'] == sha(ROOT/'CONTRACT.json')
        actual_files = {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name not in ('COMPLETE.json', 'PROGRESS.json')}
        assert set(complete['files']) == actual_files
        totals['new_run_file_hashes'] += file_manifest(folder, complete['files'])
        assert {'TRAINING.json', 'model.pt', 'curve.json', 'evaluation/METRICS.json', 'evaluation/PREDICTION_SEAL.json', 'evaluation/diagnostics.jsonl'} <= actual_files
        equal(metadata['loss_weights'], {key: 1. for key in LOSS_KEYS})
        assert metadata['no_qk'] and metadata['learned_value_retained'] and metadata['learned_factors'] == list(FACTORS)
        assert metadata['source_gold_input'] is False and metadata['protocol_input'] is False and metadata['target_protocol_training'] is False
        assert metadata['device'] == 'cuda' and metadata['cpu_threads'] == 2 and metadata['tf32'] is False
        equal(metadata['optimizer'], dict(name='AdamW', lr=.002, weight_decay=.01, clip=1.))
        replay = streams[(job['target'], job['seed'])]
        assert metadata['stream_sha256'] == replay['stream_sha256']
        equal(metadata['source_sample_counts'], replay['source_sample_counts'])
        curve = read(folder/'curve.json')
        assert len(curve) == STEPS
        for step, record in enumerate(curve, 1):
            assert set(record) == {'step', 'loss', 'grad_norm', *LOSS_KEYS}
            assert record['step'] == step and all(math.isfinite(v) for v in record.values())
            assert all(record[k] >= 0 for k in ('loss', 'grad_norm', *LOSS_KEYS))
            assert math.isclose(record['loss'], sum(record[k] for k in LOSS_KEYS), abs_tol=2e-5, rel_tol=1e-6)
        totals['new_finite_loss_rows'] += len(curve)
        checkpoint = verify_checkpoint(folder, metadata)
        evaluation = verify_evaluation(folder/'evaluation', clean[job['target']], gold[job['target']], config=metadata['config'])
        target = job['target']
        if target in identities:
            assert evaluation['gold_identity_sha256'] == identities[target]
        identities[target] = evaluation['gold_identity_sha256']
        for key in ('npz_archives', 'positive_fields', 'all_slot_predictions', 'seal_file_hashes'):
            totals['new_'+key] += evaluation[key]
        pair = (target, job['seed'])
        comparison = dict(initial_sha256=metadata['initial_sha256'], stream_sha256=metadata['stream_sha256'],
                          source_sample_counts=metadata['source_sample_counts'], config={k: v for k, v in metadata['config'].items() if k != 'mode'})
        if pair in direct_sink:
            equal(comparison, direct_sink[pair], 'direct/sink match')
        direct_sink[pair] = comparison
        expected_this = {str(V17/'final'/target/f'{backbone}__{variant}__{job["seed"]}')
                         for backbone in ('rope', 'cope', 'tape', 'sdpa') for variant in ('off', 'hybrid')}
        assert len(metadata['controls']) == 8 and {c['path'] for c in metadata['controls']} == expected_this
        for reference in metadata['controls']:
            path = Path(reference['path'])
            frozen = contract['controls'][str(path)]
            assert sha(path/'TRAINING.json') == reference['training_sha256'] == frozen['training_sha256']
            assert sha(path/'COMPLETE.json') == reference['complete_sha256'] == frozen['complete_sha256']
            if str(path) not in controls:
                old_complete = previous.verify_run(path)
                hashes = file_manifest(path, old_complete['files'])
                old = read(path/'TRAINING.json')
                backbone, variant, seed = path.name.split('__')
                expected = dict(phase='final', target=target, sources=job['sources'], seed=int(seed), backbone=backbone, variant=variant)
                for document in (old_complete, old):
                    for key, value in expected.items():
                        equal(document[key], value)
                    assert document['steps'] == STEPS
                assert old['stream_sha256'] == replay['stream_sha256'] == frozen['stream_sha256']
                equal(old['source_sample_counts'], replay['source_sample_counts'])
                assert old['target_protocol_training'] is False and old['pretrained_checkpoint_used'] is False
                if variant == 'off':
                    equal(old['loss_weights'], {'endpoint': 1.})
                    assert old['auxiliary_unchanged'] and old['initial_auxiliary_sha256'] == old['final_auxiliary_sha256']
                    assert not any(n.startswith('host.router.') or n.startswith('presence.') for n in old['active_parameter_names'])
                else:
                    equal(old['loss_weights'], {key: 1. for key in ('endpoint', 'source', 'program', 'presence')})
                old_evaluation = verify_evaluation(path/'evaluation', clean[target], gold[target], variant=variant)
                assert old_evaluation['gold_identity_sha256'] == identities[target]
                controls[str(path)] = dict(complete_sha256=sha(path/'COMPLETE.json'), training_sha256=sha(path/'TRAINING.json'),
                                          files_verified=hashes, stream_sha256=old['stream_sha256'], evaluation=old_evaluation)
                totals['control_run_file_hashes'] += hashes
                for key in ('npz_archives', 'positive_fields', 'all_slot_predictions', 'seal_file_hashes'):
                    totals['control_'+key] += old_evaluation[key]
            assert reference['complete_artifact_hashes_verified'] == controls[str(path)]['files_verified']
            totals['matched_control_references'] += 1
        new_runs[str(folder)] = dict(job=job, complete_sha256=sha(folder/'COMPLETE.json'), checkpoint=checkpoint, evaluation=evaluation)
        print(f'AUDIT {len(new_runs)}/24: {target} {job["mode"]} {job["seed"]}; {len(controls)}/96 controls', flush=True)
    assert len(new_runs) == 24 and len(controls) == 96 and len(direct_sink) == len(streams) == 12
    assert totals['matched_control_references'] == 192 and totals['new_finite_loss_rows'] == 14400
    unique_messages = sum(len(r) for r in clean.values())
    unique_fields = sum(len(r['fields']) for rows in gold.values() for r in rows)
    assert unique_messages == 74 and unique_fields == 347
    assert totals['new_npz_archives'] == unique_messages*len(MODES)*len(SEEDS)
    assert totals['new_positive_fields'] == unique_fields*len(MODES)*len(SEEDS)
    assert totals['control_npz_archives'] == unique_messages*4*2*len(SEEDS)
    assert totals['control_positive_fields'] == unique_fields*4*2*len(SEEDS)
    mechanism = verify_mechanism_bounds()
    verify_contract()
    result = dict(status='PASS', time=now(), auditor_sha256=sha(Path(__file__)), contract_sha256=sha(ROOT/'CONTRACT.json'),
                  grid_complete_sha256=sha(ROOT/'GRID_COMPLETE.json'), new_models=len(new_runs), reused_controls=len(controls),
                  independently_replayed_streams=len(streams), direct_sink_initial_stream_matches=len(direct_sink),
                  unique_evaluation_messages=unique_messages, unique_positive_evaluation_fields=unique_fields,
                  totals=dict(totals), gold_identity_sha256=identities,
                  streams={f'{target}__{seed}': value for (target, seed), value in streams.items()},
                  new_runs=new_runs, controls=controls, post_hoc_mechanism_bounds=mechanism,
                  checks=dict(all_new_checkpoints_loaded_on_cpu=True, initial_cpu_seed_states_recreated=True,
                              all_complete_artifact_hashes_verified=True, all_64_slot_probability_arrays_checked=True,
                              all_npz_endpoint_and_factor_diagnostics_recomputed=True, all_saved_metric_groups_recomputed=True,
                              target_protocol_excluded_from_all_training=True, identical_347_field_gold_identity=True,
                              no_target_selection_or_retraining=True, four_factors_in_every_encoder_layer_and_readout=True),
                  scope=['Endpoint metrics concern annotated positive fields, not end-to-end field F1.',
                         'Negative training slots contribute presence only, not a NULL endpoint target.',
                         'Width/endian/base diagnostics are conditioned on the true source only during post-seal scoring.',
                         'Saved valid_mass is checked against diagnostics/metrics; head means alone cannot reconstruct cross-head joint mass.',
                         'This validates saved inference artifacts and checkpoint identity; it does not rerun all CPU inference or perform visual QA.',
                         'Historical, exploratory held-out-protocol evaluation is not a fresh confirmatory test.',
                         'v18 changes factorization, operator grid and parameterization as well as QK removal; it is not a single-factor causal ablation.'])
    write(ROOT/'INDEPENDENT_AUDIT.json', result, replace=(ROOT/'INDEPENDENT_AUDIT.json').exists())
    print(json.dumps(dict(status='PASS', new_models=len(new_runs), controls=len(controls), totals=dict(totals)), sort_keys=True), flush=True)
    return result


if __name__ == '__main__':
    main()
