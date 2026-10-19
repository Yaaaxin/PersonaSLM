"""Authored two-journal delivery fixtures; never open participant evidence."""

import copy
import json
from pathlib import Path

import pytest

import english_sfh_combined_review_v1 as bridge
from test_english_sfh_review_delivery_v1 import authored_case


def bound_helpers():
    root = Path(bridge.__file__).resolve().parents[1]
    paths = bridge.combined.original.shared.runtime_python_dependency_paths(
        [Path(bridge.combined.__file__), Path(bridge.delivery.__file__)])
    hashes = {path.resolve().relative_to(root).as_posix(): bridge.sha(path) for path in paths}
    hashes["docs/validation/p1/english_real_speaker_stage_v1/human_review_rubric_v1.json"] = bridge.sha(bridge.review.RUBRIC)
    return {"source_hashes": {}, "input_hashes": hashes}


def test_all_actual_import_helpers_bound_before_evidence_read():
    plan = bound_helpers()
    bridge.verify_helpers(plan, copy.deepcopy(plan))


@pytest.mark.parametrize("module", [bridge.combined, bridge.resume, bridge.review,
                                    bridge.combined.original.shared])
def test_changed_helper_rejected(module, monkeypatch):
    plan = bound_helpers()
    target = Path(module.__file__).resolve()
    original_sha = bridge.sha
    monkeypatch.setattr(bridge, "sha", lambda path: "0" * 64 if Path(path).resolve() == target else original_sha(path))
    with pytest.raises(ValueError, match="helper"):
        bridge.verify_helpers(plan, copy.deepcopy(plan))


@pytest.fixture
def sealed(tmp_path, monkeypatch):
    public, private = tmp_path / "public", tmp_path / "private"
    public.mkdir()
    private.mkdir()
    monkeypatch.setattr(bridge, "PUBLIC", public)
    monkeypatch.setattr(bridge, "PRIVATE", private)
    monkeypatch.setattr(bridge.review, "PRIVATE_ROOT", tmp_path)
    monkeypatch.setattr(bridge.delivery, "DELIVERIES", tmp_path / "reviewer-packages")
    monkeypatch.setattr(bridge, "verify_helpers", lambda parent, suffix: None)
    parent_path, suffix_path = private / "parent.json", private / "suffix.json"
    monkeypatch.setattr(bridge.resume, "PARENT_MANIFEST", parent_path)
    monkeypatch.setattr(bridge.resume, "MANIFEST", suffix_path)

    def write(path, value):
        path.write_bytes(bridge.review.json_bytes(value))
        return bridge.sha(path)

    cases, requests = [], []
    conditions = [f"C{i}" for i in range(8)] + ["M_STYLE", "N_STYLE"]
    for speaker in range(5):
        identity = f"AUTHORED_SPEAKER{speaker}"
        for context in (1, 2):
            case = authored_case(context)
            case["speaker"] = identity
            for field in ("context", "history", "style_examples"):
                for turn in case[field]:
                    if turn["speaker"] == "PRIVATE_SPEAKER_ID":
                        turn["speaker"] = identity
            cases.append(case)
            requests.extend({"request_id": f"AUTHORED_{speaker}_{context}_{condition}",
                             "speaker_id": identity, "case_id": f"{identity}_context{context}",
                             "condition": condition} for condition in conditions)
    parent = {"cases": cases, "requests": requests}
    parent_sha = write(parent_path, parent)
    suffix_sha = write(suffix_path, {"requests": requests[92:]})
    monkeypatch.setattr(bridge.resume, "PARENT_SHA", parent_sha)
    event_sets, receipts, receipt_hashes = {}, [], []
    for index, rows in enumerate((requests[:92], requests[92:])):
        folder = private / f"authored_run{index}"
        folder.mkdir()
        events = []
        for offset, row in enumerate(rows):
            content = "  Authored response with exact whitespace.\n" if offset else ""
            events += [{"kind": "english_sfh_started", "data": row},
                       {"kind": "english_sfh_raw", "data": {"request_id": row["request_id"],
                        "response": {"content": content}}}]
        tail = str(index + 1) * 64
        events.append({"kind": "run_finished", "event_hash": tail})
        event_sets[str(folder)] = events
        receipt = {"run_directory": str(folder), "terminal_event_sha256": tail}
        name = "development_execution_receipt_v1.json" if index == 0 else bridge.resume.BATCH + "_execution_receipt_v1.json"
        receipt_hashes.append(write(public / name, receipt))
        receipts.append(receipt)
    monkeypatch.setattr(bridge.resume, "RECEIPT_SHA", receipt_hashes[0])
    monkeypatch.setattr(bridge.combined.independent, "read_events", lambda path: event_sets[str(path)])
    bindings = {"original_manifest_sha256": parent_sha, "original_partial_receipt_sha256": receipt_hashes[0],
                "suffix_manifest_sha256": suffix_sha, "suffix_receipt_sha256": receipt_hashes[1],
                "original_terminal_sha256": receipts[0]["terminal_event_sha256"],
                "suffix_terminal_sha256": receipts[1]["terminal_event_sha256"]}
    analysis = {"bindings": bindings, "status": "COMPLETE_OBSERVATIONS", "allocated": 100,
                "attempts": 100, "responses": 100, "missing_responses": 0, "failed_suffix_calls": 0,
                "new_generation_retries": 0, "human_labels_created": 0, "cumulative_generations": 788,
                "cumulative_inference_seconds": 4500.0, "run_receipts": receipts}
    analysis_sha = write(public / "development_combined_analysis_v1.json", analysis)
    rows_sha = write(private / "development_combined_analysis_private_v1.json", {"rows": []})
    reproduced = {"bindings": bindings, "status": "PASS", "analysis_sha256": analysis_sha,
                  "private_file_sha256": rows_sha, "human_labels_created": 0,
                  **{key: analysis[key] for key in ("responses", "attempts", "cumulative_generations", "cumulative_inference_seconds")}}
    reproduction_sha = write(public / "development_combined_independent_reproduction_v1.json", reproduced)
    monkeypatch.setattr(bridge.combined, "analyze", lambda write=False: analysis)
    return analysis_sha, reproduction_sha, event_sets, analysis


