"""Predeclared, independent P0 single-turn diagnostic; no historical mutation."""
import argparse
import base64
from collections import Counter
import json
from pathlib import Path

from personaslm.configuration import RuntimeConfig, preflight
from personaslm.diagnostics import parse_reply
from personaslm.inference import LlamaClient, normalize_result
from personaslm.journal import RunJournal, atomic_json, read_events, utc_now
from personaslm.provenance import fingerprint, repository_root, require_local_path, sha256
from personaslm.reproducibility import source_snapshot
from personaslm.response_boundary import VERSION, VARIANTS, boundary_audit, prompt_for
from personaslm.runner import validate_completion
from personaslm.run_audit import text_hash
from personaslm.server import ManagedServer, validate_server_properties


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def freeze(session):
    cases_file = Path("tests/fixtures/p0_boundary_dev_v1.json")
    dataset = read(cases_file)
    config = RuntimeConfig.load(Path("configs/p0_runtime.local.json"))
    assert config.max_new_tokens == 96
    old = read(Path("docs/validation/P0_case_audit.json"))["cases"]
    cases = dataset["cases"]
    assert not {c["case_id"] for c in cases} & {c["case_id"] for c in old}
    prompts = [{"case_id": c["case_id"], "variant": v, "prompt_version": VARIANTS[v]["prompt_version"],
                "prompt": prompt_for(c, v), "prompt_sha256": text_hash(prompt_for(c, v)),
                "evidence_sha256": text_hash(c["trusted_evidence"])} for c in cases for v in VARIANTS]
    plan = {"created_utc": utc_now(), "phase": "P0 single-turn development diagnostic",
        "case_file": cases_file.as_posix(), "case_file_sha256": sha256(cases_file), "dataset": dataset,
        "configuration": config.as_dict(), "variants": VARIANTS, "prompts": prompts,
        "new_generations": len(prompts), "selection": "All four new development cases; no selection by factual correctness.",
        "order": "case order, then T0/T1/T2/T3; one request per cell; no adaptive stop-rule changes or retries",
        "definition": "One structurally delimited, nonempty assistant turn. A visible declared delimiter, acknowledged backend stop, or EOS establishes the boundary. Reserved-marker collisions and undeclared extra role turns fail validation. Semantic completeness remains a separate assessment.",
        "primary_criteria": "Report every case. A format is structurally validated on the tested scope only if all four cases pass. Also report the first three ordinary tasks and the delimiter challenge separately, as predefined strata.",
        "non_goals": "No factual-quality selection, Persona effect, natural EOS guarantee, general-dialogue completeness guarantee, P1 or new algorithm.",
        "parser_version": VERSION, "evaluation_version": "not_applicable_termination_diagnostic_v1",
        "reconstruction": source_snapshot(cases_file)}
    atomic_json(session / "materials/boundary_plan.json", plan)
    print(json.dumps({"frozen_utc": plan["created_utc"], "planned_requests": len(prompts), "case_ids": [c["case_id"] for c in cases]}))


