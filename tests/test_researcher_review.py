"""Synthetic importer tests; these records are not human evaluations."""
from copy import deepcopy
import csv
import json

import pytest

from personaslm.neutral_review import EDITABLE, RATINGS
from personaslm.provenance import fingerprint
from personaslm.researcher_review import (EXTRA, VERSION, compare_versions,
    RESEARCHER_PROVENANCE_FIELDS, import_attested_review, normalize_rating, read_submission, validate_submission)


@pytest.fixture
def material():
    item = {"form_version": "neutral_annotation_form_v3", "case_id": "unit_fixture",
        "condition_id": "N_style", "neutral_text": "First line.\nSecond line.",
        "material_sha256": "fixture", **{k: "" for k in EDITABLE}}
    template = {"form_version": "neutral_annotation_form_v3", "items": [item]}
    template["packet_id"] = fingerprint(template)
    row = {**item, **{k: "no" for k in RATINGS}, "semantic_neutrality": "uncertain",
           "reference_conditioning_text": "Reference.", "control_suitability": "PARTIAL",
           "speaker_referent_ambiguity": "no", "assessment_source": "", "reference_repo_commit": "fixture"}
    return template, [row], list(row), {("unit_fixture", "N_style"): "Reference."}


def test_uncertain_counts_as_reviewed_but_not_valid(material):
    result = validate_submission(*material)
    assert len(result) == 1
    assert result[0]["derived_dimension_disposition"] == "PARTIAL"
    assert result[0]["reviewed_utc"] is None


def test_dimension_failure_does_not_rewrite_overall_judgment(material):
    material[1][0]["unintended_linguistic_style"] = "yes"
    row = validate_submission(*material)[0]
    assert row["derived_dimension_disposition"] == "FAILED"
    assert row["researcher_control_suitability"] == "PARTIAL"


@pytest.mark.parametrize("field,value", [(k, "") for k in RATINGS] + [
    ("semantic_neutrality", "PASS"), ("control_suitability", ""), ("speaker_referent_ambiguity", "maybe"),
    ("form_version", "neutral_annotation_form_v4"), ("neutral_text", "changed"),
    ("reference_conditioning_text", "changed")])
def test_missing_invalid_or_changed_fields_fail(material, field, value):
    material[1][0][field] = value
    with pytest.raises(ValueError):
        validate_submission(*material)


def test_missing_and_duplicate_records_fail(material):
    template, rows, fields, refs = material
    for bad in ([], rows + rows):
        with pytest.raises(ValueError):
            validate_submission(template, bad, fields, refs)


def test_missing_column_and_bad_template_digest_fail(material):
    template, rows, fields, refs = material
    with pytest.raises(ValueError):
        validate_submission(template, rows, fields[:-1], refs)
    template["items"][0]["neutral_text"] = "tampered"
    with pytest.raises(ValueError):
        validate_submission(template, rows, fields, refs)


def test_only_line_endings_are_canonicalized(material):
    material[1][0]["neutral_text"] = "First line.\r\nSecond line."
    validate_submission(*material)
    material[1][0]["neutral_text"] += " "
    with pytest.raises(ValueError):
        validate_submission(*material)


def test_rating_polarity():
    assert normalize_rating("answer_leakage", "yes") == "FAIL"
    assert normalize_rating("semantic_neutrality", "yes") == "PASS"
    assert normalize_rating("semantic_neutrality", "no") == "FAIL"


def test_supplied_time_is_preserved_and_invalid_time_rejected(material):
    material[1][0]["reviewed_utc"] = "2026-10-12T12:00:00+00:00"
    assert validate_submission(*material)[0]["reviewed_utc"] == "2026-10-12T12:00:00+00:00"
    for value in ("not a date", "2026-10-12T12:00:00", "2026-10-12T12:00:00+02:00"):
        material[1][0]["reviewed_utc"] = value
        with pytest.raises(ValueError):
            validate_submission(*material)


