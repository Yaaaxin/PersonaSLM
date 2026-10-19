"""Authored timing fixtures only; no model, human annotations or private corpus."""
import base64
import copy
import json

import pytest

import english_sfh_native_cost_v1 as cost


@pytest.fixture
def authored():
    journals = [[], []]
    for index in range(100):
        speaker, case, condition = index // 20, index // 10, index % 10
        c = f'C{condition}' if condition < 8 else ('M_STYLE' if condition == 8 else 'N_STYLE')
        bits = condition if condition < 8 else 7
        s, f, h = (int(bool(bits & mask)) for mask in (1, 2, 4))
        n_input, n_output = 100 + speaker + 2*s + 3*f + 5*h, 10 + s + f + h
        prompt_ms, predicted_ms = n_input * 2., (n_output - 1) * 4.
        request = {'request_id': f'authored_request_{index}', 'speaker_id': f'authored_speaker_{speaker}',
                   'case_id': f'authored_case_{case}', 'condition': c,
                   'phase': 'FACTORIAL' if condition < 8 else 'DIAGNOSTIC', 'input_token_ids': [1] * n_input}
        timing = {'prompt_n': n_input, 'predicted_n': n_output, 'cache_n': 0,
                  'prompt_ms': prompt_ms, 'predicted_ms': predicted_ms,
                  'prompt_per_token_ms': 2., 'predicted_per_token_ms': 4.,
                  'prompt_per_second': 500., 'predicted_per_second': 250.}
        response = {'timings': timing, 'tokens_evaluated': n_input, 'tokens_predicted': n_output,
                    'tokens_cached': n_input + n_output - 1}
        raw = {'request_id': request['request_id'], 'response': response,
               'latency_seconds': (prompt_ms + predicted_ms) / 1000 + .01}
        journal = journals[int(index >= 92)]
        journal.extend([{'kind': 'english_sfh_started', 'data': request},
            {'kind': 'http_response', 'data': {'route': '/completion', 'status': 200,
                'body_base64': base64.b64encode(json.dumps(response).encode()).decode()}},
            {'kind': 'english_sfh_raw', 'data': raw}])
    return journals


def test_native_arithmetic_frozen_functions_and_restart_sensitivity(authored):
    before = cost.primary.METRICS, cost.independent.METRICS
    rows, recalculated = cost.extract(authored)
    report = cost.summarize(rows, recalculated)
    assert (cost.primary.METRICS, cost.independent.METRICS) == before
    assert report['responses'] == report['native_timing_coverage'] == 100
    assert report['cache_facts']['reported_prompt_reuse_count_zero'] == 100
    assert report['maximum_additive_identity_error_seconds'] < 1e-10
    effects = report['estimates']['factorial_effects']
    assert effects['input_tokens']['S']['mean'] == 2
    assert effects['input_tokens']['F']['mean'] == 3
    assert effects['input_tokens']['H']['mean'] == 5
    assert effects['prefill_seconds']['H']['mean'] == pytest.approx(.01)
    assert effects['decode_seconds']['H']['mean'] == pytest.approx(.004)
    assert effects['latency_seconds']['H']['mean'] == pytest.approx(.014)
    assert effects['input_tokens']['SFH']['mean'] == 0
    assert report['speaker_effect_vectors']['factorial_effects']['input_tokens']['H'] == {
        'sorted_values_no_identifiers': [5.] * 5, 'positive': 5, 'negative': 0, 'zero': 0}
    sensitivity = report['restart_sensitivity']
    speaker = sensitivity['exclude_entire_restart_affected_speaker']
    context = sensitivity['exclude_entire_restart_affected_context']
    assert speaker['responses_retained'] == 80 and speaker['contexts_per_speaker_sorted'] == [2] * 4
    assert context['responses_retained'] == 90 and context['contexts_per_speaker_sorted'] == [1, 2, 2, 2, 2]
    assert context['unequal_context_counts'] is True and speaker['unequal_context_counts'] is False
    assert 'different' in context['changed_estimand']
    assert 'authored_speaker' not in json.dumps(report)


@pytest.mark.parametrize('field,value', [('cache_n', 1), ('prompt_n', 999),
                                       ('predicted_per_token_ms', 3.6), ('prompt_ms', float('nan'))])
def test_invalid_native_timings_fail_closed(authored, field, value):
    request, raw = authored[0][0]['data'], copy.deepcopy(authored[0][2]['data'])
    raw['response']['timings'][field] = value
    with pytest.raises((ValueError, AssertionError)):
        cost.native_metrics(request, raw)


def test_http_tampering_and_duplicate_attempt_rejected(authored):
    bad = copy.deepcopy(authored)
    bad[0][2]['data']['response']['timings']['prompt_ms'] += 1
    with pytest.raises(ValueError, match='Raw/HTTP'):
        cost.extract(bad)
    authored[1].extend(copy.deepcopy(authored[0][:3]))
    with pytest.raises(ValueError, match='Duplicate'):
        cost.extract(authored)


def test_distinct_http_metric_recipe_and_scoped_restore_on_failure(authored, monkeypatch):
    rows, checked = cost.extract(authored)
    checked[0]['measurements']['prefill_seconds'] += 1
    original = cost.primary.METRICS, cost.independent.METRICS
    with pytest.raises(AssertionError, match='discrepancy'):
        cost.summarize(rows, checked)
    assert (cost.primary.METRICS, cost.independent.METRICS) == original


def test_exclusive_write_and_readonly_verify_do_not_touch_execution_or_reviews(authored, monkeypatch, tmp_path):
    rows, checked = cost.extract(authored)
    report, private = cost.summarize(rows, checked), {'rows': rows}
    monkeypatch.setattr(cost, 'PUBLIC', tmp_path / 'public/report.json')
    monkeypatch.setattr(cost, 'PRIVATE', tmp_path / 'private/rows.json')
    monkeypatch.setattr(cost, 'analyze', lambda: (copy.deepcopy(report), copy.deepcopy(private)))
    def forbidden(*args, **kwargs):
        pytest.fail('Post-hoc analysis called execution')
    for owner, name in ((cost.archive.original, 'run'), (cost.archive.original, 'preflight'),
                         (cost.archive.resume, 'execute')):
        monkeypatch.setattr(owner, name, forbidden)
    assert cost.main(['--write']) == 0
    before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in (cost.PUBLIC, cost.PRIVATE)]
    assert cost.main(['--verify']) == 0
    assert before == [(p.read_bytes(), p.stat().st_mtime_ns) for p in (cost.PUBLIC, cost.PRIVATE)]
    with pytest.raises(ValueError, match='no overwrite'):
        cost.main(['--write'])


def test_archival_verifier_source_must_be_frozen_before_reading_any_study(monkeypatch):
    monkeypatch.setattr(cost.archive, 'sha', lambda _: 'wrong')
    monkeypatch.setattr(cost.archive, 'reproduce', lambda *a: pytest.fail('Unbound verifier ran'))
    with pytest.raises(ValueError, match='Archival verifier source'):
        cost.analyze()
