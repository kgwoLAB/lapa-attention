"""Raw-only all-slot inference, immutable prediction seal, separate gold scoring.

Width/endian/base diagnostic probabilities are indexed at the true source
*after* prediction sealing. They are not a program classifier or gold inputs.
"""
from collections import defaultdict
import hashlib
import math
from pathlib import Path
import statistics

from common18 import ROOT, now, read, sha, write, json
import numpy as np
import torch
from lapa.types import ModelInputs
from lapa.data.schema import select_program
from lapa.programs.bank import native_bank
from executor18 import FourFactorExecutor, WIDTHS, ENDIANS, BASES

CLEAN_KEYS = {'message_id', 'data_hex', 'byte_length', 'raw_sha256'}
ARRAY_KEYS = {'final', 'source', 'width', 'endian', 'base', 'presence', 'valid_mass'}
SLOTS, BATCH = 64, 8
TOLERANCE = 1e-5


def _check_arrays(values, n):
    assert set(values) == ARRAY_KEYS
    shapes = dict(final=(SLOTS,n+2), source=(SLOTS,n), width=(SLOTS,n,len(WIDTHS)),
                  endian=(SLOTS,n,len(ENDIANS)), base=(SLOTS,n,len(BASES)),
                  presence=(SLOTS,), valid_mass=(SLOTS,))
    for key, shape in shapes.items():
        value = values[key]
        assert value.shape == shape, (key, value.shape, shape)
        assert np.isfinite(value).all() and (value >= 0).all() and (value <= 1+TOLERANCE).all(), key
        if key not in ('presence', 'valid_mass'):
            np.testing.assert_allclose(value.sum(-1), 1., atol=TOLERANCE, rtol=TOLERANCE)


def _verify_seal(folder):
    folder = Path(folder).resolve()
    assert ROOT in folder.parents
    seal = read(folder/'PREDICTION_SEAL.json')
    assert seal['gold_read'] is False and seal['protocol_id_input'] is False
    assert seal['slots'] == SLOTS and seal['batch_size'] == BATCH
    assert seal['input_keys'] == sorted(CLEAN_KEYS)
    ids = seal['input_ids']
    assert ids and len(ids) == len(set(ids)) == len(seal['input_hashes']) == len(seal['byte_lengths'])
    assert set(seal['files']) == {mid+'.npz' for mid in ids}
    assert seal['executor_fingerprint'] == FourFactorExecutor().fingerprint
    for mid, n in zip(ids, seal['byte_lengths']):
        assert mid and Path(mid).name == mid and mid not in ('.', '..')
        path = (folder/(mid+'.npz')).resolve()
        assert path.parent == folder and sha(path) == seal['files'][path.name]
        with np.load(path, allow_pickle=False) as values:
            _check_arrays(values, n)
    return seal


@torch.no_grad()
def infer(model, clean_rows, folder, device='cuda'):
    """Predict every public slot without reading gold; return the saved seal."""
    clean_rows = list(clean_rows)
    assert clean_rows and all(set(row) == CLEAN_KEYS for row in clean_rows)
    assert len({row['message_id'] for row in clean_rows}) == len(clean_rows)
    assert model.config['slots'] == SLOTS
    folder = Path(folder).resolve()
    assert ROOT in folder.parents
    folder.mkdir(parents=True, exist_ok=False)
    model.eval()
    files = {}
    for row in clean_rows:
        mid, n = row['message_id'], row['byte_length']
        assert mid and Path(mid).name == mid and mid not in ('.', '..')
        raw = bytes.fromhex(row['data_hex'])
        assert raw and len(raw) == n and hashlib.sha256(raw).hexdigest() == row['raw_sha256']
        pieces = defaultdict(list)
        for start in range(0, SLOTS, BATCH):
            data = torch.tensor(list(raw), dtype=torch.long, device=device)[None].expand(BATCH,-1)
            inputs = ModelInputs(data, torch.ones_like(data, dtype=torch.bool),
                                 torch.arange(start,start+BATCH,dtype=torch.long,device=device))
            output = model(inputs, diagnostics=False)
            for key in sorted(ARRAY_KEYS):
                if key == 'presence':
                    value = output['presence_logits'].sigmoid()
                elif key == 'valid_mass':
                    mass = output['readout']['valid_mass']
                    assert mass.shape == (BATCH, model.config['heads'], 1)
                    assert torch.isfinite(mass).all() and (mass >= 0).all() and (mass <= 1+TOLERANCE).all()
                    value = mass[:, :, 0].mean(1)
                else:
                    value = output[key]
                pieces[key].append(value.detach().cpu().numpy())
        arrays = {key: np.concatenate(parts) for key, parts in pieces.items()}
        _check_arrays(arrays, n)
        path = folder/(mid+'.npz')
        assert not path.exists()
        np.savez_compressed(path, **arrays)
        files[path.name] = sha(path)
    seal = dict(schema='lapa-four-factor-v18-prediction-seal', time=now(), files=files,
                gold_read=False, protocol_id_input=False, input_keys=sorted(CLEAN_KEYS),
                input_ids=[row['message_id'] for row in clean_rows],
                input_hashes=[row['raw_sha256'] for row in clean_rows],
                byte_lengths=[row['byte_length'] for row in clean_rows],
                slots=SLOTS, batch_size=BATCH, config=dict(model.config),
                executor_fingerprint=model.executor.fingerprint,
                model_semantics='four-factor every-layer attention and final readout; no QK/program classifier',
                endpoint_support='bytes 0..n-1, END=n, NULL=n+1; no absent-field or ABSTAIN conflation',
                factor_storage='source marginal and width/endian/base conditionals at every source; head means',
                valid_mass_storage='per-slot head mean of readout valid execution mass before normalization/smoothing; scalar in [0,1], not a distribution over slots',
                presence_not_multiplied_into_endpoint_probability=True)
    write(folder/'PREDICTION_SEAL.json', seal)
    _verify_seal(folder)
    return seal


