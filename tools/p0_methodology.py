"""P0-only budget diagnostics, independent review preparation and offline audit."""
import argparse
from collections import Counter
import csv
from dataclasses import asdict, replace
import json
from pathlib import Path
import random
import re

from personaslm.conditioning import build_prompt
from personaslm.configuration import RuntimeConfig
from personaslm.evaluation_v2 import VERSION, audit_city_response, generated_turns
from personaslm.fixtures import load_cases
from personaslm.journal import atomic_json, read_events, utc_now
from personaslm.provenance import fingerprint, repository_root, sha256
from personaslm.run_audit import audit_run, text_hash
from personaslm.runner import run_local


PUBLIC = Path("docs/validation")
OLD_SESSION = Path("results/p0_validation/20261012T164648")


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def completeness(raw):
    turns = generated_turns(raw)
    initial = next((t["text"] for t in turns if t["role"] == "Assistant"), "")
    return {"version": "structural_completeness_v1", "first_reply": initial,
            "first_reply_terminal_punctuation": bool(re.search(r"[.!?][\"']?$", initial)),
            "full_output_terminal_punctuation": bool(re.search(r"[.!?][\"']?$", raw.rstrip())),
            "ends_with_role_header": bool(re.search(r"(?:User|Assistant):\s*$", raw)),
            "generated_user_labels": len(re.findall(r"(?m)^User:", raw)),
            "generated_assistant_labels": len(re.findall(r"(?m)^Assistant:", raw)),
            "semantic_completeness_human": None,
            "note": "Structural boundary indicators only; punctuation does not prove semantic completeness."}


def budgets(session):
    plan_path = session / "budget_plan.json"
    plan = read(plan_path)
    base = RuntimeConfig.load(Path("configs/p0_runtime.local.json"))
    if base.as_dict() != plan["config"] or sha256(Path("data/synthetic/p0_cases.jsonl")) != plan["dataset_sha256"]:
        raise ValueError("Frozen configuration or dataset changed")
    destination = session / "budget_results.json"
    if destination.exists() or (session / "budget_execution_started.json").exists():
        raise FileExistsError("Use a fresh session; never automatically repeat diagnostic generations")
    atomic_json(session / "budget_execution_started.json", {"created_utc": utc_now(), "plan_sha256": sha256(plan_path)})
    cases = load_cases(session / "budget_cases.jsonl")
    if [c.case_id for c in cases] != plan["case_ids"]:
        raise ValueError("Selected case order changed")
    old = read(PUBLIC / "P0_case_audit.json")["cases"]
    frozen = {}
    for case in cases:
        frozen[case.case_id] = {}
        for condition in plan["conditions"]:
            original = next(r for r in old if r["case_id"] == case.case_id and r["condition"] == condition)
            prompt = build_prompt(case, condition)
            if prompt.text != original["prompt"]:
                raise ValueError("Diagnostic prompt differs from historical exact input")
            frozen[case.case_id][condition] = {"prompt": asdict(prompt), "token_ids": original["input_token_ids"],
                "matching": {"status": "not_applicable", "source_prompt_sha256": original["prompt_sha256"]}}
    atomic_json(session / "budget_prompt_freeze.json", {"created_utc": utc_now(), "prompts": frozen})
    runs, rows = [], []
    for budget, condition in plan["run_order"]:
        config = replace(base, max_new_tokens=budget)
        common = {k: v for k, v in config.as_dict().items() if k != "max_new_tokens"}
        metadata = {"diagnostic": "generation_budget_v1", "plan_sha256": sha256(plan_path),
                    "effective_config_sha256": fingerprint(config.as_dict()), "common_config_sha256": fingerprint(common),
                    "language_scope": plan["language"], "evaluation_version": "current_city_legacy_v1"}
        summary, directory = run_local(config, condition, session / "budget_cases.jsonl", session / "budget_runs",
                                      frozen_prompts=frozen, run_metadata=metadata)
        audit = audit_run(directory)
        atomic_json(session / f"budget_{budget}_{condition}_audit.json", audit)
        manifest = read(directory / "manifest.json")
        log = (directory / "server.log").read_text(encoding="utf-8", errors="replace")
        eog_ids = sorted({int(x) for x in re.findall(r"EOG token\s*=\s*(\d+)", log)})
        run = {"run_id": directory.name, "run_directory": directory.relative_to(repository_root()).as_posix(),
               "budget": budget, "condition": condition, "summary": summary, "audit_status": audit["status"],
               "git": manifest["reconstruction"]["git"], "config_sha256": fingerprint(config.as_dict()),
               "common_config_sha256": fingerprint(common), "source_sha256": manifest["source_sha256"],
               "language_scope": plan["language"], "manifest_sha256": sha256(directory / "manifest.json")}
        runs.append(run)
        for row in audit["cases"]:
            rows.append({**row, "run_id": directory.name, "budget": budget,
                "config_sha256": run["config_sha256"], "common_config_sha256": run["common_config_sha256"],
                "request_sha256": fingerprint(row.get("generation_request")),
                "reported_eos_or_eog": row.get("backend_finish_reason") in ("eos", "eog"),
                "loaded_eog_ids": eog_ids,
                "eog_ids_in_returned_output": [t for t in row.get("generated_token_ids", []) if t in eog_ids],
                "completeness": completeness(row.get("raw_response", "")),
                "evaluation_version": "current_city_legacy_v1"})
        print(json.dumps({"run_id": directory.name, "budget": budget, "condition": condition,
                          "status": summary["status"], "completed": summary.get("completed_cases")}), flush=True)
        if summary["status"] != "PASS" or audit["status"] != "PASS":
            break
    # Paired comparisons use saved IDs and prompt hashes, not assumptions about seeds.
    pairs = []
    for case in cases:
        for condition in plan["conditions"]:
            selected = sorted([r for r in rows if r["case_id"] == case.case_id and r["condition"] == condition], key=lambda r: r["budget"])
            pairs.append({"case_id": case.case_id, "condition": condition,
                "budgets_observed": [r["budget"] for r in selected],
                "same_prompt_hash": len({r["prompt_sha256"] for r in selected}) == 1,
                "same_input_ids": len({tuple(r["input_token_ids"]) for r in selected}) == 1,
                "same_common_config": len({r["common_config_sha256"] for r in selected}) == 1,
                "96_ids_prefix_of_larger": all(r["generated_token_ids"][:len(selected[0]["generated_token_ids"])] == selected[0]["generated_token_ids"] for r in selected[1:]) if selected else None})
    report = {"created_utc": utc_now(), "scope": plan["phase"], "language_scope": plan["language"],
              "plan_sha256": sha256(plan_path), "runs": runs, "cases": rows, "paired_controls": pairs,
              "status": "PASS" if len(rows) == plan["new_generations_planned"]
              and all(r["audit_status"] == "PASS" for r in runs)
              and all(p["same_prompt_hash"] and p["same_input_ids"] and p["same_common_config"]
                      and p["budgets_observed"] == [96, 192, 256] for p in pairs) else "PARTIAL"}
    atomic_json(destination, report)
    atomic_json(PUBLIC / "P0_budget_diagnostic.json", report)
    return 0 if report["status"] == "PASS" else 2


