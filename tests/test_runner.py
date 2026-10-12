"""All inference in this file is a TEST DOUBLE, never evidence of real inference."""
from dataclasses import replace
from dataclasses import asdict
import json

import pytest

from personaslm.configuration import RuntimeConfig
from personaslm.fixtures import build_cases
from personaslm.journal import read_events
from personaslm.runner import run_local, validate_completion
from personaslm.conditioning import build_prompt
from personaslm.schemas import Case
from test_configuration import configured


@pytest.fixture
def case_file(local_tmp):
    path = local_tmp / "cases.jsonl"
    path.write_text(json.dumps(build_cases()[0]) + "\n", encoding="utf-8")
    return path


class StubServer:
    closed = False

    def __init__(self, config, journal):
        self.config = config

    def __enter__(self):
        return self

    def __exit__(self, *_):
        type(self).closed = True

    def assert_running(self):
        pass


def client_factory(config, response_override=None):
    class StubClient:
        completions = 0

        def __init__(self, *_, **kwargs):
            pass

        def request(self, route):
            assert route == "/props"
            return {"model_path": config.model_file, "default_generation_settings": {"n_ctx": config.n_ctx},
                    "build_info": "unit-test-double"}

        def tokenize(self, text):
            return [1, 2, 3]  # TEST DOUBLE, not actual tokenization

        def complete(self, ids, **kwargs):
            type(self).completions += 1
            return {"content": "Assistant: Paris", "tokens": [10, 11], "stop_type": "eos",
                    "tokens_evaluated": len(ids), "prompt": ids, "truncated": False,
                    **(response_override or {})}

    return StubClient


def test_no_model_records_blocked_without_launch(local_tmp, case_file):
    def forbidden(*_, **kwargs):
        pytest.fail("Missing configuration must not start a process or send HTTP")
    summary, directory = run_local(RuntimeConfig(), "C0", case_file, local_tmp,
                                  server_factory=forbidden, client_factory=forbidden)
    assert summary["status"] == "BLOCKED"
    assert summary["real_inference_performed"] is False
    assert read_events(directory)[-1]["data"]["completed_cases"] == 0


def test_success_logs_frozen_prompts_raw_parser_and_result(configured, local_tmp, case_file):
    stub = client_factory(configured)
    summary, directory = run_local(configured, "C0", case_file, local_tmp, client_factory=stub, server_factory=StubServer)
    assert summary["status"] == "PASS"
    events = read_events(directory)
    kinds = [event["kind"] for event in events]
    assert kinds.index("prompt_prepared") < kinds.index("generation_started") < kinds.index("raw_generation")
    assert kinds.index("raw_generation") < kinds.index("parser_audit") < kinds.index("case_result")
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["applicability"]["synthetic_001"] == build_cases()[0]["applicability"]
    raw = next(e["data"] for e in events if e["kind"] == "raw_generation")
    assert raw["response"]["content"] == "Assistant: Paris"
    assert stub.completions == 1 and StubServer.closed


def test_parser_failure_keeps_raw_and_never_scores(configured, local_tmp, case_file, monkeypatch):
    def fail(*_, **kwargs):
        raise ValueError("injected parser failure")
    monkeypatch.setattr("personaslm.runner.parse_reply", fail)
    summary, directory = run_local(configured, "C0", case_file, local_tmp,
                                  client_factory=client_factory(configured), server_factory=StubServer)
    events = read_events(directory)
    assert summary["status"] == "BLOCKED"
    assert any(event["kind"] == "raw_generation" for event in events)
    assert not any(event["kind"] == "case_result" for event in events)
    assert any("injected parser failure" in str(event) for event in events)


@pytest.mark.parametrize("override", [{"tokens_evaluated": 4}, {"truncated": True},
                                      {"content": None}, {"prompt": [9, 8, 7]}])
def test_response_mismatch_preserves_failure_artifact(configured, local_tmp, case_file, override):
    summary, directory = run_local(configured, "C0", case_file, local_tmp,
                                  client_factory=client_factory(configured, override), server_factory=StubServer)
    assert summary["status"] == "BLOCKED"
    assert any(event["kind"] == "raw_generation" for event in read_events(directory))


def test_context_budget_fails_before_generation(configured, local_tmp, case_file):
    config = replace(configured, n_ctx=4, max_new_tokens=2)
    stub = client_factory(config)
    summary, _ = run_local(config, "C0", case_file, local_tmp, client_factory=stub, server_factory=StubServer)
    assert summary["status"] == "BLOCKED"
    assert stub.completions == 0


def test_missing_generated_ids_is_partial_not_full_pass(configured, local_tmp, case_file):
    summary, _ = run_local(configured, "C0", case_file, local_tmp,
                          client_factory=client_factory(configured, {"tokens": None}), server_factory=StubServer)
    assert summary["status"] == "PARTIAL"
    assert summary["completed_cases"] == 1
    assert "token IDs absent" in summary["limitations"][0]


def test_second_case_failure_keeps_first_case_and_both_raw_responses(configured, local_tmp):
    cases = local_tmp / "two-cases.jsonl"
    cases.write_text("\n".join(json.dumps(c) for c in build_cases()[:2]), encoding="utf-8")
    base = client_factory(configured)
    class SecondFailure(base):
        def complete(self, ids, **kwargs):
            response = super().complete(ids, **kwargs)
            if type(self).completions == 2:
                response["content"] = None
            return response
    summary, directory = run_local(configured, "C0", cases, local_tmp,
                                  client_factory=SecondFailure, server_factory=StubServer)
    assert summary["status"] == "PARTIAL"
    assert summary["completed_cases"] == 1
    kinds = [event["kind"] for event in read_events(directory)]
    assert kinds.count("raw_generation") == 2
    assert kinds.count("case_result") == 1


@pytest.mark.parametrize("result", [{}, {"tokens_evaluated": True, "truncated": False},
                                   {"tokens_evaluated": 1}, {"tokens_evaluated": 1, "truncated": True}])
def test_token_evidence_cannot_be_assumed(result):
    with pytest.raises(ValueError):
        validate_completion(result, [1])


def test_frozen_token_mismatch_blocks_all_generation(configured, local_tmp, case_file):
    case = Case.from_dict(build_cases()[0])
    frozen = {case.case_id: {"C0": {"prompt": asdict(build_prompt(case, "C0")),
              "token_ids": [99], "matching": {"status": "reference"}}}}
    stub = client_factory(configured)
    summary, directory = run_local(configured, "C0", case_file, local_tmp,
        client_factory=stub, server_factory=StubServer, frozen_prompts=frozen)
    assert summary["status"] == "BLOCKED" and stub.completions == 0
    assert "Tokenizer changed after prompt freeze" in str(read_events(directory))


def test_new_manifest_retains_exact_dataset_and_source(configured, local_tmp, case_file):
    _, directory = run_local(configured, "C0", case_file, local_tmp,
        client_factory=client_factory(configured), server_factory=StubServer)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    snapshot = manifest["reconstruction"]
    assert snapshot["dataset_utf8"].encode("utf-8") == case_file.read_bytes()
    assert "evaluation.py" in snapshot["source_utf8"]
    assert {"commit", "dirty", "status_porcelain"} <= snapshot["git"].keys()
