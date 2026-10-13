"""Offline scientific accounting tests; unit examples are not experiment outputs."""
from copy import deepcopy
import base64
import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location('p1b_calibration_analysis', Path(__file__).parents[1] / 'tools/p1b_calibration_analysis.py')
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


def bank():
    cases = {'case_a': {'persona_id':'speaker_1','family':'A'},
             'case_b': {'persona_id':'speaker_1','family':'B'},
             'case_c': {'persona_id':'speaker_2','family':'C'}}
    rows = [{'case_id':cid,'condition':'C'+str(i),'structural_status':'TRUNCATED'} for cid in cases for i in range(8)]
    return cases, rows


def test_pairing_preserves_speaker_clusters_and_simple_effect_scale():
    cases, rows = bank()
    rows[1]['structural_status']='CROSS_TURN'
    values, summary = analysis.paired_structural(rows,cases)
    record = next(r for r in summary if r['contrast']=='C1-C0' and r['outcome']=='CROSS_TURN')
    assert record['eligible_cases']==record['evaluable_cases']==3
    assert record['speaker_clusters']==2
    assert record['estimate']==pytest.approx(1/3)
    assert record['nonzero_cases']==1
    assert record['leave_one_speaker_out_min']==0
    assert record['leave_one_speaker_out_max']==0.5
    main = next(r for r in summary if r['contrast']=='S' and r['outcome']=='CROSS_TURN')
    assert main['estimate']==pytest.approx(1/12)
    assert len(values)==3*4*9


def test_missing_cell_is_not_imputed_or_removed_from_eligible_denominator():
    cases, rows=bank()
    rows.pop(1)
    _,summary=analysis.paired_structural(rows,cases)
    simple=next(r for r in summary if r['contrast']=='C1-C0' and r['outcome']=='TRUNCATED')
    other=next(r for r in summary if r['contrast']=='C3-C0' and r['outcome']=='TRUNCATED')
    assert simple['eligible_cases']==3 and simple['evaluable_cases']==2 and simple['missing_cases']==1
    assert other['evaluable_cases']==3


def test_duplicate_factorial_cells_rejected():
    cases,rows=bank()
    with pytest.raises(ValueError,match='duplicate'):
        analysis.paired_structural(rows+[rows[0]],cases)


def test_existing_analysis_csv_cannot_be_overwritten(tmp_path):
    target=tmp_path/'record.csv'
    analysis.write_csv(target,[{'a':'historical'}])
    before=target.read_bytes()
    with pytest.raises(FileExistsError):
        analysis.write_csv(target,[{'a':'new'}])
    assert target.read_bytes()==before


def test_review_packet_keeps_full_raw_and_blank_humans_without_treatment_columns():
    # Minimal explicitly synthetic unit fixture, never imported as human review.
    raw=' Supported unit-test clause.\nUser: next'
    span=' Supported unit-test clause.\n'
    case={'case_id':'UNIT','persona_id':'UNIT_PERSON','question':'Unit question?',
          'trusted_evidence':'Unit evidence','evaluation_date':'2027-04-15',
          'context':['User: unit context'], 'historical_source_fact':{'value':'unit past'},
          'expected_answer':{'components':{'answer':'unit'}},
          'applicability':{a:True for a in analysis.core.AXES}}
    result={'request_id':'UNIT_REQUEST','case_id':'UNIT','persona_id':'UNIT_PERSON','condition':'C7',
            'factors':{'S':1,'F':1,'H':1},'raw_response':raw,'generated_tokens':96,
            'raw_termination':{'stop_type':'limit'},'evaluation':{'response_status':{
                'first_span':{'start':0,'end':len(span),'text':span,'sha256':analysis.text_digest(span)},
                'raw_sha256':analysis.text_digest(raw),'excluded_tail':'User: next',
                'removed_prefix':'','status':'CROSS_TURN'}}}
    mapping={'case_aliases':{'UNIT':'BC001'},'responses':[{'anonymous_response_id':'BR001',
             **{k:result[k] for k in ('request_id','case_id','persona_id','condition','factors')}}]}
    row=analysis.review_packet([result],{'UNIT':case},mapping)[0]
    assert row['raw_full_continuation']==raw and row['raw_first_reply']==span
    assert not {'condition','factors','request_id','persona_id','case_id'}.intersection(row)
    assert all(v=='' for k,v in row.items() if k.startswith('human_'))
    assert row['reviewer_id']==row['reviewed_utc']==row['review_assistance']==''
    changed=deepcopy(mapping);changed['responses'][0]['condition']='C0'
    with pytest.raises(ValueError,match='mapping differs'):
        analysis.review_packet([result],{'UNIT':case},changed)


