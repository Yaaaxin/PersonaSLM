"""Run the frozen 42-request persona-dialogue mechanism study once.

The parent design is preserved and its prospective measurement amendment v2 is
effective.  Registration uses the official chat template and native
``llama-tokenize``; execution has no warmup, retry, or hidden completion.
"""

import argparse
import ast
import base64
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import time
import unicodedata

import p1_persona_dialogue_factorial as base


s = base.s
b = base.b
load, save, sha256, th, require = s.load, s.save, s.sha256, s.th, s.require

DESIGN = Path("docs/validation/p1/persona_dialogue_mechanism_v1/prospective_design_v1.json")
AMENDMENT = DESIGN.with_name("prospective_measurement_amendment_v2.json")
PARSER_CLARIFICATION = DESIGN.with_name("prospective_parser_clarification_v3.json")
OUT = DESIGN.parent
INTEGRITY_AMENDMENT = OUT / "preexecution_integrity_amendment_v4.json"
FROZEN_V1 = OUT / "frozen_manifest_v1.json"
AUTH_V1 = OUT / "researcher_authorization_v1.json"
FROZEN = OUT / "frozen_manifest_v2.json"
AUTH = OUT / "researcher_authorization_v2.json"
ROOT = Path("results/p1_persona_dialogue_mechanism/adaptive_validation_v1")
DEVELOPMENT_ANALYSIS = Path("docs/validation/p1/persona_dialogue_factorial_v1/analysis_v1.json")
DEVELOPMENT_AUDIT = Path("docs/validation/p1/persona_dialogue_factorial_v1/execution_audit_v1.json")
TEST_FILE = Path("tests/test_p1_persona_dialogue_mechanism.py")

DESIGN_SHA = "694b6e970ae16c4e2284d83aa385b10b78db42d7c1ec3befdbd07ec2f9aec316"
AMENDMENT_SHA = "67bd13f3a54a59e4aa04a99eabbc10b92ed362437f4aad4172aed7219d7e8eb4"
PARSER_CLARIFICATION_SHA = "ab100aee5d50e38d332770af4299103b0544a0b881a9c4bad8610520402dfb76"
INTEGRITY_AMENDMENT_SHA = "f305a4c01fc4f582d5ca35713684dd06ba3beaaff2ad36a2e752184fab96cf15"
FROZEN_V1_SHA = "c3bc7adf1c65fe5700a44ae6de6aa90f28cc787a8a5035250d5e39fbbfc68b92"
AUTH_V1_SHA = "328f63db6fabf3787374bb4e22b77f2f0b19a63d4e5b3149092f69a15fbcf144"
CASE_BANK_SHA = "8e6956c4e909bff06a7a5623593493ff84521da680c2f1703110579fb522c6d0"
POST_CANDIDATE2_SHA = "1489732ce936860d46fa0001bf1edc2328b65c3f7b5cde386563644558fbba65"
TOKENIZER_SHA = "e05dbdef761e577b3d56f3daea7b205a07f68e5d87242ea4e2544382ffdd358e"
BUDGET_FROZEN_SHA = "510e46b214dda23dea2a3e5462d44982d25b7a9db022626a7a5a1ba504d5e039"
MAX_ATTEMPTS = 42
GENERATION_BASELINE = 64
INFERENCE_BASELINE = 416.1450323000072
PRIMARY_METRICS = (
    "current_named_selection",
    "current_preference_choice",
    "history_target_selection",
    "full_canonical_both",
)
ARMS = {
    "H_ONLY", "S_H", "S_F_NO_H", "F_H_RAW", "S_F_H",
    "F_H_STRUCTURE", "F_H_REFRESH",
}


def case_bank_path(design):
    return Path(design["bindings"]["validation_case_bank"]["path"])


def source_hashes():
    design = load(DESIGN)
    paths = list(Path("src/personaslm").glob("*.py")) + [
        Path(__file__), TEST_FILE, DESIGN, AMENDMENT, PARSER_CLARIFICATION,
        INTEGRITY_AMENDMENT,
        case_bank_path(design),
        Path(design["bindings"]["post_candidate2_state"]["path"]),
        Path(b.FROZEN),
        DEVELOPMENT_ANALYSIS, DEVELOPMENT_AUDIT,
        Path("tools/p1_persona_dialogue_factorial.py"),
        Path("tools/p1d_instruct_smoke.py"),
        Path("tools/p1d_budget_calibration.py"),
        Path("tools/p1d_format_calibration.py"),
        Path("tools/p1d_instruct_template_check.py"),
    ]
    root = Path.cwd().resolve()
    return {p.resolve().relative_to(root).as_posix(): sha256(p) for p in paths}


def cfg(plan):
    return s.Runtime(plan["model"]["model_file"], plan["model"]["model_sha256"],
                     plan["model"]["backend_file"], model_label=plan["model"]["model_label"])


def source_maps(design, bank):
    personas = bank["personas"]
    cases = {case["case_id"]: case for case in bank["cases"]}
    mechanism = {case["case_id"]: case for case in design["cases"]}
    return personas, cases, mechanism


def validate_integrity_amendment():
    require(sha256(INTEGRITY_AMENDMENT) == INTEGRITY_AMENDMENT_SHA,
            "Integrity amendment changed")
    amendment = load(INTEGRITY_AMENDMENT)
    require(amendment["status"] == "FROZEN_AFTER_REGISTRATION_BEFORE_PREFLIGHT_OR_MODEL_OUTPUT",
            "Integrity amendment status")
    parent = amendment["parent_registration"]
    require(parent["manifest_path"] == FROZEN_V1.as_posix() and
            parent["manifest_sha256"] == FROZEN_V1_SHA, "Integrity parent manifest")
    require(parent["authorization_path"] == AUTH_V1.as_posix() and
            parent["authorization_sha256"] == AUTH_V1_SHA, "Integrity parent authorization")
    require(parent["registered_requests"] == MAX_ATTEMPTS and
            parent["native_tokenizer_calls"] == MAX_ATTEMPTS and
            parent["generation_requests"] == 0, "Integrity parent counts")
    state = amendment["preexecution_state"]
    require(state["execution_claim_exists"] is False and state["run_directories"] == 0 and
            state["model_generation_attempts"] == state["model_generations"] == 0 and
            state["validation_outputs_inspected"] == 0, "Integrity amendment not pre-output")
    return amendment


def construction(design, bank, mechanism_case, arm_name):
    """Construct one prompt while retaining byte-identical source material."""
    arm = design["arms"][arm_name]
    personas, source_cases, _ = source_maps(design, bank)
    source_case = source_cases[mechanism_case["case_id"]]
    persona = personas[mechanism_case["source_persona_id"]]
    system = (bank["prompt_policy"]["fixed_system_instruction"] + "\n"
              + "Speaker: " + persona["speaker_name"] + ".\n"
              + source_case["fixed_current_notes"])
    if arm["S"]:
        system += "\n" + persona["S_block"]
    if arm["F"]:
        system += "\n" + persona["F_block"]
    if arm["transform"] == "APPEND_GENERIC_STRUCTURE_INSTRUCTION_TO_SYSTEM_AFTER_F_BLOCK":
        system += "\n" + design["prompt_policy"]["generic_structure_instruction"]
    messages = [{"role": "system", "content": system}]
    if arm["H"]:
        messages.extend(source_case["history_messages"])
    current_user = source_case["fixed_current_user"]
    if arm["transform"] == "PREPEND_NAMES_ONLY_REFRESH_TO_FINAL_USER_AFTER_HISTORY":
        current_user = design["prompt_policy"]["names_only_refresh_template"].format(
            A_CANONICAL=source_case["options"]["A"]["canonical"],
            B_CANONICAL=source_case["options"]["B"]["canonical"],
            FIXED_CURRENT_USER=current_user,
        )
    messages.append({"role": "user", "content": current_user})
    factors = {key: arm[key] for key in ("S", "F", "H")}
    return factors, arm["transform"], messages


