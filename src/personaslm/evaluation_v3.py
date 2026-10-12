"""Conservative, separately versioned English synthetic residence-claim audit.

Correct describes supported residence assertions, not response relevance or
general factuality. Unsupported syntax remains Unverifiable. Legacy scoring
and v2 are intentionally untouched.
"""
from datetime import date
import re

from .evaluation_v2 import generated_turns

VERSION = "english_residence_claim_audit_v3"


def _interval(clause_time, question, past, case):
    context = clause_time or question
    exact = re.search(r"\b(20\d\d-\d\d-\d\d)\b", context)
    if exact:
        try:
            date.fromisoformat(exact[1])
            return exact[1], exact[1], "explicit_date"
        except ValueError:
            return None, None, "invalid_date"
    year = re.search(r"\bin (20\d\d)\b", context, re.I)
    if year:
        return year[1]+"-01-01", year[1]+"-12-31", "explicit_year"
    if re.search(r"\bback then\b", context, re.I):
        dates = set(re.findall(r"20\d\d-\d\d-\d\d", case.history_dialogue))
        if len(dates) == 1:
            when = next(iter(dates))
            return when, when, "unique_dated_history"
        return None, None, "ambiguous_history_date"
    if past and not clause_time:
        return None, None, "unspecified_past"
    return case.evaluation_date, case.evaluation_date, "current"


def _resolve(case, city, negative, interval):
    first, last, scope = interval
    facts = [f for f in case.facts if f.attribute == "current_city"]
    if scope == "unspecified_past":
        refs = [f.fact_id for f in facts if f.value.casefold() == city.casefold() and f.valid_from < case.evaluation_date]
        return ("Correct" if refs and not negative else "Unverifiable"), refs
    if first is None:
        return "Unverifiable", []
    # A partial overlap or conflicting source record prevents certification.
    overlaps = [f for f in facts if f.valid_from <= last and (f.valid_until is None or f.valid_until >= first)]
    covering = [f for f in overlaps if f.valid_from <= first and (f.valid_until is None or f.valid_until >= last)]
    values = {f.value.casefold() for f in overlaps}
    refs = [f.fact_id for f in overlaps]
    if len(values) != 1 or not covering:
        return "Unverifiable", refs
    same = city.casefold() in values
    return ("Correct" if (not same if negative else same) else "Incorrect"), refs


def audit_residence(case, text):
    if not case.applicability["factual_consistency"]:
        return {"version": VERSION, "status": "Not Applicable", "first_reply_status": "Not Applicable", "claims": [], "unresolved": [], "human_judgment": None}
    allowed_subject = r"(?:"+re.escape(case.persona_id)+r"|the person|she|he|they)"
    verb = r"(?:currently lives?|lives?|lived|is currently living|is living|was living|used to live|does not live|doesn't live|did not live|didn't live)"
    residence = re.compile(r"^"+allowed_subject+r"\s+(?P<verb>"+verb+r")\s+in\s+(?P<value>.+)$", re.I)
    claims, unresolved = [], []
    question, assistant_number = case.question, 0
    for turn_no, turn in enumerate(generated_turns(text)):
        if turn["role"] == "User":
            question = turn["text"]
            continue
        initial = assistant_number == 0
        assistant_number += 1
        for raw_clause in re.split(r"(?<=[.!?])\s+|\n+|;\s*|\s+but\s+", turn["text"], flags=re.I):
            clause = raw_clause.strip().rstrip(".")
            if not clause:
                continue
            match = residence.fullmatch(clause)
            value = match["value"] if match else re.sub(r"^[Ii]n\s+", "", clause)
            tense = match["verb"].lower() if match else ""
            negative = "not" in tense or "n't" in tense
            past = any(v in tense for v in ("lived", "was", "used to", "did"))
            time_match = re.search(r"\s+(now|currently|back then|in 20\d\d|on 20\d\d-\d\d-\d\d)$", value, re.I)
            explicit_time = time_match[1] if time_match else ""
            if time_match:
                value = value[:time_match.start()]
            cities = re.split(r"\s+and\s+", value)
            known = {f.value.casefold() for f in case.facts if f.attribute == "current_city"}
            valid_city = lambda city: city.casefold() in known or re.fullmatch(r"[A-Z][a-z]+(?:[ -][A-Z][a-z]+){0,2}", city) is not None
            # Restrict bare answers to one city. Arbitrary capitalized sentences
            # and foreign subjects cannot become residence claims by substring.
            bare = not match and len(cities) == 1 and value.casefold() in known and (clause == value or clause == "In "+value)
            if (not match and not bare) or not all(valid_city(city) for city in cities):
                unresolved.append({"turn": turn_no, "first_reply": initial, "text": raw_clause, "reason": "outside_certified_residence_grammar"})
                continue
            interval = _interval(explicit_time, question, past, case)
            for city in cities:
                status, refs = _resolve(case, city, negative, interval)
                claims.append({"turn": turn_no, "first_reply": initial, "text": raw_clause,
                    "city": city, "negative": negative, "time_start": interval[0], "time_end": interval[1],
                    "time_resolution": interval[2], "reference_fact_ids": refs, "status": status})
    def aggregate(cs, us):
        if any(c["status"] == "Incorrect" for c in cs):
            return "Incorrect"
        if not cs or us or any(c["status"] == "Unverifiable" for c in cs):
            return "Unverifiable"
        return "Correct"
    return {"version": VERSION, "status": aggregate(claims, unresolved),
        "first_reply_status": aggregate([c for c in claims if c["first_reply"]], [u for u in unresolved if u["first_reply"]]),
        "claims": claims, "unresolved": unresolved, "human_judgment": None,
        "scope": "Synthetic English canonical city residence assertions only; no relevance/completeness score",
        "limitations": ["Restricted grammar; aliases, quotations and unsupported constructions require review.",
            "Unknown named-city alternatives contradict a unique covering city fact only within this canonical synthetic schema.",
            "Generated follow-up turns are output material, not new benchmark input.",
            "back then uses the unique history date; ambiguous natural discourse is outside scope."]}
