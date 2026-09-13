"""Compact paper-facing tables, separate from exhaustive audit supplements.

Call write_paper_tables() only after the final audited SUMMARY exists.  The
three tables have 16 method-role rows and six protocol-semantic columns.
Neither model selection nor numeric aggregation is performed here.
"""
import math
from pathlib import Path

from common17 import ROOT, BACKBONES, read, sha, write, now


ROLES = ('off', 'hybrid', 'p_champion', 'nll_champion')
ROLE_LABELS = {'off': 'Off', 'hybrid': 'Hybrid', 'p_champion': 'P-selected', 'nll_champion': 'NLL-selected'}
BACKBONE_LABELS = {'rope': 'RoPE', 'cope': 'CoPE', 'tape': 'TAPE', 'sdpa': 'SDPA'}
COHORTS = (('dns', 'LENGTH'), ('dns', 'POINTER'), ('modbus', 'LENGTH'),
           ('tls', 'LENGTH'), ('smb2', 'LENGTH'), ('smb2', 'OFFSET'))
PROTOCOL_LABELS = {'dns': 'DNS', 'modbus': 'Modbus', 'tls': 'TLS', 'smb2': 'SMB2'}
TABLES = (
    ('p_true', 'paper_p_target.tex', 'ptrue', r'Probability assigned to the correct destination, $p(y)$ (higher is better)'),
    ('hit1', 'paper_hit1.tex', 'hit1', r'Destination Hit@1 (higher is better)'),
    ('nll', 'paper_nll.tex', 'nll', r'Destination negative log-likelihood, in nats (lower is better)'),
)


def numeric_cell(value):
    """Preserve real zeros and show nonzero values that would round to zero."""
    if value is None:
        return r'\mathrm{N/A}'
    assert math.isfinite(value)
    if value != 0 and abs(value) < .00005:
        mantissa, exponent = f'{value:.1e}'.split('e')
        return mantissa + r'\!\times\!10^{' + str(int(exponent)) + '}'
    return f'{value:.4f}'


def _write_new_or_identical(path, content):
    path = Path(path).resolve()
    assert ROOT in path.parents
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_text() == content, ('preserve changed existing paper artifact', str(path))
        return
    with path.open('x') as handle:
        handle.write(content)


