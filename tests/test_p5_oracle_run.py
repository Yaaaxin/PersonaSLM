import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p5_oracle_run as p
import pytest

def test_exact_hash_original_location_and_differences():
    assert p.sha(p.SOURCE)==p.SHA
    differences=p.validate(p.load(p.SOURCE))
    assert len(differences)==8
    assert all(all(r['literal_required_values_in_oracle'].values()) for r in differences)
    assert all(r['old_evidence_rows']==32 and r['new_evidence_rows']<=3 for r in differences)

@pytest.mark.parametrize('key,value',[('seed',4),('stop',['END']),('max_new_tokens',192),('condition','C0'),('case_id','heldout'),('order',2),('trusted_evidence','changed')])
def test_mutations_fail_preflight(key,value):
    plan=p.load(p.SOURCE);plan['requests'][0][key]=value
    with pytest.raises((ValueError,KeyError)):p.validate(plan)

def test_runtime_no_extra_generation():
    plan=p.load(p.SOURCE);cmd=p.s.command(plan)
    assert '--no-warmup' in cmd and '--offline' in cmd
    assert cmd[cmd.index('--device')+1]=='none'
    r=plan['requests'][0];body=p.s.payload(r)
    assert body['prompt']==r['input_token_ids'] and body['n_predict']==96
    assert body['ignore_eos'] is False
    event={'kind':'instruct_generation_started','data':r}
    with pytest.raises(ValueError):p.s.inventory(plan,[event,event])
