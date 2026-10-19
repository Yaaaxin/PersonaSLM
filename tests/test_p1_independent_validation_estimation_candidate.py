import importlib.util
import json
import sys
from pathlib import Path

import pytest


PATH = Path("tools/p1_independent_validation_estimation_candidate.py")
SPEC = importlib.util.spec_from_file_location(
    "p1_independent_validation_estimation_candidate", PATH
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_candidate_preserves_full_family_and_estimation_only_boundary():
    report = MODULE.build_report()
    estimands = report["endpoint_and_estimands"]
    assert len(estimands["fixed_contrast_order"]) == 11
    assert set(estimands["fixed_contrast_order"]) == set(
        estimands["contrast_registry"]
    )
    assert estimands["lead_reporting_estimand"] == "C3-C0"
    assert "Designated lead" in estimands["lead_status"]
    assert report["calibration_evidence"]["boundary"] == (
        "NO_CALIBRATED_CONFIRMATORY_TEST_IDENTIFIED"
    )
    assert report["scope"]["not_a_confirmatory_freeze"] is True
    assert report["prospective_lock"]["researcher_adopted"] is False
    assert report["execution_impact"]["cohort_authorized"] is False


def test_candidate_forbids_dichotomous_claims_and_keeps_missingness_bounds():
    report = MODULE.build_report()
    decision_rule = report["primary_reporting"]["no_decision_rule"]
    assert "No p-value" in decision_rule
    assert "no-effect" in decision_rule
    required = report["primary_reporting"]["required_for_every_active_contrast"]
    assert any("identification bounds" in row for row in required)
    assert any("denominators" in row for row in required)
    forbidden = " ".join(report["sensitivity_reporting"]["forbidden_interpretation"])
    assert "calibrated confidence interval" in forbidden
    assert "outcome-defined subset" in forbidden
    assert "No interval-like sensitivity procedure is authorized" in forbidden
    embedded = report["primary_reporting"]["missingness_policy"]["cluster_sensitivity"]
    assert "not activated by this candidate" in embedded
    assert "no interval-like procedure" in embedded


def test_signed_case_bounds_precede_equal_speaker_aggregation():
    weights = {"C0": -1.0, "C3": 1.0}
    cases = [
        {"case_id": "a1", "speaker_id": "a", "outcomes": {"C0": 0.0, "C3": 1.0}},
        {"case_id": "a2", "speaker_id": "a", "outcomes": {"C0": 0.0, "C3": None}},
        {"case_id": "b1", "speaker_id": "b", "outcomes": {"C0": 0.0, "C3": 0.0}},
        {"case_id": "b2", "speaker_id": "b", "outcomes": {"C0": 0.0, "C3": 0.0}},
    ]
    result = MODULE.aggregate_finite_cohort(
        cases, weights, expected_speakers=2, cases_per_speaker=2
    )
    assert result["unknown_active_cells"] == 1
    assert result["estimate"] is None
    assert result["lower_bound"] == pytest.approx(0.25)
    assert result["upper_bound"] == pytest.approx(0.5)
    assert result["speaker_rows"][0]["estimate"] is None
    assert result["speaker_rows"][1]["estimate"] == 0.0


def test_reference_implementation_fails_closed_on_missing_speaker():
    cases = [
        {"case_id": "a1", "speaker_id": "a", "outcomes": {"C0": 0.0, "C3": 1.0}},
        {"case_id": "a2", "speaker_id": "a", "outcomes": {"C0": 0.0, "C3": 1.0}},
    ]
    with pytest.raises(ValueError, match="Speaker count changed"):
        MODULE.aggregate_finite_cohort(cases, {"C0": -1.0, "C3": 1.0})


def test_failed_calibration_is_a_fail_closed_dependency(monkeypatch):
    original_load = MODULE.load

    def changed_load(path):
        value = original_load(path)
        if path == MODULE.CALIBRATIONS[0]:
            value["calibration_decision"]["decision"] = "MEETS_CRITERIA"
        return value

    monkeypatch.setattr(MODULE, "load", changed_load)
    with pytest.raises(ValueError, match="no longer records a negative decision"):
        MODULE.build_report()


def test_exclusive_create_and_archived_candidate_reproduces(tmp_path):
    archived = json.loads(MODULE.DESTINATION.read_text(encoding="utf-8"))
    assert archived == MODULE.build_report()
    output = tmp_path / "candidate.json"
    MODULE.write_new(output, archived)
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        MODULE.write_new(output, archived)
