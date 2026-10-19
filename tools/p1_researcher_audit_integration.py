"""Preservation-first P1 researcher-import and temporal date-binding audit.

This utility never starts a model, opens the restricted unblinding key, joins
condition identities, or changes a historical score.  It validates the real
v3 researcher submission against the frozen blinded sheet, creates a clearly
labelled compatibility view for the frozen Stage A validator, and records a
static implementation audit of the historical automatic scorer.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE_A = ROOT / "docs/validation/p1/blinded_audit_stage_a_v1"
REVIEW = STAGE_A / "blinded_researcher_audit_RESEARCHER_FILLED_DATE_RULE_v3.csv"
BLANK = STAGE_A / "blinded_researcher_audit_v1.csv"
PROPOSALS = STAGE_A / "PersonaSLM_six_proposals_NOT_APPLIED_v3.csv"
LEDGER = STAGE_A / "authorization_ledger_stage_A_v1.json"
MANIFEST_INDEX = STAGE_A / "manifest_index_frozen_v1.json"
DEFAULT_OUTPUT = ROOT / "docs/validation/p1/researcher_audit_integration_v1"
RECOVERY_REPORT = ROOT / "docs/P1_research_recovery_and_stage_B_readiness_report_v1.md"
DEVELOPMENT_LOG = ROOT / "docs/research_development_log.md"

EXPECTED_REVIEW_SHA256 = "b0e8cff9b80bdb6055d81333fc0a42a3117e1d5a3bc043f7dcce4cd9aa8ecb84"
EXPECTED_PROPOSALS_SHA256 = "49d423a8f3ec10ce52c64d9cd9561173773da012ef73d223c6b48cf4eb143275"
RESEARCHER = "Yaxin ZHENG"
REGISTERED_DATE = "2051-09-15"

IMMUTABLE_FIELDS = (
    "anonymous_review_id",
    "original_question",
    "registered_evaluation_date",
    "trusted_evidence",
    "frozen_reference_answer",
    "complete_raw_model_response",
    "required_answer_components",
)
HUMAN_FIELDS = (
    "researcher_task_success_decision",
    "researcher_factual_decision",
    "researcher_temporal_decision",
    "researcher_failure_type",
    "researcher_comment",
)
V3_AUDIT_FIELDS = (
    "researcher_name",
    "scoring_date_source",
    "requested_dates_from_question",
    "multi_date_item",
    "component_requested_date",
    "registered_evaluation_date_used_for_scoring",
    "temporal_scoring_note",
    "historical_automatic_scorer_date_usage",
    "date_mismatch_risk",
    "date_binding_rule_status",
)
TASK_LABELS = {"Success", "Failure"}
AXIS_LABELS = {"Correct", "Incorrect"}
V3_FAILURE_TYPES = {"None", "Missing required component", "Temporal selection error"}
DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

LEGACY_TASK_LABELS = {"Success": "CORRECT", "Failure": "INCORRECT"}
LEGACY_AXIS_LABELS = {"Correct": "CORRECT", "Incorrect": "INCORRECT"}
LEGACY_FAILURE_TYPES = {
    "None": "",
    "Missing required component": "Missing required component",
    "Temporal selection error": "Wrong date attribution",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames is not None, f"CSV header missing: {relative(path)}")
        return list(reader.fieldnames), list(reader)


def canonical_digest(row: dict[str, str], fields: tuple[str, ...]) -> str:
    payload = {field: row[field] for field in fields}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def json_load(value: str, label: str, review_id: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid {label} JSON: {review_id}") from error


def question_dates(question: str, review_id: str) -> list[str]:
    dates: list[str] = []
    for candidate in DATE_PATTERN.findall(question):
        try:
            date.fromisoformat(candidate)
        except ValueError as error:
            raise ValueError(f"Invalid question date {candidate}: {review_id}") from error
        if candidate not in dates:
            dates.append(candidate)
    require(bool(dates), f"No explicit requested date in question: {review_id}")
    return dates


def parse_components(row: dict[str, str]) -> list[dict[str, str]]:
    review_id = row["anonymous_review_id"]
    components = json_load(row["required_answer_components"], "required_answer_components", review_id)
    require(isinstance(components, list) and components, f"Empty component list: {review_id}")
    seen: set[str] = set()
    for component in components:
        require(isinstance(component, dict), f"Non-object component: {review_id}")
        for field in ("component", "requested_date", "requirement"):
            require(isinstance(component.get(field), str) and component[field].strip(), f"Missing component {field}: {review_id}")
        require(component["component"] not in seen, f"Duplicate component name: {review_id}")
        seen.add(component["component"])
        try:
            date.fromisoformat(component["requested_date"])
        except ValueError as error:
            raise ValueError(f"Invalid component date: {review_id}") from error
    references = json_load(row["frozen_reference_answer"], "frozen_reference_answer", review_id)
    require(isinstance(references, list) and references, f"Empty frozen reference: {review_id}")
    reference_components = {entry.get("component") for entry in references if isinstance(entry, dict)}
    require(reference_components == seen, f"Reference/component mismatch: {review_id}")
    return components


def require_reference_evidence_complete(case: dict[str, Any]) -> None:
    available = {fact["source_id"] for fact in case["facts"]}
    for component in case["reference"]:
        missing = [source_id for source_id in component["source_ids"] if source_id not in available]
        require(
            not missing,
            "Reference source missing from evidence: " + ",".join(missing),
        )


def compatibility_row(row: dict[str, str], legacy_fields: list[str]) -> dict[str, str]:
    converted = {field: row[field] for field in IMMUTABLE_FIELDS}
    converted["researcher_task_success_decision"] = LEGACY_TASK_LABELS[row["researcher_task_success_decision"]]
    converted["researcher_factual_decision"] = LEGACY_AXIS_LABELS[row["researcher_factual_decision"]]
    converted["researcher_temporal_decision"] = LEGACY_AXIS_LABELS[row["researcher_temporal_decision"]]
    converted["researcher_failure_type"] = LEGACY_FAILURE_TYPES[row["researcher_failure_type"]]
    converted["researcher_comment"] = row["researcher_comment"]
    require(list(converted) == legacy_fields, "Compatibility view changed Stage A column inventory")
    return converted


def validate_researcher_submission(
    review_path: Path = REVIEW,
    blank_path: Path = BLANK,
    proposals_path: Path = PROPOSALS,
) -> dict[str, Any]:
    """Validate v3 without opening the restricted unblinding key."""
    review_fields, review_rows = read_csv(review_path)
    blank_fields, blank_rows = read_csv(blank_path)
    expected_fields = blank_fields + list(V3_AUDIT_FIELDS)
    require(review_fields == expected_fields, "Unexpected v3 column inventory or order")
    require(tuple(blank_fields) == IMMUTABLE_FIELDS + HUMAN_FIELDS, "Frozen blank-sheet schema changed")
    require(sha256(review_path) == EXPECTED_REVIEW_SHA256, "Completed v3 review SHA-256 mismatch")
    require(sha256(proposals_path) == EXPECTED_PROPOSALS_SHA256, "Proposal comparison SHA-256 mismatch")
    require(len(review_rows) == len(blank_rows) == 32, "Expected exactly 32 review records")

    review_ids = [row["anonymous_review_id"] for row in review_rows]
    blank_ids = [row["anonymous_review_id"] for row in blank_rows]
    require(len(set(review_ids)) == 32, "Duplicate anonymous_review_id in v3 review")
    require(set(review_ids) == set(blank_ids), "v3 anonymous ID inventory differs from frozen blind sheet")
    require(review_ids == blank_ids, "v3 row shuffle/order differs from frozen blind sheet")
    blank_by_id = {row["anonymous_review_id"]: row for row in blank_rows}

    imported: list[dict[str, Any]] = []
    date_records: list[dict[str, Any]] = []
    for row in review_rows:
        review_id = row["anonymous_review_id"]
        baseline = blank_by_id[review_id]
        for field in IMMUTABLE_FIELDS:
            require(row[field] == baseline[field], f"Frozen scientific field changed: {review_id} {field}")
        require(row["researcher_task_success_decision"] in TASK_LABELS, f"Invalid task-success label: {review_id}")
        require(row["researcher_factual_decision"] in AXIS_LABELS, f"Invalid factual label: {review_id}")
        require(row["researcher_temporal_decision"] in AXIS_LABELS, f"Invalid temporal label: {review_id}")
        require(row["researcher_failure_type"] in V3_FAILURE_TYPES, f"Invalid v3 failure type: {review_id}")
        require(bool(row["researcher_comment"].strip()), f"Missing researcher comment: {review_id}")
        require(row["researcher_name"] == RESEARCHER, f"Unexpected researcher identity: {review_id}")
        if row["researcher_task_success_decision"] == "Success":
            require(
                row["researcher_failure_type"] == "None"
                and row["researcher_factual_decision"] == "Correct"
                and row["researcher_temporal_decision"] == "Correct",
                f"Inconsistent successful v3 decision: {review_id}",
            )
        else:
            require(row["researcher_failure_type"] != "None", f"Failure lacks a failure type: {review_id}")

        require(row["registered_evaluation_date"] == REGISTERED_DATE, f"Unexpected registered date: {review_id}")
        dates = question_dates(row["original_question"], review_id)
        components = parse_components(row)
        component_dates = [component["requested_date"] for component in components]
        require(all(component_date in dates for component_date in component_dates), f"Component date absent from question: {review_id}")
        expected_component_dates = "; ".join(
            f"{component['component']}={component['requested_date']}" for component in components
        )
        require(row["requested_dates_from_question"] == "|".join(dates), f"Question-date metadata mismatch: {review_id}")
        require(row["component_requested_date"] == expected_component_dates, f"Component-date metadata mismatch: {review_id}")
        require(row["multi_date_item"] == ("Yes" if len(dates) > 1 else "No"), f"Multi-date flag mismatch: {review_id}")
        require(row["scoring_date_source"] == "original_question", f"Wrong scoring-date source: {review_id}")
        require(row["registered_evaluation_date_used_for_scoring"] == "No", f"Registered-date policy mismatch: {review_id}")
        require(bool(row["temporal_scoring_note"].strip()), f"Missing temporal note: {review_id}")
        require(row["historical_automatic_scorer_date_usage"] == "NOT_AUDITED", f"Historical-code status overstated: {review_id}")
        require(
            row["date_binding_rule_status"] == "RULE_SPECIFIED__HISTORICAL_SCORER_NOT_CODE_AUDITED",
            f"Date-binding status mismatch: {review_id}",
        )
        expected_risk = "YES" if any(component_date != row["registered_evaluation_date"] for component_date in component_dates) else "NO"
        require(row["date_mismatch_risk"] == expected_risk, f"Date-mismatch risk mismatch: {review_id}")

        imported.append(
            {
                "anonymous_review_id": review_id,
                "immutable_display_fields_sha256": canonical_digest(row, IMMUTABLE_FIELDS),
                "researcher_judgments": {field: row[field] for field in HUMAN_FIELDS},
                "researcher_name": row["researcher_name"],
                "stage_a_compatibility_view": {
                    "researcher_task_success_decision": LEGACY_TASK_LABELS[row["researcher_task_success_decision"]],
                    "researcher_factual_decision": LEGACY_AXIS_LABELS[row["researcher_factual_decision"]],
                    "researcher_temporal_decision": LEGACY_AXIS_LABELS[row["researcher_temporal_decision"]],
                    "researcher_failure_type": LEGACY_FAILURE_TYPES[row["researcher_failure_type"]],
                },
            }
        )
        date_records.append(
            {
                "anonymous_review_id": review_id,
                "registered_evaluation_date": row["registered_evaluation_date"],
                "requested_dates_from_question": dates,
                "components": [
                    {"component": component["component"], "requested_date": component["requested_date"]}
                    for component in components
                ],
                "multi_date_item": row["multi_date_item"],
                "date_mismatch_risk": row["date_mismatch_risk"],
                "status": "PASS_COMPONENT_DATE_MATCHES_EXPLICIT_QUESTION_DATE",
            }
        )

    proposal_fields, proposal_rows = read_csv(proposals_path)
    expected_proposal_fields = [
        "source_row",
        "anonymous_review_id",
        "field",
        "researcher_original_value",
        "earlier_ai_patch_proposal",
        "is_different",
        "requires_researcher_decision",
    ]
    require(proposal_fields == expected_proposal_fields, "Unexpected proposal comparison schema")
    require(len(proposal_rows) == 13 and len({row["anonymous_review_id"] for row in proposal_rows}) == 6, "Expected six proposal records")
    review_by_id = {row["anonymous_review_id"]: row for row in review_rows}
    for proposal in proposal_rows:
        review_id = proposal["anonymous_review_id"]
        require(review_id in review_by_id, f"Proposal references unknown review ID: {review_id}")
        require(proposal["field"] in review_by_id[review_id], f"Proposal references unknown field: {review_id}")
        require(proposal["is_different"] == "YES" and proposal["requires_researcher_decision"] == "YES", f"Proposal status mismatch: {review_id}")
        require(
            review_by_id[review_id][proposal["field"]] == proposal["researcher_original_value"],
            f"An earlier AI proposal appears to have been applied: {review_id} {proposal['field']}",
        )

    date_counter = Counter(tuple(record["requested_dates_from_question"]) for record in date_records)
    multi_date_count = sum(record["multi_date_item"] == "Yes" for record in date_records)
    march_count = sum("2051-03-15" in record["requested_dates_from_question"] for record in date_records)
    require(march_count == 16 and multi_date_count == 4, "Unexpected March/multi-date inventory")
    require(date_counter[(REGISTERED_DATE,)] == 16, "Unexpected September-only inventory")

    compatibility_rows = [compatibility_row(row, blank_fields) for row in review_rows]
    return {
        "review_fields": review_fields,
        "blank_fields": blank_fields,
        "review_rows": review_rows,
        "compatibility_rows": compatibility_rows,
        "import_artifact": {
            "version": "p1_researcher_annotation_import_v1",
            "researcher": RESEARCHER,
            "source": {
                "review_path": relative(review_path),
                "review_sha256": sha256(review_path),
                "blank_path": relative(blank_path),
                "blank_sha256": sha256(blank_path),
                "proposal_path": relative(proposals_path),
                "proposal_sha256": sha256(proposals_path),
            },
            "validation": {
                "record_count": len(review_rows),
                "unique_anonymous_review_ids": len(set(review_ids)),
                "original_shuffle_preserved": True,
                "immutable_scientific_fields_unchanged": True,
                "all_researcher_task_success_labels_present": True,
                "all_researcher_factual_labels_present": True,
                "all_researcher_temporal_labels_present": True,
                "all_failure_types_present": True,
                "all_comments_present": True,
                "restricted_unblinding_key_read": False,
                "old_ai_proposals_applied": False,
            },
            "submitted_label_distributions": {
                "task_success": dict(Counter(row["researcher_task_success_decision"] for row in review_rows)),
                "factual": dict(Counter(row["researcher_factual_decision"] for row in review_rows)),
                "temporal": dict(Counter(row["researcher_temporal_decision"] for row in review_rows)),
                "failure_type": dict(Counter(row["researcher_failure_type"] for row in review_rows)),
            },
            "proposal_comparison": {
                "proposal_field_rows": len(proposal_rows),
                "proposal_records": len({row["anonymous_review_id"] for row in proposal_rows}),
                "source_rows": sorted({int(row["source_row"]) for row in proposal_rows}),
                "all_researcher_original_values_preserved": True,
            },
            "compatibility_view": {
                "path": "researcher_annotation_stage_a_compatibility_v1.csv",
                "purpose": "Derived Stage A validator input; raw v3 submission remains authoritative and unchanged.",
                "task_mapping": LEGACY_TASK_LABELS,
                "axis_mapping": LEGACY_AXIS_LABELS,
                "failure_type_mapping": LEGACY_FAILURE_TYPES,
                "row_count": len(compatibility_rows),
                "condition_labels_present": False,
            },
            "records": imported,
        },
        "date_artifact": {
            "version": "p1_temporal_date_binding_audit_v1",
            "source_review_sha256": sha256(review_path),
            "registered_evaluation_date": REGISTERED_DATE,
            "record_count": len(date_records),
            "records_with_2051_03_15": march_count,
            "multi_date_records": multi_date_count,
            "september_only_records": date_counter[(REGISTERED_DATE,)],
            "status": "PASS_EXPLICIT_QUESTION_AND_COMPONENT_DATE_BINDING",
            "source_row_mapping": "NOT_ACCESSED; validation uses anonymous_review_id and direct question/component dates only.",
            "restricted_unblinding_key_read": False,
            "records": date_records,
        },
    }


def line_number(path: Path, needle: str) -> int:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if needle in line:
            return number
    raise ValueError(f"Expected source text not found: {relative(path)} :: {needle}")


def static_scorer_audit() -> dict[str, Any]:
    source_paths = {
        "historical_component_scorer": ROOT / "tools/p1_measurement_scoring.py",
        "historical_temporal_scorer_v2": ROOT / "tools/p1_measurement_scoring_v2.py",
        "historical_recovery_dispatch": ROOT / "tools/p1_recovery_measurement_v2.py",
        "historical_q1_design": ROOT / "tools/p1_recovery_design.py",
        "future_stage_b_dispatch": ROOT / "tools/p1_conditional_execution.py",
    }
    for path in source_paths.values():
        require("registered_evaluation_date" not in path.read_text(encoding="utf-8"), f"Unexpected registered-date consumption: {relative(path)}")
    original = source_paths["historical_component_scorer"]
    revised = source_paths["historical_temporal_scorer_v2"]
    recovery = source_paths["historical_recovery_dispatch"]
    design = source_paths["historical_q1_design"]
    stage_b = source_paths["future_stage_b_dispatch"]
    return {
        "version": "p1_automatic_scorer_date_usage_audit_v2",
        "supersedes_for_current_source_provenance": "automatic_scorer_date_usage_audit_v1.json",
        "scope": "Static source trace plus targeted offline regression tests; no raw output regeneration or restricted-key access.",
        "source_sha256": {relative(path): sha256(path) for path in source_paths.values()},
        "call_chain": [
            {
                "path": relative(recovery),
                "function": "automatic",
                "line": line_number(recovery, "def automatic("),
                "behavior": "D0/D1 call p1_measurement_scoring_v2.score with the selected case record; D2/D3 call the frozen exact-alias Q1 scorer.",
            },
            {
                "path": relative(revised),
                "function": "temporal_check",
                "line": line_number(revised, "def temporal_check("),
                "behavior": "Q0 temporal validity checks each recognized value against c['requested_date'] and matching evidence intervals.",
            },
            {
                "path": relative(original),
                "function": "score",
                "line": line_number(original, "supported=sum(dated_attachment"),
                "behavior": "Q0 dated-comparison task success binds march_bay to March and september_bay to September per required component.",
            },
            {
                "path": relative(design),
                "function": "reference_audit",
                "line": line_number(design, "date='2051-03-15'"),
                "behavior": "Reference witnesses are checked at a component-specific date before recovery scoring.",
            },
            {
                "path": relative(design),
                "function": "q1",
                "line": line_number(design, "Which bay is assigned"),
                "behavior": "Q1 freezes one requested-date question and exact aliases; prose/date additions are not silently normalized into success.",
            },
            {
                "path": relative(stage_b),
                "function": "automatic",
                "line": line_number(stage_b, "def automatic("),
                "behavior": "Future Stage B retains the same Q0/Q1 dispatch but has not been executed.",
            },
        ],
        "conclusion": {
            "registered_evaluation_date_substitution_confirmed": False,
            "historical_date_binding_status": "NO_CONFIRMED_REGISTERED_DATE_SUBSTITUTION_DEFECT",
            "corrected_scorer_created_in_this_audit": False,
            "historical_score_files_rewritten": False,
            "record_level_original_vs_corrected_comparison": "NOT_APPLICABLE: no new date-binding scorer version was justified; restricted anonymous-to-source mapping remains unopened.",
        },
        "known_scope_limits": [
            "The Q0 dated-comparison task matcher binds the two historical component names explicitly; that is valid for the frozen historical schema but is not a generic natural-language temporal parser.",
            "Q0 comparison temporal-consistency remains Unverifiable in the v2 secondary endpoint even when task-success binding is exact; this is a documented coverage limit, not a false Correct result.",
            "Q1 uses exact whole-answer aliases and does not provide an independent automatic temporal or semantic-completeness endpoint; submitted human temporal labels remain authoritative.",
        ],
        "restricted_unblinding_key_read": False,
    }


def stage_b_readiness() -> dict[str, Any]:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    index = json.loads(MANIFEST_INDEX.read_text(encoding="utf-8"))
    require(ledger["total_attempted"] == 72 and ledger["total_remaining"] == 88, "Stage A ledger total mismatch")
    require(ledger["remaining_authorization"] == {"A_C0": 0, "B_FACTORIAL": 80, "C_DIAGNOSTIC": 8}, "Stage A branch budget mismatch")
    require(ledger["stage_B_activated"] is False, "Stage B unexpectedly activated")
    manifests: dict[str, dict[str, Any]] = {}
    for name, entry in index["manifests"].items():
        path = ROOT / entry["path"]
        require(path.is_file(), f"Frozen manifest missing: {entry['path']}")
        actual_hash = sha256(path)
        require(actual_hash == entry["sha256"], f"Frozen manifest hash mismatch: {entry['path']}")
        manifests[name] = {
            "path": entry["path"],
            "requests": entry["requests"],
            "executed": entry["executed"],
            "sha256": actual_hash,
            "registered_hash_match": True,
        }
    return {
        "ledger": {
            "authorization_id": ledger["authorization_id"],
            "attempted": ledger["attempted"],
            "remaining_authorization": ledger["remaining_authorization"],
            "total_attempted": ledger["total_attempted"],
            "total_remaining": ledger["total_remaining"],
            "stage_B_activated": ledger["stage_B_activated"],
            "activation_required": ledger["activation_required"],
        },
        "manifests": manifests,
        "status": "READY_FOR_FUTURE_AUTHORIZED_UNBLINDING_ONLY",
        "current_blocker": "The required standalone researcher authorization phrase has not been supplied; no unblinding, condition selection, or Stage B inference is permitted.",
        "blinding_provenance_correction": {
            "prior_automated_test_key_parse_detected": True,
            "scope": "The interrupted-session regression command ran two legacy Stage A tests that loaded the real restricted key after the researcher review had already been completed.",
            "mapping_disclosed_in_test_output": False,
            "condition_level_result_calculated": False,
            "current_recovery_key_content_read": False,
            "current_recovery_check": "Existence and SHA-256 only; the tests were corrected to use hash-only or synthetic-key validation.",
            "scientific_effect": "Procedural blinding incident recorded; it did not alter the already submitted researcher judgments or activate Stage B.",
        },
        "restricted_unblinding_key_read": False,
    }


def write_json_new(path: Path, payload: dict[str, Any]) -> None:
    require(not path.exists(), f"Refusing to overwrite artifact: {relative(path)}")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_csv_new(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    require(not path.exists(), f"Refusing to overwrite artifact: {relative(path)}")
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_artifacts(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    require(not output_dir.exists(), f"Refusing to reuse output directory: {relative(output_dir)}")
    audit = validate_researcher_submission()
    output_dir.mkdir(parents=True)
    import_path = output_dir / "researcher_annotation_import_v1.json"
    date_path = output_dir / "date_binding_audit_v1.json"
    scorer_path = output_dir / "automatic_scorer_date_usage_audit_v1.json"
    compatibility_path = output_dir / "researcher_annotation_stage_a_compatibility_v1.csv"
    write_json_new(import_path, audit["import_artifact"])
    write_json_new(date_path, audit["date_artifact"])
    write_json_new(scorer_path, static_scorer_audit() | {"stage_b_readiness": stage_b_readiness()})
    write_csv_new(compatibility_path, audit["blank_fields"], audit["compatibility_rows"])
    return {
        "status": "PASS_NO_UNBLINDING_NO_INFERENCE",
        "output_dir": relative(output_dir),
        "artifacts": {relative(path): sha256(path) for path in (import_path, date_path, scorer_path, compatibility_path)},
        "restricted_unblinding_key_read": False,
    }


def write_scorer_audit(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    require(output_dir.is_dir(), "Researcher integration directory is absent")
    validate_researcher_submission()
    path = output_dir / "automatic_scorer_date_usage_audit_v2.json"
    payload = static_scorer_audit() | {"stage_b_readiness": stage_b_readiness()}
    write_json_new(path, payload)
    return {"status": "PASS", "path": relative(path), "sha256": sha256(path)}


def run_regression_tests(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    require(output_dir.is_dir(), "Build import/date/scorer artifacts before recording tests")
    evidence_path = output_dir / "regression_test_evidence_v1.json"
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_p1_researcher_audit_integration.py",
        "tests/test_p1_temporal_date_binding.py",
        "tests/test_p1_measurement_pilot.py",
        "tests/test_p1_recovery_v2.py",
        "tests/test_p1_recovery_measurement_v2.py",
        "tests/test_p1_recovery_2x2.py",
        "tests/test_p1_blinded_stage_a.py",
        "tests/test_p1_native_stop_diagnostic.py",
        "-q",
        "-ra",
        "-p",
        "no:cacheprovider",
    ]
    started = utc_now()
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
    payload = {
        "version": "p1_researcher_audit_regression_evidence_v1",
        "started_utc": started,
        "finished_utc": utc_now(),
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "scope": "Offline validation only; no model server, CPU generation, unblinding, or restricted-key parsing. Real-key checks are hash-only; label/mapping tests use synthetic keys.",
        "prior_evidence_correction": "regression_test_evidence_v1.json ran legacy tests that parsed the real key and therefore overstated restricted-key non-access; that evidence also failed two tests.",
        "restricted_unblinding_key_read": False,
    }
    version = 1
    while evidence_path.exists():
        version += 1
        evidence_path = output_dir / f"regression_test_evidence_v{version}.json"
    payload["version"] = f"p1_researcher_audit_regression_evidence_v{version}"
    write_json_new(evidence_path, payload)
    if result.returncode:
        raise RuntimeError(f"Regression tests failed; evidence preserved at {relative(evidence_path)}")
    return {"status": "PASS", "path": relative(evidence_path), "sha256": sha256(evidence_path), "stdout": result.stdout.strip()}


def git_value(*arguments: str) -> str:
    result = subprocess.run(["git", *arguments], cwd=ROOT, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def write_reproducibility_manifest(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    artifact_names = [
        "researcher_annotation_import_v1.json",
        "date_binding_audit_v1.json",
        "automatic_scorer_date_usage_audit_v1.json",
        "automatic_scorer_date_usage_audit_v2.json",
        "researcher_annotation_stage_a_compatibility_v1.csv",
    ]
    regression_names = sorted(path.name for path in output_dir.glob("regression_test_evidence_v*.json"))
    require(regression_names, "Required regression evidence absent")
    final_regression = json.loads((output_dir / regression_names[-1]).read_text(encoding="utf-8"))
    require(final_regression["returncode"] == 0, "Final regression evidence is not passing")
    artifact_names.extend(regression_names)
    for name in artifact_names:
        require((output_dir / name).is_file(), f"Required artifact absent: {name}")
    require(RECOVERY_REPORT.is_file(), "Consolidated recovery report is absent")
    require(DEVELOPMENT_LOG.is_file(), "Research development log is absent")
    stage_a_seal_path = STAGE_A / "reproducibility_manifest_stage_A_v1.json"
    stage_a_seal = json.loads(stage_a_seal_path.read_text(encoding="utf-8"))
    stage_a_changed: list[dict[str, str]] = []
    stage_a_missing: list[str] = []
    for recorded_path, expected_hash in stage_a_seal["artifact_sha256"].items():
        artifact_path = Path(recorded_path)
        if not artifact_path.is_absolute():
            artifact_path = ROOT / artifact_path
        if not artifact_path.is_file():
            stage_a_missing.append(recorded_path)
            continue
        actual_hash = sha256(artifact_path)
        if actual_hash != expected_hash:
            stage_a_changed.append(
                {"path": recorded_path, "expected_sha256": expected_hash, "actual_sha256": actual_hash}
            )
    require(
        {entry["path"] for entry in stage_a_changed}
        == {"docs/research_development_log.md", "tests/test_p1_blinded_stage_a.py"},
        "Unexpected Stage A seal difference after recovery",
    )
    require(not stage_a_missing, "Stage A sealed artifact is missing")

    manifest_version = 1
    manifest_path = output_dir / "reproducibility_manifest_v1.json"
    while manifest_path.exists():
        manifest_version += 1
        manifest_path = output_dir / f"reproducibility_manifest_v{manifest_version}.json"
    predecessor = None
    if manifest_version > 1:
        predecessor_path = output_dir / f"reproducibility_manifest_v{manifest_version - 1}.json"
        predecessor = {
            "path": relative(predecessor_path),
            "sha256": sha256(predecessor_path),
            "status": "Preserved predecessor; superseded after the final Stage A seal reconciliation and report/log clarification.",
        }
    payload = {
        "version": f"p1_researcher_audit_integration_reproducibility_v{manifest_version}",
        "created_utc": utc_now(),
        "researcher": RESEARCHER,
        "phase": "P1 only",
        "source_review_sha256": sha256(REVIEW),
        "stage_a_blank_sha256": sha256(BLANK),
        "proposal_comparison_sha256": sha256(PROPOSALS),
        "stage_a_ledger_sha256": sha256(LEDGER),
        "stage_a_manifest_index_sha256": sha256(MANIFEST_INDEX),
        "generated_artifact_sha256": {
            relative(output_dir / name): sha256(output_dir / name) for name in artifact_names
        },
        "recovery_report_sha256": sha256(RECOVERY_REPORT),
        "development_log_sha256_at_manifest_creation": sha256(DEVELOPMENT_LOG),
        "predecessor_manifest": predecessor,
        "stage_a_seal_reconciliation": {
            "seal_path": relative(stage_a_seal_path),
            "seal_sha256": sha256(stage_a_seal_path),
            "recorded_artifacts": len(stage_a_seal["artifact_sha256"]),
            "matching_artifacts": len(stage_a_seal["artifact_sha256"]) - len(stage_a_changed),
            "changed_artifacts": stage_a_changed,
            "missing_artifacts": stage_a_missing,
            "interpretation": "Both changes are recovery-governance changes: the append-only development log and the Stage A test correction that prevents real restricted-key parsing. Scientific frozen artifacts are unchanged.",
        },
        "authoritative_current_evidence": {
            "automatic_scorer_audit": "automatic_scorer_date_usage_audit_v2.json",
            "regression": regression_names[-1],
        },
        "preserved_incomplete_evidence": {
            "automatic_scorer_date_usage_audit_v1.json": "Stale transient p1_recovery_design.py source hash; preserved, not authoritative.",
            "regression_test_evidence_v1.json": "116 passed, 2 failed, 1 skipped; legacy tests parsed the restricted key despite a contrary metadata claim.",
        },
        "current_source_sha256": {
            relative(path): sha256(path)
            for path in (
                ROOT / "tools/p1_researcher_audit_integration.py",
                ROOT / "tools/p1_recovery_design.py",
                ROOT / "tools/p1_measurement_scoring.py",
                ROOT / "tools/p1_measurement_scoring_v2.py",
                ROOT / "tests/test_p1_researcher_audit_integration.py",
                ROOT / "tests/test_p1_temporal_date_binding.py",
                ROOT / "tests/test_p1_measurement_pilot.py",
                ROOT / "tests/test_p1_blinded_stage_a.py",
                ROOT / "tests/test_p1_native_stop_diagnostic.py",
            )
        },
        "commands": {
            "artifact_build_historical": [sys.executable, "tools/p1_researcher_audit_integration.py", "build"],
            "scorer_audit_v2": [sys.executable, "tools/p1_researcher_audit_integration.py", "scorer"],
            "regression": [sys.executable, "tools/p1_researcher_audit_integration.py", "test"],
            "manifest": [sys.executable, "tools/p1_researcher_audit_integration.py", "manifest"],
        },
        "git": {"head": git_value("rev-parse", "HEAD"), "branch": git_value("branch", "--show-current")},
        "controls": {
            "new_generations": 0,
            "unblinding_executed": False,
            "restricted_unblinding_key_read": False,
            "prior_automated_test_key_parse_detected_and_documented": True,
            "condition_level_results_calculated": False,
            "condition_selected": False,
            "historical_score_files_rewritten": False,
            "model_settings_changed": False,
            "remaining_inference_budget": 88,
        },
        "stage_b_readiness": {
            "status": "READY",
            "meaning": "Offline scientific/engineering prerequisites are satisfied; Stage B remains inactive and unauthorized.",
            "next_required_researcher_action": "A later standalone explicit activation message is required.",
            "live_execution_preflight": "The unchanged >=3 GiB available-RAM and runtime identity checks must pass after authorization; readiness does not waive them.",
        },
        "programme_status": {
            "P0": "FROZEN",
            "P1": "ACTIVE; Stage B inactive pending explicit authorization",
            "P2": "PAUSED",
            "P3": "PAUSED",
            "P4": "PAUSED",
            "P5": "COMPLETED_DIAGNOSTIC_ARCHIVED",
            "P6": "PAUSED",
        },
    }
    write_json_new(manifest_path, payload)
    return {"status": "PASS", "path": relative(manifest_path), "sha256": sha256(manifest_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "build", "scorer", "test", "manifest"))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    if arguments.action == "validate":
        audit = validate_researcher_submission()
        payload = {
            "status": "PASS",
            "record_count": audit["import_artifact"]["validation"]["record_count"],
            "restricted_unblinding_key_read": False,
        }
    elif arguments.action == "build":
        payload = build_artifacts(arguments.output_dir)
    elif arguments.action == "scorer":
        payload = write_scorer_audit(arguments.output_dir)
    elif arguments.action == "test":
        payload = run_regression_tests(arguments.output_dir)
    else:
        payload = write_reproducibility_manifest(arguments.output_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
