import pytest
from pathlib import Path
from personaslm.provenance import append_unique_atomic, require_local_path, repository_root, audit_local_paths


def test_rejects_external_file_access():
    with pytest.raises(ValueError):
        require_local_path(Path.home() / "some_private_file.txt")


def test_project_root_resolves_correctly():
    assert (repository_root() / "docs/research_protocol_v1.1.md").exists()


def test_isolation_audit_passes_on_starter_repo():
    report = audit_local_paths()
    assert not report["links_or_junctions"]
    assert report["passed"] == (not report["unreadable_paths"])
    assert report["status"] in ("PASS", "PARTIAL")


def test_unreadable_paths_cannot_be_reported_as_pass(monkeypatch):
    def unreadable_walk(root, followlinks, onerror):
        onerror(PermissionError(13, "test access denied", str(root / "unreadable")))
        return iter([])
    monkeypatch.setattr("personaslm.provenance.os.walk", unreadable_walk)
    report = audit_local_paths()
    assert report["status"] == "PARTIAL"
    assert not report["passed"]


def test_atomic_append_deduplicates_on_key():
    file = repository_root() / "results/test_atomic_unique.jsonl"
    try:
        assert append_unique_atomic(file, {"record_id": "A", "text": "one"})
        assert not append_unique_atomic(file, {"record_id": "A", "text": "two"})
        assert file.read_text(encoding="utf-8").count("record_id") == 1
    finally:
        file.unlink(missing_ok=True)
