"""Offline Stage-A review helper; never reads the protected condition mapping."""

import argparse
import csv
import hashlib
import io
import json
from datetime import datetime
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PROTOCOL = REPO / (
    "docs/validation/p1/persona_dialogue_disjoint_surface_validation_v3/"
    "blinded_human_review_protocol_v3.json")
DELIVERY = REPO / (
    "results/p1_persona_dialogue_disjoint_surface_validation/v3/"
    "human_review/stage_a_delivery")
TEMPLATE = DELIVERY / "stage_a_current_only_REVIEW_TEMPLATE.csv"
INSTRUCTIONS = DELIVERY / "stage_a_REVIEW_INSTRUCTIONS.json"
RECEIPT = DELIVERY / "stage_a_package_receipt.json"
FROZEN_PUBLIC_HASHES = {
    "template": "1b125f7c17eebb262dbbc2ad1ecbbf8ca265fb92feff6458fa41fe6ab4c41d47",
    "instructions": "33ff59daa42ddf57fea84ae2f4973cc7930b6141e441b9cfa9d773bced878185",
    "receipt": "fb8262dad4118fde81ec8a286f48d1aca009911b06ac65a79a26ef95417895e6",
    "protocol": "e4db428b9c523a70c19781be22c1711839c3835fb8a863e3c7cf654ace986943",
}


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256(path):
    return sha256_bytes(Path(path).read_bytes())


