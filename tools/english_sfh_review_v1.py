"""Thin private English review adapter; intake never opens a condition mapping."""

import argparse
import csv
import html
import io
import json
import re
import secrets
from pathlib import Path

import p1_persona_dialogue_disjoint_surface_validation_review_v4 as prior
from real_persona_chat_sfh_review_v1 import encode_csv, json_bytes


REPO = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = REPO / ".local"
RUBRIC = REPO / "docs/validation/p1/english_real_speaker_stage_v1/human_review_rubric_v1.json"
IMMUTABLE = ("review_id", "outcome_status", "dossier", "response")
PRIMARY = ("relevance", "coherence", "linguistic_resemblance")
SECONDARY = ("history", "temporal", "behavioral", "completeness")
CLAIMS = ("supported", "contradicted", "unverifiable")
JUDGMENTS = PRIMARY + tuple(name + "_claim_count" for name in CLAIMS) + ("claim_evidence_json",) + tuple(
    field for name in SECONDARY for field in (name + "_applicability", name + "_rating")
) + ("rationale", "confidence")
EDITABLE = ("annotation_status", "missing_reason") + JUDGMENTS
FIELDS = IMMUTABLE + EDITABLE
EXPOSURES = ("prior_rubric_or_item_involvement", "prior_exposure_to_outputs",
             "condition_mapping_seen_before_lock", "automatic_or_ai_labels_seen_before_lock",
             "ai_assistance_used_for_judgments", "machine_translation_used_for_judgments")


def private_path(path):
    path = Path(path).resolve()
    if PRIVATE_ROOT.resolve() not in path.parents:
        raise ValueError("Review artifacts must remain under ignored .local")
    return path


def provenance_template():
    value = {key: None for key in EXPOSURES + (
        "human_reviewer", "english_competence_attested", "started_utc", "completed_utc",
        "completed_csv_sha256")}
    value.update({key: "" for key in ("reviewer_pseudonym", "english_competence_description",
                                      "review_environment", "aids_used", "notes")})
    value.update(schema_version="personaslm_english_review_provenance_v1",
                 relationship="PRINCIPAL_RESEARCHER", independent_of_project=False)
    return value


def csv_display(record):
    # Model/dossier text is untrusted spreadsheet input; HTML/JSON retain exact text.
    return {key: "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
            for key, value in record.items()}


