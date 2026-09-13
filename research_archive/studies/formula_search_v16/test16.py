"""Real-training-packet smoke and invariance tests; no evaluation data are read."""
import argparse
from dataclasses import fields as dataclass_fields
import io
import json
from pathlib import Path
import time

from common16 import ROOT, STUDY, PROTOCOLS, load_data, rows, write, now, sample_stream
from models16 import FormulaModel, VARIANTS
from losses16 import formula_loss

import torch
import torch.nn.functional as F
from lapa import LapaModel, LapaConfig, ModelInputs
from lapa.data.collate import collate_slots
from lapa.programs.executor import execute


def canonical_examples():
    """First two records per protocol, in the canonical train-file order."""
    if (ROOT / 'data/gold/train.jsonl').exists():
        data = load_data('train', PROTOCOLS)
        origin = ROOT / 'data'
    else:
        origin = STUDY / 'baseline_extension_v7/data'
        clean = {r['message_id']: r for r in rows(origin / 'clean/train.jsonl')}
        data = [dict(r, data_hex=clean[r['message_id']]['data_hex'],
                     fields=sorted(r['fields'], key=lambda f: (f['start'], f['end'], f['semantic'])))
                for r in rows(origin / 'gold/train.jsonl')]
    chosen = []
    for protocol in PROTOCOLS:
        candidates = [r for r in data if r['protocol'] == protocol]
        assert len(candidates) >= 2
        chosen.extend(candidates[:2])
    return chosen, origin


def auxiliary(name):
    return name.startswith('host.router.') or name.startswith('presence.')


def assert_distribution(out, inputs):
    p = out['final']
    support = torch.cat((inputs.observed, torch.ones(len(p), 2, device=p.device, dtype=torch.bool)), -1)
    assert p.shape == support.shape
    assert torch.isfinite(p).all() and (p >= 0).all() and (p <= 1.000002).all()
    assert torch.allclose(p.sum(-1), torch.ones(len(p), device=p.device), atol=2e-6, rtol=2e-6)
    assert not p.masked_select(~support).any()
    if out['route'] is not None:
        route = out['route']
        assert torch.isfinite(route['prior']).all()
        assert not route['prior'].masked_select(~support).any()
        if 'source_marginal' in route:
            assert not route['joint'].masked_select(~route['execution'].valid).any()
            assert torch.allclose(route['joint'].sum((1, 2)), route['has_valid_pair'].to(p.dtype), atol=2e-6)


