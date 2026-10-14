"""Offline measurement-state and confirmation regressions; no scientific approvals."""
import copy
import json
from pathlib import Path
import sys
from collections import Counter
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import p1c_semantic_review as a
import p1c_semantic_analysis as old
import p1c_semantic_integrity as audit
import p1c_integrity_registration as gate


def test_all_original_fields_and_masking_preserved():
    source={r['anonymous_response_id']:r for r in a.read(old.PRIMARY)}
    for path in (audit.PRIMARY,audit.SECONDARY):
        rows=a.read(path)
        assert len(rows)==len({r['anonymous_response_id'] for r in rows})==72
        for r in rows:
            assert all(r[k]==v for k,v in source[r['anonymous_response_id']].items())
            assert not {'condition','factor_assignment','persona_id','case_id','prompt','frozen_structural_status'} & r.keys()
            assert r['final_researcher_id']==r['final_researcher_decision']==r['final_human_review_timestamp']==''
            assert a.text_sha(r['raw_first_reply'])==r['first_reply_sha256']
            old.validate_rating(r['reviewed_AI_ratings'])


def test_exact_proposed_corrections_and_separate_component_reasoning():
    rows=a.read(audit.PRIMARY)
    edits={(r['anonymous_response_id'],c['metric'],c['original'],c['recommended']) for r in rows for c in r['reviewed_AI_changes']}
    assert edits=={(rid,'conversational_coherence',4,5) for rid in ('PC004','PC006','PC011','PC027','PC030')}|{('PC006','response_relevance',4,5)}
    for r in rows:
        assert r['reviewed_AI_ratings']['factual_consistency']==r['AI_factual_consistency']
        assert r['metric_evidence_audit']['task']['independently_checked_success']==r['AI_task_success']
        if r['anonymous_response_id'] in audit.WRONG:
            assert r['metric_evidence_audit']['task']['answer_delivered']=='YES'
            assert r['reviewed_AI_ratings']['semantic_completeness']=='YES'
            assert r['reviewed_AI_ratings']['task_success']==0
    pc006=next(r for r in rows if r['anonymous_response_id']=='PC006')
    assert pc006['reviewed_AI_ratings']['component_coverage']==1
    assert pc006['reviewed_AI_ratings']['task_success'] is None


def test_primary_reconstruction_matches_frozen_artifact():
    assert [audit.primary_record(r) for r in a.read(old.PRIMARY)]==a.read(audit.PRIMARY)
    for name,digest in a.read(audit.OUT/'primary_audit_freeze_v1.json')['files'].items():
        assert a.sha(audit.OUT/name)==digest


def test_boundary_changes_exactly_original_ambiguous_and_exact_prefixes():
    table=a.read(audit.OUT/'boundary_sensitivity_table_v1.json')
    assert {r['anonymous_response_id'] for r in table}==audit.BOUNDARY
    assert Counter(r['reviewed_secondary_ratings']['factual_consistency'] for r in table)=={'Correct':4,'Incorrect':4}
    prompts={r['anonymous_response_id']:r for r in a.read(audit.OUT/'protected_boundary_prompt_audit_v1.json')}
    for r in table:
        assert r['original_structural_status']=='AMBIGUOUS'
        assert r['original_primary_ratings']['factual_consistency']=='Unverifiable'
        assert r['raw_full_continuation'][r['proposed_start']:r['proposed_end']]==r['proposed_evaluation_view']
        assert a.text_sha(r['proposed_evaluation_view'])==r['proposed_view_sha256']
        assert r['multiple_interpretations_remain'] is True
        assert r['researcher_final_disposition']==''
        p=prompts[r['anonymous_response_id']]
        assert a.text_sha(p['original_prompt'])==p['prompt_sha256']
        assert a.text_sha(r['raw_full_continuation'])==p['raw_text_sha256']
    r=next(r for r in table if r['anonymous_response_id']=='PC033')
    assert r['reviewed_secondary_ratings']['component_coverage']==0.5
    assert r['reviewed_secondary_ratings']['task_success']==0


def test_uncertainty_flags_do_not_recode_endpoints():
    rows=a.read(audit.PRIMARY)
    assert sum(r['measurement_state']['boundary_state']=='BOUNDARY_UNRESOLVED' for r in rows)==8
    assert sum(r['AI_factual_consistency']=='Unverifiable' for r in rows)==9
    for r in rows:
        state=r['measurement_state']
        assert state['official_human_annotation_state']=='MISSING'
        assert state['AI_review_missing'] is False
        assert state['persona_fidelity_state']=='NOT_APPLICABLE'
        if r['anonymous_response_id'] in audit.BOUNDARY:
            assert state['metric_uncertainty_flags']['factual_consistency']==['BOUNDARY_UNRESOLVED','STRUCTURALLY_UNSCORABLE']
    r=next(r for r in a.read(audit.SECONDARY) if r['anonymous_response_id']=='PC039')
    assert r['reviewed_AI_ratings']['factual_consistency']=='Incorrect'
    assert 'EVIDENCE_UNVERIFIABLE' in r['measurement_state']['metric_uncertainty_flags']['factual_consistency']


