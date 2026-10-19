import importlib.util
import itertools
import json
import sys
from pathlib import Path

import pytest


PATH = Path("tools/p1_independent_validation_missingness_v2.py")
SPEC = importlib.util.spec_from_file_location("p1_independent_validation_missingness_v2", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_registry_extends_v1_with_both_protocol_neutral_contrasts():
    registry = MODULE.registry()
    assert tuple(registry) == MODULE.multiplicity.CONFIRMATORY_FAMILY
    assert len(registry) == 11
    assert registry["C1-N_style"]["C1"] == 1.0
    assert registry["C1-N_style"]["N_style"] == -1.0
    assert registry["C3-N_history"]["C3"] == 1.0
    assert registry["C3-N_history"]["N_history"] == -1.0


def test_signed_bounds_cover_every_single_unknown_active_cell_for_all_11_contrasts():
    for contrast_weights in MODULE.registry().values():
        active = [cell for cell, weight in contrast_weights.items() if weight]
        for unknown in active:
            observed = [cell for cell in active if cell != unknown]
            for values in itertools.product((0.0, 1.0), repeat=len(observed)):
                partial = dict(zip(observed, values))
                partial[unknown] = None
                bounded = MODULE.paired.case_contrast(partial, contrast_weights)
                completed = [
                    MODULE.paired.case_contrast(
                        {**partial, unknown: replacement}, contrast_weights
                    )["estimate"]
                    for replacement in (0.0, 1.0)
                ]
                assert bounded["estimate"] is None
                assert bounded["lower_bound"] == pytest.approx(min(completed))
                assert bounded["upper_bound"] == pytest.approx(max(completed))


def test_report_preserves_v1_and_both_failed_calibrations_without_authorization():
    report = MODULE.build_report()
    assert report["predecessor"]["preservation"] == "UNCHANGED"
    assert report["inferential_boundary"]["status"] == "NO_CALIBRATED_CONFIRMATORY_TEST_IDENTIFIED"
    assert len(report["inferential_boundary"]["failed_artifacts"]) == 2
    assert report["adoption_gate"]["cohort_authorized"] is False
    assert report["execution_impact"]["scientific_model_generations"] == 0
    assert report["execution_impact"]["human_annotations"] == 0


def test_archived_v2_policy_reproduces():
    archived = json.loads(MODULE.DESTINATION.read_text(encoding="utf-8"))
    assert archived == MODULE.build_report()
