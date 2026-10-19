import importlib.util
import sys
from pathlib import Path

import pytest


PATH = Path("tools/p1_candidate2_pilot_materialization.py")
SPEC = importlib.util.spec_from_file_location("p1_candidate2_pilot_materialization", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_source_hazard_and_explicit_c0_order_are_real():
    freeze = MODULE.recovery.validate_freeze()
    source = MODULE.recovery.load(MODULE.SOURCE)
    ordered = MODULE.ordered_source(source)
    assert [row["condition"] for row in source["requests"][:8]] != ["C0"] * 8
    assert [row["condition"] for row in ordered[:8]] == ["C0"] * 8
    assert {row["case_id"] for row in ordered[:8]} == set(
        freeze["post_screen_boundary"]["disjoint_pilot_c0_case_ids"]
    )
    with pytest.raises(ValueError, match="Candidate 2 is not activated"):
        MODULE.preparation_gate()


def test_archived_candidate2_native_materialization_is_valid_and_nonexecuting():
    result = MODULE.validate_materialized()
    assert result == {
        "status": "PASS_MATERIALIZED_NO_INFERENCE_NOT_EXECUTION_AUTHORIZATION",
        "requests": 80,
        "c0_gate_requests": 8,
        "conditional_continuation_requests": 72,
        "namespace": MODULE.NAMESPACE,
        "scientific_model_generations": 0,
    }
    value = MODULE.recovery.load(MODULE.DESTINATION)
    assert value["authorization_subledger"]["attempts_at_materialization"] == 0
    assert MODULE.recovery.cumulative()["attempts_by_candidate"][MODULE.CANDIDATE] == 8
    assert value["authorization_subledger"]["historical_160_request_ledger_consumed"] == 0
    assert value["execution_blocks"]["conditional_continuation"]["count"] == 72
    assert "semantic review" in " ".join(
        value["execution_blocks"]["conditional_continuation"]["prerequisites"]
    ).lower()
