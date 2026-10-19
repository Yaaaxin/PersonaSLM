import json
from pathlib import Path
import struct
import sys

import pytest


sys.path.insert(0, str(Path("tools").resolve()))

import p1_model_feasibility_recovery as recovery


def test_gguf_metadata_reads_key_before_value_type(tmp_path):
    key = b"tokenizer.chat_template"
    value = b"{{ messages }}"
    fixture = tmp_path / "minimal.gguf"
    fixture.write_bytes(
        b"GGUF"
        + struct.pack("<IQQ", 3, 0, 1)
        + struct.pack("<Q", len(key)) + key
        + struct.pack("<I", 8)
        + struct.pack("<Q", len(value)) + value
    )
    metadata, read_info = recovery.gguf_metadata(fixture)
    assert metadata == {"tokenizer.chat_template": "{{ messages }}"}
    assert read_info["metadata_keys"] == 1
    assert read_info["tensor_data_read"] is False


def test_existing_template_runtime_is_byte_verified_before_reuse():
    evidence = recovery.verified_template_runtime()
    assert evidence["packages"] == {"Jinja2": "3.1.6", "MarkupSafe": "3.0.4"}
    assert evidence["package_file_count"] > 40
    assert recovery.sha256(evidence["provenance_path"]) == evidence["provenance_sha256"]


def test_prospective_freeze_and_authorization_are_exact_and_separate():
    plan = recovery.validate_freeze()
    ledger = recovery.load(recovery.LEDGER)

    assert recovery.sha256(recovery.FREEZE) == recovery.FREEZE_SHA256
    assert plan["status"] == "FROZEN_PROSPECTIVE_NO_CHALLENGER_DOWNLOAD_OR_INFERENCE_EXECUTED"
    assert ledger["hard_limits"]["new_local_cpu_generations"] == 1200
    assert ledger["hard_limits"]["actual_model_inference_wall_seconds"] == 20 * 60 * 60
    assert ledger["consumption_at_freeze"] == {
        "actual_model_inference_wall_seconds": 0.0,
        "new_local_cpu_generations": 0,
    }
    historical = ledger["historical_ledger_separation"]
    assert (historical["historical_attempted"], historical["historical_authorization"],
            historical["historical_remaining"]) == (80, 160, 80)
    assert "not consumed, transferred, or double-counted" in historical["policy"]


def test_two_challengers_have_frozen_order_identity_license_and_ram_gates():
    rows = recovery.validate_freeze()["candidate_order"]
    assert [row["candidate_id"] for row in rows] == [
        "smollm2_1_7b_instruct_q4_k_m",
        "qwen2_5_3b_instruct_q4_k_m",
    ]
    assert rows[0]["artifact"]["repository_revision"] == "6a7e79393ef2957e087f11fce1e50476799e313c"
    assert rows[0]["artifact"]["remote_sha256"] == (
        "decd2598bc2c8ed08c19adc3c8fdd461ee19ed5708679d1c54ef54a5a30d4f33"
    )
    assert rows[0]["license"]["identifier"] == "Apache-2.0"
    assert rows[0]["minimum_available_physical_bytes_before_load"] == 3 * 1024**3
    assert rows[1]["artifact"]["repository_revision"] == "af75b7aaf5bb163ce4c5dab4e6b84d844e96265d"
    assert rows[1]["artifact"]["remote_sha256"] == (
        "626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d"
    )
    assert rows[1]["artifact"]["bytes"] == 2_104_932_768
    assert rows[1]["license"]["identifier"] == "Qwen Research License"
    assert rows[1]["minimum_available_physical_bytes_before_load"] == 5 * 1024**3
    assert all(row["artifact"]["locally_available_at_freeze"] is False for row in rows)
    assert all(row["artifact"]["local_path"].startswith("models/gguf/feasibility_candidates/") for row in rows)


