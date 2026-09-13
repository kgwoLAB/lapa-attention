"""Freeze design, executable code and inherited evidence before v18 fitting."""
from common18 import ROOT,V17,now,sha,read,write,jobs,previous
from executor18 import FourFactorExecutor


def main():
    assert not (ROOT/'CONTRACT.json').exists()
    assert not (ROOT/'runs').exists()
    previous.verify_contract()
    smoke = {}
    for device in ('CPU','CUDA'):
        path = ROOT/f'SMOKE_{device}.json'
        result = read(path)
        assert result['status']=='PASS'
        assert result['every_encoder_and_readout_uses_four_factors']
        assert result['standard_qk_attention_calls_forbidden']
        assert not result['evaluation_read'] and not result['development_read']
        smoke[str(path)] = sha(path)
    paths = [ROOT/name for name in ('common18.py','executor18.py','model18.py','losses18.py',
        'evaluate18.py','train18.py','run18.py','test18.py','freeze18.py','PLAN.md')]
    paths += [V17/'CODE_CONTRACT.json',V17/'DATA_CONTRACT.json']
    controls = {}
    for job in jobs():
        for backbone in ('rope','cope','tape','sdpa'):
            for variant in ('off','hybrid'):
                path = V17/'final'/job['target']/f'{backbone}__{variant}__{job["seed"]}'
                if str(path) in controls:
                    continue
                previous.verify_run(path)
                meta = read(path/'TRAINING.json')
                assert meta['steps']==600 and meta['sources']==job['sources'] and meta['seed']==job['seed']
                controls[str(path)] = dict(complete_sha256=sha(path/'COMPLETE.json'),
                    training_sha256=sha(path/'TRAINING.json'),stream_sha256=meta['stream_sha256'])
                paths += [path/'COMPLETE.json',path/'TRAINING.json']
    assert len(controls)==96 and len(jobs())==24
    contract = dict(schema='four-factor-attention-v18',time=now(),
        files={str(path):sha(path) for path in paths},smoke_files=smoke,
        data_contract_sha256=sha(V17/'DATA_CONTRACT.json'),jobs=jobs(),steps_per_model=600,
        total_updates=14400,workers=2,learned_factors=['source','width','endian','base'],
        qk_similarity=False,learned_program_head=False,value_projection_retained=True,
        mode_selection_on_target=False,development_selection=False,
        data='historical real-capture only; 3-source training / 1-held-out protocol evaluation',
        executor=FourFactorExecutor().manifest(),executor_fingerprint=FourFactorExecutor().fingerprint,
        controls=controls)
    write(ROOT/'CONTRACT.json',contract)
    print('FROZEN: 24 new models; 96 matched historical controls; no target tuning')


if __name__=='__main__': main()
