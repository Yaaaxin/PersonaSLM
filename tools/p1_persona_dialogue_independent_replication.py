"""Frozen 96-request independent synthetic persona-dialogue replication runner."""

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
import re
import shutil
import subprocess
import time
import unicodedata

import p1_persona_dialogue_mechanism as mechanism
import p1_persona_dialogue_mechanism_analysis_v2 as analysis_v2


s, b = mechanism.s, mechanism.b
load, sha256, th, require = s.load, s.sha256, s.th, s.require
DESIGN = Path("docs/validation/p1/persona_dialogue_independent_replication_v2/prospective_design_v2.json")
CASE_BANK = DESIGN.with_name("case_bank_v2.json")
AMENDMENT = DESIGN.with_name("prospective_design_amendment_v3.json")
WORDING = DESIGN.with_name("prospective_wording_clarification_v4.json")
ANALYSIS_AMENDMENT = DESIGN.with_name("prospective_analysis_completion_amendment_v5.json")
FROZEN = DESIGN.with_name("frozen_manifest_v1.json")
AUTHORIZATION = DESIGN.with_name("execution_authorization_v1.json")
PREFLIGHT = DESIGN.with_name("preflight_v1.json")
AUDIT = DESIGN.with_name("execution_audit_v1.json")
ANALYSIS = DESIGN.with_name("analysis_v1.json")
TEST_SOURCE = Path("tests/test_p1_persona_dialogue_independent_replication.py")
STRUCTURAL_TEST_SOURCE = Path("tests/test_p1_persona_dialogue_independent_replication_v2.py")
ANALYSIS_DEPENDENCY = Path("tools/p1_persona_dialogue_mechanism_analysis_v2.py")
PRIOR_BANKS = (
    Path("docs/validation/p1/persona_dialogue_factorial_v1/prospective_design_v1.json"),
    Path("docs/validation/p1/persona_dialogue_factorial_v1/independent_validation_design_v1.json"),
    Path("docs/validation/p1d/independent_candidates_v4/candidate_bank_v1.json"),
)
ROOT = Path("results/p1_persona_dialogue_independent_replication/v2")
BASELINE = Path("docs/validation/p1/persona_dialogue_mechanism_v1/analysis_v2.json")
BUDGET_FROZEN = Path("docs/validation/p1d/budget_calibration_v1/frozen_manifest_v2.json")
DESIGN_SHA = "628bedc18b8aa549cb165fbfb3f33ffbb889b5ad3090d7ef86f58112476c156c"
CASE_BANK_SHA = "a93cd629c0d152e9eb2325399235882beaebf510d4b6e32b24724975554fab8c"
AMENDMENT_SHA = "9cd70fceca8b1fb806bd6b3c3bcb4deccfd974830d2a5e762c1e75a45120d937"
RESPONSE_STATUS_SHA = "7d0cde00dcef5f75f82b9b95b06ba0b7e6a3b9a3f8209aa834be5c60e32ee0cd"
WORDING_SHA = "4cce2737b31022426a58cb7a0ef1e145c8096494dd67deb0b6ad00ad81f1c218"
ANALYSIS_AMENDMENT_SHA = "867aac85c5cc0962a657fa6befc4b05c1b11d877d46cfc901a8a43bb0a8751a3"
BASELINE_SHA = "0e690501107c8031dd3774a8b7845e9b1cf2dc61d7969404d70738e7bb32cef6"
TOKENIZER_SHA = mechanism.TOKENIZER_SHA
BUDGET_FROZEN_SHA = mechanism.BUDGET_FROZEN_SHA
MAX_ATTEMPTS = 96
GENERATION_BASELINE = 106
INFERENCE_BASELINE = 668.7530845000028
PRIMARY_METRICS = ("current_named_selection", "current_preference_choice",
                   "history_target_selection", "surface_style_uptake")


def write_exclusive(path, value):
    return analysis_v2.write_exclusive(path, value)


def source_hashes():
    paths = list(Path("src/personaslm").glob("*.py")) + [
        Path(__file__), TEST_SOURCE, STRUCTURAL_TEST_SOURCE, ANALYSIS_DEPENDENCY,
        DESIGN, CASE_BANK, AMENDMENT, WORDING, ANALYSIS_AMENDMENT, BASELINE,
        BUDGET_FROZEN, *PRIOR_BANKS,
        Path("tools/p1_persona_dialogue_factorial.py"),
        Path("tools/p1_persona_dialogue_mechanism.py"),
        Path("tools/p1d_instruct_smoke.py"), Path("tools/p1d_budget_calibration.py"),
        Path("tools/p1d_format_calibration.py"), Path("tools/p1d_instruct_template_check.py"),
    ]
    root = Path.cwd().resolve()
    return {path.resolve().relative_to(root).as_posix(): sha256(path) for path in paths}


def cfg(plan):
    model = plan["model"]
    return s.Runtime(model["model_file"], model["model_sha256"], model["backend_file"],
                     model_label=model["model_label"])


def construction(design, bank, case, condition_name):
    require(condition_name in {f"C{i}" for i in range(8)},
            "Deactivated controls cannot be materialized")
    condition = design["factors"]["conditions"][condition_name]
    persona = bank["personas"][case["persona_id"]]
    policy = design["prompt_policy"]
    system = (policy["fixed_system_instruction"] + "\n\nSYNTHETIC SPEAKER: " +
              persona["speaker_name"] + "\n\n" + case["fixed_current_notes"])
    blocks = []
    if condition["S"]:
        blocks.append(persona["S_block"])
    if condition["F"]:
        blocks.append(persona["F_block"])
    if blocks:
        system += policy["exact_materialization"]["optional_system_separator"] + \
                  policy["exact_materialization"]["optional_system_separator"].join(blocks)
    messages = [{"role": "system", "content": system}]
    if condition["H"]:
        messages.extend(copy.deepcopy(case["history_messages"]))
    messages.append({"role": "user", "content": case["fixed_current_user"]})
    return {key: condition[key] for key in ("S", "F", "H", "control")}, messages


def _normalized(text):
    value = unicodedata.normalize("NFKC", text).casefold()
    value = value.replace("—", "-").replace("–", "-").replace("―", "-").replace("−", "-")
    return " ".join(value.split())


def _sentences(text):
    value = unicodedata.normalize("NFKC", text).strip()
    return [piece.strip() for piece in re.findall(r"[^.!?]+[.!?]|[^.!?]+$", value)
            if piece.strip()]


def _exact_contains(text, target):
    return re.search(r"(?<!\w)" + re.escape(_normalized(target)) + r"(?!\w)",
                     _normalized(text)) is not None


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def leading_selection(row, text):
    sentences = _sentences(text)
    if not sentences:
        return {"category": "UNRESOLVED_NO_EXACT_TARGET", "selected_target": None,
                "selected_option": None, "first_sentence": None}
    first = _normalized(sentences[0])
    targets = []
    for option in ("A", "B"):
        target = row["options"][option]["canonical"]
        if first == _normalized(f"I recommend {target}."):
            targets.append((f"CURRENT_{option}", target, option))
    for target in row["history_target_strings"]:
        if first == _normalized(f"I recommend {target}."):
            targets.append(("HISTORY_TARGET", target, None))
    unique = {(category, _normalized(target), option): target
              for category, target, option in targets}
    if not unique:
        return {"category": "UNRESOLVED_NO_EXACT_TARGET", "selected_target": None,
                "selected_option": None, "first_sentence": sentences[0]}
    if len(unique) != 1:
        return {"category": "UNRESOLVED_MULTIPLE", "selected_target": None,
                "selected_option": None, "first_sentence": sentences[0]}
    (category, _, option), target = next(iter(unique.items()))
    return {"category": category, "selected_target": target,
            "selected_option": option, "first_sentence": sentences[0]}


