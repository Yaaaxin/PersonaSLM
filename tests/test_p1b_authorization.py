"""Unit doubles only. No test result is evidence of real model generation."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from personaslm import p1b_calibration as core
from personaslm.configuration import RuntimeConfig
from personaslm.journal import RunJournal, read_events
from personaslm.p1b_readiness import CHECKS
from personaslm.p1b_review_proposal import proposals, confirmed_copy, CONFIRM


@pytest.fixture
def materials():
    return core.load(core.DATA),core.load(core.MANIFEST),core.csv_records(core.MASTER)


def confirmed_fixture(data,master):
    # Synthetic unit reviewer, never published/imported as a research annotation.
    proposed=proposals(data,master); submission=deepcopy(proposed)
    for row in submission:
        row.update(researcher_confirmation=CONFIRM,reviewer_id='UNIT_TEST_REVIEWER',
                   review_method='UNIT_TEST synthetic confirmation, not human review')
    return proposed,submission


def test_all_proposals_keep_984_source_fields_blank_humans_and_grounded_quotes(materials):
    data,_,master=materials; generated=proposals(data,master)
    assert len(generated)==24
    for old,row in zip(master,generated):
        assert all(row[k]==v for k,v in old.items())
        assert not row['researcher_confirmation'] and not row['researcher_decision']
        quotes=json.loads(row['ai_supporting_quotations'])
        assert set(quotes)==set(CHECKS)
        for key in CHECKS:
            assert row['ai_proposed_'+key] in ('PASS','FAIL','UNCERTAIN')
            assert row['case_id'] in row['ai_explanation_'+key]
            assert quotes[key] and all(q['verbatim'] in row[q['field']] for q in quotes[key])


def test_shortcuts_and_h3_format_are_explicit_not_task_rewrites(materials):
    data,_,master=materials; rows={r['case_id']:r for r in proposals(data,master)}
    assert 'necessity is not demonstrated' in rows['p1b_H_L1']['ai_case_limitations']
    assert 'only one parcel' in rows['p1b_H_L2']['ai_case_limitations']
    assert 'User turns' in rows['p1b_H_L3']['ai_case_limitations']
    assert 'only locker' in rows['p1b_D_L1']['ai_case_limitations']
    assert 'Explicit-ID' in rows['p1b_F_L1']['ai_case_limitations']


def test_blank_proposals_cannot_be_registered(materials):
    d,_,m=materials; p=proposals(d,m)
    with pytest.raises(ValueError,match='explicit confirmation'):
        confirmed_copy(m,p,p)


@pytest.mark.parametrize('mutation', ['duplicate','prompt','label','partial','reviewer','method','date','negative'])
def test_confirmation_import_rejects_tampering_or_missing_provenance(materials,mutation):
    d,_,m=materials; p,s=confirmed_fixture(d,m)
    if mutation=='duplicate': s[1]=deepcopy(s[0])
    if mutation=='prompt': s[0]['current_question']='Changed'
    if mutation=='label': s[0]['ai_proposed_evidence_sufficient']='FAIL'
    if mutation=='partial': s[0]['researcher_confirmation']=''
    if mutation=='reviewer': s[0]['reviewer_id']=''
    if mutation=='method': s[0]['review_method']=''
    if mutation=='date': s[0]['reviewed_utc']='made-up'
    if mutation=='negative': s[0]['researcher_confirmation']='REJECT'
    with pytest.raises(ValueError): confirmed_copy(m,p,s)


def test_explicit_confirmation_converts_41_columns_without_inventing_date(materials):
    d,_,m=materials; p,s=confirmed_fixture(d,m); records=confirmed_copy(m,p,s)
    assert len(records)==24 and all(len(r)==41 for r in records)
    assert all(r['reviewed_utc']=='' and 'AI-proposed' in r['review_method'] for r in records)
    assert all(r['check_'+k]=='PASS' for r in records for k in CHECKS)
    assert all(not r['researcher_decision'] for r in m)


@pytest.mark.parametrize('field', ['order','factors','question','applicability','token','count','context','seed','generation','policy'])
def test_frozen_plan_rejects_drift(materials,field):
    d,p,_=materials; p=deepcopy(p); row=p['requests'][0]
    if field=='order': p['requests'][0],p['requests'][1]=p['requests'][1],p['requests'][0]
    if field=='factors': row['factors']['S']=1-row['factors']['S']
    if field=='question': row['prompt']+=' Changed'
    if field=='applicability': row['applicability']['temporal_consistency']=False
    if field=='token': row['input_token_ids'][0]+=1
    if field=='count': row['input_token_count']+=1
    if field=='context': row['remaining_context_after_output_budget']+=1
    if field=='seed': p['order_seed']=42
    if field=='generation': p['generation_parameters']['n_predict']=192
    if field=='policy': p['evaluation_policy_version']='other'
    with pytest.raises(ValueError): core.validate_plan(d,p)


def test_all_evaluation_axes_preserve_eligibility_and_unknown_semantics(materials):
    data,_,_=materials
    for c in data['cases']:
        for raw,backend in [(None,None),('A partial clause',{'stop_type':'limit'}),('Ash Desk.\nUser: next',{'stop_type':'limit'}),('',{'stop_type':'eog'})]:
            e=core.semantic_pending(c,raw,backend)
            assert e['applicability']==c['applicability'] and e['primary_denominator_retained']
            assert not e['persona_fidelity_scored']
            for axis in core.AXES:
                assert e['axes'][axis]['label']==('PENDING' if c['applicability'][axis] else 'Not Applicable')
    assert sum(c['applicability']['temporal_consistency'] for c in data['cases'])==11


def response(row,raw='UNIT TEST response\nUser: next'):
    return {'content':raw,'tokens_evaluated':len(row['input_token_ids']),'prompt':row['input_token_ids'],
            'tokens_predicted':5,'truncated':False,'stop_type':'limit'}


def test_missing_output_ids_remain_absent_and_cross_turn_not_incorrect(materials):
    d,p,_=materials; row=p['requests'][0]; c=next(c for c in d['cases'] if c['case_id']==row['case_id'])
    r=core.result_from_response(row,c,response(row),0.1)
    assert r['token_ids_status']=='absent' and r['generated_token_ids'] is None
    assert r['evaluation']['response_status']['status']=='CROSS_TURN'
    assert r['evaluation']['axes']['factual_consistency']['label']=='PENDING'


def test_raw_response_is_saved_before_completion_validation_fails(materials,local_tmp):
    d,p,_=materials; row=p['requests'][0]; c=next(c for c in d['cases'] if c['case_id']==row['case_id'])
    class InvalidClient:
        def complete(self,ids,**kwargs): return {**response(row),'tokens_evaluated':1}
    j=RunJournal(local_tmp,{'purpose':'unit test only'})
    with pytest.raises(ValueError,match='Prompt token mismatch'):
        core.attempt_one(row,c,InvalidClient(),j)
    events=read_events(j.directory)
    assert [e['kind'] for e in events]==['p1b_generation_started','p1b_raw_generation']
    inventory=core.resume_inventory(p,[events])
    assert inventory['pending'][0]['request_id']==p['requests'][1]['request_id']
    assert len(inventory['attempted_without_result'])==1


def test_audit_recovers_raw_without_new_model_calls_and_keeps_all_denominators(materials,local_tmp):
    d,p,_=materials; row=p['requests'][0]; cases={c['case_id']:c for c in d['cases']}
    j=RunJournal(local_tmp,{'purpose':'unit test raw interruption'})
    j.write('p1b_generation_started',row)
    j.write('p1b_raw_generation',{'request_id':row['request_id'],'response':response(row),'latency_seconds':0.1})
    result=core.audit_segments(p,cases,[read_events(j.directory)])
    assert len(result['rows'])==192 and result['rows'][0]['technical_status']=='RAW_RECOVERABLE_WITHOUT_GENERATION'
    assert result['rows'][1]['technical_status']=='UNATTEMPTED'
    assert result['rows'][1]['evaluation']['axes']['factual_consistency']['label']=='PENDING'


@pytest.mark.parametrize('problem',['duplicate','skip','orphan_result','orphan_raw','changed_input'])
def test_resume_refuses_reordering_duplicates_or_orphans(materials,problem):
    _,p,_=materials; row=deepcopy(p['requests'][0])
    events=[{'kind':'p1b_generation_started','data':row}]
    if problem=='duplicate': events*=2
    if problem=='skip': events[0]['data']=p['requests'][1]
    if problem=='orphan_result': events=[{'kind':'p1b_result','data':{'request_id':row['request_id']}}]
    if problem=='orphan_raw': events=[{'kind':'p1b_raw_generation','data':{'request_id':row['request_id']}}]
    if problem=='changed_input': row['prompt']='changed'
    with pytest.raises(ValueError): core.resume_inventory(p,[events])


def auth_fixture(materials):
    d,_,master=materials; p,s=confirmed_fixture(d,master)
    records=confirmed_copy(master,p,s)
    review={'records':records,'interpretation_confirmed':True,'evaluation_routing_confirmed':True,
            'manifest_sha256':core.MANIFEST_SHA,'dataset_sha256':core.DATA_SHA}
    auth={'authorized':True,'final_decision_authority':'researcher','researcher_id':'Yaxin_ZHENG',
          'decision_source':'UNIT TEST fixture only','manifest_sha256':core.MANIFEST_SHA,'dataset_sha256':core.DATA_SHA,
          'max_total_attempts':192,'review_registration_sha256':'r','preflight_sha256':'p',
          'adapter_version':core.VERSION,'allow_automatic_retries':False}
    prepared={'technical_readiness':'PASS','manifest_sha256':core.MANIFEST_SHA}
    return auth,review,master,prepared


@pytest.mark.parametrize('field',['authorized','review_hash','manifest','attempts','review','scope','source'])
def test_explicit_authorization_gate(materials,field):
    a,r,m,p=auth_fixture(materials)
    if field=='authorized': a['authorized']=False
    if field=='review_hash': a['review_registration_sha256']='different'
    if field=='manifest': a['manifest_sha256']='different'
    if field=='attempts': a['max_total_attempts']=193
    if field=='review': r['records'][0]['check_context_valid']='UNCERTAIN'
    if field=='scope': r['interpretation_confirmed']=False
    if field=='source': a['decision_source']=''
    with pytest.raises(ValueError): core.verify_authorization(a,r,m,p,actual_review_hash='r',actual_preflight_hash='p')


def test_valid_authorization_contract_only(materials):
    a,r,m,p=auth_fixture(materials)
    core.verify_authorization(a,r,m,p,actual_review_hash='r',actual_preflight_hash='p')


def test_pending_authorization_cannot_launch_server(materials,local_tmp,monkeypatch):
    def forbidden(*args,**kwargs): pytest.fail('An unapproved run must not touch a server')
    monkeypatch.setattr(core,'ManagedServer',forbidden)
    for name in ('auth','review','preflight'):
        (local_tmp/(name+'.json')).write_text('{}')
    with pytest.raises(ValueError,match='authorization is missing'):
        core.run_authorized(local_tmp/'auth.json',local_tmp/'review.json',local_tmp/'preflight.json')


def test_exclusive_lock_does_not_remove_someone_elses_lock(local_tmp):
    with core.writer_lock(local_tmp):
        with pytest.raises(FileExistsError):
            with core.writer_lock(local_tmp): pass
        assert (local_tmp/'active_writer.lock').exists()
    assert not (local_tmp/'active_writer.lock').exists()


def test_offline_preflight_never_launches_network_or_server(materials,monkeypatch):
    def forbidden(*args,**kwargs): pytest.fail('Offline preflight cannot use a live server/client')
    monkeypatch.setattr(core,'ManagedServer',forbidden)
    monkeypatch.setattr(core,'LlamaClient',forbidden)
    # Artifact hashes tested by actual preflight separately; avoid rehashing 1.27 GB in this unit test.
    monkeypatch.setattr(core,'pinned_runtime',lambda p:(None,{'model':{'sha256':core.MODEL_SHA},'server':{'sha256':core.BACKEND_SHA}}))
    result=core.offline_preflight()
    assert result['native_tokenizations_reconciled']==192 and result['new_server_launches']==0


@pytest.mark.parametrize('mode',['interrupt_resume','token_mismatch'])
def test_adapter_segments_use_frozen_order_and_no_duplicate_send(materials,local_tmp,monkeypatch,mode):
    _,plan,_=materials
    config=RuntimeConfig.load(Path('configs/p1_wave1_v1.json'))
    monkeypatch.setattr(core,'RUN_ROOT',local_tmp/'wave')
    monkeypatch.setattr(core,'verify_authorization',lambda *a,**k:None)
    monkeypatch.setattr(core,'offline_preflight',lambda:None)
    monkeypatch.setattr(core,'source_inventory',lambda:{})
    monkeypatch.setattr(core,'pinned_runtime',lambda p:(config,{'status':'UNIT_TEST_DOUBLE'}))
    for name in ('auth','review','preflight'):
        (local_tmp/(name+'.json')).write_text(json.dumps({'source_hashes':{}}))
    calls=[]; token_calls=[]; fail=[True]
    texts={r['prompt']:r['input_token_ids'] for r in plan['requests']}
    ids={tuple(r['input_token_ids']):r for r in plan['requests']}
    class ServerDouble:
        def __init__(self,*a): pass
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def assert_running(self): pass
    class ClientDouble:
        def __init__(self,*a,**k): self.tokens=0
        def request(self,route):
            assert route=='/props'
            return {'model_path':config.model_file,'default_generation_settings':{'n_ctx':4096},'build_info':'b11573-0f701c882'}
        def tokenize(self,text):
            self.tokens+=1; token_calls.append(text)
            return [1] if mode=='token_mismatch' else texts[text]
        def complete(self,prompt,**kwargs):
            assert self.tokens==192 and kwargs=={'seed':42,'max_new_tokens':96}
            row=ids[tuple(prompt)]; calls.append(row['request_id'])
            if fail[0] and len(calls)==2:
                fail[0]=False; raise KeyboardInterrupt('UNIT TEST interruption before raw response')
            return response(row)
    monkeypatch.setattr(core,'ManagedServer',ServerDouble); monkeypatch.setattr(core,'LlamaClient',ClientDouble)
    args=[local_tmp/'auth.json',local_tmp/'review.json',local_tmp/'preflight.json']
    _,first=core.run_authorized(*args)
    if mode=='token_mismatch':
        assert first['status']=='BLOCKED' and calls==[]
        return
    assert first['status']=='PARTIAL' and first['attempted']==2 and first['responses_received']==1
    _,second=core.run_authorized(*args,resume=True)
    assert second['status']=='PASS' and second['attempted']==190
    assert calls==[r['request_id'] for r in plan['requests']]
    assert len(token_calls)==384
    with pytest.raises(ValueError,match='No unattempted'):
        core.run_authorized(*args,resume=True)
    claim=core.load(local_tmp/'wave/claim.json')
    segments=[read_events(p) for p,_ in core.ordered_segments(local_tmp/'wave',claim)]
    inventory=core.resume_inventory(plan,segments)
    assert len(inventory['results'])==191 and len(inventory['attempted_without_result'])==1


def test_segment_order_uses_explicit_index_not_uuid_name(local_tmp):
    for name,index in [('z-first',1),('a-second',2)]:
        folder=local_tmp/'runs'/name; folder.mkdir(parents=True)
        (folder/'manifest.json').write_text(json.dumps({'claim':{},'segment_index':index}))
    assert [p.name for p,_ in core.ordered_segments(local_tmp,{})]==['z-first','a-second']
    (local_tmp/'runs/a-second/manifest.json').write_text(json.dumps({'claim':{},'segment_index':1}))
    with pytest.raises(ValueError,match='Duplicate or missing'):
        core.ordered_segments(local_tmp,{})

