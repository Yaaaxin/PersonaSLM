"""Candidate 2 disjoint C0 controller; never executes the remaining 72 requests."""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time


sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path("tools").resolve()))

import p1_candidate2_pilot_materialization as pilot  # noqa: E402
import p1_model_feasibility_recovery as recovery  # noqa: E402
from personaslm.inference import LlamaClient, normalize_result  # noqa: E402
from personaslm.journal import RunJournal, atomic_json, read_events, utc_now  # noqa: E402
from personaslm.observations import memory_observation  # noqa: E402
from personaslm.p1b_calibration import writer_lock  # noqa: E402
from personaslm.server import validate_server_properties  # noqa: E402


CANDIDATE = pilot.CANDIDATE
ROOT = Path("results/p1_candidate2_disjoint_pilot/v1")
READINESS = recovery.OUT / "candidate2_c0_controller_readiness_v1.json"
TOOL = Path("tools/p1_candidate2_c0_controller.py")
RAM_BYTES = 5 * 1024**3
MAX_COMPLETION_SECONDS = 2700.0
MATERIALIZATION_SHA256 = "44f6f1991c03c8fae23e743099cafe5b8ceb1fd95f50b942878679e90f3b47cf"
C0_THRESHOLD = 6


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def completion_account(events: list[dict]) -> tuple[float, int]:
    requests = sum(
        event["kind"] == "http_request" and event["data"].get("route") == "/completion"
        for event in events
    )
    terminals = sum(
        event["kind"] in ("http_response", "http_error")
        and event["data"].get("route") == "/completion"
        for event in events
    )
    require(terminals <= requests, "Pilot completion terminal has no request")
    seconds = sum(
        float(event["data"].get("elapsed_seconds", 0.0))
        for event in events
        if event["kind"] in ("http_response", "http_error")
        and event["data"].get("route") == "/completion"
    )
    return seconds, requests - terminals


def combined_cumulative() -> dict:
    screen = recovery.cumulative()
    artifact = recovery.load(pilot.DESTINATION)
    require(recovery.sha256(pilot.DESTINATION) == MATERIALIZATION_SHA256,
            "Candidate 2 pilot materialization hash changed")
    requests = {row["request_id"]: row for row in artifact["requests"]}
    allowed = set(artifact["execution_blocks"]["c0_gate"]["request_ids"])
    attempt_paths = sorted((ROOT / "attempts").glob("*.json")) if (ROOT / "attempts").exists() else []
    attempts = [recovery.load(path) for path in attempt_paths]
    ids = [row["request_id"] for row in attempts]
    require(len(ids) == len(set(ids)), "Duplicate Candidate 2 C0 attempt")
    require(all(row["authorization_id"] == screen["authorization_id"] for row in attempts),
            "Pilot attempt belongs to another parent authorization")
    require(all(row["authorization_namespace"] == pilot.NAMESPACE for row in attempts),
            "Pilot attempt belongs to another namespace")
    require(all(row["candidate_id"] == CANDIDATE and row["request_id"] in allowed for row in attempts),
            "Pilot attempt is not an allowed C0 request")
    require(all(row["request_sha256"] == requests[row["request_id"]]["request_sha256"] for row in attempts),
            "Pilot attempt request binding changed")
    require(len(attempts) <= 8, "Candidate 2 C0 attempt ceiling exceeded")

    pilot_seconds = 0.0
    pilot_unresolved = 0
    run_count = 0
    if (ROOT / "runs").exists():
        for folder in sorted((ROOT / "runs").iterdir()):
            if folder.is_dir():
                seconds, unresolved = completion_account(read_events(folder))
                pilot_seconds += seconds
                pilot_unresolved += unresolved
                run_count += 1
    hard = recovery.load(recovery.LEDGER)["hard_limits"]
    generations = screen["new_local_cpu_generations"] + len(attempts)
    seconds = screen["actual_model_inference_wall_seconds"] + pilot_seconds
    unresolved = screen["unresolved_in_flight_completion_requests"] + pilot_unresolved
    require(generations <= hard["new_local_cpu_generations"], "Global autonomous generation ceiling exceeded")
    require(seconds <= hard["actual_model_inference_wall_seconds"] + 1e-6,
            "Global autonomous inference-time ceiling exceeded")
    return {
        "authorization_id": recovery.load(recovery.LEDGER)["authorization_id"],
        "new_local_cpu_generations": generations,
        "actual_model_inference_wall_seconds": seconds,
        "unresolved_in_flight_completion_requests": unresolved,
        "remaining_generations": hard["new_local_cpu_generations"] - generations,
        "remaining_inference_wall_seconds": (
            hard["actual_model_inference_wall_seconds"] - seconds if unresolved == 0 else None
        ),
        "screen_generations": screen["new_local_cpu_generations"],
        "pilot_c0_generations": len(attempts),
        "screen_inference_wall_seconds": screen["actual_model_inference_wall_seconds"],
        "pilot_c0_inference_wall_seconds": pilot_seconds,
        "pilot_run_count": run_count,
        "historical_ledger_untouched": screen["historical_ledger_untouched"],
    }


