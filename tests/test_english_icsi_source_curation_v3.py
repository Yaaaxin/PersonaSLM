import english_icsi_source_curation_v3 as c


def test_exact_private_redaction_retains_original_and_offsets():
    turn = {"text": "Morgan spoke; Morgan's account. Morganic stays.", "source_segment_ids": [9]}
    result = c.redact(turn, {"Morgan": "Colleague A"})
    assert result["text"] == "Colleague A spoke; Colleague A's account. Morganic stays."
    assert result["original_text_before_name_redaction"] == turn["text"]
    assert len(result["name_redactions"]) == 2
    assert turn["text"].startswith("Morgan")


def test_explicit_name_index_ignores_normal_safe_capitals():
    assert [m[0] for m in c.flagged("I think Morgan answered. She's right.")] == ["Morgan", "She's"]
    assert c.locate({"history": [{"text": "a"}]}, "history.0")["text"] == "a"
