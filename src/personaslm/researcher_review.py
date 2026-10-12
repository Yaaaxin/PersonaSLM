"""Researcher-attested review import, separate from the immutable v3 importer.

This version accepts unknown review times explicitly. Registration time never
substitutes for a missing human review time. Authenticity comes from the
researcher's attestation, not from software or a CSV filename.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime
import json
from pathlib import Path

from .journal import atomic_json, utc_now
from .neutral_review import EDITABLE, RATINGS, VERSION as FORM_VERSION
from .provenance import fingerprint, require_local_path, sha256

VERSION = "researcher_verified_annotation_v1"
EXTRA = ("reference_conditioning_text", "control_suitability",
         "speaker_referent_ambiguity", "assessment_source", "reference_repo_commit")
RESEARCHER_PROVENANCE_FIELDS = ("previous_reviewer_id", "review_type", "independent_blind_review",
    "original_file_sha256", "initial_annotation_independent", "posthoc_reference_comparison",
    "prior_review_type", "prior_assessment_source", "source_review_file_sha256")
JUDGMENTS = (*RATINGS, "control_suitability", "speaker_referent_ambiguity")


def canonical(value):
    return str(value).replace("\r\n", "\n")


def read_submission(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        if not fields or len(fields) != len(set(fields)):
            raise ValueError("Missing or duplicate CSV columns")
        rows = list(reader)
    if any(set(r) != set(fields) or any(v is None for v in r.values()) for r in rows):
        raise ValueError("Malformed CSV row")
    return fields, rows


def normalize_rating(field, value):
    if value not in {"yes", "no", "uncertain"}:
        raise ValueError(f"Missing or invalid judgment: {field}")
    if value == "uncertain":
        return "UNCERTAIN"
    favorable = "yes" if field == "semantic_neutrality" else "no"
    return "PASS" if value == favorable else "FAIL"


def validate_submission(template, rows, fields, references):
    if template.get("form_version") != FORM_VERSION or fingerprint(
            {k: v for k, v in template.items() if k != "packet_id"}) != template.get("packet_id"):
        raise ValueError("Invalid template version/digest")
    expected = {(r["case_id"], r["condition_id"]): r for r in template["items"]}
    if len(expected) != len(template["items"]):
        raise ValueError("Duplicate template records")
    base_fields = set(template["items"][0]) | set(EXTRA)
    if set(fields) not in (base_fields, base_fields | set(RESEARCHER_PROVENANCE_FIELDS)):
        raise ValueError("Submission schema differs from the versioned source schema")
    seen, validated = set(), []
    for row in rows:
        key = row["case_id"], row["condition_id"]
        if key not in expected or key in seen:
            raise ValueError("Unknown or duplicate review record")
        seen.add(key)
        master = expected[key]
        if any(canonical(row[k]) != canonical(v) for k, v in master.items() if k not in EDITABLE):
            raise ValueError("Changed immutable material/version")
        if canonical(row["reference_conditioning_text"]) != canonical(references[key]):
            raise ValueError("Changed comparison material")
        ratings = {field: normalize_rating(field, row[field]) for field in RATINGS}
        if row["control_suitability"] not in {"PASS", "PARTIAL", "FAILED"}:
            raise ValueError("Missing or invalid suitability")
        normalize_rating("speaker_referent_ambiguity", row["speaker_referent_ambiguity"])
        if row["reviewed_utc"]:
            when = datetime.fromisoformat(row["reviewed_utc"])
            if when.tzinfo is None or when.utcoffset().total_seconds() != 0:
                raise ValueError("Supplied review time must explicitly use UTC")
        if "review_type" in row:
            if (not row["reviewer_id"].strip() or row["review_type"] != "human_manual_researcher_review"
                    or row["independent_blind_review"] != "no"):
                raise ValueError("Invalid researcher provenance fields")
            for name in ("original_file_sha256", "source_review_file_sha256"):
                if len(row[name]) != 64 or any(c not in "0123456789abcdef" for c in row[name]):
                    raise ValueError("Invalid source digest in researcher provenance")
        # No overwritten reviewer verdict: this separate, conservative software
        # disposition routes any failed dimension to repair and any uncertainty
        # to unresolved review. It is not a new human judgment.
        disposition = ("FAILED" if "FAIL" in ratings.values() else
                       "PARTIAL" if "UNCERTAIN" in ratings.values() else "PASS")
        validated.append({"case_id": key[0], "condition_id": key[1],
            "source_judgments": {k: row[k] for k in JUDGMENTS}, "normalized_dimensions": ratings,
            "researcher_control_suitability": row["control_suitability"],
            "derived_dimension_disposition": disposition, "reviewer_notes": row["reviewer_notes"],
            "material_sha256": master["material_sha256"], "reviewed_utc": row["reviewed_utc"] or None})
    if seen != set(expected):
        raise ValueError("Missing review records")
    return validated


def compare_versions(preliminary_rows, reviewed_rows):
    if preliminary_rows is None:
        return {"status": "UNAVAILABLE", "changed_judgments": None, "changed_records": None,
                "reason": "No original preliminary CSV available; do not reconstruct judgments from memory or a blank form.",
                "changes": []}
    def index(rows):
        keys = [(r["case_id"], r["condition_id"]) for r in rows]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate comparison records")
        return dict(zip(keys, rows))
    before, after = index(preliminary_rows), index(reviewed_rows)
    if set(before) != set(after):
        raise ValueError("Comparison versions have different record sets")
    changes = []
    for key in sorted(before):
        for field in JUDGMENTS:
            if before[key][field] != after[key][field]:
                changes.append({"case_id": key[0], "condition_id": key[1], "field": field,
                    "before": before[key][field], "after": after[key][field]})
    return {"status": "COMPARED", "changed_judgments": len(changes),
            "changed_records": len({(r["case_id"], r["condition_id"]) for r in changes}),
            "changes": changes, "scope": list(JUDGMENTS),
            "note": "Metadata changes and review attribution are not judgment changes."}


def import_attested_review(template_path, input_path, frozen_path, attestation_path, output_path, preliminary_path=None):
    template_path, input_path, frozen_path, attestation_path, output_path = map(require_local_path,
        (template_path, input_path, frozen_path, attestation_path, output_path))
    if output_path.exists():
        raise FileExistsError("Registered annotations are immutable; use a new version")
    template = json.loads(template_path.read_text(encoding="utf-8"))
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    if template["source_freeze_sha256"] != sha256(frozen_path):
        raise ValueError("Frozen source digest mismatch")
    attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
    if (attestation.get("version") != VERSION or not str(attestation.get("reviewer_id", "")).strip()
            or attestation.get("review_type") != "researcher_human_review"
            or attestation.get("confirmed_all_records_reviewed") is not True
            or attestation.get("assistance") != "AI-assisted human review"
            or attestation.get("blind_review") is not False
            or attestation.get("submission_sha256") != sha256(input_path)):
        raise ValueError("Missing, inconsistent or unbound researcher attestation")
    references = {(r["case_id"], r["neutral_condition"]):
        frozen["prompts"][r["case_id"]][r["reference_condition"]]["prompt"]["additions"][0]
        for r in frozen["rows"]}
    fields, rows = read_submission(input_path)
    validated = validate_submission(template, rows, fields, references)
    if "review_type" in fields and any(r["reviewer_id"] != attestation["reviewer_id"] for r in rows):
        raise ValueError("Row reviewer disagrees with researcher attestation")
    preliminary = None
    if preliminary_path is not None:
        preliminary_path = require_local_path(preliminary_path)
        old_fields, preliminary = read_submission(preliminary_path)
        validate_submission(template, preliminary, old_fields, references)
        if "original_file_sha256" in fields and any(r["original_file_sha256"] != sha256(preliminary_path) for r in rows):
            raise ValueError("Supplied preceding version does not match declared original digest")
    result = {"annotation_version": VERSION, "registered_utc": utc_now(),
        "reviewer_id": attestation["reviewer_id"], "review_type": attestation["review_type"],
        "assistance": attestation["assistance"], "blind_review": False, "reviewed_utc": None,
        "review_time_note": "Human review time was not supplied. Registration time is not review time.",
        "annotation_count": len(validated), "core_judgment_count": len(validated) * len(RATINGS),
        "review_completion_status": "COMPLETE", "independent_second_reviewer": None,
        "inter_annotator_agreement": None, "authenticity_basis": "Explicit researcher confirmation in the task; not inferred from stale CSV metadata.",
        "source_submission_sha256": sha256(input_path), "source_submission_utf8": input_path.read_bytes().decode("utf-8-sig"),
        "template_sha256": sha256(template_path), "frozen_source_sha256": sha256(frozen_path),
        "attestation_sha256": sha256(attestation_path), "attestation": attestation,
        "preliminary_sha256": sha256(preliminary_path) if preliminary_path else None,
        "preliminary_submission_utf8": preliminary_path.read_bytes().decode("utf-8-sig") if preliminary_path else None,
        "version_comparison": compare_versions(preliminary, rows),
        "researcher_control_counts": dict(Counter(r["researcher_control_suitability"] for r in validated)),
        "derived_dimension_counts": dict(Counter(r["derived_dimension_disposition"] for r in validated)),
        "derived_policy": "control_dimension_disposition_v1: any normalized FAIL -> FAILED; else any UNCERTAIN -> PARTIAL; else PASS. Separate from researcher overall judgment.",
        "raw_metadata_counts": {k: dict(Counter(r[k] for r in rows)) for k in ("reviewer_id", "reviewed_utc", "assessment_source")},
        "researcher_provenance_claims": {k: dict(Counter(r[k] for r in rows)) for k in RESEARCHER_PROVENANCE_FIELDS if k in fields},
        "comparison_limitation": "The available preceding version may already contain researcher corrections. Zero changes between supplied versions does not establish zero changes from the unavailable initial AI judgments or independent first pass.",
        "records": validated}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(output_path, result)
    return result


def main():
    parser = argparse.ArgumentParser()
    for name in ("template", "input", "freeze", "attestation", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--preliminary", type=Path)
    args = parser.parse_args()
    result = import_attested_review(args.template, args.input, args.freeze, args.attestation, args.output, args.preliminary)
    print(json.dumps({k: result[k] for k in ("annotation_version", "annotation_count", "core_judgment_count",
        "researcher_control_counts", "derived_dimension_counts", "version_comparison")}, indent=2))


if __name__ == "__main__":
    main()
