"""Offline adoption/analysis safety; invented rows below are software fixtures only."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
spec=importlib.util.spec_from_file_location('confirmed',Path(__file__).parents[1]/'tools/p1b_confirmed_analysis.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixtures():
    rows=[]
    for case in range(4):
        for cond in m.prior.contrast_weights()['S']:
            r={'case_id':f'TEST{case}','persona_id':f'TEST_SPEAKER{case//2}',
               'family':'TEST','condition':cond,'structural_status':'CROSS_TURN'}
            r.update({'applicable_'+axis:'true' for axis in m.core.AXES})
            r.update(confirmed_factual_consistency='Incorrect',confirmed_temporal_consistency='Correct',
                confirmed_response_relevance='3',confirmed_conversational_coherence='4',
                confirmed_semantic_completeness='YES',confirmed_answer_delivery='WRONG_ANSWER_DELIVERED',
                confirmed_component_coverage='0/1')
            rows.append(r)
    return rows

def test_supplied_source_integrity_and_labels():
    master=m.core.csv_records(m.prior.STAGE_A);rows=m.core.csv_records(m.SOURCE)
    check=m.validate_proposals(master,rows)
    assert check['records']==192
    assert check['distributions']['factual_consistency']=={'Correct':137,'Incorrect':34,'Unverifiable':21}
    final=m.registration_rows(rows)
    assert all(all(f[k]==r[k] for k in r) for f,r in zip(final,rows))
    assert all(f['registration_review_timestamp']=='' for f in final)
    assert all(f['registration_decision_source']=='researcher_confirmation' for f in final)

@pytest.mark.parametrize('field,value',[
    ('raw_first_reply','TAMPERED'),('applicable_temporal_consistency','false'),
    ('first_reply_sha256','0'*64),('ai_candidate_semantic_completeness','MAYBE'),
    ('ai_candidate_factual_consistency','PASS'),('ai_candidate_relevance_1_to_5','6'),
    ('ai_reference_component_coverage','99/1'),('ai_case_specific_evidence','INVENTED QUOTE')])
def test_invalid_source_rejected(field,value):
    master=m.core.csv_records(m.prior.STAGE_A);rows=m.core.csv_records(m.SOURCE)
    # Ensure the changed applicability field differs, independently of first row.
    if field=='applicable_temporal_consistency':value='true' if rows[0][field]=='false' else 'false'
    rows[0][field]=value
    with pytest.raises(ValueError):m.validate_proposals(master,rows)

def test_missing_duplicate_ids_rejected():
    master=m.core.csv_records(m.prior.STAGE_A);rows=m.core.csv_records(m.SOURCE)
    with pytest.raises(ValueError):m.validate_proposals(master,rows[:-1])
    rows[-1]=rows[0]
    with pytest.raises(ValueError):m.validate_proposals(master,rows)

def test_partial_supported_claim_is_not_task_success():
    r=fixtures()[0];r.update(confirmed_factual_consistency='Correct',confirmed_answer_delivery='PARTIAL_ANSWER',confirmed_semantic_completeness='PARTIAL')
    assert m.outcome(r,'factual_correct_label','confirmed_span_sensitivity')['value']==1
    assert m.outcome(r,'task_success','confirmed_span_sensitivity')['value']==0
    assert m.outcome(r,'semantic_complete','confirmed_span_sensitivity')['value']==0

def test_unverifiable_is_category_not_false_binary():
    r=fixtures()[0];r['confirmed_factual_consistency']='Unverifiable'
    assert m.outcome(r,'factual_unverifiable_label','boundary_conservative')['value']==1
    assert m.outcome(r,'factual_incorrect_label','boundary_conservative')['value']==0
    assert m.outcome(r,'factual_assessable_binary','boundary_conservative')['value'] is None

def test_ambiguous_sensitivity_never_relabels_structure():
    r=fixtures()[0];r['structural_status']='AMBIGUOUS'
    assert m.outcome(r,'response_relevance','boundary_conservative')['state']=='boundary_unresolved'
    assert m.outcome(r,'response_relevance','confirmed_span_sensitivity')['value']==3
    assert m.outcome(r,'structural_AMBIGUOUS','boundary_conservative')['value']==1
    assert r['structural_status']=='AMBIGUOUS'

def test_na_and_missing_are_distinct():
    r=fixtures()[0];r['applicable_temporal_consistency']='false';r['confirmed_temporal_consistency']='Not Applicable'
    assert m.outcome(r,'temporal_correct_label','boundary_conservative')['state']=='not_applicable'
    r['confirmed_factual_consistency']=''
    assert m.outcome(r,'factual_correct_label','boundary_conservative')['state']=='missing_judgment'

def test_correct_value_in_promise_is_not_delivery():
    r=fixtures()[0];r.update(confirmed_answer_delivery='NO_FINAL_ANSWER',confirmed_factual_consistency='Unverifiable',confirmed_component_coverage='1/1')
    assert m.outcome(r,'component_coverage','boundary_conservative')['value']==1
    assert m.outcome(r,'task_success','boundary_conservative')['value']==0

def test_clustered_interval_matches_existing_bundle_resampling():
    p=[{'persona_id':name,'difference':value} for name,value in [('a',1),('a',None),('b',-1),('b',-1)]]
    actual=m.interval(p,714005,1000);expected=m.prior.clustered_interval(p,714005,1000)
    assert [actual['lower'],actual['upper']]==expected['interval']
    assert actual['empty_resamples']==expected['empty_resamples']

def test_all_contrasts_pairing_loso_and_repeatability():
    rows=fixtures()
    for r in rows:
        if r['condition']=='C1':r['confirmed_factual_consistency']='Correct'
    spec=m.specification();a=m.analyze_rows(rows,spec,repeats=100);b=m.analyze_rows(rows,spec,repeats=100)
    assert a==b and a['speakers']==2 and a['cases']==4
    get=lambda c:next(s for s in a['effect_summary'] if s['policy']=='boundary_conservative' and s['metric']=='factual_correct_label' and s['family']=='ALL' and s['contrast']==c)
    assert get('C1-C0')['estimate']==1 and get('S')['estimate']==.25
    assert get('SxH')['estimate']==-.5 and get('SxFxH')['estimate']==1
    assert get('C1-C0')['evaluable_cases']==4 # All original C0 answers Incorrect, none excluded.
    leave=next(x for x in a['speaker_sensitivity'] if x['metric']=='factual_correct_label' and x['contrast']=='C1-C0')
    assert leave['eligible_cases']==2 and leave['remaining_speakers']==1

def test_ordinal_threshold_sensitivity_is_monotone():
    r=fixtures()[0]
    assert [m.outcome(r,'response_relevance_ge_'+str(k),'boundary_conservative')['value'] for k in range(2,6)]==[1,1,0,0]

@pytest.mark.parametrize('error',['duplicate','missing','identity','applicability'])
def test_invalid_factorial_analysis_rejected(error):
    rows=fixtures()
    if error=='duplicate':rows.append(rows[0])
    if error=='missing':rows.pop()
    if error=='identity':rows[0]['persona_id']='DIFFERENT'
    if error=='applicability':rows[0]['applicable_temporal_consistency']='false'
    with pytest.raises(ValueError):m.analyze_rows(rows,m.specification(),repeats=100)

def test_existing_destinations_cannot_be_overwritten(local_tmp):
    with pytest.raises(FileExistsError):m.register(output=local_tmp,final=local_tmp/'final.csv')
    with pytest.raises(FileExistsError):m.analyze(local_tmp)

def test_unregistered_analysis_cannot_unblind(local_tmp):
    (local_tmp/'registration_v1.json').write_text('{"version":"invalid","review_status":"PENDING"}',encoding='utf-8')
    with pytest.raises(ValueError):m.load_registered(local_tmp)
