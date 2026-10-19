"""Prospective disjoint synthetic history-surface validation controller.

Import and ``validate`` are offline: they do not tokenize, preflight, launch a
model server, or generate.  Operational phases require a separate exact
authorization and are append-only, zero-retry actions.
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
import re
import shutil
import subprocess
import time

import p1_persona_dialogue_history_template_mechanism as engine


base, s, b = engine.base, engine.s, engine.b
load, sha256, th, require = engine.load, engine.sha256, engine.th, engine.require
write_exclusive = engine.write_exclusive

EVIDENCE = Path("docs/validation/p1/persona_dialogue_disjoint_surface_validation_v1")
DESIGN = EVIDENCE / "prospective_design_v1.json"
CASE_BANK = EVIDENCE / "case_bank_v1.json"
REVIEW_SCHEMA = EVIDENCE / "blinded_human_review_schema_v1.json"
AUTHORIZATION = EVIDENCE / "execution_authorization_v1.json"
FROZEN = EVIDENCE / "frozen_manifest_v1.json"
PREFLIGHT = EVIDENCE / "preflight_v1.json"
AUDIT = EVIDENCE / "execution_audit_v1.json"
ANALYSIS = EVIDENCE / "analysis_v1.json"
MATERIAL_AUDIT = EVIDENCE / "material_disjointness_audit_v1.json"
TEST_SOURCE = Path("tests/test_p1_persona_dialogue_disjoint_surface_validation.py")
ROOT = Path("results/p1_persona_dialogue_disjoint_surface_validation/v1")

DESIGN_SHA = "5091736dbb3a96b38ea76e4acd299a951ef661b3db30efaf270be2bf1274808d"
CASE_BANK_SHA = "b8304ce94b8a159de4d9e779137633a9bd30460113931edf74cbf277868a7dc0"
REVIEW_SCHEMA_SHA = "c72ed0c83131bc80aac54675c29cc4a3fd6ecb33d1055a00d45bf25e48bbbd7a"
MATERIAL_AUDIT_SHA = "9bbcd2b9a4dd5969bb72a38edaf676903da1389aec4abfbf820f630b94873b24"
MAX_ATTEMPTS = 168
GENERATION_BASELINE = 340
INFERENCE_BASELINE = 1968.0195239999766
ARMS = (
    "SF_NO_H",
    "SFH_ALIGNED_RAW",
    "SFH_ALIGNED_DECLARATIVE",
    "SFH_CONFLICT_RAW",
    "SFH_CONFLICT_DECLARATIVE",
    "SFH_IRRELEVANT_RAW",
    "SFH_IRRELEVANT_DECLARATIVE",
)
PRIMARY_METRICS = (
    "preferred_current_anchor_selection",
    "any_current_anchor_selection",
)
STARTED = "disjoint_surface_validation_generation_started"
RAW = "disjoint_surface_validation_raw_generation"
DERIVED = "disjoint_surface_validation_result"


def cfg(plan):
    model = plan["model"]
    return s.Runtime(model["model_file"], model["model_sha256"],
                     model["backend_file"], model_label=model["model_label"])


def _relative(path):
    return Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix()


def _local_module_candidates(module_name):
    parts, candidates = module_name.split("."), []
    for parent in (Path("tools"), Path("src"), Path(".")):
        module = parent.joinpath(*parts)
        candidates.extend((module.with_suffix(".py"), module / "__init__.py"))
        for depth in range(1, len(parts)):
            candidates.append(parent.joinpath(*parts[:depth], "__init__.py"))
    return [path for path in candidates if path.is_file()]


def runtime_python_dependency_paths(entry_paths=None):
    """Return the deterministic transitive local import closure."""
    root = Path.cwd().resolve()
    pending = [Path(path).resolve() for path in (entry_paths or (Path(__file__),))]
    discovered = set()
    while pending:
        path = pending.pop()
        require(path.is_file() and (path == root or root in path.parents),
                "Local dependency escaped repository")
        if path in discovered:
            continue
        discovered.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.add(node.module)
                modules.update(node.module + "." + alias.name
                               for alias in node.names if alias.name != "*")
        for module_name in sorted(modules):
            for candidate in _local_module_candidates(module_name):
                if candidate.resolve() not in discovered:
                    pending.append(candidate.resolve())
    return tuple(sorted((path.relative_to(root) for path in discovered),
                        key=lambda value: value.as_posix()))


def _binding_paths(design):
    bindings = design["bindings"]
    paths = [Path(bindings[key]["path"]) for key in (
        "case_bank", "blinded_human_review_schema", "material_disjointness_audit",
        "cumulative_budget_source",
        "tokenizer_identity_source", "runner_infrastructure")]
    paths.extend(Path(item["path"])
                 for item in bindings["prior_12_case_banks_for_disjointness"])
    return paths


def source_hashes():
    design = load(DESIGN)
    paths = [*runtime_python_dependency_paths(), TEST_SOURCE, DESIGN, CASE_BANK,
             REVIEW_SCHEMA, MATERIAL_AUDIT, *_binding_paths(design)]
    unique = {Path(path).resolve() for path in paths}
    return dict(sorted((_relative(path), sha256(path)) for path in unique))


def _anchor(case, role):
    require(role in ("A", "B", "L", "C", "I"), "Unknown anchor role")
    return f"DSV{case['execution_index'] + 1:03d}{role}"


def anchors(case):
    return {
        "current": {side: _anchor(case, side) for side in ("A", "B")},
        "history": {"aligned": _anchor(case, "L"),
                    "conflict": _anchor(case, "C"),
                    "irrelevant": _anchor(case, "I")},
    }


def request_specs():
    """Freeze a case-blocked augmented cyclic-Latin order."""
    bank = load(CASE_BANK)
    cases = sorted(bank["cases"], key=lambda item: item["execution_index"])
    vectors = ((0, 1, 2, 3, 4, 5, 6),
               (3, 5, 6, 2, 0, 4, 1),
               (6, 3, 1, 4, 5, 0, 2))
    rows = []
    for case in cases:
        index = case["execution_index"]
        if index < 21:
            rotation = index % len(ARMS)
            local_arms = ARMS[rotation:] + ARMS[:rotation]
        else:
            positions = vectors[index - 21]
            local_arms = tuple(ARMS[arm_index] for arm_index, _ in
                               sorted(enumerate(positions), key=lambda item: item[1]))
        for local_position, arm in enumerate(local_arms):
            order = len(rows)
            rows.append({"order": order,
                         "request_id": f"dsv1_{order:03d}_{case['case_id']}_{arm}",
                         "case_id": case["case_id"], "arm": arm,
                         "within_case_position": local_position,
                         "quartile": order // 42 + 1})
    return rows


def _history_reason(design, persona, semantics):
    policy = design["prompt_policy"]
    key = ("irrelevant_reason_template" if semantics == "irrelevant"
           else semantics + "_reason_template")
    return policy[key].format(trait=persona["history_trait"])


def construction(design, bank, case, arm_name):
    require(arm_name in ARMS, "Unknown arm")
    arm, persona = design["arms"][arm_name], bank["personas"][case["persona_id"]]
    mark = anchors(case)
    system = (design["prompt_policy"]["fixed_system_instruction"] +
              "\n\nSYNTHETIC SPEAKER: " + persona["speaker_name"] +
              "\n\nSTYLE: " + persona["S_block"] +
              "\n\nFACTS: " + persona["F_block"])
    messages = [{"role": "system", "content": system}]
    history_user = "Earlier, for a different situation, the speaker considered: " + "; ".join(
        f"[{mark['history'][semantic]}] {case['history_targets'][semantic]}"
        for semantic in case["archived_semantic_display_order"]) + ". Which one did the speaker choose then?"
    if arm["H"]:
        semantics = arm["history_semantics"].casefold()
        semantics = "irrelevant" if semantics == "irrelevant_to_current_decision" else semantics
        target, anchor = case["history_targets"][semantics], mark["history"][semantics]
        reason = _history_reason(design, persona, semantics)
        template = (design["prompt_policy"]["raw_history_template"]
                    if arm["history_surface"] == "RAW_RECOMMENDATION"
                    else design["prompt_policy"]["declarative_history_template"])
        messages.extend(({"role": "user", "content": history_user},
                         {"role": "assistant", "content": template.format(
                             anchor=anchor, target=target, reason=reason)}))
    notes = ["CURRENT EVIDENCE: " + case["current_evidence"],
             "CURRENT CHOICES:"]
    for side in case["current_option_display_order"]:
        option = case["options"][side]
        notes.append(f"Option {side} [{mark['current'][side]}] — "
                     f"{option['canonical']}: {option['attribute']}.")
    question = bank["template_family"]["families"][case["task_family"]]
    user = ("\n".join(notes) + "\n\n" + question +
            " Begin with the exact option label, anchor, and name shown above.")
    messages.append({"role": "user", "content": user})
    return ({key: arm[key] for key in ("S", "F", "H")},
            arm["history_semantics"], arm["history_surface"], messages)


def _sentences(text):
    return base._sentences(text)


def automatic_score(row, text, valid_returned_response=True):
    mark, sentences = row["anchors"], _sentences(text)
    first = sentences[0] if sentences else ""
    all_anchors = {**{value: ("CURRENT", side) for side, value in mark["current"].items()},
                   **{value: ("ARCHIVED", semantic)
                      for semantic, value in mark["history"].items()}}
    found = [anchor for anchor in all_anchors
             if re.search(rf"(?<![A-Za-z0-9]){re.escape(anchor)}(?![A-Za-z0-9])", first)]
    found = list(dict.fromkeys(found))
    selected = all_anchors[found[0]] if len(found) == 1 else (None, None)
    if len(found) > 1:
        category = "MULTIPLE"
    elif not found:
        category = "NONE"
    elif selected[0] == "CURRENT":
        category = ("CURRENT_PREFERRED" if selected[1] == row["preferred_option"]
                    else "CURRENT_NONPREFERRED")
    else:
        category = "ARCHIVED_" + selected[1].upper()
    preferred = int(category == "CURRENT_PREFERRED") if valid_returned_response else None
    any_current = int(category.startswith("CURRENT_")) if valid_returned_response else None
    exact_forms = []
    for side in ("A", "B"):
        exact_forms.append((side, base._normalized(
            f"Option {side} [{mark['current'][side]}] — "
            f"{row['options'][side]['canonical']}.")))
    normalized_first = base._normalized(first)
    exact_consistency = int(any(normalized_first == form for _, form in exact_forms))
    archived_mentions = [anchor for anchor in mark["history"].values()
                         if base._exact_contains(text, anchor)]
    return {
        "measurement_state": ("ASSESSED_VALID_RETURNED_RESPONSE" if valid_returned_response
                              else "MISSING_INVALID_OR_ABSENT_RESPONSE"),
        "selection_category": category,
        "selected_anchor": found[0] if len(found) == 1 else None,
        "selected_scope": selected[0],
        "selected_identity": selected[1],
        "first_sentence_anchor_count": len(found),
        "preferred_current_anchor_selection": preferred,
        "any_current_anchor_selection": any_current,
        "unresolved_or_multiple": (int(category in ("NONE", "MULTIPLE"))
                                   if valid_returned_response else None),
        "exact_current_label_name_consistency": exact_consistency,
        "exact_archived_intrusion": int(bool(archived_mentions)),
        "archived_anchors_in_full_response": archived_mentions,
        "raw_recommendation_frame_occurrence": int(
            "i recommend the " in normalized_first),
        "semantic_review_status": "PENDING_BLINDED_HUMAN_STAGE_A_AND_B_REVIEW",
    }


def _ngrams(strings, n=4):
    grams = set()
    for value in strings:
        words = re.findall(r"[a-z0-9]+", value.casefold())
        grams.update(" ".join(words[index:index + n])
                     for index in range(max(0, len(words) - n + 1)))
    return grams


def material_overlap_audit():
    design, bank = load(DESIGN), load(CASE_BANK)
    current_entities = []
    for persona_id, persona in bank["personas"].items():
        current_entities.extend((persona_id, persona["speaker_name"],
                                 persona["profile_source_id"]))
    for case in bank["cases"]:
        current_entities.extend((case["case_id"], *case["history_targets"].values(),
                                 *(option["canonical"] for option in case["options"].values()),
                                 *anchors(case)["current"].values(),
                                 *anchors(case)["history"].values()))
    current_templates = [bank["template_family"]["family_id"],
                         *bank["template_family"]["families"].values()]
    prior_strings = set()
    prior_hashes = {}
    for binding in design["bindings"]["prior_12_case_banks_for_disjointness"]:
        path = Path(binding["path"])
        require(sha256(path) == binding["sha256"], "Prior bank hash changed")
        values = set(base._strings(load(path)))
        prior_strings.update(values)
        prior_hashes[path.as_posix()] = binding["sha256"]
    normalized_prior = {base._normalized(value) for value in prior_strings}
    entity_overlap = sorted(value for value in current_entities
                            if base._normalized(value) in normalized_prior)
    template_overlap = sorted(value for value in current_templates
                              if base._normalized(value) in normalized_prior)
    current_strings = set(base._strings(bank))
    lexical = sorted(_ngrams(current_strings) & _ngrams(prior_strings))
    current_entity_hashes = {th(base._normalized(value)) for value in current_entities}
    prior_string_hashes = {th(value) for value in normalized_prior}
    entity_hash_overlap = sorted(current_entity_hashes & prior_string_hashes)
    return {
        "schema_version": "personaslm_disjoint_surface_material_audit_v1",
        "status": "PASS" if not entity_overlap and not template_overlap else "FAIL",
        "case_bank_sha256": sha256(CASE_BANK),
        "prior_bank_sha256": prior_hashes,
        "current_entity_count": len(current_entities),
        "current_entity_unique_count": len({base._normalized(v) for v in current_entities}),
        "exact_entity_overlap": entity_overlap,
        "exact_template_overlap": template_overlap,
        "current_normalized_entity_sha256_count": len(current_entity_hashes),
        "prior_normalized_string_sha256_count": len(prior_string_hashes),
        "normalized_entity_sha256_overlap_count": len(entity_hash_overlap),
        "normalized_entity_sha256_overlap": entity_hash_overlap,
        "lexical_4gram_overlap_count": len(lexical),
        "lexical_4gram_overlap_sha256": th("\n".join(lexical)),
        "lexical_4gram_overlap": lexical,
        "hash_overlap_equivalent_to_exact_normalized_overlap":
            (not entity_overlap and not entity_hash_overlap),
        "new_model_generations": 0,
    }


def validate_design(require_unstarted=False):
    require(sha256(DESIGN) == DESIGN_SHA, "Prospective design changed")
    require(sha256(CASE_BANK) == CASE_BANK_SHA, "Case bank changed")
    require(sha256(REVIEW_SCHEMA) == REVIEW_SCHEMA_SHA, "Review schema changed")
    require(sha256(MATERIAL_AUDIT) == MATERIAL_AUDIT_SHA,
            "Material audit changed")
    design, bank, review = load(DESIGN), load(CASE_BANK), load(REVIEW_SCHEMA)
    require(design["status"] ==
            "FROZEN_PROSPECTIVE_CANDIDATE_NOT_AUTHORIZED_NOT_TOKENIZED_NOT_EXECUTED",
            "Design status changed")
    require(bank["status"] ==
            "FROZEN_PROSPECTIVE_SYNTHETIC_MATERIALS_NOT_AUTHORIZED_NOT_TOKENIZED_NOT_EXECUTED",
            "Case-bank status changed")
    require(design["evidence_level"] ==
            "PROSPECTIVE_INDEPENDENT_CASE_SYNTHETIC_VALIDATION" and
            "surface association only" in design["scientific_scope"]["claim_boundary"],
            "Evidence boundary changed")
    require(subprocess.check_output(["git", "branch", "--show-current"],
                                    text=True).strip() ==
            design["bindings"]["source_branch"], "Source branch changed")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"],
                                    text=True).strip() ==
            design["bindings"]["source_head"], "Source HEAD changed")
    for path in _binding_paths(design):
        binding = next((value for value in design["bindings"].values()
                        if isinstance(value, dict) and value.get("path") == path.as_posix()),
                       None)
        if binding is None:
            binding = next(value for value in
                           design["bindings"]["prior_12_case_banks_for_disjointness"]
                           if value["path"] == path.as_posix())
        require(path.is_file() and sha256(path) == binding["sha256"],
                "Bound evidence changed: " + path.as_posix())
    require(design["bindings"]["case_bank"] ==
            {"path": CASE_BANK.as_posix(), "sha256": CASE_BANK_SHA} and
            design["bindings"]["blinded_human_review_schema"] ==
            {"path": REVIEW_SCHEMA.as_posix(), "sha256": REVIEW_SCHEMA_SHA},
            "Local binding changed")

    budget_source = load(Path(design["bindings"]["cumulative_budget_source"]["path"]))[
        "cumulative_authorization_after"]
    require(budget_source == {"generations_limit": 1200,
                              "generations_used": GENERATION_BASELINE,
                              "inference_seconds_limit": 72000,
                              "inference_seconds_used": INFERENCE_BASELINE},
            "Cumulative budget source changed")
    budget = design["resource_budget"]
    require(budget["requests"] == MAX_ATTEMPTS and
            budget["maximum_generated_tokens"] == MAX_ATTEMPTS * 96 and
            budget["minimum_available_physical_ram_bytes"] == 3 * 1024 ** 3 and
            budget["minimum_free_output_disk_bytes"] == 1024 ** 3 and
            budget["global_baseline"]["generations_used"] == GENERATION_BASELINE and
            budget["global_baseline"]["inference_wall_seconds_used"] ==
            INFERENCE_BASELINE and
            1200 - GENERATION_BASELINE >= MAX_ATTEMPTS,
            "Resource budget changed")
    authorization = design["authorization"]
    require(all(authorization[key] is False for key in (
        "execution_authorized", "manifest_creation_authorized",
        "tokenization_authorized", "preflight_authorized",
        "model_server_launch_authorized")) and
        authorization["maximum_generation_attempts_if_authorized"] == MAX_ATTEMPTS and
        authorization["retries"] == authorization["hidden_warmups"] == 0,
        "Prospective authorization boundary changed")
    require(all(value == 0 for value in design["preexecution_state"].values()),
            "Nonzero pre-execution state")
    expected_runtime = {"threads": 4, "threads_batch": 4, "context_tokens": 4096,
        "gpu_layers": 0, "max_new_tokens": 96, "temperature": 0.0, "top_p": 1.0,
        "seed": 42, "stop": [], "ignore_eos": False, "cache_prompt": False,
        "warmup": False, "parallel": 1, "no_context_shift": True}
    require(all(design["runtime"][key] == value
                for key, value in expected_runtime.items()), "Runtime changed")
    require(tuple(design["arms"]) == ARMS and
            design["arms"]["SF_NO_H"]["H"] == 0 and
            all(design["arms"][arm]["H"] == 1 for arm in ARMS[1:]) and
            all(design["arms"][arm]["S"] == design["arms"][arm]["F"] == 1
                for arm in ARMS), "Arm structure changed")

    personas, cases = bank["personas"], bank["cases"]
    require(len(personas) == 12 and len(cases) == 24 and
            [case["execution_index"] for case in cases] == list(range(24)) and
            Counter(case["persona_id"] for case in cases) ==
            Counter({persona_id: 2 for persona_id in personas}),
            "Twelve-persona/two-case allocation changed")
    require(Counter(case["task_family"] for case in cases) ==
            Counter({family: 8 for family in bank["template_family"]["families"]}),
            "Task-family balance changed")
    require(Counter(case["preferred_option"] for case in cases) ==
            Counter({"A": 12, "B": 12}) and
            Counter(tuple(case["current_option_display_order"]) for case in cases) ==
            Counter({("A", "B"): 12, ("B", "A"): 12}),
            "Preferred identity/display order changed")
    preferred_position = Counter(
        "FIRST" if case["current_option_display_order"][0] == case["preferred_option"]
        else "SECOND" for case in cases)
    require(preferred_position == Counter({"FIRST": 12, "SECOND": 12}),
            "Preferred display position changed")
    permutations = {
        ("aligned", "conflict", "irrelevant"),
        ("aligned", "irrelevant", "conflict"),
        ("conflict", "aligned", "irrelevant"),
        ("conflict", "irrelevant", "aligned"),
        ("irrelevant", "aligned", "conflict"),
        ("irrelevant", "conflict", "aligned"),
    }
    require(Counter(tuple(case["archived_semantic_display_order"]) for case in cases) ==
            Counter({permutation: 4 for permutation in permutations}),
            "Archived semantic-role permutation balance changed")
    cells = Counter((tuple(case["archived_semantic_display_order"]),
                     case["preferred_option"],
                     "FIRST" if case["current_option_display_order"][0] ==
                     case["preferred_option"] else "SECOND") for case in cases)
    require(len(cells) == 24 and set(cells.values()) == {1},
            "24-cell counterbalance changed")

    entity_values, all_marks = [], []
    for case in cases:
        require(set(case["options"]) == {"A", "B"} and
                set(case["history_targets"]) ==
                {"aligned", "conflict", "irrelevant"}, "Case entities changed")
        entity_values.extend(option["canonical"] for option in case["options"].values())
        entity_values.extend(case["history_targets"].values())
        mark = anchors(case)
        all_marks.extend((*mark["current"].values(), *mark["history"].values()))
        built = {arm: construction(design, bank, case, arm)[3] for arm in ARMS}
        require(len(built["SF_NO_H"]) == 2 and
                all(len(built[arm]) == 4 for arm in ARMS[1:]),
                "Native role structure changed")
        require(all(messages[0] == built["SF_NO_H"][0] and
                    messages[-1] == built["SF_NO_H"][-1]
                    for messages in built.values()), "Current material changed by arm")
        history_users = {built[arm][1]["content"] for arm in ARMS[1:]}
        require(len(history_users) == 1, "Archived user turn changed across H arms")
        require(not any(base._exact_contains(json.dumps(built["SF_NO_H"]), target)
                        for target in case["history_targets"].values()),
                "NO_H contains archived entity")
        reason_lengths = []
        for semantics, raw_arm, declarative_arm in (
            ("aligned", "SFH_ALIGNED_RAW", "SFH_ALIGNED_DECLARATIVE"),
            ("conflict", "SFH_CONFLICT_RAW", "SFH_CONFLICT_DECLARATIVE"),
            ("irrelevant", "SFH_IRRELEVANT_RAW", "SFH_IRRELEVANT_DECLARATIVE")):
            raw = built[raw_arm][2]["content"].split(". ", 1)
            declarative = built[declarative_arm][2]["content"].split(". ", 1)
            require(len(raw) == len(declarative) == 2 and raw[1] == declarative[1],
                    "Raw/declarative pair changes beyond assistant sentence one")
            require(case["history_targets"][semantics] in raw[0] and
                    anchors(case)["history"][semantics] in raw[0],
                    "History semantic package changed")
            reason_lengths.append(len(raw[1].split()))
        require(max(reason_lengths) - min(reason_lengths) <= 2,
                "History statements not length-comparable")
    require(len(entity_values) == len({base._normalized(v) for v in entity_values}) == 120 and
            len(all_marks) == len(set(all_marks)) == 120,
            "Entity names or anchors are not globally unique")

    rows = request_specs()
    require(len(rows) == len({row["request_id"] for row in rows}) == MAX_ATTEMPTS and
            [row["order"] for row in rows] == list(range(MAX_ATTEMPTS)) and
            Counter(row["arm"] for row in rows) == Counter({arm: 24 for arm in ARMS}),
            "Frozen request allocation changed")
    require(all(Counter(row["arm"] for row in rows
                        if row["case_id"] == case["case_id"]) ==
                Counter({arm: 1 for arm in ARMS}) for case in cases),
            "Within-case pairing changed")
    require(all(Counter(row["arm"] for row in rows if row["quartile"] == quartile) ==
                Counter({arm: 6 for arm in ARMS}) for quartile in range(1, 5)),
            "Per-arm quartile balance changed")
    positions = {arm: [row["within_case_position"] for row in rows if row["arm"] == arm]
                 for arm in ARMS}
    orders = {arm: [row["order"] for row in rows if row["arm"] == arm] for arm in ARMS}
    require(all(set(Counter(values)) == set(range(7)) and
                set(Counter(values).values()) <= {3, 4}
                for values in positions.values()) and
            all(sum(values) == 72 for values in positions.values()) and
            all(sum(values) == 2004 for values in orders.values()),
            "Augmented Latin position balance changed")

    require(tuple(design["evaluation_policy"]["primary_automatic_endpoints"]) ==
            PRIMARY_METRICS, "Primary endpoints changed")
    require(review["status"] == "FROZEN_SCHEMA_ONLY_NO_REVIEW_PACKAGE_NO_HUMAN_LABELS" and
            set(review["stages"]) == {"stage_a", "stage_b"} and
            all(value in (0, False) for value in review["label_state"].values()),
            "Human-review schema is not blank")
    observed_audit = material_overlap_audit()
    require(observed_audit == load(MATERIAL_AUDIT) and
            observed_audit["status"] == "PASS" and
            not observed_audit["exact_entity_overlap"] and
            not observed_audit["exact_template_overlap"],
            "Material overlap audit changed or failed")
    if require_unstarted:
        require(not any(path.exists() for path in
                        (AUTHORIZATION, FROZEN, PREFLIGHT, AUDIT, ANALYSIS,
                         ROOT / "claim.json", ROOT / "native_tokenizer")) and
                not list((ROOT / "runs").glob("*")), "Study already initialized")
    return {"status": "PASS_PROSPECTIVE_NOT_AUTHORIZED_NOT_EXECUTED",
            "synthetic_personas": 12, "cases": 24, "task_families": 3,
            "arms": 7, "requests": MAX_ATTEMPTS,
            "counterbalance_cells": len(cells),
            "material_audit_sha256": sha256(MATERIAL_AUDIT),
            "lexical_4gram_overlap_count": observed_audit["lexical_4gram_overlap_count"],
            "model_generations": 0, "tokenizer_operations": 0,
            "human_labels": 0}


def authorization_requirements():
    checks, design = validate_design(), load(DESIGN)
    return {
        "schema_version": "personaslm_disjoint_surface_execution_authorization_v1",
        "status": "AUTHORIZED_BEFORE_TOKENIZATION_PREFLIGHT_OR_MODEL_EXECUTION",
        "authorization_path": AUTHORIZATION.as_posix(),
        "implementation": {
            "runner": {"path": _relative(Path(__file__)),
                       "sha256": sha256(Path(__file__))},
            "test": {"path": TEST_SOURCE.as_posix(), "sha256": sha256(TEST_SOURCE)}},
        "source_hashes": source_hashes(),
        "design": {"path": DESIGN.as_posix(), "sha256": DESIGN_SHA},
        "case_bank": {"path": CASE_BANK.as_posix(), "sha256": CASE_BANK_SHA},
        "review_schema": {"path": REVIEW_SCHEMA.as_posix(),
                          "sha256": REVIEW_SCHEMA_SHA},
        "material_audit": {"path": MATERIAL_AUDIT.as_posix(),
                           "sha256": MATERIAL_AUDIT_SHA},
        "model_sha256": design["model"]["artifact_sha256"],
        "backend_sha256": design["runtime"]["backend_sha256"],
        "template_sha256": design["runtime"]["chat_template_sha256"],
        "maximum_native_tokenizer_calls": MAX_ATTEMPTS,
        "maximum_live_server_tokenizer_checks": MAX_ATTEMPTS,
        "maximum_tokenizer_operations_total": 2 * MAX_ATTEMPTS,
        "maximum_generation_attempts": MAX_ATTEMPTS,
        "retries": 0, "hidden_warmups": 0,
        "minimum_available_physical_ram_bytes": 3 * 1024 ** 3,
        "minimum_free_output_disk_bytes": 1024 ** 3,
        "actual_completion_inference_seconds_ceiling": 10080.0,
        "batch_wall_seconds_ceiling": 14400.0,
        "global_baseline": copy.deepcopy(design["resource_budget"]["global_baseline"]),
        "results_root": ROOT.as_posix(), "validated_design": checks,
    }


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
    """Freeze prompts and native token IDs; make zero completion calls."""
    require(not any(path.exists() for path in
                    (FROZEN, PREFLIGHT, ROOT / "claim.json", ROOT / "native_tokenizer")) and
            not list((ROOT / "runs").glob("*")),
            "Registration evidence exists; do not replace")
    authorization_path = Path(authorization_path)
    require(authorization_path.resolve() == AUTHORIZATION.resolve(),
            "Official authorization path required")
    authorization = validate_authorization(authorization_path)
    checks, design, bank = validate_design(), load(DESIGN), load(CASE_BANK)
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
    for item in request_specs():
        case = cases[item["case_id"]]
        factors, semantics, surface, messages = construction(
            design, bank, case, item["arm"])
        prompt = s.render(template, messages)
        argv = [str(tokenizer.resolve()), "-m",
                str(Path(model["artifact_path"]).resolve()),
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
                all(type(value) is int and value >= 0 for value in token_ids),
                "Invalid native token IDs")
        log = {"started_utc": started, "finished_utc": b.utc_now(), "argv": argv,
               "returncode": completed.returncode,
               "stdout": completed.stdout.decode("utf-8", "replace"),
               "stderr": completed.stderr.decode("utf-8", "replace"),
               "prompt_sha256": th(prompt), "generation_requests": 0}
        log_path = ROOT / "native_tokenizer" / f"{item['order']:04d}.json"
        write_exclusive(log_path, log)
        logs.append({"path": log_path.as_posix(), "sha256": sha256(log_path)})
        row = {**item, "persona_id": case["persona_id"],
               "task_family": case["task_family"], "factors": factors,
               "history_semantics": semantics, "history_surface": surface,
               "messages": messages, "prompt": prompt,
               "prompt_sha256": th(prompt), "input_token_ids": token_ids,
               "input_tokens": len(token_ids),
               "input_token_ids_sha256": th(str(token_ids)),
               "preferred_option": case["preferred_option"],
               "current_option_display_order": case["current_option_display_order"],
               "archived_semantic_display_order":
                   case["archived_semantic_display_order"],
               "options": case["options"], "history_targets": case["history_targets"],
               "anchors": anchors(case), "max_new_tokens": 96, "seed": 42,
               "temperature": 0.0, "top_p": 1.0, "stop": [],
               "cache_prompt": False, "ignore_eos": False}
        require(len(token_ids) + 96 <= runtime["context_tokens"], "Context overflow")
        row["request_sha256"] = th(json.dumps(
            row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        rows.append(row)
    plan = {
        "version": "p1_persona_dialogue_disjoint_surface_manifest_v1",
        "evidence_level": design["evidence_level"],
        "design_path": DESIGN.as_posix(), "design_sha256": DESIGN_SHA,
        "case_bank_path": CASE_BANK.as_posix(), "case_bank_sha256": CASE_BANK_SHA,
        "review_schema_path": REVIEW_SCHEMA.as_posix(),
        "review_schema_sha256": REVIEW_SCHEMA_SHA,
        "material_audit_path": MATERIAL_AUDIT.as_posix(),
        "material_audit_sha256": MATERIAL_AUDIT_SHA,
        "authorization_path": authorization_path.as_posix(),
        "authorization_sha256": sha256(authorization_path),
        "model": {"model_label": model["label"],
                  "model_file": model["artifact_path"],
                  "model_sha256": model["artifact_sha256"],
                  "backend_file": runtime["backend_path"],
                  "backend_sha256": runtime["backend_sha256"],
                  "quantization": model["quantization"],
                  "artifact_revision": model["artifact_revision"],
                  "intended_upstream_revision": model["intended_upstream_revision"],
                  "conversion_lineage": model["conversion_lineage"]},
        "template_path": runtime["chat_template_path"],
        "template_sha256": runtime["chat_template_sha256"],
        "runtime": runtime, "resource_budget": design["resource_budget"],
        "requests": rows,
        "native_tokenizer_identity": {"path": tokenizer.as_posix(),
            "tokenizer_sha256": native_source["tokenizer_sha256"],
            "dll_hashes": native_source["dll_hashes"]},
        "native_tokenizer_logs": logs,
        "registration_source_hashes": source_hashes(),
        "registered_utc": b.utc_now(), "new_model_generations": 0,
        "human_labels": 0,
    }
    require(authorization["maximum_generation_attempts"] == len(rows) == MAX_ATTEMPTS,
            "Authorization row count changed")
    write_exclusive(FROZEN, plan)
    validate_plan(load(FROZEN))
    return {"status": "REGISTERED_NO_GENERATIONS",
            "manifest_sha256": sha256(FROZEN),
            "authorization_sha256": sha256(authorization_path),
            "native_tokenizer_calls": len(rows), "live_server_tokenizer_checks": 0,
            "tokenizer_operations_total": len(rows), "generation_requests": 0,
            **checks}


def validate_registered_source_hashes(expected):
    observed = source_hashes()
    require(expected == observed, "Registered source or dependency closure changed")
    return observed


def validate_plan(plan):
    require(plan["version"] == "p1_persona_dialogue_disjoint_surface_manifest_v1" and
            plan["design_sha256"] == DESIGN_SHA and
            plan["case_bank_sha256"] == CASE_BANK_SHA and
            plan["review_schema_sha256"] == REVIEW_SCHEMA_SHA and
            plan["material_audit_sha256"] == MATERIAL_AUDIT_SHA,
            "Manifest binding changed")
    validate_authorization(Path(plan["authorization_path"]))
    require(plan["authorization_sha256"] ==
            sha256(Path(plan["authorization_path"])), "Authorization changed")
    validate_registered_source_hashes(plan["registration_source_hashes"])
    checks, design, bank = validate_design(), load(DESIGN), load(CASE_BANK)
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
            plan["new_model_generations"] == plan["human_labels"] == 0 and
            plan["template_sha256"] == sha256(Path(plan["template_path"])),
            "Frozen plan changed")
    cases = {case["case_id"]: case for case in bank["cases"]}
    template = Path(plan["template_path"]).read_text(encoding="utf-8")
    specs = request_specs()
    require(len(plan["requests"]) == len(plan["native_tokenizer_logs"]) ==
            len(specs) == MAX_ATTEMPTS, "Manifest row count changed")
    for item, row, record in zip(specs, plan["requests"],
                                 plan["native_tokenizer_logs"]):
        require(all(row[key] == item[key] for key in (
            "order", "request_id", "case_id", "arm", "within_case_position",
            "quartile")), "Request order changed")
        case = cases[row["case_id"]]
        factors, semantics, surface, messages = construction(
            design, bank, case, row["arm"])
        require(row["factors"] == factors and row["history_semantics"] == semantics and
                row["history_surface"] == surface and row["messages"] == messages and
                row["prompt"] == s.render(template, messages), "Prompt changed")
        expected = {"persona_id": case["persona_id"],
            "task_family": case["task_family"],
            "preferred_option": case["preferred_option"],
            "current_option_display_order": case["current_option_display_order"],
            "archived_semantic_display_order": case["archived_semantic_display_order"],
            "options": case["options"], "history_targets": case["history_targets"],
            "anchors": anchors(case), "max_new_tokens": 96, "seed": 42,
            "temperature": 0.0, "top_p": 1.0, "stop": [],
            "cache_prompt": False, "ignore_eos": False}
        require(all(row[key] == value for key, value in expected.items()),
                "Generation/scoring metadata changed")
        require(row["prompt_sha256"] == th(row["prompt"]) and
                row["input_token_ids_sha256"] == th(str(row["input_token_ids"])) and
                row["input_tokens"] == len(row["input_token_ids"]), "Token binding changed")
        require(row["request_sha256"] == th(json.dumps(
            {key: value for key, value in row.items() if key != "request_sha256"},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"))),
            "Request hash changed")
        token_log = load(Path(record["path"]))
        require(sha256(Path(record["path"])) == record["sha256"] and
                token_log["returncode"] == token_log["generation_requests"] == 0 and
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
            "Model/backend identity changed")
    native, tokenizer = plan["native_tokenizer_identity"], Path(
        plan["native_tokenizer_identity"]["path"])
    require(sha256(tokenizer) == native["tokenizer_sha256"] and
            {path.name: sha256(path) for path in tokenizer.parent.glob("*.dll")} ==
            native["dll_hashes"], "Tokenizer identity changed")
    baseline = load(Path(load(DESIGN)["bindings"]["cumulative_budget_source"]["path"]))[
        "cumulative_authorization_after"]
    require(baseline["generations_used"] == GENERATION_BASELINE and
            baseline["inference_seconds_used"] == INFERENCE_BASELINE and
            baseline["generations_limit"] - GENERATION_BASELINE >= MAX_ATTEMPTS and
            baseline["inference_seconds_limit"] - INFERENCE_BASELINE >= 10080.0,
            "Cumulative budget changed")
    if require_unused:
        require(not (ROOT / "claim.json").exists() and
                not list((ROOT / "runs").glob("*")), "Existing allocation: no repeat")
    memory = s.memory_observation(os.getpid())
    if check_headroom:
        require(memory.get("system", {}).get("available_physical", 0) >= 3 * 1024 ** 3,
                "Less than 3 GiB available RAM")
    require(shutil.disk_usage(".").free >= 1024 ** 3, "Output disk reserve")
    return {"status": "PASS", "checked_utc": b.utc_now(), "checks": checks,
        "identity": identity, "manifest_sha256": sha256(FROZEN),
        "authorization_sha256": sha256(Path(plan["authorization_path"])),
        "design_sha256": DESIGN_SHA, "case_bank_sha256": CASE_BANK_SHA,
        "review_schema_sha256": REVIEW_SCHEMA_SHA,
        "material_audit_sha256": MATERIAL_AUDIT_SHA,
        "source_hashes": source_hashes(), "configuration": cfg(plan).as_dict(),
        "server_command": s.command(plan), "memory_before_run": memory,
        "cumulative_baseline": baseline,
        "live_gate": "All 168 parse_special=true token arrays must match before completion 1.",
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
        return {"status": "FAIL", "checked_utc": b.utc_now(),
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "expected_bindings": {"design_sha256": DESIGN_SHA,
                                  "case_bank_sha256": CASE_BANK_SHA,
                                  "review_schema_sha256": REVIEW_SCHEMA_SHA,
                                  "material_audit_sha256": MATERIAL_AUDIT_SHA},
            "memory_observation": memory,
            "free_output_disk_bytes": shutil.disk_usage(".").free,
            "minimum_available_physical_ram_bytes": 3 * 1024 ** 3,
            "minimum_free_output_disk_bytes": 1024 ** 3,
            "model_server_launches": 0, "completion_calls": 0,
            "new_model_generations": 0}


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
            "Generated token count changed")
    returned = (len(normal["generated_token_ids"])
                if normal["generated_token_ids"] is not None else None)
    require(returned is None or returned <= count, "Returned tokens exceed native count")
    if normal["stop_reason"] != "stop_sequence" and normal["token_ids_status"] == "returned":
        require(returned == count, "Token count mismatch")
    boundary = b.classify_response(normal["raw_response"], normal["raw_termination"],
                                   declared_stops=())
    first_span = boundary["first_span"]["text"]
    valid = bool(first_span and first_span.strip())
    score = automatic_score(row, normal["raw_response"], valid)
    if valid:
        require(all(score[metric] in (0, 1) for metric in PRIMARY_METRICS),
                "Complete primary denominator failed")
    return {"request_id": row["request_id"],
        "request_sha256": row["request_sha256"], **normal,
        "generated_tokens": count, "returned_token_count": returned,
        "latency_seconds": latency, "input_token_audit": token_audit,
        "response_status": boundary, "raw_text_sha256": th(normal["raw_response"]),
        "first_reply_sha256": th(first_span), "automatic_score": score,
        "human_semantic_ratings": 0,
        "human_review_status": "PENDING_BLINDED_HUMAN_STAGE_A_AND_B_REVIEW",
        "evidence_level": "PROSPECTIVE_INDEPENDENT_CASE_SYNTHETIC_VALIDATION"}


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
                "case_bank_sha256", "review_schema_sha256", "material_audit_sha256",
                "source_hashes", "configuration", "server_command"):
        require(stored[key] == fresh[key], "Preflight binding changed: " + key)
    with b.writer_lock(ROOT):
        require(not (ROOT / "claim.json").exists() and
                not list((ROOT / "runs").glob("*")),
                "Existing allocation: no repeat or resume")
        claim = {key: fresh[key] for key in (
            "manifest_sha256", "authorization_sha256", "design_sha256",
            "case_bank_sha256", "review_schema_sha256", "material_audit_sha256",
            "source_hashes")}
        claim.update(preflight_sha256=sha256(preflight_path),
                     maximum_attempts=MAX_ATTEMPTS, retries=0, hidden_warmups=0)
        write_exclusive(ROOT / "claim.json", claim)
        authorization = load(Path(plan["authorization_path"]))
        journal = b.RunJournal(ROOT / "runs", {
            "phase": "P1 disjoint synthetic history semantics-by-surface validation",
            "evidence_level": "PROSPECTIVE_INDEPENDENT_CASE_SYNTHETIC_VALIDATION",
            "claim": claim, "frozen_manifest": plan,
            "authorization": authorization, "configuration": cfg(plan).as_dict(),
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
        inference_seconds = failed_seconds = 0.0
        try:
            journal.write("preflight", fresh)
            with s.Server(plan, journal) as server:
                client = b.LlamaClient(cfg(plan).endpoint, timeout=180,
                                       audit=journal.write)
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
                    journal.write("live_prompt_verified", {
                        "request_id": row["request_id"],
                        "token_ids_sha256": th(str(tokens))})
                journal.write("live_preflight_pass", {"prompts": MAX_ATTEMPTS,
                                                       "completed_inference": 0})
                print(json.dumps({"live_preflight": "PASS",
                                  "planned": MAX_ATTEMPTS}), flush=True)
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
                        response = client.request("/completion", payload(row))
                    except BaseException:
                        elapsed = time.monotonic() - tick
                        inference_seconds += elapsed
                        failed_seconds += elapsed
                        journal.write("disjoint_surface_validation_completion_failed", {
                            "request_id": active, "elapsed_seconds": elapsed})
                        raise
                    latency = time.monotonic() - tick
                    inference_seconds += latency
                    journal.write(RAW, {"request_id": active, "response": response,
                                        "latency_seconds": latency})
                    journal.write(DERIVED, result(row, response, latency))
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
            journal.write("failure", {"type": type(exc).__name__,
                                      "message": str(exc), "request_id": active})
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
            "inference_wall_seconds":
                sum(value["latency_seconds"] for value in raw.values()) + failed_seconds,
            "failed_completion_seconds": failed_seconds,
            "batch_wall_seconds": time.monotonic() - started,
            "run_directory": journal.directory.as_posix(), "retries": 0,
            "hidden_warmups": 0, "human_semantic_ratings": 0,
            "human_review_status": "PENDING_BLINDED_HUMAN_STAGE_A_AND_B_REVIEW"}
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
    claim, manifest = load(ROOT / "claim.json"), load(folder / "manifest.json")
    require(claim["manifest_sha256"] == sha256(FROZEN) and
            claim["authorization_sha256"] ==
            sha256(Path(plan["authorization_path"])) and
            claim["design_sha256"] == DESIGN_SHA and
            claim["case_bank_sha256"] == CASE_BANK_SHA and
            claim["review_schema_sha256"] == REVIEW_SCHEMA_SHA and
            claim["material_audit_sha256"] == MATERIAL_AUDIT_SHA and
            claim["preflight_sha256"] == sha256(PREFLIGHT) and
            claim["maximum_attempts"] == MAX_ATTEMPTS and
            claim["retries"] == claim["hidden_warmups"] == 0,
            "Run claim changed")
    require(manifest["claim"] == claim and manifest["frozen_manifest"] == plan and
            manifest["authorization"] == load(Path(plan["authorization_path"])),
            "Run manifest binding changed")
    summary = load(folder / "summary.json")
    require(events and events[-1]["kind"] == "run_finished" and
            events[-1]["data"] == summary, "Terminal event changed")
    if summary["status"] == "PASS":
        require(sum(event["kind"] == "postflight" for event in events) == 1,
                "Successful run lacks postflight")
    attempted, raw, derived = inventory(plan, events)
    live = [event["data"] for event in events
            if event["kind"] == "live_prompt_verified"]
    require([item["request_id"] for item in live] ==
            [row["request_id"] for row in plan["requests"][:len(live)]] and
            (not attempted or len(live) == MAX_ATTEMPTS), "Live-token gate changed")
    for path, digest in claim["source_hashes"].items():
        snapshot = folder / "source_snapshot" / path
        require(snapshot.is_file() and sha256(snapshot) == digest,
                "Source snapshot changed: " + path)
    sent = [event["data"]["payload"] for event in events
            if event["kind"] == "http_request" and
            event["data"]["route"] == "/completion"]
    require(sent == [payload(row) for row in plan["requests"][:len(attempted)]],
            "Completion payload changed")
    bodies = [json.loads(base64.b64decode(event["data"]["body_base64"]))
              for event in events if event["kind"] == "http_response" and
              event["data"]["route"] == "/completion" and
              event["data"].get("status") == 200]
    require(bodies == [record["response"] for record in raw.values()],
            "Raw HTTP body changed")
    rows = []
    for row in plan["requests"]:
        request_id = row["request_id"]
        reconstructed = (result(row, raw[request_id]["response"],
                                raw[request_id]["latency_seconds"])
                         if request_id in raw else None)
        if request_id in derived:
            require(reconstructed == derived[request_id], "Derived result changed")
        state = ("COMPLETED" if request_id in derived else
                 "RAW_RECOVERABLE" if reconstructed is not None else
                 "ATTEMPTED_UNRESOLVED" if request_id in attempted else "UNATTEMPTED")
        rows.append((row, reconstructed, state))
    return folder, events, rows, len(bodies), raw


def audit():
    plan = load(FROZEN)
    validate_plan(plan)
    folder, events, rows, bodies, _ = replay()
    public = []
    for row, result_row, state in rows:
        public.append({"request_id": row["request_id"],
            "request_sha256": row["request_sha256"], "case_id": row["case_id"],
            "arm": row["arm"], "state": state,
            "raw_text_sha256": None if result_row is None else result_row["raw_text_sha256"],
            "first_reply_sha256": (None if result_row is None
                                   else result_row["first_reply_sha256"]),
            "generated_tokens": (None if result_row is None
                                 else result_row["generated_tokens"]),
            "stop_reason": None if result_row is None else result_row["stop_reason"],
            "latency_seconds": (None if result_row is None
                                else result_row["latency_seconds"]),
            "automatic_score": (None if result_row is None
                                else result_row["automatic_score"])})
    return {"version": "p1_persona_dialogue_disjoint_surface_integrity_v1",
        "integrity_status": "PASS", "manifest_sha256": sha256(FROZEN),
        "design_sha256": DESIGN_SHA, "case_bank_sha256": CASE_BANK_SHA,
        "review_schema_sha256": REVIEW_SCHEMA_SHA,
        "material_audit_sha256": MATERIAL_AUDIT_SHA,
        "run_directory": folder.as_posix(),
        "attempted": sum(state != "UNATTEMPTED" for _, _, state in rows),
        "results": sum(state == "COMPLETED" for _, _, state in rows),
        "http_responses_verified": bodies, "journal_events": len(events),
        "rows": public, "raw_text_embedded": False,
        "human_labels": 0, "new_generations_during_audit": 0}


def _mean(values):
    return None if not values else sum(values) / len(values)


def _binary_summary(scores, metric):
    values = [score[metric] for score in scores]
    ones = sum(value == 1 for value in values)
    zeros = sum(value == 0 for value in values)
    missing = sum(value is None for value in values)
    resolved = [value for value in values if value is not None]
    return {"ones": ones, "zeros": zeros, "missing": missing,
            "total_slots": len(values), "resolved_denominator": len(resolved),
            "mean_resolved": _mean(resolved), "logical_lower": ones / len(values),
            "logical_upper": (ones + missing) / len(values)}


def _contrast(by_case, case_ids, weights, metric, persona_by_case):
    records = []
    for case_id in sorted(case_ids):
        contribution, lower, upper, complete = 0.0, 0.0, 0.0, True
        for arm, weight in weights.items():
            value = by_case[case_id][arm][metric]
            if value is None:
                complete = False
                lower += min(0.0, weight)
                upper += max(0.0, weight)
            else:
                contribution += weight * value
                lower += weight * value
                upper += weight * value
        records.append({"case_id": case_id,
            "persona_id": persona_by_case[case_id],
            "contribution": contribution if complete else None,
            "logical_lower": lower, "logical_upper": upper})
    complete = [record["contribution"] for record in records
                if record["contribution"] is not None]
    leave_one_out = {}
    for persona_id in sorted(set(persona_by_case.values())):
        kept = [record for record in records if record["persona_id"] != persona_id]
        values = [record["contribution"] for record in kept
                  if record["contribution"] is not None]
        leave_one_out[persona_id] = {"complete_case_estimate": _mean(values),
            "complete_cases": len(values),
            "logical_lower": _mean([record["logical_lower"] for record in kept]),
            "logical_upper": _mean([record["logical_upper"] for record in kept])}
    loo = [value["complete_case_estimate"] for value in leave_one_out.values()
           if value["complete_case_estimate"] is not None]
    return {"metric": metric, "weights": weights, "eligible_cases": len(records),
        "complete_cases": len(complete), "unresolved_cases": len(records) - len(complete),
        "complete_case_estimate": _mean(complete),
        "logical_lower": _mean([record["logical_lower"] for record in records]),
        "logical_upper": _mean([record["logical_upper"] for record in records]),
        "case_contributions": records, "leave_one_persona_out": leave_one_out,
        "leave_one_persona_out_point_estimate_range":
            [min(loo), max(loo)] if loo else [None, None]}


def registered_estimand_weights():
    """Return the exact prospective arm coefficients used by analysis."""
    return {
        "theta_A": {"SFH_ALIGNED_RAW": 0.5,
                    "SFH_ALIGNED_DECLARATIVE": 0.5,
                    "SFH_IRRELEVANT_RAW": -0.5,
                    "SFH_IRRELEVANT_DECLARATIVE": -0.5},
        "theta_C": {"SFH_CONFLICT_RAW": 0.5,
                    "SFH_CONFLICT_DECLARATIVE": 0.5,
                    "SFH_IRRELEVANT_RAW": -0.5,
                    "SFH_IRRELEVANT_DECLARATIVE": -0.5},
        "theta_surface": {"SFH_ALIGNED_RAW": -1 / 3,
                          "SFH_ALIGNED_DECLARATIVE": 1 / 3,
                          "SFH_CONFLICT_RAW": -1 / 3,
                          "SFH_CONFLICT_DECLARATIVE": 1 / 3,
                          "SFH_IRRELEVANT_RAW": -1 / 3,
                          "SFH_IRRELEVANT_DECLARATIVE": 1 / 3},
        "theta_generic_history": {"SF_NO_H": -1.0,
                                  "SFH_IRRELEVANT_RAW": 0.5,
                                  "SFH_IRRELEVANT_DECLARATIVE": 0.5},
        "derived_theta_A_minus_theta_C": {"SFH_ALIGNED_RAW": 0.5,
                                           "SFH_ALIGNED_DECLARATIVE": 0.5,
                                           "SFH_CONFLICT_RAW": -0.5,
                                           "SFH_CONFLICT_DECLARATIVE": -0.5},
        "interaction_surface_aligned_minus_irrelevant": {
            "SFH_ALIGNED_RAW": -1.0, "SFH_ALIGNED_DECLARATIVE": 1.0,
            "SFH_IRRELEVANT_RAW": 1.0,
            "SFH_IRRELEVANT_DECLARATIVE": -1.0},
        "interaction_surface_conflict_minus_irrelevant": {
            "SFH_CONFLICT_RAW": -1.0, "SFH_CONFLICT_DECLARATIVE": 1.0,
            "SFH_IRRELEVANT_RAW": 1.0,
            "SFH_IRRELEVANT_DECLARATIVE": -1.0},
    }


def analyze():
    plan = load(FROZEN)
    validate_plan(plan)
    require(AUDIT.is_file(), "Frozen execution audit required before analysis")
    reconstructed_audit = audit()
    require(load(AUDIT) == reconstructed_audit, "Execution audit changed")
    folder, events, rows, _, _ = replay()
    require(all(state == "COMPLETED" for _, _, state in rows),
            "Complete 168-row run required")
    by_arm, by_case = defaultdict(list), defaultdict(dict)
    persona_by_case, family_by_case, results_only = {}, {}, []
    for row, result_row, _ in rows:
        score = result_row["automatic_score"]
        by_arm[row["arm"]].append(score)
        by_case[row["case_id"]][row["arm"]] = score
        persona_by_case[row["case_id"]] = row["persona_id"]
        family_by_case[row["case_id"]] = row["task_family"]
        results_only.append(result_row)
    require(all(set(values) == set(ARMS) for values in by_case.values()),
            "Incomplete paired case")
    weights = registered_estimand_weights()
    case_ids = sorted(by_case)
    estimates = {name: {metric: _contrast(
        by_case, case_ids, arm_weights, metric, persona_by_case)
        for metric in PRIMARY_METRICS} for name, arm_weights in weights.items()}
    family_strata = {}
    for family in sorted(set(family_by_case.values())):
        ids = [case_id for case_id in case_ids if family_by_case[case_id] == family]
        family_strata[family] = {name: {metric: _contrast(
            by_case, ids, arm_weights, metric, persona_by_case)
            for metric in PRIMARY_METRICS} for name, arm_weights in weights.items()}
    condition_summary = {}
    for arm in ARMS:
        scores = by_arm[arm]
        condition_summary[arm] = {
            **{metric: _binary_summary(scores, metric) for metric in PRIMARY_METRICS},
            "selection_categories": dict(sorted(Counter(
                score["selection_category"] for score in scores).items())),
            "exact_archived_intrusion": _binary_summary(scores,
                                                         "exact_archived_intrusion"),
            "raw_recommendation_frame_occurrence": _binary_summary(
                scores, "raw_recommendation_frame_occurrence"),
            "unresolved_or_multiple": _binary_summary(scores,
                                                       "unresolved_or_multiple"),
            "exact_current_label_name_consistency": _binary_summary(
                scores, "exact_current_label_name_consistency")}
    memory_events = [event["data"] for event in events
                     if event["kind"] == "memory_observation"]
    available = [entry.get("system", {}).get("available_physical")
                 for entry in memory_events]
    available = [value for value in available if value is not None]
    peak = max((entry.get("process", {}).get("peak_working_set", 0)
                for entry in memory_events), default=0)
    latency = sum(item["latency_seconds"] for item in results_only)
    generated = sum(item["generated_tokens"] for item in results_only)
    return {
        "version": "p1_persona_dialogue_disjoint_surface_analysis_v1",
        "evidence_level": "PROSPECTIVE_INDEPENDENT_CASE_SYNTHETIC_VALIDATION",
        "claim_boundary": load(DESIGN)["scientific_scope"]["claim_boundary"],
        "manifest_sha256": sha256(FROZEN), "execution_audit_sha256": sha256(AUDIT),
        "design_sha256": DESIGN_SHA, "case_bank_sha256": CASE_BANK_SHA,
        "review_schema_sha256": REVIEW_SCHEMA_SHA,
        "material_audit_sha256": MATERIAL_AUDIT_SHA,
        "run_directory": folder.as_posix(), "generations": len(results_only),
        "human_semantic_ratings": 0,
        "human_review_status": "PENDING_BLINDED_HUMAN_STAGE_A_AND_B_REVIEW",
        "condition_summary": condition_summary,
        "registered_estimates": estimates,
        "task_family_strata": family_strata,
        "inferential_policy": {"p_values": "NOT_COMPUTED",
            "estimation_first": True, "logical_missing_outcome_bounds": True,
            "missing_recoded_as_zero": False,
            "valid_response_multiple_or_none_complete_denominator_zero": True,
            "confirmatory_population_claim": False},
        "measurement_limits": load(CASE_BANK)["limitations"] +
                              load(DESIGN)["known_limitations"],
        "resource_observations": {"generated_tokens": generated,
            "native_stop_reason_distribution": dict(sorted(Counter(
                item["stop_reason"] for item in results_only).items())),
            "completion_inference_seconds": latency,
            "mean_completion_seconds": latency / len(results_only),
            "server_peak_working_set_bytes": peak,
            "minimum_observed_available_physical_bytes":
                min(available) if available else None},
        "cumulative_authorization_after": {"generations_limit": 1200,
            "generations_used": GENERATION_BASELINE + len(results_only),
            "inference_seconds_limit": 72000,
            "inference_seconds_used": INFERENCE_BASELINE + latency},
        "raw_text_embedded": False, "new_generations_during_analysis": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=(
        "validate", "material-audit", "authorization-requirements", "register",
        "preflight", "run", "audit", "analyze"))
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--preflight", type=Path, default=PREFLIGHT)
    args = parser.parse_args(argv)
    if args.action == "validate":
        report = validate_design()
    elif args.action == "material-audit":
        report = material_overlap_audit()
    elif args.action == "authorization-requirements":
        report = authorization_requirements()
    elif args.action == "register":
        require(args.authorization is not None, "--authorization is required")
        report = register(args.authorization)
    elif args.action == "preflight":
        report = preflight_receipt()
        write_exclusive(PREFLIGHT, report)
        if report["status"] != "PASS":
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
    elif args.action == "run":
        report = run(args.preflight)
    elif args.action == "audit":
        report = audit()
        write_exclusive(AUDIT, report)
    else:
        report = analyze()
        write_exclusive(ANALYSIS, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