def test_extended_researcher_metadata_is_checked(material):
    template, rows, fields, refs = material
    rows[0].update({k: "" for k in RESEARCHER_PROVENANCE_FIELDS})
    rows[0].update({"reviewer_id": "UNIT_TEST_NOT_HUMAN", "review_type": "human_manual_researcher_review",
        "independent_blind_review": "no", "original_file_sha256": "a" * 64, "source_review_file_sha256": "b" * 64})
    fields = list(rows[0])
    validate_submission(template, rows, fields, refs)
    for name, value in (("reviewer_id", ""), ("independent_blind_review", "yes"),
                        ("review_type", "automatic"), ("original_file_sha256", "missing")):
        changed = deepcopy(rows)
        changed[0][name] = value
        with pytest.raises(ValueError):
            validate_submission(template, changed, fields, refs)


def test_missing_preliminary_is_unknown_not_zero(material):
    result = compare_versions(None, material[1])
    assert result["changed_judgments"] is None
    assert result["status"] == "UNAVAILABLE"


def test_diff_counts_only_actual_judgment_changes(material):
    before = deepcopy(material[1])
    after = deepcopy(before)
    after[0]["reviewer_id"] = "UNIT_TEST_REVIEWER_NOT_HUMAN"
    assert compare_versions(before, after)["changed_judgments"] == 0
    after[0]["answer_leakage"] = "yes"
    after[0]["semantic_neutrality"] = "no"
    result = compare_versions(before, after)
    assert result["changed_judgments"] == 2
    assert result["changed_records"] == 1
    with pytest.raises(ValueError):
        compare_versions(before + before, after)
    with pytest.raises(ValueError):
        compare_versions(before, [])


def test_duplicate_csv_headers_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("case_id,case_id\na,b\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_submission(path)


def test_full_import_retains_raw_missing_time_and_refuses_overwrite(tmp_path, material, monkeypatch):
    import hashlib
    # Model a standalone temporary repository; preserve the production path guard.
    monkeypatch.setattr("personaslm.provenance.repository_root", lambda: tmp_path)
    template, rows, fields, refs = material
    freeze = {"rows": [{"case_id": "unit_fixture", "neutral_condition": "N_style", "reference_condition": "C1"}],
              "prompts": {"unit_fixture": {"C1": {"prompt": {"additions": ["Reference."]}}}}}
    frozen_path = tmp_path / "freeze.json"
    frozen_path.write_text(json.dumps(freeze), encoding="utf-8")
    template["source_freeze_sha256"] = hashlib.sha256(frozen_path.read_bytes()).hexdigest()
    template["packet_id"] = fingerprint({k:v for k,v in template.items() if k != "packet_id"})
    template_path = tmp_path / "template.json"
    template_path.write_text(json.dumps(template), encoding="utf-8")
    submission = tmp_path / "submission.csv"
    with submission.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    attested = {"version": VERSION, "reviewer_id": "UNIT_TEST_REVIEWER_NOT_HUMAN",
        "review_type": "researcher_human_review", "confirmed_all_records_reviewed": True,
        "assistance": "AI-assisted human review", "blind_review": False,
        "submission_sha256": hashlib.sha256(submission.read_bytes()).hexdigest()}
    attestation_path = tmp_path / "attestation.json"
    attestation_path.write_text(json.dumps(attested), encoding="utf-8")
    output = tmp_path / "result.json"
    args = template_path, submission, frozen_path, attestation_path, output
    result = import_attested_review(*args)
    assert result["annotation_count"] == 1
    assert result["source_submission_utf8"] == submission.read_bytes().decode()
    assert result["reviewed_utc"] is None and result["inter_annotator_agreement"] is None
    with pytest.raises(FileExistsError):
        import_attested_review(*args)
    for key, value in (("reviewer_id", ""), ("version", "changed"), ("submission_sha256", "wrong"),
                       ("blind_review", True), ("confirmed_all_records_reviewed", False)):
        changed = {**attested, key: value}
        attestation_path.write_text(json.dumps(changed), encoding="utf-8")
        with pytest.raises(ValueError):
            import_attested_review(*args[:-1], tmp_path / (key + ".json"))
