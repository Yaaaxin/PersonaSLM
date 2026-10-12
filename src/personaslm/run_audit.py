"""Offline reconstruction audit. Never executes saved source or modifies a run."""
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path

from .diagnostics import parse_reply
from .evaluation import judge_current_city
from .inference import normalize_result
from .journal import read_events
from .provenance import repository_root, require_local_path, sha256
from .schemas import Case


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def audit_run(directory, cases_path=None):
    directory = require_local_path(Path(directory))
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    events = read_events(directory)
    reconstruction = manifest.get("reconstruction", {})
    dataset = reconstruction.get("dataset_utf8")
    if dataset is None:
        path = require_local_path(Path(cases_path or manifest["cases_file"]))
        if sha256(path) != manifest["cases_sha256"]:
            raise ValueError("Historical dataset does not match saved hash")
        dataset = path.read_bytes().decode("utf-8")
    if text_hash(dataset) != manifest["cases_sha256"]:
        raise ValueError("Dataset snapshot digest mismatch")
    cases = {c.case_id: c for c in (Case.from_dict(json.loads(line)) for line in dataset.splitlines() if line.strip())}
    issues = []
    if not events or events[-1]["kind"] != "run_finished":
        issues.append("run has no terminal event")
    missing = []
    if not reconstruction:
        missing += ["run-time Git commit/dirty state", "embedded dataset/source snapshots", "explicit prompt SHA-256"]
    for name, digest in manifest["source_sha256"].items():
        saved = reconstruction.get("source_utf8", {}).get(name)
        if saved is not None and text_hash(saved) != digest:
            issues.append(f"source snapshot digest mismatch: {name}")
    # Replaying different parser/evaluator code must not silently certify the old run.
    for name in ("diagnostics.py", "evaluation.py", "inference.py"):
        if sha256(repository_root() / "src/personaslm" / name) != manifest["source_sha256"].get(name):
            issues.append(f"current replay implementation differs: {name}")
    index = {}
    for event in events:
        kind, data = event["kind"], event["data"]
        if kind in ("prompt_prepared", "generation_started", "raw_generation", "parser_audit", "case_result"):
            key = (kind, data["case_id"])
            if key in index:
                issues.append(f"duplicate case event: {key}")
            index[key] = event
    pending = None
    tokenizations, completions = [], []
    for event in events:
        if event["kind"] == "http_request":
            pending = event
        elif event["kind"] == "http_response" and pending:
            response = event["data"]
            request = pending["data"]
            if request["route"] != response["route"]:
                issues.append("HTTP route association mismatch")
            if response["status"] == 200 and response["route"] in ("/tokenize", "/completion"):
                decoded = json.loads(base64.b64decode(response["body_base64"]))
                record = {"request": request["payload"], "response": decoded,
                          "request_event": pending["sequence"], "response_event": event["sequence"],
                          "elapsed_seconds": response["elapsed_seconds"]}
                (tokenizations if response["route"] == "/tokenize" else completions).append(record)
            pending = None
    rows = []
    for cid in manifest["case_ids"]:
        row = {"case_id": cid, "condition": manifest["condition"], "errors": []}
        needed = [index.get((k, cid)) for k in ("prompt_prepared", "generation_started", "raw_generation", "parser_audit", "case_result")]
        if any(e is None for e in needed):
            row["errors"].append("incomplete case event chain")
            rows.append(row)
            continue
        pe, ge, re, ae, ce = needed
        if [e["sequence"] for e in needed] != sorted(e["sequence"] for e in needed):
            row["errors"].append("case event ordering")
        p, raw, parser, result = pe["data"], re["data"]["response"], ae["data"], ce["data"]
        prompt, ids = p["prompt"]["text"], p["prompt_token_ids"]
        token_calls = [t for t in tokenizations if t["request"]["content"] == prompt and t["response_event"] < pe["sequence"]]
        calls = [c for c in completions if ge["sequence"] < c["request_event"] < c["response_event"] < re["sequence"]]
        tok = token_calls[-1] if token_calls else None
        call = calls[0] if len(calls) == 1 else None
        generated = normalize_result(raw)
        parsed = parse_reply(generated["raw_response"], stop_reason=generated["stop_reason"])
        judgment = judge_current_city(cases[cid], parsed.parsed_text)
        checks = {
            "tokenizer_ids_match_prepared": tok is not None and tok["response"]["tokens"] == ids,
            "submitted_ids_match_prepared": call is not None and call["request"]["prompt"] == ids,
            "wire_response_matches_raw": call is not None and call["response"] == raw,
            "evaluated_count_matches": raw.get("tokens_evaluated") == len(ids),
            "no_context_truncation": raw.get("truncated") is False,
            "prompt_count_matches": p["prompt_tokens"] == len(ids),
            "evidence_preserved": p["prompt"]["evidence_block"] == "TRUSTED EVIDENCE:\n"+cases[cid].trusted_evidence and prompt.count(p["prompt"]["evidence_block"]) == 1,
            "question_preserved": prompt.endswith(f"User: {cases[cid].question}\nAssistant:"),
            "parser_replay_matches": parsed.parsed_text == result["parsed_response"] == parser["parsed_response"] and all(parser.get(k) == v for k, v in json.loads(json.dumps(parsed.audit())).items()),
            "evaluation_replay_matches": judgment.status == result["fact_accuracy"] and judgment.reason == result["fact_reason"],
            "condition_matches": result["condition"] == p["prompt"]["condition"] == manifest["condition"],
            "prompt_hash_matches_if_recorded": p.get("prompt_sha256", text_hash(prompt)) == text_hash(prompt),
            "returned_input_ids_match_if_supported": not isinstance(raw.get("prompt"), list) or raw["prompt"] == ids,
            "tokenizer_special_policy": tok is not None and tok["request"].get("add_special") is True and tok["request"].get("parse_special") is False,
            "generation_parameters": call is not None and all(call["request"].get(k) == v for k, v in {
                "seed": manifest["configuration"]["seed"], "n_predict": manifest["configuration"]["max_new_tokens"],
                "temperature": 0.0, "top_p": 1.0, "stop": [], "return_tokens": True, "cache_prompt": False}.items()),
            "generated_ids_preserved": result.get("generated_token_ids") == generated["generated_token_ids"],
        }
        row["errors"] += [k for k, v in checks.items() if not v]
        row.update({"checks": checks, "prompt": prompt, "prompt_sha256": text_hash(prompt),
                    "prompt_hash_origin": "recorded" if "prompt_sha256" in p else "post-hoc reconstruction",
                    "trusted_evidence": p["prompt"]["evidence_block"], "trusted_evidence_hash": text_hash(p["prompt"]["evidence_block"]),
                    "input_token_ids": ids, "input_token_count": len(ids), "tokenizer": tok,
                    "generation_request": call["request"] if call else None,
                    "evaluated_input_token_ids": raw["prompt"] if isinstance(raw.get("prompt"), list) else None,
                    "evaluated_token_count": raw.get("tokens_evaluated"), "context_truncated": raw.get("truncated"),
                    "raw_response": generated["raw_response"], "parsed_response": parsed.parsed_text,
                    "classification": parsed.classification, "fact_judgment": judgment.status, "fact_reason": judgment.reason,
                    "backend_finish_reason": raw.get("stop_type"), "generated_tokens": raw.get("tokens_predicted"),
                    "generated_token_ids": generated["generated_token_ids"],
                    "generation_settings": raw.get("generation_settings"), "timings": raw.get("timings"),
                    "response_latency_seconds": call["elapsed_seconds"] if call else None,
                    "event_sequences": [e["sequence"] for e in needed]})
        rows.append(row)
    known = set(manifest["case_ids"])
    for kind, cid in index:
        if cid not in known:
            issues.append(f"unexpected case {cid}: {kind}")
    if len(known) != len(manifest["case_ids"]):
        issues.append("duplicate manifest case IDs")
    summary = {"cases": len(rows), "completed": sum("raw_response" in r for r in rows),
               "raw_empty": sum(r.get("raw_response") == "" for r in rows),
               "raw_nonempty": sum(bool(r.get("raw_response")) for r in rows),
               "parser_classifications": dict(Counter(r.get("classification", "missing") for r in rows)),
               "factual_judgments": dict(Counter(r.get("fact_judgment", "missing") for r in rows)),
               "finish_reasons": dict(Counter(r.get("backend_finish_reason", "missing") for r in rows)),
               "cases_with_errors": sum(bool(r["errors"]) for r in rows),
               "missing_evaluated_input_ids": sum(r.get("evaluated_input_token_ids") is None for r in rows)}
    failures = [e for e in events if e["kind"] == "failure"]
    if events and events[-1]["kind"] == "run_finished":
        if events[-1]["data"].get("completed_cases") != summary["completed"]:
            issues.append("terminal completed count does not match independently identifiable results")
    return {"run_id": manifest["run_id"], "journal_integrity": "PASS", "events": len(events),
            "status": "PASS" if not issues and not failures and not summary["cases_with_errors"] else "PARTIAL",
            "scope": "offline saved-input/parser/evaluator reconstruction; not inference replay or research acceptance",
            "summary": summary, "issues": issues, "historical_missing_metadata": missing,
            "limitations": ["Backend returns decoded prompt text, not evaluated input IDs; equality of evaluated IDs cannot be independently checked.",
                            "Factual evaluation covers only the synthetic current-city question."],
            "failures": failures, "cases": rows}
