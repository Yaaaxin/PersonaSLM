"""Stage B execution wrapper with a versioned recovery-binding reconciliation.

The frozen v1 scientific controller remains unchanged.  Recovery replaced one
Stage A test so that tests no longer parse the real restricted key.  The v1
binding includes that non-runtime test and therefore rejects the safer current
test hash.  This wrapper permits exactly that documented test-only replacement,
binds itself and the Stage B decision artifacts, and delegates generation and
all scientific gates to the unchanged v1 controller.
"""

import argparse
import json
from pathlib import Path

import p1_blinded_audit as b
import p1_conditional_execution as v1
import p1_conditional_materials as materials
import p1_recovery_v2 as r


s = r.s
OUT = b.OUT
BASE_BINDING = OUT / "execution_tools_frozen_v1.json"
RECONCILIATION = OUT / "execution_binding_reconciliation_v2.json"
UNBLINDING = Path("docs/validation/p1/stage_b_v1/researcher_unblinding_record_v1.json")
DECISION = Path("docs/validation/p1/stage_b_v1/stage_b_decision_record_v1.json")
WRAPPER = Path("tools/p1_conditional_execution_v2.py")


def reconciled_source_hashes():
    base = s.load(BASE_BINDING)
    reconciliation = s.load(RECONCILIATION)
    s.require(
        s.sha256(BASE_BINDING) == reconciliation["base_binding_sha256"],
        "Frozen v1 execution binding changed",
    )
    replacement = reconciliation["permitted_test_only_replacement"]
    s.require(
        replacement["path"] == "tests/test_p1_blinded_stage_a.py",
        "Unexpected recovery-binding replacement path",
    )
    actual = {}
    differences = []
    for path, expected in base["source_sha256"].items():
        current = s.sha256(Path(path))
        actual[path] = current
        if current != expected:
            differences.append({"path": path, "expected": expected, "actual": current})
    s.require(differences == [
        {
            "path": replacement["path"],
            "expected": replacement["frozen_v1_sha256"],
            "actual": replacement["recovery_safe_sha256"],
        }
    ], "Execution binding has an unregistered source difference")
    s.require(
        s.sha256(WRAPPER) == reconciliation["wrapper_sha256"],
        "Stage B v2 wrapper changed",
    )
    s.require(
        s.sha256(UNBLINDING) == reconciliation["unblinding_artifact_sha256"],
        "Unblinding artifact changed",
    )
    s.require(
        s.sha256(DECISION) == reconciliation["decision_artifact_sha256"],
        "Stage B decision artifact changed",
    )
    actual[WRAPPER.as_posix()] = s.sha256(WRAPPER)
    actual[RECONCILIATION.as_posix()] = s.sha256(RECONCILIATION)
    actual[UNBLINDING.as_posix()] = s.sha256(UNBLINDING)
    actual[DECISION.as_posix()] = s.sha256(DECISION)
    return actual, reconciliation


def authorization_and_decision(review, activation):
    s.require(
        Path(activation).read_text(encoding="utf-8-sig").strip() == b.PHRASE,
        "Stage B not activated by exact researcher message",
    )
    policy = s.load(OUT / "stage_policy_frozen_v1.json")
    s.require(
        s.sha256(b.KEY) == policy["key_sha256"]
        and s.sha256(b.SHEET) == policy["blank_sheet_sha256"],
        "Blind key/sheet integrity",
    )
    s.require(
        s.sha256(Path(policy["source_snapshot"])) == policy["source_snapshot_sha256"],
        "Original automatic source changed",
    )
    materials.validate_all()
    source_hashes, reconciliation = reconciled_source_hashes()
    rows = b.validate_review(review)
    _, source = b.read_csv(policy["source_snapshot"])
    joined, decision = b.decide_joined(rows, s.load(b.KEY)["records"], source)

    unblinding = s.load(UNBLINDING)
    decision_record = s.load(DECISION)
    s.require(unblinding["decision"] == decision, "Persisted unblinding decision mismatch")
    s.require(
        unblinding["review_sha256"] == s.sha256(Path(review))
        and unblinding["key_sha256"] == s.sha256(b.KEY),
        "Persisted unblinding provenance mismatch",
    )
    s.require(
        decision_record["unblinding"]["artifact_sha256"] == s.sha256(UNBLINDING),
        "Decision record does not bind unblinding artifact",
    )
    s.require(
        decision_record["selection"]["branch"] == decision["branch"]
        and decision_record["selection"]["selected_configuration"]
        == decision["selected_configuration"],
        "Persisted branch decision mismatch",
    )
    for condition, counts in decision["condition_counts"].items():
        recorded = decision_record["condition_results"][condition]
        s.require(
            recorded["researcher_audited_task_success"] == counts["audited_success"]
            and recorded["automatic_audited_exact_agreement"]
            == counts["automatic_exact_agreement"]
            and recorded["denominator"] == counts["denominator"],
            "Persisted condition decision mismatch: " + condition,
        )

    return {
        "review_path": str(review),
        "review_sha256": s.sha256(Path(review)),
        "activation_path": str(activation),
        "activation_sha256": s.sha256(Path(activation)),
        "researcher": "Yaxin ZHENG",
        "human_review_timestamp": None,
        "software_recorded_utc": s.b.utc_now(),
        "provenance": "Explicit researcher activation plus validated submitted review; no independent-review claim.",
        "rows": joined,
        "decision": decision,
        "source_sha256": source_hashes,
        "execution_binding_reconciliation": {
            "path": RECONCILIATION.as_posix(),
            "sha256": s.sha256(RECONCILIATION),
            "status": reconciliation["status"],
        },
        "persisted_unblinding_sha256": s.sha256(UNBLINDING),
        "persisted_decision_sha256": s.sha256(DECISION),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["run"])
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--activation", type=Path, required=True)
    arguments = parser.parse_args()
    v1.authorization_and_decision = authorization_and_decision
    result = v1.run(arguments.review, arguments.activation)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
