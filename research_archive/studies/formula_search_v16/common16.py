"""Isolated formula-search experiment; never edits packaged LAPA or old results."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parent
WORKSPACE = next(p for p in ROOT.parents if (p/'lapa-attention/src/lapa').is_dir())
sys.path.insert(0, str(WORKSPACE/'lapa-attention/src'))
PROTOCOLS = ('dns', 'modbus', 'tls', 'smb2')
VARIANTS = ('hybrid', 'route_sink', 'route_direct', 'route_axis', 'route_joint', 'cnn_joint')
SEARCH_SEEDS = (160101, 160102)
FINAL_SEEDS = (160201, 160202, 160203)
SEARCH_STEPS, FINAL_STEPS, DEV_LIMIT = 250, 600, 32
PAIRS = tuple(itertools.combinations(PROTOCOLS, 2))

def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def rows(p): return [json.loads(line) for line in Path(p).read_text().splitlines() if line]
def write(p, value, replace=False):
    p = Path(p).resolve()
    assert ROOT in p.parents and (replace or not p.exists()), p
    p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_name(p.name+'.tmp')
    with temp.open('w') as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')
    temp.replace(p)

def write_rows(p, values):
    p = Path(p).resolve()
    assert ROOT in p.parents and not p.exists(), p
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f:
        for r in values: f.write(json.dumps(r, sort_keys=True, allow_nan=False)+'\n')

def load_data(split, protocols, clean=False, limited=False):
    kind = 'clean' if clean else 'gold'
    records = rows(ROOT/f'data/{kind}/{split}.jsonl')
    contract = read(ROOT/'DATA_CONTRACT.json')
    allowed = {mid for p in protocols for mid in contract['protocol_ids'][split][p]}
    if limited:
        allowed &= {mid for p in protocols for mid in contract['development_ids'][p]}
    records = [r for r in records if r['message_id'] in allowed]
    if not clean:
        raw = {r['message_id']:r for r in rows(ROOT/f'data/clean/{split}.jsonl')}
        records = [dict(r, data_hex=raw[r['message_id']]['data_hex'],
                        fields=sorted(r['fields'], key=lambda f:(f['start'],f['end'],f['semantic']))) for r in records]
    return records

def sample_stream(data, protocols, seed, steps):
    rng = random.Random(seed)
    groups = {p:[r for r in data if r['protocol']==p] for p in protocols}
    assert all(groups.values())
    for _ in range(steps):
        batch=[]
        for j in range(16):
            r=rng.choice(groups[rng.choice(protocols)])
            n=len(r['fields']); slot=rng.randrange(n) if j<8 else rng.randrange(n,64)
            batch.append((r,slot))
        rng.shuffle(batch)
        yield batch

def metric(records):
    assert records
    strata=defaultdict(list)
    for r in records: strata[(r['relation'],r['target_kind'])].append(r)
    return dict(n_fields=len(records), p_true=statistics.mean(r['p_true'] for r in records),
        hit1=statistics.mean(r['hit1'] for r in records), nll=statistics.mean(r['nll'] for r in records),
        balanced_log_gain=statistics.mean(statistics.mean(math.log(r['byte_length']+2)-r['nll'] for r in group) for group in strata.values()),
        strata={rel+'|'+kind:dict(n=len(group), p_true=statistics.mean(r['p_true'] for r in group),
             log_gain=statistics.mean(math.log(r['byte_length']+2)-r['nll'] for r in group)) for (rel,kind),group in strata.items()})

def verify_contract():
    contract=read(ROOT/'CODE_CONTRACT.json')
    for name,digest in contract['files'].items(): assert sha(name)==digest, name
    data=read(ROOT/'DATA_CONTRACT.json')
    for name,digest in data['files'].items(): assert sha(ROOT/name)==digest, name

def log(event, **data):
    with (ROOT/'EVENTS.jsonl').open('a') as f: f.write(json.dumps(dict(time=now(),event=event,**data),sort_keys=True)+'\n')

def verify_selection():
    selection=read(ROOT/'SELECTION.json')
    assert selection['code_contract_sha256']==sha(ROOT/'CODE_CONTRACT.json')
    assert selection['plan_sha256']==sha(ROOT/'PLAN.md')
    for target,choice in selection['choices'].items():
        assert target not in choice['sources']
        assert choice['selected']==choice['ranked'][0]['variant']
        for row in choice['ranked']:
            for evidence in row['evidence']:
                assert target not in evidence['pair'] and evidence['validation']!=target
                assert sha(evidence['path'])==evidence['sha256']
    return selection