def test_screen_uses_only_observed_development_cases_and_preserves_pilot_holdout():
    plan = recovery.validate_freeze()
    screen = plan["frozen_development_screen"]
    screen_ids = [row["case_id"] for row in screen["cases"]]
    pilot_ids = plan["post_screen_boundary"]["disjoint_pilot_c0_case_ids"]

    assert screen_ids == [
        "p1_fallback_temporal_00", "p1_fallback_temporal_03",
        "p1_fallback_temporal_05", "p1_fallback_temporal_06",
        "p1_fallback_temporal_09", "p1_fallback_temporal_11",
        "p1_fallback_temporal_13", "p1_fallback_temporal_15",
    ]
    assert screen["independent_validation"] is False
    assert "PREVIOUSLY_OBSERVED" in screen["split"]
    assert len(pilot_ids) == len(set(pilot_ids)) == 8
    assert set(screen_ids).isdisjoint(pilot_ids)
    assert "not used for model selection" in plan["post_screen_boundary"]["policy"]
    assert ">=6/8" in plan["post_screen_boundary"]["factorial_continuation_rule"]


def test_generation_template_gate_and_selection_rule_are_nonadaptive():
    plan = recovery.validate_freeze()
    settings = plan["execution_policy"]["generation"]
    assert settings == {
        "cache_prompt": False,
        "context_tokens": 4096,
        "gpu_layers": 0,
        "ignore_eos": False,
        "max_new_tokens": 96,
        "mtp": False,
        "seed": 42,
        "stop": [],
        "temperature": 0.0,
        "threads": 4,
        "threads_batch": 4,
        "top_p": 1.0,
        "vision": False,
    }
    template = plan["execution_policy"]["template_policy"]
    assert "tokenizer.chat_template embedded in the exact GGUF" in template["materialization_gate"]
    assert "no added system instruction" in template["mapping"]
    assert "manual template rewrite" in template["prohibitions"]
    assert plan["measurement"]["qualification_threshold"] == 7
    assert "First qualifying candidate" in plan["selection_rule"]["principle"]
    assert "below 7/8" in plan["selection_rule"]["candidate_1_failure"]
    assert "do not add candidates" in plan["selection_rule"]["no_candidate_passes"]
    batch = plan["execution_policy"]["batch"]
    assert batch["maximum_attempts"] == 8
    assert batch["maximum_actual_completion_wall_seconds"] == 45 * 60
    assert batch["no_retries"] is True and batch["no_hidden_warmup"] is True


def test_completed_candidate_one_run_is_integrity_valid_and_below_frozen_gate():
    first = "smollm2_1_7b_instruct_q4_k_m"
    gate = recovery.outcome(first)
    audit = recovery.audit(first)

    assert gate is not None
    assert gate["status"] == "PASS"
    assert gate["complete"] is True
    assert gate["attempted"] == gate["completed_results"] == 8
    assert gate["automatic_success"] == 1
    assert gate["answer_states"] == {
        "CURRENT_VALUE_ADOPTION": 1,
        "OUTDATED_VALUE_ADOPTION": 1,
        "UNVERIFIABLE_ANSWER": 6,
    }
    assert gate["threshold"] == 7
    assert gate["proceed"] is False
    assert gate["integrity_status"] == "PASS"
    assert audit == {
        "attempted": 8,
        "candidate_id": first,
        "complete": True,
        "completion_http_records": 8,
        "inference_wall_seconds": pytest.approx(65.8762855, abs=1e-9),
        "integrity_status": "PASS",
        "proceed": False,
        "replayed_results": 8,
        "run_status": "PASS",
        "status": "PASS",
        "success": 1,
        "threshold": 7,
    }