def style_score(persona, text, assessable=True):
    checks = persona["operational_style_checks"]
    sentences = _sentences(text)
    second = sentences[1].casefold() if len(sentences) >= 2 else ""
    components = {}
    for check in checks:
        matcher = check["matcher"]
        if matcher == "CASEFOLD_EXACT_PREFIX":
            value = second.startswith(check["value"].casefold())
        elif matcher == "CASEFOLD_EXACT_SUFFIX":
            value = second.endswith(check["value"].casefold())
        elif matcher == "CHAR_COUNT_EQUALS":
            value = text.count(check["value"]) == check["expected"]
        elif matcher == "SENTENCE_COUNT_EQUALS":
            value = len(sentences) == check["expected"]
        else:
            raise RuntimeError("Unknown frozen style matcher: " + matcher)
        components[check["check_id"]] = value
    return {"style_components": components if assessable else None,
            "surface_style_uptake": int(all(components.values())) if assessable else None,
            "sentence_count": len(sentences) if assessable else None}


def automatic_score(row, persona, text, assessable=True):
    if not assessable:
        return {"measurement_state": "BOUNDARY_CENSORED", "selection_category":
            "BOUNDARY_CENSORED", "selected_target": None, "selected_option": None,
            "current_named_selection": None, "current_preference_choice": None,
            "history_target_selection": None, "full_canonical_both": None,
            "exact_current_note_support": None, "outdated_value_adoption": None,
            "outdated_value_applicable": row["history_regime"] == "OUTDATED_CONFLICTING" and
                row["condition"] in ("C6", "C7"), **style_score(persona, text, False)}
    selection = leading_selection(row, text)
    category, option = selection["category"], selection["selected_option"]
    current = category in ("CURRENT_A", "CURRENT_B")
    history = category == "HISTORY_TARGET"
    current_named = 1 if current else 0 if history else None
    preference = int(option == row["preferred_option"]) if current else None
    if current:
        history_selection = 0
    elif history and _normalized(selection["selected_target"]) == _normalized(
            row["history_selected_target"]):
        history_selection = 1
    else:
        history_selection = None
    both = int(all(_exact_contains(text, row["options"][key]["canonical"])
                   for key in ("A", "B")))
    sentences = _sentences(text)
    second = sentences[1] if len(sentences) >= 2 else ""
    if current:
        other = "B" if option == "A" else "A"
        support = any(_exact_contains(second, cue) for cue in row["options"][option]["reason_cues"])
        contradiction = any(_exact_contains(second, cue)
                            for cue in row["options"][other]["reason_cues"])
        reason = ("SUPPORTED" if support and not contradiction else
                  "CONTRADICTED" if contradiction and not support else "UNRESOLVED")
    else:
        reason = None
    outdated_applicable = row["history_regime"] == "OUTDATED_CONFLICTING" and \
        row["condition"] in ("C6", "C7")
    outdated = None
    if outdated_applicable:
        if history and history_selection == 1:
            outdated = 1
        elif current and option == row["history_favored_option"] and option != row["preferred_option"]:
            outdated = 1
        elif current and option == row["preferred_option"]:
            outdated = 0
    return {"measurement_state": "ASSESSED_IDENTIFIABLE_UNIT",
        "selection_category": category, "selected_target": selection["selected_target"],
        "selected_option": option, "current_named_selection": current_named,
        "current_preference_choice": preference, "history_target_selection": history_selection,
        "full_canonical_both": both, "exact_current_note_support": reason,
        "outdated_value_adoption": outdated, "outdated_value_applicable": outdated_applicable,
        **style_score(persona, text, True)}


