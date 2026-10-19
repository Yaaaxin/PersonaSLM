"""Create additive reviewer-safe instructions without changing frozen RPC records."""

import json
from pathlib import Path

import real_persona_chat_sfh_review_v1 as original


PUBLIC = original.REPO / "docs/validation/p1/real_persona_chat_sfh_pilot_v1/human_review_delivery_protocol_v1_1.json"
DELIVERY = original.ROOT / "stage_a_delivery_v1_1"
QUESTIONNAIRE = "reviewer_exposure_questionnaire_v1_1_TEMPLATE.json"


def sanitized_protocol(spec):
    reviewer_keys = ("minimum_qualification", "judgment_policy", "relationship_enum",
                     "exposure_enum", "single_reviewer_limit")
    return {
        "schema_version": "personaslm_rpc_review_delivery_correction_v1_1",
        "status": "ADDITIVE_PRE_REVIEW_CORRECTION_NO_HUMAN_LABELS",
        "source_protocol_sha256": original.PROTOCOL_SHA256,
        "records_required": 64,
        "preservation": "The original protocol, delivery instructions, receipt, template, working copy, and protected map are preserved. This correction changes delivery guidance only; response text, evidence panels, row order, opaque IDs, rubric, and the 64-record requirement are unchanged.",
        "delivery_safety": "Use only the corrected delivery directory. Do not open the old delivery instructions, analyst protocol, construction code, protected map, or automatic results during review. No construction parameters or assignment information are included here.",
        "exposure_warning": "The original instructions contained material capable of revealing masked assignments. Removing that material from this new delivery cannot undo previous exposure. Zero completed labels does not establish that the reviewer has not seen it.",
        "reviewer": {key: spec["reviewer"][key] for key in reviewer_keys},
        "schema": spec["schema"],
        "exposure_questionnaire": {
            "file": QUESTIONNAIRE,
            "minimum_action": "Before judging responses, answer the separate blank questionnaire truthfully, including Japanese competence and any earlier viewing of the old instructions, analyst protocol, construction code, mapping, outputs, or automatic assessments. Save a new local copy; do not edit the template. If unsure, use UNCERTAIN rather than NO.",
            "project_role": "A principal researcher or project member cannot claim project independence. One reviewer cannot establish inter-rater reliability or independent experimental validation.",
            "legacy_provenance_mapping": "YES or UNCERTAIN for prior_assignment_key_material_exposure must be treated as corresponding mapping exposure in any later original-v1 provenance record. It cannot receive a clean masked-review classification. Prior rubric/item involvement, output exposure, and automatic-label exposure remain separate truthful attestations.",
            "japanese_qualification": "Do not begin original-Japanese semantic judgments without a truthful Japanese-competence attestation. AI-generated labels or machine translations cannot substitute for eligible original-Japanese human-only judgments.",
        },
        "workflow": [
            "Read these corrected instructions and complete the exposure questionnaire before annotation.",
            "Edit only the designated annotation columns of stage_a_WORKING_COPY.csv in this corrected directory. Save incrementally; retain all 64 rows.",
            "Run the existing real_persona_chat_sfh_review_v1.py validate-draft action with --submission pointing to the corrected working copy. The original frozen package remains its structural reference; this checks CSV integrity without creating labels or opening the mapping.",
            "After all rows are finalized, preserve the exact CSV, completed questionnaire, and truthful original-v1 provenance as separate versioned submissions. Any later intake must additionally bind this corrected protocol, instructions, receipt, and questionnaire.",
            "Existing v1 final validation alone does not attest this new delivery/provenance chain, create a seal, or authorize unblinding. These remain explicit later steps after genuine review.",
        ],
        "claim_limits": "Developmental descriptive semantic review only. Report exposure limitations and applicability. No result or Japanese competence is asserted by preparing this package.",
        "human_labels_created": 0,
        "protected_mapping_opened": False,
    }


