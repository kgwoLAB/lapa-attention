"""Post-completion ten-method endpoint aggregation; no selection or training.

New direct/sink models are distinct four-factor architectures, not four old
backbone variants. The eight v17 controls are reused only after source, seed,
sample-stream, 600-update and canonical field-identity verification.
"""
from collections import Counter, defaultdict
import math
from pathlib import Path
import statistics

import numpy as np

from common18 import (
    ROOT, V17, PROTOCOLS, SEEDS, MODES, STEPS, load_data, jobs, folder,
    now, sha, read, write, verify_contract, previous,
)
from executor18 import FourFactorExecutor


BACKBONES = ('rope', 'cope', 'tape', 'sdpa')
T95_DF2 = 4.302652729911275
ENDPOINT_METRICS = ('p_true', 'nll', 'hit1')
STAGE_METRICS = ('source_p', 'width_p', 'endian_p', 'endian_equivalence_p', 'base_axis_p', 'valid_mass')
CORE_ORDER = ('dns|LENGTH', 'dns|POINTER', 'modbus|LENGTH', 'tls|LENGTH', 'smb2|LENGTH', 'smb2|OFFSET')
RELATION_ORDER = (
    'DNS label', 'DNS root terminator', 'DNS RDLENGTH', 'DNS TXT length', 'DNS pointer',
    'Modbus MBAP length', 'TLS record length', 'SMB2 NameLength', 'SMB2 ContextLength',
    'SMB2 NameOffset', 'SMB2 ContextOffset',
)
TARGET_KIND_ORDER = ('INTERIOR', 'END', 'NULL')
GROUP_NAMES = ('by_protocol', 'by_semantic', 'by_core_cell', 'by_relation', 'by_target_kind',
               'by_protocol_target_kind', 'by_relation_target_kind')


def rows(path):
    import json
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def close(left, right, tolerance=1e-10):
    assert math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance), (left, right)


def stats(values):
    """Three matched training-seed replicates; never clip a t confidence band."""
    assert {int(seed) for seed in values} == set(SEEDS)
    seed_values = {str(seed): float(values[seed] if seed in values else values[str(seed)]) for seed in SEEDS}
    assert all(math.isfinite(value) for value in seed_values.values())
    mean = statistics.mean(seed_values.values())
    std = statistics.stdev(seed_values.values())
    margin = T95_DF2*std/math.sqrt(len(SEEDS))
    return dict(mean=mean, std=std, ci95=[mean-margin, mean+margin], seed_values=seed_values,
                n_seeds=len(SEEDS), interval='Student t95 df=2, un-clipped; training-seed variation only')


def identity(record):
    return record['message_id'], record['slot']


def _distribution(array, shape):
    assert array.shape == shape, (array.shape, shape)
    assert np.isfinite(array).all() and (array >= 0).all()
    np.testing.assert_allclose(array.sum(-1), 1., atol=1e-5, rtol=1e-5)


