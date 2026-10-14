import csv
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1d_calibration_followup as f

def test_stratified_packet_coverage_and_no_human_decisions():
    summary=f.read(f.OUT/'stratified_review_manifest_v1.json')
    rows=f.records(f.OUT/'stratified_case_review_v1.csv')
    bank={c['case_id']:c for c in f.read(f.BANK)['cases']}
    from collections import Counter
    strata=Counter((bank[r['case_id']]['family'],bank[r['case_id']]['domain']['id'],bank[r['case_id']]['date_type']) for r in rows)
    assert len(rows)==summary['selected_cases']==64
    assert len(strata)==32 and set(strata.values())=={2}
    assert all(not r['researcher_decision'] and not r['reviewer_id'] for r in rows)
    assert len({f.question_skeleton(bank[r['case_id']]) for r in rows})==16

def test_control_view_is_assignment_and_recommendation_masked():
    rows=f.records(f.OUT/'stratified_control_review_masked_v1.csv')
    mapping=f.read(f.OUT/'withheld_stratified_control_mapping_v1.json')
    assert len(rows)==len(mapping)==64
    assert {r['review_id'] for r in rows}=={r['review_id'] for r in mapping}
    assert not ({'case_id','AI_recommendation','condition'} & set(rows[0]))
    assert all(not r['control_classification'] and not r['researcher_decision'] for r in rows)

def test_all_risk_records_retain_candidate_identity_and_no_revision():
    rows=f.records(f.OUT/'case_risk_inventory_v1.csv')
    assert len(rows)==len({r['case_id'] for r in rows})==288
    assert {r['AI_disposition'] for r in rows}=={'VALID_WITH_LIMITATIONS'}
    assert {r['control_disposition'] for r in rows}=={'LENGTH_MATCHED_DIAGNOSTIC_CONTROL'}
    assert f.sha(f.BANK)=='170e43772e0e45753638228a8c2fc2bf2d5a9f06830374b22887a5929486afbd'

def test_template_concentration_is_not_independent_sample_size():
    s=f.read(f.OUT/'template_dependency_assessment_v1.json')
    assert sum(s['grammar_counts'].values())==288 and len(s['grammar_counts'])==16
    assert 0<s['inverse_concentration_grammar_count']<=16
    assert 'NOT effective sample size' in s['interpretation']
