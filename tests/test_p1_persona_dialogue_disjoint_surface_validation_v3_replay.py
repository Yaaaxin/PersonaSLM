import base64
import hashlib
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import p1_persona_dialogue_disjoint_surface_validation_v3 as module


@pytest.fixture(autouse=True)
def repository_cwd(monkeypatch):
    monkeypatch.chdir(REPO)


def _mock_partial_replay(monkeypatch, tmp_path, body):
    root = tmp_path / "root"
    folder = root / "runs" / "run-1"
    folder.mkdir(parents=True)
    authorization_path = tmp_path / "authorization.json"
    rows = [{
        "order": index, "request_id": f"r{index:03d}",
        "request_sha256": f"request-{index}", "input_token_ids": [index + 1],
        "max_new_tokens": 3, "temperature": 0.0, "top_p": 1.0,
        "seed": 42,
    } for index in range(module.MAX_ATTEMPTS)]
    plan = {"authorization_path": authorization_path.as_posix(),
            "requests": rows}
    authorization = {"researcher": "unit-test"}
    claim = {
        "manifest_sha256": "sha", "authorization_sha256": "sha",
        "design_sha256": module.DESIGN_SHA,
        "case_bank_sha256": module.CASE_BANK_SHA,
        "review_schema_sha256": module.REVIEW_SCHEMA_SHA,
        "material_audit_sha256": module.MATERIAL_AUDIT_SHA,
        "preflight_sha256": "sha", "maximum_attempts": module.MAX_ATTEMPTS,
        "retries": 0, "hidden_warmups": 0, "source_hashes": {},
    }
    manifest = {"claim": claim, "frozen_manifest": plan,
                "authorization": authorization}
    summary = {"status": "PARTIAL", "attempted": 1,
               "responses_received": 0, "results": 0, "retries": 0,
               "hidden_warmups": 0, "inference_wall_seconds": 0.25}
    events = [
        *[{"kind": "live_prompt_verified",
           "data": {"request_id": row["request_id"]}} for row in rows],
        {"kind": module.STARTED, "data": rows[0]},
        {"kind": "http_request", "data": {
            "route": "/completion", "payload": module.payload(rows[0])}},
        {"kind": "http_response", "data": {
            "route": "/completion", "status": 200,
            "body_base64": base64.b64encode(body).decode("ascii"),
            "elapsed_seconds": 0.25}},
        {"kind": "failure", "data": {"request_id": rows[0]["request_id"]}},
        {"kind": "run_finished", "data": summary},
    ]

    def fake_load(path):
        path = Path(path)
        if path == module.FROZEN:
            return plan
        if path == root / "claim.json":
            return claim
        if path == folder / "manifest.json":
            return manifest
        if path == folder / "summary.json":
            return summary
        if path == authorization_path:
            return authorization
        raise AssertionError(path)

    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "load", fake_load)
    monkeypatch.setattr(module, "sha256", lambda _path: "sha")
    monkeypatch.setattr(module, "validate_plan", lambda _plan: None)
    monkeypatch.setattr(module.b, "read_events", lambda _folder: events)
    return rows, body


def test_replay_recovers_complete_http_200_without_raw(monkeypatch, tmp_path):
    response = {"content": "wire-only"}
    body = json.dumps(response, separators=(",", ":")).encode("utf-8")
    rows, _ = _mock_partial_replay(monkeypatch, tmp_path, body)
    reconstructed = {"request_id": rows[0]["request_id"], "response": response,
                     "latency_seconds": 0.25}
    monkeypatch.setattr(module, "result", lambda *_args: reconstructed)

    _, _, replay_rows, body_count, evidence = module.replay()

    assert len(replay_rows) == module.MAX_ATTEMPTS == 168
    assert replay_rows[0] == (rows[0], reconstructed, "HTTP_BODY_RECOVERABLE")
    assert all(item[2] == "UNATTEMPTED" for item in replay_rows[1:])
    assert body_count == 1
    assert evidence[rows[0]["request_id"]]["http_status"] == 200
    assert evidence[rows[0]["request_id"]]["http_body_sha256"] == \
        hashlib.sha256(body).hexdigest()


def test_replay_keeps_malformed_http_200_as_unresolved(monkeypatch, tmp_path):
    response = {"malformed_completion": True}
    body = json.dumps(response, separators=(",", ":")).encode("utf-8")
    rows, _ = _mock_partial_replay(monkeypatch, tmp_path, body)

    def fail_derivation(*_args):
        raise ValueError("malformed completion response")

    monkeypatch.setattr(module, "result", fail_derivation)

    _, _, replay_rows, body_count, evidence = module.replay()

    first = evidence[rows[0]["request_id"]]
    assert len(replay_rows) == module.MAX_ATTEMPTS == 168
    assert replay_rows[0] == (rows[0], None, "ATTEMPTED_UNRESOLVED")
    assert body_count == 1
    assert first["http_body_sha256"] == hashlib.sha256(body).hexdigest()
    assert first["result_derivation_error"] == {
        "type": "ValueError", "message": "malformed completion response"}
