"""Independent examples for the offline enum compatibility diagnostic."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("native_stop_diagnostic", Path(__file__).parents[1] / "tools/p1_native_stop_diagnostic.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_native_eos_does_not_certify_semantic_completeness():
    backend = {"stop_type": "eos", "stop": True}
    before = deepcopy(backend)
    result = module.diagnose("The appointment is", backend)
    assert backend == before
    assert result["original"]["observed_boundary"] is None
    assert result["diagnostic"]["observed_boundary"] == "eog"
    assert result["diagnostic"]["status"] == "AMBIGUOUS"
    assert result["replacement_score"] is None


@pytest.mark.parametrize("kind", ["limit", "eog", "unknown", "word"])
def test_other_stop_kinds_remain_identical(kind):
    result = module.diagnose("Welcome to the workshop.", {"stop_type": kind})
    assert result["original"] == result["diagnostic"]
    assert not result["native_eos_alias_mapped"]


def test_conflicting_flags_remain_ambiguous():
    result = module.diagnose("Welcome.", {"stop_type": "eos", "stopped_limit": True})
    assert result["diagnostic"]["status"] == "AMBIGUOUS"
    assert "contradictory_backend_termination" in result["diagnostic"]["reasons"]


def test_cross_turn_is_not_changed_by_native_boundary_alias():
    raw = "Welcome.\nUser: Please continue.\nAssistant: Hello."
    result = module.diagnose(raw, {"stop_type": "eos"})
    assert result["original"]["status"] == result["diagnostic"]["status"] == "CROSS_TURN"
    assert result["original"]["first_span"] == result["diagnostic"]["first_span"]
