"""No inference: source-bound review, existing-text extraction and synthetic statistics."""
import copy
from datetime import date
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1c_semantic_review as a
import p1c_semantic_analysis as old
import p1c_annotation_review_check as check
import p1c_boundary_baselines as b
import p1c_postconfirmation_diagnostics as post


def test_exact_snapshot_and_six_field_changes():
    primary,secondary,changes,boundaries=check.verify()
    assert len(primary)==len(secondary)==72 and len(boundaries)==8
    assert {(x['anonymous_response_id'],x['endpoint'],x['original_rating'],x['revised_proposed_rating']) for x in changes}==check.EXPECTED
    assert len({r['anonymous_response_id'] for r in changes})==5


def test_metadata_alias_preserves_original_and_marks_pc023():
    rows=a.read(check.OUT/'derived_measurement_state_v2.json')
    row=next(r for r in rows if r['view']=='secondary' and r['anonymous_response_id']=='PC023')
    assert row['original_state']['metric_uncertainty_flags']['temporal_consistency']==[]
    assert row['derived_metric_flags']['temporal_consistency']==['INTERPRETATION_UNCERTAIN']
    assert date(2042,12,15).weekday()==0


def test_concordance_distinguishes_unknown_from_false():
    primary=a.read(check.audit.PRIMARY)
    rows,pairs,summary=check.concordance(primary)
    assert all(r['fact_task_equal_under_explicit_C_I_U_mapping'] for r in rows)
    assert sum(r['factual_as_C_I_U'] is None for r in rows)==9
    assert sum(r['factual_as_C_I_U']==0 for r in rows)==20
    assert summary['conversational_coherence']['non_null_distinct_values']==['5']
    assert sum(r['count'] for r in pairs if r['left_metric']=='factual_consistency' and r['right_metric']=='task_success')==72


@pytest.mark.parametrize('fixture',b.fixture_bank(),ids=lambda f:f['fixture_id'])
def test_every_baseline_candidate_is_original_substring(fixture):
    for method in b.METHODS:
        span=b.extract(fixture['raw'],fixture['native'],method)
        if span is not None:
            assert 0<=span[0]<span[1]<=len(fixture['raw'])


def test_fence_guard_helps_but_does_not_solve_document_or_quote_ambiguity():
    cases={r['fixture_id']:r for r in b.fixture_bank()}
    for key in ('fenced_role','fenced_heading','tilde_heading'):
        f=cases[key]
        start,end=b.extract(f['raw'],f['native'],'fence_aware_role_or_section')
        assert f['raw'][start:end]==f['authored_reference_content']
    for key in ('document_heading','multiline_quote'):
        f=cases[key]
        start,end=b.extract(f['raw'],f['native'],'fence_aware_role_or_section')
        assert f['raw'][start:end]!=f['authored_reference_content']


def test_native_eos_is_not_first_reply_boundary():
    raw='Answer.\nUser: More?\nAssistant: More.'
    assert b.extract(raw,{'stop_type':'eos'},'native_eos_only')==(0,len(raw))
    assert b.extract(raw,{'stop_type':'limit'},'native_eos_only') is None
    assert b.extract(raw,{'stop_type':'eos'},'role_or_section')==(0,8)


def test_saved_baseline_report_is_not_accuracy_or_new_human_scores():
    x=a.read(b.OUT/'summary_v1.json')
    assert x['new_generations']==0 and x['human_ratings_created'] is False
    assert all(m['independent_boundary_accuracy'] is None for m in x['methods'].values())
    assert x['methods']['role_or_section']['reference_matches']==x['methods']['fence_aware_role_or_section']['reference_matches']
    assert x['fixture_summary']['fence_aware_role_or_section']['false_splits']==2


def synthetic_views():
    spec=a.read(old.PREP/'analysis_specification_v1.json');primary=[];structural={}
    for cid,speaker in spec['cases'].items():
        for condition in spec['condition_order']:
            rid=cid+'-'+condition
            primary.append({'anonymous_response_id':rid,'case_id':cid,'persona_id':speaker,'condition':condition,
                'ratings':{'factual_consistency':'Correct','temporal_consistency':'Correct','response_relevance':5,'conversational_coherence':5,
                    'task_success':1,'component_coverage':1.0,'semantic_completeness':'YES'}})
            structural[rid]={'frozen_structural_status':'CROSS_TURN','unit_identifiable':True,'native_stop':'limit'}
    return spec,primary,copy.deepcopy(primary),structural


