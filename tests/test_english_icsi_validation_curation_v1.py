import copy

import pytest

import english_icsi_validation_curation_v1 as c


def decisions():
    return {"selection": [{"group": "V001-G1", "statement": "I tested the software.",
                           "fact_basis": "Exact self-report", "context_basis": "Interpretable technical question",
                           "style_indices": [0, 1, 2, 3]}],
            "exclusions": [{"group": "V001-G2", "reason": "Earlier qualified source selected"}]}


def test_every_group_decided_and_one_source_group_per_speaker():
    groups = {"V001-G1": {"speaker": "V001"}, "V001-G2": {"speaker": "V001"}}
    c.check_decisions(groups, decisions())
    bad = decisions()
    bad["exclusions"] = []
    with pytest.raises(ValueError, match="exactly one"):
        c.check_decisions(groups, bad)
    bad = decisions()
    extra = copy.deepcopy(bad["selection"][0])
    extra["group"] = "V001-G2"
    bad["selection"].append(extra)
    bad["exclusions"] = []
    with pytest.raises(ValueError, match="one group per speaker"):
        c.check_decisions(groups, bad)


def test_distinct_actual_style_examples_and_explicit_fact_basis_required():
    groups = {"V001-G1": {"speaker": "V001"}, "V001-G2": {"speaker": "V001"}}
    bad = decisions()
    bad["selection"][0]["style_indices"] = [0, 0, 1, 2]
    with pytest.raises(ValueError, match="distinct"):
        c.check_decisions(groups, bad)
    bad = decisions()
    bad["selection"][0]["fact_basis"] = " "
    with pytest.raises(ValueError, match="source audit"):
        c.check_decisions(groups, bad)


def test_bmr_guard_is_not_rewritten_or_monkeypatched():
    class NeverRead:
        def read(self, _):
            raise AssertionError("Body must not be read")
    group = {"first_source_meeting": "Bmr001"}
    split = {"reserved": [{"meeting": "Bmr001"}]}
    with pytest.raises(ValueError, match="reserved Bed"):
        c.style_candidates(group, split, NeverRead())