def run(session):
    plan_file = session / "materials/boundary_plan.json"
    plan = read(plan_file)
    config = RuntimeConfig.load(Path("configs/p0_runtime.local.json"))
    assert config.as_dict() == plan["configuration"] and VARIANTS == plan["variants"]
    assert sha256(Path(plan["case_file"])) == plan["case_file_sha256"]
    atomic_json(session / "experiments/started.json", {"created_utc": utc_now(), "plan_sha256": sha256(plan_file)})
    snapshot = source_snapshot(Path(plan["case_file"]))
    snapshot["evaluation_rules"] = plan["evaluation_version"]
    manifest = {"scope": plan["phase"], "plan_sha256": sha256(plan_file), "plan": plan,
                "configuration": config.as_dict(), "reconstruction": snapshot,
                "parser_version": VERSION, "evaluation_version": plan["evaluation_version"]}
    journal = RunJournal(session / "experiments/runs", manifest)
    completed = 0
    try:
        check = preflight(config)
        journal.write("preflight", check)
        if check["status"] != "PASS":
            raise ValueError("Model/backend preflight failed")
        with ManagedServer(config, journal) as server:
            client = LlamaClient(config.endpoint, timeout=config.timeout, audit=journal.write)
            props = client.request("/props")
            journal.write("server_identity", {"properties": props, "validation": validate_server_properties(props, config)})
            prepared = []
            for cell in plan["prompts"]:
                case = next(c for c in plan["dataset"]["cases"] if c["case_id"] == cell["case_id"])
                assert prompt_for(case, cell["variant"]) == cell["prompt"]
                ids = client.tokenize(cell["prompt"])
                assert len(ids) + config.max_new_tokens <= config.n_ctx
                item = {**cell, "cell_id": cell["case_id"]+"/"+cell["variant"], "input_ids": ids,
                    "input_tokens": len(ids), "request": {"prompt": ids, "n_predict": config.max_new_tokens,
                    "temperature": 0.0, "top_p": 1.0, "seed": config.seed, "cache_prompt": False,
                    "stop": VARIANTS[cell["variant"]]["stop"], "return_tokens": True, "stream": False}}
                item["request_sha256"] = fingerprint(item["request"])
                journal.write("boundary_prompt_prepared", item)
                prepared.append((case, item))
            for case, item in prepared:
                server.assert_running()
                journal.write("boundary_generation_started", {"cell_id": item["cell_id"]})
                native = client.request("/completion", item["request"])
                journal.write("boundary_raw_generation", {"cell_id": item["cell_id"], "response": native})
                token_check = validate_completion(native, item["input_ids"])
                normalized = normalize_result(native)
                legacy = parse_reply(normalized["raw_response"], stop_reason=normalized["stop_reason"])
                parsed = boundary_audit(native["content"], native, case, item["variant"])
                journal.write("boundary_result", {"cell_id": item["cell_id"], "token_check": token_check,
                    "legacy_parser": {**legacy.audit(), "parsed_response": legacy.parsed_text}, "boundary_parser": parsed,
                    "evaluation_status": "Not Applicable", "evaluation_version": plan["evaluation_version"]})
                completed += 1
                print(json.dumps({"cell_id": item["cell_id"], "stop": native.get("stop_type"),
                                  "tokens": native.get("tokens_predicted"), "boundary_status": parsed["status"]}), flush=True)
            final = preflight(config)
            journal.write("postflight", final)
            assert final["status"] == "PASS" and final["server"] == check["server"]
        journal.finish("PASS", scope="execution only; inspect boundary/semantic outcomes", completed_cases=completed)
    except Exception as exc:
        journal.write("failure", {"type": type(exc).__name__, "message": str(exc), "completed": completed})
        journal.finish("PARTIAL" if completed else "BLOCKED", completed_cases=completed)
        raise
    result = audit(journal.directory)
    atomic_json(session / "experiments/boundary_audit.json", result)
    print(json.dumps({"run_id": journal.run_id, "audit": result["status"], "summary": result["summary"]}))


def inference_http_records(events):
    """Health startup responses stay in the journal, outside inference pairs."""
    http, pending = [], None
    for event in events:
        if event["kind"] == "http_request":
            pending = event["data"]
        elif event["kind"] == "http_response" and pending:
            data = event["data"]
            assert pending["route"] == data["route"]
            if data["route"] in ("/tokenize", "/completion"):
                assert data["status"] == 200
                http.append({"route": data["route"], "request": pending["payload"],
                             "response": json.loads(base64.b64decode(data["body_base64"])),
                             "latency_seconds": data.get("elapsed_seconds")})
            pending = None
    return http