def validate_design(design=None, bank=None):
    require(sha256(DESIGN) == DESIGN_SHA, "Prospective design changed")
    require(sha256(CASE_BANK) == CASE_BANK_SHA, "Independent case bank changed")
    require(sha256(AMENDMENT) == AMENDMENT_SHA, "Prospective amendment changed")
    require(sha256(WORDING) == WORDING_SHA, "Prospective wording clarification changed")
    require(sha256(ANALYSIS_AMENDMENT) == ANALYSIS_AMENDMENT_SHA,
            "Prospective analysis amendment changed")
    require(sha256(Path("src/personaslm/response_status.py")) == RESPONSE_STATUS_SHA,
            "Response-status implementation changed")
    require(sha256(BASELINE) == BASELINE_SHA and sha256(BUDGET_FROZEN) == BUDGET_FROZEN_SHA,
            "Cumulative budget source changed")
    design, bank = design or load(DESIGN), bank or load(CASE_BANK)
    amendment = load(AMENDMENT)
    wording, analysis_amendment = load(WORDING), load(ANALYSIS_AMENDMENT)
    require(design["status"] == "FROZEN_PROSPECTIVE_DESIGN_NOT_AUTHORIZED_NOT_EXECUTED",
            "Design status")
    require(bank["status"] == "FROZEN_PROSPECTIVE_SYNTHETIC_MATERIALS_NO_OUTPUTS",
            "Case-bank status")
    require(design["authorization"]["execution_authorized"] is False and
            amendment["authorization"]["execution_authorized"] is False and
            amendment["authorization"]["maximum_attempts_if_separately_authorized"] == MAX_ATTEMPTS and
            amendment["authorization"]["retries"] == 0, "Prospective authorization boundary")
    require(amendment["parent_design"] == {"path": DESIGN.as_posix(), "sha256": DESIGN_SHA,
            "preservation": amendment["parent_design"]["preservation"]} and
            amendment["case_bank"]["path"] == CASE_BANK.as_posix() and
            amendment["case_bank"]["sha256"] == CASE_BANK_SHA, "Amendment ancestry")
    require(wording["parents"]["design_v2"]["sha256"] == DESIGN_SHA and
            wording["parents"]["execution_scope_amendment_v3"]["sha256"] == AMENDMENT_SHA and
            wording["parents"]["case_bank"]["sha256"] == CASE_BANK_SHA and
            wording["clarification"]["effective_phrase"] ==
            "controlled synthetic next-turn choice cases", "Wording clarification")
    require(analysis_amendment["parents"]["design_v2"]["sha256"] == DESIGN_SHA and
            analysis_amendment["parents"]["execution_scope_amendment_v3"]["sha256"] ==
            AMENDMENT_SHA and
            analysis_amendment["parents"]["wording_clarification_v4"]["sha256"] ==
            WORDING_SHA and analysis_amendment["parents"]["case_bank"]["sha256"] ==
            CASE_BANK_SHA, "Analysis-amendment ancestry")
    binding = design["bindings"]["case_bank"]
    require(binding == {"path": CASE_BANK.as_posix(), "sha256": CASE_BANK_SHA}, "Case-bank binding")
    require(design["bindings"]["cumulative_budget_source"] ==
            {"path": BASELINE.as_posix(), "sha256": BASELINE_SHA}, "Budget-source binding")
    require(subprocess.check_output(["git", "branch", "--show-current"], text=True).strip() ==
            design["bindings"]["source_branch"], "Source branch changed")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() ==
            design["bindings"]["source_head"], "Source HEAD changed")
    runtime = design["runtime"]
    fixed_runtime = {"threads": 4, "threads_batch": 4, "context_tokens": 4096,
        "gpu_layers": 0, "max_new_tokens": 96, "temperature": 0, "top_p": 1,
        "seed": 42, "stop": [], "ignore_eos": False, "cache_prompt": False,
        "warmup": False, "parallel": 1, "no_context_shift": True}
    for key, value in fixed_runtime.items():
        require(runtime[key] == value, "Runtime changed: " + key)
    budget = amendment["resource_budget"]
    require(budget["requests"] == MAX_ATTEMPTS and
            budget["minimum_available_physical_ram_bytes"] == 3 * 1024 ** 3 and
            budget["minimum_free_output_disk_bytes"] == 1024 ** 3 and
            budget["actual_completion_inference_seconds_ceiling"] == 5760 and
            budget["batch_wall_seconds_ceiling"] == 8640, "Resource budget changed")
    baseline = budget["global_baseline"]
    require(baseline["generations_used"] == GENERATION_BASELINE and
            baseline["inference_wall_seconds_used"] == INFERENCE_BASELINE, "Global baseline changed")
    conditions = design["factors"]["conditions"]
    require(set(conditions) == {f"C{i}" for i in range(8)} | {"N_STYLE", "N_HISTORY"},
            "Condition set")
    personas, cases = bank["personas"], {case["case_id"]: case for case in bank["cases"]}
    require(len(personas) == 4 and len(cases) == 12, "Persona/case count")
    require(Counter(case["persona_id"] for case in cases.values()) ==
            Counter({key: 3 for key in personas}), "Persona balance")
    require(Counter(case["history_regime"] for case in cases.values()) ==
            Counter({"ALIGNED_HELPFUL": 4, "OUTDATED_CONFLICTING": 4, "IRRELEVANT": 4}),
            "History-regime balance")
    require(design["bindings"]["prior_case_banks_for_disjointness"] ==
            [path.as_posix() for path in PRIOR_BANKS[:2]], "Prior-bank bindings")
    old_development, old_validation, p1d = (load(path) for path in PRIOR_BANKS)
    require(not (set(personas) & (set(old_development["personas"]) |
                                  set(old_validation["personas"]))),
            "Persona identity overlaps a prior bank")
    prior_case_ids = {case["case_id"] for case in
                      old_development["cases"] + old_validation["cases"]}
    require(not (set(cases) & prior_case_ids), "Case identity overlaps a prior bank")
    prior_strings = set(_strings(old_development)) | set(_strings(old_validation)) | \
        set(_strings(p1d))
    new_materials = []
    for persona in personas.values():
        new_materials.extend((persona["speaker_name"], persona["S_block"], persona["F_block"]))
    for case in cases.values():
        new_materials.extend((case["fixed_current_notes"], case["fixed_current_user"]))
        new_materials.extend(option["canonical"] for option in case["options"].values())
        new_materials.extend(message["content"] for message in case["history_messages"])
    require(all(material not in prior_strings for material in new_materials),
            "Exact material overlaps a prior bank")
    matcher_set = {"CASEFOLD_EXACT_PREFIX", "CASEFOLD_EXACT_SUFFIX",
                   "CHAR_COUNT_EQUALS", "SENTENCE_COUNT_EQUALS"}
    for persona_id, persona in personas.items():
        require(persona["synthetic"] is True and len(persona["operational_style_checks"]) == 5,
                "Persona material")
        require({check["matcher"] for check in persona["operational_style_checks"]} == matcher_set,
                "Style matcher set")
        prefix = persona["operational_style_checks"][0]["value"]
        require(":" not in prefix and not re.match(r"^[A-Z][A-Za-z_ ]{0,24}:", prefix),
                "Line-label-shaped style prefix")
    for case in cases.values():
        require(case["persona_id"] in personas and case["preferred_option"] in ("A", "B"),
                "Case binding")
        history = " ".join(message["content"] for message in case["history_messages"]).casefold()
        for option in case["options"].values():
            require(option["canonical"] in case["fixed_current_notes"], "Current option absent")
            require(option["canonical"].casefold() not in history, "Current option leaked into history")
            require(all(cue in case["fixed_current_notes"] for cue in option["reason_cues"]),
                    "Reason cue absent from current notes")
        require(case["history_selected_target"] in case["history_target_strings"],
                "History selected target")
        require(all(any(target in message["content"] for message in case["history_messages"])
                    for target in case["history_target_strings"]), "History target absent")
    require(amendment["effective_design"]["effective_conditions"] ==
            [f"C{i}" for i in range(8)] and amendment["effective_design"]["requests"] ==
            MAX_ATTEMPTS, "Effective condition set")
    require(all(item["authorized_attempts"] == 0 for item in
                amendment["effective_design"]["deactivated_conditions"].values()),
            "Controls must remain unexecuted")
    parent = [row for row in design["order"]["requests"]
              if row["condition"] in amendment["effective_design"]["effective_conditions"]]
    expected = [{**row, "order": index} for index, row in enumerate(parent)]
    require(amendment["order"]["requests"] == expected, "Frozen amended order")
    require(set(design["estimands"]["factorial_weights"]) == {"S", "F", "H", "FxH"},
            "Factorial estimands")
    require(analysis_amendment["factorial_effect_matrix"]["effects"] ==
            ["S", "F", "H", "SxF", "SxH", "FxH", "SxFxH"] and
            tuple(analysis_amendment["factorial_effect_matrix"]["narrow_automatic_metrics"]) ==
            PRIMARY_METRICS, "Factorial effect matrix")
    require(all(analysis_amendment["factorial_weights"][effect] ==
                design["estimands"]["factorial_weights"][effect]
                for effect in ("S", "F", "H", "FxH")), "Inherited factorial weights changed")
    affixes = []
    for persona in personas.values():
        affixes.append((
            next(check["value"] for check in persona["operational_style_checks"]
                 if check["matcher"] == "CASEFOLD_EXACT_PREFIX"),
            next(check["value"] for check in persona["operational_style_checks"]
                 if check["matcher"] == "CASEFOLD_EXACT_SUFFIX")))
    boundary_calls = 0
    for prefix, suffix in affixes:
        for case in cases.values():
            for option in ("A", "B"):
                target = case["options"][option]["canonical"]
                probe = f"I recommend {target}. {prefix} current evidence {suffix}"
                boundary = b.classify_response(probe, {"stop_type": "eos", "stop": True,
                                                        "truncated": False}, declared_stops=())
                require(boundary["unit_identifiable"] and
                        "unrecognized_line_label" not in boundary["reasons"],
                        "Boundary style probe")
                require(leading_selection({**case, "condition": "C0"}, probe)["category"] ==
                        f"CURRENT_{option}", "Current-target parser probe")
                boundary_calls += 1
            for archived_target in case["history_target_strings"]:
                probe = f"I recommend {archived_target}. {prefix} archived evidence {suffix}"
                boundary = b.classify_response(probe, {"stop_type": "eos", "stop": True,
                                                        "truncated": False}, declared_stops=())
                require(boundary["unit_identifiable"] and
                        "unrecognized_line_label" not in boundary["reasons"],
                        "Boundary history-target probe")
                require(leading_selection({**case, "condition": "C3"}, probe)["category"] ==
                        "HISTORY_TARGET", "History-target parser probe")
                boundary_calls += 1
    require(boundary_calls == 192, "Boundary probe count")
    return {"personas": 4, "cases": 12, "conditions": 8, "requests": MAX_ATTEMPTS,
            "boundary_parser_probes": boundary_calls,
            "history_regimes": dict(Counter(case["history_regime"] for case in cases.values()))}