def test_exact_registered_estimands_and_units_unchanged():
    new=a.read(audit.OUT/'primary_sensitivity_specification_v1.json')
    registry=a.read(old.REGISTRY)
    spec=a.read(old.PREP/'analysis_specification_v1.json')
    assert new['registered_contrasts']==registry['weights']==spec['weights']
    assert len(spec['weights'])==16 and len(spec['cases'])==12 and len(set(spec['cases'].values()))==6
    assert new['bootstrap_seed']==spec['bootstrap']['seed']==715004
    assert all(sum(w.values())==0 for w in spec['weights'].values())
    assert spec['weights']['RxT']=={'H_none':0,'N_history':0,'R0T0':1,'R0T1':-1,'R1T0':-1,'R1T1':1}


@pytest.fixture
def synthetic_decision():
    # Test-only fixture, never a real human decision or a repository registration.
    x=gate.template()
    x.update(reviewer_id='Yaxin_ZHENG',review_status='RESEARCHER_CONFIRMED',decision_source='researcher_confirmation',
             confirmation_statement='SYNTHETIC TEST FIXTURE ONLY',rating_version='REVIEWED_RECOMMENDATIONS',include_boundary_sensitivity=True)
    return x


def test_blank_actual_confirmation_rejected(tmp_path):
    path=audit.OUT/'researcher_confirmation_request_v1.json'
    target=tmp_path/'registration'
    with pytest.raises(ValueError,match='Explicit researcher'):
        gate.register(path,target)
    assert not target.exists()


@pytest.mark.parametrize('field,value',[
    ('reviewer_id',''),('review_status','UNCONFIRMED'),('decision_source','AI'),
    ('confirmation_statement',''),('rating_version',''),('include_boundary_sensitivity',None),('source_sha256',{})])
def test_confirmation_or_source_mismatch_fails(synthetic_decision,field,value):
    synthetic_decision[field]=value
    with pytest.raises(ValueError):gate.confirmed(synthetic_decision)


def test_versions_can_be_chosen_without_destroying_original_proposal(synthetic_decision):
    new=gate.confirmed(synthetic_decision)
    synthetic_decision['rating_version']='ORIGINAL_PROPOSALS'
    original=gate.confirmed(synthetic_decision)
    for view in new:
        n=next(r for r in new[view] if r['anonymous_response_id']=='PC006')
        o=next(r for r in original[view] if r['anonymous_response_id']=='PC006')
        assert n['ratings']['conversational_coherence']==5 and o['ratings']['conversational_coherence']==4
        assert n['original_AI_proposal']==o['original_AI_proposal']
    synthetic_decision['include_boundary_sensitivity']=False
    assert set(gate.confirmed(synthetic_decision))=={'primary'}


@pytest.mark.parametrize('metric,value',[('task_success',True),('response_relevance',2.5),('factual_consistency','Not Applicable'),('component_coverage',float('nan'))])
def test_invalid_corrections_cannot_be_registered(synthetic_decision,metric,value):
    synthetic_decision['corrections']=[{'view':'primary','anonymous_response_id':'PC006','ratings':{metric:value},'reason':'Synthetic test'}]
    with pytest.raises(ValueError):gate.confirmed(synthetic_decision)


def test_actual_scope_and_correction_reason_required(synthetic_decision):
    synthetic_decision['corrections']=[{'view':'secondary','anonymous_response_id':'PC006','ratings':{'factual_consistency':'Correct'},'reason':'Synthetic test'}]
    synthetic_decision['include_boundary_sensitivity']=False
    with pytest.raises(ValueError):gate.confirmed(synthetic_decision)
    synthetic_decision['corrections'][0].update(view='primary',reason='')
    with pytest.raises(ValueError):gate.confirmed(synthetic_decision)


def test_successful_test_registration_has_no_join_and_refuses_overwrite(synthetic_decision,tmp_path):
    proposal=tmp_path/'TEST_ONLY_approval.json'
    a.write(proposal,synthetic_decision)
    target=tmp_path/'TEST_ONLY_registration'
    assert gate.register(proposal,target)=={'registered':72,'treatment_join_performed':False}
    assert a.read(target/'registration_manifest_v1.json')['human_review_timestamp'] is None
    with pytest.raises(ValueError,match='overwrite'):gate.register(proposal,target)
    with pytest.raises(ValueError):audit.prepare_primary()
    with pytest.raises(ValueError):audit.prepare_secondary()


def test_failed_export_is_retained_but_never_active():
    old_json=audit.OUT/'reviewed_boundary_sensitivity_UNCONFIRMED_v1.json'
    old_csv=old_json.with_suffix('.csv')
    assert old_json.exists() and old_csv.exists()
    assert len(a.rows(old_csv))==9
    assert len(a.rows(audit.SECONDARY.with_suffix('.csv')))==72
    assert str(old_json) not in gate.sources()
    assert str(audit.SECONDARY) in gate.sources()
