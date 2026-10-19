import json
from collections import Counter
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import p1_persona_dialogue_history_template_mechanism as module


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_frozen_candidate_is_exactly_six_by_five_and_unexecuted():
    design, bank = load(ROOT / module.DESIGN), load(ROOT / module.CASE_BANK)
    assert module.sha256(ROOT / module.DESIGN) == module.DESIGN_SHA
    assert module.sha256(ROOT / module.CASE_BANK) == module.CASE_BANK_SHA
    assert design["research"]["evidence_level"] == "DEVELOPMENT_MECHANISM"
    assert design["research"]["zero_tokenization_and_outputs_at_freeze"] is True
    assert len(bank["personas"]) == len(bank["cases"]) == 6
    assert Counter(case["persona_id"] for case in bank["cases"]) == Counter(
        {persona_id: 1 for persona_id in bank["personas"]})
    assert Counter(case["history_regime"] for case in bank["cases"]) == {
        "ALIGNED_HELPFUL": 2, "OUTDATED_CONFLICTING": 2, "IRRELEVANT": 2}
    for regime in ("ALIGNED_HELPFUL", "OUTDATED_CONFLICTING", "IRRELEVANT"):
        assert Counter(case["preferred_option"] for case in bank["cases"]
                       if case["history_regime"] == regime) == {"A": 1, "B": 1}
    rows = design["order"]["requests"]
    assert len(rows) == len({row["request_id"] for row in rows}) == 30
    assert [row["order"] for row in rows] == list(range(30))
    assert Counter(row["arm"] for row in rows) == {arm: 6 for arm in module.ARMS}
    arm_orders = {arm: [row["order"] for row in rows if row["arm"] == arm]
                  for arm in module.ARMS}
    assert {arm: sum(orders) for arm, orders in arm_orders.items()} == {
        arm: 87 for arm in module.ARMS}
    assert {arm: sum(orders) / len(orders) for arm, orders in arm_orders.items()} == {
        arm: 14.5 for arm in module.ARMS}
    assert design["order"]["arm_order_balance"] == {
        arm: {"orders": orders, "sum": 87, "mean": 14.5}
        for arm, orders in arm_orders.items()}
    assert tuple(design["estimands"]["automatic_binary_metrics"]) == module.METRICS
    for case in bank["cases"]:
        assert Counter(row["arm"] for row in rows if row["case_id"] == case["case_id"]) == {
            arm: 1 for arm in module.ARMS}
    assert design["resource_budget"]["requests"] == 30
    assert design["resource_budget"]["minimum_available_physical_ram_bytes"] == 3 * 1024**3
    assert design["resource_budget"]["global_baseline"]["generations_used"] == 202
    assert design["resource_budget"]["global_baseline"][
        "inference_wall_seconds_used"] == pytest.approx(1187.2563158999974)
    assert design["authorization"]["execution_authorized"] is False
    assert design["authorization"]["tokenization_authorized"] is False
    assert design["authorization"]["preflight_authorized"] is False
    assert design["authorization"]["maximum_native_tokenizer_calls"] == 30
    assert design["authorization"]["maximum_live_server_tokenizer_checks"] == 30
    assert design["authorization"]["maximum_tokenizer_operations_total"] == 60
    assert design["authorization"]["maximum_generation_attempts_if_authorized"] == 30
    assert design["authorization"]["retries"] == 0
    assert not (ROOT / module.AUTHORIZATION).exists()
    assert not (ROOT / module.FROZEN).exists()
    assert not (ROOT / module.PREFLIGHT).exists()
    assert not (ROOT / module.ROOT / "claim.json").exists()


def test_full_structural_validation_includes_material_and_template_disjointness():
    checks = module.validate_design(require_unstarted=True)
    assert checks == {"personas": 6, "cases": 6, "arms": 5, "requests": 30,
                      "boundary_parser_probes": 24,
                      "material_disjointness_sources": 6}


def test_exact_prompt_transforms_hold_only_registered_differences():
    design, bank = load(ROOT / module.DESIGN), load(ROOT / module.CASE_BANK)
    for case in bank["cases"]:
        built = {arm: module.construction(design, bank, case, arm)[3]
                 for arm in module.ARMS}
        assert len(built["SF_NO_H"]) == 2
        assert all(len(built[arm]) == 4 for arm in module.ARMS[1:])
        assert all(messages[0] == built["SF_NO_H"][0] for messages in built.values())
        raw, surface = built["SFH_RAW_NATIVE"], built["SFH_SURFACE_NEUTRAL"]
        assert [message["role"] for message in raw] == [
            "system", "user", "assistant", "user"]
        assert [message["role"] for message in surface] == [
            "system", "user", "assistant", "user"]
        assert raw[0] == surface[0]
        assert raw[1] == surface[1]
        assert raw[3] == surface[3]
        raw_first, raw_second = raw[2]["content"].split(". ", 1)
        surface_first, surface_second = surface[2]["content"].split(". ", 1)
        assert raw_first + "." == f"I recommend the {case['history_selected_target']}."
        assert surface_first + "." == f"{case['history_selected_target']} was my choice."
        assert raw_second == surface_second
        current = built["SFH_CURRENT_RESTATEMENT"]
        reminder = built["SFH_FORMAT_REMINDER"]
        assert current[:3] == raw[:3]
        assert reminder[:3] == raw[:3]
        persona = bank["personas"][case["persona_id"]]
        assert persona["F_block"] in current[-1]["content"]
        assert case["fixed_current_notes"] in current[-1]["content"]
        reminder_text = design["prompt_policy"]["format_only_reminder"]
        assert reminder[-1]["content"].startswith(reminder_text + "\n\n")
        assert all(value not in reminder_text for value in (
            case["options"]["A"]["canonical"], case["options"]["B"]["canonical"],
            *case["history_target_strings"], persona["F_block"]))