def test_full_fixed_grid_preserves_raw_empty_and_whitespace_responses(sealed):
    analysis_sha, reproduction_sha, _, _ = sealed
    records, _ = bridge.sealed_records(analysis_sha, reproduction_sha)
    assert len(records) == 100 and len({row["request_id"] for row in records}) == 100
    assert records[0]["response"] == "" and records[1]["response"] == "  Authored response with exact whitespace.\n"
    assert records[92]["response"] == ""
    assert records[0]["dossier"] == records[9]["dossier"]
    assert "PRIVATE_" not in records[0]["dossier"]


@pytest.mark.parametrize("corruption", ["unsealed", "duplicate", "missing", "changed_analysis", "changed_receipt"])
def test_corruption_blocks_before_package_creation(sealed, corruption):
    analysis_sha, reproduction_sha, events, analysis = sealed
    second = list(events.values())[1]
    if corruption == "unsealed":
        second[-1]["kind"] = "still_running"
    elif corruption == "duplicate":
        second.insert(0, copy.deepcopy(list(events.values())[0][0]))
    elif corruption == "missing":
        second.pop(1)
    elif corruption == "changed_analysis":
        analysis["cumulative_generations"] += 1
    else:
        (bridge.PUBLIC / (bridge.resume.BATCH + "_execution_receipt_v1.json")).write_text("{}", encoding="utf-8")
    with pytest.raises((ValueError, AssertionError)):
        bridge.prepare(analysis_sha, reproduction_sha)
    assert not bridge.delivery.DELIVERIES.exists()


def test_blank_private_package_and_hash_only_public_receipt(sealed):
    analysis_sha, reproduction_sha, _, _ = sealed
    report = bridge.prepare(analysis_sha, reproduction_sha)
    assert report["records"] == 100 and report["human_labels_created"] == 0
    text = json.dumps(report)
    assert "AUTHORED_SPEAKER" not in text and "Authored response" not in text
    assert "protected_mapping" not in text
    directory = bridge.delivery.DELIVERIES / "english_sfh_development_v1"
    assert (directory / "records.html").is_file()
    assert not (directory / "protected_mapping_v1.json").exists()
    provenance = json.loads((directory / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["independent_of_project"] is False and provenance["human_reviewer"] is None
    with pytest.raises(ValueError, match="no overwrite"):
        bridge.prepare(analysis_sha, reproduction_sha)
