import importlib.util
import json
import sys
from pathlib import Path


PATH = Path("tools/p1_independent_validation_precision.py")
SPEC = importlib.util.spec_from_file_location("p1_independent_validation_precision", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_allocation_is_balanced_and_crossed():
    rows = MODULE.allocation()
    assert len(rows) == 96
    assert {sum(row["template_ancestor"] == template for row in rows) for template in range(8)} == {12}
    for speaker in range(48):
        templates = {row["template_ancestor"] for row in rows if row["speaker"] == speaker}
        assert len(templates) == 2


def test_report_is_deterministic_and_does_not_authorize_execution():
    first = MODULE.build_report(replicates=12)
    second = MODULE.build_report(replicates=12)
    assert first == second
    assert first["design"]["requests"] == 960
    assert first["execution_impact"]["scientific_model_generations"] == 0
    assert "does not freeze or authorize" in first["prospective_acceptance_rule"]["interpretation"]


def test_missingness_is_bounded_without_relabeling_unknowns():
    report = MODULE.build_report(replicates=24)
    rows = {row["scenario"]["name"]: row for row in report["summaries"]}
    assert rows["central"]["mean_worst_case_missingness_bound_width"] == 0.0
    assert rows["central"]["worst_case_missingness_bound_full_data_coverage"] == 1.0
    missing = rows["outcome_dependent_missingness"]
    assert missing["median_complete_pair_fraction"] < 1.0
    assert missing["mean_worst_case_missingness_bound_width"] > 0.0
    assert missing["worst_case_missingness_bound_full_data_coverage"] == 1.0


def test_archived_report_reproduces_exactly():
    archived = json.loads(
        Path(
            "docs/validation/p1/model_feasibility_recovery_v1/"
            "independent_validation_precision_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert MODULE.build_report(replicates=2_000) == archived
