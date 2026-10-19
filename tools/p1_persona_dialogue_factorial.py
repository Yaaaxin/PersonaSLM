"""One frozen 48-request synthetic persona-dialogue S/F/H development batch.

No warmup, retry, hidden completion, model download, or historical-ledger mutation.
Raw responses remain in the ignored append-only run journal; public artifacts contain
only hashes, frozen automatic categories, and aggregate estimates.
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

import p1d_instruct_smoke as s

b = s.b
DESIGN = Path("docs/validation/p1/persona_dialogue_factorial_v1/prospective_design_v1.json")
PROTOCOL = DESIGN.with_name("protocol_v1.md")
VALIDATION_DESIGN = DESIGN.with_name("independent_validation_design_v1.json")
BASELINE = Path("docs/validation/p1/model_feasibility_recovery_v1/post_candidate2_research_state_v1.json")
OUT = DESIGN.parent
FROZEN_V1 = OUT / "frozen_manifest_v1.json"
AUTH_V1 = OUT / "researcher_authorization_v1.json"
FROZEN = OUT / "frozen_manifest_v2.json"
AUTH = OUT / "researcher_authorization_v2.json"
ROOT = Path("results/p1_persona_dialogue_factorial/development_v1")
MAX_ATTEMPTS = 48
BASELINE_SHA = "1489732ce936860d46fa0001bf1edc2328b65c3f7b5cde386563644558fbba65"
load, save, sha256, th, require = s.load, s.save, s.sha256, s.th, s.require


def source_hashes():
    paths = list(Path("src/personaslm").glob("*.py")) + [
        Path(__file__), Path("tools/p1d_instruct_smoke.py"),
        Path("tools/p1d_budget_calibration.py"), Path("tools/p1d_format_calibration.py"),
        Path("tools/p1d_instruct_template_check.py"), DESIGN, PROTOCOL, VALIDATION_DESIGN,
        Path("tests/test_p1_persona_dialogue_factorial.py"),
    ]
    root = Path.cwd().resolve()
    return {p.resolve().relative_to(root).as_posix(): sha256(p) for p in paths}


def cfg(plan):
    return s.Runtime(plan["model"]["model_file"], plan["model"]["model_sha256"],
                     plan["model"]["backend_file"], model_label=plan["model"]["model_label"])


def construction(design, case, condition):
    factors = design["factors"]["conditions"][condition]
    persona = design["personas"][case["persona_id"]]
    system = (design["prompt_policy"]["fixed_system_instruction"] + "\n"
              + "Speaker: " + persona["speaker_name"] + ".\n"
              + case["fixed_current_notes"])
    if factors["S"]:
        system += "\n" + persona["S_block"]
    if factors["F"]:
        system += "\n" + persona["F_block"]
    messages = [{"role": "system", "content": system}]
    if factors["H"]:
        messages.extend(case["history_messages"])
    messages.append({"role": "user", "content": case["fixed_current_user"]})
    return factors, messages


def validate_design(design):
    require(design["status"] == "FROZEN_PROSPECTIVE_DEVELOPMENT_NOT_EXECUTED", "Design status")
    require(design["research"]["data_scope"] == "SYNTHETIC_PERSONAS_ONLY", "Data scope")
    require(design["authorization"]["maximum_attempts"] == MAX_ATTEMPTS, "Allocation")
    require(design["authorization"]["retries"] == 0, "Retry policy")
    require(design["bindings"]["post_candidate2_state"]["sha256"] == BASELINE_SHA, "Baseline binding")
    require(sha256(BASELINE) == BASELINE_SHA, "Baseline changed")
    profile = design["bindings"]["persona_profile_source"]
    require(sha256(Path(profile["path"])) == profile["sha256"], "Profile source changed")
    runtime = design["runtime"]
    for key, value in {"threads": 4, "threads_batch": 4, "context_tokens": 4096,
                       "gpu_layers": 0, "max_new_tokens": 96, "temperature": 0.0,
                       "top_p": 1.0, "seed": 42, "cache_prompt": False,
                       "warmup": False}.items():
        require(runtime[key] == value, "Runtime changed: " + key)
    require(design["resource_budget"]["requests"] == MAX_ATTEMPTS, "Request budget")
    require(design["resource_budget"]["global_baseline"]["generations_used"] == 16, "Generation baseline")
    require(design["resource_budget"]["global_baseline"]["inference_wall_seconds_used"] == 159.95704690001094,
            "Time baseline")
    conditions = design["factors"]["conditions"]
    require(set(conditions) == {f"C{i}" for i in range(8)}, "Condition set")
    cases = design["cases"]
    require(len(cases) == len({c["case_id"] for c in cases}) == 6, "Case set")
    require(len(design["order"]["requests"]) == MAX_ATTEMPTS, "Order size")
    expected = []
    seed = design["order"]["seed"]
    for case in cases:
        history = " ".join(m["content"] for m in case["history_messages"]).casefold()
        for option in case["options"].values():
            require(not any(a.casefold() in history for a in option["aliases"]),
                    "Current option leaked into history: " + case["case_id"])
        for condition in conditions:
            rid = "pdlg_v1_" + case["case_id"].lower() + "_" + condition.lower()
            key = th(str(seed) + "|" + rid)
            expected.append((key, rid, case["case_id"], condition))
    expected.sort()
    observed = design["order"]["requests"]
    require([(r["order"], r["request_id"], r["case_id"], r["condition"]) for r in observed] ==
            [(i, rid, cid, cond) for i, (_, rid, cid, cond) in enumerate(expected)], "Frozen order")
    return {"cases": 6, "conditions": 8, "requests": 48, "synthetic_personas": 2,
            "history_regimes": dict(Counter(c["history_regime"] for c in cases))}


def validate_plan(plan):
    require(plan["version"] == "p1_persona_dialogue_factorial_manifest_v2", "Manifest version")
    require(plan["design_sha256"] == sha256(DESIGN), "Design changed")
    design = load(DESIGN)
    checks = validate_design(design)
    require(plan["registration_source_hashes"] == source_hashes(), "Registered source changed")
    require(plan["template_sha256"] == sha256(Path(plan["template_path"])), "Template changed")
    rows = plan["requests"]
    require(len(rows) == len({r["request_id"] for r in rows}) == MAX_ATTEMPTS, "Rows")
    cases = {c["case_id"]: c for c in design["cases"]}
    template = Path(plan["template_path"]).read_text(encoding="utf-8")
    for i, row in enumerate(rows):
        require(row["order"] == i, "Row order")
        case = cases[row["case_id"]]
        factors, messages = construction(design, case, row["condition"])
        require(row["factors"] == factors and row["messages"] == messages, "Prompt messages changed")
        require(row["prompt"] == s.render(template, messages), "Rendered prompt changed")
        require(row["prompt_sha256"] == th(row["prompt"]), "Prompt hash")
        require(row["input_token_ids_sha256"] == th(str(row["input_token_ids"])), "Token hash")
        require(len(row["input_token_ids"]) == row["input_tokens"], "Token count")
        require(row["input_tokens"] + 96 <= 4096, "Context overflow")
        require(row["request_sha256"] == th(json.dumps(
            {k: v for k, v in row.items() if k != "request_sha256"},
            sort_keys=True, separators=(",", ":"))), "Request hash")
    for case in cases.values():
        group = [r for r in rows if r["case_id"] == case["case_id"]]
        require({r["condition"] for r in group} == {f"C{i}" for i in range(8)}, "Cell coverage")
        require(len({r["current_user_sha256"] for r in group}) == 1, "Current user invariant")
        require(len({r["current_notes_sha256"] for r in group}) == 1, "Current notes invariant")
    return {**checks, "input_token_range": [min(r["input_tokens"] for r in rows),
                                              max(r["input_tokens"] for r in rows)]}


def register():
    require(not FROZEN.exists() and not AUTH.exists(), "Registration exists; do not replace")
    require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
            "Execution allocation already exists")
    design = load(DESIGN)
    checks = validate_design(design)
    require(sha256(VALIDATION_DESIGN) == "8e6956c4e909bff06a7a5623593493ff84521da680c2f1703110579fb522c6d0",
            "Pre-output independent validation freeze changed")
    runtime = design["runtime"]
    model = design["model"]
    require(sha256(Path(model["artifact_path"])) == model["artifact_sha256"], "Model changed")
    require(sha256(Path(runtime["backend_path"])) == runtime["backend_sha256"], "Backend changed")
    require(sha256(Path(runtime["chat_template_path"])) == runtime["chat_template_sha256"], "Template changed")
    memory = s.memory_observation(os.getpid())
    require(memory.get("system", {}).get("available_physical", 0) >=
            design["resource_budget"]["minimum_available_physical_ram_bytes"], "Less than 3 GiB RAM")
    tokenizer = Path(runtime["backend_path"]).with_name("llama-tokenize.exe")
    require(sha256(tokenizer) == "e05dbdef761e577b3d56f3daea7b205a07f68e5d87242ea4e2544382ffdd358e",
            "Tokenizer changed")
    template = Path(runtime["chat_template_path"]).read_text(encoding="utf-8")
    cases = {c["case_id"]: c for c in design["cases"]}
    rows, logs = [], []
    for item in design["order"]["requests"]:
        case = cases[item["case_id"]]
        factors, messages = construction(design, case, item["condition"])
        prompt = s.render(template, messages)
        argv = [str(tokenizer.resolve()), "-m", str(Path(model["artifact_path"]).resolve()),
                "--stdin", "--ids", "--offline"]
        started = b.utc_now()
        result = subprocess.run(argv, input=prompt.encode("utf-8"), capture_output=True, timeout=90,
            env={k: v for k, v in os.environ.items() if not k.upper().startswith("LLAMA_ARG_")},
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        require(result.returncode == 0, "Native tokenizer failed")
        ids = ast.literal_eval(result.stdout.decode("utf-8", "replace").strip())
        require(isinstance(ids, list) and ids and all(type(x) is int and x >= 0 for x in ids), "Token IDs")
        log = {"started_utc": started, "finished_utc": b.utc_now(), "argv": argv,
               "returncode": result.returncode, "stdout": result.stdout.decode("utf-8", "replace"),
               "stderr": result.stderr.decode("utf-8", "replace"), "prompt_sha256": th(prompt),
               "generation_requests": 0}
        log_path = OUT / "native_tokenizer" / f"{item['order']:04d}.json"
        save(log_path, log)
        logs.append({"path": log_path.as_posix(), "sha256": sha256(log_path)})
        row = {**item, "persona_id": case["persona_id"], "history_regime": case["history_regime"],
               "factors": factors, "messages": messages, "prompt": prompt, "prompt_sha256": th(prompt),
               "input_token_ids": ids, "input_tokens": len(ids), "input_token_ids_sha256": th(str(ids)),
               "context_remaining": 4096 - 96 - len(ids), "preferred_option": case["preferred_option"],
               "history_favored_option": case["history_favored_option"], "options": case["options"],
               "metric_applicability": case["metric_applicability"],
               "current_notes_sha256": th(case["fixed_current_notes"]),
               "current_user_sha256": th(case["fixed_current_user"]), "max_new_tokens": 96,
               "seed": 42, "temperature": 0.0, "top_p": 1.0, "stop": [], "cache_prompt": False}
        require(row["context_remaining"] >= 0, "Context overflow")
        row["request_sha256"] = th(json.dumps(row, sort_keys=True, separators=(",", ":")))
        rows.append(row)
    frozen_model = {"model_label": model["label"], "model_file": model["artifact_path"],
                    "model_sha256": model["artifact_sha256"], "backend_file": runtime["backend_path"],
                    "backend_sha256": runtime["backend_sha256"], "quantization": model["quantization"],
                    "artifact_revision": model["artifact_revision"],
                    "intended_upstream_revision": model["intended_upstream_revision"],
                    "conversion_lineage": model["conversion_lineage"]}
    plan = {"version": "p1_persona_dialogue_factorial_manifest_v1", "classification": design["research"],
            "design_path": DESIGN.as_posix(), "design_sha256": sha256(DESIGN),
            "independent_validation_design_sha256": sha256(VALIDATION_DESIGN),
            "baseline_state_sha256": BASELINE_SHA, "model": frozen_model,
            "template_path": runtime["chat_template_path"], "template_sha256": runtime["chat_template_sha256"],
            "runtime": runtime, "resource_budget": design["resource_budget"], "requests": rows,
            "native_tokenizer_logs": logs, "registration_source_hashes": source_hashes(),
            "registered_utc": b.utc_now(), "new_model_generations": 0}
    save(FROZEN, plan)
    manifest_sha = sha256(FROZEN)
    save(AUTH, {"version": "p1_persona_dialogue_factorial_authorization_v1", "researcher": "Yaxin ZHENG",
          "decision": "AUTHORIZED", "decision_source": design["authorization"]["basis"],
          "registered_utc": b.utc_now(), "manifest_sha256": manifest_sha,
          "maximum_attempts": MAX_ATTEMPTS, "retries": 0,
          "scope": design["authorization"]["scope"], "prohibitions": design["authorization"]["prohibitions"],
          "independent_validation_authorized": False})
    tracked = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    save(OUT / "source_preservation_baseline_v1.json", {"recorded_utc": b.utc_now(),
          "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
          "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
          "tracked_sha256": {p: sha256(Path(p)) for p in tracked if p and Path(p).is_file()}})
    return {"status": "REGISTERED", "manifest_sha256": manifest_sha,
            "design_sha256": sha256(DESIGN), "tokenizer_calls": 48, "generation_requests": 0,
            **checks, "input_token_range": [min(r["input_tokens"] for r in rows), max(r["input_tokens"] for r in rows)]}


def amend():
    """Prospective source-only amendment after v1 registration and before any completion."""
    require(sha256(FROZEN_V1) == "fb573ef6b904bd1c640ca43ad10e98518d0237cb651b0094c4ba3e927d1047b9",
            "Registered v1 manifest changed")
    require(load(AUTH_V1)["manifest_sha256"] == sha256(FROZEN_V1), "V1 authorization changed")
    require(not FROZEN.exists() and not AUTH.exists(), "V2 amendment already exists")
    require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
            "Completion evidence exists; amendment prohibited")
    plan = load(FROZEN_V1)
    require(plan["new_model_generations"] == 0 and len(plan["requests"]) == 48, "V1 scope")
    plan["version"] = "p1_persona_dialogue_factorial_manifest_v2"
    plan["registration_source_hashes"] = source_hashes()
    plan["preexecution_amendment"] = {
        "status": "PROSPECTIVE_BEFORE_ANY_MODEL_OUTPUT",
        "amended_utc": b.utc_now(),
        "parent_manifest_path": FROZEN_V1.as_posix(),
        "parent_manifest_sha256": sha256(FROZEN_V1),
        "new_model_generations_before_amendment": 0,
        "scientific_inputs_changed": False,
        "prompt_or_token_ids_changed": False,
        "execution_order_changed": False,
        "scoring_alias_or_cue_changed": False,
        "repairs": [
            "Bind ignore_eos=false in the actual completion payload.",
            "Censor all binary automatic endpoints for empty, unidentifiable, or native-length-truncated units.",
            "Apply the remaining batch wall-time to each HTTP completion timeout.",
            "Strengthen audit checks for source snapshots, live-token verification, terminal event, and summary.",
            "Separate outdated-value NOT_APPLICABLE from applicable UNRESOLVED counts.",
            "Distinguish complete data with failed postflight from a pre-completion block."
        ]}
    save(FROZEN, plan)
    parent = load(AUTH_V1)
    save(AUTH, {**parent, "version": "p1_persona_dialogue_factorial_authorization_v2",
        "registered_utc": b.utc_now(), "manifest_sha256": sha256(FROZEN),
        "parent_authorization_path": AUTH_V1.as_posix(), "parent_authorization_sha256": sha256(AUTH_V1),
        "amendment_scope": "Execution-integrity and missingness repairs only; exact 48 prompts, token IDs, order, model, settings, aliases, cues, and resource allocation unchanged."})
    return {"status": "AMENDED_BEFORE_OUTPUT", "parent_manifest_sha256": sha256(FROZEN_V1),
            "manifest_sha256": sha256(FROZEN), "requests": 48, "prompt_or_token_changes": 0,
            "generation_requests_before_amendment": 0}


def preflight(check_headroom=True):
    plan = load(FROZEN)
    auth = load(AUTH)
    require(auth["decision"] == "AUTHORIZED" and auth["maximum_attempts"] == MAX_ATTEMPTS, "Authorization")
    require(auth["manifest_sha256"] == sha256(FROZEN), "Manifest/auth binding")
    checks = validate_plan(plan)
    config = cfg(plan)
    identity = b.file_preflight(config)
    require(identity["status"] == "PASS", "File preflight")
    require(identity["model"]["sha256"] == plan["model"]["model_sha256"], "Model identity")
    require(identity["server"]["sha256"] == plan["model"]["backend_sha256"], "Backend identity")
    directory = Path(config.server_file).parent
    native = load(b.FROZEN)["native_tokenizer_identity"]
    require(sha256(directory / "llama-tokenize.exe") == native["tokenizer_sha256"], "Tokenizer identity")
    require({p.name: sha256(p) for p in directory.glob("*.dll")} == native["dll_hashes"], "DLL identity")
    for record in plan["native_tokenizer_logs"]:
        require(sha256(Path(record["path"])) == record["sha256"], "Tokenizer log changed")
    state = load(BASELINE)["authorization_balances"]["autonomous_recovery"]
    require(state["generations_used"] == 16 and state["inference_wall_seconds_used"] == 159.95704690001094,
            "Cumulative baseline changed")
    require(state["generations_remaining"] >= MAX_ATTEMPTS, "Generation ceiling")
    memory = s.memory_observation(os.getpid())
    if check_headroom:
        require(memory.get("system", {}).get("available_physical", 0) >=
                plan["resource_budget"]["minimum_available_physical_ram_bytes"], "Less than 3 GiB RAM")
    require(shutil.disk_usage(".").free >= plan["resource_budget"]["minimum_free_output_disk_bytes"],
            "Output disk reserve")
    return {"status": "PASS", "checked_utc": b.utc_now(), "checks": checks, "identity": identity,
            "manifest_sha256": sha256(FROZEN), "authorization_sha256": sha256(AUTH),
            "source_hashes": source_hashes(), "configuration": config.as_dict(),
            "server_command": s.command(plan), "memory_before_run": memory,
            "cumulative_baseline": state,
            "live_gate": "All 48 parse_special=true token arrays must match before any completion."}


def payload(row):
    return {"prompt": row["input_token_ids"], "n_predict": 96, "temperature": 0.0, "top_p": 1.0,
            "seed": 42, "cache_prompt": False, "stop": [], "ignore_eos": False,
            "return_tokens": True, "stream": False}


def norm(text):
    text = unicodedata.normalize("NFKC", text).casefold().replace("—", "-").replace("–", "-")
    return " ".join(text.split())


def has_alias(text, aliases):
    return any(re.search(r"(?<!\w)" + re.escape(norm(alias)) + r"(?!\w)", text) for alias in aliases)


def automatic_score(row, text, assessable=True):
    if not assessable:
        return {"measurement_state": "BOUNDARY_CENSORED", "selected_option": "UNRESOLVED",
            "option_hits": {"A": False, "B": False}, "reason_support_state": "UNRESOLVED",
            "sentence_count": None, "answer_completeness": None, "task_success": None,
            "current_preference_choice": None, "history_favored_choice": None,
            "outdated_value_adoption": None,
            "outdated_value_applicable": row["history_regime"] == "OUTDATED_CONFLICTING" and
                row["condition"] in ("C6", "C7"),
            "style_target_applicable": bool(row["factors"]["S"]), "style_components": None,
            "operational_linguistic_fidelity": None, "operational_behavioral_fidelity": None}
    value = norm(text)
    hits = {key: has_alias(value, option["aliases"]) for key, option in row["options"].items()}
    selected = next((k for k in ("A", "B") if hits[k] and not hits["B" if k == "A" else "A"]), None)
    selected_pos = None
    if selected:
        positions = [value.find(norm(a)) for a in row["options"][selected]["aliases"] if norm(a) in value]
        selected_pos = min(positions) if positions else None
    selected_cues = [] if not selected else [norm(c) for c in row["options"][selected]["reason_cues"]]
    other = None if not selected else ("B" if selected == "A" else "A")
    other_cues = [] if other is None else [norm(c) for c in row["options"][other]["reason_cues"]]
    selected_support = any(c in value for c in selected_cues)
    contradiction = any(c in value for c in other_cues)
    reason = "UNRESOLVED" if not selected else ("CONTRADICTED" if contradiction else
             "SUPPORTED" if selected_support else "UNRESOLVED")
    sentences = len([x for x in re.split(r"[.!?]+", value) if x.strip()])
    complete = None if not text.strip() else int(selected is not None and reason == "SUPPORTED")
    task = None if complete is None else int(complete == 1 and sentences <= 2)
    persona_id = row["persona_id"]
    if persona_id == "SYN_PF_B":
        aliases = ["certainly", "i understand"]
        ack_positions = [value.find(a) for a in aliases if a in value]
        ack = bool(ack_positions)
        ack_before = bool(ack_positions and selected_pos is not None and min(ack_positions) < selected_pos)
        components = {"acknowledgment_present": ack, "no_exclamation_mark": "!" not in text,
                      "maximum_two_sentences": sentences <= 2}
        behavioral = ack_before
    else:
        semi = value.count(";")
        emoji = any(0x1F000 <= ord(ch) <= 0x1FAFF for ch in text)
        semi_pos = value.find(";")
        reason_after = semi_pos >= 0 and any(value.find(c, semi_pos + 1) >= 0 for c in selected_cues)
        components = {"exactly_one_semicolon": semi == 1, "no_exclamation_mark": "!" not in text,
                      "no_emoji_proxy": not emoji, "maximum_two_sentences": sentences <= 2}
        behavioral = bool(selected_pos is not None and semi == 1 and selected_pos < semi_pos and reason_after)
    linguistic = int(all(components.values()))
    current = None if selected is None else int(selected == row["preferred_option"])
    history = None if selected is None or row["history_favored_option"] is None else int(
        selected == row["history_favored_option"])
    outdated_applicable = row["history_regime"] == "OUTDATED_CONFLICTING" and row["condition"] in ("C6", "C7")
    outdated = None if not outdated_applicable or selected is None else int(
        selected == row["history_favored_option"] and selected != row["preferred_option"])
    return {"measurement_state": "ASSESSED_IDENTIFIABLE_UNIT", "selected_option": selected or "UNRESOLVED", "option_hits": hits,
            "reason_support_state": reason, "sentence_count": sentences,
            "answer_completeness": complete, "task_success": task,
            "current_preference_choice": current, "history_favored_choice": history,
            "outdated_value_adoption": outdated, "outdated_value_applicable": outdated_applicable,
            "style_target_applicable": bool(row["factors"]["S"]), "style_components": components,
            "operational_linguistic_fidelity": linguistic,
            "operational_behavioral_fidelity": int(behavioral)}


def result(row, response, latency):
    token_audit = b.validate_completion(response, row["input_token_ids"])
    normal = b.normalize_result(response)
    count = response.get("tokens_predicted")
    require(type(count) is int and 0 <= count <= 96, "Generated token count")
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
            "human_semantic_ratings": 0, "evidence_level": "AUTOMATIC_DEVELOPMENT_ONLY"}


def inventory(plan, events):
    attempted, raw, derived = [], {}, {}
    for event in events:
        data = event["data"]
        if event["kind"] == "persona_dialogue_generation_started":
            require(len(attempted) < MAX_ATTEMPTS and data == plan["requests"][len(attempted)],
                    "Repeated, reordered, or unplanned attempt")
            attempted.append(data["request_id"])
        elif event["kind"] == "persona_dialogue_raw_generation":
            rid = data["request_id"]
            require(rid in attempted and rid not in raw, "Unbound/duplicate raw response")
            raw[rid] = data
        elif event["kind"] == "persona_dialogue_result":
            rid = data["request_id"]
            require(rid in raw and rid not in derived, "Unbound/duplicate result")
            derived[rid] = data
    return attempted, raw, derived


def run(preflight_path):
    fresh, stored, plan = preflight(), load(preflight_path), load(FROZEN)
    for key in ("manifest_sha256", "authorization_sha256", "source_hashes", "configuration", "server_command"):
        require(fresh[key] == stored[key], "Preflight binding changed: " + key)
    with b.writer_lock(ROOT):
        require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
                "Existing allocation: no repeat or resume")
        claim = {key: fresh[key] for key in ("manifest_sha256", "authorization_sha256", "source_hashes")}
        claim.update(preflight_sha256=sha256(preflight_path), maximum_attempts=MAX_ATTEMPTS)
        save(ROOT / "claim.json", claim)
        journal = b.RunJournal(ROOT / "runs", {"phase": "P1 synthetic persona-dialogue S/F/H development",
            "evidence_level": "DEVELOPMENT_EXPLORATORY_SYNTHETIC", "claim": claim,
            "frozen_manifest": plan, "authorization": load(AUTH), "configuration": cfg(plan).as_dict(),
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
                journal.write("live_preflight_pass", {"prompts": 48, "completed_inference": 0})
                print(json.dumps({"live_preflight": "PASS", "planned": 48}), flush=True)
                for row in plan["requests"]:
                    remaining = plan["resource_budget"]["batch_wall_seconds_ceiling"] - (time.monotonic() - started)
                    require(remaining > 0,
                            "45-minute limit reached; preserve suffix")
                    server.assert_running()
                    client.timeout = min(180, remaining)
                    active = row["request_id"]
                    journal.write("persona_dialogue_generation_started", row)
                    tick = time.monotonic()
                    response = client.request("/completion", payload(row))
                    latency = time.monotonic() - tick
                    journal.write("persona_dialogue_raw_generation", {"request_id": active,
                                  "response": response, "latency_seconds": latency})
                    derived = result(row, response, latency)
                    journal.write("persona_dialogue_result", derived)
                    print(json.dumps({"order": row["order"], "id": active,
                        "choice": derived["automatic_score"]["selected_option"],
                        "task": derived["automatic_score"]["task_success"],
                        "tokens": derived["generated_tokens"], "stop": derived["stop_reason"],
                        "seconds": round(latency, 2)}), flush=True)
                    active = None
                server.assert_running()
                b.validate_server_properties(client.request("/props"), cfg(plan))
                after = preflight(check_headroom=False)
                require(after["identity"] == fresh["identity"] and after["source_hashes"] == fresh["source_hashes"],
                        "Postflight identity/source changed")
                journal.write("postflight", after)
            status = "PASS"
        except BaseException as exc:
            status = "PARTIAL" if active else "BLOCKED"
            journal.write("failure", {"type": type(exc).__name__, "message": str(exc), "request_id": active})
        events = b.read_events(journal.directory)
        attempted, raw, derived = inventory(plan, events)
        if status == "BLOCKED" and len(derived) == MAX_ATTEMPTS:
            status = "COMPLETE_DATA_POSTFLIGHT_FAILED"
        summary = {"status": status, "attempted": len(attempted), "responses_received": len(raw),
                   "results": len(derived), "inference_wall_seconds": sum(x["latency_seconds"] for x in raw.values()),
                   "batch_wall_seconds": time.monotonic() - started,
                   "run_directory": journal.directory.as_posix(), "retries": 0, "human_semantic_ratings": 0}
        journal.finish(**summary)
        save(journal.directory / "summary.json", summary)
        return summary


def replay():
    plan = load(FROZEN)
    folders = list((ROOT / "runs").glob("*"))
    require(len(folders) == 1, "Unexpected run count")
    folder = folders[0]
    events = b.read_events(folder)
    require(load(folder / "manifest.json")["claim"] == load(ROOT / "claim.json"), "Claim changed")
    attempted, raw, derived = inventory(plan, events)
    require(events and events[-1]["kind"] == "run_finished", "Missing terminal run event")
    require(load(folder / "summary.json") == events[-1]["data"], "Summary/terminal event changed")
    if events[-1]["data"]["status"] == "PASS":
        require(sum(e["kind"] == "postflight" for e in events) == 1, "Successful run lacks postflight")
    live = [e["data"] for e in events if e["kind"] == "live_prompt_verified"]
    require(len(live) == MAX_ATTEMPTS and [x["request_id"] for x in live] ==
            [r["request_id"] for r in plan["requests"]], "Live-token verification incomplete")
    claim = load(ROOT / "claim.json")
    for path, digest in claim["source_hashes"].items():
        snapshot = folder / "source_snapshot" / path
        require(snapshot.is_file() and sha256(snapshot) == digest, "Source snapshot changed: " + path)
    sent = [e["data"]["payload"] for e in events if e["kind"] == "http_request" and
            e["data"]["route"] == "/completion"]
    require(sent == [payload(r) for r in plan["requests"][:len(attempted)]], "Actual payload changed")
    bodies = [json.loads(base64.b64decode(e["data"]["body_base64"])) for e in events
              if e["kind"] == "http_response" and e["data"]["route"] == "/completion" and
              e["data"].get("status") == 200]
    require(bodies == [r["response"] for r in raw.values()], "Raw HTTP response changed")
    rows = []
    for row in plan["requests"]:
        rid = row["request_id"]
        reconstructed = result(row, raw[rid]["response"], raw[rid]["latency_seconds"]) if rid in raw else None
        if rid in derived:
            require(reconstructed == derived[rid], "Derived result changed")
        rows.append((row, reconstructed, "COMPLETED" if rid in derived else
                     "RAW_RECOVERABLE" if rid in raw else "ATTEMPTED_UNRESOLVED" if rid in attempted else "UNATTEMPTED"))
    return folder, events, rows, len(bodies)


def audit():
    plan = load(FROZEN)
    require(load(AUTH)["manifest_sha256"] == sha256(FROZEN), "Manifest/auth changed")
    validate_plan(plan)
    folder, events, rows, bodies = replay()
    public = []
    for row, result_row, state in rows:
        public.append({"request_id": row["request_id"], "request_sha256": row["request_sha256"],
            "case_id": row["case_id"], "condition": row["condition"], "state": state,
            "raw_text_sha256": None if result_row is None else result_row["raw_text_sha256"],
            "first_reply_sha256": None if result_row is None else result_row["first_reply_sha256"],
            "generated_tokens": None if result_row is None else result_row["generated_tokens"],
            "stop_reason": None if result_row is None else result_row["stop_reason"],
            "latency_seconds": None if result_row is None else result_row["latency_seconds"],
            "automatic_score": None if result_row is None else result_row["automatic_score"]})
    return {"version": "p1_persona_dialogue_factorial_integrity_v1", "integrity_status": "PASS",
            "manifest_sha256": sha256(FROZEN), "run_directory": folder.as_posix(),
            "attempted": sum(state != "UNATTEMPTED" for _, _, state in rows),
            "results": sum(state == "COMPLETED" for _, _, state in rows),
            "http_responses_verified": bodies, "journal_events": len(events), "rows": public,
            "raw_text_embedded": False, "new_generations_during_audit": 0}


def mean(values):
    return None if not values else sum(values) / len(values)


def analyze():
    design, plan = load(DESIGN), load(FROZEN)
    folder, events, rows, _ = replay()
    require(all(state == "COMPLETED" for _, _, state in rows), "Complete 48-row run required")
    by_condition = defaultdict(list)
    by_case = defaultdict(dict)
    metrics = ("task_success", "answer_completeness", "current_preference_choice",
               "operational_linguistic_fidelity", "operational_behavioral_fidelity")
    for row, result_row, _ in rows:
        score = result_row["automatic_score"]
        by_condition[row["condition"]].append(score)
        by_case[row["case_id"]][row["condition"]] = score
    condition_summary = {}
    for condition in sorted(by_condition):
        values = by_condition[condition]
        condition_summary[condition] = {metric: {"ones": sum(x[metric] == 1 for x in values),
            "zeros": sum(x[metric] == 0 for x in values), "unresolved": sum(x[metric] is None for x in values),
            "mean_resolved": mean([x[metric] for x in values if x[metric] is not None])} for metric in metrics}
        condition_summary[condition]["choice_distribution"] = dict(Counter(x["selected_option"] for x in values))
        condition_summary[condition]["reason_distribution"] = dict(Counter(x["reason_support_state"] for x in values))
    factorial = {}
    for metric in metrics:
        factorial[metric] = {}
        for contrast, weights in design["estimands"]["factorial_weights"].items():
            points, lower, upper = [], [], []
            for case_id, cells in by_case.items():
                point, low, high, complete = 0.0, 0.0, 0.0, True
                for condition, weight in weights.items():
                    value = cells[condition][metric]
                    if value is None:
                        complete = False
                        low += min(0.0, weight)
                        high += max(0.0, weight)
                    else:
                        point += weight * value
                        low += weight * value
                        high += weight * value
                if complete:
                    points.append(point)
                lower.append(low); upper.append(high)
            factorial[metric][contrast] = {"complete_case_estimate": mean(points),
                "complete_cases": len(points), "logical_lower": mean(lower), "logical_upper": mean(upper),
                "case_contributions": points}
    cases = {c["case_id"]: c for c in design["cases"]}
    regime_h = {}
    pairs = (("C3", "C0"), ("C5", "C1"), ("C6", "C2"), ("C7", "C4"))
    for regime in sorted({c["history_regime"] for c in cases.values()}):
        regime_h[regime] = {}
        ids = [cid for cid, c in cases.items() if c["history_regime"] == regime]
        for metric in ("task_success", "current_preference_choice"):
            values = []
            for cid in ids:
                for on, off in pairs:
                    a, z = by_case[cid][on][metric], by_case[cid][off][metric]
                    if a is not None and z is not None:
                        values.append(a - z)
            regime_h[regime][metric] = {"mean_paired_H_effect": mean(values), "resolved_pairs": len(values),
                                         "pair_contributions": values}
    results_only = [r for _, r, _ in rows]
    memory_events = [e["data"] for e in events if e["kind"] == "memory_observation"]
    peak = max((m.get("process", {}).get("peak_working_set", 0) for m in memory_events), default=0)
    minimum_available = min((m.get("system", {}).get("available_physical") for m in memory_events
                             if m.get("system", {}).get("available_physical") is not None), default=None)
    latency = sum(r["latency_seconds"] for r in results_only)
    generations = len(results_only)
    return {"version": "p1_persona_dialogue_factorial_analysis_v1",
        "evidence_level": "DEVELOPMENT_EXPLORATORY_SYNTHETIC_AUTOMATIC",
        "scientific_scope": design["research"]["purpose"], "manifest_sha256": sha256(FROZEN),
        "run_directory": folder.as_posix(), "generations": generations, "human_ratings": 0,
        "condition_summary": condition_summary, "factorial_estimates": factorial,
        "history_regime_paired_effects": regime_h,
        "outdated_adoption": {"applicable_ones": sum(r["automatic_score"]["outdated_value_applicable"] and
                r["automatic_score"]["outdated_value_adoption"] == 1 for r in results_only),
            "applicable_zeros": sum(r["automatic_score"]["outdated_value_applicable"] and
                r["automatic_score"]["outdated_value_adoption"] == 0 for r in results_only),
            "applicable_unresolved": sum(r["automatic_score"]["outdated_value_applicable"] and
                r["automatic_score"]["outdated_value_adoption"] is None for r in results_only),
            "not_applicable": sum(not r["automatic_score"]["outdated_value_applicable"] for r in results_only)},
        "resource_observations": {"generated_tokens": sum(r["generated_tokens"] for r in results_only),
            "completion_inference_seconds": latency, "peak_server_working_set_bytes": peak,
            "minimum_observed_available_physical_bytes": minimum_available},
        "cumulative_authorization_after": {"generations_used": 16 + generations,
            "generations_limit": 1200, "inference_seconds_used": 159.95704690001094 + latency,
            "inference_seconds_limit": 72000.0},
        "limits": design["known_limitations"] + [
            "Independent synthetic validation was frozen before these outputs but has not been executed or authorized.",
            "No broad relevance, coherence, human Persona Fidelity, real-speaker, causal internal-mechanism, or novelty claim is supported."],
        "new_generations_during_analysis": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
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
    shown = {k: v for k, v in value.items() if k not in ("rows", "identity", "source_hashes", "memory_before_run",
                                                           "condition_summary", "factorial_estimates")}
    print(json.dumps(shown, indent=2))
    if value.get("status") in ("PARTIAL", "BLOCKED", "COMPLETE_DATA_POSTFLIGHT_FAILED"):
        raise SystemExit(2)
