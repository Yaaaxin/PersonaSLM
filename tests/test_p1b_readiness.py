"""Offline readiness checks and adversarial source/review/contrast tests."""
from collections import Counter
from copy import deepcopy
import math

import pytest

from personaslm.p1b import build_dataset, render_evidence, canonical_hash
from personaslm.p1b_readiness import (EXPECTED, CHECKS, revise, independent_reference,
    audit, requests, review_rows, validate_reviews, contrast_weights, precision_plan)


@pytest.fixture
def dataset():
    return revise(build_dataset(), 'a'*64)[0]


def test_revision_preserves_parent_and_only_three_cases():
    original = build_dataset(); before = deepcopy(original)
    revised, changes = revise(original, 'a'*64)
    assert original == before
    assert [c['case_id'] for c in changes] == ['p1b_B_L2', 'p1b_B_L3', 'p1b_E_L3']
    assert sum(a != b for a, b in zip(original['cases'], revised['cases'])) == 3
    for c in changes[:2]:
        assert set(c['changes']) == {'question'}
    assert set(changes[2]['changes']) == {'facts', 'trusted_evidence', 'expected_answer'}
    assert original['cases'][14]['expected_answer']['components']['day'] == 'Thursday'


@pytest.mark.parametrize('short,expected', list(EXPECTED.items()))
def test_independent_english_reference_checks(dataset, short, expected):
    c = next(c for c in dataset['cases'] if c['case_id'] == 'p1b_' + short)
    # Independent reference must not depend on the builder query or stored key.
    c['query'] = None; c['expected_answer'] = None
    answer, proof = independent_reference(c)
    assert answer == expected and proof
    assert all(p['source_quote'] in c['trusted_evidence'] for p in proof)


@pytest.mark.parametrize('cid', ['p1b_C_L2', 'p1b_D_L3', 'p1b_E_L3', 'p1b_F_L3', 'p1b_H_L3'])
def test_wrong_source_rejected_even_with_self_consistent_oracle(dataset, cid):
    c = next(c for c in dataset['cases'] if c['case_id'] == cid)
    fid = c['expected_answer']['answer_fact_ids'][-1]
    next(f for f in c['facts'] if f['fact_id'] == fid)['value'] = 'Wrong replacement'
    c['trusted_evidence'] = render_evidence(c['facts'])
    key = list(c['expected_answer']['components'])[-1]
    c['expected_answer']['components'][key] = 'Wrong replacement'
    with pytest.raises(ValueError, match='Independent answer'): audit(dataset)


def test_ambiguous_entity_rejected(dataset):
    c = next(c for c in dataset['cases'] if c['case_id'] == 'p1b_F_L3')
    next(f for f in c['facts'] if f['value'] == 'treasurer')['value'] = 'archivist'
    c['trusted_evidence'] = render_evidence(c['facts'])
    with pytest.raises(ValueError, match='archivist'): independent_reference(c)


def test_context_reference_rejected(dataset):
    c = next(c for c in dataset['cases'] if c['case_id'] == 'p1b_H_L3')
    c['context'] = ['User: Please focus on Parcel 111. Please focus on Parcel 151.']
    with pytest.raises(ValueError, match='unique focus'): independent_reference(c)


def test_past_question_uses_past_date(dataset):
    c = next(c for c in dataset['cases'] if c['case_id'] == 'p1b_G_L3')
    answer, proof = independent_reference(c)
    assert answer == {'site': 'Meadow Lodge', 'current_site': 'Harbor Lodge'}
    assert [p['at'] for p in proof] == ['2027-03-20', '2027-04-15']


def test_all_192_prompts_exact_routing_and_not_executed(dataset):
    validation = audit(dataset)
    assert len(validation['cases']) == 24
    assert validation['human_review'] == 'OPEN'
    rows = requests(dataset)
    assert rows == requests(dataset) and rows != requests(dataset, seed=7)
    assert len({r['request_id'] for r in rows}) == 192
    assert all(n == 1 for n in Counter((r['case_id'], r['condition']) for r in rows).values())
    for start in range(0, 192, 8):
        assert len({r['case_id'] for r in rows[start:start+8]}) == 1
        assert {r['condition'] for r in rows[start:start+8]} == {f'C{i}' for i in range(8)}
    assert all(r['input_token_count'] is None and r['input_token_ids'] is None and not r['executed'] for r in rows)
    assert sum(r['applicability']['temporal_consistency'] for r in rows) == 88


