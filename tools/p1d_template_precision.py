"""Cross-template planning sensitivity. Simulated outcomes only; no inference.

Random template-specific E/V/ExV slopes generate cross-speaker dependence.
Speaker intervals can target the sampled fixed-template mean but cannot establish
coverage for a hypothetical new-template population. Report both targets.
"""
import itertools
import math
import random
import statistics as st
from p1d_design import allocation, CELLS, WEIGHTS, write, csvwrite, sha
from p1d_scientific_audit import DEST

SEED=716702
Z=st.NormalDist().inv_cdf(.975)
Z6=st.NormalDist().inv_cdf(1-.05/12)

def trial(rng,n,prevalence,template_sd,missing,effect):
    # Four implementation blocks shared across families: a conservative common
    # template ancestor scenario, not a measured ICC or random template sample.
    slopes=[[rng.gauss(0,template_sd) for _ in range(3)] for _ in range(4)]
    byspeaker={s:{k:[] for k in ('E','V','ExV')} for s in range(n)}
    for a in allocation(n):
        s=a['speaker_index'];t=a['template_block'];j=a['case_index']
        # A stable per-speaker jitter is drawn before both case outcomes.
        if j==0: speaker_shift=rng.uniform(-.075,.075)
        common=rng.random();ys=[];ps=[];miss=[]
        family_offset=(-.06,-.02,.02,.06)[('single_fact','multi_component','relational_integration','context_followup').index(a['family'])]
        for cell in CELLS[:4]:
            es=1 if cell[1]=='1' else -1;vs=1 if cell[3]=='1' else -1
            p=prevalence+family_offset+speaker_shift+es*(effect+slopes[t][0])/2+vs*slopes[t][1]/2+es*vs*slopes[t][2]/4
            p=max(.001,min(.999,p));ps.append(p)
            u=common if rng.random()<.5 else rng.random();ys.append(float(u<p))
            # Condition-dependent censoring: scenario, never recode unknown as false.
            miss.append(rng.random() < (0 if missing=='none' else (.20 if es==1 else .05)))
        for k in ('E','V','ExV'):
            w=[WEIGHTS[k][c] for c in CELLS[:4]]
            y=sum(x*v for x,v in zip(w,ys));expected=sum(x*v for x,v in zip(w,ps))
            obs=sum(x*v for x,v,m in zip(w,ys,miss) if not m)
            lo=obs+sum(min(0,x) for x,m in zip(w,miss) if m)
            hi=obs+sum(max(0,x) for x,m in zip(w,miss) if m)
            byspeaker[s][k].append((y,expected,lo,hi,not any(miss)))
    out={}
    for k in ('E','V','ExV'):
        ys=[st.mean(r[0] for r in d[k]) for d in byspeaker.values()]
        expected=st.mean(r[1] for d in byspeaker.values() for r in d[k])
        mean=st.mean(ys);se=st.stdev(ys)/math.sqrt(n)
        target=effect if k=='E' else 0
        # Nonlinearity near bounds makes target an approximate superpopulation
        # value when effects are nonzero. Zero-effect symmetry is exact.
        out[k]={'mean':mean,'expected_conditional_template_effect':expected,'h':Z*se,'h6':Z6*se,
                'conditional_coverage':abs(mean-expected)<=Z*se,
                'new_template_zero_effect_coverage':abs(mean-target)<=Z*se if effect==0 else None,
                'width':st.mean(r[3]-r[2] for d in byspeaker.values() for r in d[k]),
                'complete_fraction':st.mean(r[4] for d in byspeaker.values() for r in d[k])}
    return out

def simulate(reps=128):
    rows=[]
    configs=list(itertools.product((96,144,192),(.25,.5,.75),(0,.05,.10),('none','condition_dependent'),(0,.05)))
    for i,(n,p,sd,missing,effect) in enumerate(configs):
        rng=random.Random(SEED+i)
        ts=[trial(rng,n,p,sd,missing,effect) for _ in range(reps)]
        for k in ('E','V','ExV'):
            xs=[t[k] for t in ts];coverage=st.mean(x['conditional_coverage'] for x in xs)
            rows.append({'scenario':i,'speakers':n,'cases':2*n,'prevalence':p,'template_slope_sd_assumption':sd,
                'template_ancestors':4,'missingness':missing,'E_effect_assumption':effect,'contrast':k,'seed':SEED+i,'replicates':reps,
                'median_complete_data_ordinary_halfwidth':st.median(x['h'] for x in xs),
                'median_complete_data_Bonf6_halfwidth':st.median(x['h6'] for x in xs),
                'complete_data_conditional_template_coverage':coverage,'coverage_MC_SE':math.sqrt(coverage*(1-coverage)/reps),
                'complete_data_new_template_null_coverage':st.mean(x['new_template_zero_effect_coverage'] for x in xs) if effect==0 else None,
                'mean_missingness_bound_width':st.mean(x['width'] for x in xs),'complete_case_fraction':st.mean(x['complete_fraction'] for x in xs),
                'empirical_SD_of_estimates_across_templates':st.stdev(x['mean'] for x in xs)})
    return rows

def main():
    rows=simulate()
    write(DEST/'template_precision_simulation_v1.json',{'version':'p1d_template_precision_v1','seed':SEED,'scenarios':len(rows)//3,'replicates':128,
        'source_sha256':sha(__file__),'outcomes':'SYNTHETIC_PLANNING_NOT_MODEL_OUTPUTS','rows':rows,
        'scope':'Additional sensitivity, no replacement of approved estimator or N=144 target. N=192 is hypothetical, not an expanded allocation.',
        'assumptions':'Four shared template-ancestor slopes; bounded probabilities; speaker baseline shift; .5 paired-cell shared uniform; family prevalence offsets. None is empirical ICC. Intervals use latent complete data: optimistic precision, not an analysis of imputed missing outcomes.',
        'limits':'Conditional fixed-template and new-template targets differ. Four authored blocks are not four independently sampled language populations. Missingness identification width is reported separately; template-aware confirmatory redesign needs prospective amendment.'})
    csvwrite(DEST/'template_precision_simulation_v1.csv',rows)
    print({'scenarios':len(rows)//3,'trials':len(rows)//3*128,'summaries':len(rows),'new_generations':0})

if __name__=='__main__':main()
