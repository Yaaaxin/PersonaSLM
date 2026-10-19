from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import real_persona_chat_sfh_review_v1 as review


@pytest.fixture
def package():
    spec = review.protocol()
    fields = spec["schema"]["immutable_columns"] + spec["schema"]["editable_columns"]
    rows = [{**{field: "synthetic test fixture" for field in spec["schema"]["immutable_columns"]},
             "blind_record_id": f"RPC-A-{index:03d}", "model_response": "fixture response",
             **{field: "" for field in spec["schema"]["editable_columns"]}}
            for index in range(1, 65)]
    return {"spec": spec, "template_bytes": review.encode_csv(rows, fields)}, rows, fields


def test_opaque_schedule_is_output_independent_and_balanced():
    requests = [{"case_id": f"case-{case}", "condition": f"C{condition}"}
                for case in range(8) for condition in range(8)]
    rows = review.order_requests(requests, "test seed")
    assert rows == review.order_requests(list(reversed(requests)), "test seed")
    assert len({(row["case_id"], row["condition"]) for row in rows}) == 64
    for offset in range(0, 64, 8):
        assert len({row["case_id"] for row in rows[offset:offset + 8]}) == 8
        assert len({row["condition"] for row in rows[offset:offset + 8]}) == 8


def test_blank_copy_valid_draft_but_not_final(package):
    pkg, rows, fields = package
    report = review.validate_submission(pkg, review.encode_csv(rows, fields))
    assert report["errors"] == []
    assert report["counts"] == {"not_started": 64, "in_progress": 0, "finalized": 0}
    assert review.validate_submission(pkg, review.encode_csv(rows, fields), final=True)["errors"]


def test_missing_duplicate_immutable_overflow_rejected(package):
    pkg, rows, fields = package
    with pytest.raises(ValueError):
        review.validate_submission(pkg, review.encode_csv(rows[:-1], fields))
    rows[1]["blind_record_id"] = rows[0]["blind_record_id"]
    assert review.validate_submission(pkg, review.encode_csv(rows, fields))["errors"]
    content = review.encode_csv(rows, fields).rstrip() + b",EXTRA\n"
    with pytest.raises(ValueError):
        review.validate_submission(pkg, content)


def test_unavailable_is_disposition_not_zero(package):
    pkg, rows, fields = package
    for row in rows:
        row.update(annotation_status="UNAVAILABLE", missing_reason="Synthetic test reason")
    report = review.validate_submission(pkg, review.encode_csv(rows, fields), final=True)
    assert report["errors"] == [] and report["counts"]["finalized"] == 64
    rows[0]["response_relevance"] = "1"
    assert review.validate_submission(pkg, review.encode_csv(rows, fields))["errors"]


def test_completed_requires_exact_span_and_all_judgments(package):
    pkg, rows, fields = package
    row = rows[0]
    row.update(annotation_status="COMPLETED", response_relevance="4", conversational_coherence="4",
               linguistic_style_resemblance="UNCERTAIN", persona_statement_consistency="NO_RELEVANT_CLAIM",
               history_consistency="CONSISTENT", unsupported_personal_claim="NO", answer_completeness="NOT_APPLICABLE",
               evidence_span="fixture", reviewer_rationale="Synthetic fixture rationale", reviewer_confidence="LOW")
    assert not review.validate_submission(pkg, review.encode_csv(rows, fields))["errors"]
    row["evidence_span"] = "not in the response"
    assert review.validate_submission(pkg, review.encode_csv(rows, fields))["errors"]
    row["model_response"] = review.MISSING_RESPONSE
    assert review.validate_submission(pkg, review.encode_csv(rows, fields))["errors"]


def fixture_provenance(pkg, content, tmp_path, monkeypatch):
    instructions, receipt = tmp_path / "instructions.json", tmp_path / "receipt.json"
    instructions.write_text("{}")
    receipt.write_text("{}")
    monkeypatch.setattr(review, "INSTRUCTIONS", instructions)
    monkeypatch.setattr(review, "RECEIPT", receipt)
    value = review.provenance_skeleton(pkg, content)
    assert value["human_reviewer"] is None
    value.update(reviewer_pseudonym="TEST_ONLY", private_reviewer_identifier="TEST_ONLY",
                 human_reviewer=True, independent_of_project=False, japanese_competence_attested=True,
                 japanese_competence_description="Synthetic unit-test attestation", relationship="PRINCIPAL_RESEARCHER",
                 review_environment="Synthetic test fixture", aids_used="None", notes="Test only",
                 started_utc="2026-10-19T00:00:00Z", completed_utc="2026-10-19T00:01:00Z")
    for field in ("machine_translation_used_for_judgments", "prior_rubric_or_item_involvement", "prior_exposure_to_outputs",
                  "condition_mapping_seen_before_lock", "automatic_or_ai_labels_seen_before_lock", "ai_assistance_used_for_judgments"):
        value[field] = "NO"
    return value


def test_provenance_qualification_and_project_independence(package, tmp_path, monkeypatch):
    pkg, rows, fields = package
    content = review.encode_csv(rows, fields)
    value = fixture_provenance(pkg, content, tmp_path, monkeypatch)
    assert review.validate_provenance(pkg, content, value)["classification"] == "CONDITION_MASKED_NONINDEPENDENT_HUMAN"
    value["prior_rubric_or_item_involvement"] = "YES"
    assert review.validate_provenance(pkg, content, value)["classification"] == "HUMAN_EXPOSURE_LIMITED"
    value["independent_of_project"] = True
    assert review.validate_provenance(pkg, content, value)["errors"]
    value["independent_of_project"] = False
    value["japanese_competence_attested"] = False
    assert review.validate_provenance(pkg, content, value)["classification"] == "INELIGIBLE_FOR_ORIGINAL_JAPANESE_HUMAN_ONLY_CLAIM"


def test_provenance_ai_and_hash_errors_rejected(package, tmp_path, monkeypatch):
    pkg, rows, fields = package
    content = review.encode_csv(rows, fields)
    value = fixture_provenance(pkg, content, tmp_path, monkeypatch)
    value["ai_assistance_used_for_judgments"] = "UNCERTAIN"
    assert review.validate_provenance(pkg, content, value)["errors"]
    value["ai_assistance_used_for_judgments"] = "NO"
    value["completed_csv_sha256"] = "incorrect"
    assert review.validate_provenance(pkg, content, value)["errors"]


def test_private_paths_and_protocol_count():
    with pytest.raises(ValueError):
        review.private_path(review.REPO / "public.csv")
    with pytest.raises(ValueError):
        review.private_path(review.MAPPING)
    assert review.protocol()["allocation"]["records"] == 64
