"""Independent numerical/provenance/PDF-text audit of all twelve v17 figures.

This module does not import plot17 or invoke any plotting/evaluation code.
Every plotted matrix is rebuilt from SUMMARY; every paired gain is rebuilt
from final per-protocol seed values.  PDF text checks cover every page and
every numeric annotation, but do not establish layout quality.  All-page
rendered visual review remains a separate, explicitly required root task.
"""
from collections import Counter
import math
from pathlib import Path
import re
import statistics
import xml.etree.ElementTree as ET

from pypdf import PdfReader

from common17 import ROOT, PROTOCOLS, BACKBONES, VARIANTS, FINAL_SEEDS, read, sha, write, now


ROLES = ('off', 'hybrid', 'p_champion', 'nll_champion')
ROLE_LABELS = {'off': 'Off', 'hybrid': 'Hybrid', 'p_champion': 'P-selected', 'nll_champion': 'NLL-selected'}
BACKBONE_LABELS = {'rope': 'RoPE', 'cope': 'CoPE', 'tape': 'TAPE', 'sdpa': 'SDPA'}
PROTOCOL_LABELS = {'dns': 'DNS', 'modbus': 'Modbus', 'tls': 'TLS', 'smb2': 'SMB2'}
COHORTS = (('dns', 'LENGTH'), ('dns', 'POINTER'), ('modbus', 'LENGTH'),
           ('tls', 'LENGTH'), ('smb2', 'LENGTH'), ('smb2', 'OFFSET'))
FIGURE_ORDER = (
    '01_screen_balanced_p', '02_screen_log_gain', '03_refinement_selection',
    '04_final_numeric_p', '05_final_numeric_hit1', '06_final_numeric_nll',
    '07_dns_relations_p', '08_smb2_relations_p', '10_source_stage',
    '11_program_stage', '12_exact_field_f1', '09_paired_macro_gains',
)
T95_DF2 = 4.302652729911275


def _display_number(value):
    if value is None:
        return 'N/A'
    assert math.isfinite(value)
    return f'{value:.1e}' if value != 0 and abs(value) < .00005 else f'{value:.4f}'


def _normalized(text):
    return re.sub(r'\s+', ' ', text.replace('\u2212', '-')).strip()


def _role_node(summary, protocol, backbone, role):
    return summary['final'][protocol]['by_backbone'][backbone]['roles'][role]


def _row_label(backbone, role):
    return BACKBONE_LABELS[backbone] + ' / ' + ROLE_LABELS[role]


def _stat_mean(value):
    return None if value is None else float(value['mean'])


