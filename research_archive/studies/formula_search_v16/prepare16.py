"""Freeze only existing real-capture data; do not generate packets."""
from common16 import *

def main():
    historical=read(STUDY/'three_to_one_v15/DATA_CONTRACT.json')
    files={}; counts={}; dev={}; protocol_ids={}
    for split in ('train','development','evaluation'):
        collections={}
        for kind in ('clean','gold'):
            path=STUDY/f'baseline_extension_v7/data/{kind}/{split}.jsonl'
            assert sha(path)==historical['inputs'][str(path)]
            collections[kind]=rows(path)
            dest=ROOT/f'data/{kind}/{split}.jsonl'
            write_rows(dest, collections[kind]); files[str(dest.relative_to(ROOT))]=sha(dest)
        clean={r['message_id']:r for r in collections['clean']}
        assert len(clean)==len(collections['gold'])
        for r in collections['gold']:
            c=clean[r['message_id']]
            assert set(c)=={'message_id','data_hex','byte_length','raw_sha256'}
            assert hashlib.sha256(bytes.fromhex(c['data_hex'])).hexdigest()==r['raw_sha256']==c['raw_sha256']
            assert 0<len(r['fields'])<64
        counts[split]={p:dict(messages=sum(r['protocol']==p for r in collections['gold']),
            fields=sum(len(r['fields']) for r in collections['gold'] if r['protocol']==p)) for p in PROTOCOLS}
        protocol_ids[split]={p:[r['message_id'] for r in collections['gold'] if r['protocol']==p] for p in PROTOCOLS}
        if split=='development':
            for p in PROTOCOLS:
                ids={r['message_id'] for r in collections['gold'] if r['protocol']==p}
                dev[p]=[r['message_id'] for r in sorted((r for r in collections['clean'] if r['message_id'] in ids),key=lambda r:(r['raw_sha256'],r['message_id']))[:DEV_LIMIT]]
    write(ROOT/'DATA_CONTRACT.json', dict(time=now(),files=files,counts=counts,development_ids=dev,protocol_ids=protocol_ids,
        development_selection='first32 by raw_sha256,message_id within protocol; no field labels',
        historical_contract_sha256=sha(STUDY/'three_to_one_v15/DATA_CONTRACT.json'),synthetic=False,
        plan_sha256=sha(ROOT/'PLAN.md'),historical_test_previously_inspected=True))
    code=[ROOT/name for name in ('common16.py','models16.py','losses16.py','train16.py','evaluate16.py','run16.py','select16.py','test16.py','prepare16.py')]
    code+=sorted((WORKSPACE/'lapa-attention/src/lapa').rglob('*.py'))
    write(ROOT/'CODE_CONTRACT.json', dict(time=now(),files={str(p):sha(p) for p in code},
        variants=VARIANTS,search_seeds=SEARCH_SEEDS,final_seeds=FINAL_SEEDS,
        search_steps=SEARCH_STEPS,final_steps=FINAL_STEPS,anchor='tape',package_modified=False))
    log('P01_CONTRACTS_FROZEN',counts=counts)
    print(json.dumps(counts,indent=2))

if __name__=='__main__': main()