def validate_design(design, amendment=None, bank=None, clarification=None):
    amendment = amendment or load(AMENDMENT)
    clarification = clarification or load(PARSER_CLARIFICATION)
    require(sha256(DESIGN) == DESIGN_SHA, "Parent design changed")
    require(sha256(AMENDMENT) == AMENDMENT_SHA, "Measurement amendment changed")
    require(sha256(PARSER_CLARIFICATION) == PARSER_CLARIFICATION_SHA,
            "Parser clarification changed")
    require(amendment["status"] == "FROZEN_PROSPECTIVE_BEFORE_REGISTRATION_OR_MODEL_OUTPUT",
            "Amendment status")
    require(amendment["parent_design"]["path"] == DESIGN.as_posix(), "Amendment parent path")
    require(amendment["parent_design"]["sha256"] == DESIGN_SHA, "Amendment parent hash")
    require(amendment["preoutput_state"]["model_generations"] == 0, "Amendment not pre-output")
    require(clarification["status"] == "FROZEN_PROSPECTIVE_BEFORE_REGISTRATION_OR_MODEL_OUTPUT",
            "Parser clarification status")
    require(clarification["parents"]["design_path"] == DESIGN.as_posix() and
            clarification["parents"]["measurement_amendment_path"] == AMENDMENT.as_posix(),
            "Parser clarification parent paths")
    require(clarification["parents"]["design_sha256"] == DESIGN_SHA and
            clarification["parents"]["measurement_amendment_sha256"] == AMENDMENT_SHA,
            "Parser clarification parents")
    require(clarification["preoutput_state"]["model_generations"] == 0,
            "Parser clarification not pre-output")
    require(design["status"] == "FROZEN_PROSPECTIVE_NOT_EXECUTED", "Design status")
    require(subprocess.check_output(["git", "branch", "--show-current"], text=True).strip() ==
            design["bindings"]["source_branch"], "Source branch changed")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() ==
            design["bindings"]["source_head"], "Source HEAD changed")
    require(Path(b.FROZEN).as_posix() ==
            "docs/validation/p1d/budget_calibration_v1/frozen_manifest_v2.json",
            "Tokenizer-identity manifest path changed")
    require(sha256(Path(b.FROZEN)) == BUDGET_FROZEN_SHA,
            "Tokenizer-identity manifest changed")
    require(design["authorization"]["maximum_attempts"] == MAX_ATTEMPTS, "Allocation")
    require(design["authorization"]["retries"] == 0, "Retry policy")
    require(design["authorization"]["hidden_warmups"] == 0, "Warmup policy")
    require(set(design["arms"]) == ARMS, "Arm set")
    require(design["resource_budget"]["requests"] == MAX_ATTEMPTS, "Request budget")
    baseline = design["resource_budget"]["global_baseline"]
    require(baseline["generations_used"] == GENERATION_BASELINE, "Generation baseline")
    require(baseline["inference_wall_seconds_used"] == INFERENCE_BASELINE, "Time baseline")
    runtime = design["runtime"]
    fixed_runtime = {"threads": 4, "threads_batch": 4, "context_tokens": 4096,
                     "gpu_layers": 0, "max_new_tokens": 96, "temperature": 0.0,
                     "top_p": 1.0, "seed": 42, "cache_prompt": False,
                     "warmup": False, "ignore_eos": False, "parallel": 1,
                     "no_context_shift": True}
    for key, value in fixed_runtime.items():
        require(runtime[key] == value, "Runtime changed: " + key)
    binding = design["bindings"]["validation_case_bank"]
    require(binding["sha256"] == CASE_BANK_SHA, "Case-bank binding")
    require(sha256(case_bank_path(design)) == CASE_BANK_SHA, "Case bank changed")
    state_binding = design["bindings"]["post_candidate2_state"]
    require(state_binding["sha256"] == POST_CANDIDATE2_SHA, "Candidate-2 state binding")
    require(sha256(Path(state_binding["path"])) == POST_CANDIDATE2_SHA,
            "Candidate-2 state changed")
    bank = bank or load(case_bank_path(design))
    personas, source_cases, mechanism_cases = source_maps(design, bank)
    require(len(mechanism_cases) == len(design["cases"]) == 6, "Case set")
    require(set(binding["source_case_ids"]) == set(mechanism_cases), "Source case IDs")
    for case_id, case in mechanism_cases.items():
        source = source_cases[case_id]
        require(case["source_persona_id"] == source["persona_id"] in personas, "Persona binding")
        require(case["history_regime"] == source["history_regime"], "Regime binding")
        require(case["preferred_option"] == source["preferred_option"], "Preference binding")
        require(case["current_canonical"] == {k: source["options"][k]["canonical"] for k in ("A", "B")},
                "Canonical binding")
        require(case["history_selected_target"] in case["history_target_strings"], "History target")
    rows = design["order"]["requests"]
    require(len(rows) == len({r["request_id"] for r in rows}) == MAX_ATTEMPTS, "Order size")
    require([r["order"] for r in rows] == list(range(MAX_ATTEMPTS)), "Order indices")
    expected = []
    seed = design["order"]["seed"]
    for case_id in mechanism_cases:
        for arm in ARMS:
            rid = "pdlg_mech_v1_" + case_id.lower() + "_" + arm.lower()
            expected.append((th(str(seed) + "|" + rid), rid, case_id, arm))
    expected.sort()
    observed = [(r["request_id"], r["case_id"], r["arm"]) for r in rows]
    require(observed == [(rid, cid, arm) for _, rid, cid, arm in expected], "Frozen order")
    require(set(amendment["effective_primary_measurement"]["primary_endpoints"]) == set(PRIMARY_METRICS),
            "Effective primary endpoints")
    return {"cases": 6, "arms": 7, "requests": MAX_ATTEMPTS,
            "history_regimes": dict(Counter(c["history_regime"] for c in design["cases"]))}


