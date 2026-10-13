"""Software-only annotation fixtures; not human judgments or study records."""
from copy import deepcopy
import csv
import json
from pathlib import Path

import pytest

from personaslm.control_final_review import EDITABLE, RATINGS, import_review, make_packet, validate_review

PUBLIC = Path(__file__).resolve().parents[1] / "docs/validation"


@pytest.fixture
def packet():
    def read(name):
        return json.loads((PUBLIC / name).read_text(encoding="utf-8"))
    return make_packet(read("P0_control_development_review_v2.json"),
                       read("P0_control_candidate_freeze_v2.json"),
                       read("P0_control_tokenizer_validation_v2.json"), {"fixture": "SOFTWARE_ONLY"})


def fixture_reviews(packet):
    rows = deepcopy(packet["items"])
    for row in rows:
        row.update({k: "PASS" for k in RATINGS})
        row["reviewer_id"] = "SOFTWARE_TEST_NOT_HUMAN"
        row["review_assistance"] = "unassisted"
    return rows


def test_all24_materials_retained_with_dates_and_answers(packet):
    assert len(packet["items"]) == 24
    assert len({r["candidate_id"] for r in packet["items"]}) == 24
    for row in packet["items"]:
        assert row["expected_answer"] in row["trusted_evidence"]
        assert row["expected_answer"] not in row["candidate_control_text"]
        assert row["reference_token_count"] == row["candidate_token_count"]
        assert row["token_difference"] == "0"
        assert row["evaluation_date"] == "2026-10-12"
        assert (row["reference_date"] == "NOT_APPLICABLE") == (row["candidate_family"] == "style_generic")
        if row["candidate_family"] != "style_generic":
            assert row["reference_date"] in row["original_active_intervention"]
        assert all(not row[k] for k in EDITABLE)
        assert all(k in row["review_questions"] for k in RATINGS)


def test_blank_template_cannot_be_imported_as_completed(packet):
    rows = packet["items"]
    assert validate_review(packet, rows, list(rows[0]), require_complete=False) == []
    with pytest.raises(ValueError, match="Incomplete"):
        validate_review(packet, rows, list(rows[0]))


@pytest.mark.parametrize("field,value", [
    ("answer_leakage", ""), ("semantic_neutrality", "PARTIAL"), ("comparison_suitability", "NOT_APPLICABLE"),
    ("evidence_question_preservation", ""), ("reviewer_id", " "), ("review_assistance", ""),
    ("reviewed_utc", "2026-10-12T12:00:00"), ("reviewed_utc", "2026-10-12T12:00:00+02:00"),
    ("candidate_control_text", "Rewritten."), ("expected_answer", "Replaced"),
    ("reference_date", "2025-01-01"), ("candidate_token_count", "1"), ("form_version", "old"),
    ("unintended_linguistic_style_evidence_quote", "Fabricated quotation")])
def test_invalid_or_changed_review_rejected(packet, field, value):
    rows = fixture_reviews(packet)
    rows[0][field] = value
    with pytest.raises(ValueError):
        validate_review(packet, rows, list(rows[0]))


def test_duplicate_unknown_missing_rows_and_columns(packet):
    rows = fixture_reviews(packet)
    for changed in (rows + rows[:1], rows[:-1]):
        with pytest.raises(ValueError):
            validate_review(packet, changed, list(rows[0]))
    rows[0]["candidate_id"] = "unknown"
    with pytest.raises(ValueError):
        validate_review(packet, rows, list(rows[0]))
    for fields in (list(rows[0])[:-1], list(rows[0]) + ["case_id"]):
        with pytest.raises(ValueError):
            validate_review(packet, fixture_reviews(packet), fields)


def test_partial_review_is_explicit_and_missing_time_stays_missing(packet):
    rows = fixture_reviews(packet)
    rows[-1] = deepcopy(packet["items"][-1])
    with pytest.raises(ValueError, match="Incomplete"):
        validate_review(packet, rows, list(rows[0]))
    reviewed = validate_review(packet, rows, list(rows[0]), require_complete=False)
    assert len(reviewed) == 23
    assert all(row["reviewed_utc"] == "" for row in reviewed)


def test_failures_and_uncertainty_need_quotes_and_remain_distinct(packet):
    rows = fixture_reviews(packet)
    rows[0]["semantic_neutrality"] = "UNCERTAIN"
    with pytest.raises(ValueError, match="quote"):
        validate_review(packet, rows, list(rows[0]))
    rows[0]["semantic_neutrality_evidence_quote"] = rows[0]["candidate_control_text"]
    rows[1]["comparison_suitability"] = "FAIL"
    rows[1]["comparison_suitability_evidence_quote"] = rows[1]["candidate_control_text"]
    validated = validate_review(packet, rows, list(rows[0]))
    assert validated[0]["semantic_neutrality"] == "UNCERTAIN"
    assert validated[1]["comparison_suitability"] == "FAIL"


def test_family_specific_not_applicable_does_not_mean_pass(packet):
    rows = fixture_reviews(packet)
    for row in rows:
        for field in set(row["not_applicable_fields"].split(", ")) - {""}:
            row[field] = "NOT_APPLICABLE"
    assert len(validate_review(packet, rows, list(rows[0]))) == 24
    rows[1]["semantic_neutrality"] = "NOT_APPLICABLE"
    with pytest.raises(ValueError):
        validate_review(packet, rows, list(rows[0]))


def test_master_tampering_rejected(packet):
    rows = fixture_reviews(packet)
    packet["items"][0]["current_question"] = "changed"
    with pytest.raises(ValueError, match="digest"):
        validate_review(packet, rows, list(rows[0]))


def test_import_preserves_master_raw_submission_and_prior_outputs(packet, tmp_path, monkeypatch):
    from personaslm import provenance
    monkeypatch.setattr(provenance, "repository_root", lambda: tmp_path)
    master, submission, destination = (tmp_path / name for name in ("master.json", "completed.csv", "review-v1.json"))
    master.write_text(json.dumps(packet), encoding="utf-8")
    original = master.read_bytes()
    rows = fixture_reviews(packet)
    rows[0]["comparison_suitability"] = "UNCERTAIN"
    rows[0]["comparison_suitability_evidence_quote"] = rows[0]["candidate_control_text"]
    with submission.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    result = import_review(submission, destination, master_path=master)
    assert result["completed"] == 24 and result["completion_status"] == "PASS"
    assert result["human_comparison_suitability"] == {"UNCERTAIN": 1, "PASS": 23}
    assert "Not automatically" in result["control_acceptance"]
    assert master.read_bytes() == original
    assert result["submission_utf8"] == submission.read_bytes().decode("utf-8-sig")
    with pytest.raises(FileExistsError):
        import_review(submission, destination, master_path=master)
