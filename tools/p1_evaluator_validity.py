"""Aggregate-only P1 evaluator-validity evidence; no inference or row-level data."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from p1_measurement_scoring import wilson


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "stage_b": Path("docs/validation/p1/stage_b_v1/stage_b_decision_record_v1.json"),
    "p1b_crosstabs": Path(
        "docs/validation/p1b/confirmed_analysis_v1/analysis_v1/"
        "structural_semantic_crosstabs_v1.csv"
    ),
    "candidate1_audit": Path(
        "docs/validation/p1/model_feasibility_recovery_v1/candidate1_audit_v1.json"
    ),
    "candidate1_selection": Path(
        "docs/validation/p1/model_feasibility_recovery_v1/selection_after_candidate1_v1.json"
    ),
    "wave1_coverage": Path("docs/P1_wave1_evaluation_coverage.md"),
    "wave1_structural_semantic": Path("docs/P1_wave1_structural_semantic_comparison.md"),
}

# Explicit recovered aggregate only; record-level outputs are intentionally not read.
CANDIDATE1_AI_DIAGNOSTIC = {
    "current_value": 4,
    "outdated_value": 3,
    "incomplete": 1,
    "frozen_alias_recognized_within_semantically_classifiable": 2,
    "provenance_status": "POST_HOC_AI_ONLY_AGGREGATE_NOT_HUMAN_VALIDATED",
    "gate_effect": "NONE",
}


def _path(name: str) -> Path:
    return ROOT / SOURCES[name]


def _json(name: str) -> dict:
    return json.loads(_path(name).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _oq_summary(stage_b: dict) -> dict:
    rows = stage_b["condition_results"]
    _require(set(rows) == {"D0", "D1", "D2", "D3"}, "Unexpected O/Q conditions")
    denominator = sum(row["denominator"] for row in rows.values())
    agreements = sum(row["automatic_audited_exact_agreement"] for row in rows.values())
    automatic_successes = sum(row["original_automatic_task_success"] for row in rows.values())
    audited_successes = sum(row["researcher_audited_task_success"] for row in rows.values())
    _require(denominator == 32 and agreements == 31, "Unexpected O/Q aggregate inventory")
    _require(automatic_successes == audited_successes == 16, "Unexpected O/Q success totals")
    return {
        "exact_category_agreement": agreements,
        "denominator": denominator,
        "agreement_rate": agreements / denominator,
        "wilson_95_descriptive_iid_approximation": wilson(agreements, denominator),
        "automatic_task_success": automatic_successes,
        "audited_task_success": audited_successes,
        "scope": (
            "Single-reviewer aggregate agreement; not evaluator accuracy, independent "
            "replication, or inter-rater reliability."
        ),
    }


def _candidate1_summary(audit: dict, selection: dict) -> dict:
    gate = selection["gate"]
    _require(audit["integrity_status"] == gate["integrity_status"] == "PASS", "Candidate 1 integrity")
    _require(audit["attempted"] == gate["attempted"] == 8, "Candidate 1 inventory")
    _require(audit["success"] == gate["automatic_success"] == 1, "Candidate 1 gate mismatch")
    _require(audit["threshold"] == gate["threshold"] == 7, "Candidate 1 threshold mismatch")
    _require(audit["proceed"] is gate["proceed"] is False, "Candidate 1 gate changed")
    states = gate["answer_states"]
    frozen_covered = states.get("CURRENT_VALUE_ADOPTION", 0) + states.get(
        "OUTDATED_VALUE_ADOPTION", 0
    )
    diagnostic_complete = (
        CANDIDATE1_AI_DIAGNOSTIC["current_value"]
        + CANDIDATE1_AI_DIAGNOSTIC["outdated_value"]
    )
    diagnostic_covered = CANDIDATE1_AI_DIAGNOSTIC[
        "frozen_alias_recognized_within_semantically_classifiable"
    ]
    _require(
        frozen_covered == diagnostic_covered == 2 and diagnostic_complete == 7,
        "Candidate 1 aggregate changed",
    )
    return {
        "frozen_gate": {
            "automatic_success": gate["automatic_success"],
            "denominator": gate["attempted"],
            "threshold": gate["threshold"],
            "proceed": gate["proceed"],
            "status": "UNCHANGED_FAILED_1_OF_8",
        },
        "frozen_current_or_outdated_coverage": {
            "covered": frozen_covered,
            "denominator": gate["attempted"],
            "rate": frozen_covered / gate["attempted"],
        },
        "post_hoc_ai_diagnostic": dict(CANDIDATE1_AI_DIAGNOSTIC),
        "frozen_coverage_within_ai_diagnostic_complete_outputs": {
            "covered": diagnostic_covered,
            "denominator": diagnostic_complete,
            "rate": frozen_covered / diagnostic_complete,
            "scope": (
                "Cross-source descriptive coverage (2/7), not accuracy or a replacement "
                "for the frozen 1/8 gate result."
            ),
        },
    }


def _p1b_summary() -> dict:
    with _path("p1b_crosstabs").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    _require(rows and set(rows[0]) == {"axis", "structural_status", "semantic_label", "count"},
             "Unexpected P1b cross-table schema")

    axis_totals: Counter[str] = Counter()
    structural_by_axis: dict[str, Counter[str]] = defaultdict(Counter)
    semantic_by_axis: dict[str, Counter[str]] = defaultdict(Counter)
    cells: dict[tuple[str, str, str], int] = {}
    for row in rows:
        count = int(row["count"])
        _require(count >= 0, "Negative P1b count")
        axis = row["axis"]
        axis_totals[axis] += count
        structural_by_axis[axis][row["structural_status"]] += count
        semantic_by_axis[axis][row["semantic_label"]] += count
        cells[(axis, row["structural_status"], row["semantic_label"])] = count

    expected_axes = {
        "semantic_completeness",
        "answer_delivery",
        "factual_consistency",
        "temporal_consistency",
    }
    _require(set(axis_totals) == expected_axes, "Unexpected P1b axes")
    _require(set(axis_totals.values()) == {192}, "P1b axis denominator changed")
    structural_profiles = {tuple(sorted(counts.items())) for counts in structural_by_axis.values()}
    _require(len(structural_profiles) == 1, "P1b structural inventory differs by axis")
    structural_counts = dict(next(iter(structural_profiles)))

    return {
        "units_per_axis": 192,
        "axis_totals": dict(sorted(axis_totals.items())),
        "structural_counts_per_axis": structural_counts,
        "semantic_label_counts": {
            axis: dict(sorted(counts.items())) for axis, counts in sorted(semantic_by_axis.items())
        },
        "key_cross_cells": {
            "cross_turn_semantically_complete": cells[("semantic_completeness", "CROSS_TURN", "YES")],
            "cross_turn_full_answer": cells[("answer_delivery", "CROSS_TURN", "FULL_ANSWER")],
            "cross_turn_total": structural_counts["CROSS_TURN"],
        },
        "scope": "Aggregate diagnostic showing that structural status is not a semantic proxy.",
    }


def _wave1_summary() -> dict:
    coverage = _path("wave1_coverage").read_text(encoding="utf-8")
    structural = _path("wave1_structural_semantic").read_text(encoding="utf-8")
    factual = re.search(
        r"^\| Factual consistency \| (\d+)/(\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|",
        coverage,
        re.MULTILINE,
    )
    _require(factual is not None, "Wave 1 factual aggregate row missing")
    received, eligible, attempts, conclusive, unresolved_labels, human_needed = map(
        int, factual.groups()
    )
    _require((received, eligible, attempts, conclusive, unresolved_labels, human_needed)
             == (72, 72, 48, 15, 57, 57), "Wave 1 factual aggregate changed")

    statuses = {}
    for status in ("TRUNCATED", "CROSS_TURN", "AMBIGUOUS"):
        match = re.search(
            rf"^\| {status} \| (\d+) \| (\d+) \| (\d+) \|$", structural, re.MULTILINE
        )
        _require(match is not None, f"Wave 1 {status} aggregate row missing")
        complete, incomplete, total = map(int, match.groups())
        _require(complete + incomplete == total, f"Wave 1 {status} total mismatch")
        statuses[status] = {"complete": complete, "incomplete": incomplete, "total": total}
    _require(statuses == {
        "TRUNCATED": {"complete": 0, "incomplete": 17, "total": 17},
        "CROSS_TURN": {"complete": 78, "incomplete": 0, "total": 78},
        "AMBIGUOUS": {"complete": 1, "incomplete": 0, "total": 1},
    }, "Wave 1 structural-semantic aggregate changed")
    _require("95 native output-budget stops and one native EOS" in structural,
             "Wave 1 native termination aggregate changed")

    return {
        "automatic_factual_conclusive_coverage": {
            "conclusive": conclusive,
            "eligible": eligible,
            "rate": conclusive / eligible,
            "automatic_attempts": attempts,
            "unresolved_labels": unresolved_labels,
            "minimum_unresolved_human_judgments": human_needed,
        },
        "structural_semantic_counts": statuses,
        "native_termination_semantic_counts": {
            "output_budget": {"total": 95, "complete": 78, "incomplete": 17},
            "native_eos": {"total": 1, "complete": 1, "incomplete": 0},
        },
        "scope": (
            "Confirmed aggregate measurement distinction on saved Wave 1 outputs; "
            "not a termination-policy causal effect."
        ),
        "annotation_provenance": (
            "RESEARCHER_CONFIRMED_AI_ASSISTED_CODING_NOT_AN_INDEPENDENT_SECOND_RATING"
        ),
    }


def build_evidence() -> dict:
    """Reconstruct a safe aggregate evaluator-validity snapshot without side effects."""
    stage_b = _json("stage_b")
    audit = _json("candidate1_audit")
    selection = _json("candidate1_selection")
    oq = _oq_summary(stage_b)
    candidate1 = _candidate1_summary(audit, selection)
    p1b = _p1b_summary()
    wave1 = _wave1_summary()
    return {
        "version": "p1_aggregate_evaluator_validity_v1",
        "input_scope": {
            "sources": {
                name: {"path": path.as_posix(), "sha256": _sha256(ROOT / path)}
                for name, path in SOURCES.items()
            },
            "analysis_code": {
                "path": "tools/p1_evaluator_validity.py",
                "sha256": _sha256(Path(__file__)),
            },
            "method_dependency": {
                "path": "tools/p1_measurement_scoring.py",
                "function": "wilson",
                "sha256": _sha256(ROOT / "tools/p1_measurement_scoring.py"),
            },
            "restricted_or_raw_record_material_read": False,
        },
        "oq_audit": oq,
        "candidate1": candidate1,
        "wave1": wave1,
        "p1b_structural_semantic": p1b,
        "not_estimable": {
            "oq_confusion_sensitivity_specificity": {
                "status": "NOT_ESTIMABLE",
                "reason": "Condition totals and exact-category agreement do not identify the confusion matrix.",
            },
            "candidate1_semantic_accuracy": {
                "status": "NOT_ESTIMABLE",
                "reason": "The semantic diagnostic is post-hoc AI-only and has no human reference labels.",
            },
            "independent_human_inter_rater_reliability": {
                "status": "NOT_ESTIMABLE",
                "reason": "No second independent human rating aggregate is available.",
            },
            "sfh_factorial_effects": {
                "status": "NOT_ESTIMABLE",
                "reason": "The conditional 80-request factorial pilot was not executed.",
            },
        },
        "scientific_statuses": [
            {
                "status": "OQ_TASK_SUCCESS_NARROWLY_SUPPORTED_BY_AGGREGATE_AGREEMENT",
                "basis": (
                    f"{oq['exact_category_agreement']}/{oq['denominator']} exact-category "
                    "agreement from one researcher audit; not general evaluator accuracy."
                ),
            },
            {
                "status": "GENERAL_SEMANTIC_VALIDITY_INSUFFICIENT",
                "basis": (
                    "Existing aggregates do not identify a full confusion matrix, independent "
                    "inter-rater reliability, or semantic validity across outcome axes."
                ),
            },
            {
                "status": "CANDIDATE1_ENDPOINT_COVERAGE_INSUFFICIENT_REQUIRES_HUMAN_VALIDATION",
                "basis": (
                    "Frozen alias coverage is 2/8 and only 2/7 among the post-hoc AI-only "
                    "semantically classifiable outputs; this is descriptive coverage, not accuracy."
                ),
            },
        ],
        "historical_gate_integrity": {
            "stage_b_qualifying_configurations": len(stage_b["selection"]["qualifying_configurations"]),
            "stage_b_branch": stage_b["selection"]["branch"],
            "candidate1_gate_changed": False,
            "historical_threshold_changed": False,
        },
        "execution_impact": {
            "scientific_model_generations": 0,
            "model_inference_wall_seconds": 0,
            "authorization_debit_generations": 0,
            "network_calls": 0,
            "historical_outputs_modified": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(build_evidence(), indent=2, ensure_ascii=False))
