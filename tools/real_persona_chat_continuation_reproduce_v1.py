"""Independent raw-journal arithmetic audit, not an independent experiment.

Imports only the existing hash-chain reader, never the study/material/scorer.
No inference, raw-data printing, or existing-artifact overwrite is supported.
"""
import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata

from personaslm.journal import read_events


PUBLIC = Path("docs/validation/p1/real_persona_chat_continuation_v1")
PRIVATE = Path(".local/experiments/real_persona_chat_continuation_v1")
ARMS = ("NONE", "CORRECT", "MISMATCH")
CONTRASTS = (("CORRECT", "MISMATCH"), ("CORRECT", "NONE"), ("MISMATCH", "NONE"))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mean(values):
    return math.fsum(values) / len(values) if values else None


def selection(text, answer):
    stripped = text.strip() if isinstance(text, str) else None
    valid = stripped == "A" or stripped == "B"
    return {"choice": stripped if valid else None, "format_valid": valid,
            "protocol_success": int(valid and stripped == answer),
            "recognition_if_valid": int(stripped == answer) if valid else None}


def grams(text):
    text = re.sub(r"\s+", "", unicodedata.normalize("NFKC", text).casefold())
    return set(zip(text, text[1:], text[2:]))


def lexical(case, arm):
    visible = [turn["text"] for turn in case["history"]] + [case["query"]["text"]]
    if arm != "NONE":
        visible.extend(turn["text"] for turn in case[
            "source_history" if arm == "CORRECT" else "donor_source_history"])
    evidence = grams("\n".join(visible))
    scores = []
    for candidate in case["candidate_texts"]:
        candidate_grams = grams(candidate)
        union = evidence | candidate_grams
        scores.append(len(evidence & candidate_grams) / len(union) if union else 0.0)
    target = case["target_candidate_index"]
    return .5 if scores[0] == scores[1] else float(scores[target] > scores[1 - target])


def summaries(rows, cases):
    require(len(cases) == 8 and {c["pair_index"] for c in cases} == set(range(4)), "Case allocation")
    cells = {}
    for row in rows:
        if row["phase"] == "MAIN":
            key = row["case_id"], row["option_order"], row["arm"]
            require(key not in cells, "Duplicate allocated cell")
            cells[key] = row
    require(len(cells) == 48, "Main allocation must have48 cells")
    conditions = {}
    for arm in ARMS:
        group = [r for r in cells.values() if r["arm"] == arm]
        present = [r for r in group if r["protocol_success"] is not None]
        valid = [r for r in present if r["format_valid"]]
        invariance = []
        for case in cases:
            first, second = [cells[case["case_id"], order, arm] for order in (0, 1)]
            if first["format_valid"] and second["format_valid"]:
                # Swapping A/B must swap the letter to preserve candidate identity.
                invariance.append(int(first["choice"] != second["choice"]))
        conditions[arm] = {
            "allocated": 16, "returned": len(present), "format_valid": len(valid),
            "protocol_successes": sum(r["protocol_success"] for r in present),
            "protocol_success_mean": mean([r["protocol_success"] for r in present]),
            "valid_selection_recognition": mean([r["recognition_if_valid"] for r in valid]),
            "position_invariance_cases": len(invariance), "position_invariant": sum(invariance),
            "first_option_choices": sum(r["choice"] == "A" for r in valid),
            "lexical_baseline_mean": mean([lexical(case, arm) for case in cases]),
        }
    contrasts = {}
    for high, low in CONTRASTS:
        complete_pairs, observed, missing = [], [], 0
        for pair in range(4):
            selected = [case for case in cases if case["pair_index"] == pair]
            require(len(selected) == 2, "Reciprocal pair size")
            pair_values = []
            for case in selected:
                for order in (0, 1):
                    a = cells[case["case_id"], order, high]["protocol_success"]
                    b = cells[case["case_id"], order, low]["protocol_success"]
                    if a is None or b is None:
                        missing += 1
                    else:
                        pair_values.append(a - b)
            observed.extend(pair_values)
            if len(pair_values) == 4:
                complete_pairs.append(mean(pair_values))
        leave_out = [mean(complete_pairs[:i] + complete_pairs[i + 1:])
                     for i in range(len(complete_pairs))] if len(complete_pairs) > 1 else []
        contrasts[high + "-" + low] = {
            "n": len(complete_pairs), "mean": mean(complete_pairs), "values": complete_pairs,
            "leave_one_pair_out_mean_range": [min(leave_out), max(leave_out)] if leave_out else None,
            "missing_paired_order_cases": missing,
            "allocated_16_order_case_bounds": [(math.fsum(observed) - missing) / 16,
                                               (math.fsum(observed) + missing) / 16],
        }
    return conditions, contrasts


