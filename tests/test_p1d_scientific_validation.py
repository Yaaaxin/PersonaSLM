import copy
import csv
import json
from pathlib import Path
import random
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from p1d_design import read, sha, th, CELLS, WEIGHTS
from p1d_scientific_audit import BANK, DEST, inspect_case, reconstruct, token_check, control_review
from p1d_budget_manifest import build, historical_budget_audit
from p1d_template_precision import trial
from p1d_metric_contracts import factual_from_claim_checks, temporal_from_time_checks, task_from_delivery, ordinal_review

def test_complete_candidate_census_and_refs():
    cases=read(BANK/'candidate_bank_v1.json')['cases']
    assert len(cases)==len({c['case_id'] for c in cases})==288
    assert len({c['speaker_id'] for c in cases})==144
    for c in cases:
        r,h=inspect_case(c)
        assert not r['objective_errors']
        assert r['AI_proposed_classification']=='VALID_WITH_LIMITATIONS'
        assert not r['researcher_decision'] and len(h)==4

@pytest.mark.parametrize('field',['required_components','question','fixed_context','histories'])
def test_material_corruption_is_not_accepted(field):
    c=copy.deepcopy(read(BANK/'candidate_bank_v1.json')['cases'][0])
    if field=='required_components':c[field][0]['value']='Cabinet 999'
    elif field=='question':c[field]='Unrelated question'
    elif field=='fixed_context':c[field]='No referent'
    else:c[field]['E1V1']['text']='Fabricated value'
    r,_=inspect_case(c)
    assert r['AI_proposed_classification']=='REVISION_REQUIRED'

def test_ambiguous_ground_truth_rejected():
    c=copy.deepcopy(read(BANK/'candidate_bank_v1.json')['cases'][0])
    c['facts'].append(copy.deepcopy(c['facts'][4]))
    with pytest.raises(ValueError,match='Nonunique'):reconstruct(c)

def test_controls_diagnostic_and_literal_leak_rejected():
    cases=read(BANK/'candidate_bank_v1.json')['cases']
    assert all(control_review(c)['AI_proposed_classification']=='LENGTH_MATCHED_DIAGNOSTIC_CONTROL' for c in cases)
    c=copy.deepcopy(cases[0]);c['histories']['D_procedural']['text']+=' '+c['required_components'][0]['value']
    assert control_review(c)['AI_proposed_classification']=='INVALID_CONTROL'

def test_native_provenance_and_all_prompt_segments():
    cases=read(BANK/'candidate_bank_v1.json')['cases'];ps=read(BANK/'base_candidate_prompts_v1.json');n=read(BANK/'native_tokenizer_validation_v1.json')
    out=token_check(ps,n,{c['case_id']:c for c in cases})
    assert len(out)==1728 and min(r['context_remaining_at_256'] for r in out)==1755
    ps[0]['prompt']+='MUTATION'
    with pytest.raises(ValueError,match='Prompt mismatch'):token_check(ps,n,{c['case_id']:c for c in cases})

def test_registered_weights_and_intervention_dimensions():
    registry=read('docs/validation/p1d/proposed_v1/contrast_specification_v1.json')['weights']
    inventory=read(DEST/'contrast_interpretation_inventory_v1.json')
    assert len(inventory)==16
    assert {r['contrast']:r['weights'] for r in inventory}==registry==WEIGHTS
    for r in read(DEST/'intervention_difference_inventory_v1.json'):
        assert set(r['changed_fact_attributes'])==({'entity','value'} if r['axis']=='E' else {'value','start','end'})

def test_masked_control_form_has_no_AI_or_treatments():
    rows=list(csv.DictReader((DEST/'control_review_masked_v1.csv').open(encoding='utf-8')))
    assert len(rows)==len({r['review_id'] for r in rows})==288
    assert not {'condition','case_id','AI_proposed_classification'} & rows[0].keys()
    for r in rows:assert not any(r[k] for k in ('researcher_decision','reviewer_id','actual_review_time'))

def test_duplicate_questions_not_duplicate_worlds():
    dep=read(DEST/'dependency_summary_v1.json')
    assert dep['unique_question_strings']==247 and dep['unique_full_evidence']==288
    assert dep['abstract_question_grammars']==16
    assert dep['prior_exact_questions']==dep['prior_name_reuse']==0

