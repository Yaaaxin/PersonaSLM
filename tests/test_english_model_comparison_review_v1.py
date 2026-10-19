"""Authored synthetic fixtures only; no actual outputs, ratings or mappings."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import english_model_comparison_review_v1 as review


def authored_records():
    return [{"request_id": f"authored-request-{i}", "case_id": f"authored-case-{i // 20}",
             "dossier": "Authored fictional test context, not participant evidence.",
             "response": "Authored test response."} for i in range(200)]


@pytest.fixture
def package(tmp_path, monkeypatch):
    monkeypatch.setattr(review.legacy, "PRIVATE_ROOT", tmp_path)
    paths = (tmp_path / "delivery", tmp_path / "analyst" / "protected.json",
             tmp_path / "analyst" / "helper.json", tmp_path / "public.json")
    review.build_package(authored_records(), *paths, sealed_source_sha256="a" * 64,
                         dossiers_redacted=True)
    delivery, mapping, helper, receipt = paths
    return review.load_package(delivery, helper, receipt), paths


def rows_for(package, unavailable=False):
    delivery = package[1][0]
    rows = review.decode_csv((delivery / "REVIEW.csv").read_bytes())
    for row in rows:
        if unavailable:
            row.update(annotation_status="UNAVAILABLE", missing_reason="Authored unavailable fixture")
        else:
            row.update(annotation_status="COMPLETED", relevance="0", coherence="5", linguistic_resemblance="3")
    return rows


def content(rows):
    return review.legacy.encode_csv(rows, review.FIELDS)


def provenance_for(data):
    value = review.legacy.provenance_template()
    value.update({key: "NO" for key in review.legacy.EXPOSURES})
    value.update(prior_rubric_or_item_involvement="YES", prior_exposure_to_outputs="YES",
                 human_reviewer=True, english_competence_attested=True,
                 reviewer_pseudonym="AUTHORED_FIXTURE_NOT_REAL_REVIEWER",
                 english_competence_description="Authored test only", review_environment="Fixture",
                 aids_used="None in this authored fixture", started_utc="2026-01-01T00:00:00Z",
                 completed_utc="2026-01-01T01:00:00Z", completed_csv_sha256=review.legacy.prior.sha256_bytes(data))
    return value


def test_blank_delivery_model_masking_and_scoped_globals(package):
    loaded, (delivery, mapping, helper, receipt) = package
    assert review.legacy.RUBRIC != review.RUBRIC
    assert review.legacy.FIELDS != review.FIELDS
    blank = review.decode_csv((delivery / "REVIEW.csv").read_bytes())
    assert len(blank) == 200 and all(not row[key] for row in blank for key in review.EDITABLE)
    visible = (delivery / "records.json").read_text(encoding="utf-8")
    assert "authored-request" not in visible and "authored-case" not in visible
    assert not any("claim" in key or "confidence" in key for key in review.FIELDS)
    provenance = json.loads((delivery / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["human_reviewer"] is None and provenance["started_utc"] is None
    mapping.unlink()  # Intake succeeds without even this synthetic protected map.
    assert review.load_package(delivery, helper, receipt)["rows"] == loaded["rows"]
    checked = review.validate_submission(loaded, content(blank))
    assert not checked["errors"] and checked["counts"]["not_started"] == 200
    assert review.validate_submission(loaded, content(blank), final=True)["errors"]


def test_zero_five_na_and_all_unavailable_are_distinct(package):
    rows = rows_for(package)
    checked = review.validate_submission(package[0], content(rows), final=True)
    assert not checked["errors"] and checked["domain_coverage"]["relevance"]["numeric"] == 200
    rows[0]["linguistic_resemblance"] = "NA"
    assert review.validate_submission(package[0], content(rows), final=True)["errors"]
    rows[0]["rationale"] = "Authored fixture: insufficient style evidence to judge resemblance."
    checked = review.validate_submission(package[0], content(rows), final=True)
    assert not checked["errors"] and checked["domain_coverage"]["linguistic_resemblance"]["na"] == 1
    unavailable = rows_for(package, unavailable=True)
    checked = review.validate_submission(package[0], content(unavailable), final=True)
    assert not checked["errors"] and checked["counts"]["finalized"] == checked["counts"]["unavailable"] == 200
    assert checked["domain_coverage"]["relevance"] == {"numeric": 0, "na": 0, "blank": 200}
    unavailable[0]["relevance"] = "0"
    assert review.validate_submission(package[0], content(unavailable))["errors"]


def test_partial_uncertain_draft_preserves_other_genuine_entries(package):
    rows = rows_for(package)
    rows[0]["linguistic_resemblance"] = ""
    data = content(rows)
    draft = review.validate_submission(package[0], data)
    assert not draft["errors"] and draft["warnings"]
    assert review.validate_submission(package[0], data, final=True)["errors"]
    unchanged = review.decode_csv(data)
    assert unchanged[0]["relevance"] == "0" and unchanged[0]["coherence"] == "5"
    assert unchanged[0]["linguistic_resemblance"] == ""
    assert content(unchanged) == data


@pytest.mark.parametrize("value", ["6", "-1", "0.0", " 5", "UNCERTAIN", "True"])
def test_invalid_values_fail_without_rescaling(package, value):
    rows = rows_for(package)
    rows[0]["relevance"] = value
    assert review.validate_submission(package[0], content(rows))["errors"]


@pytest.mark.parametrize("change", ["remove", "duplicate", "reverse", "response", "dossier", "review_id"])
def test_fixed_cells_allocation_order_are_immutable(package, change):
    rows = rows_for(package)
    if change == "remove":
        rows.pop()
    elif change == "duplicate":
        rows[1] = rows[0].copy()
    elif change == "reverse":
        rows.reverse()
    else:
        rows[0][change] += " changed"
    assert review.validate_submission(package[0], content(rows))["errors"]


def test_package_binding_tamper_and_no_overwrite(package):
    _, (delivery, mapping, helper, receipt) = package
    with pytest.raises(ValueError):
        review.build_package(authored_records(), delivery, mapping, helper, receipt,
                             sealed_source_sha256="a" * 64, dossiers_redacted=True)
    original = receipt.read_bytes()
    altered = json.loads(original)
    altered["field_schema_sha256"] = "0" * 64
    receipt.write_bytes(review.legacy.json_bytes(altered))
    with pytest.raises(ValueError, match="bindings changed"):
        review.load_package(delivery, helper, receipt)
    receipt.write_bytes(original)
    (delivery / "records.html").write_text("authored tamper", encoding="utf-8")
    with pytest.raises(ValueError, match="Immutable delivery changed"):
        review.load_package(delivery, helper, receipt)


def test_invalid_count_case_and_dossier_fail_before_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(review.legacy, "PRIVATE_ROOT", tmp_path)
    paths = (tmp_path / "delivery", tmp_path / "mapping.json", tmp_path / "helper.json", tmp_path / "receipt.json")
    for records in (authored_records()[:-1], [{**row, "case_id": "one-case"} for row in authored_records()]):
        with pytest.raises(ValueError):
            review.build_package(records, *paths, sealed_source_sha256="a" * 64, dossiers_redacted=True)
    records = authored_records()
    records[0]["dossier"] = "Condition-specific leak"
    with pytest.raises(ValueError, match="identical dossier"):
        review.build_package(records, *paths, sealed_source_sha256="a" * 64, dossiers_redacted=True)
    assert not any(path.exists() for path in paths)
    assert review.legacy.RUBRIC != review.RUBRIC


def test_missing_and_empty_outcomes_formula_safety(tmp_path, monkeypatch):
    monkeypatch.setattr(review.legacy, "PRIVATE_ROOT", tmp_path)
    records = authored_records()
    records[0]["response"], records[1]["response"], records[2]["response"] = None, "", "=1+1"
    paths = (tmp_path / "delivery", tmp_path / "mapping.json", tmp_path / "helper.json", tmp_path / "receipt.json")
    review.build_package(records, *paths, sealed_source_sha256="a" * 64, dossiers_redacted=True)
    loaded = review.load_package(paths[0], paths[2], paths[3])
    package = loaded, paths
    rows = rows_for(package)
    missing = next(row for row in rows if row["outcome_status"] == "MISSING_OUTCOME")
    assert review.validate_submission(loaded, content(rows), final=True)["errors"]
    missing.update({name: "" for name in review.PRIMARY})
    missing.update(annotation_status="UNAVAILABLE", missing_reason="Authored absent generation")
    assert not review.validate_submission(loaded, content(rows), final=True)["errors"]
    assert any(row["response"] == "'=1+1" for row in rows)
    assert any(row["response"] == "=1+1" for row in loaded["rows"])


def test_known_prior_exposure_and_unknown_actual_provenance(package):
    data = content(rows_for(package))
    value = provenance_for(data)
    checked = review.validate_provenance(value, data)
    assert not checked["errors"] and checked["classification"] == "HUMAN_EXPOSURE_LIMITED"
    for key, wrong in (("prior_exposure_to_outputs", "NO"), ("prior_rubric_or_item_involvement", "NO"),
                       ("started_utc", None), ("ai_assistance_used_for_judgments", "YES")):
        assert review.validate_provenance({**value, key: wrong}, data)["errors"]
    assert review.validate_provenance(review.legacy.provenance_template(), data)["errors"]


def test_cli_incremental_copy_feedback_is_exclusive_and_no_mapping(package):
    _, (delivery, mapping, helper, receipt) = package
    mapping.unlink()
    working = delivery / "WORKING.csv"
    data = content(rows_for(package, unavailable=True))
    working.write_bytes(data)
    provenance = delivery / "completed-provenance.json"
    provenance.write_bytes(review.legacy.json_bytes(provenance_for(data)))
    args = ["--delivery", str(delivery), "--helper-receipt", str(helper), "--receipt", str(receipt),
            "--submission", str(working)]
    feedback = delivery.parent / "feedback.json"
    assert review.main(["validate-draft", *args, "--feedback", str(feedback)]) == 0
    with pytest.raises(FileExistsError):
        review.main(["validate-draft", *args, "--feedback", str(feedback)])
    assert working.read_bytes() == data
    final = delivery.parent / "final.json"
    assert review.main(["validate-final", *args, "--provenance", str(provenance), "--feedback", str(final)]) == 0
    checked = json.loads(final.read_text(encoding="utf-8"))
    assert checked["status"] == "READY_FOR_LOCK_NOT_LOCKED"
    assert checked["protected_mapping_opened"] is False and checked["official_lock_created"] is False
