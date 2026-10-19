import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path("tools").resolve()))

import p1_evaluator_validity as validity


ARTIFACT = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/evaluator_validity_v1.json"
)


def evidence():
    return validity.build_evidence()


def test_saved_evidence_is_exactly_reproducible_from_safe_aggregates():
    assert json.loads(ARTIFACT.read_text(encoding="utf-8")) == evidence()


def test_oq_agreement_is_aggregate_only_and_uncertainty_is_descriptive():
    result = evidence()["oq_audit"]
    assert (result["exact_category_agreement"], result["denominator"]) == (31, 32)
    assert result["agreement_rate"] == 31 / 32
    assert result["automatic_task_success"] == result["audited_task_success"] == 16
    low, high = result["wilson_95_descriptive_iid_approximation"]
    assert low < result["agreement_rate"] < high
    assert "not evaluator accuracy" in result["scope"]


def test_candidate1_preserves_gate_and_exposes_only_aggregate_coverage_gap():
    result = evidence()["candidate1"]
    assert result["frozen_gate"] == {
        "automatic_success": 1,
        "denominator": 8,
        "threshold": 7,
        "proceed": False,
        "status": "UNCHANGED_FAILED_1_OF_8",
    }
    assert result["frozen_current_or_outdated_coverage"] == {
        "covered": 2,
        "denominator": 8,
        "rate": 0.25,
    }
    assert result["post_hoc_ai_diagnostic"] == {
        "current_value": 4,
        "outdated_value": 3,
        "incomplete": 1,
        "frozen_alias_recognized_within_semantically_classifiable": 2,
        "provenance_status": "POST_HOC_AI_ONLY_AGGREGATE_NOT_HUMAN_VALIDATED",
        "gate_effect": "NONE",
    }
    coverage = result["frozen_coverage_within_ai_diagnostic_complete_outputs"]
    assert (coverage["covered"], coverage["denominator"], coverage["rate"]) == (2, 7, 2 / 7)


def test_p1b_cross_table_demonstrates_structure_semantics_separation():
    result = evidence()["p1b_structural_semantic"]
    assert set(result["axis_totals"].values()) == {192}
    assert result["structural_counts_per_axis"] == {
        "AMBIGUOUS": 1,
        "CROSS_TURN": 186,
        "TRUNCATED": 5,
    }
    assert result["key_cross_cells"] == {
        "cross_turn_semantically_complete": 142,
        "cross_turn_full_answer": 109,
        "cross_turn_total": 186,
    }


def test_wave1_aggregate_coverage_and_structure_are_reconstructed_without_rows():
    result = evidence()["wave1"]
    assert result["automatic_factual_conclusive_coverage"] == {
        "conclusive": 15,
        "eligible": 72,
        "rate": 15 / 72,
        "automatic_attempts": 48,
        "unresolved_labels": 57,
        "minimum_unresolved_human_judgments": 57,
    }
    assert result["structural_semantic_counts"] == {
        "TRUNCATED": {"complete": 0, "incomplete": 17, "total": 17},
        "CROSS_TURN": {"complete": 78, "incomplete": 0, "total": 78},
        "AMBIGUOUS": {"complete": 1, "incomplete": 0, "total": 1},
    }
    assert result["native_termination_semantic_counts"] == {
        "output_budget": {"total": 95, "complete": 78, "incomplete": 17},
        "native_eos": {"total": 1, "complete": 1, "incomplete": 0},
    }
    assert result["annotation_provenance"].startswith("RESEARCHER_CONFIRMED_AI_ASSISTED")


def test_non_identifiable_quantities_and_three_scientific_statuses_are_explicit():
    result = evidence()
    assert [row["status"] for row in result["scientific_statuses"]] == [
        "OQ_TASK_SUCCESS_NARROWLY_SUPPORTED_BY_AGGREGATE_AGREEMENT",
        "GENERAL_SEMANTIC_VALIDITY_INSUFFICIENT",
        "CANDIDATE1_ENDPOINT_COVERAGE_INSUFFICIENT_REQUIRES_HUMAN_VALIDATION",
    ]
    assert all(item["status"] == "NOT_ESTIMABLE" for item in result["not_estimable"].values())
    assert result["historical_gate_integrity"] == {
        "stage_b_qualifying_configurations": 0,
        "stage_b_branch": "B",
        "candidate1_gate_changed": False,
        "historical_threshold_changed": False,
    }


def test_output_contains_only_allowed_aggregate_sources_and_no_record_material():
    result = evidence()
    assert set(result["input_scope"]["sources"]) == {
        "stage_b",
        "p1b_crosstabs",
        "candidate1_audit",
        "candidate1_selection",
        "wave1_coverage",
        "wave1_structural_semantic",
    }
    assert result["input_scope"]["restricted_or_raw_record_material_read"] is False
    assert result["input_scope"]["analysis_code"]["path"] == "tools/p1_evaluator_validity.py"
    assert result["input_scope"]["method_dependency"] == {
        "path": "tools/p1_measurement_scoring.py",
        "function": "wilson",
        "sha256": validity._sha256(Path("tools/p1_measurement_scoring.py").resolve()),
    }
    serialized = json.dumps(result).lower()
    for forbidden in (
        "raw_response",
        "record_text",
        "private_comment",
        "yaxin",
        "zheng",
        "researcher_un" + "blinding",
        "researcher_anno" + "tation",
    ):
        assert forbidden not in serialized


def test_tool_has_zero_inference_and_zero_authorization_cost():
    impact = evidence()["execution_impact"]
    assert impact == {
        "scientific_model_generations": 0,
        "model_inference_wall_seconds": 0,
        "authorization_debit_generations": 0,
        "network_calls": 0,
        "historical_outputs_modified": False,
    }
