"""Measurement safety tests; synthetic unit ratings are never research annotations."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

TOOLS = Path(__file__).parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location('measurement_audit', TOOLS / 'p1b_measurement_audit.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def fixture():
    master = audit.core.csv_records(audit.OLD / 'output_human_review_v1.csv')
    return audit.split_views(master)


def completed_unit():
    master = [fixture()[0][0]]
    rows = deepcopy(master)
    row = rows[0]
    row.update(reviewer_id='SYNTHETIC_UNIT_TEST', review_assistance='unit fixture',
               prior_access_to_treatments_or_scores='unit fixture',
               human_semantic_completeness='UNCERTAIN', human_answer_delivery='UNCERTAIN',
               human_factual_consistency='Unverifiable', human_unverifiable_reason='unit test only',
               human_evidence_quotations='synthetic test assertion',
               human_response_relevance_1_to_5='3', human_conversational_coherence_1_to_5='3',
               human_temporal_consistency='Unverifiable' if row['applicable_temporal_consistency']=='true' else 'Not Applicable')
    return master, rows


def test_split_removes_structural_anchors_and_retains_192_stable_ids():
    first, second = fixture()
    assert len(first) == len(second) == 192
    assert {r['anonymous_response_id'] for r in first} == {f'BR{i:03}' for i in range(1,193)}
    assert not set(first[0]).intersection(audit.HIDE)
    assert not {'condition','factors','request_id','persona_id','case_id','automated_correctness'}.intersection(first[0])
    assert all(not v for r in first for k,v in r.items() if k.startswith('human_') or k in audit.PROVENANCE)
    original = {r['anonymous_response_id']:r for r in audit.core.csv_records(audit.OLD/'output_human_review_v1.csv')}
    for a,b in zip(first,second):
        source=original[a['anonymous_response_id']]
        assert a['raw_first_reply']==source['raw_first_reply']
        assert b['raw_full_continuation']==source['raw_full_continuation']
        assert b['structural_status']==source['structural_status']
    assert fixture()==(first,second)


@pytest.mark.parametrize('field', ['raw_first_reply','trusted_evidence','review_version','applicable_factual_consistency','anonymous_case_id','first_reply_sha256'])
def test_immutable_mutations_rejected(field):
    master, rows=completed_unit()
    rows[0][field]+=' altered'
    with pytest.raises(ValueError,match='Immutable'):
        audit.validate_submission(master,rows)


def test_duplicate_or_missing_ids_rejected():
    master,rows=completed_unit()
    for invalid in (rows+rows,[]):
        with pytest.raises(ValueError,match='response IDs'):
            audit.validate_submission(master,invalid)


@pytest.mark.parametrize('field,value', [('human_factual_consistency','Not Applicable'),('human_factual_consistency','PASS'),
    ('human_response_relevance_1_to_5','6'),('human_semantic_completeness','Correct'),('reviewer_id',''),
    ('human_unverifiable_reason','')])
def test_invalid_or_missing_ratings_rejected(field,value):
    master, rows=completed_unit()
    rows[0][field]=value
    with pytest.raises(ValueError):
        audit.validate_submission(master,rows)


def test_explicit_missing_is_retained_not_incorrect_or_na():
    master,rows=completed_unit()
    rows[0]['human_factual_consistency']=''
    with pytest.raises(ValueError,match='Missing eligible'):
        audit.validate_submission(master,rows)
    rows[0]['human_missing_metric_reason']='Unit boundary cannot be established in synthetic test'
    result=audit.validate_submission(master,rows)
    assert result['explicitly_missing']['factual_consistency']==1
    assert 'factual_consistency' not in result['assessed']
    assert rows[0]['reviewed_utc']==''


def test_bootstrap_resamples_speakers_with_both_cases_and_preserves_scale():
    values=[{'outcome':'CROSS_TURN','contrast':'C1-C0','persona_id':p,
             'paired_value':v,'evaluable':True} for p,v in [('a',1),('a',1),('b',-1),('b',-1)]]
    summary=audit.cluster_intervals(values,repeats=200,seed=8)[0]
    assert summary['speaker_clusters']==2 and summary['evaluable_cases']==4
    assert summary['estimate']==0
    assert summary['lower_percentile_95']==-1 and summary['upper_percentile_95']==1
    assert audit.cluster_intervals(values,200,8)==[summary]


def test_masking_rejects_annotated_source():
    rows=audit.core.csv_records(audit.OLD/'output_human_review_v1.csv')
    rows[0]['human_factual_consistency']='Correct'
    with pytest.raises(ValueError,match='blank review master'):
        audit.split_views(rows)


def test_real_packet_ambiguous_span_never_replaced_by_later_answer():
    first, second=fixture()
    source=next(r for r in second if r['structural_status']=='AMBIGUOUS')
    assert 'Factual question:' in source['raw_first_reply']
    assert 'Assistant: Bookbinding Group 6' in source['excluded_generated_continuation']
    assert next(r for r in first if r['anonymous_response_id']==source['anonymous_response_id'])['raw_first_reply']==source['raw_first_reply']


def test_context_and_metric_denominators_preserved():
    first,_=fixture()
    assert sum(r['applicable_temporal_consistency']=='true' for r in first)==88
    assert all(r['applicable_factual_consistency']=='true' for r in first)
    assert all(r['fixed_preceding_context'] for r in first)