def request_set_sha256(rows):
    return th(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def validate_source_binding(plan):
    require(plan["registration_source_hashes"] == source_hashes(), "Registered source changed")
    return True


def validate_plan(plan, allow_v1=False):
    expected = ("p1_persona_dialogue_mechanism_manifest_v1" if allow_v1 else
                "p1_persona_dialogue_mechanism_manifest_v2")
    require(plan["version"] == expected, "Manifest version")
    if not allow_v1:
        validate_integrity_amendment()
        require(sha256(FROZEN_V1) == FROZEN_V1_SHA and sha256(AUTH_V1) == AUTH_V1_SHA,
                "Parent registration changed")
        parent = plan["parent_registration"]
        require(parent == {"manifest_path": FROZEN_V1.as_posix(),
                           "manifest_sha256": FROZEN_V1_SHA,
                           "authorization_path": AUTH_V1.as_posix(),
                           "authorization_sha256": AUTH_V1_SHA}, "V2 parent registration")
        repair = plan["preexecution_integrity_amendment"]
        require(repair["path"] == INTEGRITY_AMENDMENT.as_posix() and
                repair["sha256"] == INTEGRITY_AMENDMENT_SHA and
                repair["retokenizer_calls"] == repair["generation_requests"] == 0,
                "V2 integrity repair")
        v1 = load(FROZEN_V1)
        require(plan["requests"] == v1["requests"] and
                repair["requests_sha256"] == request_set_sha256(v1["requests"]),
                "V2 requests differ from registered V1")
    require(plan["design_sha256"] == sha256(DESIGN) == DESIGN_SHA, "Design changed")
    require(plan["measurement_amendment_sha256"] == sha256(AMENDMENT) == AMENDMENT_SHA,
            "Measurement amendment changed")
    require(plan["parser_clarification_sha256"] ==
            sha256(PARSER_CLARIFICATION) == PARSER_CLARIFICATION_SHA,
            "Parser clarification changed")
    design, amendment = load(DESIGN), load(AMENDMENT)
    bank = load(case_bank_path(design))
    checks = validate_design(design, amendment, bank)
    require(plan["case_bank_sha256"] == sha256(case_bank_path(design)) == CASE_BANK_SHA,
            "Case bank changed")
    validate_source_binding(plan)
    require(plan["template_sha256"] == sha256(Path(plan["template_path"])), "Template changed")
    rows = plan["requests"]
    require(len(rows) == len({r["request_id"] for r in rows}) == MAX_ATTEMPTS, "Rows")
    mechanism_cases = {c["case_id"]: c for c in design["cases"]}
    source_cases = {c["case_id"]: c for c in bank["cases"]}
    template = Path(plan["template_path"]).read_text(encoding="utf-8")
    for index, row in enumerate(rows):
        require(row["order"] == index, "Row order")
        case = mechanism_cases[row["case_id"]]
        source = source_cases[row["case_id"]]
        factors, transform, messages = construction(design, bank, case, row["arm"])
        require(row["factors"] == factors and row["transform"] == transform, "Arm changed")
        require(row["messages"] == messages, "Prompt messages changed")
        require(row["prompt"] == s.render(template, messages), "Rendered prompt changed")
        require(row["prompt_sha256"] == th(row["prompt"]), "Prompt hash")
        require(row["input_token_ids_sha256"] == th(str(row["input_token_ids"])), "Token hash")
        require(len(row["input_token_ids"]) == row["input_tokens"], "Token count")
        require(row["input_tokens"] + row["max_new_tokens"] <= plan["runtime"]["context_tokens"],
                "Context overflow")
        require(row["current_notes_sha256"] == th(source["fixed_current_notes"]), "Notes changed")
        require(row["source_current_user_sha256"] == th(source["fixed_current_user"]), "User changed")
        unhashed = {k: v for k, v in row.items() if k != "request_sha256"}
        require(row["request_sha256"] == th(json.dumps(unhashed, sort_keys=True, separators=(",", ":"))),
                "Request hash")
    for case_id in mechanism_cases:
        group = [r for r in rows if r["case_id"] == case_id]
        require(len(group) == 7 and {r["arm"] for r in group} == ARMS, "Arm coverage")
        require(len({r["current_notes_sha256"] for r in group}) == 1, "Notes invariant")
        require(len({r["source_current_user_sha256"] for r in group}) == 1, "User invariant")
    return {**checks, "input_token_range": [min(r["input_tokens"] for r in rows),
                                               max(r["input_tokens"] for r in rows)]}


def register():
    require(not FROZEN_V1.exists() and not AUTH_V1.exists() and
            not FROZEN.exists() and not AUTH.exists(), "Registration exists; do not replace")
    require(not (OUT / "native_tokenizer").exists(), "Tokenizer evidence exists; do not replace")
    require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
            "Execution allocation already exists")
    design, amendment = load(DESIGN), load(AMENDMENT)
    bank = load(case_bank_path(design))
    checks = validate_design(design, amendment, bank)
    analysis, audit = load(DEVELOPMENT_ANALYSIS), load(DEVELOPMENT_AUDIT)
    require(analysis["generations"] == 48, "Development generation count")
    require(analysis["cumulative_authorization_after"]["generations_used"] == GENERATION_BASELINE,
            "Development generation baseline")
    require(analysis["cumulative_authorization_after"]["inference_seconds_used"] == INFERENCE_BASELINE,
            "Development time baseline")
    require(audit["integrity_status"] == "PASS" and audit["attempted"] == audit["results"] == 48,
            "Development integrity")
    runtime, model = design["runtime"], design["model"]
    require(sha256(Path(model["artifact_path"])) == model["artifact_sha256"], "Model changed")
    require(sha256(Path(runtime["backend_path"])) == runtime["backend_sha256"], "Backend changed")
    require(sha256(Path(runtime["chat_template_path"])) == runtime["chat_template_sha256"],
            "Template changed")
    memory = s.memory_observation(os.getpid())
    require(memory.get("system", {}).get("available_physical", 0) >=
            design["resource_budget"]["minimum_available_physical_ram_bytes"], "Less than 3 GiB RAM")
    tokenizer = Path(runtime["backend_path"]).with_name("llama-tokenize.exe")
    native = load(b.FROZEN)["native_tokenizer_identity"]
    require(native["tokenizer_sha256"] == TOKENIZER_SHA, "Frozen tokenizer identity changed")
    require(sha256(tokenizer) == TOKENIZER_SHA, "Tokenizer changed")
    directory = tokenizer.parent
    require({p.name: sha256(p) for p in directory.glob("*.dll")} == native["dll_hashes"],
            "Backend DLL set changed")
    template = Path(runtime["chat_template_path"]).read_text(encoding="utf-8")
    mechanism_cases = {c["case_id"]: c for c in design["cases"]}
    source_cases = {c["case_id"]: c for c in bank["cases"]}
    rows, pending_logs = [], []
    for item in design["order"]["requests"]:
        mechanism_case = mechanism_cases[item["case_id"]]
        source_case = source_cases[item["case_id"]]
        factors, transform, messages = construction(design, bank, mechanism_case, item["arm"])
        prompt = s.render(template, messages)
        argv = [str(tokenizer.resolve()), "-m", str(Path(model["artifact_path"]).resolve()),
                "--stdin", "--ids", "--offline"]
        started = b.utc_now()
        completed = subprocess.run(
            argv, input=prompt.encode("utf-8"), capture_output=True, timeout=90,
            env={k: v for k, v in os.environ.items() if not k.upper().startswith("LLAMA_ARG_")},
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        require(completed.returncode == 0, "Native tokenizer failed")
        token_ids = ast.literal_eval(completed.stdout.decode("utf-8", "replace").strip())
        require(isinstance(token_ids, list) and token_ids and
                all(type(value) is int and value >= 0 for value in token_ids), "Token IDs")
        pending_logs.append({"started_utc": started, "finished_utc": b.utc_now(), "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout.decode("utf-8", "replace"),
            "stderr": completed.stderr.decode("utf-8", "replace"),
            "prompt_sha256": th(prompt), "generation_requests": 0})
        row = {**item, "persona_id": mechanism_case["source_persona_id"],
            "history_regime": mechanism_case["history_regime"], "factors": factors,
            "transform": transform, "messages": messages, "prompt": prompt,
            "prompt_sha256": th(prompt), "input_token_ids": token_ids,
            "input_tokens": len(token_ids), "input_token_ids_sha256": th(str(token_ids)),
            "preferred_option": source_case["preferred_option"],
            "history_favored_option": source_case["history_favored_option"],
            "options": source_case["options"],
            "history_target_strings": mechanism_case["history_target_strings"],
            "history_selected_target": mechanism_case["history_selected_target"],
            "metric_applicability": source_case["metric_applicability"],
            "current_notes_sha256": th(source_case["fixed_current_notes"]),
            "source_current_user_sha256": th(source_case["fixed_current_user"]),
            "effective_current_user_sha256": th(messages[-1]["content"]),
            "max_new_tokens": 96, "seed": 42, "temperature": 0.0, "top_p": 1.0,
            "stop": [], "cache_prompt": False, "ignore_eos": False}
        require(row["input_tokens"] + 96 <= runtime["context_tokens"], "Context overflow")
        row["request_sha256"] = th(json.dumps(row, sort_keys=True, separators=(",", ":")))
        rows.append(row)
    log_records = []
    for index, log in enumerate(pending_logs):
        path = OUT / "native_tokenizer" / f"{index:04d}.json"
        require(not path.exists(), "Tokenizer log exists")
        save(path, log)
        log_records.append({"path": path.as_posix(), "sha256": sha256(path)})
    frozen_model = {"model_label": model["label"], "model_file": model["artifact_path"],
        "model_sha256": model["artifact_sha256"], "backend_file": runtime["backend_path"],
        "backend_sha256": runtime["backend_sha256"], "quantization": model["quantization"],
        "artifact_revision": model["artifact_revision"],
        "intended_upstream_revision": model["intended_upstream_revision"],
        "conversion_lineage": model["conversion_lineage"]}
    plan = {"version": "p1_persona_dialogue_mechanism_manifest_v1",
        "classification": design["research"], "design_path": DESIGN.as_posix(),
        "design_sha256": sha256(DESIGN), "measurement_amendment_path": AMENDMENT.as_posix(),
        "measurement_amendment_sha256": sha256(AMENDMENT),
        "parser_clarification_path": PARSER_CLARIFICATION.as_posix(),
        "parser_clarification_sha256": sha256(PARSER_CLARIFICATION),
        "case_bank_path": case_bank_path(design).as_posix(), "case_bank_sha256": CASE_BANK_SHA,
        "development_analysis_sha256": sha256(DEVELOPMENT_ANALYSIS),
        "development_audit_sha256": sha256(DEVELOPMENT_AUDIT), "model": frozen_model,
        "template_path": runtime["chat_template_path"],
        "template_sha256": runtime["chat_template_sha256"], "runtime": runtime,
        "resource_budget": design["resource_budget"], "requests": rows,
        "native_tokenizer_identity": {"path": tokenizer.as_posix(),
            "tokenizer_sha256": native["tokenizer_sha256"], "dll_hashes": native["dll_hashes"]},
        "native_tokenizer_logs": log_records, "registration_source_hashes": source_hashes(),
        "registered_utc": b.utc_now(), "new_model_generations": 0}
    save(FROZEN_V1, plan)
    manifest_sha = sha256(FROZEN_V1)
    save(AUTH_V1, {"version": "p1_persona_dialogue_mechanism_authorization_v1",
        "researcher": "Yaxin ZHENG", "decision": "AUTHORIZED",
        "decision_source": design["authorization"]["basis"], "registered_utc": b.utc_now(),
        "manifest_sha256": manifest_sha, "design_sha256": DESIGN_SHA,
        "measurement_amendment_sha256": AMENDMENT_SHA, "case_bank_sha256": CASE_BANK_SHA,
        "parser_clarification_sha256": PARSER_CLARIFICATION_SHA,
        "maximum_attempts": MAX_ATTEMPTS, "retries": 0,
        "scope": design["authorization"]["scope"],
        "prohibitions": design["authorization"]["prohibitions"]})
    validate_plan(plan, allow_v1=True)
    return {"status": "REGISTERED", "manifest_sha256": manifest_sha,
        "design_sha256": DESIGN_SHA, "measurement_amendment_sha256": AMENDMENT_SHA,
        "parser_clarification_sha256": PARSER_CLARIFICATION_SHA,
        "tokenizer_calls": MAX_ATTEMPTS, "generation_requests": 0, **checks,
        "input_token_range": [min(r["input_tokens"] for r in rows),
                              max(r["input_tokens"] for r in rows)]}


def build_amended_plan(v1, amended_utc):
    """Copy V1 exactly, changing only source-integrity metadata outside requests."""
    requests_sha = request_set_sha256(v1["requests"])
    plan = json.loads(json.dumps(v1))
    plan["version"] = "p1_persona_dialogue_mechanism_manifest_v2"
    plan["parent_registration"] = {"manifest_path": FROZEN_V1.as_posix(),
        "manifest_sha256": FROZEN_V1_SHA, "authorization_path": AUTH_V1.as_posix(),
        "authorization_sha256": AUTH_V1_SHA}
    plan["preexecution_integrity_amendment"] = {
        "status": "SOURCE_ONLY_REPAIR_BEFORE_PREFLIGHT_OR_MODEL_OUTPUT",
        "path": INTEGRITY_AMENDMENT.as_posix(), "sha256": INTEGRITY_AMENDMENT_SHA,
        "requests_sha256": requests_sha, "request_objects_changed": False,
        "prompt_or_token_ids_changed": False, "scientific_inputs_changed": False,
        "retokenizer_calls": 0, "generation_requests": 0}
    plan["registration_source_hashes"] = source_hashes()
    plan["amended_utc"] = amended_utc
    require(plan["requests"] == v1["requests"] and
            request_set_sha256(plan["requests"]) == requests_sha, "Request bytes changed")
    return plan


def amend():
    """Freeze the v4 source-only integrity repair without re-tokenizing."""
    validate_integrity_amendment()
    require(sha256(FROZEN_V1) == FROZEN_V1_SHA, "Registered V1 manifest changed")
    require(sha256(AUTH_V1) == AUTH_V1_SHA, "Registered V1 authorization changed")
    require(not FROZEN.exists() and not AUTH.exists(), "V2 amendment exists; do not replace")
    require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
            "Execution evidence exists; amendment prohibited")
    v1, auth_v1 = load(FROZEN_V1), load(AUTH_V1)
    require(v1["version"] == "p1_persona_dialogue_mechanism_manifest_v1" and
            v1["new_model_generations"] == 0, "Registered V1 state")
    require(len(v1["requests"]) == len({row["request_id"] for row in v1["requests"]}) ==
            MAX_ATTEMPTS, "Registered V1 rows")
    require(auth_v1["version"] == "p1_persona_dialogue_mechanism_authorization_v1" and
            auth_v1["decision"] == "AUTHORIZED" and
            auth_v1["manifest_sha256"] == FROZEN_V1_SHA and
            auth_v1["maximum_attempts"] == MAX_ATTEMPTS and auth_v1["retries"] == 0,
            "Registered V1 authorization")
    require(len(v1["native_tokenizer_logs"]) == MAX_ATTEMPTS, "Registered tokenizer logs")
    for record in v1["native_tokenizer_logs"]:
        require(sha256(Path(record["path"])) == record["sha256"], "V1 tokenizer log changed")
    plan = build_amended_plan(v1, b.utc_now())
    save(FROZEN, plan)
    manifest_sha = sha256(FROZEN)
    auth = json.loads(json.dumps(auth_v1))
    auth.update({"version": "p1_persona_dialogue_mechanism_authorization_v2",
        "manifest_sha256": manifest_sha, "amended_utc": b.utc_now(),
        "parent_manifest_path": FROZEN_V1.as_posix(),
        "parent_manifest_sha256": FROZEN_V1_SHA,
        "parent_authorization_path": AUTH_V1.as_posix(),
        "parent_authorization_sha256": AUTH_V1_SHA,
        "preexecution_integrity_amendment_path": INTEGRITY_AMENDMENT.as_posix(),
        "preexecution_integrity_amendment_sha256": INTEGRITY_AMENDMENT_SHA,
        "amendment_scope": "Source-only replay/analysis integrity repair; 42 requests, prompts, native token IDs, order, model, generation settings, allocation, parser and endpoints unchanged.",
        "retokenizer_calls": 0, "generation_requests_before_amendment": 0})
    save(AUTH, auth)
    validate_plan(load(FROZEN))
    require(load(AUTH)["manifest_sha256"] == manifest_sha, "V2 authorization binding")
    return {"status": "AMENDED_BEFORE_PREFLIGHT_OR_OUTPUT", "manifest_sha256": manifest_sha,
        "authorization_sha256": sha256(AUTH), "parent_manifest_sha256": FROZEN_V1_SHA,
        "parent_authorization_sha256": AUTH_V1_SHA,
        "integrity_amendment_sha256": INTEGRITY_AMENDMENT_SHA,
        "requests": MAX_ATTEMPTS, "request_objects_changed": 0,
        "retokenizer_calls": 0, "generation_requests": 0}


