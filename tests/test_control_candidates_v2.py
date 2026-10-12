"""Independent invariants for proposed controls; no model-answer optimization."""
from copy import deepcopy
import json

import pytest

from personaslm.control_candidates_v2 import CASE_SPECS, FAMILIES, STYLE_POOL, candidate_texts, case_record, pair
from personaslm.schemas import Case


@pytest.mark.parametrize("spec", CASE_SPECS, ids=lambda s: s["case_id"])
def test_cases_and_all_prompt_wrappers(spec):
    case = Case.from_dict(json.loads(json.dumps(case_record(spec))))
    assert case.split == "development_only"
    assert case.expected_answer == spec["current_city"]
    for family in FAMILIES:
        p = pair(spec, family)
        reference = p["reference_prompt"]
        base = reference["text"].replace(reference["additions"][0], "<INTERVENTION>", 1)
        for candidate in p["candidates"]:
            prompt = candidate["prompt"]
            assert prompt["evidence_block"] == reference["evidence_block"]
            assert prompt["text"].replace(prompt["additions"][0], "<INTERVENTION>", 1) == base
            text = candidate["conditioning_text"]
            assert spec["current_city"] not in text and spec["old_city"] not in text
            if family == "style_generic":
                assert prompt["additions"][0].startswith("Speaker style profile: ")
                assert text.count(".") == 1
            else:
                assert text.startswith(f"Historical dialogue ({spec['date']}):\nUser: ")
                assert text.count("\n") == 2
                assert text.splitlines()[2].startswith(spec["speaker"] + ": ")
                if family != "history_format":
                    assert text.splitlines()[1] == reference["additions"][0].splitlines()[1]


def test_pool_is_independent_of_required_answer_and_old_city():
    original = CASE_SPECS[0]
    changed = {**original, "current_city": "ANSWER_SENTINEL", "old_city": "OLD_SENTINEL"}
    for family in FAMILIES:
        assert candidate_texts(original, family) == candidate_texts(changed, family)
        assert len(set(candidate_texts(original, family))) == len(candidate_texts(original, family))
    assert len(set(STYLE_POOL)) == len(STYLE_POOL)


def test_unknown_family_rejected():
    with pytest.raises(ValueError):
        pair(CASE_SPECS[0], "C7")
    with pytest.raises(ValueError):
        candidate_texts(CASE_SPECS[0], "C7")


@pytest.fixture
def review():
    from personaslm.control_review_v2 import VERSION, EDITABLE, RATINGS
    from personaslm.provenance import fingerprint
    item = {"case_id": "software_fixture", "condition_id": "fixture_style", "family": "style_generic",
            "neutral_text": "A conversation includes questions and replies.", "reference_conditioning_text": "Brief replies.",
            "trusted_evidence": "Fixture evidence.", "current_question": "Fixture question?", **{k: "" for k in EDITABLE}}
    packet = {"version": VERSION, "items": [item]}
    packet["packet_id"] = fingerprint(packet)
    row = {**item, **{k: "PASS" for k in RATINGS}, "reviewer_id": "SOFTWARE_FIXTURE_NOT_HUMAN",
           "review_assistance": "unassisted"}
    return packet, [row], list(row)


def test_blank_form_is_not_review_and_time_not_fabricated(review):
    from personaslm.control_review_v2 import validate_packet
    template, rows, fields = review
    assert validate_packet(template, template["items"], fields) == []
    assert len(validate_packet(template, rows, fields)) == 1
    assert rows[0]["reviewed_utc"] == ""


@pytest.mark.parametrize("key,value", [
    ("semantic_neutrality", ""), ("answer_leakage", "YES"), ("reviewer_id", " "),
    ("review_assistance", ""), ("neutral_text", "Altered material."),
    ("comparison_suitability", "NOT_APPLICABLE"), ("reviewed_utc", "2026-10-12T10:00:00"),
    ("reviewed_utc", "2026-10-12T10:00:00+02:00"),
    ("semantic_neutrality_evidence_quote", "Invented quotation.")])
def test_incomplete_or_invalid_review_is_rejected(review, key, value):
    from personaslm.control_review_v2 import validate_packet
    review[1][0][key] = value
    with pytest.raises(ValueError):
        validate_packet(*review)


def test_uncertainty_is_retained_with_quote(review):
    from personaslm.control_review_v2 import validate_packet
    review[1][0]["semantic_neutrality"] = "UNCERTAIN"
    with pytest.raises(ValueError):
        validate_packet(*review)
    review[1][0]["semantic_neutrality_evidence_quote"] = "A conversation includes questions and replies."
    assert validate_packet(*review)[0]["semantic_neutrality"] == "UNCERTAIN"


def test_inventory_schema_version_and_tampering_rejected(review):
    from personaslm.control_review_v2 import validate_packet
    template, rows, fields = review
    for candidate in ([], rows + rows):
        with pytest.raises(ValueError):
            validate_packet(template, candidate, fields)
    for bad_fields in (fields[:-1], fields + [fields[0]]):
        with pytest.raises(ValueError):
            validate_packet(template, rows, bad_fields)
    for field, value in (("version", "other"), ("packet_id", "tampered")):
        altered = deepcopy(template)
        altered[field] = value
        with pytest.raises(ValueError):
            validate_packet(altered, rows, fields)


def test_not_applicable_is_limited_to_declared_axes(review):
    from personaslm.control_review_v2 import validate_packet
    review[1][0]["speaker_identity"] = "NOT_APPLICABLE"
    assert len(validate_packet(*review)) == 1
    review[1][0]["answer_leakage"] = "NOT_APPLICABLE"
    with pytest.raises(ValueError):
        validate_packet(*review)


def test_import_is_versioned_and_refuses_blank_or_overwrite(review, tmp_path, monkeypatch):
    import csv
    from personaslm import provenance
    from personaslm.control_review_v2 import import_review
    monkeypatch.setattr(provenance, "repository_root", lambda: tmp_path)
    packet, rows, fields = review
    template = tmp_path / "template.json"
    submission = tmp_path / "submitted.csv"
    destination = tmp_path / "review-v1.json"
    template.write_text(json.dumps(packet), encoding="utf-8")
    def write_csv(material):
        with submission.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(material)
    write_csv(packet["items"])
    with pytest.raises(ValueError, match="No completed"):
        import_review(template, submission, destination)
    assert not destination.exists()
    write_csv(rows)
    imported = import_review(template, submission, destination)
    assert imported["completed"] == 1 and imported["remaining"] == 0
    assert imported["reviews"][0]["reviewed_utc"] == ""
    with pytest.raises(FileExistsError):
        import_review(template, submission, destination)
