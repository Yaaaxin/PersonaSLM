"""Export P0 methodology evidence without changing any experimental record."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics

from personaslm.journal import atomic_json, utc_now
from personaslm.provenance import fingerprint, repository_root, sha256


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def evidence(session):
    public = Path("docs/validation")
    budget = read(session / "budget_results.json")
    plan = read(session / "budget_plan.json")
    before = read(session / "integrity_before.json")
    after = read(session / "integrity_after.json")
    later = {r["run_id"]: r for r in after["runs"]}
    historical_unchanged = all(r["file_inventory_sha256"] == later[r["run_id"]]["file_inventory_sha256"] for r in before["runs"])
    assert historical_unchanged
    rows = budget["cases"]
    assert len(rows) == 18 and budget["status"] == "PASS"
    groups, controls = [], []
    for limit in plan["budgets"]:
        for condition in plan["conditions"]:
            selected = [r for r in rows if r["budget"] == limit and r["condition"] == condition]
            latencies = [r["response_latency_seconds"] for r in selected]
            groups.append({"budget": limit, "condition": condition, "cases": len(selected),
                "generated_tokens": [r["generated_tokens"] for r in selected],
                "stop_reasons": dict(Counter(r["backend_finish_reason"] for r in selected)),
                "reported_eos_eog": sum(r["reported_eos_or_eog"] for r in selected),
                "returned_eog_ids": sum(len(r["eog_ids_in_returned_output"]) for r in selected),
                "first_reply_terminal_punctuation": sum(r["completeness"]["first_reply_terminal_punctuation"] for r in selected),
                "full_output_terminal_punctuation": sum(r["completeness"]["full_output_terminal_punctuation"] for r in selected),
                "latency_seconds_min": min(latencies), "latency_seconds_max": max(latencies),
                "latency_seconds_mean": statistics.mean(latencies)})
    for cid in plan["case_ids"]:
        for condition in plan["conditions"]:
            selected = sorted([r for r in rows if r["case_id"] == cid and r["condition"] == condition], key=lambda r: r["budget"])
            request_common = [{k: v for k, v in r["generation_request"].items() if k != "n_predict"} for r in selected]
            native_common = [{k: v for k, v in r["generation_settings"].items() if k not in ("n_predict", "max_tokens")} for r in selected]
            checks = {"same_request_except_n_predict": len({fingerprint(x) for x in request_common}) == 1,
                "same_native_settings_except_budget": len({fingerprint(x) for x in native_common}) == 1,
                "actual_requested_budget": all(r["generation_request"]["n_predict"] == r["budget"] for r in selected),
                "actual_native_budget": all(r["generation_settings"]["n_predict"] == r["budget"]
                                           and r["generation_settings"]["max_tokens"] == r["budget"] for r in selected),
                "eos_not_ignored": all(r["generation_settings"]["ignore_eos"] is False for r in selected),
                "same_trusted_evidence": len({r["trusted_evidence"] for r in selected}) == 1,
                "192_ids_prefix_of_256": selected[1]["generated_token_ids"] == selected[2]["generated_token_ids"][:192]}
            assert all(checks.values()), (cid, condition, checks)
            controls.append({"case_id": cid, "condition": condition, **checks})
    manifests = [read(Path(r["run_directory"]) / "manifest.json") for r in budget["runs"]]
    assert len({fingerprint(m["source_sha256"]) for m in manifests}) == 1
    assert len({fingerprint(m["reconstruction"]["tool_sha256"]) for m in manifests}) == 1
    assert all(m["reconstruction"]["git"]["dirty"] is True for m in manifests)
    observations = []
    for run in budget["runs"]:
        log = (Path(run["run_directory"]) / "server.log").read_text(encoding="utf-8", errors="replace")
        selected = [line for line in log.splitlines() if any(marker in line for marker in (
            "system_info: n_threads", "offloaded 0/25", "n_ctx                 =", "EOS token", "no API key", "CORS", "- CPU     :"))]
        assert "offloaded 0/25" in log and "n_threads = 4 (n_threads_batch = 4)" in log
        observations.append({"run_id": run["run_id"], "server_log_sha256": sha256(Path(run["run_directory"]) / "server.log"), "observed_lines": selected})
    summary = {"created_utc": utc_now(), "scope": "P0 diagnostic only", "groups": groups, "controls": controls,
        "historical_runs_unchanged": len(before["runs"]) if historical_unchanged else 0,
        "journals_verified": len(after["runs"]), "generation_runs_replayed_twice": sum(r["replay"] is not None for r in after["runs"]),
        "replayed_responses": sum(r["replay"]["cases"] for r in after["runs"] if r["replay"]),
        "new_generation_count": len(rows), "new_raw_nonempty": sum(bool(r["raw_response"].strip()) for r in rows),
        "new_parser_classes": dict(Counter(r["classification"] for r in rows)),
        "all_budget_run_source_and_tool_hashes_equal": True, "all_budget_run_git_dirty": True,
        "backend_observations": observations, "test_command": read(session / "tests_final.json"),
        "limitations": ["Structural completeness flags are not independent human semantic judgments.",
            "Native evaluated input IDs remain unavailable; matching evaluated counts are not ID-level proof.",
            "Observed token prefixes do not guarantee cross-platform output determinism.",
            "No new stopping or response-selection rule was imposed."]}
    atomic_json(session / "methodology_summary.json", summary)
    atomic_json(public / "P0_methodology_summary.json", summary)
    exported_plan = {k: v for k, v in plan.items() if k != "source_at_freeze"}
    exported_plan["original_plan_sha256"] = sha256(session / "budget_plan.json")
    exported_plan["source_at_freeze_summary"] = {k: v for k, v in plan["source_at_freeze"].items() if k in ("git", "source_sha256", "tool_sha256", "evaluation_rules")}
    exported_plan["note"] = "Derived public copy. Full immutable freeze and exact source snapshots are retained locally; hashes identify them. Generation-time snapshots are separately stored in each run manifest."
    atomic_json(public / "P0_budget_plan.json", exported_plan)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("backend_observations", "test_command")}))


def commands(session):
    variants = []
    for value in (str(repository_root()), repository_root().as_posix(), str(Path.home()), Path.home().as_posix()):
        variants.append(value)
        for _ in range(4):
            value = json.dumps(value)[1:-1]
            variants.append(value)
    def redact(value):
        if isinstance(value, str):
            for variant in sorted(set(variants), key=len, reverse=True):
                value = value.replace(variant, "<REPOSITORY_OR_HOME>")
            return value
        if isinstance(value, dict):
            return {k: redact(v) for k, v in value.items()}
        if isinstance(value, list):
            return [redact(v) for v in value]
        return value
    records = []
    for path in sorted(session.glob("*.json")):
        data = read(path)
        if isinstance(data, dict) and "argv" in data and "exit_code" in data:
            records.append({"local_evidence_file": path.relative_to(repository_root()).as_posix(),
                "original_file_sha256": sha256(path), "command_record": redact(data)})
    records.sort(key=lambda r: r["command_record"]["started_utc"])
    atomic_json(Path("docs/validation/P0_methodology_commands.json"), {"created_utc": utc_now(),
        "note": "Captured actual commands. Machine paths redacted; original logs retained locally. Export does not include its own later completion record.",
        "commands": records, "engineering_actions": redact(read(session / "engineering_actions.json"))})
    print(json.dumps({"commands_exported": len(records)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("evidence", "commands"))
    parser.add_argument("--session", type=Path, required=True)
    args = parser.parse_args()
    {"evidence": evidence, "commands": commands}[args.stage](args.session.resolve())
