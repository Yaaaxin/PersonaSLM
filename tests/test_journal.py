import json
import pytest

from personaslm.journal import RunJournal, atomic_json, read_events


def test_immutable_manifest_and_distinct_runs(local_tmp):
    first = RunJournal(local_tmp, {"unit_test_only": True})
    second = RunJournal(local_tmp, {"unit_test_only": True})
    assert first.directory != second.directory
    with pytest.raises(FileExistsError):
        atomic_json(first.directory / "manifest.json", {"changed": True})


def test_interrupted_run_keeps_raw_response(local_tmp):
    journal = RunJournal(local_tmp, {"unit_test_only": True})
    journal.write("raw_generation", {"content": "\nAssistant: test double\r\n"})
    (journal.directory / "events/000002.json.tmp").write_text("interrupted write", encoding="utf-8")
    events = read_events(journal.directory)
    assert len(events) == 1
    assert events[0]["data"]["content"] == "\nAssistant: test double\r\n"


def test_hash_chain_detects_tampering(local_tmp):
    journal = RunJournal(local_tmp, {"unit_test_only": True})
    journal.write("test", {"value": 1})
    journal.write("test", {"value": 2})
    path = journal.directory / "events/000001.json"
    event = json.loads(path.read_text(encoding="utf-8"))
    event["data"]["value"] = 99
    path.write_text(json.dumps(event), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity failure"):
        read_events(journal.directory)


def test_missing_event_is_detected(local_tmp):
    journal = RunJournal(local_tmp, {"unit_test_only": True})
    journal.write("test", {})
    journal.write("test", {})
    (journal.directory / "events/000001.json").unlink()
    with pytest.raises(ValueError, match="integrity failure"):
        read_events(journal.directory)


def test_manifest_tampering_is_detected(local_tmp):
    journal = RunJournal(local_tmp, {"unit_test_only": True})
    journal.write("test", {})
    path = journal.directory / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["unit_test_only"] = False
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity failure"):
        read_events(journal.directory)


def test_nonexistent_run_cannot_have_passing_integrity(local_tmp):
    with pytest.raises(FileNotFoundError):
        read_events(local_tmp / "does-not-exist")
