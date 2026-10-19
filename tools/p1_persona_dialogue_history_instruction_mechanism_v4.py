"""Prospective 96-slot History/instruction mechanism study (v4).

This thin adapter reuses the established native-tokenizer, llama.cpp server,
response-boundary, and append-only journal primitives.  Importing or validating
this module performs no tokenization, server launch, or model generation.
"""

from __future__ import annotations

import argparse
import ast
import base64
from collections import Counter, defaultdict
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import time
import unicodedata

import p1_persona_dialogue_history_template_mechanism as engine


base, s, b = engine.base, engine.s, engine.b
load, sha256, th, require = engine.load, engine.sha256, engine.th, engine.require
write_exclusive = engine.write_exclusive

OUT = Path("docs/validation/p1/persona_dialogue_placeholder_mechanism_v4")
DESIGN = OUT / "prospective_design_v4.json"
CASE_BANK = OUT / "case_bank_v4.json"
AMENDMENT = OUT / "prospective_design_amendment_v4_1.json"
MEASUREMENT_CLARIFICATION = OUT / "prospective_measurement_clarification_v4_2.json"
MATERIAL_AUDIT = OUT / "material_ancestry_audit_v4.json"
MATERIAL_REVIEW = OUT / "material_scientific_review_v4.json"
REGISTRATION = OUT / "prospective_registration_v4.json"
AUTHORIZATION = OUT / "execution_authorization_v4.json"
FROZEN = OUT / "frozen_manifest_v4.json"
REGISTRATION_FAILURE = OUT / "registration_failure_v4.json"
PREFLIGHT = OUT / "preflight_v4.json"
AUDIT = OUT / "execution_audit_v4.json"
ANALYSIS = OUT / "analysis_v4.json"
ROOT = Path("results/p1_persona_dialogue_placeholder_mechanism/v4")
TEST_SOURCE = Path("tests/test_p1_persona_dialogue_history_instruction_mechanism_v4.py")
BUDGET_SOURCE = Path(
    "docs/validation/p1/persona_dialogue_disjoint_surface_validation_v3/analysis_v3.json")
TOKENIZER_SOURCE = Path("docs/validation/p1d/budget_calibration_v1/frozen_manifest_v2.json")

DESIGN_SHA = "86429901ba24e5d8ef0a659cc3c1a0d340b58bfd6cd072f1d1c4df2feebd3723"
CASE_BANK_SHA = "a74b20b7b5039fce1035b5162f6a9441cf632c55235e44974837024b84ccc8b8"
AMENDMENT_SHA = "35a7b8e75bb1265c8d4c14da123f0f76bc081a6c38170d326a2d678c18806675"
MEASUREMENT_CLARIFICATION_SHA = "0c1cf6c1200dd9b459730a36de2f5fe09c88b6bebca34346dc6841a03047878d"
BUDGET_SOURCE_SHA = "0a2d4547a6501991d6b9f1855a4f4081ff885bba5e700f226757ace58d182a44"
TOKENIZER_SOURCE_SHA = "510e46b214dda23dea2a3e5462d44982d25b7a9db022626a7a5a1ba504d5e039"
MATERIAL_AUDIT_SHA = "d1b2b7da46d3c4c1a482d48bea1fb1ce450ff26765a2bc9ffbb61761387b7f81"
MATERIAL_REVIEW_SHA = "90eb76d15b0651b158d347f08ab93481e8c6028ac58df94fd8947f371c766758"
REGISTRATION_SHA = "d51fbadad67578640465a3f2f53fb0732e24b0bcf4c183d630c5a5dc0f3af971"

MAX_ATTEMPTS = 96
GENERATION_BASELINE = 508
INFERENCE_BASELINE = 3171.544608799969
GENERATION_LIMIT = 1200
INFERENCE_LIMIT = 72000.0
MIN_PREFLIGHT_RAM = 4 * 1024 ** 3
MIN_LIVE_RAM = 512 * 1024 ** 2
MIN_DISK = 1024 ** 3
INFERENCE_CEILING = 2400.0
WALL_CEILING = 3600.0
NATIVE_PROMPT_TOKENIZER_CALLS = 96
NATIVE_NAME_TOKENIZER_CALLS = 16
NATIVE_TOKENIZER_CALLS = NATIVE_PROMPT_TOKENIZER_CALLS + NATIVE_NAME_TOKENIZER_CALLS
LIVE_TOKENIZER_CHECKS = 96

MATERIAL_REVIEW_VERSION = (
    "personaslm_placeholder_mechanism_material_scientific_review_v4")
MATERIAL_REVIEW_STATUS = "COMPLETE_PRETOKENIZATION_REVIEW"
MATERIAL_REVIEW_VERDICT = "PASS_NO_BLOCKING_MATERIAL_ISSUES"
REGISTRATION_VERSION = "personaslm_placeholder_mechanism_prospective_registration_v4"
REGISTRATION_STATUS = (
    "PROSPECTIVELY_REGISTERED_NOT_AUTHORIZED_NOT_TOKENIZED_NOT_EXECUTED")

# Exact recursive local-tool import closure used by this adapter.  Project-local
# package modules under src/personaslm are bound separately as a complete set.
LOCAL_TOOL_DEPENDENCIES = (
    "tools/p1_persona_dialogue_history_template_mechanism.py",
    "tools/p1_persona_dialogue_independent_replication.py",
    "tools/p1_persona_dialogue_mechanism.py",
    "tools/p1_persona_dialogue_mechanism_analysis_v2.py",
    "tools/p1_persona_dialogue_factorial.py",
    "tools/p1d_instruct_smoke.py",
    "tools/p1d_budget_calibration.py",
    "tools/p1d_format_calibration.py",
    "tools/p1d_instruct_template_check.py",
    "tools/p1d_format_diagnostic_proposal.py",
    "tools/p1c_tokenize.py",
    "tools/p1c_design.py",
    "tools/p1d_design.py",
    "tools/p1d_scientific_audit.py",
)

MODEL = {
    "model_label": "Qwen3.5-2B-native-chat-Q4_K_M-third-party-development",
    "model_file": "models/gguf/instruct_candidates/lmstudio-bb84e113/Qwen3.5-2B-Q4_K_M.gguf",
    "model_sha256": "0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc",
    "backend_file": "bin/llama.cpp/llama-b11573-bin-win-cpu-x64/llama-server.exe",
    "backend_sha256": "71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846",
    "quantization": "Q4_K_M",
    "artifact_revision": "bb84e11355a036e28f080c7793fa6d22b7c4e344",
    "intended_upstream_revision": "965dcc54bc9c0591873df0e9869c056a54d323d1",
    "conversion_lineage": "PARTIALLY_VERIFIED_DEVELOPMENT_ONLY",
}
RUNTIME = {
    "backend_path": MODEL["backend_file"],
    "backend_build": "b11573-0f701c882",
    "backend_sha256": MODEL["backend_sha256"],
    "chat_template_path": (
        "docs/validation/p1d/development_readiness_v1/official_instruct_metadata/"
        "chat_template.jinja"),
    "chat_template_sha256": "0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6",
    "chat_template_kwargs": {"enable_thinking": False},
    "threads": 4,
    "threads_batch": 4,
    "context_tokens": 4096,
    "gpu_layers": 0,
    "max_new_tokens": 96,
    "temperature": 0.0,
    "top_p": 1.0,
    "seed": 42,
    "stop": [],
    "ignore_eos": False,
    "cache_prompt": False,
    "warmup": False,
    "parallel": 1,
    "no_context_shift": True,
}

CONTEXTS = ("C0_NO_HISTORY", "C1_CONTROL_LIVE", "C2_PERSONA_QUOTED",
            "C3_PERSONA_LIVE")
INSTRUCTIONS = ("I0_MINIMAL", "I1_META_LITERAL", "I2_CONCRETE_COPY")
ARMS = tuple(f"{context}__{instruction}"
             for context in CONTEXTS for instruction in INSTRUCTIONS)

BINARY_ENDPOINTS = (
    "literal_placeholder_occurrence",
    "exact_valid_current_output_line",
    "exactly_two_sentence_realization",
    "preferred_current_name_selection",
    "any_current_name_selection",
    "preferred_current_anchor_selection",
    "any_current_anchor_selection",
    "preferred_name_anchor_indicator_discordance",
    "any_archived_entity_occurrence",
    "selected_archived_target_occurrence",
    "unprompted_archived_name_occurrence",
    "control_owner_mention",
    "style_prefix_contract",
    "style_suffix_contract",
)
AUTOMATIC_ENDPOINTS = BINARY_ENDPOINTS + ("evaluator_gap",)
SEMANTIC_ENDPOINTS = (
    "semantic_selected_entity",
    "current_evidence_consistency",
    "reason_supports_selected_choice",
    "response_relevance",
    "conversational_coherence",
    "behavioral_persona_fidelity",
    "linguistic_persona_fidelity",
    "answer_completeness",
    "material_unverifiable_claim",
    "evidence_spans",
)

STARTED = "placeholder_mechanism_v4_generation_started"
RAW = "placeholder_mechanism_v4_raw_generation"
DERIVED = "placeholder_mechanism_v4_result"


def cfg(plan):
    model = plan["model"]
    return s.Runtime(model["model_file"], model["model_sha256"],
                     model["backend_file"], model_label=model["model_label"])


def _normalized(text):
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


def _relative(path):
    return Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix()


