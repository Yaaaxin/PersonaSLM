"""Researcher attestations and a single proposed Tessa repair, without new answers."""
import base64
import json
from dataclasses import asdict

from .conditioning import build_prompt
from .control_closure import replacement_preserved, text_hash
from .control_final_review import RATINGS
from .schemas import Case

VERSION = "p0_scientific_closure_v1"
TESSA_TEXT = "No speaker-specific style information appears in this profile."
STYLE_SCOPE = "Specific linguistic-style profile versus explicit absence of style information; same wrapper and exactly matched total tokens. Not equivalent to C0."
HISTORY_SCOPE = "Length- and format-matched comparison between historical residence information and unrelated coherent historical dialogue."
STYLE_FIELDS = ["case_id", "candidate_id", "speaker_name", "active_style", "neutral_candidate", "trusted_evidence", "current_question",
                "reference_token_count", "candidate_token_count", "token_difference", *("ai_" + f for f in RATINGS),
                "ai_explanation", "human_final_review", "human_review_notes"]
HISTORY_FIELDS = ["case_id", "candidate_id", "axis", "prior_human_axis_judgment", "source_passage_active", "source_passage_candidate",
                  "exact_quote_match_active", "exact_quote_match_candidate", "ai_reading", "human_quote_association_verified", "human_notes"]


