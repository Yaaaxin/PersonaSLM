from personaslm.fixtures import build_cases
from personaslm.schemas import Case
from personaslm.conditioning import FACTORIAL, P0_CONDITIONS, assert_same_evidence, build_prompt


def test_factorial_has_every_combination():
    assert len(FACTORIAL) == 8
    assert set(FACTORIAL.values()) == {(s, f, h) for s in (0, 1) for f in (0, 1) for h in (0, 1)}


def test_conditions_preserve_necessary_evidence():
    for item in build_cases():
        case = Case.from_dict(item)
        assert_same_evidence(case, list(FACTORIAL) + list(P0_CONDITIONS))
        for condition in set(FACTORIAL) | set(P0_CONDITIONS):
            prompt = build_prompt(case, condition)
            assert prompt.text.count(case.trusted_evidence) == 1
            assert prompt.text.endswith("Assistant:")


def test_style_only_condition_does_not_mention_old_city():
    case = Case.from_dict(build_cases()[0])
    prompt = build_prompt(case, "C1")
    assert case.facts[0].value not in prompt.text
    assert case.facts[1].value in prompt.text


def test_history_condition_contains_dated_old_city():
    case = Case.from_dict(build_cases()[0])
    prompt = build_prompt(case, "C3")
    assert case.facts[0].value in prompt.text
    assert "2025-05-12" in prompt.text


def test_neutral_placebo_contains_no_fact_answers():
    case = Case.from_dict(build_cases()[0])
    neutral = build_prompt(case, "N_style")
    assert case.facts[0].value not in neutral.text
    assert "Speaker context note" in neutral.text
