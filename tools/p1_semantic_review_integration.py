"""Validate and aggregate a completed blinded semantic-review package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


IMMUTABLE_FIELDS = ("anonymous_response_id", "evaluation_material", "raw_response")
REVIEW_FIELDS = IMMUTABLE_FIELDS + (
    "semantic_answer_state",
    "semantic_completeness",
    "answer_span",
    "reviewer_rationale",
    "reviewer_confidence",
    "reviewer_id",
    "reviewed_utc",
)
ANSWER_STATES = {
    "CURRENT_VALUE_ADOPTION",
    "OUTDATED_VALUE_ADOPTION",
    "OTHER_SUPPORTED_VALUE",
    "UNSUPPORTED_VALUE",
    "MULTIPLE_OR_CONTRADICTORY_VALUES",
    "NO_REQUESTED_VALUE",
    "UNCERTAIN",
}
COMPLETENESS = {"COMPLETE", "INCOMPLETE", "UNCERTAIN"}
CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def read_review_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REVIEW_FIELDS:
            raise ValueError(f"Unexpected review columns in {path}")
        return list(reader)


def parse_optional_utc(value: str | None, field: str) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"Invalid {field}: expected an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError(f"Invalid {field}: timezone is required")
    return parsed


def validate_provenance(path: Path, review_path: Path, reviewer_ids: set[str]) -> dict:
    value = read_json(path)
    if len(reviewer_ids) != 1 or value.get("reviewer_id") not in reviewer_ids:
        raise ValueError("Reviewer ID must be present and consistent across review and provenance")
    if value.get("model_and_run_labels_masked_during_initial_review") is not True:
        raise ValueError("Provenance must confirm model/run masking during initial review")
    if value.get("automatic_or_ai_labels_seen_before_initial_review") is not False:
        raise ValueError("Initial review must precede access to automatic or AI labels")
    if not isinstance(value.get("prior_exposure_to_these_outputs"), bool):
        raise ValueError("Prior output exposure must be recorded honestly as true or false")
    if value.get("initial_review_file_sha256") != sha256_file(review_path):
        raise ValueError("Provenance review-file hash mismatch")
    started = parse_optional_utc(value.get("review_started_utc"), "review_started_utc")
    finished = parse_optional_utc(value.get("review_finished_utc"), "review_finished_utc")
    if (started is None) != (finished is None):
        raise ValueError("Review start and finish timestamps must both be present or both be absent")
    if started is not None and finished < started:
        raise ValueError("Review finish precedes review start")
    return value


def validate_and_aggregate(
    template_path: Path,
    review_path: Path,
    provenance_path: Path,
    mapping_path: Path,
    package_receipt_path: Path,
) -> dict:
    receipt = read_json(package_receipt_path)
    template = read_review_csv(template_path)
    review = read_review_csv(review_path)
    if len(template) != 16 or len(review) != 16:
        raise ValueError("Expected exactly 16 template and completed-review rows")
    if receipt.get("responses") != 16 or receipt.get("completed_human_labels") != 0:
        raise ValueError("Package receipt is not the expected blank 16-response instrument")
    package_files = receipt["package_files"]
    if sha256_file(template_path) != package_files[template_path.name]["sha256"]:
        raise ValueError("Review template does not match the package receipt")
    if sha256_file(mapping_path) != package_files[mapping_path.name]["sha256"]:
        raise ValueError("Reviewer mapping does not match the package receipt")

    template_by_id = {row["anonymous_response_id"]: row for row in template}
    if len(template_by_id) != 16:
        raise ValueError("Template anonymous IDs are not unique")
    reviewer_ids = set()
    review_by_id = {}
    for row in review:
        anonymous = row["anonymous_response_id"]
        if anonymous in review_by_id or anonymous not in template_by_id:
            raise ValueError("Completed review has duplicate or unknown anonymous IDs")
        for field in IMMUTABLE_FIELDS:
            if row[field] != template_by_id[anonymous][field]:
                raise ValueError(f"Immutable review content changed for {anonymous}: {field}")
        if row["semantic_answer_state"] not in ANSWER_STATES:
            raise ValueError(f"Invalid semantic answer state for {anonymous}")
        if row["semantic_completeness"] not in COMPLETENESS:
            raise ValueError(f"Invalid semantic completeness for {anonymous}")
        if row["reviewer_confidence"] not in CONFIDENCE:
            raise ValueError(f"Invalid reviewer confidence for {anonymous}")
        if not row["reviewer_rationale"].strip() or not row["reviewer_id"].strip():
            raise ValueError(f"Missing rationale or reviewer ID for {anonymous}")
        parse_optional_utc(row["reviewed_utc"], f"reviewed_utc for {anonymous}")
        reviewer_ids.add(row["reviewer_id"])
        review_by_id[anonymous] = row
    if set(review_by_id) != set(template_by_id):
        raise ValueError("Completed review does not cover every anonymous ID")

    provenance = validate_provenance(provenance_path, review_path, reviewer_ids)
    mapping_value = read_json(mapping_path)
    mapping_by_id = {row["anonymous_response_id"]: row for row in mapping_value["rows"]}
    if len(mapping_by_id) != 16 or set(mapping_by_id) != set(review_by_id):
        raise ValueError("Mapping is not a complete one-to-one match for the review")

    public_rows = []
    for anonymous, row in review_by_id.items():
        mapping = mapping_by_id[anonymous]
        if sha256_text(row["evaluation_material"]) != mapping["evaluation_material_sha256"]:
            raise ValueError(f"Evaluation-material hash mismatch for {anonymous}")
        raw_hash = sha256_text(row["raw_response"])
        if raw_hash != mapping["packaged_raw_response_sha256"] or raw_hash != mapping["raw_output_sha256"]:
            raise ValueError(f"Raw-response hash mismatch for {anonymous}")
        public_rows.append(
            {
                "anonymous_response_id": anonymous,
                "source_arm": mapping["source_arm"],
                "source_request_id": mapping["source_request_id"],
                "case_id": mapping["case_id"],
                "semantic_answer_state": row["semantic_answer_state"],
                "semantic_completeness": row["semantic_completeness"],
                "answer_span_sha256": sha256_text(row["answer_span"]),
                "reviewer_rationale_sha256": sha256_text(row["reviewer_rationale"]),
                "reviewer_confidence": row["reviewer_confidence"],
            }
        )

    arms = {row["source_arm"] for row in public_rows}
    if arms != {"STAGE_B", "CANDIDATE_1"}:
        raise ValueError("Unexpected source arms in mapping")
    by_case = {}
    for row in public_rows:
        by_case.setdefault(row["case_id"], {})[row["source_arm"]] = row
    if len(by_case) != 8 or any(set(pair) != arms for pair in by_case.values()):
        raise ValueError("Expected eight complete Stage B/Candidate 1 case pairs")

    arm_summaries = {}
    for arm in sorted(arms):
        selected = [row for row in public_rows if row["source_arm"] == arm]
        arm_summaries[arm] = {
            "responses": len(selected),
            "semantic_answer_state_counts": dict(sorted(Counter(row["semantic_answer_state"] for row in selected).items())),
            "semantic_completeness_counts": dict(sorted(Counter(row["semantic_completeness"] for row in selected).items())),
        }
    discordance = Counter()
    for pair in by_case.values():
        stage_current = pair["STAGE_B"]["semantic_answer_state"] == "CURRENT_VALUE_ADOPTION"
        candidate_current = pair["CANDIDATE_1"]["semantic_answer_state"] == "CURRENT_VALUE_ADOPTION"
        key = {
            (True, True): "both_current",
            (True, False): "stage_b_only_current",
            (False, True): "candidate_1_only_current",
            (False, False): "neither_current",
        }[(stage_current, candidate_current)]
        discordance[key] += 1

    return {
        "schema_version": "personaslm_human_semantic_review_integration_v1",
        "status": "HUMAN_SEMANTIC_REVIEW_INTEGRATED",
        "completed_human_labels": len(public_rows),
        "reviewer_count": 1,
        "reviewer_id_sha256": sha256_text(next(iter(reviewer_ids))),
        "provenance": {
            "model_and_run_labels_masked_during_initial_review": True,
            "automatic_or_ai_labels_seen_before_initial_review": False,
            "prior_exposure_to_these_outputs": provenance["prior_exposure_to_these_outputs"],
            "review_timestamps_recorded": provenance.get("review_started_utc") is not None,
        },
        "arm_summaries": arm_summaries,
        "paired_current_value_counts": {key: discordance.get(key, 0) for key in (
            "both_current", "stage_b_only_current", "candidate_1_only_current", "neither_current"
        )},
        "rows": sorted(public_rows, key=lambda row: row["anonymous_response_id"]),
        "source_hashes": {
            "package_receipt_sha256": sha256_file(package_receipt_path),
            "blank_template_sha256": sha256_file(template_path),
            "completed_review_sha256": sha256_file(review_path),
            "reviewer_provenance_sha256": sha256_file(provenance_path),
            "mapping_sha256": sha256_file(mapping_path),
            "integration_tool_sha256": sha256_file(Path(__file__)),
        },
        "interpretation_limits": [
            "This is a single-researcher semantic review, not independent inter-rater validation.",
            "The paired development cases are not an independent confirmatory cohort.",
            "These semantic results do not change either frozen 7/8 execution gate.",
        ],
        "frozen_gate_changes": False,
        "execution_impact": {"scientific_model_generations": 0, "inference_seconds": 0.0},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--package-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Integrated review evidence already exists; never overwrite it")
    result = validate_and_aggregate(
        args.template, args.review, args.provenance, args.mapping, args.package_receipt
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "human_labels": result["completed_human_labels"]}))


if __name__ == "__main__":
    main()
