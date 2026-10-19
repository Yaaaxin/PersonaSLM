import json
import base64
from collections import Counter
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import p1_persona_dialogue_history_instruction_mechanism_v4 as module


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def valid_material_review():
    bank = load(ROOT / module.CASE_BANK)
    return {
        "version": module.MATERIAL_REVIEW_VERSION,
        "status": module.MATERIAL_REVIEW_STATUS,
        "verdict": module.MATERIAL_REVIEW_VERDICT,
        "bindings": module.expected_material_review_bindings(),
        "review_scope": "INDEPENDENT_READ_ONLY_PREOUTPUT_MATERIAL_REVIEW",
        "reviewer_provenance": {
            "reviewer_id": "independent-test-fixture-reviewer",
            "reviewer_type": "INDEPENDENT_READ_ONLY_TECHNICAL_REVIEWER",
            "human_semantic_judgments_provided": False,
            "independent_human_validation": False,
        },
        "protected_mapping_accessed": False,
        "protected_or_local_paths_enumerated": False,
        "model_outputs_accessed": False,
        "tokenizer_calls": 0,
        "generation_requests": 0,
        "reviewed_case_count": 8,
        "blocking_issues": [],
        "amendment_checks": {
            "archive_scope_repair_v4_1_applied": True,
            "instruction_package_terminology_applied": True,
            "text_declared_owner_attribution_package_terminology_applied": True,
            "archive_any_and_selected_endpoints_separated": True,
            "style_prefix_and_suffix_endpoints_separated": True,
            "indicator_discordance_construct_v4_2_applied": True,
            "all_ten_human_only_endpoints_present": True,
        },
        "claim_boundaries": {
            "synthetic_material_review_only": True,
            "human_semantic_validation": False,
            "independent_human_validation": False,
            "model_outcome_evidence": False,
            "algorithmic_novelty_evidence": False,
        },
        "case_summaries": [{
            "case_id": case["case_id"],
            "persona_id": case["persona_id"],
            "task_family": case["task_family"],
            "verdict": "PASS_NO_BLOCKING_MATERIAL_ISSUE",
            "uniquely_supported_current_option": True,
            "archive_current_attribute_separation": True,
            "clear_current_and_control_ownership": True,
            "direct_answer_leakage_detected": False,
            "blocking_issues": [],
            "rationale": "Test-only structurally valid independent review fixture.",
        } for case in bank["cases"]],
    }


