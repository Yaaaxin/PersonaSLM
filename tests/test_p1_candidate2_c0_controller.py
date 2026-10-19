import importlib.util
import json
import sys
from pathlib import Path

import pytest


PATH = Path("tools/p1_candidate2_c0_controller.py")
SPEC = importlib.util.spec_from_file_location("p1_candidate2_c0_controller", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def qualifying_selection(candidate=MODULE.CANDIDATE, success=7, integrity="PASS"):
    return {
        "status": "QUALIFIED",
        "selected_candidate": candidate,
        "gate": {
            "status": "PASS",
            "complete": True,
            "automatic_success": success,
            "integrity_status": integrity,
        },
    }


def test_current_readiness_is_nonexecuting_and_global_ledger_is_reconstructed():
    result = MODULE.validate_readiness()
    assert result["status"] == "STATE_REQUIRES_REVALIDATION"
    assert result["selection"] == {
        "status": "BOUNDED_SCREEN_NEGATIVE",
        "selected_candidate": None,
    }
    assert result["runtime_actions"] == ["validate", "preflight", "run_c0", "audit"]
    assert result["remaining_72_action_implemented"] is False
    usage = result["combined_authorization"]
    assert usage["new_local_cpu_generations"] == usage["screen_generations"] == 16
    assert usage["pilot_c0_generations"] == 0
    assert usage["remaining_generations"] == 1184
    assert usage["historical_ledger_untouched"] is True


def test_selection_gate_requires_complete_candidate2_qualification():
    assert MODULE.require_selected(qualifying_selection())["selected_candidate"] == MODULE.CANDIDATE
    with pytest.raises(ValueError, match="not a complete integrity-valid"):
        MODULE.require_selected(qualifying_selection(candidate="wrong"))
    with pytest.raises(ValueError, match="not a complete integrity-valid"):
        MODULE.require_selected(qualifying_selection(success=6))
    with pytest.raises(ValueError, match="not a complete integrity-valid"):
        MODULE.require_selected(qualifying_selection(integrity="FAIL"))
    with pytest.raises(ValueError, match="not a complete integrity-valid"):
        MODULE.require_selected()


def test_explicit_ids_not_request_position_select_c0():
    artifact = MODULE.recovery.load(MODULE.pilot.DESTINATION)
    artifact["requests"] = list(reversed(artifact["requests"]))
    rows = MODULE.c0_requests(artifact)
    assert [row["request_id"] for row in rows] == artifact["execution_blocks"]["c0_gate"]["request_ids"]
    assert {row["condition"] for row in rows} == {"C0"}


def test_ram_gate_is_unchanged_and_does_not_round_decimal_gigabytes():
    assert MODULE.RAM_BYTES == 5 * 1024**3
    MODULE.require_resource(MODULE.RAM_BYTES)
    with pytest.raises(ValueError, match=f"required={MODULE.RAM_BYTES}"):
        MODULE.require_resource(MODULE.RAM_BYTES - 1)


def test_automatic_gate_never_unblocks_remaining_72():
    rows = []
    for index in range(8):
        state = "CURRENT_VALUE_ADOPTION" if index < 6 else "OUTDATED_VALUE_ADOPTION"
        rows.append({
            "case_id": f"case-{index}",
            "request_id": f"request-{index}",
            "answer_state": state,
            "automatic_task_success": "Success" if index < 6 else "Failure",
        })
    passed = MODULE.gate_record(rows)
    assert passed["proceed"] is True and passed["automatic_success"] == 6
    assert passed["remaining_72_status"].startswith("BLOCKED_")
    rows[0]["answer_state"] = "UNVERIFIABLE_ANSWER"
    rows[0]["automatic_task_success"] = "Uncertain"
    assert MODULE.gate_record(rows)["proceed"] is False


def test_replay_result_preserves_uncertainty_and_raw_hash():
    row = MODULE.c0_requests()[0]
    bank = MODULE.recovery.case_bank()
    response = {"content": "unsupported synthetic answer", "tokens": [1], "stop_type": "eog"}
    result = MODULE.replay_result(row, response, 1.25, bank)
    assert result["answer_state"] == "UNVERIFIABLE_ANSWER"
    assert result["automatic_task_success"] == "Uncertain"
    assert result["raw_output_sha256"] == MODULE.recovery.text_sha256(response["content"])
    assert result["semantic_completeness"] == "NOT_INDEPENDENTLY_ADJUDICATED"


def test_archived_readiness_is_preserved_and_static_fields_still_match():
    archived = json.loads(MODULE.READINESS.read_text(encoding="utf-8"))
    assert MODULE.recovery.sha256(MODULE.READINESS) == (
        "f826f25c49b5b0721528a2e526088a996707ee9cd53ba343fd82e9f8425346af"
    )
    assert archived["status"] == (
        "READY_CODE_AND_MATERIALS_BLOCKED_UNTIL_CANDIDATE2_QUALIFIES_AND_RAM_PASSES"
    )
    assert archived["selection"]["status"] == "CANDIDATE_1_FAILED_CANDIDATE_2_PENDING"
    assert archived["combined_authorization"]["new_local_cpu_generations"] == 8

    current = MODULE.validate_readiness()
    assert current["status"] == "STATE_REQUIRES_REVALIDATION"
    assert current["selection"]["status"] == "BOUNDED_SCREEN_NEGATIVE"
    assert current["combined_authorization"]["new_local_cpu_generations"] == 16
    for dynamic in ("status", "selection", "combined_authorization"):
        archived.pop(dynamic)
        current.pop(dynamic)
    assert archived == current
