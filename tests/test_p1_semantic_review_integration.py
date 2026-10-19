import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PACKAGE = load_module("p1_semantic_review_package_for_integration", Path("tools/p1_semantic_review_package.py"))
INTEGRATION = load_module("p1_semantic_review_integration", Path("tools/p1_semantic_review_integration.py"))


def build_completed_fixture(tmp_path):
    records = []
    for case in range(8):
        for arm in ("STAGE_B", "CANDIDATE_1"):
            response = f"Synthetic response {case} {arm}"
            records.append(
                {
                    "source_arm": arm,
                    "source_request_id": f"request-{case}",
                    "candidate_request_id": f"candidate-{case}" if arm == "CANDIDATE_1" else None,
                    "case_id": f"case-{case}",
                    "evaluation_material": f"USER:\nSynthetic evidence and question {case}",
                    "raw_response": response,
                    "raw_output_sha256": PACKAGE.sha256_text(response),
                }
            )
    package_dir = tmp_path / "package"
    receipt_path = tmp_path / "receipt.json"
    PACKAGE.write_package(records, package_dir, receipt_path, {"fixture": True})
    template_path = package_dir / "stage_a_pointwise_REVIEW_TEMPLATE.csv"
    with template_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for index, row in enumerate(rows):
        row.update(
            {
                "semantic_answer_state": "CURRENT_VALUE_ADOPTION" if index % 2 else "OUTDATED_VALUE_ADOPTION",
                "semantic_completeness": "COMPLETE",
                "answer_span": f"answer {index}",
                "reviewer_rationale": f"Synthetic rationale {index}",
                "reviewer_confidence": "HIGH",
                "reviewer_id": "synthetic-reviewer",
                "reviewed_utc": "",
            }
        )
    review_path = package_dir / "stage_a_pointwise_RESEARCHER_REVIEW.csv"
    with review_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INTEGRATION.REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    provenance_path = package_dir / "reviewer_provenance_RESEARCHER.json"
    provenance_path.write_text(
        json.dumps(
            {
                "reviewer_id": "synthetic-reviewer",
                "review_started_utc": None,
                "review_finished_utc": None,
                "model_and_run_labels_masked_during_initial_review": True,
                "automatic_or_ai_labels_seen_before_initial_review": False,
                "prior_exposure_to_these_outputs": False,
                "initial_review_file_sha256": INTEGRATION.sha256_file(review_path),
                "notes": "Synthetic test only",
            }
        ),
        encoding="utf-8",
    )
    return {
        "template": template_path,
        "review": review_path,
        "provenance": provenance_path,
        "mapping": package_dir / "mapping_DO_NOT_OPEN_BEFORE_REVIEW.json",
        "receipt": receipt_path,
    }


def integrate(paths):
    return INTEGRATION.validate_and_aggregate(
        paths["template"], paths["review"], paths["provenance"], paths["mapping"], paths["receipt"]
    )


def test_completed_review_is_validated_and_public_aggregate_omits_text(tmp_path):
    paths = build_completed_fixture(tmp_path)
    result = integrate(paths)
    assert result["completed_human_labels"] == 16
    assert result["reviewer_count"] == 1
    assert sum(value["responses"] for value in result["arm_summaries"].values()) == 16
    assert sum(result["paired_current_value_counts"].values()) == 8
    serialized = json.dumps(result)
    for private_text in ("Synthetic response", "Synthetic evidence", "Synthetic rationale"):
        assert private_text not in serialized
    assert result["source_hashes"]["integration_tool_sha256"] == INTEGRATION.sha256_file(
        Path("tools/p1_semantic_review_integration.py")
    )
    assert result["frozen_gate_changes"] is False


def test_changed_raw_response_or_provenance_is_rejected(tmp_path):
    paths = build_completed_fixture(tmp_path)
    with paths["review"].open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["raw_response"] += " changed"
    with paths["review"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INTEGRATION.REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="Immutable review content changed"):
        integrate(paths)