def valid_registration():
    return {
        "version": module.REGISTRATION_VERSION,
        "status": module.REGISTRATION_STATUS,
        "prospective": True,
        "outcomes_observed": False,
        "observed_model_responses": [],
        "observed_endpoint_values": [],
        "bindings": module.expected_registration_bindings(),
        "allocation": {
            "synthetic_personas": 8, "cases": 8, "arms": 12,
            "planned_generation_attempts": 96, "attempts_per_case": 12,
            "attempts_per_arm": 8, "retries": 0, "hidden_warmups": 0,
        },
        "schedule_sha256": module._canonical_json_hash(
            module.request_specs(load(ROOT / module.DESIGN))),
        "estimand_weights_sha256": module._canonical_json_hash(
            module.registered_estimand_weights()),
        "resources": {
            "baseline_generations_consumed": module.GENERATION_BASELINE,
            "global_generation_limit": module.GENERATION_LIMIT,
            "projected_generations_consumed_if_complete":
                module.GENERATION_BASELINE + module.MAX_ATTEMPTS,
            "baseline_inference_seconds_consumed": module.INFERENCE_BASELINE,
            "global_inference_seconds_limit": module.INFERENCE_LIMIT,
            "batch_completion_inference_seconds_ceiling": module.INFERENCE_CEILING,
            "batch_wall_seconds_ceiling": module.WALL_CEILING,
            "minimum_preflight_available_physical_ram_bytes": module.MIN_PREFLIGHT_RAM,
            "minimum_live_available_physical_ram_bytes": module.MIN_LIVE_RAM,
            "minimum_disk_reserve_bytes": module.MIN_DISK,
            "maximum_native_tokenizer_calls": module.NATIVE_TOKENIZER_CALLS,
            "maximum_live_server_tokenizer_checks": module.LIVE_TOKENIZER_CHECKS,
            "maximum_tokenizer_operations_total":
                module.NATIVE_TOKENIZER_CALLS + module.LIVE_TOKENIZER_CHECKS,
        },
        "execution_state": {
            "authorized": False, "native_tokenizer_calls": 0,
            "live_server_tokenizer_checks": 0, "model_server_launches": 0,
            "generation_attempts": 0, "completed_generations": 0, "results": 0,
        },
        "endpoint_policy": {
            "automatic_endpoints": list(module.AUTOMATIC_ENDPOINTS),
            "automatic_claim_class":
                "LITERAL_SELECTION_FORMAT_AND_EVALUATOR_PROXIES_ONLY",
            "unassessable_automatic_values": "MISSING_NOT_ZERO",
            "structural_not_applicable_values": "N_A_EXCLUDED_NOT_ZERO",
            "semantic_endpoints": list(module.SEMANTIC_ENDPOINTS),
            "semantic_endpoint_status": "HUMAN_ONLY_NOT_RATED",
            "automatic_semantic_substitution": False,
        },
        "analysis_policy": {
            "unit": "CASE_PAIRED_WITHIN_CASE_CONTRAST",
            "inference": "ESTIMATION_FIRST_NO_P_VALUES_NO_CONFIRMATORY_SIGNIFICANCE",
            "leave_one_persona_out": True,
            "leave_one_case_out_range_is_confidence_interval": False,
            "logical_missing_outcome_bounds": True,
            "missing_recoded_as_zero": False,
            "structural_n_a_in_denominator": False,
        },
        "claim_boundaries": {
            "configuration_specific_synthetic_mechanism_associations_only": True,
            "general_semantic_history_failure_established": False,
            "real_speaker_persona_fidelity_established": False,
            "population_causality_established": False,
            "independent_human_validation_established": False,
            "algorithmic_novelty_established": False,
        },
        "stopping_and_integrity": {
            "four_gib_preflight_required": True,
            "below_gate_is_no_go_before_server_or_generation": True,
            "zero_retry": True,
            "resume_or_fill_failed_suffix": False,
            "append_only_evidence": True,
            "outcome_based_stopping": False,
            "independent_validation_set_used_for_tuning": False,
        },
    }


def test_prospective_package_is_eight_by_twelve_and_unstarted():
    design, bank = load(ROOT / module.DESIGN), load(ROOT / module.CASE_BANK)
    assert module.sha256(ROOT / module.DESIGN) == module.DESIGN_SHA
    assert module.sha256(ROOT / module.CASE_BANK) == module.CASE_BANK_SHA
    assert module.sha256(ROOT / module.AMENDMENT) == module.AMENDMENT_SHA
    assert design["status"] == bank["status"] == "NOT_AUTHORIZED_NOT_TOKENIZED_NOT_EXECUTED"
    assert len(bank["personas"]) == len(bank["cases"]) == 8
    assert Counter(case["task_family"] for case in bank["cases"]) == {
        "COLLABORATIVE_PLANNING": 2, "SUPPORTIVE_NEXT_TURN": 2,
        "ROUTINE_NEGOTIATION": 2, "MISUNDERSTANDING_REPAIR": 2}
    assert Counter(case["preferred_option"] for case in bank["cases"]) == {"A": 4, "B": 4}
    rows = module.request_specs(design)
    assert len(rows) == len({row["request_id"] for row in rows}) == 96
    assert [row["order"] for row in rows] == list(range(96))
    assert Counter(row["arm_id"] for row in rows) == {arm: 8 for arm in module.ARMS}
    assert Counter(row["round"] for row in rows) == {index: 8 for index in range(12)}
    cases = {case["case_id"]: case for case in bank["cases"]}
    for arm in module.ARMS:
        subset = [row for row in rows if row["arm_id"] == arm]
        assert Counter(row["quartile"] for row in subset) == {index: 2 for index in range(4)}
        assert Counter(cases[row["case_id"]]["preferred_option"] for row in subset) == {
            "A": 4, "B": 4}
        assert Counter(cases[row["case_id"]]["task_family"] for row in subset) == {
            family: 2 for family in set(case["task_family"] for case in cases.values())}
    for case_id in cases:
        assert Counter(row["arm_id"] for row in rows if row["case_id"] == case_id) == {
            arm: 1 for arm in module.ARMS}
    assert (ROOT / module.AUTHORIZATION).is_file()
    assert load(ROOT / module.AUTHORIZATION) == module.authorization_requirements()
    assert not (ROOT / module.FROZEN).exists()
    assert not (ROOT / module.PREFLIGHT).exists()
    assert not (ROOT / module.ROOT / "claim.json").exists()


