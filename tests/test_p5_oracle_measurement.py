import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p5_oracle_measurement as m

def test_actual_bound_run_no_retries_or_missing_outputs():
    a=m.p.audit()
    assert a['attempted']==a['results']==8 and a['new_generations']==0
    for x in a['rows']:
        q,r=x['request'],x['result']
        assert r['raw_response']==m.REVIEWS[q['case_id']][0]
        assert r['stop_reason']=='eos' and r['generated_token_ids'][-1]==248046
        assert r['response_status']['status']=='AMBIGUOUS' and r['response_status']['unit_identifiable']
        assert r['generated_tokens']==len(r['generated_token_ids'])<=96

def test_measurement_snapshot_and_provenance():
    rows=m.p.load(m.OUT/'AI_proposals_UNCONFIRMED_v1.json');s=m.p.load(m.OUT/'summary_v1.json')
    assert len(rows)==8 and s['human_semantic_ratings']==0
    assert sum(len(r['required_components']) for r in rows)==14
    assert all(r['researcher_decision']==r['reviewer_id']=='' and r['human_timestamp'] is None for r in rows)
    assert all(r['factual_evidence'] and r['temporal_evidence'] and r['task_evidence'] and r['relevance_evidence'] and r['coherence_evidence'] for r in rows)
    assert s['task_difference']==.75 and s['main_P1d_decision']=='NO_GO'

def test_alias_does_not_rewrite_span_or_certify_semantics():
    rows=m.p.load(m.OUT/'boundary_alias_sensitivity_v1.json')
    assert len(rows)==8
    for r in rows:
        assert r['same_evaluated_text'] and r['original']['status']=='AMBIGUOUS'
        assert r['sensitivity_eos_alias']['status']=='AMBIGUOUS'
        assert r['sensitivity_eos_alias']['observed_boundary']=='eog'
        assert r['independent_boundary_ground_truth'] is None

def test_original_case_pairing_and_completeness_not_accuracy():
    rows=m.p.load(m.OUT/'paired_historical_comparison_v1.json')
    assert sum(r['old_complete']=='YES' for r in rows)==5
    assert sum(r['old_task']=='Success' for r in rows)==2
    assert sum(r['old_present'] for r in rows)==8 and sum(r['old_supported'] for r in rows)==3
    assert sum(r['oracle_supported'] for r in rows)==14
    assert all(r['original_evidence_sufficient'] and r['literal_reference_values_in_oracle'] for r in rows)