def blank_questionnaire():
    return {
        "schema_version": "personaslm_rpc_reviewer_exposure_questionnaire_v1_1",
        "status": "BLANK_HUMAN_ATTESTATIONS_REQUIRED",
        "reviewer_pseudonym": "",
        "human_reviewer": None,
        "relationship": None,
        "independent_of_project": None,
        "japanese_competence_attested": None,
        "japanese_competence_description": "",
        "prior_assignment_key_material_exposure": None,
        "prior_rubric_or_item_involvement": None,
        "prior_exposure_to_outputs": None,
        "automatic_or_ai_labels_seen_before_lock": None,
        "ai_assistance_used_for_judgments": None,
        "machine_translation_used_for_judgments": None,
        "review_environment": "",
        "aids_used": "",
        "review_started_utc": None,
        "attestation_recorded_utc": None,
        "notes": "",
        "answer_guidance": "Exposure/assistance: NO, YES, or UNCERTAIN. Human/independence/competence: true or false. Supply truthful project relationship and Japanese-competence basis. Timestamps must reflect actual recorded events, not estimates invented after the fact.",
    }


def prepare():
    package = original.load_package()
    safe = sanitized_protocol(package["spec"])
    if PUBLIC.read_bytes() != original.json_bytes(safe):
        raise ValueError("Public corrected protocol differs from the deterministic reviewer-only projection")
    preserved = (original.PROTOCOL, original.TEMPLATE, original.WORKING,
                 original.INSTRUCTIONS, original.RECEIPT)
    before = {str(path.relative_to(original.REPO)): original.prior.sha256(path) for path in preserved}
    working = original.WORKING.read_bytes()
    check = original.validate_submission(package, working)
    if check["errors"] or check["counts"] != {"finalized": 0, "in_progress": 0, "not_started": 64}:
        raise ValueError("Correction requires the verified untouched 64-row blank working copy; preserve any genuine edits for separate intake")
    blobs = {
        "stage_a_REVIEW_TEMPLATE.csv": package["template_bytes"],
        "stage_a_WORKING_COPY.csv": working,
        "stage_a_REVIEW_INSTRUCTIONS_v1_1.json": original.json_bytes(safe),
        QUESTIONNAIRE: original.json_bytes(blank_questionnaire()),
    }
    receipt = {
        "schema_version": "personaslm_rpc_review_delivery_correction_receipt_v1_1",
        "status": "BLANK_CORRECTED_DELIVERY_PREPARED_NOT_REVIEWED",
        "original_artifact_sha256": before,
        "corrected_protocol_sha256": original.prior.sha256(PUBLIC),
        "correction_tool_sha256": original.prior.sha256(Path(__file__)),
        "files": {name: {"sha256": original.prior.sha256_bytes(content), "bytes": len(content)}
                  for name, content in blobs.items()},
        "records": 64, "human_labels": 0, "reviewer_exposure_status": "UNKNOWN_PENDING_TRUTHFUL_ATTESTATION",
        "original_csv_bytes_unchanged": True, "protected_mapping_opened": False,
        "official_seal_created": False, "unblinding_authorized": False,
    }
    blobs["delivery_correction_receipt_v1_1.json"] = original.json_bytes(receipt)
    if DELIVERY.exists():
        raise FileExistsError("Corrected delivery already exists; no overwrite")
    original.private_path(DELIVERY / "stage_a_WORKING_COPY.csv")
    for name, content in blobs.items():
        original.prior.write_exclusive(DELIVERY / name, content)
    if before != {str(path.relative_to(original.REPO)): original.prior.sha256(path) for path in preserved}:
        raise ValueError("Original artifacts changed concurrently; retain correction but do not deliver")
    return {"status": receipt["status"], "records": 64, "human_labels": 0,
            "original_artifacts_preserved": True, "protected_mapping_opened": False,
            "working_copy": str(DELIVERY / "stage_a_WORKING_COPY.csv"),
            "receipt_sha256": original.prior.sha256(DELIVERY / "delivery_correction_receipt_v1_1.json")}


if __name__ == "__main__":
    print(json.dumps(prepare(), indent=2))