def review(session):
    frozen = read(OLD_SESSION / "prompts_frozen_v3.json")
    cases = {c.case_id: c for c in load_cases(Path("data/synthetic/p0_cases.jsonl"))}
    source_rows = list(frozen["rows"])
    if len(source_rows) != 40 or any(r["token_difference"] != 0 for r in source_rows):
        raise ValueError("Expected all 40 historical exact-matched pairs")
    random.Random(20261012).shuffle(source_rows)
    packet, mapping = [], []
    dimensions = ["answer_leakage", "new_personal_facts", "contradictory_or_stale_information", "additional_persona_style",
                  "question_and_evidence_unchanged", "other_semantic_interference"]
    for index, row in enumerate(source_rows, 1):
        cid, neutral, reference = row["case_id"], row["neutral_condition"], row["reference_condition"]
        p, ref = frozen["prompts"][cid][neutral]["prompt"], frozen["prompts"][cid][reference]["prompt"]
        # Evidence and question are necessary for leakage checks; no model outputs or old judgments.
        packet.append({"review_id": f"neutral_review_{index:03d}", "language": "en", "translation_performed": False,
            "reference_trusted_evidence": ref["evidence_block"], "candidate_trusted_evidence": p["evidence_block"],
            "reference_question": cases[cid].question, "candidate_question": p["text"].rsplit("\n\nUser: ", 1)[1].removesuffix("\nAssistant:"),
            "neutral_text": p["additions"][0], "reference_date_wrapper": re.findall(r"\d{4}-\d{2}-\d{2}", ref["additions"][0]),
            **{key: None for key in dimensions}, "evidence_quotes": None, "overall_PASS_PARTIAL_FAILED": None,
            "reviewer_id": None, "reviewed_utc": None, "conflicts_of_interest": None, "notes": None})
        mapping.append({"review_id": packet[-1]["review_id"], "case_id": cid, "condition": neutral,
                        "reference_condition": reference, "prompt_sha256": text_hash(p["text"])})
    atomic_json(session / "neutral_review_v2_mapping.json", {"created_utc": utc_now(), "mapping": mapping})
    atomic_json(PUBLIC / "P0_neutral_review_form_v2.json", {"created_utc": utc_now(), "status": "PARTIAL", "human_reviews_completed": 0,
        "source_freeze_sha256": sha256(OLD_SESSION / "prompts_frozen_v3.json"), "items": packet})
    with (PUBLIC / "P0_neutral_review_form_v2.csv").open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(packet[0]))
        writer.writeheader()
        for row in packet:
            writer.writerow({k: json.dumps(v) if isinstance(v, list) else v for k, v in row.items()})
    print(json.dumps({"review_items": len(packet), "human_reviews_completed": 0, "status": "PARTIAL"}))
    return 0


