"""Raw-only, prediction-sealed inference and separate gold-only scoring.

Endpoint probabilities are not field F1.  The endpoint task evaluates public
ordinal slots corresponding to annotated positive fields; field F1 separately
counts all thresholded source/program field decisions, including false positives.
"""
from collections import Counter, defaultdict
import hashlib
import math
from pathlib import Path
import statistics

import numpy as np
import torch

from common16 import metric, now, read, rows, sha, write, write_rows
from lapa.data.schema import select_program
from lapa.models.heads.field import decode_field
from lapa.types import ModelInputs


CLEAN_KEYS = {'message_id', 'data_hex', 'byte_length', 'raw_sha256'}
SLOTS, BATCH = 64, 16


def input_only(row, slots, device):
    """Construct inputs without protocol identity or any annotated field value."""
    assert set(row) == CLEAN_KEYS, set(row) - CLEAN_KEYS
    raw = bytes.fromhex(row['data_hex'])
    assert raw and len(raw) == row['byte_length']
    assert hashlib.sha256(raw).hexdigest() == row['raw_sha256']
    assert all(0 <= s < SLOTS for s in slots)
    data = torch.tensor(list(raw), dtype=torch.long, device=device)[None].expand(len(slots), -1)
    return ModelInputs(data, torch.ones_like(data, dtype=torch.bool),
                       torch.tensor(slots, dtype=torch.long, device=device))


def _check_probabilities(array, shape):
    assert array.shape == shape, (array.shape, shape)
    assert np.isfinite(array).all() and (array >= 0).all()
    np.testing.assert_allclose(array.sum(-1), 1., atol=5e-6, rtol=0.)


def _verify_seal(folder):
    folder = Path(folder).resolve()
    seal = read(folder/'PREDICTION_SEAL.json')
    assert seal['gold_read'] is False and seal['protocol_id_input'] is False
    assert len(set(seal['input_ids'])) == len(seal['input_ids'])
    assert len(seal['input_ids']) == len(seal['input_hashes'])
    for name, digest in seal['files'].items():
        path = (folder/name).resolve()
        assert path.parent == folder and sha(path) == digest, name
    return seal


@torch.no_grad()
def infer(model, clean_rows, folder, device):
    """Infer all 64 slots, seal predictions, and return decoded field candidates.

    Compact program storage retains p(program | predicted source), not the full
    slot x byte x program tensor.  True-source program probability is available
    only through the explicitly post-seal ``diagnose`` function below.
    """
    clean_rows = list(clean_rows)
    assert clean_rows and all(set(r) == CLEAN_KEYS for r in clean_rows)
    assert len({r['message_id'] for r in clean_rows}) == len(clean_rows)
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    model.eval()
    candidates, files, signature = [], {}, None
    for row in clean_rows:
        message_id, n = row['message_id'], row['byte_length']
        assert message_id and Path(message_id).name == message_id and message_id not in ('.', '..')
        arrays, fields = defaultdict(list), []
        for start in range(0, SLOTS, BATCH):
            output = model(input_only(row, list(range(start, start+BATCH)), device))
            current = dict(enabled=bool(output['enabled']),
                           variant=output.get('variant', 'unspecified'),
                           base_kind=output.get('base_kind', 'retrieval_qk'),
                           base_available=bool(output.get('base_available', True)),
                           encoder_kind=output.get('encoder_kind', 'unspecified'))
            signature = current if signature is None else signature
            assert current == signature
            for key in ('base', 'final', 'source'):
                arrays[key].append(output[key].detach().cpu().numpy())
            predicted_source = output['source'].argmax(-1)
            selected_program = output['program'][torch.arange(BATCH, device=predicted_source.device), predicted_source]
            arrays['predicted_source'].append(predicted_source.cpu().numpy())
            arrays['program_at_predicted_source'].append(selected_program.detach().cpu().numpy())
            arrays['presence'].append(output['presence_logits'].sigmoid().detach().cpu().numpy())
            if output['route'] is not None:
                arrays['route'].append(output['route']['prior'].detach().cpu().numpy())
            if output['enabled']:
                for j in range(BATCH):
                    field = decode_field(output, j, model.bank, 0.)
                    if field is not None:
                        fields.append(dict(field, confidence=float(output['presence_logits'][j].sigmoid()), slot=start+j))
        values = {key: np.concatenate(parts) for key, parts in arrays.items()}
        for key in ('base', 'final'):
            _check_probabilities(values[key], (SLOTS, n+2))
        _check_probabilities(values['source'], (SLOTS, n))
        _check_probabilities(values['program_at_predicted_source'], (SLOTS, len(model.bank.programs)))
        if 'route' in values:
            _check_probabilities(values['route'], (SLOTS, n+2))
        if not signature['enabled']:
            assert np.array_equal(values['base'], values['final'])
        assert values['predicted_source'].shape == values['presence'].shape == (SLOTS,)
        assert np.isfinite(values['presence']).all()
        path = folder/(message_id+'.npz')
        assert not path.exists()
        np.savez_compressed(path, **values)
        files[path.name] = sha(path)
        candidates.append(dict(message_id=message_id, status='COMPLETE', fields=fields))
    write_rows(folder/'candidates.jsonl', candidates)
    files['candidates.jsonl'] = sha(folder/'candidates.jsonl')
    write(folder/'PREDICTION_SEAL.json', dict(
        time=now(), files=files, gold_read=False, protocol_id_input=False,
        input_ids=[r['message_id'] for r in clean_rows], input_hashes=[r['raw_sha256'] for r in clean_rows],
        slots=SLOTS, batch_size=BATCH, input_keys=sorted(CLEAN_KEYS), **signature,
        field_decoder='native decode_field: pre-validity source/program argmax, threshold zero',
        program_storage='conditional program vector at predicted source only',
        endpoint_support='raw byte positions, END at byte_length, NULL at byte_length+1; no ABSTAIN conflation'))
    # Runtime evidence allowing stage re-inference only after this same model
    # has produced sealed raw-only predictions for the corresponding messages.
    if not hasattr(model, '_formula16_prediction_seals'):
        model._formula16_prediction_seals = []
    model._formula16_prediction_seals.append(str(folder))
    return candidates


