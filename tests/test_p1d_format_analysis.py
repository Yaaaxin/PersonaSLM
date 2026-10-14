import csv
import ast
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1d_format_analysis as a
import p1d_format_calibration as f
from p1d_format_followup import stop_shadow

def test_actual_16_payloads_raw_bytes_and_reconstruction():
    check=f.audit()
    assert check==f.load(f.OUT/'execution_integrity_v1.json')
    assert check['attempted']==check['results']==check['http_responses_verified']==16

def test_all_analysis_reconstructs_without_tuple_json_false_failure():
    for name,value in a.build().items():assert f.load(a.OUT/name)==json.loads(json.dumps(value))

def test_csv_and_json_proposals_have_identical_fields_and_values():
    for name in ('primary_AI_proposals_UNCONFIRMED_v1','boundary_review_v1','paired_case_contributions_v1','historical_exact_id_comparison_v1'):
        values=f.load(a.OUT/(name+'.json'))
        with (a.OUT/(name+'.csv')).open(encoding='utf-8',newline='') as handle:rows=list(csv.DictReader(handle))
        assert len(rows)==len(values)
        for row,value in zip(rows,values):
            for k,v in value.items():
                if isinstance(v,(dict,list)):
                    # Legacy paired CSV writes Python tuple notation; JSON is canonical.
                    got=list(ast.literal_eval(row[k])) if row[k].startswith('(') else json.loads(row[k])
                    assert got==v
                else:
                    assert row[k]==('' if v is None else str(v))

def test_no_human_rating_fabrication_or_blinding_claim():
    rows=f.load(a.OUT/'primary_AI_proposals_UNCONFIRMED_v1.json')
    assert len(rows)==len({r['anonymous_response_id'] for r in rows})==16
    for r in rows:
        assert r['review_status']=='UNCONFIRMED' and not r['reviewer_id'] and not r['researcher_decision'] and r['human_review_timestamp'] is None
        assert r['annotation_origin']=='AI_assisted_diagnostic_review_with_configuration_visible'

def test_generic_policy_claims_do_not_become_task_success():
    rows=f.load(a.OUT/'primary_AI_proposals_UNCONFIRMED_v1.json')
    correct=[r for r in rows if r['factual']=='Correct']
    assert len(correct)==8
    assert all(r['task_success']=='Failure' and r['factual_alternative'].startswith('Unverifiable') for r in correct)
    assert all(r['temporal']=='Unverifiable' for r in rows)

def test_stop_ambiguity_is_not_unrecoverable_boundary():
    rows=f.load(a.OUT/'boundary_review_v1.json')
    stopped=[r for r in rows if r['native_termination']['stop_type']=='word']
    assert len(stopped)==8
    assert all(r['original_status']=='AMBIGUOUS' and r['unit_identifiable'] for r in stopped)
    assert all(r['alternative_task_success']=='Failure' and r['independent_boundary_truth'] is None for r in rows)

def test_no_input_from_future_cases_and_applicability_matches():
    matrix={(r['case_id'],r['condition']):r for r in f.load('docs/validation/p1d/proposed_v1/metric_applicability_v2.json')}
    for r in f.load(a.OUT/'provisional_analysis_dataset_v1.json'):
        assert r['case_id'] in f.b.CASE_IDS
        assert all(v==matrix[r['case_id'],'H_none'][k] for k,v in r['metric_applicability'].items())

def test_missingness_bounds_and_cluster_unit():
    u=f.load(a.OUT/'paired_uncertainty_v1.json')
    assert u['clusters']==u['paired_cases']==8 and u['missing']==0
    assert u['factual_all_eligible_unknown_difference_bounds']==[-.5,.5]
    assert u['temporal_all_eligible_unknown_difference_bounds']==[-1,1]

def test_stop_shadows_reproduce_outputs_not_accuracy():
    pairs=f.load(a.OUT/'paired_case_contributions_v1.json')
    assert all(r['stop_shadow_exact_equal'] and r['first_text_strip_equal'] and not r['first_text_exact_equal'] for r in pairs)
    example='Example:\n```\nUser: literal\n```\nAnswer.'
    assert stop_shadow(example,f.STOPS)=='Example:\n```'

def test_independent_form_hides_existing_scores_and_mapping():
    with (a.OUT/'independent_review_without_AI_scores_v1.csv').open(encoding='utf-8',newline='') as h:rows=list(csv.DictReader(h))
    assert len(rows)==16
    for r in rows:
        assert 'arm' not in r and 'request_id' not in r
        assert not any(r[k] for k in ('reviewer_id','factual','temporal','relevance','coherence','task_success','adjudication'))