def build_package(records, delivery, protected_mapping, receipt, *,
                  sealed_source_sha256, dossiers_redacted=False):
    """Caller verifies sealed outputs and redacts dossiers; no corpus or run IO here.

    Each input has exactly request_id, opaque case_id, dossier, response. Dossiers
    must already meet RUBRIC; the adapter cannot determine semantic anonymity.
    response=None records a missing outcome; empty generated text stays distinct.
    """
    if (dossiers_redacted is not True or not isinstance(sealed_source_sha256, str) or
            not re.fullmatch(r"[0-9a-f]{64}", sealed_source_sha256)):
        raise ValueError("Require caller-verified sealed source hash and redacted dossiers")
    delivery, mapping, receipt = map(private_path, (delivery, protected_mapping, receipt))
    if (delivery.exists() or mapping.exists() or receipt.exists() or mapping == receipt or
            delivery in mapping.parents or delivery in receipt.parents or
            mapping in delivery.parents or receipt in delivery.parents or
            mapping in receipt.parents or receipt in mapping.parents):
        raise ValueError("New delivery and separate analyst files required; no overwrite")
    if not isinstance(records, list) or not records:
        raise ValueError("A nonempty fixed list of review records is required")
    by_case, request_ids, ordered = {}, set(), []
    for row in records:
        if (set(row) != {"request_id", "case_id", "dossier", "response"} or
                any(not isinstance(row[key], str) for key in ("request_id", "case_id", "dossier")) or
                (row["response"] is not None and not isinstance(row["response"], str))):
            raise ValueError("Exact input schema required; response is text or None for missing")
        if any(not row[key].strip() for key in ("request_id", "case_id", "dossier")):
            raise ValueError("Nonempty source identifiers and dossier required")
        if row["request_id"] in request_ids:
            raise ValueError("Duplicate analyst request_id")
        request_ids.add(row["request_id"])
        if row["case_id"] in by_case and by_case[row["case_id"]] != row["dossier"]:
            raise ValueError("Every condition for a case must have the identical dossier")
        by_case[row["case_id"]] = row["dossier"]
        ordered.append(dict(row))
    secrets.SystemRandom().shuffle(ordered)
    public, protected, seen = [], [], set()
    for row in ordered:
        review_id = secrets.token_hex(16)
        if review_id in seen:
            raise ValueError("Opaque ID collision; no files written")
        seen.add(review_id)
        visible = {"review_id": review_id,
                   "outcome_status": "MISSING_OUTCOME" if row["response"] is None else "GENERATED",
                   "dossier": row["dossier"], "response": row["response"] or ""}
        public.append(visible)
        protected.append({"review_id": review_id, "request_id": row["request_id"],
                          "case_id": row["case_id"], "display_sha256": prior.sha256_bytes(json_bytes(visible))})
    readme = (
        "ENGLISH CONVERSATION REVIEW\n\n"
        "Review each response using its common dossier and the rubric below. The task has multiple "
        "legitimate continuations; no unique human answer is supplied. Never infer real identities.\n"
        "Open records.html locally to read the records. It contains no scripts or network resources. "
        "Copy REVIEW.csv to a new local WORKING.csv and save incremental edits there. Keep all rows "
        "and the first four columns unchanged. The original delivery files are fixed. "
        "CSV-only safety apostrophes protect formula-like source cells; leave them unchanged. "
        "The HTML and JSON retain exact source text. Import all CSV columns as text. "
        "MISSING_OUTCOME is not an empty model answer: retain it as UNAVAILABLE with a reason, never zero.\n"
        "Complete genuine judgments only; do not ask an AI to supply ratings. All source-relative "
        "judgments remain unconfirmed until this review is actually performed.\n"
        "Copy provenance.json to a new local completed-provenance.json, then truthfully fill every "
        "attestation. The principal researcher is not independent of this project. Record all prior "
        "rubric/item involvement and exposure; neither random order nor condition masking erases it.\n"
        "Set completed_csv_sha256 to the SHA-256 of the final WORKING.csv (PowerShell: "
        "(Get-FileHash -Algorithm SHA256 -LiteralPath .\\WORKING.csv).Hash.ToLower()). "
        "Any later CSV edit requires updating that hash. Do not claim double-blind review or "
        "inter-rater reliability. Validation feedback contains no condition mapping.\n\n"
    ).encode("utf-8") + RUBRIC.read_bytes()
    rendered = ("<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
                "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\">"
                "<title>English conversation review</title><body><h1>English conversation review</h1>"
                "<p>Use READ_ME.txt and save ratings in a copy of REVIEW.csv. No labels are prefilled.</p>")
    for row in public:
        rendered += ("<section><h2>Review " + html.escape(row["review_id"]) + "</h2><p>" +
                     html.escape(row["outcome_status"]) + "</p><h3>Common dossier</h3>"
                     "<pre style=\"white-space:pre-wrap\">" + html.escape(row["dossier"]) +
                     "</pre><h3>Response</h3><pre style=\"white-space:pre-wrap\">" +
                     html.escape(row["response"]) + "</pre></section><hr>")
    rendered += "</body></html>"
    files = {"READ_ME.txt": readme, "records.json": json_bytes({"records": public}),
             "records.html": rendered.encode("utf-8"),
             "REVIEW.csv": encode_csv([{**csv_display(row), **{key: "" for key in EDITABLE}} for row in public], FIELDS),
             "provenance.json": json_bytes(provenance_template())}
    mapping_bytes = json_bytes({"privacy": "PROTECTED_ANALYST_ONLY_DO_NOT_DELIVER_OR_OPEN_BEFORE_REVIEW_LOCK",
                               "sealed_source_sha256": sealed_source_sha256, "rows": protected})
    receipt_doc = {"schema_version": "personaslm_english_review_package_v1", "records": len(public),
                   "human_labels": 0, "mapping_in_delivery": False,
                   "sealed_source_sha256": sealed_source_sha256,
                   "rubric_sha256": prior.sha256(RUBRIC), "adapter_sha256": prior.sha256(Path(__file__)),
                   "protected_mapping_sha256": prior.sha256_bytes(mapping_bytes),
                   "files": {name: prior.sha256_bytes(value) for name, value in files.items()}}
    prior.write_exclusive(mapping, mapping_bytes)
    for name, value in files.items():
        prior.write_exclusive(delivery / name, value)
    prior.write_exclusive(receipt, json_bytes(receipt_doc))
    return {"records": len(public), "human_labels": 0, "mapping_in_delivery": False,
            "receipt_sha256": prior.sha256(receipt)}


