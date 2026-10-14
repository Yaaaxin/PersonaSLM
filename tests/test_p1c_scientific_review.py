"""Prospective identification and preservation checks; no inference."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1c_scientific_review as review
import p1c_design as d


@pytest.fixture(scope='module')
def audit():
    return review.build_audit()


def test_original_condition_ids_and_request_order(audit):
    assert audit['summary']['conditions']==['R0T0','R0T1','R1T0','R1T1','N_history','H_none']
    assert audit['summary']['planned_identities']==72
    assert audit['summary']['speakers']==6


@pytest.mark.parametrize('index',range(12))
def test_each_case_counterfactual_dependencies(index):
    c=d.read(d.DATA)['cases'][index]
    check=review.counterfactual_checks(c)
    assert check['auxiliary_deletion_answer_unchanged']
    assert check['required_deletions_make_reference_unanswerable']==c['reference']['fact_ids']


def test_dependency_checker_rejects_wrong_reference():
    c=copy.deepcopy(d.read(d.DATA)['cases'][0])
    c['facts']=[f for f in c['facts'] if f['fact_id']!=c['reference']['fact_ids'][0]]
    with pytest.raises(ValueError,match='Missing or nonunique'):
        review.counterfactual_checks(c)


def test_time_is_interval_and_value_package(audit):
    pairs=[p for p in audit['counterfactual_pairs'] if p['factor_changes']==['T']]
    assert len(pairs)==24
    assert all(p['same_predicate'] and not p['same_value'] and not p['same_interval'] for p in pairs)
    assert all(p['validity_a'] is False and p['validity_b'] is True for p in pairs)


def test_topic_is_not_answer_competition(audit):
    active=[r for r in audit['cell_audit'] if r['condition'] in review.RT]
    assert len(active)==48
    assert all(not r['source_used_by_answer_solver'] and not r['answer_strings_present'] for r in active)
    assert audit['summary']['same_color_cross_topic_pairs']==12


def test_comparable_format_not_semantic_equivalence(audit):
    assert len(audit['counterfactual_pairs'])==72
    assert all(p['same_turns_roles_archive_date'] and p['token_difference']==0 for p in audit['counterfactual_pairs'])
    assert not any(p['same_proposition_entity_predicate_value'] for p in audit['counterfactual_pairs'])


def test_original_neutral_failure_is_preserved(audit):
    repairs=audit['neutral_repair_inventory']
    assert len(repairs)==12
    assert all(r['original_difference']==-1 and r['repaired_difference']==0 for r in repairs)
    assert all(r['original_text'].replace('its two parts.','its two distinct parts.')==r['repaired_text'] for r in repairs)


@pytest.mark.parametrize('name,count',[('case_review',12),('history_text_review',60),('neutral_review',12)])
def test_reviewer_fields_are_blank(audit,name,count):
    assert len(audit[name])==count
    for r in audit[name]:
        assert r['AI_assisted_recommendation']
        assert all(not v for k,v in r.items() if k.startswith('researcher_') or k=='reviewer_id')


def test_exact_factorial_weights_on_independent_polynomial():
    # Independent mathematical test, not a simulated model observation.
    spec=review.contrast_spec()['weights']
    y={c:2+3*v['R']+5*v['T']+7*v['R']*v['T'] for c,v in d.CONDITIONS.items() if c in review.RT}
    y.update(N_history=100,H_none=-100)
    calculate=lambda key:sum(w*y[c] for c,w in spec[key].items())
    assert calculate('R')==6.5
    assert calculate('T')==8.5
    assert calculate('RxT')==7
    assert calculate('R1T0-R0T0')==3
    assert calculate('R1T1-R0T1')==10
    assert all(sum(w.values())==0 for w in spec.values())


def test_unknown_is_not_automatically_incorrect():
    weights=review.contrast_spec()['weights']['RxT']
    assert review.unknown_bounds(weights,{c:None for c in review.CELLS})==(-2,2)
    values={c:0 for c in review.CELLS};values['R0T0']=None
    assert review.unknown_bounds(weights,values)==(0,1)
    values['R0T0']=0;values['R0T1']=None
    assert review.unknown_bounds(weights,values)==(-1,0)


def test_inventory_accounts_for_every_original_record_field(audit):
    fields=set(d.read(review.V2/'selected_prompts_v2.json')['records'][0])
    for c in d.read(d.DATA)['cases']:
        rows=[r for r in audit['intervention_difference_inventory'] if r['case_id']==c['case_id'] and r['scope']=='selected_prompt_record']
        assert {r['field'] for r in rows}==fields


def test_no_history_length_not_claimed_matched(audit):
    assert audit['summary']['no_history_token_differences']=={65:10,66:2}
    assert audit['summary']['stimulus_changes']==audit['summary']['generation_executed']==0


def test_native_recheck_is_exact_and_non_generation():
    r=d.read(review.OUT/'native_reverification_v1.json')
    assert len(r['records'])==72 and all(x['all_ids_equal'] for x in r['records'])
    assert r['new_generations']==0 and r['identity']['no_generation']


def test_historical_requested_date_is_not_newest(audit):
    historical=[c for c in d.read(d.DATA)['cases'] if c['query_mode']=='historical']
    assert len(historical)==6
    for c in historical:
        assert d.ground_truth(c)['components']!=d.ground_truth({**c,'requested_date':'2042-12-15'})['components']
        r=next(r for r in audit['cell_audit'] if r['case_id']==c['case_id'] and r['condition']=='R1T1')
        assert r['archive_is_after_requested_date'] and r['valid_at_requested_date']


def test_freeze_candidate_does_not_authorize_execution():
    x=d.read(review.OUT/'calibration_freeze_candidate_v1.json')
    assert x['status']=='INPUT_SNAPSHOT_ONLY_NOT_EXECUTION_FREEZE'
    assert x['generation_authorized'] is False
    assert x['planned_order']==d.read(review.V2/'configuration_proposal_v2.json')['proposed_order']


def test_addendum_preserves_both_protocol_files():
    x=d.read(review.OUT/'prospective_protocol_addendum_proposal_v1.json')
    assert x['historical_protocol_sha256']==d.sha('docs/research_protocol_v1.1.md')
    assert x['prospective_reference_sha256']==d.sha('docs/PersonaSLM_Research_Protocol_v1.2_Revised_Proposed_r1.md')
    assert x['status']=='PROPOSED_NOT_ADOPTED' and not x['researcher_decision']


def test_optional_budget_plan_is_bounded_and_not_applied():
    x=d.read(review.OUT/'output_budget_sensitivity_proposal_v1.json')
    assert len(x['case_ids'])*len(x['conditions'])*len(x['budgets'])==54
    assert x['actual_requests']==0 and x['original_96_token_configuration_unchanged']
    assert d.read(review.V2/'configuration_proposal_v2.json')['n_predict']==96
