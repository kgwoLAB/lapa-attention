"""TRAIN-only structural, numerical, gradient, and serialization tests for v18.

No development/evaluation packet or model result is read. Standard dot-product
attention entry points are patched to fail during every model forward. The
fixed executor can carry operator metadata, but no learned program/sign/mask
head or learned Q/K similarity head may exist. Value projections are retained
and must receive endpoint gradients in every encoder block.
"""
import argparse
from collections import Counter
from contextlib import ExitStack
from dataclasses import fields as dataclass_fields
import hashlib
import io
import json
from pathlib import Path
import time
from unittest.mock import patch

import common18
from common18 import ROOT, V17, PROTOCOLS, collate, now, write
from executor18 import FourFactorExecutor, WIDTHS, ENDIANS, BASES
from model18 import FourFactorModel, FourFactorRoute, SourceFactor
from losses18 import loss as objective

import torch
from torch import nn
import torch.nn.functional as F
from lapa.types import ModelInputs
from lapa.data.collate import collate_slots
from lapa.programs.bank import native_bank
from lapa.programs.executor import execute as native_execute
from lapa.attention.factory import make_attention


def canonical_examples():
    origin = V17/'data'
    clean = {row['message_id']: row for row in map(json.loads, (origin/'clean/train.jsonl').read_text().splitlines())}
    gold = list(map(json.loads, (origin/'gold/train.jsonl').read_text().splitlines()))
    chosen = []
    for protocol in PROTOCOLS:
        records = [row for row in gold if row['protocol'] == protocol][:2]
        assert len(records) == 2
        for row in records:
            raw = clean[row['message_id']]['data_hex']
            assert hashlib.sha256(bytes.fromhex(raw)).hexdigest() == row['raw_sha256']
            chosen.append(dict(row, data_hex=raw,
                               fields=sorted(row['fields'], key=lambda field: (field['start'], field['end'], field['semantic']))))
    return chosen, origin


def oracle_check(examples, device):
    samples = [(row, slot) for row in examples for slot in range(len(row['fields']))]
    bank = native_bank()
    native = collate_slots(samples, bank).to(device)
    inputs, labels = collate(samples, device)
    executor = FourFactorExecutor().to(device)
    assert not list(executor.parameters())
    assert executor.factor_shape == (4, 2, 7) and int(executor.grid_legal.sum()) == 42
    assert tuple(executor.widths) == WIDTHS and tuple(executor.endians) == ENDIANS and tuple(executor.bases) == BASES
    result = executor(inputs)
    reference = native_execute(bank, inputs.data, inputs.observed)
    index = torch.arange(len(samples), device=device)
    axis_labels = executor.native_labels_to_axes(native.labels.programs)
    for column, name in enumerate(('width', 'endian', 'base')):
        assert torch.equal(axis_labels[:, column], labels[name])
    selected = index, labels['source'], labels['width'], labels['endian'], labels['base']
    native_selected = index, native.labels.sources, native.labels.programs
    assert result.valid[selected].all()
    assert torch.equal(result.target[selected], labels['target'])
    for name in ('target', 'null', 'decoded'):
        assert torch.equal(getattr(result, name)[selected], getattr(reference, name)[native_selected]), name
    assert not result.valid.masked_select(~executor.grid_legal[None, None].expand_as(result.valid)).any()
    kind_counts, relations = Counter(), Counter()
    storage_length = inputs.data.shape[1]
    for i, (row, slot) in enumerate(samples):
        field = row['fields'][slot]
        kind = 'NULL' if field['target'] is None else 'END' if field['target'] == row['byte_length'] else 'INTERIOR'
        expected = storage_length+1 if kind == 'NULL' else storage_length if kind == 'END' else field['target']
        assert labels['target'][i].item() == expected
        kind_counts[kind] += 1
        relations[field['relation']] += 1
    assert len(samples) == 34 and set(kind_counts) == {'END', 'NULL', 'INTERIOR'}
    for name in ('target', 'valid', 'candidate_mask', 'decoded', 'null'):
        # Width 1 has no identifiable endian. Both fixed decodings must match.
        assert torch.equal(getattr(result, name)[:, :, 0, 0], getattr(result, name)[:, :, 0, 1]), name
    return dict(fields=len(samples), target_kinds=dict(kind_counts), relation_counts=dict(relations),
                native_exact_target_decoded_null=True, endian_width1_equivalence=True,
                executor_parameters=0, legal_grid_cells=42, full_grid_cells=56,
                executor_fingerprint=executor.fingerprint)


