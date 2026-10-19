"""Authored metadata only. Never infer, register, or read real participant data."""
import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import english_sfh_resume_v1 as resume


def fixture(monkeypatch):
    sources = {'tools/authored.py': 'sourcehash'}
    monkeypatch.setattr(resume, 'source_hashes', lambda: sources)
    parent = {'batch': 'development', 'requests': [{'order': i, 'request_id': f'authored_{i}'} for i in range(100)],
              'allocation': {'maximum_inference_seconds': 3600, 'maximum_wall_seconds': 5400},
              'source_hashes': {}, 'input_hashes': {}, 'model': {'unchanged': True}, 'runtime': {'unchanged': True}}
    receipt = {'cumulative_generations': 780, 'cumulative_inference_seconds': 4449.800786499977,
               'completion_inference_seconds': 476.6806806000386, 'wall_seconds': 483.5787732999888}
    authorization = {'decision': 'AUTHORIZED_UNATTEMPTED_SUFFIX_ONLY', 'parent_manifest_sha256': resume.PARENT_SHA,
                     'parent_receipt_sha256': resume.RECEIPT_SHA, 'parent_terminal_sha256': resume.TERMINAL_SHA,
                     'start_index': 92, 'maximum_attempts': 8,
                     'ram_gates_bytes': [resume.original.MIN_RAM, resume.original.READY_RAM, resume.original.LIVE_RAM],
                     'source_hashes': sources}
    return parent, receipt, authorization


def test_exact_suffix_unchanged_request_order_and_remaining_budget(monkeypatch):
    parent, receipt, auth = fixture(monkeypatch)
    saved = copy.deepcopy(parent)
    result = resume.derive(parent, receipt, '2026-10-19T15:44:36+00:00', 'auth.json', 'authsha', auth)
    assert parent == saved
    assert result['requests'] == parent['requests'][92:]
    assert [row['order'] for row in result['requests']] == list(range(92, 100))
    assert result['model'] == parent['model'] and result['runtime'] == parent['runtime']
    assert result['allocation']['maximum_inference_seconds'] == 3600 - receipt['completion_inference_seconds']
    assert result['allocation']['maximum_wall_seconds'] == 5400 - receipt['wall_seconds']
    assert result['resume']['original_wall_deadline'] == '2026-10-19T17:14:36+00:00'


@pytest.mark.parametrize('field,value', [('maximum_attempts', 9), ('start_index', 91),
                                       ('parent_receipt_sha256', 'wrong'), ('ram_gates_bytes', [1, 1, 1])])
def test_no_retry_or_ram_gate_reduction(monkeypatch, field, value):
    parent, receipt, auth = fixture(monkeypatch)
    auth[field] = value
    with pytest.raises(ValueError, match='suffix authorization'):
        resume.derive(parent, receipt, '2026-10-19T15:44:36+00:00', 'auth.json', 'authsha', auth)


def test_no_source_change_or_budget_reset(monkeypatch):
    parent, receipt, auth = fixture(monkeypatch)
    auth['source_hashes'] = {}
    with pytest.raises(ValueError, match='source closure'):
        resume.derive(parent, receipt, '2026-10-19T15:44:36+00:00', 'auth.json', 'authsha', auth)
    parent, receipt, auth = fixture(monkeypatch)
    receipt['cumulative_generations'] = 688
    with pytest.raises(ValueError, match='budget reset'):
        resume.derive(parent, receipt, '2026-10-19T15:44:36+00:00', 'auth.json', 'authsha', auth)


def test_deadline_and_scoped_guard_restore(monkeypatch):
    past = {'resume': {'original_wall_deadline': '2000-01-01T00:00:00+00:00'}}
    with pytest.raises(ValueError, match='deadline expired'):
        resume.remaining_wall(past)
    future = {'resume': {'original_wall_deadline': (datetime.now(timezone.utc) + timedelta(seconds=10)).isoformat()}}
    validate, memory, client = resume.original.validate, resume.original.memory, resume.original.shared.b.LlamaClient
    gates = []
    monkeypatch.setattr(resume.original, 'memory', lambda minimum, pid: gates.append(minimum))
    patched_memory = resume.original.memory
    with resume.scoped_execution(future):
        assert resume.original.validate is resume.validate
        resume.original.memory(resume.original.LIVE_RAM, 123)
        assert resume.original.shared.b.LlamaClient is not client
    assert gates == [536870912]
    assert resume.original.validate is validate and resume.original.memory is patched_memory
    assert resume.original.shared.b.LlamaClient is client


def test_live_gate_still_rejects_single_byte_deficit(monkeypatch):
    monkeypatch.setattr(resume.original.shared.s, 'memory_observation', lambda pid: {
        'system': {'available_physical': resume.original.LIVE_RAM - 1}})
    future = {'resume': {'original_wall_deadline': (datetime.now(timezone.utc) + timedelta(seconds=10)).isoformat()}}
    with resume.scoped_execution(future), pytest.raises(ValueError, match='RAM'):
        resume.original.memory(resume.original.LIVE_RAM, 123)


def test_repeat_suffix_claim_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(resume.original, 'PRIVATE', tmp_path)
    claimed = tmp_path / resume.BATCH / 'claim_v1.json'
    claimed.parent.mkdir()
    claimed.touch()
    with pytest.raises(ValueError, match='already claimed'):
        resume.original.unused(resume.BATCH)


@pytest.mark.parametrize('active,failed', [('already_started', 0), (None, 1)])
def test_parent_with_an_active_or_failed_request_cannot_resume(monkeypatch, active, failed):
    plan = {'requests': [dict(request_id=f'authored_{i}') for i in range(100)]}
    receipt = {'status': 'PARTIAL', 'attempts': 92, 'responses': 92, 'failed_seconds': 0,
               'unattempted': 8, 'retries': 0, 'terminal_event_sha256': resume.TERMINAL_SHA,
               'run_directory': 'authored_only'}
    monkeypatch.setattr(resume.original, 'sha', lambda path: resume.PARENT_SHA if path == resume.PARENT_MANIFEST else resume.RECEIPT_SHA)
    monkeypatch.setattr(resume, 'ORIGINAL_VALIDATE', lambda *args: (plan, 688, 3973))
    monkeypatch.setattr(resume.independent, 'audit_run', lambda batch: (plan, receipt, [], 0, failed))
    monkeypatch.setattr(resume.independent, 'read_events', lambda folder: [{'kind': 'failure', 'data': {
        'type': 'ValueError', 'message': 'Available physical RAM below frozen gate', 'request_id': active}}])
    with pytest.raises(ValueError, match='exact sealed|between requests'):
        resume.audit_parent()
