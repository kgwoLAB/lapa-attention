"""Resumable bounded local GPU queue, then sealed selection and final runs."""
import argparse
import subprocess
import time
from common16 import *

def jobs(phase):
    result=[]
    if phase=='search':
        for pair in PAIRS:
            for seed in SEARCH_SEEDS:
                for v in VARIANTS: result.append(dict(phase=phase,sources=list(pair),variant=v,seed=seed,target=None))
    else:
        selection=verify_selection()
        for target in PROTOCOLS:
            choice=selection['choices'][target]
            for seed in FINAL_SEEDS:
                for v in dict.fromkeys(('off','hybrid',choice['selected'])):
                    result.append(dict(phase=phase,sources=choice['sources'],variant=v,seed=seed,target=target))
    return result

def folder_for(j):
    return ROOT/j['phase']/(j['target'] if j['phase']=='final' else '_'.join(j['sources']))/f"{j['variant']}_{j['seed']}"

def queue(phase,workers):
    todo=jobs(phase);total=len(todo);done=0;running=[];failed=[];started=time.monotonic()
    while todo or running:
        while todo and len(running)<workers and not failed:
            j=todo.pop(0);folder=folder_for(j)
            if (folder/'COMPLETE.json').exists():
                c=read(folder/'COMPLETE.json')
                assert c['code_contract_sha256']==sha(ROOT/'CODE_CONTRACT.json')
                for name,digest in c['files'].items(): assert sha(folder/name)==digest
                done+=1;continue
            if folder.exists():
                failed.append(dict(job=j,error='partial run exists; preserve and investigate'))
                break
            logfile=ROOT/'logs'/phase/(('_'.join(j['sources']))+'_'+j['variant']+'_'+str(j['seed'])+'.log')
            logfile.parent.mkdir(parents=True,exist_ok=True)
            handle=logfile.open('x')
            cmd=[sys.executable,str(ROOT/'train16.py'),'--phase',phase,'--variant',j['variant'],'--seed',str(j['seed']),'--sources',*j['sources']]
            if j['target']:cmd+=['--target',j['target']]
            proc=subprocess.Popen(cmd,stdout=handle,stderr=subprocess.STDOUT,cwd=ROOT)
            running.append((proc,handle,j,str(logfile)));log('RUN_STARTED',job=j,pid=proc.pid)
        for proc,handle,j,path in running[:]:
            code=proc.poll()
            if code is None:continue
            handle.close();running.remove((proc,handle,j,path))
            if code==0 and (folder_for(j)/'COMPLETE.json').exists():done+=1;log('RUN_COMPLETE',job=j)
            else:failed.append(dict(job=j,returncode=code,log=path));log('RUN_FAILED',job=j,returncode=code)
        progress=dict(time=now(),phase=phase,done=done,total=total,pending=len(todo),
            active=[dict(job=j,pid=p.pid,log=path) for p,h,j,path in running],failed=failed,elapsed_seconds=time.monotonic()-started)
        write(ROOT/'GRID_PROGRESS.json',progress,replace=True)
        if failed and not running:raise RuntimeError(json.dumps(failed))
        if todo or running:time.sleep(2)
    log('PHASE_COMPLETE',phase=phase,models=done,seconds=time.monotonic()-started)
    return done

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    assert 1<=a.workers<=4;verify_contract()
    log('GRID_STARTED',workers=a.workers)
    n=queue('search',a.workers)
    if not (ROOT/'SELECTION.json').exists():
        from select16 import select
        select()
    m=queue('final',a.workers)
    write(ROOT/'GRID_COMPLETE.json',dict(time=now(),search_models=n,final_models=m,selection_sha256=sha(ROOT/'SELECTION.json')))
    write(ROOT/'GRID_PROGRESS.json',dict(time=now(),phase='COMPLETE',search_models=n,final_models=m),replace=True)
    log('GRID_COMPLETE',search_models=n,final_models=m)

if __name__=='__main__':main()