def test_append_only_amendment_repairs_archive_scope_and_claims():
    amendment = load(ROOT / module.AMENDMENT)
    assert amendment["parent_design"]["sha256"] == module.DESIGN_SHA
    for context in ("C1_CONTROL_LIVE", "C3_PERSONA_LIVE"):
        value = amendment["effective_prompt_replacements"][f"{context}.archive_user_template"]
        assert "This message and the following assistant message form a completed archive" in value
        assert "next two messages" not in value
    claims = " ".join(amendment["estimand_and_claim_clarifications"])
    assert "text-declared owner-attribution treatment-package" in claims
    assert "instruction-package contrast" in claims
    assert amendment["measurement_clarifications"]["replace_ambiguous_endpoint"][
        "effective_name"] == "any_archived_entity_occurrence"
    assert amendment["measurement_clarifications"]["additional_endpoint"][
        "name"] == "selected_archived_target_occurrence"
    clarification = load(ROOT / module.MEASUREMENT_CLARIFICATION)
    assert module.sha256(ROOT / module.MEASUREMENT_CLARIFICATION) == \
        module.MEASUREMENT_CLARIFICATION_SHA
    endpoint = clarification["effective_endpoint"]
    assert endpoint["replaces_provisional_key"] == "name_anchor_discordance"
    assert endpoint["name"] == "preferred_name_anchor_indicator_discordance"
    assert "correctness indicators" in endpoint["definition"]


def test_context_and_instruction_construction_isolates_registered_packages():
    design, bank = load(ROOT / module.DESIGN), load(ROOT / module.CASE_BANK)
    for case in bank["cases"]:
        for instruction in module.INSTRUCTIONS:
            built = {context: module.construction(
                design, bank, case, f"{context}__{instruction}")[1]
                for context in module.CONTEXTS}
            assert len(built["C0_NO_HISTORY"]) == len(built["C2_PERSONA_QUOTED"]) == 2
            assert len(built["C1_CONTROL_LIVE"]) == len(built["C3_PERSONA_LIVE"]) == 4
            assert all(messages[0] == built["C0_NO_HISTORY"][0]
                       for messages in built.values())
            c1, c3 = built["C1_CONTROL_LIVE"], built["C3_PERSONA_LIVE"]
            assert c1[2] == c3[2] == {"role": "assistant",
                                      "content": case["archive_assistant"]}
            assert c1[3] == c3[3] == built["C0_NO_HISTORY"][1]
            assert "next two messages" not in c1[1]["content"]
            assert "next two messages" not in c3[1]["content"]
            assert case["archive_question"] in c1[1]["content"]
            assert case["archive_question"] in c3[1]["content"]
            quoted = built["C2_PERSONA_QUOTED"][1]["content"]
            assert case["archive_question"] in quoted
            assert case["archive_assistant"] in quoted
        for context in module.CONTEXTS:
            messages = [module.construction(
                design, bank, case, f"{context}__{instruction}")[1]
                for instruction in module.INSTRUCTIONS]
            # Instruction is confined to the system message.
            assert all(value[1:] == messages[0][1:] for value in messages[1:])


def test_formal_ancestry_audit_recomputes_exactly_without_private_mapping():
    stored = load(ROOT / module.MATERIAL_AUDIT)
    assert module.sha256(ROOT / module.MATERIAL_AUDIT) == module.MATERIAL_AUDIT_SHA
    assert module.material_overlap_audit() == stored
    assert stored["status"] == "PASS_ZERO_NORMALIZED_EXACT_OVERLAP"
    assert stored["normalized_exact_overlap_total"] == 0
    assert stored["canonical_entity_normalized_sha256_overlap"] == 0
    assert stored["exact_question_or_template_overlap"] == 0
    assert stored["protected_mapping_accessed"] is False
    assert stored["lexical_fourgram_overlap"]["intersection_count"] == 12


