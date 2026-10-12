"""Quote-supported follow-up review, distinct from completed human annotation."""
import argparse
import csv
from datetime import datetime
import json
from pathlib import Path

from .journal import atomic_json, utc_now
from .neutral_review import RATINGS
from .provenance import fingerprint, require_local_path, sha256

VERSION = "neutral_control_resolution_v1"
QUOTES = tuple(k + "_evidence_quote" for k in RATINGS)
EDITABLE = (*RATINGS, *QUOTES, "reviewer_notes", "reviewer_id", "reviewed_utc")


def validate_resolution(template, rows, fields):
    if template.get("version") != VERSION or fingerprint(
            {k:v for k,v in template.items() if k != "packet_id"}) != template.get("packet_id"):
        raise ValueError("Resolution template version or hash differs")
    expected = {(r["case_id"], r["condition_id"]):r for r in template["items"]}
    if len(expected) != len(template["items"]):
        raise ValueError("Duplicate template rows")
    if len(fields) != len(set(fields)) or set(fields) != set(template["items"][0]):
        raise ValueError("Invalid resolution schema")
    reviewed, seen = [], set()
    for row in rows:
        key = row["case_id"], row["condition_id"]
        if key not in expected or key in seen or set(row) != set(fields) or any(v is None for v in row.values()):
            raise ValueError("Duplicate, unknown or malformed resolution row")
        seen.add(key)
        material = expected[key]
        if any(str(row[k]).replace("\r\n", "\n") != str(v).replace("\r\n", "\n")
               for k,v in material.items() if k not in EDITABLE):
            raise ValueError("Resolution material changed")
        if not any(row[k] for k in EDITABLE):
            continue
        if any(row[k] not in {"PASS", "FAIL", "UNCERTAIN"} for k in RATINGS):
            raise ValueError("Complete all six dimensions")
        if not row["reviewer_id"].strip():
            raise ValueError("Missing reviewer ID")
        when = datetime.fromisoformat(row["reviewed_utc"])
        if when.tzinfo is None or when.utcoffset().total_seconds() != 0:
            raise ValueError("Supply actual UTC review time")
        supplied_text = "\n".join(material[k] for k in (
            "neutral_text", "trusted_evidence", "current_question", "reference_conditioning_text"))
        for field in RATINGS:
            quote = row[field + "_evidence_quote"].replace("\r\n", "\n")
            if row[field] in {"FAIL", "UNCERTAIN"} and not quote.strip():
                raise ValueError("Quote evidence for every failure or uncertainty")
            if quote and quote not in supplied_text:
                raise ValueError("Evidence quotation is absent from supplied material")
        reviewed.append(row)
    if seen != set(expected):
        raise ValueError("Keep all resolution rows")
    return reviewed


def import_resolution(template_path, input_path, output_path):
    template_path, input_path, output_path = map(require_local_path, (template_path, input_path, output_path))
    if output_path.exists():
        raise FileExistsError("Use a new version; never overwrite a review")
    template = json.loads(template_path.read_text(encoding="utf-8"))
    with input_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames or [], list(reader)
    reviews = validate_resolution(template, rows, fields)
    if not reviews:
        raise ValueError("No completed follow-up reviews")
    result = {"version": VERSION, "imported_utc": utc_now(), "packet_id": template["packet_id"],
        "template_sha256": sha256(template_path), "submission_sha256": sha256(input_path),
        "submission_utf8": input_path.read_bytes().decode("utf-8-sig"), "completed": len(reviews),
        "remaining": len(rows)-len(reviews), "reviews": reviews,
        "scope": "Follow-up ratings only; no automatic adjudication or replacement of original researcher annotations"}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(output_path, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("template", "input", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = import_resolution(args.template, args.input, args.output)
    print(json.dumps({"completed": result["completed"], "remaining": result["remaining"]}))
