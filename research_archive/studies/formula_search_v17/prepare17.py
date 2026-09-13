from common17 import *

def main():
    old=read(V16/'DATA_CONTRACT.json');files={}
    for name,digest in old['files'].items():
        assert sha(V16/name)==digest
        write_rows(ROOT/name,rows(V16/name));files[name]=sha(ROOT/name)
    dev={p:old['development_ids'][p][:DEV_LIMIT] for p in PROTOCOLS}
    for p in PROTOCOLS:
        clean=rows(ROOT/'data/clean/development.jsonl');ids=set(old['protocol_ids']['development'][p])
        ranked=sorted((r for r in clean if r['message_id'] in ids),key=lambda r:(r['raw_sha256'],r['message_id']))[:DEV_LIMIT]
        assert dev[p]==[r['message_id'] for r in ranked]
    write(ROOT/'DATA_CONTRACT.json',dict(time=now(),files=files,protocol_ids=old['protocol_ids'],development_ids=dev,
        counts=old['counts'],synthetic=False,historical_test_previously_inspected=True,prior_data_contract_sha256=sha(V16/'DATA_CONTRACT.json')))
    paths=[ROOT/n for n in ('common17.py','models17.py','losses17.py','attribute17.py','locator17.py','execution_features17.py',
        'train17.py','run17.py','select17.py','test17.py','prepare17.py')]
    paths += [V16/n for n in ('common16.py','models16.py','evaluate16.py')]
    paths += sorted((WORKSPACE/'lapa-attention/src/lapa').rglob('*.py'))
    write(ROOT/'CODE_CONTRACT.json',dict(time=now(),files={str(p):sha(p) for p in paths},variants=VARIANTS,
        screen_seeds=SCREEN_SEEDS,refine_seeds=REFINE_SEEDS,final_seeds=FINAL_SEEDS,steps=STEPS,
        plan_sha256=sha(ROOT/'PLAN.md'),prior_package_modified=False))
    assert len(VARIANTS)==30 and len(phase_jobs('screen'))==180
    log('CONTRACTS_FROZEN',variants=30,screen_models=180)
    print(json.dumps(dict(variants=30,screen_models=180,code_files=len(paths))))

if __name__=='__main__':main()
