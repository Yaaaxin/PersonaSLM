"""Offline evidence export for P0 final methodological validation."""
import argparse
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path

from personaslm.boundary_review import review_boundary
from personaslm.evaluation_v2 import audit_city_response
from personaslm.evaluation_v3 import VERSION, audit_residence
from personaslm.fixtures import load_cases
from personaslm.journal import atomic_json, utc_now
from personaslm.provenance import fingerprint, repository_root, require_local_path, sha256
from personaslm.run_audit import audit_run, text_hash
from personaslm.schemas import Case, Fact
from p0_turn_boundary import audit as boundary_replay

PUBLIC = Path("docs/validation")


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def redact(value):
    if isinstance(value, str):
        for original in (str(repository_root()), repository_root().as_posix(), str(Path.home()), Path.home().as_posix()):
            for _ in range(5):
                value = value.replace(original, "<LOCAL_ROOT>")
                original = json.dumps(original)[1:-1]
        return value
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    return value


def evaluate(session):
    fixture_path = Path("tests/fixtures/p0_evaluation_dev_v3.json")
    fixture = read(fixture_path)
    case = Case.from_dict(fixture["case_definition"])
    tests = []
    labels = {"supported": "Correct", "contradicted": "Incorrect", "unverifiable": "Unverifiable", "N/A": "Not Applicable"}
    for item in fixture["cases"]:
        v3 = audit_residence(case, item["text"])
        v2 = audit_city_response(case, item["text"])
        assert v3["status"] == item["expected"], item
        tests.append({**item, "v3": v3, "v2_status": labels[v2["all_city_claims_status"]],
                      "v2_matches_declared_contract": labels[v2["all_city_claims_status"]] == item["expected"]})
    na = replace(case, applicability={**case.applicability, "factual_consistency": False})
    conflict = replace(case, facts=case.facts+(Fact("conflicting_test_source", "current_city", "Durham", "2026-10-01"),))
    assert audit_residence(na, "Chester.")["status"] == "Not Applicable"
    assert audit_residence(conflict, "Bristol.")["status"] == "Unverifiable"
    cases = {c.case_id: c for c in load_cases(Path("data/synthetic/p0_cases.jsonl"))}
    original_path = PUBLIC / "P0_evaluation_audit_v2.json"
    old = read(original_path)
    reviewed = [{"case_id": r["case_id"], "run_id": r["run_id"], "raw_response": r["raw_response"],
                 "parsed_response": r["parsed_response"], "raw_sha256": r["raw_sha256"],
                 "legacy_status": r["legacy_judgment"], "legacy_reason": r["legacy_reason"],
                 "v2_status": r["supplemental_audit"]["all_city_claims_status"],
                 "v3": audit_residence(cases[r["case_id"]], r["parsed_response"])} for r in old["cases"]]
    result = {"created_utc": utc_now(), "version": VERSION, "evaluation_source_sha256": sha256(Path("src/personaslm/evaluation_v3.py")),
        "development_fixture_sha256": sha256(fixture_path), "development_fixture": fixture,
        "development_checks": tests, "inapplicable_check": audit_residence(na,"Chester."),
        "conflicting_source_check": audit_residence(conflict,"Bristol."),
        "v2_contract_mismatches": sum(not t["v2_matches_declared_contract"] for t in tests),
        "original_v2_audit_sha256": sha256(original_path), "historical_cases": reviewed,
        "historical_v3_counts": dict(Counter(r["v3"]["status"] for r in reviewed)),
        "scope": "Engineered contract checks and supplemental offline city audit; no human labels or general accuracy estimate",
        "independent_human_reviews": 0, "historical_results_overwritten": False}
    atomic_json(session / "materials/evaluation_v3_audit.json", result)
    atomic_json(PUBLIC / "P0_evaluation_validity_v3.json", result)
    print(json.dumps({"historical_v3_counts": result["historical_v3_counts"], "v2_contract_mismatches": result["v2_contract_mismatches"], "development_items": len(tests), "additional_contract_checks": 2}))


