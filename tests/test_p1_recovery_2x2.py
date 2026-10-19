import copy
from collections import Counter
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1_recovery_design as d
import p1_recovery_run as run


def test_outcome_independent_selection_and_disjoint_pilot():
    bank=d.cases();chosen=d.select_cases(bank)
    assert [c['case_id'] for c in chosen]==[f'p1_measure_calibration_{i:02d}' for i in range(8)]
    altered=copy.deepcopy(bank)
    for i,c in enumerate(altered):c['task_success']='Success' if i%2 else 'Failure';c['factual']='Incorrect'
    assert [c['case_id'] for c in d.select_cases(list(reversed(altered)))]==[c['case_id'] for c in chosen]
    assert not {c['case_id'] for c in chosen}&{c['case_id'] for c in bank if c['pool']=='factorial'}


@pytest.mark.parametrize('case',d.select_cases(d.cases()),ids=lambda c:c['case_id'])
def test_fact_preservation_and_reference_uniqueness(case):
    assert d.reference_audit(case)['status'].startswith('PASS')
    arranged=d.organized_evidence(case)
    assert Counter(line for line in arranged.splitlines() if line.startswith('['))==Counter(case['trusted_evidence'].splitlines())
    q=case['question'];ref=case['reference']
    c=run.construct(case,'D1',None)
    assert c['question']==q and c['reference']==ref and c['facts']==case['facts']


def test_reference_interval_and_chain_errors_rejected():
    c=copy.deepcopy(d.select_cases(d.cases())[4]);c['reference'][1]['source_ids'].reverse()
    with pytest.raises(ValueError):d.reference_audit(c)
    c=copy.deepcopy(d.select_cases(d.cases())[0]);c['requested_date']='2052-09-15'
    with pytest.raises(ValueError):d.reference_audit(c)


def test_q1_nonunique_component_stops_without_invented_tie():
    for c in d.select_cases(d.cases()):
        if c['family']=='relational_chain':
            assert len(d.q1_candidates(c))==3
            with pytest.raises(ValueError,match='PRIORITY_UNRESOLVED'):d.q1(c)
        else:
            q=d.q1(c);assert len(q['reference'])==1
            assert q['reference'][0] in c['reference']
            assert q['reference'][0]['value'] not in q['question']
            if c['family']=='dated_comparison':assert q['selected_component']=='september_bay'


@pytest.mark.parametrize('text,success,state',[
    ('Bay B5022','Success','Correct'),('  BAY   B5022.\n','Success','Correct'),('Ｂ５０２２','Success','Correct'),
    ('Bay B5012','Failure','Incorrect'),('Bay B5022, not Bay B5022','Uncertain','Unverifiable'),
    ('Not Bay B5022','Uncertain','Unverifiable'),('Bay B5022 or Bay B5012','Uncertain','Unverifiable'),
    ('Bay B50220','Failure','Incorrect'),('**Bay B5022**','Uncertain','Unverifiable'),
    ('','Failure','Missing'),(None,'Missing','Missing')])
def test_q1_full_answer_frozen_normalization(text,success,state):
    spec=d.q1(d.select_cases(d.cases())[0]);actual=d.score_single(text,spec)
    assert actual['task_success']==success and actual['answer_state']==state


def gate_rows():
    return [{'case_id':str(i),'condition':con,'family':d.FAMILIES[i//2],
        'researcher_decision':'Success' if i<6 else 'Failure','automatic_task_success':'Success' if i<6 else 'Failure'}
        for con in ('D0','D1','D2','D3') for i in range(8)]


def test_ai_cannot_satisfy_audit_gate():
    rows=gate_rows()
    for r in rows:r['AI_task_success']=r.pop('researcher_decision')
    assert d.adjudicated_decision(rows)['status']=='SCIENTIFIC DECISION PENDING REVIEW'


def test_fixed_priority_over_highest_success_and_family_warning():
    rows=gate_rows()
    for r in rows:
        if r['condition']=='D3':r['researcher_decision']=r['automatic_task_success']='Success'
    got=d.adjudicated_decision(rows)
    assert got['selected_configuration']=='D0'
    assert got['families_not_measurement_ready']==['dated_comparison']
    assert not got['new_inference_authorized']


def test_both_gate_requirements_and_no_outcome_expansion():
    rows=gate_rows()
    for r in rows:
        if r['condition']=='D0' and r['case_id'] in ('0','1'):r['automatic_task_success']='Uncertain'
    assert d.adjudicated_decision(rows)['selected_configuration']=='D1'
    for r in rows:r['researcher_decision']='Failure';r['automatic_task_success']='Failure'
    assert d.adjudicated_decision(rows)['status']=='NO_CONFIGURATION_QUALIFIED'


def test_original_audit_reconstructs_without_label_changes():
    rows=d.original_audit()
    assert len(rows)==32 and sum(r['D0_reused_in_2x2'] for r in rows)==8
    assert sum(r['original_AI']['task_success']=='Success' for r in rows)==11
    assert all(r['D0_prompt_byte_identical'] and not r['researcher_decision'] for r in rows)


def test_frozen_eligible_scope_and_no_d0_generation():
    if not run.MANIFEST.exists():pytest.skip('Prospective manifest not yet prepared')
    plan=run.validate()
    assert len(plan['requests'])==20 and len(plan['blocked_requests'])==4
    assert Counter(r['condition'] for r in plan['requests'])=={'D1':8,'D2':6,'D3':6}
    assert all(r['condition']!='D0' and r['max_new_tokens']==96 for r in plan['requests'])
    assert {x['case_id'] for x in plan['blocked_requests']}=={'p1_measure_calibration_04','p1_measure_calibration_05'}
    assert all(not x['consumes_attempt'] for x in plan['blocked_requests'])
    ledger=d.old.cumulative()
    assert ledger['attempted']['A_C0']==32 and ledger['attempted']['B_FACTORIAL']==0
    assert 16<=ledger['attempted']['C_DIAGNOSTIC']<=40


def test_single_reviewer_inventory_does_not_fabricate_missing_ratings():
    if not run.MANIFEST.exists():pytest.skip('Manifest not prepared')
    if list((d.ROOT/'runs').glob('*')):pytest.skip('Run requires actual annotation export')
    from p1_recovery_reporting import reviewer_rows
    rows=reviewer_rows()
    assert len(rows)==56 and len({r['request_id'] for r in rows})==56
    assert sum(r['decision_gate_eligible'] for r in rows)==32
    assert sum(r['record_state']=='ARCHIVED_COMPLETED_REUSED_NO_INFERENCE' for r in rows)==32
    assert sum(r['agreement_flag']=='NOT_APPLICABLE_NO_OUTPUT' for r in rows)==24
    assert rows[0]['agreement_flag']=='DISAGREEMENT'
    assert all(not r['researcher_decision'] and not r['researcher_notes'] for r in rows)
    assert all(r['ai_assisted_label']=='NOT_EVALUATED_NO_OUTPUT' for r in rows if r['record_state'].startswith('NOT_GENERATED'))
