"""Thin controller for the frozen 60-request history semantics x surface candidate.

Importing or validating this module performs no tokenization, preflight, model
launch, or generation. Operational actions remain gated by a separate exact
authorization that is intentionally absent from the candidate package.
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

import p1_persona_dialogue_history_template_mechanism as engine


base, s, b = engine.base, engine.s, engine.b
load, sha256, th, require = engine.load, engine.sha256, engine.th, engine.require
write_exclusive = engine.write_exclusive

OUT = Path("docs/validation/p1/persona_dialogue_history_semantics_surface_factorial_v1")
DESIGN = OUT / "prospective_design_v1.json"
CASE_BANK = OUT / "case_bank_v1.json"
AUTHORIZATION = OUT / "execution_authorization_v1.json"
FROZEN = OUT / "frozen_manifest_v1.json"
PREFLIGHT = OUT / "preflight_v1.json"
AUDIT = OUT / "execution_audit_v1.json"
ANALYSIS = OUT / "analysis_v1.json"
ROOT = Path("results/p1_persona_dialogue_history_semantics_surface_factorial/v1")
TEST_SOURCE = Path("tests/test_p1_persona_dialogue_history_semantics_surface_factorial.py")

DESIGN_SHA = "1f0632aad38740fcf8938e8b703beedd181099397f6055b1c178bb601095a7a0"
CASE_BANK_SHA = "3acdc36c2525a4c858da3be5c1aaeb9be6ed52c1f046d6d04304926900d0f8cd"
MAX_ATTEMPTS = 60
GENERATION_BASELINE = 232
INFERENCE_BASELINE = 1361.7570141999922
ARMS = (
    "SF_NO_H",
    "SFH_ALIGNED_RAW",
    "SFH_ALIGNED_DECLARATIVE",
    "SFH_CONFLICT_RAW",
    "SFH_CONFLICT_DECLARATIVE",
)
PRIMARY_METRICS = (
    "current_preferred_selection",
    "current_target_selection",
    "raw_recommendation_frame_occurrence",
    "exact_history_intrusion",
    "strict_format_adherence",
)
ANALYSIS_METRICS = PRIMARY_METRICS + (
    "finite_contract_grammar_adherence",
    "surface_style_uptake",
    "exact_current_reason_cue_secondary",
)
STARTED = "history_semantics_surface_generation_started"
RAW = "history_semantics_surface_raw_generation"
DERIVED = "history_semantics_surface_result"


def _local_module_candidates(module_name):
    """Resolve a possibly local import without importing or executing it."""
    parts = module_name.split(".")
    candidates = []
    for parent in (Path("tools"), Path("src"), Path(".")):
        module = parent.joinpath(*parts)
        candidates.extend((module.with_suffix(".py"), module / "__init__.py"))
        for depth in range(1, len(parts)):
            candidates.append(parent.joinpath(*parts[:depth], "__init__.py"))
    return [path for path in candidates if path.is_file()]


def runtime_python_dependency_paths(entry_paths=None):
    """Return the complete transitive local Python import closure deterministically."""
    root = Path.cwd().resolve()
    pending = [Path(path).resolve() for path in (entry_paths or (Path(__file__),))]
    discovered = set()
    while pending:
        path = pending.pop()
        require(path.is_file() and (path == root or root in path.parents),
                "Local dependency path escaped repository")
        if path in discovered:
            continue
        discovered.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        module_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                module_names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                module_names.add(node.module)
                module_names.update(node.module + "." + alias.name
                                    for alias in node.names if alias.name != "*")
        for module_name in sorted(module_names):
            for candidate in _local_module_candidates(module_name):
                resolved = candidate.resolve()
                if resolved not in discovered:
                    pending.append(resolved)
    return tuple(sorted((path.relative_to(root) for path in discovered),
                        key=lambda value: value.as_posix()))


def cfg(plan):
    model = plan["model"]
    return s.Runtime(model["model_file"], model["model_sha256"],
                     model["backend_file"], model_label=model["model_label"])


def _binding_paths(design):
    bindings = design["bindings"]
    paths = [Path(bindings[key]["path"]) for key in (
        "completed_history_template_audit", "completed_history_template_analysis",
        "response_status", "runner_infrastructure_reused", "tokenizer_identity_source")]
    paths.extend(Path(item["path"])
                 for item in bindings["prior_material_sources_for_disjointness"])
    return paths


def source_hashes():
    design = load(DESIGN)
    paths = list(Path("src/personaslm").glob("*.py")) + [
        *runtime_python_dependency_paths(), TEST_SOURCE, DESIGN, CASE_BANK,
        *_binding_paths(design)]
    root = Path.cwd().resolve()
    unique = {path.resolve(): path for path in paths}
    return {path.relative_to(root).as_posix(): sha256(path)
            for path in sorted(unique, key=lambda value: value.as_posix())}


def validate_registered_source_hashes(expected):
    """Fail closed if any registered local source or transitive dependency changes."""
    observed = source_hashes()
    require(expected == observed, "Registered source or dependency closure changed")
    return observed


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
        semantics = arm["history_semantics"].casefold()
        surface = ("raw" if arm["history_surface"] == "RAW_RECOMMENDATION"
                   else "declarative")
        messages.extend((
            {"role": "user", "content": case["history_user"]},
            {"role": "assistant",
             "content": case["history_assistant"][f"{semantics}_{surface}"]},
        ))
    messages.append({"role": "user", "content": case["fixed_current_user"]})
    factors = {key: arm[key] for key in ("S", "F", "H")}
    return factors, arm["history_semantics"], arm["history_surface"], messages


def unique_target_selection(row, text):
    """Classify the unique exact canonical target, independent of sentence frame."""
    sentences = base._sentences(text)
    first = sentences[0] if sentences else ""
    matches = []
    scopes = (("CURRENT", row["options"]), ("ARCHIVED", row["archived_options"]))
    for scope, options in scopes:
        for option in ("A", "B"):
            target = options[option]["canonical"]
            if base._exact_contains(first, target):
                matches.append((scope, option, target))
    unique = list(dict.fromkeys(matches))
    if len(unique) == 1:
        scope, option, target = unique[0]
        if scope == "CURRENT":
            category = ("CURRENT_PREFERRED" if option == row["preferred_option"]
                        else "CURRENT_NONPREFERRED")
        else:
            category = ("ARCHIVED_ALIGNED" if option == row["aligned_history_option"]
                        else "ARCHIVED_CONFLICT")
        return {"category": category, "scope": scope, "option": option,
                "target": target, "first_sentence": sentences[0]}
    return {"category": "MULTIPLE" if unique else "NONE",
            "scope": None, "option": None, "target": None,
            "first_sentence": sentences[0] if sentences else None}


def finite_contract_selection(row, text):
    """Classify only the frozen recommendation forms as a format diagnostic."""
    sentences = base._sentences(text)
    first = base._normalized(sentences[0]) if sentences else ""
    matches = []
    for scope, options in (("CURRENT", row["options"]),
                           ("ARCHIVED", row["archived_options"])):
        for option in ("A", "B"):
            target = options[option]["canonical"]
            forms = (f"I recommend {target}.", f"I recommend the {target}.",
                     f"I recommend Option {option} — {target}.",
                     f"I recommend Option {option} - {target}.")
            if any(first == base._normalized(form) for form in forms):
                matches.append((scope, option, target))
    unique = list(dict.fromkeys(matches))
    if len(unique) == 1:
        scope, option, target = unique[0]
        return {"category": f"{scope}_{option}", "scope": scope,
                "option": option, "target": target}
    return {"category": "MULTIPLE" if unique else "NONE",
            "scope": None, "option": None, "target": None}


def automatic_score(row, persona, text):
    """Score every returned response; strict-format status never gates selection."""
    parsed = unique_target_selection(row, text)
    contract = finite_contract_selection(row, text)
    sentences = base._sentences(text)
    first = base._normalized(sentences[0]) if sentences else ""
    selected_current = parsed["scope"] == "CURRENT"
    preferred = selected_current and parsed["option"] == row["preferred_option"]
    exact_strict_option = next((option for option in ("A", "B")
        if first == base._normalized(
            f"I recommend {row['options'][option]['canonical']}.")
        ), None)
    archived_targets = [value["canonical"] for value in row["archived_options"].values()]
    forbidden = list(archived_targets)
    if exact_strict_option is not None:
        other = "B" if exact_strict_option == "A" else "A"
        forbidden.append(row["options"][other]["canonical"])
    strict = int(exact_strict_option is not None and len(sentences) == 2 and
                 not any(base._exact_contains(text, value) for value in forbidden))
    history_mentions = [target for target in archived_targets
                        if base._exact_contains(text, target)]
    reason_cue = None
    if selected_current:
        option, other = parsed["option"], "B" if parsed["option"] == "A" else "A"
        second = sentences[1] if len(sentences) >= 2 else ""
        chosen = any(base._exact_contains(second, cue)
                     for cue in row["options"][option]["reason_cues"])
        competing = any(base._exact_contains(second, cue)
                        for cue in row["options"][other]["reason_cues"])
        reason_cue = int(chosen and not competing)
    return {
        "measurement_state": "ASSESSED_FINITE_GRAMMAR_RETURNED_RESPONSE",
        "selection_category": parsed["category"],
        "selected_scope": parsed["scope"],
        "selected_option": parsed["option"],
        "selected_target": parsed["target"],
        "current_preferred_selection": int(preferred),
        "current_target_selection": int(selected_current),
        "finite_contract_selection_category": contract["category"],
        "finite_contract_grammar_adherence": int(contract["scope"] is not None),
        "raw_recommendation_frame_occurrence": int(first.startswith("i recommend the ")),
        "exact_history_intrusion": int(bool(history_mentions)),
        "exact_history_targets_in_full_response": history_mentions,
        "strict_format_adherence": strict,
        "exact_current_reason_cue_secondary": reason_cue,
        "semantic_reason_correctness": None,
        "semantic_reason_review_status": "PENDING_BLINDED_HUMAN_REVIEW",
        **base.style_score(persona, text, True),
    }


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
    require(design["research"]["evidence_level"] ==
            "DEVELOPMENT_MECHANISM_REPLICATION", "Evidence level")
    require(design["research"]["preexecution_review_amendment"]["status"] ==
            "RESOLVED_BEFORE_AUTHORIZATION_TOKENIZATION_PREFLIGHT_OR_GENERATION" and
            design["bindings"]["runtime_python_dependency_policy"] ==
            "AST_DISCOVERED_TRANSITIVE_LOCAL_IMPORT_CLOSURE_HASHED_VALIDATED_AND_SNAPSHOTTED",
            "Pre-execution review amendment")
    authorization = design["authorization"]
    require(authorization["execution_authorized"] is False and
            authorization["tokenization_authorized"] is False and
            authorization["preflight_authorized"] is False and
            authorization["maximum_native_tokenizer_calls"] == MAX_ATTEMPTS and
            authorization["maximum_live_server_tokenizer_checks"] == MAX_ATTEMPTS and
            authorization["maximum_tokenizer_operations_total"] == 2 * MAX_ATTEMPTS and
            authorization["maximum_generation_attempts_if_authorized"] == MAX_ATTEMPTS and
            authorization["retries"] == authorization["hidden_warmups"] == 0,
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
            budget["actual_completion_inference_seconds_ceiling"] == 3600.0 and
            budget["batch_wall_seconds_ceiling"] == 5400.0, "Resource budget")
    baseline = load(Path(design["bindings"]["completed_history_template_analysis"]["path"]))[
        "cumulative_authorization_after"]
    require(baseline["generations_used"] == GENERATION_BASELINE and
            baseline["inference_seconds_used"] == INFERENCE_BASELINE and
            budget["global_baseline"]["generations_used"] == GENERATION_BASELINE and
            budget["global_baseline"]["inference_wall_seconds_used"] == INFERENCE_BASELINE,
            "Cumulative baseline")

    personas = bank["personas"]
    cases = {case["case_id"]: case for case in bank["cases"]}
    require(len(personas) == len(bank["cases"]) == len(cases) == 12 and
            Counter(case["persona_id"] for case in cases.values()) ==
            Counter({persona_id: 1 for persona_id in personas}), "One persona per case")
    require(len({base._normalized(persona["speaker_name"])
                 for persona in personas.values()}) == 12 and
            len({persona["profile_source_id"] for persona in personas.values()}) == 12,
            "Persona identities not unique")
    require(Counter(case["domain"] for case in cases.values()) ==
            Counter(design["design"]["domains"]), "Domain balance")
    require(Counter(case["preferred_option"] for case in cases.values()) ==
            Counter({"A": 6, "B": 6}), "Preferred-option balance")
    require(Counter(tuple(case["current_option_display_order"])
                    for case in cases.values()) ==
            Counter({("A", "B"): 6, ("B", "A"): 6}), "Display-order balance")
    display_position = Counter(
        "PREFERRED_FIRST" if case["current_option_display_order"][0] ==
        case["preferred_option"] else "PREFERRED_SECOND"
        for case in cases.values())
    preferred_by_order = Counter(
        f"{case['preferred_option']}_{'_THEN_'.join(case['current_option_display_order'])}"
        for case in cases.values())
    require(display_position == Counter({"PREFERRED_FIRST": 6, "PREFERRED_SECOND": 6}) and
            preferred_by_order == Counter({"A_A_THEN_B": 3, "A_B_THEN_A": 3,
                                            "B_A_THEN_B": 3, "B_B_THEN_A": 3}) and
            design["design"]["preferred_option_by_display_position"] ==
            dict(display_position) and
            design["design"]["preferred_option_by_display_order"] ==
            dict(preferred_by_order), "Preference/display-position crossing")
    require(all(Counter(
        "PREFERRED_FIRST" if case["current_option_display_order"][0] ==
        case["preferred_option"] else "PREFERRED_SECOND"
        for case in cases.values() if case["domain"] == domain) ==
        Counter({"PREFERRED_FIRST": 1, "PREFERRED_SECOND": 1})
        for domain in design["design"]["domains"]),
        "Within-domain preference/display-position balance")
    require(Counter(case["aligned_history_option"] for case in cases.values()) ==
            Counter({"A": 6, "B": 6}) and
            Counter(case["conflict_history_option"] for case in cases.values()) ==
            Counter({"A": 6, "B": 6}), "Archived-target balance")
    require(Counter((case["preferred_option"], case["aligned_history_option"])
                    for case in cases.values()) ==
            Counter({("A", "A"): 3, ("A", "B"): 3,
                     ("B", "A"): 3, ("B", "B"): 3}), "Joint balance")

    rows = design["order"]["requests"]
    require(len(rows) == len({row["request_id"] for row in rows}) == MAX_ATTEMPTS and
            [row["order"] for row in rows] == list(range(MAX_ATTEMPTS)), "Frozen order")
    require(Counter(row["arm"] for row in rows) == Counter({arm: 12 for arm in ARMS}),
            "Arm allocation")
    arm_orders = {arm: [row["order"] for row in rows if row["arm"] == arm]
                  for arm in ARMS}
    require(all(sum(orders) == 354 and len(orders) == 12 for orders in arm_orders.values()) and
            design["order"]["arm_order_balance"] == {
                arm: {"orders": orders, "sum": 354, "mean": 29.5}
                for arm, orders in arm_orders.items()}, "Arm order balance")
    for case_id in cases:
        require(Counter(row["arm"] for row in rows if row["case_id"] == case_id) ==
                Counter({arm: 1 for arm in ARMS}), "Incomplete within-case pairing")

    prior_strings = set()
    for binding in design["bindings"]["prior_material_sources_for_disjointness"]:
        prior_strings.update(base._strings(load(Path(binding["path"]))))
    identifiers = [bank["template_ancestry"]["family_id"]]
    current_names = [case["options"][side]["canonical"]
                     for case in cases.values() for side in ("A", "B")]
    archived_names = [case["archived_options"][side]["canonical"]
                      for case in cases.values() for side in ("A", "B")]
    require(len({base._normalized(value) for value in current_names}) == 24 and
            len({base._normalized(value) for value in archived_names}) == 24 and
            not ({base._normalized(value) for value in current_names} &
                 {base._normalized(value) for value in archived_names}),
            "Target names not uniquely disjoint")
    probes = 0
    for persona_id, persona in personas.items():
        require(persona["synthetic"] is True and
                len(persona["operational_style_checks"]) == 5, "Persona material")
        identifiers.extend((persona_id, persona["speaker_name"], persona["profile_source_id"],
                            persona["S_block"], persona["F_block"]))
    for case in cases.values():
        require(set(case["options"]) == set(case["archived_options"]) == {"A", "B"} and
                case["aligned_history_option"] != case["conflict_history_option"],
                "Case option structure")
        current_targets = [case["options"][side]["canonical"] for side in ("A", "B")]
        history_targets = [case["archived_options"][side]["canonical"]
                           for side in ("A", "B")]
        current = case["fixed_current_notes"] + "\n" + case["fixed_current_user"]
        history = case["history_user"] + "\n" + "\n".join(
            case["history_assistant"].values())
        require(all(not base._exact_contains(history, target) for target in current_targets),
                "Current option leaks into history")
        require(all(not base._exact_contains(current, target) for target in history_targets),
                "Archived target leaks into current material")
        require(all(base._exact_contains(case["history_user"], target)
                    for target in history_targets), "History pair incomplete")
        note_positions = [case["fixed_current_notes"].index(f"Option {side} —")
                          for side in case["current_option_display_order"]]
        require(note_positions == sorted(note_positions), "Recorded display order changed")
        persona = personas[case["persona_id"]]
        prefix = next(item["value"] for item in persona["operational_style_checks"]
                      if item["check_id"] == "second_sentence_prefix")
        suffix = next(item["value"] for item in persona["operational_style_checks"]
                      if item["check_id"] == "second_sentence_suffix")
        for semantics in ("aligned", "conflict"):
            selected = case[f"{semantics}_history_option"]
            target = case["archived_options"][selected]["canonical"]
            cue = case["archived_options"][selected]["reason_cue"]
            raw = case["history_assistant"][f"{semantics}_raw"].split(". ", 1)
            declarative = case["history_assistant"][f"{semantics}_declarative"].split(". ", 1)
            require(len(raw) == len(declarative) == 2 and raw[1] == declarative[1] and
                    raw[0] + "." == f"I recommend the {target}." and
                    declarative[0] + "." == f"{target} was my choice." and
                    base._exact_contains(raw[1], cue) and
                    base._normalized(raw[1]).startswith(base._normalized(prefix)) and
                    base._normalized(raw[1]).endswith(base._normalized(suffix)),
                    "Surface pair changes more than the first sentence")
        built = {arm: construction(design, bank, case, arm)[3] for arm in ARMS}
        require(len(built["SF_NO_H"]) == 2 and
                all(len(built[arm]) == 4 for arm in ARMS[1:]), "Native role structure")
        require(all(messages[0] == built["SF_NO_H"][0] and
                    messages[-1] == built["SF_NO_H"][-1]
                    for messages in built.values()), "Current material changed across arms")
        require(len({built[arm][1]["content"] for arm in ARMS[1:]}) == 1,
                "Archived user changed across H arms")
        identifiers.extend((case["case_id"], *current_targets, *history_targets,
                            case["fixed_current_notes"], case["fixed_current_user"],
                            case["history_user"], *case["history_assistant"].values()))
        for target in current_targets + history_targets:
            sample = f"I recommend the {target}. {prefix} frozen detail, {suffix}"
            score = automatic_score({**case, "preferred_option": case["preferred_option"]},
                                    persona, sample)
            require(score["current_preferred_selection"] in (0, 1) and
                    score["current_target_selection"] in (0, 1),
                    "Finite grammar did not return a binary endpoint")
            probes += 1
    require(all(value not in prior_strings for value in identifiers),
            "New material exactly overlaps a prior bound source")
    require(tuple(design["evaluation_policy"]["primary_automatic_endpoints"]) ==
            PRIMARY_METRICS and
            design["evaluation_policy"]["semantic_reason_correctness"].startswith(
                "PENDING_BLINDED_HUMAN_REVIEW"), "Evaluation policy")
    if require_unstarted:
        require(not any(path.exists() for path in
                        (AUTHORIZATION, FROZEN, PREFLIGHT, AUDIT, ANALYSIS,
                         ROOT / "claim.json", ROOT / "native_tokenizer")) and
                not list((ROOT / "runs").glob("*")), "Study already initialized")
    dependencies = runtime_python_dependency_paths()
    require(Path(__file__).resolve().relative_to(Path.cwd().resolve()) in dependencies and
            Path("tools/p1_persona_dialogue_independent_replication.py") in dependencies and
            Path("tools/p1_persona_dialogue_mechanism_analysis_v2.py") in dependencies and
            Path("tools/p1_persona_dialogue_factorial.py") in dependencies and
            Path("tools/p1d_instruct_smoke.py") in dependencies,
            "Runtime dependency closure incomplete")
    return {"personas": 12, "cases": 12, "arms": 5, "requests": MAX_ATTEMPTS,
            "finite_grammar_probes": probes,
            "material_disjointness_sources": len(
                design["bindings"]["prior_material_sources_for_disjointness"]),
            "runtime_python_dependencies": len(dependencies),
            "new_model_generations": 0, "tokenizer_operations": 0}


def authorization_requirements():
    checks = validate_design()
    design = load(DESIGN)
    return {"schema_version": "personaslm_history_semantics_surface_authorization_v1",
        "status": "AUTHORIZED_BEFORE_TOKENIZATION_PREFLIGHT_OR_MODEL_EXECUTION",
        "authorization_path": AUTHORIZATION.as_posix(),
        "implementation": {
            "runner": {"path": Path(__file__).resolve().relative_to(
                Path.cwd().resolve()).as_posix(), "sha256": sha256(Path(__file__))},
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
        "actual_completion_inference_seconds_ceiling": 3600.0,
        "batch_wall_seconds_ceiling": 5400.0,
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
    require(not any(path.exists() for path in (FROZEN, PREFLIGHT, ROOT / "claim.json",
                                                ROOT / "native_tokenizer")) and
            not list((ROOT / "runs").glob("*")),
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
        factors, semantics, surface, messages = construction(
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
        row = {**item, "persona_id": case["persona_id"], "domain": case["domain"],
            "factors": factors, "history_semantics": semantics,
            "history_surface": surface, "messages": messages, "prompt": prompt,
            "prompt_sha256": th(prompt), "input_token_ids": token_ids,
            "input_tokens": len(token_ids), "input_token_ids_sha256": th(str(token_ids)),
            "preferred_option": case["preferred_option"],
            "current_option_display_order": case["current_option_display_order"],
            "aligned_history_option": case["aligned_history_option"],
            "conflict_history_option": case["conflict_history_option"],
            "options": case["options"], "archived_options": case["archived_options"],
            "max_new_tokens": 96, "seed": 42, "temperature": 0.0, "top_p": 1.0,
            "stop": [], "cache_prompt": False, "ignore_eos": False}
        require(len(token_ids) + 96 <= runtime["context_tokens"], "Context overflow")
        row["request_sha256"] = th(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                                separators=(",", ":")))
        rows.append(row)
    plan = {"version": "p1_history_semantics_surface_factorial_manifest_v1",
        "evidence_level": "DEVELOPMENT_MECHANISM_REPLICATION",
        "design_path": DESIGN.as_posix(), "design_sha256": DESIGN_SHA,
        "case_bank_path": CASE_BANK.as_posix(), "case_bank_sha256": CASE_BANK_SHA,
        "authorization_path": authorization_path.as_posix(),
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
    require(plan["version"] == "p1_history_semantics_surface_factorial_manifest_v1" and
            plan["design_sha256"] == DESIGN_SHA and
            plan["case_bank_sha256"] == CASE_BANK_SHA, "Manifest binding")
    validate_authorization(Path(plan["authorization_path"]))
    require(plan["authorization_sha256"] == sha256(Path(plan["authorization_path"])),
            "Registered authorization changed")
    validate_registered_source_hashes(plan["registration_source_hashes"])
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
    require(plan["model"] == expected_model and
            plan["runtime"] == design["runtime"] and
            plan["resource_budget"] == design["resource_budget"] and
            plan["new_model_generations"] == 0 and
            plan["template_sha256"] == sha256(Path(plan["template_path"])),
            "Frozen plan changed")
    cases = {case["case_id"]: case for case in bank["cases"]}
    template = Path(plan["template_path"]).read_text(encoding="utf-8")
    require(len(plan["requests"]) == len(plan["native_tokenizer_logs"]) == MAX_ATTEMPTS,
            "Frozen row count")
    for item, row, record in zip(design["order"]["requests"], plan["requests"],
                                 plan["native_tokenizer_logs"]):
        require(all(row[key] == item[key] for key in ("order", "request_id", "case_id", "arm")),
                "Request order changed")
        case = cases[row["case_id"]]
        factors, semantics, surface, messages = construction(
            design, bank, case, row["arm"])
        require(row["factors"] == factors and row["history_semantics"] == semantics and
                row["history_surface"] == surface and row["messages"] == messages and
                row["prompt"] == s.render(template, messages), "Prompt changed")
        expected_metadata = {"persona_id": case["persona_id"], "domain": case["domain"],
            "preferred_option": case["preferred_option"],
            "current_option_display_order": case["current_option_display_order"],
            "aligned_history_option": case["aligned_history_option"],
            "conflict_history_option": case["conflict_history_option"],
            "options": case["options"], "archived_options": case["archived_options"],
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
    native, tokenizer = plan["native_tokenizer_identity"], Path(
        plan["native_tokenizer_identity"]["path"])
    require(sha256(tokenizer) == native["tokenizer_sha256"] and
            {path.name: sha256(path) for path in tokenizer.parent.glob("*.dll")} ==
            native["dll_hashes"], "Tokenizer identity")
    baseline = load(Path(load(DESIGN)["bindings"]["completed_history_template_analysis"][
        "path"]))["cumulative_authorization_after"]
    require(baseline["generations_used"] == GENERATION_BASELINE and
            baseline["inference_seconds_used"] == INFERENCE_BASELINE and
            baseline["generations_limit"] - GENERATION_BASELINE >= MAX_ATTEMPTS and
            baseline["inference_seconds_limit"] - INFERENCE_BASELINE >= 3600.0,
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
        "live_gate": "All 60 parse_special=true token arrays must match before completion 1.",
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
        return {"status": "FAIL", "checked_utc": b.utc_now(),
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "expected_bindings": {"design_sha256": DESIGN_SHA,
                                  "case_bank_sha256": CASE_BANK_SHA},
            "observed_sha256": {name: sha256(path) if path.is_file() else None
                for name, path in (("design", DESIGN), ("case_bank", CASE_BANK),
                                   ("authorization", AUTHORIZATION), ("manifest", FROZEN))},
            "memory_observation": memory, "free_output_disk_bytes": disk_free,
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
    score = automatic_score(row, persona, normal["raw_response"])
    require(all(score[metric] in (0, 1)
                for metric in ("current_preferred_selection", "current_target_selection")),
            "Complete finite-grammar denominator failed")
    return {"request_id": row["request_id"], "request_sha256": row["request_sha256"],
        **normal, "generated_tokens": count, "returned_token_count": returned,
        "latency_seconds": latency, "input_token_audit": token_audit,
        "response_status": boundary, "raw_text_sha256": th(normal["raw_response"]),
        "first_reply_sha256": th(span), "automatic_score": score,
        "human_semantic_ratings": 0,
        "semantic_reason_review_status": "PENDING_BLINDED_HUMAN_REVIEW",
        "evidence_level": "DEVELOPMENT_MECHANISM_REPLICATION"}


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
    require(preflight_path.resolve() == PREFLIGHT.resolve(),
            "Official preflight path required")
    fresh, stored, plan = preflight(), load(preflight_path), load(FROZEN)
    require(stored.get("status") == fresh.get("status") == "PASS",
            "Passing preflight required")
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
            "phase": "P1 history semantics by surface development mechanism replication",
            "evidence_level": "DEVELOPMENT_MECHANISM_REPLICATION", "claim": claim,
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
                    remaining_wall = plan["resource_budget"]["batch_wall_seconds_ceiling"] - (
                        time.monotonic() - started)
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
                        response = client.request("/completion", payload(row))
                    except BaseException:
                        elapsed = time.monotonic() - tick
                        inference_seconds += elapsed
                        failed_seconds += elapsed
                        journal.write("history_semantics_surface_completion_failed",
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
            "hidden_warmups": 0, "human_semantic_ratings": 0,
            "semantic_reason_review_status": "PENDING_BLINDED_HUMAN_REVIEW"}
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


def _reconstruct_result(row, persona, raw_record, archived_derived=None):
    """Recover a scored row or preserve an explicit unscorable-response error."""
    try:
        reconstructed = result(row, persona, raw_record["response"],
                               raw_record["latency_seconds"])
    except Exception as exc:
        require(archived_derived is None,
                "Archived derived result is no longer reproducible")
        return None, {"type": type(exc).__name__, "message": str(exc)}
    if archived_derived is not None:
        require(reconstructed == archived_derived, "Derived result changed")
    return reconstructed, None


def replay():
    plan = load(FROZEN)
    validate_plan(plan)
    folders = list((ROOT / "runs").glob("*"))
    require(len(folders) == 1, "Unexpected run count")
    folder = folders[0]
    events = b.read_events(folder)
    claim = load(ROOT / "claim.json")
    manifest = load(folder / "manifest.json")
    require(claim["manifest_sha256"] == sha256(FROZEN) and
            claim["authorization_sha256"] == sha256(Path(plan["authorization_path"])) and
            claim["design_sha256"] == DESIGN_SHA and
            claim["case_bank_sha256"] == CASE_BANK_SHA and
            claim["preflight_sha256"] == sha256(PREFLIGHT) and
            claim["maximum_attempts"] == MAX_ATTEMPTS and
            claim["retries"] == claim["hidden_warmups"] == 0,
            "Run claim changed")
    require(manifest["claim"] == claim and manifest["frozen_manifest"] == plan and
            manifest["authorization"] == load(Path(plan["authorization_path"])),
            "Run binding changed")
    terminal = _terminal_summary(folder, events)
    if terminal["status"] == "PASS":
        require(sum(event["kind"] == "postflight" for event in events) == 1,
                "Successful run lacks postflight")
    attempted, raw, derived = inventory(plan, events)
    live = [event["data"] for event in events if event["kind"] == "live_prompt_verified"]
    require([item["request_id"] for item in live] ==
            [row["request_id"] for row in plan["requests"][:len(live)]],
            "Live token order")
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
    require(bodies == [record["response"] for record in raw.values()],
            "Raw response changed")
    personas = load(CASE_BANK)["personas"]
    rows = []
    for row in plan["requests"]:
        request_id = row["request_id"]
        reconstructed, reconstruction_error = None, None
        if request_id in raw:
            reconstructed, reconstruction_error = _reconstruct_result(
                row, personas[row["persona_id"]], raw[request_id],
                derived.get(request_id))
        state = ("COMPLETED" if request_id in derived else
                 "RAW_RECOVERABLE" if reconstructed is not None else
                 "RAW_UNSCORABLE" if reconstruction_error is not None else
                 "ATTEMPTED_UNRESOLVED" if request_id in attempted else "UNATTEMPTED")
        rows.append((row, reconstructed, state, reconstruction_error))
    return folder, events, rows, len(bodies)


def audit():
    plan = load(FROZEN)
    validate_plan(plan)
    folder, events, rows, bodies = replay()
    terminal = _terminal_summary(folder, events)
    public = [{"request_id": row["request_id"], "request_sha256": row["request_sha256"],
        "case_id": row["case_id"], "persona_id": row["persona_id"], "arm": row["arm"],
        "state": state, "reconstruction_error": reconstruction_error,
        "raw_text_sha256": None if result_row is None else
        result_row["raw_text_sha256"], "generated_tokens": None if result_row is None else
        result_row["generated_tokens"], "stop_reason": None if result_row is None else
        result_row["stop_reason"], "latency_seconds": None if result_row is None else
        result_row["latency_seconds"], "automatic_score": None if result_row is None else
        result_row["automatic_score"]
        } for row, result_row, state, reconstruction_error in rows]
    return {"version": "p1_history_semantics_surface_integrity_v1",
        "integrity_status": "PASS", "manifest_sha256": sha256(FROZEN),
        "run_terminal_status": terminal["status"],
        "analysis_eligible": terminal["status"] in {
            "PASS", "PARTIAL", "BLOCKED", "COMPLETE_DATA_POSTFLIGHT_FAILED"},
        "complete_run_analysis_eligible": terminal["status"] == "PASS",
        "design_sha256": DESIGN_SHA, "case_bank_sha256": CASE_BANK_SHA,
        "run_directory": folder.as_posix(),
        "attempted": sum(state != "UNATTEMPTED" for _, _, state, _ in rows),
        "results": sum(state == "COMPLETED" for _, _, state, _ in rows),
        "scorable_responses": sum(result_row is not None
                                  for _, result_row, _, _ in rows),
        "http_responses_verified": bodies, "journal_events": len(events), "rows": public,
        "raw_text_embedded": False, "new_generations_during_audit": 0}


def _analysis_inputs(rows):
    """Materialize every planned cell; absent responses remain explicit nulls."""
    by_arm, by_case = defaultdict(list), defaultdict(dict)
    latency_by_case, persona_by_case, results_only = defaultdict(dict), {}, []
    missing = {metric: None for metric in ANALYSIS_METRICS}
    missing["selection_category"] = None
    for row, result_row, _, _ in rows:
        score = copy.deepcopy(missing) if result_row is None else result_row["automatic_score"]
        by_arm[row["arm"]].append(score)
        by_case[row["case_id"]][row["arm"]] = score
        latency_by_case[row["case_id"]][row["arm"]] = (
            None if result_row is None else result_row["latency_seconds"])
        persona_by_case[row["case_id"]] = row["persona_id"]
        if result_row is not None:
            results_only.append(result_row)
    return by_arm, by_case, latency_by_case, persona_by_case, results_only


def analyze():
    plan = load(FROZEN)
    validate_plan(plan)
    require(AUDIT.is_file() and load(AUDIT) == audit(),
            "Frozen execution audit required")
    design = load(DESIGN)
    folder, events, rows, _ = replay()
    terminal = _terminal_summary(folder, events)
    require(terminal["status"] in {
        "PASS", "PARTIAL", "BLOCKED", "COMPLETE_DATA_POSTFLIGHT_FAILED"},
        "Unknown terminal status")
    by_arm, by_case, latency_by_case, persona_by_case, results_only = \
        _analysis_inputs(rows)
    require(all(score[metric] in (0, 1, None)
                for scores in by_arm.values() for score in scores
                for metric in ("current_preferred_selection", "current_target_selection")),
            "Primary target-inventory denominator invalid")
    arm_summary = {arm: {**{metric: base.binary_summary(by_arm[arm], metric)
                                  for metric in ANALYSIS_METRICS},
        "selection_categories": engine._distribution(
            [score["selection_category"] for score in by_arm[arm]]),
        "completion_latency_seconds": (lambda values: {
            "count": len(values), "missing": len(latency_by_case) - len(values),
            "mean": None if not values else sum(values) / len(values)})([
                latency_by_case[case][arm] for case in latency_by_case
                if latency_by_case[case][arm] is not None])} for arm in ARMS}
    all_cases = sorted(by_case)
    factorial = {name: {metric: base.weighted_contrast(
        by_case, all_cases, weights, metric, persona_by_case)
        for metric in ANALYSIS_METRICS}
        for name, weights in design["estimands"]["factorial_weights"].items()}
    no_history = {name: {metric: base.weighted_contrast(
        by_case, all_cases, weights, metric, persona_by_case)
        for metric in ANALYSIS_METRICS}
        for name, weights in design["estimands"]["no_history_weights"].items()}
    latency = {}
    for name, weights in design["estimands"]["no_history_weights"].items():
        nonzero = [arm for arm, weight in weights.items()
                   if arm != "SF_NO_H" and weight == 1.0]
        if len(nonzero) == 1 and weights.get("SF_NO_H") == -1.0:
            latency[name] = engine._latency_contrast(
                latency_by_case, all_cases, nonzero[0], "SF_NO_H", persona_by_case)
    memory_events = [event["data"] for event in events if event["kind"] == "memory_observation"]
    available = [item.get("system", {}).get("available_physical") for item in memory_events]
    available = [value for value in available if value is not None]
    peak = max((item.get("process", {}).get("peak_working_set", 0)
                for item in memory_events), default=0)
    inference_seconds = terminal["inference_wall_seconds"]
    return {"version": "p1_history_semantics_surface_factorial_analysis_v1",
        "evidence_level": "DEVELOPMENT_MECHANISM_REPLICATION",
        "manifest_sha256": sha256(FROZEN), "execution_audit_sha256": sha256(AUDIT),
        "design_sha256": DESIGN_SHA, "case_bank_sha256": CASE_BANK_SHA,
        "run_directory": folder.as_posix(),
        "run_terminal_status": terminal["status"],
        "analysis_mode": ("COMPLETE_REGISTERED_DESCRIPTIVE_ANALYSIS"
                          if terminal["status"] == "PASS" else
                          "PARTIAL_REGISTERED_MISSINGNESS_BOUNDS"),
        "planned_generations": MAX_ATTEMPTS,
        "generation_attempts": terminal["attempted"],
        "generations": terminal["attempted"],
        "scorable_responses": len(results_only),
        "missing_planned_responses": MAX_ATTEMPTS - len(results_only),
        "human_semantic_ratings": 0,
        "semantic_reason_review_status": "PENDING_BLINDED_HUMAN_REVIEW",
        "arm_summary": arm_summary, "factorial_effects": factorial,
        "no_history_effects": no_history, "paired_latency_effects": latency,
        "inferential_policy": {"p_values": "NOT_COMPUTED", "estimation_first": True,
            "logical_missing_outcome_bounds": True,
            "leave_one_persona_out_is_leave_one_case_out": True,
            "confirmatory_or_causal_claim": False,
            "independent_validation_claim": False, "algorithm_claim": False},
        "interpretation_limits": design["interpretation_limits"],
        "resource_observations": {"generated_tokens": sum(
                item["generated_tokens"] for item in results_only),
            "native_stop_reason_distribution": engine._distribution(
                [item["stop_reason"] for item in results_only]),
            "completion_inference_seconds": inference_seconds,
            "failed_completion_seconds": terminal["failed_completion_seconds"],
            "batch_wall_seconds": terminal["batch_wall_seconds"],
            "server_peak_working_set_bytes": peak,
            "minimum_observed_available_physical_bytes": min(available) if available else None},
        "cumulative_authorization_after": {"generations_limit": 1200,
            "generations_used": GENERATION_BASELINE + terminal["attempted"],
            "inference_seconds_limit": 72000,
            "inference_seconds_used": INFERENCE_BASELINE + inference_seconds},
        "raw_text_embedded": False, "new_generations_during_analysis": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "authorization-requirements",
                                            "register", "preflight", "run",
                                            "audit", "analyze"))
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--preflight", type=Path, default=PREFLIGHT)
    args = parser.parse_args(argv)
    if args.action == "validate":
        print(json.dumps(validate_design(require_unstarted=True), sort_keys=True))
    elif args.action == "authorization-requirements":
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
        print(json.dumps({key: report[key]
                          for key in ("integrity_status", "attempted", "results")},
                         sort_keys=True))
    else:
        report = analyze()
        write_exclusive(ANALYSIS, report)
        print(json.dumps({"status": "ANALYZED", "generations": report["generations"],
                          "output": ANALYSIS.as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
