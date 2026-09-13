"""Seal completed research artifacts after explicit all-page visual review."""
import argparse

from common17 import ROOT, now, read, sha, write, verify_contract, phase_jobs, job_folder, verify_run


def finalize(visual_review_confirmed=False):
    assert visual_review_confirmed, 'Human/agent visual inspection cannot be replaced by a numeric audit'
    verify_contract()
    grid = read(ROOT/'GRID_COMPLETE.json')
    audit = read(ROOT/'INDEPENDENT_AUDIT.json')
    figure = read(ROOT/'FIGURE_AUDIT.json')
    paper = read(ROOT/'PAPER_TABLES_AUDIT.json')
    assert grid['total_models'] == audit['completed_models'] == 400
    assert audit['status'] == figure['status'] == 'PASS'
    assert audit['training_steps'] == 140800
    assert paper['status'] == 'PASS_NUMERIC_AND_STRUCTURAL' and paper['cells_checked'] == 288
    assert figure['summary_sha256'] == paper['summary_sha256'] == sha(ROOT/'SUMMARY.json')
    assert paper['manifest_sha256'] == sha(ROOT/'PAPER_TABLES_MANIFEST.json')
    assert figure['manifest_sha256'] == sha(ROOT/'FIGURE_MANIFEST.json')
    assert figure['plotting_code_sha256'] == sha(ROOT/'plot17.py')
    pdf = ROOT/'output/pdf/LAPA_formula_search_v17.pdf'
    assert figure['combined_pdf_sha256'] == sha(pdf)
    assert '[ ]' not in (ROOT/'MASTER_CHECKLIST.md').read_text()
    pages = []
    for page in range(1, 13):
        original = ROOT/f'tmp/pdfs/v17-{page:02}.png'
        final = ROOT/f'tmp/pdfs/v17-final-{page:02}.png'
        same = sha(original) == sha(final)
        assert same if page < 12 else not same
        pages.append(dict(page=page, rendered_sha256=sha(final),
                          review='visually inspected directly' if page == 12 else
                                 'visually inspected original; final render byte-identical',
                          unchanged_by_layout_fix=same))
    write(ROOT/'VISUAL_REVIEW.json', dict(time=now(), status='PASS', pdf_sha256=sha(pdf),
        all_12_pages_reviewed=True, renderer='pdftoppm, 90 dpi', pages=pages,
        layout_fix='CI figure footer overlapped axis labels; increased bottom margin and top-aligned footer',
        post_fix_review='All first 11 pages byte-identical to reviewed renders; changed page12 re-rendered and reviewed',
        limitations='LaTeX tables were not compiled; separate numerical and structural audit only'))
    runs = {}
    for phase in ('screen', 'refine', 'final'):
        for job in phase_jobs(phase):
            folder = job_folder(job)
            verify_run(folder)
            path = folder/'COMPLETE.json'
            runs[str(path.relative_to(ROOT))] = sha(path)
    assert len(runs) == 400
    artifacts = set(ROOT.glob('*.md')) | set(ROOT.glob('*.py')) | set(ROOT.glob('*.json'))
    artifacts.add(ROOT/'EVENTS.jsonl')
    for directory in ('figures', 'output/pdf', 'tables', 'audit_snapshots', 'logs'):
        artifacts.update(p for p in (ROOT/directory).rglob('*') if p.is_file())
    artifacts.discard(ROOT/'FINAL_ARTIFACTS.json')
    artifacts.discard(ROOT/'GRID_PROGRESS.json')
    output = dict(time=now(), status='COMPLETE', unique_models=400, training_updates=140800,
        no_default_package_replacement=True, original_code_and_data_contracts_verified=True,
        files={str(p.relative_to(ROOT)): sha(p) for p in sorted(artifacts)},
        run_manifests=runs,
        integrity_chain='Final artifact -> COMPLETE run manifests -> all sealed model files; code/data contract chains retained',
        rendering_scratch_policy='Only reviewed temporary PNGs are removed after their hashes are recorded; final figures remain')
    write(ROOT/'FINAL_ARTIFACTS.json', output)
    for path, expected in output['files'].items():
        assert sha(ROOT/path) == expected
    print(f"COMPLETE: 400 models; {len(output['files'])} artifact hashes; 12 visually reviewed PDF pages")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--visual-review-confirmed', action='store_true')
    args = parser.parse_args()
    finalize(args.visual_review_confirmed)
