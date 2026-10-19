"""Authored bridge fixtures only; no real corpus, model, journal or review mapping IO."""

import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import english_sfh_review_delivery_v1 as delivery


def authored_case(index):
    return {
        "speaker": "PRIVATE_SPEAKER_ID", "case_id": "PRIVATE_ORIGINAL_CASE_ID",
        "first_source_date": "2000-01-01T10:30:00", "first_source_meeting": "PRIVATE_SOURCE_MEETING",
        "history_date": "2000-02-01T11:30:00", "history_meeting": "PRIVATE_HISTORY_MEETING",
        "target_date": f"2000-03-0{index}T12:30:00", "target_meeting": "PRIVATE_TARGET_MEETING",
        "context": [{"speaker": "OTHER_PRIVATE_ID", "text": "What should we test next?",
                     "original_text_before_name_redaction": "PRIVATE_ORIGINAL_NAME_TEXT", "source_segment_ids": [900]},
                    {"speaker": "PRIVATE_SPEAKER_ID", "text": "Perhaps the parsing interface."}],
        "history": [{"speaker": "THIRD_PRIVATE_ID", "text": "How is the parser?"},
                    {"speaker": "PRIVATE_SPEAKER_ID", "text": "I tried the test suite yesterday."}],
        "style_examples": [{"speaker": "PRIVATE_SPEAKER_ID", "text": "Well, perhaps we can check it."}],
        "style": {"per_100_words": {"contractions": 123.456}},
        "structured_facts": [{"statement": "I wrote a parser.", "source_quote": "I wrote a parser yesterday.",
                              "source_date": "2000-01-01T10:30:00", "curation_basis": "PRIVATE_CURATOR_METADATA"}],
        "facts_source_selfreports_not_world_verified": [{"text": "I wrote a parser yesterday."}],
        "reference_continuation_not_for_prompt": {"text": "UNIQUE_WITHHELD_REFERENCE_NOT_A_GOLD", "start": 10.0},
        "seed": 999, "condition": "C7", "prompt": "PRIVATE_PROMPT_TEXT", "order": 999,
    }


def test_dossier_local_roles_exact_dates_and_no_private_metadata():
    case = authored_case(1)
    text = delivery.dossier(case)
    assert "[C1] Colleague 1: What should we test next?" in text
    assert "[H1] Colleague 2: How is the parser?" in text
    assert "[S1] Participant: Well, perhaps we can check it." in text
    assert "[F1] Recorded 2000-01-01T10:30:00" in text
    assert "I wrote a parser yesterday." in text
    assert "PRIVATE_" not in text and "WITHHELD" not in text
    assert "123.456" not in text and "C7" not in text and "999" not in text
    assert "2000-01-01T10:30:00Z" not in text


@pytest.mark.parametrize("field", ["source_quote", "source_date"])
def test_dossier_rejects_lost_fact_binding(field):
    case = authored_case(1)
    case["structured_facts"][0][field] = "unsupported changed field"
    with pytest.raises(ValueError, match="source binding"):
        delivery.dossier(case)


def test_reference_leak_and_foreign_style_example_rejected():
    case = authored_case(1)
    case["context"][0]["text"] += " UNIQUE_WITHHELD_REFERENCE_NOT_A_GOLD"
    with pytest.raises(ValueError, match="Reference continuation"):
        delivery.dossier(case)
    case = authored_case(1)
    case["style_examples"][0]["speaker"] = "OTHER_PRIVATE_ID"
    with pytest.raises(ValueError, match="another speaker"):
        delivery.dossier(case)


