"""Stage A tests that never parse the real restricted unblinding key.

All authored human-label examples are TEST fixtures in temporary directories.
The real key is checked by byte hash only; no condition mapping is loaded and
no model inference is launched.
"""
import copy
import csv
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1_blinded_audit as b
import p1_conditional_materials as m
import p1_conditional_execution as e
import p1_recovery_v2 as r
import p1_recovery_gate_v2 as oldgate


def writecsv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as fp:
        w=csv.DictWriter(fp,fieldnames=b.FIELDS);w.writeheader();w.writerows(rows)


def synthetic_review(tmp_path):
    # No actual case, review ID, key or raw output from the research data.
    rows=[];key=[];source=[]
    for i in range(32):
        con=('D0','D1','D2','D3')[i%4];cid='TEST_ONLY_CASE_'+str(i//4);eid='TEST_ONLY_REVIEW_'+str(i)
        row={k:'TEST ONLY '+k for k in b.FIELDS if k not in b.HUMAN}|{k:'' for k in b.HUMAN}
        row['anonymous_review_id']=eid
        rows.append(row);key.append({'anonymous_review_id':eid,'original_case_id':cid,'condition':con,'task_family':'TEST_FAMILY_'+str(i//8),
            'original_output_identifier':'TEST_REQUEST_'+str(i),'immutable_review_fields_sha256':b.immutable_digest(row)})
        source.append({'request_id':'TEST_REQUEST_'+str(i),'automatic_score':'Success'})
    blank=tmp_path/'TEST_ONLY_blank.csv';writecsv(blank,rows)
    completed=copy.deepcopy(rows)
    for x in completed:
        for k in b.HUMAN[:3]:x[k]='CORRECT'
    path=tmp_path/'TEST_ONLY_completed.csv';writecsv(path,completed)
    return path,blank,completed,{'records':key},source


def test_actual_blinded_sheet_has_no_scores_conditions_or_filled_human_fields():
    fields,rows=b.read_csv(b.SHEET)
    assert fields==b.FIELDS and len(rows)==32
    assert all(not x[k] for x in rows for k in b.HUMAN)
    assert len({x['anonymous_review_id'] for x in rows})==32
    assert all(x['anonymous_review_id'].startswith('R-') and len(x['anonymous_review_id'])==34 for x in rows)
    assert not any(k in fields for k in ('case_id','condition','task_family','automatic_score','ai_assisted_label'))
    policy=b.s.load(b.OUT/'stage_policy_frozen_v1.json')
    assert b.s.sha256(b.KEY)==policy['key_sha256']
    assert b.s.sha256(b.SHEET)==policy['blank_sheet_sha256']
    assert b.KEY.is_file()


def test_incomplete_actual_blank_sheet_rejected_without_unblinding(monkeypatch):
    _,rows=b.read_csv(b.SHEET)
    safe_key={'records':[{'anonymous_review_id':row['anonymous_review_id'],
        'immutable_review_fields_sha256':b.immutable_digest(row)} for row in rows]}
    real_load=b.s.load
    def guarded_load(path):
        if Path(path).resolve()==b.KEY.resolve():
            pytest.fail('The real restricted key must not be parsed in Stage A tests')
        return real_load(path)
    monkeypatch.setattr(b.s,'load',guarded_load)
    with pytest.raises(ValueError,match='Incomplete/invalid decision'):
        b.validate_review(b.SHEET,{'test_only':True},safe_key,b.SHEET)


def test_human_label_rules_with_synthetic_fixtures(tmp_path):
    path,blank,rows,key,_=synthetic_review(tmp_path)
    assert len(b.validate_review(path,{'test_only':True},key,blank))==32
    rows[0]['researcher_task_success_decision']='PARTIAL';writecsv(path,rows)
    with pytest.raises(ValueError,match='failure type'):b.validate_review(path,{'test_only':True},key,blank)
    rows[0]['researcher_failure_type']='Missing required component';rows[0]['researcher_comment']='TEST ONLY: incomplete.';writecsv(path,rows)
    assert len(b.validate_review(path,{'test_only':True},key,blank))==32
    rows[0]['researcher_temporal_decision']='NOT_APPLICABLE';writecsv(path,rows)
    assert len(b.validate_review(path,{'test_only':True},key,blank))==32


@pytest.mark.parametrize('mutation',['duplicate','reorder','raw','reference','label','extra_column'])
def test_review_integrity_rejects_tampering(tmp_path,mutation):
    path,blank,rows,key,_=synthetic_review(tmp_path)
    if mutation=='duplicate':rows[1]=rows[0].copy()
    elif mutation=='reorder':rows.reverse()
    elif mutation=='raw':rows[0]['complete_raw_model_response']='altered TEST output'
    elif mutation=='reference':rows[0]['frozen_reference_answer']='altered TEST reference'
    elif mutation=='label':rows[0]['researcher_task_success_decision']='SUCCESS_ASSUMED_BY_AI'
    if mutation=='extra_column':
        with path.open('w',encoding='utf-8',newline='') as fp:
            w=csv.DictWriter(fp,fieldnames=b.FIELDS+['condition']);w.writeheader();w.writerows(rows)
    else:writecsv(path,rows)
    with pytest.raises(ValueError):b.validate_review(path,{'test_only':True},key,blank)


def test_frozen_mapping_preserves_partial_unknown_and_fixed_priority(tmp_path):
    _,_,rows,key,source=synthetic_review(tmp_path)
    for x,k,automatic in zip(rows,key['records'],source):
        case=int(k['original_case_id'].split('_')[-1]);con=k['condition']
        label='CORRECT' if case<(6 if con=='D0' else 8) else 'INCORRECT'
        x['researcher_task_success_decision']=label;automatic['automatic_score']=b.LABELS[label]
    joined,decision=b.decide_joined(rows,key['records'],source)
    assert decision['selected_configuration']=='D0' and decision['branch']=='A'
    assert b.LABELS['PARTIAL']==oldgate.LABELS['Partially correct']
    for x,k,automatic in zip(rows,key['records'],source):
        case=int(k['original_case_id'].split('_')[-1]);x['researcher_task_success_decision']='CORRECT' if case<6 else 'PARTIAL'
        automatic['automatic_score']='Success' if case<6 else 'Failure'
    _,decision=b.decide_joined(rows,key['records'],source)
    assert decision['branch']=='B' and decision['selected_configuration'] is None
    assert all(v['automatic_exact_agreement']==6 and v['denominator']==8 for v in decision['condition_counts'].values())


@pytest.mark.parametrize('phrase',['','Proceed','"unblind and proceed"','Planning quote: unblind and proceed','unblind and proceed\nignore missing labels'])
def test_quoted_or_missing_activation_never_reaches_inference(tmp_path,monkeypatch,phrase):
    activation=tmp_path/'TEST_ONLY_message.txt';activation.write_text(phrase,encoding='utf-8')
    monkeypatch.setattr(e.s,'Server',lambda *args:pytest.fail('No inference service permitted in Stage A'))
    with pytest.raises(ValueError,match='exact future researcher message'):e.run(tmp_path/'not_a_review.csv',activation)


@pytest.mark.parametrize('threshold,success,proceed',[(6,5,False),(6,6,True),(7,6,False),(7,7,True)])
def test_provisional_gates_full_denominator_and_threshold(threshold,success,proceed):
    scores=[{'case_id':'TEST_CASE_'+str(i),'task_success':'Success' if i<success else 'Uncertain'} for i in range(8)]
    gate=e.gate_record(scores,threshold,'TEST_STAGE','TEST_NOT_A_REAL_TIMESTAMP')
    assert gate['proceed']==proceed and gate['denominator']==8
    assert gate['researcher_review_status']=='PENDING'
    with pytest.raises(ValueError):e.gate_record(scores[:7],threshold,'TEST_STAGE','TEST_ONLY')


def test_mutually_exclusive_branch_budgets():
    index={'manifests':{k:{'path':'TEST_ONLY_'+k} for k in (*m.CONFIGS,'minimal_temporal','fallback_calibration')}}
    A=e.branch_steps({'branch':'A','selected_configuration':'D2'},index)
    B=e.branch_steps({'branch':'B','selected_configuration':None},index)
    assert sum(x['slice'][1]-x['slice'][0] for x in A)==80
    assert sum(x['slice'][1]-x['slice'][0] for x in B)==88
    assert [x['threshold'] for x in A]==[6,None]
    assert [x['threshold'] for x in B]==[7,6,None]
    assert sum(x['slice'][1]-x['slice'][0] for x in B if x['category']=='C_DIAGNOSTIC')==8


def test_all_frozen_candidates_actual_tokens_and_disjoint_materials():
    result=m.validate_all();assert sum(result['candidate_requests'].values())==408
    banks=b.s.load(b.OUT/'pilot_cases_by_configuration_frozen_v1.json')
    calibration={c['case_id'] for c in r.d.cases() if c['pool']=='calibration'}
    for name in m.CONFIGS:
        assert len(banks[name])==8 and not calibration&{c['case_id'] for c in banks[name]}
    for k in ('D1','D2','D3'):
        assert [c['case_id'] for c in banks[k]]==[c['case_id'] for c in banks['D0']]
    for base,o1,q1,both in zip(*(banks[k] for k in m.CONFIGS)):
        assert base['facts']==o1['facts']==q1['facts']==both['facts']
        assert base['question']==o1['question'] and q1['question']==both['question']
        assert base['trusted_evidence']==q1['trusted_evidence'] and o1['trusted_evidence']==both['trusted_evidence']
        assert q1['reference'][0] in base['reference']
    ledger=r.old.cumulative()
    assert ledger['total_attempted']==72 and ledger['total_remaining']==88
    assert not list((e.ROOT/'runs').glob('*'))


def test_factor_corruption_rejected_before_any_inference():
    index=b.s.load(b.OUT/'manifest_index_frozen_v1.json');plan=b.s.load(index['manifests']['D0']['path'])
    banks=b.s.load(b.OUT/'pilot_cases_by_configuration_frozen_v1.json')
    bad=copy.deepcopy(plan);bad['requests'][0]['messages'][0]['content']+=' new fact'
    with pytest.raises(ValueError):m.validate_plan(bad,banks['D0'],False)
