"""Transport-free test fixtures only; no model outputs are simulated for research."""
import copy
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1c_calibration as c


def test_actual_authorization_exact_manifest_and_three_decisions():
    assert c.approvals.validate_approval(c.load(c.AUTHORIZATION),c.REGISTRATION)==[]
    plan=c.load(c.p.MANIFEST)
    assert plan['generation_parameters']==c.DECODING
    assert len({c.key(r) for r in plan['requests']})==72


@pytest.fixture
def plan():return c.load(c.p.MANIFEST)


def test_uncertain_attempt_not_retried_and_order_preserved(plan):
    row=plan['requests'][0];events=[{'kind':'p1c_generation_started','data':row}]
    inv=c.inventory(plan,[events]);assert inv['pending']==plan['requests'][1:]
    assert c.key(row) in inv['attempted'] and not inv['raw']
    with pytest.raises(ValueError):c.inventory(plan,[events,events])
    with pytest.raises(ValueError):c.inventory(plan,[[{'kind':'p1c_generation_started','data':plan['requests'][1]}]])


def test_raw_before_transform_and_duplicate_result_rejected(plan):
    row=plan['requests'][0];rid=c.key(row)
    events=[{'kind':'p1c_generation_started','data':row},{'kind':'p1c_raw_generation','data':{'request_key':rid}},
            {'kind':'p1c_result','data':{'request_key':rid}}]
    assert len(c.inventory(plan,[events])['results'])==1
    with pytest.raises(ValueError):c.inventory(plan,[events+[events[-1]]])
    with pytest.raises(ValueError):c.inventory(plan,[events[1:]])


def test_response_structure_not_factual_error(plan):
    row=plan['requests'][0]
    response={'content':'Example answer.\nUser: Another question','truncated':False,
              'tokens_evaluated':len(row['input_token_ids']),'tokens_predicted':4,'tokens':[1,2,3,4],'stop_type':'limit'}
    result=c.result_from_response(row,response,.1)
    assert result['response_status']['status']=='CROSS_TURN'
    assert result['semantic_evaluation']['labels']=={}
    assert result['semantic_evaluation']['status']=='AWAITING_HUMAN_REVIEW'
    response['tokens_evaluated']-=1
    with pytest.raises(ValueError):c.result_from_response(row,response,.1)


def test_tokenizer_failure_blocks_before_completion(plan,monkeypatch):
    config=c.RuntimeConfig.load(Path('configs/p1_wave1_v1.json'));events=[]
    class Journal:
        def write(self,k,v):events.append((k,v))
    class Client:
        def request(self,route):
            assert route=='/props';return {}
        def tokenize(self,prompt):return [999999]
        def complete(self,*args,**kwargs):raise AssertionError('Generation not permitted in preflight')
    monkeypatch.setattr(c,'validate_server_properties',lambda *a:{'build_info':'b11573-0f701c882'})
    with pytest.raises(ValueError,match='Live tokenization'):c.live_preflight(plan,config,Client(),Journal())
    assert not any(k=='live_preflight_pass' for k,_ in events)


def test_complete_live_preflight_checks_every_prompt_without_generating(plan,monkeypatch):
    events=[];calls=[];by_prompt={r['prompt']:r['input_token_ids'] for r in plan['requests']}
    class Journal:
        def write(self,k,v):events.append((k,v))
    class Client:
        def request(self,route):assert route=='/props';return {}
        def tokenize(self,prompt):calls.append(prompt);return by_prompt[prompt]
    monkeypatch.setattr(c,'validate_server_properties',lambda *a:{'build_info':'b11573-0f701c882'})
    c.live_preflight(plan,None,Client(),Journal())
    assert calls==[r['prompt'] for r in plan['requests']]
    assert events[-1]==('live_preflight_pass',{'requests_verified':72,'generation_requests_so_far':0})
