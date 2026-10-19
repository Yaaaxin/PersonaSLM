"""Versioned tests and reproducibility checkpoint for P1 Stage B.

No action in this module starts a model server or performs inference.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

import p1_stage_b_closeout as closeout


s = closeout.s
ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "docs/validation/p1/stage_b_v1"
TEST_EVIDENCE = STAGE / "regression_test_evidence_v1.json"
REPORT = ROOT / "docs/P1_stage_B_unblinding_and_conditional_execution_report_v1.md"
LOG = ROOT / "docs/research_development_log.md"
PREVIOUS_REPRO = STAGE / "reproducibility_manifest_v1.json"
REPRO = STAGE / "reproducibility_manifest_v2.json"


TEST_TARGETS = [
    "tests/test_p1_stage_b_execution_v2.py",
    "tests/test_p1_stage_b_closeout.py",
    "tests/test_p1_temporal_date_binding.py",
    "tests/test_p1_native_stop_diagnostic.py",
    "tests/test_p1_researcher_audit_integration.py::test_actual_v3_researcher_submission_validates_without_unblinding_key_access",
    "tests/test_p1_researcher_audit_integration.py::test_date_audit_uses_anonymous_ids_and_component_dates",
    "tests/test_p1_researcher_audit_integration.py::test_compatibility_view_preserves_labels_without_opening_actual_key",
    "tests/test_p1_researcher_audit_integration.py::test_proposal_comparison_keeps_all_submitted_researcher_values",
    "tests/test_p1_researcher_audit_integration.py::test_build_artifacts_does_not_unblind_or_generate",
    "tests/test_p1_researcher_audit_integration.py::test_scoring_audit_records_no_registered_date_substitution",
    "tests/test_p1_researcher_audit_integration.py::test_expected_hash_mismatch_is_rejected",
    "tests/test_p1_blinded_stage_a.py::test_actual_blinded_sheet_has_no_scores_conditions_or_filled_human_fields",
    "tests/test_p1_blinded_stage_a.py::test_incomplete_actual_blank_sheet_rejected_without_unblinding",
    "tests/test_p1_blinded_stage_a.py::test_human_label_rules_with_synthetic_fixtures",
    "tests/test_p1_blinded_stage_a.py::test_review_integrity_rejects_tampering",
    "tests/test_p1_blinded_stage_a.py::test_frozen_mapping_preserves_partial_unknown_and_fixed_priority",
    "tests/test_p1_blinded_stage_a.py::test_quoted_or_missing_activation_never_reaches_inference",
    "tests/test_p1_blinded_stage_a.py::test_provisional_gates_full_denominator_and_threshold",
    "tests/test_p1_blinded_stage_a.py::test_mutually_exclusive_branch_budgets",
    "tests/test_p1_blinded_stage_a.py::test_factor_corruption_rejected_before_any_inference",
]


HISTORICAL_STATE_ASSERTIONS_NOT_RERUN = {
    "tests/test_p1_blinded_stage_a.py::test_all_frozen_candidates_actual_tokens_and_disjoint_materials": "Asserts no Stage B run and historical 72/88 ledger; superseded by the authorized post-run validator.",
    "tests/test_p1_measurement_pilot.py::test_actual_cumulative_scope_includes_later_oq_recovery": "Asserts the pre-Stage-B A32/B0/C40 ledger.",
    "tests/test_p1_recovery_measurement_v2.py::test_completed_inventory_and_no_unapproved_generation": "Asserts the pre-Stage-B 72-attempt inventory.",
    "tests/test_p1_recovery_2x2.py::test_frozen_eligible_scope_and_no_d0_generation": "Contains a historical no-Stage-B-generation state assertion.",
    "tests/test_p1_recovery_v2.py::test_transport_preserves_global_duplicate_and_quota_guards": "Uses the historical pre-Stage-B cumulative allocation state.",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT, text=True).strip()


def run_tests():
    s.require(closeout.EVIDENCE.is_file(), "Stage B execution evidence is absent")
    s.require(not TEST_EVIDENCE.exists(), "Refusing to overwrite Stage B regression evidence")
    command = [sys.executable, "-B", "-m", "pytest", *TEST_TARGETS, "-q", "-ra", "-p", "no:cacheprovider"]
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    started = utc_now()
    result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
    payload = {
        "version": "p1_stage_b_regression_test_evidence_v1",
        "started_utc": started,
        "finished_utc": utc_now(),
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "scope": "Post-Stage-B offline regression only; no model service or inference. New post-run tests replace historical assertions that Stage B had not yet run.",
        "historical_state_assertions_not_rerun": HISTORICAL_STATE_ASSERTIONS_NOT_RERUN,
        "stage_b_execution_evidence_sha256": s.sha256(closeout.EVIDENCE),
    }
    s.save(TEST_EVIDENCE, payload)
    if result.returncode:
        raise RuntimeError("Stage B regression suite failed; evidence was preserved")
    return {"status": "PASS", "path": TEST_EVIDENCE.relative_to(ROOT).as_posix(), "sha256": s.sha256(TEST_EVIDENCE), "stdout": result.stdout.strip()}


def build_manifest():
    s.require(not REPRO.exists(), "Refusing to overwrite Stage B reproducibility manifest")
    s.require(REPORT.is_file() and LOG.is_file() and TEST_EVIDENCE.is_file(), "Report, log or test evidence is absent")
    test = s.load(TEST_EVIDENCE)
    s.require(test["returncode"] == 0, "Stage B regression evidence is not passing")
    execution = closeout.audit()

    paths = [
        ROOT / "AGENTS.md",
        ROOT / "docs/research_protocol_v1.1.md",
        ROOT / "docs/research_protocol_v1.1_language_scope_addendum.md",
        ROOT / "docs/P1_research_recovery_and_stage_B_readiness_report_v1.md",
        ROOT / "docs/validation/p1/blinded_audit_stage_a_v1/stage_policy_frozen_v1.json",
        ROOT / "docs/validation/p1/blinded_audit_stage_a_v1/manifest_index_frozen_v1.json",
        ROOT / "docs/validation/p1/blinded_audit_stage_a_v1/execution_tools_frozen_v1.json",
        ROOT / "docs/validation/p1/blinded_audit_stage_a_v1/execution_binding_reconciliation_v2.json",
        ROOT / "docs/validation/p1/researcher_audit_integration_v1/researcher_annotation_import_v1.json",
        ROOT / "docs/validation/p1/researcher_audit_integration_v1/researcher_annotation_stage_a_compatibility_v1.csv",
        ROOT / "docs/validation/p1/researcher_audit_integration_v1/automatic_scorer_date_usage_audit_v2.json",
        ROOT / "docs/validation/p1/blinded_audit_stage_a_v1/blinded_researcher_audit_v1.csv",
        ROOT / "docs/validation/p1/blinded_audit_stage_a_v1/blinded_researcher_audit_RESEARCHER_FILLED_DATE_RULE_v3.csv",
        ROOT / "docs/validation/p1/blinded_audit_stage_a_v1/PersonaSLM_six_proposals_NOT_APPLIED_v3.csv",
        ROOT / "docs/validation/p1/stage_b_v1/researcher_activation_source_v1.txt",
        ROOT / "docs/validation/p1/stage_b_v1/researcher_unblinding_record_v1.json",
        ROOT / "docs/validation/p1/stage_b_v1/stage_b_decision_record_v1.json",
        ROOT / closeout.EVIDENCE,
        TEST_EVIDENCE,
        REPORT,
        LOG,
        ROOT / "tools/p1_conditional_execution.py",
        ROOT / "tools/p1_conditional_execution_v2.py",
        ROOT / "tools/p1_stage_b_closeout.py",
        ROOT / "tools/p1_stage_b_finalize.py",
        ROOT / "tools/p1_temporal_fallback.py",
        ROOT / "tests/test_p1_stage_b_execution_v2.py",
        ROOT / "tests/test_p1_stage_b_closeout.py",
        PREVIOUS_REPRO,
    ]
    index = s.load(ROOT / "docs/validation/p1/blinded_audit_stage_a_v1/manifest_index_frozen_v1.json")
    for entry in index["manifests"].values():
        paths.append(ROOT / entry["path"])
    s.require(all(path.is_file() for path in paths), "Checkpoint input file missing")

    run_root = ROOT / closeout.RUN
    run_files = sorted(path for path in run_root.rglob("*") if path.is_file())
    claim = ROOT / "results/p1_measurement_pilot/v1/claims/P1_STAGE_B_V1_fallback_calibration.json"
    attempt_files = [ROOT / path for path in execution["integrity"]["attempt_files"]]
    payload = {
        "version": "p1_stage_b_reproducibility_checkpoint_v2",
        "created_utc": utc_now(),
        "researcher": "Yaxin ZHENG",
        "phase": "P1_ACTIVE_DEVELOPMENT",
        "predecessor": {
            "path": PREVIOUS_REPRO.relative_to(ROOT).as_posix(),
            "sha256": s.sha256(PREVIOUS_REPRO),
            "status": "SUPERSEDED_BY_V2",
            "reason": "V2 records the disclosed first-manifest path-normalization failure, its fix, and directly indexes the blank and compatibility reviewer files. V1 remains preserved."
        },
        "git": {
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "status_porcelain": git("status", "--short"),
        },
        "artifact_sha256": {path.relative_to(ROOT).as_posix(): s.sha256(path) for path in dict.fromkeys(paths)},
        "run_artifact_sha256": {path.relative_to(ROOT).as_posix(): s.sha256(path) for path in run_files},
        "claim_sha256": {claim.relative_to(ROOT).as_posix(): s.sha256(claim)},
        "attempt_sha256": {path.relative_to(ROOT).as_posix(): s.sha256(path) for path in attempt_files},
        "restricted_unblinding_material": {
            "path": "docs/validation/p1/blinded_audit_stage_a_v1/restricted/unblinding_key_v1.json",
            "sha256": "8ab628c1a74a7fbb3f09c0a8f266359ab32d6c9835db39f4afe3406647dc896f",
            "commit_guidance": "Keep restricted; do not include through indiscriminate staging."
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "model_sha256": execution["preflight"]["model_sha256"],
            "backend_sha256": execution["preflight"]["backend_sha256"],
            "runtime_build": execution["preflight"]["live_runtime_build"],
        },
        "scientific_checkpoint": {
            "unblinding_integrity": "PASS_32_TO_32_BIJECTION",
            "condition_results": s.load(ROOT / closeout.DECISION)["condition_results"],
            "selected_branch": "B",
            "new_generations": 8,
            "fallback_calibration": "6/8; REGISTERED_7_OF_8_GATE_NOT_PASSED",
            "minimal_temporal_pilot_generations": 0,
            "factorial_contrasts": "NOT_ESTIMABLE",
            "remaining_budget": 80,
            "remaining_budget_status": "UNUSED_AND_BLOCKED_BY_FAILED_REGISTERED_GATE",
            "researcher_review_of_new_outputs": "PENDING",
            "confirmatory_status": "NOT_CONFIRMATORY",
        },
        "tests": {
            "evidence_path": TEST_EVIDENCE.relative_to(ROOT).as_posix(),
            "evidence_sha256": s.sha256(TEST_EVIDENCE),
            "returncode": 0,
            "historical_state_assertions_not_rerun": HISTORICAL_STATE_ASSERTIONS_NOT_RERUN,
        },
        "controls": {
            "git_commit_or_push": False,
            "model_or_backend_changed": False,
            "prompt_or_manifest_changed": False,
            "retry_count": 0,
            "training_or_lora": False,
            "paused_phase_execution": False,
        },
        "programme_status": {
            "P0": "FROZEN",
            "P1": "ACTIVE; Stage B stopped at failed fallback calibration gate",
            "P2": "PAUSED",
            "P3": "PAUSED",
            "P4": "PAUSED",
            "P5": "DIAGNOSTIC_COMPLETED_ARCHIVED",
            "P6": "PAUSED",
        },
    }
    s.save(REPRO, payload)
    return {"status": "PASS", "path": REPRO.relative_to(ROOT).as_posix(), "sha256": s.sha256(REPRO), "run_files": len(run_files)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["test", "manifest"])
    arguments = parser.parse_args()
    result = run_tests() if arguments.action == "test" else build_manifest()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
