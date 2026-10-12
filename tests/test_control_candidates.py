"""Development-pool invariants; real tokenizer evidence is logged separately."""
import pytest

from personaslm.control_candidates import DEVELOPMENT_CASES, candidates, prompt, select_match


@pytest.mark.parametrize("case", DEVELOPMENT_CASES)
@pytest.mark.parametrize("condition,reference,count", [("N_style", "C1", 36), ("N_history", "C3", 8)])
def test_candidates_cannot_select_or_leak_city_evidence(case, condition, reference, count):
    pool = candidates(case, condition)
    assert len(pool) == len(set(pool)) == count
    changed = {**case, "current_city": "UNSEEN_CURRENT", "old_city": "UNSEEN_OLD"}
    assert pool == candidates(changed, condition)
    ref = prompt(case, reference)
    for text in pool:
        assert case["current_city"] not in text and case["old_city"] not in text
        built = prompt(case, condition, text)
        assert built["trusted_evidence"] == ref["trusted_evidence"]
        assert built["current_question"] == ref["current_question"]
        assert built["text"].index("TRUSTED EVIDENCE:") == ref["text"].index("TRUSTED EVIDENCE:")
        if condition == "N_history":
            assert case["speaker"] + ":" in text
            assert case["date"] in text
            assert text.splitlines()[1] == ref["conditioning_text"].splitlines()[1]


def test_match_failure_retains_best_difference_no_tolerance_relaxation():
    observed = [{"candidate_index": 0, "token_difference": -3},
                {"candidate_index": 1, "token_difference": 1},
                {"candidate_index": 2, "token_difference": -1}]
    result = select_match(observed)
    assert result["status"] == "FAILED" and result["best_token_difference"] == 1
    assert result["best_candidate_index"] == 1
    assert result["candidate_search_attempts"] == 3 and result["tolerance"] == 0


def test_exact_match_does_not_certify_semantics_or_authorize_generation():
    result = select_match([{"candidate_index": 0, "token_difference": 0}])
    assert result["status"] == "PASS"
    assert result["semantic_status"] == "UNREVIEWED"
    assert result["generation_authorized_by_match"] is False
    with pytest.raises(ValueError):
        select_match([])
