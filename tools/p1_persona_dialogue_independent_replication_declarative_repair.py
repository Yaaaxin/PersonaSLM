"""Bounded declarative-history repair for the completed synthetic S/F/H replication.

The controller creates only 48 new H=1 requests.  Its combined analysis reads
the 48 completed H=0 observations from the parent event chain; it never
regenerates them.  Registration, preflight, execution, audit, and analysis are
separate explicit actions so the prospective artifacts can be reviewed first.
"""

from __future__ import annotations

import argparse
import ast
import base64
from collections import Counter, defaultdict
import copy
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time

import p1_persona_dialogue_independent_replication as parent


s, b = parent.s, parent.b
load, sha256, th, require = parent.load, parent.sha256, parent.th, parent.require
write_exclusive = parent.write_exclusive

EVIDENCE = Path(
    "docs/validation/p1/persona_dialogue_independent_replication_declarative_repair_v1")
DESIGN = EVIDENCE / "prospective_design_v1.json"
CASE_TRANSFORM = EVIDENCE / "case_transform_v1.json"
AUTHORIZATION = EVIDENCE / "execution_authorization_v1.json"
FROZEN = EVIDENCE / "frozen_manifest_v1.json"
PREFLIGHT = EVIDENCE / "preflight_v1.json"
AUDIT = EVIDENCE / "execution_audit_v1.json"
ANALYSIS = EVIDENCE / "analysis_v1.json"
TEST_SOURCE = Path(
    "tests/test_p1_persona_dialogue_independent_replication_declarative_repair.py")
ROOT = Path("results/p1_persona_dialogue_independent_replication_declarative_repair/v1")

PARENT_DESIGN = parent.DESIGN
PARENT_CASE_BANK = parent.CASE_BANK
PARENT_FROZEN = parent.FROZEN
PARENT_AUDIT = parent.AUDIT
PARENT_ANALYSIS = parent.ANALYSIS
PARENT_RUN = Path(
    "results/p1_persona_dialogue_independent_replication/v2/runs/"
    "20261018T173447-1b35747a4af44756a1319781a2feb7d2")
PARENT_RUN_MANIFEST = PARENT_RUN / "manifest.json"
PARENT_RUN_SUMMARY = PARENT_RUN / "summary.json"
CURRENT_BUDGET = Path(
    "docs/validation/p1/persona_dialogue_history_semantics_surface_factorial_v2/"
    "analysis_v2.json")

DESIGN_SHA = "31fba764f949ffcdcc07fd348e334195878aeb82de24b1ff3e0e8cc88f919546"
CASE_TRANSFORM_SHA = "f1f1bb31d9e088cf7ffa5f9356a43323bd2217a1585826186fe4c3a13ee86c3b"
PARENT_DESIGN_SHA = "628bedc18b8aa549cb165fbfb3f33ffbb889b5ad3090d7ef86f58112476c156c"
PARENT_CASE_BANK_SHA = "a93cd629c0d152e9eb2325399235882beaebf510d4b6e32b24724975554fab8c"
PARENT_FROZEN_SHA = "55673bc8f9a802fe22f9d4234cd0bea32e806a4d9f3386cd0e483fa1cc716485"
PARENT_AUDIT_SHA = "ed74b2f0b11c3c4a7233d290bf8ca8121b065e311765419fbc3166e9d4afb118"
PARENT_ANALYSIS_SHA = "8d50119d7e91f07a039649a85e4ffd11d007295901130db7b5603ba910776ddf"
PARENT_RUN_MANIFEST_SHA = \
    "265cc8aa596a96bd1a4f30deb033d0dac938d2f15c8ad33258adbc7b690cf07e"
PARENT_RUN_SUMMARY_SHA = \
    "455d389fe252c1f4938f0a57994a3994b4631f3d2a6e9088ebc15dcd2cea4773"
CURRENT_BUDGET_SHA = "b1afd391e9f3fedeb4a1dc920d5b8de242847869203ea52d097ceb4219270104"

MAX_ATTEMPTS = 48
H0_CONDITIONS = ("C0", "C1", "C2", "C4")
H1_CONDITIONS = ("C3", "C5", "C6", "C7")
GENERATION_BASELINE = 292
INFERENCE_BASELINE = 1701.0952766999717
PRIMARY_METRICS = (
    "selection_resolution",
    "current_named_selection",
    "current_preference_choice",
    "history_target_selection",
    "surface_style_uptake",
)
REPAIR_METRICS = PRIMARY_METRICS + ("raw_recommendation_frame_recurrence",)

STARTED = "declarative_repair_generation_started"
RAW = "declarative_repair_raw_generation"
DERIVED = "declarative_repair_result"


def _relative(path):
    return Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix()


def _bound_paths():
    return {
        DESIGN: DESIGN_SHA,
        CASE_TRANSFORM: CASE_TRANSFORM_SHA,
        PARENT_DESIGN: PARENT_DESIGN_SHA,
        PARENT_CASE_BANK: PARENT_CASE_BANK_SHA,
        PARENT_FROZEN: PARENT_FROZEN_SHA,
        PARENT_AUDIT: PARENT_AUDIT_SHA,
        PARENT_ANALYSIS: PARENT_ANALYSIS_SHA,
        PARENT_RUN_MANIFEST: PARENT_RUN_MANIFEST_SHA,
        PARENT_RUN_SUMMARY: PARENT_RUN_SUMMARY_SHA,
        CURRENT_BUDGET: CURRENT_BUDGET_SHA,
    }


def current_budget():
    require(sha256(CURRENT_BUDGET) == CURRENT_BUDGET_SHA,
            "Current cumulative-budget evidence changed")
    observed = load(CURRENT_BUDGET)["cumulative_authorization_after"]
    expected = {
        "generations_limit": 1200,
        "generations_used": GENERATION_BASELINE,
        "inference_seconds_limit": 72000,
        "inference_seconds_used": INFERENCE_BASELINE,
    }
    require(observed == expected, "Current cumulative budget changed")
    return copy.deepcopy(observed)


def source_hashes():
    paths = list(Path("src/personaslm").glob("*.py")) + [
        Path(__file__), TEST_SOURCE, DESIGN, CASE_TRANSFORM,
        Path(parent.__file__), parent.TEST_SOURCE, parent.STRUCTURAL_TEST_SOURCE,
        parent.ANALYSIS_DEPENDENCY, parent.BUDGET_FROZEN,
        *list(_bound_paths().keys()),
    ]
    unique = {Path(path) for path in paths}
    return dict(sorted((_relative(path), sha256(path)) for path in unique))


def request_specs():
    """Derive the exact 48-row order from the SHA-bound parent manifest."""
    plan = load(PARENT_FROZEN)
    selected = [row for row in plan["requests"] if row["condition"] in H1_CONDITIONS]
    require(len(selected) == MAX_ATTEMPTS, "Parent H=1 row count changed")
    return [{
        "order": order,
        "request_id": row["request_id"] + "__declarative_repair_v1",
        "parent_order": row["order"],
        "parent_request_id": row["request_id"],
        "parent_request_sha256": row["request_sha256"],
        "case_id": row["case_id"],
        "condition": row["condition"],
    } for order, row in enumerate(selected)]


