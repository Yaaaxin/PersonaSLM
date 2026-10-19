"""Synthetic-only checks for the prospective four-arm specificity study."""
import base64
import copy
import json

import pytest

import real_persona_chat_style_specificity_v1 as study


def profile(index):
    style = {name: index / 10 for name in study.MARKERS}
    style.update(mean_turn_length=1 + index, sd_turn_length=0.2)
    return {
        "speaker": f"speaker{index}", "style": style,
        "target": {"partner": f"target_partner{index}", "dialogue_id": f"target{index}"},
        "sources": [{"partner": f"source_partner{index}_{j}", "dialogue_id": f"source{index}_{j}"}
                    for j in range(2)],
    }


def case(speaker=0, context=0):
    own, donor = profile(speaker), profile(speaker + 10)
    return {
        "case_id": f"SP{speaker:02d}T{context}", "speaker_index": speaker,
        "context_index": context, "speaker_id": own["speaker"],
        "style": own["style"], "donor_style": donor["style"],
        "reference_turns": ["ああああ", "いいいい"],
        "donor_reference_turns": ["abcd", "efgh"],
        "history": [{"interlocutor_id": own["speaker"], "text": "以前の会話です。"}],
        "query": {"text": "今日はどうでしょうか。"},
        "reference": {"text": "WITHHELD_TARGET_NOT_FOR_PROMPT"},
    }


def test_primary_coordinates_exclude_lengths_and_direct_instructions():
    assert set(study.FEATURES).isdisjoint(study.MARKERS)
    assert not any("length" in key for key in study.FEATURES)
    own = case()
    assert study.margin("ああ", own) == pytest.approx(2 / 7)
    assert study.margin("ab", own) == pytest.approx(-2 / 7)
    assert study.vector(["Ａ Ｂ\n"]) == study.vector(["ab"])


def test_three_style_arms_share_focal_length_and_only_mismatch_swaps_markers():
    own = case()
    rendered = {arm: study.messages(own, arm)[1]["content"] for arm in study.ARMS}
    length_sections = {arm: text.split("[長さ]\n")[1].split("\n\n[話し方]")[0]
                       for arm, text in rendered.items()}
    assert length_sections["CORRECT"] == length_sections["MISMATCH"] == length_sections["LENGTH"]
    assert "050.0" in length_sections["CORRECT"]
    assert "550.0" not in length_sections["MISMATCH"]
    assert length_sections["NONE"] != length_sections["LENGTH"]
    assert "約000.0%" in rendered["CORRECT"]
    assert "約100.0%" in rendered["MISMATCH"]
    assert "約000.0%" not in rendered["LENGTH"]
    assert len({text.split("[過去の会話]\n")[1] for text in rendered.values()}) == 1
    assert all(own["reference"]["text"] not in text for text in rendered.values())
    changed = copy.deepcopy(own)
    changed["reference_turns"] = ["SOURCE2_NEVER_PROMPTED"]
    changed["donor_reference_turns"] = ["DONOR_SOURCE2_NEVER_PROMPTED"]
    assert study.messages(changed, "CORRECT") == study.messages(own, "CORRECT")


def test_donors_are_deterministic_one_to_one_nonself_length_matched():
    profiles = [profile(i) for i in range(4)]
    assignment, cost = study.donor_assignment(profiles)
    assert assignment == (1, 0, 3, 2)
    assert len(set(assignment)) == 4
    assert all(i != donor for i, donor in enumerate(assignment))
    assert cost == 4


@pytest.mark.parametrize("collision", ["participant", "dialogue", "displayed_markers"])
def test_donor_constraints_fail_closed(collision):
    profiles = [profile(0), profile(1)]
    if collision == "participant":
        profiles[1]["target"]["partner"] = profiles[0]["speaker"]
    elif collision == "dialogue":
        profiles[1]["sources"][0]["dialogue_id"] = profiles[0]["sources"][1]["dialogue_id"]
    else:
        for name in study.MARKERS:
            profiles[1]["style"][name] = profiles[0]["style"][name] + 0.000001
    with pytest.raises(ValueError, match="donor derangement"):
        study.donor_assignment(profiles)


def test_contexts_do_not_reuse_the_first_reference_as_second_history(monkeypatch):
    monkeypatch.setattr(study.material, "_no_answer_leak", lambda *args: True)
    turns = [{"interlocutor_id": "s" if i % 2 else "p", "text": f"これは対話用の合成文です{i}。"}
             for i in range(16)]
    pairs = study.context_pairs({"turns": turns}, "s")
    assert [p["reference_index"] for p in pairs] == [7, 15]
    assert pairs[0]["reference"] not in pairs[1]["history"]
    assert pairs[0]["reference"] != pairs[1]["query"]
    turns[0]["text"] = "<masked>"
    assert study.context_pairs({"turns": turns}, "s") == []


@pytest.mark.parametrize("stop", ["eos", "eog"])
def test_native_boundary_is_not_semantic_completion(stop):
    boundary = study.native_boundary({"stop_type": stop})
    assert boundary["observed_native_boundary"] is True
    assert boundary["semantic_completeness"] == "NOT_HUMAN_ASSESSED"
    contradictory = study.native_boundary({"stop_type": stop, "stopped_limit": True})
    assert contradictory["contradictory_stop_flags"] is True
    assert contradictory["observed_native_boundary"] is False
    word_conflict = study.native_boundary({"stop_type": stop, "stopped_word": True})
    assert word_conflict["contradictory_stop_flags"] is True
    assert word_conflict["observed_native_boundary"] is False


