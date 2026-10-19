import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "persona_dialogue_independent_replication",
    ROOT / "tools/p1_persona_dialogue_independent_replication.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def inputs():
    design = json.loads((ROOT / MODULE.DESIGN).read_text(encoding="utf-8"))
    amendment = json.loads((ROOT / MODULE.AMENDMENT).read_text(encoding="utf-8"))
    bank = json.loads((ROOT / MODULE.CASE_BANK).read_text(encoding="utf-8"))
    return design, amendment, bank


def score_row(case, condition="C7"):
    return {"case_id": case["case_id"], "persona_id": case["persona_id"],
        "condition": condition, "history_regime": case["history_regime"],
        "preferred_option": case["preferred_option"],
        "history_favored_option": case["history_favored_option"],
        "options": case["options"], "history_target_strings": case["history_target_strings"],
        "history_selected_target": case["history_selected_target"]}


def test_v2_v3_v4_bindings_effective_order_and_budget():
    design, amendment, bank = inputs()
    checks = MODULE.validate_design(design, bank)
    assert checks == {"personas": 4, "cases": 12, "conditions": 8, "requests": 96,
        "boundary_parser_probes": 192,
        "history_regimes": {"ALIGNED_HELPFUL": 4, "OUTDATED_CONFLICTING": 4,
                            "IRRELEVANT": 4}}
    assert MODULE.sha256(ROOT / MODULE.DESIGN) == MODULE.DESIGN_SHA
    assert MODULE.sha256(ROOT / MODULE.AMENDMENT) == MODULE.AMENDMENT_SHA
    assert MODULE.sha256(ROOT / MODULE.WORDING) == MODULE.WORDING_SHA
    assert MODULE.sha256(ROOT / MODULE.ANALYSIS_AMENDMENT) == MODULE.ANALYSIS_AMENDMENT_SHA
    assert MODULE.sha256(ROOT / MODULE.CASE_BANK) == MODULE.CASE_BANK_SHA
    assert amendment["resource_budget"]["actual_completion_inference_seconds_ceiling"] == 5760
    assert amendment["resource_budget"]["batch_wall_seconds_ceiling"] == 8640
    assert len(amendment["order"]["requests"]) == 96
    assert {row["condition"] for row in amendment["order"]["requests"]} == {
        f"C{i}" for i in range(8)}
    assert all(item["authorized_attempts"] == 0 for item in
               amendment["effective_design"]["deactivated_conditions"].values())


def test_v5_freezes_complete_seven_effect_four_metric_matrix_and_dependencies():
    design, _, _ = inputs()
    completion = json.loads((ROOT / MODULE.ANALYSIS_AMENDMENT).read_text(encoding="utf-8"))
    assert completion["factorial_effect_matrix"]["effects"] == [
        "S", "F", "H", "SxF", "SxH", "FxH", "SxFxH"]
    assert tuple(completion["factorial_effect_matrix"]["narrow_automatic_metrics"]) == \
        MODULE.PRIMARY_METRICS
    scales = {"S": 0.25, "F": 0.25, "H": 0.25,
              "SxF": 0.5, "SxH": 0.5, "FxH": 0.5, "SxFxH": 1.0}
    for effect, weights in completion["factorial_weights"].items():
        factors = effect.split("x")
        expected = {}
        for condition in (f"C{i}" for i in range(8)):
            sign = 1
            for factor in factors:
                sign *= 1 if design["factors"]["conditions"][condition][factor] else -1
            expected[condition] = scales[effect] * sign
        assert weights == expected
    hashes = MODULE.source_hashes()
    for path in (MODULE.STRUCTURAL_TEST_SOURCE, MODULE.ANALYSIS_DEPENDENCY,
                 *MODULE.PRIOR_BANKS, MODULE.ANALYSIS_AMENDMENT):
        assert path.as_posix() in hashes
        assert hashes[path.as_posix()] == MODULE.sha256(ROOT / path)


def test_prompt_materialization_isolates_only_c0_to_c7():
    design, amendment, bank = inputs()
    for case in bank["cases"]:
        persona = bank["personas"][case["persona_id"]]
        built = {condition: MODULE.construction(design, bank, case, condition)
                 for condition in amendment["effective_design"]["effective_conditions"]}
        for condition, (factors, messages) in built.items():
            assert messages[-1] == {"role": "user", "content": case["fixed_current_user"]}
            assert case["fixed_current_notes"] in messages[0]["content"]
            assert (persona["S_block"] in messages[0]["content"]) == bool(factors["S"])
            assert (persona["F_block"] in messages[0]["content"]) == bool(factors["F"])
            assert persona["neutral_style_block"] not in messages[0]["content"]
            assert (messages[1:-1] == case["history_messages"]) == bool(factors["H"])
            assert factors["control"] is None
        for control in ("N_STYLE", "N_HISTORY"):
            with pytest.raises(ValueError, match="Deactivated controls"):
                MODULE.construction(design, bank, case, control)


