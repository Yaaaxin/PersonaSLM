"""Bounded POSTHOC fixed-A/format diagnostic; no new scoring or inference.

A is always first, so these data cannot separate letter preference from position
preference. Format failure retains protocol score0, not a semantic-error label.
"""
import argparse
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from personaslm.journal import read_events


PUBLIC = Path("docs/validation/p1/real_persona_chat_continuation_v1")
PRIVATE = Path(".local/experiments/real_persona_chat_continuation_v1")
ARMS = ("NONE", "CORRECT", "MISMATCH")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(requests, raw):
    cells, matrix, invalid, fixed, costs = {}, Counter(), Counter(), {}, {}
    for request in requests:
        record = raw[request["request_id"]]
        response = record["response"]
        text = response["content"].strip()
        choice = text if text in ("A", "B") else "INVALID"
        success = int(choice == request["correct_label"])
        labels = [request["phase"], request["phase"] + ":" + request["arm"]]
        for label in labels:
            group = costs.setdefault(label, {"responses": 0, "input_tokens": 0, "output_tokens": 0,
                                             "latencies": [], "native_stops": Counter(), "format_valid": 0})
            group["responses"] += 1
            group["input_tokens"] += response["tokens_evaluated"]
            group["output_tokens"] += response["tokens_predicted"]
            group["latencies"].append(record["latency_seconds"])
            group["native_stops"][str(response.get("stop_type"))] += 1
            group["format_valid"] += choice != "INVALID"
        if request["phase"] != "MAIN":
            continue
        matrix[request["correct_label"], choice] += 1
        if choice == "INVALID":
            invalid[str(response.get("stop_type")), len(text)] += 1
        key = request["case_id"], request["option_order"], request["arm"]
        if key in cells:
            raise ValueError("Duplicate main cell")
        cells[key] = {"choice": choice, "success": success, "target_is_A": request["correct_label"] == "A"}
    for arm in ARMS:
        rows = [value for key, value in cells.items() if key[2] == arm]
        fixed[arm] = {
            "fixed_A_or_first_option_successes": sum(row["target_is_A"] for row in rows),
            "actual_protocol_successes": sum(row["success"] for row in rows),
            "A_target_losses_to_invalid_format": sum(row["target_is_A"] and row["choice"] == "INVALID" for row in rows),
            "A_target_losses_to_B_choice": sum(row["target_is_A"] and row["choice"] == "B" for row in rows),
            "B_target_gains_from_B_choice": sum(not row["target_is_A"] and row["choice"] == "B" for row in rows),
        }
    decomposition = {}
    for high, low in (("CORRECT", "MISMATCH"), ("CORRECT", "NONE"), ("MISMATCH", "NONE")):
        groups = {name: {"count": 0, "sum_protocol_score_difference": 0, "difference_counts": Counter()}
                  for name in ("BOTH_VALID", "AT_LEAST_ONE_FORMAT_FAILURE")}
        for case_id, order in sorted({(key[0], key[1]) for key in cells}):
            a, b = cells[case_id, order, high], cells[case_id, order, low]
            category = "BOTH_VALID" if a["choice"] != "INVALID" and b["choice"] != "INVALID" else "AT_LEAST_ONE_FORMAT_FAILURE"
            group = groups[category]
            difference = a["success"] - b["success"]
            group["count"] += 1
            group["sum_protocol_score_difference"] += difference
            group["difference_counts"][str(difference)] += 1
        decomposition[high + "-" + low] = groups
    for group in costs.values():
        latencies = group.pop("latencies")
        group["completion_wall_seconds"] = math.fsum(latencies)
        group["mean_completion_wall_seconds"] = math.fsum(latencies) / len(latencies)
        group["native_stops"] = dict(group["native_stops"])
    return {
        "target_choice_counts": [{"target": target, "choice": choice, "count": count}
                                 for (target, choice), count in sorted(matrix.items())],
        "format_invalid_native_stops_and_character_lengths": [
            {"stop": stop, "normalized_by_whitespace_strip_characters": length, "count": count}
            for (stop, length), count in sorted(invalid.items())],
        "fixed_A_or_first_option_decomposition": fixed,
        "paired_order_contrast_decomposition": decomposition,
        "observed_costs_by_phase_and_arm": costs,
    }


def diagnostic():
    receipt = load(PUBLIC / "execution_receipt_v1.json")
    plan = load(PRIVATE / "frozen_manifest_v1.json")
    registration = load(PUBLIC / "registration_v1.json")
    if sha(PRIVATE / "frozen_manifest_v1.json") != registration["manifest_sha256"]:
        raise ValueError("Frozen manifest mismatch")
    events = read_events(Path(receipt["run_directory"]))
    if events[-1]["kind"] != "run_finished" or events[-1]["event_hash"] != receipt["terminal_event_sha256"]:
        raise ValueError("Unsealed or mismatched raw journal")
    raw = {event["data"]["request_id"]: event["data"] for event in events if event["kind"] == "continuation_raw"}
    if len(raw) != 52 or set(raw) != {row["request_id"] for row in plan["requests"]}:
        raise ValueError("This bounded diagnostic requires the sealed complete52")
    result = summarize(plan["requests"], raw)
    return {"status": "POSTHOC_OBSERVED_DIAGNOSTIC", "created_utc": datetime.now(timezone.utc).isoformat(),
            "not_prospectively_registered_endpoint": True, "new_generations": 0, **result,
            "interpretation": "Correct-minus-mismatched net protocol-score advantage is decomposed without relabelling format failures. Valid-choice conditioning is a diagnostic with differential coverage, not a replacement estimand. A is always displayed first: A-label preference and first-position preference are not identifiable separately. Counterbalancing demonstrates option-order sensitivity, not its internal cause or semantic incapacity.",
            "cost_scope": "Observed completion wall time on CPU, including client/audit overhead, not process CPU time. No pure causal latency effect claimed because input/output lengths and execution order differ.",
            "semantic_boundary": "Invalid outputs remain protocol0 and semantic judgments unavailable. No discarded outputs, reparsing aliases, human labels, new qualification threshold or change to primary results.",
            "bindings": {"source_sha256": sha(Path(__file__)),
                         "manifest_sha256": sha(PRIVATE / "frozen_manifest_v1.json"),
                         "registration_sha256": sha(PUBLIC / "registration_v1.json"),
                         "execution_receipt_sha256": sha(PUBLIC / "execution_receipt_v1.json"),
                         "primary_analysis_sha256": sha(PUBLIC / "analysis_v1.json"),
                         "independent_analysis_sha256": sha(PUBLIC / "independent_analysis_reproduction_v1.json"),
                         "terminal_event_sha256": receipt["terminal_event_sha256"]},
            "privacy": "Aggregate counts/costs and hash bindings only; no raw response, context, speaker identity or case-level record."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = diagnostic()
    if args.write:
        with (PUBLIC / "posthoc_position_diagnostic_v1.json").open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
