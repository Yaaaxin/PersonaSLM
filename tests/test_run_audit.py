"""Synthetic journal fixtures only; no model generation in tests."""
import base64
from dataclasses import asdict
import json

import pytest

from personaslm.conditioning import build_prompt
from personaslm.configuration import RuntimeConfig
from personaslm.diagnostics import parse_reply
from personaslm.evaluation import judge_current_city
from personaslm.fixtures import build_cases
from personaslm.inference import normalize_result
from personaslm.journal import RunJournal
from personaslm.provenance import sha256
from personaslm.reproducibility import source_snapshot
from personaslm.run_audit import audit_run, text_hash
from personaslm.schemas import Case


def make_run(local_tmp, *, duplicate=False, wrong_tokens=False, wrong_evaluation=False):
    dataset = local_tmp / "dataset.jsonl"
    dataset.write_text(json.dumps(build_cases()[0])+"\n", encoding="utf-8")
    snapshot = source_snapshot(dataset)
    case = Case.from_dict(build_cases()[0])
    config = RuntimeConfig()
    journal = RunJournal(local_tmp, {"case_ids": [case.case_id], "condition": "C0", "cases_sha256": sha256(dataset),
        "cases_file": str(dataset), "configuration": config.as_dict(), "reconstruction": snapshot,
        "source_sha256": snapshot["source_sha256"]})
    def http(route, request, response):
        journal.write("http_request", {"route": route, "payload": request})
        journal.write("http_response", {"route": route, "status": 200, "elapsed_seconds": 0.1,
            "body_base64": base64.b64encode(json.dumps(response).encode()).decode()})
    prompt = build_prompt(case, "C0")
    http("/tokenize", {"content": prompt.text, "add_special": True, "parse_special": False}, {"tokens": [1, 2]})
    prepared = {"case_id": case.case_id, "prompt": asdict(prompt), "prompt_token_ids": [1, 2], "prompt_tokens": 2,
                "prompt_sha256": text_hash(prompt.text)}
    journal.write("prompt_prepared", prepared)
    if duplicate:
        journal.write("prompt_prepared", prepared)
    journal.write("generation_started", {"case_id": case.case_id})
    raw = {"content": " Paris", "stop_type": "eos", "tokens": [3], "tokens_predicted": 1,
           "tokens_evaluated": 2, "prompt": prompt.text, "truncated": False}
    http("/completion", {"prompt": [9, 9] if wrong_tokens else [1, 2], "seed": 42, "n_predict": 96,
        "temperature": 0.0, "top_p": 1.0, "stop": [], "return_tokens": True, "cache_prompt": False}, raw)
    journal.write("raw_generation", {"case_id": case.case_id, "response": raw})
    parsed = parse_reply(raw["content"], stop_reason="eos")
    journal.write("parser_audit", {"case_id": case.case_id, **parsed.audit(), "parsed_response": parsed.parsed_text})
    judgment = judge_current_city(case, parsed.parsed_text)
    journal.write("case_result", {"case_id": case.case_id, "condition": "C0", **normalize_result(raw),
        "parsed_response": parsed.parsed_text, "fact_accuracy": "incorrect" if wrong_evaluation else judgment.status,
        "fact_reason": judgment.reason})
    journal.finish("PASS", completed_cases=1)
    return journal.directory


def test_offline_replay_reconstructs_and_is_identical(local_tmp):
    directory = make_run(local_tmp)
    first = audit_run(directory)
    assert first == audit_run(directory)
    assert first["status"] == "PASS"
    assert first["cases"][0]["evaluated_input_token_ids"] is None
    assert first["cases"][0]["classification"] == "preserved"


@pytest.mark.parametrize("flag,expected", [("duplicate", "duplicate"), ("wrong_tokens", "submitted_ids"), ("wrong_evaluation", "evaluation_replay")])
def test_audit_detects_valid_chain_with_semantic_inconsistency(local_tmp, flag, expected):
    result = audit_run(make_run(local_tmp, **{flag: True}))
    assert result["status"] == "PARTIAL"
    assert expected in str(result["issues"] + result["cases"][0]["errors"])


def test_embedded_dataset_survives_external_dataset_change(local_tmp):
    directory = make_run(local_tmp)
    (local_tmp / "dataset.jsonl").write_text("different", encoding="utf-8")
    assert audit_run(directory)["status"] == "PASS"


def test_journal_tampering_fails_before_replay(local_tmp):
    directory = make_run(local_tmp)
    path = directory / "events/000001.json"
    path.write_text(path.read_text().replace('"/tokenize"', '"/completion"'), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        audit_run(directory)


def test_replay_cli_refuses_writing_inside_original_run(local_tmp, capsys):
    from personaslm.cli import main
    directory = make_run(local_tmp)
    with pytest.raises(SystemExit) as exc:
        main(["replay-run", "--run-dir", str(directory), "--output", str(directory / "new.json")])
    assert exc.value.code == 2
    assert "outside the immutable original run" in capsys.readouterr().out
    assert not (directory / "new.json").exists()