def test_paired_boundary_sensitivity_reconstructs_and_keeps_unknowns():
    spec,primary,secondary,structural=synthetic_views()
    # Synthetic test only: one unresolved primary cell, known sensitivity outcome.
    primary[0]['ratings']['task_success']=None
    first=post.diagnostics(primary,secondary,spec,structural,replicates=5)
    assert first==post.diagnostics(primary,secondary,spec,structural,replicates=5)
    assert len(first['structural_effects'])==7*16
    assert len({r['contrast'] for r in first['paired_boundary_sensitivity_effect_changes']})==16
    task=[r for r in first['paired_boundary_sensitivity_effect_changes'] if r['metric']=='task_success' and r['contrast']=='RxT'][0]
    assert task['evaluable_cases']==11 and task['estimate'] is None
    assert task['speaker_clusters']==6


def test_sensitivity_pair_routing_mismatch_rejected():
    spec,primary,secondary,structural=synthetic_views()
    secondary[0]['condition']='wrong'
    with pytest.raises(ValueError,match='routing'):post.diagnostics(primary,secondary,spec,structural,replicates=1)


def test_actual_confirmation_binds_exact_sources_and_never_invents_timestamp():
    import p1c_integrity_registration as gate
    root=Path('docs/validation/p1c/confirmed_semantic_v1')
    decision=a.read(root/'approval/actual_researcher_decision_v1.json')
    rows=gate.confirmed(decision)
    assert len(rows['primary'])==len(rows['secondary'])==72
    assert all(r['human_review_timestamp'] is None for view in rows.values() for r in view)
    assert a.sha('docs/P1c_final_annotation_confirmation_packet_v1.md')==check.PACKET_SHA
    bad=copy.deepcopy(decision);bad['source_sha256'][str(check.audit.PRIMARY)]='invalid'
    with pytest.raises(ValueError,match='hashes differ'):gate.confirmed(bad)


def test_actual_confirmed_exports_preserve_masked_source_and_uncertainty():
    import p1c_confirmed_reporting as report
    records,analyses,joined=report.checked_inputs()
    exported=report.exports(records,analyses,joined)
    originals={r['anonymous_response_id']:r for r in a.rows(a.SOURCE)}
    for view in ('primary','secondary'):
        rows=exported[view+'_confirmed_masked_v1.csv']
        assert len(rows)==72
        for r in rows:
            assert all(r[k]==v for k,v in originals[r['anonymous_response_id']].items())
            assert 'condition' not in r and 'persona_id' not in r
            assert r['registered_admin_missing'] is False
    task=[r for r in exported['outcome_totals_v1.csv'] if r['view']=='primary' and r['metric']=='task_success']
    assert {r['category']:r['count'] for r in task}=={'1':43,'0':20,'UNSCORABLE_OR_UNCERTAIN_NULL':9}


def test_actual_analysis_incidence_direct_pairing_and_all_registered_weights():
    import p1c_confirmed_reporting as report
    _,analyses,joined=report.checked_inputs()
    spec=a.read(old.PREP/'analysis_specification_v1.json')
    assert spec['weights']==a.read(old.REGISTRY)['weights']
    for view,data in analyses.items():
        assert len(data['effects'])==24*16
        for x in data['effects']:
            if x['metric']!='factual_consistency__Correct_incidence':continue
            manual=[]
            for cid in spec['cases']:
                cells={r['condition']:float(r['ratings']['factual_consistency']=='Correct') for r in joined[view] if r['case_id']==cid}
                manual.append(sum(w*cells[c] for c,w in spec['weights'][x['contrast']].items()))
            assert x['estimate']==pytest.approx(sum(manual)/12)
    unknown=next(x for x in analyses['primary']['effects'] if x['metric']=='task_success' and x['contrast']=='R')
    assert unknown['estimate'] is None and unknown['evaluable_cases']==8
    assert unknown['identification_bounds']==pytest.approx([-0.125,1/6])