def _canonical_json_hash(value):
    return th(json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")))


def _all_prior_bindings(design):
    gate = design["ancestry_and_material_gates"]
    return (gate["bound_prior_case_banks"] +
            gate["bound_prior_designs_and_public_audit"])


def source_hashes():
    design = load(DESIGN)
    paths = list(Path("src/personaslm").glob("*.py")) + [
        Path(__file__), TEST_SOURCE, DESIGN, CASE_BANK, AMENDMENT,
        MEASUREMENT_CLARIFICATION, MATERIAL_AUDIT,
        MATERIAL_REVIEW, REGISTRATION, BUDGET_SOURCE, TOKENIZER_SOURCE,
        *(Path(path) for path in LOCAL_TOOL_DEPENDENCIES),
        *(Path(item["path"]) for item in _all_prior_bindings(design)),
    ]
    unique = {path.resolve(): path for path in paths}
    return {_relative(path): sha256(path)
            for path in sorted(unique, key=lambda item: item.as_posix())}


def _format_instruction(template, case):
    replacements = {
        "{A.anchor}": case["options"]["A"]["anchor"],
        "{A.canonical}": case["options"]["A"]["canonical"],
        "{B.anchor}": case["options"]["B"]["anchor"],
        "{B.canonical}": case["options"]["B"]["canonical"],
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    require("{" not in template and "}" not in template,
            "Unresolved instruction placeholder")
    return template


def construction(design, bank, case, arm_id):
    """Materialize one arm without rendering a native chat template."""
    require(arm_id in ARMS and arm_id in design["arms"], "Unknown v4 arm")
    arm = design["arms"][arm_id]
    context, instruction_id = arm["context_id"], arm["instruction_id"]
    persona = bank["personas"][case["persona_id"]]
    policy = design["prompt_policy"]
    amendment = load(AMENDMENT)
    instruction = _format_instruction(
        policy["instruction_forms"][instruction_id], case)
    system = policy["system_composition_template"].format(
        speaker_name=persona["speaker_name"], S_block=persona["S_block"],
        F_block=persona["F_block"], instruction_form=instruction)
    option_lines = []
    for label in case["current_option_display_order"]:
        option = case["options"][label]
        option_lines.append(policy["current_option_line_template"].format(
            label=label, anchor=option["anchor"], canonical=option["canonical"],
            attribute=option["attribute"]))
    current = policy["current_user_template"].format(
        current_evidence=case["current_evidence"],
        current_options_in_case_display_order="\n".join(option_lines),
        question=case["question"])
    messages = [{"role": "system", "content": system}]
    if context == "C0_NO_HISTORY":
        messages.append({"role": "user", "content": current})
    elif context == "C1_CONTROL_LIVE":
        archive_user = amendment["effective_prompt_replacements"][
            "C1_CONTROL_LIVE.archive_user_template"].format(
            control_speaker_name=persona["control_speaker_name"],
            archive_question=case["archive_question"])
        messages.extend(({"role": "user", "content": archive_user},
                         {"role": "assistant", "content": case["archive_assistant"]},
                         {"role": "user", "content": current}))
    elif context == "C2_PERSONA_QUOTED":
        quoted = policy["context_forms"][context]["quoted_current_user_template"].format(
            speaker_name=persona["speaker_name"],
            archive_question=case["archive_question"],
            archive_assistant=case["archive_assistant"],
            rendered_current_user=current)
        messages.append({"role": "user", "content": quoted})
    else:
        archive_user = amendment["effective_prompt_replacements"][
            "C3_PERSONA_LIVE.archive_user_template"].format(
            speaker_name=persona["speaker_name"],
            archive_question=case["archive_question"])
        messages.extend(({"role": "user", "content": archive_user},
                         {"role": "assistant", "content": case["archive_assistant"]},
                         {"role": "user", "content": current}))
    require([message["role"] for message in messages] ==
            policy["context_forms"][context]["role_sequence"], "Role sequence changed")
    return {"S": 1, "F": 1, "context_id": context,
            "instruction_id": instruction_id}, messages


def request_specs(design=None):
    design = design or load(DESIGN)
    rows = []
    for item in design["order"]["requests"]:
        index = item["request_index"]
        rows.append({"order": index, "request_id": f"pmv4_{index:03d}",
                     "case_id": item["case_id"], "arm_id": item["arm_id"],
                     "round": item["round"], "position": item["position"],
                     "quartile": item["quartile"]})
    return rows


def _material_categories(bank):
    categories = defaultdict(list)
    for persona_id, persona in bank["personas"].items():
        categories["persona_id"].append(persona_id)
        categories["profile_source_id"].extend(
            (persona["profile_source_id"], persona["control_profile_source_id"]))
        categories["speaker_name"].append(persona["speaker_name"])
        categories["control_speaker_name"].append(persona["control_speaker_name"])
        categories["S_block"].append(persona["S_block"])
        categories["F_block"].append(persona["F_block"])
    for case in bank["cases"]:
        categories["case_id"].append(case["case_id"])
        categories["scenario"].append(case["scenario"])
        categories["current_evidence"].append(case["current_evidence"])
        categories["question"].append(case["question"])
        categories["archive_question"].append(case["archive_question"])
        categories["archive_assistant"].append(case["archive_assistant"])
        for option in case["options"].values():
            categories["current_option_canonical"].append(option["canonical"])
            categories["opaque_anchor"].append(option["anchor"])
        categories["archive_entity"].extend(
            option["canonical"] for option in case["archive_options"].values())
    return dict(categories)


def _fourgrams(strings):
    output = set()
    for value in strings:
        words = re.findall(r"[\w']+", _normalized(value), flags=re.UNICODE)
        output.update(" ".join(words[index:index + 4])
                      for index in range(max(0, len(words) - 3)))
    return output


def material_overlap_audit():
    """Recompute the deterministic ancestry audit; never reads protected mappings."""
    design, bank = load(DESIGN), load(CASE_BANK)
    prior_bindings = _all_prior_bindings(design)
    prior_strings = set()
    sources = []
    for binding in prior_bindings:
        path = Path(binding["path"])
        actual = sha256(path)
        require(actual == binding["sha256"], "Prior case bank changed: " + path.as_posix())
        values = {_normalized(value) for value in base._strings(load(path)) if value.strip()}
        prior_strings.update(values)
        sources.append({"path": path.as_posix(), "sha256": actual,
                        "normalized_strings": len(values)})
    categories = _material_categories(bank)
    overlaps = {}
    for name, values in categories.items():
        overlaps[name] = sorted({value for value in values
                                 if _normalized(value) in prior_strings})
    current_values = [value for values in categories.values() for value in values]
    current_fourgrams, prior_fourgrams = _fourgrams(current_values), _fourgrams(prior_strings)
    lexical = sorted(current_fourgrams & prior_fourgrams)
    entity_values = (categories["current_option_canonical"] +
                     categories["archive_entity"])
    entity_hashes = {th(_normalized(value)) for value in entity_values}
    prior_hashes = {th(value) for value in prior_strings}
    question_categories = ("question", "archive_question", "archive_assistant",
                           "S_block", "F_block")
    exact_total = sum(len(values) for values in overlaps.values())
    return {
        "schema_version": "personaslm_material_ancestry_audit_v4",
        "status": "PASS_ZERO_NORMALIZED_EXACT_OVERLAP" if exact_total == 0 else "FAIL",
        "normalization": "Unicode NFC, casefold, whitespace collapse",
        "case_bank": {"path": CASE_BANK.as_posix(), "sha256": sha256(CASE_BANK)},
        "prior_artifacts": sources,
        "protected_mapping_accessed": False,
        "protected_or_local_paths_enumerated": False,
        "new_material_counts": {name: len(values) for name, values in categories.items()},
        "normalized_exact_overlap_by_category": overlaps,
        "normalized_exact_overlap_total": exact_total,
        "canonical_entity_normalized_sha256_overlap": len(entity_hashes & prior_hashes),
        "exact_question_or_template_overlap": sum(
            len(overlaps[name]) for name in question_categories),
        "lexical_fourgram_overlap": {
            "current_unique": len(current_fourgrams),
            "prior_unique": len(prior_fourgrams),
            "intersection_count": len(lexical),
            "intersection_sha256": th("\n".join(lexical)),
            "examples_first_64_sorted": lexical[:64],
            "policy": "Disclosed ordinary-language overlap; not an automatic failure."},
        "scope_limits": [
            "Exact ancestry checks cannot establish semantic independence.",
            "This audit does not establish real-speaker validity or human-review independence.",
            "No model output, tokenizer, protected mapping, or private review artifact was used."],
    }


def assessability(boundary):
    span = boundary.get("first_span", {}).get("text", "")
    return bool(boundary.get("unit_identifiable") and span.strip() and
                boundary.get("status") != "TRUNCATED")


def _line(label, option):
    return f"Option {label} [{option['anchor']}] — {option['canonical']}."


def _unique_mentions(text, values):
    found = [key for key, value in values.items() if base._exact_contains(text, value)]
    return found


def automatic_score(row, text, assessable=True):
    context = row["context_id"]
    states = {endpoint: "MISSING_UNASSESSABLE" for endpoint in AUTOMATIC_ENDPOINTS}
    if not assessable:
        if context == "C0_NO_HISTORY":
            states["any_archived_entity_occurrence"] = "STRUCTURAL_NA"
            states["selected_archived_target_occurrence"] = "STRUCTURAL_NA"
        else:
            states["unprompted_archived_name_occurrence"] = "STRUCTURAL_NA"
        if context != "C1_CONTROL_LIVE":
            states["control_owner_mention"] = "STRUCTURAL_NA"
        return {"measurement_state": "MISSING_UNASSESSABLE",
                "endpoint_states": states,
                **{endpoint: None for endpoint in AUTOMATIC_ENDPOINTS},
                "option_label_selection": None,
                "label_anchor_name_consistency": None,
                "selected_name_option": None, "selected_anchor_option": None,
                "semantic_endpoints": {endpoint: {"state": "HUMAN_ONLY_NOT_RATED",
                                                    "value": None}
                                       for endpoint in SEMANTIC_ENDPOINTS}}
    sentences = base._sentences(text)
    first = sentences[0] if sentences else ""
    options = row["options"]
    names = _unique_mentions(first, {key: value["canonical"]
                                     for key, value in options.items()})
    anchors = _unique_mentions(first, {key: value["anchor"]
                                       for key, value in options.items()})
    name_option = names[0] if len(names) == 1 else None
    anchor_option = anchors[0] if len(anchors) == 1 else None
    labels = sorted(set(re.findall(r"(?i)\boption\s+([ab])\b", first.upper())))
    label = labels[0] if len(labels) == 1 else ("MULTIPLE" if len(labels) > 1 else "NONE")
    identities = []
    multiple = False
    for values in (labels, names, anchors):
        if len(values) > 1:
            multiple = True
        elif len(values) == 1:
            identities.append(values[0])
    if multiple:
        consistency = "MULTIPLE"
    elif not identities:
        consistency = "NONE"
    elif len(set(identities)) == 1:
        consistency = "CONSISTENT"
    else:
        consistency = "CONFLICT"
    preferred = row["preferred_option"]
    valid_lines = [label_id for label_id in ("A", "B")
                   if _normalized(first) == _normalized(_line(label_id, options[label_id]))]
    placeholder = int(bool(re.search(
        r"(?i)<exact\s+[ab]\s+(?:anchor|name)>", text)))
    preferred_name = int(name_option == preferred)
    preferred_anchor = int(anchor_option == preferred)
    archive_mentions = [value for value in row["archive_target_strings"]
                        if base._exact_contains(text, value)]
    second = sentences[1].casefold() if len(sentences) >= 2 else ""
    values = {
        "literal_placeholder_occurrence": placeholder,
        "exact_valid_current_output_line": int(len(valid_lines) == 1),
        "exactly_two_sentence_realization": int(len(sentences) == 2),
        "preferred_current_name_selection": preferred_name,
        "any_current_name_selection": int(name_option is not None),
        "preferred_current_anchor_selection": preferred_anchor,
        "any_current_anchor_selection": int(anchor_option is not None),
        "preferred_name_anchor_indicator_discordance": int(
            preferred_name != preferred_anchor),
        "evaluator_gap": preferred_name - preferred_anchor,
        "any_archived_entity_occurrence": int(bool(archive_mentions)),
        "selected_archived_target_occurrence": int(base._exact_contains(
            text, row["archive_selected_target"])),
        "unprompted_archived_name_occurrence": int(bool(archive_mentions)),
        "control_owner_mention": int(base._exact_contains(
            text, row["control_speaker_name"])),
        "style_prefix_contract": int(second.startswith(row["reason_prefix"].casefold())),
        "style_suffix_contract": int(second.endswith(row["reason_suffix"].casefold())),
    }
    states = {endpoint: "ASSESSED" for endpoint in AUTOMATIC_ENDPOINTS}
    if context == "C0_NO_HISTORY":
        values["any_archived_entity_occurrence"] = None
        values["selected_archived_target_occurrence"] = None
        states["any_archived_entity_occurrence"] = "STRUCTURAL_NA"
        states["selected_archived_target_occurrence"] = "STRUCTURAL_NA"
    else:
        values["unprompted_archived_name_occurrence"] = None
        states["unprompted_archived_name_occurrence"] = "STRUCTURAL_NA"
    if context != "C1_CONTROL_LIVE":
        values["control_owner_mention"] = None
        states["control_owner_mention"] = "STRUCTURAL_NA"
    return {"measurement_state": "ASSESSED_IDENTIFIABLE_UNIT",
            "endpoint_states": states, **values,
            "option_label_selection": label,
            "label_anchor_name_consistency": consistency,
            "selected_name_option": name_option,
            "selected_anchor_option": anchor_option,
            "mentioned_current_names": names,
            "mentioned_current_anchors": anchors,
            "mentioned_archive_targets": archive_mentions,
            "current_reason_evidence_coverage": {
                "state": "STRUCTURAL_NA_NO_FROZEN_LEXICAL_CUES", "value": None},
            "semantic_endpoints": {endpoint: {"state": "HUMAN_ONLY_NOT_RATED",
                                               "value": None}
                                   for endpoint in SEMANTIC_ENDPOINTS}}


def _context_weights(high, low):
    return {f"{high}__{instruction}": 1.0 / 3.0 for instruction in INSTRUCTIONS} | {
        f"{low}__{instruction}": -1.0 / 3.0 for instruction in INSTRUCTIONS}


def registered_estimand_weights():
    literal = {}
    strict = {}
    for context in CONTEXTS:
        literal[f"{context}__I1_META_LITERAL"] = 1.0 / 4.0
        literal[f"{context}__I2_CONCRETE_COPY"] = -1.0 / 4.0
        strict[f"{context}__I1_META_LITERAL"] = 1.0 / 8.0
        strict[f"{context}__I2_CONCRETE_COPY"] = 1.0 / 8.0
        strict[f"{context}__I0_MINIMAL"] = -1.0 / 4.0
    weights = {
        "instruction_package_meta_vs_concrete": literal,
        "strict_format_pressure": strict,
        "text_declared_owner_attribution_package": _context_weights(
            "C3_PERSONA_LIVE", "C1_CONTROL_LIVE"),
        "chat_role_template_package": _context_weights(
            "C3_PERSONA_LIVE", "C2_PERSONA_QUOTED"),
        "generic_added_dialogue_package": _context_weights(
            "C1_CONTROL_LIVE", "C0_NO_HISTORY"),
        "total_live_persona_history": _context_weights(
            "C3_PERSONA_LIVE", "C0_NO_HISTORY"),
        "quoted_persona_payload": _context_weights(
            "C2_PERSONA_QUOTED", "C0_NO_HISTORY"),
    }
    for context in CONTEXTS:
        weights[f"instruction_package_meta_vs_concrete_within_{context}"] = {
            f"{context}__I1_META_LITERAL": 1.0,
            f"{context}__I2_CONCRETE_COPY": -1.0}
    return weights


def range_aware_contrast(by_case, case_ids, weights, metric, persona_by_case,
                         bounds=(0.0, 1.0)):
    """Paired estimate with explicit structural N/A and range-correct missing bounds."""
    lower_value, upper_value = map(float, bounds)
    require(lower_value <= upper_value and weights and
            abs(sum(weights.values())) < 1e-12, "Invalid contrast or bounds")
    rows, resolved_values = [], []
    bound_lower = bound_upper = 0.0
    eligible = 0
    for case_id in case_ids:
        scores = by_case.get(case_id, {})
        states = []
        known = 0.0
        missing_weights = []
        cell_values = {}
        for arm, weight in weights.items():
            score = scores.get(arm)
            state = None if score is None else score.get("endpoint_states", {}).get(metric)
            value = None if score is None else score.get(metric)
            cell_values[arm] = value
            if state == "STRUCTURAL_NA":
                states.append("STRUCTURAL_NA")
            elif state == "ASSESSED" and value is not None:
                require(lower_value <= value <= upper_value, "Endpoint outside frozen range")
                states.append("ASSESSED")
                known += weight * value
            else:
                states.append("MISSING")
                missing_weights.append(weight)
        if "STRUCTURAL_NA" in states:
            rows.append({"case_id": case_id, "persona_id": persona_by_case[case_id],
                         "state": "STRUCTURAL_NA", "contrast": None,
                         "cell_values": cell_values})
            continue
        eligible += 1
        case_lower = known + sum(min(weight * lower_value, weight * upper_value)
                                 for weight in missing_weights)
        case_upper = known + sum(max(weight * lower_value, weight * upper_value)
                                 for weight in missing_weights)
        bound_lower += case_lower
        bound_upper += case_upper
        value = None if missing_weights else known
        if value is not None:
            resolved_values.append(value)
        rows.append({"case_id": case_id, "persona_id": persona_by_case[case_id],
                     "state": "RESOLVED" if value is not None else "MISSING",
                     "contrast": value, "logical_bounds": [case_lower, case_upper],
                     "cell_values": cell_values})
    lopo = {}
    personas = sorted({persona_by_case[case_id] for case_id in case_ids})
    for persona_id in personas:
        values = [row["contrast"] for row in rows
                  if row["state"] == "RESOLVED" and row["persona_id"] != persona_id]
        lopo[persona_id] = None if not values else sum(values) / len(values)
    finite_lopo = [value for value in lopo.values() if value is not None]
    return {
        "metric": metric, "endpoint_range": [lower_value, upper_value],
        "weights": weights, "planned_cases": len(case_ids),
        "eligible_cases": eligible,
        "structural_n_a_cases": len(case_ids) - eligible,
        "resolved_cases": len(resolved_values),
        "missing_cases": eligible - len(resolved_values),
        "paired_point_estimate": (None if not resolved_values else
                                  sum(resolved_values) / len(resolved_values)),
        "case_level_contrasts": rows,
        "leave_one_persona_out": lopo,
        "leave_one_case_out_range": ([min(finite_lopo), max(finite_lopo)]
                                     if finite_lopo else [None, None]),
        "logical_missing_outcome_bounds": (
            [bound_lower / eligible, bound_upper / eligible]
            if eligible else [None, None]),
        "missing_recoded_as_zero": False,
        "structural_n_a_in_denominator": False,
    }


def _runtime_checks(design):
    planned = design["planned_generation_configuration"]
    expected = {"cache_prompt": False, "temperature": 0.0, "seed": 42,
                "max_generated_tokens": 96, "cpu_threads": 4,
                "context_length": 4096, "retries": 0, "hidden_warmups": 0}
    require(all(planned[key] == value for key, value in expected.items()),
            "Planned generation configuration changed")
    resources = design["resources_and_safety"]
    require(resources["global_generation_limit"] == GENERATION_LIMIT and
            resources["baseline_generations_consumed"] == GENERATION_BASELINE and
            resources["planned_attempts"] == MAX_ATTEMPTS and
            resources["global_inference_seconds_limit"] == INFERENCE_LIMIT and
            resources["baseline_inference_seconds_consumed"] == INFERENCE_BASELINE and
            resources["batch_completion_inference_seconds_ceiling"] == INFERENCE_CEILING and
            resources["batch_wall_seconds_ceiling"] == WALL_CEILING and
            resources["required_available_physical_bytes"] == MIN_PREFLIGHT_RAM,
            "Resource plan changed")


def _binding(path, digest):
    return {"path": Path(path).as_posix(), "sha256": digest}


def _has_static_controller_binding(value):
    """Reject a registration/review -> controller hash cycle."""
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).casefold() in {
                    "controller", "controller_path", "controller_sha256",
                    "source_hashes"}:
                return True
            if _has_static_controller_binding(item):
                return True
    elif isinstance(value, list):
        return any(_has_static_controller_binding(item) for item in value)
    return False


def expected_material_review_bindings():
    return {
        "prospective_design": _binding(DESIGN, DESIGN_SHA),
        "case_bank": _binding(CASE_BANK, CASE_BANK_SHA),
        "prospective_amendment": _binding(AMENDMENT, AMENDMENT_SHA),
        "measurement_clarification": _binding(
            MEASUREMENT_CLARIFICATION, MEASUREMENT_CLARIFICATION_SHA),
        "material_ancestry_audit": _binding(MATERIAL_AUDIT, MATERIAL_AUDIT_SHA),
    }


def validate_material_review_artifact(value=None, bank=None):
    """Validate the independent, pre-output material review semantically."""
    value = load(MATERIAL_REVIEW) if value is None else value
    bank = load(CASE_BANK) if bank is None else bank
    prefix = "Material scientific review content: "
    require(isinstance(value, dict), prefix + "top level must be an object")
    require(value.get("version") == MATERIAL_REVIEW_VERSION,
            prefix + "version")
    require(value.get("status") == MATERIAL_REVIEW_STATUS, prefix + "status")
    require(value.get("verdict") == MATERIAL_REVIEW_VERDICT, prefix + "verdict")
    require(value.get("bindings") == expected_material_review_bindings(),
            prefix + "parent bindings")
    require(not _has_static_controller_binding(value),
            prefix + "must not bind the mutable controller/source inventory")
    require(value.get("review_scope") ==
            "INDEPENDENT_READ_ONLY_PREOUTPUT_MATERIAL_REVIEW",
            prefix + "review scope")
    provenance = value.get("reviewer_provenance")
    require(isinstance(provenance, dict) and
            isinstance(provenance.get("reviewer_id"), str) and
            bool(provenance["reviewer_id"].strip()) and
            provenance.get("reviewer_type") ==
                "INDEPENDENT_READ_ONLY_TECHNICAL_REVIEWER" and
            provenance.get("human_semantic_judgments_provided") is False and
            provenance.get("independent_human_validation") is False,
            prefix + "reviewer provenance")
    require(value.get("protected_mapping_accessed") is False and
            value.get("protected_or_local_paths_enumerated") is False and
            value.get("model_outputs_accessed") is False and
            value.get("tokenizer_calls") == 0 and
            value.get("generation_requests") == 0,
            prefix + "pre-output/protected-data boundaries")
    require(value.get("reviewed_case_count") == 8 and
            value.get("blocking_issues") == [], prefix + "blocking summary")
    amendment_checks = value.get("amendment_checks")
    require(amendment_checks == {
        "archive_scope_repair_v4_1_applied": True,
        "instruction_package_terminology_applied": True,
        "text_declared_owner_attribution_package_terminology_applied": True,
        "archive_any_and_selected_endpoints_separated": True,
        "style_prefix_and_suffix_endpoints_separated": True,
        "indicator_discordance_construct_v4_2_applied": True,
        "all_ten_human_only_endpoints_present": True,
    }, prefix + "amendment checks")
    boundaries = value.get("claim_boundaries")
    require(boundaries == {
        "synthetic_material_review_only": True,
        "human_semantic_validation": False,
        "independent_human_validation": False,
        "model_outcome_evidence": False,
        "algorithmic_novelty_evidence": False,
    }, prefix + "claim boundaries")
    summaries = value.get("case_summaries")
    require(isinstance(summaries, list) and len(summaries) == 8,
            prefix + "eight case summaries")
    cases = {case["case_id"]: case for case in bank["cases"]}
    require(len(cases) == 8 and
            Counter(item.get("case_id") for item in summaries) ==
                Counter({case_id: 1 for case_id in cases}),
            prefix + "case-summary identities")
    for summary in summaries:
        case = cases[summary["case_id"]]
        require(summary.get("persona_id") == case["persona_id"] and
                summary.get("task_family") == case["task_family"] and
                summary.get("verdict") == "PASS_NO_BLOCKING_MATERIAL_ISSUE" and
                summary.get("uniquely_supported_current_option") is True and
                summary.get("archive_current_attribute_separation") is True and
                summary.get("clear_current_and_control_ownership") is True and
                summary.get("direct_answer_leakage_detected") is False and
                summary.get("blocking_issues") == [] and
                isinstance(summary.get("rationale"), str) and
                bool(summary["rationale"].strip()),
                prefix + "invalid case summary " + summary["case_id"])
    return {"status": value["status"], "verdict": value["verdict"],
            "reviewed_cases": len(summaries)}


def expected_registration_bindings():
    return {
        **expected_material_review_bindings(),
        "material_scientific_review": _binding(
            MATERIAL_REVIEW, MATERIAL_REVIEW_SHA),
    }


def validate_registration_artifact(value=None, design=None):
    """Reject a nominal registration that lacks the frozen scientific contract."""
    value = load(REGISTRATION) if value is None else value
    design = load(DESIGN) if design is None else design
    prefix = "Prospective registration content: "
    require(isinstance(value, dict), prefix + "top level must be an object")
    require(value.get("version") == REGISTRATION_VERSION, prefix + "version")
    require(value.get("status") == REGISTRATION_STATUS, prefix + "status")
    require(value.get("prospective") is True and
            value.get("outcomes_observed") is False and
            value.get("observed_model_responses") == [] and
            value.get("observed_endpoint_values") == [],
            prefix + "must be prospectively outcome-free")
    require(value.get("bindings") == expected_registration_bindings(),
            prefix + "design/case/amendment/audit/review bindings")
    require(not _has_static_controller_binding(value),
            prefix + "must not bind the mutable controller/source inventory")
    allocation = value.get("allocation")
    require(allocation == {
        "synthetic_personas": 8,
        "cases": 8,
        "arms": 12,
        "planned_generation_attempts": MAX_ATTEMPTS,
        "attempts_per_case": 12,
        "attempts_per_arm": 8,
        "retries": 0,
        "hidden_warmups": 0,
    }, prefix + "finite allocation")
    require(value.get("schedule_sha256") ==
            _canonical_json_hash(request_specs(design)), prefix + "schedule hash")
    require(value.get("estimand_weights_sha256") ==
            _canonical_json_hash(registered_estimand_weights()),
            prefix + "estimand-weight hash")
    resources = value.get("resources")
    require(resources == {
        "baseline_generations_consumed": GENERATION_BASELINE,
        "global_generation_limit": GENERATION_LIMIT,
        "projected_generations_consumed_if_complete":
            GENERATION_BASELINE + MAX_ATTEMPTS,
        "baseline_inference_seconds_consumed": INFERENCE_BASELINE,
        "global_inference_seconds_limit": INFERENCE_LIMIT,
        "batch_completion_inference_seconds_ceiling": INFERENCE_CEILING,
        "batch_wall_seconds_ceiling": WALL_CEILING,
        "minimum_preflight_available_physical_ram_bytes": MIN_PREFLIGHT_RAM,
        "minimum_live_available_physical_ram_bytes": MIN_LIVE_RAM,
        "minimum_disk_reserve_bytes": MIN_DISK,
        "maximum_native_tokenizer_calls": NATIVE_TOKENIZER_CALLS,
        "maximum_live_server_tokenizer_checks": LIVE_TOKENIZER_CHECKS,
        "maximum_tokenizer_operations_total":
            NATIVE_TOKENIZER_CALLS + LIVE_TOKENIZER_CHECKS,
    }, prefix + "resource contract")
    execution = value.get("execution_state")
    require(execution == {
        "authorized": False,
        "native_tokenizer_calls": 0,
        "live_server_tokenizer_checks": 0,
        "model_server_launches": 0,
        "generation_attempts": 0,
        "completed_generations": 0,
        "results": 0,
    }, prefix + "zero-execution state")
    endpoint_policy = value.get("endpoint_policy")
    require(endpoint_policy == {
        "automatic_endpoints": list(AUTOMATIC_ENDPOINTS),
        "automatic_claim_class":
            "LITERAL_SELECTION_FORMAT_AND_EVALUATOR_PROXIES_ONLY",
        "unassessable_automatic_values": "MISSING_NOT_ZERO",
        "structural_not_applicable_values": "N_A_EXCLUDED_NOT_ZERO",
        "semantic_endpoints": list(SEMANTIC_ENDPOINTS),
        "semantic_endpoint_status": "HUMAN_ONLY_NOT_RATED",
        "automatic_semantic_substitution": False,
    }, prefix + "endpoint/semantic boundary")
    analysis_policy = value.get("analysis_policy")
    require(analysis_policy == {
        "unit": "CASE_PAIRED_WITHIN_CASE_CONTRAST",
        "inference": "ESTIMATION_FIRST_NO_P_VALUES_NO_CONFIRMATORY_SIGNIFICANCE",
        "leave_one_persona_out": True,
        "leave_one_case_out_range_is_confidence_interval": False,
        "logical_missing_outcome_bounds": True,
        "missing_recoded_as_zero": False,
        "structural_n_a_in_denominator": False,
    }, prefix + "analysis policy")
    require(value.get("claim_boundaries") == {
        "configuration_specific_synthetic_mechanism_associations_only": True,
        "general_semantic_history_failure_established": False,
        "real_speaker_persona_fidelity_established": False,
        "population_causality_established": False,
        "independent_human_validation_established": False,
        "algorithmic_novelty_established": False,
    }, prefix + "claim boundaries")
    require(value.get("stopping_and_integrity") == {
        "four_gib_preflight_required": True,
        "below_gate_is_no_go_before_server_or_generation": True,
        "zero_retry": True,
        "resume_or_fill_failed_suffix": False,
        "append_only_evidence": True,
        "outcome_based_stopping": False,
        "independent_validation_set_used_for_tuning": False,
    }, prefix + "stopping/integrity policy")
    return {"status": value["status"], "planned_attempts": MAX_ATTEMPTS,
            "outcomes_observed": False}


def validate_design(require_unstarted=False):
    require(sha256(DESIGN) == DESIGN_SHA, "Prospective design changed")
    require(sha256(CASE_BANK) == CASE_BANK_SHA, "Case bank changed")
    require(sha256(AMENDMENT) == AMENDMENT_SHA, "Prospective amendment changed")
    require(sha256(MEASUREMENT_CLARIFICATION) == MEASUREMENT_CLARIFICATION_SHA,
            "Prospective measurement clarification changed")
    require(sha256(BUDGET_SOURCE) == BUDGET_SOURCE_SHA, "Budget source changed")
    require(sha256(TOKENIZER_SOURCE) == TOKENIZER_SOURCE_SHA, "Tokenizer source changed")
    require(MATERIAL_AUDIT_SHA != "PENDING" and MATERIAL_AUDIT.is_file() and
            sha256(MATERIAL_AUDIT) == MATERIAL_AUDIT_SHA,
            "Material ancestry audit missing, pending, or changed")
    design, bank, amendment = load(DESIGN), load(CASE_BANK), load(AMENDMENT)
    clarification = load(MEASUREMENT_CLARIFICATION)
    stored_audit = load(MATERIAL_AUDIT)
    recomputed_audit = material_overlap_audit()
    require(stored_audit == recomputed_audit and
            stored_audit.get("protected_mapping_accessed") is False and
            stored_audit.get("protected_or_local_paths_enumerated") is False,
            "Material ancestry audit content changed or crossed protected boundary")
    require(MATERIAL_REVIEW_SHA != "PENDING" and MATERIAL_REVIEW.is_file() and
            sha256(MATERIAL_REVIEW) == MATERIAL_REVIEW_SHA,
            "Material scientific review missing, pending, or changed")
    validate_material_review_artifact(load(MATERIAL_REVIEW), bank)
    require(REGISTRATION_SHA != "PENDING" and REGISTRATION.is_file() and
            sha256(REGISTRATION) == REGISTRATION_SHA,
            "Prospective registration missing, pending, or changed")
    validate_registration_artifact(load(REGISTRATION), design)
    require(design["status"] == bank["status"] ==
            "NOT_AUTHORIZED_NOT_TOKENIZED_NOT_EXECUTED", "Preexecution status changed")
    require(design["materials"]["case_bank_sha256"] == CASE_BANK_SHA, "Case binding")
    require(amendment["status"] == "NOT_AUTHORIZED_NOT_TOKENIZED_NOT_EXECUTED" and
            amendment["parent_design"] == {"path": DESIGN.as_posix(),
                                            "sha256": DESIGN_SHA} and
            amendment["case_bank"] == {"path": CASE_BANK.as_posix(),
                                        "sha256": CASE_BANK_SHA},
            "Prospective amendment binding")
    require(clarification["status"] == "NOT_AUTHORIZED_NOT_TOKENIZED_NOT_EXECUTED" and
            clarification["bindings"]["parent_design"] == {
                "path": DESIGN.as_posix(), "sha256": DESIGN_SHA} and
            clarification["bindings"]["prospective_amendment"] == {
                "path": AMENDMENT.as_posix(), "sha256": AMENDMENT_SHA} and
            clarification["bindings"]["case_bank"] == {
                "path": CASE_BANK.as_posix(), "sha256": CASE_BANK_SHA} and
            clarification["effective_endpoint"]["name"] ==
                "preferred_name_anchor_indicator_discordance",
            "Prospective measurement clarification binding")
    require(design["scientific_scope"]["cases"] == 8 and
            design["scientific_scope"]["synthetic_personas"] == 8 and
            design["scientific_scope"]["arms"] == 12 and
            design["scientific_scope"]["planned_attempts"] == MAX_ATTEMPTS,
            "Scientific scope changed")
    require(tuple(design["human_review_plan"]["stage_a"]["endpoints"]) ==
            SEMANTIC_ENDPOINTS, "Human semantic endpoint inventory changed")
    require(tuple(design["arms"]) == ARMS, "Arm order changed")
    require(len(bank["personas"]) == len(bank["cases"]) == 8, "Case/persona count")
    cases = {case["case_id"]: case for case in bank["cases"]}
    require(len(cases) == 8 and Counter(case["persona_id"] for case in cases.values()) ==
            Counter({persona_id: 1 for persona_id in bank["personas"]}),
            "One unique persona per case")
    require(Counter(case["task_family"] for case in cases.values()) ==
            Counter({family: 2 for family in (
                "COLLABORATIVE_PLANNING", "SUPPORTIVE_NEXT_TURN",
                "ROUTINE_NEGOTIATION", "MISUNDERSTANDING_REPAIR")}),
            "Task-family balance")
    require(Counter(case["preferred_option"] for case in cases.values()) ==
            Counter({"A": 4, "B": 4}), "Preferred-option balance")
    preferred_positions = Counter(
        "FIRST" if case["current_option_display_order"][0] == case["preferred_option"]
        else "SECOND" for case in cases.values())
    require(preferred_positions == Counter({"FIRST": 4, "SECOND": 4}),
            "Preferred display-position balance")
    rows = request_specs(design)
    require(len(rows) == len({row["request_id"] for row in rows}) == MAX_ATTEMPTS and
            [row["order"] for row in rows] == list(range(MAX_ATTEMPTS)),
            "Request identity/order")
    require(Counter(row["arm_id"] for row in rows) ==
            Counter({arm: 8 for arm in ARMS}), "Arm allocation")
    require(Counter(row["round"] for row in rows) == Counter({i: 8 for i in range(12)}),
            "Round allocation")
    for arm in ARMS:
        arm_rows = [row for row in rows if row["arm_id"] == arm]
        require(Counter(row["quartile"] for row in arm_rows) ==
                Counter({i: 2 for i in range(4)}), "Arm/quartile balance")
        require(Counter(cases[row["case_id"]]["preferred_option"] for row in arm_rows) ==
                Counter({"A": 4, "B": 4}), "Arm preference balance")
        require(Counter(cases[row["case_id"]]["task_family"] for row in arm_rows) ==
                Counter({family: 2 for family in set(
                    case["task_family"] for case in cases.values())}),
                "Arm task-family balance")
    for case_id, case in cases.items():
        require(Counter(row["arm_id"] for row in rows if row["case_id"] == case_id) ==
                Counter({arm: 1 for arm in ARMS}), "Incomplete case pairing")
        persona = bank["personas"][case["persona_id"]]
        require(persona["synthetic"] is True and set(case["options"]) == {"A", "B"} and
                set(case["archive_options"]) == {"H1", "H2", "H3"}, "Material schema")
        require(case["archive_selected_target"] ==
                case["archive_options"][case["archive_selected_key"]]["canonical"],
                "Archive target binding")
        current = "\n".join((case["scenario"], case["current_evidence"], case["question"],
                              *(option["canonical"] + " " + option["attribute"]
                                for option in case["options"].values())))
        archive = "\n".join((case["archive_question"], case["archive_assistant"],
                              *(option["canonical"] + " " + option["attribute"]
                                for option in case["archive_options"].values())))
        require(all(not base._exact_contains(archive, option["canonical"])
                    for option in case["options"].values()),
                "Current option leaked into archive")
        require(all(not base._exact_contains(current, option["canonical"])
                    for option in case["archive_options"].values()),
                "Archive entity leaked into current material")
        built = {arm: construction(design, bank, case, arm)[1] for arm in ARMS}
        for instruction in INSTRUCTIONS:
            subset = [built[f"{context}__{instruction}"] for context in CONTEXTS]
            require(len(subset[0]) == len(subset[2]) == 2 and
                    len(subset[1]) == len(subset[3]) == 4, "Context role structure")
            require(all(messages[0] == subset[0][0] for messages in subset),
                    "Context changed system/instruction material")
            require(subset[1][2]["content"] == subset[3][2]["content"] ==
                    case["archive_assistant"], "Live archive payload changed")
            require(case["archive_question"] in subset[1][1]["content"] and
                    case["archive_question"] in subset[2][1]["content"] and
                    case["archive_question"] in subset[3][1]["content"] and
                    case["archive_assistant"] in subset[2][1]["content"],
                    "Archive payload identity")
    for binding in _all_prior_bindings(design):
        require(sha256(Path(binding["path"])) == binding["sha256"],
                "Bound prior artifact changed: " + binding["path"])
    audit = recomputed_audit
    require(audit["status"] == "PASS_ZERO_NORMALIZED_EXACT_OVERLAP" and
            audit["normalized_exact_overlap_total"] == 0 and
            audit["canonical_entity_normalized_sha256_overlap"] == 0 and
            audit["exact_question_or_template_overlap"] == 0,
            "Material ancestry audit failed")
    _runtime_checks(design)
    budget = load(BUDGET_SOURCE)["cumulative_authorization_after"]
    require(budget == {"generations_limit": GENERATION_LIMIT,
                       "generations_used": GENERATION_BASELINE,
                       "inference_seconds_limit": int(INFERENCE_LIMIT),
                       "inference_seconds_used": INFERENCE_BASELINE},
            "Cumulative budget baseline changed")
    weights = registered_estimand_weights()
    require(all(abs(sum(value.values())) < 1e-12 for value in weights.values()),
            "Contrast coefficients do not sum to zero")
    if require_unstarted:
        require(not FROZEN.exists() and not PREFLIGHT.exists() and
                not (ROOT / "claim.json").exists() and
                not list((ROOT / "runs").glob("*")) and
                not (ROOT / "native_tokenizer").exists(),
                "v4 execution/tokenization evidence already exists")
    return {"personas": 8, "cases": 8, "task_families": 4, "arms": 12,
            "requests": MAX_ATTEMPTS, "ancestry_exact_overlaps": 0,
            "registered_automatic_endpoints": len(AUTOMATIC_ENDPOINTS),
            "semantic_endpoints": "HUMAN_ONLY_NOT_RATED"}


def authorization_requirements(require_unstarted=True):
    checks = validate_design(require_unstarted=require_unstarted)
    return {
        "version": "personaslm_placeholder_mechanism_execution_authorization_v4",
        "researcher": "Yaxin ZHENG", "decision": "AUTHORIZED",
        "design": {"path": DESIGN.as_posix(), "sha256": DESIGN_SHA},
        "case_bank": {"path": CASE_BANK.as_posix(), "sha256": CASE_BANK_SHA},
        "prospective_amendment": {"path": AMENDMENT.as_posix(),
                                  "sha256": AMENDMENT_SHA},
        "measurement_clarification": {"path": MEASUREMENT_CLARIFICATION.as_posix(),
                                      "sha256": MEASUREMENT_CLARIFICATION_SHA},
        "material_audit": {"path": MATERIAL_AUDIT.as_posix(),
                           "sha256": MATERIAL_AUDIT_SHA},
        "material_review": {"path": MATERIAL_REVIEW.as_posix(),
                            "sha256": MATERIAL_REVIEW_SHA},
        "registration": {"path": REGISTRATION.as_posix(), "sha256": REGISTRATION_SHA},
        "model_sha256": MODEL["model_sha256"],
        "maximum_native_tokenizer_calls": NATIVE_TOKENIZER_CALLS,
        "maximum_live_server_tokenizer_checks": LIVE_TOKENIZER_CHECKS,
        "maximum_tokenizer_operations_total": NATIVE_TOKENIZER_CALLS + LIVE_TOKENIZER_CHECKS,
        "maximum_generation_attempts": MAX_ATTEMPTS,
        "retries": 0, "hidden_warmups": 0,
        "minimum_available_physical_ram_bytes": MIN_PREFLIGHT_RAM,
        "minimum_live_available_physical_ram_bytes": MIN_LIVE_RAM,
        "completion_inference_seconds_ceiling": INFERENCE_CEILING,
        "batch_wall_seconds_ceiling": WALL_CEILING,
        "scope": "Exact 96-slot order, new synthetic cases, frozen v4 scorer and contrasts.",
        "prohibitions": ["retry", "resume", "hidden completion", "threshold change",
                         "protected mapping access", "AI fabrication of human labels"],
        "validated_design": checks,
    }


def validate_authorization(path=AUTHORIZATION):
    path = Path(path)
    require(path.resolve() == AUTHORIZATION.resolve(), "Official authorization path required")
    value = load(path)
    expected = authorization_requirements(require_unstarted=False)
    for key in ("version", "researcher", "decision", "design", "case_bank",
                "prospective_amendment", "measurement_clarification",
                "material_audit", "material_review",
                "registration", "model_sha256",
                "maximum_native_tokenizer_calls", "maximum_live_server_tokenizer_checks",
                "maximum_tokenizer_operations_total", "maximum_generation_attempts",
                "retries", "hidden_warmups", "minimum_available_physical_ram_bytes",
                "minimum_live_available_physical_ram_bytes",
                "completion_inference_seconds_ceiling", "batch_wall_seconds_ceiling",
                "scope", "prohibitions"):
        require(value.get(key) == expected[key], "Authorization changed: " + key)
    return value


def _tokenize_native(tokenizer, text, model_path):
    argv = [str(tokenizer.resolve()), "-m", str(model_path.resolve()),
            "--stdin", "--ids", "--offline"]
    started = b.utc_now()
    completed = subprocess.run(
        argv, input=text.encode("utf-8"), capture_output=True, timeout=90,
        env={key: value for key, value in os.environ.items()
             if not key.upper().startswith("LLAMA_ARG_")},
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    require(completed.returncode == 0, "Native tokenizer failed")
    ids = ast.literal_eval(completed.stdout.decode("utf-8", "replace").strip())
    require(isinstance(ids, list) and ids and all(type(value) is int and value >= 0
                                                  for value in ids), "Token IDs")
    return ids, {"started_utc": started, "finished_utc": b.utc_now(), "argv": argv,
                 "returncode": completed.returncode,
                 "stdout": completed.stdout.decode("utf-8", "replace"),
                 "stderr": completed.stderr.decode("utf-8", "replace"),
                 "text_sha256": th(text), "generation_requests": 0}


def register(authorization_path):
    """Freeze native token IDs.  This function never requests a completion."""
    validate_design(require_unstarted=True)
    authorization_path = Path(authorization_path)
    authorization = validate_authorization(authorization_path)
    require(not REGISTRATION_FAILURE.exists(), "Prior failed registration is immutable")
    require(s.memory_observation(os.getpid()).get("system", {}).get(
        "available_physical", 0) >= MIN_PREFLIGHT_RAM,
        "Less than registered 4 GiB available RAM")
    require(shutil.disk_usage(".").free >= MIN_DISK, "Output disk reserve")
    require(sha256(Path(MODEL["model_file"])) == MODEL["model_sha256"], "Model changed")
    require(sha256(Path(RUNTIME["backend_path"])) == RUNTIME["backend_sha256"],
            "Backend changed")
    require(sha256(Path(RUNTIME["chat_template_path"])) ==
            RUNTIME["chat_template_sha256"], "Chat template changed")
    native = load(TOKENIZER_SOURCE)["native_tokenizer_identity"]
    tokenizer = Path(RUNTIME["backend_path"]).with_name("llama-tokenize.exe")
    require(sha256(tokenizer) == native["tokenizer_sha256"], "Tokenizer changed")
    require({path.name: sha256(path) for path in tokenizer.parent.glob("*.dll")} ==
            native["dll_hashes"], "Backend DLL set changed")
    template = Path(RUNTIME["chat_template_path"]).read_text(encoding="utf-8")
    design, bank = load(DESIGN), load(CASE_BANK)
    cases = {case["case_id"]: case for case in bank["cases"]}
    logs, name_counts, rows = [], {}, []
    for persona_id, persona in bank["personas"].items():
        name_counts[persona_id] = {}
        for role in ("speaker_name", "control_speaker_name"):
            ids, evidence = _tokenize_native(tokenizer, persona[role],
                                             Path(MODEL["model_file"]))
            path = ROOT / "native_tokenizer" / "names" / f"{persona_id}_{role}.json"
            write_exclusive(path, evidence)
            logs.append({"kind": "owner_name", "path": path.as_posix(),
                         "sha256": sha256(path)})
            name_counts[persona_id][role] = len(ids)
    parity_failures = [persona_id for persona_id, counts in name_counts.items()
                       if counts["speaker_name"] != counts["control_speaker_name"]]
    for spec in request_specs(design):
        case = cases[spec["case_id"]]
        factors, messages = construction(design, bank, case, spec["arm_id"])
        prompt = s.render(template, messages)
        token_ids, evidence = _tokenize_native(
            tokenizer, prompt, Path(MODEL["model_file"]))
        path = ROOT / "native_tokenizer" / "prompts" / f"{spec['order']:04d}.json"
        evidence.update(prompt_sha256=th(prompt))
        write_exclusive(path, evidence)
        logs.append({"kind": "prompt", "path": path.as_posix(), "sha256": sha256(path)})
        context, instruction = spec["arm_id"].split("__", 1)
        persona = bank["personas"][case["persona_id"]]
        row = {**spec, "persona_id": case["persona_id"], "task_family": case["task_family"],
               "context_id": context, "instruction_id": instruction,
               "factors": factors, "messages": messages, "prompt": prompt,
               "prompt_sha256": th(prompt), "input_token_ids": token_ids,
               "input_tokens": len(token_ids), "input_token_ids_sha256": th(str(token_ids)),
               "preferred_option": case["preferred_option"], "options": case["options"],
               "archive_target_strings": [option["canonical"]
                                          for option in case["archive_options"].values()],
               "archive_selected_target": case["archive_selected_target"],
               "control_speaker_name": persona["control_speaker_name"],
               "reason_prefix": persona["reason_prefix"],
               "reason_suffix": persona["reason_suffix"],
               "max_new_tokens": 96, "seed": 42, "temperature": 0.0, "top_p": 1.0,
               "stop": [], "ignore_eos": False, "cache_prompt": False}
        require(row["input_tokens"] + row["max_new_tokens"] <= 4096,
                "Context overflow")
        row["request_sha256"] = _canonical_json_hash(row)
        rows.append(row)
    token_balance_failures = []
    grouped = defaultdict(dict)
    for row in rows:
        grouped[(row["case_id"], row["context_id"])][row["instruction_id"]] = \
            row["input_tokens"]
    for key, counts in grouped.items():
        if max(counts.values()) - min(counts.values()) > 2:
            token_balance_failures.append({"case_id": key[0], "context_id": key[1],
                                           "token_counts": counts,
                                           "max_minus_min": (max(counts.values()) -
                                                             min(counts.values()))})
    if parity_failures or token_balance_failures:
        receipt = {"status": "NO_GO_TOKEN_PARITY", "checked_utc": b.utc_now(),
                   "design_sha256": DESIGN_SHA, "case_bank_sha256": CASE_BANK_SHA,
                   "owner_name_parity_failures": parity_failures,
                   "instruction_token_balance_failures": token_balance_failures,
                   "native_tokenizer_calls": len(logs), "model_server_launches": 0,
                   "completion_calls": 0, "new_model_generations": 0,
                   "required_action": "Versioned pre-output amendment and new review; no retry of this registration."}
        write_exclusive(REGISTRATION_FAILURE, receipt)
        raise ValueError("Native token-parity gate failed; immutable receipt preserved")
    plan = {"version": "personaslm_placeholder_mechanism_frozen_manifest_v4",
            "evidence_level": "PROSPECTIVE_SYNTHETIC_MECHANISM_STUDY",
            "design_path": DESIGN.as_posix(), "design_sha256": DESIGN_SHA,
            "case_bank_path": CASE_BANK.as_posix(), "case_bank_sha256": CASE_BANK_SHA,
            "prospective_amendment_path": AMENDMENT.as_posix(),
            "prospective_amendment_sha256": AMENDMENT_SHA,
            "measurement_clarification_path": MEASUREMENT_CLARIFICATION.as_posix(),
            "measurement_clarification_sha256": MEASUREMENT_CLARIFICATION_SHA,
            "material_audit_path": MATERIAL_AUDIT.as_posix(),
            "material_audit_sha256": MATERIAL_AUDIT_SHA,
            "material_review_path": MATERIAL_REVIEW.as_posix(),
            "material_review_sha256": MATERIAL_REVIEW_SHA,
            "registration_path": REGISTRATION.as_posix(),
            "registration_sha256": REGISTRATION_SHA,
            "authorization_path": authorization_path.as_posix(),
            "authorization_sha256": sha256(authorization_path),
            "model": copy.deepcopy(MODEL), "runtime": copy.deepcopy(RUNTIME),
            "resource_budget": {"requests": MAX_ATTEMPTS,
                "minimum_available_physical_ram_bytes": MIN_PREFLIGHT_RAM,
                "minimum_live_available_physical_ram_bytes": MIN_LIVE_RAM,
                "minimum_free_output_disk_bytes": MIN_DISK,
                "actual_completion_inference_seconds_ceiling": INFERENCE_CEILING,
                "batch_wall_seconds_ceiling": WALL_CEILING,
                "global_baseline": load(BUDGET_SOURCE)["cumulative_authorization_after"]},
            "native_tokenizer_identity": {"path": tokenizer.as_posix(),
                "tokenizer_sha256": native["tokenizer_sha256"],
                "dll_hashes": native["dll_hashes"]},
            "owner_name_token_counts": name_counts,
            "native_tokenizer_logs": logs, "requests": rows,
            "registration_source_hashes": source_hashes(),
            "registered_utc": b.utc_now(), "new_model_generations": 0,
            "semantic_endpoints": "HUMAN_ONLY_NOT_RATED"}
    require(authorization["maximum_generation_attempts"] == len(rows),
            "Authorization row count")
    write_exclusive(FROZEN, plan)
    validate_plan(load(FROZEN))
    return {"status": "REGISTERED_NO_GENERATIONS", "manifest_sha256": sha256(FROZEN),
            "native_tokenizer_calls": len(logs), "generation_requests": 0}


def validate_plan(plan):
    validate_design()
    require(plan["version"] == "personaslm_placeholder_mechanism_frozen_manifest_v4",
            "Manifest version")
    require(plan["design_sha256"] == DESIGN_SHA and
            plan["case_bank_sha256"] == CASE_BANK_SHA and
            plan["prospective_amendment_sha256"] == AMENDMENT_SHA and
            plan["measurement_clarification_sha256"] == MEASUREMENT_CLARIFICATION_SHA and
            plan["material_audit_sha256"] == MATERIAL_AUDIT_SHA and
            plan["material_review_sha256"] == MATERIAL_REVIEW_SHA and
            plan["registration_sha256"] == REGISTRATION_SHA, "Manifest bindings")
    require(plan["model"] == MODEL and plan["runtime"] == RUNTIME, "Model/runtime changed")
    require(Path(plan["authorization_path"]).resolve() == AUTHORIZATION.resolve() and
            plan["authorization_sha256"] == sha256(AUTHORIZATION), "Authorization binding")
    validate_authorization(AUTHORIZATION)
    validate_registered_source_hashes(plan["registration_source_hashes"])
    require(len(plan["native_tokenizer_logs"]) == NATIVE_TOKENIZER_CALLS,
            "Native tokenizer log count")
    for record in plan["native_tokenizer_logs"]:
        require(sha256(Path(record["path"])) == record["sha256"], "Tokenizer log changed")
    require(all(counts["speaker_name"] == counts["control_speaker_name"]
                for counts in plan["owner_name_token_counts"].values()),
            "Owner-name token parity")
    design, bank = load(DESIGN), load(CASE_BANK)
    cases = {case["case_id"]: case for case in bank["cases"]}
    template = Path(RUNTIME["chat_template_path"]).read_text(encoding="utf-8")
    specs, rows = request_specs(design), plan["requests"]
    require(len(rows) == MAX_ATTEMPTS, "Manifest request count")
    for spec, row in zip(specs, rows):
        require(all(row[key] == value for key, value in spec.items()), "Request order changed")
        case = cases[row["case_id"]]
        factors, messages = construction(design, bank, case, row["arm_id"])
        require(row["factors"] == factors and row["messages"] == messages and
                row["prompt"] == s.render(template, messages), "Prompt changed")
        require(row["prompt_sha256"] == th(row["prompt"]) and
                row["input_token_ids_sha256"] == th(str(row["input_token_ids"])) and
                row["input_tokens"] == len(row["input_token_ids"]), "Token binding")
        require(row["input_tokens"] + 96 <= 4096 and
                row["request_sha256"] == _canonical_json_hash(
                    {key: value for key, value in row.items() if key != "request_sha256"}),
                "Request hash/context")
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["case_id"], row["context_id"])].append(row["input_tokens"])
    require(all(max(values) - min(values) <= 2 and len(values) == 3
                for values in grouped.values()), "Instruction token-balance gate")
    return {"requests": MAX_ATTEMPTS, "native_tokenizer_calls": NATIVE_TOKENIZER_CALLS,
            "live_tokenizer_checks": LIVE_TOKENIZER_CHECKS,
            "owner_name_pairs": 8, "instruction_balance_groups": 32}


