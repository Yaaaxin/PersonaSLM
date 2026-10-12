"""Minimal P0 CLI; no network or model downloads by default."""
import argparse
import json
from dataclasses import replace
from pathlib import Path
from .conditioning import P0_CONDITIONS, assert_same_evidence, build_prompt
from .diagnostics import parse_reply
from .evaluation import judge_current_city
from .fixtures import load_cases, write_fixtures
from .configuration import RuntimeConfig, preflight
from .journal import read_events
from .runner import run_local
from .server import server_command
from .provenance import (
    audit_local_paths,
    repository_root, require_local_path, sha256,
)


def cmd_fixtures(args) -> None:
    output = require_local_path(Path(args.output))
    count = write_fixtures(output)
    print(f"Created {count} synthetic cases: {output}")


def cmd_validate(args) -> None:
    path = require_local_path(Path(args.cases))
    cases = load_cases(path)
    for case in cases:
        assert_same_evidence(case, P0_CONDITIONS)
        for condition in P0_CONDITIONS:
            prompt = build_prompt(case, condition)
            if "Verified current fact" not in prompt.text:
                raise AssertionError("trusted evidence missing")
    audit = audit_local_paths()
    if audit["links_or_junctions"]:
        raise RuntimeError(f"External links/junctions found: {audit['links_or_junctions']}")
    print(json.dumps({"status": audit["status"], "validated_cases": len(cases), "conditions": P0_CONDITIONS,
                      "applicability_predeclared": True, "isolation_audit": audit}, indent=2))
    return 0 if audit["passed"] else 2


def cmd_smoke(args) -> None:
    test_cases = load_cases(require_local_path(Path(args.cases)))
    case = test_cases[0]
    samples = [
        ("", "eos"), ("", "stop_sequence"), ("\nHello", "length"),
        ("Assistant:", "length"), (f"Alice lives in {case.expected_answer}.", "eos"),
    ]
    report = []
    for raw, stop_reason in samples:
        parsed = parse_reply(raw, stop_reason=stop_reason, stop_at_first_newline=True)
        judgment = judge_current_city(case, parsed.parsed_text)
        report.append({"raw": raw, "stop_reason": stop_reason,
                       "parsed": parsed.parsed_text, "classification": parsed.classification,
                       "fact_judgment": judgment.status})
    print(json.dumps(report, indent=2, ensure_ascii=False))


def cmd_run_local(args) -> int:
    config = runtime_config(args)
    summary, directory = run_local(config, args.condition, Path(args.cases), Path(args.output_root))
    print(json.dumps({**summary, "run_directory": str(directory)}, indent=2, ensure_ascii=False))
    return 0 if summary["status"] == "PASS" else 2


def runtime_config(args):
    config = RuntimeConfig.load(Path(args.config))
    overrides = {name: getattr(args, name) for name in config.as_dict()
                 if getattr(args, name, None) is not None}
    return replace(config, **overrides)


def cmd_preflight(args):
    config = runtime_config(args)
    report = preflight(config)
    if report["status"] == "PASS":
        report["server_command_argv"] = server_command(config)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 2


def cmd_hash_model(args):
    path = require_local_path(Path(args.model_file))
    if path.suffix.lower() != ".gguf" or not path.is_file():
        raise ValueError("An existing project-local GGUF file is required")
    print(json.dumps({"model_file": str(path), "sha256": sha256(path),
                      "note": "Computed local digest only; compare against an independently recorded trusted digest"}, indent=2))


def cmd_audit_run(args):
    events = read_events(Path(args.run_dir))
    finished = events[-1]["data"] if events and events[-1]["kind"] == "run_finished" else None
    report = {"integrity": "PASS", "events": len(events), "run_finished": finished,
              "status": finished["status"] if finished else "PARTIAL", "parser_replay": []}
    from .inference import normalize_result
    for event in events:
        if event["kind"] == "raw_generation":
            data = event["data"]
            try:
                generated = normalize_result(data["response"])
                parsed = parse_reply(generated["raw_response"], stop_reason=generated["stop_reason"])
                report["parser_replay"].append({"case_id": data["case_id"], **parsed.audit()})
            except (ValueError, TypeError) as exc:
                report["parser_replay"].append({"case_id": data["case_id"], "error": str(exc)})
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 2


def main(argv=None) -> None:
    root = repository_root()
    parser = argparse.ArgumentParser(prog="personaslm", description="PersonaSLM-Lab P0 only")
    commands = parser.add_subparsers(dest="command", required=True)
    fixtures = commands.add_parser("make-fixtures", help="Generate 20 fictional test cases")
    fixtures.add_argument("--output", default=str(root / "data/synthetic/p0_cases.jsonl"))
    fixtures.set_defaults(func=cmd_fixtures)
    validate = commands.add_parser("validate", help="Check fixtures and Track A evidence")
    validate.add_argument("--cases", default=str(root / "data/synthetic/p0_cases.jsonl"))
    validate.set_defaults(func=cmd_validate)
    smoke = commands.add_parser("smoke", help="Demonstrate parser failure classifications offline")
    smoke.add_argument("--cases", default=str(root / "data/synthetic/p0_cases.jsonl"))
    smoke.set_defaults(func=cmd_smoke)
    check = commands.add_parser("preflight", help="Offline path and checksum validation; never starts a server")
    check.set_defaults(func=cmd_preflight)
    digest = commands.add_parser("hash-model", help="Compute a project-local GGUF SHA-256")
    digest.add_argument("--model-file", required=True)
    digest.set_defaults(func=cmd_hash_model)
    audit = commands.add_parser("audit-run", help="Verify journal integrity and replay parser offline")
    audit.add_argument("--run-dir", required=True)
    audit.set_defaults(func=cmd_audit_run)
    run = commands.add_parser("run-local", help="Run P0 synthetic cases with an owned CPU-only llama-server")
    run.add_argument("--cases", default=str(root / "data/synthetic/p0_cases.jsonl"))
    run.add_argument("--output-root", default=str(root / "results/p0"))
    run.add_argument("--condition", choices=P0_CONDITIONS, default="C0")
    for command in (check, run):
        command.add_argument("--config", default=str(root / "configs/p0_runtime.example.json"))
        for name in ("model-file", "model-sha256", "server-file", "endpoint"):
            command.add_argument("--" + name, default=None)
        for name in ("seed", "max-new-tokens", "threads", "n-ctx", "token-tolerance"):
            command.add_argument("--" + name, type=int, default=None)
    run.set_defaults(func=cmd_run_local)
    args = parser.parse_args(argv)
    try:
        code = args.func(args)
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "type": type(exc).__name__, "reason": str(exc)}, ensure_ascii=False))
        code = 2
    raise SystemExit(code or 0)


if __name__ == "__main__":
    main()