def _matrix_spec(summary, name):
    """Reconstruct values and semantic labels without calling plot helpers."""
    if name in ('01_screen_balanced_p', '02_screen_log_gain'):
        metric_name = 'balanced_p' if name == '01_screen_balanced_p' else 'balanced_log_gain'
        candidate_scores = {}
        for target in PROTOCOLS:
            rows = summary['screen']['outer_candidates'][target]
            assert len(rows) == len(VARIANTS) and {r['variant'] for r in rows} == set(VARIANTS)
            candidate_scores[target] = {r['variant']: r['scores'][metric_name] for r in rows}
        return dict(values=[[candidate_scores[target][variant] for target in PROTOCOLS] for variant in VARIANTS],
                    rows=list(VARIANTS), columns=['Hold out\n'+PROTOCOL_LABELS[target] for target in PROTOCOLS],
                    heading='All 30 formulas: source-only screening',
                    unit='Balanced probability of the correct destination (higher is better)' if metric_name == 'balanced_p'
                         else 'Balanced log gain over uniform, nat (higher is better)')

    endpoint_figures = {
        '04_final_numeric_p': ('p_true', 'Final probability assigned to the correct destination', 'Mean p(target), higher is better'),
        '05_final_numeric_hit1': ('hit1', 'Final destination retrieval: Hit@1', 'Mean Hit@1, higher is better'),
        '06_final_numeric_nll': ('nll', 'Final destination negative log-likelihood', 'Mean NLL, nat; lower is better'),
    }
    if name in endpoint_figures:
        key, heading, unit = endpoint_figures[name]
        values, labels = [], []
        for backbone in BACKBONES:
            for role in ROLES:
                values.append([_stat_mean(_role_node(summary, p, backbone, role)['by_semantic'][semantic]['metrics'][key])
                               for p, semantic in COHORTS])
                labels.append(_row_label(backbone, role))
        if key != 'nll':
            for reference, label in (('always_end', 'Always END'), ('always_null', 'Always NULL'), ('uniform', 'Uniform')):
                values.append([float(summary['final'][p]['sanity']['by_semantic'][semantic]['models'][reference][key])
                               for p, semantic in COHORTS])
                labels.append(label+' (sanity only)')
        columns = [PROTOCOL_LABELS[p]+'\n'+semantic.lower()+'\n(n='+
                   str(_role_node(summary, p, BACKBONES[0], 'off')['by_semantic'][semantic]['n_fields'])+')'
                   for p, semantic in COHORTS]
        return dict(values=values, rows=labels, columns=columns, heading=heading, unit=unit)

    if name in ('07_dns_relations_p', '08_smb2_relations_p'):
        target = 'dns' if name.startswith('07') else 'smb2'
        relations = list(_role_node(summary, target, 'tape', 'off')['by_relation'])
        values, labels = [], []
        for backbone in BACKBONES:
            for role in ROLES:
                values.append([_stat_mean(_role_node(summary, target, backbone, role)['by_relation'][relation]['metrics']['p_true'])
                               for relation in relations])
                labels.append(_row_label(backbone, role))
        columns = [relation.replace('DNS ', 'DNS\n').replace('SMB2 ', 'SMB2\n')+'\n(n='+
                   str(_role_node(summary, target, BACKBONES[0], 'off')['by_relation'][relation]['n_fields'])+')'
                   for relation in relations]
        return dict(values=values, rows=labels, columns=columns,
                    heading=PROTOCOL_LABELS[target]+': separate address relations', unit='Mean p(target), higher is better')

    if name in ('10_source_stage', '11_program_stage'):
        key = 'source_p' if name == '10_source_stage' else 'program_p'
        values, labels = [], []
        for backbone in BACKBONES:
            for role in ROLES:
                if role == 'off':
                    for p, semantic in COHORTS:
                        assert _role_node(summary, p, backbone, role)['by_semantic'][semantic]['stages'][key] is None
                    continue
                values.append([_stat_mean(_role_node(summary, p, backbone, role)['by_semantic'][semantic]['stages'][key])
                               for p, semantic in COHORTS])
                labels.append(_row_label(backbone, role))
        return dict(values=values, rows=labels,
                    columns=[PROTOCOL_LABELS[p]+'\n'+semantic.lower() for p, semantic in COHORTS],
                    heading='Source localization probability' if key == 'source_p'
                            else 'Program probability conditioned on the true source',
                    unit='Mean diagnostic probability, higher is better')

    assert name == '12_exact_field_f1', name
    values, labels = [], []
    for backbone in BACKBONES:
        for role in ROLES:
            row = []
            for protocol, semantic in COHORTS:
                field = _role_node(summary, protocol, backbone, role)['field_f1']
                if role == 'off':
                    assert field is None, 'Off field F1 must remain untrained, not measured zero'
                row.append(None if field is None else _stat_mean(field['by_semantic'][semantic]))
            values.append(row)
            labels.append(_row_label(backbone, role))
    return dict(values=values, rows=labels,
                columns=[PROTOCOL_LABELS[p]+'\n'+semantic.lower() for p, semantic in COHORTS],
                heading='Exact typed-field discovery: F1', unit='Mean exact typed-span F1, higher is better')


def _assert_nested(actual, expected, path='root'):
    if isinstance(expected, dict):
        assert isinstance(actual, dict) and set(actual) == set(expected), path
        for key, value in expected.items():
            _assert_nested(actual[key], value, path+'.'+str(key))
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected), path
        for index, value in enumerate(expected):
            _assert_nested(actual[index], value, path+f'[{index}]')
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        assert isinstance(actual, (int, float)) and math.isfinite(actual), (path, actual)
        assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), (path, actual, expected)
    else:
        assert actual == expected, (path, actual, expected)


def _numeric_audit(figure, expected):
    assert figure['kind'] == 'numeric_heatmap'
    assert [_normalized(v) for v in figure['rows']] == [_normalized(v) for v in expected['rows']]
    assert [_normalized(v) for v in figure['columns']] == [_normalized(v) for v in expected['columns']]
    assert figure['unit'] == expected['unit']
    _assert_nested(figure['values'], expected['values'], figure['name']+'.values')
    flat = [value for row in expected['values'] for value in row]
    present = [value for value in flat if value is not None]
    assert len(flat) == len(expected['rows']) * len(expected['columns'])
    assert figure['numeric_cells'] == len(present)
    assert figure['missing_cells'] == len(flat) - len(present)
    assert all(math.isfinite(value) for value in present)
    return dict(kind='numeric_heatmap', shape=[len(expected['rows']), len(expected['columns'])],
                numeric_cells=len(present), missing_cells=len(flat)-len(present),
                exact_zero_cells=sum(value == 0 for value in present),
                tiny_nonzero_cells=sum(0 < abs(value) < .00005 for value in present),
                annotation_counts=dict(Counter(_display_number(value) for value in flat)))


