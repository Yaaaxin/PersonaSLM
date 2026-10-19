from datetime import datetime
import xml.etree.ElementTree as ET

from english_icsi_material_v1 import clean_text, metadata_split, material_candidates, natural_window, parse_development_meeting, style_profile


def test_split_excludes_every_cross_participant_meeting():
    rows = [{"meeting": "Bmr001", "group": "Bmr", "date": datetime(2000, 1, 1), "participants": {"me001", "me002"}},
            {"meeting": "Bed001", "group": "Bed", "date": datetime(2000, 1, 2), "participants": {"me001", "me003"}},
            {"meeting": "Bed002", "group": "Bed", "date": datetime(2000, 1, 3), "participants": {"me003", "me004"}}]
    result = metadata_split(rows)
    assert [m["meeting"] for m in result["reserved"]] == ["Bed002"]
    assert set(result["development_speakers"]).isdisjoint(result["reserved_speakers"])


def test_privacy_and_uncertainty_filter():
    assert clean_text(ET.fromstring("<Segment>I wrote the code.</Segment>")) == "I wrote the code."
    for text in ["I worked with Alice.", "My wife wrote the code.", "I used <Uncertain>something</Uncertain>.", "<Foreign Language='de'>ja</Foreign>"]:
        assert clean_text(ET.fromstring(f"<Segment>{text}</Segment>")) is None


def test_native_segments_preserve_exclusion_gap():
    raw = b'<Meeting Session="Bmr001"><Transcript><Segment Participant="me001" StartTime="1" EndTime="2">I wrote the code.</Segment><Segment Participant="me002" StartTime="3" EndTime="4">I called Alice.</Segment><Segment Participant="me001" StartTime="5" EndTime="6">I tested the script.</Segment></Transcript></Meeting>'
    turns, rejected = parse_development_meeting(raw, "Bmr001", {"me001", "me002"})
    assert len(turns) == 2
    assert turns[1]["source_segment_ids"] == [2]
    assert rejected["privacy_language_or_transcription_filter"] == 1
    assert not natural_window(turns, 0, 2)


def test_style_has_no_length_outcome_and_excludes_facts():
    turns = [{"speaker": "me001", "start": i, "end": i + .5, "source_segment_ids": [i], "text": "I think I'm probably using the tool and I am testing it."} for i in range(12)]
    style = style_profile(turns, "me001", {0, 1})
    assert style is not None
    assert style["turns"] == 10
    assert 0 not in style["source_segment_ids"]
    assert set(style["per_100_words"]) == {"contractions", "fillers", "hedges"}


def test_material_sources_and_target_contexts_stay_separate():
    def turn(i, speaker, text):
        return {"speaker": speaker, "start": float(i), "end": i + .5, "source_segment_ids": [i], "text": text}
    first = [turn(0, "me001", "I wrote the code for the tool and tested the script.")]
    first += [turn(i, "me001", "I think I'm probably checking the tool and maybe the results are useful.") for i in range(1, 13)]
    history = [turn(i, "me001" if i % 2 == 0 else "me002", "The earlier discussion concerns the recording tool and its tests.") for i in range(6)]
    later = [turn(i, "me001" if i % 2 == 0 else "me002", "The current discussion concerns a different part of the project.") for i in range(14)]
    later[6] = turn(6, "me001", "I would consider the new design carefully because there are several separate issues that remain unresolved today.")
    later[13] = turn(13, "me001", "I think the second decision needs a more detailed discussion before we can choose a sensible next step.")
    split = {"development_speakers": ["me001", "me002"], "development": [
        {"meeting": f"Bmr{i:03}", "date": f"2000-01-0{i}T12:00:00", "participants": ["me001", "me002"]} for i in range(1, 4)]}
    cases, _, _ = material_candidates(split, {"Bmr001": first, "Bmr002": history, "Bmr003": later})
    assert len(cases) == 2
    for case in cases:
        assert case["first_source_date"] < case["history_date"] < case["target_date"]
        assert 0 not in case["style"]["source_segment_ids"]
        assert case["reference_continuation_not_for_prompt"]["source_segment_ids"][0] not in {i for t in case["context"] for i in t["source_segment_ids"]}
    first_keys = {i for t in cases[0]["context"] for i in t["source_segment_ids"]} | set(cases[0]["reference_continuation_not_for_prompt"]["source_segment_ids"])
    second_keys = {i for t in cases[1]["context"] for i in t["source_segment_ids"]} | set(cases[1]["reference_continuation_not_for_prompt"]["source_segment_ids"])
    assert first_keys.isdisjoint(second_keys)
