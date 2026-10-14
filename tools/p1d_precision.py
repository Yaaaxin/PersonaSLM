"""Bounded Monte Carlo planning; synthetic Bernoulli outcomes, never model outputs."""
import argparse
import itertools
import math
import random
import statistics
from p1d_design import OUT,write,csvwrite,WEIGHTS,CELLS,allocation,sha

SEED=716101
Z=statistics.NormalDist().inv_cdf(.975)
Z6=statistics.NormalDist().inv_cdf(1-.05/12)

def quantile(x,p):
    y=sorted(x);i=(len(y)-1)*p;a=int(i);return y[a]+(y[min(a+1,len(y)-1)]-y[a])*(i-a)

def one(rng,n,p,cluster_share,pair_share,missing,effect):
    output={c:[] for c in ('E','V','ExV')};all_complete={c:[] for c in output}
    for speaker in range(n):
        shared=rng.random();speaker_u=[shared if rng.random()<pair_share else rng.random() for _ in range(4)]
        values={c:[] for c in output};known={c:[] for c in output}
        for j in range(2):
            # Four family offsets are balanced over the cyclic allocation, not inferred from P1c.
            family=(speaker+j)%4;prevalence=p+(-.075,-.025,.025,.075)[family]
            u=rng.random();own=[u if rng.random()<pair_share else rng.random() for _ in range(4)]
            uniforms=speaker_u if rng.random()<cluster_share else own
            probs=[prevalence+effect*((1 if e else -1)*.5-(1 if v else -1)*.5+(1 if e==v else -1)*.5) for e,v in ((0,0),(0,1),(1,0),(1,1))]
            assert min(probs)>=0 and max(probs)<=1
            y=[float(u<pr) for u,pr in zip(uniforms,probs)]
            miss=[rng.random()<(0 if missing=='none' else .1 if missing=='balanced_10' else (.2 if k>=2 else .05)) for k in range(4)]
            for c in output:
                w=[WEIGHTS[c][cell] for cell in CELLS[:4]]
                truth=sum(a*b for a,b in zip(w,y));observed=sum(a*b for a,b,m in zip(w,y,miss) if not m)
                lo=observed+sum(min(0,a) for a,m in zip(w,miss) if m);hi=observed+sum(max(0,a) for a,m in zip(w,miss) if m)
                values[c].append((truth,observed,lo,hi));known[c].append(None if any(miss) else truth)
        for c in output:
            output[c].append([sum(x[k] for x in values[c])/2 for k in range(4)])
            all_complete[c].extend(known[c])
    result={}
    for c,rows in output.items():
        true=[x[0] for x in rows];inc=[x[1] for x in rows];se=statistics.stdev(true)/math.sqrt(n)
        mean=statistics.mean(true);target=effect if c=='E' else -effect if c=='V' else 2*effect
        lo=statistics.mean(x[2] for x in rows);hi=statistics.mean(x[3] for x in rows)
        known=[x for x in all_complete[c] if x is not None]
        result[c]={'halfwidth':Z*se,'familywise_halfwidth':Z6*se,'complete_data_coverage':abs(mean-target)<=Z*se,
            'known_label_incidence_bias':statistics.mean(inc)-target,'bound_width':hi-lo,
            'realized_complete_data_mean_in_bounds':lo<=mean<=hi,'assessed_case_fraction':len(known)/(2*n),
            'assessed_only_bias':None if not known else statistics.mean(known)-target,
            'truth':target,'latent_cluster_share_not_empirical_ICC':cluster_share}
    return result

def simulate(replicates=128):
    rows=[];configs=list(itertools.product((48,96,144),(.25,.5,.75),(0,.4),(.25,.75),('none','balanced_10','condition_dependent'),(0,.05)))
    for index,(n,p,icc,pair,missing,effect) in enumerate(configs):
        rng=random.Random(SEED+index);trials=[one(rng,n,p,icc,pair,missing,effect) for _ in range(replicates)]
        for c in ('E','V','ExV'):
            vals=[t[c] for t in trials]
            rows.append({'scenario':index,'speakers':n,'cases':2*n,'requests_one_arm':12*n,'baseline_prevalence':p,'cluster_sharing_assumption':icc,
                'paired_cell_sharing':pair,'missingness':missing,'effect_assumption':effect,'contrast':c,'replicates':replicates,'seed':SEED+index,
                'median_95_halfwidth':statistics.median(x['halfwidth'] for x in vals),'p90_95_halfwidth':quantile([x['halfwidth'] for x in vals],.9),
                'median_six_comparison_halfwidth':statistics.median(x['familywise_halfwidth'] for x in vals),
                'complete_data_MC_coverage':statistics.mean(x['complete_data_coverage'] for x in vals),
                'MC_coverage_SE':math.sqrt(statistics.mean(x['complete_data_coverage'] for x in vals)*(1-statistics.mean(x['complete_data_coverage'] for x in vals))/replicates),
                'median_unknown_identification_width':statistics.median(x['bound_width'] for x in vals),
                'known_label_incidence_bias_mean':statistics.mean(x['known_label_incidence_bias'] for x in vals),
                'assessed_case_fraction_mean':statistics.mean(x['assessed_case_fraction'] for x in vals),
                'assessed_only_bias_mean':statistics.mean(x['assessed_only_bias'] for x in vals if x['assessed_only_bias'] is not None),
                'bounds_contain_realized_mean_all_trials':all(x['realized_complete_data_mean_in_bounds'] for x in vals)})
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--replicates',type=int,default=128);args=p.parse_args()
    if not 16<=args.replicates<=512:raise ValueError('Bounded simulation requires 16..512 replicates')
    rows=simulate(args.replicates)
    write(OUT/'precision_simulation_v1.json',{'seed':SEED,'replicates':args.replicates,'scenarios':len(rows)//3,'rows':rows,
        'source_sha256':sha(__file__),'data_kind':'SIMULATED_PLANNING_ONLY_NOT_GENERATIONS',
        'assumptions':'Binary paired cell outcomes with shared uniforms within case and within speaker; four family prevalence offsets. Sharing probability is not an estimated or guaranteed outcome/contrast ICC.',
        'intervals':'Normal approximation to whole-speaker mean contrast; simulated coverage reported. Six-test Bonferroni margins are prospective planning sensitivity, not guaranteed precision.',
        'missingness':'Known-label incidence changes estimand under unscorability. Bounds use original weights. No correctness imputation.',
        'models':'Per-arm planning. Two arms on identical units need paired between-arm contrasts; no assumption of independent model samples.'})
    csvwrite(OUT/'precision_simulation_v1.csv',rows)
    print({'scenarios':len(rows)//3,'contrast_summaries':len(rows),'replicates':args.replicates,'new_generations':0})

if __name__=='__main__':main()
