"""Broad, precommitted real-protocol formula exploration; isolated from v16."""
from collections import Counter, defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import statistics
import sys

ROOT=Path(__file__).resolve().parent
STUDY=ROOT.parent
V16=STUDY/'formula_search_v16'
WORKSPACE=next(p for p in ROOT.parents if (p/'lapa-attention/src/lapa').is_dir())
sys.path.insert(0,str(V16));sys.path.insert(0,str(ROOT));sys.path.insert(0,str(WORKSPACE/'lapa-attention/src'))
import common16 as compat
compat.ROOT=ROOT  # In-memory IO routing only. No historical source/result edits.
now,sha,read,rows,write,write_rows,log=(getattr(compat,n) for n in ('now','sha','read','rows','write','write_rows','log'))
PROTOCOLS=('dns','modbus','tls','smb2')
BACKBONES=('rope','cope','tape','sdpa')
PAIRS=tuple(itertools.combinations(PROTOCOLS,2))
VARIANTS=('hybrid','route_sink','route_direct','route_joint','axis_direct',
    'attr_only','attr_content','attr_distance','attr_product','attr_mix',
    'mix_half','mix_learned','mix_entropy','power_learned','weak_product','stopgrad_product',
    'smooth_route','soft_joint','valid_mass_route','cnn_shared_route','cnn_shared_attr',
    'gru_shared_route','gru_shared_attr','shared_slot_hybrid','aux_small','aux_large',
    'bilinear_program','shared_slot_route','execute_score','equivalent_program')
NO_BACKBONE=('cnn_shared_route','cnn_shared_attr','gru_shared_route','gru_shared_attr')
ATTRIBUTE_VARIANTS=tuple(v for v in VARIANTS if v.startswith('attr_') or v.endswith('_attr'))
SCREEN_SEEDS=(170101,)
REFINE_SEEDS=(170201,170202)
FINAL_SEEDS=(170301,170302,170303)
STEPS={'screen':120,'refine':400,'final':600}
DEV_LIMIT=24

_original_metric=compat.metric
def metric(records):
    result=_original_metric(records);strata=defaultdict(list)
    for r in records:strata[(r['relation'],r['target_kind'])].append(r['p_true'])
    result['balanced_p']=statistics.mean(statistics.mean(v) for v in strata.values())
    return result
compat.metric=metric
load_data=compat.load_data
sample_stream=compat.sample_stream
import evaluate16 as ev

def canonical_backbone(variant,backbone):return 'none' if variant in NO_BACKBONE else backbone
def verify_contract():
    for filename,digest in read(ROOT/'CODE_CONTRACT.json')['files'].items():assert sha(filename)==digest,filename
    for filename,digest in read(ROOT/'DATA_CONTRACT.json')['files'].items():assert sha(ROOT/filename)==digest,filename

def verify_run(folder):
    c=read(folder/'COMPLETE.json')
    assert c['code_contract_sha256']==sha(ROOT/'CODE_CONTRACT.json')
    for name,digest in c['files'].items():assert sha(folder/name)==digest,(folder,name)
    return c

def job_folder(j):
    group=j['target'] if j['phase']=='final' else '_'.join(j['sources'])
    return ROOT/j['phase']/group/f"{j['backbone']}__{j['variant']}__{j['seed']}"

def phase_jobs(phase):
    jobs=[]
    def add(sources,variant,seed,backbone='tape',target=None):
        j=dict(phase=phase,sources=list(sources),variant=variant,seed=seed,
            backbone=canonical_backbone(variant,backbone),target=target)
        if j not in jobs:jobs.append(j)
    if phase=='screen':
        for pair in PAIRS:
            for variant in VARIANTS:
                for seed in SCREEN_SEEDS:add(pair,variant,seed)
    elif phase=='refine':
        for target,choice in read(ROOT/'PROMOTION.json')['choices'].items():
            for pair in itertools.combinations(choice['sources'],2):
                for variant in choice['promoted']:
                    for seed in REFINE_SEEDS:add(pair,variant,seed)
    else:
        assert phase=='final'
        for target,choice in read(ROOT/'SELECTION.json')['choices'].items():
            for backbone in BACKBONES:
                for variant in dict.fromkeys(('off','hybrid',choice['p_champion'],choice['nll_champion'])):
                    for seed in FINAL_SEEDS:add(choice['sources'],variant,seed,backbone,target)
    return jobs

def verify_choice_file(name):
    value=read(ROOT/name)
    assert value['code_contract_sha256']==sha(ROOT/'CODE_CONTRACT.json')
    assert value['plan_sha256']==sha(ROOT/'PLAN.md')
    for target,choice in value['choices'].items():
        assert choice['sources']==[p for p in PROTOCOLS if p!=target]
        for item in choice['candidates']:
            for e in item['evidence']:
                assert target not in e['sources'] and target!=e['validation']
                assert sha(e['path'])==e['sha256']
    return value
