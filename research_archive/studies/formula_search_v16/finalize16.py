"""Final artifact checks after root-agent PDF visual review."""
from common16 import *
from pypdf import PdfReader

def main():
    verify_contract();verify_selection()
    independent=read(ROOT/'INDEPENDENT_AUDIT.json')
    assert independent['status']=='PASS_COMPLETE'
    assert independent['search_models']==72 and independent['final_models']==27
    manifest=read(ROOT/'FIGURE_MANIFEST.json')
    pdf=Path(manifest['pdf'])
    assert sha(pdf)==manifest['pdf_sha256']
    reader=PdfReader(pdf)
    assert len(reader.pages)==len(manifest['pages'])==8
    qa=read(ROOT/'VISUAL_REVIEW.json')
    assert qa['status']=='PASS' and qa['pdf_sha256']==sha(pdf) and qa['pages_reviewed']==list(range(1,9))
    # Rotated font kerning can be extracted as "T yped" by pypdf.
    assert 'TypedexactfieldF1' in ''.join(reader.pages[7].extract_text().split())
    numeric=[a for a in manifest['annotations'] if a['value'] is not None]
    missing=[a for a in manifest['annotations'] if a['value'] is None]
    assert len(numeric)==234 and len(missing)==6
    for row in numeric:
        value=row['value']
        expected=f'{value:.1e}' if 0<abs(value)<.00005 else f'{value:.4f}'
        assert row['text']==expected
        assert value==0 or row['text'] not in ('0.0000','-0.0000'), 'Do not display tiny nonzero as zero'
    for row in missing:
        assert row['figure']=='07_field_f1' and row['row']=='TAPE Off (endpoint loss)' and row['text']=='N/A'
    for page in manifest['pages']:
        for ext in ('png','svg'):
            assert sha(ROOT/f"figures/{page['name']}.{ext}")==page[ext+'_sha256']
    text=(ROOT/'MASTER_CHECKLIST.md').read_text()
    assert '- [ ]' not in text
    paths=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in ('.md','.py','.json') and p.name!='COMPLETION.json']
    paths+=list((ROOT/'figures').glob('*.png'))+list((ROOT/'figures').glob('*.svg'))+list((ROOT/'tables').glob('*.tex'))+[pdf]
    result=dict(time=now(),status='COMPLETE',search_models=72,final_models=27,total_models=99,
        training_steps=34200,all_required_steps_complete=True,released_package_changed=False,
        conclusion='No consistently superior replacement formula established; retain current hybrid default',
        scope='TAPE anchor plus CNN; real DNS/Modbus/TLS/SMB2 nested selection and3-to1 historical test',
        pages=8,numeric_table_cells=234,explicit_untrained_na_cells=6,
        independent_audit_sha256=sha(ROOT/'INDEPENDENT_AUDIT.json'),visual_review_sha256=sha(ROOT/'VISUAL_REVIEW.json'),
        artifacts={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))})
    write(ROOT/'COMPLETION.json',result)
    log('P09_COMPLETE',models=99,pdf_pages=8,numeric_cells=234)
    print(json.dumps(dict(status='COMPLETE',models=99,pages=8,artifact_hashes=len(paths))))

if __name__=='__main__':main()
