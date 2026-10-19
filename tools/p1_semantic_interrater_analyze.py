"""Analyze two independently locked semantic reviews without emitting private text."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import p1_semantic_interrater_prepare as preparation


ROOT = Path(__file__).resolve().parents[1]
TOOL = Path(__file__).resolve()
DEFAULT_PLAN = ROOT / (
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "semantic_interrater_calibration_plan_v1.json"
)
DEFAULT_READINESS = ROOT / (
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "semantic_interrater_analysis_readiness_v1.json"
)


def empty_matrix(labels: tuple[str, ...]) -> list[list[int]]:
    return [[0 for _ in labels] for _ in labels]


def matrix_for(pairs: list[tuple[str, str]], labels: tuple[str, ...]) -> list[list[int]]:
    positions = {label: index for index, label in enumerate(labels)}
    matrix = empty_matrix(labels)
    for left, right in pairs:
        matrix[positions[left]][positions[right]] += 1
    return matrix


def exact_agreement(matrix: list[list[int]]) -> dict:
    denominator = sum(sum(row) for row in matrix)
    numerator = sum(matrix[index][index] for index in range(len(matrix)))
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": None if denominator == 0 else round(numerator / denominator, 12),
        "status": "UNDEFINED_NO_COMMON_COMPLETED" if denominator == 0 else "DEFINED",
    }


def nominal_kappa(matrix: list[list[int]]) -> dict:
    total = sum(sum(row) for row in matrix)
    if total == 0:
        return {
            "status": "UNDEFINED_NO_COMMON_COMPLETED",
            "value": None,
            "observed_agreement": None,
            "expected_agreement": None,
        }
    row_totals = [sum(row) for row in matrix]
    column_totals = [sum(matrix[row][column] for row in range(len(matrix))) for column in range(len(matrix))]
    matches = sum(matrix[index][index] for index in range(len(matrix)))
    expected_numerator = sum(left * right for left, right in zip(row_totals, column_totals))
    denominator = total * total - expected_numerator
    observed = round(matches / total, 12)
    expected = round(expected_numerator / (total * total), 12)
    if denominator == 0:
        return {
            "status": "UNDEFINED_DEGENERATE_EXPECTED_AGREEMENT_ONE",
            "value": None,
            "observed_agreement": observed,
            "expected_agreement": expected,
        }
    return {
        "status": "DEFINED",
        "value": round((matches * total - expected_numerator) / denominator, 12),
        "observed_agreement": observed,
        "expected_agreement": expected,
    }


def metric_summary(pairs: list[tuple[str, str]], labels: tuple[str, ...]) -> dict:
    matrix = matrix_for(pairs, labels)
    return {
        "label_order": list(labels),
        "rows": "R1",
        "columns": "R2",
        "counts": matrix,
        "raw_exact_agreement": exact_agreement(matrix),
        "nominal_cohen_kappa": nominal_kappa(matrix),
    }


def validate_plan_and_deliveries(plan_path: Path, records: dict[str, tuple[Path, Path, Path]]) -> dict:
    plan = preparation.read_json(plan_path)
    if plan.get("schema_version") != "personaslm_semantic_interrater_calibration_plan_v1":
        raise ValueError("Unexpected inter-rater plan schema")
    if plan.get("status") != "READY_FOR_RECRUITMENT_ZERO_LABELS":
        raise ValueError("Inter-rater plan is not the frozen zero-label preparation")
    if plan.get("responses") != 16 or plan.get("completed_human_labels") != 0:
        raise ValueError("Inter-rater plan does not describe the blank 16-response cohort")
    if set(records) != set(preparation.SLOTS):
        raise ValueError("Both fixed reviewer slots are required")
    if plan.get("preparation_tool", {}).get("sha256") != preparation.sha256_file(
        Path(preparation.__file__)
    ):
        raise ValueError("Preparation tool hash differs from the frozen plan")

    id_hashes = set()
    for slot, (delivery, _, _) in records.items():
        planned = plan.get("reviewer_slots", {}).get(slot, {})
        delivery_files = planned.get("delivery_files", {})
        expected_files = {
            preparation.REVIEW_TEMPLATE,
            preparation.INSTRUCTIONS,
            preparation.PROVENANCE_TEMPLATE,
            preparation.DELIVERY_MANIFEST,
        }
        if set(delivery_files) != expected_files:
            raise ValueError(f"Frozen delivery inventory is incomplete for {slot}")
        for name, receipt in delivery_files.items():
            path = delivery / name
            if not path.is_file() or preparation.sha256_file(path) != receipt.get("sha256"):
                raise ValueError(f"Delivery file hash mismatch for {slot}/{name}")
            if path.stat().st_size != receipt.get("bytes"):
                raise ValueError(f"Delivery file size mismatch for {slot}/{name}")
        rows = preparation.read_csv(delivery / preparation.REVIEW_TEMPLATE, preparation.REVIEW_FIELDS)
        id_hashes.add(preparation.id_set_sha256({row["anonymous_response_id"] for row in rows}))
    if id_hashes != {plan.get("common_anonymous_id_set_sha256")}:
        raise ValueError("Delivery anonymous-ID set differs from the frozen plan")
    return plan


def private_values(records: dict[str, tuple[Path, Path, Path]]) -> set[str]:
    values = set()
    for delivery, completed, provenance in records.values():
        for path in (delivery / preparation.REVIEW_TEMPLATE, completed):
            for row in preparation.read_csv(path, preparation.REVIEW_FIELDS):
                for field in (
                    "anonymous_response_id",
                    "evaluation_material",
                    "raw_response",
                    "missing_reason",
                    "answer_span",
                    "reviewer_rationale",
                ):
                    if row[field]:
                        values.add(row[field])
        pseudonym = preparation.read_json(provenance).get("reviewer_pseudonym")
        if pseudonym:
            values.add(pseudonym)
    return values


def assert_public_safe(result: dict, records: dict[str, tuple[Path, Path, Path]]) -> None:
    serialized = json.dumps(result, ensure_ascii=False, sort_keys=True)
    for value in private_values(records):
        if json.dumps(value, ensure_ascii=False) in serialized:
            raise ValueError("Aggregate analysis leaks private reviewer material")
    forbidden_keys = {
        "anonymous_response_id",
        "evaluation_material",
        "raw_response",
        "missing_reason",
        "answer_span",
        "reviewer_rationale",
        "reviewer_pseudonym",
        "source_request_id",
        "candidate_request_id",
        "case_id",
    }

    def walk(value: object) -> None:
        if isinstance(value, dict):
            if forbidden_keys.intersection(value):
                raise ValueError("Aggregate analysis contains a forbidden private field")
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)

    walk(result)


def analyze(
    plan_path: Path,
    records: dict[str, tuple[Path, Path, Path]],
) -> dict:
    plan = validate_plan_and_deliveries(plan_path, records)
    validated = preparation.validate_completed_pair(records)
    reviews = {
        slot: {
            row["anonymous_response_id"]: row
            for row in preparation.read_csv(completed, preparation.REVIEW_FIELDS)
        }
        for slot, (_, completed, _) in records.items()
    }
    ids = set(reviews["R1"])
    if ids != set(reviews["R2"]):
        raise ValueError("Completed reviews do not cover the same anonymous IDs")

    both_completed = []
    both_unavailable = r1_only_unavailable = r2_only_unavailable = 0
    for anonymous in sorted(ids):
        left = reviews["R1"][anonymous]
        right = reviews["R2"][anonymous]
        left_done = left["annotation_status"] == "COMPLETED"
        right_done = right["annotation_status"] == "COMPLETED"
        if left_done and right_done:
            both_completed.append((left, right))
        elif not left_done and not right_done:
            both_unavailable += 1
        elif not left_done:
            r1_only_unavailable += 1
        else:
            r2_only_unavailable += 1

    answer_pairs = [
        (left["semantic_answer_state"], right["semantic_answer_state"])
        for left, right in both_completed
    ]
    completeness_pairs = [
        (left["semantic_completeness"], right["semantic_completeness"])
        for left, right in both_completed
    ]
    span_eligible = [
        (left["answer_span"], right["answer_span"])
        for left, right in both_completed
        if left["semantic_answer_state"] in preparation.VALUE_BEARING_STATES
        and right["semantic_answer_state"] in preparation.VALUE_BEARING_STATES
    ]
    span_matches = sum(left == right for left, right in span_eligible)
    span_denominator = len(span_eligible)

    result = {
        "schema_version": "personaslm_semantic_interrater_analysis_v1",
        "status": "DESCRIPTIVE_ANALYSIS_COMPLETE_NO_PASS_FAIL",
        "scope": plan["scope"],
        "coverage": {
            "unique_assigned_responses": len(ids),
            "assigned_annotations_per_reviewer": 16,
            "completed_annotations": {
                slot: validated[slot]["completed"] for slot in preparation.SLOTS
            },
            "unavailable_annotations": {
                slot: validated[slot]["unavailable"] for slot in preparation.SLOTS
            },
            "mutually_completed_responses": len(both_completed),
            "responses_with_any_unavailable_review": (
                both_unavailable + r1_only_unavailable + r2_only_unavailable
            ),
            "both_unavailable": both_unavailable,
            "r1_only_unavailable": r1_only_unavailable,
            "r2_only_unavailable": r2_only_unavailable,
        },
        "semantic_answer_state": metric_summary(answer_pairs, preparation.ANSWER_STATES),
        "semantic_completeness": metric_summary(completeness_pairs, preparation.COMPLETENESS),
        "answer_span_exact_agreement": {
            "scope": "Mutually completed rows where both raters selected value-bearing answer states; descriptive only.",
            "numerator": span_matches,
            "denominator": span_denominator,
            "value": None
            if span_denominator == 0
            else round(span_matches / span_denominator, 12),
            "status": "UNDEFINED_NO_ELIGIBLE_ROWS" if span_denominator == 0 else "DEFINED",
        },
        "source_hashes": {
            "frozen_plan_sha256": preparation.sha256_file(plan_path),
            "preparation_tool_sha256": preparation.sha256_file(Path(preparation.__file__)),
            "analysis_tool_sha256": preparation.sha256_file(TOOL),
            "review_inputs": {
                slot: {
                    "delivery_manifest_sha256": preparation.sha256_file(
                        delivery / preparation.DELIVERY_MANIFEST
                    ),
                    "completed_review_sha256": preparation.sha256_file(completed),
                    "reviewer_provenance_sha256": preparation.sha256_file(provenance),
                }
                for slot, (delivery, completed, provenance) in records.items()
            },
        },
        "interpretation": {
            "acceptance_threshold": None,
            "pass_fail_claim": False,
            "adjudication_performed": False,
            "reviewer_identities_disclosed": False,
            "record_level_labels_disclosed": False,
            "frozen_gate_changes": False,
        },
        "limitations": [
            "This development calibration is not independent experimental replication.",
            "Sparse categories can make nominal kappa unstable or undefined.",
            "Exact span agreement is descriptive and is not semantic boundary validation.",
        ],
        "execution_impact": {"scientific_model_generations": 0, "inference_seconds": 0.0},
    }
    assert_public_safe(result, records)
    return result


def readiness(plan_path: Path) -> dict:
    plan = preparation.read_json(plan_path)
    if plan.get("schema_version") != "personaslm_semantic_interrater_calibration_plan_v1":
        raise ValueError("Unexpected inter-rater plan schema")
    if plan.get("status") != "READY_FOR_RECRUITMENT_ZERO_LABELS":
        raise ValueError("Inter-rater preparation is not ready")
    if plan.get("human_reviewers_recruited") != 0 or plan.get("completed_human_labels") != 0:
        raise ValueError("Readiness receipt requires the zero-reviewer, zero-label plan")
    if plan.get("preparation_tool", {}).get("sha256") != preparation.sha256_file(
        Path(preparation.__file__)
    ):
        raise ValueError("Preparation tool hash differs from the frozen plan")
    return {
        "schema_version": "personaslm_semantic_interrater_analysis_readiness_v1",
        "status": "READY_FOR_TWO_VALIDATED_HUMAN_INPUTS_ZERO_RESULTS",
        "human_reviewers_recruited": 0,
        "completed_human_labels": 0,
        "agreement_results": 0,
        "requirements": [
            "Both completed review files must pass immutable-content and label-contract validation.",
            "Both provenance records must attest to distinct independent external humans and blind initial locks.",
            "Both delivery manifests and the common anonymous-ID set must match the frozen plan.",
        ],
        "analysis_contract": {
            "coverage": "Assigned, completed, mutually completed, and unavailable counts are retained.",
            "semantic_answer_state": "Fixed-order 7x7 matrix, raw exact agreement, nominal Cohen kappa.",
            "semantic_completeness": "Fixed-order 3x3 matrix, raw exact agreement, nominal Cohen kappa.",
            "degenerate_kappa": "Reported as undefined, never coerced to zero or one.",
            "answer_span": "Exact agreement only on mutually completed rows where both states are value-bearing; descriptive only.",
            "acceptance_threshold": None,
            "adjudication": False,
        },
        "privacy_contract": {
            "record_text_emitted": False,
            "rationales_or_spans_emitted": False,
            "anonymous_or_source_ids_emitted": False,
            "reviewer_identities_emitted": False,
            "protected_mapping_read_or_emitted": False,
        },
        "source_hashes": {
            "frozen_plan": {
                "path": preparation.display_path(plan_path),
                "sha256": preparation.sha256_file(plan_path),
            },
            "preparation_tool": {
                "path": preparation.display_path(Path(preparation.__file__)),
                "sha256": preparation.sha256_file(Path(preparation.__file__)),
            },
            "analysis_tool": {
                "path": preparation.display_path(TOOL),
                "sha256": preparation.sha256_file(TOOL),
            },
        },
        "execution_impact": {"scientific_model_generations": 0, "inference_seconds": 0.0},
        "limitations": [
            "This receipt contains no human result, agreement estimate, threshold decision, or adjudication.",
            "A completed analysis would remain development calibration rather than independent replication.",
        ],
    }


def write_exclusive(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(preparation.json_bytes(value))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    ready = subparsers.add_parser("readiness")
    ready.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    ready.add_argument("--output", type=Path, default=DEFAULT_READINESS)

    run = subparsers.add_parser("analyze")
    run.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    for slot in preparation.SLOTS:
        prefix = slot.lower()
        run.add_argument(f"--{prefix}-delivery", type=Path, required=True)
        run.add_argument(f"--{prefix}-review", type=Path, required=True)
        run.add_argument(f"--{prefix}-provenance", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.action == "readiness":
        result = readiness(args.plan)
    else:
        records = {
            slot: (
                getattr(args, f"{slot.lower()}_delivery"),
                getattr(args, f"{slot.lower()}_review"),
                getattr(args, f"{slot.lower()}_provenance"),
            )
            for slot in preparation.SLOTS
        }
        result = analyze(args.plan, records)
    write_exclusive(args.output, result)
    print(json.dumps({"status": result["status"], "output_sha256": preparation.sha256_file(args.output)}, sort_keys=True))


if __name__ == "__main__":
    main()