def compare(actual, expected, label="aggregate"):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and actual.keys() == expected.keys(), label + " keys")
        for key in expected:
            compare(actual[key], expected[key], label + "." + key)
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), label + " length")
        for index, value in enumerate(expected):
            compare(actual[index], value, label + f"[{index}]")
    elif type(expected) is float:
        require(type(actual) in (int, float) and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12),
                label + " numeric discrepancy")
    else:
        require(actual == expected, label + " discrepancy")


def expected_payload(request):
    return {"prompt": request["input_token_ids"], "n_predict": 8, "temperature": 0.0,
            "top_p": 1.0, "seed": 42, "cache_prompt": False, "stop": [],
            "ignore_eos": False, "return_tokens": True, "stream": False}


def reconcile(plan, receipt, events):
    starts = [event["data"] for event in events if event["kind"] == "continuation_started"]
    require(starts == plan["requests"][:len(starts)] and len(starts) == receipt["attempts"],
            "Attempted prefix/accounting mismatch")
    requests = [event["data"] for event in events if event["kind"] == "http_request"
                and event["data"]["route"] == "/completion"]
    require([row["payload"] for row in requests] == [expected_payload(row) for row in starts],
            "Actual HTTP payload/count mismatch")
    by_id, failures, active, response_body, http_elapsed = {}, [], None, None, None
    for event in events:
        data, kind = event["data"], event["kind"]
        if kind == "continuation_started":
            require(active is None, "Concurrent/unresolved attempt")
            active, response_body, http_elapsed = data["request_id"], None, None
        elif kind == "http_response" and data["route"] == "/completion":
            require(active is not None, "Unbound completion HTTP response")
            http_elapsed = data.get("elapsed_seconds")
            if data.get("status") == 200 and not data.get("incomplete"):
                response_body = json.loads(base64.b64decode(data["body_base64"]).decode("utf-8"))
        elif kind == "continuation_raw":
            require(active == data["request_id"] and active not in by_id, "Unbound/repeated raw response")
            require(response_body == data["response"], "Raw response differs from archived HTTP bytes")
            require(isinstance(http_elapsed, (int, float)) and
                    data["latency_seconds"] + 1e-6 >= http_elapsed >= 0, "HTTP/outer latency inconsistency")
            by_id[active], active = data, None
        elif kind == "continuation_failed":
            require(active == data["request_id"] and active not in by_id, "Failed-attempt identity")
            failures.append(data)
            active = None
    require(active is None and len(by_id) == receipt["responses"], "Unresolved/returned count")
    require(len(starts) == len(by_id) + len(failures), "Attempt/raw/failure accounting")
    seconds = math.fsum(row["latency_seconds"] for row in [*by_id.values(), *failures])
    failed_seconds = math.fsum(row["latency_seconds"] for row in failures)
    require(math.isclose(seconds, receipt["completion_inference_seconds"], abs_tol=1e-8), "Inference cost")
    require(math.isclose(failed_seconds, receipt["failed_seconds"], abs_tol=1e-8), "Failed inference cost")
    require(receipt["cumulative_generations"] == 636 + len(starts), "Cumulative generation ledger")
    require(math.isclose(receipt["cumulative_inference_seconds"], 3828.328792899886 + seconds,
                         abs_tol=1e-8), "Cumulative seconds ledger")
    require(receipt["unattempted"] == 52 - len(starts) and receipt["retries"] == 0, "Remaining/retry ledger")
    return by_id, seconds, len(failures)


