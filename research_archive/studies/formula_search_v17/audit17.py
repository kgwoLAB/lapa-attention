"""Independent completed-artifact audit; never modifies frozen experiment code.

An active grid is a valid partial audit, not a failure. Only this script's
AUDIT_PARTIAL/INDEPENDENT_AUDIT output and its own prior snapshots are written.
Training is not rerun and test results cannot alter promotion or selection.
"""
import argparse
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
PROTOCOLS = ('dns', 'modbus', 'tls', 'smb2')
BACKBONES = ('rope', 'cope', 'tape', 'sdpa')
NO_BACKBONE = {'cnn_shared_route', 'cnn_shared_attr', 'gru_shared_route', 'gru_shared_attr'}
CLEAN_KEYS = {'message_id', 'data_hex', 'byte_length', 'raw_sha256'}
OFF_ENDPOINT_PREFIXES = (
    'host.byte_embedding.', 'host.query_id_embedding.', 'host.version_embedding.',
    'host.embedding_norm.', 'host.blocks.', 'host.readout.', 'host.cope.',
    'host.retrieval_query.', 'host.retrieval_key.', 'special_endpoints.',
)


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def close(left, right, *, tolerance=1e-10):
    assert math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance), (left, right)


def auxiliary(name):
    return name != 'host.task_query' and not name.startswith(OFF_ENDPOINT_PREFIXES)


def tensor_manifest_hash(manifest, only_auxiliary=False):
    digest = hashlib.sha256()
    for name, value in sorted(manifest.items()):
        if only_auxiliary and not auxiliary(name):
            continue
        digest.update(name.encode())
        digest.update(value.encode())
    return digest.hexdigest()


def replay_stream(train, sources, seed, steps):
    """Reimplement the sampler independently, without importing its function."""
    rng = random.Random(seed)
    grouped = {p: [r for r in train if r['protocol'] == p] for p in sources}
    digest, exposure = hashlib.sha256(), Counter()
    for _ in range(steps):
        batch = []
        for index in range(16):
            row = rng.choice(grouped[rng.choice(sources)])
            count = len(row['fields'])
            slot = rng.randrange(count) if index < 8 else rng.randrange(count, 64)
            batch.append((row['message_id'], slot))
            exposure[row['protocol']] += 1
        rng.shuffle(batch)
        digest.update(json.dumps(batch).encode())
    return digest.hexdigest(), dict(exposure)


def distribution(array, shape):
    assert array.shape == shape, (array.shape, shape)
    assert np.isfinite(array).all() and (array >= 0).all()
    np.testing.assert_allclose(array.sum(-1), 1., atol=5e-6, rtol=0.)


def metric(details):
    groups = defaultdict(list)
    for row in details:
        groups[row['relation'], row['target_kind']].append(row)
    return dict(
        n_fields=len(details), p_true=statistics.mean(r['p_true'] for r in details),
        hit1=statistics.mean(r['hit1'] for r in details), nll=statistics.mean(r['nll'] for r in details),
        balanced_p=statistics.mean(statistics.mean(r['p_true'] for r in group) for group in groups.values()),
        balanced_log_gain=statistics.mean(statistics.mean(math.log(r['byte_length']+2)-r['nll']
                                                        for r in group) for group in groups.values()),
    )


def run_folder(job):
    group = job['target'] if job['phase'] == 'final' else '_'.join(job['sources'])
    return ROOT/job['phase']/group/f"{job['backbone']}__{job['variant']}__{job['seed']}"


def enumerate_jobs(code, promotion, selection):
    """Independent schedule, including one shared no-backbone run per seed."""
    jobs = []
    def add(phase, sources, variant, seed, backbone='tape', target=None):
        job = dict(phase=phase, sources=list(sources), variant=variant, seed=seed,
                   backbone='none' if variant in NO_BACKBONE else backbone, target=target)
        if job not in jobs:
            jobs.append(job)
    for pair in itertools.combinations(PROTOCOLS, 2):
        for variant in code['variants']:
            for seed in code['screen_seeds']:
                add('screen', pair, variant, seed)
    if promotion:
        for target, choice in promotion['choices'].items():
            for pair in itertools.combinations(choice['sources'], 2):
                for variant in choice['promoted']:
                    for seed in code['refine_seeds']:
                        add('refine', pair, variant, seed)
    if selection:
        for target, choice in selection['choices'].items():
            for backbone in BACKBONES:
                for variant in dict.fromkeys(('off', 'hybrid', choice['p_champion'], choice['nll_champion'])):
                    for seed in code['final_seeds']:
                        add('final', choice['sources'], variant, seed, backbone, target)
    assert len({str(run_folder(job)) for job in jobs}) == len(jobs)
    return jobs