def test_native_string_false_is_not_boolean_eos_evidence():
    with pytest.raises(ValueError, match="Native stop flags"):
        study.native_boundary({"stop_type": "unknown", "stopped_eos": "false"})


def synthetic_analysis(monkeypatch, tmp_path, *, empty_first_correct=False,
                       limit_first_correct=False, tamper_order=False):
    cases = [case(speaker, context) for speaker in range(8) for context in range(2)]
    requests = []
    events = []
    special_applied = False
    for item in cases:
        offset = (item["speaker_index"] + item["context_index"]) % 4
        for position in range(4):
            arm = study.ARMS[(position + offset) % 4]
            request = {"request_id": f"RPCSPEC{len(requests):03d}", "case_id": item["case_id"],
                       "arm": arm, "input_token_ids": [1, 2], "input_tokens": 2}
            requests.append(request)
            text, stop = ("abcd" if arm == "MISMATCH" else "ああああ"), "eos"
            if arm == "CORRECT" and not special_applied:
                if empty_first_correct:
                    text = ""
                if limit_first_correct:
                    stop = "limit"
                special_applied = True
            response = {"content": text, "tokens_predicted": len(text), "stop_type": stop}
            events.extend([
                {"kind": "specificity_started", "data": request},
                {"kind": "http_request", "data": {"route": "/completion", "payload": study.old.payload(request)}},
                {"kind": "http_response", "data": {"route": "/completion", "status": 200,
                    "body_base64": base64.b64encode(json.dumps(response).encode()).decode()}},
                {"kind": "specificity_raw", "data": {"request_id": request["request_id"],
                    "response": response, "latency_seconds": 1.0}},
            ])
    if tamper_order:
        events[0] = {"kind": "specificity_started", "data": requests[1]}
    events.append({"kind": "run_finished", "event_hash": "0" * 64, "data": {}})
    run_root = tmp_path / "synthetic_runs"
    (run_root / "one").mkdir(parents=True)
    monkeypatch.setattr(study, "RUNS", run_root)
    monkeypatch.setattr(study, "validate", lambda: {"cases": cases, "requests": requests})
    monkeypatch.setattr(study.old.b, "read_events", lambda path: events)
    monkeypatch.setattr(study.old.b, "validate_completion", lambda *args: {})
    monkeypatch.setattr(study, "load", lambda path: {"claim_boundary": "synthetic test only"})
    monkeypatch.setattr(study, "sha", lambda path: "0" * 64)
    return study.analyze(write_files=False)


def test_all_capped_primary_includes_limit_and_eos_sensitivity_discloses_loss(monkeypatch, tmp_path):
    result = synthetic_analysis(monkeypatch, tmp_path, limit_first_correct=True)
    primary = result["contrasts"]["margin"]["CORRECT-MISMATCH"]
    assert primary["n"] == 8
    assert primary["paired_contexts"] == 16
    assert primary["mean"] == pytest.approx(4 / 7)
    assert result["native_stop_counts"] == {"eos": 63, "limit": 1}
    assert result["contrasts"]["eos_margin"]["CORRECT-MISMATCH"]["n"] == 7
    assert result["conditions"]["CORRECT"]["margin"]["n"] == 16


def test_empty_margin_remains_missing_with_allocation_bounds(monkeypatch, tmp_path):
    result = synthetic_analysis(monkeypatch, tmp_path, empty_first_correct=True)
    effect = result["contrasts"]["margin"]["CORRECT-MISMATCH"]
    assert effect["n"] == 7
    assert effect["paired_contexts"] == 15
    assert effect["missing_contexts"] == 1
    assert effect["mean"] == pytest.approx(4 / 7)
    assert effect["all_16_context_logical_bounds"] == pytest.approx([(15 * 4 / 7 - 2) / 16, (15 * 4 / 7 + 2) / 16])
    assert result["conditions"]["CORRECT"]["margin"]["n"] == 15
    assert result["conditions"]["CORRECT"]["output_chars"]["n"] == 16
    assert result["conditions"]["MISMATCH"]["prefix_margin"]["n"] == 15


def test_reordered_generation_journal_is_rejected(monkeypatch, tmp_path):
    with pytest.raises(ValueError, match="Repeated/reordered request"):
        synthetic_analysis(monkeypatch, tmp_path, tamper_order=True)


def test_latin_positions_balanced_without_human_blinding_material():
    counts = {(arm, position): 0 for arm in study.ARMS for position in range(4)}
    for speaker in range(8):
        for context in range(2):
            for position in range(4):
                counts[study.ARMS[(position + speaker + context) % 4], position] += 1
    assert set(counts.values()) == {4}


def test_empty_and_one_speaker_summaries_do_not_invent_uncertainty():
    assert study.summary([]) == {"n": 0, "mean": None, "range": None,
                                 "leave_one_speaker_out_mean_range": None}
    assert study.summary([0.25])["leave_one_speaker_out_mean_range"] is None
