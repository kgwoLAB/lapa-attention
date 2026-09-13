"""Fixed-budget formula training. Search and final are separate sealed phases."""
import argparse
import time
from common16 import *
import numpy as np
import torch
from lapa.data.collate import collate_slots
from models16 import FormulaModel
from losses16 import formula_loss
import evaluate16 as ev

def state_hash(model, auxiliary=False):
    digest=hashlib.sha256()
    for name,value in sorted(model.state_dict().items()):
        if auxiliary and not (name.startswith('host.router.') or name.startswith('presence.')): continue
        digest.update(name.encode());digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()

def initialize(variant,seed,device='cuda'):
    torch.set_num_threads(2)
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    if device=='cuda':
        assert torch.cuda.is_available(), 'GPU required: never silently switch device/budget'
        from torch._native.registry import deregister_op_overrides
        deregister_op_overrides(disable_dsl_names='triton')
        torch.cuda.set_per_process_memory_fraction(.18)
        torch.backends.cuda.matmul.allow_tf32=False
        torch.backends.cudnn.allow_tf32=False
    return FormulaModel(variant).to(device)

def run(phase,variant,seed,sources,target=None):
    verify_contract()
    assert sources==[p for p in PROTOCOLS if p in sources]
    if phase=='search':
        assert len(sources)==2 and seed in SEARCH_SEEDS and variant in VARIANTS and target is None
        steps=SEARCH_STEPS; folder=ROOT/'search'/('_'.join(sources))/f'{variant}_{seed}'
    else:
        assert phase=='final' and len(sources)==3 and target not in sources and seed in FINAL_SEEDS
        selection=verify_selection(); choice=selection['choices'][target]
        assert sources==choice['sources'] and variant in {'off','hybrid',choice['selected']}
        steps=FINAL_STEPS;folder=ROOT/'final'/target/f'{variant}_{seed}'
    folder.mkdir(parents=True,exist_ok=False)
    model=initialize(variant,seed);data=load_data('train',sources)
    assert {r['protocol'] for r in data}==set(sources)
    initial=state_hash(model); aux=state_hash(model,True)
    optimizer=torch.optim.AdamW(model.parameters(),lr=.002,weight_decay=.01)
    stream=hashlib.sha256();exposure=Counter();curve=[];started=time.monotonic()
    model.train()
    active=set()
    for step,samples in enumerate(sample_stream(data,sources,seed,steps),1):
        stream.update(json.dumps([(r['message_id'],slot) for r,slot in samples]).encode())
        exposure.update(r['protocol'] for r,slot in samples)
        batch=collate_slots(samples,model.bank).to('cuda')
        optimizer.zero_grad(set_to_none=True)
        output=model(batch.inputs);loss,parts=formula_loss(model,output,batch.labels)
        assert torch.isfinite(loss);loss.backward()
        active.update(name for name,p in model.named_parameters() if p.grad is not None)
        if variant=='off':
            assert set(parts)=={'endpoint'}
            assert all(p.grad is None for name,p in model.named_parameters() if name.startswith(('host.router.','presence.')))
        else: assert set(parts)=={'presence','source','program','endpoint'}
        norm=torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
        optimizer.step()
        curve.append(dict(step=step,loss=float(loss.detach()),grad_norm=float(norm),**{k:float(v.detach()) for k,v in parts.items()}))
        if step==1 or step%100==0 or step==steps:
            progress=dict(time=now(),phase=phase,variant=variant,sources=sources,target=target,seed=seed,
                stage='TRAINING',step=step,steps=steps,seconds=time.monotonic()-started)
            write(folder/'PROGRESS.json',progress,replace=True);print(json.dumps(progress),flush=True)
    aux_final=state_hash(model,True)
    assert variant!='off' or aux==aux_final
    meta=dict(time=now(),phase=phase,variant=variant,sources=sources,target=target,seed=seed,steps=steps,
        initial_sha256=initial,final_sha256=state_hash(model),stream_sha256=stream.hexdigest(),
        auxiliary_unchanged=aux==aux_final,source_sample_counts=dict(exposure),parameters=sum(p.numel() for p in model.parameters()),
        gradient_active_parameters=sum(p.numel() for name,p in model.named_parameters() if name in active),
        active_parameter_names=sorted(active),loss_keys=list(parts),program_loss='mean_five_axis_ce' if variant in ('route_axis','route_joint','cnn_joint') else 'valid_bank_ce' if variant!='off' else None,
        endpoint_qk=variant in ('off','hybrid'),encoder_qkv=variant!='cnn_joint',seconds_training=time.monotonic()-started,
        target_protocol_training=False,pretrained_checkpoint_used=False,torch=str(torch.__version__),
        bank_fingerprint=model.bank.fingerprint,code_contract_sha256=sha(ROOT/'CODE_CONTRACT.json'),data_contract_sha256=sha(ROOT/'DATA_CONTRACT.json'),
        selection_sha256=sha(ROOT/'SELECTION.json') if phase=='final' else None)
    torch.save(dict(schema='lapa-formula-search-v16',variant=variant,backbone='tape',bank_fingerprint=model.bank.fingerprint,
        state_dict={k:v.detach().cpu() for k,v in model.state_dict().items()},metadata=meta),folder/'model.pt')
    write(folder/'TRAINING.json',meta);write(folder/'curve.json',curve)
    if phase=='search':
        for validation in PROTOCOLS:
            if validation in sources: continue
            vf=folder/'validation'/validation
            write(folder/'PROGRESS.json',dict(time=now(),stage='INNER_VALIDATION',protocol=validation),replace=True)
            ev.infer(model,load_data('development',[validation],clean=True,limited=True),vf,'cuda')
            ev.score(vf,load_data('development',[validation],limited=True))
    else:
        cutoff=.5
        if variant!='off':
            write(folder/'PROGRESS.json',dict(time=now(),stage='SOURCE_THRESHOLD'),replace=True)
            candidates=ev.infer(model,load_data('development',sources,clean=True,limited=True),folder/'development','cuda')
            gold=load_data('development',sources,limited=True)
            choice=ev.choose_threshold(candidates,gold,sources);cutoff=choice['threshold']
            write(folder/'THRESHOLD.json',choice)
        write(folder/'PROGRESS.json',dict(time=now(),stage='TARGET_INFERENCE'),replace=True)
        candidates=ev.infer(model,load_data('evaluation',[target],clean=True),folder/'evaluation','cuda')
        gold=load_data('evaluation',[target])
        records=ev.score(folder/'evaluation',gold)
        # Ground-truth indices are used only after the output seal, for diagnostics.
        stage=ev.diagnose(model,gold,'cuda');write_rows(folder/'STAGES.jsonl',stage)
        pred=ev.selected(candidates,cutoff) if variant!='off' else None
        if pred is not None: write_rows(folder/'FIELDS.jsonl',pred)
        write(folder/'FIELD_METRICS.json',dict(threshold=cutoff,all=ev.field_f1(gold,pred) if pred is not None else None,
            by_semantic={sem:ev.field_f1(gold,pred,semantic=sem) for sem in ('LENGTH','OFFSET','POINTER')} if pred is not None else None,
            off_field_head_untrained=variant=='off'))
    complete=dict(time=now(),phase=phase,variant=variant,sources=sources,target=target,seed=seed,steps=steps,
        seconds=time.monotonic()-started,code_contract_sha256=sha(ROOT/'CODE_CONTRACT.json'),
        files={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file() and p.name!='PROGRESS.json'})
    write(folder/'COMPLETE.json',complete)
    write(folder/'PROGRESS.json',dict(time=now(),stage='COMPLETE',seconds=complete['seconds']),replace=True)
    print(json.dumps(dict(status='COMPLETE',phase=phase,variant=variant,sources=sources,target=target,seed=seed,seconds=complete['seconds'])),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('search','final'),required=True)
    ap.add_argument('--variant',choices=('off',)+VARIANTS,required=True);ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--sources',nargs='+',choices=PROTOCOLS,required=True);ap.add_argument('--target',choices=PROTOCOLS)
    a=ap.parse_args();run(a.phase,a.variant,a.seed,a.sources,a.target)