def forbid_standard_attention():
    stack = ExitStack()
    def fail(*args, **kwargs):
        raise AssertionError('v18 called a forbidden standard QK attention entry point')
    stack.enter_context(patch.object(F, 'scaled_dot_product_attention', side_effect=fail))
    stack.enter_context(patch.object(nn.MultiheadAttention, 'forward', side_effect=fail))
    if hasattr(torch, '_native_multi_head_attention'):
        stack.enter_context(patch.object(torch, '_native_multi_head_attention', side_effect=fail))
    for cls in {type(make_attention(name)) for name in ('sdpa', 'rope', 'cope', 'tape')}:
        stack.enter_context(patch.object(cls, 'logits', side_effect=fail))
    return stack


def check_structure(model):
    forbidden = ('query', 'key', 'q_proj', 'k_proj', 'qkv', 'in_proj', 'program', 'sign', 'mask')
    parameters = dict(model.named_parameters())
    for name in parameters:
        pieces = name.lower().split('.')
        assert not any(piece == word or piece.startswith(word+'_') or piece.endswith('_'+word)
                       for piece in pieces for word in forbidden), name
    assert not any(isinstance(module, nn.MultiheadAttention) for module in model.modules())
    assert not list(model.executor.parameters())
    routes = [block.routing for block in model.blocks] + [model.readout]
    assert len(routes) == model.config['layers']+1
    for route in routes:
        assert isinstance(route, FourFactorRoute) and isinstance(route.source_factor, SourceFactor)
        assert set(dict(route.named_children())) == {'source_factor', 'width_factor', 'endian_factor', 'base_factor'}
        assert route.width_factor.out_features == model.config['heads']*4
        assert route.endian_factor.out_features == model.config['heads']*2
        assert route.base_factor.out_features == model.config['heads']*7
    for block in model.blocks:
        assert isinstance(block.value, nn.Linear) and isinstance(block.output, nn.Linear)
    return dict(learned_parameters=sum(parameter.numel() for parameter in parameters.values()),
                factor_modules=len(routes), no_learned_qk_program_sign_mask_heads=True,
                value_projection_retained=True)


def _probability(probability, support, tolerance):
    mask = torch.broadcast_to(support, probability.shape)
    assert torch.isfinite(probability).all() and (probability >= -tolerance).all()
    assert not probability.masked_select(~mask).any()
    assert (probability <= 1+tolerance).all()


