"""Training-only v17 smoke, loss, invariant and checkpoint contract tests.

The first two canonical TRAIN messages per real protocol are the only packets
read. Annotation access is confined to loss/oracle checks, never model inputs.
CUDA scatter_add uses atomic floating-point additions: unchanged-input and
checkpoint comparisons therefore allow 1e-5, not bitwise determinism. Exact
native Off/hybrid initialization parity remains a bitwise state-dict test.
"""

import argparse
from dataclasses import fields as dataclass_fields
import io
import json
from pathlib import Path
import time

from common17 import ROOT, V16, PROTOCOLS, BACKBONES, VARIANTS, NO_BACKBONE, ATTRIBUTE_VARIANTS, rows, write, now, sample_stream
from models17 import SearchModel
from losses17 import loss as formula_loss
from attribute17 import AttributeDestination

import torch
import torch.nn.functional as F
from lapa import LapaModel, LapaConfig, ModelInputs
from lapa.data.collate import collate_slots
from lapa.programs.executor import execute
from lapa.training.losses import joint_loss


def canonical_examples():
    """Do not load development/evaluation files or their contracts."""
    origin = V16 / 'data'
    clean = {r['message_id']: r for r in rows(origin / 'clean/train.jsonl')}
    chosen = []
    gold = rows(origin / 'gold/train.jsonl')
    for protocol in PROTOCOLS:
        candidates = [r for r in gold if r['protocol'] == protocol]
        assert len(candidates) >= 2, protocol
        for row in candidates[:2]:
            chosen.append(dict(row, data_hex=clean[row['message_id']]['data_hex'],
                               fields=sorted(row['fields'], key=lambda f: (f['start'], f['end'], f['semantic']))))
    return chosen, origin


def auxiliary(name):
    return name.startswith('host.router.') or name.startswith('presence.')


def assert_distribution(output, inputs, tolerance):
    probability = output['final']
    support = torch.cat((inputs.observed, torch.ones(len(probability), 2, dtype=torch.bool, device=probability.device)), -1)
    assert probability.shape == support.shape
    assert torch.isfinite(probability).all() and (probability >= 0).all() and (probability <= 1 + tolerance).all()
    assert torch.allclose(probability.sum(-1), torch.ones(len(probability), device=probability.device), atol=tolerance, rtol=tolerance)
    assert not probability.masked_select(~support).any()
    assert not output['source'].masked_select(~inputs.observed).any()
    assert not output['program'].masked_select(~inputs.observed[:, :, None].expand_as(output['program'])).any()
    assert torch.allclose(output['source'].sum(-1), torch.ones(len(probability), device=probability.device), atol=tolerance, rtol=tolerance)
    assert torch.allclose(output['program'].sum(-1)[inputs.observed], torch.ones_like(output['program'].sum(-1)[inputs.observed]), atol=tolerance, rtol=tolerance)
    if output['route'] is not None:
        prior = output['route']['prior']
        assert torch.isfinite(prior).all() and not prior.masked_select(~support).any()
        assert torch.allclose(prior.sum(-1), torch.ones(len(prior), device=prior.device), atol=tolerance, rtol=tolerance)


def oracle_check(bank, examples, device):
    samples = [(record, slot) for record in examples for slot in range(len(record['fields']))]
    batch = collate_slots(samples, bank).to(device)
    result = execute(bank, batch.inputs.data, batch.inputs.observed)
    index = torch.arange(len(samples), device=device)
    source, program, target = batch.labels.sources, batch.labels.programs, batch.labels.targets
    assert result.valid[index, source, program].all()
    assert torch.equal(result.target[index, source, program], target)
    # The equivalent-program loss's candidate set must include the annotated
    # native program, including mask/guard and SMB2 companion-field rules.
    equivalent = result.valid[index, source] & (result.target[index, source] == target[:, None])
    assert equivalent[index, program].all() and equivalent.any(-1).all()
    kind_counts = {'END': 0, 'NULL': 0, 'INTERIOR': 0}
    length = batch.inputs.data.shape[1]
    for i, (record, slot) in enumerate(samples):
        field = record['fields'][slot]
        if field['target'] is None:
            assert target[i].item() == length + 1
            kind_counts['NULL'] += 1
        elif field['target'] == record['byte_length']:
            assert target[i].item() == length
            kind_counts['END'] += 1
        else:
            assert target[i].item() == field['target']
            kind_counts['INTERIOR'] += 1
    assert len(samples) == 34, f'Canonical first-two TRAIN packet fixture changed: {len(samples)} fields, expected 34'
    return dict(fields=len(samples), target_kinds=kind_counts,
                gold_program_in_equivalence_mask=True,
                equivalent_program_counts=equivalent.sum(-1).tolist())