def test_current_ledger_and_progression_close_bounded_two_candidate_screen():
    first = "smollm2_1_7b_instruct_q4_k_m"
    second = "qwen2_5_3b_instruct_q4_k_m"
    usage = recovery.cumulative()
    assert usage["new_local_cpu_generations"] == 16
    assert usage["actual_model_inference_wall_seconds"] == pytest.approx(
        159.95704690001094, abs=1e-9
    )
    assert usage["actual_model_inference_wall_seconds_status"] == (
        "KNOWN_COMPLETED_OR_FAILED_HTTP_INTERVALS"
    )
    assert usage["unresolved_in_flight_completion_requests"] == 0
    assert usage["attempts_by_candidate"] == {first: 8, second: 8}
    assert usage["run_count"] == 2
    assert usage["remaining_generations"] == 1184
    assert usage["remaining_inference_wall_seconds"] == pytest.approx(
        71840.04295309998, abs=1e-9
    )
    assert usage["historical_ledger_untouched"] is True

    selection = recovery.selection_status()
    assert selection["status"] == "BOUNDED_SCREEN_NEGATIVE"
    assert selection["selected_candidate"] is None
    assert selection["candidate_1"]["automatic_success"] == 1
    assert selection["candidate_2"]["automatic_success"] == 2
    assert selection["candidate_1"]["integrity_status"] == "PASS"
    assert selection["candidate_2"]["integrity_status"] == "PASS"
    assert selection["candidate_1"]["proceed"] is False
    assert selection["candidate_2"]["proceed"] is False
    with pytest.raises(ValueError, match="Candidate 1 already attempted"):
        recovery.candidate_allowed(first)
    with pytest.raises(ValueError, match="Candidate 2 is not activated"):
        recovery.candidate_allowed(second)

    audit = recovery.audit(second)
    assert audit["attempted"] == audit["replayed_results"] == 8
    assert audit["success"] == 2
    assert audit["threshold"] == 7
    assert audit["proceed"] is False
    assert audit["integrity_status"] == "PASS"

    materialized = recovery.materialized_path(second)
    assert recovery.sha256(materialized) == (
        "591dadd21a2b893a6c327d4d8737da3159a380a5f921049f9d5364a5bc849c43"
    )
    manifest = recovery.load(materialized)
    assert manifest["candidate_id"] == second
    assert manifest["candidate_model_sha256"] == (
        "626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d"
    )
    assert manifest["generation_requests"] == 0
    assert len(manifest["requests"]) == 8
    assert manifest["status"] == "MATERIALIZED_AND_NATIVE_TOKENIZED_NO_COMPLETIONS"


def test_candidate_two_preflight_is_resource_blocked_without_generation():
    receipt_path = recovery.OUT / "candidate2_preflight_attempt_v1.json"
    assert recovery.sha256(receipt_path) == (
        "51047252c9cfc194c882dbe2804b65a9ec710097865bf8e04cf91aa2a9d4c1ed"
    )
    receipt = recovery.load(receipt_path)
    assert receipt["action"] == "preflight"
    assert receipt["candidate_id"] == "qwen2_5_3b_instruct_q4_k_m"
    assert receipt["status"] == "BLOCKED"
    assert receipt["generation_requests_in_failed_action"] == 0
    assert receipt["required_available_physical_bytes"] == 5 * 1024**3
    assert receipt["error_message"] == (
        "RAM preflight failed: available=4746973184 required=5368709120; no inference"
    )
    assert receipt["memory_observation"]["system"]["available_physical"] == 4_737_028_096
    usage = receipt["authorization_usage_observed"]
    assert usage["new_local_cpu_generations"] == 8
    assert usage["actual_model_inference_wall_seconds"] == pytest.approx(
        65.8762855, abs=1e-9
    )
    assert usage["attempts_by_candidate"]["qwen2_5_3b_instruct_q4_k_m"] == 0
    assert usage["historical_ledger_untouched"] is True


def test_runtime_failure_after_eight_results_cannot_select_or_advance(monkeypatch):
    first, second = [row["candidate_id"] for row in recovery.validate_freeze()["candidate_order"]]
    partial = {
        "candidate_id": first,
        "status": "PARTIAL",
        "complete": True,
        "automatic_success": 8,
        "proceed": True,
    }
    monkeypatch.setattr(recovery, "outcome", lambda candidate_id: partial if candidate_id == first else None)
    assert recovery.selection_status() == {
        "status": "STOPPED_INCOMPLETE_CANDIDATE_1",
        "selected_candidate": None,
    }


def test_runtime_failure_in_candidate_two_cannot_qualify(monkeypatch):
    first, second = [row["candidate_id"] for row in recovery.validate_freeze()["candidate_order"]]
    first_failure = {
        "candidate_id": first,
        "status": "PASS",
        "complete": True,
        "automatic_success": 6,
        "proceed": False,
    }
    second_partial = {
        "candidate_id": second,
        "status": "PARTIAL",
        "complete": True,
        "automatic_success": 8,
        "proceed": True,
    }
    monkeypatch.setattr(
        recovery,
        "outcome",
        lambda candidate_id: first_failure if candidate_id == first else second_partial,
    )
    status = recovery.selection_status()
    assert status["status"] == "STOPPED_INCOMPLETE_CANDIDATE_2"
    assert status["selected_candidate"] is None


