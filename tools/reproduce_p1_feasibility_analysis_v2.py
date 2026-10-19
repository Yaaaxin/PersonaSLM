"""Reproduce the completed two-candidate P1 feasibility analysis without inference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import p1_model_feasibility_recovery as recovery
from reproduce_p1_feasibility_analysis import _sha256, _write_new_atomic


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT = Path("docs/validation/p1/model_feasibility_recovery_v1")
CANDIDATE_1 = "smollm2_1_7b_instruct_q4_k_m"
CANDIDATE_2 = "qwen2_5_3b_instruct_q4_k_m"
EXPECTED_SUCCESS = {CANDIDATE_1: 1, CANDIDATE_2: 2}
EXPECTED_SECONDS = 159.95704690001094
EVIDENCE = {
    "candidate1_run_receipt": (
        OUT / "candidate1_run_receipt_v1.json",
        "541cabb568afe3be0ace249f4a9d24dc507c652f2624e62d6722f70ed8ff3485",
    ),
    "candidate1_audit": (
        OUT / "candidate1_audit_v1.json",
        "d73d16cf9b8ab7b433f4f53ff2b7567d186d88003b3b7a119df5bd439d725921",
    ),
    "candidate2_preflight_v4": (
        OUT / "candidate2_preflight_attempt_v4.json",
        "ca96e25002d5c78f9bf3f15ea6ad0412032bc2ebb3df9adc5b62723417cc9c2d",
    ),
    "candidate2_run_receipt": (
        OUT / "candidate2_run_receipt_v1.json",
        "f9140b58adfcf68e57543cc2452798fc7ac5e9499946fe62f2aeb2a0dc5523e7",
    ),
    "candidate2_audit": (
        OUT / "candidate2_audit_v1.json",
        "e1d2718bd1c5fdd1395329d736ea581c7c03cfdd00d1de8b63bd5a5d771f0984",
    ),
    "selection_after_candidate2": (
        OUT / "selection_after_candidate2_v1.json",
        "362fcac650cc8fe286ac5ade0c5a35fab7ef6d862c0214724b439d0bd8848b7e",
    ),
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _bound_evidence() -> tuple[dict[str, dict], dict[str, dict]]:
    values = {}
    bindings = {}
    for name, (relative, expected_sha256) in EVIDENCE.items():
        path = PROJECT_ROOT / relative
        _require(path.is_file(), f"Missing bound evidence: {relative}")
        _require(_sha256(path) == expected_sha256, f"Bound evidence changed: {relative}")
        values[name] = recovery.load(path)
        bindings[name] = {"path": relative.as_posix(), "sha256": expected_sha256}
    return values, bindings


def _replay(candidate_id: str, archived: dict, receipt: dict) -> dict:
    audit = recovery.audit(candidate_id)
    expected_success = EXPECTED_SUCCESS[candidate_id]
    _require(audit == archived, f"{candidate_id} replay differs from archived audit")
    _require(
        audit["integrity_status"] == audit["status"] == audit["run_status"] == "PASS",
        f"{candidate_id} integrity failed",
    )
    _require(
        audit["attempted"] == audit["replayed_results"] == audit["completion_http_records"] == 8,
        f"{candidate_id} does not have exactly eight attempts/results/HTTP records",
    )
    _require(
        audit["complete"] is True
        and audit["success"] == expected_success
        and audit["threshold"] == 7
        and audit["proceed"] is False,
        f"{candidate_id} gate changed",
    )
    _require(
        receipt["candidate_id"] == candidate_id
        and receipt["status"] == "PASS"
        and receipt["complete"] is True
        and receipt["attempted"] == receipt["completed_results"] == 8
        and receipt["automatic_success"] == expected_success
        and receipt["threshold"] == 7
        and receipt["proceed"] is False
        and receipt["inference_wall_seconds_observed"] == audit["inference_wall_seconds"],
        f"{candidate_id} run receipt differs from replay",
    )
    return {
        "candidate_id": candidate_id,
        "raw_journal_replay": "PASS",
        "attempts": audit["attempted"],
        "result_records": audit["replayed_results"],
        "completion_http_records": audit["completion_http_records"],
        "automatic_success": audit["success"],
        "threshold": audit["threshold"],
        "proceed": audit["proceed"],
        "inference_wall_seconds": audit["inference_wall_seconds"],
    }


def build_report() -> dict:
    """Replay both ignored run journals and publish only aggregate evidence."""
    evidence, bindings = _bound_evidence()
    usage_before = recovery.cumulative()
    candidate_1 = _replay(
        CANDIDATE_1, evidence["candidate1_audit"], evidence["candidate1_run_receipt"]
    )
    candidate_2 = _replay(
        CANDIDATE_2, evidence["candidate2_audit"], evidence["candidate2_run_receipt"]
    )
    selection = recovery.selection_status()
    usage_after = recovery.cumulative()

    _require(
        selection == evidence["selection_after_candidate2"],
        "Current selection differs from the bound post-Candidate-2 archive",
    )
    _require(
        selection["status"] == "BOUNDED_SCREEN_NEGATIVE"
        and selection["selected_candidate"] is None
        and selection["candidate_1"]["automatic_success"] == 1
        and selection["candidate_2"]["automatic_success"] == 2,
        "Bounded selection result changed",
    )

    preflight = evidence["candidate2_preflight_v4"]
    candidate_2_plan = recovery.candidates()[CANDIDATE_2]
    _require(
        preflight["status"] == "PASS"
        and preflight["candidate_id"] == CANDIDATE_2
        and preflight["freeze_sha256"] == recovery.FREEZE_SHA256
        and preflight["authorization_ledger_sha256"] == _sha256(PROJECT_ROOT / recovery.LEDGER)
        and preflight["model_sha256"] == candidate_2_plan["artifact"]["remote_sha256"]
        and preflight["required_available_physical_bytes"]
        == candidate_2_plan["minimum_available_physical_bytes_before_load"]
        and preflight["memory_before"]["system"]["available_physical"]
        >= preflight["required_available_physical_bytes"],
        "Candidate 2 v4 preflight binding changed",
    )

    _require(usage_before == usage_after, "Analysis reproduction changed authorization usage")
    _require(
        usage_after["new_local_cpu_generations"] == 16
        and usage_after["remaining_generations"] == 1184
        and usage_after["actual_model_inference_wall_seconds"] == EXPECTED_SECONDS
        and usage_after["remaining_inference_wall_seconds"] == 72000.0 - EXPECTED_SECONDS
        and usage_after["attempts_by_candidate"] == {CANDIDATE_1: 8, CANDIDATE_2: 8}
        and usage_after["unresolved_in_flight_completion_requests"] == 0
        and usage_after["historical_ledger_untouched"] is True,
        "Autonomous authorization reconstruction changed",
    )
    ledger = recovery.load(recovery.LEDGER)
    historical = ledger["historical_ledger_separation"]
    _require(
        (
            historical["historical_attempted"],
            historical["historical_authorization"],
            historical["historical_remaining"],
        )
        == (80, 160, 80),
        "Historical P1 ledger changed",
    )

    return {
        "version": "p1_feasibility_analysis_reproduction_v2",
        "analysis_code": {
            "path": "tools/reproduce_p1_feasibility_analysis_v2.py",
            "sha256": _sha256(Path(__file__)),
        },
        "evidence_bindings": bindings,
        "local_private_archive_replay": {
            "status": "PASS",
            "candidates": [candidate_1, candidate_2],
            "restricted_record_content_exported": False,
        },
        "selection": {
            "status": selection["status"],
            "selected_candidate": selection["selected_candidate"],
            "candidate_1_success": 1,
            "candidate_2_success": 2,
            "qualification_threshold": 7,
        },
        "authorization": {
            "autonomous": {
                "authorization_id": usage_after["authorization_id"],
                "consumed_generations": usage_after["new_local_cpu_generations"],
                "generation_limit": 1200,
                "remaining_generations": usage_after["remaining_generations"],
                "actual_model_inference_wall_seconds": usage_after[
                    "actual_model_inference_wall_seconds"
                ],
                "inference_wall_seconds_limit": 72000.0,
                "remaining_inference_wall_seconds": usage_after[
                    "remaining_inference_wall_seconds"
                ],
                "attempts_by_candidate": usage_after["attempts_by_candidate"],
            },
            "historical": {
                "attempted": historical["historical_attempted"],
                "authorization": historical["historical_authorization"],
                "remaining": historical["historical_remaining"],
                "untouched": usage_after["historical_ledger_untouched"],
            },
        },
        "reproduction_boundaries": {
            "analysis_reproduction": "PASS_LOCAL_PRIVATE_ARCHIVE",
            "generation_reproduction": "NOT_RUN",
            "public_clone_only_full_reproduction": "PARTIAL_RAW_JOURNALS_AND_WEIGHTS_REQUIRED",
        },
        "execution_impact": {
            "scientific_model_generations": 0,
            "model_inference_wall_seconds": 0,
            "network_calls": 0,
            "authorization_usage_before_equals_after": True,
            "historical_outputs_modified": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = build_report()
    if arguments.output is not None:
        _write_new_atomic(arguments.output, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