def reproduce():
    registration = load(PUBLIC / "registration_v1.json")
    plan = load(PRIVATE / "frozen_manifest_v1.json")
    receipt = load(PUBLIC / "execution_receipt_v1.json")
    primary = load(PUBLIC / "analysis_v1.json")
    require(sha(PRIVATE / "frozen_manifest_v1.json") == registration["manifest_sha256"], "Frozen manifest hash")
    run = Path(receipt["run_directory"])
    manifest = load(run / "manifest.json")
    require(manifest["frozen_manifest"] == plan, "Archived plan identity")
    require(manifest["claim"] == load(PRIVATE / "claim_v1.json"), "Run claim identity")
    for source, digest in plan["source_hashes"].items():
        require(sha(run / "source_snapshot" / source) == digest, "Archived implementation dependency hash")
    events = read_events(run)
    require(events[-1]["kind"] == "run_finished" and
            events[-1]["event_hash"] == receipt["terminal_event_sha256"], "Sealed terminal chain")
    for key, value in events[-1]["data"].items():
        require(receipt[key] == value, "Receipt/terminal mismatch")
    raw, seconds, failed = reconcile(plan, receipt, events)
    cases_by_id = {case["case_id"]: case for case in plan["cases"]}
    require(len(cases_by_id) == 8, "Unique case identities")
    for pair in range(4):
        paired = [case for case in plan["cases"] if case["pair_index"] == pair]
        require(len(paired) == 2 and paired[0]["candidate_texts"] == paired[1]["candidate_texts"] and
                {case["target_candidate_index"] for case in paired} == {0, 1}, "Reciprocal candidate construction")
    rows = []
    for request in plan["requests"]:
        if request["phase"] == "MAIN":
            case = cases_by_id[request["case_id"]]
            target = case["target_candidate_index"]
            require(case["reference"]["text"] == case["candidate_texts"][target], "Actual reference provenance")
            order = request["option_order"]
            require(order in (0, 1) and request["correct_label"] == "AB"[target ^ order], "Option/answer mapping")
            displayed = case["candidate_texts"] if order == 0 else case["candidate_texts"][::-1]
            require(request["messages"][-1]["content"].endswith(
                "A: " + displayed[0] + "\nB: " + displayed[1]), "Actual displayed candidate order")
        record = raw.get(request["request_id"])
        if record:
            response = record["response"]
            require(response.get("truncated") is False and
                    response.get("tokens_evaluated") == len(request["input_token_ids"]), "Native input accounting")
            if isinstance(response.get("prompt"), list):
                require(response["prompt"] == request["input_token_ids"], "Native input token identity")
            require(type(response.get("tokens_predicted")) is int and 0 <= response["tokens_predicted"] <= 8,
                    "Native output token bound")
            outcome = selection(response.get("content"), request["correct_label"])
        else:
            outcome = {key: None for key in ("choice", "format_valid", "protocol_success", "recognition_if_valid")}
        rows.append({**request, **outcome})
    controls = sum(row["protocol_success"] or 0 for row in rows if row["phase"] == "CONTROL")
    require(controls == receipt["controls_correct"], "Authored control arithmetic")
    require(not any(row["phase"] == "MAIN" for row in plan["requests"][:receipt["attempts"]]) or controls == 4,
            "Main executed without4/4 gate")
    conditions, contrasts = summaries(rows, plan["cases"])
    compare(conditions, primary["conditions"], "conditions")
    compare(contrasts, primary["contrasts"], "contrasts")
    stops = dict(Counter(record["response"].get("stop_type") for record in raw.values()
                         if record["response"].get("stop_type")))
    compare(stops, primary["native_stops"], "stops")
    require(primary["resources"] == receipt, "Primary resource identity")
    return {"status": "PASS", "scope": "INDEPENDENT_ARITHMETIC_NOT_EXPERIMENTAL_OR_HUMAN_VALIDATION",
            "audited_utc": datetime.now(timezone.utc).isoformat(),
            "attempts": receipt["attempts"], "responses": len(raw), "failed_calls": failed,
            "http_payloads_and_raw_bytes_verified": len(raw), "controls_correct": controls,
            "completion_inference_seconds": seconds,
            "cumulative_generations": receipt["cumulative_generations"],
            "cumulative_inference_seconds": receipt["cumulative_inference_seconds"],
            "conditions": conditions, "contrasts": contrasts, "native_stops": stops,
            "bindings": {"registration_sha256": sha(PUBLIC / "registration_v1.json"),
                         "manifest_sha256": sha(PRIVATE / "frozen_manifest_v1.json"),
                         "receipt_sha256": sha(PUBLIC / "execution_receipt_v1.json"),
                         "primary_analysis_sha256": sha(PUBLIC / "analysis_v1.json"),
                         "reproduction_source_sha256": sha(Path(__file__)),
                         "terminal_event_sha256": receipt["terminal_event_sha256"]},
            "limits": "Shared journal-chain reader only; scoring, pairing, lexical baseline and cost arithmetic independently implemented. No participant rows public. Peak-memory observation not independently reproduced. Public clone-only reproduction PARTIAL."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = reproduce()
    if args.write:
        with (PUBLIC / "independent_analysis_reproduction_v1.json").open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            handle.write("\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
