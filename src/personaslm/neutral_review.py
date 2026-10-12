"""Versioned researcher forms; importing a form never manufactures human ratings."""
import argparse
import csv
import hashlib
from datetime import datetime
import json
from pathlib import Path

from .journal import atomic_json, utc_now
from .provenance import fingerprint, require_local_path, sha256

VERSION = "neutral_annotation_form_v3"
RATINGS = ("answer_leakage", "additional_factual_information", "contradictory_information",
           "temporal_interference", "unintended_linguistic_style", "semantic_neutrality")
EDITABLE = (*RATINGS, "reviewer_notes", "reviewer_id", "reviewed_utc")
VALUES = {"PASS", "FAIL", "UNCERTAIN"}


def make_packet(frozen, source_sha256):
    items = []
    for row in sorted(frozen["rows"], key=lambda r: (r["case_id"], r["neutral_condition"])):
        case_id, condition = row["case_id"], row["neutral_condition"]
        p = frozen["prompts"][case_id][condition]["prompt"]
        ref = frozen["prompts"][case_id][row["reference_condition"]]["prompt"]
        assert row["token_difference"] == 0 and p["evidence_block"] == ref["evidence_block"]
        item = {"form_version": VERSION, "language": "en", "case_id": case_id, "condition_id": condition,
            "neutral_text": p["additions"][0], "reference_condition": row["reference_condition"],
            "token_count": row["neutral_token_count"], "reference_token_count": row["reference_token_count"],
            "token_difference": row["token_difference"], "prompt_template_version": row["prompt_template_version"],
            "trusted_evidence": p["evidence_block"],
            "current_question": p["text"].rsplit("\n\nUser: ", 1)[1].removesuffix("\nAssistant:"),
            "prompt_sha256": hashlib.sha256(p["text"].encode("utf-8")).hexdigest(), "trusted_evidence_hash": row["trusted_evidence_hash"]}
        assert p["text"].rsplit("\n\nUser: ", 1)[1] == ref["text"].rsplit("\n\nUser: ", 1)[1]
        item["material_sha256"] = fingerprint(item)
        item.update({field: "" for field in EDITABLE})
        items.append(item)
    assert len(items) == 40 and len({(r["case_id"], r["condition_id"]) for r in items}) == 40
    packet = {"form_version": VERSION, "source_freeze_sha256": source_sha256, "items": items,
              "blinding": "unblinded condition/case identifiers, as requested; no model outputs or scores supplied",
              "token_count_scope": "entire final prompt, not neutral_text alone", "human_reviews_completed": 0}
    packet["packet_id"] = fingerprint(packet)
    return packet


def export_form(frozen_path, output_prefix):
    frozen_path, output_prefix = require_local_path(frozen_path), require_local_path(output_prefix)
    packet = make_packet(json.loads(frozen_path.read_text(encoding="utf-8")), sha256(frozen_path))
    json_path, csv_path = output_prefix.with_suffix(".json"), output_prefix.with_suffix(".csv")
    if json_path.exists() or csv_path.exists():
        raise FileExistsError("Form versions are immutable; choose a new output prefix")
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(json_path, packet)
    with csv_path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(packet["items"][0]))
        writer.writeheader()
        writer.writerows(packet["items"])
    return packet


def import_review(template_path, submitted_path, output_path, review_round):
    template_path, submitted_path, output_path = map(require_local_path, (template_path, submitted_path, output_path))
    if output_path.exists():
        raise FileExistsError("Never overwrite an imported review")
    template = json.loads(template_path.read_text(encoding="utf-8"))
    unsigned = {k: v for k, v in template.items() if k != "packet_id"}
    if template.get("form_version") != VERSION or fingerprint(unsigned) != template.get("packet_id"):
        raise ValueError("Template version or digest mismatch")
    if not isinstance(review_round, str) or not review_round.strip():
        raise ValueError("A review-round identifier is required")
    with submitted_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_fields = set(template["items"][0])
        if reader.fieldnames is None or len(reader.fieldnames) != len(expected_fields) or set(reader.fieldnames) != expected_fields:
            raise ValueError("CSV schema differs from the locked form")
        rows = list(reader)
    expected = {(r["case_id"], r["condition_id"]): r for r in template["items"]}
    seen, reviewed = set(), []
    for row in rows:
        if set(row) != expected_fields:
            raise ValueError("CSV row has extra fields")
        key = (row.get("case_id"), row.get("condition_id"))
        if key not in expected or key in seen:
            raise ValueError("Unknown or duplicate review item")
        seen.add(key)
        original = expected[key]
        if any(row.get(k) != str(v) for k, v in original.items() if k not in EDITABLE):
            raise ValueError("Immutable annotation material changed")
        if not any(row.get(k) for k in EDITABLE):
            continue
        if any(row.get(k) not in VALUES for k in RATINGS):
            raise ValueError("Reviewed items require six PASS/FAIL/UNCERTAIN ratings")
        if not row.get("reviewer_id", "").strip():
            raise ValueError("Missing reviewer ID")
        when = datetime.fromisoformat(row.get("reviewed_utc", ""))
        if when.tzinfo is None or when.utcoffset().total_seconds() != 0:
            raise ValueError("Review time must be an explicit UTC timestamp")
        reviewed.append(row)
    if seen != set(expected):
        raise ValueError("Keep every item in the form; leave unreviewed rows blank")
    if not reviewed:
        raise ValueError("No completed review items; no human judgments imported")
    result = {"schema_version": VERSION, "packet_id": template["packet_id"], "review_round": review_round,
        "imported_utc": utc_now(), "template_sha256": sha256(template_path), "submission_sha256": sha256(submitted_path),
        "submission_utf8": submitted_path.read_bytes().decode("utf-8-sig"), "completed": len(reviewed),
        "remaining": len(expected)-len(reviewed), "reviews": reviewed,
        "provenance_note": "Imported reviewer-supplied ratings; software validates structure, not reviewer identity or human authenticity. No automatic adjudication."}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(output_path, result)
    return result


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="stage", required=True)
    export = sub.add_parser("export")
    export.add_argument("--freeze", type=Path, required=True)
    export.add_argument("--output-prefix", type=Path, required=True)
    ingest = sub.add_parser("import")
    ingest.add_argument("--template", type=Path, required=True)
    ingest.add_argument("--input", type=Path, required=True)
    ingest.add_argument("--output", type=Path, required=True)
    ingest.add_argument("--review-round", required=True)
    args = parser.parse_args()
    if args.stage == "export":
        result = export_form(args.freeze, args.output_prefix)
        print(json.dumps({"packet_id": result["packet_id"], "items": len(result["items"]), "human_reviews_completed": 0}))
    else:
        result = import_review(args.template, args.input, args.output, args.review_round)
        print(json.dumps({"completed": result["completed"], "remaining": result["remaining"], "review_round": result["review_round"]}))


if __name__ == "__main__":
    main()