def write_paper_tables():
    assert (ROOT/'GRID_COMPLETE.json').exists()
    summary = read(ROOT/'SUMMARY.json')
    assert summary['audit']['status'] == 'PASS'
    assert summary['audit']['grid_complete_sha256'] == sha(ROOT/'GRID_COMPLETE.json')
    assert summary['audit']['selection_sha256'] == sha(ROOT/'SELECTION.json')
    counts = [summary['final'][p]['by_backbone'][BACKBONES[0]]['roles']['off']['by_semantic'][semantic]['n_fields']
              for p, semantic in COHORTS]
    headers = [r'\shortstack{' + PROTOCOL_LABELS[p] + r'\\' + semantic.lower() +
               r'\\($n=' + str(count) + r'$)}' for (p, semantic), count in zip(COHORTS, counts)]
    manifest = []
    for metric, filename, label, description in TABLES:
        lines = [
            '% Generated exclusively from the audited v17 SUMMARY.json.',
            '% Requires booktabs. Values are seed means; full CIs remain supplementary.',
            r'\begin{table*}[tb]', r'\centering', r'\small',
            r'\setlength{\tabcolsep}{5pt}',
            r'\caption{' + description + '. Entries are raw field means averaged over three training seeds. '
            'P-selected and NLL-selected formulas vary by held-out target and are selected using only the three source protocols, '
            'with balanced source-validation objectives. Selection uses a TAPE anchor; it is not repeated for each backbone. '
            r'Identical formula roles reuse the same runs. A $\dagger$ marks a canonical CNN/GRU result reused across backbone panels. '
            r'Full seed values and 95\% seed-variation intervals are supplementary.}',
            r'\label{tab:lapa-v17-' + label + '}',
            r'\begin{tabular}{l*{6}{r}}', r'\toprule',
            'Backbone / role & ' + ' & '.join(headers) + r' \\', r'\midrule',
        ]
        rows, actual_values = [], []
        for backbone_index, backbone in enumerate(BACKBONES):
            if backbone_index:
                lines.append(r'\addlinespace[3pt]')
            for role in ROLES:
                display, values, metadata = [], [], []
                for protocol, semantic in COHORTS:
                    result = summary['final'][protocol]['by_backbone'][backbone]['roles'][role]
                    stat = result['by_semantic'][semantic]['metrics'][metric]
                    value = None if stat is None else float(stat['mean'])
                    assert value is not None, (metric, protocol, backbone, role, 'all endpoint cohorts must be supported')
                    canonical = result['actual_backbone'] == 'none'
                    display.append('$' + numeric_cell(value) + (r'^{\dagger}' if canonical else '') + '$')
                    values.append(value)
                    metadata.append(dict(protocol=protocol, semantic=semantic, formula=result['formula'],
                                         actual_backbone=result['actual_backbone'], alias_of=result.get('alias_of')))
                row_label = BACKBONE_LABELS[backbone] + ' / ' + ROLE_LABELS[role]
                lines.append(row_label + ' & ' + ' & '.join(display) + r' \\')
                rows.append(dict(label=row_label, backbone=backbone, role=role, formatted_cells=display, metadata=metadata))
                actual_values.append(values)
        lines.extend([r'\bottomrule', r'\end{tabular}', r'\end{table*}', ''])
        assert len(rows) == 16 and all(len(row) == 6 for row in actual_values)
        path = ROOT/'tables'/filename
        _write_new_or_identical(path, '\n'.join(lines))
        manifest.append(dict(path=str(path), sha256=sha(path), metric=metric, shape=[16, 6],
                             columns=[dict(protocol=p, semantic=s, n_fields=n) for (p, s), n in zip(COHORTS, counts)],
                             rows=rows, values=actual_values,
                             numeric_cells=96, exact_zero_cells=sum(value == 0 for row in actual_values for value in row),
                             tiny_nonzero_cells=sum(0 < abs(value) < .00005 for row in actual_values for value in row)))
    readme = """# v17 tables: compact main-paper tables and full audit supplements

Use these three compact tables for the main paper:

- `paper_p_target.tex`: final correct-destination probability.
- `paper_hit1.tex`: final destination Hit@1.
- `paper_nll.tex`: final destination NLL in nats.

Each is a complete `table*` environment with `\\small`, `booktabs`, 16 rows
(RoPE/CoPE/TAPE/SDPA × Off/Hybrid/P-selected/NLL-selected), and six result
columns: DNS length, DNS pointer, Modbus length, TLS length, SMB2 length,
SMB2 offset. No provenance columns expand these compact tables.

Add `\\usepackage{booktabs}` to the paper preamble. Standard LaTeX
`\\shortstack` handles multi-line headers; no `makecell` dependency is needed.
For example, include `\\input{path/to/tables/paper_p_target.tex}` where the
main-paper table should float. In a one-column document, replace `table*`
with `table` if the venue template requires it. The generated originals
remain unchanged; adapt a copy in the manuscript tree.

Numbers are raw field means averaged across the three final training seeds,
not balanced selection scores. Meaningful tiny nonzero values use scientific
notation rather than appearing as zero. Genuine zero remains `0.0000`.
Probabilities and Hit@1 are proportions, not percentages.

P-selected and NLL-selected can choose different formulas for different
held-out targets. Both are selected entirely inside source protocols using
the frozen TAPE-anchored selection procedure. These are selection-procedure
roles, not two globally fixed new architectures. Backbone names refer to the
native_v4_compact implementations used throughout this study, not a claim of
full original-paper model reproduction.

If a selected CNN/GRU uses no Transformer backbone, its cell has a dagger.
The same canonical run is reused in the four display panels, not trained
again as four separate backbone combinations. When selected roles coincide
with Hybrid or with each other, their values alias the same sealed runs.

The other `.tex` files and `../TABLES.md` preserve the exhaustive audit,
full per-seed 95% Student-t intervals, relation/target-kind details, F1,
source/program stages, source-only candidate scores, and full validation
matrices. Those long tables are supplementary/provenance material; they are
not intended to be dropped wholesale into the main-paper two-column layout.
Intervals quantify training-seed variation only, not independent capture or
protocol uncertainty. See `../DATA_LIMITATIONS.md` for capture overlap,
END shortcuts, sample sizes, and supervision coverage.

`../PAPER_TABLES_MANIFEST.json` records the exact unrounded values, displayed
strings, formula aliases, cohort sizes, file hashes, and SUMMARY provenance.
Generate with the experiment environment's Python and `../paper_tables17.py`
only after the audited SUMMARY and GRID_COMPLETE artifacts exist. The writer
accepts an identical rerun but refuses to overwrite changed table contents.
"""
    readme_path = ROOT/'tables/README.md'
    _write_new_or_identical(readme_path, readme)
    payload = dict(schema='lapa-v17-compact-paper-tables-1', time=now(),
                   summary_sha256=sha(ROOT/'SUMMARY.json'), writer_code_sha256=sha(__file__),
                   tables=manifest, total_tables=3, total_numeric_cells=288,
                   readme=dict(path=str(readme_path), sha256=sha(readme_path)))
    if (ROOT/'PAPER_TABLES_MANIFEST.json').exists():
        previous = read(ROOT/'PAPER_TABLES_MANIFEST.json')
        for key in ('summary_sha256', 'writer_code_sha256', 'tables', 'total_tables', 'total_numeric_cells', 'readme'):
            assert previous[key] == payload[key], ('existing paper table manifest changed', key)
        return previous
    write(ROOT/'PAPER_TABLES_MANIFEST.json', payload)
    print('Created three compact 16 x 6 paper tables (288 numeric cells).', flush=True)
    return payload


if __name__ == '__main__':
    write_paper_tables()
