"""Software contracts for bounded candidates, exact quotes and blank review forms."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from personaslm.control_closure import (
    STYLE_POOL, frozen_pairs, replacement_preserved, make_style_review,
    history_evidence, annotation_audit, exact_excerpt, validate_confirmations,
)
from personaslm.control_candidates import select_match
from personaslm.control_decisions import read_csv
from personaslm.control_final_review import EDITABLE, validate_review

PUBLIC = Path(__file__).resolve().parents[1] / "docs/validation"


@pytest.fixture
def materials():
    read = lambda name: json.loads((PUBLIC / name).read_text(encoding="utf-8"))
    return (read("P0_control_candidate_freeze_v2.json"), read("P0_final_control_review_v3.json"),
            read("P0_final_control_researcher_registration_v1/registration.json"))


def test_fixed_six_case_pool_no_answer_or_name_leakage(materials):
    frozen, master, registration = materials
    pairs = frozen_pairs(*materials)
    assert len(pairs) == 6 and len(STYLE_POOL) == len(set(STYLE_POOL)) == 12
    assert sum(len(p["candidates"]) for p in pairs) == 72
    for p in pairs:
        assert len(p["candidates"]) == 12
        for c in p["candidates"]:
            assert replacement_preserved(p["reference_prompt"], c["prompt"])
            assert c["conditioning_text"] in STYLE_POOL
            assert c["conditioning_text"].count(".") == 1


@pytest.mark.parametrize("change", ["decision", "case_count", "reference"])
def test_no_scope_or_reference_change(materials, change):
    frozen, master, registration = deepcopy(materials)
    if change == "decision":
        registration["records"][0]["researcher_decision"] = "ACCEPT_NARROW"
    elif change == "case_count":
        master["items"] = master["items"][1:]
    else:
        master["items"][0]["reference_prompt"] += " changed"
    with pytest.raises(ValueError):
        frozen_pairs(frozen, master, registration)


def test_wrapper_and_evidence_changes_rejected(materials):
    p = frozen_pairs(*materials)[0]
    for field in ("text", "evidence_block"):
        bad = deepcopy(p["candidates"][0]["prompt"])
        bad[field] += " altered"
        assert not replacement_preserved(p["reference_prompt"], bad)


def test_failed_matching_remains_failed_and_first_exact_wins():
    attempts = [{"candidate_index": i, "token_difference": d} for i, d in enumerate([2, -1, 1])]
    assert select_match(attempts)["status"] == "FAILED"
    assert select_match(attempts)["best_candidate_index"] == 1
    attempts += [{"candidate_index": 3, "token_difference": 0}, {"candidate_index": 4, "token_difference": 0}]
    assert select_match(attempts)["best_candidate_index"] == 3


def test_review_is_new_and_unjudged_even_for_failed_counts(materials):
    _, master, _ = materials
    pairs = frozen_pairs(*materials)
    for p in pairs:
        p["reference_token_count"] = 10
        p["attempts"] = [{**c, "token_count": 11, "token_difference": 1, "token_ids": [1]*11} for c in p.pop("candidates")]
    packet = make_style_review(master, {"pairs": pairs, "scope": "SOFTWARE_FIXTURE_ONLY"})
    fields, _ = read_csv(PUBLIC / "P0_final_control_review_v3.csv")
    assert len(packet["items"]) == 6
    assert validate_review(packet, packet["items"], fields, require_complete=False) == []
    for item in packet["items"]:
        assert item["token_difference"] == "1"
        assert "FAILED" in item["candidate_class"]
        assert all(item[k] == "" for k in EDITABLE)
        assert item["candidate_id"] not in {r["candidate_id"] for r in master["items"]}


def test_evidence_is_exact_and_preserves_original_judgments(materials):
    _, master, registration = materials
    rows = history_evidence(master, registration)
    items = {r["candidate_id"]: r for r in master["items"]}
    assert len(rows) == 18
    for row in rows:
        for arm, field in (("active", "original_active_intervention"), ("candidate", "candidate_control_text")):
            excerpt = row[arm + "_excerpt"]
            assert items[row["candidate_id"]][field][excerpt["start"]:excerpt["end"]] == excerpt["quote"]
        assert row["source_judgment_verbatim"] == ("uncertain" if row["field"] == "conversational_coherence" else "no")
        assert row["researcher_confirmation"] == row["reviewer_id"] == row["reviewed_utc"] == ""


def test_quotation_cannot_be_invented():
    with pytest.raises(ValueError):
        exact_excerpt("A real source sentence.", "A fabricated sentence.")


def test_annotation_audit_distinguishes_archive_and_adoption(materials):
    _, _, registration = materials
    _, rows = read_csv(PUBLIC / "P0_final_control_researcher_registration_v1/annotation_65_columns.csv")
    result = annotation_audit(registration, rows)
    assert result["historical_counts_verified"] == {"missing_official_label": 18, "not_applicable_not_allowed": 6, "missing_required_field_quote": 81}
    assert result["adopted_history_quote_confirmations"] == 18
    assert result["optional_empty_quote_fields"] == 279
    assert len(result["derived_labels_requiring_explicit_confirmation"]) == 6
    assert all(r["researcher_value"] == "" and r["source_categorical_label"] is None for r in result["derived_labels_requiring_explicit_confirmation"])
    assert sum(r["gate"] == "adopted_history_a_confirmation" for r in result["details"]) == 18


def test_confirmation_blank_unknown_duplicate_and_edited_material_rejected():
    expected = [{"id": "one", "quote": "Actual quote", "judgment": "", "researcher_notes": "", "reviewer_id": "", "reviewed_utc": ""}]
    kwargs = {"key": "id", "judgment": "judgment", "allowed": {"CONFIRM", "REJECT", "UNCERTAIN"}}
    for patch in ({}, {"id": "bad"}, {"quote": "changed"}, {"judgment": "PASS"}, {"reviewed_utc": "2026-10-13T12:00:00"}):
        row = {**expected[0], "judgment": "CONFIRM", "reviewer_id": "SOFTWARE_ONLY", **patch}
        if patch == {}:
            row["judgment"] = ""
        with pytest.raises(ValueError):
            validate_confirmations(expected, [row], **kwargs)
    with pytest.raises(ValueError):
        validate_confirmations(expected, expected * 2, **kwargs)


@pytest.mark.parametrize("label", ["CONFIRM", "REJECT", "UNCERTAIN"])
def test_actual_confirmation_keeps_uncertainty_and_missing_time(label):
    expected = [{"id": "one", "quote": "Actual quote", "judgment": "", "researcher_notes": "", "reviewer_id": "", "reviewed_utc": ""}]
    row = {**expected[0], "judgment": label, "reviewer_id": "SOFTWARE_ONLY"}
    result = validate_confirmations(expected, [row], key="id", judgment="judgment", allowed={"CONFIRM", "REJECT", "UNCERTAIN"})
    assert result[0]["judgment"] == label and result[0]["reviewed_utc"] == ""