def authorization_requirements():
    design = load(DESIGN)
    validate_design(design, load(CASE_BANK))
    return {"schema_version": "personaslm_independent_replication_execution_authorization_v1",
        "status": "AUTHORIZED_BEFORE_TOKENIZATION_OR_MODEL_EXECUTION",
        "authorization_path": AUTHORIZATION.as_posix(),
        "implementation": {
            "runner": {"path": Path(__file__).resolve().relative_to(Path.cwd().resolve()).as_posix(),
                       "sha256": sha256(Path(__file__))},
            "test": {"path": TEST_SOURCE.as_posix(), "sha256": sha256(TEST_SOURCE)}},
        "source_hashes": source_hashes(),
        "design": {"path": DESIGN.as_posix(), "sha256": DESIGN_SHA},
        "prospective_amendment": {"path": AMENDMENT.as_posix(), "sha256": AMENDMENT_SHA},
        "wording_clarification": {"path": WORDING.as_posix(), "sha256": WORDING_SHA},
        "analysis_completion_amendment": {"path": ANALYSIS_AMENDMENT.as_posix(),
                                           "sha256": ANALYSIS_AMENDMENT_SHA},
        "case_bank": {"path": CASE_BANK.as_posix(), "sha256": CASE_BANK_SHA},
        "budget_source": {"path": BASELINE.as_posix(), "sha256": BASELINE_SHA},
        "model_sha256": design["model"]["artifact_sha256"],
        "backend_sha256": design["runtime"]["backend_sha256"],
        "template_sha256": design["runtime"]["chat_template_sha256"],
        "maximum_tokenizer_calls": MAX_ATTEMPTS, "maximum_generation_attempts": MAX_ATTEMPTS,
        "retries": 0, "hidden_warmups": 0,
        "minimum_available_physical_ram_bytes": 3 * 1024 ** 3,
        "minimum_free_output_disk_bytes": 1024 ** 3,
        "actual_completion_inference_seconds_ceiling": 5760,
        "batch_wall_seconds_ceiling": 8640,
        "global_baseline": copy.deepcopy(design["resource_budget"]["global_baseline"]),
        "results_root": ROOT.as_posix()}


def validate_authorization(path=AUTHORIZATION):
    authorization = load(path)
    for key, expected in authorization_requirements().items():
        require(authorization.get(key) == expected, "Execution authorization changed: " + key)
    require(authorization.get("researcher") == "Yaxin ZHENG", "Researcher authorization missing")
    return authorization