def evaluate(session):
    cases = {c.case_id: c for c in load_cases(Path("data/synthetic/p0_cases.jsonl"))}
    source = PUBLIC / "P0_case_audit.json"
    original = [r for r in read(source)["cases"] if r["condition"] == "C3" and r["fact_judgment"] == "incorrect"]
    if len(original) != 14:
        raise ValueError("Historical C3 review denominator changed")
    rows = []
    for row in original:
        audit = audit_city_response(cases[row["case_id"]], row["parsed_response"])
        contradictions = [c for c in audit["claims"] if c["status"] == "contradicted"]
        uncertain = [c for c in audit["claims"] if c["status"] == "unverifiable"]
        categories = {"verifiable_factual_error": bool(contradictions),
            "generation_stopped_by_length_limit": row["backend_finish_reason"] == "limit",
            "temporal_confusion_supported_by_claims": any(c["time_resolution"] != "current" for c in contradictions),
            "legacy_current_conflict_reason_not_supported": audit["first_reply_city_status"] == "supported" and not any(c["status"] == "contradicted" and c["time_resolution"] == "current" for c in audit["claims"]),
            "undetermined_claims_present": bool(uncertain or audit["unresolved"])}
        rows.append({"case_id": row["case_id"], "run_id": row["run_id"], "condition": "C3", "language": "en",
            "raw_response": row["raw_response"], "raw_sha256": text_hash(row["raw_response"]),
            "parsed_response": row["parsed_response"], "legacy_judgment": row["fact_judgment"],
            "legacy_reason": row["fact_reason"], "legacy_evaluation_version": "current_city_legacy_v1",
            "budget": row["generated_tokens"], "stop_reason": row["backend_finish_reason"],
            "categories_nonexclusive": categories, "completeness": completeness(row["raw_response"]), "supplemental_audit": audit})
    output = {"created_utc": utc_now(), "version": VERSION, "evaluation_source_sha256": sha256(Path("src/personaslm/evaluation_v2.py")),
        "original_audit_sha256": sha256(source), "reviewer": "automated bounded rule audit plus documented agent inspection; no independent human judgments",
        "legacy_results_unchanged": True, "human_reviews_completed": 0, "cases": rows,
        "category_counts": {key: sum(r["categories_nonexclusive"][key] for r in rows) for key in rows[0]["categories_nonexclusive"]},
        "supplemental_full_city_status": dict(Counter(r["supplemental_audit"]["all_city_claims_status"] for r in rows))}
    atomic_json(session / "evaluation_audit_v2.json", output)
    atomic_json(PUBLIC / "P0_evaluation_audit_v2.json", output)
    print(json.dumps({k:v for k,v in output.items() if k != "cases"}))
    return 0


def integrity(session):
    root = repository_root()
    candidates = sorted((root / "results/p0").glob("*/manifest.json"))
    for parent in (OLD_SESSION / "controlled_runs", OLD_SESSION / "tokenizer_runs", session / "budget_runs"):
        candidates += sorted(parent.resolve().glob("*/manifest.json"))
    previous = {r["run_id"]: r for r in read(PUBLIC / "P0_final_evidence.json")["runs"]}
    output = []
    for path in candidates:
        directory = path.parent
        events = read_events(directory)
        manifest = read(path)
        digests = {p.relative_to(directory).as_posix(): sha256(p) for p in sorted(directory.rglob("*")) if p.is_file()}
        matches_prior = digests == previous[directory.name]["files"] if directory.name in previous else None
        if matches_prior is False:
            raise ValueError("Historical run changed: "+directory.name)
        replay = None
        if any(e["kind"] == "raw_generation" for e in events):
            first, second = audit_run(directory), audit_run(directory)
            replay = {"status": first["status"], "identical": first == second, "cases": first["summary"]["cases"]}
            if first != second or first["status"] != "PASS":
                raise ValueError("Saved-input replay failed: "+directory.name)
        row = {"run_id": directory.name, "relative_directory": directory.relative_to(root).as_posix(),
            "journal_integrity": "PASS", "events": len(events), "terminal": events[-1]["data"] if events else None,
            "manifest_sha256": sha256(path), "terminal_event_hash": events[-1]["event_hash"] if events else None,
            "matches_previous_file_inventory": matches_prior, "file_inventory_sha256": fingerprint(digests), "replay": replay}
        output.append(row)
        print(json.dumps(row), flush=True)
    result = {"created_utc": utc_now(), "runs_checked": len(output), "runs": output,
              "note": "Historical BLOCKED/PARTIAL terminal states remain unchanged despite valid journal integrity."}
    name = "integrity_after" if (session / "budget_runs").exists() else "integrity_before"
    atomic_json(session / f"{name}.json", result)
    if name == "integrity_after":
        atomic_json(PUBLIC / "P0_methodology_integrity.json", result)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("budgets", "review", "evaluate", "integrity"))
    parser.add_argument("--session", type=Path, required=True)
    args = parser.parse_args()
    code = {"budgets": budgets, "review": review, "evaluate": evaluate, "integrity": integrity}[args.stage](args.session.resolve())
    raise SystemExit(code)


if __name__ == "__main__":
    main()
