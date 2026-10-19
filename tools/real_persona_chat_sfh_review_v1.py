"""Private 64-row RPC review adapter; validation never opens the condition map."""

import argparse
import csv
import io
import json
from pathlib import Path

import p1_persona_dialogue_disjoint_surface_validation_review_v4 as prior


REPO = Path(__file__).resolve().parents[1]
PROTOCOL = REPO / "docs/validation/p1/real_persona_chat_sfh_pilot_v1/human_review_protocol_v1.json"
PROTOCOL_SHA256 = "a9be9c934d1fb09cbbe62f3d5d54930a9b2558a5e8ac2609c2fcb4382cc5e3d0"
ROOT = REPO / ".local/reviewer-packages/real_persona_chat_sfh_pilot_v1"
DELIVERY = ROOT / "stage_a_delivery"
TEMPLATE = DELIVERY / "stage_a_REVIEW_TEMPLATE.csv"
WORKING = DELIVERY / "stage_a_WORKING_COPY.csv"
INSTRUCTIONS = DELIVERY / "stage_a_REVIEW_INSTRUCTIONS.json"
RECEIPT = DELIVERY / "stage_a_package_receipt.json"
MAPPING = ROOT / "protected/stage_a_mapping.json"
MISSING_RESPONSE = "[GENERATION_UNAVAILABLE]"


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def encode_csv(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8-sig")


def private_path(path):
    path = Path(path).resolve()
    if (REPO / ".local").resolve() not in path.parents:
        raise ValueError("Review artifacts must remain under ignored .local")
    if (ROOT / "protected").resolve() in path.parents:
        raise ValueError("Review actions may not read or write the protected mapping directory")
    return path


def protocol():
    if prior.sha256(PROTOCOL) != PROTOCOL_SHA256:
        raise ValueError("Frozen 64-row review protocol changed")
    return prior.load_json_bytes(PROTOCOL.read_bytes())


def order_requests(requests, seed):
    digest = lambda domain, value: prior.sha256_bytes(f"{seed}|{domain}|{value}".encode())
    cases = sorted({row["case_id"] for row in requests}, key=lambda value: digest("case", value))
    conditions = sorted({row["condition"] for row in requests}, key=lambda value: digest("condition", value))
    lookup = {(row["case_id"], row["condition"]): row for row in requests}
    if len(requests) != 64 or len(lookup) != 64 or len(cases) != 8 or set(conditions) != {f"C{i}" for i in range(8)}:
        raise ValueError("Expected eight cases crossed with all eight conditions")
    return [lookup[case, conditions[(round_number + index) % 8]]
            for round_number in range(8) for index, case in enumerate(cases)]


def prepare():
    import real_persona_chat_sfh_pilot_execution_v1 as execution
    import real_persona_chat_sfh_pilot_execution_amendment_v1_1 as amended
    import real_persona_chat_sfh_pilot_v1 as material_tool

    spec = protocol()
    if any(path.exists() for path in (TEMPLATE, WORKING, INSTRUCTIONS, RECEIPT, MAPPING)):
        raise ValueError("Review package already exists or construction is incomplete; no overwrite")
    with amended._analysis_paths():
        public, private = execution.analyze(write=False)
    material = execution.load(execution.PRIVATE_MATERIAL)
    expected = spec["bindings"]
    for name, path in (("design_sha256", execution.DESIGN),
                       ("materialization_receipt_sha256", execution.MATERIAL_RECEIPT),
                       ("private_material_sha256", execution.PRIVATE_MATERIAL)):
        if prior.sha256(path) != expected[name]:
            raise ValueError("Frozen review/source binding changed")
    material_tool.verify_live_source(material["dataset_root"])
    _, dialogues, split_hash, _ = material_tool.load_development_view(material["dataset_root"])
    if split_hash != material["split_assignment_sha256"]:
        raise ValueError("Development speaker split changed")
    dialogues = {row["dialogue_id"]: row for row in dialogues}
    cases = {row["case_id"]: row for row in material["cases"]}
    results = {row["request_id"]: row for row in private["rows"]}
    panels = {}
    for case_id, case in cases.items():
        examples, count = [], 0
        for number, dialogue_id in enumerate(case["source_dialogue_ids"], 1):
            record = material_tool._dialogue_record(dialogues[dialogue_id], case["speaker_id"])
            if record is None:
                raise ValueError("Source dialogue chronology unavailable")
            examples.append(f"Earlier dialogue {number}:\n" + "\n".join(record["speaker_turns"]))
            count += len(record["speaker_turns"])
        if count != case["style_source_turn_count"]:
            raise ValueError("Frozen source-turn allocation changed")
        history = "\n".join(("匿名話者" if turn["interlocutor_id"] == case["speaker_id"] else "相手") +
                            ": " + turn["text"] for turn in case["history"])
        panels[case_id] = {
            "task_instruction": "最後の相手の発話に続く自然な返答を評価してください。実在人物の特定はしないでください。",
            "current_partner_query": case["query"]["text"],
            "preceding_dialogue": history,
            "participant_self_statements": "Self-statements; temporal truth unknown.\n" + "\n".join(case["facts"]),
            "earlier_speaker_utterances": "\n\n".join(examples),
        }
    rows, mapping = [], []
    for number, request in enumerate(order_requests(material["requests"], spec["construction"]["order_seed"]), 1):
        result = results.get(request["request_id"], {})
        response = result.get("raw_response", MISSING_RESPONSE)
        row = {"blind_record_id": f"RPC-A-{number:03d}", **panels[request["case_id"]],
               "model_response": response, **{field: "" for field in spec["schema"]["editable_columns"]}}
        rows.append(row)
        mapping.append({"blind_record_id": row["blind_record_id"], "request_id": request["request_id"],
                        "case_id": request["case_id"], "condition": request["condition"],
                        "response_sha256": prior.sha256_bytes(response.encode("utf-8")),
                        "display_sha256": prior.sha256_bytes(json_bytes(row))})
    fields = spec["schema"]["immutable_columns"] + spec["schema"]["editable_columns"]
    template_bytes = encode_csv(rows, fields)
    instructions_bytes = json_bytes(spec)
    mapping_bytes = json_bytes({"privacy": "PROTECTED_DO_NOT_DELIVER_OR_OPEN_BEFORE_SEAL", "rows": mapping})
    folder, events, summary = execution._read_only_run()
    receipt = {
        "schema_version": "personaslm_rpc_sfh_review_package_v1", "records": 64,
        "human_labels": 0, "ai_labels": 0, "mapping_in_delivery": False,
        "template_sha256": prior.sha256_bytes(template_bytes),
        "instructions_sha256": prior.sha256_bytes(instructions_bytes),
        "protocol_sha256": PROTOCOL_SHA256, "mapping_sha256": prior.sha256_bytes(mapping_bytes),
        "adapter_sha256": prior.sha256(Path(__file__)),
        "source_bindings": {"execution_manifest_sha256": prior.sha256(amended.FROZEN),
                            "execution_integrity_amendment_sha256": prior.sha256(amended.AMENDMENT),
                            "run_summary_sha256": prior.sha256(folder / "summary.json"),
                            "journal_terminal_event_sha256": events[-1]["event_hash"],
                            "run_file_sha256": {path.name: prior.sha256(path) for path in sorted(folder.iterdir()) if path.is_file()},
                            **expected},
        "source_status": public["status"], "planned_slots": summary["planned_slots"],
        "opaque_id_order_sha256": prior.sha256_bytes(json_bytes([row["blind_record_id"] for row in rows])),
        "review_state": "BLANK_NOT_HUMAN_REVIEWED", "protected_mapping_opened": False,
    }
    for path, content in ((MAPPING, mapping_bytes), (TEMPLATE, template_bytes),
                          (INSTRUCTIONS, instructions_bytes), (WORKING, template_bytes),
                          (RECEIPT, json_bytes(receipt))):
        prior.write_exclusive(path, content)
    return {"status": "PRIVATE_64_ROW_BLANK_PACKAGE_CREATED", "records": 64,
            "working_copy": str(WORKING), "human_labels": 0, "protected_mapping_opened": False,
            "receipt_sha256": prior.sha256(RECEIPT)}


def load_package():
    spec = protocol()
    receipt = prior.load_json_bytes(RECEIPT.read_bytes())
    for key, path in (("template_sha256", TEMPLATE), ("instructions_sha256", INSTRUCTIONS),
                      ("protocol_sha256", PROTOCOL)):
        if receipt.get(key) != prior.sha256(path):
            raise ValueError("Review delivery hash mismatch")
    if receipt.get("records") != 64 or receipt.get("human_labels") != 0 or receipt.get("mapping_in_delivery") is not False:
        raise ValueError("Review receipt invariants changed")
    return {"spec": spec, "receipt": receipt, "template_bytes": TEMPLATE.read_bytes()}


def decode_csv(content, fields):
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
    if reader.fieldnames != fields:
        raise ValueError("Exact CSV header/order required")
    rows = list(reader)
    if len(rows) != 64 or any(None in row or None in row.values() for row in rows):
        raise ValueError("Exactly 64 records with no missing or overflow cells required")
    return rows


def validate_submission(package, content, final=False):
    schema = package["spec"]["schema"]
    fields = schema["immutable_columns"] + schema["editable_columns"]
    rows = decode_csv(content, fields)
    originals = decode_csv(package["template_bytes"], fields)
    errors, warnings = [], []
    counts = {"finalized": 0, "in_progress": 0, "not_started": 0}
    judgments = schema["editable_columns"][2:]
    for number, (row, original) in enumerate(zip(rows, originals), 1):
        row_errors, incomplete = [], []
        changed = [key for key in schema["immutable_columns"] if row[key] != original[key]]
        if changed:
            row_errors.append("Immutable cells changed: " + ", ".join(changed))
        for field, choices in schema["enums"].items():
            if row[field] and row[field] not in choices:
                row_errors.append("Invalid enum: " + field)
        span = row["evidence_span"]
        if span and span not in row["model_response"] and not (span == "NO_SUPPORTING_SPAN" and row["reviewer_rationale"].strip()):
            row_errors.append("Evidence span must be exact or a justified NO_SUPPORTING_SPAN")
        status = row["annotation_status"]
        if status == "UNAVAILABLE":
            if not row["missing_reason"].strip():
                incomplete.append("UNAVAILABLE requires missing_reason")
            if any(row[key].strip() for key in judgments):
                row_errors.append("UNAVAILABLE requires blank judgments")
        elif status == "COMPLETED":
            if row["model_response"] == MISSING_RESPONSE:
                row_errors.append("Missing generation must be UNAVAILABLE")
            if row["missing_reason"].strip():
                row_errors.append("COMPLETED requires blank missing_reason")
            missing = [key for key in judgments if not row[key].strip()]
            if missing:
                incomplete.append("Missing completed fields: " + ", ".join(missing))
        else:
            incomplete.append("Record is not finalized")
        state = "finalized" if not row_errors and not incomplete else "in_progress"
        if all(not row[key].strip() for key in schema["editable_columns"]):
            state = "not_started"
        counts[state] += 1
        errors.extend(prior.issue("ROW_INVALID", value, row=number, blind_record_id=original["blind_record_id"]) for value in row_errors)
        target = errors if final else warnings
        target.extend(prior.issue("ROW_INCOMPLETE", value, row=number, blind_record_id=original["blind_record_id"]) for value in incomplete)
    return {"records": 64, "counts": counts, "errors": errors, "warnings": warnings}


def provenance_skeleton(package, content):
    value = {key: None for key in package["spec"]["reviewer"]["provenance_required"]}
    for key in ("reviewer_pseudonym", "private_reviewer_identifier", "japanese_competence_description", "review_environment", "aids_used", "notes"):
        value[key] = ""
    value.update(template_sha256=prior.sha256_bytes(package["template_bytes"]),
                 instructions_sha256=prior.sha256(INSTRUCTIONS), protocol_sha256=PROTOCOL_SHA256,
                 source_receipt_sha256=prior.sha256(RECEIPT), completed_csv_sha256=prior.sha256_bytes(content))
    return value


def validate_provenance(package, content, value):
    required = package["spec"]["reviewer"]["provenance_required"]
    errors = []
    if set(value) != set(required):
        return {"errors": ["Provenance must contain exactly the required fields"]}
    for key in ("human_reviewer", "independent_of_project", "japanese_competence_attested"):
        if type(value[key]) is not bool:
            errors.append(key + " requires a human-supplied boolean")
    for key in ("reviewer_pseudonym", "private_reviewer_identifier", "japanese_competence_description", "review_environment", "aids_used"):
        if not isinstance(value[key], str) or not value[key].strip():
            errors.append(key + " requires truthful text")
    if not isinstance(value["notes"], str):
        errors.append("notes must be text")
    exposure = ("machine_translation_used_for_judgments", "prior_rubric_or_item_involvement", "prior_exposure_to_outputs",
                "condition_mapping_seen_before_lock", "automatic_or_ai_labels_seen_before_lock", "ai_assistance_used_for_judgments")
    if any(value[key] not in ("YES", "NO", "UNCERTAIN") for key in exposure):
        errors.append("All assistance/exposure fields require YES, NO, or UNCERTAIN")
    if value["relationship"] not in package["spec"]["reviewer"]["relationship_enum"]:
        errors.append("Invalid reviewer relationship")
    if value["independent_of_project"] is True and value["relationship"] != "INDEPENDENT_EXTERNAL":
        errors.append("Project member or principal researcher cannot attest project independence")
    try:
        if prior._parse_utc(value["started_utc"]) > prior._parse_utc(value["completed_utc"]):
            errors.append("Review UTC times out of order")
    except (TypeError, ValueError):
        errors.append("Explicit UTC review timestamps required")
    skeleton = provenance_skeleton(package, content)
    for key in ("template_sha256", "instructions_sha256", "protocol_sha256", "source_receipt_sha256", "completed_csv_sha256"):
        if value[key] != skeleton[key]:
            errors.append(key + " mismatch")
    classification = None
    if not errors:
        if value["human_reviewer"] is not True or value["japanese_competence_attested"] is not True or any(value[key] != "NO" for key in ("ai_assistance_used_for_judgments", "machine_translation_used_for_judgments")):
            classification = "INELIGIBLE_FOR_ORIGINAL_JAPANESE_HUMAN_ONLY_CLAIM"
            errors.append("Qualified original-Japanese human-only judgments are required")
        elif any(value[key] != "NO" for key in exposure[1:-1]):
            classification = "HUMAN_EXPOSURE_LIMITED"
        elif value["independent_of_project"] is True:
            classification = "CLEAN_INDEPENDENT_CONDITION_MASKED_HUMAN"
        else:
            classification = "CONDITION_MASKED_NONINDEPENDENT_HUMAN"
    return {"errors": errors, "classification": classification,
            "independent_experimental_validation": False, "inter_rater_reliability": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "init-copy", "validate-draft", "create-provenance", "validate-final"))
    parser.add_argument("--submission", type=Path, default=WORKING)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    if args.action == "prepare":
        report = prepare()
    else:
        package = load_package()
        submission = private_path(args.submission)
        if args.action == "init-copy":
            prior.write_exclusive(submission, package["template_bytes"])
            report = {"status": "EXACT_TEMPLATE_COPY_CREATED", "human_labels": 0}
        else:
            content = submission.read_bytes()
            final = args.action == "validate-final"
            report = validate_submission(package, content, final=final)
            if args.action == "create-provenance":
                if args.provenance is None:
                    parser.error("create-provenance requires --provenance")
                report = validate_submission(package, content, final=True)
                if report["errors"]:
                    report["status"] = "NOT_READY"
                else:
                    prior.write_exclusive(private_path(args.provenance), json_bytes(provenance_skeleton(package, content)))
                    report["status"] = "BLANK_HUMAN_ATTESTATIONS_CREATED"
            else:
                if final:
                    if args.provenance is None:
                        report["errors"].append(prior.issue("PROVENANCE_REQUIRED", "Truthful reviewer provenance required"))
                    else:
                        provenance = prior.load_json_bytes(private_path(args.provenance).read_bytes())
                        checked = validate_provenance(package, content, provenance)
                        report["provenance"] = checked
                        report["errors"].extend(prior.issue("PROVENANCE_INVALID", value) for value in checked["errors"])
                report["status"] = "NOT_READY" if report["errors"] else "READY_FOR_SEAL_NOT_SEALED" if final else "DRAFT_VALID"
            report["submission_sha256"] = prior.sha256_bytes(content)
    report.update(protected_mapping_opened=False, official_seal_created=False, unblinding_authorized=False)
    rendered = json_bytes(report)
    if args.report:
        prior.write_exclusive(private_path(args.report), rendered)
    print(rendered.decode("utf-8"))
    return int(report.get("status") == "NOT_READY")


if __name__ == "__main__":
    raise SystemExit(main())
