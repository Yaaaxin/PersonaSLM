"""Immutable imports for new development materials, separate from old reviews."""
import argparse
import csv
from datetime import datetime
import json
from pathlib import Path

from .journal import atomic_json, utc_now
from .neutral_review import RATINGS as CORE_RATINGS
from .provenance import fingerprint, require_local_path, sha256

VERSION = "control_development_review_v2"
HISTORY_RATINGS = ("speaker_identity", "dialogue_structure", "timestamp_format", "topic_alignment", "temporal_relationships")
RATINGS = (*CORE_RATINGS, "unnecessary_repetition", *HISTORY_RATINGS, "conversational_coherence", "comparison_suitability")
EDITABLE = (*RATINGS, *(k + "_evidence_quote" for k in RATINGS),
            "reviewer_id", "reviewed_utc", "reviewer_notes", "review_assistance")


def validate_packet(template, rows, fields):
    if template.get("version") != VERSION or fingerprint(
            {k: v for k, v in template.items() if k != "packet_id"}) != template.get("packet_id"):
        raise ValueError("Template version or digest differs")
    items = template.get("items", [])
    if not items:
        raise ValueError("Empty review template")
    expected = {(r["case_id"], r["condition_id"]): r for r in items}
    if len(expected) != len(items) or len(fields) != len(set(fields)) or set(fields) != set(items[0]):
        raise ValueError("Duplicate material or invalid schema")
    reviewed, seen = [], set()
    for row in rows:
        if set(row) != set(fields) or any(not isinstance(v, str) for v in row.values()):
            raise ValueError("Malformed review row")
        key = row["case_id"], row["condition_id"]
        if key not in expected or key in seen:
            raise ValueError("Duplicate or unknown review item")
        seen.add(key)
        item = expected[key]
        norm = lambda v: str(v).replace("\r\n", "\n")
        if any(norm(row[k]) != norm(v) for k, v in item.items() if k not in EDITABLE):
            raise ValueError("Frozen review material changed")
        if not any(row[k] for k in EDITABLE):
            continue
        for field in RATINGS:
            allowed = {"PASS", "FAIL", "UNCERTAIN"}
            if (item["family"] == "style_generic" and field in HISTORY_RATINGS) or (
                    item["family"] == "history_stale_generalized" and field == "semantic_neutrality"):
                allowed.add("NOT_APPLICABLE")
            if row[field] not in allowed:
                raise ValueError("Missing or invalid judgment: " + field)
        if not row["reviewer_id"].strip():
            raise ValueError("Reviewer identifier required")
        if row["review_assistance"] not in {"unassisted", "AI-assisted", "other-assisted"}:
            raise ValueError("Declare review assistance")
        # Review time is optional; do not ask anyone to invent a missing time.
        if row["reviewed_utc"]:
            when = datetime.fromisoformat(row["reviewed_utc"])
            if when.tzinfo is None or when.utcoffset().total_seconds() != 0:
                raise ValueError("If supplied, review time must have UTC offset")
        texts = "\n".join(item[k] for k in ("neutral_text", "reference_conditioning_text", "trusted_evidence", "current_question"))
        for field in RATINGS:
            quote = norm(row[field + "_evidence_quote"])
            if row[field] in {"FAIL", "UNCERTAIN"} and not quote.strip():
                raise ValueError("Quote the evidence for failure or uncertainty")
            if quote and quote not in texts:
                raise ValueError("Evidence quotation not in supplied material")
        reviewed.append(row)
    if seen != set(expected):
        raise ValueError("Keep the full review inventory")
    return reviewed


def import_review(template_path, input_path, output_path):
    template_path, input_path, output_path = map(require_local_path, (template_path, input_path, output_path))
    if output_path.exists():
        raise FileExistsError("Choose a new immutable review output")
    template = json.loads(template_path.read_text(encoding="utf-8"))
    with input_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames or [], list(reader)
    reviewed = validate_packet(template, rows, fields)
    if not reviewed:
        raise ValueError("No completed human reviews supplied")
    result = {"version": VERSION, "imported_utc": utc_now(), "packet_id": template["packet_id"],
              "template_sha256": sha256(template_path), "submission_sha256": sha256(input_path),
              "submission_utf8": input_path.read_text(encoding="utf-8-sig"),
              "completed": len(reviewed), "remaining": len(rows) - len(reviewed), "reviews": reviewed,
              "scope": "New development candidates only; no automatic acceptance or reuse of historical annotations"}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(output_path, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("template", "input", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = import_review(args.template, args.input, args.output)
    print(json.dumps({"completed": result["completed"], "remaining": result["remaining"]}))
