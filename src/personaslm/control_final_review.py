"""A new review view of unchanged v2 candidates; never supplies human judgments."""
import argparse
from collections import Counter
import csv
from datetime import datetime
import json
from pathlib import Path

from .control_review_v2 import EDITABLE as OLD_EDITABLE, HISTORY_RATINGS
from .journal import atomic_json, utc_now
from .provenance import fingerprint, require_local_path, sha256

VERSION = "control_final_review_v3"
QUESTIONS = {
    "answer_leakage": "Does the candidate avoid disclosing the required current answer outside the unchanged trusted evidence?",
    "additional_factual_information": "Does the candidate avoid additional personal assertions beyond the trusted evidence? Count retained historical assertions too; diagnostic intent does not erase them.",
    "contradictory_information": "Is the candidate free of contradictions with dated evidence or with itself?",
    "temporal_interference": "Does the candidate avoid unintended temporal implications for answering the current question?",
    "unintended_linguistic_style": "Does the candidate avoid unintended style, brevity, register, repetition or question-asking cues, including effects of the heading?",
    "semantic_neutrality": "Is the candidate semantically neutral for the proposed comparison, rather than merely equal in token length?",
    "unnecessary_repetition": "Is the candidate free of redundant within-text repetition used as padding?",
    "speaker_identity": "Does the historical reply unambiguously refer to the same named person as the current evidence and question?",
    "dialogue_structure": "Are roles, turn order and adjacency/speech-act structure adequately matched? Distinguish question-answer from question-clarification.",
    "timestamp_format": "Are the historical date value and header format identical to the active intervention?",
    "topic_alignment": "Is the topic matched without adding a different issue, such as an address-versus-city distinction?",
    "temporal_relationships": "Is the reference's past-residence relation preserved, beyond merely retaining a date label?",
    "conversational_coherence": "Is the candidate a plausible natural English contribution or exchange?",
    "evidence_question_preservation": "Are the actual trusted evidence and current question unchanged in the two full prompts?",
    "comparison_suitability": "Is this candidate suitable for its stated narrow comparison, given all residual differences? A diagnostic need not be neutral.",
}
RATINGS = tuple(QUESTIONS)
EDITABLE = (*RATINGS, *(k + "_evidence_quote" for k in RATINGS),
            "reviewer_notes", "reviewer_id", "review_assistance", "reviewed_utc")
FAMILIES = {"style_generic", "history_format", "history_topic", "history_stale_generalized"}


def _check_digest(packet):
    if fingerprint({k: v for k, v in packet.items() if k != "packet_id"}) != packet.get("packet_id"):
        raise ValueError("Review master digest differs")


