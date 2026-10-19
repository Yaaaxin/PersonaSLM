import importlib.util
import json
import sys
from pathlib import Path

import pytest


PATH = Path("tools/p1_independent_validation_multiplicity.py")
SPEC = importlib.util.spec_from_file_location("p1_independent_validation_multiplicity", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_candidate_family_preserves_protocol_simple_and_factorial_contrasts():
    assert len(MODULE.CONFIRMATORY_FAMILY) == len(set(MODULE.CONFIRMATORY_FAMILY)) == 11
    assert MODULE.CONFIRMATORY_FAMILY[:4] == MODULE.PROTOCOL_SIMPLE_CONTRASTS
    registry = MODULE.contrast_registry()
    assert tuple(registry) == MODULE.CONFIRMATORY_FAMILY
    assert all(abs(sum(row.values())) < 1e-12 for row in registry.values())
    assert registry["C1-N_style"]["C1"] == 1.0
    assert registry["C1-N_style"]["N_style"] == -1.0
    assert registry["C3-N_history"]["C3"] == 1.0
    assert registry["C3-N_history"]["N_history"] == -1.0


def test_holm_reference_values_and_unavailable_hypothesis_stays_in_family():
    order = ("a", "b", "c", "d")
    result = MODULE.holm_adjust({"a": 0.01, "b": 0.03, "c": 0.04, "d": None}, order)
    rows = {row["hypothesis"]: row for row in result["rows"]}
    assert result["family_size"] == 4
    assert rows["a"]["adjusted_p_value"] == pytest.approx(0.04)
    assert rows["b"]["adjusted_p_value"] == pytest.approx(0.09)
    assert rows["c"]["adjusted_p_value"] == pytest.approx(0.09)
    assert rows["d"]["adjusted_p_value"] == 1.0
    assert rows["a"]["reject"] is True
    assert all(rows[name]["reject"] is False for name in ("b", "c", "d"))
    assert rows["d"]["status"] == "UNTESTABLE_RETAINED_AS_NONREJECTION"


def test_holm_ties_follow_declared_order_and_adjusted_values_are_monotone_by_rank():
    order = ("first", "second", "third")
    result = MODULE.holm_adjust({"third": 0.02, "second": 0.01, "first": 0.01}, order)
    by_rank = sorted(result["rows"], key=lambda row: row["rank"])
    assert [row["hypothesis"] for row in by_rank] == ["first", "second", "third"]
    adjusted = [row["adjusted_p_value"] for row in by_rank]
    assert adjusted == sorted(adjusted)


@pytest.mark.parametrize(
    "pvalues,order",
    [
        ({"a": -0.1}, ("a",)),
        ({"a": 1.1}, ("a",)),
        ({"a": float("nan")}, ("a",)),
        ({"a": True}, ("a",)),
        ({"a": 0.1}, ("a", "b")),
        ({"a": 0.1}, ("a", "a")),
    ],
)
def test_holm_rejects_invalid_or_mismatched_inputs(pvalues, order):
    with pytest.raises(ValueError):
        MODULE.holm_adjust(pvalues, order)


def test_report_exposes_registry_gap_and_does_not_authorize_cohort():
    report = MODULE.build_report()
    assert report["status"].startswith("PROSPECTIVE_CANDIDATE_PENDING_")
    assert report["audit_finding"]["protocol_simple_contrasts_absent_from_existing_registry"] == [
        "C1-N_style", "C3-N_history"
    ]
    assert report["candidate_endpoint_hierarchy"]["family_size"] == 11
    assert report["adoption_gate"]["cohort_authorized"] is False
    assert report["execution_impact"]["scientific_model_generations"] == 0
    assert report["execution_impact"]["human_annotations"] == 0


def test_archived_candidate_reproduces_current_report():
    archived = json.loads(MODULE.DESTINATION.read_text(encoding="utf-8"))
    assert archived == MODULE.build_report()
