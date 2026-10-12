import json
from pathlib import Path
from dataclasses import replace
import pytest
from personaslm.evaluation_v3 import audit_residence
from personaslm.evaluation_v2 import audit_city_response
from personaslm.schemas import Case, Fact

FIXTURE = json.loads((Path(__file__).parent/"fixtures/p0_evaluation_dev_v3.json").read_text())
ITEMS = FIXTURE["cases"]


def independent_case():
    return Case.from_dict(FIXTURE["case_definition"])


@pytest.mark.parametrize("item", ITEMS, ids=[str(i)+"_"+x["category"] for i,x in enumerate(ITEMS)])
def test_independent_residence_contract(item):
    result = audit_residence(independent_case(), item["text"])
    assert result["status"] == item["expected"]
    assert result["human_judgment"] is None


def test_inapplicable_is_neither_correct_nor_incorrect():
    case = independent_case()
    case = replace(case, applicability={**case.applicability, "factual_consistency": False})
    assert audit_residence(case, "Chester.")["status"] == "Not Applicable"


def test_conflicting_source_facts_fail_closed():
    case = independent_case()
    case = replace(case, facts=case.facts+(Fact("conflict", "current_city", "Durham", "2026-10-01"),))
    assert audit_residence(case, "Bristol.")["status"] == "Unverifiable"


def test_foreign_subject_regression_preserves_v2_behavior():
    case = independent_case()
    text = "Taylor currently lives in Bristol."
    assert audit_city_response(case, text)["all_city_claims_status"] == "supported"
    assert audit_residence(case, text)["status"] == "Unverifiable"