class Verifier:
    def __init__(self):
        self.verified = {}
        self.npz_count = 0
        self.field_count = 0

    def file(self, path, expected):
        path = Path(path).resolve()
        if path not in self.verified:
            self.verified[path] = sha(path)
        assert self.verified[path] == expected, ('artifact hash mismatch', str(path))

    def run(self, path, expected, *, v18):
        complete, metadata = read(path/'COMPLETE.json'), read(path/'TRAINING.json')
        for key, value in expected.items():
            assert complete[key] == metadata[key] == value, (path, key)
        assert complete['steps'] == metadata['steps'] == STEPS == 600
        assert metadata['target_protocol_training'] is False
        assert set(metadata['source_sample_counts']) == set(expected['sources'])
        assert sum(metadata['source_sample_counts'].values()) == 16*STEPS
        if v18:
            assert complete['contract_sha256'] == metadata['contract_sha256'] == sha(ROOT/'CONTRACT.json')
            assert metadata['no_qk'] is True and metadata['learned_value_retained'] is True
            assert metadata['learned_factors'] == ['source', 'width', 'endian', 'base']
            assert metadata['source_gold_input'] is False and metadata['protocol_input'] is False
            assert metadata['loss_weights'] == dict(presence=1., source=1., attributes=1., endpoint=1.)
        else:
            assert complete['code_contract_sha256'] == metadata['code_contract_sha256'] == sha(V17/'CODE_CONTRACT.json')
            assert metadata['data_contract_sha256'] == sha(V17/'DATA_CONTRACT.json')
            assert metadata['pretrained_checkpoint_used'] is False
            if expected['variant'] == 'off':
                assert metadata['loss_weights'] == {'endpoint': 1.} and metadata['auxiliary_unchanged']
            else:
                assert metadata['loss_weights'] == dict(presence=1., source=1., program=1., endpoint=1.)
        required = {'TRAINING.json', 'curve.json', 'model.pt', 'evaluation/METRICS.json',
                    'evaluation/PREDICTION_SEAL.json', 'evaluation/diagnostics.jsonl'}
        assert required <= set(complete['files'])
        for name, digest in complete['files'].items():
            resolved = (path/name).resolve()
            assert path.resolve() in resolved.parents
            self.file(resolved, digest)
        assert len(read(path/'curve.json')) == STEPS
        return complete, metadata

    def predictions(self, path, gold, *, v18):
        evaluation = path/'evaluation'
        seal = read(evaluation/'PREDICTION_SEAL.json')
        assert seal['gold_read'] is False and seal['protocol_id_input'] is False and seal['slots'] == 64
        assert set(seal['input_keys']) == {'message_id', 'data_hex', 'byte_length', 'raw_sha256'}
        expected_hashes = {r['message_id']: r['raw_sha256'] for r in gold}
        assert len(seal['input_ids']) == len(set(seal['input_ids'])) == len(expected_hashes)
        assert dict(zip(seal['input_ids'], seal['input_hashes'])) == expected_hashes
        if v18:
            assert seal['presence_not_multiplied_into_endpoint_probability'] is True
            assert seal['executor_fingerprint'] == FourFactorExecutor().fingerprint
        for name, digest in seal['files'].items():
            artifact = (evaluation/name).resolve()
            assert artifact.parent == evaluation.resolve()
            self.file(artifact, digest)
        raw = rows(evaluation/'diagnostics.jsonl')
        lookup = {identity(r): r for r in raw}
        assert len(lookup) == len(raw)
        expected_pairs = {(r['message_id'], slot) for r in gold for slot in range(len(r['fields']))}
        assert set(lookup) == expected_pairs
        for row in gold:
            mid, n = row['message_id'], row['byte_length']
            with np.load(evaluation/(mid+'.npz'), allow_pickle=False) as values:
                self.npz_count += 1
                _distribution(values['final'], (64, n+2))
                _distribution(values['source'], (64, n))
                if v18:
                    for axis, size in (('width', 4), ('endian', 2), ('base', 7)):
                        _distribution(values[axis], (64, n, size))
                    mass = values['valid_mass']
                    assert mass.shape == (64,) and np.isfinite(mass).all()
                    assert ((mass >= 0) & (mass <= 1+1e-5)).all()
                else:
                    _distribution(values['base'], (64, n+2))
                for slot, field in enumerate(row['fields']):
                    record = lookup[mid, slot]
                    target = n+1 if field['target'] is None else field['target']
                    expected = dict(protocol=row['protocol'], semantic=field['semantic'], relation=field['relation'],
                                    source=field['start'], field_end=field['end'], byte_length=n, target=target,
                                    target_kind='NULL' if target == n+1 else 'END' if target == n else 'INTERIOR')
                    assert all(record[key] == value for key, value in expected.items()), (mid, slot)
                    p = float(values['final'][slot, target])
                    close(record['p_true'], p)
                    close(record['nll'], -math.log(max(p, 1e-30)))
                    assert record['hit1'] == int(values['final'][slot].argmax() == target)
                    close(record['source_p'], values['source'][slot, field['start']])
                    if v18:
                        for axis in ('width', 'endian', 'base'):
                            close(record[axis+'_p'], values[axis][slot, field['start'], record[axis+'_id']])
                        close(record['valid_mass'], values['valid_mass'][slot])
                    self.field_count += 1
        saved = read(evaluation/'METRICS.json')
        assert saved['prediction_seal_sha256'] == sha(evaluation/'PREDICTION_SEAL.json')
        assert saved['diagnostics_sha256'] == sha(evaluation/'diagnostics.jsonl')
        assert saved['overall']['n_fields'] == len(raw)
        for key in ENDPOINT_METRICS:
            close(saved['overall'][key], statistics.mean(r[key] for r in raw))
        # Never merge v17's endpoint-base probability with v18's base-axis
        # probability. Copy only common endpoint metrics into controls.
        records = []
        for record in raw:
            keys = ('message_id', 'slot', 'protocol', 'semantic', 'relation', 'source', 'field_end',
                    'byte_length', 'target', 'target_kind') + ENDPOINT_METRICS
            normalized = {key: record[key] for key in keys}
            if v18:
                normalized.update(source_p=record['source_p'], width_p=record['width_p'],
                                  endian_p=record['endian_p'], base_axis_p=record['base_p'],
                                  valid_mass=record['valid_mass'],
                                  endian_equivalence_p=1. if record['field_end']-record['source'] == 1 else record['endian_p'])
            records.append(normalized)
        return records, seal


