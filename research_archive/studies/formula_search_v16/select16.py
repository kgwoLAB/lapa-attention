"""Outer-target selection never reads that target's development score."""
from common16 import *

def select():
    verify_contract()
    choices={}
    for target in PROTOCOLS:
        sources=[p for p in PROTOCOLS if p!=target]; table=[]
        for variant in VARIANTS:
            evidence=[]
            for pair in itertools.combinations(sources,2):
                validation=next(p for p in sources if p not in pair)
                assert target not in pair and validation!=target
                for seed in SEARCH_SEEDS:
                    folder=ROOT/'search'/('_'.join(pair))/f'{variant}_{seed}'
                    complete=read(folder/'COMPLETE.json')
                    assert complete['phase']=='search' and complete['sources']==list(pair)
                    assert complete['code_contract_sha256']==sha(ROOT/'CODE_CONTRACT.json')
                    for name,digest in complete['files'].items(): assert sha(folder/name)==digest
                    path=folder/f'validation/{validation}/METRICS.json'
                    result=read(path)
                    evidence.append(dict(pair=list(pair),validation=validation,seed=seed,
                        score=result['overall']['balanced_log_gain'],path=str(path),sha256=sha(path)))
            assert len(evidence)==6
            table.append(dict(variant=variant,score=statistics.mean(r['score'] for r in evidence),evidence=evidence))
        ranked=sorted(table,key=lambda r:(-r['score'],VARIANTS.index(r['variant'])))
        choices[target]=dict(sources=sources,selected=ranked[0]['variant'],ranked=ranked,
            target_development_used=False,target_evaluation_used=False)
    write(ROOT/'SELECTION.json',dict(time=now(),choices=choices,
        plan_sha256=sha(ROOT/'PLAN.md'),code_contract_sha256=sha(ROOT/'CODE_CONTRACT.json'),
        rule='macro inner-protocol/seed, within protocol equal relation×targetkind uniform-relative log gain'))
    log('P05_SELECTION_SEALED',selected={p:r['selected'] for p,r in choices.items()})
    return choices

if __name__=='__main__': print(json.dumps(select(),indent=2))
