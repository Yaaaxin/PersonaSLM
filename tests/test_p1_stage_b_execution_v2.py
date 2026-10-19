from pathlib import Path
import sys


sys.path.insert(0, str(Path("tools").resolve()))
sys.path.insert(0, str(Path("src").resolve()))

import p1_conditional_execution as v1
import p1_conditional_execution_v2 as v2


def test_recovery_binding_has_only_registered_test_difference():
    hashes, reconciliation = v2.reconciled_source_hashes()
    assert reconciliation["status"] == "PASS_VERSIONED_TEST_ONLY_RECONCILIATION"
    assert hashes["tools/p1_conditional_execution.py"] == (
        "d51b15dd23bb268bd272bc7f7f4c6f28ee69d8a7027ab18b4019646b28602c65"
    )
    assert hashes["tests/test_p1_blinded_stage_a.py"] == (
        "a769ef71de64b6328f9cb75e42d8a9f6ae4b3ff74df1487fdc3a3bd773619534"
    )


def test_persisted_decision_selects_registered_fallback_steps():
    decision_record = v2.s.load(v2.DECISION)
    assert decision_record["selection"]["selected_configuration"] is None
    assert decision_record["selection"]["branch"] == "B"
    assert all(not row["qualifies"] for row in decision_record["condition_results"].values())
    index = v2.s.load(v2.OUT / "manifest_index_frozen_v1.json")
    steps = v1.branch_steps(
        {"branch": "B", "selected_configuration": None},
        index,
    )
    assert [(step["name"], step["slice"], step["threshold"]) for step in steps] == [
        ("fallback_calibration", [0, 8], 7),
        ("pilot_C0", [0, 8], 6),
        ("pilot_remaining", [8, 80], None),
    ]
    assert sum(step["slice"][1] - step["slice"][0] for step in steps) == 88


def test_decision_artifact_is_bound_before_any_generation():
    reconciliation = v2.s.load(v2.RECONCILIATION)
    decision = v2.s.load(v2.DECISION)
    assert v2.s.sha256(v2.DECISION) == reconciliation["decision_artifact_sha256"]
    assert v2.s.sha256(v2.UNBLINDING) == reconciliation["unblinding_artifact_sha256"]
    assert decision["inference_authorization"]["new_generations_at_decision_record"] == 0
    assert decision["inference_authorization"]["remaining_before_stage_b"] == 88