def preflight(check_headroom=True, require_unused=True):
    plan, auth = load(FROZEN), load(AUTH)
    require(auth["version"] == "p1_persona_dialogue_mechanism_authorization_v2" and
            auth["decision"] == "AUTHORIZED" and auth["maximum_attempts"] == MAX_ATTEMPTS,
            "Authorization")
    require(auth["manifest_sha256"] == sha256(FROZEN), "Manifest/auth binding")
    require(auth["design_sha256"] == DESIGN_SHA and
            auth["measurement_amendment_sha256"] == AMENDMENT_SHA, "Design/auth binding")
    require(auth["parser_clarification_sha256"] == PARSER_CLARIFICATION_SHA,
            "Parser-clarification/auth binding")
    require(auth["parent_manifest_sha256"] == FROZEN_V1_SHA and
            auth["parent_authorization_sha256"] == AUTH_V1_SHA and
            auth["preexecution_integrity_amendment_sha256"] == INTEGRITY_AMENDMENT_SHA and
            auth["retokenizer_calls"] == auth["generation_requests_before_amendment"] == 0,
            "Integrity-amendment/auth binding")
    checks = validate_plan(plan)
    config = cfg(plan)
    identity = b.file_preflight(config)
    require(identity["status"] == "PASS", "File preflight")
    require(identity["model"]["sha256"] == plan["model"]["model_sha256"], "Model identity")
    require(identity["server"]["sha256"] == plan["model"]["backend_sha256"], "Backend identity")
    native = plan["native_tokenizer_identity"]
    tokenizer = Path(native["path"])
    require(native["tokenizer_sha256"] == TOKENIZER_SHA and sha256(tokenizer) == TOKENIZER_SHA,
            "Tokenizer identity")
    require({p.name: sha256(p) for p in tokenizer.parent.glob("*.dll")} == native["dll_hashes"],
            "DLL identity")
    for record in plan["native_tokenizer_logs"]:
        require(sha256(Path(record["path"])) == record["sha256"], "Tokenizer log changed")
    analysis, audit = load(DEVELOPMENT_ANALYSIS), load(DEVELOPMENT_AUDIT)
    baseline = analysis["cumulative_authorization_after"]
    require(audit["integrity_status"] == "PASS" and audit["attempted"] == audit["results"] == 48,
            "Development audit")
    require(baseline["generations_used"] == GENERATION_BASELINE and
            baseline["inference_seconds_used"] == INFERENCE_BASELINE, "Cumulative baseline changed")
    require(baseline["generations_limit"] - GENERATION_BASELINE >= MAX_ATTEMPTS,
            "Generation ceiling")
    require(baseline["inference_seconds_limit"] - INFERENCE_BASELINE >=
            plan["resource_budget"]["batch_wall_seconds_ceiling"], "Inference ceiling")
    if require_unused:
        require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
                "Existing allocation: no repeat")
    memory = s.memory_observation(os.getpid())
    if check_headroom:
        require(memory.get("system", {}).get("available_physical", 0) >=
                plan["resource_budget"]["minimum_available_physical_ram_bytes"], "Less than 3 GiB RAM")
    require(shutil.disk_usage(".").free >= plan["resource_budget"]["minimum_free_output_disk_bytes"],
            "Output disk reserve")
    return {"status": "PASS", "checked_utc": b.utc_now(), "checks": checks,
        "identity": identity, "manifest_sha256": sha256(FROZEN),
        "authorization_sha256": sha256(AUTH), "design_sha256": DESIGN_SHA,
        "measurement_amendment_sha256": AMENDMENT_SHA,
        "parser_clarification_sha256": PARSER_CLARIFICATION_SHA,
        "integrity_amendment_sha256": INTEGRITY_AMENDMENT_SHA,
        "source_hashes": source_hashes(),
        "configuration": config.as_dict(), "server_command": s.command(plan),
        "memory_before_run": memory, "cumulative_baseline": baseline,
        "live_gate": "All 42 parse_special=true token arrays must match before any completion."}


