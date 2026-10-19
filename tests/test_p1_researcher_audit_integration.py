import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import p1_blinded_audit as stage_a
import p1_researcher_audit_integration as integration


def test_actual_v3_researcher_submission_validates_without_unblinding_key_access():
    review_hash = integration.sha256(integration.REVIEW)
    audit = integration.validate_researcher_submission()

    report = audit["import_artifact"]
    assert review_hash == integration.EXPECTED_REVIEW_SHA256
    assert integration.sha256(integration.REVIEW) == review_hash
    assert report["validation"]["record_count"] == 32
    assert report["validation"]["unique_anonymous_review_ids"] == 32
    assert report["validation"]["immutable_scientific_fields_unchanged"] is True
    assert report["validation"]["old_ai_proposals_applied"] is False
    assert report["validation"]["restricted_unblinding_key_read"] is False
    assert {record["researcher_name"] for record in report["records"]} == {"Yaxin ZHENG"}
    assert report["submitted_label_distributions"]["task_success"] == {"Success": 16, "Failure": 16}


def test_date_audit_uses_anonymous_ids_and_component_dates():
    audit = integration.validate_researcher_submission()["date_artifact"]

    assert audit["record_count"] == 32
    assert audit["records_with_2051_03_15"] == 16
    assert audit["multi_date_records"] == 4
    assert audit["september_only_records"] == 16
    assert audit["restricted_unblinding_key_read"] is False
    assert all(record["status"] == "PASS_COMPONENT_DATE_MATCHES_EXPLICIT_QUESTION_DATE" for record in audit["records"])


def test_compatibility_view_preserves_labels_without_opening_actual_key(tmp_path):
    audit = integration.validate_researcher_submission()
    compatibility_path = tmp_path / "compatibility.csv"
    integration.write_csv_new(compatibility_path, audit["blank_fields"], audit["compatibility_rows"])
    _, blank_rows = integration.read_csv(integration.BLANK)
    synthetic_key = {
        "records": [
            {
                "anonymous_review_id": row["anonymous_review_id"],
                "immutable_review_fields_sha256": stage_a.immutable_digest(row),
            }
            for row in blank_rows
        ]
    }

    validated = stage_a.validate_review(
        compatibility_path,
        policy={"test_only": True},
        key=synthetic_key,
        blank_path=integration.BLANK,
    )
    original_rows = audit["review_rows"]
    assert len(validated) == len(original_rows) == 32
    assert [row["anonymous_review_id"] for row in validated] == [row["anonymous_review_id"] for row in original_rows]
    assert all(
        (original["researcher_task_success_decision"], converted["researcher_task_success_decision"])
        in {("Success", "CORRECT"), ("Failure", "INCORRECT")}
        for original, converted in zip(original_rows, validated)
    )
    assert all("condition" not in row for row in validated)


def test_proposal_comparison_keeps_all_submitted_researcher_values():
    report = integration.validate_researcher_submission()["import_artifact"]["proposal_comparison"]

    assert report["proposal_records"] == 6
    assert report["proposal_field_rows"] == 13
    assert report["source_rows"] == [6, 16, 17, 22, 27, 29]
    assert report["all_researcher_original_values_preserved"] is True


def test_build_artifacts_does_not_unblind_or_generate(tmp_path):
    result = integration.build_artifacts(tmp_path / "audit")

    assert result["status"] == "PASS_NO_UNBLINDING_NO_INFERENCE"
    assert result["restricted_unblinding_key_read"] is False
    names = {Path(path).name for path in result["artifacts"]}
    assert names == {
        "researcher_annotation_import_v1.json",
        "date_binding_audit_v1.json",
        "automatic_scorer_date_usage_audit_v1.json",
        "researcher_annotation_stage_a_compatibility_v1.csv",
    }


def test_scoring_audit_records_no_registered_date_substitution():
    report = integration.static_scorer_audit()

    assert report["conclusion"]["registered_evaluation_date_substitution_confirmed"] is False
    assert report["conclusion"]["corrected_scorer_created_in_this_audit"] is False
    assert report["restricted_unblinding_key_read"] is False
    assert len(report["call_chain"]) == 6


def test_stage_b_readiness_preserves_frozen_branch_budget_and_manifest_hashes():
    readiness = integration.stage_b_readiness()

    assert readiness["ledger"]["total_attempted"] == 72
    assert readiness["ledger"]["total_remaining"] == 88
    assert readiness["ledger"]["stage_B_activated"] is False
    assert set(readiness["manifests"]) == {"D0", "D1", "D2", "D3", "minimal_temporal", "fallback_calibration"}
    assert all(entry["registered_hash_match"] for entry in readiness["manifests"].values())
    assert readiness["restricted_unblinding_key_read"] is False


def test_expected_hash_mismatch_is_rejected(tmp_path):
    changed = tmp_path / "changed_v3.csv"
    changed.write_bytes(integration.REVIEW.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        integration.validate_researcher_submission(review_path=changed)