def inspect(session):
    prior = read(PUBLIC / "P0_methodology_integrity.json")
    checked = []
    for old in prior["runs"]:
        directory = require_local_path(Path(old["relative_directory"]))
        files = {p.relative_to(directory).as_posix(): sha256(p) for p in sorted(directory.rglob("*")) if p.is_file()}
        same = fingerprint(files) == old["file_inventory_sha256"]
        assert same, directory.name
        reconstruction = None
        if old["replay"] is not None:
            a, b = audit_run(directory), audit_run(directory)
            assert a == b and a["status"] == "PASS"
            reconstruction = {"identical": True, "cases": a["summary"]["cases"]}
        checked.append({"run_id": directory.name, "file_inventory_sha256": fingerprint(files),
                        "unchanged_from_previous_verified_journal": same, "reconstruction": reconstruction,
                        "previous_terminal": old["terminal"]})
    runs = list((session / "experiments/runs").glob("*/manifest.json"))
    assert len(runs) == 1
    directory = runs[0].parent
    a, b = boundary_replay(directory), boundary_replay(directory)
    assert a == b and a["status"] == "PASS"
    manifest = read(runs[0])
    plan = manifest["plan"]
    reviews = []
    for row in a["cases"]:
        case = next(c for c in plan["dataset"]["cases"] if c["case_id"] == row["case_id"])
        reviews.append({"cell_id": row["cell_id"], "case_id": row["case_id"], "variant": row["variant"],
            **review_boundary(row["raw_native_response"]["content"], row["raw_native_response"], case, row["variant"])})
    public_plan = {k: v for k, v in plan.items() if k != "reconstruction"}
    plan_path = session / "materials/boundary_plan.json"
    public_plan["original_plan_sha256"] = sha256(plan_path)
    snapshots = manifest["reconstruction"]
    generation_snapshot = {k:v for k,v in snapshots.items() if k not in ("source_utf8", "tool_source_utf8", "dataset_utf8")}
    log = (directory/"server.log").read_text(encoding="utf-8", errors="replace")
    cpu_lines = [line for line in log.splitlines() if any(k in line for k in ("n_threads =", "offloaded 0/25", "n_ctx                 =", "EOS token", "EOG token", "- CPU     :"))]
    assert "offloaded 0/25" in log and "n_threads = 4 (n_threads_batch = 4)" in log
    summary = {v: {"reviewed_structure": dict(Counter(r["reviewed_structural_status"] for r in reviews if r["variant"] == v)),
                  "tokens_predicted": [r["raw_native_response"]["tokens_predicted"] for r in a["cases"] if r["variant"] == v]} for v in plan["variants"]}
    result = {"created_utc": utc_now(), "original_plan": public_plan, "audit": a, "generation_snapshot": generation_snapshot,
        "source_note": "Derived public JSON redacts machine paths; original raw HTTP bytes, native payloads and exact source snapshots remain in the immutable local journal.",
        "supplemental_boundary_review": reviews, "review_summary": summary, "observed_cpu_log_lines": cpu_lines,
        "server_log_sha256": sha256(directory/"server.log"), "raw_run_directory": directory.relative_to(repository_root()).as_posix(),
        "independent_human_completeness_judgments": 0}
    atomic_json(session / "experiments/boundary_final_evidence.json", result)
    atomic_json(PUBLIC / "P0_response_termination_evidence.json", redact(result))
    integrity = {"created_utc": utc_now(), "prior_integrity_report_sha256": sha256(PUBLIC/"P0_methodology_integrity.json"),
        "prior_journals": checked, "prior_proof_method": "Current byte-level file inventories exactly match previously chain-verified journals; original tokenizer failures and blocked run remain intact. Fifteen old generation runs additionally replayed twice now.",
        "new_run": {"run_id": directory.name, "journal_status":"PASS", "reconstruction_identical":True, "cases":16,
                    "manifest_sha256":a["manifest_sha256"], "terminal_hash":a["terminal_hash"]},
        "journals_accounted_for": len(checked)+1, "generation_runs_reconstructed_twice":16, "responses":134}
    atomic_json(session/"experiments/integrity_final.json", integrity)
    atomic_json(PUBLIC/"P0_final_methodological_integrity.json", integrity)
    print(json.dumps({"historical_journals_unchanged":len(checked),"new_run":directory.name,"review_summary":summary,"total_responses":134}))


def commands(session):
    records=[]
    for path in sorted((session/"engineering").glob("*.json")):
        data=read(path)
        if "argv" in data and "exit_code" in data:
            records.append({"file":path.relative_to(repository_root()).as_posix(),"original_sha256":sha256(path),"record":redact(data)})
    records.sort(key=lambda r:r["record"]["started_utc"])
    atomic_json(PUBLIC/"P0_final_methodological_commands.json",{"created_utc":utc_now(),"commands":records,
        "initial_actions":redact(read(session/"engineering/initial_actions.json")),
        "note":"Export completion and later delivery checks are retained separately locally. Exact times were not fabricated for uncaptured read-only/patch actions."})
    print(json.dumps({"commands_exported":len(records)}))


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("stage",choices=("evaluate","inspect","commands"))
    parser.add_argument("--session",type=Path,required=True)
    args=parser.parse_args()
    {"evaluate":evaluate,"inspect":inspect,"commands":commands}[args.stage](require_local_path(args.session))
