"""Only authored fixtures; never imports or opens participant content/maps."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import english_sfh_review_v1 as review


@pytest.fixture
def package(tmp_path, monkeypatch):
    monkeypatch.setattr(review, "PRIVATE_ROOT", tmp_path)
    delivery = tmp_path / "delivery"
    receipt = tmp_path / "analyst" / "receipt.json"
    mapping = tmp_path / "protected" / "mapping.json"
    records = [{"request_id": "fixture-request-" + str(i), "case_id": "opaque-fixture-case",
                "dossier": "Earlier authored example [E1]: I write software. Current context: Describe your work.",
                "response": "I write software."} for i in range(2)]
    result = review.build_package(records, delivery, mapping, receipt,
                                  sealed_source_sha256="a" * 64, dossiers_redacted=True)
    assert result["human_labels"] == 0
    return review.load_package(delivery, receipt), delivery, receipt, mapping, records


def completed_rows(package):
    loaded, delivery, *_ = package
    rows = review.decode_csv((delivery / "REVIEW.csv").read_bytes())
    for row in rows:
        row.update(annotation_status="COMPLETED", relevance="3", coherence="3",
                   linguistic_resemblance="NA", supported_claim_count="1", contradicted_claim_count="0",
                   unverifiable_claim_count="0", confidence="MEDIUM",
                   rationale="Authored fixture only. The source supports the claim; too little style evidence.",
                   claim_evidence_json=json.dumps({"claims": [{"status": "supported",
                       "response_span": "I write software.", "reference_span": "I write software.",
                       "rationale": "Exact authored self-report."}]}))
        for name in review.SECONDARY:
            row[name + "_applicability"] = "NOT_APPLICABLE"
            row[name + "_rating"] = "NA"
    return rows


def genuine_fixture_provenance(content):
    value = review.provenance_template()
    value.update({key: "NO" for key in review.EXPOSURES})
    value.update(human_reviewer=True, english_competence_attested=True,
                 reviewer_pseudonym="AUTHORED_FIXTURE_NOT_ACTUAL_REVIEWER",
                 english_competence_description="Authored test only", review_environment="Test fixture",
                 aids_used="None in this synthetic fixture", prior_rubric_or_item_involvement="YES",
                 started_utc="2026-01-01T00:00:00Z", completed_utc="2026-01-01T01:00:00Z",
                 completed_csv_sha256=review.prior.sha256_bytes(content))
    return value


def test_delivery_has_no_analyst_identifiers_and_blank_actual_attestations(package):
    loaded, delivery, receipt, mapping, records = package
    assert {p.name for p in delivery.iterdir()} == {"READ_ME.txt", "records.json", "records.html", "REVIEW.csv", "provenance.json"}
    visible = (delivery / "records.json").read_text(encoding="utf-8")
    assert "fixture-request" not in visible and "opaque-fixture-case" not in visible
    assert all(set(row) == set(review.IMMUTABLE) for row in loaded["rows"])
    provenance = json.loads((delivery / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["independent_of_project"] is False
    assert all(provenance[key] is None for key in review.EXPOSURES)
    assert provenance["human_reviewer"] is None
    # Intake must not read even this authored protected mapping.
    mapping.unlink()
    assert review.load_package(delivery, receipt)["rows"] == loaded["rows"]


def test_blank_draft_passes_but_final_rejects(package):
    loaded, delivery, *_ = package
    content = (delivery / "REVIEW.csv").read_bytes()
    draft = review.validate_submission(loaded, content)
    assert not draft["errors"] and draft["counts"]["not_started"] == 2
    assert review.validate_submission(loaded, content, final=True)["errors"]


@pytest.mark.parametrize("mutation", ["response", "dossier", "review_id", "missing", "duplicate"])
def test_fixed_cells_and_record_set_enforced(package, mutation):
    rows = completed_rows(package)
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[1] = rows[0].copy()
    else:
        rows[0][mutation] += " changed"
    assert review.validate_submission(package[0], review.encode_csv(rows, review.FIELDS))["errors"]


def test_exact_spans_counts_and_applicability(package):
    rows = completed_rows(package)
    content = review.encode_csv(rows, review.FIELDS)
    assert not review.validate_submission(package[0], content, final=True)["errors"]
    rows[0]["supported_claim_count"] = "2"
    assert review.validate_submission(package[0], review.encode_csv(rows, review.FIELDS))["errors"]
    rows[0]["supported_claim_count"] = "1"
    rows[0]["claim_evidence_json"] = rows[0]["claim_evidence_json"].replace("I write software.", "I grow trees.")
    assert review.validate_submission(package[0], review.encode_csv(rows, review.FIELDS))["errors"]
    rows = completed_rows(package)
    rows[0]["history_rating"] = "0"
    assert review.validate_submission(package[0], review.encode_csv(rows, review.FIELDS))["errors"]


def test_no_claim_is_not_perfect_accuracy_and_missing_is_not_zero(package):
    rows = completed_rows(package)
    rows[0].update(claim_evidence_json='{"claims": []}', supported_claim_count="0")
    rows[1].update({key: "" for key in review.JUDGMENTS})
    rows[1].update(annotation_status="UNAVAILABLE", missing_reason="Authored inaccessible-record fixture")
    report = review.validate_submission(package[0], review.encode_csv(rows, review.FIELDS), final=True)
    assert not report["errors"] and report["counts"]["unavailable"] == 1
    assert report["counts"]["completed"] == 1
    assert "accuracy" not in report


def test_true_provenance_and_exposure_classification(package):
    content = review.encode_csv(completed_rows(package), review.FIELDS)
    value = genuine_fixture_provenance(content)
    checked = review.validate_provenance(value, content)
    assert not checked["errors"] and checked["classification"] == "HUMAN_EXPOSURE_LIMITED"
    assert checked["inter_rater_reliability"] is False
    for key, bad in (("independent_of_project", True), ("prior_exposure_to_outputs", None),
                     ("ai_assistance_used_for_judgments", "YES"), ("completed_csv_sha256", "b" * 64)):
        changed = {**value, key: bad}
        assert review.validate_provenance(changed, content)["errors"]
    assert review.validate_provenance(review.provenance_template(), content)["errors"]


def test_builder_same_dossier_private_paths_and_no_overwrite(package, tmp_path):
    _, delivery, receipt, mapping, records = package
    with pytest.raises(ValueError):
        review.build_package(records, delivery, mapping, receipt, sealed_source_sha256="a" * 64, dossiers_redacted=True)
    different = [records[0], {**records[1], "dossier": "Different condition-specific evidence"}]
    with pytest.raises(ValueError, match="identical dossier"):
        review.build_package(different, tmp_path / "new", tmp_path / "map2.json", tmp_path / "receipt2.json",
                             sealed_source_sha256="a" * 64, dossiers_redacted=True)
    assert not (tmp_path / "new").exists()
    with pytest.raises(ValueError, match="ignored .local"):
        review.private_path(tmp_path.parent / "unsafe.json")


def test_cli_draft_feedback_and_final_requires_provenance(package):
    _, delivery, receipt, _, _ = package
    base = ["--delivery", str(delivery), "--receipt", str(receipt), "--submission", str(delivery / "REVIEW.csv")]
    feedback = delivery.parent / "draft-feedback.json"
    assert review.main(["validate-draft", *base, "--feedback", str(feedback)]) == 0
    with pytest.raises(FileExistsError):
        review.main(["validate-draft", *base, "--feedback", str(feedback)])
    final_feedback = delivery.parent / "final-feedback.json"
    assert review.main(["validate-final", *base, "--feedback", str(final_feedback)]) == 1
    doc = json.loads(final_feedback.read_text(encoding="utf-8"))
    assert any(item["code"] == "PROVENANCE_REQUIRED" for item in doc["errors"])


def test_delivery_tamper_fails_closed(package):
    _, delivery, receipt, _, _ = package
    (delivery / "READ_ME.txt").write_text("tampered authored fixture", encoding="utf-8")
    with pytest.raises(ValueError, match="Immutable delivery changed"):
        review.load_package(delivery, receipt)


def test_completed_cli_accepts_exposed_pi_not_independent(package):
    _, delivery, receipt, _, _ = package
    content = review.encode_csv(completed_rows(package), review.FIELDS)
    submission = delivery / "WORKING.csv"
    submission.write_bytes(content)
    provenance = delivery / "completed-provenance.json"
    provenance.write_bytes(review.json_bytes(genuine_fixture_provenance(content)))
    feedback = delivery.parent / "completed-feedback.json"
    assert review.main(["validate-final", "--delivery", str(delivery), "--receipt", str(receipt),
                        "--submission", str(submission), "--provenance", str(provenance),
                        "--feedback", str(feedback)]) == 0
    doc = json.loads(feedback.read_text(encoding="utf-8"))
    assert doc["status"] == "READY_FOR_LOCK_NOT_LOCKED"
    assert doc["provenance"]["classification"] == "HUMAN_EXPOSURE_LIMITED"
    assert doc["official_lock_created"] is False and doc["protected_mapping_opened"] is False


def test_html_escapes_and_missing_outcomes_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(review, "PRIVATE_ROOT", tmp_path)
    records = [{"request_id": "authored-1", "case_id": "case", "dossier": "<script>fixture</script>",
                "response": None},
               {"request_id": "authored-2", "case_id": "case", "dossier": "<script>fixture</script>",
                "response": ""}]
    delivery, receipt = tmp_path / "delivery", tmp_path / "receipt.json"
    review.build_package(records, delivery, tmp_path / "protected.json", receipt,
                         sealed_source_sha256="a" * 64, dossiers_redacted=True)
    rendered = (delivery / "records.html").read_text(encoding="utf-8")
    assert "<script>" not in rendered and "&lt;script&gt;" in rendered
    assert "default-src 'none'" in rendered and "https://" not in rendered
    package = review.load_package(delivery, receipt)
    assert {row["outcome_status"] for row in package["rows"]} == {"GENERATED", "MISSING_OUTCOME"}
    rows = review.decode_csv((delivery / "REVIEW.csv").read_bytes())
    missing = next(row for row in rows if row["outcome_status"] == "MISSING_OUTCOME")
    missing["annotation_status"] = "COMPLETED"
    errors = review.validate_submission(package, review.encode_csv(rows, review.FIELDS))["errors"]
    assert any("never rated as zero" in error["message"] for error in errors)


def test_csv_formula_safety_does_not_change_raw_response(tmp_path, monkeypatch):
    monkeypatch.setattr(review, "PRIVATE_ROOT", tmp_path)
    records = [{"request_id": "authored-1", "case_id": "case", "dossier": "Authored context.",
                "response": "  =SUM(1,2)"}]
    delivery, receipt = tmp_path / "delivery", tmp_path / "receipt.json"
    review.build_package(records, delivery, tmp_path / "map.json", receipt,
                         sealed_source_sha256="a" * 64, dossiers_redacted=True)
    package = review.load_package(delivery, receipt)
    content = (delivery / "REVIEW.csv").read_bytes()
    assert review.decode_csv(content)[0]["response"] == "'  =SUM(1,2)"
    assert package["rows"][0]["response"] == "  =SUM(1,2)"
    assert not review.validate_submission(package, content)["errors"]