def load_package(delivery, receipt):
    """Read only delivery and its analyst hash receipt, never the protected map."""
    delivery, receipt = private_path(delivery), private_path(receipt)
    if delivery in receipt.parents:
        raise ValueError("Analyst receipt must not be in reviewer delivery")
    doc = prior.load_json_bytes(receipt.read_bytes())
    if (doc.get("schema_version") != "personaslm_english_review_package_v1" or
            doc.get("human_labels") != 0 or doc.get("mapping_in_delivery") is not False or
            doc.get("rubric_sha256") != prior.sha256(RUBRIC) or
            set(doc.get("files", {})) != {"READ_ME.txt", "records.json", "records.html", "REVIEW.csv", "provenance.json"}):
        raise ValueError("Package receipt or frozen rubric changed")
    for name, expected in doc["files"].items():
        if prior.sha256(delivery / name) != expected:
            raise ValueError("Immutable delivery changed: " + name)
    rows = prior.load_json_bytes((delivery / "records.json").read_bytes())["records"]
    if not rows or len(rows) != doc["records"] or len({row["review_id"] for row in rows}) != len(rows):
        raise ValueError("Fixed record set changed")
    return {"rows": rows, "receipt": doc}


def decode_csv(content):
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""), strict=True)
    if reader.fieldnames != list(FIELDS):
        raise ValueError("Exact CSV header/order required")
    rows = list(reader)
    if any(None in row or None in row.values() for row in rows):
        raise ValueError("Missing or extra CSV cells")
    return rows


