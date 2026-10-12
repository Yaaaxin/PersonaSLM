import pytest
from personaslm.schemas import Case
from personaslm.fixtures import build_cases
from personaslm.evaluation import judge_current_city


@pytest.fixture
def case():
    return Case.from_dict(build_cases()[0])


@pytest.mark.parametrize("response, expected", [
    ("Alice currently lives in Paris.", "correct"),
    ("She lives in Lyon.", "incorrect"),
    ("Not Paris, Lyon.", "incorrect"),
    ("Not Lyon, she lives in Paris.", "correct"),
    ("Paris and Lyon are both her current home.", "incorrect"),
    ("I don't know.", "unknown"),
    ("She used to live in Lyon but now lives in Paris.", "correct"),
    ("", "unknown"),
])
def test_synthetic_fact_checker_cases(case, response, expected):
    assert judge_current_city(case, response).status == expected


def test_applicability_is_not_chosen_after_output(case):
    from dataclasses import replace
    case2 = replace(case, applicability={**case.applicability, "factual_consistency": False})
    assert judge_current_city(case2, "Lyon").status == "N/A"