def audit(directory):
    directory = require_local_path(directory)
    manifest = read(directory / "manifest.json")
    plan = manifest["plan"]
    events = read_events(directory)
    assert events[-1]["kind"] == "run_finished"
    assert text_hash(manifest["reconstruction"]["dataset_utf8"]) == plan["case_file_sha256"]
    for name, digest in manifest["reconstruction"]["source_sha256"].items():
        assert text_hash(manifest["reconstruction"]["source_utf8"][name]) == digest
    for name in ("response_boundary.py", "diagnostics.py", "inference.py"):
        assert sha256(repository_root()/"src/personaslm"/name) == manifest["reconstruction"]["source_sha256"][name]
    http = inference_http_records(events)
    def of_kind(kind):
        return [e["data"] for e in events if e["kind"] == kind]
    prepared, raw, results = (of_kind(k) for k in ("boundary_prompt_prepared", "boundary_raw_generation", "boundary_result"))
    tokenizations = [x for x in http if x["route"] == "/tokenize"]
    completions = [x for x in http if x["route"] == "/completion"]
    assert len(prepared) == len(raw) == len(results) == len(tokenizations) == len(completions) == plan["new_generations"]
    assert len({x["cell_id"] for x in prepared}) == len(prepared)
    rows = []
    for p, r, saved, tok, wire in zip(prepared, raw, results, tokenizations, completions):
        assert p["cell_id"] == r["cell_id"] == saved["cell_id"]
        case = next(c for c in plan["dataset"]["cases"] if c["case_id"] == p["case_id"])
        assert p["prompt"] == prompt_for(case, p["variant"])
        assert text_hash(p["prompt"]) == p["prompt_sha256"]
        assert tok["request"]["content"] == p["prompt"] and tok["response"]["tokens"] == p["input_ids"]
        assert wire["request"] == p["request"] and wire["response"] == r["response"]
        assert fingerprint(wire["request"]) == p["request_sha256"]
        native = r["response"]
        assert validate_completion(native, p["input_ids"]) == saved["token_check"]
        actual = boundary_audit(native["content"], native, case, p["variant"])
        assert actual == saved["boundary_parser"]
        legacy = parse_reply(native["content"], stop_reason=normalize_result(native)["stop_reason"])
        assert json.loads(json.dumps({**legacy.audit(), "parsed_response": legacy.parsed_text})) == saved["legacy_parser"]
        rows.append({**p, **saved, "raw_native_response": native, "response_latency_seconds": wire["latency_seconds"]})
    pairs = []
    for case in plan["dataset"]["cases"]:
        for reference, stopped in (("T0", "T1"), ("T2", "T3")):
            a, b = [next(r for r in rows if r["case_id"] == case["case_id"] and r["variant"] == v) for v in (reference, stopped)]
            assert a["input_ids"] == b["input_ids"] and a["prompt_sha256"] == b["prompt_sha256"]
            aa, bb = ({k: v for k, v in r["request"].items() if k != "stop"} for r in (a, b))
            assert aa == bb
            prefix = a["boundary_parser"]["parsed_response"]
            stopped_text = b["raw_native_response"]["content"].strip()
            pairs.append({"case_id": case["case_id"], "reference": reference, "stopped": stopped,
                "same_prompt_ids_and_request_except_stop": True, "returned_body_equals_shadow_extraction": prefix == stopped_text,
                "note": "Unstopped shadow is a separate actual generation, not reconstructed unseen continuation."})
    return {"status": "PASS", "scope": "journal/wire/input/parser reconstruction only", "run_id": directory.name,
        "manifest_sha256": sha256(directory / "manifest.json"), "terminal_hash": events[-1]["event_hash"],
        "audit_tool_sha256": sha256(Path(__file__)),
        "non_generation_http_statuses": [{"sequence": e["sequence"], "route": e["data"]["route"], "status": e["data"]["status"]}
            for e in events if e["kind"] == "http_response" and e["data"]["route"] not in ("/tokenize", "/completion")],
        "git": manifest["reconstruction"]["git"], "configuration": manifest["configuration"],
        "configuration_sha256": fingerprint(manifest["configuration"]), "plan_sha256": manifest["plan_sha256"],
        "cases": rows, "pairs": pairs,
        "summary": {v: {"cases": sum(r["variant"] == v for r in rows),
                         "boundary": dict(Counter(r["boundary_parser"]["status"] for r in rows if r["variant"] == v)),
                         "stop": dict(Counter(r["raw_native_response"]["stop_type"] for r in rows if r["variant"] == v))} for v in VARIANTS}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("freeze", "run", "audit"))
    parser.add_argument("--session", type=Path)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.stage == "audit":
        result = audit(args.run_dir)
        atomic_json(args.output, result)
        print(json.dumps({"status": result["status"], "run_id": result["run_id"], "summary": result["summary"]}))
    else:
        {"freeze": freeze, "run": run}[args.stage](require_local_path(args.session))
