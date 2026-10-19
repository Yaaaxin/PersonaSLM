import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest


PATH = Path("tools/p1_semantic_interrater_prepare.py")
SPEC = importlib.util.spec_from_file_location("p1_semantic_interrater_prepare", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


SOURCE_FIELDS = (
    "anonymous_response_id",
    "evaluation_material",
    "raw_response",
    "semantic_answer_state",
    "semantic_completeness",
    "answer_span",
    "reviewer_rationale",
    "reviewer_confidence",
    "reviewer_id",
    "reviewed_utc",
)


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def source_fixture(tmp_path):
    package = tmp_path / "source"
    package.mkdir()
    rows = []
    mapping = []
    for index in range(16):
        anonymous = f"SYN-{index:03d}"
        material = f"Synthetic evaluation material {index}"
        response = f"Synthetic raw response {index}"
        rows.append(
            {
                "anonymous_response_id": anonymous,
                "evaluation_material": material,
                "raw_response": response,
                **{field: "" for field in SOURCE_FIELDS[3:]},
            }
        )
        mapping.append(
            {
                "anonymous_response_id": anonymous,
                "source_arm": "SYNTHETIC_ARM",
                "source_request_id": f"protected-request-{index}",
                "candidate_request_id": f"protected-candidate-{index}",
                "case_id": f"protected-case-{index // 2}",
                "raw_output_sha256": MODULE.sha256_text(response),
                "evaluation_material_sha256": MODULE.sha256_text(material),
                "packaged_raw_response_sha256": MODULE.sha256_text(response),
            }
        )
    write_csv(package / MODULE.SOURCE_TEMPLATE, rows, SOURCE_FIELDS)
    (package / MODULE.SOURCE_MAPPING).write_text(
        json.dumps({"schema_version": "synthetic_mapping", "rows": mapping}, indent=2) + "\n",
        encoding="utf-8",
    )
    (package / MODULE.SOURCE_INSTRUCTIONS).write_text("Synthetic source instructions\n", encoding="utf-8")
    (package / MODULE.SOURCE_PROVENANCE).write_text("{}\n", encoding="utf-8")
    package_files = {
        name: {
            "sha256": MODULE.sha256_file(package / name),
            "bytes": (package / name).stat().st_size,
        }
        for name in (
            MODULE.SOURCE_TEMPLATE,
            MODULE.SOURCE_MAPPING,
            MODULE.SOURCE_INSTRUCTIONS,
            MODULE.SOURCE_PROVENANCE,
        )
    }
    receipt = tmp_path / "source_receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema_version": "personaslm_blinded_semantic_review_package_v1",
                "responses": 16,
                "completed_human_labels": 0,
                "package_files": package_files,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return package, receipt, rows


def prepare_fixture(tmp_path):
    package, source_receipt, source_rows = source_fixture(tmp_path)
    output = tmp_path / "private_delivery"
    public = tmp_path / "public_receipt.json"
    plan = MODULE.prepare(package, source_receipt, output, public, ignore_checker=lambda _: True)
    return package, source_receipt, source_rows, output, public, plan


def test_two_zero_label_deliveries_are_distinct_but_share_ids(tmp_path):
    _, _, source_rows, output, public, plan = prepare_fixture(tmp_path)
    orders = {}
    for slot in MODULE.SLOTS:
        delivery = output / slot
        rows = MODULE.read_csv(delivery / MODULE.REVIEW_TEMPLATE, MODULE.REVIEW_FIELDS)
        orders[slot] = [row["anonymous_response_id"] for row in rows]
        assert set(orders[slot]) == {row["anonymous_response_id"] for row in source_rows}
        assert all(row["reviewer_slot_id"] == slot for row in rows)
        assert all(
            not row[field]
            for row in rows
            for field in MODULE.REVIEW_FIELDS[3:10]
        )
        assert not (delivery / MODULE.SOURCE_MAPPING).exists()
        manifest = MODULE.read_json(delivery / MODULE.DELIVERY_MANIFEST)
        assert manifest["human_labels"] == 0
        assert manifest["protected_mapping_included"] is False
        for name, record in plan["reviewer_slots"][slot]["delivery_files"].items():
            assert record["sha256"] == MODULE.sha256_file(delivery / name)
    assert orders["R1"] != orders["R2"]
    assert plan["human_reviewers_recruited"] == plan["completed_human_labels"] == 0
    assert plan["status"] == "READY_FOR_RECRUITMENT_ZERO_LABELS"
    assert MODULE.read_json(public) == plan


def test_public_receipt_contains_no_review_or_mapping_payload(tmp_path):
    _, _, source_rows, _, public, _ = prepare_fixture(tmp_path)
    text = public.read_text(encoding="utf-8")
    for row in source_rows:
        assert row["anonymous_response_id"] not in text
        assert row["evaluation_material"] not in text
        assert row["raw_response"] not in text
    for index in range(16):
        assert f"protected-request-{index}" not in text
        assert f"protected-case-{index // 2}" not in text
    assert '"rows"' not in text


def test_unignored_target_and_existing_outputs_fail_closed(tmp_path):
    package, source_receipt, _ = source_fixture(tmp_path)
    output = tmp_path / "private_delivery"
    public = tmp_path / "public_receipt.json"
    with pytest.raises(PermissionError, match="not verified Git-ignored"):
        MODULE.prepare(package, source_receipt, output, public, ignore_checker=lambda _: False)
    assert not output.exists() and not public.exists()
    MODULE.prepare(package, source_receipt, output, public, ignore_checker=lambda _: True)
    source_hash = MODULE.sha256_file(package / MODULE.SOURCE_TEMPLATE)
    with pytest.raises(FileExistsError, match="never overwrite"):
        MODULE.prepare(package, source_receipt, output, public, ignore_checker=lambda _: True)
    assert MODULE.sha256_file(package / MODULE.SOURCE_TEMPLATE) == source_hash


def test_changed_source_is_rejected_before_any_output(tmp_path):
    package, source_receipt, _ = source_fixture(tmp_path)
    path = package / MODULE.SOURCE_TEMPLATE
    path.write_text(path.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
    output = tmp_path / "private_delivery"
    public = tmp_path / "public_receipt.json"
    with pytest.raises(ValueError, match="Source-package hash mismatch"):
        MODULE.prepare(package, source_receipt, output, public, ignore_checker=lambda _: True)
    assert not output.exists() and not public.exists()


def completed_review(delivery, slot, pseudonym):
    rows = MODULE.read_csv(delivery / MODULE.REVIEW_TEMPLATE, MODULE.REVIEW_FIELDS)
    for index, row in enumerate(rows):
        if index == 0:
            row["annotation_status"] = "UNAVAILABLE"
            row["missing_reason"] = "Synthetic unavailable review"
        else:
            row["annotation_status"] = "COMPLETED"
            row["semantic_answer_state"] = "UNCERTAIN" if index == 1 else "CURRENT_VALUE_ADOPTION"
            row["semantic_completeness"] = "UNCERTAIN" if index == 1 else "COMPLETE"
            row["answer_span"] = "" if index == 1 else "Synthetic value"
            row["reviewer_rationale"] = "Synthetic test rationale"
            row["reviewer_confidence"] = "LOW" if index == 1 else "HIGH"
    completed = delivery / f"completed_{slot}.csv"
    write_csv(completed, rows, MODULE.REVIEW_FIELDS)
    provenance = MODULE.read_json(delivery / MODULE.PROVENANCE_TEMPLATE)
    provenance.update(
        {
            "reviewer_pseudonym": pseudonym,
            "human_reviewer": True,
            "independent_of_project": True,
            "reviewer_role_or_relationship": "INDEPENDENT_EXTERNAL",
            "prior_involvement_in_item_or_rubric_creation": False,
            "prior_exposure_to_these_outputs": False,
            "condition_mapping_seen_before_initial_lock": False,
            "automatic_or_ai_labels_seen_before_initial_lock": False,
            "other_reviewer_labels_seen_before_initial_lock": False,
            "adjudication_material_seen_before_initial_lock": False,
            "ai_assistance_used": False,
            "completed_review_file_sha256": MODULE.sha256_file(completed),
        }
    )
    provenance_path = delivery / f"provenance_{slot}.json"
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return completed, provenance_path


def test_completed_pair_validation_preserves_missing_vs_uncertainty(tmp_path):
    _, _, _, output, _, _ = prepare_fixture(tmp_path)
    records = {}
    for slot, pseudonym in (("R1", "human-alpha"), ("R2", "human-beta")):
        delivery = output / slot
        completed, provenance = completed_review(delivery, slot, pseudonym)
        records[slot] = (delivery, completed, provenance)
    result = MODULE.validate_completed_pair(records)
    assert result["R1"]["completed"] == result["R2"]["completed"] == 15
    assert result["R1"]["unavailable"] == result["R2"]["unavailable"] == 1
    assert result["R1"]["semantic_uncertain"] == result["R2"]["semantic_uncertain"] == 1

    provenance = MODULE.read_json(records["R2"][2])
    provenance["reviewer_pseudonym"] = "human-alpha"
    records["R2"][2].write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(ValueError, match="Two distinct human"):
        MODULE.validate_completed_pair(records)


def test_completed_review_rejects_labels_on_unavailable_and_changed_text(tmp_path):
    _, _, _, output, _, _ = prepare_fixture(tmp_path)
    delivery = output / "R1"
    completed, provenance = completed_review(delivery, "R1", "human-alpha")
    rows = MODULE.read_csv(completed, MODULE.REVIEW_FIELDS)
    rows[0]["semantic_answer_state"] = "UNCERTAIN"
    write_csv(completed, rows, MODULE.REVIEW_FIELDS)
    value = MODULE.read_json(provenance)
    value["completed_review_file_sha256"] = MODULE.sha256_file(completed)
    provenance.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="Unavailable review contains semantic labels"):
        MODULE.validate_completed_delivery(delivery, completed, provenance, "R1")

    rows[0]["semantic_answer_state"] = ""
    rows[0]["raw_response"] += " changed"
    write_csv(completed, rows, MODULE.REVIEW_FIELDS)
    value["completed_review_file_sha256"] = MODULE.sha256_file(completed)
    provenance.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="Immutable review content changed"):
        MODULE.validate_completed_delivery(delivery, completed, provenance, "R1")
