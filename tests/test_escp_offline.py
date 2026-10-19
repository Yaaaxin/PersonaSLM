import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from escp_offline import *
import pytest

@pytest.mark.parametrize('f',fixtures(),ids=lambda f:f['id'])
def test_authored_expectations(f):
    assert verify(f['evidence'],f['required'],f['claims'],abstains=f['abstains'])['supported_task']==f['expected_supported_task']
    assert simple_rule_reference(f['evidence'],f['required'],f['claims'],abstains=f['abstains'])==f['expected_supported_task']

def test_untrusted_priority_and_persona_channels():
    f=fixtures()[0];a=replace(f['evidence'][1],source='h',value='L9',trust_priority=999999)
    out=admit(f['evidence'],[a],f['required'],['brief'],['answer first'])
    assert out['quarantined_history']==['h'] and out['style']==['brief'] and out['behavior']==['answer first']
    assert out['trusted_evidence_ids']==[a.source for a in f['evidence']]

def test_assertion_date_is_not_validity_date():
    f=fixtures()[0];e=[replace(a,asserted_at='2048-12-31') for a in f['evidence']]
    assert verify(e,f['required'],f['claims'])['supported_task']
    assert not verify(e,f['required'],f['claims'],as_of='2048-05-15')['supported_task']

def test_invalid_dates_fail_closed():
    with pytest.raises(ValueError):Atom('x','M','a','v','2048-12-31','2048-01-01')

def test_factual_correctness_does_not_entail_delivery():
    f=next(x for x in fixtures() if x['id']=='correct_intermediate_incomplete')
    out=verify(f['evidence'],f['required'],f['claims'])
    assert out['all_claims_supported'] and not out['supported_task'] and not out['delivered']