def test_material_ancestry_audit_is_an_unconditional_content_gate(
        tmp_path, monkeypatch):
    audit = tmp_path / "material-audit.json"
    monkeypatch.setattr(module, "MATERIAL_AUDIT", audit)
    monkeypatch.setattr(module, "MATERIAL_AUDIT_SHA", "PENDING")
    with pytest.raises(ValueError, match="Material ancestry audit missing"):
        module.validate_design()
    audit.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(module, "MATERIAL_AUDIT_SHA", module.sha256(audit))
    with pytest.raises(ValueError, match="Material ancestry audit content"):
        module.validate_design()


def test_review_and_registration_are_unconditional_pretokenization_gates(
        tmp_path, monkeypatch):
    review = tmp_path / "review.json"
    registration = tmp_path / "registration.json"
    monkeypatch.setattr(module, "MATERIAL_REVIEW", review)
    monkeypatch.setattr(module, "REGISTRATION", registration)
    monkeypatch.setattr(module, "MATERIAL_REVIEW_SHA", "PENDING")
    monkeypatch.setattr(module, "REGISTRATION_SHA", "PENDING")
    with pytest.raises(ValueError, match="Material scientific review"):
        module.validate_design()
    review.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(module, "MATERIAL_REVIEW_SHA", module.sha256(review))
    with pytest.raises(ValueError, match="Material scientific review content"):
        module.validate_design()
    review.write_text(json.dumps(valid_material_review()), encoding="utf-8")
    monkeypatch.setattr(module, "MATERIAL_REVIEW_SHA", module.sha256(review))
    with pytest.raises(ValueError, match="Prospective registration missing"):
        module.validate_design()
    registration.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(module, "REGISTRATION_SHA", module.sha256(registration))
    with pytest.raises(ValueError, match="Prospective registration content"):
        module.validate_design()


def test_static_review_and_registration_contracts_reject_semantic_drift():
    review = valid_material_review()
    assert module.validate_material_review_artifact(review)["reviewed_cases"] == 8
    invalid_review = json.loads(json.dumps(review))
    invalid_review["case_summaries"][0]["direct_answer_leakage_detected"] = True
    with pytest.raises(ValueError, match="invalid case summary"):
        module.validate_material_review_artifact(invalid_review)
    registration = valid_registration()
    assert module.validate_registration_artifact(registration)[
        "planned_attempts"] == 96
    invalid_registration = json.loads(json.dumps(registration))
    invalid_registration["execution_state"]["generation_attempts"] = 1
    with pytest.raises(ValueError, match="zero-execution state"):
        module.validate_registration_artifact(invalid_registration)


def test_recursive_local_dependency_closure_is_exact_and_complete(monkeypatch):
    expected = {
        "tools/p1_persona_dialogue_history_template_mechanism.py",
        "tools/p1_persona_dialogue_independent_replication.py",
        "tools/p1_persona_dialogue_mechanism.py",
        "tools/p1_persona_dialogue_mechanism_analysis_v2.py",
        "tools/p1_persona_dialogue_factorial.py",
        "tools/p1d_instruct_smoke.py",
        "tools/p1d_budget_calibration.py",
        "tools/p1d_format_calibration.py",
        "tools/p1d_instruct_template_check.py",
        "tools/p1d_format_diagnostic_proposal.py",
        "tools/p1c_tokenize.py",
        "tools/p1c_design.py",
        "tools/p1d_design.py",
        "tools/p1d_scientific_audit.py",
    }
    assert set(module.LOCAL_TOOL_DEPENDENCIES) == expected
    monkeypatch.setattr(module, "MATERIAL_REVIEW", ROOT / module.AMENDMENT)
    monkeypatch.setattr(module, "REGISTRATION", ROOT / module.MEASUREMENT_CLARIFICATION)
    inventory = module.source_hashes()
    assert expected <= set(inventory)


