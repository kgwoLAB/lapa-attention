"""Publication-oriented numeric figures from the sealed v17 aggregation only."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

from common17 import ROOT, PROTOCOLS, BACKBONES, VARIANTS, read, sha, write, now

ROLES = ('off', 'hybrid', 'p_champion', 'nll_champion')
ROLE_NAMES = ('Off', 'Hybrid', 'P-selected', 'NLL-selected')
BNAME = dict(rope='RoPE', cope='CoPE', tape='TAPE', sdpa='SDPA')
PNAME = dict(dns='DNS', modbus='Modbus', tls='TLS', smb2='SMB2')
COHORTS = [('dns', 'LENGTH'), ('dns', 'POINTER'), ('modbus', 'LENGTH'),
           ('tls', 'LENGTH'), ('smb2', 'LENGTH'), ('smb2', 'OFFSET')]
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                     'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
                     'axes.spines.top': False, 'axes.spines.right': False})


def fmt(value):
    if not np.isfinite(value):
        return 'N/A'
    if value != 0 and abs(value) < .00005:
        return f'{value:.1e}'
    return f'{value:.4f}'


class Figures:
    def __init__(self, summary):
        self.s = summary
        self.directory = ROOT/'figures'
        self.directory.mkdir(exist_ok=True)
        self.output = ROOT/'output/pdf'
        self.output.mkdir(parents=True, exist_ok=True)
        self.pdf_path = self.output/'LAPA_formula_search_v17.pdf'
        self.pdf = PdfPages(self.pdf_path, metadata={
            'Title': 'LAPA formula search v17: real-protocol transfer',
            'Subject': 'Exploratory sealed formula search; training-seed variation',
            'Author': 'LAPA research workspace'})
        self.manifest = []

    def save(self, fig, name, data):
        paths = []
        for suffix in ('png', 'pdf', 'svg'):
            path = self.directory/(name+'.'+suffix)
            fig.savefig(path, dpi=240, facecolor='white')
            paths.append(dict(path=str(path), sha256=sha(path)))
        self.pdf.savefig(fig, facecolor='white')
        plt.close(fig)
        self.manifest.append(dict(name=name, files=paths, **data))

    def heatmap(self, name, title, values, row_labels, col_labels, unit,
                footer, probability=False, low_good=False, dividers=()):
        values = np.asarray(values, float)
        assert values.shape == (len(row_labels), len(col_labels))
        finite = values[np.isfinite(values)]
        assert finite.size
        height = max(7.8, 3.8+.36*len(row_labels))
        fig, ax = plt.subplots(figsize=(14, height))
        fig.subplots_adjust(left=.265, right=.92, top=.80, bottom=.23)
        cmap = plt.get_cmap('YlGnBu_r' if low_good else 'YlGnBu').copy()
        cmap.set_bad('#e4e4e4')
        lo, hi = (0., 1.) if probability else (float(finite.min()), float(finite.max()))
        if hi == lo:
            hi = lo+1
        im = ax.imshow(np.ma.masked_invalid(values), aspect='auto', cmap=cmap, vmin=lo, vmax=hi)
        ax.set_xticks(range(len(col_labels)), col_labels, fontsize=11)
        ax.xaxis.tick_top()
        ax.tick_params(axis='x', length=0, pad=10)
        ax.set_yticks(range(len(row_labels)), row_labels, fontsize=11)
        ax.tick_params(axis='y', length=0, pad=9)
        for spine in ax.spines.values():
            spine.set_visible(False)
        for i, row in enumerate(values):
            for j, value in enumerate(row):
                rgba = cmap(im.norm(value)) if np.isfinite(value) else (.9, .9, .9, 1)
                luminance = .2126*rgba[0]+.7152*rgba[1]+.0722*rgba[2]
                ax.text(j, i, fmt(value), ha='center', va='center', fontsize=10.5,
                        color='white' if luminance < .46 else '#111111')
        for boundary in dividers:
            ax.axhline(boundary-.5, color='white', linewidth=2.5)
        cb = fig.colorbar(im, ax=ax, fraction=.028, pad=.025)
        cb.set_label(unit)
        fig.text(.06, .95, title, fontsize=18, weight='bold', va='top')
        fig.text(.06, .90, unit, fontsize=12, va='top')
        fig.text(.06, .15, footer, fontsize=10, va='top', linespacing=1.55)
        self.save(fig, name, dict(kind='numeric_heatmap', rows=row_labels, columns=col_labels,
                  values=[[float(v) if np.isfinite(v) else None for v in row] for row in values],
                  numeric_cells=int(np.isfinite(values).sum()), missing_cells=int(np.isnan(values).sum()),
                  unit=unit))

    def search(self):
        for key, name, title, unit, probability in (
            ('balanced_p', '01_screen_balanced_p', 'All 30 formulas: source-only screening',
             'Balanced probability of the correct destination (higher is better)', True),
            ('balanced_log_gain', '02_screen_log_gain', 'All 30 formulas: source-only screening',
             'Balanced log gain over uniform, nat (higher is better)', False)):
            lookup = {p: {r['variant']: r['scores'][key] for r in self.s['screen']['outer_candidates'][p]}
                      for p in PROTOCOLS}
            values = [[lookup[p][v] for p in PROTOCOLS] for v in VARIANTS]
            self.heatmap(name, title, values, list(VARIANTS),
                ['Hold out\n'+PNAME[p] for p in PROTOCOLS], unit,
                '120 updates; one seed; TAPE anchor (CNN/GRU: no Transformer backbone).\n'
                'Each column uses only inner validation within its three source protocols; the held-out target is excluded.\n'
                'These are selection-stage scores, not final test results.', probability)

    def selection(self):
        fig, ax = plt.subplots(figsize=(14, 8.5))
        ax.axis('off')
        records, body = [], []
        for p in PROTOCOLS:
            choice = self.s['selection']['choices'][p]
            for candidate in choice['candidates']:
                v = candidate['variant']
                tags = []
                if v == choice['p_champion']: tags.append('P')
                if v == choice['nll_champion']: tags.append('NLL')
                row = [PNAME[p], v, fmt(candidate['scores']['balanced_p']),
                       fmt(candidate['scores']['balanced_log_gain']), ' + '.join(tags) or '-']
                body.append(row)
                records.append(dict(target=p, **candidate, selected_for=tags))
        table = ax.table(cellText=body, colLabels=['Held-out target', 'Refined formula', 'Balanced p',
                         'Log gain (nat)', 'Selected role'], cellLoc='left', loc='center',
                         colWidths=[.15, .33, .16, .20, .16])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 1.65)
        for (i, j), cell in table.get_celld().items():
            cell.set_edgecolor('#d7dce1')
            cell.set_linewidth(.4)
            cell.set_facecolor('#e8eef5' if i == 0 else ('#f4f7fa' if ((i-1)//4)%2 else 'white'))
        fig.subplots_adjust(left=.05, right=.97, top=.84, bottom=.15)
        fig.text(.05, .94, 'Source-only refinement and frozen formula selection', fontsize=18, weight='bold')
        fig.text(.05, .07, '400 updates from scratch; two fresh seeds; four promoted formulas per outer target.\n'
                 'P and NLL are selected independently. Selection is anchored to TAPE, not retuned per final backbone.',
                 fontsize=11, linespacing=1.5)
        self.save(fig, '03_refinement_selection', dict(kind='selection_table', records=records))

    def final_nodes(self, group='by_semantic', columns=None):
        columns = columns or COHORTS
        nodes, labels = [], []
        for backbone in BACKBONES:
            for role, label in zip(ROLES, ROLE_NAMES):
                nodes.append([self.s['final'][p]['by_backbone'][backbone]['roles'][role][group][key]
                              for p, key in columns])
                labels.append(BNAME[backbone]+' / '+label)
        return nodes, labels

    def numeric(self):
        nodes, labels = self.final_nodes()
        cols = [PNAME[p]+'\n'+semantic.lower()+'\n(n='+str(nodes[0][j]['n_fields'])+')'
                for j, (p, semantic) in enumerate(COHORTS)]
        note = ('3 source protocols -> 1 held-out target; three seeds; 600 updates. Shown: raw field means, not balanced selection scores.\n'
                'P-selected / NLL-selected formulas vary by target (see selection table); no target-based reselection.\n'
                'Any CNN/GRU champion is one canonical model reused across backbone panels. Tiny nonzero values use scientific notation.')
        for metric, name, title, unit in (
            ('p_true', '04_final_numeric_p', 'Final probability assigned to the correct destination', 'Mean p(target), higher is better'),
            ('hit1', '05_final_numeric_hit1', 'Final destination retrieval: Hit@1', 'Mean Hit@1, higher is better'),
            ('nll', '06_final_numeric_nll', 'Final destination negative log-likelihood', 'Mean NLL, nat; lower is better')):
            values = [[cell['metrics'][metric]['mean'] for cell in row] for row in nodes]
            row_labels = labels.copy()
            if metric != 'nll':
                for sanity_name, display in [('always_end', 'Always END'), ('always_null', 'Always NULL'), ('uniform', 'Uniform')]:
                    values.append([self.s['final'][p]['sanity']['by_semantic'][semantic]['models'][sanity_name][metric]
                                   for p, semantic in COHORTS])
                    row_labels.append(display+' (sanity only)')
            footer = note + ('\nUniform Hit@1 uses deterministic argmax at byte 0, not sampled-hit expectation.' if metric == 'hit1' else '')
            self.heatmap(name, title, values, row_labels, cols, unit, footer,
                         probability=metric != 'nll', low_good=metric == 'nll', dividers=[4,8,12,16])
        for protocol, name in [('dns', '07_dns_relations_p'), ('smb2', '08_smb2_relations_p')]:
            relations = list(self.s['final'][protocol]['by_backbone']['tape']['roles']['off']['by_relation'])
            detail, detail_labels = self.final_nodes('by_relation', [(protocol, r) for r in relations])
            values = [[cell['metrics']['p_true']['mean'] for cell in row] for row in detail]
            cols = [r.replace('DNS ', 'DNS\n').replace('SMB2 ', 'SMB2\n')
                    +'\n(n='+str(detail[0][i]['n_fields'])+')' for i,r in enumerate(relations)]
            self.heatmap(name, PNAME[protocol]+': separate address relations', values, detail_labels, cols,
                         'Mean p(target), higher is better', note, probability=True, dividers=[4,8,12])
        for metric, name, title in [('source_p', '10_source_stage', 'Source localization probability'),
                                    ('program_p', '11_program_stage', 'Program probability conditioned on the true source')]:
            values = [[np.nan if cell['stages'][metric] is None else cell['stages'][metric]['mean'] for cell in row]
                      for i, row in enumerate(nodes) if i%4 != 0]
            row_labels = [label for i,label in enumerate(labels) if i%4 != 0]
            self.heatmap(name, title, values, row_labels,
                [PNAME[p]+'\n'+s.lower() for p,s in COHORTS], 'Mean diagnostic probability, higher is better',
                'Gold source is used only for post-seal diagnostics, never as a model input.\n'
                'Program correctness uses the labeled program; alternative programs can have the same executed destination.\n'
                'Pre-validity head probabilities, not normalized route posteriors. Off heads are untrained and omitted; three-seed means.',
                probability=True, dividers=[3,6,9])
        values = []
        for b in BACKBONES:
            for role in ROLES:
                row = []
                for p,s in COHORTS:
                    field = self.s['final'][p]['by_backbone'][b]['roles'][role]['field_f1']
                    row.append(np.nan if field is None else field['by_semantic'][s]['mean'])
                values.append(row)
        self.heatmap('12_exact_field_f1', 'Exact typed-field discovery: F1', values, labels,
            [PNAME[p]+'\n'+s.lower() for p,s in COHORTS], 'Mean exact typed-span F1, higher is better',
            'Threshold chosen on source development data only; three-seed means.\n'
            'Off has endpoint NLL only: its untrained field head is N/A, not a measured zero.\n'
            'A destination probability is not a field-discovery F1; these metrics answer different questions.',
            probability=True, dividers=[4,8,12])

    def gains(self):
        fig, axes = plt.subplots(1, 2, figsize=(14, 7.5), sharey=True)
        fig.subplots_adjust(left=.20, right=.97, top=.82, bottom=.31, wspace=.24)
        labels, records = [], []
        contrasts = [('p_champion_minus_hybrid', 'P-selected - Hybrid'),
                     ('nll_champion_minus_hybrid', 'NLL-selected - Hybrid')]
        for backbone in BACKBONES:
            for contrast, name in contrasts:
                labels.append(BNAME[backbone]+' / '+name.replace(' - Hybrid', ''))
                node = self.s['macro']['by_backbone'][backbone]['all_fields']['comparisons'][contrast]
                records.append(dict(backbone=backbone, contrast=contrast, gains=node['gains']))
        for ax, key, title in zip(axes, ('p_true_gain', 'nll_gain'),
                                  ('Probability gain over Hybrid', 'NLL reduction from Hybrid (nat)')):
            ax.axvline(0, color='#555555', linewidth=1)
            for i, row in enumerate(records):
                st = row['gains'][key]
                color = '#0072b2' if i%2 == 0 else '#d55e00'
                ax.errorbar(st['mean'], i, xerr=[[st['mean']-st['ci95'][0]], [st['ci95'][1]-st['mean']]],
                            fmt='o' if i%2 == 0 else 's', color=color, capsize=4, markersize=6)
            ax.set_title(title, fontsize=12)
            ax.set_xlabel('Positive favors the selected formula')
            ax.grid(axis='x', alpha=.18)
        axes[0].set_yticks(range(len(labels)), labels)
        axes[0].invert_yaxis()
        fig.text(.05, .94, 'Paired changes: equal-protocol macro average', fontsize=18, weight='bold')
        fig.text(.05, .16, 'Points: paired three-seed means. Whiskers: un-clipped 95% Student-t intervals (df=2).\n'
                 'Each protocol receives equal weight; fields are averaged within protocol.\n'
                 'Intervals describe training-seed variability, not uncertainty over captures or unseen protocols.\n'
                 'Blue circles: P-selected; orange squares: NLL-selected. Selection is source-only and TAPE-anchored.', fontsize=11, linespacing=1.5, va='top')
        self.save(fig, '09_paired_macro_gains', dict(kind='paired_errorbars', records=records))

    def close(self):
        self.pdf.close()
        write(ROOT/'FIGURE_MANIFEST.json', dict(time=now(), summary_sha256=sha(ROOT/'SUMMARY.json'),
              plotting_code_sha256=sha(__file__), figures=self.manifest, pages=len(self.manifest),
              pdf=dict(path=str(self.pdf_path), sha256=sha(self.pdf_path))), replace=True)


def main():
    assert (ROOT/'GRID_COMPLETE.json').exists()
    summary = read(ROOT/'SUMMARY.json')
    assert summary['audit']['status'] == 'PASS'
    assert summary['audit']['grid_complete_sha256'] == sha(ROOT/'GRID_COMPLETE.json')
    figures = Figures(summary)
    figures.search()
    figures.selection()
    figures.numeric()
    figures.gains()
    figures.close()
    print(json.dumps({'figures': len(figures.manifest), 'pdf': str(figures.pdf_path)}))


if __name__ == '__main__':
    main()
