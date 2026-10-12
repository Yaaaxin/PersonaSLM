"""Frozen, conservative single-reply measurement; never a factuality score."""
import hashlib
import re

VERSION = "response_status_v1"
STATUSES = ("COMPLETE", "TRUNCATED", "CROSS_TURN", "AMBIGUOUS")
ROLE = re.compile(r"^[ \t]*(user|assistant|system|human|bot)[ \t]*:", re.I | re.M)
PREFIX = re.compile(r"\A\s*assistant[ \t]*:[ \t]*", re.I)
QUOTED_ROLE = re.compile(r"^[ \t]*[>\"']+[ \t]*(user|assistant|system|human|bot)[ \t]*:", re.I | re.M)
UNKNOWN_ROLE = re.compile(r"^[ \t]*[A-Z][A-Za-z_ ]{0,24}:[ \t]*", re.M)


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def classify_response(raw, backend, *, declared_stops=(), literal_delimiters=False, semantic_review=None):
    """Classify saved output, preserving its exact first-span and excluded tail.

    COMPLETE requires a separately supplied completeness judgment bound to this
    raw hash. No automatic punctuation/answer-correctness completion heuristic.
    Literal/quoted/fenced role text is conservatively outside automated scope.
    """
    if not isinstance(raw, str) or not isinstance(backend, dict):
        raise ValueError("Raw text and backend evidence are required")
    if not all(isinstance(s, str) and s for s in declared_stops):
        raise ValueError("Stop declarations must be nonempty strings")
    digest = text_hash(raw)
    if semantic_review is not None:
        if (semantic_review.get("label") not in ("COMPLETE", "INCOMPLETE", "UNCERTAIN")
            or semantic_review.get("raw_sha256") != digest
            or not semantic_review.get("review_id") or not semantic_review.get("basis")):
            raise ValueError("Completeness review requires label, raw hash, review ID and basis")
    semantics = semantic_review or {"label": "UNCERTAIN", "basis": "No independent completeness judgment supplied"}
    prefix = PREFIX.match(raw)
    start = prefix.end() if prefix else 0
    body = raw[start:]
    roles = list(ROLE.finditer(body))
    suspicious = [m for m in UNKNOWN_ROLE.finditer(body) if not ROLE.match(body, m.start())]
    kind = backend.get("stop_type")
    flag_kinds = [k for k, field in (("eog", "stopped_eos"), ("word", "stopped_word"), ("limit", "stopped_limit")) if backend.get(field) is True]
    contradictory = len(set(flag_kinds + ([kind] if kind in ("eog", "word", "limit") else []))) > 1
    kind = kind or (flag_kinds[0] if len(flag_kinds) == 1 else "unknown")
    hazards = []
    if literal_delimiters:
        hazards.append("predeclared_literal_delimiter_content")
    if QUOTED_ROLE.search(body) or ("```" in body and (roles or any(s in body for s in declared_stops))):
        hazards.append("quoted_or_fenced_delimiter")
    if suspicious:
        hazards.append("unrecognized_line_label")
    without_headers = ROLE.sub("", body)
    if re.search(r"\b(user|assistant|system|human|bot)[ \t]*:", without_headers, re.I):
        hazards.append("inline_or_quoted_role_label")
    if contradictory:
        hazards.append("contradictory_backend_termination")
    # Only declared role boundaries and a whole-line sentinel are certified.
    sentinel = "\n<END_OF_REPLY>"
    hits = [(m.start(), m.end(), "role_transition") for m in roles]
    if sentinel in declared_stops:
        hits += [(m.start(), m.end(), "declared_marker") for m in re.finditer(r"(?m)^<END_OF_REPLY>[ \t]*(?=\r?$)", body)]
    hit = min(hits, default=None)
    end = start + hit[0] if hit else len(raw)
    unit = raw[start:end]
    stopping_word = backend.get("stopping_word")
    valid_native_stop = kind == "word" and stopping_word in declared_stops and (
        stopping_word == sentinel or ROLE.fullmatch(stopping_word.strip()) is not None)
    closed = bool(hit) or kind == "eog" or valid_native_stop
    if hazards or not unit.strip():
        status, reason, identifiable = "AMBIGUOUS", hazards or ["empty_first_reply"], False
    elif hit and (hit[2] == "role_transition" or body[hit[1]:].strip()):
        status, reason, identifiable = "CROSS_TURN", ["visible_continuation_after_first_reply"], True
    elif closed:
        status = "COMPLETE" if semantics["label"] == "COMPLETE" else "AMBIGUOUS"
        reason, identifiable = ["bounded_reply_with_separate_completeness_judgment" if status == "COMPLETE" else "bounded_reply_semantics_not_certified"], True
    elif kind == "limit":
        status, reason, identifiable = "TRUNCATED", ["budget_ended_without_observed_reply_boundary"], True
    else:
        status, reason, identifiable = "AMBIGUOUS", ["no_certified_boundary_or_budget_evidence"], True
    return {"version": VERSION, "status": status, "reasons": reason,
        "backend_termination": dict(backend), "backend_kind": kind,
        "raw_response": raw, "raw_sha256": digest, "raw_empty": not raw.strip(),
        "first_span": {"start": start, "end": end, "text": unit, "sha256": text_hash(unit)},
        "removed_prefix": raw[:start], "excluded_tail": raw[end:],
        "unit_identifiable": identifiable, "observed_boundary": hit[2] if hit else (kind if closed else None),
        "declared_stops": list(declared_stops), "literal_delimiters": literal_delimiters,
        "semantic_completeness": semantics, "factual_judgment_used": False,
        "scope": "TRUNCATED is a boundary-censored observation, not proof of semantic incompleteness or factual error."}
