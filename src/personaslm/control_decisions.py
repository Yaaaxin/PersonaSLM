"""Lossless researcher-decision registration, separate from strict v3 import.

A 34-column disposition form is not a complete 65-column annotation form.
Keep source verdicts, permitted-use decisions and schema gaps independently.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

from .control_final_review import EDITABLE, RATINGS, VERSION as FORM_VERSION, validate_review
from .journal import atomic_json, utc_now
from .provenance import fingerprint, require_local_path, sha256

VERSION = "researcher_confirmed_control_decisions_v1"
CHECKS = tuple(field for field in RATINGS if field != "comparison_suitability")
SOURCE_FIELDS = (
    "item_number", "case_id", "candidate_id", "candidate_family", "speaker",
    "expected_answer_reference_only", "active_intervention", "candidate_control_text",
    "reported_reference_tokens", "reported_candidate_tokens", "prompt_hashes_verified_locally",
    "evidence_question_preserved_locally", "researcher_suggested_suitability",
    "researcher_supported_comparison", "researcher_residual_confounders",
    "researcher_textual_evidence_quote", "researcher_explanation", "researcher_recommended_action",
    "researcher_decision", "researcher_notes", *("researcher_check_" + field for field in CHECKS),
)
MATERIAL_FIELDS = {
    "case_id": "case_id", "candidate_id": "candidate_id", "candidate_family": "candidate_family",
    "speaker": "speaker_name", "expected_answer_reference_only": "expected_answer",
    "active_intervention": "original_active_intervention", "candidate_control_text": "candidate_control_text",
    "reported_reference_tokens": "reference_token_count", "reported_candidate_tokens": "candidate_token_count",
}
LABEL_MAP = {"yes": "PASS", "no": "FAIL", "uncertain": "UNCERTAIN", "not_applicable": "NOT_APPLICABLE"}
DECISIONS = {"REVISION_REQUIRED", "ACCEPT_NARROW", "REJECT_AS_NEUTRAL", "DIAGNOSTIC_ONLY"}
EXPECTED_DECISIONS = {"style_generic": "REVISION_REQUIRED", "history_format": "ACCEPT_NARROW",
                      "history_topic": "REJECT_AS_NEUTRAL", "history_stale_generalized": "DIAGNOSTIC_ONLY"}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames or [], list(reader)
    if not fields or len(fields) != len(set(fields)):
        raise ValueError("Missing or duplicate columns")
    if any(set(row) != set(fields) or any(not isinstance(v, str) for v in row.values()) for row in rows):
        raise ValueError("Malformed CSV row")
    return fields, rows


def canonical(text):
    return text.replace("\r\n", "\n")


def verify_master(master, fields, rows):
    if master.get("version") != FORM_VERSION or len(master.get("items", [])) != 24:
        raise ValueError("Expected the 24-item v3 master")
    if len(fields) != 65 or len(rows) != 24:
        raise ValueError("Expected 65 columns and24 master rows")
    if validate_review(master, rows, fields, require_complete=False):
        raise ValueError("Use the unchanged blank master")
    for item in master["items"]:
        if any(item[k] for k in EDITABLE):
            raise ValueError("JSON master must be blank")
        if fingerprint({k: v for k, v in item.items() if k not in EDITABLE and k != "material_sha256"}) != item["material_sha256"]:
            raise ValueError("Material fingerprint differs")
        for field, digest_field in (("reference_prompt", "reference_prompt_sha256"), ("candidate_prompt", "prompt_sha256")):
            if hashlib.sha256(item[field].encode("utf-8")).hexdigest() != item[digest_field]:
                raise ValueError("Prompt digest differs")
        if int(item["token_difference"]) != 0 or item["reference_token_count"] != item["candidate_token_count"]:
            raise ValueError("Master does not describe an exact match")


def validate_source(master, fields, rows):
    if len(fields) != len(set(fields)) or set(fields) != set(SOURCE_FIELDS):
        raise ValueError("Expected the 34-column researcher decision schema")
    expected = {row["candidate_id"]: row for row in master["items"]}
    seen, numbers = set(), set()
    for row in rows:
        if set(row) != set(fields) or any(not isinstance(v, str) for v in row.values()):
            raise ValueError("Malformed source row")
        key = row["candidate_id"]
        if key not in expected or key in seen:
            raise ValueError("Unknown or duplicate candidate ID")
        seen.add(key)
        if row["item_number"] in numbers or not row["item_number"].isdigit():
            raise ValueError("Invalid or duplicate item number")
        numbers.add(row["item_number"])
        item = expected[key]
        for source, target in MATERIAL_FIELDS.items():
            if canonical(row[source]) != canonical(item[target]):
                raise ValueError("Source material differs: " + source)
        for field in CHECKS:
            if row["researcher_check_" + field] not in LABEL_MAP:
                raise ValueError("Missing or invalid source judgment: " + field)
        if row["researcher_decision"] not in DECISIONS:
            raise ValueError("Missing or invalid researcher decision")
        if row["researcher_decision"] != EXPECTED_DECISIONS[item["candidate_family"]]:
            raise ValueError("Decision differs from the confirmed v1 family inventory; use a new registration version")
        if row["prompt_hashes_verified_locally"] not in {"yes", "no", "uncertain"} or row["evidence_question_preserved_locally"] not in {"yes", "no", "uncertain"}:
            raise ValueError("Invalid supplied local-verification flag")
        # A global quote remains global; it never becomes fifteen individual quotes.
        quote = canonical(row["researcher_textual_evidence_quote"])
        material = "\n".join(item[k] for k in ("original_active_intervention", "candidate_control_text", "trusted_evidence", "current_question", "reference_prompt", "candidate_prompt"))
        if quote and quote not in material:
            raise ValueError("Source global quote is absent from the candidate material")
    if seen != set(expected) or numbers != {str(i) for i in range(1, 25)}:
        raise ValueError("Missing source inventory")


def convert_rows(master, rows, *, attestation):
    if attestation.get("source_label_mapping") != LABEL_MAP or not attestation.get("mapping_confirmation"):
        raise ValueError("Explicit researcher confirmation of label polarity is required")
    if (not attestation.get("reviewer_id", "").strip()
            or attestation.get("researcher_confirmed") is not True
            or attestation.get("preliminary_ai_recommendations_available") is not True
            or attestation.get("blind_review") is not False):
        raise ValueError("Researcher identity, confirmation and assistance attestation required")
    expected = {item["candidate_id"]: item for item in master["items"]}
    converted, records, gaps = [], [], []
    for source in rows:
        key = source["candidate_id"]
        item = expected[key]
        row = dict(item)
        field_sources = {k: "unchanged_v3_master" for k in item if k not in EDITABLE}
        for field in CHECKS:
            row[field] = LABEL_MAP[source["researcher_check_" + field]]
            field_sources[field] = "researcher_check_" + field
        row["reviewer_id"] = attestation["reviewer_id"]
        row["review_assistance"] = "AI-assisted"
        row["reviewer_notes"] = source["researcher_notes"]
        row["reviewed_utc"] = ""  # Registration time is never a human review time.
        field_sources.update({"reviewer_id": "researcher_attestation", "review_assistance": "researcher_attestation",
                              "reviewer_notes": "researcher_notes", "reviewed_utc": "not_supplied"})
        decision = source["researcher_decision"]
        # Only A has explicit acceptance of the exact narrow comparison in v3.
        # B rejects neutrality, not every clarification diagnostic; C permits a
        # diagnostic role without certifying its adequacy; revision has no
        # unique PASS/FAIL/UNCERTAIN translation. Do not guess those labels.
        narrow = decision == "ACCEPT_NARROW" and item["candidate_family"] == "history_format"
        row["comparison_suitability"] = "PASS" if narrow else ""
        field_sources["comparison_suitability"] = (
            "researcher_decision ACCEPT_NARROW; exact unrelated-topic comparison only" if narrow
            else "scope-specific decision retained separately; official categorical label requires confirmation")
        for field in RATINGS:
            field_sources[field + "_evidence_quote"] = "not_supplied_per_field; global_quote_preserved_separately"
        allowed_na = set(item["not_applicable_fields"].split(", ")) - {""}
        row_gaps = []
        for field in RATINGS:
            if not row[field]:
                row_gaps.append({"field": field, "issue": "missing_official_label", "source_decision": decision})
            elif row[field] == "NOT_APPLICABLE" and field not in allowed_na:
                row_gaps.append({"field": field, "issue": "not_applicable_not_allowed", "source_value": source.get("researcher_check_" + field), "preserved_value": row[field]})
            if row[field] in {"FAIL", "UNCERTAIN"} and not row[field + "_evidence_quote"]:
                row_gaps.append({"field": field + "_evidence_quote", "issue": "missing_required_field_quote", "source_label": row[field]})
        for gap in row_gaps:
            gap.update({"candidate_id": key, "candidate_family": item["candidate_family"]})
        gaps.extend(row_gaps)
        converted.append(row)
        records.append({"candidate_id": key, "candidate_family": item["candidate_family"],
                        "source_row": dict(source), "researcher_decision": decision,
                        "supported_comparison_verbatim": source["researcher_supported_comparison"],
                        "global_quote_verbatim": source["researcher_textual_evidence_quote"],
                        "official_comparison_suitability": row["comparison_suitability"] or None,
                        "comparison_mapping_basis": field_sources["comparison_suitability"],
                        "unqualified_neutral_acceptance": False,
                        "field_provenance": field_sources, "schema_issues": row_gaps})
    return converted, records, gaps


def register(input_path, master_json, master_csv, attestation_path, output_dir):
    input_path, master_json, master_csv, attestation_path, output_dir = map(
        require_local_path, (input_path, master_json, master_csv, attestation_path, output_dir))
    if output_dir.exists():
        raise FileExistsError("Use a fresh output directory; submissions and registrations are immutable")
    master = json.loads(master_json.read_text(encoding="utf-8"))
    master_fields, master_rows = read_csv(master_csv)
    fields, source = read_csv(input_path)
    verify_master(master, master_fields, master_rows)
    validate_source(master, fields, source)
    attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
    if attestation.get("source_sha256") != sha256(input_path):
        raise ValueError("Attestation is not bound to the supplied source")
    rows, records, gaps = convert_rows(master, source, attestation=attestation)
    try:
        validate_review(master, rows, master_fields)
        strict = {"status": "PASS", "error": None}
    except ValueError as exc:
        strict = {"status": "PARTIAL", "error": str(exc), "completed_under_strict_import": 0}
    output_dir.mkdir(parents=True, exist_ok=False)
    archive = output_dir / "source_review.csv"
    archive.write_bytes(input_path.read_bytes())
    converted_path = output_dir / "annotation_65_columns.csv"
    with converted_path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=master_fields)
        writer.writeheader()
        writer.writerows(rows)
    gap_path = output_dir / "confirmation_needed.csv"
    gap_fields = ("candidate_id", "candidate_family", "field", "issue", "source_value", "preserved_value", "source_label", "source_decision", "researcher_confirmation", "researcher_evidence_quote", "researcher_notes")
    with gap_path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=gap_fields)
        writer.writeheader()
        writer.writerows(gaps)
    result = {
        "version": VERSION, "registered_utc": utc_now(), "packet_id": master["packet_id"],
        "source_path": str(input_path.relative_to(require_local_path(Path.cwd()))).replace("\\", "/"),
        "source_sha256": sha256(input_path), "source_archive_sha256": sha256(archive),
        "source_fields": fields, "source_annotation_checks": len(source) * len(CHECKS),
        "master_json_sha256": sha256(master_json), "master_csv_sha256": sha256(master_csv),
        "source_columns": len(fields), "converted_columns": len(master_fields),
        "converted_csv_sha256": sha256(converted_path), "confirmation_csv_sha256": sha256(gap_path),
        "attestation": attestation, "attestation_sha256": sha256(attestation_path),
        "reviewer_id": attestation["reviewer_id"], "review_type": "researcher_human_review",
        "review_assistance": "AI-assisted", "blind_review": False, "reviewed_utc": None,
        "review_time_note": "Not supplied; registration time is distinct and must not be substituted",
        "authenticity_basis": "Researcher supplied and confirmed decisions and polarity in task instructions; no software authentication",
        "decision_completion_status": "PASS", "researcher_confirmed_decisions": len(source),
        "decision_counts": dict(Counter(row["researcher_decision"] for row in source)),
        "strict_annotation_schema": strict,
        "gap_counts": dict(Counter(gap["issue"] for gap in gaps)),
        "per_field_quotes_supplied": 0, "global_quotes_retained": sum(bool(r["researcher_textual_evidence_quote"]) for r in source),
        "records": records, "schema_issues": gaps,
        "control_acceptance": "Six History A cases accepted only for their declared unrelated-topic, format/length-matched comparison; no unqualified neutrality approval. N_style requires revision; B rejected as neutral; C diagnostic only.",
        "historical_token_evidence": "Counts are checked against the frozen v3 master and its recorded actual-tokenizer evidence; no new tokenizer or generation calls",
        "P0": "PARTIAL", "P1": "NOT STARTED",
    }
    atomic_json(output_dir / "registration.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Register researcher decisions and preserve unresolved v3 annotation gaps")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--master-json", type=Path, default=Path("docs/validation/P0_final_control_review_v3.json"))
    parser.add_argument("--master-csv", type=Path, default=Path("docs/validation/P0_final_control_review_v3.csv"))
    parser.add_argument("--attestation", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = register(args.input, args.master_json, args.master_csv, args.attestation, args.output_dir)
    print(json.dumps({key: result[key] for key in ("version", "researcher_confirmed_decisions", "decision_counts", "strict_annotation_schema", "gap_counts", "P0")}))
