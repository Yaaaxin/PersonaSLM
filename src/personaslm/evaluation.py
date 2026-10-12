"""Synthetic P0 fact and temporal evaluator: NOT a general-purpose semantic judge."""
import re
from dataclasses import dataclass
from .schemas import Case


@dataclass(frozen=True)
class FactJudgment:
    status: str
    reason: str
    applicable: bool
    expected: str | None


def _found_city_mentions(text: str, cities: set[str]) -> set[str]:
    return {city for city in cities if re.search(r"(?<![A-Za-z])" + re.escape(city) + r"(?![A-Za-z])", text, re.I)}


def judge_current_city(case: Case, response: str) -> FactJudgment:
    if not case.applicability["factual_consistency"]:
        return FactJudgment("N/A", "inapplicable_before_generation", False, None)
    if not isinstance(response, str) or not response.strip():
        return FactJudgment("unknown", "empty_response", True, case.expected_answer)

    text = response.strip().lower()
    expected = case.expected_answer.lower()
    all_cities = {f.value.lower() for f in case.facts}
    mentioned = _found_city_mentions(text, all_cities)
    if not mentioned:
        return FactJudgment("unknown", "no_known_city_asserted", True, case.expected_answer)

    # Explicit negative claims: "not Paris", "isn't Paris", "不是巴黎".
    def negated(city: str) -> bool:
        return bool(re.search(r"\b(?:not|isn'?t|is not|no longer)\s+(?:in\s+)?" + re.escape(city) + r"\b", text)) or ("不是" + city in text)

    # A previous city can be validly mentioned, but only with an explicit past cue.
    def old_city_only_in_past(city: str) -> bool:
        escaped = re.escape(city)
        return bool(
            re.search(r"(?:used to (?:live|be)|previously (?:lived|in)|before (?:living|moving)|formerly (?:in|lived)|back then(?: in)?)\s+(?:in\s+)?" + escaped, text)
            or re.search(r"(?:once|was)\s+in\s+" + escaped, text)
        )

    if negated(expected):
        return FactJudgment("incorrect", "explicitly_negates_current_city", True, case.expected_answer)
    if expected not in mentioned:
        wrong = ", ".join(sorted(mentioned))
        return FactJudgment("incorrect", f"mentions_only_noncurrent_cities:{wrong}", True, case.expected_answer)
    other = mentioned - {expected}
    if any(not negated(city) and not old_city_only_in_past(city) for city in other):
        return FactJudgment("incorrect", "incompatible_city_also_asserted", True, case.expected_answer)
    return FactJudgment("correct", "states_current_city_without_current_conflict", True, case.expected_answer)
