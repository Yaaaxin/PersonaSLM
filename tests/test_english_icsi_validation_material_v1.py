import copy

import pytest

import english_icsi_validation_material_v1 as m


def metadata():
    speakers = [f"reserved{i:02}" for i in range(12)]
    meetings = [{"meeting": f"Bed{i:03}", "date": f"2001-01-{i+1:02}",
                 "participants": speakers[:8] if i < 9 else speakers[8 + (i - 9) * 2:10 + (i - 9) * 2]}
                for i in range(11)]
    return {"development_speakers": ["development01"], "reserved_speakers": speakers, "reserved": meetings}


def test_original_participant_split_not_just_pseudonym_disjointness():
    source = metadata()
    assert len(m.reserved_metadata(source)["development"]) == 11
    bad = copy.deepcopy(source)
    bad["reserved"][0]["participants"].append("development01")
    with pytest.raises(ValueError, match="Participant leakage"):
        m.reserved_metadata(bad)
    bad = copy.deepcopy(source)
    bad["reserved"][0]["meeting"] = "Bmr001"
    with pytest.raises(ValueError, match="Unexpected"):
        m.reserved_metadata(bad)


def test_prefix_only_relabels_structured_ids_not_utterance_content():
    source = [{"candidate_group_id": "D001-G2", "speaker": "D001",
               "history": [{"speaker": "D002", "text": "An authored D001 example."}], "first_source_meeting": "Bed001"}]
    result = m.validation_labels(source)
    assert result[0]["candidate_group_id"] == "V001-G2"
    assert result[0]["history"][0]["speaker"] == "V002"
    assert result[0]["history"][0]["text"] == source[0]["history"][0]["text"]
    assert source[0]["speaker"] == "D001"


def test_body_read_guard_requires_explicit_bound_authorization(monkeypatch):
    monkeypatch.setattr(m, "checked_json", lambda path, expected: {} if path != m.POLICY else {"development_manifest": {"sha256": "manifest"}})
    with pytest.raises(ValueError, match="GO required"):
        m.retrieve("policy", "unauthorized", "hash")
