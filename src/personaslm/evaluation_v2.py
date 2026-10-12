"""Supplemental English city/time audit; never replaces legacy run scoring.

This bounded rule audit distinguishes the first reply from model-authored turns.
It is not a general factuality judge or a substitute for independent annotation.
"""
from datetime import date
import re

VERSION = "english_city_temporal_audit_v2"


def generated_turns(text):
    """Keep model-authored role labels explicit; original prompt is never extended."""
    matches = list(re.finditer(r"(?m)^(User|Assistant):[ \t]*", text))
    turns = []
    start, role = 0, "Assistant"
    for match in matches:
        if match.start() > start:
            turns.append({"role": role, "text": text[start:match.start()].strip(), "offset": start})
        role, start = match.group(1), match.end()
    if start < len(text):
        turns.append({"role": role, "text": text[start:].strip(), "offset": start})
    return turns


def _time_scope(text, question, case):
    history_dates = set(re.findall(r"\d{4}-\d{2}-\d{2}", case.history_dialogue))
    lowered = text.lower()
    pending_past = bool(re.search(r"\b(lived|was living|used to live|was in|previously|formerly)\b", lowered))
    # Resolve explicit dates before present/past morphology; never discard a year.
    for index, candidate in enumerate((text, question)):
        exact = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", candidate)
        if exact:
            try:
                date.fromisoformat(exact.group(1))
            except ValueError:
                return None, None, "invalid_date"
            return exact.group(1), exact.group(1), "explicit_date"
        year = re.search(r"\bin\s+(20\d{2})\b", candidate, re.I)
        if year:
            return year.group(1)+"-01-01", year.group(1)+"-12-31", "explicit_year"
        if re.search(r"\b(currently|now|current)\b", candidate, re.I):
            if index == 1 and pending_past:
                return None, None, "unspecified_past"
            return case.evaluation_date, case.evaluation_date, "current"
        if re.search(r"\b(back then|at the time)\b", candidate, re.I):
            if len(history_dates) == 1:
                history_date = next(iter(history_dates))
                return history_date, history_date, "fixed_history_date"
            return None, None, "unresolved_past"
    if pending_past:
        return None, None, "unspecified_past"
    return None, None, "unresolved"


def _claim_status(case, city, first, last, scope, negative):
    facts = [f for f in case.facts if f.attribute == "current_city"]
    if scope == "unspecified_past":
        candidates = [f for f in facts if f.value.lower() == city.lower() and f.valid_from < case.evaluation_date]
        return ("supported" if candidates and not negative else "unverifiable"), [f.fact_id for f in candidates]
    if first is None:
        return "unverifiable", []
    # For a year-level claim, require one fact to cover the entire year.
    active = [f for f in facts if f.valid_from <= first and (f.valid_until is None or f.valid_until >= last)]
    if not active:
        return "unverifiable", []
    cities = {f.value.lower() for f in active}
    if len(cities) != 1:
        return "unverifiable", [f.fact_id for f in active]
    same = city.lower() in cities
    supported = not same if negative else same
    return ("supported" if supported else "contradicted"), [f.fact_id for f in active]


def audit_city_response(case, text):
    if not case.applicability["factual_consistency"]:
        return {"version": VERSION, "first_reply_city_status": "N/A", "all_city_claims_status": "N/A",
                "claims": [], "unresolved": [], "human_adjudication": None,
                "reason": "inapplicable_before_generation"}
    claims, unresolved = [], []
    question = case.question
    reply_number = 0
    known = sorted({f.value for f in case.facts if f.attribute == "current_city"}, key=len, reverse=True)
    city_pattern = re.compile(r"(?<![A-Za-z])("+"|".join(re.escape(c) for c in known)+r")(?![A-Za-z])", re.I)
    for turn_number, turn in enumerate(generated_turns(text)):
        if turn["role"] == "User":
            question = turn["text"]
            continue
        first_reply = reply_number == 0
        reply_number += 1
        # Work on individual clauses so a past cue cannot license a later present assertion.
        clauses = re.split(r"(?<=[.!?])\s+|\n+|\bbut\b", turn["text"], flags=re.I)
        for clause in clauses:
            if not clause.strip():
                continue
            mentions = list(city_pattern.finditer(clause))
            if not mentions:
                unresolved.append({"turn": turn_number, "text": clause, "reason": "outside_known_city_rule_scope", "first_reply": first_reply})
                continue
            # Questions and quoted/conditional examples are not certified as assertions.
            uncertain = clause.rstrip().endswith("?") or bool(re.search(r"\b(if|maybe|perhaps|might|could|said|believe|think)\b|[\"“”]", clause, re.I))
            # A city mention alone does not make an arbitrary sentence a residence claim.
            bare_answer = city_pattern.sub("CITY", clause.strip())
            residence = bool(re.search(r"\b(lives?|lived|living|current home|was in|previously in)\b", clause, re.I))
            bare = bool(re.fullmatch(r"(?:(?:[Ii]n |[Nn]ot )?CITY|[Nn]ot CITY,\s*CITY)[.!]?", bare_answer))
            if not residence and not bare:
                uncertain = True
            if re.search(r"\bnot\b", clause, re.I) and not re.search(r"\bnot\s+(?:in\s+)?"+city_pattern.pattern, clause, re.I):
                uncertain = True
            first, last, scope = _time_scope(clause, question, case)
            for match in mentions:
                prefix = clause[:match.start()]
                negative = bool(re.search(r"\b(?:not|isn't|wasn't|no longer)\s+(?:in\s+)?$", prefix, re.I))
                status, refs = _claim_status(case, match.group(), first, last, scope, negative)
                if uncertain:
                    status = "unverifiable"
                claims.append({"turn": turn_number, "first_reply": first_reply, "text": clause,
                    "city": match.group(), "negative": negative, "time_start": first, "time_end": last,
                    "time_resolution": scope, "context_question": question, "status": status,
                    "reference_fact_ids": refs})
    def verdict(items, extra_unresolved):
        if any(c["status"] == "contradicted" for c in items):
            return "contradicted"
        if not items or extra_unresolved or any(c["status"] == "unverifiable" for c in items):
            return "unverifiable"
        return "supported"
    initial = [c for c in claims if c["first_reply"]]
    return {"version": VERSION, "scope": "English synthetic city/time claims only",
            "first_reply_city_status": verdict(initial, [u for u in unresolved if u["first_reply"]]),
            "all_city_claims_status": verdict(claims, unresolved), "claims": claims, "unresolved": unresolved,
            "human_adjudication": None,
            "limitations": ["Model-authored follow-up turns are audited separately; they are not new benchmark user inputs.",
                            "back then is resolved only against the unique dated synthetic history header.",
                            "Non-city facts, language fluency and general factuality are outside this rule audit."]}