def check_distributions(model, output, inputs, tolerance):
    batch, length = inputs.data.shape
    heads, count = model.config['heads'], length+1
    observed = inputs.observed
    endpoint_support = torch.cat((observed, torch.ones(batch, 2, device=observed.device, dtype=torch.bool)), -1)
    receiver_support = torch.cat((torch.ones(batch, 1, device=observed.device, dtype=torch.bool), observed), -1)
    assert not any(name in output for name in ('program', 'program_logits', 'sign', 'mask'))
    assert output['final'].shape == (batch, length+2)
    _probability(output['final'], endpoint_support, tolerance)
    torch.testing.assert_close(output['final'].sum(-1), torch.ones(batch, device=observed.device), atol=tolerance, rtol=tolerance)
    assert output['source'].shape == (batch, length)
    _probability(output['source'], observed, tolerance)
    torch.testing.assert_close(output['source'].sum(-1), torch.ones(batch, device=observed.device), atol=tolerance, rtol=tolerance)
    for factor, classes in (('width', 4), ('endian', 2), ('base', 7)):
        assert output[factor].shape == (batch, length, classes)
        _probability(output[factor], observed[:, :, None], tolerance)
        torch.testing.assert_close(output[factor].sum(-1), observed.to(output[factor].dtype), atol=tolerance, rtol=tolerance)
    assert len(output['layers']) == model.config['layers']
    for i, route in enumerate(output['layers'] + [output['readout']]):
        final = i == model.config['layers']
        queries = 1 if final else count
        receivers = torch.ones(batch, 1, device=observed.device, dtype=torch.bool) if final else receiver_support
        assert route['source'].shape == (batch, heads, queries, length)
        _probability(route['source'], receivers[:, None, :, None] & observed[:, None, None, :], tolerance)
        expected_rows = receivers[:, None].expand(batch, heads, queries).to(route['source'].dtype)
        torch.testing.assert_close(route['source'].sum(-1), expected_rows, atol=tolerance, rtol=tolerance)
        assert route['destination'].shape == (batch, heads, queries, length+2)
        _probability(route['destination'], receivers[:, None, :, None] & endpoint_support[:, None, None, :], tolerance)
        torch.testing.assert_close(route['destination'].sum(-1), expected_rows, atol=tolerance, rtol=tolerance)
        for factor, classes in (('width', 4), ('endian', 2), ('base', 7)):
            assert route[factor].shape == (batch, heads, length, classes)
            _probability(route[factor], observed[:, None, :, None], tolerance)
            torch.testing.assert_close(route[factor].sum(-1), observed[:, None].expand(batch, heads, length).to(route[factor].dtype), atol=tolerance, rtol=tolerance)
        assert torch.isfinite(route['valid_mass']).all()
        assert (route['valid_mass'] >= -tolerance).all() and (route['valid_mass'] <= 1+tolerance).all()
        if not final:
            assert route['attention'].shape == (batch, heads, count, count)
            allowed = receiver_support[:, None, :, None] & receiver_support[:, None, None, :]
            _probability(route['attention'], allowed, tolerance)
            torch.testing.assert_close(route['attention'].sum(-1), expected_rows, atol=tolerance, rtol=tolerance)
            # A separable additive a_i+b_j score would erase receiver identity.
            assert (route['source'][:, :, 0] - route['source'][:, :, 1]).abs().max() > 1e-8
        else:
            assert 'attention' not in route


def check_padding(model, inputs, tolerance):
    length, extra = inputs.data.shape[1], 7
    padded = ModelInputs(F.pad(inputs.data, (0, extra), value=255),
                         F.pad(inputs.observed, (0, extra), value=False), inputs.slots)
    with torch.no_grad():
        original, extended = model(inputs), model(padded)
    check_distributions(model, original, inputs, tolerance)
    check_distributions(model, extended, padded, tolerance)
    aligned_final = torch.cat((extended['final'][:, :length], extended['final'][:, length+extra:]), -1)
    torch.testing.assert_close(original['final'], aligned_final, atol=tolerance, rtol=tolerance)
    for factor in ('source', 'width', 'endian', 'base'):
        torch.testing.assert_close(original[factor], extended[factor][:, :length], atol=tolerance, rtol=tolerance)
    for i, (before, after) in enumerate(zip(original['layers']+[original['readout']], extended['layers']+[extended['readout']])):
        queries = 1 if i == model.config['layers'] else length+1
        torch.testing.assert_close(before['source'], after['source'][:, :, :queries, :length], atol=tolerance, rtol=tolerance)
        destination = torch.cat((after['destination'][:, :, :queries, :length], after['destination'][:, :, :queries, length+extra:]), -1)
        torch.testing.assert_close(before['destination'], destination, atol=tolerance, rtol=tolerance)
        for factor in ('width', 'endian', 'base'):
            torch.testing.assert_close(before[factor], after[factor][:, :, :length], atol=tolerance, rtol=tolerance)
        if 'attention' in before:
            torch.testing.assert_close(before['attention'], after['attention'][:, :, :queries, :queries], atol=tolerance, rtol=tolerance)
    return float((original['final']-aligned_final).abs().max())