def test_frozen_source_inventory_detects_transitive_dependency_drift(monkeypatch):
    review = ROOT / module.AMENDMENT
    registration = ROOT / module.MEASUREMENT_CLARIFICATION
    monkeypatch.setattr(module, "MATERIAL_REVIEW", review)
    monkeypatch.setattr(module, "REGISTRATION", registration)
    monkeypatch.setattr(module, "MATERIAL_REVIEW_SHA", module.sha256(review))
    monkeypatch.setattr(module, "REGISTRATION_SHA", module.sha256(registration))
    expected = module.source_hashes()
    dependency = (ROOT / "tools/p1_persona_dialogue_mechanism_analysis_v2.py").resolve()
    key = dependency.relative_to(ROOT).as_posix()
    assert key in expected
    real_sha256 = module.sha256

    def drift(path):
        return "0" * 64 if Path(path).resolve() == dependency else real_sha256(path)

    monkeypatch.setattr(module, "sha256", drift)
    with pytest.raises(ValueError, match="source/dependency inventory changed"):
        module.validate_registered_source_hashes(expected)


def _scoring_row(case, persona, context):
    return {
        "context_id": context,
        "preferred_option": case["preferred_option"],
        "options": case["options"],
        "archive_target_strings": [value["canonical"]
                                   for value in case["archive_options"].values()],
        "archive_selected_target": case["archive_selected_target"],
        "control_speaker_name": persona["control_speaker_name"],
        "reason_prefix": persona["reason_prefix"],
        "reason_suffix": persona["reason_suffix"],
    }


def test_automatic_endpoints_are_literal_and_semantics_are_explicitly_unrated():
    bank = load(ROOT / module.CASE_BANK)
    case = bank["cases"][0]
    persona = bank["personas"][case["persona_id"]]
    preferred = case["preferred_option"]
    option = case["options"][preferred]
    row = _scoring_row(case, persona, "C3_PERSONA_LIVE")
    response = (f"Option {preferred} [{option['anchor']}] — {option['canonical']}. "
                f"{persona['reason_prefix']} the current evidence, {persona['reason_suffix']}")
    score = module.automatic_score(row, response)
    assert score["exact_valid_current_output_line"] == 1
    assert score["exactly_two_sentence_realization"] == 1
    assert score["preferred_current_name_selection"] == 1
    assert score["preferred_current_anchor_selection"] == 1
    assert score["evaluator_gap"] == 0
    assert score["preferred_name_anchor_indicator_discordance"] == 0
    assert score["label_anchor_name_consistency"] == "CONSISTENT"
    assert score["style_prefix_contract"] == score["style_suffix_contract"] == 1
    assert all(item == {"state": "HUMAN_ONLY_NOT_RATED", "value": None}
               for item in score["semantic_endpoints"].values())

    meta = module.automatic_score(
        row, "Option A [<exact A anchor>] — <exact A name>. A literal schema remains.")
    assert meta["literal_placeholder_occurrence"] == 1
    assert meta["exact_valid_current_output_line"] == 0

    name_only = module.automatic_score(
        row, f"I choose {option['canonical']}. {persona['reason_prefix']} it, "
             f"{persona['reason_suffix']}")
    assert name_only["preferred_current_name_selection"] == 1
    assert name_only["preferred_current_anchor_selection"] == 0
    assert name_only["evaluator_gap"] == 1
    assert name_only["preferred_name_anchor_indicator_discordance"] == 1

    anchor_only = module.automatic_score(
        row, f"Option {preferred} [{option['anchor']}]. {persona['reason_prefix']} it, "
             f"{persona['reason_suffix']}")
    assert anchor_only["preferred_current_name_selection"] == 0
    assert anchor_only["preferred_current_anchor_selection"] == 1
    assert anchor_only["evaluator_gap"] == -1

    archived = module.automatic_score(
        row, f"I recall {case['archive_selected_target']}. It is only archived.")
    assert archived["any_archived_entity_occurrence"] == 1
    assert archived["selected_archived_target_occurrence"] == 1
    assert archived["unprompted_archived_name_occurrence"] is None
    assert archived["endpoint_states"]["unprompted_archived_name_occurrence"] == "STRUCTURAL_NA"