def validate_registered_source_hashes(expected):
    actual = source_hashes()
    require(expected == actual, "Registered source/dependency inventory changed")
    return actual


def preflight(check_headroom=True, require_unused=True):
    plan = load(FROZEN)
    checks = validate_plan(plan)
    authorization = validate_authorization(AUTHORIZATION)
    identity = b.file_preflight(cfg(plan))
    require(identity["status"] == "PASS" and
            identity["model"]["sha256"] == MODEL["model_sha256"] and
            identity["server"]["sha256"] == MODEL["backend_sha256"],
            "Model/backend identity")
    native = plan["native_tokenizer_identity"]
    tokenizer = Path(native["path"])
    require(sha256(tokenizer) == native["tokenizer_sha256"] and
            {path.name: sha256(path) for path in tokenizer.parent.glob("*.dll")} ==
            native["dll_hashes"], "Tokenizer/DLL identity")
    baseline = load(BUDGET_SOURCE)["cumulative_authorization_after"]
    require(baseline["generations_used"] == GENERATION_BASELINE and
            baseline["inference_seconds_used"] == INFERENCE_BASELINE and
            baseline["generations_limit"] - GENERATION_BASELINE >= MAX_ATTEMPTS and
            baseline["inference_seconds_limit"] - INFERENCE_BASELINE >= INFERENCE_CEILING,
            "Cumulative budget recovery/remaining budget")
    if require_unused:
        require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
                "Existing allocation: zero retry and zero resume")
    memory = s.memory_observation(os.getpid())
    available = memory.get("system", {}).get("available_physical")
    require(type(available) is int, "Official available physical RAM unavailable")
    if check_headroom:
        require(available >= MIN_PREFLIGHT_RAM,
                "Less than registered 4 GiB available physical RAM")
    require(shutil.disk_usage(".").free >= MIN_DISK, "Output disk reserve")
    return {"status": "PASS", "checked_utc": b.utc_now(), "checks": checks,
            "identity": identity, "manifest_sha256": sha256(FROZEN),
            "authorization_sha256": sha256(AUTHORIZATION),
            "design_sha256": DESIGN_SHA, "case_bank_sha256": CASE_BANK_SHA,
            "prospective_amendment_sha256": AMENDMENT_SHA,
            "measurement_clarification_sha256": MEASUREMENT_CLARIFICATION_SHA,
            "material_audit_sha256": MATERIAL_AUDIT_SHA,
            "material_review_sha256": MATERIAL_REVIEW_SHA,
            "registration_sha256": REGISTRATION_SHA,
            "source_hashes": source_hashes(), "configuration": cfg(plan).as_dict(),
            "server_command": s.command(plan), "memory_before_run": memory,
            "required_available_physical_ram_bytes": MIN_PREFLIGHT_RAM,
            "cumulative_baseline": baseline,
            "live_gate": "All 96 live parse_special token arrays match before completion 1.",
            "authorization": {"researcher": authorization["researcher"],
                              "maximum_attempts": MAX_ATTEMPTS, "retries": 0}}