def make_packet(old_master, frozen, validation, source_hashes):
    _check_digest(old_master)
    if old_master.get("version") != "control_development_review_v2":
        raise ValueError("Unexpected source review version")
    if len(old_master["items"]) != 24 or len(validation["pairs"]) != 24:
        raise ValueError("Expected all24 v2 candidates")
    pairs = {(p["case_id"], p["family"]): p for p in validation["pairs"]}
    if len(pairs) != 24 or Counter(p["family"] for p in validation["pairs"]) != Counter({k: 6 for k in FAMILIES}):
        raise ValueError("Unexpected candidate inventory")
    cases = {r["case_id"]: r for r in frozen["dataset_records"]}
    specs = {r["case_id"]: r for r in frozen["case_specs"]}
    items, seen = [], set()
    for old in old_master["items"]:
        key = old["case_id"], old["family"]
        if key in seen or key not in pairs:
            raise ValueError("Duplicate or unknown source candidate")
        seen.add(key)
        if any(old[k] for k in OLD_EDITABLE):
            raise ValueError("Use the blank original master; never transfer annotations")
        p = pairs[key]
        if p["matching"]["status"] != "PASS":
            raise ValueError("Cannot publish a failed match as a validated control")
        a = p["attempts"][p["matching"]["best_candidate_index"]]
        case, spec = cases[key[0]], specs[key[0]]
        if (old["neutral_text"] != a["prompt"]["additions"][0]
                or old["reference_conditioning_text"] != p["reference_prompt"]["additions"][0]
                or old["current_question"] != case["question"]
                or old["trusted_evidence"] != case["trusted_evidence"]
                or old["prompt_sha256"] != a["prompt_sha256"]
                or int(old["token_count"]) != len(a["token_ids"])
                or int(old["reference_token_count"]) != len(p["reference_token_ids"])
                or int(old["token_difference"]) != 0
                or len(a["token_ids"]) != len(p["reference_token_ids"])):
            raise ValueError("Source review materials differ from observed tokenized prompts")
        family = old["family"]
        item = {
            "candidate_id": f"{key[0]}__{family}__pool{a['candidate_index']:02d}__{a['prompt_sha256'][:12]}",
            "case_id": key[0], "candidate_family": family,
            "original_active_intervention": old["reference_conditioning_text"],
            "candidate_control_text": old["neutral_text"],
            "trusted_evidence": old["trusted_evidence"], "current_question": old["current_question"],
            "reference_date": "NOT_APPLICABLE" if family == "style_generic" else spec["date"],
            "evaluation_date": case["evaluation_date"], "expected_answer": case["expected_answer"],
            "speaker_name": spec["speaker"], "reference_condition": old["reference_condition"],
            "reference_token_count": str(len(p["reference_token_ids"])), "candidate_token_count": str(len(a["token_ids"])),
            "token_difference": "0", "intended_comparison": old["intended_comparison"],
            "review_questions": "\n".join(f"{i}. {field}: {question}" for i, (field, question) in enumerate(QUESTIONS.items(), 1)),
            **{k: "" for k in EDITABLE},
            "reference_prompt": p["reference_prompt"]["text"], "candidate_prompt": a["prompt"]["text"],
            "form_version": VERSION, "candidate_version": old["candidate_version"],
            "prompt_template_version": old["prompt_template_version"], "source_condition_id": old["condition_id"],
            "source_candidate_index": str(a["candidate_index"]), "prompt_sha256": a["prompt_sha256"],
            "reference_prompt_sha256": p["reference_prompt_sha256"], "trusted_evidence_hash": p["trusted_evidence_hash"],
            "reference_date_scope": "No dated style block" if family == "style_generic" else "Historical header date, not evaluation date",
            "not_applicable_fields": ", ".join(HISTORY_RATINGS) if family == "style_generic" else (
                "semantic_neutrality" if family == "history_stale_generalized" else ""),
            "candidate_class": "Diagnostic; not a neutral placebo" if family == "history_stale_generalized" else (
                "Topic-matched clarification comparison; neutrality unestablished" if family == "history_topic" else "Proposed neutral control; unreviewed"),
        }
        item["material_sha256"] = fingerprint({k: v for k, v in item.items() if k not in EDITABLE})
        items.append(item)
    packet = {"version": VERSION, "created_utc": utc_now(), "language": "en", "items": items,
              "source_hashes": source_hashes, "human_reviews_completed": 0,
              "scope": "Expanded review presentation only; unchanged v2 experimental inputs and selections",
              "blinding": "Unblinded materials including expected answer; no prior human labels or model responses",
              "annotation_rule": "All fields blank; no transfer of old40 reviews or automated analytical assessments"}
    packet["packet_id"] = fingerprint(packet)
    return packet


