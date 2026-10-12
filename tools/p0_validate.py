"""Reproducible P0-only prompt freeze and staged controlled adapter validation.

Never selects by generated answer quality. Never overwrites runs or experiment files.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from personaslm.conditioning import build_prompt
from personaslm.configuration import RuntimeConfig, preflight
from personaslm.fixtures import load_cases
from personaslm.inference import LlamaClient
from personaslm.journal import RunJournal, atomic_json, utc_now
from personaslm.matching import TokenMatchError, match_neutral
from personaslm.provenance import sha256
from personaslm.reproducibility import source_snapshot
from personaslm.run_audit import audit_run, text_hash
from personaslm.runner import run_local
from personaslm.server import ManagedServer, validate_server_properties


CONDITIONS = ("C1", "N_style", "C3", "N_history")


def prepare(session, config, dataset, selection, freeze_name, reuse_history):
    destination = session / freeze_name
    if destination.exists():
        raise FileExistsError(destination)
    cases = sorted(load_cases(dataset), key=lambda c: c.case_id)
    journal = RunJournal(session / "tokenizer_runs", {"scope": "P0 token validation only; no completions",
        "configuration": config.as_dict(), "selection": selection, "reconstruction": source_snapshot(dataset)})
    frozen, rows, failures = {}, [], []
    previous = json.loads((session / reuse_history).read_text(encoding="utf-8")) if reuse_history else None
    if previous and (previous["dataset_sha256"] != sha256(dataset) or previous["configuration"] != config.as_dict()):
        raise ValueError("Cannot reuse history validation after dataset/config changes")
    try:
        check = preflight(config)
        journal.write("preflight", check)
        if check["status"] != "PASS":
            raise ValueError("Preflight blocked")
        with ManagedServer(config, journal):
            client = LlamaClient(config.endpoint, timeout=config.timeout, audit=journal.write)
            props = client.request("/props")
            journal.write("server_identity", {"properties": props, "validation": validate_server_properties(props, config)})
            probes = []
            for text in ("Hello", "<|endoftext|>", build_prompt(cases[0], "C0").text):
                for add in (False, True):
                    for parse in (False, True):
                        request = {"content": text, "add_special": add, "parse_special": parse, "with_pieces": False}
                        probes.append({"request": request, "response": client.request("/tokenize", request)})
            journal.write("special_token_probes", {"probes": probes})
            for case in cases:
                frozen[case.case_id] = {}
                for reference, neutral in (("C1", "N_style"), ("C3", "N_history")):
                    if neutral == "N_history" and previous:
                        old = previous["prompts"][case.case_id]
                        frozen[case.case_id].update({"C3": old["C3"], "N_history": old["N_history"]})
                        row = next(r for r in previous["rows"] if r["case_id"] == case.case_id and r["neutral_condition"] == neutral)
                        if row["matching_status"] != "PASS":
                            raise ValueError("Only successful history validation can be reused")
                        rows.append(row)
                        journal.write("matching_reused", {"row": row, "source_sha256": sha256(session / reuse_history)})
                        continue
                    target = build_prompt(case, reference)
                    try:
                        match = match_neutral(case, neutral, client.tokenize, tolerance=0, max_candidates=config.max_match_candidates)
                        audit = match.audit
                        frozen[case.case_id][reference] = {"prompt": asdict(target), "token_ids": audit["target_token_ids"],
                            "matching": {"status": "reference", "neutral_condition": neutral}}
                        frozen[case.case_id][neutral] = {"prompt": asdict(match.prompt), "token_ids": match.token_ids,
                            "matching": audit, "neutral_text": audit["neutral_text"]}
                        row = {"case_id": case.case_id, "reference_condition": reference, "neutral_condition": neutral,
                            "reference_token_count": audit["target_tokens"], "neutral_token_count": audit["actual_tokens"],
                            "token_difference": audit["delta"], "matching_status": "PASS", "attempted": audit["attempted"],
                            "trusted_evidence_hash": text_hash(target.evidence_block), "prompt_template_version": config.prompt_template,
                            "neutral_text": audit["neutral_text"], "human_review": None}
                    except TokenMatchError as exc:
                        audit = exc.audit
                        row = {"case_id": case.case_id, "reference_condition": reference, "neutral_condition": neutral,
                            "reference_token_count": audit["target_tokens"], "neutral_token_count": None,
                            "token_difference": audit["best_delta"], "matching_status": "BLOCKED", "attempted": audit["attempted"],
                            "trusted_evidence_hash": text_hash(target.evidence_block), "prompt_template_version": config.prompt_template}
                        failures.append(row)
                    journal.write("matching_audit", {**row, "audit": audit})
                    rows.append(row)
                    print(json.dumps(row), flush=True)
            final = preflight(config)
            if final != check:
                raise ValueError("Preflight identity changed during tokenizer validation")
            journal.write("postflight", final)
        artifact = {"created_utc": utc_now(), "configuration": config.as_dict(), "dataset_sha256": sha256(dataset),
                    "tokenizer_run": str(journal.directory), "rows": rows, "prompts": frozen, "failures": failures,
                    "selection_sha256": sha256(session / "selection_freeze.json")}
        atomic_json(destination, artifact)
        journal.finish("PARTIAL" if failures else "PASS", comparisons=len(rows), failures=len(failures), completion_requests=0)
    except Exception as exc:
        journal.write("failure", {"type": type(exc).__name__, "message": str(exc)})
        journal.finish("BLOCKED", completion_requests=0)
        raise
    return 2 if failures else 0


def generate(session, config, dataset, selection, stage, freeze_name):
    destination = session / f"{stage}_generation.json"
    if destination.exists():
        raise FileExistsError(destination)
    frozen_path = session / freeze_name
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    if frozen["configuration"] != config.as_dict() or frozen["dataset_sha256"] != sha256(dataset):
        raise ValueError("Config/dataset changed after prompt validation")
    ids = selection["initial_subset" if stage == "initial" else "expansion_subset"]
    if stage == "expansion":
        initial = json.loads((session / "initial_generation.json").read_text(encoding="utf-8"))
        if len(initial["runs"]) != 4 or any(r["summary"]["status"] != "PASS" or r["audit_status"] != "PASS" for r in initial["runs"]):
            raise ValueError("Initial engineering validation did not pass; no automatic expansion")
    # Require every selected pair to have succeeded before any generation in this stage.
    if any(set(frozen["prompts"][cid]) != set(CONDITIONS) for cid in ids):
        raise ValueError("A selected pair failed tokenizer validation; generation blocked")
    selected = session / f"{stage}_cases.jsonl"
    rows = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    with selected.open("x", encoding="utf-8", newline="\n") as handle:
        for cid in ids:
            handle.write(json.dumps(next(r for r in rows if r["case_id"] == cid), ensure_ascii=False)+"\n")
    runs = []
    for condition in CONDITIONS:
        summary, directory = run_local(config, condition, selected, session / "controlled_runs", frozen_prompts=frozen["prompts"])
        audit = audit_run(directory)
        atomic_json(session / f"{stage}_{condition}_audit.json", audit)
        entry = {"condition": condition, "run_directory": str(directory), "summary": summary, "audit_status": audit["status"]}
        runs.append(entry)
        print(json.dumps(entry), flush=True)
        if summary["status"] != "PASS" or audit["status"] != "PASS":
            break
    atomic_json(destination, {"created_utc": utc_now(), "stage": stage, "case_ids": ids,
                            "prompts_freeze_sha256": sha256(frozen_path), "runs": runs})
    return 0 if len(runs) == 4 and all(r["summary"]["status"] == "PASS" and r["audit_status"] == "PASS" for r in runs) else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("prepare", "initial", "expansion"))
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/p0_runtime.local.json"))
    parser.add_argument("--cases", type=Path, default=Path("data/synthetic/p0_cases.jsonl"))
    parser.add_argument("--freeze-name", default="prompts_frozen.json")
    parser.add_argument("--reuse-history-from", default=None)
    args = parser.parse_args()
    config = RuntimeConfig.load(args.config)
    selection = json.loads((args.session / "selection_freeze.json").read_text(encoding="utf-8"))
    if sha256(args.cases) != selection["dataset_sha256"] or config.token_tolerance != 0 or config.max_match_candidates != selection["max_match_candidates"]:
        raise ValueError("Frozen input/matching policy changed")
    if args.stage == "prepare":
        result = prepare(args.session, config, args.cases, selection, args.freeze_name, args.reuse_history_from)
    else:
        result = generate(args.session, config, args.cases, selection, args.stage, args.freeze_name)
    raise SystemExit(result)


if __name__ == "__main__":
    main()
