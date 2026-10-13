"""Independent oracle, routing, and failure tests for proposed offline stimuli."""
from copy import deepcopy
import math

import pytest

from personaslm.p1b import (build_dataset, validate_dataset, solve, prompt, active,
                           precision, render_evidence)
from personaslm.conditioning import FACTORIAL


def case(cid):
    return next(c for c in build_dataset()['cases'] if c['case_id']==cid)


def test_full_development_allocation_and_no_empirical_claim():
    d=build_dataset();r=validate_dataset(d)
    assert r['prompt_count']==192
    assert r['empirical_discrimination']=='UNTESTED'
    assert all(c['empirical_difficulty'] is None and c['actual_prompt_token_counts'] is None for c in d['cases'])


@pytest.mark.parametrize('cid,expected',[
    ('p1b_C_L1',{'counter':'Birch Counter'}),
    ('p1b_C_L2',{'counter':'Cedar Counter'}),
    ('p1b_C_L3',{'counter':'Cedar Counter','previous_counter':'Birch Counter'}),
    ('p1b_G_L2',{'site':'Meadow Lodge'}),
    ('p1b_G_L3',{'site':'Meadow Lodge','current_site':'Harbor Lodge'}),
    ('p1b_E_L3',{'day':'Thursday'}),
    ('p1b_F_L3',{'shelf':'Amber Shelf'}),
    ('p1b_H_L3',{'desk':'Ash Desk'}),
])
def test_independently_specified_answers(cid,expected):
    assert solve(case(cid))['components']==expected


def test_inclusive_temporal_boundaries():
    f={'valid_from':'2027-04-01','valid_until':'2027-04-09'}
    assert active(f,'2027-04-01') and active(f,'2027-04-09')
    assert not active(f,'2027-03-31') and not active(f,'2027-04-10')


def test_missing_link_refuses_unsupported_answer():
    c=case('p1b_D_L3');c['facts']=c['facts'][1:]
    with pytest.raises(ValueError,match='exactly one'):solve(c)


def test_ambiguous_role_refuses_answer():
    c=case('p1b_F_L3')
    next(f for f in c['facts'] if f['value']=='treasurer')['value']='archivist'
    with pytest.raises(ValueError,match='exactly one'):solve(c)


def test_wrong_entity_distractor_does_not_change_answer():
    c=case('p1b_F_L3');expected=solve(c)['components']
    next(f for f in c['facts'] if f['value']=='Violet Shelf')['value']='Scarlet Shelf'
    assert solve(c)['components']==expected


def test_context_is_required_and_preserved():
    c=case('p1b_H_L3');c['context']=[]
    with pytest.raises(ValueError,match='verbatim source'):solve(c)


@pytest.mark.parametrize('condition,bits',list(FACTORIAL.items()))
def test_factor_routing_independent_of_answer(condition,bits):
    c=case('p1b_D_L3');text=prompt(c,condition)
    assert ('Speaker style profile:' in text)==bool(bits[0])
    assert ('Additional fact:' in text)==bool(bits[1])
    assert ('Historical dialogue (' in text)==bool(bits[2])
    assert text.count(c['trusted_evidence'])==1
    assert '\n'.join(c['context']) in text
    assert text.endswith('User: '+c['question']+'\nAssistant:')
    assert text.index(c['trusted_evidence'])==prompt(c,'C0').index(c['trusted_evidence'])


@pytest.mark.parametrize('mutation', ['answer','evidence','overlap','leak','scope'])
def test_invalid_material_rejected(mutation):
    d=build_dataset();c=d['cases'][0]
    if mutation=='answer':c['expected_answer']['components']['room']='Unsupported room'
    elif mutation=='evidence':c['trusted_evidence']='Missing source'
    elif mutation=='overlap':
        f=deepcopy(c['facts'][0]);f['fact_id']='extra';f['value']='Other room';c['facts'].append(f)
        c['trusted_evidence']=render_evidence(c['facts'])
    elif mutation=='leak':c['style_only']+=' '+c['expected_answer']['components']['room']
    else:c['inference_authorized']=True
    with pytest.raises(ValueError):validate_dataset(d)


def test_cluster_precision_formula_and_multiplicity():
    r=precision(24,8,.3,.2)
    assert r['design_effect']==pytest.approx(2.4)
    assert r['effective_case_count']==pytest.approx(80)
    assert r['half_width']==pytest.approx(1.959963984540054*math.sqrt(.3/80))
    assert precision(48,8,.3,.2)['half_width']==pytest.approx(r['half_width']/math.sqrt(2))
    assert precision(24,8,.3,.2,comparisons=8)['half_width']>r['half_width']
    assert precision(24,8,.3,0)['half_width']<r['half_width']


@pytest.mark.parametrize('q,d',[(-.1,0),(.1,.2),(1.1,0)])
def test_impossible_precision_assumptions_rejected(q,d):
    with pytest.raises(ValueError):precision(24,8,q,.2,d)
