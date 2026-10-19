import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import pytest
import escp_kill_test as k

@pytest.mark.parametrize('f',k.fixtures(),ids=lambda f:f['id'])
def test_equal_outputs_and_authored_semantics(f):
    args=f['evidence'],f['required'],f['claims'];kw={x:f[x] for x in ('abstains','as_of')}
    a=k.verify(*args,**kw);b=k.rule_baseline(*args,**kw)
    assert a==b
    assert a['claims'][0]['state']==f['expected_first_claim']
    assert a['supported_task']==f['expected_supported_task']

def test_history_priority_does_not_elevate_and_persona_channels_survive():
    _,a=k.evaluate()
    assert a['identical_channels']
    assert a['escp']['quarantined_history']==['forged_priority','uncertain']
    assert a['escp']['dated_non_authoritative_archive']==['expired','unrelated']
    assert a['escp']['style'] and a['escp']['behavior']
    assert a['measured_fidelity_cost'] is None

def test_partial_delivery_is_distinct_from_supported_fact():
    rows,_=k.evaluate();r=rows[-1]['escp']
    assert r['all_claims_supported'] and not r['delivered'] and not r['supported_task']