def test_applicability_distinguishes_structural_na_from_missing_and_zero():
    bank = load(ROOT / module.CASE_BANK)
    case = bank["cases"][0]
    persona = bank["personas"][case["persona_id"]]
    c0 = _scoring_row(case, persona, "C0_NO_HISTORY")
    score = module.automatic_score(
        c0, f"I remember {case['archive_selected_target']}. That is unprompted.")
    assert score["any_archived_entity_occurrence"] is None
    assert score["selected_archived_target_occurrence"] is None
    assert score["endpoint_states"]["any_archived_entity_occurrence"] == "STRUCTURAL_NA"
    assert score["unprompted_archived_name_occurrence"] == 1
    assert score["control_owner_mention"] is None
    assert score["endpoint_states"]["control_owner_mention"] == "STRUCTURAL_NA"

    missing = module.automatic_score(c0, "", assessable=False)
    assert missing["preferred_current_name_selection"] is None
    assert missing["endpoint_states"]["preferred_current_name_selection"] == \
        "MISSING_UNASSESSABLE"
    assert missing["endpoint_states"]["any_archived_entity_occurrence"] == "STRUCTURAL_NA"
    assert missing["endpoint_states"]["control_owner_mention"] == "STRUCTURAL_NA"


def _score(value, metric, state="ASSESSED"):
    return {metric: value, "endpoint_states": {metric: state}}


@pytest.mark.parametrize(
    "bounds,complete_high,complete_low,missing_high,expected",
    [((0, 1), 1, 0, None, (7 / 8, 1.0)),
     ((-1, 1), 1, 0, None, (6 / 8, 1.0)),
     ((1, 5), 5, 1, None, (3.5, 4.0))])
def test_range_aware_bounds_and_lopo_cover_binary_gap_and_human_scales(
        bounds, complete_high, complete_low, missing_high, expected):
    cases = [f"case_{index}" for index in range(8)]
    personas = {case: f"persona_{index}" for index, case in enumerate(cases)}
    metric = "endpoint"
    by_case = {}
    for index, case in enumerate(cases):
        by_case[case] = {
            "high": _score(missing_high if index == 0 else complete_high, metric,
                           "MISSING_UNASSESSABLE" if index == 0 else "ASSESSED"),
            "low": _score(complete_low, metric),
        }
    result = module.range_aware_contrast(
        by_case, cases, {"high": 1.0, "low": -1.0}, metric, personas, bounds)
    assert result["planned_cases"] == result["eligible_cases"] == 8
    assert result["resolved_cases"] == 7
    assert result["missing_cases"] == 1
    assert result["logical_missing_outcome_bounds"] == pytest.approx(expected)
    assert len(result["leave_one_persona_out"]) == 8
    assert result["missing_recoded_as_zero"] is False


def test_structural_na_is_excluded_not_bounded_or_zeroed():
    cases = ["case_a", "case_b"]
    personas = {"case_a": "persona_a", "case_b": "persona_b"}
    by_case = {
        "case_a": {"high": _score(None, "x", "STRUCTURAL_NA"),
                   "low": _score(0, "x")},
        "case_b": {"high": _score(1, "x"), "low": _score(0, "x")}}
    result = module.range_aware_contrast(
        by_case, cases, {"high": 1.0, "low": -1.0}, "x", personas, (0, 1))
    assert result["eligible_cases"] == 1
    assert result["structural_n_a_cases"] == 1
    assert result["paired_point_estimate"] == 1
    assert result["logical_missing_outcome_bounds"] == [1, 1]


def test_registered_estimands_are_paired_zero_sum_and_primary_coefficients():
    weights = module.registered_estimand_weights()
    assert "literal_metasyntax" not in weights
    assert "persona_history_attribution" not in weights
    assert all(sum(value.values()) == pytest.approx(0) for value in weights.values())
    literal = weights["instruction_package_meta_vs_concrete"]
    assert len(literal) == 8
    assert all(abs(value) == pytest.approx(1 / 4) for value in literal.values())
    history = weights["text_declared_owner_attribution_package"]
    assert len(history) == 6
    assert all(abs(value) == pytest.approx(1 / 3) for value in history.values())


def test_human_only_endpoint_inventory_matches_all_ten_parent_endpoints():
    design = load(ROOT / module.DESIGN)
    assert tuple(design["human_review_plan"]["stage_a"]["endpoints"]) == \
        module.SEMANTIC_ENDPOINTS
    assert len(module.SEMANTIC_ENDPOINTS) == 10
    assert "material_unverifiable_claim" in module.SEMANTIC_ENDPOINTS
    assert "evidence_spans" in module.SEMANTIC_ENDPOINTS