def _field_order(row):
    return sorted(row['fields'], key=lambda f: (f['start'], f['end'], f['semantic']))


def _target(field, n):
    target = n+1 if field['target'] is None else field['target']
    assert isinstance(target, int) and 0 <= target <= n+1
    return target


def _identity(row, field, slot):
    n = row['byte_length']
    target = _target(field, n)
    return dict(message_id=row['message_id'], protocol=row['protocol'],
                semantic=field['semantic'], relation=field['relation'], slot=slot,
                source=int(field['start']), field_end=int(field['end']), byte_length=n,
                target=target, target_kind='NULL' if target == n+1 else 'END' if target == n else 'INTERIOR')


def score(folder, gold_rows):
    """Verify all sealed artifacts before inspecting gold fields; return rows."""
    folder = Path(folder).resolve()
    seal = _verify_seal(folder)
    gold_rows = list(gold_rows)
    assert len({r['message_id'] for r in gold_rows}) == len(gold_rows)
    assert set(seal['input_ids']) == {r['message_id'] for r in gold_rows}
    input_hashes = dict(zip(seal['input_ids'], seal['input_hashes']))
    diagnostics = []
    for row in gold_rows:
        assert row['raw_sha256'] == input_hashes[row['message_id']]
        n = row['byte_length']
        fields = _field_order(row)
        assert len(fields) <= SLOTS
        with np.load(folder/(row['message_id']+'.npz'), allow_pickle=False) as values:
            _check_probabilities(values['final'], (SLOTS, n+2))
            _check_probabilities(values['base'], (SLOTS, n+2))
            _check_probabilities(values['source'], (SLOTS, n))
            for slot, field in enumerate(fields):
                result = _identity(row, field, slot)
                target = result['target']
                p = float(values['final'][slot, target])
                base_p = float(values['base'][slot, target])
                result.update(p_true=p, final_p=p, hit1=int(values['final'][slot].argmax() == target),
                              nll=-math.log(max(p, 1e-30)), base_p=base_p,
                              base_nll=-math.log(max(base_p, 1e-30)),
                              source_p=float(values['source'][slot, field['start']]),
                              source_hit1=int(values['predicted_source'][slot] == field['start']),
                              base_kind=seal['base_kind'],
                              route_p=float(values['route'][slot, target]) if 'route' in values else None)
                diagnostics.append(result)
    write_rows(folder/'diagnostics.jsonl', diagnostics)
    groups = defaultdict(list)
    for record in diagnostics:
        groups[record['protocol']].append(record)
    write(folder/'METRICS.json', dict(
        overall=metric(diagnostics), by_protocol={p: metric(group) for p, group in groups.items()},
        endpoint_fields_only=True, field_f1_not_in_endpoint_metric=True,
        prediction_seal_sha256=sha(folder/'PREDICTION_SEAL.json'),
        diagnostics_sha256=sha(folder/'diagnostics.jsonl'), base_kind=seal['base_kind']))
    return diagnostics


