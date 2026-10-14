"""Prospective paired analysis primitives; no inference or automatic human adoption."""
import random
import statistics
from p1d_design import WEIGHTS,CELLS

def case_contrast(values,contrast):
    """Binary eligible outcomes only; None is unresolved, never a factual error."""
    if set(values)!=set(CELLS):raise ValueError('All six cells must be explicitly represented')
    if any(x is not None and (type(x) not in (int,float) or not 0<=x<=1) for x in values.values()):raise ValueError('Binary/bounded values required')
    weights=WEIGHTS[contrast];active=[c for c,w in weights.items() if w]
    observed=sum(weights[c]*values[c] for c in active if values[c] is not None)
    unknown=[c for c in active if values[c] is None]
    return {'complete_case_contrast':None if unknown else observed,
        'lower':observed+sum(min(0,weights[c]) for c in unknown),
        'upper':observed+sum(max(0,weights[c]) for c in unknown),
        'unresolved_cells':unknown,'no_renormalization':True}

def cluster_summary(rows,seed=716201,repeats=2000):
    """Rows are complete case contrasts with explicit speaker IDs; subset estimand disclosed."""
    if not rows:raise ValueError('No evaluable cases')
    groups={}
    for r in rows:groups.setdefault(r['speaker_id'],[]).append(r['value'])
    means={s:statistics.mean(v) for s,v in groups.items()};speakers=sorted(means)
    if len(speakers)<2:raise ValueError('At least two clusters required')
    rng=random.Random(seed);boot=sorted(statistics.mean(means[rng.choice(speakers)] for _ in speakers) for _ in range(repeats))
    return {'equal_speaker_mean':statistics.mean(means.values()),'cases':len(rows),'speakers':len(means),
        'speaker_means':means,'leave_one_speaker_out':{s:statistics.mean(v for k,v in means.items() if k!=s) for s in speakers},
        'bootstrap_percentiles':[boot[int(.025*(repeats-1))],boot[int(.975*(repeats-1))]],'seed':seed,'resamples':repeats,
        'estimand':'Equal evaluable-speaker mean, preserving all supplied cases per resampled cluster; not automatically the all-eligible estimand.',
        'coverage_caveat':'A cluster percentile interval does not guarantee population coverage.'}

def boundary_errors(prediction,allowed_spans,adjudicated):
    """Character offsets into unchanged raw text; unknown gold is not parser error."""
    if not adjudicated:return {'status':'UNRESOLVED_GROUND_TRUTH','accuracy':None}
    if not allowed_spans:return {'status':'NO_RECOVERABLE_REPLY','accuracy':int(prediction is None)}
    if prediction is None:return {'status':'ABSTENTION','accuracy':0,'answer_loss_possible':True}
    if prediction in allowed_spans:return {'status':'MATCH_TO_ACCEPTED_SPAN','accuracy':1,'unique_gold':len(allowed_spans)==1}
    # Distance is diagnostic; a semantic answer-loss decision still requires annotation.
    closest=min(allowed_spans,key=lambda s:abs(s[0]-prediction[0])+abs(s[1]-prediction[1]))
    return {'status':'SPAN_MISMATCH','accuracy':0,'under_extraction_chars':max(0,prediction[0]-closest[0])+max(0,closest[1]-prediction[1]),
        'over_extraction_chars':max(0,closest[0]-prediction[0])+max(0,prediction[1]-closest[1]),'semantic_answer_loss':'REQUIRES_REVIEW'}
