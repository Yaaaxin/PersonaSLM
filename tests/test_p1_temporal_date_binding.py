import copy
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from p1_measurement_scoring import score as historical_score
from p1_measurement_scoring_v2 import score as revised_score
from p1_recovery_design import evidence_line, reference_audit, score_single
from p1_researcher_audit_integration import require_reference_evidence_complete


def fact(source_id, entity, attribute, value, valid_from, valid_to):
    return {
        "source_id": source_id,
        "entity": entity,
        "attribute": attribute,
        "value": value,
        "valid_from": valid_from,
        "valid_to": valid_to,
    }


def base_case(requested_date="2051-09-15", reference_value="Bay B200"):
    facts = [
        fact("E01", "Avery", "assigned_bay", "Bay B100", "2051-01-01", "2051-06-30"),
        fact("E02", "Avery", "assigned_bay", "Bay B200", "2051-07-01", "2051-12-31"),
        fact("E03", "Other", "assigned_bay", "Bay B300", "2051-07-01", "2051-12-31"),
    ]
    source_id = "E01" if reference_value == "Bay B100" else "E02"
    return {
        "family": "single_lookup",
        "speaker_name": "Avery",
        "requested_date": requested_date,
        "evaluation_date": "2051-09-15",
        "facts": facts,
        "reference": [{"key": "requested_bay", "value": reference_value, "source_ids": [source_id]}],
        "stale_endpoint": {"eligible": True, "old_value": "Bay B100", "current_value": "Bay B200"},
        "fidelity_target": {"linguistic": "short direct", "behavioral": "answer_then_acknowledgment"},
        "trusted_evidence": "\n".join(evidence_line(item) for item in facts),
    }


def dual_component_case():
    case = base_case()
    case["family"] = "dual_component"
    case["facts"].append(fact("E04", "Avery", "collection_window", "14:00-15:00", "2051-07-01", "2051-12-31"))
    case["trusted_evidence"] = "\n".join(evidence_line(item) for item in case["facts"])
    case["reference"] = [
        {"key": "current_bay", "value": "Bay B200", "source_ids": ["E02"]},
        {"key": "collection_window", "value": "14:00-15:00", "source_ids": ["E04"]},
    ]
    return case


def dated_comparison_case():
    case = base_case()
    case["family"] = "dated_comparison"
    case["reference"] = [
        {"key": "march_bay", "value": "Bay B100", "source_ids": ["E01"]},
        {"key": "september_bay", "value": "Bay B200", "source_ids": ["E02"]},
    ]
    return case


def test_march_only_question_uses_requested_date_not_registered_date():
    case = base_case(requested_date="2051-03-15", reference_value="Bay B100")
    result = revised_score("Bay B100.", case)

    assert result["task_success"] == "Success"
    assert result["factual"] == "Correct"
    assert result["temporal"] == "Correct"


def test_september_only_question_uses_requested_date():
    result = revised_score("Bay B200.", base_case())

    assert result["task_success"] == "Success"
    assert result["factual"] == "Correct"
    assert result["temporal"] == "Correct"


def test_registered_evaluation_date_is_not_consumed_by_historical_temporal_scorer():
    case = base_case(requested_date="2051-03-15", reference_value="Bay B100")
    changed_registered_date = copy.deepcopy(case)
    changed_registered_date["evaluation_date"] = "2099-01-01"
    changed_registered_date["registered_evaluation_date"] = "2099-01-01"
    changed_requested_date = copy.deepcopy(case)
    changed_requested_date["requested_date"] = "2051-09-15"

    baseline = revised_score("Bay B100.", case)
    assert revised_score("Bay B100.", changed_registered_date) == baseline
    assert revised_score("Bay B100.", changed_requested_date)["temporal"] == "Incorrect"


def test_multi_date_comparison_binds_each_component_to_its_requested_date():
    for scorer in (historical_score, revised_score):
        result = scorer("March: Bay B100; September: Bay B200.", dated_comparison_case())

        assert result["task_success"] == "Success"
        assert result["semantic_completeness"] == "YES"
        assert result["temporal"] == "Unverifiable"


def test_correct_values_assigned_to_the_wrong_dates_are_not_task_success():
    result = historical_score("March: Bay B200; September: Bay B100.", dated_comparison_case())

    assert result["task_success"] != "Success"
    assert result["semantic_completeness"] == "YES"


def test_correct_entity_under_an_outdated_period_is_temporally_incorrect():
    result = revised_score("Bay B100.", base_case())

    assert result["task_success"] == "Failure"
    assert result["factual"] == "Incorrect"
    assert result["temporal"] == "Incorrect"


def test_correct_date_with_wrong_entity_is_not_temporally_certified():
    result = revised_score("Bay B300.", base_case())

    assert result["task_success"] == "Failure"
    assert result["factual"] == "Incorrect"
    assert result["temporal"] == "Unverifiable"


def test_partial_multi_component_answer_is_not_task_success_or_factual_failure_by_default():
    result = revised_score("Bay B200.", dual_component_case())

    assert result["task_success"] == "Failure"
    assert result["factual"] == "Correct"
    assert result["temporal"] == "Correct"
    assert result["semantic_completeness"] == "NO"


def test_contradictory_answer_preserves_separate_factual_and_temporal_failure():
    result = revised_score("Bay B200; Bay B100.", base_case())

    assert result["task_success"] == "Failure"
    assert result["factual"] == "Incorrect"
    assert result["temporal"] == "Incorrect"


def test_truncated_structural_status_does_not_erase_semantically_complete_components():
    result = revised_score("Bay B200; 14:00-15:00", dual_component_case())
    structural_status = "TRUNCATED"

    assert structural_status == "TRUNCATED"
    assert result["task_success"] == "Success"
    assert result["semantic_completeness"] == "YES"


def test_correct_components_with_incomplete_trailing_explanation_remain_complete_but_unverified_prose():
    result = revised_score("Bay B200; 14:00-15:00; because", dual_component_case())
    structural_status = "TRUNCATED"

    assert structural_status == "TRUNCATED"
    assert result["task_success"] == "Success"
    assert result["semantic_completeness"] == "YES"
    assert result["factual"] == "Unverifiable"
    assert result["temporal"] == "Unverifiable"


def test_frozen_alias_and_identifier_normalization_remains_narrow():
    result = revised_score("Bay: B200", base_case())
    q1 = score_single("b200.", {"aliases": ["Bay B200", "B200"]})

    assert result["task_success"] == "Success"
    assert q1["task_success"] == "Success"
    assert score_single("Bay B100", {"aliases": ["Bay B200", "B200"]})["task_success"] == "Failure"


def test_missing_evidence_is_rejected_before_scoring():
    case = dual_component_case()
    case["facts"] = [item for item in case["facts"] if item["source_id"] != "E04"]
    case["trusted_evidence"] = "\n".join(evidence_line(item) for item in case["facts"])

    with pytest.raises(ValueError, match="Reference source missing"):
        require_reference_evidence_complete(case)


def test_reference_answer_ambiguity_is_rejected_before_scoring():
    case = base_case()
    ambiguous = fact("E04", "Avery", "assigned_bay", "Bay B200", "2051-07-01", "2051-12-31")
    case["facts"].append(ambiguous)
    case["trusted_evidence"] = "\n".join(evidence_line(item) for item in case["facts"])

    with pytest.raises(ValueError, match="Non-unique reference witness"):
        reference_audit(case)