def validate_plan(plan):
    require(plan["version"] == "p1_persona_dialogue_independent_replication_manifest_v1",
            "Manifest version")
    require(plan["design_sha256"] == DESIGN_SHA and plan["case_bank_sha256"] == CASE_BANK_SHA,
            "Design/case binding")
    require(plan["prospective_amendment_sha256"] == sha256(AMENDMENT) == AMENDMENT_SHA,
            "Prospective-amendment binding")
    require(plan["wording_clarification_sha256"] == sha256(WORDING) == WORDING_SHA,
            "Wording-clarification binding")
    require(plan["analysis_completion_amendment_sha256"] ==
            sha256(ANALYSIS_AMENDMENT) == ANALYSIS_AMENDMENT_SHA,
            "Analysis-completion binding")
    require(Path(plan["authorization_path"]).resolve() == AUTHORIZATION.resolve(),
            "Official authorization path changed")
    require(plan["authorization_sha256"] == sha256(Path(plan["authorization_path"])),
            "Registration authorization changed")
    validate_authorization(Path(plan["authorization_path"]))
    design, bank, amendment = load(DESIGN), load(CASE_BANK), load(AMENDMENT)
    checks = validate_design(design, bank)
    require(plan["registration_source_hashes"] == source_hashes(), "Registered source changed")
    expected_model = {"model_label": design["model"]["label"],
        "model_file": design["model"]["artifact_path"],
        "model_sha256": design["model"]["artifact_sha256"],
        "backend_file": design["runtime"]["backend_path"],
        "backend_sha256": design["runtime"]["backend_sha256"],
        "quantization": design["model"]["quantization"],
        "artifact_revision": design["model"]["artifact_revision"],
        "intended_upstream_revision": design["model"]["intended_upstream_revision"],
        "conversion_lineage": design["model"]["conversion_lineage"]}
    require(plan["model"] == expected_model and plan["runtime"] == design["runtime"],
            "Frozen model/runtime changed")
    require(plan["resource_budget"] == amendment["resource_budget"],
            "Frozen resource budget changed")
    require(plan["new_model_generations"] == 0 and plan["deactivated_conditions"] ==
            amendment["effective_design"]["deactivated_conditions"], "Registration state changed")
    require(plan["template_sha256"] == sha256(Path(plan["template_path"])), "Template changed")
    native = load(BUDGET_FROZEN)["native_tokenizer_identity"]
    require(plan["native_tokenizer_identity"] == {
        "path": Path(design["runtime"]["backend_path"]).with_name("llama-tokenize.exe").as_posix(),
        "tokenizer_sha256": TOKENIZER_SHA, "dll_hashes": native["dll_hashes"]},
        "Native tokenizer identity changed")
    cases = {case["case_id"]: case for case in bank["cases"]}
    template = Path(plan["template_path"]).read_text(encoding="utf-8")
    rows = plan["requests"]
    require(len(rows) == len({row["request_id"] for row in rows}) == MAX_ATTEMPTS, "Rows")
    require([(row["order"], row["request_id"], row["case_id"], row["condition"])
             for row in rows] == [(row["order"], row["request_id"], row["case_id"],
                                    row["condition"])
                                   for row in amendment["order"]["requests"]],
            "Effective request order changed")
    require(len(plan["native_tokenizer_logs"]) == MAX_ATTEMPTS and
            len({record["path"] for record in plan["native_tokenizer_logs"]}) == MAX_ATTEMPTS,
            "Native tokenizer log inventory")
    for index, row in enumerate(rows):
        require(row["order"] == index, "Row order")
        case = cases[row["case_id"]]
        factors, messages = construction(design, bank, case, row["condition"])
        require(row["factors"] == factors and row["messages"] == messages, "Prompt changed")
        expected_metadata = {"persona_id": case["persona_id"],
            "history_regime": case["history_regime"],
            "preferred_option": case["preferred_option"],
            "history_favored_option": case["history_favored_option"],
            "options": case["options"], "history_target_strings": case["history_target_strings"],
            "history_selected_target": case["history_selected_target"],
            "metric_applicability": case["metric_applicability"],
            "current_notes_sha256": th(case["fixed_current_notes"]),
            "current_user_sha256": th(case["fixed_current_user"]),
            "max_new_tokens": 96, "seed": 42, "temperature": 0.0, "top_p": 1.0,
            "stop": [], "cache_prompt": False, "ignore_eos": False}
        require(all(row[key] == value for key, value in expected_metadata.items()),
                "Scoring or generation metadata changed")
        require(row["prompt"] == s.render(template, messages), "Rendered prompt changed")
        require(row["prompt_sha256"] == th(row["prompt"]), "Prompt hash")
        require(row["input_token_ids_sha256"] == th(str(row["input_token_ids"])) and
                len(row["input_token_ids"]) == row["input_tokens"], "Token binding")
        require(row["input_tokens"] + row["max_new_tokens"] <= 4096, "Context overflow")
        require(row["request_sha256"] == th(json.dumps(
            {key: value for key, value in row.items() if key != "request_sha256"},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"))), "Request hash")
        record = plan["native_tokenizer_logs"][index]
        expected_path = ROOT / "native_tokenizer" / f"{index:04d}.json"
        require(record["path"] == expected_path.as_posix() and
                sha256(expected_path) == record["sha256"], "Tokenizer log changed")
        token_log = load(expected_path)
        require(token_log["returncode"] == token_log["generation_requests"] == 0 and
                token_log["prompt_sha256"] == row["prompt_sha256"] and
                ast.literal_eval(token_log["stdout"].strip()) == row["input_token_ids"],
                "Tokenizer log content changed")
    for case_id in cases:
        group = [row for row in rows if row["case_id"] == case_id]
        require({row["condition"] for row in group} ==
                set(amendment["effective_design"]["effective_conditions"]),
                "Cell coverage")
        require(len({row["current_notes_sha256"] for row in group}) == 1 and
                len({row["current_user_sha256"] for row in group}) == 1,
                "Current material invariant")
    return {**checks, "input_token_range": [min(row["input_tokens"] for row in rows),
                                              max(row["input_tokens"] for row in rows)]}


def register(authorization_path):
    """Freeze prompts and native token IDs; this action makes no model completion calls."""
    require(not FROZEN.exists(), "Registration exists; do not replace")
    require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
            "Execution evidence exists")
    require(not (ROOT / "native_tokenizer").exists(), "Tokenizer evidence exists; do not replace")
    authorization_path = Path(authorization_path)
    require(authorization_path.resolve() == AUTHORIZATION.resolve(),
            "Registration requires the frozen official authorization path")
    authorization = validate_authorization(authorization_path)
    design, bank, amendment = load(DESIGN), load(CASE_BANK), load(AMENDMENT)
    checks = validate_design(design, bank)
    runtime, model = design["runtime"], design["model"]
    require(sha256(Path(model["artifact_path"])) == model["artifact_sha256"], "Model changed")
    require(sha256(Path(runtime["backend_path"])) == runtime["backend_sha256"],
            "Backend changed")
    require(sha256(Path(runtime["chat_template_path"])) == runtime["chat_template_sha256"],
            "Template changed")
    budget_frozen = load(BUDGET_FROZEN)
    native = budget_frozen["native_tokenizer_identity"]
    tokenizer = Path(runtime["backend_path"]).with_name("llama-tokenize.exe")
    require(sha256(BUDGET_FROZEN) == BUDGET_FROZEN_SHA and
            native["tokenizer_sha256"] == TOKENIZER_SHA and sha256(tokenizer) == TOKENIZER_SHA,
            "Tokenizer identity changed")
    require({path.name: sha256(path) for path in tokenizer.parent.glob("*.dll")} ==
            native["dll_hashes"], "Backend DLL set changed")
    require(s.memory_observation(os.getpid()).get("system", {}).get("available_physical", 0) >=
            3 * 1024 ** 3, "Less than 3 GiB available RAM")
    require(shutil.disk_usage(".").free >= 1024 ** 3, "Less than 1 GiB free output disk")
    template = Path(runtime["chat_template_path"]).read_text(encoding="utf-8")
    cases = {case["case_id"]: case for case in bank["cases"]}
    rows, logs = [], []
    for item in amendment["order"]["requests"]:
        case = cases[item["case_id"]]
        factors, messages = construction(design, bank, case, item["condition"])
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
            "messages": messages, "prompt": prompt, "prompt_sha256": th(prompt),
            "input_token_ids": token_ids, "input_tokens": len(token_ids),
            "input_token_ids_sha256": th(str(token_ids)),
            "preferred_option": case["preferred_option"],
            "history_favored_option": case["history_favored_option"],
            "options": case["options"], "history_target_strings": case["history_target_strings"],
            "history_selected_target": case["history_selected_target"],
            "metric_applicability": case["metric_applicability"],
            "current_notes_sha256": th(case["fixed_current_notes"]),
            "current_user_sha256": th(case["fixed_current_user"]),
            "max_new_tokens": 96, "seed": 42, "temperature": 0.0, "top_p": 1.0,
            "stop": [], "cache_prompt": False, "ignore_eos": False}
        require(row["input_tokens"] + row["max_new_tokens"] <= runtime["context_tokens"],
                "Context overflow")
        row["request_sha256"] = th(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                                separators=(",", ":")))
        rows.append(row)
    frozen_model = {"model_label": model["label"], "model_file": model["artifact_path"],
        "model_sha256": model["artifact_sha256"], "backend_file": runtime["backend_path"],
        "backend_sha256": runtime["backend_sha256"], "quantization": model["quantization"],
        "artifact_revision": model["artifact_revision"],
        "intended_upstream_revision": model["intended_upstream_revision"],
        "conversion_lineage": model["conversion_lineage"]}
    plan = {"version": "p1_persona_dialogue_independent_replication_manifest_v1",
        "evidence_level": amendment["effective_design"]["evidence_level"],
        "design_path": DESIGN.as_posix(), "design_sha256": DESIGN_SHA,
        "prospective_amendment_path": AMENDMENT.as_posix(),
        "prospective_amendment_sha256": AMENDMENT_SHA,
        "wording_clarification_path": WORDING.as_posix(),
        "wording_clarification_sha256": WORDING_SHA,
        "analysis_completion_amendment_path": ANALYSIS_AMENDMENT.as_posix(),
        "analysis_completion_amendment_sha256": ANALYSIS_AMENDMENT_SHA,
        "case_bank_path": CASE_BANK.as_posix(), "case_bank_sha256": CASE_BANK_SHA,
        "authorization_path": authorization_path.as_posix(),
        "authorization_sha256": sha256(authorization_path), "model": frozen_model,
        "template_path": runtime["chat_template_path"],
        "template_sha256": runtime["chat_template_sha256"], "runtime": runtime,
        "resource_budget": amendment["resource_budget"], "requests": rows,
        "native_tokenizer_identity": {"path": tokenizer.as_posix(),
            "tokenizer_sha256": TOKENIZER_SHA, "dll_hashes": native["dll_hashes"]},
        "native_tokenizer_logs": logs, "registration_source_hashes": source_hashes(),
        "registered_utc": b.utc_now(), "new_model_generations": 0,
        "deactivated_conditions": copy.deepcopy(
            amendment["effective_design"]["deactivated_conditions"])}
    require(authorization["maximum_generation_attempts"] == len(rows) == MAX_ATTEMPTS,
            "Authorization row count")
    write_exclusive(FROZEN, plan)
    validate_plan(load(FROZEN))
    return {"status": "REGISTERED_NO_GENERATIONS", "manifest_sha256": sha256(FROZEN),
            "authorization_sha256": sha256(authorization_path), "tokenizer_calls": len(rows),
            "generation_requests": 0, **checks}


