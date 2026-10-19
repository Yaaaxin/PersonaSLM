import csv
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path("tools").resolve()))
import p1_semantic_interrater_analyze as analysis
import p1_semantic_interrater_prepare as preparation


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


def prepare_synthetic(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    rows = []
    mapping = []
    for index in range(16):
        anonymous = f"PRIVATE-ID-{index:03d}"
        material = f"PRIVATE-EVALUATION-TEXT-{index}"
        response = f"PRIVATE-RAW-RESPONSE-{index}"
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
                "source_request_id": f"PRIVATE-REQUEST-{index}",
                "candidate_request_id": f"PRIVATE-CANDIDATE-{index}",
                "case_id": f"PRIVATE-CASE-{index // 2}",
                "evaluation_material_sha256": preparation.sha256_text(material),
                "packaged_raw_response_sha256": preparation.sha256_text(response),
            }
        )
    write_csv(source / preparation.SOURCE_TEMPLATE, rows, SOURCE_FIELDS)
    (source / preparation.SOURCE_MAPPING).write_text(
        json.dumps({"rows": mapping}) + "\n", encoding="utf-8"
    )
    (source / preparation.SOURCE_INSTRUCTIONS).write_text("Synthetic instructions\n", encoding="utf-8")
    (source / preparation.SOURCE_PROVENANCE).write_text("{}\n", encoding="utf-8")
    files = {
        name: {
            "sha256": preparation.sha256_file(source / name),
            "bytes": (source / name).stat().st_size,
        }
        for name in (
            preparation.SOURCE_TEMPLATE,
            preparation.SOURCE_MAPPING,
            preparation.SOURCE_INSTRUCTIONS,
            preparation.SOURCE_PROVENANCE,
        )
    }
    source_receipt = tmp_path / "source_receipt.json"
    source_receipt.write_text(
        json.dumps(
            {
                "schema_version": "personaslm_blinded_semantic_review_package_v1",
                "responses": 16,
                "completed_human_labels": 0,
                "package_files": files,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    deliveries = tmp_path / "deliveries"
    plan = tmp_path / "plan.json"
    preparation.prepare(source, source_receipt, deliveries, plan, ignore_checker=lambda _: True)
    return deliveries, plan, rows


def completed_input(delivery, slot, pseudonym, degenerate=False):
    rows = preparation.read_csv(delivery / preparation.REVIEW_TEMPLATE, preparation.REVIEW_FIELDS)
    for row in rows:
        index = int(row["anonymous_response_id"].rsplit("-", 1)[1])
        unavailable = not degenerate and (
            index == 0 or (slot == "R1" and index == 1) or (slot == "R2" and index == 2)
        )
        if unavailable:
            row["annotation_status"] = "UNAVAILABLE"
            row["missing_reason"] = f"PRIVATE-MISSING-{slot}-{index}"
            continue
        row["annotation_status"] = "COMPLETED"
        if degenerate:
            state = "CURRENT_VALUE_ADOPTION"
            completeness = "COMPLETE"
        else:
            left = {
                3: "CURRENT_VALUE_ADOPTION",
                4: "CURRENT_VALUE_ADOPTION",
                5: "OUTDATED_VALUE_ADOPTION",
                6: "NO_REQUESTED_VALUE",
                7: "UNCERTAIN",
            }
            right = {
                3: "CURRENT_VALUE_ADOPTION",
                4: "OUTDATED_VALUE_ADOPTION",
                5: "OUTDATED_VALUE_ADOPTION",
                6: "NO_REQUESTED_VALUE",
                7: "CURRENT_VALUE_ADOPTION",
            }
            state = (left if slot == "R1" else right).get(index, "CURRENT_VALUE_ADOPTION")
            if index == 4:
                completeness = "COMPLETE" if slot == "R1" else "INCOMPLETE"
            elif index == 7:
                completeness = "UNCERTAIN"
            else:
                completeness = "COMPLETE"
        row["semantic_answer_state"] = state
        row["semantic_completeness"] = completeness
        if state in preparation.VALUE_BEARING_STATES:
            row["answer_span"] = (
                f"PRIVATE-DIFFERENT-SPAN-{slot}-{index}"
                if not degenerate and index == 4
                else f"PRIVATE-COMMON-SPAN-{index}"
            )
        row["reviewer_rationale"] = f"PRIVATE-RATIONALE-{slot}-{index}"
        row["reviewer_confidence"] = "HIGH"
    completed = delivery / f"completed_{slot}.csv"
    write_csv(completed, rows, preparation.REVIEW_FIELDS)

    provenance = preparation.read_json(delivery / preparation.PROVENANCE_TEMPLATE)
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
            "completed_review_file_sha256": preparation.sha256_file(completed),
        }
    )
    provenance_path = delivery / f"provenance_{slot}.json"
    provenance_path.write_text(json.dumps(provenance) + "\n", encoding="utf-8")
    return completed, provenance_path


def analysis_fixture(tmp_path, degenerate=False):
    deliveries, plan, source_rows = prepare_synthetic(tmp_path)
    records = {}
    for slot, pseudonym in (("R1", "PRIVATE-HUMAN-ALPHA"), ("R2", "PRIVATE-HUMAN-BETA")):
        delivery = deliveries / slot
        completed, provenance = completed_input(delivery, slot, pseudonym, degenerate)
        records[slot] = (delivery, completed, provenance)
    return plan, records, source_rows


def test_missingness_is_retained_and_fixed_matrices_cover_common_rows(tmp_path):
    plan, records, _ = analysis_fixture(tmp_path)
    result = analysis.analyze(plan, records)
    coverage = result["coverage"]
    assert coverage == {
        "unique_assigned_responses": 16,
        "assigned_annotations_per_reviewer": 16,
        "completed_annotations": {"R1": 14, "R2": 14},
        "unavailable_annotations": {"R1": 2, "R2": 2},
        "mutually_completed_responses": 13,
        "responses_with_any_unavailable_review": 3,
        "both_unavailable": 1,
        "r1_only_unavailable": 1,
        "r2_only_unavailable": 1,
    }
    answer = result["semantic_answer_state"]
    assert len(answer["counts"]) == 7 and all(len(row) == 7 for row in answer["counts"])
    assert sum(map(sum, answer["counts"])) == 13
    current = answer["label_order"].index("CURRENT_VALUE_ADOPTION")
    outdated = answer["label_order"].index("OUTDATED_VALUE_ADOPTION")
    assert answer["counts"][current][current] == 9
    assert answer["counts"][current][outdated] == 1
    assert answer["raw_exact_agreement"]["numerator"] == 11
    assert answer["raw_exact_agreement"]["denominator"] == 13
    assert result["semantic_completeness"]["raw_exact_agreement"]["numerator"] == 12
    assert result["answer_span_exact_agreement"]["numerator"] == 10
    assert result["answer_span_exact_agreement"]["denominator"] == 11


def test_degenerate_kappa_is_honestly_undefined(tmp_path):
    plan, records, _ = analysis_fixture(tmp_path, degenerate=True)
    result = analysis.analyze(plan, records)
    for metric in ("semantic_answer_state", "semantic_completeness"):
        kappa = result[metric]["nominal_cohen_kappa"]
        assert kappa["status"] == "UNDEFINED_DEGENERATE_EXPECTED_AGREEMENT_ONE"
        assert kappa["value"] is None
        assert kappa["observed_agreement"] == kappa["expected_agreement"] == 1.0
    assert result["interpretation"]["pass_fail_claim"] is False
    assert result["interpretation"]["acceptance_threshold"] is None
    empty = analysis.nominal_kappa(analysis.empty_matrix(preparation.ANSWER_STATES))
    assert empty["status"] == "UNDEFINED_NO_COMMON_COMPLETED"
    assert empty["value"] is None


def test_public_result_omits_text_ids_spans_rationales_and_reviewer_identity(tmp_path):
    plan, records, source_rows = analysis_fixture(tmp_path)
    result = analysis.analyze(plan, records)
    output = tmp_path / "aggregate.json"
    analysis.write_exclusive(output, result)
    serialized = output.read_text(encoding="utf-8")
    for row in source_rows:
        for field in ("anonymous_response_id", "evaluation_material", "raw_response"):
            assert row[field] not in serialized
    for forbidden in (
        "PRIVATE-RATIONALE",
        "PRIVATE-COMMON-SPAN",
        "PRIVATE-DIFFERENT-SPAN",
        "PRIVATE-MISSING",
        "PRIVATE-HUMAN-ALPHA",
        "PRIVATE-HUMAN-BETA",
    ):
        assert forbidden not in serialized
    with pytest.raises(FileExistsError):
        analysis.write_exclusive(output, result)


def test_changed_completed_text_is_rejected_even_when_its_file_hash_is_updated(tmp_path):
    plan, records, _ = analysis_fixture(tmp_path)
    delivery, completed, provenance_path = records["R1"]
    rows = preparation.read_csv(completed, preparation.REVIEW_FIELDS)
    rows[0]["raw_response"] += " PRIVATE-TAMPER"
    write_csv(completed, rows, preparation.REVIEW_FIELDS)
    provenance = preparation.read_json(provenance_path)
    provenance["completed_review_file_sha256"] = preparation.sha256_file(completed)
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(ValueError, match="Immutable review content changed"):
        analysis.analyze(plan, records)


def test_zero_result_readiness_is_hash_bound_and_exclusive(tmp_path):
    _, plan, _ = prepare_synthetic(tmp_path)
    receipt = analysis.readiness(plan)
    assert receipt["status"] == "READY_FOR_TWO_VALIDATED_HUMAN_INPUTS_ZERO_RESULTS"
    assert receipt["human_reviewers_recruited"] == 0
    assert receipt["completed_human_labels"] == 0
    assert receipt["agreement_results"] == 0
    assert receipt["analysis_contract"]["acceptance_threshold"] is None
    output = tmp_path / "readiness.json"
    analysis.write_exclusive(output, receipt)
    assert preparation.read_json(output) == receipt
    with pytest.raises(FileExistsError):
        analysis.write_exclusive(output, receipt)