def load_json_bytes(value):
    def unique_object(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = item
        return result

    parsed = json.loads(value.decode("utf-8-sig"), object_pairs_hook=unique_object)
    if not isinstance(parsed, dict):
        raise ValueError("JSON object required")
    return parsed


def issue(code, message, field=None, row=None, blind_record_id=None):
    result = {"code": code, "message": message}
    if field is not None:
        result["field"] = field
    if row is not None:
        result["row"] = row
    if blind_record_id is not None:
        result["blind_record_id"] = blind_record_id
    return result


def load_package(template=TEMPLATE, instructions=INSTRUCTIONS,
                 receipt=RECEIPT, protocol=PROTOCOL):
    paths = tuple(Path(path) for path in
                  (template, instructions, receipt, protocol))
    if not all(path.is_file() for path in paths):
        raise ValueError("Official Stage-A delivery or protocol file is missing")
    template, instructions, receipt_path, protocol_path = paths
    official_paths = tuple(path.resolve() for path in
                           (TEMPLATE, INSTRUCTIONS, RECEIPT, PROTOCOL))
    if tuple(path.resolve() for path in paths) == official_paths:
        actual = {"template": sha256(template),
                  "instructions": sha256(instructions),
                  "receipt": sha256(receipt_path),
                  "protocol": sha256(protocol_path)}
        if actual != FROZEN_PUBLIC_HASHES:
            raise ValueError("Frozen Stage-A public artifact hash changed")
    receipt_doc = load_json_bytes(receipt_path.read_bytes())
    protocol_doc = load_json_bytes(protocol_path.read_bytes())
    expected = {
        "template_sha256": sha256(template),
        "instructions_sha256": sha256(instructions),
        "review_schema_sha256": sha256(protocol_path),
    }
    if any(receipt_doc.get(key) != value for key, value in expected.items()):
        raise ValueError("Official Stage-A public package hash binding changed")
    if (receipt_doc.get("stage") != "A" or
            receipt_doc.get("record_count") != 168 or
            receipt_doc.get("mapping_in_delivery") is not False or
            receipt_doc.get("labels_created") != 0):
        raise ValueError("Official Stage-A public receipt invariants changed")
    stage = protocol_doc["stage_a"]
    return {
        "template_path": template,
        "instructions_path": instructions,
        "receipt_path": receipt_path,
        "protocol_path": protocol_path,
        "template_bytes": template.read_bytes(),
        "receipt": receipt_doc,
        "protocol": protocol_doc,
        "immutable": tuple(stage["reviewer_visible_immutable_columns"]),
        "editable": tuple(stage["editable_columns"]),
        "enums": stage["enums"],
    }


def decode_csv(value, expected_fields):
    reader = csv.DictReader(io.StringIO(value.decode("utf-8-sig"), newline=""))
    if reader.fieldnames != list(expected_fields):
        raise ValueError("CSV header/order differs from the official template")
    rows = list(reader)
    if any(None in row or None in row.values() or
           set(row) != set(expected_fields) for row in rows):
        raise ValueError("CSV contains a missing or extra cell")
    if len(rows) != 168:
        raise ValueError(f"CSV must retain all 168 rows; found {len(rows)}")
    return rows


def _row_judgment_issues(row, enums, final, row_number, blind_id):
    judgment_fields = tuple(field for field in row if field not in (
        "blind_record_id", "response_instruction", "synthetic_persona_profile",
        "current_evidence_and_choices", "current_user_turn", "model_response",
        "annotation_status", "missing_reason"))
    errors, warnings = [], []

    def add_incomplete(code, message, field=None):
        target = errors if final else warnings
        target.append(issue(code, message, field, row_number, blind_id))

    for field in judgment_fields:
        value = row[field]
        if value and field in enums and value not in enums[field]:
            errors.append(issue("INVALID_ENUM", f"Invalid value for {field}.",
                                field, row_number, blind_id))
    span = row["evidence_span"]
    if span:
        sentinel_ok = span == "NO_SUPPORTING_SPAN" and (
            row["selected_entity"] == "NONE" or
            row["reason_support"] == "NO_REASON")
        if span not in row["model_response"] and not sentinel_ok:
            errors.append(issue(
                "INVALID_EVIDENCE_SPAN",
                "evidence_span must be an exact model-response substring or "
                "an applicable NO_SUPPORTING_SPAN.",
                "evidence_span", row_number, blind_id))

    status = row["annotation_status"]
    if not status.strip():
        if any(row[field].strip() for field in
               ("missing_reason",) + judgment_fields):
            add_incomplete("STATUS_REQUIRED",
                           "Set annotation_status after editing this row.",
                           "annotation_status")
        return "NOT_STARTED" if all(not row[field].strip() for field in
                                    ("missing_reason",) + judgment_fields) \
            else "IN_PROGRESS", errors, warnings
    if status not in enums["annotation_status"]:
        errors.append(issue("INVALID_STATUS", "Invalid annotation_status.",
                            "annotation_status", row_number, blind_id))
        return "IN_PROGRESS", errors, warnings
    if status == "UNAVAILABLE":
        if not row["missing_reason"].strip():
            add_incomplete("MISSING_REASON_REQUIRED",
                           "UNAVAILABLE requires missing_reason.",
                           "missing_reason")
        populated = [field for field in judgment_fields if row[field].strip()]
        if populated:
            errors.append(issue(
                "UNAVAILABLE_HAS_JUDGMENTS",
                "UNAVAILABLE requires every judgment field to be blank.",
                ",".join(populated), row_number, blind_id))
        return ("FINALIZED" if not errors and not warnings else "IN_PROGRESS",
                errors, warnings)

    if row["missing_reason"].strip():
        errors.append(issue("COMPLETED_HAS_MISSING_REASON",
                            "COMPLETED requires blank missing_reason.",
                            "missing_reason", row_number, blind_id))
    missing = [field for field in judgment_fields if not row[field].strip()]
    if missing:
        add_incomplete("COMPLETED_FIELDS_MISSING",
                       "COMPLETED requires all judgment fields.",
                       ",".join(missing))
    uncertain = any(row[field] == "UNCERTAIN" for field in judgment_fields)
    if uncertain and not row["reviewer_rationale"].strip():
        add_incomplete("UNCERTAIN_RATIONALE_REQUIRED",
                       "UNCERTAIN requires reviewer_rationale.",
                       "reviewer_rationale")
    return ("FINALIZED" if not errors and not warnings else "IN_PROGRESS",
            errors, warnings)


def validate_submission(package, submission_bytes, final=False):
    fields = package["immutable"] + package["editable"]
    template_rows = decode_csv(package["template_bytes"], fields)
    submitted = decode_csv(submission_bytes, fields)
    errors, warnings = [], []
    counts = {"FINALIZED": 0, "IN_PROGRESS": 0, "NOT_STARTED": 0}
    for number, (expected, observed) in enumerate(zip(template_rows, submitted), 1):
        blind_id = expected["blind_record_id"]
        changed = [field for field in package["immutable"]
                   if observed[field] != expected[field]]
        if changed:
            errors.append(issue(
                "IMMUTABLE_CELL_CHANGED",
                "Reviewer-visible source material differs from the official template.",
                ",".join(changed), number, blind_id))
        state, row_errors, row_warnings = _row_judgment_issues(
            observed, package["enums"], final, number, blind_id)
        counts[state] += 1
        errors.extend(row_errors)
        warnings.extend(row_warnings)
    if final and counts["FINALIZED"] != 168:
        errors.append(issue(
            "ALL_168_RECORDS_REQUIRED",
            "Final validation requires all 168 records to be valid COMPLETED "
            "or documented UNAVAILABLE rows."))
    return {"counts": {"records_assigned": 168,
                       "records_finalized": counts["FINALIZED"],
                       "records_in_progress": counts["IN_PROGRESS"],
                       "records_not_started": counts["NOT_STARTED"]},
            "errors": errors, "warnings": warnings}


def _parse_utc(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("UTC timestamp is required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("Timestamp must use UTC with an explicit zone")
    return parsed


def corrected_classification(provenance):
    ai = provenance["ai_assistance_used_for_judgments"]
    if provenance["human_reviewer"] is not True or ai in ("YES", "UNCERTAIN"):
        return "INELIGIBLE_AS_GENUINE_HUMAN"
    exposure_fields = (
        "prior_rubric_or_item_involvement",
        "prior_exposure_to_outputs",
        "condition_mapping_seen_before_lock",
        "automatic_or_ai_labels_seen_before_lock",
        "stage_b_material_seen_before_stage_a_lock",
    )
    if any(provenance[field] != "NO" for field in exposure_fields):
        return "HUMAN_EXPOSURE_LIMITED"
    if (provenance["independent_of_project"] is True and
            provenance["relationship"] == "INDEPENDENT_EXTERNAL"):
        return "CLEAN_INDEPENDENT_BLINDED_HUMAN"
    return "BLINDED_NONINDEPENDENT_HUMAN"


def legacy_v3_classification(provenance):
    ai = provenance["ai_assistance_used_for_judgments"]
    if provenance["human_reviewer"] is not True or ai in ("YES", "UNCERTAIN"):
        return "INELIGIBLE_AS_GENUINE_HUMAN"
    exposures = (
        provenance["prior_exposure_to_outputs"],
        provenance["condition_mapping_seen_before_lock"],
        provenance["automatic_or_ai_labels_seen_before_lock"],
        provenance["stage_b_material_seen_before_stage_a_lock"],
    )
    return ("CLEAN_BLINDED_HUMAN" if set(exposures) == {"NO"}
            else "HUMAN_EXPOSURE_LIMITED")


def validate_provenance(package, provenance_bytes, submission_bytes):
    errors = []
    try:
        value = load_json_bytes(provenance_bytes)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        return {"errors": [issue("PROVENANCE_JSON_INVALID", str(exc))]}
    protocol = package["protocol"]["provenance"]
    required = set(protocol["required_fields"])
    if set(value) != required:
        missing = sorted(required - set(value))
        extra = sorted(set(value) - required)
        errors.append(issue(
            "PROVENANCE_FIELDS_CHANGED",
            f"Missing fields: {missing}; extra fields: {extra}."))
        return {"errors": errors}
    if value["schema_version"] != protocol["schema_version"]:
        errors.append(issue("PROVENANCE_SCHEMA_INVALID",
                            "Provenance schema_version changed.",
                            "schema_version"))
    for field in ("reviewer_pseudonym", "private_reviewer_identifier",
                  "review_environment"):
        if not isinstance(value[field], str) or not value[field].strip():
            errors.append(issue("PROVENANCE_TEXT_REQUIRED",
                                f"{field} must be nonempty.", field))
    if not isinstance(value["notes"], str):
        errors.append(issue("PROVENANCE_NOTES_INVALID",
                            "notes must be a string.", "notes"))
    for field in ("human_reviewer", "independent_of_project"):
        if type(value[field]) is not bool:
            errors.append(issue("PROVENANCE_BOOLEAN_REQUIRED",
                                f"{field} must be true or false.", field))
    if value["relationship"] not in protocol["relationship_enum"]:
        errors.append(issue("PROVENANCE_RELATIONSHIP_INVALID",
                            "relationship is invalid.", "relationship"))
    if (value["independent_of_project"] is True and
            value["relationship"] != "INDEPENDENT_EXTERNAL"):
        errors.append(issue(
            "INDEPENDENCE_ATTESTATION_CONFLICT",
            "independent_of_project=true requires relationship=INDEPENDENT_EXTERNAL.",
            "independent_of_project"))
    exposure_fields = (
        "prior_rubric_or_item_involvement", "prior_exposure_to_outputs",
        "condition_mapping_seen_before_lock",
        "automatic_or_ai_labels_seen_before_lock",
        "ai_assistance_used_for_judgments",
        "stage_b_material_seen_before_stage_a_lock")
    for field in exposure_fields:
        if value[field] not in protocol["exposure_enum"]:
            errors.append(issue("PROVENANCE_EXPOSURE_INVALID",
                                f"{field} must be NO, YES, or UNCERTAIN.", field))
    try:
        started, completed = (_parse_utc(value[field]) for field in
                              ("started_utc", "completed_utc"))
        if started > completed:
            errors.append(issue("PROVENANCE_TIME_ORDER_INVALID",
                                "started_utc must not follow completed_utc."))
    except (TypeError, ValueError) as exc:
        errors.append(issue("PROVENANCE_UTC_INVALID", str(exc)))
    expected_hashes = {
        "template_sha256": sha256_bytes(package["template_bytes"]),
        "instructions_sha256": sha256(package["instructions_path"]),
        "schema_sha256": sha256(package["protocol_path"]),
        "source_receipt_sha256": sha256(package["receipt_path"]),
        "completed_csv_sha256": sha256_bytes(submission_bytes),
    }
    for field, expected in expected_hashes.items():
        if value[field] != expected:
            errors.append(issue("PROVENANCE_HASH_MISMATCH",
                                f"{field} does not bind the current file.", field))
    if errors:
        return {"errors": errors}
    corrected = corrected_classification(value)
    legacy = legacy_v3_classification(value)
    claim = {
        "CLEAN_INDEPENDENT_BLINDED_HUMAN":
            "Genuine condition-blinded human review with attested project "
            "independence; not inter-rater or independent experimental validation.",
        "BLINDED_NONINDEPENDENT_HUMAN":
            "Genuine condition-blinded human review; not independent review, "
            "inter-rater reliability, or independent validation.",
        "HUMAN_EXPOSURE_LIMITED":
            "Genuine human review with recorded exposure limitations; no clean "
            "blinded-review claim. Project independence is reported separately "
            "and is not independent experimental validation.",
        "INELIGIBLE_AS_GENUINE_HUMAN":
            "Not eligible as genuine human-only judgment evidence.",
    }[corrected]
    return {"errors": [], "corrected_classification_v4": corrected,
            "legacy_v3_classification_prediction": legacy,
            "legacy_v3_classification_differs": corrected != legacy,
            "legacy_v3_would_overstate_cleanliness":
                legacy == "CLEAN_BLINDED_HUMAN" and corrected in (
                    "BLINDED_NONINDEPENDENT_HUMAN",
                    "HUMAN_EXPOSURE_LIMITED"),
            "classification_inputs": {
                "prior_rubric_or_item_involvement":
                    value["prior_rubric_or_item_involvement"],
                "prior_item_exposure": value["prior_exposure_to_outputs"],
                "independent_of_project": value["independent_of_project"],
                "relationship": value["relationship"],
                "ai_assistance_used_for_judgments":
                    value["ai_assistance_used_for_judgments"]},
            "claim_boundary": claim}


def validate(package, submission, provenance=None, final=False):
    submission_bytes = Path(submission).read_bytes()
    report = validate_submission(package, submission_bytes, final)
    provenance_report = None
    if provenance is not None:
        provenance_report = validate_provenance(
            package, Path(provenance).read_bytes(), submission_bytes)
        report["errors"].extend(provenance_report["errors"])
    elif final:
        report["errors"].append(issue(
            "PROVENANCE_REQUIRED", "Final validation requires provenance JSON."))
    if (final and provenance_report and not provenance_report["errors"] and
            provenance_report["corrected_classification_v4"] ==
            "INELIGIBLE_AS_GENUINE_HUMAN"):
        report["errors"].append(issue(
            "GENUINE_HUMAN_PROVENANCE_REQUIRED",
            "AI-assisted, uncertain-AI, or non-human judgments cannot satisfy "
            "the genuine-human review requirement."))
    report.update({
        "schema_version": "personaslm_dsv_stage_a_offline_review_helper_v4",
        "mode": "FINAL" if final else "DRAFT",
        "status": ("READY_FOR_OFFICIAL_SEAL_ATTEMPT_NOT_SEALED"
                   if final and not report["errors"] else
                   "DRAFT_VALID" if not final and not report["errors"] else
                   "NOT_READY"),
        "provenance": provenance_report,
        "protected_mapping_accessed": False,
        "official_seal_created": False,
        "unblinding_authorized": False,
        "submission_sha256": sha256_bytes(submission_bytes),
        "provenance_sha256": (None if provenance is None else
                              sha256(provenance)),
        "bindings": {
            "helper_sha256": sha256(Path(__file__)),
            "official_template_sha256": sha256_bytes(
                package["template_bytes"]),
            "official_instructions_sha256": sha256(
                package["instructions_path"]),
            "review_protocol_sha256": sha256(package["protocol_path"]),
            "public_receipt_sha256": sha256(package["receipt_path"]),
        },
    })
    return report


def provenance_skeleton(package, submission_bytes):
    protocol = package["protocol"]["provenance"]
    return {
        "schema_version": protocol["schema_version"],
        "reviewer_pseudonym": "",
        "private_reviewer_identifier": "",
        "human_reviewer": None,
        "relationship": None,
        "independent_of_project": None,
        "prior_rubric_or_item_involvement": None,
        "prior_exposure_to_outputs": None,
        "condition_mapping_seen_before_lock": None,
        "automatic_or_ai_labels_seen_before_lock": None,
        "ai_assistance_used_for_judgments": None,
        "stage_b_material_seen_before_stage_a_lock": None,
        "review_environment": "",
        "started_utc": None,
        "completed_utc": None,
        "template_sha256": sha256_bytes(package["template_bytes"]),
        "instructions_sha256": sha256(package["instructions_path"]),
        "schema_sha256": sha256(package["protocol_path"]),
        "source_receipt_sha256": sha256(package["receipt_path"]),
        "completed_csv_sha256": sha256_bytes(submission_bytes),
        "notes": "",
    }


def write_exclusive(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(value)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=(
        "init-copy", "validate-draft", "create-provenance", "validate-final"))
    parser.add_argument("--submission", required=True, type=Path)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--report", type=Path,
                        help="Optional exclusive-create JSON receipt path")
    args = parser.parse_args(argv)
    package = load_package()
    if args.action == "init-copy":
        write_exclusive(args.submission, package["template_bytes"])
        report = {"schema_version":
                  "personaslm_dsv_stage_a_offline_review_helper_v4",
                  "status": "EXACT_OFFICIAL_TEMPLATE_COPY_CREATED",
                  "submission": args.submission.as_posix(),
                  "submission_sha256": sha256(args.submission),
                  "protected_mapping_accessed": False}
    elif args.action == "create-provenance":
        submission_bytes = args.submission.read_bytes()
        readiness = validate_submission(package, submission_bytes, final=True)
        if readiness["errors"]:
            report = {**readiness, "schema_version":
                      "personaslm_dsv_stage_a_offline_review_helper_v4",
                      "status": "NOT_READY_FOR_PROVENANCE_TEMPLATE",
                      "protected_mapping_accessed": False}
        elif args.provenance is None:
            parser.error("create-provenance requires --provenance")
        else:
            value = (json.dumps(provenance_skeleton(package, submission_bytes),
                                ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            write_exclusive(args.provenance, value)
            report = {"schema_version":
                      "personaslm_dsv_stage_a_offline_review_helper_v4",
                      "status": "INCOMPLETE_PROVENANCE_SKELETON_CREATED",
                      "provenance": args.provenance.as_posix(),
                      "provenance_sha256": sha256(args.provenance),
                      "human_attestations_prefilled": False,
                      "protected_mapping_accessed": False}
    else:
        report = validate(package, args.submission, args.provenance,
                          final=args.action == "validate-final")
    rendered = (json.dumps(report, ensure_ascii=False, indent=2,
                           sort_keys=True) + "\n").encode("utf-8")
    if args.report is not None:
        write_exclusive(args.report, rendered)
    print(rendered.decode("utf-8"), end="")
    return 0 if report["status"] not in ("NOT_READY",
                                         "NOT_READY_FOR_PROVENANCE_TEMPLATE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
