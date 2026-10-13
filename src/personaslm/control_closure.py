"""One bounded six-case style repair and source-based annotation reconciliation.

No generation, adaptive candidate expansion or inferred human judgments.
"""
from collections import Counter
from dataclasses import asdict
from datetime import datetime
import hashlib

from .conditioning import build_prompt
from .control_candidates import select_match
from .control_final_review import EDITABLE, RATINGS, VERSION as FORM_VERSION
from .provenance import fingerprint
from .schemas import Case

VERSION = "neutral_style_closure_v1_dev"
PROMPT_VERSION = "transcript_base_v1"
STYLE_POOL = (
    "No speaker-specific style information is provided.",
    "No speaker-specific style information is provided in this profile.",
    "No speaker-specific linguistic style information is provided in this profile.",
    "No speaker-specific linguistic style information is provided in this profile entry.",
    "No speaker-specific linguistic style information is provided in this particular profile entry.",
    "This profile contains no speaker-specific style information.",
    "This profile contains no speaker-specific information about linguistic style.",
    "This profile entry contains no speaker-specific information about linguistic style.",
    "This profile entry contains no speaker-specific information about linguistic style or expression.",
    "Linguistic style information for the speaker is not specified in this profile.",
    "Linguistic style information for the speaker is not specified in this profile entry.",
    "Linguistic style information for the speaker is not specified in this particular profile entry.",
)


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def replacement_preserved(reference, candidate):
    heading = "Speaker style profile: "
    return (len(reference["additions"]) == len(candidate["additions"]) == 1
            and reference["additions"][0].startswith(heading)
            and candidate["additions"][0].startswith(heading)
            and reference["text"].replace(reference["additions"][0], "<INTERVENTION>", 1)
            == candidate["text"].replace(candidate["additions"][0], "<INTERVENTION>", 1)
            and reference["evidence_block"] == candidate["evidence_block"])


def frozen_pairs(previous_freeze, master, registration):
    cases = {r["case_id"]: r for r in previous_freeze["dataset_records"]}
    specs = {r["case_id"]: r for r in previous_freeze["case_specs"]}
    decisions = {r["candidate_id"]: r for r in registration["records"]}
    items = [r for r in master["items"] if r["candidate_family"] == "style_generic"]
    if len(items) != 6 or len({r["case_id"] for r in items}) != 6:
        raise ValueError("Closure is restricted to the six existing style development cases")
    pairs = []
    for item in items:
        if decisions[item["candidate_id"]]["researcher_decision"] != "REVISION_REQUIRED":
            raise ValueError("Only revision-required style controls may be changed")
        case = Case.from_dict(cases[item["case_id"]])
        reference = asdict(build_prompt(case, "C1"))
        if reference["text"] != item["reference_prompt"]:
            raise ValueError("Historical reference prompt changed")
        candidates = []
        for index, text in enumerate(STYLE_POOL):
            spec = specs[case.case_id]
            if any(value.lower() in text.lower() for value in (spec["speaker"], spec["current_city"], spec["old_city"])):
                raise ValueError("Candidate contains a source name or city")
            prompt = asdict(build_prompt(case, "N_style", neutral_override=text))
            if not replacement_preserved(reference, prompt):
                raise ValueError("Wrapper, evidence, question or context changed")
            candidates.append({"candidate_index": index, "conditioning_text": text, "prompt": prompt,
                               "prompt_sha256": text_hash(prompt["text"])})
        pairs.append({"case_id": case.case_id, "previous_candidate_id": item["candidate_id"],
                      "reference_prompt": reference, "reference_prompt_sha256": text_hash(reference["text"]),
                      "trusted_evidence": case.trusted_evidence, "current_question": case.question,
                      "trusted_evidence_hash": text_hash(case.trusted_evidence), "candidates": candidates})
    return pairs