def _metric(records):
    assert records
    names = ('p_true', 'nll', 'hit1', 'source_p', 'width_p', 'endian_p', 'base_p', 'valid_mass')
    return dict(n_fields=len(records), **{name: statistics.mean(row[name] for row in records) for name in names})


def score(folder, gold_rows):
    """Verify complete 64-slot predictions before any gold metric is computed."""
    folder = Path(folder).resolve()
    seal = _verify_seal(folder)
    gold_rows = list(gold_rows)
    assert gold_rows and len({row['message_id'] for row in gold_rows}) == len(gold_rows)
    assert {row['message_id'] for row in gold_rows} == set(seal['input_ids'])
    source_hashes = dict(zip(seal['input_ids'], seal['input_hashes']))
    source_lengths = dict(zip(seal['input_ids'], seal['byte_lengths']))
    bank = native_bank()
    diagnostics = []
    for row in gold_rows:
        mid, n = row['message_id'], row['byte_length']
        assert row['raw_sha256'] == source_hashes[mid] and n == source_lengths[mid]
        if 'data_hex' in row:
            raw = bytes.fromhex(row['data_hex'])
            assert len(raw) == n and hashlib.sha256(raw).hexdigest() == source_hashes[mid]
        fields = sorted(row['fields'], key=lambda f:(f['start'],f['end'],f['semantic']))
        assert len(fields) <= SLOTS
        with np.load(folder/(mid+'.npz'), allow_pickle=False) as values:
            _check_arrays(values, n)
            for slot, field in enumerate(fields):
                source, field_end = int(field['start']), int(field['end'])
                assert 0 <= source < field_end <= n
                target = n+1 if field['target'] is None else field['target']
                assert isinstance(target, int) and not isinstance(target, bool) and 0 <= target <= n+1
                wi, ei, bi = FourFactorExecutor.native_to_axes(select_program(field,row['protocol'],bank),bank)
                probability = float(values['final'][slot,target])
                diagnostics.append(dict(message_id=mid, slot=slot, protocol=row['protocol'],
                    semantic=field['semantic'], relation=field['relation'], source=source, field_end=field_end,
                    target=target, byte_length=n, target_kind='NULL' if target==n+1 else 'END' if target==n else 'INTERIOR',
                    width_id=wi, endian_id=ei, base_id=bi, p_true=probability,
                    nll=-math.log(max(probability,1e-30)), hit1=int(values['final'][slot].argmax()==target),
                    source_p=float(values['source'][slot,source]), width_p=float(values['width'][slot,source,wi]),
                    endian_p=float(values['endian'][slot,source,ei]), base_p=float(values['base'][slot,source,bi]),
                    valid_mass=float(values['valid_mass'][slot])))
    assert diagnostics
    grouped = {}
    for column in ('protocol', 'semantic', 'relation', 'target_kind'):
        buckets = defaultdict(list)
        for row in diagnostics:
            buckets[row[column]].append(row)
        grouped['by_'+column] = {key:_metric(records) for key,records in sorted(buckets.items())}
    path = folder/'diagnostics.jsonl'
    with path.open('x') as handle:
        for row in diagnostics:
            handle.write(json.dumps(row, sort_keys=True, allow_nan=False)+'\n')
    metrics = dict(overall=_metric(diagnostics), **grouped, endpoint_fields_only=True,
                   field_f1_computed=False, gold_used_for_post_seal_indexing_only=True,
                   factor_condition='width/endian/base indexed at true source after sealed raw-only inference',
                   valid_mass_condition=seal['valid_mass_storage'],
                   prediction_seal_sha256=sha(folder/'PREDICTION_SEAL.json'), diagnostics_sha256=sha(path),
                   nll_probability_floor=1e-30, config=seal['config'], executor_fingerprint=seal['executor_fingerprint'])
    write(folder/'METRICS.json', metrics)
    return metrics