def test_real_boundary_classifier_and_exact_parser_cross_all_frozen_targets():
    _, _, bank = inputs()
    affixes = []
    for persona in bank["personas"].values():
        affixes.append((
            next(check["value"] for check in persona["operational_style_checks"]
                 if check["matcher"] == "CASEFOLD_EXACT_PREFIX"),
            next(check["value"] for check in persona["operational_style_checks"]
                 if check["matcher"] == "CASEFOLD_EXACT_SUFFIX")))
    calls = 0
    termination = {"stop_type": "eos", "stop": True, "truncated": False}
    for prefix, suffix in affixes:
        for case in bank["cases"]:
            row = score_row(case)
            for option in ("A", "B"):
                target = case["options"][option]["canonical"]
                text = f"I recommend {target}. {prefix} current evidence {suffix}"
                boundary = MODULE.b.classify_response(text, termination, declared_stops=())
                assert boundary["unit_identifiable"] is True
                assert "unrecognized_line_label" not in boundary["reasons"]
                assert MODULE.leading_selection(row, text)["category"] == f"CURRENT_{option}"
                calls += 1
            for target in case["history_target_strings"]:
                text = f"I recommend {target}. {prefix} archived evidence {suffix}"
                boundary = MODULE.b.classify_response(text, termination, declared_stops=())
                assert boundary["unit_identifiable"] is True
                assert "unrecognized_line_label" not in boundary["reasons"]
                assert MODULE.leading_selection(row, text)["category"] == "HISTORY_TARGET"
                calls += 1
    assert calls == 4 * (24 + 24) == 192


def test_exact_scoring_keeps_selection_style_reason_and_missingness_distinct():
    _, _, bank = inputs()
    case = next(case for case in bank["cases"]
                if case["history_regime"] == "OUTDATED_CONFLICTING")
    persona = bank["personas"][case["persona_id"]]
    row = score_row(case)
    preferred = case["preferred_option"]
    target = case["options"][preferred]["canonical"]
    cue = case["options"][preferred]["reason_cues"][0]
    prefix = next(check["value"] for check in persona["operational_style_checks"]
                  if check["matcher"] == "CASEFOLD_EXACT_PREFIX")
    suffix = next(check["value"] for check in persona["operational_style_checks"]
                  if check["matcher"] == "CASEFOLD_EXACT_SUFFIX")
    text = f"I recommend {target}. {prefix} {cue} {suffix}"
    score = MODULE.automatic_score(row, persona, text)
    assert score["selection_category"] == f"CURRENT_{preferred}"
    assert score["current_preference_choice"] == 1
    assert score["exact_current_note_support"] == "SUPPORTED"
    assert score["outdated_value_adoption"] == 0
    assert score["surface_style_uptake"] == 1
    unresolved = MODULE.automatic_score(row, persona, "The notes are mixed. I cannot decide.")
    assert unresolved["selection_category"] == "UNRESOLVED_NO_EXACT_TARGET"
    assert unresolved["current_named_selection"] is None
    assert unresolved["current_preference_choice"] is None
    censored = MODULE.automatic_score(row, persona, text, assessable=False)
    assert censored["measurement_state"] == "BOUNDARY_CENSORED"
    assert censored["current_preference_choice"] is None
    assert censored["surface_style_uptake"] is None
    other = "B" if preferred == "A" else "A"
    mixed = MODULE.automatic_score(
        row, persona, f"I recommend {target}. {prefix} {cue} and "
        f"{case['options'][other]['reason_cues'][0]} {suffix}")
    assert mixed["exact_current_note_support"] == "UNRESOLVED"


def test_first_sentence_contract_rejects_repairs_and_preserves_both_as_secondary():
    _, _, bank = inputs()
    case = bank["cases"][0]
    row = score_row(case, "C0")
    a, z = case["options"]["A"]["canonical"], case["options"]["B"]["canonical"]
    assert MODULE.leading_selection(row, f"I recommend {a}. Then {z}.")["category"] == "CURRENT_A"
    assert MODULE.leading_selection(row, f"Certainly, I recommend {a}.")["category"] == \
        "UNRESOLVED_NO_EXACT_TARGET"
    assert MODULE.leading_selection(row, f"I recommend {a} or {z}.")["category"] == \
        "UNRESOLVED_NO_EXACT_TARGET"
    score = MODULE.automatic_score(row, bank["personas"][case["persona_id"]],
                                   f"I recommend {a}. {z} is also named.")
    assert score["selection_category"] == "CURRENT_A"
    assert score["full_canonical_both"] == 1