def _row(case):
    return {**case, "options": case["options"],
            "history_target_strings": case["history_target_strings"],
            "history_selected_target": case["history_selected_target"]}


def test_finite_selection_grammar_is_separate_from_strict_contract():
    bank = load(ROOT / module.CASE_BANK)
    case = bank["cases"][0]
    persona = bank["personas"][case["persona_id"]]
    preferred = case["options"][case["preferred_option"]]
    prefix = next(item["value"] for item in persona["operational_style_checks"]
                  if item["check_id"] == "second_sentence_prefix")
    suffix = next(item["value"] for item in persona["operational_style_checks"]
                  if item["check_id"] == "second_sentence_suffix")
    response = (f"I recommend {preferred['canonical']}. {prefix} "
                f"{preferred['reason_cues'][0]}, {suffix}")
    score = module.automatic_score(_row(case), persona, response)
    assert score["selection_category"] == "CURRENT_PREFERRED"
    assert score["current_target_selection"] == 1
    assert score["historical_target_intrusion"] == 0
    assert score["history_template_copy"] == 0

    censored = module.automatic_score(_row(case), persona, response, assessable=False)
    assert censored["selection_category"] == "BOUNDARY_CENSORED"
    assert censored["current_target_selection"] is None
    assert censored["historical_target_intrusion"] is None
    assert censored["history_template_copy"] is None
    assert censored["strict_format_adherence"] is None
    assert score["strict_format_adherence"] == 1
    assert score["current_preference_task_success"] == 1
    assert score["surface_style_uptake"] == 1

    optional_the = (f"I recommend the {preferred['canonical']}. {prefix} "
                    f"{preferred['reason_cues'][0]}, {suffix}")
    score = module.automatic_score(_row(case), persona, optional_the)
    assert score["selection_category"] == "CURRENT_PREFERRED"
    assert score["current_target_selection"] == 1
    assert score["history_template_copy"] == 1
    assert score["strict_format_adherence"] == 0
    assert score["current_preference_task_success"] == 0

    labeled = (f"I recommend Option {case['preferred_option']} — {preferred['canonical']}. "
               f"{prefix} {preferred['reason_cues'][0]}, {suffix}")
    score = module.automatic_score(_row(case), persona, labeled)
    assert score["selection_category"] == "CURRENT_PREFERRED"
    assert score["current_target_selection"] == 1
    assert score["history_template_copy"] == 0
    assert score["strict_format_adherence"] == 0

    wrong_label = "B" if case["preferred_option"] == "A" else "A"
    mislabeled = (f"I recommend Option {wrong_label} — {preferred['canonical']}. "
                  f"{prefix} detail, {suffix}")
    score = module.automatic_score(_row(case), persona, mislabeled)
    assert score["selection_category"] == "NONE"
    assert score["current_target_selection"] == 0

    other_option = "B" if case["preferred_option"] == "A" else "A"
    nonpreferred = case["options"][other_option]["canonical"]
    score = module.automatic_score(
        _row(case), persona, f"I recommend the {nonpreferred}. {prefix} detail, {suffix}")
    assert score["selection_category"] == "CURRENT_NONPREFERRED"
    assert score["current_target_selection"] == 1
    assert score["current_preference_task_success"] == 0

    history = (f"I recommend {case['history_selected_target']}. {prefix} "
               f"the archived detail, {suffix}")
    score = module.automatic_score(_row(case), persona, history)
    assert score["selection_category"] == "HISTORY_TARGET"
    assert score["current_target_selection"] == 0
    assert score["historical_target_intrusion"] == 1
    assert score["history_template_copy"] == 0
    assert score["strict_format_adherence"] == 0
    assert score["current_preference_task_success"] == 0

    other_history = case["history_target_strings"][1]
    score = module.automatic_score(
        _row(case), persona, f"I recommend the {other_history}. {prefix} detail, {suffix}")
    assert score["selection_category"] == "HISTORY_TARGET"
    assert score["historical_target_intrusion"] == 1
    assert score["history_template_copy"] == 1

    multiple = (f"I recommend {preferred['canonical']} and {case['history_selected_target']}. "
                f"{prefix} detail, {suffix}")
    score = module.automatic_score(_row(case), persona, multiple)
    assert score["selection_category"] == "MULTIPLE"
    assert score["current_target_selection"] == 0
    assert score["historical_target_intrusion"] == 1

    second_sentence_intrusion = (f"I recommend {preferred['canonical']}. {prefix} "
                                 f"{case['history_selected_target']} remains archived, {suffix}")
    score = module.automatic_score(_row(case), persona, second_sentence_intrusion)
    assert score["selection_category"] == "CURRENT_PREFERRED"
    assert score["mentioned_history_targets"] == []
    assert score["full_reply_history_targets"] == [case["history_selected_target"]]
    assert score["current_target_selection"] == 1
    assert score["historical_target_intrusion"] == 1
    assert score["strict_format_adherence"] == 0

    unregistered = f"{preferred['canonical']} is my choice. {prefix} detail, {suffix}"
    score = module.automatic_score(_row(case), persona, unregistered)
    assert score["selection_category"] == "NONE"
    assert score["mentioned_current_options"] == [case["preferred_option"]]
    assert score["current_target_selection"] == 0
    assert score["historical_target_intrusion"] == 0

    score = module.automatic_score(
        _row(case), persona, f"I would choose something else. {prefix} detail, {suffix}")
    assert score["selection_category"] == "NONE"
    assert score["current_target_selection"] == 0
    assert score["historical_target_intrusion"] == 0
    assert score["history_template_copy"] == 0


