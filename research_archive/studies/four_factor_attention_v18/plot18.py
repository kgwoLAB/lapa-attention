"""Publication-ready numeric comparisons from frozen complete-run summaries.

Exports numeric PNG/SVG figures and one vector PDF collection; no model fitting.
"""
import math
import statistics
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from common18 import ROOT,PROTOCOLS,SEEDS,MODES,now,sha,read,write

CORE = ('dns|LENGTH','dns|POINTER','modbus|LENGTH','tls|LENGTH','smb2|LENGTH','smb2|OFFSET')
CORE_LABELS = ('DNS\nlength (230)','DNS\npointer (36)','Modbus\nlength (6)',
               'TLS\nlength (15)','SMB2\nlength (30)','SMB2\noffset (30)')
SHORT = {'rope_off':'RoPE / Off','rope_hybrid':'RoPE / LAPA On',
         'cope_off':'CoPE / Off','cope_hybrid':'CoPE / LAPA On',
         'tape_off':'TAPE / Off','tape_hybrid':'TAPE / LAPA On',
         'sdpa_off':'SDPA / Off','sdpa_hybrid':'SDPA / LAPA On',
         'four_factor_direct':'Four-factor / Direct','four_factor_sink':'Four-factor / Sink'}
FOOT = ('3-source training -> held-out protocol | 600 updates | mean of 3 seeds | '
        '74 historical real-capture messages / 347 fields')