def test_authorization_contract_is_read_only_finite_and_uses_four_gib_gate():
    before = {path: (ROOT / path).exists() for path in (
        module.AUTHORIZATION, module.FROZEN, module.PREFLIGHT, module.ROOT / "claim.json")}
    required = module.authorization_requirements()
    assert required["maximum_native_tokenizer_calls"] == 112
    assert required["maximum_live_server_tokenizer_checks"] == 96
    assert required["maximum_tokenizer_operations_total"] == 208
    assert required["maximum_generation_attempts"] == 96
    assert required["retries"] == required["hidden_warmups"] == 0
    assert required["minimum_available_physical_ram_bytes"] == 4 * 1024**3
    assert required["minimum_live_available_physical_ram_bytes"] == 512 * 1024**2
    assert required["completion_inference_seconds_ceiling"] == 2400
    assert required["batch_wall_seconds_ceiling"] == 3600
    after = {path: (ROOT / path).exists() for path in before}
    assert after == before
    assert module.authorization_requirements(require_unstarted=False)[
        "maximum_generation_attempts"] == 96


def test_register_accepts_present_official_authorization_and_uses_mock_tokenizer_only(
        tmp_path, monkeypatch):
    binary = tmp_path / "bin"
    binary.mkdir()
    model_path = tmp_path / "model.gguf"
    backend_path = binary / "llama-server.exe"
    tokenizer_path = binary / "llama-tokenize.exe"
    template_path = tmp_path / "chat-template.jinja"
    for path, value in ((model_path, b"model"), (backend_path, b"server"),
                        (tokenizer_path, b"tokenizer")):
        path.write_bytes(value)
    template_path.write_text("test-template", encoding="utf-8")

    model = dict(module.MODEL)
    model.update(model_file=model_path.as_posix(), model_sha256=module.sha256(model_path),
                 backend_file=backend_path.as_posix(),
                 backend_sha256=module.sha256(backend_path))
    runtime = dict(module.RUNTIME)
    runtime.update(backend_path=backend_path.as_posix(),
                   backend_sha256=module.sha256(backend_path),
                   chat_template_path=template_path.as_posix(),
                   chat_template_sha256=module.sha256(template_path))
    tokenizer_source = tmp_path / "tokenizer-source.json"
    tokenizer_source.write_text(json.dumps({"native_tokenizer_identity": {
        "tokenizer_sha256": module.sha256(tokenizer_path), "dll_hashes": {}}}),
        encoding="utf-8")

    output = tmp_path / "evidence"
    results = tmp_path / "results"
    monkeypatch.setattr(module, "MODEL", model)
    monkeypatch.setattr(module, "RUNTIME", runtime)
    monkeypatch.setattr(module, "TOKENIZER_SOURCE", tokenizer_source)
    monkeypatch.setattr(module, "TOKENIZER_SOURCE_SHA", module.sha256(tokenizer_source))
    monkeypatch.setattr(module, "AUTHORIZATION", output / "execution_authorization_v4.json")
    monkeypatch.setattr(module, "FROZEN", output / "frozen_manifest_v4.json")
    monkeypatch.setattr(module, "PREFLIGHT", output / "preflight_v4.json")
    monkeypatch.setattr(module, "REGISTRATION_FAILURE", output / "registration_failure_v4.json")
    monkeypatch.setattr(module, "REGISTRATION", output / "prospective_registration_v4.json")
    monkeypatch.setattr(module, "MATERIAL_REVIEW", output / "material_scientific_review_v4.json")
    monkeypatch.setattr(module, "ROOT", results)
    monkeypatch.setattr(module.s, "memory_observation",
                        lambda _pid: {"system": {"available_physical": 8 * 1024**3}})
    monkeypatch.setattr(module.shutil, "disk_usage",
                        lambda _path: type("Disk", (), {"free": 8 * 1024**3})())
    monkeypatch.setattr(module.s, "render",
                        lambda _template, messages: json.dumps(
                            messages, ensure_ascii=False, sort_keys=True))
    monkeypatch.setattr(module, "source_hashes", lambda: {"mocked": "for-unit-test"})
    monkeypatch.setattr(module, "validate_plan", lambda plan: {"requests": len(plan["requests"])})

    calls = []

    def fake_tokenize(_tokenizer, text, _model):
        calls.append(text)
        return [101, 102], {"returncode": 0, "generation_requests": 0,
                            "text_sha256": module.th(text)}

    monkeypatch.setattr(module, "_tokenize_native", fake_tokenize)
    output.mkdir(parents=True)
    module.MATERIAL_REVIEW.write_text(json.dumps(valid_material_review()), encoding="utf-8")
    monkeypatch.setattr(module, "MATERIAL_REVIEW_SHA", module.sha256(module.MATERIAL_REVIEW))
    module.REGISTRATION.write_text(json.dumps(valid_registration()), encoding="utf-8")
    monkeypatch.setattr(module, "REGISTRATION_SHA", module.sha256(module.REGISTRATION))
    required = module.authorization_requirements()
    module.AUTHORIZATION.write_text(json.dumps(required), encoding="utf-8")

    report = module.register(module.AUTHORIZATION)
    assert report["status"] == "REGISTERED_NO_GENERATIONS"
    assert report["native_tokenizer_calls"] == 112
    assert report["generation_requests"] == 0
    assert len(calls) == 112
    assert module.FROZEN.is_file()
    assert not module.REGISTRATION_FAILURE.exists()