def endpoint_gradient_check(model, inputs, labels):
    model.zero_grad(set_to_none=True)
    output = model(inputs)
    pos = labels['present'].bool()
    endpoint = -output['final'][pos].gather(1, labels['target'][pos, None]).clamp_min(1e-30).log().mean()
    endpoint.backward()
    norms = {}
    routes = [('blocks.'+str(i)+'.routing', block.routing) for i, block in enumerate(model.blocks)] + [('readout', model.readout)]
    for prefix, route in routes:
        for factor in ('source_factor', 'width_factor', 'endian_factor', 'base_factor'):
            parameters = list(getattr(route, factor).parameters())
            assert parameters and all(p.grad is not None and torch.isfinite(p.grad).all() for p in parameters)
            norm = sum(float(p.grad.abs().sum()) for p in parameters)
            assert norm > 0, (prefix, factor, 'factor receives no endpoint gradient')
            norms[prefix+'.'+factor] = norm
    for i, block in enumerate(model.blocks):
        for name in ('value', 'output'):
            parameters = list(getattr(block, name).parameters())
            assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in parameters)
            norm = sum(float(p.grad.abs().sum()) for p in parameters)
            assert norm > 0, (i, name)
            norms[f'blocks.{i}.{name}'] = norm
    model.zero_grad(set_to_none=True)
    return norms


def independent_loss(output, labels):
    pos = labels['present'].bool()
    presence_terms = [F.softplus(-output['presence_logits'][pos]).mean()]
    if (~pos).any():
        presence_terms.append(F.softplus(output['presence_logits'][~pos]).mean())
    per_field = []
    for index in torch.where(pos)[0]:
        source = int(labels['source'][index])
        terms = [-output['width'][index, source, labels['width'][index]].clamp_min(1e-30).log(),
                 -output['base'][index, source, labels['base'][index]].clamp_min(1e-30).log()]
        if int(labels['width'][index]) != 0:
            terms.append(-output['endian'][index, source, labels['endian'][index]].clamp_min(1e-30).log())
        per_field.append(sum(terms))
    return dict(presence=torch.stack(presence_terms).mean(),
                source=-output['source'][pos].gather(1, labels['source'][pos, None]).clamp_min(1e-30).log().mean(),
                attributes=torch.stack(per_field).mean(),
                endpoint=-output['final'][pos].gather(1, labels['target'][pos, None]).clamp_min(1e-30).log().mean())


