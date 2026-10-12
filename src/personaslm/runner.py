"""P0 only: preflight, immutable provenance, raw logging, parsing and narrow scoring."""
from dataclasses import asdict
from pathlib import Path
import platform

from .conditioning import P0_CONDITIONS, build_prompt
from .configuration import preflight
from .diagnostics import parse_reply
from .evaluation import judge_current_city
from .fixtures import load_cases
from .inference import LlamaClient, normalize_result
from .journal import RunJournal
from .matching import MATCHER_VERSION, match_neutral
from .provenance import repository_root, require_local_path, sha256
from .server import ManagedServer, validate_server_properties


def validate_completion(result, prompt_ids):
    if result.get("truncated") is not False:
        raise ValueError("Completion must explicitly report truncated=false")
    evaluated = result.get("tokens_evaluated")
    if type(evaluated) is not int or evaluated != len(prompt_ids):
        raise ValueError(f"Prompt token mismatch: sent={len(prompt_ids)} evaluated={evaluated}")
    processed = result.get("prompt")
    if isinstance(processed, list) and processed != prompt_ids:
        raise ValueError("Server changed prompt token IDs")
    return {"sent_tokens": len(prompt_ids), "tokens_evaluated": evaluated,
            "count_matches": True, "returned_ids_match": processed == prompt_ids if isinstance(processed, list) else None,
            "truncated": False}


def run_local(config, condition: str, cases_path: Path, output_root: Path, *,
              client_factory=LlamaClient, server_factory=ManagedServer) -> tuple[dict, Path]:
    if condition not in P0_CONDITIONS:
        raise ValueError("P0 condition required")
    cases_path = require_local_path(cases_path)
    cases = load_cases(cases_path)
    if not cases or any(case.split != "p0_synthetic_only" for case in cases):
        raise ValueError("P0 requires nonempty synthetic-only cases")
    files = sorted((repository_root() / "src/personaslm").glob("*.py"))
    manifest = {"scope": "P0 pipeline validation only", "configuration": config.as_dict(),
                "condition": condition, "cases_sha256": sha256(cases_path), "cases_file": str(cases_path),
                "case_ids": [case.case_id for case in cases],
                "applicability": {case.case_id: case.applicability for case in cases},
                "source_sha256": {file.name: sha256(file) for file in files},
                "python": platform.python_version(), "os": platform.platform(), "cpu": platform.processor(),
                "tokenizer": {"source": "same owned llama-server /tokenize", "add_special": True,
                              "parse_special": False, "generation_input": "exact token IDs"},
                "matcher_version": MATCHER_VERSION, "parser_version": "p0_parser_v2"}
    journal = RunJournal(output_root, manifest)
    completed = 0
    attempted = 0
    responses_received = 0
    limitations = []
    try:
        check = preflight(config)
        journal.write("preflight", check)
        if check["status"] != "PASS":
            summary = {"status": "BLOCKED", "completed_cases": 0, "real_inference_performed": False,
                       "reason": "Independent model/server configuration is missing or invalid"}
            journal.finish(**summary)
            return summary, journal.directory
        with server_factory(config, journal) as server:
            client = client_factory(config.endpoint, timeout=config.timeout, audit=journal.write)
            props = client.request("/props")
            identity = validate_server_properties(props, config)
            if not identity["build_info"]:
                limitations.append("Server did not expose build_info")
            journal.write("server_identity", {"properties": props, "validation": identity})
            prepared = []
            # Freeze every prompt and matching decision before any completion.
            for case in cases:
                if condition in ("N_style", "N_history"):
                    matched = match_neutral(case, condition, client.tokenize, tolerance=config.token_tolerance,
                                            max_candidates=config.max_match_candidates)
                    prompt, ids, matching = matched.prompt, matched.token_ids, matched.audit
                else:
                    prompt = build_prompt(case, condition)
                    ids = client.tokenize(prompt.text)
                    matching = {"status": "not_applicable", "condition": condition}
                if len(ids) + config.max_new_tokens > config.n_ctx:
                    raise ValueError(f"Context budget exceeded before generation for {case.case_id}")
                journal.write("prompt_prepared", {"case_id": case.case_id, "prompt": asdict(prompt),
                              "prompt_token_ids": ids, "prompt_tokens": len(ids), "matching": matching,
                              "applicability": case.applicability})
                prepared.append((case, prompt, ids))
            for case, prompt, ids in prepared:
                server.assert_running()
                journal.write("generation_started", {"case_id": case.case_id, "condition": condition})
                attempted += 1
                response = client.complete(ids, seed=config.seed, max_new_tokens=config.max_new_tokens)
                responses_received += 1
                # Separate raw native payload survives all validation/parser/scorer failures.
                journal.write("raw_generation", {"case_id": case.case_id, "response": response})
                token_audit = validate_completion(response, ids)
                generated = normalize_result(response)
                if generated["token_ids_status"] != "returned":
                    limitations.append(f"{case.case_id}: generated token IDs {generated['token_ids_status']}")
                if generated["stop_reason"] not in ("eos", "length", "stop_sequence"):
                    limitations.append(f"{case.case_id}: unrecognized termination {generated['stop_reason']}")
                parsed = parse_reply(generated["raw_response"], stop_reason=generated["stop_reason"])
                journal.write("parser_audit", {"case_id": case.case_id, **parsed.audit(),
                              "raw_response": parsed.raw_text, "parsed_response": parsed.parsed_text})
                judgment = judge_current_city(case, parsed.parsed_text)
                journal.write("case_result", {"case_id": case.case_id, "condition": condition,
                              "applicability": case.applicability, "token_audit": token_audit, **generated,
                              "parsed_response": parsed.parsed_text, "fact_accuracy": judgment.status,
                              "fact_reason": judgment.reason, "evaluation_scope": "synthetic current-city cases only"})
                completed += 1
            server.assert_running()
            final_props = client.request("/props")
            validate_server_properties(final_props, config)
            if final_props.get("build_info") != props.get("build_info"):
                raise ValueError("Server build identity changed during run")
            final_check = preflight(config)
            journal.write("postflight", final_check)
            if final_check["status"] != "PASS" or final_check["server"] != check["server"]:
                raise ValueError("Model or server file changed during run")
        summary = {"status": "PARTIAL" if limitations else "PASS", "scope": "P0 adapter execution; not complete P0 research sign-off",
                   "completed_cases": completed, "real_inference_performed": True,
                   "completion_requests_attempted": attempted, "completion_responses_received": responses_received,
                   "limitations": limitations,
                   "remaining": ["Independent CPU hardware/log review", "GGUF architecture/quantization and Base identity review",
                                 "Neutral semantic review", "Real token-ID support review if response tokens are empty/absent"]}
        journal.finish(**summary)
        return summary, journal.directory
    except Exception as exc:
        journal.write("failure", {"type": type(exc).__name__, "message": str(exc),
                      "audit": getattr(exc, "audit", None), "completed_cases": completed})
        summary = {"status": "BLOCKED" if completed == 0 else "PARTIAL", "completed_cases": completed,
                   "reason": str(exc), "real_inference_performed": True if responses_received else (None if attempted else False),
                   "completion_requests_attempted": attempted, "completion_responses_received": responses_received,
                   "note": "Inspect raw events; failed HTTP calls are never retried automatically"}
        journal.finish(**summary)
        return summary, journal.directory
