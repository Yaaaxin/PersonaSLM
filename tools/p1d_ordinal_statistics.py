"""Prospective ordinal diagnostics. No interval-scale or significance assumption."""
from collections import Counter
from statistics import mean
from p1d_design import CELLS

def validate_score(x):
    if x is not None and (type(x) is not int or x not in range(1,6)):
        raise ValueError('Ordinal score must be 1..5 or explicitly missing')

def distribution(scores):
    for x in scores:validate_score(x)
    observed=[x for x in scores if x is not None];counts=Counter(observed)
    return {'eligible':len(scores),'observed':len(observed),'missing_or_unscorable':len(scores)-len(observed),
        'categories':{str(i):counts[i] for i in range(1,6)},'floor':counts[1],'ceiling':counts[5],
        'descriptive_mean':mean(observed) if observed else None,
        'zero_observed_variance':len(set(observed))==1 if observed else None,
        'caveat':'Numerical mean is descriptive; distinct measurement states must also be reported separately'}

def paired_sign_rank(rows,left,right):
    if left not in CELLS or right not in CELLS or left==right:raise ValueError('Distinct registered cells required')
    if len({r['case_id'] for r in rows})!=len(rows):raise ValueError('Duplicate paired case')
    contributions=[]
    for r in rows:
        if set(r['values'])!=set(CELLS):raise ValueError('All cells must be explicit')
        a,b=r['values'][left],r['values'][right];validate_score(a);validate_score(b)
        contributions.append({'case_id':r['case_id'],'speaker_id':r['speaker_id'],
            'difference':None if a is None or b is None else a-b,'left':a,'right':b})
    nz=[c for c in contributions if c['difference'] not in (None,0)]
    ordered=sorted(abs(c['difference']) for c in nz)
    ranks={value:mean(i+1 for i,x in enumerate(ordered) if x==value) for value in set(ordered)}
    for c in contributions:
        d=c['difference'];c['signed_rank']=None if d is None else 0 if d==0 else ranks[abs(d)]*(1 if d>0 else -1)
    return {'case_contributions':contributions,'positive':sum(c['difference'] is not None and c['difference']>0 for c in contributions),
        'negative':sum(c['difference'] is not None and c['difference']<0 for c in contributions),
        'ties':sum(c['difference']==0 for c in contributions),'unresolved_pairs':sum(c['difference'] is None for c in contributions),
        'positive_rank_sum':sum(c['signed_rank'] for c in contributions if c['signed_rank'] is not None and c['signed_rank']>0),
        'negative_rank_sum':-sum(c['signed_rank'] for c in contributions if c['signed_rank'] is not None and c['signed_rank']<0),
        'p_value':None,'interpretation':'Descriptive paired ranks with midranks for ties. No independent-case Wilcoxon significance claim; speaker dependencies retained.'}

def threshold_views(rows):
    """Preparable secondary sensitivity, not replacement for original 1..5 scores."""
    result={}
    for cutoff in range(2,6):
        transformed=[]
        for r in rows:
            if set(r['values'])!=set(CELLS):raise ValueError('All cells must be explicit')
            for v in r['values'].values():validate_score(v)
            transformed.append({**r,'values':{c:None if v is None else int(v>=cutoff) for c,v in r['values'].items()}})
        result[f'score_at_least_{cutoff}']=transformed
    return result