@pytest.fixture
def synthetic_transport():
    # In-memory audit fixture only: no server call, saved run or scientific response.
    rows=[{'request_id':f'UNIT-{i}', 'prompt':'unit prompt', 'input_token_ids':[42],
           'input_token_count':1, 'prompt_sha256':analysis.text_digest('unit prompt')} for i in range(192)]
    events=[]
    def add(kind,data): events.append({'sequence':len(events)+1,'kind':kind,'data':data})
    def encoded(data): return base64.b64encode(json.dumps(data).encode()).decode()
    for row in rows:
        add('http_request',{'route':'/tokenize','payload':{'content':row['prompt'],'add_special':True,'parse_special':False,'with_pieces':False}})
        add('http_response',{'route':'/tokenize','status':200,'body_base64':encoded({'tokens':[42]})})
        add('p1b_live_prompt_verified',row)
    for row in rows:
        raw={'content':'unit response','prompt':'unit prompt','tokens':[7],'tokens_predicted':1,
             'tokens_evaluated':1,'truncated':False,'timings':{'cache_n':0},
             'generation_settings':{'seed':42,'temperature':0.0,'n_predict':96,'top_p':1.0,'stop':[],'ignore_eos':False}}
        add('p1b_generation_started',row)
        add('http_request',{'route':'/completion','payload':{'prompt':[42],**analysis.core.DECODING}})
        add('http_response',{'route':'/completion','status':200,'body_base64':encoded(raw)})
        add('p1b_raw_generation',{'request_id':row['request_id'],'response':raw})
        add('p1b_result',{'request_id':row['request_id'],'evaluation':{'response_status':{
            'first_span':{'start':0,'end':13,'text':'unit response'},'raw_sha256':analysis.text_digest('unit response'),
            'removed_prefix':'','excluded_tail':''}}})
    return {'requests':rows},events


def test_transport_reconciles_separate_native_tokenizer_and_generation_phases(synthetic_transport):
    plan,events=synthetic_transport
    verified=analysis.verify_transport(plan,events)
    assert verified['native_tokenizations_reconciled']==verified['native_completions_reconciled']==192
    assert verified['evaluated_input_token_ids_returned'] is False


@pytest.mark.parametrize('mutation',['order','input_id','body','native_setting','prompt','cache','span'])
def test_transport_rejects_scientific_record_drift(synthetic_transport,mutation):
    plan,events=deepcopy(synthetic_transport)
    def first(kind): return next(e['data'] for e in events if e['kind']==kind and (kind not in ('http_request','http_response') or e['data']['route']=='/completion'))
    if mutation=='order':
        plan['requests']=list(reversed(plan['requests']))
    elif mutation=='input_id': first('http_request')['payload']['prompt']=[43]
    elif mutation=='body': first('http_response')['body_base64']=base64.b64encode(b'{}').decode()
    elif mutation in ('native_setting','prompt','cache'):
        raw=first('p1b_raw_generation')['response']
        if mutation=='native_setting':raw['generation_settings']['seed']=43
        if mutation=='prompt':raw['prompt']='changed'
        if mutation=='cache':raw['timings']['cache_n']=1
        first('http_response')['body_base64']=base64.b64encode(json.dumps(raw).encode()).decode()
    elif mutation=='span':first('p1b_result')['evaluation']['response_status']['first_span']['end']=1
    with pytest.raises(ValueError):analysis.verify_transport(plan,events)