def cohort(per_seed, *, macro=False, stages=False):
    assert set(per_seed) == set(SEEDS)
    first = per_seed[SEEDS[0]]
    assert first
    expected = {identity(r) for r in first}
    assert len(expected) == len(first)
    assert all({identity(r) for r in values} == expected and len(values) == len(expected) for values in per_seed.values())
    protocols = [p for p in PROTOCOLS if any(r['protocol'] == p for r in first)]
    def average(records, metric_name):
        if macro:
            return statistics.mean(statistics.mean(r[metric_name] for r in records if r['protocol'] == p) for p in protocols)
        return statistics.mean(r[metric_name] for r in records)
    result = dict(n_fields=len(first), n_messages=len({r['message_id'] for r in first}),
                  n_predictions=len(first)*len(SEEDS), n_protocols=len(protocols), protocols=protocols,
                  weighting='equal protocol means within seed, then equal seeds' if macro else 'equal fields within seed, then equal seeds',
                  target_kind_counts=dict(Counter(r['target_kind'] for r in first)),
                  protocol_field_counts=dict(Counter(r['protocol'] for r in first)),
                  metrics={key: stats({seed: average(records, key) for seed, records in per_seed.items()}) for key in ENDPOINT_METRICS},
                  stages={key: stats({seed: average(records, key) for seed, records in per_seed.items()}) for key in STAGE_METRICS} if stages else {})
    return result


def summarize(per_seed, *, stages=False):
    first = per_seed[SEEDS[0]]
    result = dict(overall_micro=cohort(per_seed, stages=stages),
                  overall_protocol_macro=cohort(per_seed, macro=True, stages=stages))
    groupers = {
        'by_protocol': lambda r: r['protocol'],
        'by_semantic': lambda r: r['semantic'],
        'by_core_cell': lambda r: r['protocol']+'|'+r['semantic'],
        'by_relation': lambda r: r['protocol']+'|'+r['relation'],
        'by_target_kind': lambda r: r['target_kind'],
        'by_protocol_target_kind': lambda r: r['protocol']+'|'+r['target_kind'],
        'by_relation_target_kind': lambda r: r['protocol']+'|'+r['relation']+'|'+r['target_kind'],
    }
    for name, group_key in groupers.items():
        keys = sorted({group_key(r) for r in first})
        result[name] = {
            key: cohort({seed: [r for r in records if group_key(r) == key] for seed, records in per_seed.items()}, stages=stages)
            for key in keys
        }
    return result


