import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from personaslm.response_status import classify_response


BASE = ROOT / "docs/validation/p1/persona_dialogue_independent_replication_v2"
DESIGN_PATH = BASE / "prospective_design_v2.json"
CASE_BANK_PATH = BASE / "case_bank_v2.json"
AMENDMENT_PATH = BASE / "prospective_design_amendment_v3.json"
CONDITIONS = ("C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "N_STYLE", "N_HISTORY")
FACTORIAL = CONDITIONS[:8]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def materialize(design, bank, case, condition):
    factors = design["factors"]["conditions"][condition]
    persona = bank["personas"][case["persona_id"]]
    policy = design["prompt_policy"]
    system = (
        policy["fixed_system_instruction"]
        + "\n\nSYNTHETIC SPEAKER: "
        + persona["speaker_name"]
        + "\n\n"
        + case["fixed_current_notes"]
    )
    if factors["S"]:
        system += "\n\n" + persona["S_block"]
    if factors["F"]:
        system += "\n\n" + persona["F_block"]
    if factors["control"] == "N_STYLE":
        system += "\n\n" + persona["neutral_style_block"]
    messages = [{"role": "system", "content": system}]
    if factors["H"]:
        messages.extend(case["history_messages"])
    if factors["control"] == "N_HISTORY":
        messages.extend(case["neutral_history_messages"])
    messages.append({"role": "user", "content": case["fixed_current_user"]})
    return messages


def test_frozen_schema_hash_order_model_and_resources():
    design, bank = read(DESIGN_PATH), read(CASE_BANK_PATH)
    assert design["status"] == "FROZEN_PROSPECTIVE_DESIGN_NOT_AUTHORIZED_NOT_EXECUTED"
    assert bank["status"] == "FROZEN_PROSPECTIVE_SYNTHETIC_MATERIALS_NO_OUTPUTS"
    assert design["research"]["zero_outputs_at_freeze"] is True
    assert design["authorization"]["execution_authorized"] is False
    assert design["bindings"]["case_bank"]["sha256"] == sha256(CASE_BANK_PATH)
    assert tuple(design["factors"]["conditions"]) == CONDITIONS
    assert design["model"]["artifact_sha256"] == (
        "0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc")
    assert sha256(ROOT / design["model"]["artifact_path"]) == design["model"]["artifact_sha256"]
    assert sha256(ROOT / design["runtime"]["backend_path"]) == design["runtime"]["backend_sha256"]
    assert sha256(ROOT / design["runtime"]["chat_template_path"]) == design["runtime"]["chat_template_sha256"]
    assert design["runtime"]["max_new_tokens"] == 96
    assert design["runtime"]["temperature"] == 0.0
    assert design["resource_budget"]["requests"] == 120
    assert design["resource_budget"]["maximum_generated_tokens"] == 11520
    assert design["resource_budget"]["minimum_available_physical_ram_bytes"] == 3 * 1024**3
    assert design["resource_budget"]["minimum_free_output_disk_bytes"] == 1024**3
    assert design["resource_budget"]["actual_completion_inference_seconds_ceiling"] == 7200.0
    assert design["resource_budget"]["global_baseline"]["generations_used"] == 106
    assert design["resource_budget"]["global_baseline"]["inference_wall_seconds_used"] == 668.7530845000028

    seed = design["order"]["seed"]
    expected = [
        {
            "request_id": f"pdlg_ir2_{case['case_id'].lower()}_{condition.lower()}",
            "case_id": case["case_id"],
            "condition": condition,
        }
        for case in bank["cases"]
        for condition in CONDITIONS
    ]
    expected.sort(key=lambda row: (
        hashlib.sha256(f"{seed}|{row['request_id']}".encode("utf-8")).hexdigest(),
        row["request_id"],
    ))
    expected = [{"order": index, **row} for index, row in enumerate(expected)]
    assert design["order"]["requests"] == expected


def test_persona_case_balance_and_information_isolation():
    bank = read(CASE_BANK_PATH)
    assert len(bank["personas"]) == 4
    assert len(bank["cases"]) == 12
    assert all(persona["synthetic"] is True for persona in bank["personas"].values())

    by_persona = defaultdict(list)
    by_regime = defaultdict(list)
    current_names = []
    for case in bank["cases"]:
        by_persona[case["persona_id"]].append(case)
        by_regime[case["history_regime"]].append(case)
        assert set(case["options"]) == {"A", "B"}
        names = [case["options"][side]["canonical"] for side in ("A", "B")]
        current_names.extend(names)
        history_text = "\n".join(message["content"] for message in case["history_messages"]).casefold()
        neutral_text = "\n".join(message["content"] for message in case["neutral_history_messages"]).casefold()
        current_text = (case["fixed_current_notes"] + "\n" + case["fixed_current_user"]).casefold()
        assert all(name.casefold() not in history_text for name in names)
        assert all(name.casefold() not in neutral_text for name in names)
        assert case["history_selected_target"].casefold() in history_text
        assert all(target.casefold() not in current_text for target in case["history_target_strings"])
        assert all(target.casefold() not in neutral_text for target in case["history_target_strings"])
        assert [message["role"] for message in case["history_messages"]] == ["user", "assistant"]
        assert [message["role"] for message in case["neutral_history_messages"]] == ["user", "assistant"]
        if case["history_regime"] == "ALIGNED_HELPFUL":
            assert case["history_favored_option"] == case["preferred_option"]
        elif case["history_regime"] == "OUTDATED_CONFLICTING":
            assert case["history_favored_option"] in {"A", "B"}
            assert case["history_favored_option"] != case["preferred_option"]
            assert case["metric_applicability"]["outdated_value_adoption"] == "C6_C7_ONLY"
        else:
            assert case["history_regime"] == "IRRELEVANT"
            assert case["history_favored_option"] is None

    assert len(set(current_names)) == 24
    assert all(len(cases) == 3 for cases in by_persona.values())
    assert all({case["history_regime"] for case in cases} == {
        "ALIGNED_HELPFUL", "OUTDATED_CONFLICTING", "IRRELEVANT"} for cases in by_persona.values())
    assert all(len(cases) == 4 for cases in by_regime.values())
    assert all(Counter(case["preferred_option"] for case in cases) == {"A": 2, "B": 2}
               for cases in by_regime.values())


def test_exact_materialization_for_all_ten_conditions():
    design, bank = read(DESIGN_PATH), read(CASE_BANK_PATH)
    for case in bank["cases"]:
        persona = bank["personas"][case["persona_id"]]
        built = {condition: materialize(design, bank, case, condition) for condition in CONDITIONS}
        assert all(messages[-1] == {"role": "user", "content": case["fixed_current_user"]}
                   for messages in built.values())
        assert all(case["fixed_current_notes"] in messages[0]["content"]
                   for messages in built.values())
        for condition, messages in built.items():
            factors = design["factors"]["conditions"][condition]
            system = messages[0]["content"]
            assert (persona["S_block"] in system) == bool(factors["S"])
            assert (persona["F_block"] in system) == bool(factors["F"])
            assert (persona["neutral_style_block"] in system) == (condition == "N_STYLE")
            assert all(message not in messages for message in case["neutral_history_messages"]) == (
                condition != "N_HISTORY")
            assert all(message not in messages for message in case["history_messages"]) == (not factors["H"])
            assert len(messages) == (4 if factors["H"] or condition == "N_HISTORY" else 2)


def test_new_materials_are_exactly_disjoint_from_prior_banks():
    bank = read(CASE_BANK_PATH)
    old_dev = read(ROOT / "docs/validation/p1/persona_dialogue_factorial_v1/prospective_design_v1.json")
    old_val = read(ROOT / "docs/validation/p1/persona_dialogue_factorial_v1/independent_validation_design_v1.json")
    p1d = read(ROOT / "docs/validation/p1d/independent_candidates_v4/candidate_bank_v1.json")
    prior_strings = set(strings(old_dev)) | set(strings(old_val)) | set(strings(p1d))
    prior_personas = set(old_dev["personas"]) | set(old_val["personas"])
    prior_cases = {case["case_id"] for case in old_dev["cases"] + old_val["cases"]}
    assert not (set(bank["personas"]) & prior_personas)
    assert not ({case["case_id"] for case in bank["cases"]} & prior_cases)

    new_materials = []
    for persona in bank["personas"].values():
        new_materials.extend((persona["speaker_name"], persona["S_block"], persona["F_block"]))
    for case in bank["cases"]:
        new_materials.extend((case["fixed_current_notes"], case["fixed_current_user"]))
        new_materials.extend(option["canonical"] for option in case["options"].values())
        new_materials.extend(message["content"] for message in case["history_messages"])
    assert all(material not in prior_strings for material in new_materials)
    assert all(marker.casefold() not in "\n".join(new_materials).casefold() for marker in (
        "that is the practical fit.", "the key point is", "my pick:"))


def test_style_markers_and_exact_choice_are_prospectively_boundary_safe():
    design, bank = read(DESIGN_PATH), read(CASE_BANK_PATH)
    style_policy = design["evaluation_policy"]["surface_style_uptake"]
    assert tuple(style_policy["scored_factorial_conditions"]) == FACTORIAL
    assert tuple(style_policy["scored_diagnostic_controls"]) == ("N_STYLE", "N_HISTORY")
    assert design["boundary_and_parser_preflight"]["applicable_style_scope"].startswith(
        "Score every persona's target surface-style markers in every C0-C7 factorial cell")
    unknown_line_label = re.compile(r"(?m)^[ \t]*[A-Z][A-Za-z_ ]{0,24}:[ \t]*")
    target_pattern = re.compile(r"^I recommend (.+)\.$")
    allowed_matchers = {
        "CASEFOLD_EXACT_PREFIX", "CASEFOLD_EXACT_SUFFIX",
        "CHAR_COUNT_EQUALS", "SENTENCE_COUNT_EQUALS",
    }
    for persona_id, persona in bank["personas"].items():
        checks = persona["operational_style_checks"]
        assert {check["matcher"] for check in checks} <= allowed_matchers
        prefix = next(check["value"] for check in checks if check["check_id"] == "second_sentence_prefix")
        suffix = next(check["value"] for check in checks if check["check_id"] == "second_sentence_suffix")
        assert ":" not in prefix
        assert not unknown_line_label.match(prefix.capitalize())
        for case in (item for item in bank["cases"] if item["persona_id"] == persona_id):
            for side in ("A", "B"):
                target = case["options"][side]["canonical"]
                response = f"I recommend {target}. {prefix} the stated reason, {suffix}"
                assert not unknown_line_label.search(response)
                assert response.split(". ", 1)[0] == f"I recommend {target}"
                assert target_pattern.fullmatch(response.split(". ", 1)[0] + ".").group(1) == target


def test_claim_boundaries_missingness_and_stopping_are_explicit():
    design = read(DESIGN_PATH)
    assert design["authorization"]["retries"] == 0
    assert design["stopping_and_reporting"]["outcome_based_stopping"] is False
    assert design["stopping_and_reporting"]["selection_threshold"] is None
    assert "Never recode unresolved" in design["evaluation_policy"]["missingness"]
    assert design["estimands"]["analysis"]["persona_clusters"] == 4
    assert "leave-one-persona-out" in design["estimands"]["analysis"]["persona_summary"]
    assert "no confirmatory p-values" in design["estimands"]["analysis"]["inference"]
    assert len(design["evaluation_policy"]["human_only"]) == 4
    assert any("real-speaker" in limitation for limitation in design["known_limitations"])


def test_v3_deactivates_unmatched_controls_and_freezes_96_request_subset():
    design, bank, amendment = read(DESIGN_PATH), read(CASE_BANK_PATH), read(AMENDMENT_PATH)
    assert amendment["status"] == "FROZEN_PROSPECTIVE_AMENDMENT_NOT_AUTHORIZED_NOT_EXECUTED"
    assert amendment["parent_design"]["sha256"] == sha256(DESIGN_PATH)
    assert amendment["case_bank"]["sha256"] == sha256(CASE_BANK_PATH)
    assert sha256(ROOT / amendment["measurement_source_binding"]["response_status_path"]) == (
        amendment["measurement_source_binding"]["response_status_sha256"])
    assert amendment["authorization"]["execution_authorized"] is False
    assert tuple(amendment["effective_design"]["effective_conditions"]) == FACTORIAL
    assert amendment["effective_design"]["requests"] == 96
    assert amendment["effective_design"]["retries"] == 0
    assert amendment["resource_budget"]["maximum_generated_tokens"] == 9216
    assert amendment["resource_budget"]["actual_completion_inference_seconds_ceiling"] == 5760.0
    assert amendment["resource_budget"]["maximum_after_batch"]["generations_used"] == 202
    assert all(value == 0 for value in amendment["pre_amendment_observation_state"].values()
               if isinstance(value, int))
    for control in ("N_STYLE", "N_HISTORY"):
        state = amendment["effective_design"]["deactivated_conditions"][control]
        assert state["status"] == "DEACTIVATED_NOT_EXECUTABLE_NOT_ATTEMPTED"
        assert state["authorized_attempts"] == 0
    assert all("N_STYLE" not in estimand and "N_HISTORY" not in estimand
               for estimand in amendment["effective_estimands"]["primary"])
    assert any("C1 minus N_STYLE" in estimand
               for estimand in amendment["effective_estimands"]["explicitly_removed"])
    assert any("C3 minus N_HISTORY" in estimand
               for estimand in amendment["effective_estimands"]["explicitly_removed"])

    filtered = [row for row in design["order"]["requests"] if row["condition"] in FACTORIAL]
    expected = [{"order": index, "request_id": row["request_id"],
                 "case_id": row["case_id"], "condition": row["condition"]}
                for index, row in enumerate(filtered)]
    assert amendment["order"]["requests"] == expected
    assert len({row["request_id"] for row in expected}) == 96
    assert all(row["condition"] in FACTORIAL for row in expected)


def test_bound_response_classifier_accepts_all_style_target_crossings_without_line_label_hazard():
    bank, amendment = read(CASE_BANK_PATH), read(AMENDMENT_PATH)
    assert sha256(ROOT / amendment["measurement_source_binding"]["response_status_path"]) == (
        amendment["measurement_source_binding"]["response_status_sha256"])
    prefixes = [
        next(check["value"] for check in persona["operational_style_checks"]
             if check["check_id"] == "second_sentence_prefix")
        for persona in bank["personas"].values()
    ]
    suffixes = [
        next(check["value"] for check in persona["operational_style_checks"]
             if check["check_id"] == "second_sentence_suffix")
        for persona in bank["personas"].values()
    ]
    current_targets = [case["options"][side]["canonical"]
                       for case in bank["cases"] for side in ("A", "B")]
    history_targets = [target for case in bank["cases"] for target in case["history_target_strings"]]
    assert len(current_targets) == len(set(current_targets)) == 24
    assert len(history_targets) == len(set(history_targets)) == 24
    for prefix, suffix in zip(prefixes, suffixes):
        for target in current_targets + history_targets:
            raw = f"I recommend {target}.\n{prefix} the documented reason, {suffix}"
            status = classify_response(raw, {"stop_type": "eog"})
            assert status["unit_identifiable"] is True
            assert status["first_span"]["text"] == raw
            assert status["excluded_tail"] == ""
            assert "unrecognized_line_label" not in status["reasons"]
