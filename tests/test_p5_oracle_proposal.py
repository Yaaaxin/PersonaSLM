import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p5_oracle_proposal as p
import copy
import pytest

@pytest.mark.parametrize('case_id',p.s.b.CASE_IDS)
def test_proof_sources_stay_in_development(case_id):
    c=next(c for c in p.s.load(p.s.b.DEV/'development_examples_v5.json')['cases'] if c['case_id']==case_id)
    ids=p.proof_ids(c)
    assert 1<=len(ids)<=3
    assert {x['source_id'] for x in c['required_components']}<=set(ids)
    assert c['independent_validation'] is False

def test_bad_reference_rejected():
    c=copy.deepcopy(p.s.load(p.s.b.DEV/'development_examples_v5.json')['cases'][0])
    c['required_components'][0]['value']='WRONG'
    with pytest.raises(ValueError):p.proof_ids(c)
