"""Post-hoc boundary sensitivity for the frozen 42-request mechanism study."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
import json
from pathlib import Path

import p1_persona_dialogue_mechanism as m
import p1_persona_dialogue_mechanism_analysis_v2 as a2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT = Path("docs/validation/p1/persona_dialogue_mechanism_v1")
REGISTRATION = OUT / "posthoc_boundary_sensitivity_registration_v1.json"
AMENDMENT = OUT / "posthoc_boundary_sensitivity_registration_amendment_v2.json"
ANALYSIS_V2 = OUT / "analysis_v2.json"
ANALYSIS_REPRODUCTION = OUT / "analysis_v2_reproduction_v1.json"
AUDIT = OUT / "execution_audit_v1.json"
TEST_SOURCE = Path("tests/test_p1_persona_dialogue_mechanism_boundary_sensitivity.py")
EXPECTED_OUTPUT = OUT / "posthoc_boundary_sensitivity_v1.json"

REGISTRATION_SHA256 = "a1bdafcbe5cfce9e33b134b274bb316a4c1075da23d50adce5d8cc8312de0c53"
AMENDMENT_SHA256 = "74a82d26e227ba5f34daf332188233f90982b4deb3ee67d05b0cbebc746c5ca6"
ANALYSIS_V2_SHA256 = "0e690501107c8031dd3774a8b7845e9b1cf2dc61d7969404d70738e7bb32cef6"
ANALYSIS_REPRODUCTION_SHA256 = "16d325bb519339239882afa60d2cf31eaef6e4c7082770dc2b6c20b26770af3a"
AUDIT_SHA256 = "6f2201716d7d7fbd1356827cd29891a1e1b000e44757fb16f5e7c329036a59e3"
BOUNDARY_LABEL = "BOUNDARY_CENSORED"
CONTRAST_PAIRS = {
    "F_H_STRUCTURE_minus_F_H_RAW": ("F_H_STRUCTURE", "F_H_RAW"),
    "F_H_REFRESH_minus_F_H_RAW": ("F_H_REFRESH", "F_H_RAW"),
    "F_H_RAW_minus_S_F_NO_H": ("F_H_RAW", "S_F_NO_H"),
    "S_F_H_minus_F_H_RAW": ("S_F_H", "F_H_RAW"),
    "S_H_minus_H_ONLY": ("S_H", "H_ONLY"),
}
EXPECTED_PREDICATE = {
    "all_conditions_required": True,
    "original_measurement_state": "BOUNDARY_CENSORED",
    "original_response_status": "AMBIGUOUS",
    "original_response_status_reasons_exact": ["unrecognized_line_label"],
    "persona_id": "SYN_VAL_D",
    "raw_response_nonempty": True,
    "raw_response_prefix_exact": "My pick:",
    "native_stop": True,
    "native_stop_type": "eos",
    "native_truncated": False,
    "first_span_equals_raw_response": True,
    "first_span_offsets_cover_full_raw_response": True,
    "first_reply_sha256_equals_raw_text_sha256": True,
    "removed_prefix_exact": "",
    "excluded_tail_exact": "",
    "raw_generation_and_result_text_and_token_ids_equal": True,
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def load(path):
    return json.loads((PROJECT_ROOT / path).read_text(encoding="utf-8"))


def sha256(path):
    return m.sha256(PROJECT_ROOT / path)


def validate_registration():
    require(sha256(REGISTRATION) == REGISTRATION_SHA256, "Sensitivity registration changed")
    require(sha256(AMENDMENT) == AMENDMENT_SHA256, "Sensitivity amendment changed")
    registration, amendment = load(REGISTRATION), load(AMENDMENT)
    require(registration["status"] ==
            "POSTHOC_OUTPUT_INFORMED_SENSITIVITY_REGISTERED_BEFORE_EXECUTION",
            "Sensitivity registration status")
    require(registration["inclusion_predicate"] == EXPECTED_PREDICATE,
            "Sensitivity inclusion predicate changed")
    require(amendment["status"] ==
            "CLERICAL_REQUEST_ID_CORRECTION_BEFORE_IMPLEMENTATION_OR_EXECUTION",
            "Sensitivity amendment status")
    require(amendment["parent_registration"] == {
        "path": REGISTRATION.as_posix(), "sha256": REGISTRATION_SHA256},
        "Sensitivity amendment parent changed")
    original_ids = set(registration["expected_selected_set"]["request_ids"])
    corrected_ids = (original_ids - {amendment["correction"]["remove_request_id"]} |
                     {amendment["correction"]["add_request_id"]})
    effective_ids = amendment["effective_expected_selected_set_request_ids"]
    require(corrected_ids == set(effective_ids) and len(effective_ids) == len(set(effective_ids)) and
            len(corrected_ids) == registration["expected_selected_set"]["count"] == 11,
            "Effective selected IDs changed")
    require(all(value is True for key, value in amendment["unchanged"].items()
                if key not in ("expected_count", "authorized_output_path",
                               "maximum_new_model_generations")) and
            amendment["unchanged"]["expected_count"] == 11,
            "Amendment changed registered fields")
    require(amendment["unchanged"]["authorized_output_path"] ==
            registration["authorized_output_path"] == EXPECTED_OUTPUT.as_posix() and
            amendment["unchanged"]["maximum_new_model_generations"] ==
            registration["maximum_new_model_generations"] == 0,
            "Output or generation authorization changed")
    bindings = registration["bindings"]
    evidence = {
        m.FROZEN: bindings["effective_manifest_sha256"],
        AUDIT: bindings["execution_audit_sha256"],
        ANALYSIS_V2: bindings["analysis_v2_sha256"],
        ANALYSIS_REPRODUCTION: bindings["analysis_v2_reproduction_sha256"],
        m.PARSER_CLARIFICATION: bindings["prospective_parser_clarification_v3_sha256"],
        Path(m.__file__).resolve(): bindings["frozen_runner_sha256"],
    }
    for path, expected in evidence.items():
        require(sha256(path) == expected, f"Registered sensitivity evidence changed: {path}")
    require(bindings["analysis_v2_sha256"] == ANALYSIS_V2_SHA256 and
            bindings["analysis_v2_reproduction_sha256"] == ANALYSIS_REPRODUCTION_SHA256 and
            bindings["execution_audit_sha256"] == AUDIT_SHA256,
            "Sensitivity evidence constants changed")
    folders = list((m.ROOT / "runs").glob("*"))
    require(len(folders) == 1 and folders[0].as_posix() == bindings["run_directory"],
            "Registered sensitivity run directory changed")
    require(set(registration["outcomes"]["arm_summaries"]) == set(m.PRIMARY_METRICS) and
            set(registration["outcomes"]["paired_contrasts"]) == set(CONTRAST_PAIRS),
            "Registered sensitivity outcomes changed")
    return registration, amendment


def authorization_requirements():
    registration, amendment = validate_registration()
    return {
        "schema_version": "personaslm_persona_dialogue_mechanism_boundary_sensitivity_authorization_v1",
        "status": "AUTHORIZED_BEFORE_POSTHOC_BOUNDARY_SENSITIVITY_EXECUTION",
        "authorized_action": "ZERO_GENERATION_REPLAY_AND_POSTHOC_BOUNDARY_SENSITIVITY",
        "implementation": {
            "tool": {"path": Path(__file__).resolve().relative_to(PROJECT_ROOT).as_posix(),
                     "sha256": m.sha256(Path(__file__))},
            "test": {"path": TEST_SOURCE.as_posix(), "sha256": sha256(TEST_SOURCE)},
        },
        "registration_chain": {
            "registration": {"path": REGISTRATION.as_posix(), "sha256": REGISTRATION_SHA256},
            "amendment": {"path": AMENDMENT.as_posix(), "sha256": AMENDMENT_SHA256},
        },
        "evidence_bindings": copy.deepcopy(registration["bindings"]),
        "effective_expected_selected_set_request_ids": copy.deepcopy(
            amendment["effective_expected_selected_set_request_ids"]),
        "inclusion_predicate": copy.deepcopy(registration["inclusion_predicate"]),
        "authorized_transformation": copy.deepcopy(registration["authorized_transformation"]),
        "authorized_output_path": EXPECTED_OUTPUT.as_posix(),
        "maximum_new_model_generations": 0,
        "network_calls": 0,
    }


def validate_authorization(path, output_path):
    authorization = load(path)
    for key, expected in authorization_requirements().items():
        require(authorization.get(key) == expected,
                f"Boundary-sensitivity authorization changed: {key}")
    require(authorization.get("researcher") == "Yaxin ZHENG",
            "Boundary-sensitivity researcher authorization missing")
    require(Path(output_path).as_posix() == EXPECTED_OUTPUT.as_posix(),
            "Boundary-sensitivity output path is not authorized")
    return authorization


def matches_inclusion(row, result, raw_record, registration):
    predicate = registration["inclusion_predicate"]
    require(predicate == EXPECTED_PREDICATE, "Unrecognized sensitivity predicate")
    raw = result["raw_response"]
    status = result["response_status"]
    span = status["first_span"]
    termination = result["raw_termination"]
    normalized = m.b.normalize_result(raw_record["response"])
    conditions = (
        result["automatic_score"]["measurement_state"] ==
            predicate["original_measurement_state"],
        status["status"] == predicate["original_response_status"],
        status["reasons"] == predicate["original_response_status_reasons_exact"],
        row["persona_id"] == predicate["persona_id"],
        bool(raw.strip()) is predicate["raw_response_nonempty"],
        raw.startswith(predicate["raw_response_prefix_exact"]),
        termination.get("stop") is predicate["native_stop"],
        termination.get("stop_type") == predicate["native_stop_type"],
        termination.get("truncated") is predicate["native_truncated"],
        span["text"] == raw,
        span["start"] == 0 and span["end"] == len(raw),
        result["first_reply_sha256"] == result["raw_text_sha256"],
        status["removed_prefix"] == predicate["removed_prefix_exact"],
        status["excluded_tail"] == predicate["excluded_tail_exact"],
        normalized["raw_response"] == raw and
            normalized["generated_token_ids"] == result["generated_token_ids"],
    )
    return all(conditions)


def apply_sensitivity(rows, results, raw_records, registration, scorer=None):
    scorer = scorer or m.automatic_score
    original, updated = copy.deepcopy(results), copy.deepcopy(results)
    selected = []
    for row in rows:
        request_id = row["request_id"]
        require(request_id in results and request_id in raw_records and
                results[request_id]["request_id"] == raw_records[request_id]["request_id"] == request_id,
                "Sensitivity replay identity mismatch")
        if not matches_inclusion(row, results[request_id], raw_records[request_id], registration):
            continue
        selected.append(request_id)
        span = results[request_id]["response_status"]["first_span"]["text"]
        updated[request_id]["automatic_score"] = scorer(row, span, assessable=True)
    selected_set = set(selected)
    for request_id in results:
        if request_id not in selected_set:
            require(updated[request_id] == original[request_id],
                    "Non-selected record changed")
        else:
            left, right = copy.deepcopy(updated[request_id]), copy.deepcopy(original[request_id])
            left.pop("automatic_score")
            right.pop("automatic_score")
            require(left == right, "Selected raw or non-score evidence changed")
    require(results == original, "Sensitivity mutated frozen replay records")
    return updated, selected


def _category_counts(scores):
    counts = dict(Counter(score["selection_category"] for score in scores))
    if None in counts:
        require(BOUNDARY_LABEL not in counts, "Boundary-label collision")
        counts[BOUNDARY_LABEL] = counts.pop(None)
    return counts


def aggregate_primary(rows, results):
    by_arm, by_case = defaultdict(list), defaultdict(dict)
    for row in rows:
        score = results[row["request_id"]]["automatic_score"]
        by_arm[row["arm"]].append(score)
        by_case[row["case_id"]][row["arm"]] = score
    arm_summary = {}
    for arm in sorted(by_arm):
        scores = by_arm[arm]
        arm_summary[arm] = {metric: m.binary_summary(scores, metric)
                            for metric in m.PRIMARY_METRICS}
        arm_summary[arm]["selection_categories"] = _category_counts(scores)
    contrasts = {name: {metric: m.paired_contrast(by_case, treatment, control, metric)
                         for metric in m.PRIMARY_METRICS}
                 for name, (treatment, control) in CONTRAST_PAIRS.items()}
    return {"primary_arm_summary": arm_summary, "primary_paired_contrasts": contrasts}


def side_by_side(archived_primary, recomputed_primary, sensitivity):
    require(archived_primary == recomputed_primary,
            "Recomputed registered primary analysis changed")
    return {"registered_primary": copy.deepcopy(archived_primary),
            "posthoc_boundary_sensitivity": copy.deepcopy(sensitivity)}


def assert_public_safe(value):
    forbidden = {"raw_response", "first_span", "generated_token_ids", "content", "prompt"}
    if isinstance(value, dict):
        require(not (set(value) & forbidden), "Sensitivity output embeds restricted raw material")
        for child in value.values():
            assert_public_safe(child)
    elif isinstance(value, list):
        for child in value:
            assert_public_safe(child)


def build_report(authorization_path, output_path):
    authorization = validate_authorization(authorization_path, output_path)
    registration, amendment = validate_registration()
    plan = load(m.FROZEN)
    folder, events, replay_rows, bodies = m.replay()
    attempted, raw_records, archived_results = m.inventory(plan, events)
    require(len(attempted) == len(raw_records) == len(archived_results) == bodies == 42,
            "Frozen replay is not complete 42/42")
    rows = [row for row, _, state in replay_rows if state == "COMPLETED"]
    results = {row["request_id"]: result for row, result, state in replay_rows
               if state == "COMPLETED"}
    sensitivity_results, selected = apply_sensitivity(
        rows, results, raw_records, registration)
    expected = amendment["effective_expected_selected_set_request_ids"]
    require(set(selected) == set(expected) and len(selected) == len(expected) == 11,
            "Observed sensitivity set differs from the amended registration")
    design_cases = {case["case_id"]: case for case in load(m.DESIGN)["cases"]}
    selected_rows = [row for row in rows if row["request_id"] in set(selected)]
    require(dict(Counter(row["arm"] for row in selected_rows)) ==
            registration["expected_selected_set"]["arm_counts"], "Selected arm counts changed")
    require(dict(Counter(design_cases[row["case_id"]]["history_regime"]
                         for row in selected_rows)) ==
            registration["expected_selected_set"]["history_regime_counts"],
            "Selected history-regime counts changed")

    primary_archive = load(ANALYSIS_V2)["analysis"]
    archived_primary = {key: copy.deepcopy(primary_archive[key]) for key in (
        "primary_arm_summary", "primary_paired_contrasts")}
    comparison = side_by_side(
        archived_primary, aggregate_primary(rows, results),
        aggregate_primary(rows, sensitivity_results))
    metric_changes = []
    for row in selected_rows:
        request_id = row["request_id"]
        before = results[request_id]["automatic_score"]
        after = sensitivity_results[request_id]["automatic_score"]
        metric_changes.append({"request_id": request_id, "case_id": row["case_id"],
            "arm": row["arm"], "history_regime": design_cases[row["case_id"]]["history_regime"],
            "raw_text_sha256": results[request_id]["raw_text_sha256"],
            "first_reply_sha256": results[request_id]["first_reply_sha256"],
            "original_measurement_state": before["measurement_state"],
            "sensitivity_measurement_state": after["measurement_state"],
            "sensitivity_selection_category": after["selection_category"],
            "primary_metrics": {metric: {"registered_primary": before[metric],
                                         "sensitivity": after[metric]}
                                for metric in m.PRIMARY_METRICS}})
    report = {
        "version": "p1_persona_dialogue_mechanism_posthoc_boundary_sensitivity_v1",
        "status": "COMPLETE_EXPLORATORY_POSTHOC_SENSITIVITY",
        "evidence_level": registration["evidence_level"],
        "authorization": {"path": Path(authorization_path).as_posix(),
                          "sha256": sha256(Path(authorization_path)),
                          "researcher": authorization["researcher"]},
        "registration_chain": authorization["registration_chain"],
        "evidence_bindings": copy.deepcopy(registration["bindings"]),
        "source_bindings": copy.deepcopy(authorization["implementation"]),
        "run_directory": folder.as_posix(), "replayed_results": 42,
        "selected_count": len(selected), "selected_request_ids": selected,
        "selected_record_changes": metric_changes,
        "primary_side_by_side": comparison,
        "inferential_policy": {"p_values": "NOT_COMPUTED", "estimation_first": True,
                               "registered_primary_remains_primary": True},
        "integrity": {"raw_outputs_changed": False, "token_ids_changed": False,
                      "nonselected_records_changed": False, "parser_changed": False,
                      "new_model_generations": 0, "network_calls": 0,
                      "raw_response_text_embedded": False},
        "interpretation_limits": copy.deepcopy(registration["interpretation_limits"]),
    }
    assert_public_safe(report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = build_report(args.authorization, args.output)
    a2.write_exclusive(args.output, report)
    print(json.dumps({"status": report["status"], "selected_count": report["selected_count"],
                      "new_model_generations": 0, "output": args.output.as_posix()}, indent=2))


if __name__ == "__main__":
    main()
