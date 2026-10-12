"""Simulated review inputs only; never independent human evaluation evidence."""
import csv
import json
import pytest

from personaslm.neutral_review import EDITABLE, RATINGS, export_form, import_review


@pytest.fixture
def packet(local_tmp):
    frozen = {"rows": [], "prompts": {}}
    for n in range(20):
        cid = f"TEST_ONLY_{n}"
        frozen["prompts"][cid] = {}
        for neutral, ref in (("N_style", "C1"), ("N_history", "C3")):
            prompt = {"evidence_block": "Test evidence", "additions": ["Test-only neutral text."],
                      "text": "Test evidence\n\nUser: Test question?\nAssistant:"}
            frozen["prompts"][cid][neutral] = {"prompt": prompt}
            frozen["prompts"][cid][ref] = {"prompt": prompt}
            frozen["rows"].append({"case_id": cid, "neutral_condition": neutral, "reference_condition": ref,
                "neutral_token_count": 10, "reference_token_count": 10, "token_difference": 0,
                "prompt_template_version": "TEST_ONLY", "trusted_evidence_hash": "test_hash"})
    source = local_tmp / "freeze.json"
    source.write_text(json.dumps(frozen))
    prefix = local_tmp / "form"
    template = export_form(source, prefix)
    return local_tmp, prefix, template


def submitted(packet, mutate=None):
    root, prefix, template = packet
    rows = [dict(r) for r in template["items"]]
    rows[0].update({k: "PASS" for k in RATINGS})
    rows[0].update(reviewer_id="TEST_DOUBLE_NOT_HUMAN", reviewed_utc="2026-10-12T12:00:00+00:00",
                   reviewer_notes="Synthetic import test, not a human judgment.")
    if mutate:
        mutate(rows)
    path = root / "simulated_submission.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_export_preserves_blank_judgments_and_identifiers(packet):
    _, _, template = packet
    assert len(template["items"]) == 40 and template["human_reviews_completed"] == 0
    assert all(r[k] == "" for r in template["items"] for k in EDITABLE)


def test_partial_import_is_versioned_and_cannot_overwrite(packet):
    root, prefix, template = packet
    path = submitted(packet)
    output = root / "review_1.json"
    result = import_review(prefix.with_suffix(".json"), path, output, "TEST_ROUND")
    assert result["completed"] == 1 and result["remaining"] == 39
    assert result["packet_id"] == template["packet_id"]
    assert "TEST_DOUBLE_NOT_HUMAN" in result["submission_utf8"]
    with pytest.raises(FileExistsError):
        import_review(prefix.with_suffix(".json"), path, output, "TEST_ROUND")


@pytest.mark.parametrize("mutate", [
    lambda rows: rows[0].update(answer_leakage="correct"),
    lambda rows: rows[0].update(neutral_text="tampered material"),
    lambda rows: rows[0].update(token_count=11),
    lambda rows: rows[0].update(reviewer_id=""),
    lambda rows: rows[0].update(reviewed_utc="2026-10-12T12:00:00"),
    lambda rows: rows.__setitem__(1, dict(rows[0])),
])
def test_invalid_or_tampered_review_is_not_imported(packet, mutate):
    root, prefix, _ = packet
    path = submitted(packet, mutate)
    with pytest.raises(ValueError):
        import_review(prefix.with_suffix(".json"), path, root/"invalid.json", "TEST_ROUND")
    assert not (root/"invalid.json").exists()


def test_empty_master_cannot_be_mistaken_for_human_review(packet):
    root, prefix, _ = packet
    with pytest.raises(ValueError, match="No completed review"):
        import_review(prefix.with_suffix(".json"), prefix.with_suffix(".csv"), root/"empty.json", "TEST_ROUND")