def reviewed(dataset):
    master = review_rows(dataset, audit(dataset), canonical_hash(dataset))
    rows = deepcopy(master)
    for r in rows:
        for k in CHECKS: r['check_'+k] = 'PASS'
        r.update(researcher_decision='ACCEPT', reviewer_id='test_only_reviewer', review_method='synthetic unit-test fixture')
    return master, rows


def test_blank_review_rejected_and_no_timestamp_invention(dataset):
    master, rows = reviewed(dataset)
    with pytest.raises(ValueError, match='judgment'): validate_reviews(master, master)
    result = validate_reviews(master, rows)
    assert result['accepted'] == 24 and not result['inference_authorized']
    assert all(not r['reviewed_utc'] for r in rows)


@pytest.mark.parametrize('mutation', ['duplicate', 'missing', 'content', 'label', 'identity', 'version', 'conflict', 'timestamp'])
def test_review_failures_preserved(dataset, mutation):
    master, rows = reviewed(dataset)
    if mutation == 'duplicate': rows[-1] = deepcopy(rows[0])
    elif mutation == 'missing': rows.pop()
    elif mutation == 'content': rows[0]['trusted_evidence'] += 'X'
    elif mutation == 'label': rows[0]['check_answers_unique'] = 'yes'
    elif mutation == 'identity': rows[0]['reviewer_id'] = ''
    elif mutation == 'version': rows[0]['review_version'] = 'other'
    elif mutation == 'conflict': rows[0]['check_no_accidental_answer_leakage'] = 'FAIL'
    elif mutation == 'timestamp': rows[0]['reviewed_utc'] = 'unrecorded'
    with pytest.raises(ValueError): validate_reviews(master, rows)


def test_revision_required_review_is_registered_not_approved(dataset):
    master, rows = reviewed(dataset)
    rows[0]['check_entities_clear'] = 'UNCERTAIN'
    rows[0]['researcher_decision'] = 'REVISION_REQUIRED'
    rows[0]['reviewer_notes'] = 'Synthetic fixture: ambiguous subject needs review.'
    result = validate_reviews(master, rows)
    assert result['reviewed_records'] == 24 and result['accepted'] == 23 and not result['all_accepted']


def test_main_simple_and_interaction_conventions_differ():
    weights = contrast_weights()
    y = {'C0': 0, 'C1': 0, 'C2': 0, 'C3': 0, 'C4': 0, 'C5': 1, 'C6': 0, 'C7': 1}
    values = {k: sum(w[c]*y[c] for c in w) for k, w in weights.items()}
    assert values['C1-C0'] == 0 and values['S'] == .5 and values['SxH'] == 1
    assert values['SxF'] == 0 and values['FxH'] == 0 and values['SxFxH'] == 0
    assert all(sum(w.values()) == 0 for w in weights.values())


def test_precision_uses_actual_unequal_temporal_clusters(dataset):
    plan = precision_plan(dataset)
    row = next(r for r in plan['rows'] if r['metric'] == 'temporal_consistency' and r['contrast'] == 'C1-C0'
               and r['response_correlation_assumption'] == .5 and r['contrast_icc_assumption'] == .2 and r['comparisons'] == 1)
    assert (row['cases'], row['speakers']) == (11, 9)
    assert sorted(row['cluster_sizes'].values()) == [1]*7 + [2]*2
    assert math.isclose(row['effective_n'], 121/11.8)
    assert math.isclose(row['variance_assumption'], .25)
    main = next(r for r in plan['rows'] if all(r[k] == row[k] for k in ('metric', 'response_correlation_assumption', 'contrast_icc_assumption', 'comparisons')) and r['contrast'] == 'S')
    assert math.isclose(main['normal_approximation_half_width'], row['normal_approximation_half_width']/2)
