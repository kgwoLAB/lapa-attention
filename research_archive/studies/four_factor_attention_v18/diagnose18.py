"""Post-hoc analytic bounds, not a new model, selection rule or training run.

For sink only, true-source destination mass <= .98 * mean_head_source_p.
Neutral mass = (1-.98*mean_head_valid_mass)/(n+2), exactly. The remainder
lower-bounds mass transported from other sources to the correct destination.
"""
from collections import defaultdict
import json
import statistics
from common18 import ROOT,SEEDS,PROTOCOLS,now,sha,write,folder,read,verify_contract


def main():
    verify_contract()
    assert read(ROOT/'GRID_COMPLETE.json')['models']==24
    groups=defaultdict(list)
    for target in PROTOCOLS:
        for seed in SEEDS:
            run=folder(dict(target=target,mode='sink',seed=seed))
            complete=read(run/'COMPLETE.json')
            path=run/'evaluation/diagnostics.jsonl'
            assert sha(path)==complete['files']['evaluation/diagnostics.jsonl']
            for line in path.read_text().splitlines():
                r=json.loads(line)
                neutral=(1-.98*r['valid_mass'])/(r['byte_length']+2)
                upper=.98*r['source_p']
                other_lower=max(0.,r['p_true']-neutral-upper)
                value=dict(p_true=r['p_true'],neutral_p=neutral,true_source_p_upper_bound=upper,
                           other_source_p_lower_bound=other_lower)
                for key in (r['protocol']+'|'+r['semantic'],r['protocol']+'|'+r['relation']):
                    groups[key].append(value)
    summary={}
    for key,rs in sorted(groups.items()):
        averages={name:statistics.mean(r[name] for r in rs) for name in rs[0]}
        averages['other_source_fraction_of_total_correct_mass_lower_bound']=averages['other_source_p_lower_bound']/averages['p_true']
        averages['n_field_seed_pairs']=len(rs)
        summary[key]=averages
    out=dict(time=now(),status='POST_HOC_ANALYTIC_BOUND',mode='sink',epsilon=.02,
        method='Upper bound on correct-target mass from true source, exact neutral mass, lower bound from other sources',
        formula='p_other(y) >= max(0, p_final(y) - (1-.98*valid_mass)/(n+2) - .98*source_p(true_source))',
        not_applied_to_direct=True,not_a_new_metric_for_selection=True,head_mean_bounds_exact=True,
        note='Endpoint collisions are allowed; these bounds do not identify which wrong source or base caused them.',
        groups=summary,source_sha256=sha(__file__))
    write(ROOT/'MECHANISM_DIAGNOSIS.json',out)
    print(json.dumps(summary['dns|DNS pointer'],indent=2))


if __name__=='__main__':main()
