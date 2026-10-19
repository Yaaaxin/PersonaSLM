import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "persona_dialogue_mechanism", ROOT / "tools/p1_persona_dialogue_mechanism.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def inputs():
    design = json.loads((ROOT / MODULE.DESIGN).read_text(encoding="utf-8"))
    amendment = json.loads((ROOT / MODULE.AMENDMENT).read_text(encoding="utf-8"))
    bank = json.loads((ROOT / MODULE.case_bank_path(design)).read_text(encoding="utf-8"))
    return design, amendment, bank


def scorer_row(case_id, arm="F_H_RAW"):
    design, _, bank = inputs()
    mechanism = next(case for case in design["cases"] if case["case_id"] == case_id)
    source = next(case for case in bank["cases"] if case["case_id"] == case_id)
    factors = {key: design["arms"][arm][key] for key in ("S", "F", "H")}
    return {"case_id": case_id, "persona_id": mechanism["source_persona_id"],
        "arm": arm, "factors": factors, "preferred_option": source["preferred_option"],
        "options": source["options"], "history_target_strings": mechanism["history_target_strings"],
        "history_selected_target": mechanism["history_selected_target"]}


def test_v1_v2_design_bindings_order_and_budget():
    design, amendment, bank = inputs()
    checks = MODULE.validate_design(design, amendment, bank)
    assert checks["requests"] == 42
    assert checks["cases"] == 6
    assert checks["arms"] == 7
    assert MODULE.sha256(ROOT / MODULE.DESIGN) == MODULE.DESIGN_SHA
    assert MODULE.sha256(ROOT / MODULE.AMENDMENT) == MODULE.AMENDMENT_SHA
    assert MODULE.sha256(ROOT / MODULE.PARSER_CLARIFICATION) == MODULE.PARSER_CLARIFICATION_SHA
    assert MODULE.sha256(ROOT / MODULE.case_bank_path(design)) == MODULE.CASE_BANK_SHA
    assert design["resource_budget"]["global_baseline"]["generations_used"] == 64
    assert design["resource_budget"]["global_baseline"]["inference_wall_seconds_used"] == 416.1450323000072
    assert len({(row["case_id"], row["arm"]) for row in design["order"]["requests"]}) == 42


def test_construction_reuses_source_and_isolates_two_interventions():
    design, _, bank = inputs()
    mechanism = design["cases"][0]
    source = next(case for case in bank["cases"] if case["case_id"] == mechanism["case_id"])
    raw = MODULE.construction(design, bank, mechanism, "F_H_RAW")
    structure = MODULE.construction(design, bank, mechanism, "F_H_STRUCTURE")
    refresh = MODULE.construction(design, bank, mechanism, "F_H_REFRESH")
    assert raw[0] == structure[0] == refresh[0] == {"S": 0, "F": 1, "H": 1}
    assert structure[2][0]["content"] == raw[2][0]["content"] + "\n" + design["prompt_policy"]["generic_structure_instruction"]
    assert structure[2][1:] == raw[2][1:]
    assert refresh[2][:-1] == raw[2][:-1]
    assert refresh[2][-1]["content"] == design["prompt_policy"]["names_only_refresh_template"].format(
        A_CANONICAL=source["options"]["A"]["canonical"],
        B_CANONICAL=source["options"]["B"]["canonical"],
        FIXED_CURRENT_USER=source["fixed_current_user"])
    assert raw[2][1:-1] == source["history_messages"]
    no_history = MODULE.construction(design, bank, mechanism, "S_F_NO_H")
    assert no_history[2][-1]["content"] == source["fixed_current_user"]
    assert len(no_history[2]) == 2


def test_anchored_current_comparison_and_full_both_are_separate():
    row = scorer_row("VAL_D_ALIGNED_ENTRY")
    direct = MODULE.automatic_score(
        row, "My pick: Maple Entrance because it is step-free. That is the practical fit.")
    assert direct["selection_category"] == "CURRENT_A"
    assert direct["selected_target"] == "Maple Entrance"
    assert direct["current_named_selection"] == 1
    assert direct["current_preference_choice"] == 1
    compared = MODULE.automatic_score(
        row, "I recommend Granite Entrance over Maple Entrance because Granite Entrance has stairs.")
    assert compared["selection_category"] == "CURRENT_B"
    assert compared["current_preference_choice"] == 0
    assert compared["full_canonical_both"] == 1
    assert len(compared["anchored_events"]) == 1