def difference(candidate, reference):
    assert candidate['n_fields'] == reference['n_fields'] and candidate['protocol_field_counts'] == reference['protocol_field_counts']
    values = {}
    for metric_name in ENDPOINT_METRICS:
        left = candidate['metrics'][metric_name]['seed_values']
        right = reference['metrics'][metric_name]['seed_values']
        values['delta_'+metric_name] = stats({seed: left[str(seed)]-right[str(seed)] for seed in SEEDS})
    values['nll_gain'] = stats({seed: -values['delta_nll']['seed_values'][str(seed)] for seed in SEEDS})
    return dict(n_fields=candidate['n_fields'], n_messages=candidate['n_messages'],
                weighting=candidate['weighting'], metrics=values, paired=True,
                direction='delta = candidate - reference for every original metric; positive nll_gain = reference NLL - candidate NLL')


def contrast(candidate, reference):
    result = {name: difference(candidate[name], reference[name]) for name in ('overall_micro', 'overall_protocol_macro')}
    for name in GROUP_NAMES:
        assert set(candidate[name]) == set(reference[name])
        result[name] = {key: difference(node, reference[name][key]) for key, node in candidate[name].items()}
    return result


def _method_catalog():
    labels = {'rope': 'RoPE', 'cope': 'CoPE', 'tape': 'TAPE', 'sdpa': 'SDPA'}
    catalog = []
    for backbone in BACKBONES:
        for variant in ('off', 'hybrid'):
            catalog.append(dict(id=backbone+'_'+variant,
                                label=labels[backbone]+(' Off' if variant == 'off' else ' + LAPA (v17)'),
                                family='v17_reused_control', actual_backbone=backbone, variant=variant,
                                qk_free=False, learned_value_retained=True))
    for mode in MODES:
        catalog.append(dict(id='four_factor_'+mode, label='Four-factor '+mode+' (v18)',
                            family='v18_four_factor', actual_backbone='none', mode=mode,
                            qk_free=True, learned_value_retained=True))
    return catalog


def _tex_escape(value):
    mapping = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
               '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(mapping.get(char, char) for char in str(value))


def _table(headers, values, caption):
    markdown = ['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']+['---:']*(len(headers)-1))+' |']
    markdown += ['| '+' | '.join(str(value).replace('|', '/') for value in row)+' |' for row in values]
    latex = [r'\begin{table}[t]', r'\centering', r'\scriptsize', r'\caption{'+_tex_escape(caption)+'}',
             r'\begin{tabular}{l'+'r'*(len(headers)-1)+'}', r'\toprule',
             ' & '.join(_tex_escape(value) for value in headers)+r' \\', r'\midrule']
    latex += [' & '.join(_tex_escape(value) for value in row)+r' \\' for row in values]
    latex += [r'\bottomrule', r'\end{tabular}', r'\end{table}', '']
    return '\n'.join(markdown), '\n'.join(latex)


def _value(stat, interval=False):
    if interval:
        return f"{stat['mean']:.6f} [{stat['ci95'][0]:.6f}, {stat['ci95'][1]:.6f}]"
    return f"{stat['mean']:.6f}"


