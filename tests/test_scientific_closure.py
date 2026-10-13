"""Contracts for lossless registration and a single non-approved Tessa proposal."""
import base64
from copy import deepcopy
import json
from pathlib import Path

import pytest

from personaslm.control_decisions import read_csv
from personaslm.scientific_closure import register_reviews, tessa_plan, TESSA_TEXT, reconcile_tokenizations
from personaslm.control_closure import replacement_preserved

PUBLIC = Path(__file__).resolve().parents[1] / 'docs/validation'

@pytest.fixture
def inputs():
    sf, sr = read_csv(PUBLIC/'PersonaSLM_P0_style_v1.csv')
    hf, hr = read_csv(PUBLIC/'PersonaSLM_P0_historyA_evidence_notes_v1.csv')
    read = lambda name: json.loads((PUBLIC/name).read_text(encoding='utf-8'))
    attestation = {'source_judgments_confirmed': True, 'history_associations_confirmed': True,
       'reviewer_id':'Yaxin_ZHENG', 'decision_source':'researcher', 'history_comparison_suitability':'PASS',
       'history_decision':'ACCEPT_NARROW',
       'style_decisions':{n:('REVISION_REQUIRED' if n=='Tessa' else 'ACCEPT_NARROW') for n in ['Riley','Samara','Devon','Tessa','Blair','Robin']}}
    return [sf,sr,hf,hr,read('P0_style_closure_review_v1.json'),read('P0_history_a_evidence_v1.json'),attestation]

def test_current_attestation_preserves_all_source_values_and_assistance(inputs):
    original = deepcopy(inputs)
    result = register_reviews(*inputs)
    assert inputs == original
    assert result['counts'] == {'style_decisions':6,'source_style_axis_judgments':90,'style_accepted_narrow':5,'history_confirmations':18,'history_narrow_decisions':6}
    assert result['review_type'] == 'researcher_verified_human_review'
    assert result['final_decision_authority'] == 'researcher'
    assert 'Not blind' in result['blinding'] and result['review_assistance'] == 'AI-assisted'
    assert all(r['source_row_verbatim']['human_final_review']=='' for r in result['styles'])
    assert all(r['semantic_neutrality_not_overridden']=='UNCERTAIN' for r in result['styles'])
    assert result['human_review_timestamp'] is None
    assert all(r['preserved_judgments']=={'topic_alignment':'FAIL','temporal_relationships':'FAIL','conversational_coherence':'UNCERTAIN'} for r in result['history_decisions'])

@pytest.mark.parametrize('corruption',['duplicate_style','missing_history','changed_text','changed_quote','changed_score','invalid_label','unknown_column','conflicting_human','missing_attestation','wrong_authority'])
def test_registration_rejects_material_or_authority_changes(inputs, corruption):
    if corruption=='duplicate_style': inputs[1][1]=inputs[1][0]
    elif corruption=='missing_history': inputs[3].pop()
    elif corruption=='changed_text': inputs[1][0]['neutral_candidate']+=' extra'
    elif corruption=='changed_quote': inputs[3][0]['source_passage_active']+=' altered'
    elif corruption=='changed_score': inputs[3][0]['prior_human_axis_judgment']='PASS'
    elif corruption=='invalid_label': inputs[1][0]['ai_answer_leakage']='MAYBE'
    elif corruption=='unknown_column': inputs[0].append('unknown')
    elif corruption=='conflicting_human': inputs[1][0]['human_final_review']='REJECT_AS_NEUTRAL'
    elif corruption=='missing_attestation': inputs[-1]['source_judgments_confirmed']=False
    elif corruption=='wrong_authority': inputs[-1]['decision_source']='automated_rule'
    with pytest.raises(ValueError): register_reviews(*inputs)

def test_tessa_is_single_proposal_not_new_human_approval(inputs):
    old = json.loads((PUBLIC/'P0_style_closure_freeze_v1.json').read_text(encoding='utf-8'))
    plan = tessa_plan(old['dataset_records'], inputs[4])
    assert plan['candidate_text'] == TESSA_TEXT
    assert plan['maximum_candidate_requests'] == plan['maximum_reference_requests'] == 1
    assert plan['token_tolerance'] == 0 and plan['review_status']=='PENDING_RESEARCHER_CONFIRMATION'
    assert replacement_preserved(plan['reference_prompt'], plan['candidate_prompt'])
    assert all(s not in plan['candidate_text'] for s in ['Tessa','Norwich','Hull'])
    assert 'Speaker style profile: '+TESSA_TEXT in plan['candidate_prompt']['text']

def test_tessa_reference_must_remain_original(inputs):
    old = json.loads((PUBLIC/'P0_style_closure_freeze_v1.json').read_text(encoding='utf-8'))
    inputs[4]['items'][3]['reference_prompt']+=' altered'
    with pytest.raises(ValueError): tessa_plan(old['dataset_records'], inputs[4])

def events():
    return [{'kind':'http_request','data':{'route':'/tokenize','payload':{'content':'software fixture','add_special':True,'parse_special':False,'with_pieces':False}}},
            {'kind':'http_response','data':{'route':'/tokenize','status':200,'body_base64':base64.b64encode(json.dumps({'tokens':[1,2]}).encode()).decode()}}]

def test_native_ids_are_bound_to_actual_request_and_response():
    assert reconcile_tokenizations(events(), [('software fixture',[1,2])])==1
    with pytest.raises(ValueError): reconcile_tokenizations(events(), [('software fixture',[2,1])])
    with pytest.raises(ValueError): reconcile_tokenizations(events(), [('other prompt',[1,2])])

@pytest.mark.parametrize('route',['/completion','/v1/completions','/v1/chat/completions'])
def test_answer_generation_is_rejected(route):
    with pytest.raises(ValueError):
        reconcile_tokenizations([{'kind':'http_request','data':{'route':route}}],[])
