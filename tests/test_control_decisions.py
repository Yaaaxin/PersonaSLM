"""Synthetic software submissions exercise conversion, not human validity."""
import csv
import json
from pathlib import Path

import pytest

from personaslm.control_decisions import (
    CHECKS, EXPECTED_DECISIONS, LABEL_MAP, MATERIAL_FIELDS, SOURCE_FIELDS,
    convert_rows, read_csv, register, validate_source, verify_master,
)
from personaslm.control_final_review import EDITABLE, RATINGS, validate_review
from personaslm.provenance import sha256

PUBLIC = Path(__file__).resolve().parents[1] / "docs/validation"


@pytest.fixture
def materials():
    master = json.loads((PUBLIC / "P0_final_control_review_v3.json").read_text(encoding="utf-8"))
    fields, master_rows = read_csv(PUBLIC / "P0_final_control_review_v3.csv")
    rows = []
    for index, item in enumerate(master["items"], 1):
        row = dict.fromkeys(SOURCE_FIELDS, "SOFTWARE_TEST_ONLY")
        row.update({src: item[dst] for src, dst in MATERIAL_FIELDS.items()})
        row.update({"item_number": str(index), "prompt_hashes_verified_locally": "yes",
                    "evidence_question_preserved_locally": "yes",
                    "researcher_textual_evidence_quote": item["candidate_control_text"],
                    "researcher_decision": EXPECTED_DECISIONS[item["candidate_family"]]})
        row.update({"researcher_check_" + key: "yes" for key in CHECKS})
        rows.append(row)
    attestation = {"reviewer_id": "SOFTWARE_TEST_NOT_HUMAN", "researcher_confirmed": True,
                   "preliminary_ai_recommendations_available": True, "blind_review": False,
                   "source_label_mapping": LABEL_MAP, "mapping_confirmation": "ENGINEERED_TEST_INPUT"}
    return master, fields, master_rows, rows, attestation


def test_blank_master_and_all_source_materials_validate(materials):
    master, fields, master_rows, rows, _ = materials
    verify_master(master, fields, master_rows)
    validate_source(master, list(SOURCE_FIELDS), rows)


@pytest.mark.parametrize("field,value", [
    ("candidate_id", "unknown"), ("candidate_control_text", "changed"),
    ("active_intervention", "changed"), ("case_id", "wrong"),
    ("candidate_family", "style_generic_other"), ("speaker", "wrong"),
    ("reported_candidate_tokens", "999"), ("expected_answer_reference_only", "wrong"),
    ("researcher_check_answer_leakage", ""), ("researcher_check_semantic_neutrality", "MAYBE"),
    ("researcher_decision", "PASS"), ("researcher_decision", "ACCEPT_NARROW"),
    ("researcher_textual_evidence_quote", "Not found anywhere in the materials"),
])
def test_changed_materials_and_invalid_source_rejected(materials, field, value):
    master, _, _, rows, _ = materials
    rows[0][field] = value
    with pytest.raises(ValueError):
        validate_source(master, list(SOURCE_FIELDS), rows)


def test_missing_duplicate_and_malformed_rows_rejected(materials):
    master, _, _, rows, _ = materials
    for bad in (rows[:-1], rows + rows[:1], [dict(rows[0], item_number="2"), *rows[1:]],
                [dict(rows[0], researcher_notes=None), *rows[1:]]):
        with pytest.raises(ValueError):
            validate_source(master, list(SOURCE_FIELDS), bad)
    for fields in (list(SOURCE_FIELDS)[:-1], [*SOURCE_FIELDS, "case_id"]):
        with pytest.raises(ValueError):
            validate_source(master, fields, rows)


def test_four_label_mapping_does_not_follow_overall_disposition(materials):
    master, fields, _, rows, attestation = materials
    for source, label in LABEL_MAP.items():
        rows[1]["researcher_check_semantic_neutrality"] = source
        converted, records, _ = convert_rows(master, rows, attestation=attestation)
        assert converted[1]["semantic_neutrality"] == label
        assert converted[1]["comparison_suitability"] == "PASS"
        assert records[1]["researcher_decision"] == "ACCEPT_NARROW"
        assert not records[1]["unqualified_neutral_acceptance"]
        # JSON master keys are sorted; the CSV writer uses the official CSV
        # header order, verified by the registration round-trip test below.
        assert set(converted[1]) == set(fields)


