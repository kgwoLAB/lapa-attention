"""Fixed-budget v17 training with source-only selection and sealed inference.

Only jobs enumerated by the frozen common17 phase schedule may run.  Loss
components returned by losses17 are already weighted; their sum is checked
against the differentiated total.  Completed output hashes are immutable.
"""
import argparse
import time

from common17 import *
import numpy as np
import torch
from lapa.data.collate import collate_slots
from models17 import SearchModel
from losses17 import loss as formula_loss


# Off may update only the established endpoint path, never newly introduced
# routing, attribute, mixture, or presence modules.  This is intentionally an
# allow-list, not merely a test for the two old auxiliary-head prefixes.
OFF_ENDPOINT_PREFIXES = (
    'host.byte_embedding.', 'host.query_id_embedding.', 'host.version_embedding.',
    'host.embedding_norm.', 'host.blocks.', 'host.readout.', 'host.cope.',
    'host.retrieval_query.', 'host.retrieval_key.', 'special_endpoints.',
)


def is_auxiliary(name):
    return name != 'host.task_query' and not name.startswith(OFF_ENDPOINT_PREFIXES)


def tensor_hash(value):
    value = value.detach().cpu().contiguous()
    digest = hashlib.sha256()
    digest.update(str(value.dtype).encode())
    digest.update(str(tuple(value.shape)).encode())
    digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def state_hash(model, auxiliary=False):
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        if auxiliary and not is_auxiliary(name):
            continue
        digest.update(name.encode())
        digest.update(tensor_hash(value).encode())
    return digest.hexdigest()


def initialize(variant, backbone, seed, device='cuda'):
    torch.set_num_threads(2)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if device == 'cuda':
        assert torch.cuda.is_available(), 'GPU required; never silently change device or budget'
        from torch._native.registry import deregister_op_overrides
        deregister_op_overrides(disable_dsl_names='triton')
        torch.cuda.set_per_process_memory_fraction(.20)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
    # "none" is the schedule's explicit no-backbone label, not a fifth
    # attention mechanism. SearchModel owns canonical construction internally.
    return SearchModel(variant, backbone).to(device)


def _verify_job(phase, variant, backbone, seed, sources, target):
    assert phase in STEPS
    assert sources == [p for p in PROTOCOLS if p in sources]
    assert backbone == canonical_backbone(variant, backbone)
    if phase == 'refine':
        verify_choice_file('PROMOTION.json')
    if phase == 'final':
        verify_choice_file('SELECTION.json')
    job = dict(phase=phase, variant=variant, backbone=backbone, seed=seed,
               sources=list(sources), target=target)
    assert job in phase_jobs(phase), ('job is not in frozen phase schedule', job)
    assert target is None if phase != 'final' else target not in sources
    return job