def _case_maps(bank=None, transform=None):
    bank = bank or load(PARENT_CASE_BANK)
    transform = transform or load(CASE_TRANSFORM)
    cases = {case["case_id"]: case for case in bank["cases"]}
    mappings = {case["case_id"]: case for case in transform["cases"]}
    require(set(cases) == set(mappings), "Transform does not cover the parent cases")
    return cases, mappings


def declarative_messages(case, mapping, condition, design=None, bank=None):
    design = design or load(PARENT_DESIGN)
    bank = bank or load(PARENT_CASE_BANK)
    require(condition in H1_CONDITIONS, "Only H=1 cells may be repaired")
    factors, raw_messages = parent.construction(design, bank, case, condition)
    require(factors["H"] == 1 and len(raw_messages) == 4 and
            [item["role"] for item in raw_messages] ==
            ["system", "user", "assistant", "user"], "Unexpected parent history layout")
    require(raw_messages[2]["content"] == mapping["history_assistant_raw"],
            "Raw archived assistant changed")
    messages = copy.deepcopy(raw_messages)
    messages[2]["content"] = mapping["history_assistant_declarative"]
    return factors, messages, raw_messages


def _validate_transform(case, mapping):
    raw = mapping["history_assistant_raw"]
    declarative = mapping["history_assistant_declarative"]
    target = case["history_selected_target"]
    require(mapping["history_selected_target"] == target and
            case["history_messages"][1]["content"] == raw,
            "Transform target/raw source changed")
    raw_first = f"I recommend the {target}."
    declarative_first = f"My choice was {target}."
    require(raw.startswith(raw_first + " ") and
            declarative.startswith(declarative_first + " "),
            "Unexpected first-sentence transform")
    require(raw[len(raw_first):] == declarative[len(declarative_first):],
            "Archived reason sentence changed")


def archived_index(conditions):
    audit = load(PARENT_AUDIT)
    rows = [row for row in audit["rows"] if row["condition"] in conditions]
    require(len(rows) == 12 * len(conditions) and
            all(row["state"] == "COMPLETED" for row in rows),
            "Archived parent row inventory changed")
    return [{key: row[key] for key in (
        "request_id", "request_sha256", "case_id", "condition", "state",
        "raw_text_sha256", "first_reply_sha256", "generated_tokens",
        "stop_reason", "latency_seconds")}
        for row in rows]


def validate_design():
    for path, expected in _bound_paths().items():
        require(path.is_file() and sha256(path) == expected,
                "Bound evidence changed: " + path.as_posix())
    design, transform = load(DESIGN), load(CASE_TRANSFORM)
    parent_design, bank = load(PARENT_DESIGN), load(PARENT_CASE_BANK)
    require(design["status"] ==
            "FROZEN_PROSPECTIVE_OUTPUT_INFORMED_DEVELOPMENT_NOT_AUTHORIZED_NOT_EXECUTED",
            "Design status changed")
    require(transform["status"] ==
            "FROZEN_PROSPECTIVE_OUTPUT_INFORMED_DEVELOPMENT_MATERIALS_NOT_EXECUTED",
            "Transform status changed")
    require(design["evidence_level"] == "OUTPUT_INFORMED_SYNTHETIC_DEVELOPMENT" and
            design["output_informed_status"]["explicit"] is True,
            "Output-informed evidence boundary changed")
    require(design["bindings"]["case_transform"] == {
        "path": CASE_TRANSFORM.as_posix(), "sha256": CASE_TRANSFORM_SHA},
        "Transform binding changed")
    require(subprocess.check_output(["git", "branch", "--show-current"],
                                    text=True).strip() ==
            design["bindings"]["source_branch"], "Source branch changed")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() ==
            design["bindings"]["source_head"], "Source HEAD changed")
    budget = design["resource_budget"]
    require(budget["requests"] == MAX_ATTEMPTS and
            budget["maximum_generated_tokens"] == MAX_ATTEMPTS * 96 and
            budget["minimum_available_physical_ram_bytes"] == 3 * 1024 ** 3 and
            budget["minimum_free_output_disk_bytes"] == 1024 ** 3 and
            budget["actual_completion_inference_seconds_ceiling"] == 2880.0 and
            budget["batch_wall_seconds_ceiling"] == 4320.0,
            "Resource budget changed")
    observed_budget = current_budget()
    require(budget["global_baseline"] == {
        "generation_ceiling": observed_budget["generations_limit"],
        "generations_used": observed_budget["generations_used"],
        "generations_remaining": observed_budget["generations_limit"] -
            observed_budget["generations_used"],
        "inference_wall_seconds_ceiling": observed_budget["inference_seconds_limit"],
        "inference_wall_seconds_used": observed_budget["inference_seconds_used"],
        "inference_wall_seconds_remaining": observed_budget["inference_seconds_limit"] -
            observed_budget["inference_seconds_used"],
    }, "Design cumulative baseline changed")
    authorization = design["authorization"]
    require(all(authorization[key] is False for key in (
        "execution_authorized", "tokenization_authorized", "preflight_authorized",
        "model_server_launch_authorized", "manifest_creation_authorized")) and
        authorization["maximum_generation_attempts_if_authorized"] == MAX_ATTEMPTS and
        authorization["retries"] == authorization["hidden_warmups"] == 0,
        "Prospective authorization boundary changed")
    require(all(value == 0 for value in design["preexecution_state"].values()),
            "Nonzero preexecution state")
    require(design["model"]["artifact_sha256"] ==
            parent_design["model"]["artifact_sha256"] and
            design["runtime"] == parent_design["runtime"],
            "Model/runtime differs from parent")
    require(design["reuse_and_generation_policy"]["archived_h0_conditions"] ==
            list(H0_CONDITIONS) and
            design["reuse_and_generation_policy"]["new_h1_conditions"] ==
            list(H1_CONDITIONS) and
            design["reuse_and_generation_policy"]["archived_h0_results"] == 48 and
            design["reuse_and_generation_policy"]["new_h1_requests"] == 48,
            "Reuse/new-generation allocation changed")
    cases, mappings = _case_maps(bank, transform)
    for case_id, case in cases.items():
        _validate_transform(case, mappings[case_id])
        for condition in H1_CONDITIONS:
            factors, messages, raw = declarative_messages(
                case, mappings[case_id], condition, parent_design, bank)
            require(factors == {key: parent_design["factors"]["conditions"][condition][key]
                                for key in ("S", "F", "H", "control")},
                    "Factor binding changed")
            require(messages[0] == raw[0] and messages[1] == raw[1] and
                    messages[3] == raw[3] and messages[2]["role"] == raw[2]["role"],
                    "Material outside archived assistant text changed")
    specs = request_specs()
    require([row["order"] for row in specs] == list(range(MAX_ATTEMPTS)) and
            len({row["request_id"] for row in specs}) == MAX_ATTEMPTS and
            Counter(row["condition"] for row in specs) ==
            Counter({condition: 12 for condition in H1_CONDITIONS}) and
            Counter(row["case_id"] for row in specs) ==
            Counter({case_id: 4 for case_id in cases}), "Request allocation changed")
    h0 = archived_index(H0_CONDITIONS)
    raw_h1 = archived_index(H1_CONDITIONS)
    require(len(h0) == len(raw_h1) == MAX_ATTEMPTS, "Archived allocation changed")
    parent_summary = load(PARENT_RUN_SUMMARY)
    require(parent_summary["status"] == "PASS" and parent_summary["results"] == 96 and
            parent_summary["retries"] == 0, "Parent run is not complete")
    weights = design["estimands"]["repaired_factorial_weights"]
    require(set(weights) == {"S", "F", "H_DECLARATIVE", "SxF",
                             "SxH_DECLARATIVE", "FxH_DECLARATIVE",
                             "SxFxH_DECLARATIVE"} and
            all(set(value) == {f"C{i}" for i in range(8)} for value in weights.values()),
            "Factorial estimands changed")
    return {"status": "PASS_PROSPECTIVE_NOT_AUTHORIZED_NOT_EXECUTED",
            "new_h1_requests": len(specs), "archived_h0_rows": len(h0),
            "archived_raw_h1_comparators": len(raw_h1),
            "model_generations": 0, "tokenizer_calls": 0,
            "authorization_files_created": 0, "preflight_receipts_created": 0}