def preflight(check_headroom=True, require_unused=True):
    plan = load(FROZEN)
    checks = validate_plan(plan)
    authorization = validate_authorization(Path(plan["authorization_path"]))
    require(plan["authorization_sha256"] == sha256(Path(plan["authorization_path"])),
            "Authorization changed")
    config = cfg(plan)
    identity = b.file_preflight(config)
    require(identity["status"] == "PASS" and
            identity["model"]["sha256"] == plan["model"]["model_sha256"] and
            identity["server"]["sha256"] == plan["model"]["backend_sha256"],
            "Model/backend identity")
    native = plan["native_tokenizer_identity"]
    tokenizer = Path(native["path"])
    require(sha256(tokenizer) == native["tokenizer_sha256"] == TOKENIZER_SHA,
            "Tokenizer identity")
    require({path.name: sha256(path) for path in tokenizer.parent.glob("*.dll")} ==
            native["dll_hashes"], "Backend DLL set changed")
    for record in plan["native_tokenizer_logs"]:
        require(sha256(Path(record["path"])) == record["sha256"], "Tokenizer log changed")
    baseline = load(BASELINE)["cumulative_authorization_after"]
    require(baseline["generations_used"] == GENERATION_BASELINE and
            baseline["inference_seconds_used"] == INFERENCE_BASELINE,
            "Cumulative baseline changed")
    require(baseline["generations_limit"] - GENERATION_BASELINE >= MAX_ATTEMPTS and
            baseline["inference_seconds_limit"] - INFERENCE_BASELINE >=
            plan["resource_budget"]["actual_completion_inference_seconds_ceiling"],
            "Cumulative budget insufficient")
    if require_unused:
        require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
                "Existing allocation: no repeat")
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
        "authorization_sha256": sha256(Path(plan["authorization_path"])),
        "design_sha256": DESIGN_SHA, "prospective_amendment_sha256": AMENDMENT_SHA,
        "wording_clarification_sha256": WORDING_SHA,
        "analysis_completion_amendment_sha256": ANALYSIS_AMENDMENT_SHA,
        "case_bank_sha256": CASE_BANK_SHA, "source_hashes": source_hashes(),
        "configuration": config.as_dict(), "server_command": s.command(plan),
        "memory_before_run": memory, "cumulative_baseline": baseline,
        "live_gate": "All 96 parse_special=true token arrays must match before any completion.",
        "deactivated_controls": {"N_STYLE": "NOT_EXECUTED", "N_HISTORY": "NOT_EXECUTED"},
        "authorization": {"researcher": authorization["researcher"],
                          "maximum_attempts": MAX_ATTEMPTS, "retries": 0}}


def preflight_receipt():
    """Return a persistent-safe PASS/FAIL receipt without launching a model server."""
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
        observed = {}
        for name, path in (("design", DESIGN), ("prospective_amendment", AMENDMENT),
                           ("wording_clarification", WORDING), ("case_bank", CASE_BANK),
                           ("analysis_completion_amendment", ANALYSIS_AMENDMENT),
                           ("manifest", FROZEN), ("baseline", BASELINE)):
            observed[name] = sha256(path) if path.is_file() else None
        return {"status": "FAIL", "checked_utc": b.utc_now(),
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "expected_bindings": {"design_sha256": DESIGN_SHA,
                "prospective_amendment_sha256": AMENDMENT_SHA,
                "wording_clarification_sha256": WORDING_SHA,
                "analysis_completion_amendment_sha256": ANALYSIS_AMENDMENT_SHA,
                "case_bank_sha256": CASE_BANK_SHA, "baseline_sha256": BASELINE_SHA},
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
        "human_semantic_ratings": 0,
        "evidence_level": "PROSPECTIVE_INDEPENDENT_CASE_SYNTHETIC_REPLICATION"}


STARTED = "independent_replication_generation_started"
RAW = "independent_replication_raw_generation"
DERIVED = "independent_replication_result"


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
    require(claim["manifest_sha256"] == sha256(FROZEN), "Claim/manifest binding changed")
    require(claim["authorization_sha256"] == sha256(Path(plan["authorization_path"])),
            "Claim/authorization binding changed")
    require(claim["design_sha256"] == sha256(DESIGN) == DESIGN_SHA,
            "Claim/design binding changed")
    require(claim["prospective_amendment_sha256"] == sha256(AMENDMENT) == AMENDMENT_SHA,
            "Claim/amendment binding changed")
    require(claim["wording_clarification_sha256"] == sha256(WORDING) == WORDING_SHA,
            "Claim/wording binding changed")
    require(claim["analysis_completion_amendment_sha256"] ==
            sha256(ANALYSIS_AMENDMENT) == ANALYSIS_AMENDMENT_SHA,
            "Claim/analysis-amendment binding changed")
    require(claim["case_bank_sha256"] == sha256(CASE_BANK) == CASE_BANK_SHA,
            "Claim/case-bank binding changed")
    require(run_manifest["claim"] == claim, "Journal claim changed")
    require(run_manifest["frozen_manifest"] == plan, "Journal manifest changed")
    require(run_manifest["authorization"] == authorization, "Journal authorization changed")
    return True


