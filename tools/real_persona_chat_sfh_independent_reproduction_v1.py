"""Independently recalculate the completed RPC pilot; never run inference.

Numeric/text scoring is separately implemented. The frozen boundary parser and
atomic artifact writer are shared infrastructure, explicitly disclosed below.
Participant text and row identifiers are never included in the public receipt.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import unicodedata

from personaslm.journal import atomic_json
from personaslm.response_status import classify_response

PUBLIC = Path("docs/validation/p1/real_persona_chat_sfh_pilot_v1")
PRIVATE = Path(".local/experiments/real_persona_chat_sfh_pilot_v1/execution_v1")
ANALYSIS = PUBLIC / "analysis_v1_1.json"
FROZEN = PRIVATE / "frozen_manifest_v1_1.json"
RECEIPT = PUBLIC / "independent_analysis_reproduction_v1.json"
BASELINE = Path("docs/validation/p1/persona_dialogue_disjoint_surface_validation_v3/analysis_v3.json")
METRICS = (
    "structural_response_validity", "japanese_character_present", "japanese_script_rate",
    "output_length_characters", "reference_character_trigram_f1", "source_style_distance",
    "copy_S_trigram_precision", "copy_S_lcs_ratio", "copy_F_trigram_precision",
    "copy_F_lcs_ratio", "copy_H_trigram_precision", "copy_H_lcs_ratio",
    "copy_query_trigram_precision", "copy_query_lcs_ratio", "generated_tokens",
    "latency_seconds")
SUBSETS = {"S": 1, "F": 2, "H": 4, "SF": 3, "SH": 5, "FH": 6, "SFH": 7}
LABELS = ("[話し方]", "[人物情報]", "[過去の会話]", "[相手の発話]")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def check(condition, label):
    if not condition:
        raise AssertionError(label)


def close(left, right):
    if left is None or right is None:
        return left is right
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def norm(text):
    return "".join(unicodedata.normalize("NFKC", text).casefold().split())


def grams(text):
    value = norm(text)
    return set(zip(value, value[1:], value[2:]))


def overlap(generated, reference):
    left, right = grams(generated), grams(reference)
    check(bool(right), "Reference trigram eligibility")
    return 2 * len(left.intersection(right)) / (len(left) + len(right)) if left else 0.0


def copy_metrics(text, units):
    normalized, output = norm(text), grams(text)
    sources = [norm(item) for item in units if norm(item)]
    source_grams = set().union(*(grams(item) for item in sources)) if sources else set()
    precision = len(output.intersection(source_grams)) / len(output) if output else 0.0
    longest = max((SequenceMatcher(None, normalized, item, autojunk=False)
                   .find_longest_match().size for item in sources), default=0)
    return precision, longest / len(normalized) if normalized else 0.0


def style_distance(text, case):
    clean = re.sub(r"<[^>]+>", "", text).replace("＊＊", "")
    values = [len(clean) / 50, int("?" in clean or "？" in clean),
              int("!" in clean or "！" in clean), int("…" in clean or "..." in clean),
              int("笑" in clean or bool(re.search(r"(?i)(^|\W)w+(\W|$)", clean))),
              int(bool(re.search(r"(です|ます|でした|ません)[。！？!?]*$", clean)))]
    source = case["style_features"]
    expected = [source["mean_turn_length_characters"] / 50,
                *[source[key] for key in ("question_turn_rate", "exclamation_turn_rate",
                  "ellipsis_turn_rate", "laughter_turn_rate", "polite_ending_rate")]]
    return sum(abs(left - right) for left, right in zip(values, expected)) / 6


def score(response, case, latency):
    termination = {key: response[key] for key in (
        "stop_type", "stopped_eos", "stopped_word", "stopped_limit", "stopping_word",
        "stop", "truncated") if key in response}
    boundary = classify_response(response["content"], termination, declared_stops=())
    text = boundary["first_span"]["text"]
    valid = (boundary["unit_identifiable"] and bool(text.strip()) and
             boundary["status"] != "TRUNCATED" and not any(label in text for label in LABELS))
    result = dict.fromkeys(METRICS)
    result.update(structural_response_validity=int(valid),
                  generated_tokens=response["tokens_predicted"], latency_seconds=latency)
    if not valid:
        if not norm(text):
            result.update(output_length_characters=0, reference_character_trigram_f1=0.0)
            for source in ("S", "F", "H", "query"):
                result[f"copy_{source}_trigram_precision"] = 0.0
                result[f"copy_{source}_lcs_ratio"] = 0.0
        return result, boundary
    value = norm(text)
    japanese = sum(0x3040 <= ord(c) <= 0x30ff or 0x3400 <= ord(c) <= 0x4dbf or
                   0x4e00 <= ord(c) <= 0x9fff for c in value)
    result.update(japanese_character_present=int(japanese > 0),
                  japanese_script_rate=japanese / len(value) if value else 0.0,
                  output_length_characters=len(value),
                  reference_character_trigram_f1=overlap(text, case["reference"]["text"]),
                  source_style_distance=style_distance(text, case))
    sources = {"S": [case["style_profile"]], "F": case["facts"],
               "H": [turn["text"] for turn in case["history"]],
               "query": [case["query"]["text"]]}
    for source, units in sources.items():
        precision, lcs = copy_metrics(text, units)
        result[f"copy_{source}_trigram_precision"] = precision
        result[f"copy_{source}_lcs_ratio"] = lcs
    return result, boundary


def effect(values, subset):
    positive, negative = [], []
    for condition, value in values.items():
        index = int(condition[1:])
        sign = 1
        for bit in (1, 2, 4):
            if subset & bit:
                sign *= 1 if index & bit else -1
        (positive if sign == 1 else negative).append(value)
    check(len(positive) == len(negative) == 4, "Complete paired factorial required")
    return statistics.fmean(positive) - statistics.fmean(negative)


def summarize(values):
    return {"n": len(values), "mean": statistics.fmean(values) if values else None,
            "median": statistics.median(values) if values else None,
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None}


def self_check():
    check(overlap("abcdef", "abcdef") == 1, "Identity F1")
    check(close(overlap("abcd", "bcde"), 0.5), "Nontrivial F1")
    check(copy_metrics("abcde", ["zabcdx"])[1] == 0.8, "Contiguous-copy check")
    for target, mask in SUBSETS.items():
        values = {f"C{i}": math.prod(1 if i & bit else -1
                                    for bit in (1, 2, 4) if mask & bit) for i in range(8)}
        for other, other_mask in SUBSETS.items():
            check(close(effect(values, other_mask), 2 if target == other else 0),
                  "Hadamard orthogonality")
    case = {"reference": {"text": "これは参照の文章です。"}, "style_profile": "", "facts": [],
            "history": [], "query": {"text": ""}, "style_features": {
                "mean_turn_length_characters": 0, "question_turn_rate": 0,
                "exclamation_turn_rate": 0, "ellipsis_turn_rate": 0,
                "laughter_turn_rate": 0, "polite_ending_rate": 0}}
    empty, _ = score({"content": "", "stop_type": "eog", "tokens_predicted": 0}, case, 1)
    check(empty["structural_response_validity"] == 0 and
          empty["reference_character_trigram_f1"] == 0 and empty["source_style_distance"] is None,
          "Successful-empty missingness")
    truncated, _ = score({"content": "こんにちは", "stop_type": "limit",
                          "tokens_predicted": 96}, case, 1)
    check(truncated["structural_response_validity"] == 0 and
          truncated["reference_character_trigram_f1"] is None, "Truncation missingness")
    check(close(style_distance("abcde", case), 1 / 60), "Length scale")


def reproduce():
    self_check()
    check(ANALYSIS.exists(), "Completed public analysis required before journal access")
    analysis, plan = load(ANALYSIS), load(FROZEN)
    check(sha(FROZEN) == analysis["bindings"]["private_frozen_manifest_sha256"],
          "Frozen analysis binding")
    folders = [path for path in (PRIVATE / "runs").iterdir() if path.is_dir()]
    check(len(folders) == 1, "Exactly one run required")
    folder = folders[0]
    summary = load(folder / "summary.json")
    previous, events = digest(load(folder / "manifest.json")), []
    for index, path in enumerate(sorted((folder / "events").glob("*.json")), 1):
        item = load(path)
        claimed = item.pop("event_hash")
        check(item["sequence"] == index and item["previous_hash"] == previous and
              digest(item) == claimed, "Journal chain")
        previous = claimed
        events.append(item)
    check(events[-1]["kind"] == "run_finished" and events[-1]["data"] == summary,
          "Terminal summary")
    check(previous == analysis["bindings"]["journal_terminal_event_sha256"], "Analysis journal binding")
    started = [event["data"] for event in events if event["kind"] == "rpc_sfh_generation_started"]
    raw = [event["data"] for event in events if event["kind"] == "rpc_sfh_raw_generation"]
    derived = [event["data"] for event in events if event["kind"] == "rpc_sfh_result"]
    http = [event["data"] for event in events if event["kind"] == "http_response" and
            event["data"].get("route") == "/completion" and event["data"].get("status") == 200]
    calls = [event["data"]["payload"] for event in events if event["kind"] == "http_request" and
             event["data"].get("route") == "/completion"]
    check(len(started) == len(raw) == len(derived) == len(http) == len(calls) == 64,
          "This reproduction covers the completed 64-request allocation only")
    check(started == plan["requests"], "Exact allocation and order")
    rows, stops, boundary_counts, token_counts = [], Counter(), Counter(), []
    for request, saved, target, packet, payload in zip(started, raw, derived, http, calls):
        response = json.loads(base64.b64decode(packet["body_base64"]).decode("utf-8"))
        check(response == saved["response"], "HTTP/raw binding")
        check(saved["request_id"] == target["request_id"] == request["request_id"], "Row binding")
        check(payload["prompt"] == request["input_token_ids"], "Native prompt token binding")
        check(payload["n_predict"] == 96 and payload["temperature"] == 0 and
              payload["top_p"] == 1 and payload["seed"] == 42 and payload["stop"] == [] and
              payload["cache_prompt"] is False and payload["ignore_eos"] is False,
              "Actual completion configuration")
        rebuilt, boundary = score(response, request["latent_case"], saved["latency_seconds"])
        check(all(close(rebuilt[key], target["automatic_score"][key]) for key in METRICS),
              "Independent row-level scoring")
        check(boundary == target["response_status"], "Boundary parser reproducibility")
        check(target["human_semantic_review"] == {"status": "PENDING_NOT_COLLECTED",
              "rating_count": 0, "ratings": []}, "No human labels")
        check(len(response["tokens"]) == response["tokens_predicted"], "Native token count")
        stops[response.get("stop_type", "unknown")] += 1
        boundary_counts[boundary["status"]] += 1
        token_counts.append(response["tokens_predicted"])
        rows.append((request["case_id"], request["condition"], rebuilt))
    for metric in METRICS:
        for condition in (f"C{i}" for i in range(8)):
            values = [values[metric] for _, label, values in rows
                      if label == condition and values[metric] is not None]
            expected = analysis["condition_summary"][metric][condition]
            check(all(close(value, expected[key]) for key, value in summarize(values).items()),
                  "Independent condition estimates")
            check(expected["missing"] == 8 - len(values), "Condition coverage")
        cases = defaultdict(dict)
        for case, condition, values in rows:
            if values[metric] is not None:
                cases[case][condition] = values[metric]
        for subset, mask in SUBSETS.items():
            values = [effect(value, mask) for value in cases.values() if len(value) == 8]
            expected = analysis["speaker_paired_factorial_effects"][metric][subset]
            check(all(close(value, expected[key]) for key, value in summarize(values).items()),
                  "Independent factorial estimates")
            check(expected["complete_speakers"] == len(values) and
                  expected["incomplete_speakers"] == 8 - len(values), "Paired coverage")
            loo = [statistics.fmean(values[:i] + values[i + 1:])
                   for i in range(len(values))] if len(values) > 1 else []
            check(close(min(loo) if loo else None, expected["leave_one_speaker_out_mean_minimum"])
                  and close(max(loo) if loo else None, expected["leave_one_speaker_out_mean_maximum"]),
                  "Independent leave-one-speaker-out estimates")
    memory = [event["data"] for event in events if event["kind"] in (
        "memory_observation", "after_server_ready_memory_gate", "post_live_tokenization_memory_gate",
        "before_request_memory_gate")]
    minimum_ram = min(item["system"]["available_physical"] for item in memory
                      if type(item.get("system", {}).get("available_physical")) is int)
    peak_ram = max(item.get("process", {}).get("peak_working_set", 0) for item in memory)
    elapsed = math.fsum(item["latency_seconds"] for item in raw)
    resources = analysis["resources"]
    check(close(elapsed, resources["completion_inference_seconds"]), "Inference cost")
    check(minimum_ram == resources["minimum_observed_available_physical_bytes"] and
          peak_ram == resources["peak_server_working_set_bytes"], "Memory extrema")
    check(sha(BASELINE) == "0a2d4547a6501991d6b9f1855a4f4081ff885bba5e700f226757ace58d182a44",
          "Frozen prior budget evidence")
    baseline = load(BASELINE)["cumulative_authorization_after"]
    cumulative_generations = baseline["generations_used"] + len(started)
    cumulative_seconds = baseline["inference_seconds_used"] + elapsed
    check(resources["cumulative_after"]["generations_used"] == cumulative_generations and
          close(resources["cumulative_after"]["inference_seconds_used"], cumulative_seconds),
          "Cumulative budget")
    return {
        "schema_version": "personaslm_rpc_sfh_independent_analysis_reproduction_v1",
        "status": "PASS", "created_utc": datetime.now(timezone.utc).isoformat(),
        "provenance": "Separate AI analyst and independently implemented numeric scorer; not human review or independent experimental validation",
        "scope": "Completed 64-response development allocation only; no dataset or held-out-speaker access",
        "bindings": {"analysis_sha256": sha(ANALYSIS), "frozen_manifest_sha256": sha(FROZEN),
                     "journal_terminal_event_sha256": previous, "script_sha256": sha(__file__),
                     "shared_boundary_parser_sha256": sha("src/personaslm/response_status.py"),
                     "prior_budget_analysis_sha256": sha(BASELINE)},
        "reproduced": {"raw_http_responses": len(http), "automatic_metrics": len(METRICS),
                       "row_metric_values_checked": len(rows) * len(METRICS),
                       "condition_metric_summaries": 8 * len(METRICS),
                       "factorial_metric_summaries": 7 * len(METRICS),
                       "native_stop_counts": dict(stops), "boundary_status_counts": dict(boundary_counts),
                       "total_generated_tokens": sum(token_counts),
                       "generated_token_summary": summarize(token_counts),
                       "completion_latency_summary": summarize([item["latency_seconds"] for item in raw]),
                       "completion_inference_seconds": elapsed,
                       "minimum_observed_available_physical_bytes": minimum_ram,
                       "peak_server_working_set_bytes": peak_ram,
                       "cumulative_generations_used": cumulative_generations,
                       "cumulative_inference_seconds_used": cumulative_seconds},
        "shared_dependency": "Frozen response_status_v1 boundary parser; separately implemented F1, LCS, style, Japanese rate, missingness, effects, LOO, journal-chain and resource arithmetic",
        "limits": ["Does not validate construct validity or human semantic quality",
                   "Does not reproduce generation or establish bit-identical repeatability",
                   "Private frozen prompts and raw journals are required; public clone-only reproduction remains PARTIAL"],
        "privacy": {"participant_text_public": False, "row_identifiers_public": False},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        print("PASS: independent formula self-checks; no experimental data accessed")
    else:
        receipt = reproduce()
        if args.write:
            atomic_json(RECEIPT, receipt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