def authorization_requirements():
    validate_design()
    design = load(DESIGN)
    return {
        "schema_version":
            "personaslm_independent_replication_declarative_repair_authorization_v1",
        "status": "AUTHORIZED_BEFORE_TOKENIZATION_OR_MODEL_EXECUTION",
        "design": {"path": DESIGN.as_posix(), "sha256": DESIGN_SHA},
        "case_transform": {"path": CASE_TRANSFORM.as_posix(),
                           "sha256": CASE_TRANSFORM_SHA},
        "parent_frozen_manifest": {"path": PARENT_FROZEN.as_posix(),
                                   "sha256": PARENT_FROZEN_SHA},
        "parent_execution_audit": {"path": PARENT_AUDIT.as_posix(),
                                   "sha256": PARENT_AUDIT_SHA},
        "current_budget_evidence": {"path": CURRENT_BUDGET.as_posix(),
                                    "sha256": CURRENT_BUDGET_SHA},
        "source_hashes": source_hashes(),
        "model_sha256": design["model"]["artifact_sha256"],
        "backend_sha256": design["runtime"]["backend_sha256"],
        "template_sha256": design["runtime"]["chat_template_sha256"],
        "maximum_native_tokenizer_calls": MAX_ATTEMPTS,
        "maximum_live_server_tokenizer_checks": MAX_ATTEMPTS,
        "maximum_generation_attempts": MAX_ATTEMPTS,
        "retries": 0,
        "hidden_warmups": 0,
        "minimum_available_physical_ram_bytes": 3 * 1024 ** 3,
        "minimum_free_output_disk_bytes": 1024 ** 3,
        "actual_completion_inference_seconds_ceiling": 2880.0,
        "batch_wall_seconds_ceiling": 4320.0,
        "global_baseline": current_budget(),
        "results_root": ROOT.as_posix(),
        "scope": "Only the exact 48 derived C3/C5/C6/C7 declarative-history requests; archived C0/C1/C2/C4 are read-only and must not be regenerated.",
    }


def validate_authorization(path=AUTHORIZATION):
    authorization = load(path)
    required = authorization_requirements()
    for key, expected in required.items():
        require(authorization.get(key) == expected, "Authorization changed: " + key)
    require(authorization.get("researcher") == "Yaxin ZHENG",
            "Researcher authorization missing")
    allowed = set(required) | {"researcher", "authorized_utc", "authorization_statement"}
    require(set(authorization) <= allowed, "Unexpected authorization field")
    return authorization


def _frozen_model(design):
    model, runtime = design["model"], design["runtime"]
    return {"model_label": model["label"], "model_file": model["artifact_path"],
        "model_sha256": model["artifact_sha256"],
        "backend_file": runtime["backend_path"],
        "backend_sha256": runtime["backend_sha256"],
        "quantization": model["quantization"],
        "artifact_revision": model["artifact_revision"],
        "intended_upstream_revision": model["intended_upstream_revision"],
        "conversion_lineage": model["conversion_lineage"]}


