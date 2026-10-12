"""Authored software inputs only, never actual reviewer identities or ratings."""
from copy import deepcopy
import pytest

from personaslm.control_resolution_review import VERSION, EDITABLE, validate_resolution
from personaslm.neutral_review import RATINGS
from personaslm.provenance import fingerprint


@pytest.fixture
def review():
    item = {"case_id":"fixture", "condition_id":"N_style", "neutral_text":"Repeated text.",
            "trusted_evidence":"Fixture evidence.", "current_question":"Fixture question?",
            "reference_conditioning_text":"Fixture reference.", **{k:"" for k in EDITABLE}}
    template = {"version":VERSION, "items":[item]}
    template["packet_id"] = fingerprint(template)
    submitted = {**item, **{k:"PASS" for k in RATINGS}, "reviewer_id":"SOFTWARE_FIXTURE_NOT_HUMAN",
                 "reviewed_utc":"2026-10-12T12:00:00+00:00"}
    return template, [submitted], list(submitted)


def test_valid_review_and_blank_template(review):
    assert len(validate_resolution(*review)) == 1
    assert validate_resolution(review[0], review[0]["items"], review[2]) == []


@pytest.mark.parametrize("field,value", [("reviewer_id",""), ("reviewed_utc",""),
    ("semantic_neutrality",""), ("neutral_text","changed"),
    ("unintended_linguistic_style_evidence_quote","not present")])
def test_incomplete_or_changed_review_rejected(review, field, value):
    review[1][0][field] = value
    with pytest.raises(ValueError):
        validate_resolution(*review)


def test_uncertainty_requires_real_evidence_quote(review):
    review[1][0]["semantic_neutrality"] = "UNCERTAIN"
    with pytest.raises(ValueError):
        validate_resolution(*review)
    review[1][0]["semantic_neutrality_evidence_quote"] = "Repeated text."
    assert len(validate_resolution(*review)) == 1


def test_duplicate_missing_and_version_mismatch(review):
    template, rows, fields = review
    for bad in ([], rows + rows):
        with pytest.raises(ValueError):
            validate_resolution(template, bad, fields)
    template["version"] = "different"
    with pytest.raises(ValueError):
        validate_resolution(template, rows, fields)
