"""Publish synthetic audit evidence with repository-relative paths only.

Original journals stay untouched and ignored by Git. Public derived files have
their own hashes; they do not pretend to be the original event chain.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from personaslm.journal import atomic_json, read_events, utc_now
from personaslm.provenance import repository_root, sha256
from personaslm.run_audit import audit_run, text_hash


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def controls(session):
    output = []
    for filename in ("prompts_frozen.json", "prompts_frozen_v2.json", "prompts_frozen_v3.json"):
        frozen = read(session / filename)
        directory = Path(frozen["tokenizer_run"])
        events = read_events(directory)
        matches = [e["data"] for e in events if e["kind"] == "matching_audit"]
        failed = []
        for match in matches:
            if match["matching_status"] != "PASS":
                candidates = [c for c in match["audit"]["candidate_search"] if "delta" in c]
                best = min(candidates, key=lambda c: abs(c["delta"])) if candidates else None
                failed.append({k: v for k, v in match.items() if k != "audit"} | {"best_candidate": best,
                    "candidate_search": match["audit"]["candidate_search"]})
        probes = next(e["data"] for e in events if e["kind"] == "special_token_probes")
        output.append({"freeze_file": filename, "freeze_sha256": sha256(session / filename), "run_id": directory.name,
            "journal_integrity": "PASS", "events": len(events), "terminal": events[-1]["data"],
            "comparisons": frozen["rows"], "failures": failed, "special_token_probes": probes,
            "source_sha256": read(directory / "manifest.json")["reconstruction"]["source_sha256"]})
        print(json.dumps({"verified": directory.name, "events": len(events)}), flush=True)
    atomic_json(Path("docs/validation/P0_control_matching.json"), {"created_utc": utc_now(), "passes": output})


def final(session):
    root = repository_root()
    original = root / "results/p0/20261012T163840-d0e467a28a4e4df89eb35ce788dfa917"
    inventory = read(session / "original_c0_inventory.json")
    print("original inventory keys", list(inventory), flush=True)
    reports, runs = [], []
    paths = [original] + [Path(r["run_directory"]) for stage in ("initial", "expansion")
                        for r in read(session / f"{stage}_generation.json")["runs"]]
    for directory in paths:
        audit = audit_run(directory)
        second = audit_run(directory)
        if audit != second:
            raise AssertionError("Offline reconstruction changed on repeated audit")
        events = read_events(directory)
        manifest = read(directory / "manifest.json")
        snapshots = manifest.get("reconstruction", {})
        for name, digest in snapshots.get("tool_sha256", {}).items():
            if text_hash(snapshots["tool_source_utf8"][name]) != digest:
                raise AssertionError(f"Tool snapshot digest mismatch: {name}")
        memory = [e["data"] for e in events if e["kind"] == "memory_observation"]
        model = next(e["data"] for e in events if e["kind"] == "preflight")
        props = next(e["data"] for e in events if e["kind"] == "server_identity")
        rel = directory.relative_to(root).as_posix()
        public_config = dict(manifest["configuration"])
        for key in ("model_file", "server_file"):
            public_config[key] = Path(public_config[key]).resolve().relative_to(root).as_posix()
        record = {"run_id": directory.name, "relative_directory": rel, "condition": manifest["condition"],
            "started_utc": manifest["created_utc"], "finished_utc": events[-1]["created_utc"],
            "summary": audit["summary"], "audit_status": audit["status"], "audit_issues": audit["issues"],
            "offline_replay_identical": audit == second, "case_ids": manifest["case_ids"], "configuration": public_config,
            "git": manifest.get("reconstruction", {}).get("git"), "source_sha256": manifest["source_sha256"],
            "dataset_sha256": manifest["cases_sha256"], "model_sha256": model["model"]["sha256"],
            "server_sha256": model["server"]["sha256"], "backend_build": props["validation"]["build_info"],
            "historical_missing_metadata": audit["historical_missing_metadata"], "memory_observations": memory,
            "files": {f.relative_to(directory).as_posix(): sha256(f) for f in sorted(directory.rglob("*")) if f.is_file()},
            "terminal_summary": events[-1]["data"]}
        # Git porcelain may name local source files, but contains no model/private file contents.
        runs.append(record)
        reports.append(audit)
        print(json.dumps({"audited": directory.name, "status": audit["status"], "counts": audit["summary"]}), flush=True)
    if runs[0]["files"] != inventory["files"]:
        raise AssertionError("Original C0 file inventory changed")
    rows = [{"run_id": report["run_id"], **row} for report in reports for row in report["cases"]]
    aggregates = {}
    for condition in ("C0", "C1", "N_style", "C3", "N_history"):
        selected = [r for r in rows if r["condition"] == condition]
        ids = [r["case_id"] for r in selected]
        if len(ids) != len(set(ids)):
            raise AssertionError("A condition repeated a selected case")
        latencies = [r["response_latency_seconds"] for r in selected]
        aggregates[condition] = {"cases": len(selected), "raw_empty": sum(r["raw_response"] == "" for r in selected),
            "raw_nonempty": sum(r["raw_response"] != "" for r in selected),
            "classification": dict(Counter(r["classification"] for r in selected)),
            "factual_judgment": dict(Counter(r["fact_judgment"] for r in selected)),
            "stop": dict(Counter(r["backend_finish_reason"] for r in selected)),
            "latency_seconds_min": min(latencies), "latency_seconds_max": max(latencies),
            "input_tokens_min": min(r["input_token_count"] for r in selected),
            "input_tokens_max": max(r["input_token_count"] for r in selected),
            "errors": sum(bool(r["errors"]) for r in selected)}
    publisher = read(session / "publisher_metadata_verified.json")
    files = json.loads(publisher["responses"][0]["body"])
    artifact = next(f for f in files if f["path"] == "Qwen3.5-2B-Base.Q4_K_M.gguf")
    assert artifact["lfs"]["oid"] == runs[0]["model_sha256"]
    scorer_review = []
    for row in rows:
        if row["fact_reason"] == "incompatible_city_also_asserted" and re.search(r"\blived in\b.+\bin 20\d{2}", row["parsed_response"]):
            scorer_review.append({"run_id": row["run_id"], "case_id": row["case_id"], "condition": row["condition"],
                "original_judgment": row["fact_judgment"], "original_reason": row["fact_reason"],
                "raw_response": row["raw_response"], "trusted_evidence": row["trusted_evidence"],
                "issue": "Legacy evaluator does not recognize dated 'lived in ... in YEAR' as a past cue; possible false positive. Other extra claims may remain unverifiable.",
                "adjudicated_judgment": None, "human_review_complete": False})
    atomic_json(Path("docs/validation/P0_evaluator_review.json"), {"created_utc": utc_now(), "status": "PARTIAL",
        "note": "Screen for a known rule limitation, not independent semantic ground truth; original scoring remains unchanged.", "cases": scorer_review})
    atomic_json(Path("docs/validation/P0_case_audit.json"), {"created_utc": utc_now(), "scope": "P0 synthetic observations only", "cases": rows})
    atomic_json(Path("docs/validation/P0_final_evidence.json"), {"created_utc": utc_now(), "runs": runs,
        "aggregates": aggregates, "hardware": read(session / "hardware_observed.json"),
        "published_artifact": artifact, "publisher_metadata_observed": publisher["responses"][0]["finished_utc"],
        "publisher_revision": "765d2baaa04dbb8d6df3e78af571e6beaa4373d7", "semantic_audit": read(session / "neutral_semantic_audit.json"),
        "selection": read(session / "selection_freeze.json"), "original_c0_unchanged": True,
        "case_audit_sha256": sha256(Path("docs/validation/P0_case_audit.json"))})


def commands(session):
    session = session.resolve()
    root = str(repository_root())
    variants = []
    for base in (root, root.replace("\\", "/"), str(Path.home()), str(Path.home()).replace("\\", "/")):
        variants.append(base)
        for _ in range(4):
            base = json.dumps(base)[1:-1]
            variants.append(base)
    def redact(value):
        if isinstance(value, str):
            for variant in sorted(set(variants), key=len, reverse=True):
                value = value.replace(variant, "<REPOSITORY>")
            return value
        if isinstance(value, list):
            return [redact(item) for item in value]
        if isinstance(value, dict):
            return {key: redact(item) for key, item in value.items()}
        return value
    entries = []
    for path in sorted(session.glob("*.json")):
        data = read(path)
        if isinstance(data, dict) and "argv" in data and "exit_code" in data:
            entries.append({"local_evidence_file": path.relative_to(repository_root()).as_posix(),
                "original_file_sha256": sha256(path), "command_record": redact(data)})
    entries.sort(key=lambda item: item["command_record"]["started_utc"])
    atomic_json(Path("docs/validation/P0_final_commands.json"), {"created_utc": utc_now(),
        "note": "Actual captured command output; repository absolute paths redacted. Original files and hashes retained locally. See development log for initial inspections and apply_patch actions.",
        "commands": entries})
    print(json.dumps({"commands_exported": len(entries), "public_absolute_paths": "redacted"}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("controls", "final", "commands"))
    parser.add_argument("--session", type=Path, required=True)
    args = parser.parse_args()
    {"controls": controls, "final": final, "commands": commands}[args.stage](args.session)


if __name__ == "__main__":
    main()
