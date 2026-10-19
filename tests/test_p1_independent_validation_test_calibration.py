import importlib.util
import json
import sys
from pathlib import Path

import pytest


PATH = Path("tools/p1_independent_validation_test_calibration.py")
SPEC = importlib.util.spec_from_file_location("p1_independent_validation_test_calibration", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_student_t_two_sided_matches_registered_df7_critical_values():
    assert MODULE.student_t_two_sided_p(0.0) == pytest.approx(1.0)
    assert MODULE.student_t_two_sided_p(2.364624251) == pytest.approx(0.05, abs=2e-10)
    assert MODULE.student_t_two_sided_p(3.4994833) == pytest.approx(0.01, abs=2e-8)
    assert MODULE.student_t_two_sided_p(5.0) < MODULE.student_t_two_sided_p(3.0)


def test_wilson_interval_contains_observed_fraction():
    interval = MODULE.wilson(50, 1000)
    assert interval[0] < 0.05 < interval[1]
    assert MODULE.wilson(0, 100)[0] == 0.0
    assert MODULE.wilson(100, 100)[1] == 1.0


def test_single_trial_covers_exact_family_with_valid_or_unavailable_pvalues():
    trial = MODULE.simulate_trial(
        MODULE.random.Random(MODULE.SEED), MODULE.SCENARIOS[0]
    )
    assert tuple(trial["pvalues"]) == MODULE.FAMILY
    assert tuple(trial["holm_rejections"]) == MODULE.FAMILY
    assert tuple(trial["nonpositive_variance"]) == MODULE.FAMILY
    assert all(value is None or 0.0 <= value <= 1.0 for value in trial["pvalues"].values())
    assert all(isinstance(value, bool) for value in trial["holm_rejections"].values())


def test_small_report_is_deterministic_nonexecuting_and_uses_declared_rule():
    first = MODULE.build_report(3)
    second = MODULE.build_report(3)
    assert first == second
    assert first["replicates_per_scenario"] == 3
    assert first["design"]["family_size"] == 11
    assert first["design"]["nonpositive_variance_rule"].startswith("UNTESTABLE_NONREJECTION")
    assert first["prospective_calibration_rule"]["declared_before_full_simulation"] is True
    assert first["execution_impact"]["scientific_model_generations"] == 0
    assert first["execution_impact"]["cohort_authorized"] is False


def test_decision_requires_every_declared_threshold():
    base = {
        "global_null_holm_fwer_wilson_95": [0.0, 0.05],
        "marginal": {
            name: {
                "raw_type1_wilson_95_of_all_trials": [0.0, 0.06],
                "untestable_nonpositive_variance_fraction": 0.01,
            }
            for name in MODULE.FAMILY
        },
    }
    assert MODULE.calibration_decision([base])["decision"].startswith("MEETS_")
    for field, value in (
        ("global_null_holm_fwer_wilson_95", [0.0, 0.061]),
        ("raw_type1_wilson_95_of_all_trials", [0.0, 0.066]),
        ("untestable_nonpositive_variance_fraction", 0.021),
    ):
        changed = json.loads(json.dumps(base))
        if field == "global_null_holm_fwer_wilson_95":
            changed[field] = value
        else:
            changed["marginal"][MODULE.FAMILY[0]][field] = value
        assert MODULE.calibration_decision([changed])["decision"].startswith("DOES_NOT_")


def test_archived_full_calibration_reproduces():
    archived = json.loads(MODULE.DESTINATION.read_text(encoding="utf-8"))
    assert archived == MODULE.build_report(MODULE.REPLICATES)