def preflight_receipt():
    """Persistent-safe receipt; failures launch no server and make no completion call."""
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
        available = memory.get("system", {}).get("available_physical")
        deficit = (max(0, MIN_PREFLIGHT_RAM - available)
                   if type(available) is int else None)
        observed = {}
        for name, path in (("design", DESIGN), ("case_bank", CASE_BANK),
                           ("prospective_amendment", AMENDMENT),
                           ("measurement_clarification", MEASUREMENT_CLARIFICATION),
                           ("material_audit", MATERIAL_AUDIT),
                           ("material_review", MATERIAL_REVIEW),
                           ("registration", REGISTRATION), ("manifest", FROZEN),
                           ("authorization", AUTHORIZATION), ("budget", BUDGET_SOURCE)):
            observed[name] = sha256(path) if path.is_file() else None
        return {"status": "FAIL", "scientific_status": "BLOCKED_RESOURCE_OR_INTEGRITY",
                "checked_utc": b.utc_now(),
                "error": {"type": type(exc).__name__, "message": str(exc)},
                "expected_bindings": {"design_sha256": DESIGN_SHA,
                    "case_bank_sha256": CASE_BANK_SHA,
                    "prospective_amendment_sha256": AMENDMENT_SHA,
                    "measurement_clarification_sha256": MEASUREMENT_CLARIFICATION_SHA,
                    "material_audit_sha256": MATERIAL_AUDIT_SHA,
                    "material_review_sha256": MATERIAL_REVIEW_SHA,
                    "registration_sha256": REGISTRATION_SHA,
                    "budget_source_sha256": BUDGET_SOURCE_SHA},
                "observed_sha256": observed, "memory_observation": memory,
                "measured_available_physical_ram_bytes": available,
                "required_available_physical_ram_bytes": MIN_PREFLIGHT_RAM,
                "available_ram_deficit_bytes": deficit,
                "free_output_disk_bytes": disk_free,
                "minimum_free_output_disk_bytes": MIN_DISK,
                "model_server_launches": 0, "completion_calls": 0,
                "new_model_generations": 0, "retry_permitted_without_change": False}


