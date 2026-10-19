import xml.etree.ElementTree as ET

from english_icsi_material_v2 import contiguous, history_window, screened_text, targets_for


def turn(i, person, text, start=None, end=None):
    return {"speaker": person, "text": text, "source_segment_ids": [i], "start": float(i) if start is None else start,
            "end": i + .5 if end is None else end, "possible_name_tokens_for_private_audit": []}


def test_capitalization_is_flagged_not_automatically_rejected():
    result = screened_text(ET.fromstring("<Segment>I worked with Alice on the code.</Segment>"))
    assert result is not None
    assert "Alice" in result[1]
    assert screened_text(ET.fromstring("<Segment>I discussed my password.</Segment>")) is None
    assert screened_text(ET.fromstring("<Segment>I used <Uncertain>something</Uncertain>.</Segment>")) is None


def test_history_overlap_allowed_but_removed_source_gap_not_allowed():
    turns = [turn(i, "me001" if i == 0 else "me002", "The earlier discussion concerns the recording software and its practical limitations.", end=i + 1.5) for i in range(6)]
    assert contiguous(turns)
    assert len(history_window(turns, "me001")) == 6
    turns[2]["source_segment_ids"] = [99]
    assert not contiguous(turns)
    assert history_window(turns, "me001") is None


def test_target_does_not_see_concurrent_future_context():
    turns = [turn(i, "me001" if i % 2 else "me002", "The context discusses the current tool.") for i in range(5)]
    turns[4] = turn(4, "me001", "I think the design needs a different approach because the old implementation does not support these particular requirements.")
    meetings = [{"meeting": "Bmr003"}]
    assert len(targets_for("me001", meetings, {"Bmr003": turns}, "")) == 1
    turns[3]["end"] = 4.5
    assert targets_for("me001", meetings, {"Bmr003": turns}, "") == []
