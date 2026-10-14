"""Non-generation checks of the newly authorized boundary/stop diagnostic."""
import copy
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1d_format_calibration as f

def plan():return f.load(f.MANIFEST)

def test_exact_authorized_source():
    assert f.sha256(f.MANIFEST)==f.MANIFEST_SHA
    assert f.validate_plan(plan())['requests']==16

@pytest.mark.parametrize('key,value',[('order',9),('case_id','heldout'),('condition','E0V0'),('max_new_tokens',192),('seed',43),('stop',['NEW']),('prompt','replacement'),('reference',[])])
def test_reject_changed_frozen_inputs(key,value):
    p=plan();p['requests'][0][key]=value
    with pytest.raises((ValueError,KeyError)):f.validate_plan(p)

def test_payload_only_adds_registered_stop_override():
    from personaslm.inference import LlamaClient
    client=LlamaClient('http://127.0.0.1:8080');calls=[]
    client.request=lambda route,payload:calls.append(payload)
    for r in plan()['requests']:
        client.complete(r['input_token_ids'],seed=r['seed'],max_new_tokens=96)
        expected=calls[-1];expected['stop']=r['stop']
        assert f.payload(r)==expected

def test_no_repeated_or_reordered_attempts():
    p=plan();e={'kind':'format_generation_started','data':p['requests'][0]}
    assert len(f.inventory(p,[e])[0])==1
    with pytest.raises(ValueError):f.inventory(p,[e,e])
    with pytest.raises(ValueError):f.inventory(p,[{'kind':e['kind'],'data':p['requests'][1]}])

def test_native_stop_is_not_automatic_semantic_completion():
    r=next(r for r in plan()['requests'] if r['stop'])
    raw={'content':'I will check.','truncated':False,'tokens_evaluated':r['input_tokens'],
        'tokens_predicted':7,'tokens':[1,2,3,4],'stop_type':'word','stopping_word':'\nUser:'}
    out=f.result(r,raw,1.0)
    assert out['response_status']['status']=='AMBIGUOUS'
    assert out['response_status']['unit_identifiable'] is True
    assert out['native_minus_returned_tokens']==3
    raw['stopping_word']='UNREGISTERED'
    with pytest.raises(ValueError):f.result(r,raw,1.0)

def test_non_stop_token_count_mismatch_rejected():
    r=plan()['requests'][0]
    raw={'content':'Wait.','truncated':False,'tokens_evaluated':r['input_tokens'],'tokens_predicted':4,'tokens':[1,2],'stop_type':'limit'}
    with pytest.raises(ValueError):f.result(r,raw,1)
