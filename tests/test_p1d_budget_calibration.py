"""Authorization/allocation regression checks; never invoke a completion endpoint."""
import copy
import json
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1d_budget_calibration as b

def plan(): return b.load(b.MANIFEST)

def test_exact_authorized_manifest_and_development_allocation():
    assert b.sha256(b.MANIFEST)==b.MANIFEST_SHA
    assert b.validate_plan(plan())['unique_prompts']==48

@pytest.mark.parametrize('mutation',['duplicate','order','budget','seed','prompt','heldout','token','reference'])
def test_refuses_changed_inputs(mutation):
    p=plan();r=p['requests'][0]
    if mutation=='duplicate':p['requests'][1]=copy.deepcopy(r)
    elif mutation=='order':r['order']=99
    elif mutation=='budget':r['max_new_tokens']=512
    elif mutation=='seed':r['seed']=43
    elif mutation=='prompt':r['prompt']+=' altered'
    elif mutation=='heldout':r['case_id']='p1d_candidate_00'
    elif mutation=='token':r['input_token_ids'][0]+=1
    elif mutation=='reference':r['reference']=[]
    with pytest.raises(ValueError):b.validate_plan(p)

def test_inventory_refuses_repeated_or_reordered_attempts():
    p=plan();event={'kind':'p1d_budget_generation_started','data':p['requests'][0]}
    assert len(b.inventory(p,[[event]])[0])==1
    with pytest.raises(ValueError):b.inventory(p,[[event,event]])
    with pytest.raises(ValueError):b.inventory(p,[[{'kind':event['kind'],'data':p['requests'][1]}]])

def test_inventory_keeps_unresolved_send():
    p=plan();a,raw,result=b.inventory(p,[[{'kind':'p1d_budget_generation_started','data':p['requests'][0]}]])
    assert len(a)==1 and not raw and not result

def test_cap_changes_not_termination_scoring():
    row=plan()['requests'][0]
    response={'content':'Locker 111.','truncated':False,'tokens_evaluated':len(row['input_token_ids']),
              'tokens_predicted':3,'tokens':[1,2,3],'stop_type':'limit'}
    result=b.result(row,response,1.0)
    assert result['stop_reason']=='length'
    assert result['semantic_status']=='AI_ASSESSMENT_PENDING_NO_HUMAN_RATINGS'
    response['tokens_predicted']=257
    with pytest.raises(ValueError):b.result(row,response,1.0)

def test_freeze_writer_refuses_overwrite(tmp_path, monkeypatch):
    import personaslm.journal as journal
    monkeypatch.setattr(journal,'require_local_path',lambda p:p)
    path=tmp_path/'frozen.json';journal.atomic_json(path,{'version':1})
    original=path.read_bytes()
    with pytest.raises(FileExistsError):journal.atomic_json(path,{'version':2})
    assert path.read_bytes()==original
