"""Isolated v18 IO and matched historical real-capture sampling."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
V17 = ROOT.parent/'formula_search_v17'
WORKSPACE = next(p for p in ROOT.parents if (p/'lapa-attention/src/lapa').is_dir())
sys.path.insert(0, str(V17))
sys.path.insert(0, str(WORKSPACE/'lapa-attention/src'))
import common17 as previous
import torch
from lapa.data.collate import collate_slots
from lapa.programs.bank import native_bank

PROTOCOLS = ('dns', 'modbus', 'tls', 'smb2')
SEEDS = (170301, 170302, 170303)
MODES = ('direct', 'sink')
STEPS = 600
load_data, sample_stream = previous.load_data, previous.sample_stream


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value, replace=False):
    path = Path(path).resolve()
    assert ROOT in path.parents and (replace or not path.exists()), path
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')
    temp.replace(path)


def collate(samples, device='cpu'):
    from executor18 import FourFactorExecutor
    bank = native_bank()
    batch = collate_slots(samples, bank).to(device)
    axes = [FourFactorExecutor.native_to_axes(int(p), bank) if present else (0,0,0)
            for p,present in zip(batch.labels.programs.cpu(),batch.labels.present.cpu())]
    labels = dict(present=batch.labels.present, source=batch.labels.sources, target=batch.labels.targets)
    for i, name in enumerate(('width','endian','base')):
        labels[name] = torch.tensor([a[i] for a in axes], dtype=torch.long, device=device)
    return batch.inputs, labels


def verify_contract():
    previous.verify_contract()
    contract = read(ROOT/'CONTRACT.json')
    for path, expected in contract['files'].items():
        assert sha(path) == expected, path
    assert sha(V17/'DATA_CONTRACT.json') == contract['data_contract_sha256']


def jobs():
    return [dict(target=p, sources=[s for s in PROTOCOLS if s != p], mode=m, seed=seed)
            for p in PROTOCOLS for m in MODES for seed in SEEDS]


def folder(job):
    return ROOT/'runs'/job['target']/f"{job['mode']}__{job['seed']}"
