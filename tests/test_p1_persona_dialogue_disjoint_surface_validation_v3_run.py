"""Offline end-to-end failure tests for the V3 one-shot ``run`` action."""

import base64
from collections import Counter
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import tempfile

import pytest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import p1_persona_dialogue_disjoint_surface_validation_v3 as module


@pytest.fixture(autouse=True)
def repository_cwd(monkeypatch):
    monkeypatch.chdir(REPO)


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        self.value += 1.0
        return self.value


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _row(index):
    current = {"A": f"V3T{index:03d}A", "B": f"V3T{index:03d}B"}
    return {
        "order": index,
        "request_id": f"offline_v3_{index:03d}",
        "request_sha256": f"{index:064x}",
        "prompt": f"offline prompt {index}",
        "input_token_ids": [index + 1],
        "max_new_tokens": 96,
        "temperature": 0.0,
        "top_p": 1.0,
        "seed": 42,
        "preferred_option": "A",
        "options": {
            "A": {"canonical": f"Current Alpha {index}"},
            "B": {"canonical": f"Current Beta {index}"},
        },
        "anchors": {
            "current": current,
            "history": {
                "aligned": f"V3T{index:03d}H1",
                "conflict": f"V3T{index:03d}H2",
                "irrelevant": f"V3T{index:03d}H3",
            },
        },
    }


def _response(row):
    return {
        "content": (f"Option A [{row['anchors']['current']['A']}] — "
                    f"{row['options']['A']['canonical']}."),
        "stop_type": "eog",
        "stopped_eos": True,
        "truncated": False,
        "tokens_evaluated": len(row["input_token_ids"]),
        "prompt": row["input_token_ids"],
        "tokens_predicted": 1,
        "tokens": [900000 + row["order"]],
    }


def _run_with_offline_failure(monkeypatch, failure_index):
    with ExitStack() as stack:
        local = Path(stack.enter_context(tempfile.TemporaryDirectory(
            prefix="dsv3-run-e2e-", dir=REPO / ".local")))
        root = local / "results"
        frozen = local / "frozen.json"
        prepared = local / "preflight.json"
        authorization = local / "authorization.json"
        rows = [_row(index) for index in range(module.MAX_ATTEMPTS)]
        plan = {
            "authorization_path": authorization.as_posix(),
            "model": {
                "model_file": "tools/p1_persona_dialogue_disjoint_surface_validation_v3.py",
                "model_sha256": "0" * 64,
                "backend_file": "tools/p1_persona_dialogue_disjoint_surface_validation_v3.py",
                "model_label": "OFFLINE_TEST_DOUBLE",
            },
            "resource_budget": {
                "batch_wall_seconds_ceiling": 100000.0,
                "actual_completion_inference_seconds_ceiling": 100000.0,
            },
            "requests": rows,
        }
        _write_json(authorization, {"status": "OFFLINE_TEST_FIXTURE"})
        _write_json(frozen, plan)
        configuration = module.cfg(plan).as_dict()
        fresh = {
            "status": "PASS",
            "manifest_sha256": "1" * 64,
            "authorization_sha256": "2" * 64,
            "design_sha256": "3" * 64,
            "case_bank_sha256": "4" * 64,
            "review_schema_sha256": "5" * 64,
            "material_audit_sha256": "6" * 64,
            "source_hashes": {},
            "configuration": configuration,
            "server_command": ["OFFLINE_TEST_DOUBLE"],
            "identity": {"fixture": True},
        }
        _write_json(prepared, fresh)

        class Server:
            assertions = 0

            def __init__(self, supplied_plan, journal):
                assert supplied_plan == plan
                self.journal = journal

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def assert_running(self):
                type(self).assertions += 1

        class Client:
            completion_payloads = []
            tokenized_prompts = []

            def __init__(self, endpoint, timeout, audit):
                self.timeout = timeout
                self.audit = audit

            def request(self, route, value=None):
                if route == "/props":
                    return {"offline": True}
                if route == "/tokenize":
                    self.tokenized_prompts.append(value["content"])
                    index = int(value["content"].rsplit(" ", 1)[1])
                    return {"tokens": rows[index]["input_token_ids"]}
                assert route == "/completion"
                index = len(self.completion_payloads)
                self.completion_payloads.append(value)
                self.audit("http_request", {"route": route, "payload": value})
                if index == failure_index:
                    self.audit("http_error", {"route": route,
                                               "type": "RuntimeError",
                                               "error": "offline injected failure",
                                               "elapsed_seconds": 1.0})
                    raise RuntimeError("offline injected failure")
                response = _response(rows[index])
                self.audit("http_response", {
                    "route": route,
                    "status": 200,
                    "body_base64": base64.b64encode(json.dumps(
                        response).encode("utf-8")).decode("ascii"),
                    "elapsed_seconds": 1.0,
                })
                return response

        clock = Clock()
        monkeypatch.setattr(module, "ROOT", root)
        monkeypatch.setattr(module, "FROZEN", frozen)
        monkeypatch.setattr(module, "PREFLIGHT", prepared)
        monkeypatch.setattr(module, "preflight", lambda *_, **__: dict(fresh))
        monkeypatch.setattr(module.s, "Server", Server)
        monkeypatch.setattr(module.b, "LlamaClient", Client)
        monkeypatch.setattr(module.b, "validate_server_properties",
                            lambda *_: {"build_info": "b11573-0f701c882"})
        monkeypatch.setattr(module.subprocess, "check_output",
                            lambda command, **_: ("test-head" if command[1] ==
                                                  "rev-parse" else ""))
        monkeypatch.setattr(module.time, "monotonic", clock)

        summary = module.run(prepared)
        run_directory = Path(summary["run_directory"])
        events = module.b.read_events(run_directory)
        return summary, events, rows, list(Client.completion_payloads), \
            list(Client.tokenized_prompts), Server.assertions