def require_selected(selection: dict | None = None) -> dict:
    selection = selection or recovery.selection_status()
    require(
        selection.get("status") == "QUALIFIED"
        and selection.get("selected_candidate") == CANDIDATE
        and selection.get("gate", {}).get("status") == "PASS"
        and selection.get("gate", {}).get("complete") is True
        and selection.get("gate", {}).get("automatic_success", -1) >= 7
        and selection.get("gate", {}).get("integrity_status") == "PASS",
        "Candidate 2 is not a complete integrity-valid qualifying selected configuration",
    )
    return selection


def c0_requests(artifact: dict | None = None) -> list[dict]:
    artifact = artifact or recovery.load(pilot.DESTINATION)
    by_id = {row["request_id"]: row for row in artifact["requests"]}
    ids = artifact["execution_blocks"]["c0_gate"]["request_ids"]
    require(len(ids) == len(set(ids)) == 8, "C0 request ID inventory changed")
    require(set(ids).issubset(by_id), "C0 request ID missing from materialization")
    rows = [by_id[request_id] for request_id in ids]
    require(all(row["condition"] == "C0" for row in rows), "Non-C0 request selected for gate")
    return rows


def require_resource(available: int, required: int = RAM_BYTES) -> None:
    require(available >= required,
            f"RAM preflight failed: available={available} required={required}; no inference")


def gate_record(results: list[dict]) -> dict:
    require(len(results) == 8 and len({row["case_id"] for row in results}) == 8,
            "C0 gate requires eight unique attempted cases")
    success = sum(row["answer_state"] == "CURRENT_VALUE_ADOPTION" for row in results)
    return {
        "stage": "candidate2_disjoint_pilot_C0",
        "threshold": C0_THRESHOLD,
        "denominator": 8,
        "automatic_success": success,
        "decision": (
            "AUTOMATIC DEVELOPMENT GATE PASSED"
            if success >= C0_THRESHOLD else "AUTOMATIC DEVELOPMENT GATE NOT PASSED"
        ),
        "proceed": success >= C0_THRESHOLD,
        "case_scores": [
            {key: row[key] for key in ("case_id", "request_id", "answer_state", "automatic_task_success")}
            for row in results
        ],
        "researcher_review_status": "PENDING",
        "remaining_72_status": "BLOCKED_PENDING_GENUINE_SEMANTIC_REVIEW_ENDPOINT_VALIDITY_AND_SEPARATE_CONTROLLER",
    }


def source_hashes() -> dict[str, str]:
    paths = {
        **recovery._source_hashes(),
        TOOL.as_posix(): recovery.sha256(TOOL),
        pilot.TOOL.as_posix(): recovery.sha256(pilot.TOOL),
        pilot.DESTINATION.as_posix(): recovery.sha256(pilot.DESTINATION),
    }
    return dict(sorted(paths.items()))


