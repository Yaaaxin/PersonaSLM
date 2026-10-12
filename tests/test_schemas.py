import copy
import pytest
from personaslm.fixtures import build_cases
from personaslm.schemas import Case, SchemaError


def test_20_synthetic_cases_are_valid():
    cases = build_cases()
    assert len(cases) == 20
    assert len({c["case_id"] for c in cases}) == 20
    for item in cases:
        case = Case.from_dict(item)
        assert case.split == "p0_synthetic_only"
        assert case.applicability["factual_consistency"]


def test_invalid_fact_time_rejected():
    item = copy.deepcopy(build_cases()[0])
    item["facts"][0]["valid_until"] = "2020-01-01"
    with pytest.raises(SchemaError):
        Case.from_dict(item)


def test_missing_applicability_rejected():
    item = copy.deepcopy(build_cases()[0])
    del item["applicability"]["temporal_consistency"]
    with pytest.raises(SchemaError):
        Case.from_dict(item)


def test_current_fact_must_match_answer():
    item = copy.deepcopy(build_cases()[0])
    item["expected_answer"] = "Shanghai"
    with pytest.raises(SchemaError):
        Case.from_dict(item)