def payload(row):
    return {"prompt": row["input_token_ids"], "n_predict": row["max_new_tokens"],
            "temperature": row["temperature"], "top_p": row["top_p"],
            "seed": row["seed"], "cache_prompt": False, "stop": [],
            "ignore_eos": False, "return_tokens": True, "stream": False}


def result(row, response, latency):
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
    return {"request_id": row["request_id"], "request_sha256": row["request_sha256"],
            **normal, "generated_tokens": count, "returned_token_count": returned,
            "latency_seconds": latency, "input_token_audit": token_audit,
            "response_status": boundary, "raw_text_sha256": th(normal["raw_response"]),
            "first_reply_sha256": th(span),
            "automatic_score": automatic_score(row, span, assessability(boundary)),
            "human_semantic_ratings": 0,
            "semantic_endpoint_status": "HUMAN_ONLY_NOT_RATED",
            "evidence_level": "PROSPECTIVE_SYNTHETIC_MECHANISM_STUDY"}


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


def planned_slot_states(plan, attempted, raw, derived):
    states = []
    for row in plan["requests"]:
        request_id = row["request_id"]
        state = ("COMPLETED" if request_id in derived else
                 "RAW_RECOVERABLE" if request_id in raw else
                 "ATTEMPTED_UNRESOLVED" if request_id in attempted else "UNATTEMPTED")
        states.append({"request_id": request_id, "order": row["order"],
                       "case_id": row["case_id"], "arm_id": row["arm_id"],
                       "state": state})
    return states