def test_run_and_audit_require_integrity_valid_terminal_state():
    source = recovery.TOOL.read_text(encoding="utf-8")
    assert '"complete": status == "PASS" and completed == 8' in source
    assert '"proceed": status == "PASS" and completed == 8 and success >= 7' in source
    assert 'events[-1]["kind"] == "run_finished"' in source
    assert 'events[-1]["data"] == summary' in source
    assert 'postflight[0]["status"] == "PASS"' in source
    assert '"authorization_usage_after_run": cumulative()' in source
    assert "Current audit dependency differs from run source" in source
    assert "LOWER_BOUND_WITH_INTERRUPTED_IN_FLIGHT_REQUEST" in source


def test_failed_preflight_receipt_preserves_ram_evidence(monkeypatch):
    usage_before = recovery.cumulative()
    monkeypatch.setattr(
        recovery,
        "memory_observation",
        lambda _pid: {"system": {"available_physical": 123}},
    )
    receipt = recovery._failure_receipt(
        "preflight", "smollm2_1_7b_instruct_q4_k_m", ValueError("RAM preflight failed")
    )
    assert receipt["status"] == "BLOCKED"
    assert receipt["generation_requests_in_failed_action"] == 0
    assert receipt["authorization_usage_observed"] == usage_before
    assert receipt["memory_observation"]["system"]["available_physical"] == 123
    assert receipt["required_available_physical_bytes"] == 3 * 1024**3
    assert receipt["error_message"] == "RAM preflight failed"


def test_frozen_endpoint_separates_current_outdated_wrong_entity_and_unknown():
    plan = recovery.validate_freeze()
    cases = recovery.case_bank()
    case_id = plan["frozen_development_screen"]["cases"][0]["case_id"]
    case = cases[case_id]

    assert recovery.fallback.endpoint(case["aliases"]["current"][0], case) == "CURRENT_VALUE_ADOPTION"
    assert recovery.fallback.endpoint(case["aliases"]["outdated"][0], case) == "OUTDATED_VALUE_ADOPTION"
    other = next(fact for fact in case["facts"] if fact["entity"] != case["speaker_name"])
    assert recovery.fallback.endpoint(other["value"], case) == "WRONG_ENTITY_ANSWER"
    assert recovery.fallback.endpoint("An unsupported response", case) == "UNVERIFIABLE_ANSWER"
    assert recovery.fallback.endpoint("", case) == "EMPTY_RESPONSE"
    assert recovery.fallback.endpoint(None, case) == "MISSING_RECORD"
    assert plan["measurement"]["semantic_policy"].startswith(
        "Automatic exact/alias outcomes are provisional developmental controls"
    )
    assert "Persona Fidelity" in plan["measurement"]["semantic_policy"]


@pytest.mark.parametrize(
    ("answer_state", "expected"),
    [
        ("CURRENT_VALUE_ADOPTION", "Success"),
        ("OUTDATED_VALUE_ADOPTION", "Failure"),
        ("WRONG_ENTITY_ANSWER", "Failure"),
        ("EMPTY_RESPONSE", "Failure"),
        ("MISSING_RECORD", "Missing"),
        ("UNVERIFIABLE_ANSWER", "Uncertain"),
        ("CONTRADICTORY_ANSWER_REQUIRES_REVIEW", "Uncertain"),
    ],
)
def test_automatic_task_labels_preserve_missing_and_uncertain(answer_state, expected):
    assert recovery.automatic_task_label(answer_state) == expected


def test_unknown_endpoint_state_is_not_silently_collapsed_to_failure():
    with pytest.raises(ValueError, match="Unknown frozen endpoint state"):
        recovery.automatic_task_label("NEW_UNREGISTERED_STATE")