def oracle_check(model, examples, device):
    samples = [(r, slot) for r in examples for slot in range(len(r['fields']))]
    batch = collate_slots(samples, model.bank).to(device)
    execution = execute(model.bank, batch.inputs.data, batch.inputs.observed)
    index = torch.arange(len(samples), device=device)
    assert execution.valid[index, batch.labels.sources, batch.labels.programs].all()
    assert torch.equal(execution.target[index, batch.labels.sources, batch.labels.programs], batch.labels.targets)
    # Distinct special indices are storage-length based, not each row's length.
    length = batch.inputs.data.shape[1]
    special = {'END': 0, 'NULL': 0, 'INTERIOR': 0}
    for i, (record, slot) in enumerate(samples):
        field = record['fields'][slot]
        if field['target'] is None:
            assert batch.labels.targets[i].item() == length + 1
            special['NULL'] += 1
        elif field['target'] == record['byte_length']:
            assert batch.labels.targets[i].item() == length
            special['END'] += 1
        else:
            assert batch.labels.targets[i].item() == field['target']
            special['INTERIOR'] += 1
    return dict(fields=len(samples), target_kinds=special)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    parser.add_argument('--output', type=str)
    args = parser.parse_args()
    started = time.monotonic()
    torch.set_num_threads(2)
    if args.device == 'cuda':
        assert torch.cuda.is_available(), 'CUDA requested but unavailable; no silent fallback'
        torch._native.registry.deregister_op_overrides(disable_dsl_names='triton')
        torch.cuda.set_per_process_memory_fraction(.20)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    examples, origin = canonical_examples()
    seed = 160016
    torch.manual_seed(seed)
    reference = LapaModel(LapaConfig(attention='tape')).to(args.device)
    reference_state = {name: tensor.detach().cpu().clone() for name, tensor in reference.state_dict().items()}
    oracle = oracle_check(reference, examples, args.device)
    batches = list(sample_stream(examples, PROTOCOLS, seed + 1, 3))
    probe = collate_slots(batches[0], reference.bank).to(args.device)
    assert {f.name for f in dataclass_fields(ModelInputs)} == {'data', 'observed', 'slots'}
    assert set(vars(probe.inputs)) == {'data', 'observed', 'slots'}
    initial_direct = None
    results = []
    for variant in VARIANTS:
        torch.manual_seed(seed)
        model = FormulaModel(variant).to(args.device)
        state = model.state_dict()
        shared = sorted(set(state) & set(reference_state))
        assert shared
        for name in shared:
            assert torch.equal(state[name].detach().cpu(), reference_state[name]), (variant, name)
        if variant not in ('off', 'hybrid'):
            assert not any('retrieval_query' in n or 'retrieval_key' in n or 'special_endpoints' in n for n in state)
        if variant not in ('off', 'hybrid', 'route_sink'):
            assert not any('top_head' in n or 'wellformed_width_score' in n for n in state)
        if variant == 'cnn_joint':
            assert not any('.attention.' in n or '.query.' in n or '.key.' in n or '.value.' in n for n, _ in model.named_parameters())
        model.eval()
        with torch.no_grad():
            out = model(probe.inputs)
            assert_distribution(out, probe.inputs)
            if variant in ('off', 'hybrid'):
                torch.manual_seed(seed)
                legacy = LapaModel(LapaConfig(attention='tape', lapa_enabled=variant == 'hybrid')).to(args.device).eval()
                old = legacy(probe.inputs)
                for key in ('final', 'base', 'source', 'program', 'program_logits', 'presence_logits'):
                    assert torch.equal(out[key], old[key]), (variant, key)
                del legacy
            if variant == 'route_direct':
                initial_direct = out['final'].detach().clone()
            if variant == 'route_axis':
                assert torch.equal(out['final'], initial_direct)
            # Add storage padding only; every observed byte remains unchanged.
            old_length = probe.inputs.data.shape[1]
            added = 7
            padded = ModelInputs(F.pad(probe.inputs.data, (0, added), value=255),
                                 F.pad(probe.inputs.observed, (0, added), value=False), probe.inputs.slots)
            extended = model(padded)
            assert_distribution(extended, padded)
            aligned = torch.cat((extended['final'][:, :old_length], extended['final'][:, old_length + added:]), -1)
            assert torch.allclose(out['final'], aligned, atol=3e-6, rtol=3e-5), (variant, (out['final'] - aligned).abs().max().item())
            # Labels/metadata are not acceptable forward inputs, and mutating
            # separate supervision cannot alter a raw-only forward result.
            original_labels = probe.labels.targets.clone()
            probe.labels.targets.zero_()
            again = model(probe.inputs)
            probe.labels.targets.copy_(original_labels)
            assert torch.equal(out['final'], again['final'])
            for forbidden in (probe, probe.labels):
                try:
                    model(forbidden)
                except TypeError:
                    pass
                else:
                    raise AssertionError('forward accepted an object containing labels')
        optimizer = torch.optim.AdamW(model.parameters(), lr=.002, weight_decay=.01)
        losses = []
        model.train()
        initial_aux = {n: p.detach().clone() for n, p in model.named_parameters() if auxiliary(n)}
        for samples in batches:
            batch = collate_slots(samples, model.bank).to(args.device)
            optimizer.zero_grad(set_to_none=True)
            output = model(batch.inputs)
            assert_distribution(output, batch.inputs)
            loss, parts = formula_loss(model, output, batch.labels)
            assert torch.isfinite(loss)
            assert set(parts) == ({'endpoint'} if variant == 'off' else {'presence', 'source', 'program', 'endpoint'})
            loss.backward()
            for name, parameter in model.named_parameters():
                if parameter.grad is not None:
                    assert torch.isfinite(parameter.grad).all(), (variant, name)
                if variant == 'off' and auxiliary(name):
                    assert parameter.grad is None, name
            if variant != 'off':
                for prefix in ('presence.', 'host.router.source_score.', 'host.router.axis_heads.'):
                    assert any(p.grad is not None for n, p in model.named_parameters() if n.startswith(prefix)), (variant, prefix)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
            optimizer.step()
            losses.append(dict(total=float(loss.detach()), **{k: float(v.detach()) for k, v in parts.items()}))
        if variant == 'off':
            assert all(torch.equal(initial_aux[n], p) for n, p in model.named_parameters() if auxiliary(n))
        model.eval()
        with torch.no_grad():
            expected = model(probe.inputs)['final']
        # Exercise serialization and explicit experimental-class reconstruction
        # without creating or overwriting any training artifact.
        buffer = io.BytesIO()
        torch.save(dict(variant=variant, config=model.config.to_dict(), bank=model.bank.fingerprint,
                        state_dict=model.state_dict()), buffer)
        buffer.seek(0)
        payload = torch.load(buffer, map_location=args.device, weights_only=True)
        restored = FormulaModel(payload['variant'], backbone=payload['config']['attention']).to(args.device).eval()
        assert restored.config.to_dict() == payload['config'] and restored.bank.fingerprint == payload['bank']
        restored.load_state_dict(payload['state_dict'], strict=True)
        with torch.no_grad():
            actual = restored(probe.inputs)['final']
        assert torch.equal(expected, actual), variant
        results.append(dict(variant=variant, steps=3, parameters=sum(p.numel() for p in model.parameters()),
                            shared_initial_tensors=len(shared), loss_curve=losses, tests='PASS'))
        del model, restored, optimizer
    result = dict(status='PASS', time=now(), device=args.device, seconds=time.monotonic() - started,
                  train_data_origin=str(origin), examples=[r['message_id'] for r in examples],
                  protocols=list(PROTOCOLS), evaluation_data_read=False, synthetic_packets=False,
                  oracle=oracle, variants=results,
                  checks=['legacy_exact_parity', 'shared_initial_state', 'loss_sets_and_gradients',
                          'removed_retrieval_modules', 'cnn_no_qkv', 'probability_normalization',
                          'padding_and_special_endpoint_remap', 'raw_only_forward',
                          'oracle_executor_known_training_fields', 'direct_axis_forward_parity',
                          'checkpoint_variant_roundtrip'])
    if args.output:
        destination = Path(args.output) if Path(args.output).is_absolute() else ROOT / args.output
        write(destination, result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