def register(authorization_path):
    """Freeze 48 prompts/token arrays; never makes a completion request."""
    require(not FROZEN.exists() and not (ROOT / "native_tokenizer").exists(),
            "Registration exists; do not replace")
    require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
            "Execution evidence exists; do not repeat")
    authorization_path = Path(authorization_path)
    require(authorization_path.resolve() == AUTHORIZATION.resolve(),
            "Registration requires the official authorization path")
    authorization = validate_authorization(authorization_path)
    checks = validate_design()
    design, parent_design, bank, transform = (
        load(DESIGN), load(PARENT_DESIGN), load(PARENT_CASE_BANK), load(CASE_TRANSFORM))
    runtime, model = design["runtime"], design["model"]
    require(sha256(Path(model["artifact_path"])) == model["artifact_sha256"] and
            sha256(Path(runtime["backend_path"])) == runtime["backend_sha256"] and
            sha256(Path(runtime["chat_template_path"])) ==
            runtime["chat_template_sha256"], "Model/backend/template changed")
    native = load(parent.BUDGET_FROZEN)["native_tokenizer_identity"]
    tokenizer = Path(runtime["backend_path"]).with_name("llama-tokenize.exe")
    require(sha256(parent.BUDGET_FROZEN) == parent.BUDGET_FROZEN_SHA and
            native["tokenizer_sha256"] == parent.TOKENIZER_SHA and
            sha256(tokenizer) == parent.TOKENIZER_SHA, "Tokenizer identity changed")
    require({path.name: sha256(path) for path in tokenizer.parent.glob("*.dll")} ==
            native["dll_hashes"], "Backend DLL set changed")
    require(s.memory_observation(os.getpid()).get("system", {}).get(
            "available_physical", 0) >= 3 * 1024 ** 3, "Less than 3 GiB available RAM")
    require(shutil.disk_usage(".").free >= 1024 ** 3, "Less than 1 GiB free disk")
    template = Path(runtime["chat_template_path"]).read_text(encoding="utf-8")
    cases, mappings = _case_maps(bank, transform)
    rows, logs = [], []
    for item in request_specs():
        case = cases[item["case_id"]]
        factors, messages, _ = declarative_messages(
            case, mappings[item["case_id"]], item["condition"], parent_design, bank)
        prompt = s.render(template, messages)
        argv = [str(tokenizer.resolve()), "-m", str(Path(model["artifact_path"]).resolve()),
                "--stdin", "--ids", "--offline"]
        started = b.utc_now()
        completed = subprocess.run(
            argv, input=prompt.encode("utf-8"), capture_output=True, timeout=90,
            env={key: value for key, value in os.environ.items()
                 if not key.upper().startswith("LLAMA_ARG_")},
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        require(completed.returncode == 0, "Native tokenizer failed")
        token_ids = ast.literal_eval(completed.stdout.decode("utf-8", "replace").strip())
        require(isinstance(token_ids, list) and token_ids and
                all(type(value) is int and value >= 0 for value in token_ids), "Token IDs")
        token_log = {"started_utc": started, "finished_utc": b.utc_now(),
            "argv": argv, "returncode": completed.returncode,
            "stdout": completed.stdout.decode("utf-8", "replace"),
            "stderr": completed.stderr.decode("utf-8", "replace"),
            "prompt_sha256": th(prompt), "generation_requests": 0}
        log_path = ROOT / "native_tokenizer" / f"{item['order']:04d}.json"
        write_exclusive(log_path, token_log)
        logs.append({"path": log_path.as_posix(), "sha256": sha256(log_path)})
        row = {**item, "persona_id": case["persona_id"],
            "history_regime": case["history_regime"], "factors": factors,
            "messages": messages, "prompt": prompt, "prompt_sha256": th(prompt),
            "input_token_ids": token_ids, "input_tokens": len(token_ids),
            "input_token_ids_sha256": th(str(token_ids)),
            "preferred_option": case["preferred_option"],
            "history_favored_option": case["history_favored_option"],
            "options": case["options"],
            "history_target_strings": case["history_target_strings"],
            "history_selected_target": case["history_selected_target"],
            "metric_applicability": case["metric_applicability"],
            "current_notes_sha256": th(case["fixed_current_notes"]),
            "current_user_sha256": th(case["fixed_current_user"]),
            "max_new_tokens": 96, "seed": 42, "temperature": 0.0, "top_p": 1.0,
            "stop": [], "cache_prompt": False, "ignore_eos": False}
        require(row["input_tokens"] + row["max_new_tokens"] <=
                runtime["context_tokens"], "Context overflow")
        row["request_sha256"] = th(json.dumps(
            row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        rows.append(row)
    plan = {"version":
            "p1_persona_dialogue_independent_replication_declarative_repair_manifest_v1",
        "evidence_level": design["evidence_level"],
        "design_path": DESIGN.as_posix(), "design_sha256": DESIGN_SHA,
        "case_transform_path": CASE_TRANSFORM.as_posix(),
        "case_transform_sha256": CASE_TRANSFORM_SHA,
        "parent_frozen_manifest_sha256": PARENT_FROZEN_SHA,
        "parent_execution_audit_sha256": PARENT_AUDIT_SHA,
        "authorization_path": authorization_path.as_posix(),
        "authorization_sha256": sha256(authorization_path),
        "model": _frozen_model(design), "runtime": runtime,
        "template_path": runtime["chat_template_path"],
        "template_sha256": runtime["chat_template_sha256"],
        "resource_budget": design["resource_budget"], "requests": rows,
        "archived_h0_reuse_index": archived_index(H0_CONDITIONS),
        "archived_raw_h1_comparator_index": archived_index(H1_CONDITIONS),
        "native_tokenizer_identity": {"path": tokenizer.as_posix(),
            "tokenizer_sha256": parent.TOKENIZER_SHA,
            "dll_hashes": native["dll_hashes"]},
        "native_tokenizer_logs": logs,
        "registration_source_hashes": source_hashes(),
        "registered_utc": b.utc_now(), "new_model_generations": 0,
        "archived_h0_regenerations": 0}
    require(authorization["maximum_generation_attempts"] == len(rows) == MAX_ATTEMPTS,
            "Authorization row count")
    write_exclusive(FROZEN, plan)
    validate_plan(load(FROZEN))
    return {"status": "REGISTERED_NO_GENERATIONS", "manifest_sha256": sha256(FROZEN),
            "authorization_sha256": sha256(authorization_path),
            "native_tokenizer_calls": len(rows), "generation_requests": 0,
            "archived_h0_regenerations": 0, **checks}


def validate_plan(plan):
    require(plan["version"] ==
            "p1_persona_dialogue_independent_replication_declarative_repair_manifest_v1",
            "Manifest version")
    require(plan["design_sha256"] == sha256(DESIGN) == DESIGN_SHA and
            plan["case_transform_sha256"] == sha256(CASE_TRANSFORM) ==
            CASE_TRANSFORM_SHA, "Design/transform binding")
    require(Path(plan["authorization_path"]).resolve() == AUTHORIZATION.resolve() and
            plan["authorization_sha256"] == sha256(AUTHORIZATION),
            "Authorization binding")
    validate_authorization(AUTHORIZATION)
    checks = validate_design()
    require(plan["registration_source_hashes"] == source_hashes(),
            "Registered source changed")
    design, parent_design, bank, transform = (
        load(DESIGN), load(PARENT_DESIGN), load(PARENT_CASE_BANK), load(CASE_TRANSFORM))
    require(plan["model"] == _frozen_model(design) and
            plan["runtime"] == design["runtime"] and
            plan["resource_budget"] == design["resource_budget"],
            "Frozen model/runtime/budget changed")
    require(plan["new_model_generations"] == 0 and
            plan["archived_h0_regenerations"] == 0,
            "Registration generation state changed")
    require(plan["archived_h0_reuse_index"] == archived_index(H0_CONDITIONS) and
            plan["archived_raw_h1_comparator_index"] == archived_index(H1_CONDITIONS),
            "Archived index changed")
    require(plan["template_sha256"] == sha256(Path(plan["template_path"])),
            "Template changed")
    native = load(parent.BUDGET_FROZEN)["native_tokenizer_identity"]
    tokenizer = Path(design["runtime"]["backend_path"]).with_name("llama-tokenize.exe")
    require(plan["native_tokenizer_identity"] == {
        "path": tokenizer.as_posix(), "tokenizer_sha256": parent.TOKENIZER_SHA,
        "dll_hashes": native["dll_hashes"]}, "Native tokenizer identity changed")
    rows, specs = plan["requests"], request_specs()
    require(len(rows) == len({row["request_id"] for row in rows}) == MAX_ATTEMPTS and
            [{key: row[key] for key in specs[0]} for row in rows] == specs,
            "Registered request order changed")
    require(len(plan["native_tokenizer_logs"]) == MAX_ATTEMPTS,
            "Tokenizer log count changed")
    template = Path(plan["template_path"]).read_text(encoding="utf-8")
    cases, mappings = _case_maps(bank, transform)
    for index, row in enumerate(rows):
        case = cases[row["case_id"]]
        factors, messages, _ = declarative_messages(
            case, mappings[row["case_id"]], row["condition"], parent_design, bank)
        require(row["order"] == index and row["factors"] == factors and
                row["messages"] == messages, "Registered prompt materials changed")
        require(row["prompt"] == s.render(template, messages) and
                row["prompt_sha256"] == th(row["prompt"]), "Rendered prompt changed")
        require(row["input_token_ids_sha256"] == th(str(row["input_token_ids"])) and
                len(row["input_token_ids"]) == row["input_tokens"] and
                row["input_tokens"] + 96 <= 4096, "Token binding changed")
        require(row["request_sha256"] == th(json.dumps(
            {key: value for key, value in row.items() if key != "request_sha256"},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"))),
            "Request hash changed")
        record = plan["native_tokenizer_logs"][index]
        expected_path = ROOT / "native_tokenizer" / f"{index:04d}.json"
        require(record == {"path": expected_path.as_posix(),
                           "sha256": sha256(expected_path)}, "Tokenizer log changed")
        token_log = load(expected_path)
        require(token_log["returncode"] == token_log["generation_requests"] == 0 and
                token_log["prompt_sha256"] == row["prompt_sha256"] and
                ast.literal_eval(token_log["stdout"].strip()) == row["input_token_ids"],
                "Tokenizer log content changed")
    return {**checks,
            "input_token_range": [min(row["input_tokens"] for row in rows),
                                  max(row["input_tokens"] for row in rows)]}


def preflight(check_headroom=True, require_unused=True):
    plan = load(FROZEN)
    checks = validate_plan(plan)
    authorization = validate_authorization(Path(plan["authorization_path"]))
    config = parent.cfg(plan)
    identity = b.file_preflight(config)
    require(identity["status"] == "PASS" and
            identity["model"]["sha256"] == plan["model"]["model_sha256"] and
            identity["server"]["sha256"] == plan["model"]["backend_sha256"],
            "Model/backend identity")
    native = plan["native_tokenizer_identity"]
    tokenizer = Path(native["path"])
    require(sha256(tokenizer) == native["tokenizer_sha256"] == parent.TOKENIZER_SHA and
            {path.name: sha256(path) for path in tokenizer.parent.glob("*.dll")} ==
            native["dll_hashes"], "Tokenizer/DLL identity")
    for record in plan["native_tokenizer_logs"]:
        require(sha256(Path(record["path"])) == record["sha256"],
                "Tokenizer log changed")
    baseline = current_budget()
    require(baseline["generations_limit"] - baseline["generations_used"] >= MAX_ATTEMPTS and
            baseline["inference_seconds_limit"] - baseline["inference_seconds_used"] >=
            plan["resource_budget"]["actual_completion_inference_seconds_ceiling"],
            "Cumulative budget insufficient")
    if require_unused:
        require(not (ROOT / "claim.json").exists() and
                not list((ROOT / "runs").glob("*")), "Existing allocation: no repeat")
    memory = s.memory_observation(os.getpid())
    if check_headroom:
        require(memory.get("system", {}).get("available_physical", 0) >=
                plan["resource_budget"]["minimum_available_physical_ram_bytes"],
                "Less than 3 GiB available RAM")
    require(shutil.disk_usage(".").free >=
            plan["resource_budget"]["minimum_free_output_disk_bytes"],
            "Output disk reserve")
    return {"status": "PASS", "checked_utc": b.utc_now(), "checks": checks,
        "identity": identity, "manifest_sha256": sha256(FROZEN),
        "authorization_sha256": sha256(AUTHORIZATION),
        "design_sha256": DESIGN_SHA, "case_transform_sha256": CASE_TRANSFORM_SHA,
        "parent_frozen_manifest_sha256": PARENT_FROZEN_SHA,
        "parent_execution_audit_sha256": PARENT_AUDIT_SHA,
        "current_budget_evidence_sha256": CURRENT_BUDGET_SHA,
        "source_hashes": source_hashes(), "configuration": config.as_dict(),
        "server_command": s.command(plan), "memory_before_run": memory,
        "cumulative_baseline": baseline,
        "live_gate": "All 48 parse_special=true token arrays must match before any completion.",
        "archived_h0_regenerations": 0,
        "authorization": {"researcher": authorization["researcher"],
                          "maximum_attempts": MAX_ATTEMPTS, "retries": 0}}


def preflight_receipt():
    try:
        return preflight()
    except BaseException as exc:
        try:
            memory = s.memory_observation(os.getpid())
        except BaseException as observation_error:
            memory = {"observation_error": {"type": type(observation_error).__name__,
                                             "message": str(observation_error)}}
        try:
            disk_free = shutil.disk_usage(".").free
        except BaseException:
            disk_free = None
        return {"status": "FAIL", "checked_utc": b.utc_now(),
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "expected_bindings": {"design_sha256": DESIGN_SHA,
                "case_transform_sha256": CASE_TRANSFORM_SHA,
                "parent_frozen_manifest_sha256": PARENT_FROZEN_SHA,
                "parent_execution_audit_sha256": PARENT_AUDIT_SHA,
                "current_budget_evidence_sha256": CURRENT_BUDGET_SHA},
            "memory_observation": memory, "free_output_disk_bytes": disk_free,
            "minimum_available_physical_ram_bytes": 3 * 1024 ** 3,
            "minimum_free_output_disk_bytes": 1024 ** 3,
            "model_server_launches": 0, "completion_calls": 0,
            "new_model_generations": 0, "archived_h0_regenerations": 0}


def _augmented_score(result_row):
    score = copy.deepcopy(result_row["automatic_score"])
    assessable = score["measurement_state"] != "BOUNDARY_CENSORED"
    category = score["selection_category"]
    score["selection_resolution"] = (None if not assessable else int(
        category in ("CURRENT_A", "CURRENT_B", "HISTORY_TARGET")))
    first = result_row["response_status"]["first_span"]["text"]
    score["raw_recommendation_frame_recurrence"] = (None if not assessable else int(
        parent._normalized(first).startswith("i recommend the ")))
    return score


def result(row, persona, response, latency):
    value = parent.result(row, persona, response, latency)
    value["automatic_score"] = _augmented_score(value)
    value["evidence_level"] = "OUTPUT_INFORMED_SYNTHETIC_DEVELOPMENT"
    return value


def inventory(plan, events):
    attempted, raw, derived = [], {}, {}
    for event in events:
        data = event["data"]
        if event["kind"] == STARTED:
            require(len(attempted) < MAX_ATTEMPTS and
                    data == plan["requests"][len(attempted)],
                    "Repeated, reordered, or unplanned attempt")
            attempted.append(data["request_id"])
        elif event["kind"] == RAW:
            request_id = data["request_id"]
            require(request_id in attempted and request_id not in raw,
                    "Unbound or duplicate raw response")
            raw[request_id] = data
        elif event["kind"] == DERIVED:
            request_id = data["request_id"]
            require(request_id in raw and request_id not in derived,
                    "Unbound or duplicate derived result")
            derived[request_id] = data
    return attempted, raw, derived


def validate_run_bindings(claim, run_manifest, plan, authorization):
    require(claim["manifest_sha256"] == sha256(FROZEN) and
            claim["authorization_sha256"] == sha256(AUTHORIZATION) and
            claim["design_sha256"] == sha256(DESIGN) == DESIGN_SHA and
            claim["case_transform_sha256"] == sha256(CASE_TRANSFORM) ==
            CASE_TRANSFORM_SHA and
            claim["parent_frozen_manifest_sha256"] == PARENT_FROZEN_SHA and
            claim["parent_execution_audit_sha256"] == PARENT_AUDIT_SHA,
            "Run claim binding changed")
    require(run_manifest["claim"] == claim and
            run_manifest["frozen_manifest"] == plan and
            run_manifest["authorization"] == authorization,
            "Run manifest binding changed")
    return True


def run(preflight_path):
    preflight_path = Path(preflight_path)
    fresh, stored, plan = preflight(), load(preflight_path), load(FROZEN)
    require(preflight_path.resolve() == PREFLIGHT.resolve(),
            "Only the official preflight is accepted")
    require(stored.get("status") == fresh.get("status") == "PASS",
            "Run requires a frozen passing preflight")
    keys = ("manifest_sha256", "authorization_sha256", "design_sha256",
            "case_transform_sha256", "parent_frozen_manifest_sha256",
            "parent_execution_audit_sha256", "current_budget_evidence_sha256",
            "source_hashes", "configuration", "server_command")
    for key in keys:
        require(fresh[key] == stored[key], "Preflight binding changed: " + key)
    with b.writer_lock(ROOT):
        require(not (ROOT / "claim.json").exists() and
                not list((ROOT / "runs").glob("*")), "Existing allocation: no repeat")
        claim = {key: fresh[key] for key in keys if key not in (
            "configuration", "server_command")}
        claim.update(preflight_sha256=sha256(preflight_path),
                     maximum_attempts=MAX_ATTEMPTS, retries=0, hidden_warmups=0,
                     archived_h0_regenerations=0)
        write_exclusive(ROOT / "claim.json", claim)
        authorization = load(AUTHORIZATION)
        journal = b.RunJournal(ROOT / "runs", {
            "phase": "P1 output-informed declarative-history S/F/H repair",
            "evidence_level": "OUTPUT_INFORMED_SYNTHETIC_DEVELOPMENT",
            "claim": claim, "frozen_manifest": plan,
            "authorization": authorization,
            "configuration": parent.cfg(plan).as_dict(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                text=True).strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"],
                                                  text=True),
            "python": platform.python_version(), "platform": platform.platform()})
        for path, digest in claim["source_hashes"].items():
            destination = journal.directory / "source_snapshot" / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as handle:
                handle.write(Path(path).read_bytes())
            require(sha256(destination) == digest, "Source snapshot changed")
        started, active, status = time.monotonic(), None, "BLOCKED"
        inference_seconds, failed_completion_seconds = 0.0, 0.0
        personas = load(PARENT_CASE_BANK)["personas"]
        try:
            journal.write("preflight", fresh)
            with s.Server(plan, journal) as server:
                client = b.LlamaClient(parent.cfg(plan).endpoint, timeout=180,
                                       audit=journal.write)
                props = client.request("/props")
                binding = b.validate_server_properties(props, parent.cfg(plan))
                require(binding["build_info"] == "b11573-0f701c882", "Backend build")
                journal.write("effective_server_defaults", {"props": props,
                                                              "validation": binding})
                for row in plan["requests"]:
                    tokens = client.request("/tokenize", {"content": row["prompt"],
                        "add_special": True, "parse_special": True,
                        "with_pieces": False})["tokens"]
                    require(tokens == row["input_token_ids"],
                            "Live native tokenizer changed")
                    journal.write("live_prompt_verified", {"request_id": row["request_id"],
                                  "token_ids_sha256": th(str(tokens))})
                journal.write("live_preflight_pass", {"prompts": MAX_ATTEMPTS,
                                                       "completed_inference": 0})
                print(json.dumps({"live_preflight": "PASS", "planned": MAX_ATTEMPTS}),
                      flush=True)
                for row in plan["requests"]:
                    remaining_wall = plan["resource_budget"][
                        "batch_wall_seconds_ceiling"] - (time.monotonic() - started)
                    remaining_inference = plan["resource_budget"][
                        "actual_completion_inference_seconds_ceiling"] - inference_seconds
                    require(remaining_wall > 0 and remaining_inference > 0,
                            "Registered time ceiling reached; preserve suffix")
                    server.assert_running()
                    client.timeout = min(180, remaining_wall, remaining_inference)
                    active = row["request_id"]
                    journal.write(STARTED, row)
                    tick = time.monotonic()
                    try:
                        response = client.request("/completion", parent.payload(row))
                    except BaseException:
                        failed_latency = time.monotonic() - tick
                        inference_seconds += failed_latency
                        failed_completion_seconds += failed_latency
                        journal.write("declarative_repair_completion_failed", {
                            "request_id": active, "elapsed_seconds": failed_latency})
                        raise
                    latency = time.monotonic() - tick
                    inference_seconds += latency
                    journal.write(RAW, {"request_id": active, "response": response,
                                        "latency_seconds": latency})
                    journal.write(DERIVED, result(
                        row, personas[row["persona_id"]], response, latency))
                    print(json.dumps({"completed": row["order"] + 1,
                                      "planned": MAX_ATTEMPTS}), flush=True)
                    active = None
                server.assert_running()
                b.validate_server_properties(client.request("/props"), parent.cfg(plan))
                after = preflight(check_headroom=False, require_unused=False)
                require(after["identity"] == fresh["identity"] and
                        after["source_hashes"] == fresh["source_hashes"],
                        "Postflight identity/source changed")
                journal.write("postflight", after)
            status = "PASS"
        except BaseException as exc:
            status = "PARTIAL" if active or inference_seconds else "BLOCKED"
            journal.write("failure", {"type": type(exc).__name__,
                                      "message": str(exc), "request_id": active})
        events = b.read_events(journal.directory)
        attempted, raw, derived = inventory(plan, events)
        if status != "PASS" and len(derived) == MAX_ATTEMPTS:
            status = "COMPLETE_DATA_POSTFLIGHT_FAILED"
        summary = {"status": status, "attempted": len(attempted),
            "responses_received": len(raw), "results": len(derived),
            "inference_wall_seconds":
                sum(value["latency_seconds"] for value in raw.values()) +
                failed_completion_seconds,
            "failed_completion_seconds": failed_completion_seconds,
            "batch_wall_seconds": time.monotonic() - started,
            "run_directory": journal.directory.as_posix(), "retries": 0,
            "hidden_warmups": 0, "human_semantic_ratings": 0,
            "archived_h0_regenerations": 0}
        journal.finish(**summary)
        write_exclusive(journal.directory / "summary.json", summary)
        return summary


def replay():
    plan = load(FROZEN)
    validate_plan(plan)
    folders = list((ROOT / "runs").glob("*"))
    require(len(folders) == 1, "Unexpected repair run count")
    folder = folders[0]
    events = b.read_events(folder)
    claim, authorization = load(ROOT / "claim.json"), load(AUTHORIZATION)
    validate_run_bindings(claim, load(folder / "manifest.json"), plan, authorization)
    attempted, raw, derived = inventory(plan, events)
    require(events and events[-1]["kind"] == "run_finished" and
            load(folder / "summary.json") == events[-1]["data"],
            "Missing or changed terminal run evidence")
    live = [event["data"] for event in events if event["kind"] == "live_prompt_verified"]
    require([item["request_id"] for item in live] ==
            [row["request_id"] for row in plan["requests"][:len(live)]],
            "Live-token verification is not a frozen prefix")
    require(not attempted or len(live) == MAX_ATTEMPTS,
            "Generation began before all live-token checks passed")
    for path, digest in claim["source_hashes"].items():
        snapshot = folder / "source_snapshot" / path
        require(snapshot.is_file() and sha256(snapshot) == digest,
                "Source snapshot changed: " + path)
    sent = [event["data"]["payload"] for event in events
            if event["kind"] == "http_request" and event["data"]["route"] == "/completion"]
    require(sent == [parent.payload(row) for row in plan["requests"][:len(attempted)]],
            "Actual completion payload changed")
    bodies = [json.loads(base64.b64decode(event["data"]["body_base64"]))
              for event in events if event["kind"] == "http_response" and
              event["data"]["route"] == "/completion" and
              event["data"].get("status") == 200]
    require(bodies == [record["response"] for record in raw.values()],
            "Raw HTTP response changed")
    personas = load(PARENT_CASE_BANK)["personas"]
    rows = []
    for row in plan["requests"]:
        request_id = row["request_id"]
        reconstructed = (result(row, personas[row["persona_id"]],
                                raw[request_id]["response"],
                                raw[request_id]["latency_seconds"])
                         if request_id in raw else None)
        if request_id in derived:
            require(reconstructed == derived[request_id], "Derived result changed")
        state = ("COMPLETED" if request_id in derived else
                 "RAW_RECOVERABLE" if request_id in raw else
                 "ATTEMPTED_UNRESOLVED" if request_id in attempted else "UNATTEMPTED")
        rows.append((row, reconstructed, state))
    return folder, events, rows, len(bodies)


def audit():
    plan = load(FROZEN)
    validate_plan(plan)
    folder, events, rows, bodies = replay()
    public = []
    for row, result_row, state in rows:
        public.append({"request_id": row["request_id"],
            "parent_request_id": row["parent_request_id"],
            "request_sha256": row["request_sha256"], "case_id": row["case_id"],
            "condition": row["condition"], "state": state,
            "raw_text_sha256": None if result_row is None else result_row["raw_text_sha256"],
            "first_reply_sha256": None if result_row is None else
                result_row["first_reply_sha256"],
            "generated_tokens": None if result_row is None else
                result_row["generated_tokens"],
            "stop_reason": None if result_row is None else result_row["stop_reason"],
            "latency_seconds": None if result_row is None else
                result_row["latency_seconds"],
            "automatic_score": None if result_row is None else
                result_row["automatic_score"]})
    return {"version":
            "p1_persona_dialogue_independent_replication_declarative_repair_integrity_v1",
        "integrity_status": "PASS", "manifest_sha256": sha256(FROZEN),
        "design_sha256": DESIGN_SHA, "case_transform_sha256": CASE_TRANSFORM_SHA,
        "parent_execution_audit_sha256": PARENT_AUDIT_SHA,
        "parent_integrity_replay": "REQUIRED_FOR_COMBINED_ANALYSIS",
        "run_directory": folder.as_posix(),
        "attempted": sum(state != "UNATTEMPTED" for _, _, state in rows),
        "results": sum(state == "COMPLETED" for _, _, state in rows),
        "http_responses_verified": bodies, "journal_events": len(events),
        "new_h1_rows": public, "archived_h0_reuse_index": archived_index(H0_CONDITIONS),
        "raw_text_embedded": False, "new_generations_during_audit": 0,
        "archived_h0_regenerations": 0}


def _paired_effect(by_unit, unit_ids, metric, persona_by_unit):
    return parent.weighted_contrast(
        by_unit, unit_ids, {"ARCHIVED_RAW": -1.0, "DECLARATIVE": 1.0},
        metric, persona_by_unit)


def _outdated_analysis(by_case, archived_raw, declarative,
                       persona_by_case, regime_by_case):
    """Summarize only the frozen OUTDATED_CONFLICTING C6/C7 slots."""
    conflicting = sorted(case_id for case_id, regime in regime_by_case.items()
                         if regime == "OUTDATED_CONFLICTING")
    require(len(conflicting) == 4, "Outdated-conflicting case allocation changed")
    by_unit, persona_by_unit = {}, {}
    for case_id in conflicting:
        for condition in ("C6", "C7"):
            key = (case_id, condition)
            require(key in archived_raw and key in declarative,
                    "Missing applicable outdated-value repair pair")
            require(archived_raw[key]["outdated_value_applicable"] is True and
                    declarative[key]["outdated_value_applicable"] is True,
                    "Outdated-value applicability changed")
            unit = case_id + "__" + condition
            by_unit[unit] = {"ARCHIVED_RAW": archived_raw[key],
                             "DECLARATIVE": declarative[key]}
            persona_by_unit[unit] = persona_by_case[case_id]
    units = sorted(by_unit)
    return {
        "eligible_slots": len(units),
        "archived_raw_by_condition": {
            condition: parent.binary_summary(
                [archived_raw[(case_id, condition)] for case_id in conflicting],
                "outdated_value_adoption")
            for condition in ("C6", "C7")},
        "declarative_by_condition": {
            condition: parent.binary_summary(
                [declarative[(case_id, condition)] for case_id in conflicting],
                "outdated_value_adoption")
            for condition in ("C6", "C7")},
        "declarative_minus_archived_raw": _paired_effect(
            by_unit, units, "outdated_value_adoption", persona_by_unit),
        "repaired_declarative_C7_minus_C6": parent.weighted_contrast(
            by_case, conflicting, {"C6": -1.0, "C7": 1.0},
            "outdated_value_adoption", persona_by_case),
        "inapplicable_slots_included": 0,
        "inapplicable_or_missing_recoded_as_zero": False,
    }


def analyze():
    design, bank = load(DESIGN), load(PARENT_CASE_BANK)
    plan = load(FROZEN)
    validate_plan(plan)
    require(AUDIT.is_file() and load(AUDIT) == audit(),
            "Frozen execution audit required and must reproduce")
    require(load(PARENT_AUDIT) == parent.audit(),
            "Parent execution audit/event replay changed")
    folder, events, new_rows, _ = replay()
    require(all(state == "COMPLETED" for _, _, state in new_rows),
            "Complete 48-row repair run required")
    _, _, parent_rows, _ = parent.replay()
    parent_h0 = [(row, result_row) for row, result_row, state in parent_rows
                 if row["condition"] in H0_CONDITIONS and state == "COMPLETED"]
    parent_h1 = [(row, result_row) for row, result_row, state in parent_rows
                 if row["condition"] in H1_CONDITIONS and state == "COMPLETED"]
    require(len(parent_h0) == len(parent_h1) == MAX_ATTEMPTS,
            "Parent rows incomplete")
    by_case, persona_by_case, regime_by_case = defaultdict(dict), {}, {}
    by_condition = defaultdict(list)
    for row, result_row in parent_h0:
        score = _augmented_score(result_row)
        by_case[row["case_id"]][row["condition"]] = score
        by_condition[row["condition"]].append(score)
        persona_by_case[row["case_id"]] = row["persona_id"]
        regime_by_case[row["case_id"]] = row["history_regime"]
    new_results = []
    for row, result_row, _ in new_rows:
        score = result_row["automatic_score"]
        by_case[row["case_id"]][row["condition"]] = score
        by_condition[row["condition"]].append(score)
        persona_by_case[row["case_id"]] = row["persona_id"]
        regime_by_case[row["case_id"]] = row["history_regime"]
        new_results.append(result_row)
    all_cases = sorted(by_case)
    require(len(all_cases) == 12 and
            all(set(by_case[case_id]) == {f"C{i}" for i in range(8)}
                for case_id in all_cases), "Repaired factorial cell coverage")
    condition_summary = {}
    for condition in (f"C{i}" for i in range(8)):
        scores = by_condition[condition]
        condition_summary[condition] = {
            metric: parent.binary_summary(scores, metric) for metric in REPAIR_METRICS}
        condition_summary[condition].update({
            "selection_categories": parent._distribution(
                [score["selection_category"] for score in scores]),
            "exact_current_note_support": parent._distribution(
                [score["exact_current_note_support"] for score in scores]),
            "full_canonical_both": parent.binary_summary(scores, "full_canonical_both")})
    weights = design["estimands"]["repaired_factorial_weights"]
    factorial = {effect: {metric: parent.weighted_contrast(
        by_case, all_cases, effect_weights, metric, persona_by_case)
        for metric in PRIMARY_METRICS}
        for effect, effect_weights in weights.items()}
    h_by_regime = {}
    for regime in design["estimands"]["history_regime_strata"]:
        case_ids = [case_id for case_id in all_cases
                    if regime_by_case[case_id] == regime]
        h_by_regime[regime] = {metric: parent.weighted_contrast(
            by_case, case_ids, weights["H_DECLARATIVE"], metric, persona_by_case)
            for metric in PRIMARY_METRICS}
    archived_raw = {(row["case_id"], row["condition"]): _augmented_score(result_row)
                    for row, result_row in parent_h1}
    declarative = {(row["case_id"], row["condition"]): result_row["automatic_score"]
                   for row, result_row, _ in new_rows}
    require(set(archived_raw) == set(declarative), "Repair pair coverage")
    by_unit, persona_by_unit = {}, {}
    for case_id, condition in sorted(declarative):
        unit = case_id + "__" + condition
        by_unit[unit] = {"ARCHIVED_RAW": archived_raw[(case_id, condition)],
                         "DECLARATIVE": declarative[(case_id, condition)]}
        persona_by_unit[unit] = persona_by_case[case_id]
    all_units = sorted(by_unit)
    repair_effects = {metric: _paired_effect(
        by_unit, all_units, metric, persona_by_unit) for metric in REPAIR_METRICS}
    repair_by_condition = {}
    for condition in H1_CONDITIONS:
        units = [unit for unit in all_units if unit.endswith("__" + condition)]
        repair_by_condition[condition] = {metric: _paired_effect(
            by_unit, units, metric, persona_by_unit) for metric in REPAIR_METRICS}
    outdated = _outdated_analysis(
        by_case, archived_raw, declarative, persona_by_case, regime_by_case)
    memory_events = [event["data"] for event in events
                     if event["kind"] == "memory_observation"]
    available = [entry.get("system", {}).get("available_physical")
                 for entry in memory_events]
    available = [value for value in available if value is not None]
    peak = max((entry.get("process", {}).get("peak_working_set", 0)
                for entry in memory_events), default=0)
    latency = sum(item["latency_seconds"] for item in new_results)
    generated = sum(item["generated_tokens"] for item in new_results)
    return {"version":
            "p1_persona_dialogue_independent_replication_declarative_repair_analysis_v1",
        "evidence_level": "OUTPUT_INFORMED_SYNTHETIC_DEVELOPMENT",
        "claim_boundary": design["output_informed_status"]["allowed_claim"],
        "forbidden_claims": design["output_informed_status"]["forbidden_claims"],
        "manifest_sha256": sha256(FROZEN), "execution_audit_sha256": sha256(AUDIT),
        "design_sha256": DESIGN_SHA, "case_transform_sha256": CASE_TRANSFORM_SHA,
        "parent_execution_audit_sha256": PARENT_AUDIT_SHA,
        "run_directory": folder.as_posix(), "new_generations": len(new_results),
        "archived_h0_rows_reused": len(parent_h0), "archived_h0_regenerations": 0,
        "archived_raw_h1_comparators": len(parent_h1),
        "combined_factorial_rows": len(parent_h0) + len(new_results),
        "human_semantic_ratings": 0, "condition_summary": condition_summary,
        "primary_repair_effects_declarative_minus_archived_raw": repair_effects,
        "repair_effects_by_condition": repair_by_condition,
        "outdated_value_adoption": outdated,
        "repaired_factorial_effects": {"status":
            "EXPLORATORY_DESCRIPTIVE_OUTPUT_INFORMED_NOT_CONFIRMATORY",
            "effects": factorial, "H_by_history_regime": h_by_regime},
        "inferential_policy": {"p_values": "NOT_COMPUTED",
            "estimation_first": True, "logical_missing_outcome_bounds": True,
            "missing_recoded_as_zero": False, "confirmatory_population_claim": False},
        "semantic_and_persona_endpoints": "PENDING_GENUINE_BLINDED_HUMAN_REVIEW",
        "resource_observations_new_h1_only": {"generated_tokens": generated,
            "native_stop_reason_distribution": parent._distribution(
                [item["stop_reason"] for item in new_results]),
            "completion_inference_seconds": latency,
            "mean_completion_seconds": latency / len(new_results),
            "server_peak_working_set_bytes": peak,
            "minimum_observed_available_physical_bytes":
                min(available) if available else None},
        "cumulative_authorization_after": {"generations_limit": 1200,
            "generations_used": GENERATION_BASELINE + len(new_results),
            "inference_seconds_limit": 72000,
            "inference_seconds_used": INFERENCE_BASELINE + latency},
        "interpretation_limits": design["interpretation_limits"],
        "raw_text_embedded": False, "new_generations_during_analysis": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=(
        "validate", "materialization-summary", "authorization-requirements",
        "register", "preflight", "run", "audit", "analyze"))
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--preflight", type=Path, default=PREFLIGHT)
    args = parser.parse_args(argv)
    if args.action == "validate":
        value = validate_design()
    elif args.action == "materialization-summary":
        value = {"requests": request_specs(), "new_model_generations": 0,
                 "tokenizer_calls": 0}
    elif args.action == "authorization-requirements":
        value = authorization_requirements()
    elif args.action == "register":
        require(args.authorization is not None, "--authorization is required")
        value = register(args.authorization)
    elif args.action == "preflight":
        require(not PREFLIGHT.exists(), "Preflight evidence exists; do not replace")
        value = preflight_receipt()
        write_exclusive(PREFLIGHT, value)
    elif args.action == "run":
        value = run(args.preflight)
    elif args.action == "audit":
        require(not AUDIT.exists(), "Audit exists; do not replace")
        value = audit()
        write_exclusive(AUDIT, value)
    else:
        require(not ANALYSIS.exists(), "Analysis exists; do not replace")
        value = analyze()
        write_exclusive(ANALYSIS, value)
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
