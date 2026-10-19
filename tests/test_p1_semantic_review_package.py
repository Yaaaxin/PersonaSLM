import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest


PATH = Path("tools/p1_semantic_review_package.py")
SPEC = importlib.util.spec_from_file_location("p1_semantic_review_package", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def fixture_records():
    return [
        {
            "source_arm": arm,
            "source_request_id": f"request-{index}",
            "case_id": f"case-{index % 2}",
            "evaluation_material": f"USER:\nEvidence and question {index}",
            "raw_response": f"Response {index}",
            "raw_output_sha256": MODULE.sha256_text(f"Response {index}"),
        }
        for index, arm in enumerate(("STAGE_B", "CANDIDATE_1", "STAGE_B", "CANDIDATE_1"))
    ]


def test_review_form_is_pointwise_blinded_and_unlabeled(tmp_path):
    output = tmp_path / "package"
    receipt_path = tmp_path / "receipt.json"
    receipt = MODULE.write_package(fixture_records(), output, receipt_path, {"fixture": True})
    with (output / "stage_a_pointwise_REVIEW_TEMPLATE.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert tuple(rows[0]) == MODULE.REVIEW_FIELDS
    assert all(not row["semantic_answer_state"] and not row["reviewer_rationale"] for row in rows)
    serialized = json.dumps(rows)
    for forbidden in ("STAGE_B", "CANDIDATE_1", "case_id", "request_id", "automatic"):
        assert forbidden not in serialized
    assert receipt["completed_human_labels"] == 0
    assert receipt["blinding"]["pointwise_not_pairwise"] is True


def test_mapping_is_separate_and_existing_evidence_is_never_overwritten(tmp_path):
    output = tmp_path / "package"
    receipt_path = tmp_path / "receipt.json"
    MODULE.write_package(fixture_records(), output, receipt_path, {"fixture": True})
    mapping = json.loads((output / "mapping_DO_NOT_OPEN_BEFORE_REVIEW.json").read_text(encoding="utf-8"))
    assert {row["source_arm"] for row in mapping["rows"]} == {"STAGE_B", "CANDIDATE_1"}
    with pytest.raises(FileExistsError):
        MODULE.write_package(fixture_records(), output, receipt_path, {"fixture": True})
