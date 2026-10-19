import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import real_persona_chat_style_signal_v1 as module


def row(dialogue_id, partner, key, turns):
    return {"dialogue_id": dialogue_id, "partner": partner,
            "key": (key, dialogue_id), "turns": turns}


def test_profile_selection_is_chronological_and_partner_disjoint():
    records = {"S": [
        row(1, "A", "2026-01-01", ["a"]),
        row(2, "B", "2026-01-02", ["b"]),
        row(3, "C", "2026-01-03", ["c"]),
        row(4, "D", "2026-01-04", ["d"]),
    ]}
    selected = module.select_profiles(records)["S"]
    assert [value["dialogue_id"] for value in selected["source"]] == [1, 2]
    assert [value["dialogue_id"] for value in selected["target"]] == [3, 4]
    assert selected["partners"] == {"A", "B", "C", "D"}


def test_style_vector_contains_only_frozen_aggregate_features():
    vector = module.style_vector([row(
        1, "A", "2026-01-01",
        ["こんにちは！", "そうです。", "<AA>＊＊？"] )])
    assert tuple(vector) == module.FEATURES
    assert vector["exclamation_turn_rate"] == 1 / 3
    assert vector["polite_ending_rate"] == 1 / 3
    assert all(isinstance(value, float) for value in vector.values())
    assert "こんにちは" not in json.dumps(vector, ensure_ascii=False)


def test_eligibility_prunes_until_control_rule_is_stable(monkeypatch):
    monkeypatch.setattr(module, "MIN_CONTROLS", 2)
    selected = {
        "A": {"partners": {"p1"}},
        "B": {"partners": {"p2"}},
        "C": {"partners": {"p2"}},
    }
    assert module.eligible_profiles(selected, minimum_controls=2) == {}


def test_same_style_is_closer_than_distinct_style(monkeypatch):
    monkeypatch.setattr(module, "MIN_CONTROLS", 1)
    selected = {
        "A": {"source": [row(1, "p1", "1", ["です。"] * 10)],
              "target": [row(2, "p2", "2", ["ます。"] * 10)],
              "partners": {"p1", "p2"}},
        "B": {"source": [row(3, "p3", "1", ["WOW!!!"] * 10)],
              "target": [row(4, "p4", "2", ["HEY!!!"] * 10)],
              "partners": {"p3", "p4"}},
    }
    result = module.evaluate(selected)
    assert len(result["margins"]) == 2
    assert all(value > 0 for value in result["margins"])


def test_exclusive_writer_refuses_overwrite(tmp_path):
    target = tmp_path / "receipt.json"
    module.write_exclusive(target, {"first": True})
    try:
        module.write_exclusive(target, {"second": True})
        assert False, "exclusive writer overwrote evidence"
    except FileExistsError:
        pass
