"""Fixed-budget four-factor training; target inference is sealed before score."""
import argparse
from collections import Counter
import hashlib
import json
import random
import time

import numpy as np
import torch
from common18 import ROOT,V17,PROTOCOLS,SEEDS,MODES,STEPS,load_data,sample_stream,collate,now,sha,read,write,verify_contract,jobs,folder,previous
from model18 import FourFactorModel
from losses18 import loss
from evaluate18 import infer,score


def state_hash(model):
    digest = hashlib.sha256()
    for name,value in sorted(model.state_dict().items()):
        v = value.detach().cpu().contiguous()
        digest.update(name.encode()); digest.update(str(tuple(v.shape)).encode())
        digest.update(str(v.dtype).encode()); digest.update(v.numpy().tobytes())
    return digest.hexdigest()


def run(job):
    verify_contract()
    assert job in jobs()
    path = folder(job)
    assert not path.exists(), 'Preserve existing or partial runs; do not silently retry'
    assert torch.cuda.is_available(), 'CUDA required; no silent device/budget fallback'
    from torch._native.registry import deregister_op_overrides
    deregister_op_overrides(disable_dsl_names='triton')
    torch.set_num_threads(2)
    torch.cuda.set_per_process_memory_fraction(.35)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    random.seed(job['seed']); np.random.seed(job['seed']); torch.manual_seed(job['seed'])
    model = FourFactorModel(mode=job['mode']).cuda()
    initial = state_hash(model)
    path.mkdir(parents=True)
    data = load_data('train',job['sources'])
    optimizer = torch.optim.AdamW(model.parameters(),lr=.002,weight_decay=.01)
    stream = hashlib.sha256()
    counts,active,curve = Counter(),set(),[]
    started = time.monotonic()
    model.train()
    for step,samples in enumerate(sample_stream(data,job['sources'],job['seed'],STEPS),1):
        stream.update(json.dumps([(r['message_id'],slot) for r,slot in samples]).encode())
        counts.update(r['protocol'] for r,slot in samples)
        inputs,labels = collate(samples,'cuda')
        optimizer.zero_grad(set_to_none=True)
        output = model(inputs,diagnostics=False)
        total,parts = loss(output,labels)
        assert torch.isfinite(total) and set(parts)=={'presence','source','attributes','endpoint'}
        total.backward()
        active.update(n for n,p in model.named_parameters() if p.grad is not None)
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
        optimizer.step()
        curve.append(dict(step=step,loss=float(total.detach()),grad_norm=float(norm),
                          **{k:float(v.detach()) for k,v in parts.items()}))
        if step==1 or step%100==0:
            progress = dict(time=now(),**job,stage='TRAINING',step=step,steps=STEPS,seconds=time.monotonic()-started)
            write(path/'PROGRESS.json',progress,replace=True)
            print(json.dumps(progress),flush=True)
    # Prior controls are reusable only after exact source/seed/sample matching.
    controls = []
    for backbone in ('rope','cope','tape','sdpa'):
        for variant in ('off','hybrid'):
            control = V17/'final'/job['target']/f'{backbone}__{variant}__{job["seed"]}'
            control_complete = previous.verify_run(control)
            expected_control = dict(phase='final', target=job['target'], backbone=backbone,
                                    variant=variant, seed=job['seed'], sources=job['sources'])
            assert all(control_complete[k] == v for k,v in expected_control.items()), control
            meta = read(control/'TRAINING.json')
            assert all(meta[k] == v for k,v in expected_control.items()), control
            assert meta['steps']==STEPS and meta['sources']==job['sources']
            assert meta['seed']==job['seed'] and meta['stream_sha256']==stream.hexdigest()
            controls.append(dict(path=str(control),training_sha256=sha(control/'TRAINING.json'),
                                 complete_sha256=sha(control/'COMPLETE.json'),
                                 complete_artifact_hashes_verified=len(control_complete['files'])))
    metadata = dict(time=now(),**job,steps=STEPS,config=model.config,
        initial_sha256=initial,final_sha256=state_hash(model),stream_sha256=stream.hexdigest(),
        source_sample_counts=dict(counts),parameters=sum(p.numel() for p in model.parameters()),
        active_parameters=sorted(active),loss_weights={k:1. for k in parts},
        attribute_objective='sum of width/endian/base NLL at true training source; width1 endian marginalized',
        no_qk=True,learned_factors=['source','width','endian','base'],learned_value_retained=True,
        source_gold_input=False,protocol_input=False,target_protocol_training=False,
        executor_fingerprint=model.executor.fingerprint,contract_sha256=sha(ROOT/'CONTRACT.json'),
        controls=controls,training_seconds=time.monotonic()-started,torch_version=str(torch.__version__),
        device='cuda',cpu_threads=2,tf32=False,optimizer=dict(name='AdamW',lr=.002,weight_decay=.01,clip=1.))
    torch.save(dict(schema='four-factor-attention-v18',config=model.config,state_dict=model.state_dict(),metadata=metadata),path/'model.pt')
    write(path/'TRAINING.json',metadata)
    write(path/'curve.json',curve)
    write(path/'PROGRESS.json',dict(time=now(),**job,stage='TARGET_INFERENCE'),replace=True)
    model.eval()
    infer(model,load_data('evaluation',[job['target']],clean=True),path/'evaluation','cuda')
    score(path/'evaluation',load_data('evaluation',[job['target']]))
    verify_contract()
    complete = dict(time=now(),**job,steps=STEPS,seconds=time.monotonic()-started,
        contract_sha256=sha(ROOT/'CONTRACT.json'),
        files={str(p.relative_to(path)):sha(p) for p in sorted(path.rglob('*')) if p.is_file() and p.name!='PROGRESS.json'})
    write(path/'COMPLETE.json',complete)
    write(path/'PROGRESS.json',dict(time=now(),**job,stage='COMPLETE'),replace=True)
    print(json.dumps(dict(status='COMPLETE',**job,seconds=complete['seconds'])),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--target',choices=PROTOCOLS,required=True)
    parser.add_argument('--mode',choices=MODES,required=True)
    parser.add_argument('--seed',type=int,choices=SEEDS,required=True)
    args=parser.parse_args()
    run(dict(target=args.target,mode=args.mode,seed=args.seed,sources=[p for p in PROTOCOLS if p!=args.target]))
