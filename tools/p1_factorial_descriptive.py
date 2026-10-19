"""Prepared paired descriptive estimators. No actual factorial outputs exist yet."""
from collections import defaultdict
import random
import statistics
from personaslm_alignment import contrasts,CELLS
from p1_measurement_scoring import signed_bounds


def quantile(xs,p):
    xs=sorted(xs);q=(len(xs)-1)*p;i=int(q);fraction=q-i
    return xs[i]*(1-fraction)+xs[min(i+1,len(xs)-1)]*fraction


def cluster_sensitivity(values,seed=731701,repetitions=5000):
    """Each entry is one whole speaker/paired-case contribution, not one output."""
    if len(values)<2:return {'interval':None,'reason':'Fewer than two clusters'}
    rng=random.Random(seed);draws=[statistics.mean(rng.choices(values,k=len(values))) for _ in range(repetitions)]
    return {'mean':statistics.mean(values),'clusters':len(values),'resamples':repetitions,'seed':seed,
            'interval':[quantile(draws,.025),quantile(draws,.975)],
            'leave_one_cluster_out':[statistics.mean(values[:i]+values[i+1:]) for i in range(len(values))],
            'scope':'Descriptive resampling sensitivity; synthetic/template dependencies prevent guaranteed population coverage; no significance test.'}


def paired_contrast(rows,weights,outcome,low=0,high=1):
    """No missing-cell renormalization. Complete-case estimand separately named."""
    cases=defaultdict(dict)
    for row in rows:
        key=row['case_id'];condition=row['condition']
        if condition in cases[key]:raise ValueError('Duplicate case-condition')
        cases[key][condition]=row
    contributions=[]
    for cid,group in sorted(cases.items()):
        if len({x['speaker_id'] for x in group.values()})!=1:raise ValueError('Speaker changed within case')
        values={k:group[k].get(outcome) if k in group else None for k,w in weights.items() if w}
        for v in values.values():
            if v is not None and not low<=v<=high:raise ValueError('Outcome outside declared scale')
        complete=all(v is not None for v in values.values())
        estimate=sum(weights[k]*v for k,v in values.items()) if complete else None
        lo=hi=0
        for k,v in values.items():
            w=weights[k]
            if v is None:lo+=min(w*low,w*high);hi+=max(w*low,w*high)
            else:lo+=w*v;hi+=w*v
        contributions.append({'case_id':cid,'speaker_id':next(iter(group.values()))['speaker_id'],
                              'estimate':estimate,'bounds':[lo,hi],'complete':complete})
    complete=[x for x in contributions if x['complete']];speakers=defaultdict(list)
    for x in complete:speakers[x['speaker_id']].append(x['estimate'])
    return {'cases':contributions,'assigned_cases':len(cases),'complete_cases':len(complete),
        'complete_case_mean':statistics.mean(x['estimate'] for x in complete) if complete else None,
        'full_assigned_identification_bounds':[statistics.mean(x['bounds'][i] for x in contributions) for i in (0,1)] if contributions else None,
        'speaker_equal_weight_sensitivity':cluster_sensitivity([statistics.mean(v) for v in speakers.values()]) if speakers else None,
        'estimand_warning':'Complete-case mean, full-denominator bounds, and equal-speaker resampling are separately labeled; no silent denominator switch.'}


def validate_factorial_inventory(rows):
    groups=defaultdict(list)
    for row in rows:groups[row['case_id']].append(row)
    if len(rows)!=80 or len(groups)!=8:raise ValueError('Exactly eight cases and eighty outputs required')
    for group in groups.values():
        if len(group)!=10 or {x['condition'] for x in group}!=set(CELLS)|{'N_style','N_history'}:raise ValueError('Incomplete factorial/control inventory')
        for field in ('speaker_id','evidence_sha256','question_sha256','reference_sha256','evaluation_date'):
            if len({x[field] for x in group})!=1:raise ValueError('Within-case invariant changed: '+field)
    return True


def all_descriptive(rows,outcome,low=0,high=1):
    validate_factorial_inventory(rows)
    return {name:paired_contrast(rows,spec['weights'],outcome,low,high) for name,spec in contrasts().items()}