def build_run_summary(status, plan, events, inference_seconds, failed_seconds,
                      batch_wall_seconds, run_directory):
    attempted, raw, derived = inventory(plan, events)
    live_checks = sum(event["kind"] == "live_prompt_verified" for event in events)
    return {"status": status, "attempted": len(attempted),
            "responses_received": len(raw), "results": len(derived),
            "planned_slots": MAX_ATTEMPTS,
            "slot_states": planned_slot_states(plan, attempted, raw, derived),
            "native_tokenizer_calls": NATIVE_TOKENIZER_CALLS,
            "live_server_tokenizer_checks": live_checks,
            "tokenizer_operations_total": NATIVE_TOKENIZER_CALLS + live_checks,
            "inference_wall_seconds": inference_seconds,
            "failed_completion_seconds": failed_seconds,
            "batch_wall_seconds": batch_wall_seconds,
            "run_directory": Path(run_directory).as_posix(), "retries": 0,
            "hidden_warmups": 0, "human_semantic_ratings": 0,
            "semantic_endpoint_status": "HUMAN_ONLY_NOT_RATED"}


def run(preflight_path=PREFLIGHT):
    preflight_path = Path(preflight_path)
    require(preflight_path.resolve() == PREFLIGHT.resolve(), "Official preflight required")
    fresh, stored, plan = preflight(), load(preflight_path), load(FROZEN)
    require(stored.get("status") == fresh.get("status") == "PASS",
            "Passing official preflight required")
    for key in ("manifest_sha256", "authorization_sha256", "design_sha256",
                "case_bank_sha256", "prospective_amendment_sha256",
                "measurement_clarification_sha256",
                "material_audit_sha256", "material_review_sha256",
                "registration_sha256", "source_hashes", "configuration", "server_command"):
        require(stored[key] == fresh[key], "Preflight binding changed: " + key)
    with b.writer_lock(ROOT):
        require(not (ROOT / "claim.json").exists() and not list((ROOT / "runs").glob("*")),
                "Existing allocation: zero retry and zero resume")
        claim = {key: fresh[key] for key in (
            "manifest_sha256", "authorization_sha256", "design_sha256",
            "case_bank_sha256", "prospective_amendment_sha256",
            "measurement_clarification_sha256",
            "material_audit_sha256", "material_review_sha256",
            "registration_sha256", "source_hashes")}
        claim.update(preflight_sha256=sha256(preflight_path),
                     maximum_attempts=MAX_ATTEMPTS, retries=0, hidden_warmups=0,
                     resume_permitted=False)
        write_exclusive(ROOT / "claim.json", claim)
        journal = b.RunJournal(ROOT / "runs", {
            "phase": "P1 prospective History/instruction mechanism v4",
            "evidence_level": "PROSPECTIVE_SYNTHETIC_MECHANISM_STUDY",
            "claim": claim, "frozen_manifest": plan,
            "authorization": load(AUTHORIZATION), "configuration": cfg(plan).as_dict(),
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
        try:
            journal.write("preflight", fresh)
            with s.Server(plan, journal) as server:
                client = b.LlamaClient(cfg(plan).endpoint, timeout=180, audit=journal.write)
                props = client.request("/props")
                binding = b.validate_server_properties(props, cfg(plan))
                require(binding["build_info"] == RUNTIME["backend_build"], "Backend build")
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
                for row in plan["requests"]:
                    remaining_wall = WALL_CEILING - (time.monotonic() - started)
                    remaining_inference = INFERENCE_CEILING - inference_seconds
                    require(remaining_wall > 0 and remaining_inference > 0,
                            "Registered time ceiling reached; preserve suffix")
                    server.assert_running()
                    observation = s.memory_observation(server.process.pid)
                    journal.write("memory_observation", observation)
                    available = observation.get("system", {}).get("available_physical")
                    require(type(available) is int and available >= MIN_LIVE_RAM,
                            "Registered live RAM headroom reached; preserve suffix")
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
                        journal.write("placeholder_mechanism_v4_completion_failed",
                                      {"request_id": active, "elapsed_seconds": elapsed})
                        raise
                    latency = time.monotonic() - tick
                    inference_seconds += latency
                    journal.write(RAW, {"request_id": active, "response": response,
                                        "latency_seconds": latency})
                    journal.write(DERIVED, result(row, response, latency))
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
        _, _, derived = inventory(plan, events)
        if status != "PASS" and len(derived) == MAX_ATTEMPTS:
            status = "COMPLETE_DATA_POSTFLIGHT_FAILED"
        summary = build_run_summary(status, plan, events, inference_seconds,
                                    failed_seconds, time.monotonic() - started,
                                    journal.directory)
        journal.finish(**summary)
        write_exclusive(journal.directory / "summary.json", summary)
        return summary


def _terminal_summary(folder, events, require_pass=False):
    summary = load(folder / "summary.json")
    require(events and events[-1]["kind"] == "run_finished" and
            summary == events[-1]["data"], "Terminal journal event")
    if require_pass:
        require(summary["status"] == "PASS", "Formal analysis requires terminal PASS")
    return summary


def _completion_http_evidence(events, attempted):
    bodies = {}
    response_index = 0
    for event in events:
        if event["kind"] != "http_response":
            continue
        data = event["data"]
        if data.get("route") != "/completion":
            continue
        require(response_index < len(attempted), "More completion responses than attempts")
        request_id = attempted[response_index]
        response_index += 1
        if data.get("status") != 200:
            continue
        try:
            body = json.loads(base64.b64decode(data["body_base64"]))
        except (ValueError, TypeError, KeyError):
            continue
        if not isinstance(body, dict) or "error" in body:
            continue
        bodies[request_id] = {"response": body,
                              "latency_seconds": data.get("elapsed_seconds")}
    return bodies


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
            manifest["authorization"] == load(AUTHORIZATION), "Run binding changed")
    _terminal_summary(folder, events)
    attempted, raw, derived = inventory(plan, events)
    live = [event["data"] for event in events if event["kind"] == "live_prompt_verified"]
    require([item["request_id"] for item in live] ==
            [row["request_id"] for row in plan["requests"][:len(live)]],
            "Live token order")
    require(not attempted or len(live) == MAX_ATTEMPTS,
            "Completion began before all 96 live token checks")
    for path, digest in claim["source_hashes"].items():
        snapshot = folder / "source_snapshot" / path
        require(snapshot.is_file() and sha256(snapshot) == digest, "Snapshot changed")
    sent = [event["data"]["payload"] for event in events
            if event["kind"] == "http_request" and
            event["data"]["route"] == "/completion"]
    require(sent == [payload(row) for row in plan["requests"][:len(attempted)]],
            "Completion payload changed")
    http = _completion_http_evidence(events, attempted)
    rows = []
    for row in plan["requests"]:
        request_id = row["request_id"]
        raw_record = raw.get(request_id) or http.get(request_id)
        response = raw_record["response"] if raw_record else None
        latency = raw_record["latency_seconds"] if raw_record else None
        reconstructed = (result(row, response, latency)
                         if response is not None and latency is not None else None)
        if request_id in derived:
            require(reconstructed == derived[request_id], "Derived result changed")
        state = ("COMPLETED" if request_id in derived else
                 "RAW_RECOVERABLE" if request_id in raw else
                 "HTTP_200_RECOVERABLE" if request_id in http else
                 "ATTEMPTED_UNRESOLVED" if request_id in attempted else "UNATTEMPTED")
        rows.append((row, reconstructed, state))
    return folder, events, rows, len(http)


def audit():
    plan = load(FROZEN)
    validate_plan(plan)
    folder, events, rows, bodies = replay()
    terminal = _terminal_summary(folder, events)
    public = [{"request_id": row["request_id"],
        "request_sha256": row["request_sha256"], "case_id": row["case_id"],
        "persona_id": row["persona_id"], "arm_id": row["arm_id"], "state": state,
        "raw_text_sha256": None if result_row is None else result_row["raw_text_sha256"],
        "generated_tokens": None if result_row is None else result_row["generated_tokens"],
        "stop_reason": None if result_row is None else result_row["stop_reason"],
        "latency_seconds": None if result_row is None else result_row["latency_seconds"],
        "automatic_score": None if result_row is None else result_row["automatic_score"]}
        for row, result_row, state in rows]
    return {"version": "personaslm_placeholder_mechanism_integrity_v4",
        "integrity_status": "PASS", "manifest_sha256": sha256(FROZEN),
        "run_terminal_status": terminal["status"],
        "analysis_eligible": terminal["status"] == "PASS",
        "design_sha256": DESIGN_SHA, "case_bank_sha256": CASE_BANK_SHA,
        "prospective_amendment_sha256": AMENDMENT_SHA,
        "measurement_clarification_sha256": MEASUREMENT_CLARIFICATION_SHA,
        "run_directory": folder.as_posix(),
        "attempted": sum(state != "UNATTEMPTED" for _, _, state in rows),
        "results": sum(state == "COMPLETED" for _, _, state in rows),
        "http_responses_verified": bodies, "journal_events": len(events), "rows": public,
        "raw_text_embedded": False, "new_generations_during_audit": 0,
        "semantic_endpoint_status": "HUMAN_ONLY_NOT_RATED"}


def _endpoint_summary(scores, endpoint):
    states = Counter(score["endpoint_states"][endpoint] for score in scores)
    values = [score[endpoint] for score in scores
              if score["endpoint_states"][endpoint] == "ASSESSED"]
    return {"planned": len(scores), "resolved": len(values),
            "missing": states["MISSING_UNASSESSABLE"],
            "structural_n_a": states["STRUCTURAL_NA"],
            "mean": None if not values else sum(values) / len(values),
            "distribution": dict(sorted(Counter(str(value) for value in values).items()))}


def analyze():
    plan = load(FROZEN)
    validate_plan(plan)
    require(AUDIT.is_file() and load(AUDIT) == audit(), "Frozen execution audit required")
    folder, events, rows, _ = replay()
    _terminal_summary(folder, events, require_pass=True)
    require(all(state == "COMPLETED" for _, _, state in rows),
            "Complete 96-row run required")
    by_arm, by_case, persona_by_case, results_only = defaultdict(list), defaultdict(dict), {}, []
    for row, result_row, _ in rows:
        score = result_row["automatic_score"]
        by_arm[row["arm_id"]].append(score)
        by_case[row["case_id"]][row["arm_id"]] = score
        persona_by_case[row["case_id"]] = row["persona_id"]
        results_only.append(result_row)
    case_ids = sorted(by_case)
    weights = registered_estimand_weights()
    primary_specs = {
        "delta_instruction_package_placeholder_occurrence": (
            "instruction_package_meta_vs_concrete",
            "literal_placeholder_occurrence", (0, 1)),
        "delta_instruction_package_evaluator_gap": (
            "instruction_package_meta_vs_concrete", "evaluator_gap", (-1, 1)),
        "delta_text_declared_owner_attribution_name_proxy": (
            "text_declared_owner_attribution_package",
            "preferred_current_name_selection", (0, 1)),
        "delta_chat_role_template_package_name_proxy": (
            "chat_role_template_package", "preferred_current_name_selection", (0, 1)),
    }
    primary = {name: range_aware_contrast(
        by_case, case_ids, weights[contrast], metric, persona_by_case, bounds)
        for name, (contrast, metric, bounds) in primary_specs.items()}
    secondary_metrics = (
        "literal_placeholder_occurrence", "exact_valid_current_output_line",
        "exactly_two_sentence_realization", "preferred_current_name_selection",
        "any_current_name_selection", "preferred_current_anchor_selection",
        "any_current_anchor_selection",
        "preferred_name_anchor_indicator_discordance", "evaluator_gap")
    secondary = {}
    for contrast, coefficients in weights.items():
        secondary[contrast] = {}
        for metric in secondary_metrics:
            bounds = (-1, 1) if metric == "evaluator_gap" else (0, 1)
            secondary[contrast][metric] = range_aware_contrast(
                by_case, case_ids, coefficients, metric, persona_by_case, bounds)
    memory_events = [event["data"] for event in events if event["kind"] == "memory_observation"]
    available = [item.get("system", {}).get("available_physical")
                 for item in memory_events]
    available = [value for value in available if value is not None]
    peak = max((item.get("process", {}).get("peak_working_set", 0)
                for item in memory_events), default=0)
    inference_seconds = sum(item["latency_seconds"] for item in results_only)
    return {"version": "personaslm_placeholder_mechanism_analysis_v4",
        "evidence_level": "PROSPECTIVE_SYNTHETIC_MECHANISM_STUDY",
        "manifest_sha256": sha256(FROZEN), "execution_audit_sha256": sha256(AUDIT),
        "design_sha256": DESIGN_SHA, "case_bank_sha256": CASE_BANK_SHA,
        "prospective_amendment_path": AMENDMENT.as_posix(),
        "prospective_amendment_sha256": AMENDMENT_SHA,
        "measurement_clarification_path": MEASUREMENT_CLARIFICATION.as_posix(),
        "measurement_clarification_sha256": MEASUREMENT_CLARIFICATION_SHA,
        "effective_estimand_terminology": {
            "I1_minus_I2": "instruction-package_meta-versus-concrete",
            "C3_minus_C1": "text-declared-owner-attribution-package",
            "parent_aliases_are_not_effective_claim_names": True},
        "run_directory": folder.as_posix(), "generations": len(results_only),
        "human_semantic_ratings": 0,
        "semantic_endpoints": {endpoint: "HUMAN_ONLY_NOT_RATED"
                               for endpoint in SEMANTIC_ENDPOINTS},
        "arm_summary": {arm: {endpoint: _endpoint_summary(by_arm[arm], endpoint)
                              for endpoint in AUTOMATIC_ENDPOINTS} for arm in ARMS},
        "primary_automatic_estimands": primary,
        "secondary_automatic_estimands": secondary,
        "primary_human_estimand": "NOT_COMPUTED_NO_GENUINE_HUMAN_LABELS",
        "inferential_policy": {"p_values": "NOT_COMPUTED", "estimation_first": True,
            "logical_missing_outcome_bounds": True,
            "leave_one_persona_out_is_leave_one_case_out": True,
            "confirmatory_or_population_causal_claim": False},
        "effective_claim_boundary": [
            "I1-I2 is an instruction-package contrast, not a pure metasyntax intervention.",
            "C3-C1 is a text-declared-owner-attribution package, not a genuine different-speaker intervention."],
        "resource_observations": {
            "generated_tokens": sum(item["generated_tokens"] for item in results_only),
            "completion_inference_seconds": inference_seconds,
            "server_peak_working_set_bytes": peak,
            "minimum_observed_available_physical_bytes": min(available) if available else None},
        "cumulative_authorization_after": {
            "generations_limit": GENERATION_LIMIT,
            "generations_used": GENERATION_BASELINE + len(results_only),
            "inference_seconds_limit": INFERENCE_LIMIT,
            "inference_seconds_used": INFERENCE_BASELINE + inference_seconds},
        "claim_limits": load(DESIGN)["limitations"],
        "raw_text_embedded": False, "new_generations_during_analysis": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "material-audit",
                                            "authorization-requirements", "register",
                                            "preflight", "run", "audit", "analyze"))
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--preflight", type=Path, default=PREFLIGHT)
    args = parser.parse_args(argv)
    if args.action == "validate":
        print(json.dumps(validate_design(require_unstarted=True), indent=2,
                         ensure_ascii=False, sort_keys=True))
    elif args.action == "material-audit":
        print(json.dumps(material_overlap_audit(), indent=2,
                         ensure_ascii=False, sort_keys=True))
    elif args.action == "authorization-requirements":
        print(json.dumps(authorization_requirements(), indent=2,
                         ensure_ascii=False, sort_keys=True))
    elif args.action == "register":
        require(args.authorization is not None, "--authorization is required")
        print(json.dumps(register(args.authorization), indent=2,
                         ensure_ascii=False, sort_keys=True))
    elif args.action == "preflight":
        report = preflight_receipt()
        write_exclusive(PREFLIGHT, report)
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
        if report["status"] != "PASS":
            return 2
    elif args.action == "run":
        report = run(args.preflight)
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
        if report["status"] != "PASS":
            return 2
    elif args.action == "audit":
        report = audit()
        write_exclusive(AUDIT, report)
        print(json.dumps({"integrity_status": report["integrity_status"],
                          "attempted": report["attempted"],
                          "results": report["results"]}, indent=2, sort_keys=True))
    else:
        report = analyze()
        write_exclusive(ANALYSIS, report)
        print(json.dumps({"generations": report["generations"],
                          "primary_automatic_estimands":
                              report["primary_automatic_estimands"]},
                         indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
