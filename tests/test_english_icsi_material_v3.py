from english_icsi_material_v3 import history, screen, targets


def turn(i, who, text):
    return {"speaker": who, "text": text, "source_segment_ids": [i], "start": float(i), "end": i + .5}


def test_children_and_calibration_not_professional_history():
    assert not screen({"text": "I took the kids to the station."})
    assert not screen({"text": "Please say your name for the microphone test."})
    assert screen({"text": "I tested the microphone software with the script."})


def test_history_backchannel_is_insufficient():
    turns = [turn(i, "D001" if i == 0 else "D002", "Yeah." if i == 0 else "The software processes the recorded files and produces the annotations.") for i in range(10)]
    assert history(turns, "D001") is None
    turns[0]["text"] = "I tested the software on the recorded files and the resulting annotations need additional inspection before we can use the data."
    assert history(turns, "D001") is not None


def test_eight_turn_context_and_future_exclusion():
    turns = [turn(i, "D001" if i % 2 else "D002", "The context concerns the software.") for i in range(9)]
    turns[8] = turn(8, "D001", "I think this implementation needs further testing because the current results do not yet resolve all of the remaining issues.")
    meetings = [{"meeting": "Bmr003"}]
    assert len(targets("D001", meetings, {"Bmr003": turns}, "")) == 1
    assert targets("D001", meetings, {"Bmr003": turns[1:]}, "") == []
    turns[7]["end"] = 8.5
    assert targets("D001", meetings, {"Bmr003": turns}, "") == []
