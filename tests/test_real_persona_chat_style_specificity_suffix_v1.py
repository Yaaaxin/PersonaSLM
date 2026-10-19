"""Synthetic suffix-accounting fixtures; never read participant records."""
import base64
import json
from pathlib import Path

import pytest
import real_persona_chat_style_specificity_suffix_v1 as suffix


def fixture(monkeypatch, tmp_path):
    requests = [{'request_id': f'R{i}', 'input_token_ids': [i], 'request_sha256': str(i)} for i in range(64)]
    response = {'content': 'synthetic', 'tokens_predicted': 1}
    events = []
    for row in requests[:54]:
        events.extend([{'kind': 'specificity_started', 'data': row},
                       {'kind': 'http_request', 'data': {'route': '/completion', 'payload': row}},
                       {'kind': 'http_response', 'data': {'route': '/completion', 'status': 200,
                        'body_base64': base64.b64encode(json.dumps(response).encode()).decode()}},
                       {'kind': 'specificity_raw', 'data': {'request_id': row['request_id'], 'response': response,
                        'latency_seconds': 250.87214489997132 / 54}}])
    events.append({'kind': 'run_finished', 'event_hash': 'terminal', 'data': {}})
    receipt = {'status': 'PARTIAL', 'attempts': 54, 'responses': 54, 'unattempted': 10, 'failed_seconds': 0,
               'retries': 0, 'completion_inference_seconds': 250.87214489997132,
               'cumulative_generations': 626, 'cumulative_inference_seconds': suffix.BASE_SECONDS,
               'terminal_event_sha256': 'terminal'}
    amendment = {'original_manifest_sha256': 'hash', 'original_receipt_sha256': 'hash'}
    runs = tmp_path / 'original_runs'
    (runs / 'one').mkdir(parents=True)
    monkeypatch.setattr(suffix.base, 'RUNS', runs)
    monkeypatch.setattr(suffix.base, 'validate', lambda: {'requests': requests})
    monkeypatch.setattr(suffix, 'sha', lambda p: 'hash')
    monkeypatch.setattr(suffix, 'load', lambda p: amendment if p == suffix.AMENDMENT else receipt)
    monkeypatch.setattr(suffix.old.b, 'read_events', lambda p: events)
    monkeypatch.setattr(suffix.old, 'payload', lambda r: r)
    monkeypatch.setattr(suffix.old.b, 'validate_completion', lambda *a: None)
    return requests, events, receipt


def test_exact54_prefix_returns_only_original_unattempted10(monkeypatch, tmp_path):
    requests, _, _ = fixture(monkeypatch, tmp_path)
    assert suffix.reconcile()['requests'][suffix.PREFIX:] == requests[54:]
    assert len(requests[54:]) == suffix.N == 10


@pytest.mark.parametrize('problem', ['duplicate', 'failed', 'missing_raw', 'unsealed', 'wrong_budget', 'wrong_seconds', 'wrong_http'])
def test_reconciliation_fails_closed(monkeypatch, tmp_path, problem):
    requests, events, receipt = fixture(monkeypatch, tmp_path)
    if problem == 'duplicate':
        events[4] = {'kind': 'specificity_started', 'data': requests[0]}
    elif problem == 'failed':
        events.insert(-1, {'kind': 'specificity_failed', 'data': {'request_id': 'R53'}})
    elif problem == 'missing_raw':
        events.pop(-2)
    elif problem == 'unsealed':
        events.pop()
    elif problem == 'wrong_budget':
        receipt['cumulative_generations'] = 572
    elif problem == 'wrong_seconds':
        receipt['completion_inference_seconds'] += 1
    else:
        events[1]['data']['payload'] = {'request_id': 'wrong'}
    with pytest.raises(ValueError):
        suffix.reconcile()


@pytest.mark.parametrize('existing', ['claim', 'run', 'receipt'])
def test_any_suffix_execution_artifact_blocks_second_run(monkeypatch, tmp_path, existing):
    claim, runs, receipt = tmp_path / 'claim.json', tmp_path / 'runs', tmp_path / 'receipt.json'
    monkeypatch.setattr(suffix, 'CLAIM', claim)
    monkeypatch.setattr(suffix, 'RUNS', runs)
    monkeypatch.setattr(suffix, 'RECEIPT', receipt)
    suffix.unused()
    if existing == 'claim':
        claim.touch()
    elif existing == 'receipt':
        receipt.touch()
    else:
        (runs / 'one').mkdir(parents=True)
    with pytest.raises(ValueError, match='no retry'):
        suffix.unused()


def test_constants_preserve_safety_and_cumulative_allocation():
    assert (suffix.PREFIX, suffix.N, suffix.BASE_GENERATIONS) == (54, 10, 626)
    assert suffix.old.MIN_PREFLIGHT_RAM == 3 * 1024 ** 3
    assert suffix.old.MIN_READY_RAM == 1024 ** 3
    assert suffix.old.MIN_LIVE_RAM == 512 * 1024 ** 2


def test_snapshot_bindings_are_workspace_relative(monkeypatch):
    monkeypatch.setattr(suffix, 'sha', lambda p: 'hash')
    assert all(not Path(p).is_absolute() and '..' not in Path(p).parts for p in suffix.bindings())
