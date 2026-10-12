from personaslm.boundary_review import review_boundary


def test_uppercase_role_cannot_be_certified_as_single_turn():
    case = {"trusted_evidence": "A test record.", "question": "A test question?", "literal_role_text_allowed": False}
    result = review_boundary("An answer.\n\nUSER: Extra turn.\n", {"stop_type":"word", "stopping_word":"\nUser:"}, case, "T1")
    assert result["frozen_v1_status"] == "PASS"
    assert result["reviewed_structural_status"] == "PARTIAL"
    assert result["v1_false_structural_pass"] is True


def test_multiline_body_is_preserved_as_single_turn():
    case = {"trusted_evidence": "A test record.", "question": "A test question?", "literal_role_text_allowed": False}
    result = review_boundary("- first\n- second\n", {"stop_type":"word", "stopping_word":"\nUser:"}, case, "T1")
    assert result["reviewed_structural_status"] == "PASS"
