"""Scoped primary-only review adapter; never reads a protected mapping or run.

Package creation accepts caller-sealed allocations, not unverified raw journals.
Use sequentially: the existing helper's globals are patched only for each call.
"""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from unittest.mock import patch

import english_sfh_review_v1 as legacy


REPO = Path(__file__).resolve().parents[1]
RUBRIC = REPO / "docs/validation/p1/english_model_comparison_v1/primary_review_rubric_v1.json"
PROTOCOL = REPO / "docs/validation/p1/english_model_comparison_v1/prospective_protocol_v1.json"
PRIMARY = legacy.PRIMARY
IMMUTABLE = legacy.IMMUTABLE
EDITABLE = ("annotation_status", "missing_reason") + PRIMARY + ("rationale",)
FIELDS = IMMUTABLE + EDITABLE
SCHEMA = {"version": "english_model_comparison_primary_review_v1", "records": 200,
          "cases": 10, "records_per_case": 20, "fields": list(FIELDS),
          "ratings": ["0", "1", "2", "3", "4", "5", "NA"],
          "statuses": ["COMPLETED", "UNAVAILABLE"]}
RECEIPT_SCHEMA = "english_model_comparison_primary_review_receipt_v1"


def _scope():
    return patch.multiple(legacy, RUBRIC=RUBRIC, EDITABLE=EDITABLE, FIELDS=FIELDS)


def _bindings():
    return {"adapter_sha256": legacy.prior.sha256(Path(__file__)),
            "helper_sha256": legacy.prior.sha256(Path(legacy.__file__)),
            "rubric_sha256": legacy.prior.sha256(RUBRIC),
            "protocol_sha256": legacy.prior.sha256(PROTOCOL),
            "field_schema_sha256": legacy.prior.sha256_bytes(legacy.json_bytes(SCHEMA))}


def build_package(records, delivery, protected_mapping, helper_receipt, receipt, *,
                  sealed_source_sha256, dossiers_redacted=False):
    """Build one mixed model/condition-masked package from 200 sealed allocations.

    Each record has the old helper's exact request_id/case_id/dossier/response
    schema. The caller verifies both 100-cell model grids, unchanged native
    outputs and a combined source seal. None preserves a missing outcome; an
    empty string preserves an actual empty generation. No model/condition label
    is displayed. The separate wrapper receipt is aggregate/hash-only and may
    be public; the helper receipt and mapping remain separate private files.
    """
    if (not isinstance(records, list) or len(records) != 200 or
            any(not isinstance(row, dict) or not isinstance(row.get("case_id"), str)
                for row in records)):
        raise ValueError("Exactly 200 caller-sealed allocated records required")
    cases = Counter(row["case_id"] for row in records)
    if len(cases) != 10 or set(cases.values()) != {20}:
        raise ValueError("Exactly ten cases with twenty records per common dossier required")
    receipt = Path(receipt).resolve()
    others = [legacy.private_path(value) for value in (delivery, protected_mapping, helper_receipt)]
    if receipt.exists() or any(receipt == item or receipt in item.parents or
                               item in receipt.parents for item in others):
        raise ValueError("Separate new wrapper receipt required; no overwrite or delivery inclusion")
    bindings = _bindings()
    with _scope():
        legacy.build_package(records, delivery, protected_mapping, helper_receipt,
                             sealed_source_sha256=sealed_source_sha256,
                             dossiers_redacted=dossiers_redacted)
    result = {"schema": RECEIPT_SCHEMA, "records": 200, "cases": 10,
              "human_labels_created": 0, "mapping_in_delivery": False,
              "sealed_source_sha256": sealed_source_sha256,
              "helper_receipt_sha256": legacy.prior.sha256(helper_receipt),
              "generated_outcomes": sum(row["response"] is not None for row in records),
              "missing_outcomes": sum(row["response"] is None for row in records),
              "caller_verified": "Both frozen 100-cell model allocations and common redacted dossiers",
              **bindings}
    legacy.prior.write_exclusive(receipt, legacy.json_bytes(result))
    return result


def load_package(delivery, helper_receipt, receipt):
    """Only delivery, receipts and frozen local source/rubric/protocol are read."""
    doc = legacy.prior.load_json_bytes(Path(receipt).read_bytes())
    if (doc.get("schema") != RECEIPT_SCHEMA or doc.get("records") != 200 or
            doc.get("cases") != 10 or doc.get("human_labels_created") != 0 or
            doc.get("mapping_in_delivery") is not False or
            any(doc.get(key) != value for key, value in _bindings().items()) or
            doc.get("helper_receipt_sha256") != legacy.prior.sha256(legacy.private_path(helper_receipt))):
        raise ValueError("Wrapper receipt, helper receipt or frozen source bindings changed")
    with _scope():
        package = legacy.load_package(delivery, helper_receipt)
    original = package["receipt"]
    if (len(package["rows"]) != 200 or original["adapter_sha256"] != doc["helper_sha256"] or
            original["sealed_source_sha256"] != doc["sealed_source_sha256"] or
            sum(row["outcome_status"] == "GENERATED" for row in package["rows"]) != doc["generated_outcomes"] or
            sum(row["outcome_status"] == "MISSING_OUTCOME" for row in package["rows"]) != doc["missing_outcomes"]):
        raise ValueError("Fixed allocation or sealed source receipt mismatch")
    return package