def audit(dry_run=False, max_completed=None):
    started = time.monotonic()
    code, data = read(ROOT/'CODE_CONTRACT.json'), read(ROOT/'DATA_CONTRACT.json')
    code_hash, data_hash, plan_hash = sha(ROOT/'CODE_CONTRACT.json'), sha(ROOT/'DATA_CONTRACT.json'), sha(ROOT/'PLAN.md')
    verified = {}
    def verify(path, expected):
        path = Path(path).resolve()
        if path not in verified:
            verified[path] = sha(path)
        assert verified[path] == expected, ('file hash mismatch', str(path))
    for path, expected in code['files'].items():
        verify(path, expected)
    for path, expected in data['files'].items():
        verify(ROOT/path, expected)
    assert code['plan_sha256'] == plan_hash
    assert code['steps'] == {'screen': 120, 'refine': 400, 'final': 600}
    assert len(code['variants']) == len(set(code['variants'])) == 30
    assert code['screen_seeds'] == [170101] and code['refine_seeds'] == [170201, 170202]
    assert code['final_seeds'] == [170301, 170302, 170303]
    assert data['synthetic'] is False and data['historical_test_previously_inspected'] is True
    canonical = {split: rows(ROOT/f'data/gold/{split}.jsonl') for split in ('train', 'development', 'evaluation')}
    clean = {split: {r['message_id']: r for r in rows(ROOT/f'data/clean/{split}.jsonl')} for split in canonical}
    gold_lookup = {split: {r['message_id']: r for r in values} for split, values in canonical.items()}
    for split in canonical:
        assert len(gold_lookup[split]) == len(canonical[split]) == len(clean[split])
        assert set(gold_lookup[split]) == set(clean[split])
        for row in clean[split].values():
            assert set(row) == CLEAN_KEYS
            raw = bytes.fromhex(row['data_hex'])
            assert len(raw) == row['byte_length'] and hashlib.sha256(raw).hexdigest() == row['raw_sha256']
        for protocol in PROTOCOLS:
            actual = [r for r in canonical[split] if r['protocol'] == protocol]
            assert set(data['protocol_ids'][split][protocol]) == {r['message_id'] for r in actual}
            assert data['counts'][split][protocol] == dict(messages=len(actual), fields=sum(len(r['fields']) for r in actual))
    for protocol in PROTOCOLS:
        eligible = set(data['protocol_ids']['development'][protocol])
        ranked = sorted((r for r in clean['development'].values() if r['message_id'] in eligible),
                        key=lambda r: (r['raw_sha256'], r['message_id']))[:24]
        assert data['development_ids'][protocol] == [r['message_id'] for r in ranked]

    promotion = read(ROOT/'PROMOTION.json') if (ROOT/'PROMOTION.json').exists() else None
    selection = read(ROOT/'SELECTION.json') if (ROOT/'SELECTION.json').exists() else None
    order = {variant: i for i, variant in enumerate(code['variants'])}
    attributes = {v for v in code['variants'] if v.startswith('attr_') or v.endswith('_attr')}
    evidence_count = 0
    for document, phase in ((promotion, 'screen'), (selection, 'refine')):
        if document is None:
            continue
        assert document['code_contract_sha256'] == code_hash and document['plan_sha256'] == plan_hash
        assert document['data_contract_sha256'] == data_hash and set(document['choices']) == set(PROTOCOLS)
        assert document['outer_target_development_used'] is False and document['outer_target_evaluation_used'] is False
        for target, choice in document['choices'].items():
            sources = [p for p in PROTOCOLS if p != target]
            assert choice['sources'] == sources
            candidates = choice['candidates']
            expected_variants = code['variants'] if phase == 'screen' else promotion['choices'][target]['promoted']
            assert [r['variant'] for r in candidates] == expected_variants
            seeds = code[f'{phase}_seeds']
            for row in candidates:
                expected = {(pair, next(p for p in sources if p not in pair), seed)
                            for pair in itertools.combinations(sources, 2) for seed in seeds}
                actual = {(tuple(e['sources']), e['validation'], e['seed']) for e in row['evidence']}
                assert actual == expected and len(actual) == len(row['evidence'])
                for evidence in row['evidence']:
                    assert target not in evidence['sources'] and target != evidence['validation']
                    job = dict(phase=phase, sources=evidence['sources'], variant=row['variant'],
                               seed=evidence['seed'], backbone='none' if row['variant'] in NO_BACKBONE else 'tape', target=None)
                    path = run_folder(job)/'validation'/evidence['validation']/'METRICS.json'
                    assert str(path) == evidence['path'] and (run_folder(job)/'COMPLETE.json').exists()
                    verify(path, evidence['sha256'])
                    metrics = read(path)
                    assert set(metrics['by_protocol']) == {evidence['validation']}
                    for key in ('balanced_p', 'balanced_log_gain'):
                        close(evidence[key], metrics['overall'][key])
                    evidence_count += 1
                for key in ('balanced_p', 'balanced_log_gain'):
                    close(row['scores'][key], statistics.mean(e[key] for e in row['evidence']))
            rankings = {key: sorted(candidates, key=lambda r: (-r['scores'][key], order[r['variant']]))
                        for key in ('balanced_p', 'balanced_log_gain')}
            ranks = {key: {r['variant']: i for i, r in enumerate(values)} for key, values in rankings.items()}
            assert choice['metric_ranks'] == ranks
            if phase == 'screen':
                summed = sorted(candidates, key=lambda r: (sum(rank[r['variant']] for rank in ranks.values()), order[r['variant']]))
                best_attribute = next(r['variant'] for r in summed if r['variant'] in attributes)
                promoted = list(dict.fromkeys(('hybrid', rankings['balanced_p'][0]['variant'],
                                               rankings['balanced_log_gain'][0]['variant'], best_attribute)))
                for row in summed:
                    if len(promoted) == 4:
                        break
                    if row['variant'] not in promoted:
                        promoted.append(row['variant'])
                assert choice['promoted'] == promoted and len(promoted) == len(set(promoted)) == 4
            else:
                assert choice['p_champion'] == rankings['balanced_p'][0]['variant']
                assert choice['nll_champion'] == rankings['balanced_log_gain'][0]['variant']
    if selection:
        assert selection['promotion_sha256'] == sha(ROOT/'PROMOTION.json')

    jobs = enumerate_jobs(code, promotion, selection)
    assert sum(j['phase'] == 'screen' for j in jobs) == 180
    pending, completed, run_checks, streams = [], {}, [], {}
    archives = seals_checked = diagnostics_checked = 0
    for job in jobs:
        folder = run_folder(job)
        if not (folder/'COMPLETE.json').exists() or (max_completed is not None and len(completed) >= max_completed):
            pending.append(str(folder.relative_to(ROOT)))
            continue
        complete, meta = read(folder/'COMPLETE.json'), read(folder/'TRAINING.json')
        for key, expected in job.items():
            assert complete[key] == meta[key] == expected, (folder, key)
        phase, variant, sources = job['phase'], job['variant'], job['sources']
        steps = code['steps'][phase]
        assert complete['steps'] == meta['steps'] == steps
        assert complete['code_contract_sha256'] == meta['code_contract_sha256'] == code_hash
        assert meta['data_contract_sha256'] == data_hash
        assert sources == [p for p in PROTOCOLS if p in sources] and job['target'] not in sources
        assert meta['target_protocol_training'] is False and meta['pretrained_checkpoint_used'] is False
        assert meta['encoder_qkv'] == (variant not in NO_BACKBONE)
        for name, expected in complete['files'].items():
            path = (folder/name).resolve()
            assert folder in path.parents
            verify(path, expected)
        stream_key = (tuple(sources), job['seed'], steps)
        if stream_key not in streams:
            streams[stream_key] = replay_stream(canonical['train'], sources, job['seed'], steps)
        stream_hash, exposure = streams[stream_key]
        assert meta['stream_sha256'] == stream_hash and meta['source_sample_counts'] == exposure
        assert sum(exposure.values()) == 16*steps
        loss_keys = {'endpoint'} if variant == 'off' else {'presence', 'source', 'program', 'endpoint'}
        expected_weights = {key: (.25 if variant == 'aux_small' else 4. if variant == 'aux_large' else 1.)
                            if key != 'endpoint' else 1. for key in loss_keys}
        assert set(meta['loss_keys']) == loss_keys and meta['loss_weights'] == expected_weights
        assert all(value > 0 for value in meta['loss_weights'].values())
        assert meta['curve_components'] == 'already weighted; each step components sum to differentiated total'
        curve = read(folder/'curve.json')
        assert len(curve) == steps
        for index, step in enumerate(curve, 1):
            assert step['step'] == index and set(step) == loss_keys | {'step', 'loss', 'grad_norm'}
            assert all(math.isfinite(float(value)) for value in step.values())
            assert all(step[key] >= -1e-6 for key in loss_keys)
            close(step['loss'], sum(step[key] for key in loss_keys), tolerance=1e-5)
        initial = meta['initial_tensor_sha256']
        assert tensor_manifest_hash(initial) == meta['initial_sha256']
        assert tensor_manifest_hash(initial, True) == meta['initial_auxiliary_sha256']
        if variant == 'off':
            assert meta['auxiliary_unchanged'] is True
            assert meta['initial_auxiliary_sha256'] == meta['final_auxiliary_sha256']
            assert not any(auxiliary(name) for name in meta['active_parameter_names'])
        else:
            for prefix in ('host.router.source_score.', 'host.router.axis_heads.', 'presence.'):
                assert any(name.startswith(prefix) for name in meta['active_parameter_names']), (folder, prefix)
        if phase in ('refine', 'final'):
            assert meta['promotion_sha256'] == sha(ROOT/'PROMOTION.json')
        if phase == 'final':
            assert meta['selection_sha256'] == sha(ROOT/'SELECTION.json')
        expected_seals = ([folder/'validation'/p/'PREDICTION_SEAL.json' for p in PROTOCOLS if p not in sources]
                          if phase != 'final' else [folder/'evaluation'/'PREDICTION_SEAL.json'] +
                          ([] if variant == 'off' else [folder/'development'/'PREDICTION_SEAL.json']))
        assert set(folder.rglob('PREDICTION_SEAL.json')) == set(expected_seals)
        for seal_path in expected_seals:
            seal = read(seal_path); seals_checked += 1
            final_test = phase == 'final' and seal_path.parent.name == 'evaluation'
            split = 'evaluation' if final_test else 'development'
            included = [job['target']] if final_test else sources if phase == 'final' else [seal_path.parent.name]
            expected_ids = {mid for p in included for mid in
                            (data['protocol_ids'][split][p] if final_test else data['development_ids'][p])}
            assert seal['gold_read'] is False and seal['protocol_id_input'] is False
            assert set(seal['input_keys']) == CLEAN_KEYS and seal['slots'] == 64 and seal['variant'] == variant
            assert set(seal['input_ids']) == expected_ids and len(seal['input_ids']) == len(expected_ids)
            assert seal['input_hashes'] == [clean[split][mid]['raw_sha256'] for mid in seal['input_ids']]
            assert {Path(name).stem for name in seal['files'] if name.endswith('.npz')} == expected_ids
            for name, expected in seal['files'].items():
                path = (seal_path.parent/name).resolve()
                assert path.parent == seal_path.parent
                verify(path, expected)
            # Numerical NPZ replay is focused on all final evaluation packets;
            # every screen/refine/dev archive is still integrity-hash checked.
            if not final_test:
                continue
            details = rows(seal_path.parent/'diagnostics.jsonl')
            lookup = {(r['message_id'], r['slot']): r for r in details}
            assert len(lookup) == len(details)
            expected_pairs = {(mid, slot) for mid in expected_ids for slot in range(len(gold_lookup[split][mid]['fields']))}
            assert set(lookup) == expected_pairs
            for mid in seal['input_ids']:
                n = clean[split][mid]['byte_length']
                fields = sorted(gold_lookup[split][mid]['fields'], key=lambda f: (f['start'], f['end'], f['semantic']))
                with np.load(seal_path.parent/(mid+'.npz'), allow_pickle=False) as values:
                    archives += 1
                    for key in ('base', 'final', 'route'):
                        if key in values:
                            distribution(values[key], (64, n+2))
                    distribution(values['source'], (64, n))
                    distribution(values['program_at_predicted_source'], (64, 68))
                    assert values['presence'].shape == values['predicted_source'].shape == (64,)
                    assert np.isfinite(values['presence']).all() and ((0 <= values['presence']) & (values['presence'] <= 1)).all()
                    np.testing.assert_array_equal(values['predicted_source'], values['source'].argmax(-1))
                    if variant == 'off':
                        np.testing.assert_array_equal(values['base'], values['final'])
                    for slot, field in enumerate(fields):
                        detail = lookup[mid, slot]
                        target = n+1 if field['target'] is None else field['target']
                        kind = 'NULL' if target == n+1 else 'END' if target == n else 'INTERIOR'
                        assert detail['target'] == target and detail['target_kind'] == kind
                        assert detail['protocol'] == job['target'] and detail['relation'] == field['relation']
                        assert detail['source'] == field['start'] and detail['field_end'] == field['end']
                        p = float(values['final'][slot, target]); base_p = float(values['base'][slot, target])
                        close(detail['p_true'], p); close(detail['nll'], -math.log(max(p, 1e-30)))
                        close(detail['base_p'], base_p); close(detail['base_nll'], -math.log(max(base_p, 1e-30)))
                        assert detail['hit1'] == int(values['final'][slot].argmax() == target)
                        close(detail['source_p'], values['source'][slot, field['start']])
                        if 'route' in values:
                            close(detail['route_p'], values['route'][slot, target])
            measured = read(seal_path.parent/'METRICS.json')
            assert measured['prediction_seal_sha256'] == sha(seal_path)
            assert measured['diagnostics_sha256'] == sha(seal_path.parent/'diagnostics.jsonl')
            assert set(measured['by_protocol']) == {job['target']}
            for key, expected in metric(details).items():
                close(measured['overall'][key], expected)
            stage = rows(folder/'STAGES.jsonl')
            assert len(stage) == len(details)
            stage_lookup = {(r['message_id'], r['slot']): r for r in stage}
            assert set(stage_lookup) == set(lookup)
            for key, detail in lookup.items():
                assert stage_lookup[key]['inputs_gold_free'] is True
                close(stage_lookup[key]['final_p'], detail['p_true'], tolerance=1e-6)
            diagnostics_checked += len(details)
        if phase == 'final' and variant != 'off':
            threshold = read(folder/'THRESHOLD.json')
            assert threshold['sources'] == sources and len(threshold['sweep']) == 19
            assert [r['threshold'] for r in threshold['sweep']] == [i/20 for i in range(1, 20)]
            assert all(set(r['by_protocol']) == set(sources) for r in threshold['sweep'])
            best = max(threshold['sweep'], key=lambda r: (r['macro_f1'], r['threshold']))
            close(threshold['threshold'], best['threshold'])
        completed[str(folder)] = meta
        run_checks.append(dict(**job, steps=steps, folder=str(folder.relative_to(ROOT)), complete_sha256=sha(folder/'COMPLETE.json')))
        if len(completed) % 20 == 0:
            print(json.dumps(dict(audited=len(completed), expected=len(jobs), seconds=time.monotonic()-started)), flush=True)

    paired, shared = [], []
    shared_prefixes = ('host.byte_embedding.', 'host.version_embedding.', 'host.embedding_norm.',
                       'host.readout.', 'host.router.', 'presence.')
    for entry in run_checks:
        baseline = dict(entry)
        baseline = {key: baseline[key] for key in ('phase', 'sources', 'variant', 'seed', 'backbone', 'target')}
        baseline['variant'] = 'hybrid'
        if baseline['backbone'] == 'none':
            baseline['backbone'] = 'tape'
        reference = completed.get(str(run_folder(baseline)))
        meta = completed[str(ROOT/entry['folder'])]
        if reference is None:
            continue
        assert meta['stream_sha256'] == reference['stream_sha256']
        common = {name for name in meta['initial_tensor_sha256'] if name == 'host.task_query' or name.startswith(shared_prefixes)}
        common &= set(reference['initial_tensor_sha256'])
        assert common and all(meta['initial_tensor_sha256'][name] == reference['initial_tensor_sha256'][name] for name in common)
        shared.append(dict(folder=entry['folder'], shared_initial_tensor_count=len(common)))
        if entry['variant'] == 'off':
            assert meta['initial_sha256'] == reference['initial_sha256']
            assert meta['initial_tensor_sha256'] == reference['initial_tensor_sha256']
            paired.append(dict(target=entry['target'], backbone=entry['backbone'], seed=entry['seed']))
    grid_path = ROOT/'GRID_COMPLETE.json'
    final_pass = grid_path.exists() and not pending and selection is not None and max_completed is None
    counts = {phase: sum(r['phase'] == phase for r in run_checks) for phase in ('screen', 'refine', 'final')}
    if final_pass:
        grid = read(grid_path)
        assert grid['code_contract_sha256'] == code_hash
        assert grid['promotion_sha256'] == sha(ROOT/'PROMOTION.json') and grid['selection_sha256'] == sha(ROOT/'SELECTION.json')
        assert grid['total_models'] == len(jobs) == len(completed)
        assert all(grid[f'{phase}_models'] == counts[phase] for phase in counts)
        assert len(paired) == 4*4*len(code['final_seeds'])
    result = dict(
        status='PASS' if final_pass else 'PASS_COMPLETED_SUBSET', time=datetime.now(timezone.utc).isoformat(),
        seconds=time.monotonic()-started, audit_source_sha256=sha(__file__), code_contract_sha256=code_hash,
        data_contract_sha256=data_hash, expected_known_jobs=len(jobs), completed_models=len(completed),
        pending=pending, model_counts=counts, training_steps=sum(r['steps'] for r in run_checks),
        file_hashes_verified=len(verified), deterministic_streams_replayed=len(streams),
        selection_evidence_verified=evidence_count, prediction_seals_verified=seals_checked,
        final_probability_archives_verified=archives, final_endpoint_diagnostics_verified=diagnostics_checked,
        off_hybrid_exact_initial_pairs=paired, shared_initial_tensor_checks=shared, runs=run_checks,
        no_training_or_frozen_code_changes=True, no_target_metric_selection_changes=True,
        checks_scope='All completed run hashes, steps, weighted losses, sampling replay, initial hash metadata, '
                     'source-only selection/seals, all final evaluation NPZ distributions and endpoint metrics. '
                     'Checkpoint tensors are integrity-hashed; no fresh training or full initial-state reconstruction.',
        limitation='Integrity checks do not remove historical-test exposure, small samples, or seed-only uncertainty.',
    )
    if not dry_run:
        output = ROOT/('INDEPENDENT_AUDIT.json' if final_pass else 'AUDIT_PARTIAL.json')
        if output.exists():
            archive = ROOT/'audit_snapshots'/f'{output.stem}_{sha(output)[:16]}.json'
            archive.parent.mkdir(exist_ok=True)
            if not archive.exists():
                archive.write_bytes(output.read_bytes())
        temporary = output.with_name(output.name+'.tmp')
        with temporary.open('w') as stream:
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write('\n')
        temporary.replace(output)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('runs', 'pending', 'shared_initial_tensor_checks', 'off_hybrid_exact_initial_pairs')}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--max-completed', type=int)
    args = parser.parse_args()
    audit(dry_run=args.dry_run, max_completed=args.max_completed)