def test_decision_scope_is_not_unqualified_comparison_pass(materials):
    master, _, _, rows, attestation = materials
    converted, records, gaps = convert_rows(master, rows, attestation=attestation)
    assert sum(r["comparison_suitability"] == "PASS" for r in converted) == 6
    assert sum(r["comparison_suitability"] == "" for r in converted) == 18
    for original, record in zip(rows, records):
        assert record["source_row"] == original
        assert record["researcher_decision"] == original["researcher_decision"]
    assert sum(g["issue"] == "missing_official_label" for g in gaps) == 18


def test_incompatible_na_is_preserved_and_flagged(materials):
    master, _, _, rows, attestation = materials
    rows[0]["researcher_check_conversational_coherence"] = "not_applicable"
    converted, _, gaps = convert_rows(master, rows, attestation=attestation)
    assert converted[0]["conversational_coherence"] == "NOT_APPLICABLE"
    assert any(g["issue"] == "not_applicable_not_allowed" and g["field"] == "conversational_coherence" for g in gaps)


def test_global_quote_never_fabricates_per_field_attribution(materials):
    master, fields, _, rows, attestation = materials
    rows[1]["researcher_check_topic_alignment"] = "no"
    converted, records, gaps = convert_rows(master, rows, attestation=attestation)
    assert records[1]["global_quote_verbatim"] == rows[1]["researcher_textual_evidence_quote"]
    assert all(row[field + "_evidence_quote"] == "" for row in converted for field in RATINGS)
    assert any(g["field"] == "topic_alignment_evidence_quote" for g in gaps)
    with pytest.raises(ValueError):
        validate_review(master, converted, fields)


@pytest.mark.parametrize("key", ["mapping_confirmation", "reviewer_id", "researcher_confirmed", "preliminary_ai_recommendations_available", "blind_review"])
def test_provenance_must_be_attested(materials, key):
    master, _, _, rows, attestation = materials
    del attestation[key]
    with pytest.raises(ValueError):
        convert_rows(master, rows, attestation=attestation)


def test_unknown_review_time_not_registration_time(materials):
    master, _, _, rows, attestation = materials
    converted, _, _ = convert_rows(master, rows, attestation=attestation)
    assert all(row["reviewed_utc"] == "" for row in converted)
    assert all(row["reviewer_id"] == "SOFTWARE_TEST_NOT_HUMAN" and row["review_assistance"] == "AI-assisted" for row in converted)


def test_master_and_prompt_tampering_rejected(materials):
    master, fields, master_rows, _, _ = materials
    master["items"][0]["candidate_prompt"] += " altered"
    with pytest.raises(ValueError):
        verify_master(master, fields, master_rows)


def test_registration_archives_bytes_and_refuses_overwrite(materials, tmp_path, monkeypatch):
    from personaslm import provenance
    monkeypatch.setattr(provenance, "repository_root", lambda: tmp_path)
    monkeypatch.chdir(tmp_path)
    master, fields, master_rows, rows, attestation = materials
    master_json = tmp_path / "master.json"
    master_json.write_text(json.dumps(master), encoding="utf-8")
    master_csv, submission = tmp_path / "master.csv", tmp_path / "source.csv"
    for path, names, values in ((master_csv, fields, master_rows), (submission, SOURCE_FIELDS, rows)):
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=names)
            writer.writeheader()
            writer.writerows(values)
    source_bytes, master_bytes = submission.read_bytes(), master_csv.read_bytes()
    attestation_path = tmp_path / "attestation.json"
    attestation["source_sha256"] = sha256(submission)
    attestation_path.write_text(json.dumps(attestation), encoding="utf-8")
    output = tmp_path / "registration"
    result = register(submission, master_json, master_csv, attestation_path, output)
    assert result["decision_completion_status"] == "PASS"
    assert result["researcher_confirmed_decisions"] == 24
    assert result["strict_annotation_schema"]["status"] == "PARTIAL"
    assert result["reviewed_utc"] is None
    assert submission.read_bytes() == (output / "source_review.csv").read_bytes() == source_bytes
    assert master_csv.read_bytes() == master_bytes
    converted_fields, converted_rows = read_csv(output / "annotation_65_columns.csv")
    assert converted_fields == fields and len(converted_rows) == 24
    assert all(row["reviewer_notes"] == original["researcher_notes"] for row, original in zip(converted_rows, rows))
    with pytest.raises(FileExistsError):
        register(submission, master_json, master_csv, attestation_path, output)
    attestation["source_sha256"] = "0" * 64
    attestation_path.write_text(json.dumps(attestation), encoding="utf-8")
    with pytest.raises(ValueError, match="bound"):
        register(submission, master_json, master_csv, attestation_path, tmp_path / "bad")
    assert not (tmp_path / "bad").exists()