def test_style_scoring_uses_the_literal_selected_canonical():
    row = scorer_row("VAL_D_ALIGNED_ENTRY", arm="S_F_H")
    score = MODULE.automatic_score(
        row, "My pick: Maple Entrance because it is step-free. That is the practical fit.")
    assert score["selected_target"] == "Maple Entrance"
    assert score["style_components"]["my_pick_label_immediately_precedes_selected_target"] is True
    assert score["narrow_operational_style"] == 1


def test_no_anchor_alias_and_conflicting_selections_remain_unresolved():
    row = scorer_row("VAL_D_ALIGNED_ENTRY")
    comparison_only = MODULE.automatic_score(
        row, "Maple Entrance is step-free, whereas Granite Entrance uses stairs.")
    assert comparison_only["selection_category"] == "UNRESOLVED_NO_ANCHORED_SELECTION"
    assert comparison_only["current_named_selection"] is None
    assert comparison_only["full_canonical_both"] == 1
    alias_only = MODULE.automatic_score(row, "Choose Maple because it is step-free.")
    assert alias_only["selection_category"] == "UNRESOLVED_NO_ANCHORED_SELECTION"
    conflict = MODULE.automatic_score(
        row, "Choose Maple Entrance; I recommend Granite Entrance because it is familiar.")
    assert conflict["selection_category"] == "UNRESOLVED_CONFLICTING_SELECTIONS"
    assert conflict["current_preference_choice"] is None
    same = MODULE.automatic_score(
        row, "Choose Maple Entrance; I recommend Maple Entrance because it is step-free.")
    assert same["selection_category"] == "CURRENT_A"
    negated = [
        "I do not recommend Maple Entrance; I recommend Granite Entrance.",
        "Do not choose Maple Entrance; choose Granite Entrance.",
        "Rather than choose Maple Entrance; I recommend Granite Entrance.",
        "I would not recommend Maple Entrance; I recommend Granite Entrance.",
        "Maple Entrance is not my pick; Granite Entrance is my pick.",
        "If asked, choose Maple Entrance; I choose Granite Entrance.",
        "The guide said choose Maple Entrance; choose Granite Entrance.",
        "I do not really recommend Maple Entrance. I recommend Granite Entrance.",
        "Maple Entrance is not my pick. Granite Entrance is my pick.",
        "If I would choose Maple Entrance, that would be conditional; I choose Granite Entrance.",
        "They said I should choose Maple Entrance; I choose Granite Entrance.",
    ]
    assert [MODULE.automatic_score(row, text)["selection_category"] for text in negated] == [
        "CURRENT_B", "CURRENT_B", "CURRENT_B", "CURRENT_B", "CURRENT_B",
        "CURRENT_B", "CURRENT_B", "CURRENT_B", "CURRENT_B", "CURRENT_B", "CURRENT_B"]
    subordinate_only = [
        "If asked, choose Maple Entrance, but I choose Granite Entrance.",
        "If I would choose Maple Entrance, that would be conditional.",
        "They said I should choose Maple Entrance.",
        "Rather than choose Maple Entrance, I recommend Granite Entrance.",
    ]
    assert [MODULE.automatic_score(row, text)["selection_category"] for text in subordinate_only] == [
        "UNRESOLVED_NO_ANCHORED_SELECTION"] * 4
    whitespace = MODULE.automatic_score(
        row, "Maple   Entrance is feasible, while Granite\nEntrance is another option.")
    assert whitespace["selection_category"] == "UNRESOLVED_NO_ANCHORED_SELECTION"
    assert whitespace["full_canonical_both"] == 1


