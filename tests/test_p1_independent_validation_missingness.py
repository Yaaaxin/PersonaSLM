import importlib.util
import itertools
import json
import sys
from pathlib import Path

import pytest


PATH = Path("tools/p1_independent_validation_missingness.py")
SPEC = importlib.util.spec_from_file_location("p1_independent_validation_missingness", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_policy_reuses_registered_contrasts_and_does_not_authorize_execution():
    report = MODULE.build_report()
    assert set(report["contrast_registry"]) == set(MODULE.CONTRASTS)
    assert report["compatibility"]["constant_contrasts_verified_zero"] == 9
    assert report["execution_impact"]["scientific_model_generations"] == 0
    assert report["execution_impact"]["cohort_authorized"] is False
    assert report["adoption_gate"]["status"] == "PENDING_RESEARCHER_ADOPTION"


def test_signed_bounds_cover_every_completion_of_single_unknown_cells():
    for contrast_weights in MODULE.registry().values():
        active = [cell for cell, weight in contrast_weights.items() if weight]
        for unknown in active:
            observed = [cell for cell in active if cell != unknown]
            for values in itertools.product((0.0, 1.0), repeat=len(observed)):
                partial = dict(zip(observed, values))
                partial[unknown] = None
                bounded = MODULE.paired.case_contrast(partial, contrast_weights)
                completed = []
                for replacement in (0.0, 1.0):
                    full = {**partial, unknown: replacement}
                    completed.append(MODULE.paired.case_contrast(full, contrast_weights)["estimate"])
                assert bounded["estimate"] is None
                assert bounded["lower_bound"] == pytest.approx(min(completed))
                assert bounded["upper_bound"] == pytest.approx(max(completed))


def test_zero_weight_missing_cells_do_not_make_a_contrast_unknown():
    values = {condition: None for condition in MODULE.FACTORIAL}
    values.update(C0=0.0, C3=1.0)
    result = MODULE.paired.case_contrast(values, MODULE.weights("C3-C0"))
    assert result["estimate"] == 1.0
    assert result["unknown_cells"] == []


def test_archived_policy_reproduces_exactly():
    archived = json.loads(
        Path(
            "docs/validation/p1/model_feasibility_recovery_v1/"
            "independent_validation_missingness_policy_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert MODULE.build_report() == archived
