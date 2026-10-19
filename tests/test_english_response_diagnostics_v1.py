import copy

import pytest

import english_response_diagnostics_v1 as diagnostics
from test_english_model_comparison_analysis_v1 import rows


@pytest.mark.parametrize('text', ['', ' \r\n\t', '!!!', '日本語', 'one two three four',
    'one two three four five', 'ONE two three four five one two three four five',
    "It's a test. It's a test. It's a test.", 'alpha ' * 20, 'alpha ' * 21])
def test_direct_count_agrees_and_preserves_applicability(text):
    assert diagnostics.measure(text) == diagnostics.direct_measure(text)


def test_empty_is_distinct_from_no_english_words_and_missing_windows():
    assert diagnostics.measure('')['raw_empty'] == 1
    assert diagnostics.measure(' \n')['raw_empty'] == 0
    assert diagnostics.measure(' \n')['whitespace_empty'] == 1
    assert diagnostics.measure('!!!')['whitespace_empty'] == 0
    assert diagnostics.measure('one two')['repeat5_excess'] is None
    assert diagnostics.measure('one two three four five')['repeat5_excess'] == 0
    with pytest.raises(ValueError):
        diagnostics.measure(None)


def test_fixed_prefix_is_not_a_zero_for_short_answers():
    assert diagnostics.measure('a ' * 19)['prefix20_repeat5_excess'] is None
    assert diagnostics.measure('a ' * 20)['prefix20_repeat5_excess'] == 15 / 16
    assert diagnostics.measure('a ' * 20 + 'b c d e f')['prefix20_repeat5_excess'] == 15 / 16


def test_actual_recurrence_and_case_insensitivity():
    result = diagnostics.measure('One two three four five one two three four five')
    assert result['repeat5_excess'] == 1 / 6
    assert result['repeat5_any'] == 1


def test_two_factorial_implementations_and_na_coverage():
    group = rows('base')
    for row in group:
        row['measurements'] = dict.fromkeys(diagnostics.METRICS, row['measurements']['output_tokens'])
    result = diagnostics.summarize(group)
    assert result['estimates']['all_speakers']['factorial_effects']['raw_empty']['S']['mean'] == 3
    changed = copy.deepcopy(group)
    changed[0]['measurements']['repeat5_excess'] = None
    result = diagnostics.summarize(changed)
    assert result['overall']['repeat5_excess']['n'] == 99
    assert result['estimates']['all_speakers']['factorial_effects']['repeat5_excess']['S']['n'] == 4


def test_existing_evidence_stops_before_data_access(tmp_path, monkeypatch):
    target = tmp_path / 'existing.json'
    target.write_text('authored evidence', encoding='utf-8')
    monkeypatch.setattr(diagnostics, 'RESULT', target)
    monkeypatch.setattr(diagnostics, 'ROWS', tmp_path / 'private.json')
    monkeypatch.setattr(diagnostics, 'calculate', lambda *args: pytest.fail('Must not access data'))
    with pytest.raises(ValueError, match='No overwrite'):
        diagnostics.run('write', 'scope', 'implementation')
    assert target.read_text(encoding='utf-8') == 'authored evidence'