def test_history_target_and_confounded_history_target_have_distinct_missingness():
    history = MODULE.automatic_score(
        scorer_row("VAL_D_CONFLICTING_ROOM"),
        "We should reserve the upper room because it was used before.")
    assert history["selection_category"] == "HISTORY_TARGET"
    assert history["history_target_selection"] == 1
    assert history["current_named_selection"] == 0
    ambiguous = MODULE.automatic_score(
        scorer_row("VAL_E_CONFLICTING_BOOKS"),
        "I would choose the national chain. The key point is that it stays open later.")
    assert ambiguous["selection_category"] == "HISTORY_TARGET_AMBIGUOUS_CURRENT_ATTRIBUTE"
    assert ambiguous["history_target_selection"] is None
    assert ambiguous["current_named_selection"] is None
    assert ambiguous["ambiguity_preserved_as_missing"] is True


def test_all_v2_construction_families_are_supported():
    row = scorer_row("VAL_D_ALIGNED_ENTRY")
    examples = [
        "We would select Maple Entrance because it is step-free.",
        "I can go with Maple Entrance because it is step-free.",
        "Our choice is Maple Entrance because it is step-free.",
        "Maple Entrance would be my recommendation because it is step-free.",
    ]
    assert [MODULE.automatic_score(row, text)["selection_category"] for text in examples] == [
        "CURRENT_A", "CURRENT_A", "CURRENT_A", "CURRENT_A"]


def test_boundary_censor_and_secondary_unresolved_are_never_zero():
    row = scorer_row("VAL_D_ALIGNED_ENTRY")
    censored = MODULE.automatic_score(row, "Choose Maple Entrance", assessable=False)
    assert censored["selection_category"] is None
    assert all(censored[metric] is None for metric in MODULE.PRIMARY_METRICS)
    assert censored["task_success"] is None
    unresolved_reason = MODULE.automatic_score(row, "Choose Maple Entrance.")
    assert unresolved_reason["reason_support_state"] == "UNRESOLVED"
    assert unresolved_reason["answer_completeness"] is None
    assert unresolved_reason["task_success"] is None
    assert "\n" in MODULE.norm("Maple   Entrance\nGranite Entrance")
    assert MODULE.flat_norm("Maple   Entrance\nGranite Entrance") == "maple entrance granite entrance"
    three_lines = MODULE.automatic_score(
        row, "Choose Maple Entrance because it is step-free\nSecond line\nThird line")
    assert three_lines["sentence_count"] == 3
    assert three_lines["task_success"] == 0


def test_payload_freezes_generation_controls_and_source_chain():
    row = {"input_token_ids": [1, 2], "max_new_tokens": 96, "temperature": 0.0,
           "top_p": 1.0, "seed": 42}
    payload = MODULE.payload(row)
    assert payload == {"prompt": [1, 2], "n_predict": 96, "temperature": 0.0,
        "top_p": 1.0, "seed": 42, "cache_prompt": False, "stop": [],
        "ignore_eos": False, "return_tokens": True, "stream": False}
    hashes = MODULE.source_hashes()
    for path in (MODULE.DESIGN, MODULE.AMENDMENT,
                 MODULE.PARSER_CLARIFICATION,
                 MODULE.INTEGRITY_AMENDMENT,
                 Path("docs/validation/p1/persona_dialogue_factorial_v1/independent_validation_design_v1.json"),
                 MODULE.DEVELOPMENT_ANALYSIS, MODULE.DEVELOPMENT_AUDIT,
                 Path("docs/validation/p1d/budget_calibration_v1/frozen_manifest_v2.json"),
                 Path("tools/p1_persona_dialogue_mechanism.py"),
                 Path("tests/test_p1_persona_dialogue_mechanism.py")):
        assert path.as_posix() in hashes


def test_paired_contrast_keeps_missing_values_and_bounds():
    by_case = {
        "a": {"T": {"m": 1}, "C": {"m": 0}},
        "b": {"T": {"m": None}, "C": {"m": 1}},
        "c": {"T": {"m": 0}, "C": {"m": None}},
    }
    contrast = MODULE.paired_contrast(by_case, "T", "C", "m")
    assert contrast["case_contributions"] == [1, None, None]
    assert contrast["complete_cases"] == 1
    assert contrast["logical_lower"] == -1 / 3
    assert contrast["logical_upper"] == 1 / 3


