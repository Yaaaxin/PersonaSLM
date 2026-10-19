"""Authored two-journal arithmetic fixtures only; no actual raw evidence access."""
import copy

import pytest

import english_sfh_combined_v1 as combined
from test_english_sfh_execution_v1 import manifest


def fixture():
    plan = manifest()
    requests = plan['requests']
    first, second, parent_rows, suffix_rows = [], [], [], []
    for index, request in enumerate(requests):
        # Fixture request case labels must remain globally unique for this grid.
        request['case_id'] = request['speaker_id'] + '_' + request['case_id']
        response = {'content': 'An authored professional continuation without copying.',
                    'tokens_predicted': 9 + index % 3, 'stop_type': 'eos'}
        raw = {'request_id': request['request_id'], 'response': response, 'latency_seconds': 0.25 + index / 1000}
        events = first if index < 92 else second
        events.extend([{'kind': 'english_sfh_started', 'data': request}, {'kind': 'english_sfh_raw', 'data': raw}])
        identity = {key: request[key] for key in ('request_id', 'speaker_id', 'case_id', 'condition', 'phase')}
        row = identity | {'measurements': combined.independent.measurements(request, response, raw['latency_seconds'])}
        parent_rows.append(row if index < 92 else identity | {'measurements': dict.fromkeys(combined.primary.METRICS)})
        if index >= 92:
            suffix_rows.append(row)
    return plan, parent_rows, {'requests': requests[92:]}, suffix_rows, first, second


def test_disjoint_journals_restore100_without_changing_original_missing_rows():
    values = fixture()
    preserved = copy.deepcopy(values[1])
    rows, estimates, responses, attempts = combined.paired_rows(*values)
    assert responses == attempts == len(rows) == 100
    assert values[1] == preserved
    assert all(row['measurements']['output_tokens'] is not None for row in rows)
    assert estimates['condition_summary']['output_tokens']['C0']['allocated'] == 10
    assert all(value['n'] == 5 for value in estimates['factorial_effects']['output_tokens'].values())


def test_repeated_attempt_or_changed_suffix_rejected():
    values = fixture()
    values[-1].insert(0, values[-2][0])
    with pytest.raises(ValueError, match='Repeated cross-journal attempt'):
        combined.paired_rows(*values)
    values = fixture()
    values[2]['requests'] = list(reversed(values[2]['requests']))
    with pytest.raises(ValueError, match='exact original suffix'):
        combined.paired_rows(*values)


def test_failed_or_unattempted_suffix_is_missing_not_zero():
    values = fixture()
    request_id = values[3][-1]['request_id']
    values[3][-1]['measurements'] = dict.fromkeys(combined.primary.METRICS)
    values[-1][:] = [event for event in values[-1] if not (
        event['kind'] == 'english_sfh_raw' and event['data']['request_id'] == request_id)]
    rows, estimates, count, attempts = combined.paired_rows(*values)
    assert count == 99 and attempts == 100
    assert all(value is None for value in rows[-1]['measurements'].values())
    assert estimates['condition_summary']['output_tokens']['N_STYLE']['missing_or_inapplicable'] == 1
