import pytest

from personaslm.conditioning import build_prompt
from personaslm.fixtures import build_cases
from personaslm.matching import TokenMatchError, match_neutral, neutral_candidates
from personaslm.schemas import Case


@pytest.mark.parametrize("condition", ["N_style", "N_history"])
def test_matching_uses_full_prompt_and_preserves_structure(condition):
    case = Case.from_dict(build_cases()[0])
    reference = build_prompt(case, "C1" if condition == "N_style" else "C3")
    candidates = list(__import__("itertools").islice(neutral_candidates(case, condition), 2))
    wanted = build_prompt(case, condition, neutral_override=candidates[1])
    calls = []

    def tokenizer_test_double(text):
        calls.append(text)
        return [9] * (100 if text in (reference.text, wanted.text) else 101)

    matched = match_neutral(case, condition, tokenizer_test_double, max_candidates=2)
    assert matched.prompt.text == wanted.text
    assert matched.audit["attempted"] == 2
    assert matched.audit["delta"] == 0
    assert matched.prompt.evidence_block == reference.evidence_block
    assert len(matched.prompt.additions[0].splitlines()) == len(reference.additions[0].splitlines())
    assert all(text.startswith("CONTINUE THE DIALOGUE") and text.endswith("Assistant:") for text in calls)
    assert all(f.value not in matched.prompt.additions[0] for f in case.facts)


def test_unmatched_control_fails_with_evidence():
    case = Case.from_dict(build_cases()[0])
    target = build_prompt(case, "C1").text
    with pytest.raises(TokenMatchError) as error:
        match_neutral(case, "N_style", lambda text: [1] * (10 if text == target else 12), max_candidates=3)
    assert error.value.audit["best_delta"] == 2
    assert error.value.audit["attempted"] == 3


def test_predeclared_tolerance_is_honored():
    case = Case.from_dict(build_cases()[0])
    target = build_prompt(case, "C1").text
    matched = match_neutral(case, "N_style", lambda text: [1] * (10 if text == target else 11), tolerance=1)
    assert matched.audit["delta"] == 1
