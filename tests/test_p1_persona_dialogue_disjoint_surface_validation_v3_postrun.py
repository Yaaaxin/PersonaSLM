import csv
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
EVIDENCE = REPO / "docs/validation/p1/persona_dialogue_disjoint_surface_validation_v3"
ROOT = REPO / "results/p1_persona_dialogue_disjoint_surface_validation/v3"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_completed_execution_chain_is_hash_linked_and_complete():
    authorization = EVIDENCE / "execution_authorization_v3.json"
    manifest = EVIDENCE / "frozen_manifest_v3.json"
    preflight = EVIDENCE / "preflight_v3.json"
    audit = EVIDENCE / "execution_audit_v3.json"
    analysis = EVIDENCE / "analysis_v3.json"
    auth, plan = load(authorization), load(manifest)
    gate, checked, estimates = load(preflight), load(audit), load(analysis)

    assert auth["implementation"]["runner"]["sha256"] == sha256(
        REPO / auth["implementation"]["runner"]["path"])
    assert auth["implementation"]["test"]["sha256"] == sha256(
        REPO / auth["implementation"]["test"]["path"])
    assert plan["authorization_sha256"] == sha256(authorization)
    assert gate["manifest_sha256"] == checked["manifest_sha256"] == sha256(manifest)
    assert checked["integrity_status"] == checked["execution_status"] == "PASS"
    assert checked["attempted"] == checked["recoverable_results"] == 168
    assert estimates["execution_audit_sha256"] == sha256(audit)
    assert estimates["attempted_generations"] == estimates["recoverable_results"] == 168
    assert estimates["new_generations_during_analysis"] == 0
    assert estimates["human_semantic_ratings"] == 0

    run = REPO / estimates["run_directory"]
    summary = load(run / "summary.json")
    assert summary["status"] == "PASS"
    assert summary["attempted"] == summary["responses_received"] == 168
    assert summary["retries"] == summary["hidden_warmups"] == 0


def test_registered_automatic_estimates_and_budget_are_frozen():
    analysis = load(EVIDENCE / "analysis_v3.json")
    expected = {
        "theta_A": (0.041666666666666664, 0.041666666666666664),
        "theta_C": (0.020833333333333332, 0.041666666666666664),
        "theta_surface": (0.0, 0.013888888888888888),
        "theta_generic_history": (-0.1875, -0.1875),
        "derived_theta_A_minus_theta_C": (0.020833333333333332, 0.0),
        "interaction_surface_aligned_minus_irrelevant": (
            0.08333333333333333, 0.08333333333333333),
        "interaction_surface_conflict_minus_irrelevant": (
            0.041666666666666664, 0.08333333333333333),
    }
    for name, (preferred, any_current) in expected.items():
        assert analysis["registered_estimates"][name][
            "preferred_current_anchor_selection"]["complete_case_estimate"] == preferred
        assert analysis["registered_estimates"][name][
            "any_current_anchor_selection"]["complete_case_estimate"] == any_current

    resources = analysis["resource_observations"]
    assert resources["native_stop_reason_distribution"] == {"eos": 168}
    assert resources["generated_tokens"] == 8691
    assert resources["maintained_attempt_inference_seconds"] == 1203.5250847999923
    assert analysis["cumulative_authorization_after"]["generations_used"] == 508
    assert analysis["cumulative_authorization_after"][
        "inference_seconds_used"] == 3171.544608799969


def test_stage_a_delivery_is_blank_and_does_not_expose_mapping():
    delivery = ROOT / "human_review/stage_a_delivery"
    template = delivery / "stage_a_current_only_REVIEW_TEMPLATE.csv"
    receipt = load(delivery / "stage_a_package_receipt.json")
    rows = list(csv.DictReader(template.open(encoding="utf-8", newline="")))
    immutable = {
        "blind_record_id", "response_instruction", "synthetic_persona_profile",
        "current_evidence_and_choices", "current_user_turn", "model_response",
    }
    editable = set(rows[0]) - immutable

    assert len(rows) == receipt["record_count"] == 168
    assert receipt["labels_created"] == 0
    assert receipt["mapping_in_delivery"] is False
    assert receipt["history_fields_in_delivery"] is False
    assert all(not row[field] for row in rows for field in editable)
    assert not ({"arm", "history_semantics", "history_surface", "request_id"} & set(rows[0]))