def main():
    data = read(ROOT/'SUMMARY.json')
    assert read(ROOT/'INDEPENDENT_AUDIT.json')['status']=='PASS'
    order = data['method_order']; methods = data['methods']
    assert len(order)==10 and set(order)==set(SHORT)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':16,
        'axes.labelsize':11,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
        'savefig.facecolor':'white'})
    out = ROOT/'figures'; out.mkdir(exist_ok=True)
    pdfpath = ROOT/'output/pdf/LAPA_four_factor_attention_v18.pdf'
    pdfpath.parent.mkdir(parents=True,exist_ok=True)
    manifest = dict(time=now(),summary_sha256=sha(ROOT/'SUMMARY.json'),figures=[],
                    uncertainty='Unclipped t95(df=2); training-seed variation only')

    def finish(fig,name,details=None):
        fig.text(.02,.025,FOOT,fontsize=9,color='#444444')
        fig.canvas.draw()
        for text in fig.findobj(matplotlib.text.Text):
            if not text.get_visible() or not text.get_text(): continue
            bbox=text.get_window_extent(fig.canvas.get_renderer())
            # Tick marks outside axes can be intentional; page clipping cannot.
            assert bbox.x0 >= -2 and bbox.y0 >= -2 and bbox.x1 <= fig.bbox.width+2 and bbox.y1 <= fig.bbox.height+2, (name,text.get_text(),bbox)
        for ext in ('png','svg'):
            fig.savefig(out/f'{name}.{ext}',dpi=220)
        pdf.savefig(fig)
        manifest['figures'].append(dict(name=name,details=details or {},
            files={str((out/f'{name}.{e}').relative_to(ROOT)):sha(out/f'{name}.{e}') for e in ('png','svg')}))
        plt.close(fig)

    def heatmap(name,title,columns,labels,metric='p_true',family='by_core_cell',maximum=None):
        cohorts = [[methods[m][family][c] for c in columns] for m in order]
        values = np.array([[c['metrics'][metric]['mean'] for c in row] for row in cohorts])
        assert np.isfinite(values).all()
        maximum = maximum if maximum is not None else (float(values.max()) if metric=='nll' else 1.)
        fig,ax = plt.subplots(figsize=(14.5,8.3))
        fig.subplots_adjust(left=.23,right=.91,top=.78,bottom=.12)
        cmap = 'magma_r' if metric=='nll' else 'YlGnBu'
        im=ax.imshow(values,vmin=0,vmax=maximum,cmap=cmap,aspect='auto')
        ax.set_xticks(range(len(columns)),labels,fontsize=11)
        ax.xaxis.tick_top();ax.tick_params(axis='both',length=0,pad=8)
        ax.set_yticks(range(len(order)),[SHORT[m] for m in order])
        ax.set_xticks(np.arange(-.5,len(columns),1),minor=True)
        ax.set_yticks(np.arange(-.5,len(order),1),minor=True)
        ax.grid(which='minor',color='white',linewidth=1)
        ax.tick_params(which='minor',bottom=False,left=False)
        for y,row in enumerate(values):
            for x,value in enumerate(row):
                rgba=im.cmap(im.norm(value)); light=.2126*rgba[0]+.7152*rgba[1]+.0722*rgba[2]
                label=f'{value:.2e}' if 0<value<5e-5 else f'{value:.4f}'
                ax.text(x,y,label,ha='center',va='center',color='black' if light>.56 else 'white',fontsize=12)
        ax.axhline(7.5,color='#222222',linewidth=2)
        fig.suptitle(title,y=.965,fontsize=18)
        fig.text(.5,.91,'New rows use Source / Width / Endian / Base in every layer; no QK similarity. Learned V is retained.',ha='center',fontsize=10)
        cax=fig.add_axes([.93,.16,.014,.57]);bar=fig.colorbar(im,cax=cax)
        bar.set_label('NLL (nat; lower is better)' if metric=='nll' else 'Hit@1 (higher is better)' if metric=='hit1' else 'p(target) (higher is better)')
        finish(fig,name,dict(metric=metric,family=family,columns=list(columns),rows=order,values=values.tolist()))

    with PdfPages(pdfpath) as pdf:
        heatmap('01_all_methods_numeric_probability','Correct-destination probability | same held-out fields',CORE,CORE_LABELS)
        heatmap('02_all_methods_numeric_nll','Correct-destination NLL | same held-out fields',CORE,CORE_LABELS,metric='nll')
        heatmap('03_all_methods_numeric_hit1','Correct-destination Hit@1 | same held-out fields',CORE,CORE_LABELS,metric='hit1')
        dns = ('dns|DNS label','dns|DNS root terminator','dns|DNS RDLENGTH','dns|DNS TXT length','dns|DNS pointer')
        heatmap('04_dns_relation_probability','DNS detail | length subtypes and pointer',dns,
            ('DNS label\n(164)','DNS root\n(40)','DNS RDLENGTH\n(25)','DNS TXT length\n(1)','DNS pointer\n(36)'),family='by_relation')
        smb=('smb2|SMB2 NameLength','smb2|SMB2 ContextLength','smb2|SMB2 NameOffset','smb2|SMB2 ContextOffset')
        heatmap('05_smb2_relation_probability','SMB2 detail | length and offset',smb,
            ('NameLength\n(15)','ContextLength\n(15)','NameOffset\n(15)','ContextOffset\n(15)'),family='by_relation')
        # Endpoint strata are field means, not equal-protocol macro means.
        kinds=('INTERIOR','END','NULL')
        counts=[methods[order[0]]['by_target_kind'][k]['n_fields'] for k in kinds]
        heatmap('06_destination_kind_probability','Endpoint strata | existing fields only',kinds,
            [f'{k}\n({n})' for k,n in zip(kinds,counts)],family='by_target_kind')

        stage_names=('source_p','width_p','endian_equivalence_p','base_axis_p','valid_mass')
        stagerows=[(m,c) for m in order[-2:] for c in CORE]
        values=np.array([[methods[m]['by_core_cell'][c]['stages'][s]['mean'] for s in stage_names] for m,c in stagerows])
        fig,ax=plt.subplots(figsize=(14.5,8.3));fig.subplots_adjust(left=.30,right=.94,top=.77,bottom=.14)
        im=ax.imshow(values,vmin=0,vmax=1,cmap='YlGnBu',aspect='auto')
        ax.set_xticks(range(5),('Source p','Width p\n| true source','Endian p (equiv.)\n| true source','Base p\n| true source','Valid mass'))
        ax.xaxis.tick_top();ax.tick_params(length=0,pad=8)
        ax.set_yticks(range(12),[('Direct' if m.endswith('direct') else 'Sink')+' / '+c.replace('|',' ').replace('smb2','SMB2').replace('dns','DNS') for m,c in stagerows])
        for y,row in enumerate(values):
            for x,v in enumerate(row):ax.text(x,y,f'{v:.4f}',ha='center',va='center',color='white' if v>.55 else 'black')
        ax.axhline(5.5,color='#222222',linewidth=2)
        fig.suptitle('Four learned factors | post-inference diagnostics',y=.965,fontsize=18)
        fig.text(.5,.915,'Gold source is used for indexing only after predictions are sealed; it is never a forward input.',ha='center',fontsize=10)
        fig.text(.5,.085,'Width-1 endian equivalents are summed. Valid mass precedes normalization/smoothing; stage means do not multiply to final p.',ha='center',fontsize=9)
        finish(fig,'07_four_factor_stages',dict(rows=stagerows,columns=stage_names,values=values.tolist()))

        # Paired seed effects are recomputed from exact summary seed means.
        pairs=[(new,old) for new in order[-2:] for old in order if old.endswith('hybrid')]
        fig,axes=plt.subplots(1,2,figsize=(14.5,8.3),sharey=True)
        fig.subplots_adjust(left=.25,right=.97,top=.79,bottom=.17,wspace=.22)
        effects=[]
        for panel,metric in enumerate(('p_true','nll')):
            ax=axes[panel];plotvals=[]
            for y,(new,old) in enumerate(pairs):
                n=methods[new]['overall_protocol_macro']['metrics'][metric]['seed_values']
                o=methods[old]['overall_protocol_macro']['metrics'][metric]['seed_values']
                diffs=[(n[str(s)]-o[str(s)])*(1 if metric=='p_true' else -1) for s in SEEDS]
                mean=statistics.mean(diffs);margin=4.302652729911275*statistics.stdev(diffs)/math.sqrt(3)
                color='#0072B2' if new.endswith('direct') else '#D55E00'
                ax.errorbar(mean,y,xerr=margin,fmt='o',color=color,capsize=4)
                plotvals.extend((mean-margin,mean+margin)); effects.append(dict(new=new,old=old,metric=metric,mean=mean,ci95=[mean-margin,mean+margin]))
            ax.axvline(0,color='#555555',linewidth=1)
            span=max(plotvals)-min(plotvals);pad=max(span*.12,.01)
            ax.set_xlim(min(min(plotvals),0)-pad,max(max(plotvals),0)+pad)
            ax.grid(axis='x',alpha=.2)
            ax.set_xlabel('p(target) gain: new - old' if panel==0 else 'NLL gain: old - new (nat)')
            ax.set_title('Positive favors four-factor',fontsize=12)
        axes[0].set_yticks(range(8),[('Direct' if n.endswith('direct') else 'Sink')+' vs '+SHORT[o].replace(' / LAPA On',' Hybrid') for n,o in pairs])
        axes[0].invert_yaxis()
        fig.suptitle('Paired effects against existing LAPA On | equal-protocol macro',y=.965,fontsize=17)
        fig.text(.5,.91,'Mean paired difference and 95% t interval (df=2); three training seeds, not new capture uncertainty.',ha='center',fontsize=10)
        fig.text(.5,.082,'Architecture, operator support and auxiliary objective also change; this is not an isolated causal test of removing QK.',ha='center',fontsize=10)
        finish(fig,'08_paired_macro_effects',dict(effects=effects))

        fig,ax=plt.subplots(figsize=(14.5,8.3));fig.subplots_adjust(left=.02,right=.98,bottom=.14,top=.81);ax.axis('off')
        cells=[]
        for m in order:
            row=[SHORT[m]]
            for metric in ('p_true','nll','hit1'):
                x=methods[m]['overall_protocol_macro']['metrics'][metric]
                row.append(f'{x["mean"]:.4f} [{x["ci95"][0]:.4f}, {x["ci95"][1]:.4f}]')
            cells.append(row)
        table=ax.table(cellText=cells,colLabels=['Model','p(target) [95% CI]','NLL [95% CI]','Hit@1 [95% CI]'],cellLoc='center',loc='center',colWidths=[.25,.25,.25,.25])
        table.auto_set_font_size(False);table.set_fontsize(10.5);table.scale(1,2.35)
        for (r,c),cell in table.get_celld().items():
            cell.set_edgecolor('white')
            cell.set_facecolor('#E3EDF3' if r==0 else '#E5F2ED' if r>=9 else '#F5F6F7' if r%2 else 'white')
            if r==0:cell.set_text_props(weight='bold')
        fig.suptitle('Summary table | equal weight for each held-out protocol',y=.955,fontsize=18)
        fig.text(.5,.895,'Within-protocol field mean -> four-protocol mean -> three-seed mean; intervals are intentionally not clipped.',ha='center',fontsize=10)
        fig.text(.5,.085,'Modbus and TLS targets are all END. High accuracy there alone does not establish successful length arithmetic.',ha='center',fontsize=10)
        finish(fig,'09_macro_numeric_table',dict(rows=order,cells=cells))
    manifest['pdf']=dict(path=str(pdfpath.relative_to(ROOT)),sha256=sha(pdfpath),pages=len(manifest['figures']))
    write(ROOT/'FIGURE_MANIFEST.json',manifest,replace=True)
    print(f'Created {len(manifest["figures"])} numeric figures and one vector PDF collection.')


if __name__=='__main__':main()
