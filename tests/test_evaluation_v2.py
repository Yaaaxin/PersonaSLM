from dataclasses import replace
import pytest

from personaslm.evaluation import judge_current_city
from personaslm.evaluation_v2 import audit_city_response
from personaslm.fixtures import build_cases
from personaslm.schemas import Case


@pytest.fixture
def case():
    return Case.from_dict(build_cases()[0])


@pytest.mark.parametrize("text,first,whole", [
    ("Alice currently lives in Paris.", "supported", "supported"),
    ("She currently lives in Lyon.", "contradicted", "contradicted"),
    ("Paris and Lyon are both her current home.", "contradicted", "contradicted"),
    ("Not Lyon, she lives in Paris.", "supported", "supported"),
    ("Not Paris, Lyon.", "contradicted", "contradicted"),
    ("She lived in Lyon in 2025. She lives in Paris now.", "supported", "supported"),
    ("She lived in Lyon in 2023. She lives in Paris now.", "unverifiable", "unverifiable"),
    ("She used to live in Lyon but now lives in Paris.", "supported", "supported"),
    ("She used to live in Lyon but now lives in Lyon.", "contradicted", "contradicted"),
    ("Paris.\n\nUser: Where did Alice live in 2025?\nAssistant: In Lyon.", "supported", "supported"),
    ("Paris.\n\nUser: Where did Alice live in 2023?\nAssistant: In Lyon.", "supported", "unverifiable"),
    ("Paris.\n\nUser: Where did Alice live back then?\nAssistant: Paris.", "supported", "contradicted"),
    ("Paris.\n\nUser: Where did Alice live back then?\nAssistant: She was living in Lyon back then.", "supported", "supported"),
    ("Maybe Paris.", "unverifiable", "unverifiable"),
    ('She said "Paris".', "unverifiable", "unverifiable"),
    ("Alice lives in Tokyo.", "unverifiable", "unverifiable"),
    ("Paris is lovely.", "unverifiable", "unverifiable"),
    ("Paris is not where she lives.", "unverifiable", "unverifiable"),
    ("She lives in Paris on 2026-99-99.", "unverifiable", "unverifiable"),
    ("Paris.\nUser: Where did Alice live in 2023?\nAssistant: She lived in Lyon.", "supported", "unverifiable"),
    ("", "unverifiable", "unverifiable"),
])
def test_city_time_audit(case, text, first, whole):
    result = audit_city_response(case, text)
    assert result["first_reply_city_status"] == first
    assert result["all_city_claims_status"] == whole
    assert result["human_adjudication"] is None


def test_legacy_result_is_not_overwritten(case):
    text = "Alice lives in Paris now. She lived in Lyon in 2025."
    original = judge_current_city(case, text)
    assert original.status == "incorrect"
    assert audit_city_response(case, text)["all_city_claims_status"] == "supported"
    assert judge_current_city(case, text) == original


def test_year_with_midyear_move_is_not_assumed(case):
    result = audit_city_response(case, "She lived in Lyon in 2026.")
    assert result["all_city_claims_status"] == "unverifiable"


def test_inapplicable_endpoint_stays_inapplicable(case):
    case = replace(case, applicability={**case.applicability, "factual_consistency": False})
    assert audit_city_response(case, "Paris.")["all_city_claims_status"] == "N/A"
