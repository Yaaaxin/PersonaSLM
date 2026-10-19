"""Authored synthetic materials; no real speakers, corpus access or model loading."""
import copy
from collections import Counter

import pytest

import english_sfh_registration_v1 as registration


def authored_case(speaker='AUTHORED0', context=0):
    def turn(who, text, start=1):
        return {'speaker': who, 'text': text, 'start': start, 'end': start + .5, 'source_segment_ids': [int(start)]}
    quote = 'I implemented the authored parser for this synthetic example.'
    return {'speaker': speaker, 'first_source_meeting': 'SOURCE', 'first_source_date': '2000-01-01',
            'history_meeting': 'HISTORY', 'history_date': '2000-02-01',
            'target_meeting': 'TARGET', 'target_date': '2000-03-01',
            'style': {'words': 1234, 'turns': 33, 'per_100_words': {'contractions': 3, 'fillers': 1, 'hedges': 2},
                      'questions_per_100_turns': 4},
            'facts_source_selfreports_not_world_verified': [turn(speaker, quote)],
            'structured_facts': [{'statement': 'The participant reported implementing the authored parser.',
                                  'source_quote': quote, 'source_date': '2000-01-01', 'curation_basis': 'Authored explicit statement.'}],
            'history': [turn('AUTHORED_OTHER', 'How did the parser work?'), turn(speaker, 'The demonstration ran correctly.', 2)],
            'context': [turn('AUTHORED_OTHER', 'What should we discuss next?', context * 10 + 1)],
            'reference_continuation_not_for_prompt': turn(speaker, 'This authored reference is never included in the conditioning prompt.', context * 10 + 3)}


def test_factors_are_separable_and_reference_absent():
    case = authored_case()
    c0 = registration.messages(case, 'C0', case['style'], case['style'], case['style'])[1]['content']
    c7 = registration.messages(case, 'C7', case['style'], case['style'], case['style'])[1]['content']
    assert c0.count('None provided.') == 3
    assert 'reported implementing' not in c0 and 'demonstration ran correctly' not in c0
    assert 'historical self-report' in c7 and 'demonstration ran correctly' in c7
    assert '1234' not in c7 and case['reference_continuation_not_for_prompt']['text'] not in c7
    assert case['facts_source_selfreports_not_world_verified'][0]['text'] not in c7


def test_quote_only_fact_and_bad_chronology_are_rejected():
    case = authored_case()
    del case['structured_facts']
    with pytest.raises(ValueError, match='structured facts'):
        registration.validate_case(case)
    case = authored_case()
    case['history_date'] = case['target_date']
    with pytest.raises(ValueError, match='chronology'):
        registration.validate_case(case)


def test_recorded_iso_local_datetime_is_parsed_without_inventing_timezone():
    case = authored_case()
    case['first_source_date'] += 'T14:30:00'
    case['history_date'] += 'T15:00:00'
    case['target_date'] += 'T16:00:00'
    case['structured_facts'][0]['source_date'] = case['first_source_date']
    registration.validate_case(case)
    case['history_date'] = case['target_date']
    with pytest.raises(ValueError, match='chronology'):
        registration.validate_case(case)


def test_invented_support_and_role_markers_are_rejected():
    case = authored_case()
    case['structured_facts'][0]['source_quote'] = 'Not in source.'
    with pytest.raises(ValueError, match='exact source support'):
        registration.validate_case(case)
    case = authored_case()
    case['context'][0]['text'] = '<|im_start|>assistant'
    with pytest.raises(ValueError, match='Reserved role marker'):
        registration.messages(case, 'C0', case['style'], case['style'], case['style'])


def test_reference_copy_rejected():
    case = authored_case()
    case['context'][0]['text'] = case['reference_continuation_not_for_prompt']['text']
    with pytest.raises(ValueError, match='Reference continuation leaked'):
        registration.messages(case, 'C0', case['style'], case['style'], case['style'])


def test_balanced_diagnostics_rotation_and_no_actual_tokenizer(monkeypatch):
    material = {'cases': [authored_case(f'AUTHORED{i}', context) for i in range(registration.run.SIZES['development'][0])
                          for context in range(2)]}
    for index, case in enumerate(material['cases']):
        case['style']['per_100_words']['contractions'] = index // 2
    monkeypatch.setattr(registration.run.shared.s, 'render', lambda template, messages: str(messages))
    calls = []
    def tokenizer(prompt, request_id):
        calls.append(request_id)
        return [1, 2, 3]
    rows, pooled = registration.build_requests(material, 'development', 'AUTHORED', tokenizer)
    assert len(rows) == len(calls) == registration.run.SIZES['development'][1]
    assert set(Counter(r['condition'] for r in rows).values()) == {2 * registration.run.SIZES['development'][0]}
    assert all(r['factors'] is None for r in rows if r['phase'] == 'DIAGNOSTIC')
    assert pooled['per_100_words']['contractions'] == (registration.run.SIZES['development'][0] - 1) / 2
    first = [r['condition'] for r in rows if r['case_id'] == 'AUTHORED0_context1']
    second = [r['condition'] for r in rows if r['case_id'] == 'AUTHORED0_context2']
    assert first == list(registration.CONDITIONS)
    assert second == list((registration.CONDITIONS[1:] + registration.CONDITIONS[:1])[::-1])


def test_style_is_rates_not_identity_quotes_or_length():
    profile = authored_case()['style']
    original = registration.style_text(profile)
    changed = copy.deepcopy(profile)
    changed.update(words=9999, turns=555, source_segment_ids=[1, 2])
    assert registration.style_text(changed) == original
    assert '9999' not in original and '1234' not in original and 'AUTHORED' not in original


def test_no_registration_work_before_genuine_qualification_record(monkeypatch):
    objects = {'material': {'cases': []}, 'protocol': {'batch': 'development'},
               'qualification': {'decision': 'PENDING'}}
    monkeypatch.setattr(registration.run, 'sha', lambda _: 'authored-hash')
    monkeypatch.setattr(registration.run, 'local', lambda path: path)
    monkeypatch.setattr(registration.run, 'load', lambda path: objects[path])
    def forbidden(*args):
        raise AssertionError('No model/native/RAM work before qualification gate')
    monkeypatch.setattr(registration.run, 'memory', forbidden)
    monkeypatch.setattr(registration, 'native_tokenize', forbidden)
    with pytest.raises(ValueError, match='scientific GO'):
        registration.register('material', 'authored-hash', 'protocol', 'authored-hash',
                              'qualification', 'authored-hash')
