import copy
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1d_instruct_smoke as s

def test_exact_registered_plan_and_native_sources():
    assert s.sha256(s.SOURCE)==s.SHA
    assert s.validate_plan(s.load(s.SOURCE))['requests']==8

@pytest.mark.parametrize('key,value',[('seed',43),('stop',['END']),('max_new_tokens',192),('ignore_eos',True),
    ('condition','E0V0'),('case_id','validation_case'),('prompt','new text'),('order',9)])
def test_frozen_changes_rejected(key,value):
    p=s.load(s.SOURCE);p['requests'][0][key]=value
    with pytest.raises((ValueError,KeyError)):s.validate_plan(p)

def test_no_warmup_or_speculation_or_vision():
    p=s.load(s.SOURCE);cmd=s.command(p)
    assert '--no-warmup' in cmd and '--no-mmproj' in cmd
    assert cmd[cmd.index('--spec-type')+1]=='none'
    assert cmd[cmd.index('--device')+1]=='none'
    assert cmd[cmd.index('--threads')+1]=='4' and cmd[cmd.index('--ctx-size')+1]=='4096'
    assert cmd[cmd.index('--chat-template-file')+1]==str(Path(p['template_path']).resolve())

def test_exact_completion_payload_and_no_hidden_template():
    r=s.load(s.SOURCE)['requests'][0];p=s.payload(r)
    assert p=={'prompt':r['input_token_ids'],'n_predict':96,'temperature':0.0,'top_p':1.0,
        'seed':42,'cache_prompt':False,'stop':[],'ignore_eos':False,'return_tokens':True,'stream':False}

def test_duplicate_attempt_or_reorder_refused():
    p=s.load(s.SOURCE);event={'kind':'instruct_generation_started','data':p['requests'][0]}
    assert len(s.inventory(p,[event])[0])==1
    with pytest.raises(ValueError):s.inventory(p,[event,event])
    with pytest.raises(ValueError):s.inventory(p,[{'kind':event['kind'],'data':p['requests'][1]}])

def test_instruct_config_does_not_claim_base_prompt_template():
    cfg=s.config(s.load(s.SOURCE))
    assert cfg.prompt_template=='explicit_official_nonthinking_token_ids_v1'
    assert cfg.max_new_tokens==96 and cfg.model_sha256==s.MODEL_SHA