def payload(row):
    return {"prompt": row["input_token_ids"], "n_predict": row["max_new_tokens"],
        "temperature": row["temperature"], "top_p": row["top_p"], "seed": row["seed"],
        "cache_prompt": False, "stop": [], "ignore_eos": False,
        "return_tokens": True, "stream": False}


def norm(text):
    value = unicodedata.normalize("NFKC", text).casefold()
    value = value.replace("—", "-").replace("–", "-").replace("―", "-").replace("−", "-")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"[^\S\n]+", " ", value)


def flat_norm(text):
    return " ".join(norm(text).split())


def exact_pattern(target):
    return r"(?<!\w)" + re.escape(flat_norm(target)) + r"(?!\w)"


def has_exact(text, target):
    return re.search(exact_pattern(target), flat_norm(text)) is not None


def first_two_spans(text):
    normalized = norm(text)
    spans = [" ".join(piece.split()) for piece in re.split(r"[.!?\n]+", normalized) if piece.strip()]
    return spans[:2]


def anchored_selection(row, text):
    """Apply only amendment-v2 exact, anchored selection constructions."""
    targets = ([row["options"][key]["canonical"] for key in ("A", "B")] +
               list(row["history_target_strings"]))
    normalized_targets = sorted({flat_norm(target): target for target in targets}.items(),
                                key=lambda item: (-len(item[0]), item[0]))
    literal_lookup = dict(normalized_targets)
    alternation = "|".join(r"(?<!\w)" + re.escape(value) + r"(?!\w)"
                           for value, _ in normalized_targets)
    subject = r"(?:i|we)\s+(?:(?:would|will|can|should)\s+)?"
    clause_start = r"(?:^|(?<=;))\s*"
    verbs = r"(?:recommend|choose|select|pick|book|reserve|use|visit|take)\b"
    alternatives = r"(?:go\s+with|opt\s+for)\b"
    optional_lead = r"\s*(?::|-)?\s*(?:the\s+)?"
    patterns = [
        re.compile(clause_start + subject + verbs + optional_lead +
                   r"(?P<target>" + alternation + r")"),
        re.compile(clause_start + subject + alternatives + optional_lead +
                   r"(?P<target>" + alternation + r")"),
        re.compile(clause_start + verbs + optional_lead +
                   r"(?P<target>" + alternation + r")"),
        re.compile(clause_start + alternatives + optional_lead +
                   r"(?P<target>" + alternation + r")"),
        re.compile(clause_start + r"(?:my|our)\s+(?:pick|choice|recommendation)\s*(?:is|:)" +
                   r"\s*(?:the\s+)?(?P<target>" + alternation + r")"),
        re.compile(clause_start + r"(?P<target>" + alternation +
                   r")\s+(?:is|would\s+be)\s+" +
                   r"(?:my|our)\s+(?:pick|choice|recommendation)"),
    ]
    events = []
    spans = first_two_spans(text)
    canonical_lookup = {flat_norm(row["options"][key]["canonical"]): "CURRENT_" + key
                        for key in ("A", "B")}
    for span_index, span in enumerate(spans):
        for pattern_index, pattern in enumerate(patterns):
            for match in pattern.finditer(span):
                target_normalized = flat_norm(match.group("target"))
                events.append({"span_index": span_index, "start": match.start(),
                    "end": match.end(), "pattern_index": pattern_index,
                    "target": literal_lookup[target_normalized],
                    "target_normalized": target_normalized})
    events.sort(key=lambda event: (event["span_index"], event["start"], event["end"],
                                   event["pattern_index"]))
    unique = []
    seen = set()
    for event in events:
        identity = (event["span_index"], event["start"], event["end"], event["target_normalized"])
        if identity not in seen:
            seen.add(identity)
            unique.append(event)
    selected_targets = {event["target_normalized"] for event in unique}
    if not unique:
        category = "UNRESOLVED_NO_ANCHORED_SELECTION"
        selected_target = None
    elif len(selected_targets) != 1:
        category = "UNRESOLVED_CONFLICTING_SELECTIONS"
        selected_target = None
    else:
        selected_normalized = next(iter(selected_targets))
        selected_target = next(event["target"] for event in unique
                               if event["target_normalized"] == selected_normalized)
        if selected_normalized in canonical_lookup:
            category = canonical_lookup[selected_normalized]
        elif (row["case_id"] == "VAL_E_CONFLICTING_BOOKS" and
              selected_normalized == flat_norm("national chain")):
            category = "HISTORY_TARGET_AMBIGUOUS_CURRENT_ATTRIBUTE"
        else:
            category = "HISTORY_TARGET"
    return {"category": category, "selected_target": selected_target,
            "events": unique, "searched_spans": spans}


def style_score(row, text, selection):
    if not row["factors"]["S"]:
        return {"style_target_applicable": False, "style_components": None,
                "narrow_operational_style": None}
    value = norm(text).strip()
    sentences = [part.strip() for part in re.split(r"[.!?\n]+", value) if part.strip()]
    category = selection["category"]
    target = selection["selected_target"]
    if row["persona_id"] == "SYN_VAL_D":
        immediate = bool(target and re.search(r"(?<!\w)my\s+pick\s*:\s*(?:the\s+)?" +
                         exact_pattern(target), value))
        components = {"my_pick_label_immediately_precedes_selected_target": immediate,
            "exact_terminal_sentence": value.endswith("that is the practical fit."),
            "semicolon_count_zero": value.count(";") == 0,
            "no_exclamation_mark": "!" not in text, "maximum_two_sentences": len(sentences) <= 2}
    else:
        components = {"first_sentence_prefix": bool(sentences and
                      sentences[0].startswith("i would choose")),
            "second_sentence_prefix": len(sentences) == 2 and
                      sentences[1].startswith("the key point is"),
            "reason_only_second_sentence": len(sentences) == 2 and
                      not any(marker in sentences[0] for marker in (" because ", " since ", " as ")),
            "semicolon_count_zero": value.count(";") == 0,
            "no_exclamation_mark": "!" not in text, "sentence_count_two": len(sentences) == 2}
    return {"style_target_applicable": True, "style_components": components,
            "narrow_operational_style": int(all(components.values()))
                    if not category.startswith("UNRESOLVED") else None}


