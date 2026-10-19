import csv
import io
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import p1_persona_dialogue_disjoint_surface_validation_review_v4 as module


def test_official_public_review_artifacts_remain_frozen():
    assert {"template": module.sha256(module.TEMPLATE),
            "instructions": module.sha256(module.INSTRUCTIONS),
            "receipt": module.sha256(module.RECEIPT),
            "protocol": module.sha256(module.PROTOCOL)} == \
        module.FROZEN_PUBLIC_HASHES


def encode(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def fixture_package(tmp_path):
    protocol = json.loads(module.PROTOCOL.read_text(encoding="utf-8"))
    stage = protocol["stage_a"]
    fields = (stage["reviewer_visible_immutable_columns"] +
              stage["editable_columns"])
    rows = []
    for index in range(168):
        rows.append({
            "blind_record_id": f"DSV1-A-{index + 1:03d}",
            "response_instruction": "Choose one option.",
            "synthetic_persona_profile": "Synthetic profile.",
            "current_evidence_and_choices": "Current evidence.",
            "current_user_turn": "Please choose.",
            "model_response": "Alpha response.",
            **{field: "" for field in stage["editable_columns"]},
        })
    template = tmp_path / "template.csv"
    instructions = tmp_path / "instructions.json"
    receipt = tmp_path / "receipt.json"
    protocol_path = tmp_path / "protocol.json"
    template.write_bytes(encode(rows, fields))
    instructions.write_text("{}\n", encoding="utf-8")
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
    receipt.write_text(json.dumps({
        "stage": "A", "record_count": 168, "mapping_in_delivery": False,
        "labels_created": 0, "template_sha256": module.sha256(template),
        "instructions_sha256": module.sha256(instructions),
        "review_schema_sha256": module.sha256(protocol_path),
    }), encoding="utf-8")
    package = module.load_package(
        template, instructions, receipt, protocol_path)
    return package, rows, fields


def unavailable_rows(rows):
    result = [dict(row) for row in rows]
    for row in result:
        row["annotation_status"] = "UNAVAILABLE"
        row["missing_reason"] = "Reviewer could not assess this record."
    return result


def complete_first_row(rows):
    result = unavailable_rows(rows)
    row = result[0]
    row.update({
        "annotation_status": "COMPLETED", "missing_reason": "",
        "selected_entity": "CURRENT_OPTION_A", "reason_support": "SUPPORTED",
        "current_fact_consistency": "CONSISTENT",
        "behavioral_persona_fidelity": "5", "response_relevance": "5",
        "conversational_coherence": "5", "answer_completeness": "COMPLETE",
        "linguistic_prefix_match": "EXACT", "linguistic_suffix_match": "EXACT",
        "global_linguistic_persona_fidelity": "4",
        "material_unverifiable_claim": "NO", "evidence_span": "Alpha",
        "reviewer_rationale": "The response selects the current option.",
        "reviewer_confidence": "HIGH",
    })
    return result


def provenance(package, submission, **updates):
    value = module.provenance_skeleton(package, submission)
    value.update({
        "reviewer_pseudonym": "R1",
        "private_reviewer_identifier": "private-local-id",
        "human_reviewer": True,
        "relationship": "PRINCIPAL_RESEARCHER",
        "independent_of_project": False,
        "prior_rubric_or_item_involvement": "NO",
        "prior_exposure_to_outputs": "NO",
        "condition_mapping_seen_before_lock": "NO",
        "automatic_or_ai_labels_seen_before_lock": "NO",
        "ai_assistance_used_for_judgments": "NO",
        "stage_b_material_seen_before_stage_a_lock": "NO",
        "review_environment": "offline spreadsheet",
        "started_utc": "2026-10-19T10:00:00Z",
        "completed_utc": "2026-10-19T12:00:00Z",
        "notes": "",
    })
    value.update(updates)
    return (json.dumps(value) + "\n").encode("utf-8")


def test_incremental_draft_accepts_blank_and_partial_rows(tmp_path):
    package, rows, fields = fixture_package(tmp_path)
    blank = module.validate_submission(package, encode(rows, fields), final=False)
    assert not blank["errors"]
    assert blank["counts"] == {
        "records_assigned": 168, "records_finalized": 0,
        "records_in_progress": 0, "records_not_started": 168}

    rows[0]["selected_entity"] = "CURRENT_OPTION_A"
    partial = module.validate_submission(package, encode(rows, fields), final=False)
    assert not partial["errors"]
    assert partial["counts"]["records_in_progress"] == 1
    assert partial["warnings"][0]["code"] == "STATUS_REQUIRED"
    assert partial["warnings"][0]["blind_record_id"] == "DSV1-A-001"


def test_truncated_row_reports_missing_cell_instead_of_crashing(tmp_path):
    package, rows, fields = fixture_package(tmp_path)
    lines = encode(rows, fields).decode("utf-8").splitlines()
    lines[1] = lines[1].rsplit(",", 1)[0]
    malformed = ("\n".join(lines) + "\n").encode("utf-8")

    try:
        module.validate_submission(package, malformed, final=False)
        assert False, "truncated row unexpectedly passed validation"
    except ValueError as exc:
        assert str(exc) == "CSV contains a missing or extra cell"


def test_draft_reports_immutable_and_value_errors_without_response_text(tmp_path):
    package, rows, fields = fixture_package(tmp_path)
    rows[0]["current_user_turn"] = "changed"
    rows[1]["annotation_status"] = "COMPLETED"
    rows[1]["selected_entity"] = "NOT_AN_ENUM"
    report = module.validate_submission(package, encode(rows, fields), final=False)
    codes = {item["code"] for item in report["errors"]}
    assert {"IMMUTABLE_CELL_CHANGED", "INVALID_ENUM"} <= codes
    assert "Alpha response" not in json.dumps(report)


def test_partial_draft_reports_invalid_enum_and_evidence_span(tmp_path):
    package, rows, fields = fixture_package(tmp_path)
    rows[0]["selected_entity"] = "NOT_AN_ENUM"
    rows[0]["evidence_span"] = "not present"

    report = module.validate_submission(
        package, encode(rows, fields), final=False)
    assert {item["code"] for item in report["errors"]} == {
        "INVALID_ENUM", "INVALID_EVIDENCE_SPAN"}
    assert {item["code"] for item in report["warnings"]} == {
        "STATUS_REQUIRED"}


def test_final_requires_168_adjudicated_rows(tmp_path):
    package, rows, fields = fixture_package(tmp_path)
    report = module.validate_submission(package, encode(rows, fields), final=True)
    assert report["counts"]["records_not_started"] == 168
    assert "ALL_168_RECORDS_REQUIRED" in {
        item["code"] for item in report["errors"]}


def test_complete_and_unavailable_rows_match_frozen_semantics(tmp_path):
    package, rows, fields = fixture_package(tmp_path)
    submitted = encode(complete_first_row(rows), fields)
    report = module.validate_submission(package, submitted, final=True)
    assert not report["errors"]
    assert report["counts"]["records_finalized"] == 168

    bad = complete_first_row(rows)
    bad[0]["evidence_span"] = "not present"
    bad_report = module.validate_submission(package, encode(bad, fields), final=True)
    assert "INVALID_EVIDENCE_SPAN" in {
        item["code"] for item in bad_report["errors"]}


def test_v4_classification_includes_rubric_item_exposure_and_independence(tmp_path):
    package, rows, fields = fixture_package(tmp_path)
    submitted = encode(unavailable_rows(rows), fields)
    base = json.loads(provenance(package, submitted))

    assert module.corrected_classification(base) == \
        "BLINDED_NONINDEPENDENT_HUMAN"
    assert module.legacy_v3_classification(base) == "CLEAN_BLINDED_HUMAN"

    rubric = {**base, "prior_rubric_or_item_involvement": "YES"}
    assert module.corrected_classification(rubric) == "HUMAN_EXPOSURE_LIMITED"
    assert module.legacy_v3_classification(rubric) == "CLEAN_BLINDED_HUMAN"

    exposed = {**base, "prior_exposure_to_outputs": "UNCERTAIN"}
    assert module.corrected_classification(exposed) == "HUMAN_EXPOSURE_LIMITED"

    independent = {**base, "relationship": "INDEPENDENT_EXTERNAL",
                   "independent_of_project": True}
    assert module.corrected_classification(independent) == \
        "CLEAN_INDEPENDENT_BLINDED_HUMAN"

    ai = {**base, "ai_assistance_used_for_judgments": "UNCERTAIN"}
    assert module.corrected_classification(ai) == \
        "INELIGIBLE_AS_GENUINE_HUMAN"


def test_final_readiness_binds_files_and_never_claims_pi_independence(tmp_path):
    package, rows, fields = fixture_package(tmp_path)
    submission_path = tmp_path / "review.csv"
    provenance_path = tmp_path / "provenance.json"
    submitted = encode(unavailable_rows(rows), fields)
    submission_path.write_bytes(submitted)
    provenance_path.write_bytes(provenance(package, submitted))
    report = module.validate(
        package, submission_path, provenance_path, final=True)
    assert report["status"] == "READY_FOR_OFFICIAL_SEAL_ATTEMPT_NOT_SEALED"
    assert report["protected_mapping_accessed"] is False
    assert report["official_seal_created"] is False
    assert report["provenance"]["corrected_classification_v4"] == \
        "BLINDED_NONINDEPENDENT_HUMAN"
    assert report["provenance"]["legacy_v3_classification_prediction"] == \
        "CLEAN_BLINDED_HUMAN"
    assert report["provenance"]["legacy_v3_classification_differs"] is True
    assert report["provenance"]["legacy_v3_would_overstate_cleanliness"] is True
    assert "not independent" in report["provenance"]["claim_boundary"]


def test_final_rejects_ai_assistance(tmp_path):
    package, rows, fields = fixture_package(tmp_path)
    submission_path = tmp_path / "review.csv"
    provenance_path = tmp_path / "provenance.json"
    submitted = encode(unavailable_rows(rows), fields)
    submission_path.write_bytes(submitted)
    provenance_path.write_bytes(provenance(
        package, submitted, ai_assistance_used_for_judgments="YES"))
    report = module.validate(package, submission_path, provenance_path, final=True)
    assert report["status"] == "NOT_READY"
    assert report["provenance"]["corrected_classification_v4"] == \
        "INELIGIBLE_AS_GENUINE_HUMAN"
    assert "GENUINE_HUMAN_PROVENANCE_REQUIRED" in {
        item["code"] for item in report["errors"]}


def test_final_rejects_hash_mismatch_and_false_independence(tmp_path):
    package, rows, fields = fixture_package(tmp_path)
    submitted = encode(unavailable_rows(rows), fields)
    provenance_report = module.validate_provenance(
        package, provenance(package, submitted,
                               independent_of_project=True,
                               completed_csv_sha256="0" * 64), submitted)
    codes = {item["code"] for item in provenance_report["errors"]}
    assert {"PROVENANCE_HASH_MISMATCH",
            "INDEPENDENCE_ATTESTATION_CONFLICT"} <= codes


def test_init_and_provenance_writes_are_exclusive(tmp_path):
    target = tmp_path / "working" / "review.csv"
    module.write_exclusive(target, b"first")
    try:
        module.write_exclusive(target, b"second")
        assert False, "exclusive write unexpectedly overwrote a file"
    except FileExistsError:
        pass
    assert target.read_bytes() == b"first"


def test_cli_can_preserve_an_exclusive_final_receipt(tmp_path, monkeypatch):
    package, rows, fields = fixture_package(tmp_path)
    submitted = encode(unavailable_rows(rows), fields)
    submission_path = tmp_path / "review.csv"
    provenance_path = tmp_path / "provenance.json"
    report_path = tmp_path / "validation_v4.json"
    submission_path.write_bytes(submitted)
    provenance_path.write_bytes(provenance(package, submitted))
    monkeypatch.setattr(module, "load_package", lambda: package)
    assert module.main([
        "validate-final", "--submission", str(submission_path),
        "--provenance", str(provenance_path), "--report", str(report_path)]) == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "READY_FOR_OFFICIAL_SEAL_ATTEMPT_NOT_SEALED"
    assert report["bindings"]["helper_sha256"] == module.sha256(
        Path(module.__file__))
