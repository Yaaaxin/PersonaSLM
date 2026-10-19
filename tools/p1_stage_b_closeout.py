"""Offline audit and closeout helpers for the authorized P1 Stage B run.

This module never starts a model service and never performs inference.  It
reconstructs the immutable journal, frozen exact/alias scores, claims, attempts,
budget and provenance of the one authorized Stage B run.
"""

import argparse
from collections import Counter
from pathlib import Path
import json
import statistics

from personaslm.journal import read_events

import p1_conditional_execution as execution
import p1_recovery_v2 as recovery
import p1_temporal_fallback as fallback


s = recovery.s
RUN_ID = "20261016T211841-ca844dad54ba434e87904cffed817a43"
RUN = Path("results/p1_conditional_sfh/v1/runs") / RUN_ID
STAGE = Path("docs/validation/p1/stage_b_v1")
INDEX = Path("docs/validation/p1/blinded_audit_stage_a_v1/manifest_index_frozen_v1.json")
DECISION = STAGE / "stage_b_decision_record_v1.json"
UNBLINDING = STAGE / "researcher_unblinding_record_v1.json"
EVIDENCE = STAGE / "stage_b_execution_evidence_v1.json"
CLAIM_ROOT = Path("results/p1_measurement_pilot/v1/claims")
ATTEMPT_ROOT = Path("results/p1_measurement_pilot/v1/attempts")


def event_index(events, kind):
    return [event for event in events if event["kind"] == kind]


