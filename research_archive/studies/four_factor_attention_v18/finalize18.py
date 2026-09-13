"""Seal completed artifacts after actual root visual review of all PDF pages."""
import argparse
import subprocess
from common18 import ROOT,WORKSPACE,now,read,write,sha,verify_contract,jobs,folder
from run18 import verify_completed_grid


def main(visual_review_confirmed=False):
    assert visual_review_confirmed, 'Root must inspect all rendered PDF pages before confirming'
    verify_contract(); grid=verify_completed_grid()
    assert grid['models']==24 and grid['steps']==14400
    assert read(ROOT/'INDEPENDENT_AUDIT.json')['status']=='PASS'
    assert read(ROOT/'FIGURE_AUDIT.json')['status']=='PASS'
    assert read(ROOT/'REPORT_AUDIT.json')['status']=='PASS'
    manifest=read(ROOT/'FIGURE_MANIFEST.json')
    assert sha(ROOT/'SUMMARY.json')==manifest['summary_sha256']
    assert manifest['pdf']['pages']==9 and sha(ROOT/manifest['pdf']['path'])==manifest['pdf']['sha256']
    assert len(manifest['figures'])==9
    for figure in manifest['figures']:
        for name,expected in figure['files'].items(): assert sha(ROOT/name)==expected
    assert '- [ ]' not in (ROOT/'MASTER_CHECKLIST.md').read_text()
    status=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=WORKSPACE/'lapa-attention',text=True)
    assert not status, 'Do not claim released package unchanged with a dirty tracked worktree'
    rendered=[ROOT/'tmp/pdfs'/f'review-{n}.png' for n in range(1,10)]
    assert all(p.is_file() for p in rendered)
    visual=dict(time=now(),status='PASS',root_visually_reviewed=True,
        pdf_sha256=sha(ROOT/manifest['pdf']['path']),pages_reviewed=list(range(1,10)),
        rendered_png_sha256={p.name:sha(p) for p in rendered},
        checks=['all nine latest rendered pages inspected','no clipped or overlapping labels',
                'numeric cells legible','tiny positive probabilities use scientific notation',
                'paired CI zero-lines and labels distinguish NLL direction','all means and CI checked independently'],
        temp_render_cleanup='Only these nine reproducible scratch renders may be removed; final PNG/SVG/PDF and numeric artifacts retained')
    write(ROOT/'VISUAL_REVIEW.json',visual)
    selected=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or 'tmp' in p.relative_to(ROOT).parts:
            continue
        if p.name=='FINAL_ARTIFACTS.json':continue
        selected.append(p)
    final=dict(time=now(),status='COMPLETE',models_new=24,models_reused=96,new_training_updates=14400,
        no_target_selection=True,tracked_package_unchanged=True,contract_sha256=sha(ROOT/'CONTRACT.json'),
        figures=9,latex_tables=len(list((ROOT/'tables').glob('*.tex'))),pdf_pages=9,
        runs={str(folder(j).relative_to(ROOT)):sha(folder(j)/'COMPLETE.json') for j in jobs()},
        files={str(p.relative_to(ROOT)):sha(p) for p in selected})
    write(ROOT/'FINAL_ARTIFACTS.json',final)
    for name,expected in final['files'].items():assert sha(ROOT/name)==expected
    print(f'COMPLETE: {len(final["files"])} artifact hashes verified; 24 runs, 9 figures, {final["latex_tables"]} tables')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--visual-review-confirmed',action='store_true')
    main(parser.parse_args().visual_review_confirmed)
