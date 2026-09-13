"""Four-worker, fail-closed screen -> refine -> final GPU training queue.

No background detachment, silent retry, seed addition, or budget change is
performed. Existing COMPLETE runs must pass their entire artifact manifest.
Partial runs and pre-existing logs without a completed run are preserved for
investigation. The root task may monitor GRID_PROGRESS.json throughout.
"""
import argparse
import subprocess
import time

from common17 import *


def _command(job):
    command = [sys.executable, str(ROOT/'train17.py'), '--phase', job['phase'],
               '--variant', job['variant'], '--backbone', job['backbone'],
               '--seed', str(job['seed']), '--sources', *job['sources']]
    if job['target'] is not None:
        command += ['--target', job['target']]
    return command


def queue(phase, workers):
    verify_contract()
    if phase == 'refine':
        verify_choice_file('PROMOTION.json')
    if phase == 'final':
        verify_choice_file('SELECTION.json')
    pending = phase_jobs(phase)
    total, completed = len(pending), 0
    running, failures = [], []
    started = time.monotonic()
    while pending or running:
        while pending and len(running) < workers and not failures:
            job = pending.pop(0)
            folder = job_folder(job)
            if (folder/'COMPLETE.json').exists():
                try:
                    complete = verify_run(folder)
                    assert all(complete[key] == value for key, value in job.items()), job
                    completed += 1
                    log('RUN_REUSED_VERIFIED', job=job)
                    continue
                except Exception as error:
                    failures.append(dict(job=job, error='completed run verification failed', detail=repr(error)))
                    break
            if folder.exists():
                failures.append(dict(job=job, error='partial run exists; preserve and investigate', folder=str(folder)))
                break
            group = job['target'] if phase == 'final' else '_'.join(job['sources'])
            logfile = ROOT/'logs'/phase/f"{group}__{job['backbone']}__{job['variant']}__{job['seed']}.log"
            logfile.parent.mkdir(parents=True, exist_ok=True)
            if logfile.exists():
                failures.append(dict(job=job, error='existing log without completed run; preserve and investigate', log=str(logfile)))
                break
            handle = logfile.open('x')
            try:
                process = subprocess.Popen(_command(job), stdout=handle, stderr=subprocess.STDOUT, cwd=ROOT)
            except Exception as error:
                handle.close()
                failures.append(dict(job=job, error='launch failed', detail=repr(error), log=str(logfile)))
                break
            running.append((process, handle, job, str(logfile)))
            log('RUN_STARTED', job=job, pid=process.pid, log=str(logfile))

        for process, handle, job, logfile in running[:]:
            returncode = process.poll()
            if returncode is None:
                continue
            handle.close()
            running.remove((process, handle, job, logfile))
            try:
                assert returncode == 0, ('nonzero worker exit', returncode)
                complete = verify_run(job_folder(job))
                assert all(complete[key] == value for key, value in job.items()), job
            except Exception as error:
                failures.append(dict(job=job, returncode=returncode, error=repr(error), log=logfile))
                log('RUN_FAILED', job=job, returncode=returncode, error=repr(error))
            else:
                completed += 1
                log('RUN_COMPLETE', job=job, seconds=complete['seconds'])

        progress = dict(time=now(), phase=phase, done=completed, total=total,
                        pending=len(pending), active=[dict(job=job, pid=p.pid, log=logfile)
                                                     for p, handle, job, logfile in running],
                        failed=failures, elapsed_seconds=time.monotonic() - started,
                        status='DRAINING_AFTER_FAILURE' if failures and running else 'FAILED' if failures else 'RUNNING')
        write(ROOT/'GRID_PROGRESS.json', progress, replace=True)
        # On failure, stop launching work and let already running scoped jobs
        # finish and seal. Their work is recoverable without silent reruns.
        if failures and not running:
            log('PHASE_FAILED', phase=phase, failures=failures)
            raise RuntimeError(json.dumps(failures))
        if pending or running:
            time.sleep(2)
    assert completed == total
    log('PHASE_COMPLETE', phase=phase, models=completed, seconds=time.monotonic() - started)
    return completed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    assert 1 <= args.workers <= 4
    verify_contract()
    started = time.monotonic()
    log('GRID_STARTED', workers=args.workers)
    screen = queue('screen', args.workers)
    if not (ROOT/'PROMOTION.json').exists():
        from select17 import promote
        promote()
    verify_choice_file('PROMOTION.json')
    refine = queue('refine', args.workers)
    if not (ROOT/'SELECTION.json').exists():
        from select17 import select
        select()
    verify_choice_file('SELECTION.json')
    final = queue('final', args.workers)
    verify_contract()
    complete = dict(time=now(), screen_models=screen, refine_models=refine, final_models=final,
                    total_models=screen + refine + final, seconds=time.monotonic() - started,
                    code_contract_sha256=sha(ROOT/'CODE_CONTRACT.json'),
                    promotion_sha256=sha(ROOT/'PROMOTION.json'),
                    selection_sha256=sha(ROOT/'SELECTION.json'))
    if (ROOT/'GRID_COMPLETE.json').exists():
        prior = read(ROOT/'GRID_COMPLETE.json')
        for key in ('screen_models', 'refine_models', 'final_models', 'total_models',
                    'code_contract_sha256', 'promotion_sha256', 'selection_sha256'):
            assert prior[key] == complete[key], (key, prior[key], complete[key])
    else:
        write(ROOT/'GRID_COMPLETE.json', complete)
    write(ROOT/'GRID_PROGRESS.json', dict(complete, phase='COMPLETE', status='COMPLETE',
                                        done=screen + refine + final, total=screen + refine + final,
                                        pending=0, active=[], failed=[]), replace=True)
    log('GRID_COMPLETE', screen_models=screen, refine_models=refine, final_models=final)


if __name__ == '__main__':
    main()