def automatic_score(row, text, assessable=True):
    if not assessable:
        return {"measurement_state": "BOUNDARY_CENSORED", "selection_category": None,
            "selected_target": None, "anchored_events": None,
            "current_named_selection": None, "current_preference_choice": None,
            "history_target_selection": None, "full_canonical_both": None,
            "reason_support_state": None, "answer_completeness": None,
            "task_success": None, "sentence_count": None, "style_target_applicable":
            bool(row["factors"]["S"]), "style_components": None,
            "narrow_operational_style": None,
            "secondary_endpoints_enter_primary_effects": False}
    selection = anchored_selection(row, text)
    category = selection["category"]
    current = category in ("CURRENT_A", "CURRENT_B")
    history = category == "HISTORY_TARGET"
    ambiguous = category == "HISTORY_TARGET_AMBIGUOUS_CURRENT_ATTRIBUTE"
    unresolved = category.startswith("UNRESOLVED")
    current_named = 1 if current else 0 if history else None
    history_selected = 1 if history else 0 if current else None
    preferred = None
    selected_key = None
    if current:
        selected_key = category[-1]
        preferred = int(selected_key == row["preferred_option"])
    both = int(all(has_exact(text, row["options"][key]["canonical"]) for key in ("A", "B")))
    sentences = len([part for part in re.split(r"[.!?\n]+", norm(text)) if part.strip()])
    if not current:
        reason = "NOT_APPLICABLE" if (history or ambiguous) else "UNRESOLVED"
        complete = task = None
    else:
        first_event = selection["events"][0]
        searched = selection["searched_spans"]
        reason_text = " ".join(
            [searched[first_event["span_index"]][first_event["end"]:]] +
            searched[first_event["span_index"] + 1:]
        ).replace("-", " ")
        chosen_cues = [flat_norm(cue).replace("-", " ")
                       for cue in row["options"][selected_key]["reason_cues"]]
        other_key = "B" if selected_key == "A" else "A"
        other_cues = [flat_norm(cue).replace("-", " ")
                      for cue in row["options"][other_key]["reason_cues"]]
        support = any(cue in reason_text for cue in chosen_cues)
        contradiction = any(cue in reason_text for cue in other_cues)
        reason = "CONTRADICTED" if contradiction else "SUPPORTED" if support else "UNRESOLVED"
        complete = 1 if reason == "SUPPORTED" else 0 if reason == "CONTRADICTED" else None
        task = None if complete is None else int(complete == 1 and sentences <= 2)
    style = style_score(row, text, selection)
    return {"measurement_state": "ASSESSED_IDENTIFIABLE_UNIT",
        "selection_category": category, "selected_target": selection["selected_target"],
        "anchored_events": selection["events"], "current_named_selection": current_named,
        "current_preference_choice": preferred, "history_target_selection": history_selected,
        "full_canonical_both": both, "reason_support_state": reason,
        "answer_completeness": complete, "task_success": task, "sentence_count": sentences,
        **style, "secondary_endpoints_enter_primary_effects": False,
        "ambiguity_preserved_as_missing": ambiguous,
        "unresolved_preserved_as_missing": unresolved}


def result(row, response, latency):
    token_audit = b.validate_completion(response, row["input_token_ids"])
    normal = b.normalize_result(response)
    count = response.get("tokens_predicted")
    require(type(count) is int and 0 <= count <= row["max_new_tokens"], "Generated token count")
    returned = len(normal["generated_token_ids"]) if normal["generated_token_ids"] is not None else None
    require(returned is None or returned <= count, "Returned tokens exceed native count")
    if normal["stop_reason"] != "stop_sequence" and normal["token_ids_status"] == "returned":
        require(returned == count, "Token count mismatch")
    boundary = b.classify_response(normal["raw_response"], normal["raw_termination"], declared_stops=())
    span = boundary["first_span"]["text"]
    assessable = bool(boundary["unit_identifiable"] and span.strip() and boundary["status"] != "TRUNCATED")
    return {"request_id": row["request_id"], "request_sha256": row["request_sha256"], **normal,
        "generated_tokens": count, "returned_token_count": returned, "latency_seconds": latency,
        "input_token_audit": token_audit, "response_status": boundary,
        "raw_text_sha256": th(normal["raw_response"]), "first_reply_sha256": th(span),
        "automatic_score": automatic_score(row, span, assessable=assessable),
        "human_semantic_ratings": 0, "evidence_level": "ADAPTIVE_SYNTHETIC_AUTOMATIC_ONLY"}


def inventory(plan, events):
    attempted, raw, derived = [], {}, {}
    for event in events:
        data = event["data"]
        if event["kind"] == "persona_dialogue_mechanism_generation_started":
            require(len(attempted) < MAX_ATTEMPTS and data == plan["requests"][len(attempted)],
                    "Repeated, reordered, or unplanned attempt")
            attempted.append(data["request_id"])
        elif event["kind"] == "persona_dialogue_mechanism_raw_generation":
            request_id = data["request_id"]
            require(request_id in attempted and request_id not in raw, "Unbound/duplicate raw response")
            raw[request_id] = data
        elif event["kind"] == "persona_dialogue_mechanism_result":
            request_id = data["request_id"]
            require(request_id in raw and request_id not in derived, "Unbound/duplicate result")
            derived[request_id] = data
    return attempted, raw, derived


def validate_run_bindings(claim, run_manifest, plan, auth):
    """Reject altered claim, frozen inputs, or embedded authorization evidence."""
    require(claim["manifest_sha256"] == sha256(FROZEN), "Claim/manifest binding changed")
    require(claim["authorization_sha256"] == sha256(AUTH), "Claim/authorization binding changed")
    require(claim["design_sha256"] == sha256(DESIGN) == DESIGN_SHA,
            "Claim/design binding changed")
    require(claim["measurement_amendment_sha256"] == sha256(AMENDMENT) == AMENDMENT_SHA,
            "Claim/amendment binding changed")
    require(claim["parser_clarification_sha256"] ==
            sha256(PARSER_CLARIFICATION) == PARSER_CLARIFICATION_SHA,
            "Claim/parser-clarification binding changed")
    require(claim["integrity_amendment_sha256"] ==
            sha256(INTEGRITY_AMENDMENT) == INTEGRITY_AMENDMENT_SHA,
            "Claim/integrity-amendment binding changed")
    require(run_manifest["claim"] == claim, "Claim changed")
    require(run_manifest["frozen_manifest"] == plan, "Journal manifest changed")
    require(run_manifest["authorization"] == auth, "Journal authorization changed")
    return True