def run(phase, variant, backbone, seed, sources, target=None):
    verify_contract()
    job = _verify_job(phase, variant, backbone, seed, sources, target)
    folder = job_folder(job)
    assert not folder.exists(), ('preserve existing or partial run; queue must verify completed runs', str(folder))
    steps = STEPS[phase]
    data = load_data('train', sources)
    assert {r['protocol'] for r in data} == set(sources)
    model = initialize(variant, backbone, seed)
    folder.mkdir(parents=True, exist_ok=False)
    initial = state_hash(model)
    auxiliary_initial = state_hash(model, True)
    initial_tensors = {name: tensor_hash(value) for name, value in sorted(model.state_dict().items())}
    optimizer = torch.optim.AdamW(model.parameters(), lr=.002, weight_decay=.01)
    stream = hashlib.sha256()
    exposure, active, curve = Counter(), set(), []
    started = time.monotonic()
    model.train()
    for step, samples in enumerate(sample_stream(data, sources, seed, steps), 1):
        stream.update(json.dumps([(row['message_id'], slot) for row, slot in samples]).encode())
        exposure.update(row['protocol'] for row, slot in samples)
        batch = collate_slots(samples, model.bank).to('cuda')
        optimizer.zero_grad(set_to_none=True)
        output = model(batch.inputs)
        total, parts = formula_loss(model, output, batch.labels)
        assert torch.isfinite(total), (job, step, 'non-finite loss')
        expected = {'endpoint'} if variant == 'off' else {'presence', 'source', 'program', 'endpoint'}
        assert set(parts) == expected, (variant, set(parts), expected)
        assert all(torch.isfinite(value) for value in parts.values()), (job, step)
        torch.testing.assert_close(total.detach(), sum(parts.values()).detach(), rtol=1e-5, atol=1e-6)
        total.backward()
        active.update(name for name, parameter in model.named_parameters() if parameter.grad is not None)
        if variant == 'off':
            assert all(parameter.grad is None for name, parameter in model.named_parameters() if is_auxiliary(name)), (
                'Off auxiliary gradient', [name for name, p in model.named_parameters() if is_auxiliary(name) and p.grad is not None])
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
        optimizer.step()
        curve.append(dict(step=step, loss=float(total.detach()), grad_norm=float(norm),
                          **{key: float(value.detach()) for key, value in parts.items()}))
        if step == 1 or step % 100 == 0 or step == steps:
            progress = dict(time=now(), **job, stage='TRAINING', step=step, steps=steps,
                            seconds=time.monotonic() - started)
            write(folder/'PROGRESS.json', progress, replace=True)
            print(json.dumps(progress), flush=True)

    auxiliary_final = state_hash(model, True)
    assert variant != 'off' or auxiliary_initial == auxiliary_final
    active_count = sum(p.numel() for name, p in model.named_parameters() if name in active)
    loss_weights = {key: float(value) for key, value in model.loss_weights.items()}
    assert all(math.isfinite(value) and value >= 0 for value in loss_weights.values())
    meta = dict(
        time=now(), **job, steps=steps, initial_sha256=initial, final_sha256=state_hash(model),
        initial_tensor_sha256=initial_tensors, stream_sha256=stream.hexdigest(),
        initial_auxiliary_sha256=auxiliary_initial, final_auxiliary_sha256=auxiliary_final,
        auxiliary_unchanged=auxiliary_initial == auxiliary_final, source_sample_counts=dict(exposure),
        parameters=sum(p.numel() for p in model.parameters()), gradient_active_parameters=active_count,
        active_parameter_names=sorted(active), loss_keys=list(parts), loss_weights=loss_weights,
        curve_components='already weighted; each step components sum to differentiated total',
        encoder_kind=output.get('encoder_kind'), base_kind=output.get('base_kind'),
        base_available=bool(output.get('base_available', True)),
        encoder_qkv=variant not in NO_BACKBONE, seconds_training=time.monotonic() - started,
        target_protocol_training=False, pretrained_checkpoint_used=False, torch=str(torch.__version__),
        device='cuda', cuda_memory_fraction=.20, cpu_threads=2, tf32=False,
        optimizer=dict(name='AdamW', learning_rate=.002, weight_decay=.01, gradient_clip_norm=1.),
        checkpoint_rule='fixed final step; no target-dependent checkpoint selection',
        bank_fingerprint=model.bank.fingerprint,
        code_contract_sha256=sha(ROOT/'CODE_CONTRACT.json'),
        data_contract_sha256=sha(ROOT/'DATA_CONTRACT.json'),
        promotion_sha256=sha(ROOT/'PROMOTION.json') if phase in ('refine', 'final') else None,
        selection_sha256=sha(ROOT/'SELECTION.json') if phase == 'final' else None,
    )
    if hasattr(model.host, 'parameter_counts'):
        meta['encoder_parameter_counts'] = model.host.parameter_counts()
    torch.save(dict(schema='lapa-formula-search-v17', variant=variant, backbone=backbone,
                    bank_fingerprint=model.bank.fingerprint,
                    state_dict={key: value.detach().cpu() for key, value in model.state_dict().items()},
                    config=model.config.to_dict(), metadata=meta), folder/'model.pt')
    write(folder/'TRAINING.json', meta)
    write(folder/'curve.json', curve)

    if phase in ('screen', 'refine'):
        # Both excluded protocols are scored for reuse by different outer
        # folds. Selection must discard all evidence involving its outer target.
        for validation in PROTOCOLS:
            if validation in sources:
                continue
            validation_folder = folder/'validation'/validation
            write(folder/'PROGRESS.json', dict(time=now(), **job, stage='INNER_VALIDATION', protocol=validation), replace=True)
            ev.infer(model, load_data('development', [validation], clean=True, limited=True), validation_folder, 'cuda')
            ev.score(validation_folder, load_data('development', [validation], limited=True))
    else:
        threshold = .5
        if variant != 'off':
            write(folder/'PROGRESS.json', dict(time=now(), **job, stage='SOURCE_THRESHOLD'), replace=True)
            candidates = ev.infer(model, load_data('development', sources, clean=True, limited=True), folder/'development', 'cuda')
            source_gold = load_data('development', sources, limited=True)
            choice = ev.choose_threshold(candidates, source_gold, sources)
            threshold = choice['threshold']
            write(folder/'THRESHOLD.json', choice)
        write(folder/'PROGRESS.json', dict(time=now(), **job, stage='TARGET_INFERENCE'), replace=True)
        candidates = ev.infer(model, load_data('evaluation', [target], clean=True), folder/'evaluation', 'cuda')
        # Gold is accessed only after raw-only predictions have been sealed.
        gold = load_data('evaluation', [target])
        ev.score(folder/'evaluation', gold)
        stage = ev.diagnose(model, gold, 'cuda')
        write_rows(folder/'STAGES.jsonl', stage)
        predictions = ev.selected(candidates, threshold) if variant != 'off' else None
        if predictions is not None:
            write_rows(folder/'FIELDS.jsonl', predictions)
        write(folder/'FIELD_METRICS.json', dict(
            threshold=threshold,
            all=ev.field_f1(gold, predictions) if predictions is not None else None,
            by_semantic={semantic: ev.field_f1(gold, predictions, semantic=semantic)
                         for semantic in ('LENGTH', 'OFFSET', 'POINTER')} if predictions is not None else None,
            off_field_head_untrained=variant == 'off',
        ))
    # Do not seal outputs if code or input manifests changed during execution.
    verify_contract()
    complete = dict(time=now(), **job, steps=steps, seconds=time.monotonic() - started,
                    code_contract_sha256=sha(ROOT/'CODE_CONTRACT.json'),
                    files={str(path.relative_to(folder)): sha(path) for path in sorted(folder.rglob('*'))
                           if path.is_file() and path.name not in ('PROGRESS.json', 'COMPLETE.json')})
    write(folder/'COMPLETE.json', complete)
    verify_run(folder)
    write(folder/'PROGRESS.json', dict(time=now(), **job, stage='COMPLETE', seconds=complete['seconds']), replace=True)
    print(json.dumps(dict(status='COMPLETE', **job, seconds=complete['seconds'])), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=tuple(STEPS), required=True)
    parser.add_argument('--variant', choices=('off',) + VARIANTS, required=True)
    parser.add_argument('--backbone', choices=BACKBONES + ('none',), required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--sources', nargs='+', choices=PROTOCOLS, required=True)
    parser.add_argument('--target', choices=PROTOCOLS)
    args = parser.parse_args()
    run(args.phase, args.variant, args.backbone, args.seed, args.sources, args.target)
