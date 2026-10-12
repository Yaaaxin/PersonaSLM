"""Prospective P0 measurement policy; historical scoring is untouched."""
from collections import Counter

from .evaluation_v3 import audit_residence, VERSION as FACT_VERSION
from .response_status import classify_response

VERSION = "separate_axes_policy_v1"
CATEGORIES = ("Correct", "Incorrect", "Unverifiable", "Not Applicable")


def evaluate_response(case, raw, backend, **boundary_options):
    boundary = classify_response(raw, backend, **boundary_options)
    eligible = case.applicability
    audit = None
    if not eligible["factual_consistency"]:
        fact, fact_reason = "Not Applicable", "Predeclared endpoint inapplicability"
    elif not boundary["unit_identifiable"]:
        fact, fact_reason = "Unverifiable", "Reply unit is ambiguous; retain raw text for independent adjudication"
    else:
        audit = audit_residence(case, boundary["first_span"]["text"])
        fact, fact_reason = audit["status"], "Recognized assertions in the observed first reply/prefix only; no completion penalty"
    def manual(endpoint, categorical=False):
        return {"label": ("Unverifiable" if categorical else "PENDING") if eligible[endpoint] else "Not Applicable",
                "rating": None, "scale": list(CATEGORIES) if categorical else "1-5 per existing annotation guidelines",
                "reason": "Independent annotation pending" if eligible[endpoint] else "Predeclared endpoint inapplicability"}
    return {"policy_version": VERSION, "case_id": case.case_id, "applicability": dict(eligible),
            "response_completeness": boundary,
            "factual_support": {"label": fact, "reason": fact_reason, "evaluator_version": FACT_VERSION, "audit": audit},
            "response_relevance": manual("response_relevance"),
            "temporal_consistency": manual("temporal_consistency", True),
            "conversational_coherence": manual("conversational_coherence"),
            "scored_unit": "Observed first reply/prefix; continuation excluded with exact offsets; ambiguous units require adjudication",
            "completeness_judgment_supplied": boundary_options.get("semantic_review") is not None,
            "limitations": ["City grammar is bounded; unsupported claims remain Unverifiable.",
                            "Temporal consistency and relevance are not inferred from factual support or response length."]}


def category_accounting(rows):
    """Counts preserve every pre-eligible observation, including uncertainty."""
    counts = Counter(row["factual_support"]["label"] for row in rows)
    if set(counts) - set(CATEGORIES):
        raise ValueError("Unknown factual category")
    counts = {key: counts[key] for key in CATEGORIES}
    return {"policy_version": VERSION, "counts": counts,
            "all_preeligible": len(rows) - counts["Not Applicable"],
            "total": len(rows), "uncertain_excluded_from_primary_denominator": False,
            "scope": "Category distribution only; no scalar general factual accuracy or causal estimate"}
