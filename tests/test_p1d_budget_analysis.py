"""Authored mathematical fixtures, not generated observations or human scores."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1d_budget_analysis as a

def rows():
    return [{'speaker_id':str(i),'case_id':str(i),'family':'authored','condition':c,'budget':cap,
        'factual':'Unverifiable','temporal':'Unverifiable','task_success':'Failure','semantic_completeness':'NO',
        'relevance':3,'coherence':5,'persona_fidelity':4,'components':[{'presence':'ABSENT','support':'ABSENT'}],
        'unit_identifiable':True,'structural_status':'CROSS_TURN','stop_reason':'length','latency_seconds':1.}
        for i in range(8) for c in a.b.CELLS for cap in (96,192,256)]

def pick(summary,metric,lo=96,hi=192):
    return next(r for r in summary if r['metric']==metric and r['lower_budget']==lo and r['higher_budget']==hi)

def test_unknown_not_factual_error_or_task_failure_by_alias():
    v=a.metric_values(rows()[0]);assert v['factual_Unverifiable_label_incidence']==1
    assert v['factual_Incorrect_label_incidence']==0 and v['factual_unknown_correctness'] is None
    assert v['task_success']==0 and v['coherence']==5
    assert v['budget_termination_incidence']==1 and v['eos_termination_incidence']==0

def test_signed_unknown_bounds():
    assert a.bounds_difference(None,0)==(-1,0)
    assert a.bounds_difference(0,None)==(0,1)
    assert a.bounds_difference(None,None,(1,5))==(-4,4)

def test_case_pairing_and_no_missing_cell_renormalization():
    r=rows()
    for x in r:
        if x['speaker_id']=='0' and x['budget']==192:x['task_success']='Success'
    _,c,s=a.paired_estimates(r,draws=100)
    z=pick(s,'task_success');assert z['all_eligible_paired_estimate']==1/8
    assert z['positive_speakers']==1 and z['zero_speakers']==7
    assert min(z['leave_one_speaker_out'])==0 and max(z['leave_one_speaker_out'])==1/7
    for x in r:
        if x['speaker_id']=='0' and x['budget']==192 and x['condition']=='E0V0':x['task_success']='Uncertain'
    _,_,s=a.paired_estimates(r,draws=100);z=pick(s,'task_success')
    assert z['all_eligible_paired_estimate'] is None
    assert z['observed_complete_speakers']==7 and z['complete_speaker_alternative_mean']==0
    assert z['all_eligible_identification_bounds']==[5/48,1/8]

def test_bootstrap_reconstructs_exactly_and_retains_zero_variance():
    r=rows();one=a.paired_estimates(r,draws=100);two=a.paired_estimates(r,draws=100)
    assert one==two
    z=pick(one[2],'task_success');assert z['speaker_bootstrap_sensitivity_interval']==[0,0]
    assert z['eligible_speakers']==8