def run(preflight_path):
    fresh, stored, plan = preflight(), load(preflight_path), load(FROZEN)
    for key in ("manifest_sha256", "authorization_sha256", "design_sha256",
                "measurement_amendment_sha256", "parser_clarification_sha256",
                "integrity_amendment_sha256",
                "source_hashes", "configuration", "server_command"):
        require(fresh[key] == stored[key], "Preflight binding changed: " + key)
    with b.writer_lock(ROOT):
        require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
                "Existing allocation: no repeat or resume")
        claim = {key: fresh[key] for key in ("manifest_sha256", "authorization_sha256",
                 "design_sha256", "measurement_amendment_sha256",
                 "parser_clarification_sha256", "integrity_amendment_sha256",
                 "source_hashes")}
        claim.update(preflight_sha256=sha256(preflight_path), maximum_attempts=MAX_ATTEMPTS)
        save(ROOT / "claim.json", claim)
        journal = b.RunJournal(ROOT / "runs", {
            "phase": "P1 adaptive synthetic persona-dialogue mechanism validation",
            "evidence_level": "ADAPTIVE_VALIDATION_UNSEEN_SYNTHETIC_CASES_AUTOMATIC",
            "claim": claim, "frozen_manifest": plan, "authorization": load(AUTH),
            "configuration": cfg(plan).as_dict(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
            "python": platform.python_version(), "platform": platform.platform()})
        for path, digest in claim["source_hashes"].items():
            destination = journal.directory / "source_snapshot" / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as handle:
                handle.write(Path(path).read_bytes())
            require(sha256(destination) == digest, "Source snapshot changed")
        started, active, status = time.monotonic(), None, "BLOCKED"
        try:
            journal.write("preflight", fresh)
            with s.Server(plan, journal) as server:
                client = b.LlamaClient(cfg(plan).endpoint, timeout=180, audit=journal.write)
                props = client.request("/props")
                binding = b.validate_server_properties(props, cfg(plan))
                require(binding["build_info"] == "b11573-0f701c882", "Backend build")
                journal.write("effective_server_defaults", {"props": props, "validation": binding})
                for row in plan["requests"]:
                    tokens = client.request("/tokenize", {"content": row["prompt"], "add_special": True,
                        "parse_special": True, "with_pieces": False})["tokens"]
                    require(tokens == row["input_token_ids"], "Live native tokenizer changed")
                    journal.write("live_prompt_verified", {"request_id": row["request_id"],
                                  "token_ids_sha256": th(str(tokens))})
                journal.write("live_preflight_pass", {"prompts": MAX_ATTEMPTS, "completed_inference": 0})
                print(json.dumps({"live_preflight": "PASS", "planned": MAX_ATTEMPTS}), flush=True)
                for row in plan["requests"]:
                    remaining = plan["resource_budget"]["batch_wall_seconds_ceiling"] - (
                        time.monotonic() - started)
                    require(remaining > 0, "45-minute limit reached; preserve suffix")
                    server.assert_running()
                    client.timeout = min(180, remaining)
                    active = row["request_id"]
                    journal.write("persona_dialogue_mechanism_generation_started", row)
                    tick = time.monotonic()
                    response = client.request("/completion", payload(row))
                    latency = time.monotonic() - tick
                    journal.write("persona_dialogue_mechanism_raw_generation", {
                                  "request_id": active, "response": response,
                                  "latency_seconds": latency})
                    derived = result(row, response, latency)
                    journal.write("persona_dialogue_mechanism_result", derived)
                    print(json.dumps({"order": row["order"], "id": active,
                        "category": derived["automatic_score"]["selection_category"],
                        "tokens": derived["generated_tokens"], "stop": derived["stop_reason"],
                        "seconds": round(latency, 2)}), flush=True)
                    active = None
                server.assert_running()
                b.validate_server_properties(client.request("/props"), cfg(plan))
                after = preflight(check_headroom=False, require_unused=False)
                require(after["identity"] == fresh["identity"] and
                        after["source_hashes"] == fresh["source_hashes"],
                        "Postflight identity/source changed")
                journal.write("postflight", after)
            status = "PASS"
        except BaseException as exc:
            status = "PARTIAL" if active else "BLOCKED"
            journal.write("failure", {"type": type(exc).__name__, "message": str(exc),
                                      "request_id": active})
        events = b.read_events(journal.directory)
        attempted, raw, derived = inventory(plan, events)
        if status == "BLOCKED" and len(derived) == MAX_ATTEMPTS:
            status = "COMPLETE_DATA_POSTFLIGHT_FAILED"
        summary = {"status": status, "attempted": len(attempted),
            "responses_received": len(raw), "results": len(derived),
            "inference_wall_seconds": sum(value["latency_seconds"] for value in raw.values()),
            "batch_wall_seconds": time.monotonic() - started,
            "run_directory": journal.directory.as_posix(), "retries": 0,
            "human_semantic_ratings": 0}
        journal.finish(**summary)
        save(journal.directory / "summary.json", summary)
        return summary


def replay():
    plan = load(FROZEN)
    validate_plan(plan)
    folders = list((ROOT / "runs").glob("*"))
    require(len(folders) == 1, "Unexpected run count")
    folder = folders[0]
    events = b.read_events(folder)
    claim = load(ROOT / "claim.json")
    run_manifest = load(folder / "manifest.json")
    validate_run_bindings(claim, run_manifest, plan, load(AUTH))
    attempted, raw, derived = inventory(plan, events)
    require(events and events[-1]["kind"] == "run_finished", "Missing terminal run event")
    require(load(folder / "summary.json") == events[-1]["data"], "Summary/terminal event changed")
    if events[-1]["data"]["status"] == "PASS":
        require(sum(event["kind"] == "postflight" for event in events) == 1,
                "Successful run lacks postflight")
    live = [event["data"] for event in events if event["kind"] == "live_prompt_verified"]
    require(len(live) == MAX_ATTEMPTS and [item["request_id"] for item in live] ==
            [row["request_id"] for row in plan["requests"]], "Live-token verification incomplete")
    for path, digest in claim["source_hashes"].items():
        snapshot = folder / "source_snapshot" / path
        require(snapshot.is_file() and sha256(snapshot) == digest,
                "Source snapshot changed: " + path)
    sent = [event["data"]["payload"] for event in events if event["kind"] == "http_request" and
            event["data"]["route"] == "/completion"]
    require(sent == [payload(row) for row in plan["requests"][:len(attempted)]],
            "Actual payload changed")
    bodies = [json.loads(base64.b64decode(event["data"]["body_base64"])) for event in events
              if event["kind"] == "http_response" and event["data"]["route"] == "/completion" and
              event["data"].get("status") == 200]
    require(bodies == [record["response"] for record in raw.values()], "Raw HTTP response changed")
    rows = []
    for row in plan["requests"]:
        request_id = row["request_id"]
        reconstructed = (result(row, raw[request_id]["response"], raw[request_id]["latency_seconds"])
                         if request_id in raw else None)
        if request_id in derived:
            require(reconstructed == derived[request_id], "Derived result changed")
        state = ("COMPLETED" if request_id in derived else "RAW_RECOVERABLE" if request_id in raw else
                 "ATTEMPTED_UNRESOLVED" if request_id in attempted else "UNATTEMPTED")
        rows.append((row, reconstructed, state))
    return folder, events, rows, len(bodies)


def audit():
    plan, auth = load(FROZEN), load(AUTH)
    require(auth["decision"] == "AUTHORIZED" and auth["maximum_attempts"] == MAX_ATTEMPTS and
            auth["retries"] == 0, "Authorization changed")
    require(auth["manifest_sha256"] == sha256(FROZEN), "Manifest/auth changed")
    require(auth["design_sha256"] == DESIGN_SHA and
            auth["measurement_amendment_sha256"] == AMENDMENT_SHA, "Design/auth changed")
    require(auth["parser_clarification_sha256"] == PARSER_CLARIFICATION_SHA,
            "Parser-clarification/auth changed")
    require(auth["preexecution_integrity_amendment_sha256"] == INTEGRITY_AMENDMENT_SHA,
            "Integrity-amendment/auth changed")
    validate_plan(plan)
    folder, events, rows, bodies = replay()
    public = []
    for row, result_row, state in rows:
        public.append({"request_id": row["request_id"], "request_sha256": row["request_sha256"],
            "case_id": row["case_id"], "arm": row["arm"], "state": state,
            "raw_text_sha256": None if result_row is None else result_row["raw_text_sha256"],
            "first_reply_sha256": None if result_row is None else result_row["first_reply_sha256"],
            "generated_tokens": None if result_row is None else result_row["generated_tokens"],
            "stop_reason": None if result_row is None else result_row["stop_reason"],
            "latency_seconds": None if result_row is None else result_row["latency_seconds"],
            "automatic_score": None if result_row is None else result_row["automatic_score"]})
    return {"version": "p1_persona_dialogue_mechanism_integrity_v1",
        "integrity_status": "PASS", "manifest_sha256": sha256(FROZEN),
        "design_sha256": DESIGN_SHA, "measurement_amendment_sha256": AMENDMENT_SHA,
        "parser_clarification_sha256": PARSER_CLARIFICATION_SHA,
        "integrity_amendment_sha256": INTEGRITY_AMENDMENT_SHA,
        "run_directory": folder.as_posix(),
        "attempted": sum(state != "UNATTEMPTED" for _, _, state in rows),
        "results": sum(state == "COMPLETED" for _, _, state in rows),
        "http_responses_verified": bodies, "journal_events": len(events), "rows": public,
        "raw_text_embedded": False, "new_generations_during_audit": 0}


def mean(values):
    return None if not values else sum(values) / len(values)


def binary_summary(scores, metric):
    values = [score[metric] for score in scores]
    ones = sum(value == 1 for value in values)
    zeros = sum(value == 0 for value in values)
    missing = sum(value is None for value in values)
    total = len(values)
    resolved = [value for value in values if value is not None]
    return {"ones": ones, "zeros": zeros, "missing": missing,
        "resolved_denominator": len(resolved), "mean_resolved": mean(resolved),
        "logical_lower": ones / total, "logical_upper": (ones + missing) / total}


def paired_contrast(by_case, treatment, control, metric):
    contributions, lower, upper = [], [], []
    for case_id in sorted(by_case):
        left = by_case[case_id][treatment][metric]
        right = by_case[case_id][control][metric]
        contributions.append(None if left is None or right is None else left - right)
        lower.append((0 if left is None else left) - (1 if right is None else right))
        upper.append((1 if left is None else left) - (0 if right is None else right))
    resolved = [value for value in contributions if value is not None]
    return {"treatment": treatment, "control": control,
        "case_contributions": contributions, "complete_cases": len(resolved),
        "complete_case_estimate": mean(resolved), "logical_lower": mean(lower),
        "logical_upper": mean(upper)}


def analyze():
    plan = load(FROZEN)
    validate_plan(plan)
    design, amendment = load(DESIGN), load(AMENDMENT)
    folder, events, rows, _ = replay()
    require(all(state == "COMPLETED" for _, _, state in rows), "Complete 42-row run required")
    by_arm, by_case, regimes = defaultdict(list), defaultdict(dict), {}
    results_only = []
    for row, result_row, _ in rows:
        score = result_row["automatic_score"]
        by_arm[row["arm"]].append(score)
        by_case[row["case_id"]][row["arm"]] = score
        regimes[row["case_id"]] = row["history_regime"]
        results_only.append(result_row)
    arm_summary = {}
    for arm in sorted(by_arm):
        scores = by_arm[arm]
        arm_summary[arm] = {metric: binary_summary(scores, metric) for metric in PRIMARY_METRICS}
        arm_summary[arm]["selection_categories"] = dict(Counter(
            score["selection_category"] for score in scores))
    contrast_pairs = {
        "F_H_STRUCTURE_minus_F_H_RAW": ("F_H_STRUCTURE", "F_H_RAW"),
        "F_H_REFRESH_minus_F_H_RAW": ("F_H_REFRESH", "F_H_RAW"),
        "F_H_RAW_minus_S_F_NO_H": ("F_H_RAW", "S_F_NO_H"),
        "S_F_H_minus_F_H_RAW": ("S_F_H", "F_H_RAW"),
        "S_H_minus_H_ONLY": ("S_H", "H_ONLY"),
    }
    contrasts = {name: {metric: paired_contrast(by_case, left, right, metric)
                         for metric in PRIMARY_METRICS}
                 for name, (left, right) in contrast_pairs.items()}
    regime_strata = {}
    for regime in sorted(set(regimes.values())):
        ids = [case_id for case_id, value in regimes.items() if value == regime]
        regime_strata[regime] = {}
        for name, (left, right) in contrast_pairs.items():
            regime_strata[regime][name] = {}
            for metric in PRIMARY_METRICS:
                values = []
                lower, upper = [], []
                for case_id in sorted(ids):
                    a, z = by_case[case_id][left][metric], by_case[case_id][right][metric]
                    values.append(None if a is None or z is None else a - z)
                    lower.append((0 if a is None else a) - (1 if z is None else z))
                    upper.append((1 if a is None else a) - (0 if z is None else z))
                resolved = [value for value in values if value is not None]
                regime_strata[regime][name][metric] = {"case_contributions": values,
                    "pairs_total": len(ids), "resolved_pairs": len(resolved),
                    "mean_resolved": mean(resolved),
                    "logical_lower": mean(lower), "logical_upper": mean(upper)}
    secondary = {}
    for arm in sorted(by_arm):
        scores = by_arm[arm]
        style = (binary_summary(scores, "narrow_operational_style")
                 if design["arms"][arm]["S"] else
                 {"applicability": "STRUCTURAL_NOT_APPLICABLE", "ones": 0, "zeros": 0,
                  "missing": 0, "resolved_denominator": 0, "mean_resolved": None,
                  "logical_lower": None, "logical_upper": None})
        secondary[arm] = {"reason_support_distribution": dict(Counter(
            score["reason_support_state"] for score in scores)),
            "task_success": binary_summary(scores, "task_success"),
            "narrow_operational_style": style}
    memory_events = [event["data"] for event in events if event["kind"] == "memory_observation"]
    peak = max((entry.get("process", {}).get("peak_working_set", 0) for entry in memory_events),
               default=0)
    available = [entry.get("system", {}).get("available_physical") for entry in memory_events]
    available = [value for value in available if value is not None]
    latency = sum(result_row["latency_seconds"] for result_row in results_only)
    return {"version": "p1_persona_dialogue_mechanism_analysis_v1",
        "evidence_level": "ADAPTIVE_VALIDATION_UNSEEN_SYNTHETIC_CASES_AUTOMATIC",
        "scientific_scope": design["research"]["purpose"], "manifest_sha256": sha256(FROZEN),
        "design_sha256": DESIGN_SHA, "measurement_amendment_sha256": AMENDMENT_SHA,
        "parser_clarification_sha256": PARSER_CLARIFICATION_SHA,
        "integrity_amendment_sha256": INTEGRITY_AMENDMENT_SHA,
        "run_directory": folder.as_posix(), "generations": len(results_only), "human_ratings": 0,
        "primary_arm_summary": arm_summary, "primary_paired_contrasts": contrasts,
        "history_regime_strata": regime_strata,
        "secondary_only_not_in_primary_effects": secondary,
        "inferential_policy": {"p_values": "NOT_COMPUTED", "estimation_first": True,
            "missing_ambiguous_or_unresolved_recoded_as_zero": False},
        "resource_observations": {"generated_tokens": sum(
            result_row["generated_tokens"] for result_row in results_only),
            "completion_inference_seconds": latency, "peak_server_working_set_bytes": peak,
            "minimum_observed_available_physical_bytes": min(available) if available else None},
        "cumulative_authorization_after": {"generations_used": GENERATION_BASELINE + len(results_only),
            "generations_limit": 1200, "inference_seconds_used": INFERENCE_BASELINE + latency,
            "inference_seconds_limit": 72000.0},
        "limits": amendment["interpretation_limits"] + design["limitations"],
        "new_generations_during_analysis": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("register", "amend", "preflight", "run", "audit", "analyze"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preflight", type=Path)
    args = parser.parse_args()
    if args.action == "register":
        value = register()
    elif args.action == "amend":
        value = amend()
    elif args.action == "run":
        if not args.preflight:
            parser.error("--preflight required")
        value = run(args.preflight)
    else:
        if not args.output:
            parser.error("--output required")
        value = preflight() if args.action == "preflight" else audit() if args.action == "audit" else analyze()
        save(args.output, value)
    hidden = ("rows", "identity", "source_hashes", "memory_before_run", "primary_arm_summary",
              "primary_paired_contrasts", "history_regime_strata")
    print(json.dumps({key: value for key, value in value.items() if key not in hidden}, indent=2))
    if value.get("status") in ("PARTIAL", "BLOCKED", "COMPLETE_DATA_POSTFLIGHT_FAILED"):
        raise SystemExit(2)