def _three_seed_statistics(seed_values):
    values = {str(seed): float(seed_values[seed]) for seed in FINAL_SEEDS}
    mean, std = statistics.mean(values.values()), statistics.stdev(values.values())
    margin = T95_DF2*std/math.sqrt(len(values))
    return dict(mean=mean, std=std, ci95=[mean-margin, mean+margin], seed_values=values, n_seeds=3)


def _gain_audit(summary, figure):
    assert figure['kind'] == 'paired_errorbars'
    expected_records = []
    for backbone in BACKBONES:
        for role in ('p_champion', 'nll_champion'):
            contrast = role+'_minus_hybrid'
            gains = {}
            for name, key, direction in (('p_true_gain', 'p_true', 1), ('hit1_gain', 'hit1', 1),
                                         ('nll_gain', 'nll', -1), ('balanced_p_gain', 'balanced_p', 1),
                                         ('balanced_log_gain_gain', 'balanced_log_gain', 1)):
                by_seed = {}
                for seed in FINAL_SEEDS:
                    candidate = statistics.mean(_role_node(summary, p, backbone, role)['metrics'][key]['seed_values'][str(seed)] for p in PROTOCOLS)
                    reference = statistics.mean(_role_node(summary, p, backbone, 'hybrid')['metrics'][key]['seed_values'][str(seed)] for p in PROTOCOLS)
                    by_seed[seed] = direction*(candidate-reference)
                recomputed = _three_seed_statistics(by_seed)
                stored = summary['macro']['by_backbone'][backbone]['all_fields']['comparisons'][contrast]['gains'][name]
                for stat_key, value in recomputed.items():
                    _assert_nested(stored[stat_key], value, f'{backbone}.{contrast}.{name}.{stat_key}')
                assert 'df=2' in stored['interval'] and 'un-clipped' in stored['interval']
                gains[name] = stored
            expected_records.append(dict(backbone=backbone, contrast=contrast, gains=gains))
    _assert_nested(figure['records'], expected_records, 'paired.records')
    return dict(kind='paired_errorbars', records=len(expected_records),
                independently_recomputed_gain_statistics=len(expected_records)*5,
                plotted_points=2*len(expected_records), displayed_ci='Student t df=2 across three paired training seeds')


def _selection_audit(summary, figure):
    assert figure['kind'] == 'selection_table'
    expected = []
    annotations = []
    for target in PROTOCOLS:
        choice = summary['selection']['choices'][target]
        for candidate in choice['candidates']:
            roles = []
            if candidate['variant'] == choice['p_champion']:
                roles.append('P')
            if candidate['variant'] == choice['nll_champion']:
                roles.append('NLL')
            expected.append(dict(target=target, **candidate, selected_for=roles))
            annotations.extend(_display_number(candidate['scores'][key]) for key in ('balanced_p', 'balanced_log_gain'))
    _assert_nested(figure['records'], expected, 'selection.records')
    return dict(kind='selection_table', rows=len(expected), annotation_counts=dict(Counter(annotations)))


def _read_pdf(path, expected_pages):
    reader = PdfReader(str(path), strict=True)
    assert not reader.is_encrypted, path
    assert len(reader.pages) == expected_pages, (path, len(reader.pages), expected_pages)
    text = []
    for index, page in enumerate(reader.pages):
        assert float(page.mediabox.width) > 0 and float(page.mediabox.height) > 0
        value = page.extract_text() or ''
        assert len(value.strip()) > 100, (path, index, 'missing readable page text')
        assert '\ufffd' not in value and '\x00' not in value, (path, index, 'unreadable replacement/NUL glyph')
        text.append(value)
    return text


def _verify_annotations(text, annotation_counts, label):
    normal = text.replace('\u2212', '-')
    for token, count in annotation_counts.items():
        # Check every repeated value, not merely presence of one representative
        # token. Axis/footer coincidences may add tokens but may not remove cells.
        assert normal.count(token) >= count, (label, token, normal.count(token), count)
    return sum(annotation_counts.values())