def make_style_review(master, validation):
    source = {r["candidate_id"]: r for r in master["items"]}
    items = []
    for pair in validation["pairs"]:
        # A failed closest attempt is still reviewable, but visibly unqualified.
        match = select_match(pair["attempts"])
        chosen = pair["attempts"][match["best_candidate_index"]]
        item = dict(source[pair["previous_candidate_id"]])
        item.update({k: "" for k in EDITABLE})
        item.update({
            "candidate_id": f"{pair['case_id']}__style_closure_v1__pool{chosen['candidate_index']:02d}__{chosen['prompt_sha256'][:12]}",
            "candidate_version": VERSION, "candidate_control_text": chosen["prompt"]["additions"][0],
            "candidate_prompt": chosen["prompt"]["text"], "prompt_sha256": chosen["prompt_sha256"],
            "candidate_token_count": str(chosen["token_count"]),
            "reference_token_count": str(pair["reference_token_count"]),
            "token_difference": str(chosen["token_difference"]),
            "source_candidate_index": str(chosen["candidate_index"]), "source_condition_id": "N_style_closure_v1_dev",
            "intended_comparison": "Specific style-profile content versus an explicit absence-of-profile-information statement; wrapper and total length matched only when token_difference is zero",
            "candidate_class": "DEVELOPMENT ONLY; human semantic review pending; tokenizer status " + match["status"],
        })
        item["material_sha256"] = fingerprint({k: v for k, v in item.items() if k not in EDITABLE and k != "material_sha256"})
        items.append(item)
    packet = {"version": FORM_VERSION, "candidate_version": VERSION, "items": items,
              "human_reviews_completed": 0, "language": "en", "validation_sha256": fingerprint(validation),
              "scope": "Six new style texts only; no prior judgments transferred; failed exact matches cannot be adopted",
              "blinding": "Unblinded researcher review; assistance must be declared; missing actual review time stays blank"}
    packet["packet_id"] = fingerprint(packet)
    return packet


def exact_excerpt(text, quote):
    start = text.find(quote)
    if start < 0:
        raise ValueError("Quotation is not present verbatim")
    return {"quote": quote, "start": start, "end": start + len(quote), "source_text_sha256": text_hash(text)}


def history_evidence(master, registration):
    items = {r["candidate_id"]: r for r in master["items"]}
    rows = []
    for record in registration["records"]:
        if record["candidate_family"] != "history_format":
            continue
        if record["researcher_decision"] != "ACCEPT_NARROW":
            raise ValueError("History A evidence does not authorize a new decision")
        item = items[record["candidate_id"]]
        active, control = item["original_active_intervention"], item["candidate_control_text"]
        active_lines, control_lines = active.splitlines(), control.splitlines()
        for field in ("topic_alignment", "temporal_relationships", "conversational_coherence"):
            if field == "topic_alignment":
                qa, qc = active_lines[1], control_lines[1]
                reason = "Residence versus conversation topic; the excerpt documents the difference, not its causal effect."
            elif field == "temporal_relationships":
                qa, qc = active, control
                reason = "Identical dated headers; the active reply asserts past residence whereas the generic reply does not."
            else:
                qa, qc = "\n".join(active_lines[1:]), "\n".join(control_lines[1:])
                reason = "The full question-answer adjacency is shown; excerpts cannot establish a human coherence verdict."
            ea, ec = exact_excerpt(active, qa), exact_excerpt(control, qc)
            source_label = record["source_row"]["researcher_check_" + field]
            rows.append({"evidence_id": item["candidate_id"] + "__" + field,
                         "candidate_id": item["candidate_id"], "case_id": item["case_id"], "field": field,
                         "researcher_decision_verbatim": record["researcher_decision"],
                         "source_judgment_verbatim": source_label,
                         "normalized_original_judgment": {"no": "FAIL", "uncertain": "UNCERTAIN"}[source_label],
                         "active_source_field": "original_active_intervention", "active_excerpt": ea,
                         "candidate_source_field": "candidate_control_text", "candidate_excerpt": ec,
                         "existing_global_quote": record["global_quote_verbatim"],
                         "trusted_evidence": item["trusted_evidence"], "current_question": item["current_question"],
                         "intended_comparison": item["intended_comparison"], "extraction_note": reason,
                         "quote_provenance": "Automated verbatim extraction for human confirmation; not a new human decision",
                         "researcher_confirmation": "", "researcher_notes": "", "reviewer_id": "", "reviewed_utc": ""})
    if len(rows) != 18:
        raise ValueError("Expected exactly18 evidence associations")
    return rows