def test_missing_bounds_and_weighted_case_contrasts_do_not_impute_zero():
    summary = MODULE.binary_summary([{"x": 1}, {"x": 0}, {"x": None}], "x")
    assert summary["mean_resolved"] == 0.5
    assert summary["logical_lower"] == pytest.approx(1 / 3)
    assert summary["logical_upper"] == pytest.approx(2 / 3)
    weights = {"C0": -1.0, "C1": 1.0}
    by_case = {"A": {"C0": {"x": 0}, "C1": {"x": 1}},
               "B": {"C0": {"x": None}, "C1": {"x": 1}}}
    contrast = MODULE.weighted_contrast(
        by_case, ["A", "B"], weights, "x", {"A": "P1", "B": "P2"})
    assert contrast["complete_cases"] == 1
    assert contrast["complete_case_estimate"] == 1
    assert contrast["logical_lower"] == pytest.approx(0.5)
    assert contrast["logical_upper"] == 1
    assert contrast["case_contributions"][1]["contribution"] is None
    assert contrast["unresolved_cases"] == 1
    assert contrast["leave_one_persona_out_point_estimate_range"] == [1.0, 1.0]
    completion = json.loads((ROOT / MODULE.ANALYSIS_AMENDMENT).read_text(encoding="utf-8"))
    full_case = {condition: {metric: int(index % 2 == 1)
                             for metric in MODULE.PRIMARY_METRICS}
                 for index, condition in enumerate(f"C{i}" for i in range(8))}
    matrix = MODULE.build_effect_matrix(
        {"CASE": full_case}, ["CASE"], completion["factorial_weights"], {"CASE": "P"})
    assert set(matrix) == {"S", "F", "H", "SxF", "SxH", "FxH", "SxFxH"}
    assert all(set(metrics) == set(MODULE.PRIMARY_METRICS) for metrics in matrix.values())
    assert all(summary["eligible_cases"] == 1
               for metrics in matrix.values() for summary in metrics.values())


def test_authorization_is_exactly_bound_and_payload_has_no_retry_escape(tmp_path):
    required = MODULE.authorization_requirements()
    assert required["analysis_completion_amendment"]["sha256"] == \
        MODULE.ANALYSIS_AMENDMENT_SHA
    authorization = {**required, "researcher": "Yaxin ZHENG"}
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps(authorization), encoding="utf-8")
    assert MODULE.validate_authorization(path)["maximum_generation_attempts"] == 96
    authorization["maximum_generation_attempts"] = 97
    path.write_text(json.dumps(authorization), encoding="utf-8")
    with pytest.raises(ValueError, match="authorization changed"):
        MODULE.validate_authorization(path)
    request = MODULE.payload({"input_token_ids": [1, 2], "max_new_tokens": 96,
                              "temperature": 0.0, "top_p": 1.0, "seed": 42})
    assert request == {"prompt": [1, 2], "n_predict": 96, "temperature": 0.0,
                       "top_p": 1.0, "seed": 42, "cache_prompt": False, "stop": [],
                       "ignore_eos": False, "return_tokens": True, "stream": False}


def test_failed_preflight_is_serializable_exclusive_zero_generation_evidence(
        tmp_path, monkeypatch):
    def fail():
        raise ValueError("Less than 3 GiB available RAM")

    monkeypatch.setattr(MODULE, "preflight", fail)
    monkeypatch.setattr(MODULE.s, "memory_observation",
                        lambda _pid: {"system": {"available_physical": 123}})
    monkeypatch.setattr(MODULE.shutil, "disk_usage",
                        lambda _path: type("Disk", (), {"free": 456})())
    receipt = MODULE.preflight_receipt()
    assert receipt["status"] == "FAIL"
    assert receipt["error"] == {"type": "ValueError",
                                 "message": "Less than 3 GiB available RAM"}
    assert receipt["memory_observation"]["system"]["available_physical"] == 123
    assert receipt["free_output_disk_bytes"] == 456
    assert receipt["model_server_launches"] == receipt["completion_calls"] == \
        receipt["new_model_generations"] == 0
    output = tmp_path / "preflight_fail.json"
    MODULE.write_exclusive(output, receipt)
    assert json.loads(output.read_text(encoding="utf-8")) == receipt
    with pytest.raises(FileExistsError):
        MODULE.write_exclusive(output, receipt)