def tables(summary):
    """Return Markdown and LaTeX text in memory; no CSV or plot side effects."""
    methods, order = summary['methods'], summary['method_order']
    blocks = ['# v18: 네 요인 직접 attention 수치표', '',
              '실제74개 메시지/347개 동일 필드,3→1 평가, seed170301–170303의 평균이다. 새24개 모델과 기존96개 검증된 대조군을 비교한다.', '',
              '대괄호는3개 training seed의 Student t95(df=2) CI이며 물리적 범위로 자르지 않았다. 표준편차와 모든 seed 수치는 SUMMARY.json에 있다. 단순 평균 p, NLL, Hit@1은 서로 다른 지표다.', '',
              '세부 표는 필드 micro 평균, overall protocol-macro는4개 protocol 평균의 동등 평균이다. F1은 이번 표에 포함하지 않는다. 세부 평균의 CI/std도 SUMMARY.json에 보존한다.', '']
    latex = {}
    def add(stem, title, headers, values, caption):
        markdown, text = _table(headers, values, caption)
        blocks.extend(['## '+title, '', markdown, ''])
        latex[stem+'.tex'] = text
    for scope, title in (('overall_protocol_macro', '전체: protocol-macro'), ('overall_micro', '전체: field-micro')):
        add(scope, title, ['Method', 'p(target) [95% CI]', 'NLL [95% CI]', 'Hit@1 [95% CI]'],
            [[methods[mid]['label']]+[_value(methods[mid][scope]['metrics'][key], True) for key in ENDPOINT_METRICS] for mid in order],
            title+'; training-seed t95 intervals, not packet or protocol sampling uncertainty.')
    for key in ENDPOINT_METRICS:
        add('core_'+key, 'Protocol×semantic: '+key,
            ['Method']+[cell.replace('|', '-')+f" (n={methods[order[0]]['by_core_cell'][cell]['n_fields']})" for cell in CORE_ORDER],
            [[methods[mid]['label']]+[_value(methods[mid]['by_core_cell'][cell]['metrics'][key]) for cell in CORE_ORDER] for mid in order],
            'Protocol-semantic endpoint '+key+'; three-seed means, matching fields.')
        for protocol in PROTOCOLS:
            keys = [value for value in summary['cohort_orders']['by_relation'] if value.startswith(protocol+'|')]
            add(protocol+'_relations_'+key, protocol.upper()+' 세부 관계: '+key,
                ['Method']+[value.split('|', 1)[1]+f" (n={methods[order[0]]['by_relation'][value]['n_fields']})" for value in keys],
                [[methods[mid]['label']]+[_value(methods[mid]['by_relation'][value]['metrics'][key]) for value in keys] for mid in order],
                protocol.upper()+' relation endpoint '+key+'; three-seed means.')
        add('target_kind_'+key, 'Endpoint 종류: '+key, ['Method']+list(TARGET_KIND_ORDER),
            [[methods[mid]['label']]+[_value(methods[mid]['by_target_kind'][kind]['metrics'][key]) for kind in TARGET_KIND_ORDER] for mid in order],
            'INTERIOR/END/NULL field-micro '+key+'; distinct endpoint types.')
    stage_keys = ('source_p', 'width_p', 'endian_equivalence_p', 'base_axis_p', 'valid_mass')
    for mode in MODES:
        method = methods['four_factor_'+mode]
        add('stages_'+mode, 'v18 '+mode+'의4요인 및 유효 질량', ['Cell']+list(stage_keys),
            [[cell.replace('|', '-')]+[_value(method['by_core_cell'][cell]['stages'][key]) for key in stage_keys] for cell in CORE_ORDER],
            'Post-seal factor diagnostics at true source; these marginal probabilities do not multiply to final probability.')
    blocks.extend(['width1에서는 endian이 식별되지 않으므로 위 stage 표는 두 endian의 동치 확률 합(1)을 사용한다. raw canonical endian_p도 SUMMARY.json에 별도로 보존한다.', '',
                   'base_axis_p는 v18의 base 연산 축 확률이다. v17 base_p는 목적지 QK 확률이므로 둘을 비교하거나 결합하지 않았다.', ''])
    for scope, label in (('overall_protocol_macro', 'protocol-macro'), ('overall_micro', 'field-micro')):
        add('paired_'+scope, 'Paired contrasts: '+label,
            ['Candidate - reference', 'Delta p [95% CI]', 'Delta NLL [95% CI]', 'Delta Hit@1 [95% CI]'],
            [[methods[row['candidate']]['label']+' - '+methods[row['reference']]['label']]+
             [_value(row[scope]['metrics'][key], True) for key in ('delta_p_true', 'delta_nll', 'delta_hit1')]
             for row in summary['contrasts'].values()],
            'Same-seed candidate-minus-reference differences; negative delta NLL is improvement.')
    blocks.extend(['## 해석 제한', '',
                   'p(target)·Hit@1의 양의 차이는 candidate에 유리하며, NLL의 음의 차이가 candidate에 유리하다. 별도 nll_gain은 reference−candidate로 SUMMARY.json에 보존한다.', '',
                   '두 mode 및 모든17개 paired 대비를 사전 고정해 보고한다. target 결과로 수식이나 대조군을 선택하지 않았다. historical test, 작은 표본 및3seed 한계를 유지한다.', '',
                   'LaTeX 원본은 tables/*.tex이며 booktabs가 필요하다. 넓은 표의 페이지 배치는 최종 논문 문서에서 조절한다.', ''])
    return '\n'.join(blocks), latex