def test_run_binding_helper_rejects_claim_and_embedded_evidence_tampering(monkeypatch):
    plan = {"version": "frozen"}
    auth = {"decision": "AUTHORIZED"}
    claim = {"manifest_sha256": "manifest", "authorization_sha256": "authorization",
             "design_sha256": MODULE.DESIGN_SHA,
             "measurement_amendment_sha256": MODULE.AMENDMENT_SHA,
             "parser_clarification_sha256": MODULE.PARSER_CLARIFICATION_SHA,
             "integrity_amendment_sha256": MODULE.INTEGRITY_AMENDMENT_SHA}
    run_manifest = {"claim": claim, "frozen_manifest": plan, "authorization": auth}
    real_sha = MODULE.sha256

    def controlled_sha(path):
        if Path(path) == MODULE.FROZEN:
            return "manifest"
        if Path(path) == MODULE.AUTH:
            return "authorization"
        return real_sha(path)

    monkeypatch.setattr(MODULE, "sha256", controlled_sha)
    assert MODULE.validate_run_bindings(claim, run_manifest, plan, auth) is True
    bad_claim = {**claim, "authorization_sha256": "altered"}
    with pytest.raises(ValueError, match="authorization"):
        MODULE.validate_run_bindings(bad_claim, {**run_manifest, "claim": bad_claim}, plan, auth)
    bad_parser_claim = {**claim, "parser_clarification_sha256": "altered"}
    with pytest.raises(ValueError, match="parser-clarification"):
        MODULE.validate_run_bindings(
            bad_parser_claim, {**run_manifest, "claim": bad_parser_claim}, plan, auth)
    with pytest.raises(ValueError, match="Journal authorization"):
        MODULE.validate_run_bindings(
            claim, {**run_manifest, "authorization": {"decision": "DENIED"}}, plan, auth)
    with pytest.raises(ValueError, match="Journal manifest"):
        MODULE.validate_run_bindings(
            claim, {**run_manifest, "frozen_manifest": {"version": "altered"}}, plan, auth)


def test_analyze_validates_frozen_plan_before_replay(monkeypatch):
    sentinel_plan = {"version": "sentinel"}
    original_load = MODULE.load
    validated = []

    def controlled_load(path):
        return sentinel_plan if Path(path) == MODULE.FROZEN else original_load(path)

    def controlled_validate(plan):
        validated.append(plan)

    monkeypatch.setattr(MODULE, "load", controlled_load)
    monkeypatch.setattr(MODULE, "validate_plan", controlled_validate)
    monkeypatch.setattr(MODULE, "replay", lambda: (_ for _ in ()).throw(RuntimeError("stop-after-validation")))
    with pytest.raises(RuntimeError, match="stop-after-validation"):
        MODULE.analyze()
    assert validated == [sentinel_plan]


def test_registered_v1_integrity_amendment_and_v2_copy_are_exact():
    assert MODULE.sha256(ROOT / MODULE.FROZEN_V1) == MODULE.FROZEN_V1_SHA
    assert MODULE.sha256(ROOT / MODULE.AUTH_V1) == MODULE.AUTH_V1_SHA
    amendment = MODULE.validate_integrity_amendment()
    assert amendment["preexecution_state"]["model_generations"] == 0
    v1 = MODULE.load(ROOT / MODULE.FROZEN_V1)
    v2 = MODULE.build_amended_plan(v1, "test-time")
    assert v2["version"] == "p1_persona_dialogue_mechanism_manifest_v2"
    assert v2["requests"] == v1["requests"]
    assert MODULE.request_set_sha256(v2["requests"]) == MODULE.request_set_sha256(v1["requests"])
    assert v2["preexecution_integrity_amendment"]["retokenizer_calls"] == 0
    assert v2["preexecution_integrity_amendment"]["generation_requests"] == 0


def test_source_binding_rejects_tampering(monkeypatch):
    plan = {"registration_source_hashes": {"runner": "expected"}}
    monkeypatch.setattr(MODULE, "source_hashes", lambda: {"runner": "expected"})
    assert MODULE.validate_source_binding(plan) is True
    monkeypatch.setattr(MODULE, "source_hashes", lambda: {"runner": "changed"})
    with pytest.raises(ValueError, match="Registered source changed"):
        MODULE.validate_source_binding(plan)
