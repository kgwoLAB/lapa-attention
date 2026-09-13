"""Independent numeric/vector/image audit of the nine v18 result figures.

Reads SUMMARY, manifests, SVG/PNG and PDF metadata. It never creates/edits a
figure or PDF. Automated checks are not a substitute for rendered-page visual
inspection, which is deliberately left to the root task.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
SEEDS = (170301, 170302, 170303)
T95 = 4.302652729911275
CORE = ('dns|LENGTH', 'dns|POINTER', 'modbus|LENGTH', 'tls|LENGTH', 'smb2|LENGTH', 'smb2|OFFSET')
CORE_COUNTS = (230, 36, 6, 15, 30, 30)
CORE_LABELS = ('DNS\nlength (230)', 'DNS\npointer (36)', 'Modbus\nlength (6)',
               'TLS\nlength (15)', 'SMB2\nlength (30)', 'SMB2\noffset (30)')
DNS = ('dns|DNS label', 'dns|DNS root terminator', 'dns|DNS RDLENGTH', 'dns|DNS TXT length', 'dns|DNS pointer')
SMB = ('smb2|SMB2 NameLength', 'smb2|SMB2 ContextLength', 'smb2|SMB2 NameOffset', 'smb2|SMB2 ContextOffset')
KINDS = ('INTERIOR', 'END', 'NULL')
STAGES = ('source_p', 'width_p', 'endian_equivalence_p', 'base_axis_p', 'valid_mass')
ORDER = ('rope_off', 'rope_hybrid', 'cope_off', 'cope_hybrid', 'tape_off', 'tape_hybrid',
         'sdpa_off', 'sdpa_hybrid', 'four_factor_direct', 'four_factor_sink')
SHORT = {'rope_off': 'RoPE / Off', 'rope_hybrid': 'RoPE / LAPA On',
         'cope_off': 'CoPE / Off', 'cope_hybrid': 'CoPE / LAPA On',
         'tape_off': 'TAPE / Off', 'tape_hybrid': 'TAPE / LAPA On',
         'sdpa_off': 'SDPA / Off', 'sdpa_hybrid': 'SDPA / LAPA On',
         'four_factor_direct': 'Four-factor / Direct', 'four_factor_sink': 'Four-factor / Sink'}
HEATMAPS = (
    ('01_all_methods_numeric_probability', 'by_core_cell', CORE, 'p_true'),
    ('02_all_methods_numeric_nll', 'by_core_cell', CORE, 'nll'),
    ('03_all_methods_numeric_hit1', 'by_core_cell', CORE, 'hit1'),
    ('04_dns_relation_probability', 'by_relation', DNS, 'p_true'),
    ('05_smb2_relation_probability', 'by_relation', SMB, 'p_true'),
    ('06_destination_kind_probability', 'by_target_kind', KINDS, 'p_true'),
)
FIGURES = tuple(item[0] for item in HEATMAPS) + ('07_four_factor_stages', '08_paired_macro_effects', '09_macro_numeric_table')
NUMBER = r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?'
PLAIN_FOUR = re.compile(r'^[-+]?\d+\.\d{4}$')
SCIENTIFIC_TWO = re.compile(r'^\d\.\d{2}e[-+]\d+$')
INTERVAL_FOUR = re.compile(r'^[-+]?\d+\.\d{4} \[[-+]?\d+\.\d{4}, [-+]?\d+\.\d{4}\]$')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def close(left, right, tolerance=1e-10):
    assert math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance), (left, right)


def stat(record):
    """Check stored means/std/CIs against their exact three source seed values."""
    assert {int(seed) for seed in record['seed_values']} == set(SEEDS) and record['n_seeds'] == 3
    values = [record['seed_values'][str(seed)] for seed in SEEDS]
    assert all(math.isfinite(value) for value in values)
    mean, std = statistics.mean(values), statistics.stdev(values)
    margin = T95*std/math.sqrt(3)
    close(record['mean'], mean); close(record['std'], std)
    close(record['ci95'][0], mean-margin); close(record['ci95'][1], mean+margin)
    return mean


def xml_texts(svg):
    return [dict(text=''.join(node.itertext()).strip(), element=node)
            for node in svg.iter() if node.tag.endswith('}text')]


def require_labels(texts, labels):
    available = Counter(item['text'] for item in texts)
    required = Counter(part.strip() for label in labels for part in label.split('\n'))
    assert all(available[key] >= count for key, count in required.items()), ('missing SVG labels', required-available)


def grid_texts(texts, matrix, *, intervals=False, tiny_scientific=False):
    assert not (intervals and tiny_scientific)
    def numeric(text):
        if intervals:
            return INTERVAL_FOUR.fullmatch(text)
        return PLAIN_FOUR.fullmatch(text) or (tiny_scientific and SCIENTIFIC_TWO.fullmatch(text))
    actual = [item for item in texts if numeric(item['text'])]
    def formatted(value):
        if intervals:
            return value
        return f'{value:.2e}' if tiny_scientific and 0 < value < 5e-5 else f'{value:.4f}'
    expected = [formatted(value) for row in matrix for value in row]
    assert [item['text'] for item in actual] == expected, ('SVG numeric annotations differ', len(actual), len(expected))
    nrows, ncols = len(matrix), len(matrix[0])
    assert all(len(row) == ncols for row in matrix)
    xs = [float(item['element'].get('x')) for item in actual]
    ys = [float(item['element'].get('y')) for item in actual]
    column_x = xs[:ncols]
    row_y = [ys[row*ncols] for row in range(nrows)]
    assert all(left < right for left, right in zip(column_x, column_x[1:]))
    assert all(left < right for left, right in zip(row_y, row_y[1:]))
    for row in range(nrows):
        for column in range(ncols):
            index = row*ncols+column
            close(xs[index], column_x[column], tolerance=1e-6)
            close(ys[index], row_y[row], tolerance=1e-6)
    return len(expected)


def check_svg(svg):
    box = [float(value) for value in svg.attrib['viewBox'].split()]
    np.testing.assert_allclose(box, [0., 0., 14.5*72, 8.3*72], atol=1e-4, rtol=0.)
    texts = xml_texts(svg)
    assert texts and not any('\ufffd' in item['text'] for item in texts)
    fonts = []
    for item in texts:
        element = item['element']
        match = re.search(r'font-size:\s*([\d.]+)px', element.get('style', ''))
        if match:
            fonts.append(float(match.group(1)))
        if element.get('x') is not None and element.get('y') is not None:
            x, y = float(element.get('x')), float(element.get('y'))
            assert -2 <= x <= box[2]+2 and -2 <= y <= box[3]+2, item['text']
    assert fonts and min(fonts) >= 8.5
    return texts, dict(view_box=box, text_elements=len(texts), minimum_font_size=min(fonts),
                       note='Baseline positions/font sizes only; text overlap and full glyph clipping require rendered-page review.')


def check_png(path):
    with Image.open(path) as image:
        assert image.format == 'PNG'
        width, height = image.size
        assert abs(width-14.5*220) <= 1 and abs(height-8.3*220) <= 1, image.size
        dpi = image.info.get('dpi')
        if dpi:
            assert all(abs(value-220) < 1 for value in dpi)
        pixels = np.asarray(image.convert('RGB'))
        assert pixels.std() > 10
        foreground = float((pixels.min(-1) < 245).mean())
        assert .02 < foreground < .98
        assert all(np.all(pixels[y, x] >= 245) for y, x in ((0,0), (0,width-1), (height-1,0), (height-1,width-1)))
    return dict(width=width, height=height, dpi=list(dpi) if dpi else None, nonwhite_fraction=foreground,
                note='Canvas resolution/nonblank/margin check; not an OCR or perceptual readability proof.')


def check_errorbar_geometry(svg, effects):
    """Verify actual SVG errorbar and mean-marker geometry, not metadata alone."""
    by_id = {node.get('id'): node for node in svg.iter() if node.get('id')}
    details = []
    for panel, metric_name in enumerate(('p_true', 'nll'), 1):
        axis = by_id['axes_'+str(panel)]
        actual = []
        clip = None
        for group in axis.iter():
            if not group.get('id', '').startswith('LineCollection_'):
                continue
            paths = [node for node in group.iter() if node.tag.endswith('}path')]
            assert len(paths) == 1
            path = paths[0]
            coordinates = [float(value) for value in re.findall(NUMBER, path.attrib['d'])]
            assert len(coordinates) == 4
            close(coordinates[1], coordinates[3], tolerance=1e-6)
            actual.append(coordinates)
            clip_id = re.fullmatch(r'url\(#(.+)\)', path.attrib['clip-path']).group(1)
            rectangle = next(node for node in by_id[clip_id] if node.tag.endswith('}rect'))
            current = {key: float(rectangle.get(key)) for key in ('x', 'y', 'width', 'height')}
            assert clip is None or current == clip
            clip = current
        expected = [row for row in effects if row['metric'] == metric_name]
        assert len(actual) == len(expected) == 8
        endpoints = [point for row in expected for point in row['ci95']]
        padding = max((max(endpoints)-min(endpoints))*.12, .01)
        lower, upper = min(min(endpoints), 0)-padding, max(max(endpoints), 0)+padding
        to_svg = lambda value: clip['x']+(value-lower)/(upper-lower)*clip['width']
        for coordinates, row in zip(actual, expected):
            close(coordinates[0], to_svg(row['ci95'][0]), tolerance=2e-6)
            close(coordinates[2], to_svg(row['ci95'][1]), tolerance=2e-6)
        markers = []
        for use in axis.iter():
            if not use.tag.endswith('}use'):
                continue
            href = use.get('{http://www.w3.org/1999/xlink}href', '')
            definition = by_id.get(href.lstrip('#'))
            if definition is not None and 'C' in definition.get('d', ''):
                markers.append((float(use.get('x')), float(use.get('y'))))
        assert len(markers) == 8, ('mean marker count', panel, len(markers))
        for point, coordinates, row in zip(sorted(markers, key=lambda item: item[1]), actual, expected):
            close(point[0], to_svg(row['mean']), tolerance=2e-6)
            close(point[1], coordinates[1], tolerance=2e-6)
        details.append(dict(metric=metric_name, errorbars_verified=8, mean_markers_verified=8,
                            reconstructed_xlim=[lower, upper]))
    return details


def verify():
    assert (ROOT/'FIGURE_MANIFEST.json').exists(), 'Figures are not complete; no waiting or partial figure approval'
    summary, manifest = read(ROOT/'SUMMARY.json'), read(ROOT/'FIGURE_MANIFEST.json')
    assert read(ROOT/'INDEPENDENT_AUDIT.json')['status'] == 'PASS'
    assert summary['status'] == 'COMPLETE' and summary['new_models'] == 24 and summary['reused_control_models'] == 96
    assert summary['n_fields'] == 347 and summary['n_messages'] == 74
    assert manifest['summary_sha256'] == sha(ROOT/'SUMMARY.json')
    assert summary['method_order'] == list(ORDER)
    methods = summary['methods']
    verified_files = {}
    def verify_hash(path, expected):
        path = Path(path).resolve()
        if path not in verified_files:
            verified_files[path] = sha(path)
        assert verified_files[path] == expected, str(path)
    contract = read(ROOT/'CONTRACT.json')
    assert summary['contract_sha256'] == sha(ROOT/'CONTRACT.json')
    for path, digest in contract['files'].items():
        verify_hash(path, digest)
    for path, digest in summary['files'].items():
        resolved = (ROOT/path).resolve()
        assert ROOT in resolved.parents
        verify_hash(resolved, digest)
    assert [row['name'] for row in manifest['figures']] == list(FIGURES)
    figure_map = {row['name']: row for row in manifest['figures']}
    svg_map, text_map, checks = {}, {}, {}
    for name in FIGURES:
        entry = figure_map[name]
        assert set(entry['files']) == {f'figures/{name}.png', f'figures/{name}.svg'}
        for relative, digest in entry['files'].items():
            verify_hash(ROOT/relative, digest)
        svg = ET.parse(ROOT/'figures'/f'{name}.svg').getroot()
        texts, svg_check = check_svg(svg)
        svg_map[name], text_map[name] = svg, texts
        checks[name] = dict(svg=svg_check, png=check_png(ROOT/'figures'/f'{name}.png'))
    heatmap_cells = 0
    for name, family, columns, metric_name in HEATMAPS:
        details = figure_map[name]['details']
        assert details['metric'] == metric_name and details['family'] == family
        assert details['columns'] == list(columns) and details['rows'] == list(ORDER)
        expected = [[stat(methods[method][family][column]['metrics'][metric_name]) for column in columns] for method in ORDER]
        np.testing.assert_allclose(details['values'], expected, rtol=1e-12, atol=1e-12)
        heatmap_cells += grid_texts(text_map[name], expected, tiny_scientific=True)
        labels = [SHORT[method] for method in ORDER]
        if family == 'by_core_cell':
            for method in ORDER:
                assert [methods[method][family][column]['n_fields'] for column in columns] == list(CORE_COUNTS)
            labels += list(CORE_LABELS)
        elif columns == DNS:
            assert [methods[ORDER[0]][family][column]['n_fields'] for column in columns] == [164,40,25,1,36]
            labels += ['DNS label\n(164)', 'DNS root\n(40)', 'DNS RDLENGTH\n(25)', 'DNS TXT length\n(1)', 'DNS pointer\n(36)']
        elif columns == SMB:
            assert all(methods[ORDER[0]][family][column]['n_fields'] == 15 for column in columns)
            labels += ['NameLength\n(15)', 'ContextLength\n(15)', 'NameOffset\n(15)', 'ContextOffset\n(15)']
        else:
            assert sum(methods[ORDER[0]][family][column]['n_fields'] for column in columns) == 347
            labels += [kind+'\n('+str(methods[ORDER[0]][family][kind]['n_fields'])+')' for kind in KINDS]
        require_labels(text_map[name], labels)
        checks[name]['numeric_cells'] = len(expected)*len(columns)
    assert heatmap_cells == 300
    stage_name = '07_four_factor_stages'
    stage_rows = [(method, core) for method in ORDER[-2:] for core in CORE]
    stage_details = figure_map[stage_name]['details']
    assert stage_details['rows'] == [list(row) for row in stage_rows] and stage_details['columns'] == list(STAGES)
    expected_stage = [[stat(methods[method]['by_core_cell'][core]['stages'][key]) for key in STAGES] for method, core in stage_rows]
    np.testing.assert_allclose(stage_details['values'], expected_stage, rtol=1e-12, atol=1e-12)
    stage_cells = grid_texts(text_map[stage_name], expected_stage)
    assert stage_cells == 60
    require_labels(text_map[stage_name], ['Source p', 'Width p\n| true source', 'Endian p (equiv.)\n| true source',
                                        'Base p\n| true source', 'Valid mass'] +
                   [('Direct' if method.endswith('direct') else 'Sink')+' / '+core.replace('|',' ').replace('smb2','SMB2').replace('dns','DNS')
                    for method, core in stage_rows])
    checks[stage_name]['numeric_cells'] = stage_cells
    effect_name = '08_paired_macro_effects'
    pairs = [(new, old) for new in ORDER[-2:] for old in ORDER if old.endswith('hybrid')]
    expected_effects = []
    for metric_name in ('p_true', 'nll'):
        for new, old in pairs:
            left = methods[new]['overall_protocol_macro']['metrics'][metric_name]['seed_values']
            right = methods[old]['overall_protocol_macro']['metrics'][metric_name]['seed_values']
            values = [(left[str(seed)]-right[str(seed)])*(1 if metric_name == 'p_true' else -1) for seed in SEEDS]
            mean, margin = statistics.mean(values), T95*statistics.stdev(values)/math.sqrt(3)
            expected_effects.append(dict(new=new, old=old, metric=metric_name, mean=mean, ci95=[mean-margin, mean+margin]))
    stored_effects = figure_map[effect_name]['details']['effects']
    assert len(stored_effects) == len(expected_effects) == 16
    for stored, expected in zip(stored_effects, expected_effects):
        assert all(stored[key] == expected[key] for key in ('new', 'old', 'metric'))
        close(stored['mean'], expected['mean'])
        np.testing.assert_allclose(stored['ci95'], expected['ci95'], rtol=1e-12, atol=1e-12)
        key = 'delta_p_true' if stored['metric'] == 'p_true' else 'nll_gain'
        node = summary['contrasts'][stored['new']+'_minus_'+stored['old']]['overall_protocol_macro']['metrics'][key]
        close(node['mean'], expected['mean'])
        np.testing.assert_allclose(node['ci95'], expected['ci95'], rtol=1e-12, atol=1e-12)
    checks[effect_name]['vector_errorbars'] = check_errorbar_geometry(svg_map[effect_name], expected_effects)
    require_labels(text_map[effect_name], [('Direct' if new.endswith('direct') else 'Sink')+' vs '+SHORT[old].replace(' / LAPA On',' Hybrid')
                                         for new, old in pairs])
    macro_name = '09_macro_numeric_table'
    cells = []
    for method in ORDER:
        row = [SHORT[method]]
        for metric_name in ('p_true', 'nll', 'hit1'):
            node = methods[method]['overall_protocol_macro']['metrics'][metric_name]
            stat(node)
            row.append(f'{node["mean"]:.4f} [{node["ci95"][0]:.4f}, {node["ci95"][1]:.4f}]')
        cells.append(row)
    assert figure_map[macro_name]['details']['rows'] == list(ORDER)
    assert figure_map[macro_name]['details']['cells'] == cells
    table_cells = grid_texts(text_map[macro_name], [row[1:] for row in cells], intervals=True)
    assert table_cells == 30
    require_labels(text_map[macro_name], [SHORT[method] for method in ORDER] +
                   ['Model', 'p(target) [95% CI]', 'NLL [95% CI]', 'Hit@1 [95% CI]'])
    checks[macro_name]['numeric_interval_cells'] = table_cells
    pdf = manifest['pdf']
    pdf_path = (ROOT/pdf['path']).resolve()
    assert (ROOT/'output/pdf').resolve() in pdf_path.parents
    verify_hash(pdf_path, pdf['sha256'])
    reader = PdfReader(pdf_path)
    assert pdf['pages'] == len(reader.pages) == 9
    sizes = []
    for page in reader.pages:
        size = [float(page.mediabox.width), float(page.mediabox.height)]
        np.testing.assert_allclose(size, [14.5*72, 8.3*72], atol=.01, rtol=0.)
        sizes.append(size)
    result = dict(status='PASS', time=datetime.now(timezone.utc).isoformat(),
                  verifier_source_sha256=sha(__file__), summary_sha256=sha(ROOT/'SUMMARY.json'),
                  figure_manifest_sha256=sha(ROOT/'FIGURE_MANIFEST.json'),
                  figures=9, heatmap_numeric_cells=300, factor_stage_cells=60, macro_interval_cells=30,
                  total_numeric_cells=390, paired_effects=16, paired_svg_errorbars=16, paired_svg_mean_markers=16,
                  pdf_pages=9, pdf_page_sizes=sizes, file_hashes_verified=len(verified_files), checks=checks,
                  no_figures_or_pdf_modified=True, full_rendered_visual_review_performed=False,
                  scope='Exact plotted cell text and matrix mapping, field-count labels, seed-derived statistics and '
                        'paired vector geometry, SVG text anchors/font sizes, PNG canvas/nonblank checks, PDF page metadata. '
                        'Root must separately inspect rendered pages for perceptual layout and legibility.')
    output = ROOT/'FIGURE_AUDIT.json'
    if output.exists():
        snapshot = ROOT/'audit_snapshots'/f'FIGURE_AUDIT_{sha(output)[:16]}.json'
        snapshot.parent.mkdir(exist_ok=True)
        if not snapshot.exists():
            snapshot.write_bytes(output.read_bytes())
    temporary = output.with_name(output.name+'.tmp')
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    temporary.replace(output)
    print(json.dumps({key: value for key, value in result.items() if key not in ('checks', 'pdf_page_sizes')}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    verify()
