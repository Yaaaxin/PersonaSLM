import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "persona_dialogue_mechanism_boundary_sensitivity",
    ROOT / "tools/p1_persona_dialogue_mechanism_boundary_sensitivity.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def registration():
    return {"inclusion_predicate": copy.deepcopy(MODULE.EXPECTED_PREDICATE)}


def candidate(request_id="selected"):
    text = "My pick: Maple Entrance because it is step-free. That is the practical fit."
    digest = MODULE.m.th(text)
    row = {"request_id": request_id, "persona_id": "SYN_VAL_D",
           "case_id": "VAL_D_ALIGNED_ENTRY", "arm": "S_F_H"}
    result = {"request_id": request_id, "raw_response": text,
        "generated_token_ids": [101, 102], "raw_text_sha256": digest,
        "first_reply_sha256": digest,
        "raw_termination": {"stop": True, "stop_type": "eos", "truncated": False},
        "response_status": {"status": "AMBIGUOUS", "reasons": ["unrecognized_line_label"],
            "unit_identifiable": False,
            "first_span": {"start": 0, "end": len(text), "text": text, "sha256": digest},
            "removed_prefix": "", "excluded_tail": ""},
        "automatic_score": {"measurement_state": "BOUNDARY_CENSORED"},
        "untouched": {"latency_seconds": 1.25}}
    raw = {"request_id": request_id,
           "response": {"content": text, "tokens": [101, 102], "stop": True,
                        "stop_type": "eos", "truncated": False}}
    return row, result, raw


def test_exact_all_conditions_candidate_is_included():
    row, result, raw = candidate()
    assert MODULE.matches_inclusion(row, result, raw, registration()) is True


def test_every_nonmatching_condition_is_rejected():
    mutations = [
        lambda row, result, raw: result["automatic_score"].update(measurement_state="ASSESSED"),
        lambda row, result, raw: result["response_status"].update(status="COMPLETE"),
        lambda row, result, raw: result["response_status"].update(reasons=["other"]),
        lambda row, result, raw: row.update(persona_id="SYN_VAL_E"),
        lambda row, result, raw: result.update(raw_response=""),
        lambda row, result, raw: result.update(raw_response="my pick: Maple Entrance"),
        lambda row, result, raw: result["raw_termination"].update(stop=False),
        lambda row, result, raw: result["raw_termination"].update(stop_type="limit"),
        lambda row, result, raw: result["raw_termination"].update(truncated=True),
        lambda row, result, raw: result["response_status"]["first_span"].update(text="different"),
        lambda row, result, raw: result["response_status"]["first_span"].update(start=1),
        lambda row, result, raw: result.update(first_reply_sha256="different"),
        lambda row, result, raw: result["response_status"].update(removed_prefix="Assistant: "),
        lambda row, result, raw: result["response_status"].update(excluded_tail="tail"),
        lambda row, result, raw: raw["response"].update(content="different"),
        lambda row, result, raw: raw["response"].update(tokens=[999]),
    ]
    for mutate in mutations:
        row, result, raw = candidate()
        mutate(row, result, raw)
        assert MODULE.matches_inclusion(row, result, raw, registration()) is False


def test_sensitivity_changes_only_target_score_and_never_mutates_inputs():
    selected_row, selected_result, selected_raw = candidate("selected")
    other_row, other_result, other_raw = candidate("other")
    other_row["persona_id"] = "SYN_VAL_E"
    rows = [selected_row, other_row]
    results = {"selected": selected_result, "other": other_result}
    raw = {"selected": selected_raw, "other": other_raw}
    preserved_results, preserved_raw = copy.deepcopy(results), copy.deepcopy(raw)
    rescored = {"measurement_state": "ASSESSED_IDENTIFIABLE_UNIT",
        "selection_category": "CURRENT_A", "current_named_selection": 1,
        "current_preference_choice": 1, "history_target_selection": 0,
        "full_canonical_both": 0}
    updated, selected = MODULE.apply_sensitivity(
        rows, results, raw, registration(), scorer=lambda *_args, **_kwargs: rescored)
    assert selected == ["selected"]
    assert updated["selected"]["automatic_score"] == rescored
    assert {key: value for key, value in updated["selected"].items()
            if key != "automatic_score"} == {
               key: value for key, value in selected_result.items() if key != "automatic_score"}
    assert updated["other"] == other_result
    assert results == preserved_results and raw == preserved_raw


def test_side_by_side_preserves_registered_primary_and_rejects_drift():
    primary = {"primary_arm_summary": {"A": {"metric": 1}},
               "primary_paired_contrasts": {"A-B": {"estimate": None}}}
    sensitivity = {"primary_arm_summary": {"A": {"metric": 2}},
                   "primary_paired_contrasts": {"A-B": {"estimate": 1}}}
    preserved = copy.deepcopy(primary)
    compared = MODULE.side_by_side(primary, copy.deepcopy(primary), sensitivity)
    assert primary == preserved
    assert compared == {"registered_primary": primary,
                        "posthoc_boundary_sensitivity": sensitivity}
    with pytest.raises(RuntimeError, match="primary analysis changed"):
        MODULE.side_by_side(primary, sensitivity, sensitivity)


def test_public_safety_rejects_raw_or_token_payloads():
    MODULE.assert_public_safe({"raw_text_sha256": "hash", "new_model_generations": 0})
    for key in ("raw_response", "first_span", "generated_token_ids", "content", "prompt"):
        with pytest.raises(RuntimeError, match="restricted raw material"):
            MODULE.assert_public_safe({key: "forbidden"})


def test_authorization_binds_sources_registration_and_fixed_output(tmp_path):
    authorization = MODULE.authorization_requirements()
    authorization.update({"researcher": "Yaxin ZHENG", "authorized_utc": "TEST_ONLY"})
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps(authorization), encoding="utf-8")
    assert MODULE.validate_authorization(path, MODULE.EXPECTED_OUTPUT) == authorization
    changed = copy.deepcopy(authorization)
    changed["effective_expected_selected_set_request_ids"] = changed[
        "effective_expected_selected_set_request_ids"][:-1]
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(RuntimeError, match="authorization changed"):
        MODULE.validate_authorization(path, MODULE.EXPECTED_OUTPUT)
    path.write_text(json.dumps(authorization), encoding="utf-8")
    with pytest.raises(RuntimeError, match="output path"):
        MODULE.validate_authorization(path, tmp_path / "wrong.json")


def test_exclusive_output_and_zero_generation_surface(tmp_path, monkeypatch):
    for name in ("run", "preflight"):
        monkeypatch.setattr(MODULE.m, name,
                            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                                AssertionError("generation path called")))
    output = tmp_path / "sensitivity.json"
    value = {"integrity": {"new_model_generations": 0, "network_calls": 0}}
    MODULE.a2.write_exclusive(output, value)
    assert json.loads(output.read_text(encoding="utf-8")) == value
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        MODULE.a2.write_exclusive(output, value)
