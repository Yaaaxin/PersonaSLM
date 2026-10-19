"""Synthetic material checks; never open corpus or protected reviewer records."""
from datetime import datetime
import copy

import pytest

import real_persona_chat_continuation_material_v1 as study


def profile(index):
    speaker, partner, source_partner = f"s{index}", f"p{index}", f"q{index}"
    turns = [{"interlocutor_id": speaker if i % 2 == 0 else source_partner,
              "text": f"合成参考発話の内容{i}。"} for i in range(6)]
    local = [{"interlocutor_id": speaker if i % 2 == 0 else partner,
              "text": f"合成局所会話の内容{i}。"} for i in range(6)]
    return {"speaker": speaker,
            "target": {"dialogue_id": f"target{index}", "partner": partner,
                       "start": datetime(2020, 2, 1)},
            "context": {"history": local, "query": {"text": "合成質問ですか。"},
                        "reference": {"text": f"別の実験用正解選択肢{index}。"}, "reference_index": 7},
            "source_windows": [{"dialogue_id": f"source{index}", "partner": source_partner,
                                "start_index": 0, "end": datetime(2020, 1, 1), "turns": turns}]}


def test_reciprocal_pairs_and_both_orders_are_exact():
    cases, receipt = study.select_cases([profile(i) for i in range(8)], lambda text: 30)
    assert len(cases) == 8
    assert receipt["reciprocal_pairs"] == 4
    assert receipt["disjoint_participants_in_selected_material"] == 24
    for offset in range(0, 8, 2):
        left, right = cases[offset:offset + 2]
        assert left["candidate_texts"] == right["candidate_texts"]
        assert left["source_history"] == right["donor_source_history"]
        for order in (0, 1):
            options, correct = study.options(left, order)
            assert options[correct] == left["reference"]["text"]
            other, other_correct = study.options(right, order)
            assert options == other and correct != other_correct
    assert receipt["maximum_observed_source_token_difference"] == 0


@pytest.mark.parametrize("mutation", ["people", "dialogue", "chronology", "length", "same_candidate", "copy"])
def test_pair_exclusions_fail_closed(mutation):
    left, right = profile(0), profile(1)
    if mutation == "people":
        right["target"]["partner"] = left["source_windows"][0]["partner"]
    elif mutation == "dialogue":
        right["source_windows"][0]["dialogue_id"] = left["target"]["dialogue_id"]
    elif mutation == "chronology":
        right["source_windows"][0]["end"] = left["target"]["start"]
    elif mutation == "length":
        right["context"]["reference"]["text"] *= 3
    elif mutation == "same_candidate":
        right["context"]["reference"]["text"] = left["context"]["reference"]["text"]
    else:
        right["source_windows"][0]["turns"][0]["text"] = left["context"]["reference"]["text"]
    assert study.paired_windows(left, right, lambda text: 30, set(), {}) is None


def test_native_source_tolerance_is_fixed_and_no_padding():
    left, right = profile(0), profile(1)
    right["source_windows"][0]["turns"][0]["text"] = "固有の合成参考発話です。"
    tokenizer = lambda text: 39 if "固有" in text else 30
    before = copy.deepcopy((left, right))
    assert study.paired_windows(left, right, tokenizer, set(), {}) is None
    assert (left, right) == before
    assert study.paired_windows(left, right, lambda text: 38 if "固有" in text else 30, set(), {})


def test_no_fallback_sample_size_and_no_reuse_of_partners():
    with pytest.raises(ValueError, match="3/4"):
        study.select_cases([profile(i) for i in range(6)], lambda text: [1, 2])
    profiles = [profile(i) for i in range(8)]
    profiles[7]["target"]["partner"] = profiles[0]["source_windows"][0]["partner"]
    with pytest.raises(ValueError, match="3/4"):
        study.select_cases(profiles, lambda text: [1, 2])
    with pytest.raises(ValueError, match="exactly four"):
        study.select_cases([], lambda text: 1, pair_count=3)


def test_source_window_count_and_starts_are_bounded():
    row = profile(0)["source_windows"][0]
    record = {**row, "turns": row["turns"] * 5}
    windows = study.source_windows(record, "s0")
    assert len(windows) == 8
    assert [window["start_index"] for window in windows] == list(range(0, 16, 2))
    assert all(len(window["turns"]) == 6 for window in windows)


def test_lexical_baseline_uses_only_visible_evidence_and_ties_half():
    case = study.select_cases([profile(i) for i in range(8)], lambda text: 30)[0][0]
    case["candidate_texts"] = ["リンゴを食べました。", "電車に乗りました。"]
    case["history"] = []
    case["query"] = {"text": "リンゴを食べました。"}
    case["reference"] = {"text": "この変更は採点に影響しない"}
    assert study.lexical_baseline(case, "NONE")["accuracy"] == 1
    case["query"] = {"text": "ab"}
    assert study.lexical_baseline(case, "NONE")["accuracy"] == .5
    with pytest.raises(ValueError, match="Unknown"):
        study.lexical_baseline(case, "BAD")


def test_target_rejects_future_or_invalid_chronology_through_shared_parser():
    dialogue = {"dialogue_id": "synthetic", "interlocutors": ["s", "p"],
                "utterances": [{"interlocutor_id": "s", "timestamp": "NaT", "text": "合成"}]}
    assert study.material._dialogue_record(dialogue, "s") is None


def test_development_header_guard_precedes_json_parsing(monkeypatch):
    class ExcludedPath:
        def __truediv__(self, name):
            return self
        def glob(self, pattern):
            return [self]
        def read_bytes(self):
            raise AssertionError("Reserved body must never be read")
    monkeypatch.setattr(study, "Path", lambda path: ExcludedPath())
    monkeypatch.setattr(study.material, "_speaker_ids", lambda path: ["dev", "held"])
    monkeypatch.setattr(study.material.intake, "speaker_split", lambda ids: (
        {"dev": "DEVELOPMENT", "held": "INDEPENDENT_VALIDATION"}, "synthetic-hash"))
    monkeypatch.setattr(study.material, "_dialogue_participants", lambda path: ["dev", "held"])
    dialogues, split_hash, excluded = study.load_development_dialogues("synthetic-only")
    assert dialogues == [] and split_hash == "synthetic-hash" and excluded == 1
