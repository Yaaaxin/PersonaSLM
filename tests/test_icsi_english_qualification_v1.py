import io
from datetime import datetime

import pytest

from tools.icsi_english_qualification_v1 import read_header, summarize


def test_header_stops_before_any_transcript_byte():
    prefix = b'<Meeting Session="Bmr001" DateTimeStamp="2001-02-01-1500"><Preamble><Participants><Participant Name="me001"/></Participants></Preamble>'
    stream = io.BytesIO(prefix + b'<Transcript>PRIVATE TARGET MUST NOT BE READ</Transcript></Meeting>')
    result = read_header(stream)
    assert stream.tell() == len(prefix)
    assert result["date"] == datetime(2001, 2, 1, 15)


def test_bad_date_is_not_inferred_from_meeting_number():
    text = b'<Meeting Session="Bmr001" DateTimeStamp="NaT"><Preamble><Participants><Participant Name="me001"/></Participants></Preamble>'
    with pytest.raises(ValueError):
        read_header(io.BytesIO(text))


def test_documented_computer_label_is_not_a_real_speaker():
    text = b'<Meeting Session="Bmr001" DateTimeStamp="2001-02-01-1500"><Preamble><Participants><Participant Name="me001"/><Participant Name="xe002"/></Participants></Preamble>'
    record = read_header(io.BytesIO(text))
    assert record["participants"] == {"me001"}
    assert record["computer_participant_count"] == 1


def test_coparticipant_leakage_and_separate_windows():
    records = []
    for day in range(1, 4):
        for group, people in (("Bmr", {"me001", "me002"}), ("Bed", {"me003", "me004"})):
            records.append({"meeting": f"{group}{day:03}", "group": group, "date": datetime(2001, 1, day), "participants": people})
    result = summarize(records)
    assert result["speakers_with_at_least_three_dates"] == 4
    assert result["participant_disjoint_window_pairs"] == 4
    assert len(result["full_corpus_coparticipation_components"]) == 2
    assert len(result["group_disjoint_feasibility_candidates_not_selected"]) == 2
    assert all(r["first_speakers_at_least_three_dates"] == 2 for r in result["group_disjoint_feasibility_candidates_not_selected"])
    records[-1]["participants"].add("me001")
    changed = summarize(records)
    assert len(changed["full_corpus_coparticipation_components"]) == 1
    assert changed["group_disjoint_feasibility_candidates_not_selected"] == []