def checkpoint_roundtrip(model, inputs, device, tolerance):
    model.eval()
    with torch.no_grad():
        expected = model(inputs)['final']
    buffer = io.BytesIO()
    torch.save(dict(variant=model.variant, backbone=model.backbone,
                    config=model.config.to_dict(), bank=model.bank.fingerprint,
                    state_dict=model.state_dict()), buffer)
    buffer.seek(0)
    payload = torch.load(buffer, map_location=device, weights_only=True)
    restored = SearchModel(payload['variant'], payload['backbone']).to(device).eval()
    assert restored.variant == payload['variant'] and restored.backbone == payload['backbone']
    assert restored.config.to_dict() == payload['config'] and restored.bank.fingerprint == payload['bank']
    restored.load_state_dict(payload['state_dict'], strict=True)
    with torch.no_grad():
        actual = restored(inputs)['final']
    assert torch.allclose(expected, actual, atol=tolerance, rtol=tolerance), model.variant
    return float((expected - actual).abs().max())


def expected_weighted_parts(model, output, labels):
    """Check the returned losses independently of losses17's sum operation."""
    if model.variant == 'off':
        return {'endpoint': -output['final'][labels.present].gather(1, labels.targets[labels.present, None]).clamp_min(1e-30).log().mean()}
    _, raw_parts = joint_loss(output, labels)
    positive = labels.present.bool()
    source, program = labels.sources[positive], labels.programs[positive]
    index = torch.arange(len(source), device=source.device)
    if model.variant == 'axis_direct':
        terms = []
        for axis, ids in model.bank.axis_ids().items():
            selected = output['axis_logits'][axis][positive][index, source]
            terms.append(F.cross_entropy(selected, ids.to(source.device)[program]))
        raw_parts['program'] = 4 * torch.stack(terms).mean()
    elif model.variant == 'equivalent_program':
        execution = output['route']['execution']
        equivalent = execution.valid[positive][index, source] & (execution.target[positive][index, source] == labels.targets[positive, None])
        assert equivalent[index, program].all()
        log_probability = F.log_softmax(output['program_logits'][positive][index, source], -1)
        raw_parts['program'] = -torch.logsumexp(log_probability.masked_fill(~equivalent, float('-inf')), -1).mean()
    assert set(model.loss_weights) == {'presence', 'source', 'program', 'endpoint'}
    assert all(value > 0 for value in model.loss_weights.values())
    return {name: value * model.loss_weights[name] for name, value in raw_parts.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    parser.add_argument('--output')
    args = parser.parse_args()
    started = time.monotonic()
    torch.set_num_threads(2)
    if args.device == 'cuda':
        assert torch.cuda.is_available(), 'CUDA requested but unavailable; no silent fallback'
        torch._native.registry.deregister_op_overrides(disable_dsl_names='triton')
        torch.cuda.set_per_process_memory_fraction(.20)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    tolerance = 1e-5 if args.device == 'cuda' else 3e-6
    examples, origin = canonical_examples()
    seed = 170017
    torch.manual_seed(seed)
    reference = LapaModel(LapaConfig(attention='tape')).to(args.device)
    reference_state = {name: tensor.detach().cpu().clone() for name, tensor in reference.state_dict().items()}
    oracle = oracle_check(reference.bank, examples, args.device)
    batches = list(sample_stream(examples, PROTOCOLS, seed + 1, 2))
    probe = collate_slots(batches[0], reference.bank).to(args.device)
    assert {f.name for f in dataclass_fields(ModelInputs)} == {'data', 'observed', 'slots'}
    assert set(vars(probe.inputs)) == {'data', 'observed', 'slots'}
    parity = []
    for backbone in BACKBONES:
        for variant in ('off', 'hybrid'):
            torch.manual_seed(seed)
            old = LapaModel(LapaConfig(attention=backbone, lapa_enabled=variant == 'hybrid')).to(args.device).eval()
            torch.manual_seed(seed)
            current = SearchModel(variant, backbone).to(args.device).eval()
            assert old.state_dict().keys() == current.state_dict().keys()
            assert all(torch.equal(value, current.state_dict()[name]) for name, value in old.state_dict().items())
            with torch.no_grad():
                previous, actual = old(probe.inputs), current(probe.inputs)
            for key in ('final', 'base', 'source', 'program', 'program_logits', 'presence_logits'):
                assert torch.allclose(previous[key], actual[key], atol=tolerance, rtol=tolerance), (variant, backbone, key)
            error = checkpoint_roundtrip(current, probe.inputs, args.device, tolerance)
            parity.append(dict(variant=variant, backbone=backbone, exact_initial_state=True,
                               checkpoint_max_abs_error=error, tests='PASS'))
            del old, current
    results = []
    for variant in ('off',) + VARIANTS:
        variant_started = time.monotonic()
        backbone = 'none' if variant in NO_BACKBONE else 'tape'
        torch.manual_seed(seed)
        model = SearchModel(variant, backbone).to(args.device)
        state = model.state_dict()
        shared = [name for name in sorted(set(state) & set(reference_state)) if state[name].shape == reference_state[name].shape]
        assert shared
        for name in shared:
            assert torch.equal(state[name].detach().cpu(), reference_state[name]), (variant, name)
        if not model.native_endpoint_qk:
            assert not hasattr(model.host, 'retrieval_query') and not hasattr(model.host, 'retrieval_key')
            assert not hasattr(model, 'special_endpoints')
        if variant in ATTRIBUTE_VARIANTS:
            assert isinstance(model.attribute, AttributeDestination)
            assert hasattr(model.attribute, 'query_attributes') and hasattr(model.attribute, 'key_attributes')
            assert not model.native_endpoint_qk
        if variant in NO_BACKBONE:
            assert not model.encoder_qkv
            assert not hasattr(model.host, 'cope')
            assert not any('.attention.' in name or '.query.' in name or '.key.' in name or '.value.' in name for name, _ in model.host.named_parameters())
            assert not any(isinstance(module, torch.nn.MultiheadAttention) for module in model.host.modules())

        model.eval()
        with torch.no_grad():
            output = model(probe.inputs)
            assert_distribution(output, probe.inputs, tolerance)
            old_length, extra = probe.inputs.data.shape[1], 7
            padded = ModelInputs(F.pad(probe.inputs.data, (0, extra), value=255),
                                 F.pad(probe.inputs.observed, (0, extra), value=False), probe.inputs.slots)
            extended = model(padded)
            assert_distribution(extended, padded, tolerance)
            aligned = torch.cat((extended['final'][:, :old_length], extended['final'][:, old_length + extra:]), -1)
            padding_error = float((output['final'] - aligned).abs().max())
            assert torch.allclose(output['final'], aligned, atol=tolerance, rtol=tolerance), (variant, 'final_padding', padding_error)
            assert torch.allclose(output['program'], extended['program'][:, :old_length], atol=tolerance, rtol=tolerance), (variant, 'program_padding')
            assert torch.allclose(output['source'], extended['source'][:, :old_length], atol=tolerance, rtol=tolerance), (variant, 'source_padding')
            target_backup = probe.labels.targets.clone()
            probe.labels.targets.zero_()
            changed_labels = model(probe.inputs)
            probe.labels.targets.copy_(target_backup)
            assert torch.allclose(output['final'], changed_labels['final'], atol=tolerance, rtol=tolerance)
            for forbidden in (probe, probe.labels):
                try:
                    model(forbidden)
                except TypeError:
                    pass
                else:
                    raise AssertionError('forward accepted labels/metadata')

        endpoint_attribute_gradients = None
        if variant == 'attr_only':
            model.zero_grad(set_to_none=True)
            predicted = model(probe.inputs)
            endpoint = -predicted['final'][probe.labels.present].gather(1, probe.labels.targets[probe.labels.present, None]).clamp_min(1e-30).log().mean()
            endpoint.backward()
            endpoint_attribute_gradients = {}
            for name, parameter in [('source', model.host.router.source_score.weight),
                                    ('program_embedding', model.attribute.program_embedding.weight),
                                    *[(axis, head.weight) for axis, head in model.host.router.axis_heads.items()]]:
                assert parameter.grad is not None and torch.isfinite(parameter.grad).all()
                magnitude = float(parameter.grad.abs().sum())
                assert magnitude > 0, (variant, 'endpoint_only_gradient', name)
                endpoint_attribute_gradients[name] = magnitude
            model.zero_grad(set_to_none=True)

        optimizer = torch.optim.AdamW(model.parameters(), lr=.002, weight_decay=.01)
        initial_aux = {name: parameter.detach().clone() for name, parameter in model.named_parameters() if auxiliary(name)}
        curve = []
        active_names = set()
        model.train()
        for samples in batches:
            batch = collate_slots(samples, model.bank).to(args.device)
            optimizer.zero_grad(set_to_none=True)
            output = model(batch.inputs)
            assert_distribution(output, batch.inputs, tolerance)
            value, pieces = formula_loss(model, output, batch.labels)
            expected_pieces = expected_weighted_parts(model, output, batch.labels)
            assert set(pieces) == set(expected_pieces)
            assert torch.isfinite(value) and torch.allclose(value, sum(pieces.values()), atol=tolerance, rtol=tolerance)
            for name in pieces:
                assert torch.allclose(pieces[name], expected_pieces[name], atol=tolerance, rtol=tolerance), (variant, name)
            value.backward()
            for name, parameter in model.named_parameters():
                if parameter.grad is not None:
                    assert torch.isfinite(parameter.grad).all(), (variant, name)
                    active_names.add(name)
                if variant == 'off' and auxiliary(name):
                    assert parameter.grad is None, (variant, name)
            if variant != 'off':
                for prefix in ('presence.', 'host.router.source_score.', 'host.router.axis_heads.'):
                    assert any(parameter.grad is not None for name, parameter in model.named_parameters() if name.startswith(prefix)), (variant, prefix)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
            optimizer.step()
            curve.append(dict(total=float(value.detach()), **{name: float(piece.detach()) for name, piece in pieces.items()}))
        if variant == 'off':
            assert all(torch.equal(initial_aux[name], parameter) for name, parameter in model.named_parameters() if auxiliary(name))
        checkpoint_error = checkpoint_roundtrip(model, probe.inputs, args.device, tolerance)
        result = dict(variant=variant, backbone=backbone, steps=2,
                      parameters=sum(parameter.numel() for parameter in model.parameters()),
                      parameters_with_gradient=sum(parameter.numel() for name, parameter in model.named_parameters() if name in active_names),
                      shared_initial_tensors=len(shared), loss_weights=model.loss_weights,
                      loss_curve=curve, padding_max_abs_error=padding_error,
                      checkpoint_max_abs_error=checkpoint_error,
                      endpoint_only_attribute_gradients=endpoint_attribute_gradients,
                      seconds=time.monotonic() - variant_started, tests='PASS')
        results.append(result)
        print(json.dumps(dict(variant=variant, status='PASS', seconds=result['seconds'])), flush=True)
        del model, optimizer
    result = dict(status='PASS', time=now(), device=args.device, seconds=time.monotonic() - started,
                  train_data_origin=str(origin), examples=[record['message_id'] for record in examples],
                  protocols=list(PROTOCOLS), evaluation_data_read=False, development_data_read=False,
                  synthetic_packets=False, oracle=oracle, legacy_parity=parity, variants=results,
                  probability_tolerance=tolerance, cuda_scatter_bitwise_determinism_claimed=False,
                  checks=['native_off_hybrid_exact_initialization_all_four_backbones',
                          'shared_initial_tensors', 'two_adamw_updates_all_31_variants',
                          'all_on_four_positive_weighted_losses', 'off_only_endpoint_auxiliary_grad_none_unchanged',
                          'attribute_actual_qk_replacement', 'attribute_endpoint_gradient_all_axes_and_source',
                          'cnn_gru_encoder_no_qkv', 'finite_support_normalized_probabilities',
                          'nonzero_right_padding_final_program_source_invariance',
                          'END_NULL_remapping', 'raw_only_forward',
                          'native_bank_oracle_34_known_training_fields', 'equivalence_mask_includes_gold_program',
                          'checkpoint_variant_backbone_roundtrip'])
    if args.output:
        destination = Path(args.output) if Path(args.output).is_absolute() else ROOT / args.output
        write(destination, result)
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