def _inventory(rows, expected, key):
    ids = [key(r) for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError("Missing, duplicate or unknown review items")


def register_reviews(style_fields, styles, history_fields, histories, style_master, evidence_master, attestation):
    """Record explicit researcher decisions; blank source cells remain verbatim."""
    if style_fields != STYLE_FIELDS or history_fields != HISTORY_FIELDS:
        raise ValueError("Unexpected researcher source schema")
    if not attestation.get("source_judgments_confirmed") or not attestation.get("history_associations_confirmed"):
        raise ValueError("Explicit researcher confirmation is required")
    if attestation.get("reviewer_id") != "Yaxin_ZHENG" or attestation.get("decision_source") != "researcher":
        raise ValueError("Missing researcher authority")
    sm = {r["candidate_id"]: r for r in style_master["items"]}
    hm = {(r["candidate_id"], r["field"]): r for r in evidence_master["items"]}
    _inventory(styles, sm, lambda r: r["candidate_id"])
    _inventory(histories, hm, lambda r: (r["candidate_id"], r["axis"]))
    style_records = []
    for row in styles:
        original = sm[row["candidate_id"]]
        mapping = {"active_style": "original_active_intervention", "neutral_candidate": "candidate_control_text"}
        for field in STYLE_FIELDS[:10]:
            if row[field].replace("\r\n", "\n") != original[mapping.get(field, field)].replace("\r\n", "\n"):
                raise ValueError("Reviewed style materials differ from the frozen master")
        ratings = {field: row["ai_" + field] for field in RATINGS}
        if any(label not in {"PASS", "FAIL", "UNCERTAIN", "NOT_APPLICABLE"} for label in ratings.values()):
            raise ValueError("Invalid recorded judgment")
        decision = attestation["style_decisions"][row["speaker_name"]]
        expected_decision = "REVISION_REQUIRED" if row["speaker_name"] == "Tessa" else "ACCEPT_NARROW"
        if decision != expected_decision:
            raise ValueError("Decision differs from the scope authorized for this registration version")
        if row["human_final_review"] and row["human_final_review"] != decision:
            raise ValueError("Source human decision conflicts with the supplied attestation")
        style_records.append({"candidate_id": row["candidate_id"], "case_id": row["case_id"], "speaker_name": row["speaker_name"],
            "researcher_decision": decision, "decision_provenance": "Explicit current researcher instruction, bound to the checked source item",
            "source_row_verbatim": row, "researcher_confirmed_source_judgments": ratings,
            "judgment_origin": "Preliminary AI-prefixed fields, subsequently confirmed by researcher; original field names retained",
            "prompt_sha256": original["prompt_sha256"], "permitted_scope": STYLE_SCOPE,
            "semantic_neutrality_not_overridden": ratings["semantic_neutrality"], "reviewed_utc": None})
    history_records = []
    for row in histories:
        original = hm[(row["candidate_id"], row["axis"])]
        checks = {"case_id": original["case_id"], "prior_human_axis_judgment": original["normalized_original_judgment"],
                  "source_passage_active": original["active_excerpt"]["quote"], "source_passage_candidate": original["candidate_excerpt"]["quote"],
                  "ai_reading": original["extraction_note"]}
        if any(row[k].replace("\r\n", "\n") != v.replace("\r\n", "\n") for k, v in checks.items()):
            raise ValueError("History source quotation, identity or original judgment changed")
        if row["exact_quote_match_active"] != "YES" or row["exact_quote_match_candidate"] != "YES":
            raise ValueError("Source reports a non-exact quotation")
        if row["human_quote_association_verified"] not in {"", "YES", "CONFIRM"}:
            raise ValueError("Source association conflicts with explicit confirmation")
        history_records.append({"evidence_id": original["evidence_id"], "candidate_id": row["candidate_id"],
            "case_id": row["case_id"], "axis": row["axis"], "researcher_confirmation": "CONFIRM",
            "confirmation_source": "Explicit current researcher instruction; source human cell preserved separately",
            "preserved_axis_judgment": row["prior_human_axis_judgment"], "source_row_verbatim": row,
            "active_excerpt": original["active_excerpt"], "candidate_excerpt": original["candidate_excerpt"], "reviewed_utc": None})
    if attestation.get("history_comparison_suitability") != "PASS" or attestation.get("history_decision") != "ACCEPT_NARROW":
        raise ValueError("Expected explicit narrow History A authority")
    decisions = []
    for cid in sorted({r["candidate_id"] for r in history_records}):
        axes = {r["axis"]: r["preserved_axis_judgment"] for r in history_records if r["candidate_id"] == cid}
        decisions.append({"candidate_id": cid, "researcher_decision": "ACCEPT_NARROW", "comparison_suitability": "PASS",
            "suitability_source": "Explicit researcher instruction; not inferred from ACCEPT_NARROW", "permitted_scope": HISTORY_SCOPE,
            "preserved_judgments": axes, "semantic_neutrality_claim": False})
    return {"version": VERSION, "reviewer_id": "Yaxin_ZHENG", "review_type": "researcher_verified_human_review",
        "decision_source": "researcher", "final_decision_authority": "researcher", "review_assistance": "AI-assisted",
        "blinding": "Not blind to preliminary assessments in the supplied materials; no independent blind review established",
        "human_review_timestamp": None, "reviewer_identity_authentication": "Researcher attestation, not software authentication",
        "styles": style_records, "history_associations": history_records, "history_decisions": decisions,
        "counts": {"style_decisions": len(styles), "source_style_axis_judgments": len(styles)*len(RATINGS),
                   "style_accepted_narrow": sum(r["researcher_decision"] == "ACCEPT_NARROW" for r in style_records),
                   "history_confirmations": len(histories), "history_narrow_decisions": len(decisions)}}


def tessa_plan(dataset_records, style_master):
    item = next(r for r in style_master["items"] if r["speaker_name"] == "Tessa")
    case = Case.from_dict(next(r for r in dataset_records if r["case_id"] == item["case_id"]))
    reference = asdict(build_prompt(case, "C1"))
    candidate = asdict(build_prompt(case, "N_style", neutral_override=TESSA_TEXT))
    if reference["text"] != item["reference_prompt"] or not replacement_preserved(reference, candidate):
        raise ValueError("Historical reference or invariant prompt content changed")
    return {"version": "tessa_minimal_repair_v1", "case_id": case.case_id, "previous_candidate_id": item["candidate_id"],
        "candidate_id": case.case_id + "__tessa_minimal_v1__" + text_hash(candidate["text"])[:12],
        "candidate_text": TESSA_TEXT, "candidate_prompt": candidate, "reference_prompt": reference,
        "candidate_prompt_sha256": text_hash(candidate["text"]), "reference_prompt_sha256": text_hash(reference["text"]),
        "trusted_evidence_sha256": text_hash(case.trusted_evidence), "question_sha256": text_hash(case.question),
        "previous_text": item["candidate_control_text"], "change": "Replace is provided with appears; all other intervention words remain fixed",
        "prompt_template_version": "transcript_base_v1", "maximum_candidate_requests": 1, "maximum_reference_requests": 1,
        "token_tolerance": 0, "selection": "Test only this predeclared wording once. Retain failure; no adaptive expansion.",
        "review_status": "PENDING_RESEARCHER_CONFIRMATION", "permitted_scope_if_approved": STYLE_SCOPE}


def reconcile_tokenizations(events, expected):
    """Bind each published ID array to the exact native request and raw response."""
    observed, pending = [], None
    for event in events:
        data = event["data"]
        if event["kind"] == "http_request":
            if data["route"] in {"/completion", "/v1/completions", "/v1/chat/completions"}:
                raise ValueError("No answer generation is authorized")
            if data["route"] == "/tokenize":
                if pending is not None:
                    raise ValueError("Unpaired request")
                pending = data["payload"]
        elif event["kind"] == "http_response" and data["route"] == "/tokenize":
            if pending is None or data["status"] != 200:
                raise ValueError("Unpaired or unsuccessful response")
            ids = json.loads(base64.b64decode(data["body_base64"]))["tokens"]
            observed.append((pending, ids))
            pending = None
    if pending is not None or len(observed) != len(expected):
        raise ValueError("Unexpected tokenizer inventory")
    for (request, ids), (prompt, saved_ids) in zip(observed, expected):
        if request != {"content": prompt, "add_special": True, "parse_special": False, "with_pieces": False} or ids != saved_ids:
            raise ValueError("Raw native tokenization differs from the saved input or IDs")
    return len(observed)
