import pytest
from personaslm.diagnostics import parse_reply


@pytest.mark.parametrize("raw, reason, split, expected", [
    ("", "eos", False, "direct_eos"),
    ("", "stop_sequence", False, "stop_without_visible_text"),
    ("", "length", False, "raw_empty"),
    ("\nHello", "length", True, "newline_truncation"),
    ("Assistant:", "length", False, "parsing_or_filter_removed"),
    ("Alice: Paris", "eos", False, "preserved"),
    ("Paris", "eos", False, "preserved"),
])
def test_parser_failure_classes(raw, reason, split, expected):
    record = parse_reply(raw, stop_reason=reason, stop_at_first_newline=split)
    assert record.classification == expected
    assert record.raw_text == raw


def test_downstream_filter_is_independently_auditable():
    record = parse_reply("valid answer", filter_all=True)
    assert record.classification == "parsing_or_filter_removed"
    assert "downstream_filter_removed" in record.steps


def test_production_compatible_newline_split_only_when_requested():
    raw = "\nParis"
    assert parse_reply(raw).parsed_text == "Paris"
    assert parse_reply(raw, stop_at_first_newline=True).parsed_text == ""


def test_transformations_are_replayable_and_whitespace_is_not_misattributed():
    parsed = parse_reply("Alice: Paris\nOther text", stop_at_first_newline=True)
    assert parsed.steps == ("first_newline_stop", "speaker_prefix_removed")
    current = parsed.raw_text
    for step in parsed.transformations:
        assert step["before"] == current
        current = step["after"]
    assert current == parsed.parsed_text == "Paris"
    audit = parsed.audit()
    assert audit["changed"] and not audit["raw_empty"]
    assert audit["raw_sha256"] != audit["parsed_sha256"]


def test_whitespace_only_output_is_not_direct_eos():
    parsed = parse_reply(" \r\n", stop_reason="eos")
    assert parsed.classification == "parsing_or_filter_removed"
    assert parsed.audit()["raw_visible_empty"]
    assert not parsed.audit()["raw_empty"]