def validate_review(master, rows, fields, *, require_complete=True):
    _check_digest(master)
    if master.get("version") != VERSION or not master.get("items"):
        raise ValueError("Unexpected or empty review version")
    items = master["items"]
    if len(fields) != len(set(fields)) or set(fields) != set(items[0]):
        raise ValueError("Invalid CSV columns")
    expected = {r["candidate_id"]: r for r in items}
    if len(expected) != len(items):
        raise ValueError("Duplicate master candidate")
    reviewed, seen = [], set()
    for row in rows:
        if set(row) != set(fields) or any(not isinstance(v, str) for v in row.values()):
            raise ValueError("Malformed CSV row")
        key = row["candidate_id"]
        if key not in expected or key in seen:
            raise ValueError("Unknown or duplicate candidate ID")
        seen.add(key)
        item = expected[key]
        norm = lambda value: value.replace("\r\n", "\n")
        if any(norm(row[k]) != norm(v) for k, v in item.items() if k not in EDITABLE):
            raise ValueError("Locked review material changed")
        if not any(row[k] for k in EDITABLE):
            continue
        na_fields = set(item["not_applicable_fields"].split(", ")) - {""}
        for field in RATINGS:
            allowed = {"PASS", "FAIL", "UNCERTAIN"} | ({"NOT_APPLICABLE"} if field in na_fields else set())
            if row[field] not in allowed:
                raise ValueError("Missing or invalid label: " + field)
        if not row["reviewer_id"].strip() or row["review_assistance"] not in {"unassisted", "AI-assisted", "other-assisted"}:
            raise ValueError("Declare reviewer identifier and assistance")
        if row["reviewed_utc"]:
            when = datetime.fromisoformat(row["reviewed_utc"])
            if when.tzinfo is None or when.utcoffset().total_seconds() != 0:
                raise ValueError("Actual review time, if supplied, must use UTC")
        supplied = "\n".join(item[k] for k in ("original_active_intervention", "candidate_control_text", "trusted_evidence", "current_question", "reference_prompt", "candidate_prompt"))
        for field in RATINGS:
            quote = norm(row[field + "_evidence_quote"])
            if row[field] in {"FAIL", "UNCERTAIN"} and not quote.strip():
                raise ValueError("Evidence quote required: " + field)
            if quote and quote not in supplied:
                raise ValueError("Quotation absent from supplied input")
        reviewed.append(row)
    if seen != set(expected):
        raise ValueError("Missing review inventory rows")
    if require_complete and len(reviewed) != len(items):
        raise ValueError(f"Incomplete human review: {len(reviewed)}/{len(items)}")
    return reviewed


def import_review(input_path, output_path, *, master_path=None, allow_partial=False):
    if master_path is None:
        master_path = Path(__file__).resolve().parents[2] / "docs/validation/P0_final_control_review_v3.json"
    master_path, input_path, output_path = map(require_local_path, (master_path, input_path, output_path))
    if output_path.exists():
        raise FileExistsError("Use a new output; existing reviews and masters are immutable")
    master = json.loads(master_path.read_text(encoding="utf-8"))
    with input_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames or [], list(reader)
    reviewed = validate_review(master, rows, fields, require_complete=not allow_partial)
    if not reviewed:
        raise ValueError("No human annotations supplied")
    result = {"version": VERSION, "imported_utc": utc_now(), "packet_id": master["packet_id"],
              "master_sha256": sha256(master_path), "submission_sha256": sha256(input_path),
              "submission_utf8": input_path.read_bytes().decode("utf-8-sig"),
              "completed": len(reviewed), "remaining": len(rows)-len(reviewed), "reviews": reviewed,
              "completion_status": "PASS" if len(rows) == len(reviewed) else "PARTIAL",
              "human_comparison_suitability": dict(Counter(r["comparison_suitability"] for r in reviewed)),
              "control_acceptance": "Not automatically decided by import; resolve substantive findings separately",
              "authenticity_limit": "Reviewer identity/assistance are supplied attestations, not authenticated by software"}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(output_path, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import a completed final-control review without changing the master")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--master", type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    result = import_review(args.input, args.output, master_path=args.master, allow_partial=args.allow_partial)
    print(json.dumps({k: result[k] for k in ("completed", "remaining", "completion_status", "control_acceptance")}))