def checkpoint_roundtrip(model, inputs, tolerance, device):
    model.eval()
    with torch.no_grad():
        expected = model(inputs)['final']
    buffer = io.BytesIO()
    torch.save(dict(config=model.config, executor_fingerprint=model.executor.fingerprint, state_dict=model.state_dict()), buffer)
    buffer.seek(0)
    payload = torch.load(buffer, map_location=device, weights_only=True)
    restored = FourFactorModel(**payload['config']).to(device).eval()
    assert restored.executor.fingerprint == payload['executor_fingerprint']
    restored.load_state_dict(payload['state_dict'], strict=True)
    with torch.no_grad():
        actual = restored(inputs)['final']
    torch.testing.assert_close(expected, actual, atol=tolerance, rtol=tolerance)
    return float((expected-actual).abs().max())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    parser.add_argument('--output')
    args = parser.parse_args()
    started = time.monotonic()
    torch.set_num_threads(2)
    if args.device == 'cuda':
        assert torch.cuda.is_available(), 'No silent GPU-to-CPU fallback'
        torch._native.registry.deregister_op_overrides(disable_dsl_names='triton')
        torch.cuda.set_per_process_memory_fraction(.20)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    tolerance = 1e-5 if args.device == 'cuda' else 3e-6
    examples, origin = canonical_examples()
    oracle = oracle_check(examples, args.device)
    assert {field.name for field in dataclass_fields(ModelInputs)} == {'data', 'observed', 'slots'}
    batches = [[(row, slot) for row in examples for slot in (0 if j == 0 else len(row['fields'])-1, 63)] for j in range(2)]
    inputs, labels = collate(batches[0], args.device)
    assert labels['present'].sum() == 8 and (~labels['present']).sum() == 8
    results = []
    with forbid_standard_attention():
        for mode in ('direct', 'sink'):
            torch.manual_seed(180018)
            model = FourFactorModel(mode=mode).to(args.device)
            structure = check_structure(model)
            model.eval()
            padding_error = check_padding(model, inputs, tolerance)
            with torch.no_grad():
                first = model(inputs)
                changed_labels = {name: value.clone() for name, value in labels.items()}
                changed_labels['target'].zero_()
                unchanged = model(inputs)
                torch.testing.assert_close(first['final'], unchanged['final'], atol=tolerance, rtol=tolerance)
                compact = model(inputs, diagnostics=False)
                assert compact['layers'] == []
                torch.testing.assert_close(first['final'], compact['final'], atol=tolerance, rtol=tolerance)
                for forbidden in (labels, (inputs, labels)):
                    try:
                        model(forbidden)
                    except (TypeError, AttributeError, AssertionError):
                        pass
                    else:
                        raise AssertionError('Model accepted annotations as forward input')
            gradient_norms = endpoint_gradient_check(model, inputs, labels)
            optimizer = torch.optim.AdamW(model.parameters(), lr=.002, weight_decay=.01)
            curve = []
            model.train()
            for samples in batches:
                batch_inputs, batch_labels = collate(samples, args.device)
                optimizer.zero_grad(set_to_none=True)
                output = model(batch_inputs)
                check_distributions(model, output, batch_inputs, tolerance)
                total, parts = objective(output, batch_labels)
                expected = independent_loss(output, batch_labels)
                assert set(parts) == {'presence', 'source', 'attributes', 'endpoint'}
                for name in parts:
                    torch.testing.assert_close(parts[name], expected[name], atol=tolerance, rtol=tolerance)
                torch.testing.assert_close(total, sum(parts.values()), atol=tolerance, rtol=tolerance)
                # Absent slots have no source/attribute/endpoint targets.
                changed = {name: value.clone() for name, value in batch_labels.items()}
                for name in ('source', 'target', 'width', 'endian', 'base'):
                    changed[name][~changed['present']] = 99999
                changed_total, changed_parts = objective(output, changed)
                torch.testing.assert_close(total, changed_total, atol=tolerance, rtol=tolerance)
                total.backward()
                assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
                optimizer.step()
                curve.append(dict(total=float(total.detach()), **{name: float(value.detach()) for name, value in parts.items()}))
            model.eval()
            trained_padding_error = check_padding(model, inputs, tolerance)
            checkpoint_error = checkpoint_roundtrip(model, inputs, tolerance, args.device)
            results.append(dict(mode=mode, status='PASS', steps=2, **structure,
                                endpoint_gradient_l1=gradient_norms, loss_curve=curve,
                                initial_padding_max_abs_error=padding_error,
                                trained_padding_max_abs_error=trained_padding_error,
                                checkpoint_max_abs_error=checkpoint_error))
            print(json.dumps(dict(mode=mode, status='PASS')), flush=True)
    report = dict(status='PASS', time=now(), device=args.device, seconds=time.monotonic()-started,
                  train_data_origin=str(origin), train_messages=[row['message_id'] for row in examples],
                  development_read=False, evaluation_read=False, synthetic_observed_packets=False,
                  standard_qk_attention_calls_forbidden=True, no_learned_program_sign_mask_head=True,
                  every_encoder_and_readout_uses_four_factors=True, values_retained=True,
                  padded_rows_zero=True, observed_rows_normalized=True, negative_queries_not_null_targets=True,
                  oracle=oracle, variants=results, tolerance=tolerance,
                  cuda_scatter_bitwise_determinism_claimed=False)
    if args.output:
        path = Path(args.output) if Path(args.output).is_absolute() else ROOT/args.output
        write(path, report)
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    return report


if __name__ == '__main__':
    main()