def _claim_errors(row):
    errors = []
    counts = {}
    for name in CLAIMS:
        value = row[name + "_claim_count"]
        if value:
            if not re.fullmatch(r"0|[1-9][0-9]*", value):
                errors.append("Nonnegative integer required: " + name + "_claim_count")
            else:
                counts[name] = int(value)
    if not row["claim_evidence_json"]:
        return errors
    try:
        doc = prior.load_json_bytes(row["claim_evidence_json"].encode("utf-8"))
        if set(doc) != {"claims"} or not isinstance(doc["claims"], list):
            raise ValueError("claim_evidence_json requires only a claims array")
        found = dict.fromkeys(CLAIMS, 0)
        for claim in doc["claims"]:
            if (not isinstance(claim, dict) or set(claim) != {
                    "status", "response_span", "reference_span", "rationale"} or
                    any(not isinstance(value, str) for value in claim.values()) or
                    claim["status"] not in CLAIMS):
                raise ValueError("Invalid atomic claim schema/status")
            if not claim["response_span"].strip() or claim["response_span"] not in row["response"]:
                raise ValueError("Claim response_span must be an exact nonempty response substring")
            reference = claim["reference_span"]
            if ((reference and reference not in row["dossier"]) or
                    (claim["status"] != "unverifiable" and not reference.strip())):
                raise ValueError("Supported/contradicted claims require an exact nonempty dossier span")
            if not claim["rationale"].strip():
                raise ValueError("Each claim requires a human rationale")
            found[claim["status"]] += 1
        if any(found[key] != value for key, value in counts.items()):
            raise ValueError("Claim counts differ from evidence entries")
    except (TypeError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def validate_submission(package, content, final=False):
    errors, warnings = [], []
    counts = {"assigned": len(package["rows"]), "finalized": 0, "completed": 0,
              "unavailable": 0, "not_started": 0}
    try:
        rows = decode_csv(content)
    except (UnicodeDecodeError, ValueError, csv.Error) as exc:
        return {"counts": counts, "errors": [prior.issue("CSV_INVALID", str(exc))], "warnings": []}
    if len(rows) != counts["assigned"]:
        return {"counts": counts, "errors": [prior.issue("FIXED_RECORD_SET_REQUIRED", "Keep every assigned row exactly once.")], "warnings": []}
    for number, (row, original) in enumerate(zip(rows, package["rows"]), 1):
        invalid, incomplete = [], []
        expected = csv_display(original)
        if any(row[key] != expected[key] for key in IMMUTABLE):
            invalid.append("Immutable source cells or fixed record order changed")
        for field in PRIMARY + tuple(name + "_rating" for name in SECONDARY):
            if row[field] and row[field] not in ("0", "1", "2", "3", "NA"):
                invalid.append("Invalid rating: " + field)
        for name in SECONDARY:
            applicability, rating = row[name + "_applicability"], row[name + "_rating"]
            if applicability and applicability not in ("APPLICABLE", "NOT_APPLICABLE", "UNCERTAIN"):
                invalid.append("Invalid applicability: " + name)
            if applicability and rating and ((applicability == "APPLICABLE") == (rating == "NA")):
                invalid.append("Applicability/rating conflict: " + name)
        if row["confidence"] and row["confidence"] not in ("LOW", "MEDIUM", "HIGH"):
            invalid.append("Invalid confidence")
        invalid.extend(_claim_errors({**row, "dossier": original["dossier"], "response": original["response"]}))
        if row["annotation_status"] == "UNAVAILABLE":
            if not row["missing_reason"].strip():
                incomplete.append("UNAVAILABLE requires missing_reason")
            if any(row[key].strip() for key in JUDGMENTS):
                invalid.append("UNAVAILABLE must not contain judgments")
            counts["unavailable"] += 1
        elif row["annotation_status"] == "COMPLETED":
            if original["outcome_status"] == "MISSING_OUTCOME":
                invalid.append("MISSING_OUTCOME must be UNAVAILABLE, never rated as zero")
            if row["missing_reason"].strip():
                invalid.append("COMPLETED requires blank missing_reason")
            missing = [key for key in JUDGMENTS if not row[key].strip()]
            if missing:
                incomplete.append("Missing judgments: " + ", ".join(missing))
        else:
            if row["annotation_status"]:
                invalid.append("Invalid annotation_status")
            incomplete.append("Record is not finalized")
        if all(not row[key].strip() for key in EDITABLE):
            counts["not_started"] += 1
        if not invalid and not incomplete:
            counts["finalized"] += 1
            counts["completed"] += int(row["annotation_status"] == "COMPLETED")
        errors.extend(prior.issue("ROW_INVALID", message, row=number, blind_record_id=original["review_id"]) for message in invalid)
        target = errors if final else warnings
        target.extend(prior.issue("ROW_INCOMPLETE", message, row=number, blind_record_id=original["review_id"]) for message in incomplete)
    return {"counts": counts, "errors": errors, "warnings": warnings}


def validate_provenance(value, content):
    errors = []
    if set(value) != set(provenance_template()):
        return {"errors": ["Exactly the provenance template fields are required"], "classification": None}
    if (value["schema_version"] != provenance_template()["schema_version"] or
            value["relationship"] != "PRINCIPAL_RESEARCHER" or value["independent_of_project"] is not False):
        errors.append("This principal-researcher review is not project-independent")
    for key in ("human_reviewer", "english_competence_attested"):
        if value[key] is not True:
            errors.append(key + " requires genuine affirmative human attestation")
    for key in ("reviewer_pseudonym", "english_competence_description", "review_environment", "aids_used"):
        if not isinstance(value[key], str) or not value[key].strip():
            errors.append(key + " requires truthful text")
    if not isinstance(value["notes"], str):
        errors.append("notes must be text")
    if any(value[key] not in ("YES", "NO", "UNCERTAIN") for key in EXPOSURES):
        errors.append("Every involvement/exposure/assistance attestation is required")
    if any(value[key] != "NO" for key in EXPOSURES[-2:]):
        errors.append("AI-assisted or machine-translated judgments are not original-English human-only evidence")
    try:
        if prior._parse_utc(value["started_utc"]) > prior._parse_utc(value["completed_utc"]):
            errors.append("Review timestamps are out of order")
    except (TypeError, ValueError):
        errors.append("Actual explicitly zoned UTC review timestamps required")
    if value["completed_csv_sha256"] != prior.sha256_bytes(content):
        errors.append("completed_csv_sha256 does not bind this submission")
    classification = None if errors else (
        "HUMAN_EXPOSURE_LIMITED" if any(value[key] != "NO" for key in EXPOSURES[:4])
        else "CONDITION_MASKED_NONINDEPENDENT_HUMAN")
    return {"errors": errors, "classification": classification,
            "independent_reviewer": False, "inter_rater_reliability": False,
            "independent_experimental_validation": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate-draft", "validate-final"))
    parser.add_argument("--delivery", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--feedback", type=Path, required=True)
    args = parser.parse_args(argv)
    package = load_package(args.delivery, args.receipt)
    content = private_path(args.submission).read_bytes()
    final = args.action == "validate-final"
    report = validate_submission(package, content, final=final)
    if final:
        if args.provenance is None:
            report["errors"].append(prior.issue("PROVENANCE_REQUIRED", "Final review requires genuine provenance."))
        else:
            checked = validate_provenance(prior.load_json_bytes(private_path(args.provenance).read_bytes()), content)
            report["provenance"] = checked
            report["errors"].extend(prior.issue("PROVENANCE_INVALID", message) for message in checked["errors"])
    report.update(status="NOT_READY" if report["errors"] else "READY_FOR_LOCK_NOT_LOCKED" if final else "DRAFT_VALID",
                  submission_sha256=prior.sha256_bytes(content), protected_mapping_opened=False,
                  unblinding_authorized=False, official_lock_created=False)
    prior.write_exclusive(private_path(args.feedback), json_bytes(report))
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "error_count": len(report["errors"]), "warning_count": len(report["warnings"])}, sort_keys=True))
    return int(bool(report["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
