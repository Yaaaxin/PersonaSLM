"""Offline acceptance guards for the final review packet, not model behavior tests."""
import ast
import csv
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1c_design as d
import p1c_final_review as f
import p1c_scientific_review as a


def load(name):
    return d.read(f.OUT/name)


@pytest.mark.parametrize('kind,count',[('case',12),('history',60),('neutral',12)])
def test_review_identity_source_and_no_human_approval(kind,count):
    rows=load(f'final_{kind}_review_proposed_v1.json')
    assert len(rows)==count
    assert len({r.get('item_id',r['case_id']) for r in rows})==count
    assert all(r[h]=='' for r in rows for h in f.HUMAN)
    cases={c['case_id']:c for c in d.read(d.DATA)['cases']}
    original={(r['case_id'],r['condition']):r for r in d.read(a.V2/'selected_prompts_v2.json')['records']}
    for r in rows:
        c=cases[r['case_id']]
        assert r['current_question']==c['question']
        if kind=='case':
            assert r['trusted_evidence']==c['trusted_evidence']
            assert all(q in c['trusted_evidence'] for q in r['supporting_source_quotations'].splitlines())
        else:
            assert r['full_text']==original[(r['case_id'],r['condition'])]['history']
            assert r['source_quote'] in (r['full_text'] if kind=='neutral' or r['condition']=='N_history' else c['trusted_evidence'])


def test_uncertainty_and_failed_pure_identification_not_hidden():
    cases=load('final_case_review_proposed_v1.json')
    assert all(r['AI_checks']['isolated_factor_semantics']['label']=='FAIL' for r in cases)
    assert sum(r['AI_checks']['operational_topical_relevance']['label']=='UNCERTAIN' for r in cases)==8
    assert all(r['AI_checks']['absence_of_reasoning_shortcuts']['label']=='UNCERTAIN' for r in cases)
    assert all(r['AI_case_decision']=='ACCEPT_WITH_RESTRICTED_ESTIMAND' for r in cases)


def test_neutral_subset_is_identical_and_not_approved_as_inert():
    neutral=load('final_neutral_review_proposed_v1.json')
    assert neutral==[r for r in load('final_history_review_proposed_v1.json') if r['condition']=='N_history']
    for r in neutral:
        assert r['AI_checks']['information_equivalence']['label']=='FAIL'
        assert r['AI_checks']['absence_of_topic_or_style_priming']['label']=='FAIL'
        assert r['AI_overall_judgment']=='UNCERTAIN'


def test_confirmation_form_covers_unique_items_without_duplicate_neutral_approval():
    with (f.OUT/'researcher_confirmation_form_v1.csv').open(encoding='utf-8-sig',newline='') as stream:
        rows=list(csv.DictReader(stream))
    assert len(rows)==77
    assert sum(r['item_type']=='case' for r in rows)==12
    assert sum(r['item_type']=='history_text' for r in rows)==60
    assert all(r[h]=='' for r in rows for h in f.HUMAN)


def test_manifest_preserves_every_original_prompt_field_and_order():
    manifest=load('calibration_manifest_candidate_v1.json')
    cfg=d.read(a.V2/'configuration_proposal_v2.json')
    original={(r['case_id'],r['condition']):r for r in d.read(a.V2/'selected_prompts_v2.json')['records']}
    assert [r['request_identity'] for r in manifest['requests']]==cfg['proposed_order']
    for r in manifest['requests']:
        assert {k:r[k] for k in original[tuple(r['request_identity'])]}==original[tuple(r['request_identity'])]
        assert r['factor_assignment']==d.CONDITIONS[r['condition']]
        assert r['input_tokens']+96<=4096
    assert not manifest['execution_authorized']
    assert manifest['generations_executed']==0
    receipt=load('calibration_manifest_sha256_v1.json')
    assert d.sha(receipt['path'])==receipt['sha256']


def test_native_evidence_proves_ids_not_just_lengths():
    selected={r['prompt_sha256']:r for r in d.read(a.V2/'selected_prompts_v2.json')['records']}
    proof=d.read(a.OUT/'reproducibility_manifest_v1.json')['native_recheck_logs']
    assert len(proof)==72
    for path,sha in proof.items():
        assert d.sha(path)==sha
        log=d.read(path);r=selected[log['prompt_sha256']]
        assert log['prompt']==r['prompt']
        assert ast.literal_eval(log['stdout'].strip())==r['input_token_ids']


def test_policy_does_not_change_original_applicability():
    cases={c['case_id']:c for c in d.read(d.DATA)['cases']}
    rows=load('applicability_matrix_v1.json')
    assert len(rows)==72
    for row in rows:
        assert {k:row[k] for k in cases[row['case_id']]['applicability']}==cases[row['case_id']]['applicability']
        assert row['persona_fidelity'] is False
    assert load('evaluation_policy_proposed_v1.json')['categories']==['Correct','Incorrect','Unverifiable','Not Applicable']


def test_two_stage_templates_mask_treatments_and_keep_outcomes_blank():
    with (f.OUT/'stage_a_semantic_template_v1.csv').open(encoding='utf-8-sig',newline='') as stream:
        rows=list(csv.DictReader(stream))
    assert len(rows)==72
    assert not {'condition','R','T','structural_status','raw_full_continuation','AI_prediction'} & set(rows[0])
    assert all(not v for r in rows for k,v in r.items() if k.startswith('human_') or k in ('first_reply','reviewer_id'))
    mapping=load('protected_treatment_mapping_proposed_v1.json')['records']
    assert {r['anonymous_response_id'] for r in rows}=={r['anonymous_response_id'] for r in mapping}
    assert len({tuple(r['request_identity']) for r in mapping})==72


def test_estimands_retain_weights_and_separate_baseline_meanings():
    spec=load('estimand_registry_proposed_v1.json')
    assert spec['weights']==a.contrast_spec()['weights']
    assert len(spec['registry'])==16
    for r in spec['registry']:
        assert sum(r['weights'].values())==0
        assert len(r['eligible_case_ids'])==12
        assert r['approval_status']=='PENDING'
        if 'H_none' in r['contrast_id']:assert 'length' in r['target_estimand']
    assert spec['weights']['RxT']==dict(R0T0=1,R0T1=-1,R1T0=-1,R1T1=1,N_history=0,H_none=0)


def test_exclusive_creation_cannot_overwrite_final_candidate(tmp_path):
    path=tmp_path/'manifest.json';d.write_json(path,{'approved':False})
    before=path.read_bytes()
    with pytest.raises(FileExistsError):d.write_json(path,{'approved':True})
    assert path.read_bytes()==before


@pytest.mark.parametrize('label',['APPROVED','',None])
def test_invalid_AI_check_label_rejected(label):
    with pytest.raises(ValueError):f.check(label,'not an authorized human decision')
