from pathlib import Path
import json
import sys


sys.path.insert(0, str(Path("tools").resolve()))
sys.path.insert(0, str(Path("src").resolve()))

import p1_stage_b_closeout as closeout


def evidence():
    return closeout.audit()


def test_stage_b_journal_and_generation_inventory():
    result = evidence()
    assert result["run"]["journal_integrity"] == "PASS"
    assert result["run"]["events"] == 372
    assert result["run"]["attempted"] == result["run"]["results"] == 8
    assert result["run"]["retries"] == 0
    assert result["preflight"]["live_prompt_token_arrays_verified"] == 88


def test_fallback_calibration_gate_is_recomputed_exactly():
    gate = evidence()["calibration_gate"]
    assert gate["threshold"] == 7
    assert gate["denominator"] == 8
    assert gate["automatic_success"] == 6
    assert gate["answer_states"] == {
        "CURRENT_VALUE_ADOPTION": 6,
        "OUTDATED_VALUE_ADOPTION": 2,
    }
    assert gate["proceed"] is False
    assert gate["researcher_review_status"] == "PENDING"


def test_failed_gate_preserves_unexecuted_factorial_pilot_and_budget():
    result = evidence()
    assert result["authorization"]["new_generations"] == 8
    assert result["authorization"]["remaining_development_budget"] == 80
    assert result["authorization"]["minimal_temporal_pilot_attempts"] == 0
    assert result["authorization"]["minimal_temporal_pilot_ungenerated"] == 80
    assert result["analysis"]["factorial_contrasts"] == "NOT_ESTIMABLE"


def test_missingness_structure_and_persona_fidelity_are_not_collapsed():
    status = evidence()["measurement_status"]
    assert status["missing_calibration_outputs"] == 0
    assert status["empty_calibration_outputs"] == 0
    assert status["all_units_identifiable"] is True
    assert status["structural_status"] == {"AMBIGUOUS": 8}
    assert status["linguistic_persona_fidelity"] == "NOT_APPLICABLE"
    assert status["behavioral_persona_fidelity"] == "NOT_APPLICABLE"


def test_persisted_execution_evidence_matches_fresh_reconstruction():
    saved = json.loads(closeout.EVIDENCE.read_text(encoding="utf-8"))
    assert saved == evidence()