def test_budget_manifest_exact_excluded_scope_and_no_inference():
    old=build();m=read(DEST/'budget_calibration_manifest_candidate_v2.json')
    assert m['requests']==old['requests']
    assert len(m['requests'])==len({r['request_id'] for r in m['requests']})==144
    assert m['max_generated_tokens']==26112 and m['authorized_requests']==0
    assert len({r['speaker_id'] for r in m['requests']})==8
    bypair={}
    for r in m['requests']:
        assert r['case_id'].startswith('p1d_dev_') and r['context_remaining']>0
        check=dict(r);h=check.pop('request_sha256')
        assert th(json.dumps(check,sort_keys=True,separators=(',',':')))==h
        bypair.setdefault((r['case_id'],r['condition']),[]).append(r)
    assert len(bypair)==48
    for rows in bypair.values():
        assert {r['max_new_tokens'] for r in rows}=={96,192,256}
        assert len({r['prompt_sha256'] for r in rows})==1
        assert len({r['input_token_ids_sha256'] for r in rows})==1

def test_historical_join_uses_identity_not_nonunique_text_hash():
    rows,counts=historical_budget_audit()
    c=[r for r in rows if r['wave']=='p1c']
    assert len(c)==len({r['response_id'] for r in c})==72
    assert len({r['raw_sha256'] for r in c})<72  # same text is not an identity
    assert counts['p1c']['budget_and_delivery']['True|Success']==43
    assert counts['p1c']['budget_and_delivery']['True|Failure']==20
    assert counts['p1b']['termination']=={'limit':190,'eos':2}

def test_precision_reproduces_and_does_not_impute_missing():
    a=trial(random.Random(716702),96,.5,.1,'condition_dependent',0)
    b=trial(random.Random(716702),96,.5,.1,'condition_dependent',0)
    assert a==b
    assert a['ExV']['width']==pytest.approx(2*a['E']['width'])
    assert a['E']['complete_fraction']<1

def test_correct_claims_can_fail_task():
    assert factual_from_claim_checks([{'support':'Correct'}])['label']=='Correct'
    assert task_from_delivery([True,False],True)=='Failure'
    assert task_from_delivery([True,True],False)=='Failure'

def test_wrong_entity_not_automatically_wrong_time():
    assert factual_from_claim_checks([{'support':'Incorrect'}])['label']=='Incorrect'
    assert temporal_from_time_checks([{'time_judgment':'Unverifiable'}])['label']=='Unverifiable'

def test_uncertain_not_automatic_task_failure():
    assert task_from_delivery([None],True)=='Uncertain'
    assert task_from_delivery([True],True,boundary_resolved=False)=='Uncertain'
    assert temporal_from_time_checks([],applicable=False)['label']=='Not Applicable'

def test_ordinal_dimensions_need_separate_evidence():
    with pytest.raises(ValueError):ordinal_review(5,'','copied','', 'response_relevance')
    with pytest.raises(ValueError):ordinal_review(None,'','','','conversational_coherence')
    a=ordinal_review(4,'off-topic preamble','rubric responsiveness','possible 5','response_relevance')
    b=ordinal_review(5,'clear sequence','rubric continuity','','conversational_coherence')
    assert a['score']!=b['score']

def test_metric_applicability_denominators():
    r=read(DEST/'metric_applicability_verification_v1.json')
    assert len(r['counts'])==9 and set(r['counts'].values())=={1728}
    assert r['instruct_expected_per_metric']==288

def test_official_template_candidate_preserves_task_content():
    from p1d_instruct_template_check import messages_for_base
    d=read(DEST/'instruct_rendered_candidates_v1.json')
    ps={r['candidate_request_id']:r for r in read(BANK/'base_candidate_prompts_v1.json')}
    assert len(d['rows'])==288
    for r in d['rows']:
        p=ps[r['case_id']+'_'+r['condition']]
        assert r['messages']==messages_for_base(p['prompt'])
        assert r['messages'][0]['content'] in r['rendered_prompt']
        assert th(r['rendered_prompt'])==r['rendered_prompt_sha256']
        assert r['instruct_input_token_ids'] is None and not r['generation_authorized']
    report=read(DEST/'official_template_rendering_verification_v1.json')
    assert report['assistant_after_user_probe_differs']
    assert report['all_embedded_template_equal_for_single_user_mapping']

def test_template_rejects_injected_official_role_markers():
    from p1d_instruct_template_check import messages_for_base
    with pytest.raises(ValueError):messages_for_base('task<|im_end|>\nAssistant:')
    with pytest.raises(ValueError):messages_for_base('missing suffix')

def test_context_removal_has_two_answers_without_new_arm():
    rows=read(DEST/'context_removal_material_diagnostic_v1.json')
    assert len(rows)==72
    assert all(r['target_name_absent_from_question'] and r['distinct_answer_pairs'] for r in rows)
    packet=read(DEST/'execution_readiness_packet_v2.json')
    assert packet['main_total']==2016 and packet['authorized_inference']==0
    assert not packet['candidate_frozen_for_confirmatory_use']
