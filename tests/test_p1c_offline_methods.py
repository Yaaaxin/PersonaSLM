"""Numerical fixtures are synthetic test values, never model generations."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1c_paired_statistics as s
import p1c_decision_compatibility as c
import development_component_baseline as b


def test_all_registered_contrasts_annihilate_constant_and_ignore_zero_weight_missing():
    weights=c.policy_audit()['weights']
    for w in weights.values():
        result=s.case_contrast({k:.6 for k,v in w.items() if v},w)
        assert result['estimate']==pytest.approx(0)


def test_factorial_scale_and_interaction_not_halved():
    weights=c.policy_audit()['weights'];values=dict(zip(c.policy_audit()['condition_ids'],[0,0,0,1,None,None]))
    assert s.case_contrast(values,weights['R'])['estimate']==.5
    assert s.case_contrast(values,weights['T'])['estimate']==.5
    assert s.case_contrast(values,weights['RxT'])['estimate']==1
    assert s.case_contrast({},weights['RxT'])['lower_bound']==-2
    assert s.case_contrast({},weights['RxT'])['upper_bound']==2


def test_unknown_keeps_weights_and_signed_bounds():
    r=s.case_contrast({'a':1,'b':None},{'a':1,'b':-1})
    assert r['estimate'] is None and [r['lower_bound'],r['upper_bound']]==[0,1]


def test_equal_speaker_weight_and_cluster_replay():
    rows=[{'case_id':'a','speaker_id':'s1','values':{'x':1,'y':0}},
          {'case_id':'b','speaker_id':'s1','values':{'x':1,'y':0}},
          {'case_id':'c','speaker_id':'s2','values':{'x':0,'y':0}}]
    result=s.summarize(rows,{'x':1,'y':-1},replicates=200)
    assert result['estimate']==.5
    assert result==s.summarize(list(reversed(rows)),{'x':1,'y':-1},replicates=200)
    assert [r['estimate'] for r in result['leave_one_speaker_out']]==[0,1]
    rows[0]['values']['x']=None
    result=s.summarize(rows,{'x':1,'y':-1},replicates=200)
    assert result['estimate'] is None and result['percentile_cluster_interval'] is None
    assert result['evaluable_cases']==2 and result['assessed_only_sensitivity']['estimate']==.5


@pytest.mark.parametrize('value',[float('nan'),float('inf'),2,-1])
def test_invalid_binary_value_rejected(value):
    with pytest.raises(ValueError):s.case_contrast({'a':value,'b':0},{'a':1,'b':-1})


def test_ordinal_bounds_are_not_binary_bounds():
    r=s.case_contrast({}, {'a':1,'b':-1},1,5)
    assert [r['lower_bound'],r['upper_bound']]==[-4,4]


def test_literal_match_word_boundaries_and_case():
    assert b.contains_phrase('CEDAR Hall 5.', 'Cedar Hall 5')
    assert not b.contains_phrase('Cedar Hall 50', 'Cedar Hall 5')
    assert not b.contains_phrase('Cedar and Hall 5', 'Cedar Hall 5')


def test_presence_does_not_claim_support_or_temporal_validity():
    assert b.contains_phrase('It is NOT Cedar Hall 5.', 'Cedar Hall 5')
    assert 'Mention is not assertion' in b.POLICY['limitations']