def audit():
    manifest = s.load(RUN / "manifest.json")
    summary = s.load(RUN / "summary.json")
    events = read_events(RUN)
    kinds = Counter(event["kind"] for event in events)
    s.require(events and events[-1]["kind"] == "run_finished", "Run has no terminal event")
    s.require(not event_index(events, "failure"), "Stage B journal contains a failure event")
    s.require(summary["status"] == "AUTOMATIC DEVELOPMENT GATE NOT PASSED", "Unexpected Stage B status")
    s.require(summary["branch"] == "B" and summary["attempted"] == summary["results"] == 8, "Unexpected Stage B inventory")
    s.require(summary["retries"] == 0, "Retry detected")
    s.require(manifest["git_head"] == "c40667ad266082481b1850453f67784b593f3723", "Execution Git HEAD mismatch")

    registration = manifest["registration"]
    s.require(registration["decision"]["branch"] == "B", "Run branch differs from unblinding decision")
    s.require(registration["decision"]["selected_configuration"] is None, "Unexpected selected O/Q configuration")
    s.require(registration["persisted_unblinding_sha256"] == s.sha256(UNBLINDING), "Unblinding binding mismatch")
    s.require(registration["persisted_decision_sha256"] == s.sha256(DECISION), "Decision binding mismatch")

    snapshot_mismatches = []
    current_source_mismatches = []
    for path, expected in registration["source_sha256"].items():
        snapshot = RUN / "source_snapshot" / path
        if not snapshot.is_file() or s.sha256(snapshot) != expected:
            snapshot_mismatches.append(path)
        if not Path(path).is_file() or s.sha256(Path(path)) != expected:
            current_source_mismatches.append(path)
    s.require(not snapshot_mismatches, "Run source snapshot mismatch")
    s.require(not current_source_mismatches, "Bound source changed after inference")

    index = s.load(INDEX)
    calibration_entry = index["manifests"]["fallback_calibration"]
    pilot_entry = index["manifests"]["minimal_temporal"]
    calibration_path = Path(calibration_entry["path"])
    pilot_path = Path(pilot_entry["path"])
    s.require(s.sha256(calibration_path) == calibration_entry["sha256"], "Calibration manifest changed")
    s.require(s.sha256(pilot_path) == pilot_entry["sha256"], "Conditional pilot manifest changed")
    calibration_plan = s.load(calibration_path)
    pilot_plan = s.load(pilot_path)
    s.require(len(calibration_plan["requests"]) == 8 and len(pilot_plan["requests"]) == 80, "Manifest request inventory")
    expected_ids = [request["request_id"] for request in calibration_plan["requests"]]
    pilot_ids = {request["request_id"] for request in pilot_plan["requests"]}

    claims = sorted(CLAIM_ROOT.glob("P1_STAGE_B_V1_*.json"))
    s.require([path.name for path in claims] == ["P1_STAGE_B_V1_fallback_calibration.json"], "Unexpected Stage B claim inventory")
    claim = s.load(claims[0])
    s.require(claim["request_ids"] == expected_ids and claim["maximum_attempts"] == 8, "Calibration claim mismatch")
    s.require(claim["manifest_sha256"] == calibration_entry["sha256"] and claim["branch"] == "B", "Claim provenance mismatch")

    attempt_paths = [ATTEMPT_ROOT / (request_id + ".json") for request_id in expected_ids]
    s.require(all(path.is_file() for path in attempt_paths), "Missing calibration attempt")
    attempts = [s.load(path) for path in attempt_paths]
    s.require([row["request_id"] for row in attempts] == expected_ids, "Attempt order/inventory mismatch")
    s.require(all(row["category"] == "C_DIAGNOSTIC" for row in attempts), "Wrong calibration budget category")
    s.require(not any((ATTEMPT_ROOT / (request_id + ".json")).exists() for request_id in pilot_ids), "Conditional pilot was unexpectedly attempted")

    started = event_index(events, "p1_generation_started")
    raw = event_index(events, "p1_raw_generation")
    results = event_index(events, "p1_result")
    scores = event_index(events, "provisional_automatic_score")
    gates = event_index(events, "provisional_execution_gate")
    s.require(len(started) == len(raw) == len(results) == len(scores) == 8 and len(gates) == 1, "Incomplete result chain")
    s.require([event["data"]["request_id"] for event in started] == expected_ids, "Generation order changed")
    s.require(kinds["live_prompt_verified"] == 88, "Not all branch prompts received live-token verification")
    s.require(max(event["sequence"] for event in event_index(events, "live_prompt_verified")) < started[0]["sequence"], "Generation began before live-token verification completed")

    bank = s.load(fallback.OUT / "bank_frozen_v1.json")
    cases = {case["case_id"]: case for case in bank["cases"] if case["pool"] == "fallback_calibration"}
    result_by_id = {event["data"]["request_id"]: event["data"] for event in results}
    raw_by_id = {event["data"]["request_id"]: event["data"] for event in raw}
    score_by_id = {event["data"]["request_id"]: event["data"] for event in scores}
    rows = []
    for request in calibration_plan["requests"]:
        request_id = request["request_id"]
        case_id = request["case_id"]
        result = result_by_id[request_id]
        wire = raw_by_id[request_id]
        score = score_by_id[request_id]
        text = result["raw_response"]
        state = fallback.endpoint(text, cases[case_id])
        expected_task = "Success" if state == "CURRENT_VALUE_ADOPTION" else "Failure" if state in (
            "OUTDATED_VALUE_ADOPTION", "WRONG_ENTITY_ANSWER", "EMPTY_RESPONSE"
        ) else "Missing" if state == "MISSING_RECORD" else "Uncertain"
        s.require(score["full_score"]["answer_state"] == state and score["task_success"] == expected_task, "Frozen scorer replay mismatch")
        s.require(score["raw_output_sha256"] == s.th(text) == result["raw_text_sha256"], "Raw-output hash mismatch")
        s.require(result["request_sha256"] == request["request_sha256"], "Request hash mismatch")
        s.require(wire["response"]["content"] == text, "Raw HTTP/result mismatch")
        s.require(result["input_token_audit"]["count_matches"] and result["input_token_audit"]["truncated"] is False, "Input-token integrity failure")
        rows.append({
            "case_id": case_id,
            "request_id": request_id,
            "task_success": expected_task,
            "answer_state": state,
            "raw_output_sha256": score["raw_output_sha256"],
            "request_sha256": result["request_sha256"],
            "structural_status": result["response_status"]["status"],
            "semantic_completeness": result["response_status"]["semantic_completeness"],
            "stop_reason": result["stop_reason"],
            "input_tokens": result["input_token_audit"]["sent_tokens"],
            "generated_tokens": result["generated_tokens"],
            "latency_seconds": result["latency_seconds"],
        })

    states = Counter(row["answer_state"] for row in rows)
    task_success = sum(row["task_success"] == "Success" for row in rows)
    gate = gates[0]["data"]
    s.require(task_success == 6 and states == {"CURRENT_VALUE_ADOPTION": 6, "OUTDATED_VALUE_ADOPTION": 2}, "Unexpected calibration result")
    s.require(gate["stage"] == "fallback_calibration" and gate["threshold"] == 7 and gate["denominator"] == 8, "Wrong calibration gate")
    s.require(gate["automatic_success"] == 6 and gate["proceed"] is False, "Calibration gate arithmetic")
    s.require(gate["researcher_review_status"] == "PENDING", "Automatic gate was silently adjudicated")

    preflight = event_index(events, "preflight")[0]["data"]
    s.require(preflight["status"] == "PASS", "Saved inference preflight failed")
    minimum_ram = 3 * 1024 ** 3
    available_ram = preflight["memory_before"]["system"]["available_physical"]
    s.require(available_ram >= minimum_ram, "Saved RAM preflight below threshold")
    plan = manifest["plans"][0]
    identity = s.b.file_preflight(s.config(plan))
    s.require(identity["status"] == "PASS" and identity["model"]["sha256"] == preflight["identity"]["model"]["sha256"], "Current model identity mismatch")
    s.require(identity["server"]["sha256"] == preflight["identity"]["server"]["sha256"], "Current backend identity mismatch")

    memory = [event["data"] for event in event_index(events, "memory_observation") if "system" in event["data"]]
    latencies = [row["latency_seconds"] for row in rows]
    ledger = recovery.old.cumulative()
    expected_ledger = {
        "attempted": {"A_C0": 32, "B_FACTORIAL": 0, "C_DIAGNOSTIC": 48},
        "remaining_authorization": {"A_C0": 0, "B_FACTORIAL": 80, "C_DIAGNOSTIC": 0},
        "total_attempted": 80,
        "total_remaining": 80,
    }
    for key, value in expected_ledger.items():
        s.require(ledger[key] == value and summary["ledger"][key] == value, "Authorization ledger mismatch: " + key)

    return {
        "version": "p1_stage_b_execution_evidence_v1",
        "scope": "Authorized P1 development fallback calibration; offline reconstruction, not human adjudication or confirmatory inference",
        "run": {
            "run_id": RUN_ID,
            "path": RUN.as_posix(),
            "manifest_sha256": s.sha256(RUN / "manifest.json"),
            "summary_sha256": s.sha256(RUN / "summary.json"),
            "journal_integrity": "PASS",
            "events": len(events),
            "event_kind_counts": dict(sorted(kinds.items())),
            "status": summary["status"],
            "branch": "B",
            "attempted": 8,
            "results": 8,
            "retries": 0,
        },
        "preflight": {
            "status": "PASS",
            "checked_software_utc": preflight["checked_software_utc"],
            "available_physical_bytes": available_ram,
            "required_physical_bytes": minimum_ram,
            "deficit_bytes": 0,
            "model_sha256": preflight["identity"]["model"]["sha256"],
            "backend_sha256": preflight["identity"]["server"]["sha256"],
            "live_prompt_token_arrays_verified": kinds["live_prompt_verified"],
            "live_runtime_build": event_index(events, "effective_server_defaults")[0]["data"]["validation"]["build_info"],
        },
        "unblinding_and_selection": {
            "unblinding_sha256": s.sha256(UNBLINDING),
            "decision_sha256": s.sha256(DECISION),
            "selected_configuration": None,
            "selected_branch": "B",
            "first_manifest_path": calibration_entry["path"],
            "first_manifest_sha256": calibration_entry["sha256"],
            "conditional_pilot_path": pilot_entry["path"],
            "conditional_pilot_sha256": pilot_entry["sha256"],
        },
        "calibration_gate": {
            "scorer": "p1_temporal_fallback.endpoint; frozen exact current alias only is Success",
            "threshold": 7,
            "denominator": 8,
            "automatic_success": task_success,
            "decision": gate["decision"],
            "proceed": False,
            "answer_states": dict(sorted(states.items())),
            "researcher_review_status": "PENDING",
            "rows": rows,
        },
        "measurement_status": {
            "missing_calibration_outputs": 0,
            "empty_calibration_outputs": sum(not result_by_id[row["request_id"]]["raw_response"] for row in rows),
            "all_units_identifiable": all(result_by_id[row["request_id"]]["response_status"]["unit_identifiable"] for row in rows),
            "structural_status": dict(Counter(row["structural_status"] for row in rows)),
            "semantic_completeness": "PENDING_RESEARCHER_REVIEW; EOS and one recognized identifier do not independently establish semantic completeness",
            "factual_correctness": "NOT_INDEPENDENTLY_SCORED; the two failed exact endpoints emitted trusted historical values that are outdated for the requested date",
            "temporal_correctness": "PROVISIONAL_EXACT_ENDPOINT: 6 current-value adoptions and 2 outdated-value adoptions",
            "response_relevance": "NOT_INDEPENDENTLY_SCORED",
            "conversational_coherence": "NOT_INDEPENDENTLY_SCORED",
            "linguistic_persona_fidelity": "NOT_APPLICABLE",
            "behavioral_persona_fidelity": "NOT_APPLICABLE",
        },
        "performance": {
            "latency_seconds_total": sum(latencies),
            "latency_seconds_mean": statistics.mean(latencies),
            "latency_seconds_median": statistics.median(latencies),
            "latency_seconds_min": min(latencies),
            "latency_seconds_max": max(latencies),
            "input_tokens_total": sum(row["input_tokens"] for row in rows),
            "generated_tokens_total": sum(row["generated_tokens"] for row in rows),
            "stop_reasons": dict(Counter(row["stop_reason"] for row in rows)),
            "memory_samples": len(memory),
            "minimum_available_physical_bytes_during_model_residence": min(row["system"]["available_physical"] for row in memory),
            "maximum_sampled_working_set_bytes": max(row["process"]["working_set"] for row in memory),
            "maximum_reported_peak_working_set_bytes": max(row["process"]["peak_working_set"] for row in memory),
        },
        "authorization": {
            "ledger": ledger,
            "new_generations": 8,
            "remaining_development_budget": 80,
            "remaining_budget_execution_status": "UNUSED_AND_BLOCKED_BY_FAILED_REGISTERED_CALIBRATION_GATE",
            "minimal_temporal_pilot_attempts": 0,
            "minimal_temporal_pilot_ungenerated": 80,
        },
        "analysis": {
            "full_factorial_pilot_completed": False,
            "factorial_contrasts": "NOT_ESTIMABLE",
            "reason": "The registered 7/8 fallback calibration gate failed at 6/8, so all 80 minimal-temporal S/F/H pilot requests remained ungenerated.",
            "model_feasibility": "The fixed model/format produced exact current values in 6/8 calibration cases and adopted an outdated value in 2/8. It did not meet the prespecified 7/8 readiness control; this small development result is not proof of general model incapability.",
        },
        "integrity": {
            "source_snapshots": len(registration["source_sha256"]),
            "source_snapshot_mismatches": snapshot_mismatches,
            "current_bound_source_mismatches": current_source_mismatches,
            "claims": [path.as_posix() for path in claims],
            "attempt_files": [path.as_posix() for path in attempt_paths],
            "conditional_pilot_attempt_detected": False,
        },
    }


def write_evidence():
    s.require(not EVIDENCE.exists(), "Refusing to overwrite Stage B execution evidence")
    payload = audit()
    s.save(EVIDENCE, payload)
    return {"status": "PASS", "path": EVIDENCE.as_posix(), "sha256": s.sha256(EVIDENCE)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["audit", "evidence"])
    arguments = parser.parse_args()
    result = audit() if arguments.action == "audit" else write_evidence()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
