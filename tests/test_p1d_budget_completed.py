"""Real bounded-run integrity checks; do not execute or mock model inference."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1d_budget_calibration as b
from p1d_budget_analysis import OUT as A,metric_values
from p1d_budget_measurement import OUT as M
from p1d_budget_continuation_diagnostics import heading_shadow

F=Path('docs/validation/p1d/final_preparation_v1')

def test_completed_allocation_and_exact_raw_reconstruction():
    actual=b.audit();saved=b.load(M/'execution_integrity_v1.json')
    assert actual==saved
    assert actual['attempted']==actual['results']==actual['raw_responses']==actual['http_responses_verified']==144
    assert Counter(x['request']['max_new_tokens'] for x in actual['rows'])=={96:48,192:48,256:48}
    assert {x['request']['case_id'] for x in actual['rows']}==set(b.CASE_IDS)
    assert b.sha256(b.MANIFEST)==b.sha256(b.FROZEN)==b.MANIFEST_SHA
    for segment in actual['segments']:
        folder=Path(segment['path']);manifest=b.load(folder/'manifest.json')
        assert b.load(folder/'summary.json')['status']=='PASS'
        for path,digest in manifest['claim']['source_hashes'].items():
            assert b.sha256(Path(path))==b.sha256(folder/'source_snapshot'/path)==digest

def test_masking_provenance_and_metric_specific_evidence():
    rows=b.load(A/'primary_AI_proposals_UNCONFIRMED_v1.json')
    assert len(rows)==len({r['anonymous_response_id'] for r in rows})==144
    with (A/'primary_AI_proposals_UNCONFIRMED_v1.csv').open(encoding='utf-8-sig',newline='') as f:csvrows=list(csv.DictReader(f))
    assert {r['anonymous_response_id'] for r in rows}=={r['anonymous_response_id'] for r in csvrows}
    for r in rows:
        assert not {'condition','budget','case_id','request_id','speaker_id'} & set(r)
        assert r['review_status']=='UNCONFIRMED' and r['researcher_decision']==r['reviewer_id']==''
        assert r['human_review_timestamp'] is None
        assert b.th(r['primary_text'])==r['primary_text_sha256']
        assert all(r['metric_applicability'].values())
        assert all(r[k] for k in ('factual_reason','temporal_reason','task_reason','completeness_reason','relevance_reason','coherence_reason','persona_reason','alternative','trusted_evidence'))
        assert len({r['factual_reason'],r['task_reason'],r['relevance_reason'],r['coherence_reason']})==4

def test_join_and_original_structure_preserved():
    audit=b.load(M/'execution_integrity_v1.json');original={x['request']['request_id']:x for x in audit['rows']}
    rows=b.load(A/'provisional_analysis_dataset_v1.json');assert len(rows)==len(original)==144
    for r in rows:
        q=original[r['request_id']]['request'];v=original[r['request_id']]['result']
        assert (r['condition'],r['budget'],r['speaker_id'])==(q['condition'],q['max_new_tokens'],q['speaker_id'])
        assert r['structural_status']==v['response_status']['status']
        assert r['raw_text_sha256']==v['raw_text_sha256']
        assert metric_values(r)['budget_termination_incidence']==float(v['stop_reason']=='length')

def test_future_format_proposal_is_separately_gated_and_dev_only():
    p=b.load(F/'format_diagnostic_manifest_proposed_v1.json')
    assert p['authorized_requests']==0 and p['proposed_requests']==16 and p['maximum_generated_tokens']==1536
    assert len({r['request_id'] for r in p['requests']})==16
    assert {r['case_id'] for r in p['requests']}==set(b.CASE_IDS)
    assert {r['condition'] for r in p['requests']}=={'H_none'}
    assert {r['max_new_tokens'] for r in p['requests']}=={96}
    for r in p['requests']:
        assert b.th(r['prompt'])==r['prompt_sha256']
        assert b.th(str(r['input_token_ids']))==r['input_token_ids_sha256']
        content={k:v for k,v in r.items() if k!='request_sha256'}
        assert b.th(json.dumps(content,sort_keys=True,separators=(',',':')))==r['request_sha256']
    t=b.load(F/'format_diagnostic_tokenizer_validation_v1.json');assert t['new_model_generations']==0
    for entry in t['logs']:assert b.sha256(Path(entry['path']))==entry['sha256']

def test_heading_heuristic_has_documented_false_positive():
    raw='A requested document follows.\nCURRENT QUESTION\nThis is literal document content.\nAssistant: next'
    span=heading_shadow(raw,{'stop_type':'limit'})
    assert span is not None and 'literal document content' not in raw[slice(*span)]
    # An operational cut is not a semantic ground-truth label.
    candidates=b.load(b.OUT/'boundary_diagnostics_v1/summary_v1.json')
    assert candidates['changed_primary_labels']==0 and candidates['new_generations']==0

def test_engineering_report_counts_actual_http_attempts():
    r=b.load(b.OUT/'engineering_summary_v1.json')
    assert r['http_completion_requests']==r['requests_attempted']==r['validated_results']==144
    assert r['failed_requests']==r['remaining_authorized_requests']==0
    assert r['new_independent_validation_requests']==r['new_instruct_requests']==r['human_semantic_confirmations']==0
    assert r['main_study_decision']=='NO_GO'
