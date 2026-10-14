"""Offline scalar contrast engine for the proposed P1c policy, not observed results."""
import math
import random
import statistics


def case_contrast(values, weights, lower=0.0, upper=1.0):
    if lower > upper or not weights or not math.isclose(sum(weights.values()),0,abs_tol=1e-12):
        raise ValueError('Invalid range or contrast weights')
    lo=hi=0.0;unknown=[]
    for cell,weight in weights.items():
        if not weight:continue
        value=values.get(cell)
        if value is not None and (not math.isfinite(value) or not lower<=value<=upper):
            raise ValueError('Invalid outcome: '+cell)
        a,b=(lower,upper) if value is None else (value,value)
        if value is None:unknown.append(cell)
        lo+=weight*(a if weight>0 else b)
        hi+=weight*(b if weight>0 else a)
    return {'estimate':None if unknown else lo,'lower_bound':lo,'upper_bound':hi,'unknown_cells':unknown}


def quantile(values,q):
    ordered=sorted(values);position=(len(ordered)-1)*q;a=int(position);b=min(a+1,len(ordered)-1)
    return ordered[a]+(ordered[b]-ordered[a])*(position-a)


def summarize(cases, weights, seed=715004, replicates=10000, lower=0.0, upper=1.0):
    """Cases have case_id, speaker_id, values; unknowns never change cell weights."""
    if not cases or len({r['case_id'] for r in cases})!=len(cases):raise ValueError('Empty/duplicate cases')
    if type(replicates) is not int or replicates<1:raise ValueError('Invalid replicate count')
    table=[];groups={}
    for row in sorted(cases,key=lambda r:r['case_id']):
        result={'case_id':row['case_id'],'speaker_id':row['speaker_id'],**case_contrast(row['values'],weights,lower,upper)}
        table.append(result);groups.setdefault(row['speaker_id'],[]).append(result)
    clusters=[]
    for speaker,rows in sorted(groups.items()):
        clusters.append({'speaker_id':speaker,'cases':len(rows),
            'estimate':None if any(r['estimate'] is None for r in rows) else statistics.mean(r['estimate'] for r in rows),
            'lower_bound':statistics.mean(r['lower_bound'] for r in rows),
            'upper_bound':statistics.mean(r['upper_bound'] for r in rows)})
    all_known=all(r['estimate'] is not None for r in clusters)
    interval=None;loso=[]
    if all_known:
        rng=random.Random(seed);means=[r['estimate'] for r in clusters]
        draws=[statistics.mean(rng.choices(means,k=len(means))) for _ in range(replicates)]
        interval=[quantile(draws,.025),quantile(draws,.975)]
        for i,row in enumerate(clusters):
            loso.append({'omitted_speaker':row['speaker_id'],'estimate':statistics.mean(means[:i]+means[i+1:]) if len(means)>1 else None})
    complete_groups={s:[r['estimate'] for r in rs if r['estimate'] is not None] for s,rs in groups.items()}
    assessed=[statistics.mean(v) for v in complete_groups.values() if v]
    return {'version':'p1c_paired_statistics_v1','eligible_cases':len(cases),'speaker_clusters':len(clusters),
        'evaluable_cases':sum(r['estimate'] is not None for r in table),
        'estimate':statistics.mean(r['estimate'] for r in clusters) if all_known else None,
        'identification_bounds':[statistics.mean(r['lower_bound'] for r in clusters),statistics.mean(r['upper_bound'] for r in clusters)],
        'assessed_only_sensitivity':{'estimate':statistics.mean(assessed) if assessed else None,'speakers':len(assessed),
            'limitation':'Selected complete cases; not the all-eligible estimand; selection may depend on condition.'},
        'percentile_cluster_interval':interval,'bootstrap_seed':seed,'bootstrap_replicates':replicates,
        'leave_one_speaker_out':loso,'case_table':table,'speaker_table':clusters,
        'warning':'Six purposive development clusters do not support population significance. Bounds are not sampling intervals.'}