def test_persistent_research_state_binds_freeze_and_separate_ledgers():
    state_path = recovery.OUT / "research_state_v1.json"
    state = recovery.load(state_path)

    assert state["research_programme"] == {
        "P0": "FROZEN", "P1": "ACTIVE", "P2": "PAUSED", "P3": "PAUSED",
        "P4": "PAUSED", "P5": "DIAGNOSTIC_COMPLETED", "P6": "PAUSED",
    }
    assert state["current_active_experiment"]["freeze_sha256"] == recovery.FREEZE_SHA256
    refs = state["frozen_artifact_references"]
    assert refs["prospective_feasibility_freeze"]["sha256"] == recovery.sha256(recovery.FREEZE)
    assert refs["autonomous_authorization_ledger"]["sha256"] == recovery.sha256(recovery.LEDGER)
    for name in (
        "candidate_2_blocked_preflight_v2",
        "analysis_reproduction_v1",
        "analysis_reproduction_regression_v1",
        "primary_source_review_addendum_2026_10_18_v1",
        "primary_source_review_addendum_regression_2026_10_18_v1",
    ):
        artifact = refs[name]
        assert artifact["sha256"] == recovery.sha256(Path(artifact["path"]))
    budgets = state["authorization_balances"]
    assert budgets["historical_p1_ledger"] == {
        "authorization": 160,
        "attempted": 80,
        "remaining": 80,
        "policy": "Preserved and not consumed, transferred, or double-counted by the autonomous recovery.",
    }
    autonomous = budgets["autonomous_recovery_ledger"]
    assert autonomous["authorization_id"] == "P1_AUTONOMOUS_MODEL_FEASIBILITY_20261017_V1"
    assert autonomous["generation_limit"] == 1200
    assert autonomous["actual_inference_wall_seconds_limit"] == 72000.0
    literature = state["literature_monitoring"]
    assert literature["status"] == (
        "LAST_SUCCESSFUL_RUN_PRESERVED_CURRENT_SCHEDULER_VISIBILITY_UNVERIFIED_"
        "GITHUB_NOT_DEPLOYED"
    )
    assert literature["last_successful_primary_source_check_date"] == "2026-10-18"
    assert literature["last_successful_scheduled_check_utc"] == "2026-10-18T09:28:51Z"
    assert literature["reviewed_ledger_records"] == 14
    assert literature["structured_review_addendum_records"] == 3
    assert literature["scheduler_historically_verified"] is True
    assert "TASK_NOT_FOUND" in literature["scheduler_current_session_validation"]
    assert state["current_active_experiment"]["latest_formal_preflight"]["classification"] == (
        "FORMAL_VERSIONED_PREFLIGHT_V2_BLOCKED"
    )
    assert state["current_model_configuration"]["status"] == (
        "MATERIALIZED_BUT_BLOCKED_RESOURCE_ZERO_ATTEMPTS"
    )
    receipt = Path(literature["current_checkpoint_receipt"]["path"])
    assert recovery.sha256(receipt) == literature["current_checkpoint_receipt"]["sha256"]
    scorecard = state["publication_readiness_scorecard"]
    assert "overall_score" not in scorecard
    assert set(scorecard["sections"]) == {
        "A_research_question_validity",
        "B_construct_validity",
        "C_experimental_control",
        "D_dataset_independence",
        "E_sample_adequacy",
        "F_evaluation_reliability",
        "G_statistical_credibility",
        "H_baseline_strength",
        "I_generalization_evidence",
        "J_novelty_assessment",
        "K_reproducibility",
        "L_ethics_and_data_availability",
        "M_manuscript_completeness",
    }
    assert scorecard["sections"]["H_baseline_strength"]["status"] == "BLOCKED"
    assert scorecard["sections"]["G_statistical_credibility"]["status"] == "EVIDENCE_INSUFFICIENT"


def test_public_freeze_and_tool_do_not_reference_restricted_review_material():
    state = recovery.OUT / "research_state_v1.json"
    combined = (
        recovery.FREEZE.read_text(encoding="utf-8").lower()
        + recovery.TOOL.read_text(encoding="utf-8").lower()
        + state.read_text(encoding="utf-8").lower()
    )
    assert "restricted/unblinding_key" not in combined
    assert "researcher_unblinding_record" not in combined
    assert "api_token" not in combined
    assert "password" not in combined


def test_candidate_artifact_urls_are_revision_pinned_and_weights_stay_outside_docs():
    for candidate in recovery.validate_freeze()["candidate_order"]:
        artifact = candidate["artifact"]
        assert artifact["repository_revision"] in artifact["resolved_url"]
        assert artifact["filename"] in artifact["resolved_url"]
        assert Path(artifact["local_path"]).parts[0:3] == ("models", "gguf", "feasibility_candidates")
        assert candidate["license"]["weight_staging_policy"] == "Model weights remain ignored and must not enter Git"


def test_materialized_request_hash_contract_is_stable_without_running_tokenizer():
    row = {
        "candidate_id": "fixture",
        "case_id": "case",
        "input_token_ids": [1, 2, 3],
        "messages": [{"role": "user", "content": "fixture"}],
        "order": 0,
    }
    first = recovery.canonical_sha256(row)
    second = recovery.canonical_sha256(json.loads(json.dumps(row)))
    assert first == second
    assert len(first) == 64
