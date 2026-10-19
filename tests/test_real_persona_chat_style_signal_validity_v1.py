import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import real_persona_chat_style_signal_validity_v1 as module


def test_structural_filter_does_not_parse_excluded_utterances(tmp_path, monkeypatch):
    dialogue_dir = tmp_path / "dialogues"
    dialogue_dir.mkdir()
    (dialogue_dir / "dev.json").write_text(
        '{"dialogue_id":"d","interlocutors":["a","b"],"utterances":[]}',
        encoding="utf-8")
    (dialogue_dir / "reserve.json").write_text(
        '{"dialogue_id":"r","interlocutors":["x","y"],'
        '"utterances":[THIS_IS_INTENTIONALLY_INVALID_AND_MUST_NOT_PARSE]}',
        encoding="utf-8")

    monkeypatch.setattr(module.intake, "speaker_split", lambda speakers: (
        {"a": "DEVELOPMENT", "b": "DEVELOPMENT",
         "x": "INDEPENDENT_VALIDATION_RESERVED",
         "y": "EXPLORATORY_TEST"}, "frozen"))
    manifest, _, access = module.development_manifest(dialogue_dir, "frozen")

    assert [path.name for path in manifest] == ["dev.json"]
    assert access["excluded_dialogues_not_text_parsed"] == 1


def test_structural_header_rejects_content_before_utterances_key(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(
        '{"text":"private","interlocutors":["a","b"],"utterances":[]}',
        encoding="utf-8")
    with pytest.raises(ValueError, match="content appeared"):
        module.participants_from_structural_header(path)


def row(dialogue, partner, turns, partner_turns=None):
    return {"dialogue_id": dialogue, "partner": partner, "key": (dialogue,),
            "turns": turns, "partner_turns": partner_turns or ["partner"]}


def test_exact_turn_decontamination_removes_only_cross_side_duplicates():
    selected = {"speaker": {
        "source": [row("s", "p1", [" Same  turn ", "source-only"])],
        "target": [row("t", "p2", ["same turn", "target-only"])],
        "partners": {"p1", "p2"},
    }}
    cleaned, audit = module.exact_turn_decontamination(selected)
    assert cleaned["speaker"]["source"][0]["turns"] == ["source-only"]
    assert cleaned["speaker"]["target"][0]["turns"] == ["target-only"]
    assert audit == {
        "profiles_with_any_exact_normalized_turn_overlap": 1,
        "unique_exact_normalized_turns_shared_sum": 1,
        "source_turn_occurrences_removed": 1,
        "target_turn_occurrences_removed": 1,
    }


def test_character_ngrams_are_lexical_negative_control():
    rows = [row("a", "p", ["東京です。"])]
    assert module.content_ngrams(rows) == {"東京で", "京です"}
    assert module.jaccard({"abc", "def"}, {"abc"}) == 0.5


def test_rankdata_and_spearman_handle_ties():
    assert module.rankdata([1, 1, 3]) == [1.5, 1.5, 3.0]
    assert module.spearman([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)


def test_writer_is_exclusive(tmp_path):
    path = tmp_path / "evidence.json"
    module.write_exclusive(path, {"status": "first"})
    with pytest.raises(FileExistsError):
        module.write_exclusive(path, {"status": "second"})
    assert json.loads(path.read_text(encoding="utf-8")) == {"status": "first"}
