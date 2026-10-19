"""Authored metadata only: legitimate new HEAD must not block read-only analysis."""
import copy
import json
from pathlib import Path
import subprocess

import pytest

import english_sfh_archival_reproduce_v1 as archival
from test_english_sfh_resume_v1 import fixture as authored_resume


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding='utf-8')
    return archival.sha(path)


def suffix_fixture(monkeypatch, tmp_path):
    parent, receipt, authorization = authored_resume(monkeypatch)
    parent['source_head'] = 'a' * 40
    public = tmp_path / 'public'
    auth_path = public / 'authored_authorization.json'
    auth_sha = write_json(auth_path, authorization)
    created = '2026-10-19T15:44:36+00:00'
    plan = archival.resume.derive(parent, receipt, created, auth_path, auth_sha, authorization)
    path = tmp_path / 'private/frozen_manifest.json'
    manifest_sha = write_json(path, plan)
    monkeypatch.setattr(archival.resume, 'MANIFEST', path)
    monkeypatch.setattr(archival, 'PUBLIC', public)
    return path, manifest_sha, parent, receipt, created, {'suffix_manifest_sha256': manifest_sha}


def test_legitimate_new_head_does_not_call_execution_validator(monkeypatch, tmp_path):
    path, digest, parent, receipt, created, bindings = suffix_fixture(monkeypatch, tmp_path)

    def advanced_head(command, **kwargs):
        assert command == ['git', 'rev-parse', 'HEAD']
        return 'b' * 40 + '\n'

    def forbidden(*args, **kwargs):
        pytest.fail('Archival analysis called an execution or HEAD-dependent validator')

    monkeypatch.setattr(subprocess, 'check_output', advanced_head)
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip() != parent['source_head']
    for owner, name in [(archival.original, 'validate'), (archival.original, 'preflight'),
                        (archival.original, 'run'), (archival.resume, 'ORIGINAL_VALIDATE'),
                        (archival.resume, 'execute'), (archival.resume, 'prepared')]:
        monkeypatch.setattr(owner, name, forbidden)
    result, generations, seconds = archival.archival_validate(path, digest, parent=parent,
        parent_receipt=receipt, created_utc=created, bindings=bindings)
    assert result['requests'] == parent['requests'][92:]
    assert result['source_head'] == 'a' * 40 and generations == 780 and seconds == 4449.800786499977


def test_suffix_bytes_cannot_change_even_with_new_manifest_hash(monkeypatch, tmp_path):
    path, _, parent, receipt, created, _ = suffix_fixture(monkeypatch, tmp_path)
    changed = json.loads(path.read_text(encoding='utf-8'))
    changed['requests'][0]['request_id'] = 'not_the_original_suffix'
    digest = write_json(path, changed)
    with pytest.raises(ValueError, match='differs from exact original'):
        archival.archival_validate(path, digest, parent=parent, parent_receipt=receipt,
            created_utc=created, bindings={'suffix_manifest_sha256': digest})


def test_authorization_cannot_change_after_freeze(monkeypatch, tmp_path):
    path, digest, parent, receipt, created, bindings = suffix_fixture(monkeypatch, tmp_path)
    plan = json.loads(path.read_text(encoding='utf-8'))
    auth = Path(plan['resume']['authorization_path'])
    value = json.loads(auth.read_text(encoding='utf-8'))
    value['maximum_attempts'] = 9
    write_json(auth, value)
    with pytest.raises(ValueError, match='Externally bound artifact'):
        archival.archival_validate(path, digest, parent=parent, parent_receipt=receipt,
            created_utc=created, bindings=bindings)


def test_live_source_tampering_and_external_hash_guard(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / 'tools/authored.py'
    path.parent.mkdir()
    path.write_text('# original authored helper\n', encoding='utf-8')
    digest = archival.sha(path)
    path.write_text('# changed authored helper\n', encoding='utf-8')
    with pytest.raises(ValueError, match='Frozen live source changed'):
        archival.live_sources({'source_hashes': {'tools/authored.py': digest}})
    artifact = tmp_path / 'authored.json'
    bound = write_json(artifact, {'result': 1})
    write_json(artifact, {'result': 2})
    with pytest.raises(ValueError, match='Externally bound artifact'):
        archival.checked_json(artifact, bound)


def test_receipt_write_once_and_verify_never_rewrites(monkeypatch, tmp_path):
    path = tmp_path / 'archival_receipt.json'
    result = {'status': 'PASS', 'responses': 100, 'new_generations': 0,
              'analysis_sha256': 'analysis', 'prior_reproduction_sha256': 'reproduction'}
    monkeypatch.setattr(archival, 'ARCHIVAL_RECEIPT', path)
    monkeypatch.setattr(archival, 'reproduce', lambda *args: copy.deepcopy(result))
    arguments = ['--analysis-sha256', 'analysis', '--reproduction-sha256', 'reproduction']
    assert archival.main(['--write'] + arguments) == 0
    data, modified = path.read_bytes(), path.stat().st_mtime_ns
    assert archival.main(['--verify'] + arguments) == 0
    assert path.read_bytes() == data and path.stat().st_mtime_ns == modified
    with pytest.raises(FileExistsError):
        archival.main(['--write'] + arguments)
    result['responses'] = 99
    with pytest.raises(AssertionError, match='discrepancy'):
        archival.main(['--verify'] + arguments)