def decode_csv(content):
    with _scope():
        return legacy.decode_csv(content)


def validate_submission(package, content, final=False):
    counts = {"assigned": 200, "finalized": 0, "completed": 0,
              "unavailable": 0, "not_started": 0}
    coverage = {name: {"numeric": 0, "na": 0, "blank": 0} for name in PRIMARY}
    result = {"counts": counts, "domain_coverage": coverage, "errors": [], "warnings": []}
    try:
        rows = decode_csv(content)
    except (UnicodeDecodeError, ValueError, csv.Error) as exc:
        result["errors"].append(legacy.prior.issue("CSV_INVALID", str(exc)))
        return result
    if len(rows) != 200 or len(package["rows"]) != 200:
        result["errors"].append(legacy.prior.issue("FIXED_RECORD_SET_REQUIRED", "Retain all 200 allocated rows exactly once."))
        return result
    for number, (row, original) in enumerate(zip(rows, package["rows"]), 1):
        invalid, incomplete = [], []
        expected = legacy.csv_display(original)
        if any(row[key] != expected[key] for key in IMMUTABLE):
            invalid.append("Immutable source cells or fixed record order changed")
        for name in PRIMARY:
            value = row[name]
            if value and value not in SCHEMA["ratings"]:
                invalid.append("Expected an exact ordinal category 0..5 or NA: " + name)
        status = row["annotation_status"]
        if status == "UNAVAILABLE":
            counts["unavailable"] += 1
            if not row["missing_reason"].strip():
                incomplete.append("UNAVAILABLE requires a truthful missing_reason")
            if any(row[name].strip() for name in PRIMARY):
                invalid.append("UNAVAILABLE ratings must stay blank, never zero or NA")
        elif status == "COMPLETED":
            if original["outcome_status"] == "MISSING_OUTCOME":
                invalid.append("MISSING_OUTCOME must remain UNAVAILABLE, not a rated empty generation")
            if row["missing_reason"].strip():
                invalid.append("COMPLETED requires blank missing_reason")
            if any(not row[name] for name in PRIMARY):
                incomplete.append("COMPLETED requires all three numeric or NA entries")
            if any(row[name] == "NA" for name in PRIMARY) and not row["rationale"].strip():
                incomplete.append("Each NA requires a truthful domain-specific reason in rationale")
        else:
            if status:
                invalid.append("Invalid annotation_status")
            incomplete.append("Record is not finalized")
        if all(not row[name].strip() for name in EDITABLE):
            counts["not_started"] += 1
        if not invalid and not incomplete:
            counts["finalized"] += 1
            counts["completed"] += int(status == "COMPLETED")
            for name in PRIMARY:
                coverage[name]["blank" if status == "UNAVAILABLE" else
                               "na" if row[name] == "NA" else "numeric"] += 1
        result["errors"].extend(legacy.prior.issue("ROW_INVALID", text, row=number,
                                                    blind_record_id=original["review_id"]) for text in invalid)
        target = result["errors"] if final else result["warnings"]
        target.extend(legacy.prior.issue("ROW_INCOMPLETE", text, row=number,
                                         blind_record_id=original["review_id"]) for text in incomplete)
    return result


def validate_provenance(value, content):
    checked = legacy.validate_provenance(value, content)
    for key in ("prior_rubric_or_item_involvement", "prior_exposure_to_outputs"):
        if value.get(key) != "YES":
            checked["errors"].append("Known PI involvement and exposure to the older 100-output package cannot be denied: " + key)
    if checked["errors"]:
        checked["classification"] = None
    return checked


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate-draft", "validate-final"))
    for name in ("delivery", "helper-receipt", "receipt", "submission", "feedback"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--provenance", type=Path)
    args = parser.parse_args(argv)
    package = load_package(args.delivery, args.helper_receipt, args.receipt)
    content = legacy.private_path(args.submission).read_bytes()
    final = args.action == "validate-final"
    result = validate_submission(package, content, final)
    if final:
        if args.provenance is None:
            result["errors"].append(legacy.prior.issue("PROVENANCE_REQUIRED", "Truthful actual provenance required; do not invent dates or aids."))
        else:
            value = legacy.prior.load_json_bytes(legacy.private_path(args.provenance).read_bytes())
            result["provenance"] = validate_provenance(value, content)
            result["errors"].extend(legacy.prior.issue("PROVENANCE_INVALID", text)
                                     for text in result["provenance"]["errors"])
    result.update(status="NOT_READY" if result["errors"] else
                  "READY_FOR_LOCK_NOT_LOCKED" if final else "DRAFT_VALID",
                  submission_sha256=legacy.prior.sha256_bytes(content),
                  protected_mapping_opened=False, unblinding_authorized=False,
                  official_lock_created=False, human_labels_created=0)
    legacy.prior.write_exclusive(legacy.private_path(args.feedback), legacy.json_bytes(result))
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "errors": len(result["errors"]), "warnings": len(result["warnings"])}, sort_keys=True))
    return int(bool(result["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