@pytest.fixture
def sealed_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(delivery.review, "PRIVATE_ROOT", tmp_path)
    monkeypatch.setattr(delivery, "PUBLIC", tmp_path / "public")
    monkeypatch.setattr(delivery, "PRIVATE", tmp_path / "private")
    monkeypatch.setattr(delivery, "DELIVERIES", tmp_path / "reviewer-packages")
    cases = [authored_case(2), authored_case(1)]
    requests = [{"request_id": f"authored_{index}", "speaker_id": "PRIVATE_SPEAKER_ID",
                 "case_id": f"PRIVATE_SPEAKER_ID_context{context}", "condition": condition}
                for index, (context, condition) in enumerate(((1, "C0"), (1, "C7"), (2, "C0"), (2, "C7")))]
    plan = {"batch": "development", "cases": cases, "requests": requests,
            "input_hashes": {**{relative: delivery.hashlib.sha256(Path(sys.modules[name].__file__).read_bytes()).hexdigest()
                                  for name, relative in delivery.LIVE_HELPERS.items()},
                "docs/validation/p1/english_real_speaker_stage_v1/human_review_rubric_v1.json": delivery.FROZEN_RUBRIC_SHA256}}
    manifest = delivery.PRIVATE / "development" / "frozen_manifest_v1.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(delivery.review.json_bytes(plan))
    manifest_hash = delivery.review.prior.sha256(manifest)
    folder = delivery.PRIVATE / "development" / "runs" / "authored_fixture"
    folder.mkdir(parents=True)
    receipt = {"batch": "development", "status": "PARTIAL", "manifest_sha256": manifest_hash,
               "responses": 2, "run_directory": str(folder), "terminal_event_sha256": "b" * 64}
    receipt_path = delivery.PUBLIC / "development_execution_receipt_v1.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_bytes(delivery.review.json_bytes(receipt))
    receipt_hash = delivery.review.prior.sha256(receipt_path)
    events = [{"kind": "english_sfh_raw", "data": {"request_id": requests[0]["request_id"],
                "response": {"content": "  Authored exact response.\n"}}},
              {"kind": "english_sfh_raw", "data": {"request_id": requests[1]["request_id"],
                "response": {"content": ""}}},
              {"kind": "run_finished", "event_hash": "b" * 64, "data": receipt}]
    monkeypatch.setattr(delivery.reproduction, "audit_run", lambda batch: (plan, receipt, [], 0, 0))
    monkeypatch.setattr(delivery.reproduction, "read_events", lambda path: events)
    return plan, receipt, events, manifest_hash, receipt_hash


def test_registry_sorting_common_dossier_and_raw_text_preservation(sealed_fixture):
    plan, _, _, manifest_hash, receipt_hash = sealed_fixture
    lookup = delivery.case_lookup(plan)
    assert lookup["PRIVATE_SPEAKER_ID_context1"]["target_date"] == "2000-03-01T12:30:00"
    rows, _ = delivery.sealed_records("development", manifest_hash, receipt_hash)
    assert len(rows) == 4 and rows[0]["dossier"] == rows[1]["dossier"]
    assert rows[0]["response"] == "  Authored exact response.\n"
    assert rows[1]["response"] == ""
    assert rows[2]["response"] is None and rows[3]["response"] is None


def test_unsealed_hash_or_raw_count_blocks_before_delivery(sealed_fixture):
    _, _, events, manifest_hash, receipt_hash = sealed_fixture
    with pytest.raises(ValueError, match="externally verified hash"):
        delivery.sealed_records("development", manifest_hash, "0" * 64)
    events[-1]["kind"] = "still_running"
    with pytest.raises(ValueError, match="not sealed"):
        delivery.prepare("development", manifest_hash, receipt_hash)
    assert not delivery.DELIVERIES.exists()
    events[-1]["kind"] = "run_finished"
    events.insert(0, copy.deepcopy(events[0]))
    with pytest.raises(ValueError, match="count/identity"):
        delivery.prepare("development", manifest_hash, receipt_hash)
    assert not delivery.DELIVERIES.exists()


@pytest.mark.parametrize("module_name", tuple(delivery.LIVE_HELPERS))
def test_changed_live_helper_rejected_before_audit_or_delivery(sealed_fixture, monkeypatch, module_name):
    _, _, _, manifest_hash, receipt_hash = sealed_fixture
    target = Path(sys.modules[module_name].__file__).resolve()
    original = Path.read_bytes

    def changed_bytes(path):
        value = original(path)
        return value + b"\n# authored changed helper\n" if path.resolve() == target else value

    def forbidden_audit(batch):
        pytest.fail("Changed live helper reached evidence audit")

    monkeypatch.setattr(Path, "read_bytes", changed_bytes)
    monkeypatch.setattr(delivery.reproduction, "audit_run", forbidden_audit)
    with pytest.raises(ValueError, match="Live helper differs from frozen input"):
        delivery.prepare("development", manifest_hash, receipt_hash)
    assert not delivery.DELIVERIES.exists()


def test_builds_blank_fixed_private_package_and_hash_only_public_receipt(sealed_fixture):
    _, _, _, manifest_hash, receipt_hash = sealed_fixture
    report = delivery.prepare("development", manifest_hash, receipt_hash)
    assert report["records"] == 4 and report["generated_outcomes"] == report["missing_outcomes"] == 2
    assert report["human_labels_created"] == 0
    public = json.dumps(report)
    assert "PRIVATE_SPEAKER" not in public and "Authored exact response" not in public
    assert "protected_mapping" not in public
    directory = delivery.DELIVERIES / "english_sfh_development_v1"
    assert (directory / "records.html").exists()
    assert not (directory / "protected_mapping_v1.json").exists()
    with pytest.raises(ValueError, match="no rebuild"):
        delivery.prepare("development", manifest_hash, receipt_hash)