def verify():
    assert (ROOT/'GRID_COMPLETE.json').exists()
    manifest = read(ROOT/'FIGURE_MANIFEST.json')
    summary = read(ROOT/'SUMMARY.json')
    assert summary['audit']['status'] == 'PASS'
    assert summary['audit']['grid_complete_sha256'] == sha(ROOT/'GRID_COMPLETE.json')
    assert summary['audit']['selection_sha256'] == sha(ROOT/'SELECTION.json')
    assert manifest['summary_sha256'] == sha(ROOT/'SUMMARY.json')
    assert manifest['plotting_code_sha256'] == sha(ROOT/'plot17.py')
    assert manifest['pages'] == 12
    assert tuple(figure['name'] for figure in manifest['figures']) == FIGURE_ORDER
    combined = Path(manifest['pdf']['path']).resolve()
    assert combined == (ROOT/'output/pdf/LAPA_formula_search_v17.pdf').resolve()
    assert sha(combined) == manifest['pdf']['sha256']
    combined_text = _read_pdf(combined, 12)
    results, paths = [], set()
    for index, figure in enumerate(manifest['figures']):
        name = figure['name']
        if name == '03_refinement_selection':
            result = _selection_audit(summary, figure)
            heading = 'Source-only refinement and frozen formula selection'
            expected = None
        elif name == '09_paired_macro_gains':
            result = _gain_audit(summary, figure)
            heading = 'Paired changes: equal-protocol macro average'
            expected = None
        else:
            expected = _matrix_spec(summary, name)
            result = _numeric_audit(figure, expected)
            heading = expected['heading']
        assert {Path(entry['path']).suffix for entry in figure['files']} == {'.png', '.pdf', '.svg'}
        assert len(figure['files']) == 3
        individual_text = None
        verified_files = []
        for entry in figure['files']:
            path = Path(entry['path']).resolve()
            assert path.parent == (ROOT/'figures').resolve() and path.stem == name
            assert path not in paths and sha(path) == entry['sha256']
            paths.add(path)
            if path.suffix == '.pdf':
                individual_text = _read_pdf(path, 1)[0]
            elif path.suffix == '.png':
                with path.open('rb') as handle:
                    assert handle.read(8) == b'\x89PNG\r\n\x1a\n'
            else:
                assert ET.parse(path).getroot().tag == '{http://www.w3.org/2000/svg}svg'
            verified_files.append(dict(path=str(path), sha256=entry['sha256']))
        assert individual_text is not None
        for label, text in (('combined page '+str(index+1), combined_text[index]), ('individual '+name, individual_text)):
            assert _normalized(heading) in _normalized(text), (label, 'heading not found')
            if expected is not None:
                for text_label in expected['rows'] + expected['columns']:
                    assert _normalized(text_label) in _normalized(text), (label, text_label)
            if 'annotation_counts' in result:
                _verify_annotations(text, result['annotation_counts'], label)
        # Both exports originate from the same figure, not different results.
        assert _normalized(individual_text) == _normalized(combined_text[index]), (name, 'PDF exports differ in extracted content')
        result.update(name=name, combined_page=index+1, files=verified_files,
                      text_characters=len(combined_text[index]), all_numeric_annotations_checked='annotation_counts' in result)
        results.append(result)
    audit = dict(
        schema='lapa-v17-independent-figure-audit-1', time=now(), status='PASS',
        manifest_sha256=sha(ROOT/'FIGURE_MANIFEST.json'), summary_sha256=sha(ROOT/'SUMMARY.json'),
        plotting_code_sha256=sha(ROOT/'plot17.py'), validator_code_sha256=sha(__file__),
        combined_pdf_sha256=sha(combined), combined_pdf_pages=12,
        individual_pdf_pages_checked=12, verified_figure_files=len(paths),
        total_numeric_cells=sum(result.get('numeric_cells', 0) for result in results),
        total_missing_cells=sum(result.get('missing_cells', 0) for result in results),
        total_exact_zero_cells=sum(result.get('exact_zero_cells', 0) for result in results),
        total_tiny_nonzero_cells=sum(result.get('tiny_nonzero_cells', 0) for result in results),
        plotted_module_imported=False, all_pages_text_checked=True, arbitrary_sampling_used=False,
        visual_review_performed=False, visual_review_required=True,
        limitations='Text readability and complete numeric/provenance checks do not detect overlap, clipping, or layout defects; separate all-page rendered inspection required.',
        figures=results,
    )
    write(ROOT/'FIGURE_AUDIT.json', audit)
    print(f"PASS: {len(results)} figures, {len(paths)} files, all 12 PDF pages; visual review remains required", flush=True)
    return audit


if __name__ == '__main__':
    verify()
