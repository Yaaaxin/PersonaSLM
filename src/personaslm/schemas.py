"""P0 record validation. No coercion of malformed data or secret fields."""
from dataclasses import dataclass
from datetime import date
from typing import Any

ENDPOINTS = (
    "response_relevance", "factual_consistency", "temporal_consistency",
    "conversational_coherence", "linguistic_fidelity", "behavioral_fidelity",
)


class SchemaError(ValueError):
    pass


def _string(obj: dict, name: str) -> str:
    value = obj.get(name)
    if not isinstance(value, str) or not value.strip():
        raise SchemaError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class Fact:
    fact_id: str
    attribute: str
    value: str
    valid_from: str
    valid_until: str | None = None

    @staticmethod
    def from_dict(obj: dict[str, Any]) -> "Fact":
        if not isinstance(obj, dict):
            raise SchemaError("fact must be a dict")
        f = Fact(
            _string(obj, "fact_id"), _string(obj, "attribute"),
            _string(obj, "value"), _string(obj, "valid_from"), obj.get("valid_until"),
        )
        try:
            first = date.fromisoformat(f.valid_from)
            if f.valid_until is not None:
                last = date.fromisoformat(f.valid_until)
                if last < first:
                    raise SchemaError("valid_until precedes valid_from")
        except (ValueError, TypeError) as exc:
            raise SchemaError(f"invalid fact date: {exc}") from exc
        return f

    def active_at(self, evaluation_date: str) -> bool:
        now = date.fromisoformat(evaluation_date)
        return date.fromisoformat(self.valid_from) <= now and (
            self.valid_until is None or now <= date.fromisoformat(self.valid_until)
        )


@dataclass(frozen=True)
class Case:
    case_id: str
    persona_id: str
    evaluation_date: str
    task_type: str
    context: tuple[str, ...]
    question: str
    trusted_evidence: str
    expected_answer: str
    facts: tuple[Fact, ...]
    style_only: str
    supplemental_fact: str
    history_dialogue: str
    neutral_style: str
    neutral_history: str
    applicability: dict[str, bool]
    split: str

    @staticmethod
    def from_dict(obj: dict[str, Any]) -> "Case":
        if not isinstance(obj, dict):
            raise SchemaError("case must be a dict")
        date.fromisoformat(_string(obj, "evaluation_date"))
        context = obj.get("context", [])
        if not isinstance(context, list) or not all(isinstance(c, str) for c in context):
            raise SchemaError("context must be a list of strings")
        applicability = obj.get("applicability")
        if not isinstance(applicability, dict) or set(applicability) != set(ENDPOINTS):
            raise SchemaError(f"applicability must contain exactly {ENDPOINTS}")
        if not all(type(v) is bool for v in applicability.values()):
            raise SchemaError("applicability values must be booleans fixed before generation")
        raw_facts = obj.get("facts")
        if not isinstance(raw_facts, list) or not raw_facts:
            raise SchemaError("facts must be nonempty list")
        facts = tuple(Fact.from_dict(f) for f in raw_facts)
        evaluation_date = _string(obj, "evaluation_date")
        expected = _string(obj, "expected_answer")
        if not any(f.attribute == "current_city" and f.active_at(evaluation_date) and f.value == expected for f in facts):
            raise SchemaError("expected answer must match a currently valid trusted city fact")
        return Case(
            _string(obj, "case_id"), _string(obj, "persona_id"), evaluation_date,
            _string(obj, "task_type"), tuple(context), _string(obj, "question"),
            _string(obj, "trusted_evidence"), expected, facts,
            _string(obj, "style_only"), _string(obj, "supplemental_fact"),
            _string(obj, "history_dialogue"), _string(obj, "neutral_style"),
            _string(obj, "neutral_history"), applicability, _string(obj, "split"),
        )
