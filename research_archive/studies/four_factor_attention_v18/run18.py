"""Two-worker fail-closed queue; never change budgets or replace partial output."""
import subprocess
import sys
import time
from common18 import ROOT,STEPS,now,read,sha,write,verify_contract,jobs,folder


def verify_job(job):
    path=folder(job); done=read(path/'COMPLETE.json')
    assert all(done[k]==v for k,v in job.items()) and done['steps']==STEPS
    assert done['contract_sha256']==sha(ROOT/'CONTRACT.json')
    required={'TRAINING.json','curve.json','model.pt','evaluation/METRICS.json',
              'evaluation/PREDICTION_SEAL.json','evaluation/diagnostics.jsonl'}
    assert required <= set(done['files']), (path,'missing required sealed artifacts')
    for name,digest in done['files'].items():
        resolved=(path/name).resolve()
        assert path.resolve() in resolved.parents, (path,name)
        assert sha(resolved)==digest, (path,name)
    metadata=read(path/'TRAINING.json')
    assert all(metadata[k]==v for k,v in job.items()) and metadata['steps']==STEPS
    assert metadata['contract_sha256']==sha(ROOT/'CONTRACT.json')
    return done


def verify_completed_grid():
    complete=read(ROOT/'GRID_COMPLETE.json')
    expected=jobs()
    def identity(job):
        return job['target'],job['mode'],job['seed'],tuple(job['sources'])
    assert complete['contract_sha256']==sha(ROOT/'CONTRACT.json')
    assert complete['models']==len(expected) and complete['steps']==len(expected)*STEPS
    assert len(complete['jobs'])==len(expected)
    assert {identity(job) for job in complete['jobs']}=={identity(job) for job in expected}
    for job in expected:
        verify_job(job)
    return complete


def main():
    verify_contract()
    if (ROOT/'GRID_COMPLETE.json').exists():
        complete=verify_completed_grid()
        write(ROOT/'GRID_PROGRESS.json',dict(complete,status='COMPLETE',done=complete['models'],
            total=complete['models'],pending=0,active=[],failed=[]),replace=True)
        print('VERIFIED COMPLETE: existing four-factor grid; no models rerun',flush=True)
        return complete
    queue=jobs(); active=[]; completed=[]; failed=[]; started=time.monotonic()
    while queue or active:
        while queue and len(active)<2 and not failed:
            job=queue.pop(0); path=folder(job)
            if (path/'COMPLETE.json').exists():
                try:
                    verify_job(job)
                except Exception as error:
                    failed.append(dict(job=job,error='Completed resume verification failed',detail=repr(error)))
                    break
                completed.append(job);continue
            logfile=ROOT/'logs'/f'{job["target"]}__{job["mode"]}__{job["seed"]}.log'
            if path.exists() or logfile.exists():
                failed.append(dict(job=job,error='Partial run/log exists; preserved for investigation'));break
            logfile.parent.mkdir(exist_ok=True)
            handle=None
            try:
                handle=logfile.open('x')
                process=subprocess.Popen([sys.executable,str(ROOT/'train18.py'),'--target',job['target'],
                                          '--mode',job['mode'],'--seed',str(job['seed'])],cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT)
            except Exception as error:
                if handle is not None: handle.close()
                failed.append(dict(job=job,error='Worker launch failed; log preserved',detail=repr(error),log=str(logfile)))
                break
            active.append((process,handle,job,str(logfile)))
        for process,handle,job,logfile in active[:]:
            status=process.poll()
            if status is None:continue
            handle.close();active.remove((process,handle,job,logfile))
            try:
                assert status==0, ('worker exit',status)
                verify_job(job)
            except Exception as error:failed.append(dict(job=job,error=repr(error),log=logfile))
            else:completed.append(job)
        write(ROOT/'GRID_PROGRESS.json',dict(time=now(),done=len(completed),total=24,pending=len(queue),
            active=[dict(job=j,pid=p.pid,log=l) for p,h,j,l in active],failed=failed,
            elapsed_seconds=time.monotonic()-started,
            status='DRAINING_AFTER_FAILURE' if failed and active else 'FAILED' if failed else 'RUNNING'),replace=True)
        if failed and not active:raise RuntimeError(failed)
        if queue or active:time.sleep(2)
    verify_contract()
    assert len(completed)==24
    complete=dict(time=now(),models=24,steps=14400,seconds=time.monotonic()-started,
                  contract_sha256=sha(ROOT/'CONTRACT.json'),jobs=completed)
    if (ROOT/'GRID_COMPLETE.json').exists():
        complete=verify_completed_grid()
    else:
        write(ROOT/'GRID_COMPLETE.json',complete)
    write(ROOT/'GRID_PROGRESS.json',dict(complete,status='COMPLETE',done=24,total=24,pending=0,active=[],failed=[]),replace=True)
    print('COMPLETE: 24 four-factor models',flush=True)


if __name__=='__main__':main()
