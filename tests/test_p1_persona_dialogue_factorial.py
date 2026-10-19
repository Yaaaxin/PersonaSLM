import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location("persona_dialogue", ROOT / "tools/p1_persona_dialogue_factorial.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_frozen_design_structure_and_order():
    design = json.loads((ROOT / MODULE.DESIGN).read_text(encoding="utf-8"))
    checks = MODULE.validate_design(design)
    assert checks["requests"] == 48
    assert checks["cases"] == 6


def test_prompt_factor_isolation():
    design = json.loads((ROOT / MODULE.DESIGN).read_text(encoding="utf-8"))
    for case in design["cases"]:
        built = {c: MODULE.construction(design, case, c) for c in design["factors"]["conditions"]}
        assert all(messages[-1]["content"] == case["fixed_current_user"] for _, messages in built.values())
        assert all(case["fixed_current_notes"] in messages[0]["content"] for _, messages in built.values())
        for condition, (factors, messages) in built.items():
            persona = design["personas"][case["persona_id"]]
            assert (persona["S_block"] in messages[0]["content"]) == bool(factors["S"])
            assert (persona["F_block"] in messages[0]["content"]) == bool(factors["F"])
            assert (len(messages) == 4) == bool(factors["H"])


def test_automatic_score_preserves_unresolved_and_applicability():
    design = json.loads((ROOT / MODULE.DESIGN).read_text(encoding="utf-8"))
    case = design["cases"][1]
    factors, messages = MODULE.construction(design, case, "C7")
    row = {"persona_id": case["persona_id"], "history_regime": case["history_regime"],
           "condition": "C7", "factors": factors, "preferred_option": case["preferred_option"],
           "history_favored_option": case["history_favored_option"], "options": case["options"]}
    unresolved = MODULE.automatic_score(row, "I cannot decide from this information.")
    assert unresolved["selected_option"] == "UNRESOLVED"
    assert unresolved["current_preference_choice"] is None
    assert unresolved["outdated_value_adoption"] is None
    current = MODULE.automatic_score(row, "Certainly. Choose Orchid Room because it is quiet.")
    assert current["selected_option"] == "B"
    assert current["reason_support_state"] == "SUPPORTED"
    assert current["current_preference_choice"] == 1
    assert current["outdated_value_adoption"] == 0


def test_reason_contradiction_precedes_support():
    design = json.loads((ROOT / MODULE.DESIGN).read_text(encoding="utf-8"))
    case = design["cases"][0]
    factors, _ = MODULE.construction(design, case, "C0")
    row = {"persona_id": case["persona_id"], "history_regime": case["history_regime"],
           "condition": "C0", "factors": factors, "preferred_option": case["preferred_option"],
           "history_favored_option": case["history_favored_option"], "options": case["options"]}
    score = MODULE.automatic_score(row, "Choose Cedar Cafe because it is quiet, although it is lively.")
    assert score["selected_option"] == "A"
    assert score["reason_support_state"] == "CONTRADICTED"


def test_payload_and_boundary_censoring_are_frozen():
    row = {"input_token_ids": [1, 2], "factors": {"S": 1}, "history_regime": "IRRELEVANT",
           "condition": "C1", "persona_id": "SYN_PF_B", "preferred_option": "A",
           "history_favored_option": None, "options": {"A": {"aliases": ["a"], "reason_cues": ["x"]},
                                                        "B": {"aliases": ["b"], "reason_cues": ["y"]}}}
    assert MODULE.payload(row)["ignore_eos"] is False
    score = MODULE.automatic_score(row, "A because x", assessable=False)
    assert score["measurement_state"] == "BOUNDARY_CENSORED"
    assert score["task_success"] is None
    assert score["operational_linguistic_fidelity"] is None


def test_independent_design_is_preexecution_and_disjoint():
    dev = json.loads((ROOT / MODULE.DESIGN).read_text(encoding="utf-8"))
    val = json.loads((ROOT / MODULE.VALIDATION_DESIGN).read_text(encoding="utf-8"))
    assert val["status"] == "FROZEN_PREEXECUTION_NOT_AUTHORIZED"
    assert val["study_type"] == "INDEPENDENT_SYNTHETIC_REPLICATION_NOT_REAL_SPEAKER"
    assert not ({c["case_id"] for c in dev["cases"]} & {c["case_id"] for c in val["cases"]})
