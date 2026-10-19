import importlib.util
import json
import statistics
import sys
from pathlib import Path


PATH = Path("tools/p1_independent_validation_test_calibration_v2.py")
SPEC = importlib.util.spec_from_file_location("p1_independent_validation_test_calibration_v2", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_equalizing_shift_preserves_exact_finite_allocation_mean():
    base = [-2.0, -1.0, 0.0, 1.0] * 2
    templates = list(range(8))
    slopes = [-0.8, -0.4, -0.2, -0.1, 0.1, 0.2, 0.4, 0.8]
    target = statistics.fmean(MODULE.precision.logistic(value) for value in base)
    shift = MODULE.equalizing_shift(base, templates, slopes, target)
    achieved = statistics.fmean(
        MODULE.precision.logistic(value + slopes[template] + shift)
        for value, template in zip(base, templates)
    )
    assert abs(achieved - target) < 1e-12


def test_single_trial_uses_speaker_cluster_family_without_invalid_values():
    trial = MODULE.simulate_trial(
        MODULE.random.Random(MODULE.SEED), MODULE.SCENARIOS[-1]
    )
    assert tuple(trial["pvalues"]) == MODULE.FAMILY
    assert tuple(trial["holm_rejections"]) == MODULE.FAMILY
    assert all(value is None or 0.0 <= value <= 1.0 for value in trial["pvalues"].values())


def test_small_report_preserves_v1_failure_and_narrows_target():
    first = MODULE.build_report(2)
    second = MODULE.build_report(2)
    assert first == second
    assert first["predecessor_negative_result"]["decision"].startswith("DOES_NOT_")
    assert first["predecessor_negative_result"]["preservation"] == "UNCHANGED"
    assert first["design"]["degrees_of_freedom"] == 47
    assert first["target_boundary"]["template_generalization"].startswith("Not claimed")
    assert first["execution_impact"]["scientific_model_generations"] == 0
    assert first["execution_impact"]["cohort_authorized"] is False


def test_archived_full_v2_calibration_reproduces():
    archived = json.loads(MODULE.DESTINATION.read_text(encoding="utf-8"))
    assert archived == MODULE.build_report(MODULE.REPLICATES)