def annotation_audit(registration, converted_rows):
    records = {r["candidate_id"]: r for r in registration["records"]}
    counts = Counter()
    details = []
    derived = []
    for row in converted_rows:
        rec = records[row["candidate_id"]]
        allowed_na = set(row["not_applicable_fields"].split(", ")) - {""}
        for field in RATINGS:
            issue = None
            if not row[field]:
                issue = "missing_official_label"
            elif row[field] == "NOT_APPLICABLE" and field not in allowed_na:
                issue = "not_applicable_not_allowed"
            if issue:
                counts[issue] += 1
                details.append({"candidate_id": row["candidate_id"], "field": field, "issue": issue,
                                "gate": "archival_only_for_superseded_or_excluded_controls"})
            if row[field] in {"FAIL", "UNCERTAIN"} and not row[field + "_evidence_quote"]:
                counts["missing_required_field_quote"] += 1
                details.append({"candidate_id": row["candidate_id"], "field": field + "_evidence_quote",
                                "issue": "missing_required_field_quote",
                                "gate": "adopted_history_a_confirmation" if row["candidate_family"] == "history_format" else "archival_only_for_superseded_or_excluded_controls"})
        if row["candidate_family"] == "history_format":
            derived.append({"candidate_id": row["candidate_id"], "case_id": row["case_id"],
                            "field": "comparison_suitability", "historical_converted_value": row["comparison_suitability"],
                            "source_decision_verbatim": rec["researcher_decision"],
                            "source_categorical_label": None,
                            "finding": "Historical PASS was conversion-derived, not a supplied per-axis rating. Do not use it as a uniquely inferred human label.",
                            "intended_comparison": row["intended_comparison"],
                            "review_question": "For this exact narrow comparison, explicitly supply PASS, FAIL or UNCERTAIN; the ACCEPT_NARROW decision remains unchanged.",
                            "researcher_value": "", "researcher_notes": "", "reviewer_id": "", "reviewed_utc": ""})
    if dict(counts) != registration["gap_counts"]:
        raise ValueError("Historical gap counts do not reconstruct")
    return {"historical_counts_verified": dict(counts), "details": details, "derived_labels_requiring_explicit_confirmation": derived,
            "labels_are": "Comparison suitability ratings, not endpoint applicability; do not change the frozen applicability matrix",
            "strict_archive_issues": sum(counts.values()), "adopted_history_quote_confirmations": 18,
            "adopted_history_suitability_confirmations": len(derived),
            "optional_empty_quote_fields": 360 - counts["missing_required_field_quote"],
            "nonblocking": ["Unknown review time", "No second reviewer", "Missing optional PASS quotes", "Unresolved fields on superseded style, excluded B or diagnostic-only C"],
            "new_style_review": "All six revised texts need new human review; historical labels never transfer"}


def validate_confirmations(expected, rows, *, key, judgment, allowed):
    """Confirm quoted associations or an explicit rating, never infer either."""
    reference = {r[key]: r for r in expected}
    if len(reference) != len(expected) or len(rows) != len(expected):
        raise ValueError("Confirmation inventory differs")
    editable = {judgment, "researcher_notes", "reviewer_id", "reviewed_utc"}
    seen = set()
    normalize = lambda value: str(value).replace("\r\n", "\n")
    for row in rows:
        item_id = row.get(key)
        if item_id not in reference or item_id in seen:
            raise ValueError("Unknown or duplicate confirmation")
        seen.add(item_id)
        original = reference[item_id]
        if set(row) != set(original) or any(not isinstance(v, str) for v in row.values()):
            raise ValueError("Malformed confirmation row")
        if any(normalize(row[k]) != normalize(v) for k, v in original.items() if k not in editable):
            raise ValueError("Locked quote, source judgment or comparison changed")
        if row[judgment] not in allowed or not row["reviewer_id"].strip():
            raise ValueError("Actual researcher confirmation and identifier required")
        if row["reviewed_utc"]:
            when = datetime.fromisoformat(row["reviewed_utc"])
            if when.tzinfo is None or when.utcoffset().total_seconds() != 0:
                raise ValueError("Actual review time, if supplied, must use UTC")
    return rows
