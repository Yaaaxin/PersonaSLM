"""Independently reproduce the frozen v3 analysis without inference.

This module deliberately does not import the v3 controller.  It reads the
frozen manifest and append-only raw journal, verifies their bindings, rescans
the raw response text, and reconstructs every registered automatic estimate.
"""

from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATION = Path("docs/validation/p1/persona_dialogue_disjoint_surface_validation_v3")
RESULTS = Path("results/p1_persona_dialogue_disjoint_surface_validation/v3")
RUN_RELATIVE = RESULTS / "runs/20261018T214135-eb079a7d40da4ca1a1db9135718d6ad2"
FROZEN_MANIFEST = VALIDATION / "frozen_manifest_v3.json"
ARCHIVED_ANALYSIS = VALIDATION / "analysis_v3.json"
EXECUTION_AUDIT = VALIDATION / "execution_audit_v3.json"
PREFLIGHT = VALIDATION / "preflight_v3.json"
CLAIM = RESULTS / "claim.json"
DEFAULT_OUTPUT = VALIDATION / "analysis_reproduction_v1.json"
TEST_PATH = Path("tests/test_p1_persona_dialogue_disjoint_surface_validation_v3_reproduce.py")

PRIMARY_METRICS = (
    "preferred_current_anchor_selection",
    "any_current_anchor_selection",
)
WEIGHTS = {
    "theta_A": {
        "SFH_ALIGNED_RAW": 0.5,
        "SFH_ALIGNED_DECLARATIVE": 0.5,
        "SFH_IRRELEVANT_RAW": -0.5,
        "SFH_IRRELEVANT_DECLARATIVE": -0.5,
    },
    "theta_C": {
        "SFH_CONFLICT_RAW": 0.5,
        "SFH_CONFLICT_DECLARATIVE": 0.5,
        "SFH_IRRELEVANT_RAW": -0.5,
        "SFH_IRRELEVANT_DECLARATIVE": -0.5,
    },
    "theta_surface": {
        "SFH_ALIGNED_RAW": -1.0 / 3.0,
        "SFH_ALIGNED_DECLARATIVE": 1.0 / 3.0,
        "SFH_CONFLICT_RAW": -1.0 / 3.0,
        "SFH_CONFLICT_DECLARATIVE": 1.0 / 3.0,
        "SFH_IRRELEVANT_RAW": -1.0 / 3.0,
        "SFH_IRRELEVANT_DECLARATIVE": 1.0 / 3.0,
    },
    "theta_generic_history": {
        "SF_NO_H": -1.0,
        "SFH_IRRELEVANT_RAW": 0.5,
        "SFH_IRRELEVANT_DECLARATIVE": 0.5,
    },
    "derived_theta_A_minus_theta_C": {
        "SFH_ALIGNED_RAW": 0.5,
        "SFH_ALIGNED_DECLARATIVE": 0.5,
        "SFH_CONFLICT_RAW": -0.5,
        "SFH_CONFLICT_DECLARATIVE": -0.5,
    },
    "interaction_surface_aligned_minus_irrelevant": {
        "SFH_ALIGNED_RAW": -1.0,
        "SFH_ALIGNED_DECLARATIVE": 1.0,
        "SFH_IRRELEVANT_RAW": 1.0,
        "SFH_IRRELEVANT_DECLARATIVE": -1.0,
    },
    "interaction_surface_conflict_minus_irrelevant": {
        "SFH_CONFLICT_RAW": -1.0,
        "SFH_CONFLICT_DECLARATIVE": 1.0,
        "SFH_IRRELEVANT_RAW": 1.0,
        "SFH_IRRELEVANT_DECLARATIVE": -1.0,
    },
}
EXPECTED_EVENT_COUNTS = {
    "preflight": 1,
    "server_launch": 1,
    "server_process": 1,
    "http_request": 354,
    "http_response": 354,
    "memory_observation": 170,
    "effective_server_defaults": 1,
    "live_prompt_verified": 168,
    "live_preflight_pass": 1,
    "disjoint_surface_validation_v3_generation_started": 168,
    "disjoint_surface_validation_v3_raw_generation": 168,
    "disjoint_surface_validation_v3_result": 168,
    "postflight": 1,
    "run_finished": 1,
}
FIRST_SENTENCE = re.compile(r"[.!?](?=(?:[\"\u2019\u201d]*)\s|$)")
ANCHOR_PLACEHOLDER_PATTERN = r"<exact [AB] anchor>"
ANCHOR_PLACEHOLDER = re.compile(ANCHOR_PLACEHOLDER_PATTERN)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _load(relative: Path) -> dict:
    return json.loads((PROJECT_ROOT / relative).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    path = path if path.is_absolute() else PROJECT_ROOT / path
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _fingerprint(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _same_number(left: object, right: object) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-15)
    return left == right


def _verify_journal_records(
    manifest: dict, records: list[tuple[str, dict]]
) -> list[dict]:
    previous = _fingerprint(manifest)
    events = []
    for sequence, (filename, original) in enumerate(records, 1):
        _require(filename == f"{sequence:06d}.json", f"Journal gap at {filename}")
        saved = dict(original)
        event_hash = saved.pop("event_hash", None)
        _require(saved.get("sequence") == sequence, f"Bad sequence at {filename}")
        _require(saved.get("previous_hash") == previous, f"Bad chain at {filename}")
        _require(_fingerprint(saved) == event_hash, f"Bad event hash at {filename}")
        saved["event_hash"] = event_hash
        events.append(saved)
        previous = event_hash
    _require(events and events[-1]["kind"] == "run_finished", "Missing terminal event")
    _require(events[-1]["data"]["status"] == "PASS", "Run did not terminate PASS")
    return events


def _read_journal() -> tuple[dict, list[dict]]:
    run = PROJECT_ROOT / RUN_RELATIVE
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    _require(manifest.get("journal_version") == 1, "Unsupported journal version")
    records = [
        (path.name, json.loads(path.read_text(encoding="utf-8")))
        for path in sorted((run / "events").glob("*.json"))
    ]
    events = _verify_journal_records(manifest, records)
    return manifest, events


def _verify_file_bindings(frozen: dict, claim: dict, run_manifest: dict) -> dict:
    checks = {
        "frozen_manifest": (FROZEN_MANIFEST, claim["manifest_sha256"]),
        "authorization": (
            Path(frozen["authorization_path"]),
            frozen["authorization_sha256"],
        ),
        "design": (Path(frozen["design_path"]), frozen["design_sha256"]),
        "case_bank": (Path(frozen["case_bank_path"]), frozen["case_bank_sha256"]),
        "material_audit": (
            Path(frozen["material_audit_path"]),
            frozen["material_audit_sha256"],
        ),
        "review_schema": (
            Path(frozen["review_schema_path"]),
            frozen["review_schema_sha256"],
        ),
        "chat_template": (Path(frozen["template_path"]), frozen["template_sha256"]),
        "model": (
            Path(frozen["model"]["model_file"]),
            frozen["model"]["model_sha256"],
        ),
        "backend": (
            Path(frozen["model"]["backend_file"]),
            frozen["model"]["backend_sha256"],
        ),
        "preflight": (PREFLIGHT, claim["preflight_sha256"]),
    }
    observed = {}
    for name, (path, expected) in checks.items():
        actual = _sha256(path)
        _require(actual == expected, f"Bound {name} changed: {path}")
        observed[name] = {"path": path.as_posix(), "sha256": actual}

    tokenizer = frozen["native_tokenizer_identity"]
    tokenizer_path = Path(tokenizer["path"])
    _require(
        _sha256(tokenizer_path) == tokenizer["tokenizer_sha256"],
        "Native tokenizer changed",
    )
    dll_directory = PROJECT_ROOT / tokenizer_path.parent
    for filename, expected in tokenizer["dll_hashes"].items():
        _require(_sha256(dll_directory / filename) == expected, f"DLL changed: {filename}")

    source_current = 0
    source_snapshot = 0
    for relative, expected in frozen["registration_source_hashes"].items():
        _require(_sha256(Path(relative)) == expected, f"Source changed: {relative}")
        source_current += 1
        snapshot = PROJECT_ROOT / RUN_RELATIVE / "source_snapshot" / relative
        _require(_sha256(snapshot) == expected, f"Snapshot changed: {relative}")
        source_snapshot += 1

    native_logs = 0
    for record in frozen["native_tokenizer_logs"]:
        _require(
            _sha256(Path(record["path"])) == record["sha256"],
            f"Tokenizer log changed: {record['path']}",
        )
        native_logs += 1

    _require(run_manifest["frozen_manifest"] == frozen, "Run embeds another manifest")
    _require(run_manifest["claim"] == claim, "Run embeds another claim")
    archived_analysis = _load(ARCHIVED_ANALYSIS)
    execution_audit_sha = _sha256(EXECUTION_AUDIT)
    _require(
        archived_analysis["execution_audit_sha256"] == execution_audit_sha,
        "Execution audit binding changed",
    )
    return {
        "status": "PASS_ZERO_HASH_DIFFERENCES",
        "bound_files": observed,
        "tokenizer_sha256": tokenizer["tokenizer_sha256"],
        "tokenizer_dll_hashes_verified": len(tokenizer["dll_hashes"]),
        "registration_source_hashes_verified_current": source_current,
        "registration_source_hashes_verified_snapshot": source_snapshot,
        "native_tokenizer_log_hashes_verified": native_logs,
        "run_manifest_sha256": _sha256(RUN_RELATIVE / "manifest.json"),
        "run_summary_sha256": _sha256(RUN_RELATIVE / "summary.json"),
        "claim_sha256": _sha256(CLAIM),
        "execution_audit_sha256": execution_audit_sha,
        "archived_analysis_sha256": _sha256(ARCHIVED_ANALYSIS),
    }


def _first_sentence(text: str) -> str:
    match = FIRST_SENTENCE.search(text)
    return text[: match.end()] if match else text


def _anchor_present(text: str, anchor: str) -> bool:
    return bool(
        re.search(r"(?<![A-Za-z0-9])" + re.escape(anchor) + r"(?![A-Za-z0-9])", text)
    )


def _rescore(started: dict, raw: dict, archived: dict) -> dict:
    response = raw["response"]
    text = response["content"].strip()
    assessable = bool(text) and response.get("truncated") is not True
    anchors = {
        "A": started["anchors"]["current"]["A"],
        "B": started["anchors"]["current"]["B"],
        "H1": started["anchors"]["history"]["aligned"],
        "H2": started["anchors"]["history"]["conflict"],
        "H3": started["anchors"]["history"]["irrelevant"],
    }
    first = _first_sentence(text) if assessable else ""
    found = [key for key, anchor in anchors.items() if _anchor_present(first, anchor)]
    selected = found[0] if len(found) == 1 else None
    if not assessable:
        category = "MISSING"
        preferred = any_current = exact = unresolved = None
    elif len(found) > 1:
        category = "MULTIPLE"
        preferred = any_current = exact = 0
        unresolved = 1
    elif selected in ("A", "B"):
        category = (
            "CURRENT_PREFERRED"
            if selected == started["preferred_option"]
            else "CURRENT_NONPREFERRED"
        )
        preferred = int(category == "CURRENT_PREFERRED")
        any_current = 1
        expected = (
            f"Option {selected} [{anchors[selected]}] \u2014 "
            f"{started['options'][selected]['canonical']}."
        )
        exact = int(first.strip() == expected)
        unresolved = 0
    elif selected is not None:
        category = "ARCHIVED"
        preferred = any_current = exact = 0
        unresolved = 0
    else:
        category = "NONE"
        preferred = any_current = exact = 0
        unresolved = 1

    automatic = archived["automatic_score"]
    comparisons = {
        "preferred_current_anchor_selection": preferred,
        "any_current_anchor_selection": any_current,
        "selection_category": category,
        "exact_current_label_name_consistency": exact,
        "first_sentence_anchor_count": len(found),
        "unresolved_or_multiple": unresolved,
    }
    for name, value in comparisons.items():
        _require(value == automatic[name], f"Rescore differs for {started['request_id']}:{name}")
    if selected in ("A", "B"):
        _require(
            automatic["selected_anchor"] == anchors[selected]
            and automatic["selected_identity"] == selected
            and automatic["selected_scope"] == "CURRENT",
            f"Selected current identity differs for {started['request_id']}",
        )
    elif selected is None:
        _require(
            automatic["selected_anchor"] is None
            and automatic["selected_identity"] is None
            and automatic["selected_scope"] is None,
            f"Unresolved selection differs for {started['request_id']}",
        )
    return {
        "request_id": started["request_id"],
        "case_id": started["case_id"],
        "persona_id": started["persona_id"],
        "task_family": started["task_family"],
        "arm": started["arm"],
        "selected_identity": selected,
        "selection_category": category,
        "preferred_current_anchor_selection": preferred,
        "any_current_anchor_selection": any_current,
        "exact_current_label_name_consistency": exact,
        "first_sentence": first,
        "raw_text": text,
        "preferred_option": started["preferred_option"],
        "preferred_name": started["options"][started["preferred_option"]]["canonical"],
        "generated_tokens": response["tokens_predicted"],
        "latency_seconds": raw["latency_seconds"],
        "stop_reason": response["stop_type"],
    }


def _estimate(
    rows: list[dict],
    weights: dict[str, float],
    metric: str,
    personas: list[str] | None = None,
) -> dict:
    by_case: dict[str, dict] = defaultdict(dict)
    case_persona = {}
    for row in rows:
        by_case[row["case_id"]][row["arm"]] = row[metric]
        case_persona[row["case_id"]] = row["persona_id"]
    cases = []
    for case_id in sorted(by_case):
        values = by_case[case_id]
        _require(all(arm in values for arm in weights), f"Incomplete planned case: {case_id}")
        complete = True
        observed = lower = upper = 0.0
        for arm, coefficient in weights.items():
            value = values[arm]
            if value is None:
                complete = False
                lower += min(0.0, coefficient)
                upper += max(0.0, coefficient)
            else:
                observed += coefficient * value
                lower += coefficient * value
                upper += coefficient * value
        cases.append(
            {
                "case_id": case_id,
                "persona_id": case_persona[case_id],
                "contribution": observed if complete else None,
                "logical_lower": lower,
                "logical_upper": upper,
            }
        )

    personas = personas or sorted({row["persona_id"] for row in rows})

    def summarize(units: list[dict]) -> dict:
        complete = [x["contribution"] for x in units if x["contribution"] is not None]
        return {
            "complete_case_estimate": sum(complete) / len(complete) if complete else None,
            "complete_cases": len(complete),
            "logical_lower": (
                sum(x["logical_lower"] for x in units) / len(units) if units else None
            ),
            "logical_upper": (
                sum(x["logical_upper"] for x in units) / len(units) if units else None
            ),
        }

    overall = summarize(cases)
    leave_one_out = {}
    for persona in personas:
        leave_one_out[persona] = summarize(
            [case for case in cases if case["persona_id"] != persona]
        )
    points = [
        x["complete_case_estimate"]
        for x in leave_one_out.values()
        if x["complete_case_estimate"] is not None
    ]
    return {
        "metric": metric,
        "weights": weights,
        "eligible_cases": len(cases),
        "complete_cases": overall["complete_cases"],
        "unresolved_cases": len(cases) - overall["complete_cases"],
        "complete_case_estimate": overall["complete_case_estimate"],
        "logical_lower": overall["logical_lower"],
        "logical_upper": overall["logical_upper"],
        "case_contributions": cases,
        "leave_one_persona_out": leave_one_out,
        "leave_one_persona_out_point_estimate_range": (
            [min(points), max(points)] if points else [None, None]
        ),
    }


def _compare_estimate(reproduced: dict, archived: dict, label: str) -> None:
    scalar_fields = (
        "metric",
        "eligible_cases",
        "complete_cases",
        "unresolved_cases",
        "complete_case_estimate",
        "logical_lower",
        "logical_upper",
    )
    for field in scalar_fields:
        _require(
            _same_number(reproduced[field], archived[field]),
            f"Estimate differs: {label}:{field}",
        )
    _require(set(reproduced["weights"]) == set(archived["weights"]), f"Weights differ: {label}")
    for arm, value in reproduced["weights"].items():
        _require(_same_number(value, archived["weights"][arm]), f"Weight differs: {label}:{arm}")

    archived_cases = {x["case_id"]: x for x in archived["case_contributions"]}
    _require(len(archived_cases) == len(reproduced["case_contributions"]), f"Cases differ: {label}")
    for case in reproduced["case_contributions"]:
        prior = archived_cases[case["case_id"]]
        for field in ("persona_id", "contribution", "logical_lower", "logical_upper"):
            _require(
                _same_number(case[field], prior[field]),
                f"Case contribution differs: {label}:{case['case_id']}:{field}",
            )

    _require(
        set(reproduced["leave_one_persona_out"])
        == set(archived["leave_one_persona_out"]),
        f"LOPO personas differ: {label}",
    )
    for persona, result in reproduced["leave_one_persona_out"].items():
        prior = archived["leave_one_persona_out"][persona]
        for field in (
            "complete_case_estimate",
            "complete_cases",
            "logical_lower",
            "logical_upper",
        ):
            _require(
                _same_number(result[field], prior[field]),
                f"LOPO differs: {label}:{persona}:{field}",
            )
    for index in (0, 1):
        _require(
            _same_number(
                reproduced["leave_one_persona_out_point_estimate_range"][index],
                archived["leave_one_persona_out_point_estimate_range"][index],
            ),
            f"LOPO range differs: {label}",
        )


def _compact_estimate(value: dict) -> dict:
    return {
        "estimate": value["complete_case_estimate"],
        "complete_cases": value["complete_cases"],
        "unresolved_cases": value["unresolved_cases"],
        "logical_bounds": [value["logical_lower"], value["logical_upper"]],
        "leave_one_persona_out_point_estimate_range": value[
            "leave_one_persona_out_point_estimate_range"
        ],
    }


def _reproduce_estimates(rows: list[dict], archived: dict) -> tuple[dict, dict]:
    registered = {}
    strata = {}
    personas = sorted({row["persona_id"] for row in rows})
    _require(set(archived["registered_estimates"]) == set(WEIGHTS), "Estimand set changed")
    for name, weights in WEIGHTS.items():
        registered[name] = {}
        for metric in PRIMARY_METRICS:
            result = _estimate(rows, weights, metric, personas)
            _compare_estimate(result, archived["registered_estimates"][name][metric], f"{name}:{metric}")
            registered[name][metric] = _compact_estimate(result)

    families = sorted({row["task_family"] for row in rows})
    _require(set(families) == set(archived["task_family_strata"]), "Task strata changed")
    for family in families:
        family_rows = [row for row in rows if row["task_family"] == family]
        strata[family] = {}
        for name, weights in WEIGHTS.items():
            strata[family][name] = {}
            for metric in PRIMARY_METRICS:
                result = _estimate(family_rows, weights, metric, personas)
                _compare_estimate(
                    result,
                    archived["task_family_strata"][family][name][metric],
                    f"{family}:{name}:{metric}",
                )
                strata[family][name][metric] = _compact_estimate(result)
    return registered, strata


def _binary_summary(values: list[int | None]) -> dict:
    resolved = [value for value in values if value is not None]
    missing = len(values) - len(resolved)
    return {
        "total_slots": len(values),
        "resolved_denominator": len(resolved),
        "missing": missing,
        "ones": sum(resolved),
        "zeros": len(resolved) - sum(resolved),
        "mean_resolved": sum(resolved) / len(resolved) if resolved else None,
        "logical_lower": sum(resolved) / len(values),
        "logical_upper": (sum(resolved) + missing) / len(values),
    }


def _condition_summary(rows: list[dict], archived: dict) -> dict:
    result = {}
    for arm in sorted({row["arm"] for row in rows}):
        arm_rows = [row for row in rows if row["arm"] == arm]
        result[arm] = {}
        for metric in (*PRIMARY_METRICS, "exact_current_label_name_consistency"):
            summary = _binary_summary([row[metric] for row in arm_rows])
            prior = archived["condition_summary"][arm][metric]
            for field, value in summary.items():
                _require(_same_number(value, prior[field]), f"Condition differs: {arm}:{metric}:{field}")
            result[arm][metric] = summary
        categories = dict(sorted(Counter(row["selection_category"] for row in arm_rows).items()))
        _require(
            categories == archived["condition_summary"][arm]["selection_categories"],
            f"Selection categories differ: {arm}",
        )
        result[arm]["selection_categories"] = categories
    return result


def _post_hoc_exploratory(rows: list[dict]) -> dict:
    history_rows = [row for row in rows if row["arm"] != "SF_NO_H"]
    placeholder_rows = [row for row in history_rows if ANCHOR_PLACEHOLDER.search(row["raw_text"])]
    any_exact_rows = [row for row in history_rows if "<exact" in row["raw_text"]]
    _require(len(history_rows) == 144, "History-conditioned post-hoc denominator changed")
    _require(len(placeholder_rows) == 24, "Literal anchor-placeholder count changed")

    no_history_preferred = [
        row
        for row in rows
        if row["arm"] == "SF_NO_H"
        and row["preferred_current_anchor_selection"] == 1
    ]
    name_matches = [
        row for row in no_history_preferred if row["preferred_name"] in row["first_sentence"]
    ]
    _require(
        len(no_history_preferred) == len(name_matches) == 23,
        "NO_H preferred-name post-hoc audit changed",
    )

    nonpreferred = [
        row for row in rows if row["selection_category"] == "CURRENT_NONPREFERRED"
    ]
    persona_distribution = dict(sorted(Counter(row["persona_id"] for row in nonpreferred).items()))
    case_distribution = dict(sorted(Counter(row["case_id"] for row in nonpreferred).items()))
    _require(
        len(nonpreferred) == 8 and persona_distribution == {"DSV_P02": 8},
        "Nonpreferred-selection concentration changed",
    )
    return {
        "classification": "POST_HOC_EXPLORATORY_NOT_PREREGISTERED_NOT_CONFIRMATORY",
        "separation_from_registered_estimands": True,
        "literal_anchor_placeholder_in_history_conditioned_outputs": {
            "source_event_kind": "disjoint_surface_validation_v3_raw_generation",
            "source_decoded_field": "event.data.response.content",
            "counting_stage": "AFTER_JSON_LOADS_ON_DECODED_UNICODE_TEXT",
            "escaped_json_representation_scanned": False,
            "case_sensitive_regex": ANCHOR_PLACEHOLDER_PATTERN,
            "exact_utf8_literal_hex": {
                "<exact A anchor>": "3c6578616374204120616e63686f723e",
                "<exact B anchor>": "3c6578616374204220616e63686f723e",
            },
            "scope_note": "Counts only literal A/B anchor placeholders; <exact A/B name> alone is outside this 24 numerator.",
            "hits": len(placeholder_rows),
            "denominator": len(history_rows),
            "fraction": len(placeholder_rows) / len(history_rows),
            "any_decoded_less_than_exact_substring_outputs": len(any_exact_rows),
            "arm_distribution": dict(sorted(Counter(row["arm"] for row in placeholder_rows).items())),
            "persona_distribution": dict(
                sorted(Counter(row["persona_id"] for row in placeholder_rows).items())
            ),
        },
        "no_history_preferred_anchor_with_preferred_name_in_first_sentence": {
            "hits": len(name_matches),
            "denominator": len(no_history_preferred),
            "fraction": len(name_matches) / len(no_history_preferred),
            "definition": "Among SF_NO_H responses with exactly the preferred current anchor, require the exact canonical preferred option name in the independently extracted first sentence.",
        },
        "current_nonpreferred_selection_concentration": {
            "count": len(nonpreferred),
            "persona_distribution": persona_distribution,
            "case_distribution": case_distribution,
            "interpretation_limit": "Observed concentration only; it is not a registered persona effect or causal explanation.",
        },
    }


def build_report() -> dict:
    frozen = _load(FROZEN_MANIFEST)
    claim = _load(CLAIM)
    archived = _load(ARCHIVED_ANALYSIS)
    run_manifest, events = _read_journal()
    hashes = _verify_file_bindings(frozen, claim, run_manifest)

    counts = Counter(event["kind"] for event in events)
    _require(dict(counts) == EXPECTED_EVENT_COUNTS, "Journal event accounting changed")
    _require(len(events) == 1557, "Journal event total changed")

    def indexed(kind: str) -> dict[str, dict]:
        records = [event["data"] for event in events if event["kind"] == kind]
        _require(len(records) == len({x["request_id"] for x in records}), f"Duplicate {kind}")
        return {x["request_id"]: x for x in records}

    starts = indexed("disjoint_surface_validation_v3_generation_started")
    raws = indexed("disjoint_surface_validation_v3_raw_generation")
    derived = indexed("disjoint_surface_validation_v3_result")
    live = indexed("live_prompt_verified")
    frozen_requests = {x["request_id"]: x for x in frozen["requests"]}
    _require(len(frozen_requests) == 168, "Frozen request count changed")
    _require(
        set(frozen_requests) == set(starts) == set(raws) == set(derived) == set(live),
        "Request ID sets differ",
    )
    _require(
        sorted(record["order"] for record in starts.values()) == list(range(168)),
        "Execution orders are not exactly 0..167",
    )
    for request_id, request in frozen_requests.items():
        _require(request == starts[request_id], f"Started request differs: {request_id}")
        _require(
            live[request_id]["token_ids_sha256"] == request["input_token_ids_sha256"],
            f"Live token IDs differ: {request_id}",
        )

    completion_responses = [
        event["data"]
        for event in events
        if event["kind"] == "http_response" and event["data"]["route"] == "/completion"
    ]
    raw_ordered = [
        event["data"]
        for event in events
        if event["kind"] == "disjoint_surface_validation_v3_raw_generation"
    ]
    _require(len(completion_responses) == len(raw_ordered) == 168, "Completion HTTP count changed")
    rows = []
    for http, raw in zip(completion_responses, raw_ordered, strict=True):
        _require(http["status"] == 200, "Non-200 completion response")
        body = json.loads(base64.b64decode(http["body_base64"]).decode("utf-8"))
        _require(body == raw["response"], f"HTTP body differs: {raw['request_id']}")
        request_id = raw["request_id"]
        result = derived[request_id]
        response = raw["response"]
        text = response["content"]
        _require(result["request_sha256"] == starts[request_id]["request_sha256"], "Request hash differs")
        _require(result["raw_response"] == text, f"Raw response differs: {request_id}")
        _require(
            result["raw_text_sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest(),
            f"Raw response hash differs: {request_id}",
        )
        _require(result["generated_token_ids"] == response["tokens"], "Returned IDs differ")
        _require(
            result["generated_tokens"] == response["tokens_predicted"] == len(response["tokens"]),
            "Generated token count differs",
        )
        _require(result["latency_seconds"] == raw["latency_seconds"], "Latency differs")
        _require(result["stop_reason"] == response["stop_type"], "Stop reason differs")
        rows.append(_rescore(starts[request_id], raw, result))

    condition_summary = _condition_summary(rows, archived)
    registered, strata = _reproduce_estimates(rows, archived)

    latency = sum(row["latency_seconds"] for row in rows)
    generated_tokens = sum(row["generated_tokens"] for row in rows)
    stop_reasons = dict(sorted(Counter(row["stop_reason"] for row in rows).items()))
    memory = [
        event["data"]
        for event in events
        if event["kind"] == "memory_observation" and event["data"].get("status") == "observed"
    ]
    peak_working_set = max(record["process"]["peak_working_set"] for record in memory)
    minimum_available = min(record["system"]["available_physical"] for record in memory)
    summary = json.loads(
        (PROJECT_ROOT / RUN_RELATIVE / "summary.json").read_text(encoding="utf-8")
    )
    _require(
        summary["attempted"] == summary["responses_received"] == summary["results"] == 168
        and summary["retries"] == summary["hidden_warmups"] == 0
        and summary["native_tokenizer_calls"] == summary["live_server_tokenizer_checks"] == 168
        and summary["tokenizer_operations_total"] == 336
        and summary["inference_wall_seconds"] == latency,
        "Run summary differs from raw events",
    )
    resources = archived["resource_observations"]
    independently_reproduced_resources = {
        "generated_tokens": generated_tokens,
        "inference_wall_seconds": latency,
        "mean_response_latency_seconds": latency / 168,
        "batch_wall_seconds": summary["batch_wall_seconds"],
        "native_stop_reason_distribution": stop_reasons,
        "server_peak_working_set_bytes": peak_working_set,
        "minimum_observed_available_physical_bytes": minimum_available,
    }
    comparisons = {
        "generated_tokens": generated_tokens,
        "maintained_attempt_inference_seconds": latency,
        "resolved_response_latency_seconds": latency,
        "mean_resolved_completion_seconds": latency / 168,
        "native_stop_reason_distribution": stop_reasons,
        "server_peak_working_set_bytes": peak_working_set,
        "minimum_observed_available_physical_bytes": minimum_available,
    }
    for field, value in comparisons.items():
        _require(_same_number(value, resources[field]), f"Resource differs: {field}")

    baseline = frozen["resource_budget"]["global_baseline"]
    cumulative_generations = baseline["generations_used"] + 168
    cumulative_seconds = baseline["inference_wall_seconds_used"] + latency
    _require(
        archived["cumulative_authorization_after"]["generations_used"] == cumulative_generations
        and archived["cumulative_authorization_after"]["inference_seconds_used"]
        == cumulative_seconds,
        "Cumulative budget differs",
    )

    post_hoc = _post_hoc_exploratory(rows)
    return {
        "schema_version": "personaslm_disjoint_surface_analysis_reproduction_v1",
        "status": "PASS_ZERO_DIFFERENCES",
        "reproduction_type": "READ_ONLY_INDEPENDENT_RECONSTRUCTION_FROM_FROZEN_MANIFEST_AND_RAW_JOURNAL",
        "independence_boundary": "Separate implementation in the same autonomous session; not an independent researcher, model, sample, human validation, or generation reproduction.",
        "analysis_code": {
            "path": Path(__file__).resolve().relative_to(PROJECT_ROOT).as_posix(),
            "sha256": _sha256(Path(__file__).resolve()),
            "controller_imported": False,
            "archived_analyze_called": False,
        },
        "test_code": {"path": TEST_PATH.as_posix(), "sha256": _sha256(TEST_PATH)},
        "execution_impact": {
            "model_calls": 0,
            "new_generations": 0,
            "network_calls": 0,
            "human_labels_created": 0,
            "historical_evidence_modified": False,
        },
        "run_directory": RUN_RELATIVE.as_posix(),
        "hash_verification": hashes,
        "journal_and_slot_accounting": {
            "journal_events": len(events),
            "journal_hash_chain": "PASS",
            "terminal_event_hash": events[-1]["event_hash"],
            "event_counts": dict(counts),
            "planned_slots": 168,
            "started": len(starts),
            "raw_generations": len(raws),
            "derived_results": len(derived),
            "live_tokenizer_checks": len(live),
            "completion_http_200_bodies_matching_raw_events": len(completion_responses),
            "native_tokenizer_calls": 168,
            "total_tokenizer_operations": 336,
            "retries": 0,
            "hidden_warmups": 0,
        },
        "score_reconstruction": {
            "responses_rescored_from_decoded_raw_text": len(rows),
            "automatic_score_discrepancies": 0,
            "condition_summary_discrepancies": 0,
            "registered_estimand_discrepancies": 0,
            "leave_one_persona_out_discrepancies": 0,
            "task_family_strata_discrepancies": 0,
            "resource_discrepancies": 0,
        },
        "condition_summary": condition_summary,
        "registered_automatic_estimates": registered,
        "task_family_strata": strata,
        "post_hoc_exploratory_audit": post_hoc,
        "resources": independently_reproduced_resources,
        "cumulative_authorization_after": {
            "generations_used": cumulative_generations,
            "generations_limit": baseline["generations_limit"],
            "generations_remaining": baseline["generations_limit"] - cumulative_generations,
            "inference_seconds_used": cumulative_seconds,
            "inference_seconds_limit": baseline["inference_wall_seconds_ceiling"],
            "inference_seconds_remaining": baseline["inference_wall_seconds_ceiling"]
            - cumulative_seconds,
        },
        "scientific_limits": [
            "The registered estimates concern synthetic, constrained anchor choices in one model with S=F=1; they are not a full S/F/H factorial or real-speaker result.",
            "Human semantic and Persona Fidelity labels remain pending.",
            "The three explicitly separated post-hoc audits are exploratory observations and cannot revise the registered estimands.",
            "Available physical memory fell to 289243136 bytes during execution; this is a repeat-run safety warning, not an analysis discrepancy.",
        ],
    }


def _write_exclusive(path: Path, value: dict) -> None:
    target = path if path.is_absolute() else PROJECT_ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    report = build_report()
    _write_exclusive(arguments.output, report)
    output = arguments.output if arguments.output.is_absolute() else PROJECT_ROOT / arguments.output
    print(
        json.dumps(
            {
                "status": report["status"],
                "output": output.relative_to(PROJECT_ROOT).as_posix(),
                "sha256": _sha256(output),
                "model_calls": 0,
                "new_generations": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
