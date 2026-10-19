import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import real_persona_chat_intake as module


def test_speaker_split_is_disjoint_deterministic_and_bound():
    speakers = [f"S{index:03d}" for index in range(233)]
    first, first_hash = module.speaker_split(speakers)
    second, second_hash = module.speaker_split(reversed(speakers))
    assert first == second
    assert first_hash == second_hash
    assert len(first) == 233
    assert {name: list(first.values()).count(name)
            for name in module.SPLIT_COUNTS} == module.SPLIT_COUNTS


def test_audit_never_emits_participant_text(tmp_path, monkeypatch):
    root = tmp_path / "rpc"
    dialogues = root / "real_persona_chat" / "dialogues"
    dialogues.mkdir(parents=True)
    (root / "VERSION").write_text("test\n", encoding="utf-8")
    (root / "LICENSE").write_text("license", encoding="utf-8")
    (root / "README.md").write_text("readme", encoding="utf-8")
    people = {"AA": {"persona": ["private persona"]},
              "BB": {"persona": ["other private persona"]}}
    (root / "real_persona_chat" / "interlocutors.json").write_text(
        json.dumps(people), encoding="utf-8")
    (dialogues / "00001.json").write_text(json.dumps({
        "dialogue_id": 1, "interlocutors": ["AA", "BB"],
        "utterances": [{"utterance_id": 0, "interlocutor_id": "AA",
                        "text": "sensitive utterance", "timestamp": "NaT"}],
        "evaluations": [],
    }), encoding="utf-8")
    monkeypatch.setattr(module, "EXPECTED", {})
    monkeypatch.setattr(module, "SPLIT_COUNTS", {
        "DEVELOPMENT": 1, "EXPLORATORY_TEST": 1,
        "INDEPENDENT_VALIDATION_RESERVED": 0})
    report = module.audit(root, observed_revision="test-revision")
    rendered = json.dumps(report)
    assert report["participant_text_emitted"] is False
    assert "sensitive utterance" not in rendered
    assert "private persona" not in rendered


def test_pinned_release_hashes_are_complete():
    assert set(module.EXPECTED) == {
        "version", "revision", "license_sha256", "readme_sha256",
        "version_sha256", "interlocutors_sha256",
        "dialogue_manifest_sha256", "dialogues", "utterances", "speakers",
        "pairs"}
    assert len(module.EXPECTED["revision"]) == 40
    assert all(len(module.EXPECTED[key]) == 64 for key in (
        "license_sha256", "readme_sha256", "version_sha256",
        "interlocutors_sha256", "dialogue_manifest_sha256"))
