import json
from pathlib import Path

import pytest
from personaslm.response_boundary import boundary_audit, prompt_for

CASES = json.loads((Path(__file__).parent / "fixtures/p0_boundary_dev_v1.json").read_text())["cases"]


def test_prompt_stop_pairing_preserves_exact_inputs():
    for case in CASES:
        assert prompt_for(case, "T0") == prompt_for(case, "T1")
        assert prompt_for(case, "T2") == prompt_for(case, "T3")
        for variant in ("T0", "T1", "T2", "T3"):
            text = prompt_for(case, variant)
            assert case["trusted_evidence"] in text and case["question"] in text


@pytest.mark.parametrize("raw,native,variant,case,status,body", [
    (" Bath.\n\nUser: Next?", {"stop_type":"limit"}, "T0", 0, "PASS", "Bath."),
    (" Bath.\n", {"stop_type":"word", "stopping_word":"\nUser:"}, "T1", 0, "PASS", "Bath."),
    ("Bath.", {"stop_type":"limit"}, "T0", 0, "PARTIAL", "Bath."),
    ("", {"stop_type":"word", "stopping_word":"\nUser:"}, "T1", 0, "PARTIAL", ""),
    ("- notebook\n- compass\n<END_OF_REPLY>tail", {"stop_type":"limit"}, "T2", 2, "PASS", "- notebook\n- compass"),
    ("Bath.\nUser: Next?\n<END_OF_REPLY>", {"stop_type":"limit"}, "T2", 0, "PARTIAL", "Bath.\nUser: Next?"),
    ("Start\nUser: archive heading", {"stop_type":"limit"}, "T0", 3, "PARTIAL", "Start"),
    ("Start\nUser: archive heading\nA label.\n<END_OF_REPLY>", {"stop_type":"limit"}, "T2", 3, "PASS", "Start\nUser: archive heading\nA label."),
    ("Bath.", {"stop_type":"word", "stopping_word":"unexpected"}, "T3", 0, "PARTIAL", "Bath."),
])
def test_boundary_keeps_raw_and_reports_uncertainty(raw, native, variant, case, status, body):
    result = boundary_audit(raw, native, CASES[case], variant)
    assert result["status"] == status and result["parsed_response"] == body
    assert result["raw_response"] == raw
    assert raw[result["slice_end"]:] == result["excluded_tail"]
    assert result["human_semantic_completeness"] is None