def test_registered_paired_bounds_and_lopo_keep_missing_outcomes():
    bank = load(ROOT / module.CASE_BANK)
    persona_by_case = {case["case_id"]: case["persona_id"] for case in bank["cases"]}
    by_case = {}
    for index, case in enumerate(bank["cases"]):
        by_case[case["case_id"]] = {
            "SFH_RAW_NATIVE": {"strict_format_adherence": None if index == 0 else 0},
            "SFH_FORMAT_REMINDER": {"strict_format_adherence": 1},
        }
    summary = module.base.weighted_contrast(
        by_case, sorted(by_case), {"SFH_FORMAT_REMINDER": 1.0,
                                   "SFH_RAW_NATIVE": -1.0},
        "strict_format_adherence", persona_by_case)
    assert summary["eligible_cases"] == 6
    assert summary["complete_cases"] == 5
    assert summary["unresolved_cases"] == 1
    assert summary["complete_case_estimate"] == 1.0
    assert summary["logical_lower"] == pytest.approx(5 / 6)
    assert summary["logical_upper"] == 1.0
    assert len(summary["leave_one_persona_out"]) == 6


def test_authorization_requirements_are_read_only_and_exactly_bounded():
    before = {path: path.exists() for path in (
        ROOT / module.AUTHORIZATION, ROOT / module.FROZEN, ROOT / module.PREFLIGHT,
        ROOT / module.ROOT / "claim.json")}
    required = module.authorization_requirements()
    assert required["maximum_native_tokenizer_calls"] == 30
    assert required["maximum_live_server_tokenizer_checks"] == 30
    assert required["maximum_tokenizer_operations_total"] == 60
    assert required["maximum_generation_attempts"] == 30
    assert required["retries"] == required["hidden_warmups"] == 0
    assert required["minimum_available_physical_ram_bytes"] == 3 * 1024**3
    assert required["design"]["sha256"] == module.DESIGN_SHA
    assert required["case_bank"]["sha256"] == module.CASE_BANK_SHA
    assert required["validated_design"]["personas"] == 6
    after = {path: path.exists() for path in before}
    assert after == before


def test_failed_preflight_receipt_records_zero_execution(monkeypatch):
    def fail():
        raise ValueError("Less than 3 GiB available RAM")

    monkeypatch.setattr(module, "preflight", fail)
    monkeypatch.setattr(module.s, "memory_observation",
                        lambda _pid: {"system": {"available_physical": 123}})
    monkeypatch.setattr(module.shutil, "disk_usage",
                        lambda _path: type("Disk", (), {"free": 456})())
    receipt = module.preflight_receipt()
    assert receipt["status"] == "FAIL"
    assert receipt["error"]["message"] == "Less than 3 GiB available RAM"
    assert receipt["memory_observation"]["system"]["available_physical"] == 123
    assert receipt["free_output_disk_bytes"] == 456
    assert receipt["model_server_launches"] == 0
    assert receipt["completion_calls"] == 0
    assert receipt["new_model_generations"] == 0


def test_formal_analysis_rejects_complete_data_with_failed_postflight(tmp_path):
    summary = {"status": "COMPLETE_DATA_POSTFLIGHT_FAILED", "results": 30}
    (tmp_path / "summary.json").write_text(
        json.dumps(summary, sort_keys=True), encoding="utf-8")
    events = [{"kind": "run_finished", "data": summary}]
    assert module._terminal_summary(tmp_path, events) == summary
    with pytest.raises(ValueError, match="terminal run status PASS"):
        module._terminal_summary(tmp_path, events, require_pass=True)