def validate_readiness() -> dict:
    materialized = pilot.validate_materialized()
    require(recovery.sha256(pilot.DESTINATION) == MATERIALIZATION_SHA256,
            "Candidate 2 pilot materialization hash changed")
    artifact = recovery.load(pilot.DESTINATION)
    block = artifact["execution_blocks"]["c0_gate"]
    require(block["condition"] == "C0" and block["denominator"] == 8
            and block["automatic_current_value_threshold"] == C0_THRESHOLD,
            "Candidate 2 C0 gate registration changed")
    cumulative = combined_cumulative()
    selection = recovery.selection_status()
    require(cumulative["historical_ledger_untouched"] is True, "Historical ledger separation changed")
    require(materialized["c0_gate_requests"] == 8 and materialized["conditional_continuation_requests"] == 72,
            "Materialized execution blocks changed")
    return {
        "schema_version": "personaslm_candidate2_c0_controller_readiness_v1",
        "status": (
            "READY_CODE_AND_MATERIALS_BLOCKED_UNTIL_CANDIDATE2_QUALIFIES_AND_RAM_PASSES"
            if selection["status"] == "CANDIDATE_1_FAILED_CANDIDATE_2_PENDING"
            else "STATE_REQUIRES_REVALIDATION"
        ),
        "selection": {"status": selection["status"], "selected_candidate": selection["selected_candidate"]},
        "materialization": {
            "path": pilot.DESTINATION.as_posix(),
            "sha256": recovery.sha256(pilot.DESTINATION),
            **materialized,
        },
        "controller": {"path": TOOL.as_posix(), "sha256": recovery.sha256(TOOL)},
        "explicit_c0_request_ids": [row["request_id"] for row in c0_requests()],
        "runtime_actions": ["validate", "preflight", "run_c0", "audit"],
        "remaining_72_action_implemented": False,
        "required_available_physical_bytes": RAM_BYTES,
        "combined_authorization": cumulative,
        "execution_impact": {"scientific_model_generations": 0, "inference_seconds": 0.0},
    }


def preflight() -> dict:
    pilot.validate_materialized()
    require(recovery.sha256(pilot.DESTINATION) == MATERIALIZATION_SHA256,
            "Candidate 2 pilot materialization hash changed")
    selection = require_selected()
    require(not list((ROOT / "runs").glob("*")) if (ROOT / "runs").exists() else True,
            "Candidate 2 C0 run already exists")
    require(not list((ROOT / "claims").glob("*.json")) if (ROOT / "claims").exists() else True,
            "Candidate 2 C0 claim already exists")
    require(not list((ROOT / "attempts").glob("*.json")) if (ROOT / "attempts").exists() else True,
            "Candidate 2 C0 attempt already exists")
    plan = recovery.validate_freeze()
    candidate = recovery.candidates(plan)[CANDIDATE]
    model = Path(candidate["artifact"]["local_path"])
    backend = plan["execution_policy"]["backend"]
    tokenizer = plan["execution_policy"]["native_tokenizer"]
    require(model.is_file() and recovery.sha256(model) == candidate["artifact"]["remote_sha256"],
            "Candidate 2 model identity mismatch")
    require(recovery.sha256(backend["path"]) == backend["sha256"], "Backend identity mismatch")
    require(recovery.sha256(tokenizer["path"]) == tokenizer["sha256"], "Tokenizer identity mismatch")
    memory = memory_observation(os.getpid())
    require_resource(memory.get("system", {}).get("available_physical", 0))
    require(shutil.disk_usage(".").free >= 1024**3, "Less than 1 GiB output reserve")
    usage = combined_cumulative()
    require(usage["unresolved_in_flight_completion_requests"] == 0,
            "Interrupted completion has unknown wall time; stop pilot inference")
    require(usage["remaining_generations"] >= 8 and usage["remaining_inference_wall_seconds"] > 1.0,
            "Autonomous authorization exhausted")
    return {
        "status": "PASS",
        "candidate_id": CANDIDATE,
        "checked_software_utc": utc_now(),
        "selection": selection,
        "materialization_path": pilot.DESTINATION.as_posix(),
        "materialization_sha256": recovery.sha256(pilot.DESTINATION),
        "controller_sha256": recovery.sha256(TOOL),
        "model_sha256": recovery.sha256(model),
        "required_available_physical_bytes": RAM_BYTES,
        "memory_before": memory,
        "configuration": recovery.runtime(CANDIDATE, plan).as_dict(),
        "server_command": recovery.command(CANDIDATE, plan),
        "c0_request_ids": [row["request_id"] for row in c0_requests()],
        "ledger_before": usage,
        "source_hashes": source_hashes(),
    }