def aggregate():
    """Fail closed until every v18 job and all matched historical controls exist."""
    assert (ROOT/'GRID_COMPLETE.json').exists(), 'Do not aggregate partial v18 results'
    verify_contract()
    contract = read(ROOT/'CONTRACT.json')
    grid = read(ROOT/'GRID_COMPLETE.json')
    assert grid['contract_sha256'] == sha(ROOT/'CONTRACT.json')
    assert grid['models'] == 24 and grid['steps'] == 14400
    expected_jobs = jobs()
    job_id = lambda job: (job['target'], job['mode'], job['seed'], tuple(job['sources']))
    assert len(grid['jobs']) == len(expected_jobs) == 24
    assert {job_id(j) for j in grid['jobs']} == {job_id(j) for j in expected_jobs}
    assert len(contract['controls']) == 96
    verifier = Verifier()
    gold = {p: load_data('evaluation', [p]) for p in PROTOCOLS}
    assert sum(len(r['fields']) for records in gold.values() for r in records) == 347
    assert sum(len(records) for records in gold.values()) == 74
    catalog = _method_catalog()
    per_method = {item['id']: {seed: [] for seed in SEEDS} for item in catalog}
    run_metadata, run_manifests = {}, []
    control_streams = {}
    for item in catalog:
        is_new = item['family'] == 'v18_four_factor'
        for target in PROTOCOLS:
            sources = [p for p in PROTOCOLS if p != target]
            for seed in SEEDS:
                if is_new:
                    expected = dict(target=target, sources=sources, mode=item['mode'], seed=seed)
                    path = folder(expected)
                else:
                    expected = dict(phase='final', target=target, sources=sources,
                                    variant=item['variant'], backbone=item['actual_backbone'], seed=seed)
                    path = V17/'final'/target/f"{item['actual_backbone']}__{item['variant']}__{seed}"
                    prior = contract['controls'][str(path)]
                    verifier.file(path/'COMPLETE.json', prior['complete_sha256'])
                    verifier.file(path/'TRAINING.json', prior['training_sha256'])
                complete, metadata = verifier.run(path, expected, v18=is_new)
                stream_key = (target, seed)
                if stream_key not in control_streams:
                    control_streams[stream_key] = metadata['stream_sha256']
                assert metadata['stream_sha256'] == control_streams[stream_key], ('sample stream mismatch', path)
                if not is_new:
                    assert metadata['stream_sha256'] == contract['controls'][str(path)]['stream_sha256']
                else:
                    assert metadata['executor_fingerprint'] == contract['executor_fingerprint']
                    assert len(metadata['controls']) == 8
                    for control in metadata['controls']:
                        assert control['path'] in contract['controls']
                        prior = contract['controls'][control['path']]
                        assert control['training_sha256'] == prior['training_sha256']
                        assert control['complete_sha256'] == prior['complete_sha256']
                records, seal = verifier.predictions(path, gold[target], v18=is_new)
                per_method[item['id']][seed].extend(records)
                run_metadata[item['id'], target, seed] = metadata
                run_manifests.append(dict(method=item['id'], target=target, sources=sources, seed=seed,
                                          path=str(path), reused=not is_new, steps=600,
                                          stream_sha256=metadata['stream_sha256'], parameters=metadata['parameters'],
                                          complete_sha256=sha(path/'COMPLETE.json'), training_sha256=sha(path/'TRAINING.json'),
                                          prediction_seal_sha256=sha(path/'evaluation/PREDICTION_SEAL.json'),
                                          diagnostics_sha256=sha(path/'evaluation/diagnostics.jsonl')))
    expected_identities = {identity(r) for r in per_method[catalog[0]['id']][SEEDS[0]]}
    assert len(expected_identities) == 347
    for values in per_method.values():
        for records in values.values():
            assert len(records) == 347 and {identity(r) for r in records} == expected_identities
    for target in PROTOCOLS:
        for seed in SEEDS:
            direct = run_metadata['four_factor_direct', target, seed]
            sink = run_metadata['four_factor_sink', target, seed]
            assert direct['initial_sha256'] == sink['initial_sha256']
            assert direct['stream_sha256'] == sink['stream_sha256']
    methods = {}
    for item in catalog:
        methods[item['id']] = dict(item, **summarize(per_method[item['id']], stages=item['family'] == 'v18_four_factor'))
        methods[item['id']]['n_distinct_runs'] = 12
        methods[item['id']]['runs'] = [r for r in run_manifests if r['method'] == item['id']]
    controls = [item['id'] for item in catalog if item['family'] == 'v17_reused_control']
    pairs = [('four_factor_'+mode, reference) for mode in MODES for reference in controls]
    pairs.append(('four_factor_direct', 'four_factor_sink'))
    contrasts = {candidate+'_minus_'+reference: dict(candidate=candidate, reference=reference,
                 **contrast(methods[candidate], methods[reference])) for candidate, reference in pairs}
    first = methods[catalog[0]['id']]
    assert set(first['by_core_cell']) == set(CORE_ORDER)
    relation_keys = list(first['by_relation'])
    ordered_relations = [key for relation in RELATION_ORDER for key in relation_keys if key.split('|', 1)[1] == relation]
    assert set(ordered_relations) == set(relation_keys) and len(ordered_relations) == 11
    summary = dict(
        schema='four-factor-attention-v18-summary-v1', time=now(), status='COMPLETE',
        contract_sha256=sha(ROOT/'CONTRACT.json'), aggregate_source_sha256=sha(__file__),
        method_order=[item['id'] for item in catalog], methods=methods, contrasts=contrasts,
        cohort_orders=dict(by_protocol=list(PROTOCOLS), by_core_cell=list(CORE_ORDER),
                           by_relation=ordered_relations, by_target_kind=list(TARGET_KIND_ORDER)),
        seeds=list(SEEDS), n_fields=347, n_messages=74, new_models=24, reused_control_models=96,
        distinct_models=120, new_training_updates=14400, reused_control_updates=57600,
        paired_contrasts=17, comparison_fields_identical=True, matched_source_seed_stream=True,
        qk_removed_every_v18_layer_and_readout=True, v_retained=True, no_new_old_backbone_aliases=True,
        field_f1_computed=False, no_target_selection=True, nll_probability_floor=1e-30,
        verification=dict(file_hashes=len(verifier.verified), final_npz_archives=verifier.npz_count,
                          endpoint_predictions=verifier.field_count, matched_direct_sink_initializations=12),
        statistic_note='Three matched training-seed replicates only; Student t95 df=2, un-clipped; '
                       'overall macro first averages fields within protocol, then four protocols equally.',
        stage_note='v18 factors indexed at true source after sealed inference; head-mean marginal diagnostics '
                   'do not multiply to final destination probability. base_axis_p is not v17 endpoint base_p. '
                   'endian_p is canonical raw probability; endian_equivalence_p marginalizes one-byte endian equivalence.',
        limitations=['Historical test previously inspected, not a fresh confirmatory test.',
                     'Confidence intervals quantify training-seed variation only, not capture or protocol population uncertainty.',
                     'Update counts match; architecture, supervision, parameters and FLOPs are not identical.',
                     'Modbus/TLS END shortcut and known DNS/SMB operator priors remain.'],
        files={},
    )
    markdown, latex = tables(summary)
    artifacts = {ROOT/'TABLES.md': markdown, **{ROOT/'tables'/name: content for name, content in latex.items()}}
    assert not (ROOT/'SUMMARY.json').exists(), 'Preserve prior summary; do not overwrite results silently'
    assert all(not path.exists() for path in artifacts), 'Preserve pre-existing tables'
    for path, content in artifacts.items():
        path.parent.mkdir(exist_ok=True)
        with path.open('x') as stream:
            stream.write(content)
        summary['files'][str(path.relative_to(ROOT))] = sha(path)
    write(ROOT/'SUMMARY.json', summary)
    print(f'COMPLETE: 10 methods, 120 distinct runs, 347 matching fields, 17 paired contrasts; {len(latex)} LaTeX tables', flush=True)
    return summary


if __name__ == '__main__':
    aggregate()