def test_failed_four_gib_preflight_records_exact_deficit_and_zero_execution(monkeypatch):
    available = 4_000_000_000

    def fail():
        raise ValueError("Less than registered 4 GiB available physical RAM")

    monkeypatch.setattr(module, "preflight", fail)
    monkeypatch.setattr(module.s, "memory_observation",
                        lambda _pid: {"system": {"available_physical": available}})
    monkeypatch.setattr(module.shutil, "disk_usage",
                        lambda _path: type("Disk", (), {"free": 9_000_000_000})())
    receipt = module.preflight_receipt()
    assert receipt["status"] == "FAIL"
    assert receipt["measured_available_physical_ram_bytes"] == available
    assert receipt["required_available_physical_ram_bytes"] == 4 * 1024**3
    assert receipt["available_ram_deficit_bytes"] == 4 * 1024**3 - available
    assert receipt["model_server_launches"] == receipt["completion_calls"] == 0
    assert receipt["new_model_generations"] == 0
    assert receipt["retry_permitted_without_change"] is False


def test_inventory_and_slot_states_preserve_prefix_without_retry_or_fill():
    plan = {"requests": [{"order": index, "request_id": f"r{index}",
                           "case_id": f"c{index}", "arm_id": "arm"}
                          for index in range(3)]}
    first = plan["requests"][0]
    events = [
        {"kind": module.STARTED, "data": first},
        {"kind": module.RAW, "data": {"request_id": "r0", "response": {},
                                        "latency_seconds": 1.0}},
        {"kind": module.DERIVED, "data": {"request_id": "r0"}},
    ]
    attempted, raw, derived = module.inventory(plan, events)
    assert attempted == ["r0"]
    states = module.planned_slot_states(plan, attempted, raw, derived)
    assert [row["state"] for row in states] == ["COMPLETED", "UNATTEMPTED", "UNATTEMPTED"]
    with pytest.raises(ValueError, match="Repeated"):
        module.inventory(plan, events + [{"kind": module.STARTED, "data": first}])


def test_cli_run_returns_nonzero_for_nonpass(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "run", lambda _path: {"status": "BLOCKED", "results": 0})
    assert module.main(["run", "--preflight", str(tmp_path / "preflight.json")]) == 2


def test_malformed_http_200_remains_unresolved_and_does_not_shift_slots():
    attempted = ["r0", "r1"]
    valid = {"content": "ok"}
    events = [
        {"kind": "http_response", "data": {
            "route": "/completion", "status": 200,
            "body_base64": base64.b64encode(b"not-json").decode("ascii"),
            "elapsed_seconds": 1.0}},
        {"kind": "http_response", "data": {
            "route": "/completion", "status": 200,
            "body_base64": base64.b64encode(json.dumps(valid).encode()).decode("ascii"),
            "elapsed_seconds": 2.0}},
    ]
    recovered = module._completion_http_evidence(events, attempted)
    assert "r0" not in recovered
    assert recovered["r1"] == {"response": valid, "latency_seconds": 2.0}