@pytest.mark.parametrize("failure_index", [0, 84, 167],
                         ids=["first", "middle", "last"])
def test_actual_run_stops_after_one_failed_attempt_and_preserves_prefix(
        monkeypatch, failure_index):
    summary, events, rows, sent, tokenized, server_assertions = \
        _run_with_offline_failure(monkeypatch, failure_index)
    attempted = failure_index + 1
    completed = failure_index

    assert summary["status"] == "PARTIAL"
    assert summary["attempted"] == attempted
    assert summary["responses_received"] == completed
    assert summary["results"] == completed
    assert summary["retries"] == summary["hidden_warmups"] == 0
    assert summary["inference_wall_seconds"] == pytest.approx(float(attempted))
    assert summary["failed_completion_seconds"] == pytest.approx(1.0)
    assert summary["batch_wall_seconds"] >= summary["inference_wall_seconds"]

    assert tokenized == [row["prompt"] for row in rows]
    assert sent == [module.payload(row) for row in rows[:attempted]]
    assert server_assertions == attempted

    started = [event["data"] for event in events
               if event["kind"] == module.STARTED]
    raw = [event["data"] for event in events if event["kind"] == module.RAW]
    derived = [event["data"] for event in events
               if event["kind"] == module.DERIVED]
    assert [item["request_id"] for item in started] == [
        row["request_id"] for row in rows[:attempted]]
    assert Counter(item["request_id"] for item in started) == Counter(
        {row["request_id"]: 1 for row in rows[:attempted]})
    assert [item["request_id"] for item in raw] == [
        row["request_id"] for row in rows[:completed]]
    assert [item["request_id"] for item in derived] == [
        row["request_id"] for row in rows[:completed]]
    assert all(item["latency_seconds"] == pytest.approx(1.0) for item in raw)
    assert all(item["latency_seconds"] == pytest.approx(1.0)
               for item in derived)

    failed = [event["data"] for event in events if event["kind"] ==
              "disjoint_surface_validation_v3_completion_failed"]
    assert failed == [{"request_id": rows[failure_index]["request_id"],
                       "elapsed_seconds": 1.0}]
    terminal_failure = [event["data"] for event in events
                        if event["kind"] == "failure"]
    assert terminal_failure == [{
        "type": "RuntimeError",
        "message": "offline injected failure",
        "request_id": rows[failure_index]["request_id"],
    }]
    assert events[-1]["kind"] == "run_finished"
    assert events[-1]["data"] == summary
