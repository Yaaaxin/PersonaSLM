"""Scientific review, input preservation and tokenization-only boundary tests."""
from copy import deepcopy
import csv
import json
from pathlib import Path

import pytest

from personaslm.p1b import hash_text
from personaslm.p1b_review_resolution import (compare_review_sources, inspect_prompts,
    recent_turns, context_necessity_cases, TokenizationOnlyClient, tokenized_requests)

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT/'docs/validation/p1b/final_v1'
SUPPORT = ROOT/'docs/validation/p1b/review_support'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def csv_rows(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


@pytest.fixture
def materials():
    return (read(ROOT/'data/synthetic/p1b_development_proposed_v2.json'), read(OLD/'calibration_manifest_v1.json'))


@pytest.fixture
def reviews():
    return [csv_rows(p) for p in (OLD/'stimulus_review_v2.csv',
        SUPPORT/'PersonaSLM_P1b_stimulus_review_v2_with_AI_suggestions.csv',
        SUPPORT/'PersonaSLM_P1b_24case_independent_AI_stimulus_audit_v1.csv')]


def test_all_reference_dates_visible_and_original_fields_preserved(materials, reviews):
    dataset, parent = materials
    frozen = deepcopy(materials)
    report = inspect_prompts(dataset, parent)
    assert report['visible_reference_dates'] == 192 and report['undated_question_cases'] == 13
    assert report['same_user_followup_prompts'] == 8
    source = compare_review_sources(*reviews)
    assert source['original_fields_compared'] == 984 and source['original_fields_changed'] == 0
    assert source['human_decisions_present'] == 0
    assert source['ai_status_counts'] == {'HOLD_REFERENCE_DATE_VISIBILITY': 13,
        'REVIEW_READY_WITH_LIMITATIONS': 10, 'HOLD_TURN_BOUNDARY_CHECK': 1}
    assert materials == frozen


@pytest.mark.parametrize('mutation', ['duplicate', 'evidence', 'human_field', 'version', 'quote', 'ai_disagreement'])
def test_invalid_review_materials_are_not_silently_imported(reviews, mutation):
    master, suggested, independent = reviews
    if mutation == 'duplicate': suggested[-1] = deepcopy(suggested[0])
    elif mutation == 'evidence': suggested[0]['trusted_evidence'] += ' fabricated text'
    elif mutation == 'human_field': suggested[0]['check_evidence_sufficient'] = 'PASS'
    elif mutation == 'version': independent[0]['source_review_version'] = 'different'
    elif mutation == 'quote':
        independent[0]['ai_reference_quotes'] = suggested[0]['ai_reference_quotes'] = 'not in the evidence'
    elif mutation == 'ai_disagreement': independent[0]['ai_proposed_status'] = 'changed'
    with pytest.raises(ValueError): compare_review_sources(master, suggested, independent)


@pytest.mark.parametrize('condition', [f'C{i}' for i in range(8)])
def test_h_l3_is_explicit_two_user_messages_not_missing_boundary(materials, condition):
    _, manifest = materials
    row = next(r for r in manifest['requests'] if r['case_id']=='p1b_H_L3' and r['condition']==condition)
    turns = recent_turns(row['prompt'])
    assert [t['role'] for t in turns] == ['User','Assistant','User','User','Assistant']
    assert turns[2]['content'] == 'Please focus on Parcel 111.'
    assert turns[3]['content'] == 'Which desk should it go to on 2027-04-10?'
    assert turns[4]['content'] == ''
    for turn in turns:
        assert row['prompt'][turn['start']:turn['end']].startswith(turn['role']+':')


@pytest.mark.parametrize('bad', [
    'no section', '\n\nRECENT CONVERSATION:\nAssistant:',
    '\n\nRECENT CONVERSATION:\nUser: Question\nAssistant: supplied answer',
    '\n\nRECENT CONVERSATION:\nUnlabelled text\nUser: Question\nAssistant:',
    '\n\nRECENT CONVERSATION:\nUser:\nAssistant:'])
def test_bad_boundaries_refused(bad):
    with pytest.raises(ValueError): recent_turns(bad)


@pytest.mark.parametrize('change', ['date', 'order', 'evidence', 'question', 'applicability'])
def test_mutated_frozen_requests_refused(materials, change):
    dataset, manifest = materials
    if change == 'order': manifest['requests'].reverse()
    elif change == 'date':
        manifest['requests'][0]['prompt'] = manifest['requests'][0]['prompt'].replace('Evaluation reference: 2027-04-15.', '')
    elif change == 'evidence': manifest['requests'][0]['trusted_evidence_sha256'] = 'a'*64
    elif change == 'question': manifest['requests'][0]['question_sha256'] = 'b'*64
    else: manifest['requests'][0]['applicability']['temporal_consistency'] = 'changed'
    with pytest.raises(ValueError): inspect_prompts(dataset, manifest)


def test_context_is_necessary_only_when_source_has_competing_answers(materials):
    cases = context_necessity_cases(materials[0])
    assert [r['distinct_possible_answers'] for r in cases] == [1, 1, 2]
    assert [r['context_necessity_supported_by_source'] for r in cases] == [False, False, True]
    assert cases[2]['possible_parcel_answers_without_focus'] == {'Parcel 111': 'Ash Desk', 'Parcel 151': 'Oak Desk'}
    assert all(r['model_requests'] == 0 and r['empirical_context_use'] == 'UNTESTED' for r in cases)


def test_completion_blocked_before_any_http_request():
    events = []
    client = TokenizationOnlyClient('http://127.0.0.1:8080', audit=lambda *args: events.append(args))
    with pytest.raises(ValueError, match='forbidden'): client.complete([1])
    with pytest.raises(ValueError, match='forbidden'): client.request('/completion', {'prompt':[1]})
    with pytest.raises(ValueError, match='forbidden'): client.request('/v1/chat/completions', {})
    assert events == []


def test_tokenization_preserves_exact_input_and_logs_before_context_refusal(materials):
    rows = materials[1]['requests'][:1]; before = deepcopy(rows); seen = []; events = []
    def tokenizer(text):
        seen.append(text)
        return [1]*4001  # Test fixture only: exceeds4096 after96 output tokens.
    with pytest.raises(ValueError, match='exceed context'):
        tokenized_requests(rows, tokenizer, lambda *args: events.append(args))
    assert seen == [rows[0]['prompt']] and rows == before
    assert events[0][0] == 'p1b_prompt_tokenized' and events[0][1]['context_fit'] == 'FAILED'
    assert events[0][1]['input_token_count'] == 4001


def test_tokenization_rejects_boolean_ids_and_altered_prompt(materials):
    rows = materials[1]['requests'][:1]
    with pytest.raises(ValueError, match='integer token IDs'):
        tokenized_requests(rows, lambda _: [True], lambda *args: None)
    rows[0]['prompt'] += 'changed'
    with pytest.raises(ValueError, match='altered prompt'):
        tokenized_requests(rows, lambda _: pytest.fail('Must reject before tokenization'), lambda *args: None)


def test_tokenized_plan_keeps_all_case_conditions_and_unknown_human_labels(materials):
    rows = materials[1]['requests']; before = deepcopy(rows); events=[]
    result = tokenized_requests(rows, lambda _: [1, 2, 3], lambda *args: events.append(args))
    assert len(result) == len(events) == 192 and rows == before
    for a,b in zip(rows,result):
        assert a['request_id']==b['request_id'] and a['prompt_sha256']==b['prompt_sha256']
        assert a['applicability']==b['applicability'] and b['executed'] is False
        assert b['input_token_count']==3 and b['remaining_context_after_output_budget']==3997
