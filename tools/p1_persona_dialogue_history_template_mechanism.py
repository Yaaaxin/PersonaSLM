"""One-shot adapter for the frozen 30-request history-template mechanism study.

This module reuses the existing PersonaSLM native-tokenizer, llama.cpp server,
append-only journal, response-boundary, and paired-bound infrastructure.  Merely
importing it or validating the design performs no tokenization or inference.
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

import p1_persona_dialogue_independent_replication as base


s, b = base.s, base.b
load, sha256, th, require = s.load, s.sha256, s.th, s.require
write_exclusive = base.write_exclusive

OUT = Path("docs/validation/p1/persona_dialogue_history_template_mechanism_v1")
DESIGN = OUT / "prospective_design_v1.json"
CASE_BANK = OUT / "case_bank_v1.json"
AUTHORIZATION = OUT / "execution_authorization_v1.json"
FROZEN = OUT / "frozen_manifest_v1.json"
PREFLIGHT = OUT / "preflight_v1.json"
AUDIT = OUT / "execution_audit_v1.json"
ANALYSIS = OUT / "analysis_v1.json"
ROOT = Path("results/p1_persona_dialogue_history_template_mechanism/v1")
TEST_SOURCE = Path("tests/test_p1_persona_dialogue_history_template_mechanism.py")

DESIGN_SHA = "dcc70c37a19e7fa26de491d3d4311dc7b4573a78b1033d345b5b31c2db27d619"
CASE_BANK_SHA = "f471a2a3cf54f2c3e72d83437822a16b6732fa4f03d98a62ad18e53e2d5bc98d"
MAX_ATTEMPTS = 30
GENERATION_BASELINE = 202
INFERENCE_BASELINE = 1187.2563158999974
ARMS = (
    "SF_NO_H",
    "SFH_RAW_NATIVE",
    "SFH_SURFACE_NEUTRAL",
    "SFH_CURRENT_RESTATEMENT",
    "SFH_FORMAT_REMINDER",
)
METRICS = (
    "current_target_selection",
    "historical_target_intrusion",
    "history_template_copy",
    "strict_format_adherence",
    "current_preference_task_success",
    "surface_style_uptake",
)
STARTED = "history_template_generation_started"
RAW = "history_template_raw_generation"
DERIVED = "history_template_result"


def cfg(plan):
    model = plan["model"]
    return s.Runtime(model["model_file"], model["model_sha256"],
                     model["backend_file"], model_label=model["model_label"])


def _binding_paths(design):
    bindings = design["bindings"]
    paths = [Path(bindings[key]["path"]) for key in (
        "completed_replication_audit", "completed_replication_analysis",
        "response_status", "runner_infrastructure_reused",
        "tokenizer_identity_source")]
    paths.extend(Path(item["path"])
                 for item in bindings["prior_material_sources_for_disjointness"])
    return paths


def source_hashes():
    design = load(DESIGN)
    paths = list(Path("src/personaslm").glob("*.py")) + [
        Path(__file__), TEST_SOURCE, DESIGN, CASE_BANK,
        Path("tools/p1_persona_dialogue_independent_replication.py"),
        Path("tools/p1_persona_dialogue_mechanism_analysis_v2.py"),
        Path("tools/p1_persona_dialogue_factorial.py"),
        *_binding_paths(design),
    ]
    root = Path.cwd().resolve()
    unique = {path.resolve(): path for path in paths}
    return {path.relative_to(root).as_posix(): sha256(path)
            for path in sorted(unique, key=lambda value: value.as_posix())}


def construction(design, bank, case, arm_name):
    require(arm_name in ARMS, "Unknown frozen arm")
    arm = design["arms"][arm_name]
    persona = bank["personas"][case["persona_id"]]
    policy = design["prompt_policy"]
    system = (policy["fixed_system_instruction"] + "\n\nSYNTHETIC SPEAKER: " +
              persona["speaker_name"] + "\n\n" + case["fixed_current_notes"] +
              "\n\n" + persona["S_block"] + "\n\n" + persona["F_block"])
    messages = [{"role": "system", "content": system}]
    if arm["H"]:
        assistant = (case["history_assistant_surface_neutral"]
                     if arm_name == "SFH_SURFACE_NEUTRAL"
                     else case["history_assistant_raw"])
        messages.extend((
            {"role": "user", "content": case["history_user"]},
            {"role": "assistant", "content": assistant},
        ))
    final_user = case["fixed_current_user"]
    if arm_name == "SFH_CURRENT_RESTATEMENT":
        final_user = ("CURRENT RESTATEMENT AFTER THE ARCHIVE:\n" + persona["F_block"] +
                      "\n" + case["fixed_current_notes"] + "\n\n" + final_user)
    elif arm_name == "SFH_FORMAT_REMINDER":
        final_user = policy["format_only_reminder"] + "\n\n" + final_user
    messages.append({"role": "user", "content": final_user})
    factors = {key: arm[key] for key in ("S", "F", "H")}
    return factors, arm["history_frame"], arm["post_history_intervention"], messages


def selection_category(row, text):
    sentences = base._sentences(text)
    if not sentences:
        return {"category": "NONE", "selected_target": None, "selected_option": None,
                "mentioned_current_options": [], "mentioned_history_targets": [],
                "first_sentence": None}
    first = base._normalized(sentences[0])
    current_mentions = [option for option in ("A", "B")
                        if base._exact_contains(sentences[0],
                                                row["options"][option]["canonical"])]
    history_mentions = [target for target in row["history_target_strings"]
                        if base._exact_contains(sentences[0], target)]
    if len(current_mentions) + len(history_mentions) > 1:
        return {"category": "MULTIPLE", "selected_target": None,
                "selected_option": None,
                "mentioned_current_options": current_mentions,
                "mentioned_history_targets": history_mentions,
                "first_sentence": sentences[0]}
    for option in ("A", "B"):
        target = row["options"][option]["canonical"]
        forms = (f"I recommend {target}.", f"I recommend the {target}.",
                 f"I recommend Option {option} — {target}.")
        if current_mentions == [option] and any(
                first == base._normalized(form) for form in forms):
            category = ("CURRENT_PREFERRED" if option == row["preferred_option"]
                        else "CURRENT_NONPREFERRED")
            return {"category": category, "selected_target": target,
                    "selected_option": option,
                    "mentioned_current_options": current_mentions,
                    "mentioned_history_targets": history_mentions,
                    "first_sentence": sentences[0]}
    for target in row["history_target_strings"]:
        forms = (f"I recommend {target}.", f"I recommend the {target}.")
        if history_mentions == [target] and any(
                first == base._normalized(form) for form in forms):
            return {"category": "HISTORY_TARGET", "selected_target": target,
                    "selected_option": None,
                    "mentioned_current_options": current_mentions,
                    "mentioned_history_targets": history_mentions,
                    "first_sentence": sentences[0]}
    return {"category": "NONE", "selected_target": None, "selected_option": None,
            "mentioned_current_options": current_mentions,
            "mentioned_history_targets": history_mentions,
            "first_sentence": sentences[0]}


def automatic_score(row, persona, text, assessable=True):
    if not assessable:
        return {"measurement_state": "BOUNDARY_CENSORED",
                "selection_category": "BOUNDARY_CENSORED",
                "selected_target": None, "selected_option": None,
                "mentioned_current_options": None, "mentioned_history_targets": None,
                "full_reply_history_targets": None,
                "current_target_selection": None,
                "historical_target_intrusion": None,
                "history_template_copy": None,
                "strict_format_adherence": None,
                "current_preference_task_success": None,
                "exact_current_reason_support": None,
                **base.style_score(persona, text, False)}
    parsed = selection_category(row, text)
    category, target, option = (parsed["category"], parsed["selected_target"],
                                parsed["selected_option"])
    sentences = base._sentences(text)
    current = category in ("CURRENT_PREFERRED", "CURRENT_NONPREFERRED")
    first = base._normalized(sentences[0]) if sentences else ""
    strict_option = next((candidate for candidate in ("A", "B")
                          if first == base._normalized(
                              f"I recommend {row['options'][candidate]['canonical']}.")
                          ), None)
    forbidden = list(row["history_target_strings"])
    if strict_option is not None:
        forbidden.append(row["options"]["B" if strict_option == "A" else "A"]["canonical"])
    strict = int(strict_option is not None and len(sentences) == 2 and
                 not any(base._exact_contains(text, value) for value in forbidden))
    reason_support = False
    if current and len(sentences) >= 2:
        other = "B" if option == "A" else "A"
        chosen_cue = any(base._exact_contains(sentences[1], cue)
                         for cue in row["options"][option]["reason_cues"])
        other_cue = any(base._exact_contains(sentences[1], cue)
                        for cue in row["options"][other]["reason_cues"])
        reason_support = chosen_cue and not other_cue
    task_success = int(strict == 1 and option == row["preferred_option"] and reason_support)
    current_selection = int(current)
    full_reply_history_targets = [target for target in row["history_target_strings"]
                                  if base._exact_contains(text, target)]
    historical_intrusion = int(bool(full_reply_history_targets))
    template_copy = int(first.startswith("i recommend the "))
    return {"measurement_state": "ASSESSED_IDENTIFIABLE_UNIT",
            "selection_category": category, "selected_target": target,
            "selected_option": option,
            "mentioned_current_options": parsed["mentioned_current_options"],
            "mentioned_history_targets": parsed["mentioned_history_targets"],
            "full_reply_history_targets": full_reply_history_targets,
            "current_target_selection": current_selection,
            "historical_target_intrusion": historical_intrusion,
            "history_template_copy": template_copy,
            "strict_format_adherence": strict,
            "current_preference_task_success": task_success,
            "exact_current_reason_support": int(reason_support) if current else None,
            **base.style_score(persona, text, True)}


def validate_design(design=None, bank=None, require_unstarted=False):
    require(sha256(DESIGN) == DESIGN_SHA, "Prospective design changed")
    require(sha256(CASE_BANK) == CASE_BANK_SHA, "Case bank changed")
    design, bank = design or load(DESIGN), bank or load(CASE_BANK)
    require(design["status"] ==
            "FROZEN_CANDIDATE_PROSPECTIVE_DESIGN_NOT_AUTHORIZED_NOT_TOKENIZED_NOT_EXECUTED",
            "Design status")
    require(bank["status"] ==
            "FROZEN_CANDIDATE_PROSPECTIVE_SYNTHETIC_MATERIALS_NO_TOKENIZATION_NO_OUTPUTS",
            "Case-bank status")
    require(design["bindings"]["case_bank"] ==
            {"path": CASE_BANK.as_posix(), "sha256": CASE_BANK_SHA}, "Case binding")
    require(subprocess.check_output(["git", "branch", "--show-current"],
                                    text=True).strip() ==
            design["bindings"]["source_branch"], "Source branch changed")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() ==
            design["bindings"]["source_head"], "Source HEAD changed")
    for key, binding in design["bindings"].items():
        if isinstance(binding, dict) and set(binding) >= {"path", "sha256"}:
            require(sha256(Path(binding["path"])) == binding["sha256"],
                    "Bound source changed: " + key)
    for binding in design["bindings"]["prior_material_sources_for_disjointness"]:
        require(sha256(Path(binding["path"])) == binding["sha256"],
                "Prior material changed: " + binding["path"])
    require(design["research"]["evidence_level"] == "DEVELOPMENT_MECHANISM",
            "Evidence level")
    require(design["authorization"]["execution_authorized"] is False and
            design["authorization"]["tokenization_authorized"] is False and
            design["authorization"]["preflight_authorized"] is False and
            design["authorization"]["maximum_native_tokenizer_calls"] ==
            MAX_ATTEMPTS and
            design["authorization"]["maximum_live_server_tokenizer_checks"] ==
            MAX_ATTEMPTS and
            design["authorization"]["maximum_tokenizer_operations_total"] ==
            2 * MAX_ATTEMPTS and
            design["authorization"]["maximum_generation_attempts_if_authorized"] ==
            MAX_ATTEMPTS and design["authorization"]["retries"] == 0 and
            design["authorization"]["hidden_warmups"] == 0,
            "Prospective authorization boundary")
    require(tuple(design["arms"]) == ARMS, "Arm order changed")
    require(all(design["arms"][arm]["S"] == design["arms"][arm]["F"] == 1
                for arm in ARMS), "S/F not fixed")
    require(design["arms"]["SF_NO_H"]["H"] == 0 and
            all(design["arms"][arm]["H"] == 1 for arm in ARMS[1:]), "H arms")
    runtime = design["runtime"]
    expected_runtime = {"threads": 4, "threads_batch": 4, "context_tokens": 4096,
        "gpu_layers": 0, "max_new_tokens": 96, "temperature": 0.0, "top_p": 1.0,
        "seed": 42, "stop": [], "ignore_eos": False, "cache_prompt": False,
        "warmup": False, "parallel": 1, "no_context_shift": True}
    require(all(runtime[key] == value for key, value in expected_runtime.items()),
            "Runtime changed")
    budget = design["resource_budget"]
    require(budget["requests"] == MAX_ATTEMPTS and
            budget["maximum_generated_tokens"] == MAX_ATTEMPTS * 96 and
            budget["minimum_available_physical_ram_bytes"] == 3 * 1024 ** 3 and
            budget["minimum_free_output_disk_bytes"] == 1024 ** 3 and
            budget["actual_completion_inference_seconds_ceiling"] == 1800.0 and
            budget["batch_wall_seconds_ceiling"] == 2700.0, "Resource budget")
    baseline = load(Path(design["bindings"]["completed_replication_analysis"]["path"]))[
        "cumulative_authorization_after"]
    require(baseline["generations_used"] == GENERATION_BASELINE and
            baseline["inference_seconds_used"] == INFERENCE_BASELINE and
            budget["global_baseline"]["generations_used"] == GENERATION_BASELINE and
            budget["global_baseline"]["inference_wall_seconds_used"] == INFERENCE_BASELINE,
            "Cumulative baseline")
    personas = bank["personas"]
    cases = {case["case_id"]: case for case in bank["cases"]}
    require(len(personas) == len(cases) == 6 and
            Counter(case["persona_id"] for case in cases.values()) ==
            Counter({persona_id: 1 for persona_id in personas}), "One persona per case")
    require(Counter(case["history_regime"] for case in cases.values()) ==
            Counter({"ALIGNED_HELPFUL": 2, "OUTDATED_CONFLICTING": 2,
                     "IRRELEVANT": 2}), "Regime allocation")
    for regime in ("ALIGNED_HELPFUL", "OUTDATED_CONFLICTING", "IRRELEVANT"):
        require(Counter(case["preferred_option"] for case in cases.values()
                        if case["history_regime"] == regime) == Counter({"A": 1, "B": 1}),
                "Within-regime A/B balance")
    rows = design["order"]["requests"]
    require(len(rows) == len({row["request_id"] for row in rows}) == MAX_ATTEMPTS and
            [row["order"] for row in rows] == list(range(MAX_ATTEMPTS)), "Frozen order")
    require(Counter(row["arm"] for row in rows) == Counter({arm: 6 for arm in ARMS}),
            "Arm allocation")
    arm_orders = {arm: [row["order"] for row in rows if row["arm"] == arm]
                  for arm in ARMS}
    require(all(sum(orders) == 87 and len(orders) == 6 for orders in arm_orders.values()) and
            design["order"]["arm_order_balance"] == {
                arm: {"orders": orders, "sum": 87, "mean": 14.5}
                for arm, orders in arm_orders.items()}, "Arm order balance")
    for case_id in cases:
        require(Counter(row["arm"] for row in rows if row["case_id"] == case_id) ==
                Counter({arm: 1 for arm in ARMS}), "Incomplete within-case pairing")
    prior_strings = set()
    for binding in design["bindings"]["prior_material_sources_for_disjointness"]:
        prior_strings.update(base._strings(load(Path(binding["path"]))))
    family = bank["template_ancestry"]["family_id"]
    new_materials = [design["prompt_policy"]["fixed_system_instruction"],
                     design["prompt_policy"]["format_only_reminder"], family]
    for persona_id, persona in personas.items():
        require(persona["synthetic"] is True and
                len(persona["operational_style_checks"]) == 5, "Persona material")
        new_materials.extend((persona_id, persona["speaker_name"], persona["profile_source_id"],
                              persona["S_block"], persona["F_block"]))
    for case in cases.values():
        require(set(case["options"]) == {"A", "B"} and
                case["history_selected_target"] in case["history_target_strings"],
                "Case targets")
        current = case["fixed_current_notes"] + "\n" + case["fixed_current_user"]
        history = (case["history_user"] + "\n" + case["history_assistant_raw"] + "\n" +
                   case["history_assistant_surface_neutral"])
        require(all(not base._exact_contains(history, case["options"][side]["canonical"])
                    for side in ("A", "B")), "Current option leaks into history")
        require(all(not base._exact_contains(current, target)
                    for target in case["history_target_strings"]),
                "History target leaks into current material")
        raw = case["history_assistant_raw"].split(". ", 1)
        reframed = case["history_assistant_surface_neutral"].split(". ", 1)
        require(len(raw) == len(reframed) == 2 and raw[1] == reframed[1] and
                raw[0] + "." == f"I recommend the {case['history_selected_target']}." and
                reframed[0] + "." == f"{case['history_selected_target']} was my choice.",
                "Surface-reframed arm changes more than the first sentence")
        new_materials.extend((case["case_id"], case["fixed_current_notes"],
            case["fixed_current_user"], case["history_user"],
            case["history_assistant_raw"], case["history_assistant_surface_neutral"],
            *case["history_target_strings"],
            *(case["options"][side]["canonical"] for side in ("A", "B"))))
        built = {arm: construction(design, bank, case, arm)[3] for arm in ARMS}
        require(len(built["SF_NO_H"]) == 2 and
                all(len(built[arm]) == 4 for arm in ARMS[1:]), "Native role structure")
        raw_messages = built["SFH_RAW_NATIVE"]
        surface_messages = built["SFH_SURFACE_NEUTRAL"]
        require(raw_messages[0] == surface_messages[0] and
                raw_messages[1] == surface_messages[1] and
                raw_messages[3] == surface_messages[3] and
                raw_messages[2]["role"] == surface_messages[2]["role"] == "assistant" and
                raw_messages[2]["content"].split(". ", 1)[1] ==
                surface_messages[2]["content"].split(". ", 1)[1],
                "Surface arm invariant")
        require(built["SFH_CURRENT_RESTATEMENT"][:3] == raw_messages[:3] and
                built["SFH_FORMAT_REMINDER"][:3] == raw_messages[:3],
                "Post-history baselines changed native history")
        reminder = design["prompt_policy"]["format_only_reminder"]
        forbidden = [persona["F_block"], case["fixed_current_notes"],
                     *case["history_target_strings"],
                     *(case["options"][side]["canonical"] for side in ("A", "B"))]
        require(not any(value in reminder for value in forbidden),
                "Format reminder contains case content")
    require(all(value not in prior_strings for value in new_materials),
            "New persona/case material overlaps a prior bound source")
    require(family == design["bindings"]["task_template_ancestry"]["family_id"] and
            family not in prior_strings and
            bank["template_ancestry"]["parent_case_or_template_id"] is None,
            "Template ancestry not disjoint")
    probes = 0
    for case in cases.values():
        persona = personas[case["persona_id"]]
        prefix = next(item["value"] for item in persona["operational_style_checks"]
                      if item["check_id"] == "second_sentence_prefix")
        suffix = next(item["value"] for item in persona["operational_style_checks"]
                      if item["check_id"] == "second_sentence_suffix")
        for target in [case["options"][side]["canonical"] for side in ("A", "B")] + \
                case["history_target_strings"]:
            probe = f"I recommend {target}. {prefix} the documented detail, {suffix}"
            status = b.classify_response(probe, {"stop_type": "eos", "stop": True,
                                                   "truncated": False}, declared_stops=())
            require(status["unit_identifiable"] and
                    "unrecognized_line_label" not in status["reasons"],
                    "Boundary probe")
            probes += 1
    if require_unstarted:
        require(not AUTHORIZATION.exists() and not FROZEN.exists() and not PREFLIGHT.exists() and
                not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
                "Study already initialized")
    return {"personas": 6, "cases": 6, "arms": 5, "requests": MAX_ATTEMPTS,
            "boundary_parser_probes": probes,
            "material_disjointness_sources": len(
                design["bindings"]["prior_material_sources_for_disjointness"])}


def authorization_requirements():
    checks = validate_design()
    design = load(DESIGN)
    return {"schema_version": "personaslm_history_template_execution_authorization_v1",
        "status": "AUTHORIZED_BEFORE_TOKENIZATION_PREFLIGHT_OR_MODEL_EXECUTION",
        "authorization_path": AUTHORIZATION.as_posix(),
        "implementation": {"runner": {"path": Path(__file__).resolve().relative_to(
            Path.cwd().resolve()).as_posix(),
            "sha256": sha256(Path(__file__))},
            "test": {"path": TEST_SOURCE.as_posix(), "sha256": sha256(TEST_SOURCE)}},
        "source_hashes": source_hashes(),
        "design": {"path": DESIGN.as_posix(), "sha256": DESIGN_SHA},
        "case_bank": {"path": CASE_BANK.as_posix(), "sha256": CASE_BANK_SHA},
        "model_sha256": design["model"]["artifact_sha256"],
        "backend_sha256": design["runtime"]["backend_sha256"],
        "template_sha256": design["runtime"]["chat_template_sha256"],
        "maximum_native_tokenizer_calls": MAX_ATTEMPTS,
        "maximum_live_server_tokenizer_checks": MAX_ATTEMPTS,
        "maximum_tokenizer_operations_total": 2 * MAX_ATTEMPTS,
        "maximum_generation_attempts": MAX_ATTEMPTS, "retries": 0,
        "hidden_warmups": 0, "minimum_available_physical_ram_bytes": 3 * 1024 ** 3,
        "minimum_free_output_disk_bytes": 1024 ** 3,
        "actual_completion_inference_seconds_ceiling": 1800.0,
        "batch_wall_seconds_ceiling": 2700.0,
        "global_baseline": copy.deepcopy(design["resource_budget"]["global_baseline"]),
        "results_root": ROOT.as_posix(), "validated_design": checks}


def validate_authorization(path=AUTHORIZATION):
    authorization = load(path)
    required = authorization_requirements()
    for key, expected in required.items():
        require(authorization.get(key) == expected, "Authorization changed: " + key)
    require(authorization.get("researcher") == "Yaxin ZHENG" and
            isinstance(authorization.get("authorized_utc"), str),
            "Researcher authorization missing")
    return authorization


def register(authorization_path):
    """Freeze prompts and native token IDs; makes zero completion calls."""
    require(not FROZEN.exists() and not PREFLIGHT.exists() and
            not (ROOT / "native_tokenizer").exists() and
            not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
            "Registration evidence exists; do not replace")
    authorization_path = Path(authorization_path)
    require(authorization_path.resolve() == AUTHORIZATION.resolve(),
            "Official authorization path required")
    authorization = validate_authorization(authorization_path)
    design, bank = load(DESIGN), load(CASE_BANK)
    checks = validate_design(design, bank)
    model, runtime = design["model"], design["runtime"]
    require(sha256(Path(model["artifact_path"])) == model["artifact_sha256"] and
            sha256(Path(runtime["backend_path"])) == runtime["backend_sha256"] and
            sha256(Path(runtime["chat_template_path"])) ==
            runtime["chat_template_sha256"], "Model/runtime artifact changed")
    require(s.memory_observation(os.getpid()).get("system", {}).get(
        "available_physical", 0) >= 3 * 1024 ** 3, "Less than 3 GiB available RAM")
    require(shutil.disk_usage(".").free >= 1024 ** 3, "Less than 1 GiB free disk")
    native_source = load(Path(design["bindings"]["tokenizer_identity_source"]["path"]))[
        "native_tokenizer_identity"]
    tokenizer = Path(runtime["backend_path"]).with_name("llama-tokenize.exe")
    require(sha256(tokenizer) == native_source["tokenizer_sha256"] and
            {path.name: sha256(path) for path in tokenizer.parent.glob("*.dll")} ==
            native_source["dll_hashes"], "Native tokenizer identity changed")
    template = Path(runtime["chat_template_path"]).read_text(encoding="utf-8")
    cases = {case["case_id"]: case for case in bank["cases"]}
    rows, logs = [], []
    for item in design["order"]["requests"]:
        case = cases[item["case_id"]]
        factors, frame, intervention, messages = construction(
            design, bank, case, item["arm"])
        prompt = s.render(template, messages)
        argv = [str(tokenizer.resolve()), "-m", str(Path(model["artifact_path"]).resolve()),
                "--stdin", "--ids", "--offline"]
        started = b.utc_now()
        completed = subprocess.run(argv, input=prompt.encode("utf-8"), capture_output=True,
            timeout=90, env={key: value for key, value in os.environ.items()
                             if not key.upper().startswith("LLAMA_ARG_")},
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        require(completed.returncode == 0, "Native tokenizer failed")
        token_ids = ast.literal_eval(completed.stdout.decode("utf-8", "replace").strip())
        require(isinstance(token_ids, list) and token_ids and
                all(type(value) is int and value >= 0 for value in token_ids), "Token IDs")
        log = {"started_utc": started, "finished_utc": b.utc_now(), "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout.decode("utf-8", "replace"),
            "stderr": completed.stderr.decode("utf-8", "replace"),
            "prompt_sha256": th(prompt), "generation_requests": 0}
        log_path = ROOT / "native_tokenizer" / f"{item['order']:04d}.json"
        write_exclusive(log_path, log)
        logs.append({"path": log_path.as_posix(), "sha256": sha256(log_path)})
        row = {**item, "persona_id": case["persona_id"],
            "history_regime": case["history_regime"], "factors": factors,
            "history_frame": frame, "post_history_intervention": intervention,
            "messages": messages, "prompt": prompt, "prompt_sha256": th(prompt),
            "input_token_ids": token_ids, "input_tokens": len(token_ids),
            "input_token_ids_sha256": th(str(token_ids)),
            "preferred_option": case["preferred_option"],
            "history_favored_option": case["history_favored_option"],
            "options": case["options"],
            "history_target_strings": case["history_target_strings"],
            "history_selected_target": case["history_selected_target"],
            "metric_applicability": case["metric_applicability"],
            "max_new_tokens": 96, "seed": 42, "temperature": 0.0, "top_p": 1.0,
            "stop": [], "cache_prompt": False, "ignore_eos": False}
        require(len(token_ids) + 96 <= runtime["context_tokens"], "Context overflow")
        row["request_sha256"] = th(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                                separators=(",", ":")))
        rows.append(row)
    plan = {"version": "p1_history_template_mechanism_manifest_v1",
        "evidence_level": "DEVELOPMENT_MECHANISM", "design_path": DESIGN.as_posix(),
        "design_sha256": DESIGN_SHA, "case_bank_path": CASE_BANK.as_posix(),
        "case_bank_sha256": CASE_BANK_SHA, "authorization_path": authorization_path.as_posix(),
        "authorization_sha256": sha256(authorization_path),
        "model": {"model_label": model["label"], "model_file": model["artifact_path"],
            "model_sha256": model["artifact_sha256"],
            "backend_file": runtime["backend_path"],
            "backend_sha256": runtime["backend_sha256"],
            "quantization": model["quantization"],
            "artifact_revision": model["artifact_revision"],
            "intended_upstream_revision": model["intended_upstream_revision"],
            "conversion_lineage": model["conversion_lineage"]},
        "template_path": runtime["chat_template_path"],
        "template_sha256": runtime["chat_template_sha256"], "runtime": runtime,
        "resource_budget": design["resource_budget"], "requests": rows,
        "native_tokenizer_identity": {"path": tokenizer.as_posix(),
            "tokenizer_sha256": native_source["tokenizer_sha256"],
            "dll_hashes": native_source["dll_hashes"]},
        "native_tokenizer_logs": logs, "registration_source_hashes": source_hashes(),
        "registered_utc": b.utc_now(), "new_model_generations": 0}
    require(authorization["maximum_generation_attempts"] == len(rows) == MAX_ATTEMPTS,
            "Authorization row count")
    write_exclusive(FROZEN, plan)
    validate_plan(load(FROZEN))
    return {"status": "REGISTERED_NO_GENERATIONS", "manifest_sha256": sha256(FROZEN),
            "authorization_sha256": sha256(authorization_path),
            "native_tokenizer_calls": len(rows), "live_server_tokenizer_checks": 0,
            "tokenizer_operations_total": len(rows), "generation_requests": 0, **checks}


def validate_plan(plan):
    require(plan["version"] == "p1_history_template_mechanism_manifest_v1" and
            plan["design_sha256"] == DESIGN_SHA and
            plan["case_bank_sha256"] == CASE_BANK_SHA, "Manifest binding")
    validate_authorization(Path(plan["authorization_path"]))
    require(plan["authorization_sha256"] == sha256(Path(plan["authorization_path"])) and
            plan["registration_source_hashes"] == source_hashes(), "Registered source changed")
    design, bank = load(DESIGN), load(CASE_BANK)
    checks = validate_design(design, bank)
    model = design["model"]
    expected_model = {"model_label": model["label"],
        "model_file": model["artifact_path"], "model_sha256": model["artifact_sha256"],
        "backend_file": design["runtime"]["backend_path"],
        "backend_sha256": design["runtime"]["backend_sha256"],
        "quantization": model["quantization"],
        "artifact_revision": model["artifact_revision"],
        "intended_upstream_revision": model["intended_upstream_revision"],
        "conversion_lineage": model["conversion_lineage"]}
    require(plan["model"] == expected_model and plan["runtime"] == design["runtime"] and
            plan["resource_budget"] == design["resource_budget"] and
            plan["new_model_generations"] == 0, "Frozen plan changed")
    require(plan["template_sha256"] == sha256(Path(plan["template_path"])),
            "Template changed")
    cases = {case["case_id"]: case for case in bank["cases"]}
    template = Path(plan["template_path"]).read_text(encoding="utf-8")
    require(len(plan["requests"]) == len(plan["native_tokenizer_logs"]) == MAX_ATTEMPTS,
            "Frozen row count")
    for item, row, record in zip(design["order"]["requests"], plan["requests"],
                                 plan["native_tokenizer_logs"]):
        require(all(row[key] == item[key] for key in ("order", "request_id", "case_id", "arm")),
                "Request order changed")
        case = cases[row["case_id"]]
        factors, frame, intervention, messages = construction(design, bank, case, row["arm"])
        require(row["factors"] == factors and row["history_frame"] == frame and
                row["post_history_intervention"] == intervention and
                row["messages"] == messages and row["prompt"] == s.render(template, messages),
                "Prompt changed")
        expected_metadata = {"persona_id": case["persona_id"],
            "history_regime": case["history_regime"],
            "preferred_option": case["preferred_option"],
            "history_favored_option": case["history_favored_option"],
            "options": case["options"],
            "history_target_strings": case["history_target_strings"],
            "history_selected_target": case["history_selected_target"],
            "metric_applicability": case["metric_applicability"],
            "max_new_tokens": 96, "seed": 42, "temperature": 0.0, "top_p": 1.0,
            "stop": [], "cache_prompt": False, "ignore_eos": False}
        require(all(row[key] == value for key, value in expected_metadata.items()),
                "Scoring or generation metadata changed")
        require(row["prompt_sha256"] == th(row["prompt"]) and
                row["input_token_ids_sha256"] == th(str(row["input_token_ids"])) and
                row["input_tokens"] == len(row["input_token_ids"]), "Token binding")
        require(row["request_sha256"] == th(json.dumps(
            {key: value for key, value in row.items() if key != "request_sha256"},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"))), "Request hash")
        path = Path(record["path"])
        token_log = load(path)
        require(sha256(path) == record["sha256"] and token_log["returncode"] == 0 and
                token_log["generation_requests"] == 0 and
                token_log["prompt_sha256"] == row["prompt_sha256"] and
                ast.literal_eval(token_log["stdout"].strip()) == row["input_token_ids"],
                "Tokenizer evidence changed")
    return {**checks, "input_token_range": [
        min(row["input_tokens"] for row in plan["requests"]),
        max(row["input_tokens"] for row in plan["requests"])]}


def preflight(check_headroom=True, require_unused=True):
    plan = load(FROZEN)
    checks = validate_plan(plan)
    authorization = validate_authorization(Path(plan["authorization_path"]))
    identity = b.file_preflight(cfg(plan))
    require(identity["status"] == "PASS" and
            identity["model"]["sha256"] == plan["model"]["model_sha256"] and
            identity["server"]["sha256"] == plan["model"]["backend_sha256"],
            "Model/backend identity")
    native = plan["native_tokenizer_identity"]
    tokenizer = Path(native["path"])
    require(sha256(tokenizer) == native["tokenizer_sha256"] and
            {path.name: sha256(path) for path in tokenizer.parent.glob("*.dll")} ==
            native["dll_hashes"], "Tokenizer identity")
    baseline = load(Path(load(DESIGN)["bindings"]["completed_replication_analysis"]["path"]))[
        "cumulative_authorization_after"]
    require(baseline["generations_used"] == GENERATION_BASELINE and
            baseline["inference_seconds_used"] == INFERENCE_BASELINE and
            baseline["generations_limit"] - GENERATION_BASELINE >= MAX_ATTEMPTS and
            baseline["inference_seconds_limit"] - INFERENCE_BASELINE >= 1800.0,
            "Cumulative budget")
    if require_unused:
        require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
                "Existing allocation: no repeat")
    memory = s.memory_observation(os.getpid())
    if check_headroom:
        require(memory.get("system", {}).get("available_physical", 0) >= 3 * 1024 ** 3,
                "Less than 3 GiB available RAM")
    require(shutil.disk_usage(".").free >= 1024 ** 3, "Output disk reserve")
    return {"status": "PASS", "checked_utc": b.utc_now(), "checks": checks,
        "identity": identity, "manifest_sha256": sha256(FROZEN),
        "authorization_sha256": sha256(Path(plan["authorization_path"])),
        "design_sha256": DESIGN_SHA, "case_bank_sha256": CASE_BANK_SHA,
        "source_hashes": source_hashes(), "configuration": cfg(plan).as_dict(),
        "server_command": s.command(plan), "memory_before_run": memory,
        "cumulative_baseline": baseline,
        "live_gate": "All 30 parse_special=true token arrays must match before completion 1.",
        "authorization": {"researcher": authorization["researcher"],
                          "maximum_native_tokenizer_calls": MAX_ATTEMPTS,
                          "maximum_live_server_tokenizer_checks": MAX_ATTEMPTS,
                          "maximum_tokenizer_operations_total": 2 * MAX_ATTEMPTS,
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
        observed = {name: sha256(path) if path.is_file() else None for name, path in (
            ("design", DESIGN), ("case_bank", CASE_BANK), ("authorization", AUTHORIZATION),
            ("manifest", FROZEN))}
        return {"status": "FAIL", "checked_utc": b.utc_now(),
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "expected_bindings": {"design_sha256": DESIGN_SHA,
                                  "case_bank_sha256": CASE_BANK_SHA},
            "observed_sha256": observed, "memory_observation": memory,
            "free_output_disk_bytes": disk_free,
            "minimum_available_physical_ram_bytes": 3 * 1024 ** 3,
            "minimum_free_output_disk_bytes": 1024 ** 3,
            "model_server_launches": 0, "completion_calls": 0,
            "new_model_generations": 0}


def payload(row):
    return {"prompt": row["input_token_ids"], "n_predict": row["max_new_tokens"],
        "temperature": row["temperature"], "top_p": row["top_p"], "seed": row["seed"],
        "cache_prompt": False, "stop": [], "ignore_eos": False,
        "return_tokens": True, "stream": False}


def result(row, persona, response, latency):
    token_audit = b.validate_completion(response, row["input_token_ids"])
    normal = b.normalize_result(response)
    count = response.get("tokens_predicted")
    require(type(count) is int and 0 <= count <= row["max_new_tokens"],
            "Generated token count")
    returned = (len(normal["generated_token_ids"])
                if normal["generated_token_ids"] is not None else None)
    require(returned is None or returned <= count, "Returned tokens exceed native count")
    if normal["stop_reason"] != "stop_sequence" and normal["token_ids_status"] == "returned":
        require(returned == count, "Token count mismatch")
    boundary = b.classify_response(normal["raw_response"], normal["raw_termination"],
                                   declared_stops=())
    span = boundary["first_span"]["text"]
    assessable = bool(boundary["unit_identifiable"] and span.strip() and
                      boundary["status"] != "TRUNCATED")
    return {"request_id": row["request_id"], "request_sha256": row["request_sha256"],
        **normal, "generated_tokens": count, "returned_token_count": returned,
        "latency_seconds": latency, "input_token_audit": token_audit,
        "response_status": boundary, "raw_text_sha256": th(normal["raw_response"]),
        "first_reply_sha256": th(span),
        "automatic_score": automatic_score(row, persona, span, assessable),
        "human_semantic_ratings": 0, "evidence_level": "DEVELOPMENT_MECHANISM"}


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
            require(data["request_id"] in attempted and data["request_id"] not in raw,
                    "Unbound or duplicate raw response")
            raw[data["request_id"]] = data
        elif event["kind"] == DERIVED:
            require(data["request_id"] in raw and data["request_id"] not in derived,
                    "Unbound or duplicate derived result")
            derived[data["request_id"]] = data
    return attempted, raw, derived


def run(preflight_path=PREFLIGHT):
    preflight_path = Path(preflight_path)
    fresh, stored, plan = preflight(), load(preflight_path), load(FROZEN)
    require(stored.get("status") == fresh.get("status") == "PASS", "Passing preflight required")
    for key in ("manifest_sha256", "authorization_sha256", "design_sha256",
                "case_bank_sha256", "source_hashes", "configuration", "server_command"):
        require(stored[key] == fresh[key], "Preflight binding changed: " + key)
    with b.writer_lock(ROOT):
        require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
                "Existing allocation: no repeat or resume")
        claim = {key: fresh[key] for key in ("manifest_sha256", "authorization_sha256",
                 "design_sha256", "case_bank_sha256", "source_hashes")}
        claim.update(preflight_sha256=sha256(preflight_path), maximum_attempts=MAX_ATTEMPTS,
                     retries=0, hidden_warmups=0)
        write_exclusive(ROOT / "claim.json", claim)
        authorization = load(Path(plan["authorization_path"]))
        journal = b.RunJournal(ROOT / "runs", {
            "phase": "P1 history-template development mechanism",
            "evidence_level": "DEVELOPMENT_MECHANISM", "claim": claim,
            "frozen_manifest": plan, "authorization": authorization,
            "configuration": cfg(plan).as_dict(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                text=True).strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
            "python": platform.python_version(), "platform": platform.platform()})
        for path, digest in claim["source_hashes"].items():
            destination = journal.directory / "source_snapshot" / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as handle:
                handle.write(Path(path).read_bytes())
            require(sha256(destination) == digest, "Source snapshot changed")
        started, active, status = time.monotonic(), None, "BLOCKED"
        inference_seconds = failed_seconds = 0.0
        personas = load(CASE_BANK)["personas"]
        try:
            journal.write("preflight", fresh)
            with s.Server(plan, journal) as server:
                client = b.LlamaClient(cfg(plan).endpoint, timeout=180, audit=journal.write)
                props = client.request("/props")
                binding = b.validate_server_properties(props, cfg(plan))
                require(binding["build_info"] == "b11573-0f701c882", "Backend build")
                journal.write("effective_server_defaults", {"props": props,
                                                              "validation": binding})
                for row in plan["requests"]:
                    tokens = client.request("/tokenize", {"content": row["prompt"],
                        "add_special": True, "parse_special": True,
                        "with_pieces": False})["tokens"]
                    require(tokens == row["input_token_ids"], "Live tokenizer changed")
                    journal.write("live_prompt_verified", {"request_id": row["request_id"],
                                  "token_ids_sha256": th(str(tokens))})
                journal.write("live_preflight_pass", {"prompts": MAX_ATTEMPTS,
                                                       "completed_inference": 0})
                print(json.dumps({"live_preflight": "PASS", "planned": MAX_ATTEMPTS}),
                      flush=True)
                for row in plan["requests"]:
                    remaining_wall = 2700.0 - (time.monotonic() - started)
                    remaining_inference = 1800.0 - inference_seconds
                    require(remaining_wall > 0 and remaining_inference > 0,
                            "Registered time ceiling reached; preserve suffix")
                    server.assert_running()
                    client.timeout = min(180, remaining_wall, remaining_inference)
                    active = row["request_id"]
                    journal.write(STARTED, row)
                    tick = time.monotonic()
                    try:
                        response = client.request("/completion", payload(row))
                    except BaseException:
                        elapsed = time.monotonic() - tick
                        inference_seconds += elapsed
                        failed_seconds += elapsed
                        journal.write("history_template_completion_failed",
                                      {"request_id": active, "elapsed_seconds": elapsed})
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
                b.validate_server_properties(client.request("/props"), cfg(plan))
                after = preflight(check_headroom=False, require_unused=False)
                require(after["identity"] == fresh["identity"] and
                        after["source_hashes"] == fresh["source_hashes"],
                        "Postflight identity/source changed")
                journal.write("postflight", after)
            status = "PASS"
        except BaseException as exc:
            status = "PARTIAL" if active or inference_seconds else "BLOCKED"
            journal.write("failure", {"type": type(exc).__name__, "message": str(exc),
                                      "request_id": active})
        events = b.read_events(journal.directory)
        attempted, raw, derived = inventory(plan, events)
        if status != "PASS" and len(derived) == MAX_ATTEMPTS:
            status = "COMPLETE_DATA_POSTFLIGHT_FAILED"
        live_checks = sum(event["kind"] == "live_prompt_verified" for event in events)
        summary = {"status": status, "attempted": len(attempted),
            "responses_received": len(raw), "results": len(derived),
            "native_tokenizer_calls": MAX_ATTEMPTS,
            "live_server_tokenizer_checks": live_checks,
            "tokenizer_operations_total": MAX_ATTEMPTS + live_checks,
            "inference_wall_seconds": sum(value["latency_seconds"] for value in raw.values()) +
                                      failed_seconds,
            "failed_completion_seconds": failed_seconds,
            "batch_wall_seconds": time.monotonic() - started,
            "run_directory": journal.directory.as_posix(), "retries": 0,
            "hidden_warmups": 0, "human_semantic_ratings": 0}
        journal.finish(**summary)
        write_exclusive(journal.directory / "summary.json", summary)
        return summary


def _terminal_summary(folder, events, require_pass=False):
    summary = load(folder / "summary.json")
    require(events and events[-1]["kind"] == "run_finished" and
            summary == events[-1]["data"], "Terminal event")
    if require_pass:
        require(summary.get("status") == "PASS",
                "Formal analysis requires terminal run status PASS")
    return summary


def replay():
    plan = load(FROZEN)
    validate_plan(plan)
    folders = list((ROOT / "runs").glob("*"))
    require(len(folders) == 1, "Unexpected run count")
    folder = folders[0]
    events = b.read_events(folder)
    claim = load(ROOT / "claim.json")
    manifest = load(folder / "manifest.json")
    require(manifest["claim"] == claim and manifest["frozen_manifest"] == plan and
            manifest["authorization"] == load(Path(plan["authorization_path"])),
            "Run binding changed")
    _terminal_summary(folder, events)
    attempted, raw, derived = inventory(plan, events)
    live = [event["data"] for event in events if event["kind"] == "live_prompt_verified"]
    require([item["request_id"] for item in live] ==
            [row["request_id"] for row in plan["requests"][:len(live)]], "Live token order")
    require(not attempted or len(live) == MAX_ATTEMPTS,
            "Generation began before all token checks")
    for path, digest in claim["source_hashes"].items():
        snapshot = folder / "source_snapshot" / path
        require(snapshot.is_file() and sha256(snapshot) == digest, "Snapshot changed")
    sent = [event["data"]["payload"] for event in events if event["kind"] == "http_request" and
            event["data"]["route"] == "/completion"]
    require(sent == [payload(row) for row in plan["requests"][:len(attempted)]],
            "Completion payload changed")
    bodies = [json.loads(base64.b64decode(event["data"]["body_base64"])) for event in events
              if event["kind"] == "http_response" and
              event["data"]["route"] == "/completion" and
              event["data"].get("status") == 200]
    require(bodies == [record["response"] for record in raw.values()], "Raw response changed")
    personas = load(CASE_BANK)["personas"]
    rows = []
    for row in plan["requests"]:
        request_id = row["request_id"]
        reconstructed = (result(row, personas[row["persona_id"]],
                                raw[request_id]["response"], raw[request_id]["latency_seconds"])
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
    terminal = _terminal_summary(folder, events)
    public = [{"request_id": row["request_id"], "request_sha256": row["request_sha256"],
        "case_id": row["case_id"], "persona_id": row["persona_id"], "arm": row["arm"],
        "state": state, "raw_text_sha256": None if result_row is None else
        result_row["raw_text_sha256"], "generated_tokens": None if result_row is None else
        result_row["generated_tokens"], "stop_reason": None if result_row is None else
        result_row["stop_reason"], "latency_seconds": None if result_row is None else
        result_row["latency_seconds"], "automatic_score": None if result_row is None else
        result_row["automatic_score"]} for row, result_row, state in rows]
    return {"version": "p1_history_template_mechanism_integrity_v1",
        "integrity_status": "PASS", "manifest_sha256": sha256(FROZEN),
        "run_terminal_status": terminal["status"],
        "analysis_eligible": terminal["status"] == "PASS",
        "design_sha256": DESIGN_SHA, "case_bank_sha256": CASE_BANK_SHA,
        "run_directory": folder.as_posix(),
        "attempted": sum(state != "UNATTEMPTED" for _, _, state in rows),
        "results": sum(state == "COMPLETED" for _, _, state in rows),
        "http_responses_verified": bodies, "journal_events": len(events), "rows": public,
        "raw_text_embedded": False, "new_generations_during_audit": 0}


def _distribution(values, missing_label="MISSING"):
    return dict(sorted(Counter(missing_label if value is None else str(value)
                               for value in values).items()))


def _latency_contrast(by_case, case_ids, high, low, persona_by_case):
    contributions = []
    for case_id in case_ids:
        high_value, low_value = by_case[case_id].get(high), by_case[case_id].get(low)
        value = None if high_value is None or low_value is None else high_value - low_value
        contributions.append({"case_id": case_id,
            "persona_id": persona_by_case[case_id], "seconds": value})
    observed = [item["seconds"] for item in contributions if item["seconds"] is not None]
    loo = {}
    for persona_id in sorted(set(persona_by_case.values())):
        values = [item["seconds"] for item in contributions
                  if item["persona_id"] != persona_id and item["seconds"] is not None]
        loo[persona_id] = None if not values else sum(values) / len(values)
    finite = [value for value in loo.values() if value is not None]
    return {"high_arm": high, "low_arm": low, "case_contributions": contributions,
        "observed_pairs": len(observed), "missing_pairs": len(case_ids) - len(observed),
        "mean_paired_seconds": None if not observed else sum(observed) / len(observed),
        "leave_one_persona_out_range": [min(finite), max(finite)] if finite else [None, None],
        "missing_latency_imputed": False}


def analyze():
    plan = load(FROZEN)
    validate_plan(plan)
    require(AUDIT.is_file() and load(AUDIT) == audit(), "Frozen execution audit required")
    design = load(DESIGN)
    folder, events, rows, _ = replay()
    _terminal_summary(folder, events, require_pass=True)
    require(all(state == "COMPLETED" for _, _, state in rows),
            "Complete 30-row run required")
    by_arm, by_case, latency_by_case = defaultdict(list), defaultdict(dict), defaultdict(dict)
    persona_by_case, regime_by_case, results_only = {}, {}, []
    for row, result_row, _ in rows:
        score = result_row["automatic_score"]
        by_arm[row["arm"]].append(score)
        by_case[row["case_id"]][row["arm"]] = score
        latency_by_case[row["case_id"]][row["arm"]] = result_row["latency_seconds"]
        persona_by_case[row["case_id"]] = row["persona_id"]
        regime_by_case[row["case_id"]] = row["history_regime"]
        results_only.append(result_row)
    arm_summary = {arm: {**{metric: base.binary_summary(by_arm[arm], metric)
                                  for metric in METRICS},
        "selection_categories": _distribution(
            [score["selection_category"] for score in by_arm[arm]]),
        "completion_latency_seconds": {"count": len(by_arm[arm]),
            "mean": sum(latency_by_case[case][arm] for case in latency_by_case) /
                    len(latency_by_case)}} for arm in ARMS}
    contrasts, regime_contrasts, latency = {}, {}, {}
    all_cases = sorted(by_case)
    for name, (high, low) in design["estimands"]["primary_paired_contrasts"].items():
        weights = {high: 1.0, low: -1.0}
        contrasts[name] = {metric: base.weighted_contrast(
            by_case, all_cases, weights, metric, persona_by_case) for metric in METRICS}
        latency[name] = _latency_contrast(
            latency_by_case, all_cases, high, low, persona_by_case)
        regime_contrasts[name] = {}
        for regime in sorted(set(regime_by_case.values())):
            ids = [case_id for case_id in all_cases if regime_by_case[case_id] == regime]
            regime_contrasts[name][regime] = {metric: base.weighted_contrast(
                by_case, ids, weights, metric, persona_by_case) for metric in METRICS}
    memory_events = [event["data"] for event in events if event["kind"] == "memory_observation"]
    available = [item.get("system", {}).get("available_physical") for item in memory_events]
    available = [value for value in available if value is not None]
    peak = max((item.get("process", {}).get("peak_working_set", 0)
                for item in memory_events), default=0)
    inference_seconds = sum(item["latency_seconds"] for item in results_only)
    return {"version": "p1_history_template_mechanism_analysis_v1",
        "evidence_level": "DEVELOPMENT_MECHANISM", "manifest_sha256": sha256(FROZEN),
        "execution_audit_sha256": sha256(AUDIT), "design_sha256": DESIGN_SHA,
        "case_bank_sha256": CASE_BANK_SHA, "run_directory": folder.as_posix(),
        "generations": len(results_only), "human_semantic_ratings": 0,
        "arm_summary": arm_summary, "paired_effects": contrasts,
        "regime_stratified_paired_effects": regime_contrasts,
        "paired_latency_effects": latency,
        "inferential_policy": {"p_values": "NOT_COMPUTED", "estimation_first": True,
            "logical_missing_outcome_bounds": True,
            "leave_one_persona_out_is_leave_one_case_out": True,
            "confirmatory_or_causal_claim": False},
        "interpretation_limits": design["interpretation_limits"],
        "resource_observations": {"generated_tokens": sum(
                item["generated_tokens"] for item in results_only),
            "native_stop_reason_distribution": _distribution(
                [item["stop_reason"] for item in results_only]),
            "completion_inference_seconds": inference_seconds,
            "server_peak_working_set_bytes": peak,
            "minimum_observed_available_physical_bytes": min(available) if available else None},
        "cumulative_authorization_after": {"generations_limit": 1200,
            "generations_used": GENERATION_BASELINE + len(results_only),
            "inference_seconds_limit": 72000,
            "inference_seconds_used": INFERENCE_BASELINE + inference_seconds},
        "raw_text_embedded": False, "new_generations_during_analysis": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("authorization-requirements", "register",
                                            "preflight", "run", "audit", "analyze"))
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--preflight", type=Path, default=PREFLIGHT)
    args = parser.parse_args(argv)
    if args.action == "authorization-requirements":
        print(json.dumps(authorization_requirements(), ensure_ascii=False, indent=2,
                         sort_keys=True))
    elif args.action == "register":
        require(args.authorization is not None, "--authorization is required")
        print(json.dumps(register(args.authorization), ensure_ascii=False, indent=2,
                         sort_keys=True))
    elif args.action == "preflight":
        report = preflight_receipt()
        write_exclusive(PREFLIGHT, report)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        if report["status"] != "PASS":
            return 2
    elif args.action == "run":
        print(json.dumps(run(args.preflight), ensure_ascii=False, indent=2, sort_keys=True))
    elif args.action == "audit":
        report = audit()
        write_exclusive(AUDIT, report)
        print(json.dumps({key: report[key] for key in ("integrity_status", "attempted", "results")},
                         sort_keys=True))
    else:
        report = analyze()
        write_exclusive(ANALYSIS, report)
        print(json.dumps({"status": "ANALYZED", "generations": report["generations"],
                          "output": ANALYSIS.as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