def run(preflight_path):
    preflight_path = Path(preflight_path)
    fresh, stored, plan = preflight(), load(preflight_path), load(FROZEN)
    require(stored.get("status") == fresh.get("status") == "PASS",
            "Run requires a frozen passing preflight")
    keys = ("manifest_sha256", "authorization_sha256", "design_sha256",
            "prospective_amendment_sha256", "wording_clarification_sha256",
            "analysis_completion_amendment_sha256", "case_bank_sha256", "source_hashes",
            "configuration", "server_command")
    for key in keys:
        require(fresh[key] == stored[key], "Preflight binding changed: " + key)
    with b.writer_lock(ROOT):
        require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
                "Existing allocation: no repeat or resume")
        claim = {key: fresh[key] for key in ("manifest_sha256", "authorization_sha256",
                 "design_sha256", "prospective_amendment_sha256",
                 "wording_clarification_sha256", "analysis_completion_amendment_sha256",
                 "case_bank_sha256", "source_hashes")}
        claim.update(preflight_sha256=sha256(preflight_path), maximum_attempts=MAX_ATTEMPTS,
                     retries=0, hidden_warmups=0)
        write_exclusive(ROOT / "claim.json", claim)
        authorization = load(Path(plan["authorization_path"]))
        journal = b.RunJournal(ROOT / "runs", {
            "phase": "P1 independent synthetic controlled next-turn choice replication",
            "evidence_level": "PROSPECTIVE_INDEPENDENT_CASE_SYNTHETIC_REPLICATION",
            "claim": claim, "frozen_manifest": plan, "authorization": authorization,
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
        inference_seconds, failed_completion_seconds = 0.0, 0.0
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
                    require(tokens == row["input_token_ids"], "Live native tokenizer changed")
                    journal.write("live_prompt_verified", {"request_id": row["request_id"],
                                  "token_ids_sha256": th(str(tokens))})
                journal.write("live_preflight_pass", {"prompts": MAX_ATTEMPTS,
                                                       "completed_inference": 0})
                print(json.dumps({"live_preflight": "PASS", "planned": MAX_ATTEMPTS}), flush=True)
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
                        failed_latency = time.monotonic() - tick
                        inference_seconds += failed_latency
                        failed_completion_seconds += failed_latency
                        journal.write("independent_replication_completion_failed", {
                            "request_id": active, "elapsed_seconds": failed_latency})
                        raise
                    latency = time.monotonic() - tick
                    inference_seconds += latency
                    journal.write(RAW, {"request_id": active, "response": response,
                                        "latency_seconds": latency})
                    derived = result(row, personas[row["persona_id"]], response, latency)
                    journal.write(DERIVED, derived)
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
        summary = {"status": status, "attempted": len(attempted),
            "responses_received": len(raw), "results": len(derived),
            "inference_wall_seconds": (sum(value["latency_seconds"] for value in raw.values()) +
                                       failed_completion_seconds),
            "failed_completion_seconds": failed_completion_seconds,
            "batch_wall_seconds": time.monotonic() - started,
            "run_directory": journal.directory.as_posix(), "retries": 0,
            "hidden_warmups": 0, "human_semantic_ratings": 0,
            "deactivated_control_attempts": {"N_STYLE": 0, "N_HISTORY": 0}}
        journal.finish(**summary)
        write_exclusive(journal.directory / "summary.json", summary)
        return summary


def replay():
    plan = load(FROZEN)
    validate_plan(plan)
    folders = list((ROOT / "runs").glob("*"))
    require(len(folders) == 1, "Unexpected run count")
    folder = folders[0]
    events = b.read_events(folder)
    claim = load(ROOT / "claim.json")
    authorization = load(Path(plan["authorization_path"]))
    validate_run_bindings(claim, load(folder / "manifest.json"), plan, authorization)
    attempted, raw, derived = inventory(plan, events)
    require(events and events[-1]["kind"] == "run_finished", "Missing terminal run event")
    require(load(folder / "summary.json") == events[-1]["data"],
            "Summary/terminal event changed")
    if events[-1]["data"]["status"] == "PASS":
        require(sum(event["kind"] == "postflight" for event in events) == 1,
                "Successful run lacks postflight")
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
    sent = [event["data"]["payload"] for event in events if event["kind"] == "http_request" and
            event["data"]["route"] == "/completion"]
    require(sent == [payload(row) for row in plan["requests"][:len(attempted)]],
            "Actual completion payload changed")
    bodies = [json.loads(base64.b64decode(event["data"]["body_base64"])) for event in events
              if event["kind"] == "http_response" and
              event["data"]["route"] == "/completion" and
              event["data"].get("status") == 200]
    require(bodies == [record["response"] for record in raw.values()],
            "Raw HTTP response changed")
    personas = load(CASE_BANK)["personas"]
    rows = []
    for row in plan["requests"]:
        request_id = row["request_id"]
        reconstructed = (result(row, personas[row["persona_id"]], raw[request_id]["response"],
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
            "request_sha256": row["request_sha256"], "case_id": row["case_id"],
            "condition": row["condition"], "state": state,
            "raw_text_sha256": None if result_row is None else result_row["raw_text_sha256"],
            "first_reply_sha256": None if result_row is None else result_row["first_reply_sha256"],
            "generated_tokens": None if result_row is None else result_row["generated_tokens"],
            "stop_reason": None if result_row is None else result_row["stop_reason"],
            "latency_seconds": None if result_row is None else result_row["latency_seconds"],
            "automatic_score": None if result_row is None else result_row["automatic_score"]})
    return {"version": "p1_persona_dialogue_independent_replication_integrity_v1",
        "integrity_status": "PASS", "manifest_sha256": sha256(FROZEN),
        "design_sha256": DESIGN_SHA, "prospective_amendment_sha256": AMENDMENT_SHA,
        "wording_clarification_sha256": WORDING_SHA,
        "analysis_completion_amendment_sha256": ANALYSIS_AMENDMENT_SHA,
        "case_bank_sha256": CASE_BANK_SHA,
        "run_directory": folder.as_posix(),
        "attempted": sum(state != "UNATTEMPTED" for _, _, state in rows),
        "results": sum(state == "COMPLETED" for _, _, state in rows),
        "http_responses_verified": bodies, "journal_events": len(events), "rows": public,
        "raw_text_embedded": False, "new_generations_during_audit": 0,
        "deactivated_control_attempts": {"N_STYLE": 0, "N_HISTORY": 0}}


def mean(values):
    return None if not values else sum(values) / len(values)


def binary_summary(scores, metric):
    values = [score[metric] for score in scores]
    ones = sum(value == 1 for value in values)
    zeros = sum(value == 0 for value in values)
    missing = sum(value is None for value in values)
    total = len(values)
    resolved = [value for value in values if value is not None]
    return {"ones": ones, "zeros": zeros, "missing": missing, "total_slots": total,
        "resolved_denominator": len(resolved), "mean_resolved": mean(resolved),
        "logical_lower": ones / total, "logical_upper": (ones + missing) / total}


def weighted_contrast(by_case, case_ids, weights, metric, persona_by_case=None):
    """Aggregate frozen case-level factorial weights with logical missing bounds."""
    records = []
    for case_id in sorted(case_ids):
        contribution, lower, upper, complete = 0.0, 0.0, 0.0, True
        for condition, weight in weights.items():
            value = by_case[case_id][condition][metric]
            if value is None:
                complete = False
                lower += min(0.0, weight)
                upper += max(0.0, weight)
            else:
                contribution += weight * value
                lower += weight * value
                upper += weight * value
        records.append({"case_id": case_id,
            "persona_id": None if persona_by_case is None else persona_by_case[case_id],
            "contribution": contribution if complete else None,
            "logical_lower": lower, "logical_upper": upper})
    complete_values = [record["contribution"] for record in records
                       if record["contribution"] is not None]
    personas = sorted({record["persona_id"] for record in records
                       if record["persona_id"] is not None})
    leave_one_out = {}
    for persona_id in personas:
        kept = [record for record in records if record["persona_id"] != persona_id]
        values = [record["contribution"] for record in kept
                  if record["contribution"] is not None]
        leave_one_out[persona_id] = {"complete_case_estimate": mean(values),
            "complete_cases": len(values),
            "logical_lower": mean([record["logical_lower"] for record in kept]),
            "logical_upper": mean([record["logical_upper"] for record in kept])}
    loo_values = [value["complete_case_estimate"] for value in leave_one_out.values()
                  if value["complete_case_estimate"] is not None]
    return {"metric": metric, "weights": weights, "eligible_cases": len(records),
        "complete_cases": len(complete_values),
        "unresolved_cases": len(records) - len(complete_values),
        "complete_case_estimate": mean(complete_values),
        "logical_lower": mean([record["logical_lower"] for record in records]),
        "logical_upper": mean([record["logical_upper"] for record in records]),
        "case_contributions": records, "leave_one_persona_out": leave_one_out,
        "leave_one_persona_out_point_estimate_range":
            [min(loo_values), max(loo_values)] if loo_values else [None, None]}


def _distribution(values, missing_label="MISSING_OR_NOT_APPLICABLE"):
    return dict(sorted(Counter(missing_label if value is None else str(value)
                               for value in values).items()))


def build_effect_matrix(by_case, case_ids, weights_by_effect, persona_by_case):
    return {effect: {metric: weighted_contrast(by_case, case_ids, weights, metric,
                                                persona_by_case)
                     for metric in PRIMARY_METRICS}
            for effect, weights in weights_by_effect.items()}


def analyze():
    plan = load(FROZEN)
    validate_plan(plan)
    require(AUDIT.is_file(), "Frozen execution audit required before analysis")
    reconstructed_audit = audit()
    require(load(AUDIT) == reconstructed_audit, "Execution audit changed")
    design, amendment, bank = load(DESIGN), load(AMENDMENT), load(CASE_BANK)
    analysis_amendment = load(ANALYSIS_AMENDMENT)
    folder, events, rows, _ = replay()
    require(all(state == "COMPLETED" for _, _, state in rows),
            "Complete 96-row run required")
    by_condition, by_case, persona_by_case, regime_by_case = defaultdict(list), \
        defaultdict(dict), {}, {}
    results_only = []
    for row, result_row, _ in rows:
        score = result_row["automatic_score"]
        by_condition[row["condition"]].append(score)
        by_case[row["case_id"]][row["condition"]] = score
        persona_by_case[row["case_id"]] = row["persona_id"]
        regime_by_case[row["case_id"]] = row["history_regime"]
        results_only.append(result_row)
    condition_summary = {}
    for condition in amendment["effective_design"]["effective_conditions"]:
        scores = by_condition[condition]
        condition_summary[condition] = {
            metric: binary_summary(scores, metric) for metric in PRIMARY_METRICS}
        condition_summary[condition].update({
            "selection_categories": _distribution(
                [score["selection_category"] for score in scores]),
            "exact_current_note_support": _distribution(
                [score["exact_current_note_support"] for score in scores]),
            "full_canonical_both": binary_summary(scores, "full_canonical_both")})
    all_cases = sorted(by_case)
    weights = design["estimands"]["factorial_weights"]
    primary = {
        "F_main_current_preference_choice": weighted_contrast(
            by_case, all_cases, weights["F"], "current_preference_choice", persona_by_case),
        "S_main_surface_style_uptake": weighted_contrast(
            by_case, all_cases, weights["S"], "surface_style_uptake", persona_by_case)}
    primary["H_by_history_regime"] = {}
    for regime in sorted(set(regime_by_case.values())):
        ids = [case_id for case_id in all_cases if regime_by_case[case_id] == regime]
        primary["H_by_history_regime"][regime] = {
            metric: weighted_contrast(by_case, ids, weights["H"], metric, persona_by_case)
            for metric in ("current_preference_choice", "history_target_selection")}
    conflicting = [case_id for case_id in all_cases
                   if regime_by_case[case_id] == "OUTDATED_CONFLICTING"]
    primary["FxH_outdated_conflicting_current_preference_choice"] = weighted_contrast(
        by_case, conflicting, weights["FxH"], "current_preference_choice", persona_by_case)
    factorial_effect_matrix = build_effect_matrix(
        by_case, all_cases, analysis_amendment["factorial_weights"], persona_by_case)
    outdated = {}
    for condition in ("C6", "C7"):
        scores = [by_case[case_id][condition] for case_id in conflicting]
        outdated[condition] = binary_summary(scores, "outdated_value_adoption")
    outdated["C7_minus_C6"] = weighted_contrast(
        by_case, conflicting, {"C6": -1.0, "C7": 1.0},
        "outdated_value_adoption", persona_by_case)
    persona_summary = {}
    for persona_id in sorted(set(persona_by_case.values())):
        ids = [case_id for case_id in all_cases if persona_by_case[case_id] == persona_id]
        persona_summary[persona_id] = {
            "cases": ids,
            "F_main_current_preference_choice": weighted_contrast(
                by_case, ids, weights["F"], "current_preference_choice"),
            "S_main_surface_style_uptake": weighted_contrast(
                by_case, ids, weights["S"], "surface_style_uptake")}
    memory_events = [event["data"] for event in events if event["kind"] == "memory_observation"]
    available = [entry.get("system", {}).get("available_physical") for entry in memory_events]
    available = [value for value in available if value is not None]
    peak = max((entry.get("process", {}).get("peak_working_set", 0)
                for entry in memory_events), default=0)
    latency = sum(item["latency_seconds"] for item in results_only)
    generated = sum(item["generated_tokens"] for item in results_only)
    return {"version": "p1_persona_dialogue_independent_replication_analysis_v1",
        "evidence_level": "PROSPECTIVE_INDEPENDENT_CASE_SYNTHETIC_REPLICATION",
        "effective_description": "controlled synthetic next-turn choice cases",
        "claim_boundary": load(WORDING)["claim_boundary"],
        "analysis_claim_boundary": analysis_amendment["claim_boundary"],
        "manifest_sha256": sha256(FROZEN), "execution_audit_sha256": sha256(AUDIT),
        "design_sha256": DESIGN_SHA, "prospective_amendment_sha256": AMENDMENT_SHA,
        "wording_clarification_sha256": WORDING_SHA,
        "analysis_completion_amendment_sha256": ANALYSIS_AMENDMENT_SHA,
        "case_bank_sha256": CASE_BANK_SHA,
        "run_directory": folder.as_posix(), "generations": len(results_only),
        "human_semantic_ratings": 0, "condition_summary": condition_summary,
        "primary_estimands": primary,
        "factorial_effect_matrix": {
            "status": "EXPLORATORY_DESCRIPTIVE_NOT_CONFIRMATORY",
            "effects": factorial_effect_matrix},
        "persona_summary": persona_summary,
        "outdated_value_adoption": outdated,
        "deactivated_controls": {"N_STYLE": {"status": "NOT_EXECUTED_DEACTIVATED",
                                               "attempts": 0},
                                 "N_HISTORY": {"status": "NOT_EXECUTED_DEACTIVATED",
                                                "attempts": 0}},
        "inferential_policy": {"p_values": "NOT_COMPUTED",
            "estimation_first": True, "logical_missing_outcome_bounds": True,
            "missing_unresolved_or_inapplicable_recoded_as_zero": False,
            "confirmatory_population_claim": False},
        "measurement_limits": bank.get("limitations", []) + design["known_limitations"],
        "resource_observations": {"generated_tokens": generated,
            "native_stop_reason_distribution": _distribution(
                [item["stop_reason"] for item in results_only]),
            "completion_inference_seconds": latency,
            "mean_completion_seconds": latency / len(results_only),
            "server_peak_working_set_bytes": peak,
            "minimum_observed_available_physical_bytes": min(available) if available else None},
        "cumulative_authorization_after": {"generations_limit": 1200,
            "generations_used": GENERATION_BASELINE + len(results_only),
            "inference_seconds_limit": 72000,
            "inference_seconds_used": INFERENCE_BASELINE + latency},
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
                         ensure_ascii=False, sort_keys=True))
    else:
        report = analyze()
        write_exclusive(ANALYSIS, report)
        print(json.dumps({"status": "ANALYZED", "generations": report["generations"],
                          "output": ANALYSIS.as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
