"""Matplotlib publication-source charts; never chooses a model from test results."""
from common16 import *
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import TwoSlopeNorm

LABELS=dict(hybrid='H: Current TAPE + LAPA',route_sink='R: Route prior only',route_direct='D: Valid-normalized route',
    route_axis='A: D + axis supervision',route_joint='J: Joint source-program',cnn_joint='C: CNN joint (no QKV)')
ROLES=('off','hybrid','selected')
ROLE_LABELS=('TAPE Off (endpoint loss)','Current TAPE + LAPA','Source-dev selected formula')
MAIN=(('dns','LENGTH'),('dns','POINTER'),('modbus','LENGTH'),('tls','LENGTH'),('smb2','LENGTH'),('smb2','OFFSET'))
RELATIONS=('DNS label','DNS root terminator','DNS RDLENGTH','DNS TXT length','DNS pointer',
    'Modbus MBAP length','TLS record length','SMB2 NameLength','SMB2 ContextLength','SMB2 NameOffset','SMB2 ContextOffset')

def main():
    assert (ROOT/'GRID_COMPLETE.json').exists() and (ROOT/'SUMMARY.json').exists()
    selection=verify_selection()['choices']
    frames={}; stages={}; field={}
    for p in PROTOCOLS:
        for role in ROLES:
            variant=selection[p]['selected'] if role=='selected' else role
            for seed in FINAL_SEEDS:
                folder=ROOT/'final'/p/f'{variant}_{seed}'
                frames[p,role,seed]=rows(folder/'evaluation/diagnostics.jsonl')
                stages[p,role,seed]=rows(folder/'STAGES.jsonl')
                field[p,role,seed]=read(folder/'FIELD_METRICS.json')
    gold=[r for p in PROTOCOLS for r in frames[p,'off',FINAL_SEEDS[0]]]
    selection_note='Selected per held-out target: '+', '.join(p.upper()+'='+selection[p]['selected'] for p in PROTOCOLS)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':15,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
    out=ROOT/'figures';out.mkdir(exist_ok=True)
    pdfdir=ROOT/'output/pdf';pdfdir.mkdir(parents=True,exist_ok=True)
    path=pdfdir/'lapa_formula_search_results.pdf'
    annotations=[];manifest=[]

    def cell_value(role,cohort,key):
        p,kind,value=cohort
        vals=[]
        for seed in FINAL_SEEDS:
            r=[r for r in frames[p,role,seed] if kind is None or r[kind]==value]
            vals.append(statistics.mean(x[key] for x in r))
        return statistics.mean(vals)

    def baseline(cohort,name,key):
        p,kind,value=cohort
        selected=[r for r in gold if r['protocol']==p and (kind is None or r[kind]==value)]
        if name=='Uniform':
            return statistics.mean(1/(r['byte_length']+2) for r in selected) if key=='p_true' else statistics.mean(r['target']==0 for r in selected)
        target_kind='END' if name=='Always END' else 'NULL'
        return statistics.mean(r['target_kind']==target_kind for r in selected)

    def fmt(v):
        if not math.isfinite(v):return 'N/A'
        return f'{v:.1e}' if 0<abs(v)<.00005 else f'{v:.4f}'

    def save(fig,name,title,pdf):
        fig.savefig(out/(name+'.png'),dpi=200)
        fig.savefig(out/(name+'.svg'))
        pdf.savefig(fig)
        manifest.append(dict(page=len(manifest)+1,name=name,title=title,
            png_sha256=sha(out/(name+'.png')),svg_sha256=sha(out/(name+'.svg'))))
        plt.close(fig)

    def heat(pdf,name,title,matrix,row_names,col_names,footer,diverging=False):
        data=np.array(matrix,dtype=float)
        fig,ax=plt.subplots(figsize=(16,6.8))
        fig.subplots_adjust(left=.205,right=.955,top=.72,bottom=.18)
        cmap=plt.get_cmap('RdBu_r' if diverging else 'YlGnBu').copy();cmap.set_bad('#eeeeee')
        norm=TwoSlopeNorm(vmin=min(-.001,float(np.nanmin(data))),vcenter=0.,vmax=max(.001,float(np.nanmax(data)))) if diverging else None
        im=ax.imshow(data,aspect='auto',cmap=cmap,vmin=None if diverging else 0,vmax=None if diverging else 1,norm=norm)
        ax.set_xticks(range(len(col_names)),col_names,fontsize=9)
        ax.xaxis.tick_top();ax.tick_params(length=0,pad=10)
        ax.set_yticks(range(len(row_names)),row_names,fontsize=10)
        ax.set_xticks(np.arange(-.5,len(col_names),1),minor=True)
        ax.set_yticks(np.arange(-.5,len(row_names),1),minor=True)
        ax.grid(which='minor',color='white',linewidth=1.4);ax.tick_params(which='minor',length=0)
        for spine in ax.spines.values():spine.set_visible(False)
        for i,j in np.ndindex(data.shape):
            value=data[i,j]; text=fmt(value)
            shade=im.norm(value) if math.isfinite(value) else 0
            color='white' if math.isfinite(value) and (shade>.66 or diverging and shade<.17) else '#17222c'
            ax.text(j,i,text,ha='center',va='center',fontsize=10,color=color)
            annotations.append(dict(figure=name,row=row_names[i],column=col_names[j],value=float(value) if math.isfinite(value) else None,text=text))
        cb=fig.colorbar(im,ax=ax,fraction=.025,pad=.02)
        cb.ax.tick_params(labelsize=9)
        cb.set_label('Balanced log gain (nat)' if diverging else 'Typed exact field F1' if name=='07_field_f1' else 'Probability / exact accuracy',fontsize=9)
        fig.suptitle(title,x=.205,ha='left',y=.96,fontweight='bold')
        fig.text(.205,.065,footer,fontsize=9,va='bottom',linespacing=1.5)
        save(fig,name,title,pdf)

    with PdfPages(path) as pdf:
        matrix=[[next(r['score'] for r in selection[p]['ranked'] if r['variant']==v) for p in PROTOCOLS] for v in VARIANTS]
        columns=[p.upper()+' held out\nchoose '+selection[p]['selected'] for p in PROTOCOLS]
        heat(pdf,'01_nested_selection','Nested source-only formula selection (higher is better)',matrix,[LABELS[v] for v in VARIANTS],columns,
             'Each cell: 3 inner validation protocols x 2 seeds; 250 updates/model. Target development is excluded from its column.\nEqual relation x destination-kind strata; log(n+2) - NLL. 32 raw-hash-ranked dev messages/protocol. Not test performance.',True)
        cohorts=[(p,'semantic',sem) for p,sem in MAIN]
        cols=[p.upper()+'\n'+sem.lower()+'\nn='+str(sum(r['protocol']==p and r['semantic']==sem for r in gold)) for p,sem in MAIN]
        for key,title,suffix in [('p_true','Final probability assigned to the correct destination','p_true'),('hit1','Exact destination Hit@1','hit1')]:
            matrix=[[cell_value(role,c,key) for c in cohorts] for role in ROLES]
            refs=('Always END','Always NULL','Uniform')
            matrix.extend([[baseline(c,r,key) for c in cohorts] for r in refs])
            heat(pdf,'02_main_'+suffix,title,matrix,[*ROLE_LABELS,*refs],cols,
                selection_note+'\n3-source -> 1-target; 600 updates, 3 fresh seeds. Historical test, exploratory. END/NULL are distinct destinations.'+
                ('\nUniform Hit@1 uses deterministic argmax (byte0), not random-sampling expected accuracy.' if key=='hit1' else '\nModbus/TLS all END: high scores there do not by themselves establish arithmetic generalization.'))
        cohorts=[(next(r['protocol'] for r in gold if r['relation']==rel),'relation',rel) for rel in RELATIONS]
        colnames=[rel.replace('DNS ','DNS\n').replace('Modbus MBAP ','Modbus\nMBAP ').replace('TLS record ','TLS\nrecord ').replace('SMB2 ','SMB2\n').replace('root terminator','root')+'\nn='+str(sum(r['relation']==rel for r in gold)) for rel in RELATIONS]
        matrix=[[cell_value(role,c,'p_true') for c in cohorts] for role in ROLES]
        matrix.extend([[baseline(c,r,'p_true') for c in cohorts] for r in ('Always END','Always NULL','Uniform')])
        heat(pdf,'03_relation_p_true','Per-field relation: final correct-destination probability',matrix,[*ROLE_LABELS,'Always END','Always NULL','Uniform'],colnames,
             selection_note+'\nMean over 3 seeds. DNS TXT has only 1 field; Modbus has 6. Decimal zeros are not substituted for missing support.')
        summary=read(ROOT/'SUMMARY.json')
        # Paired effects are computed directly from matching fresh-seed records.
        fig,axes=plt.subplots(1,2,figsize=(16,6.8));fig.subplots_adjust(left=.08,right=.95,top=.78,bottom=.24,wspace=.3)
        for ax,key,title in zip(axes,('p_true','balanced_log_gain'),('Change in mean correct-destination probability','Change in balanced log gain (nat)')):
            means=[];errors=[]
            for p in PROTOCOLS:
                deltas=[]
                for seed in FINAL_SEEDS:
                    get=lambda role:metric(frames[p,role,seed])[key]
                    deltas.append(get('selected')-get('hybrid'))
                m=statistics.mean(deltas);d=4.302652729911275*statistics.stdev(deltas)/math.sqrt(3)
                means.append(m);errors.append(d)
            ax.errorbar(range(4),means,yerr=errors,fmt='o',color='#087e8b',capsize=5,markersize=7)
            ax.axhline(0,color='#666666',linewidth=1);ax.set_xticks(range(4),[p.upper() for p in PROTOCOLS]);ax.set_xlim(-.4,3.4)
            ax.set_title(title,fontsize=12);ax.set_xlabel('Held-out target protocol');ax.set_ylabel('Selected - current hybrid')
            ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.2)
            for i,m in enumerate(means):ax.annotate(f'{m:+.4f}',(i,m),xytext=(9,0),textcoords='offset points',va='center',fontsize=10)
        fig.suptitle('Paired final effects: selected formula versus current LAPA',x=.08,ha='left',y=.94,fontweight='bold')
        fig.text(.08,.065,selection_note+'\n95% Student-t intervals over 3 paired seed means (df=2), not packet-population confidence. Intervals are not clipped.\nFormula choices were frozen before target inference; a negative result does not trigger reselection.',fontsize=9,linespacing=1.5)
        save(fig,'04_paired_effects','Paired final effects',pdf)
        # Diagnostic rows use learned head probabilities at true source, not oracle inputs.
        cols=[p.upper()+'\n'+sem.lower() for p,sem in MAIN]
        matrix=[];labels=[]
        for role,label in [('hybrid','Current'),('selected','Selected')]:
            for key,stagename in [('source_p','Source p'),('program_p','Program p | true source'),('route_p','Route p(target)'),('final_p','Final p(target)')]:
                line=[]
                for p,sem in MAIN:
                    line.append(statistics.mean(statistics.mean(r[key] for r in stages[p,role,seed] if r['semantic']==sem) for seed in FINAL_SEEDS))
                matrix.append(line);labels.append(label+': '+stagename)
        heat(pdf,'05_stages','Locator, executor and final prediction: separate stage probabilities',matrix,labels,cols,
             selection_note+'\nProgram probability is indexed at the true source only after a raw-only forward and prediction seal.\nSource/Program are pre-validity heads; route probability additionally includes execution/validity normalization. No oracle inputs.')
        matrix=[];labels=[]
        for role,label in zip(ROLES,ROLE_LABELS):
            vals=[]
            for slotgroup in (lambda r:r['slot']<4,lambda r:r['slot']>=4):
                for key in ('p_true','hit1'):
                    vals.append(statistics.mean(statistics.mean(r[key] for r in frames['dns',role,seed] if slotgroup(r)) for seed in FINAL_SEEDS))
            matrix.append(vals);labels.append(label)
        n_seen=sum(r['slot']<4 for r in gold if r['protocol']=='dns');n_unseen=266-n_seen
        heat(pdf,'06_dns_ordinal','DNS ordinal-query shift is separate from the QKV hypothesis',matrix,labels,
             [f'Slots 0-3\np(target), n={n_seen}',f'Slots 0-3\nHit@1, n={n_seen}',f'Slots >=4\np(target), n={n_unseen}',f'Slots >=4\nHit@1, n={n_unseen}'],
             'DNS was held out. Source protocols have no positive training queries beyond slot3.\nThis is a conditional diagnostic subset, not a second training experiment. The fixed ordinal-query interface is unchanged.')
        matrix=[]
        for role in ROLES:
            matrix.append([float('nan') if role=='off' else statistics.mean(field[p,role,seed]['by_semantic'][sem]['f1'] for seed in FINAL_SEEDS) for p,sem in MAIN])
        heat(pdf,'07_field_f1','Typed exact field-discovery F1 (separate from endpoint probability)',matrix,list(ROLE_LABELS),cols,
             selection_note+'\nOff has no trained presence/source/program discovery head: N/A is intentional. On threshold uses source-dev only.\nExact (start,end,semantic) multiset scoring; repeated predictions count as false positives. Native pre-validity field decoder retained.')
    write(ROOT/'FIGURE_MANIFEST.json',dict(time=now(),pdf=str(path),pdf_sha256=sha(path),pages=manifest,annotations=annotations,
        summary_sha256=sha(ROOT/'SUMMARY.json'),selection_sha256=sha(ROOT/'SELECTION.json')),replace=True)
    log('P08_FIGURES_CREATED',pages=len(manifest),numeric_cells=len(annotations),pdf=str(path))
    print(json.dumps(dict(pdf=str(path),pages=len(manifest),numeric_cells=len(annotations))))

if __name__=='__main__':main()