@torch.no_grad()
def diagnose(model, gold_rows, device):
    """Post-seal stage probabilities; labels only index already computed outputs.

    This API intentionally requires ``infer`` to have been called on this model.
    It reuses neither gold source positions nor program IDs as forward inputs.
    Pre-validity heads and the valid-pair route posterior are distinct columns.
    """
    sealed = {}
    for folder in getattr(model, '_formula16_prediction_seals', []):
        seal = _verify_seal(folder)
        sealed.update(zip(seal['input_ids'], seal['input_hashes']))
    assert sealed, 'diagnose requires sealed raw-only infer on this model first'
    gold_rows = list(gold_rows)
    assert all(sealed.get(r['message_id']) == r['raw_sha256'] for r in gold_rows)
    model.eval()
    diagnostics = []
    for row in gold_rows:
        clean = {key: row[key] for key in CLEAN_KEYS}
        # All public slots are inferred before inspecting any field labels.
        outputs = [model(input_only(clean, list(range(start, start+BATCH)), device))
                   for start in range(0, SLOTS, BATCH)]
        for slot, field in enumerate(_field_order(row)):
            output, j = outputs[slot//BATCH], slot % BATCH
            source, program_id = field['start'], select_program(field, row['protocol'], model.bank)
            result = _identity(row, field, slot)
            target = result['target']
            route = output['route']
            result.update(program_id=program_id,
                          source_p=float(output['source'][j, source]),
                          program_p=float(output['program'][j, source, program_id]),
                          program_hit1=int(output['program'][j, source].argmax() == program_id),
                          route_p=float(route['prior'][j, target]) if route is not None else None,
                          route_real_p=float(route['real'][j, target]) if route is not None else None,
                          final_p=float(output['final'][j, target]),
                          route_source_p=float(route['source_marginal'][j, source]) if route is not None and 'source_marginal' in route else None,
                          route_program_p=float(route['program_conditional'][j, source, program_id]) if route is not None and 'program_conditional' in route else None,
                          route_valid_mass=float(route['valid_mass'][j]) if route is not None and 'valid_mass' in route else None,
                          route_sink=float(route['sink'][j]) if route is not None else None,
                          inputs_gold_free=True, program_condition='true source indexed after forward')
            diagnostics.append(result)
        del outputs
    return diagnostics


def selected(candidates, threshold):
    """Filter presence confidence; retaining duplicate predictions is deliberate."""
    assert 0. <= threshold <= 1.
    return [dict(message_id=row['message_id'], status=row.get('status', 'COMPLETE'),
                 fields=[{key: value for key, value in field.items() if key != 'confidence'}
                         for field in row['fields'] if field['confidence'] >= threshold])
            for row in candidates]


def field_f1(gold_rows, predictions, protocol=None, semantic=None):
    """Typed exact (start, end, semantic) multiset F1, independent of target."""
    predictions, gold_rows = list(predictions), list(gold_rows)
    lookup = {row['message_id']: row for row in predictions}
    assert len(lookup) == len(predictions)
    assert len({row['message_id'] for row in gold_rows}) == len(gold_rows)
    assert {row['message_id'] for row in gold_rows} <= set(lookup)
    tp = fp = fn = count = 0
    for row in gold_rows:
        if protocol is not None and row['protocol'] != protocol:
            continue
        count += 1
        def bag(fields):
            return Counter((field['start'], field['end'], field['semantic'])
                           for field in fields if semantic is None or field['semantic'] == semantic)
        actual, predicted = bag(row['fields']), bag(lookup[row['message_id']]['fields'])
        tp += sum((actual & predicted).values())
        fp += sum((predicted - actual).values())
        fn += sum((actual - predicted).values())
    denominator = 2*tp+fp+fn
    return dict(n_messages=count, tp=tp, fp=fp, fn=fn,
                f1=2*tp/denominator if denominator else None)


def choose_threshold(candidates, gold_rows, sources):
    """Presence cutoff from source-dev protocol-macro typed field F1 only."""
    candidates, gold_rows, sources = list(candidates), list(gold_rows), tuple(sources)
    assert sources and len(set(sources)) == len(sources)
    assert {row['protocol'] for row in gold_rows} == set(sources)
    assert {row['message_id'] for row in candidates} == {row['message_id'] for row in gold_rows}
    sweep = []
    for index in range(1, 20):
        threshold = index/20
        predictions = selected(candidates, threshold)
        metrics = {source: field_f1(gold_rows, predictions, source) for source in sources}
        assert all(value['f1'] is not None for value in metrics.values())
        macro = statistics.mean(value['f1'] for value in metrics.values())
        sweep.append(dict(threshold=threshold, macro_f1=macro, f1=macro, by_protocol=metrics))
    best = max(sweep, key=lambda result: (result['macro_f1'], result['threshold']))
    return dict(threshold=best['threshold'], macro_f1=best['macro_f1'],
                sweep=sweep, sources=list(sources),
                selection='source-development protocol-macro typed F1 only; highest threshold wins ties')
