"""Prospective allocation indices only; no independent stimuli or model calls."""
import random
import math
from p1d_design import OUT,write,allocation

def selection(n=144):
    if n!=144:raise ValueError('Recompute precision and version a changed proposal')
    rng=random.Random(716401);blocks={b:[s for s in range(n) if s%24==b] for b in range(24)}
    review=[rng.choice(blocks[b]) for b in range(24)]
    for pair in range(12):
        b=2*pair+rng.randrange(2);review.append(rng.choice([s for s in blocks[b] if s not in review]))
    model_rng=random.Random(716403);model=[model_rng.choice(blocks[b]) for b in range(24)]
    return {'allocation':allocation(n),'independent_review_speaker_indices':sorted(review),'instruct_speaker_indices':sorted(model),
        'review_seed':716401,'model_subset_seed':716403,'status':'PROSPECTIVE_INDICES_ONLY_NO_DATA_OR_EXECUTION'}

def main():
    write(OUT/'allocation_selection_v1.json',selection())
    # Transparent analytic sensitivity, not an empirical model-correlation estimate.
    rows=[]
    for rho in (0,.5,.9):
        for name,case_sd in [('main',.5),('interaction',1.)]:
            speaker_sd=case_sd*math.sqrt((1+.16)/2)
            half=1.959963984540054*speaker_sd*math.sqrt(2*(1-rho)/24)
            rows.append({'contrast':name,'speakers':24,'assumed_case_contrast_sd':case_sd,'assumed_within_speaker_contrast_ICC':.16,
                'assumed_between_model_contrast_correlation':rho,'normal_95_model_difference_halfwidth':half})
    write(OUT/'model_pair_precision_sensitivity_v1.json',{'rows':rows,'interpretation':'Analytic covariance sensitivity for paired between-model contrasts; all inputs are hypothetical, none estimated from P1c. Small subset is secondary.'})
    print('144-cluster allocation; 36 independent-review and 24 model-subset indices; no stimuli or generations')

if __name__=='__main__':main()