def replay_result(row: dict, response: dict, elapsed: float, bank: dict) -> dict:
    normalized = normalize_result(response)
    answer_state = recovery.fallback.endpoint(normalized["raw_response"], bank[row["case_id"]])
    task_label = recovery.automatic_task_label(answer_state)
    structural = "EMPTY" if not normalized["raw_response"].strip() else (
        "TRUNCATED" if normalized["stop_reason"] == "length" else "AMBIGUOUS"
    )
    return {
        "answer_state": answer_state,
        "automatic_task_success": task_label,
        "case_id": row["case_id"],
        "candidate_id": CANDIDATE,
        "component_exact_coverage": 1 if task_label == "Success" else 0,
        "generated_tokens": len(normalized["generated_token_ids"] or []),
        "latency_seconds": elapsed,
        "native_stop_reason": normalized["stop_reason"],
        "persona_fidelity": "NOT_APPLICABLE",
        "raw_output_sha256": recovery.text_sha256(normalized["raw_response"]),
        "request_id": row["request_id"],
        "semantic_completeness": "NOT_INDEPENDENTLY_ADJUDICATED",
        "structural_status": structural,
    }


def run_c0(preflight_path: Path) -> dict:
    with writer_lock(ROOT):
        fresh = preflight()
        stored = recovery.load(preflight_path)
        for key in (
            "candidate_id", "selection", "materialization_sha256", "controller_sha256",
            "model_sha256", "required_available_physical_bytes", "configuration", "server_command",
            "c0_request_ids", "ledger_before", "source_hashes", "status",
        ):
            require(stored[key] == fresh[key], f"C0 preflight binding changed: {key}")
        claim_path = ROOT / "claims" / "candidate2_c0.json"
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        require(not claim_path.exists(), "Candidate 2 C0 claim already exists")
        claim = {
            "authorization_id": recovery.load(recovery.LEDGER)["authorization_id"],
            "authorization_namespace": pilot.NAMESPACE,
            "candidate_id": CANDIDATE,
            "maximum_attempts": 8,
            "maximum_actual_completion_wall_seconds": MAX_COMPLETION_SECONDS,
            "materialization_sha256": recovery.sha256(pilot.DESTINATION),
            "preflight_path": preflight_path.as_posix(),
            "preflight_sha256": recovery.sha256(preflight_path),
            "request_ids": stored["c0_request_ids"],
            "source_hashes": stored["source_hashes"],
        }
        atomic_json(claim_path, claim)
        plan = recovery.validate_freeze()
        artifact = recovery.load(pilot.DESTINATION)
        rows = c0_requests(artifact)
        journal = RunJournal(ROOT / "runs", {
            "authorization": claim,
            "candidate_id": CANDIDATE,
            "configuration": recovery.runtime(CANDIDATE, plan).as_dict(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
            "materialization_sha256": claim["materialization_sha256"],
            "phase": "P1 Candidate 2 disjoint C0 development pilot",
            "platform": platform.platform(),
            "python": platform.python_version(),
        })
        for path, digest in claim["source_hashes"].items():
            destination = journal.directory / "source_snapshot" / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as handle:
                handle.write(Path(path).read_bytes())
            require(recovery.sha256(destination) == digest, "Source snapshot mismatch")

        bank = recovery.case_bank()
        completed = 0
        active = None
        results = []
        status = "BLOCKED"
        try:
            journal.write("preflight", fresh)
            with recovery.Server(CANDIDATE, journal, plan) as server:
                client = LlamaClient(recovery.runtime(CANDIDATE, plan).endpoint, timeout=180, audit=journal.write)
                properties = client.request("/props")
                validation = validate_server_properties(properties, recovery.runtime(CANDIDATE, plan))
                require("0f701c882" in validation["build_info"], "Wrong backend build")
                journal.write("effective_server_defaults", {"props": properties, "validation": validation})
                for row in rows:
                    tokens = client.request("/tokenize", {
                        "content": row["prompt"], "add_special": True,
                        "parse_special": True, "with_pieces": False,
                    })["tokens"]
                    require(tokens == row["input_token_ids"], "Live C0 native tokenization differs")
                    journal.write("live_prompt_verified", {
                        "request_id": row["request_id"],
                        "token_ids_sha256": recovery.text_sha256(str(tokens)),
                    })
                journal.write("live_preflight_pass", {"prompts": 8, "completed_inference": 0})
                tick = time.monotonic()
                for row in rows:
                    usage = combined_cumulative()
                    remaining = min(
                        usage["remaining_inference_wall_seconds"],
                        MAX_COMPLETION_SECONDS - (time.monotonic() - tick),
                    )
                    require(remaining > 1.0 and usage["remaining_generations"] >= 1,
                            "Pilot authorization or wall-time ceiling reached")
                    client.timeout = min(180.0, remaining - 0.5)
                    server.assert_running()
                    active = row["request_id"]
                    attempt_path = ROOT / "attempts" / f"{active}.json"
                    attempt_path.parent.mkdir(parents=True, exist_ok=True)
                    atomic_json(attempt_path, {
                        "authorization_id": recovery.load(recovery.LEDGER)["authorization_id"],
                        "authorization_namespace": pilot.NAMESPACE,
                        "candidate_id": CANDIDATE,
                        "order": row["order"],
                        "request_id": active,
                        "request_sha256": row["request_sha256"],
                        "run_id": journal.run_id,
                        "started_utc": utc_now(),
                    })
                    journal.write("candidate2_c0_generation_started", row)
                    started = time.monotonic()
                    response = client.request("/completion", recovery._payload(row, artifact["generation_settings"]))
                    elapsed = time.monotonic() - started
                    journal.write("candidate2_c0_raw_generation", {
                        "latency_seconds": elapsed,
                        "request_id": active,
                        "response": response,
                        "raw_output_sha256": recovery.text_sha256(response.get("content", "")),
                    })
                    result = replay_result(row, response, elapsed, bank)
                    result_path = ROOT / "results" / f"{active}.json"
                    result_path.parent.mkdir(parents=True, exist_ok=True)
                    atomic_json(result_path, result)
                    journal.write("candidate2_c0_result", result)
                    results.append(result)
                    completed += 1
                    active = None
                    journal.write("memory_observation", memory_observation(server.process.pid))
                server.assert_running()
            require(completed == 8, "Incomplete Candidate 2 C0 result")
            for path, digest in claim["source_hashes"].items():
                require(recovery.sha256(path) == digest, f"Postflight source changed: {path}")
            status = "PASS"
        except BaseException as exc:
            status = "PARTIAL" if active is not None or completed else "BLOCKED"
            journal.write("failure", {
                "attempt_consumed": active is not None,
                "message": str(exc),
                "request_id": active,
                "type": type(exc).__name__,
            })
        gate = gate_record(results) if completed == 8 else None
        summary = {
            "status": status,
            "candidate_id": CANDIDATE,
            "attempted": combined_cumulative()["pilot_c0_generations"],
            "completed_results": completed,
            "complete": status == "PASS" and completed == 8,
            "automatic_gate": gate,
            "authorization_usage_after_run": combined_cumulative(),
            "retries": 0,
            "researcher_semantic_review": "PENDING",
            "remaining_72_status": "BLOCKED_NOT_IMPLEMENTED_PENDING_SEMANTIC_VALIDITY",
        }
        journal.finish(**summary)
        atomic_json(journal.directory / "summary.json", summary)
        return summary


def audit() -> dict:
    folders = sorted(path for path in (ROOT / "runs").glob("*") if path.is_dir())
    require(len(folders) == 1, "Candidate 2 C0 must have exactly one run")
    folder = folders[0]
    manifest = recovery.load(folder / "manifest.json")
    summary = recovery.load(folder / "summary.json")
    events = read_events(folder)
    require(events and events[-1]["kind"] == "run_finished" and events[-1]["data"] == summary,
            "C0 terminal event/summary mismatch")
    claim = manifest["authorization"]
    require(claim["authorization_namespace"] == pilot.NAMESPACE, "C0 namespace mismatch")
    require(claim["materialization_sha256"] == recovery.sha256(pilot.DESTINATION),
            "C0 materialization changed")
    for path, digest in claim["source_hashes"].items():
        require(recovery.sha256(path) == digest, f"Current C0 dependency changed: {path}")
        require(recovery.sha256(folder / "source_snapshot" / path) == digest,
                f"C0 source snapshot mismatch: {path}")
    rows = {row["request_id"]: row for row in c0_requests()}
    bank = recovery.case_bank()
    raw = {event["data"]["request_id"]: event["data"] for event in events
           if event["kind"] == "candidate2_c0_raw_generation"}
    saved = {event["data"]["request_id"]: event["data"] for event in events
             if event["kind"] == "candidate2_c0_result"}
    raw_events = [event for event in events if event["kind"] == "candidate2_c0_raw_generation"]
    saved_events = [event for event in events if event["kind"] == "candidate2_c0_result"]
    require(len(raw) == len(raw_events) and len(saved) == len(saved_events),
            "Duplicate C0 raw or result event")
    attempt_paths = sorted((ROOT / "attempts").glob("*.json"))
    attempts = [recovery.load(path) for path in attempt_paths]
    require(set(raw) == set(saved) == {row["request_id"] for row in attempts},
            "C0 raw/result/attempt inventory differs")
    require(all(
        row["authorization_id"] == combined_cumulative()["authorization_id"]
        and row["authorization_namespace"] == pilot.NAMESPACE
        and row["candidate_id"] == CANDIDATE
        and row["request_sha256"] == rows[row["request_id"]]["request_sha256"]
        and row["run_id"] == manifest["run_id"]
        for row in attempts
    ), "C0 attempt provenance differs")
    for request_id, event in raw.items():
        response = event["response"]
        require(recovery.text_sha256(response.get("content", "")) == event["raw_output_sha256"],
                "C0 raw output hash mismatch")
        replayed = replay_result(rows[request_id], response, event["latency_seconds"], bank)
        require(replayed == saved[request_id], "C0 replayed result differs")
        require(recovery.load(ROOT / "results" / f"{request_id}.json") == replayed,
                "C0 materialized result differs")
    complete = summary["status"] == "PASS" and summary["complete"] is True
    if complete:
        require(len(raw) == 8 and summary["completed_results"] == 8, "PASS C0 run is incomplete")
        require(sum(event["kind"] == "live_prompt_verified" for event in events) == 8,
                "PASS C0 run lacks eight live prompt checks")
        require(summary["automatic_gate"] == gate_record(list(saved.values())), "C0 gate replay differs")
    return {
        "status": "PASS" if complete else "INTEGRITY_PASS_RUN_INCOMPLETE",
        "integrity_status": "PASS",
        "candidate_id": CANDIDATE,
        "attempted": len(attempt_paths),
        "replayed_results": len(saved),
        "complete": complete,
        "automatic_gate": summary["automatic_gate"],
        "remaining_72_status": summary["remaining_72_status"],
    }


def write_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), f"Refusing to overwrite existing evidence: {path}")
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def failure_receipt(action: str, exc: BaseException) -> dict:
    value = {
        "action": action,
        "candidate_id": CANDIDATE,
        "error_message": str(exc),
        "error_type": type(exc).__name__,
        "generation_requests_in_failed_action": combined_cumulative()["pilot_c0_generations"],
        "software_recorded_utc": utc_now(),
        "status": "BLOCKED",
    }
    if action == "preflight":
        value["required_available_physical_bytes"] = RAM_BYTES
        value["memory_observation"] = memory_observation(os.getpid())
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "preflight", "run_c0", "audit"))
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    try:
        if arguments.action == "validate":
            value = validate_readiness()
        elif arguments.action == "preflight":
            value = preflight()
        elif arguments.action == "run_c0":
            if arguments.preflight is None:
                parser.error("--preflight is required for run_c0")
            value = run_c0(arguments.preflight)
        else:
            value = audit()
    except BaseException as exc:
        if arguments.action in ("preflight", "run_c0") and arguments.output is not None:
            value = failure_receipt(arguments.action, exc)
            write_new(arguments.output, value)
            print(json.dumps(value, indent=2))
            raise SystemExit(2)
        raise
    if arguments.output is not None:
        write_new(arguments.output, value)
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
