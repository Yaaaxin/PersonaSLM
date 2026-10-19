"""Register, execute, and reproduce the private 64-request RPC S/F/H pilot.

Importing and ``validate`` are offline.  Registration performs native
tokenization but no server launch or completion.  Participant material,
prompts, token arrays, raw outputs, and row-level results stay under .local.
"""

from __future__ import annotations

import argparse
import ast
import base64
from collections import defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import statistics
import subprocess
import time
import unicodedata

import p1_persona_dialogue_history_template_mechanism as engine
import real_persona_chat_style_signal_v1 as style_signal


s, b = engine.s, engine.b
load, sha256, th, require = engine.load, engine.sha256, engine.th, engine.require

OUT = Path("docs/validation/p1/real_persona_chat_sfh_pilot_v1")
DESIGN = OUT / "prospective_design_v1.json"
MATERIAL_RECEIPT = OUT / "materialization_receipt_v1.json"
AUDIT = OUT / "independent_execution_audit_v1.json"
AUTHORIZATION_DRAFT = OUT / "execution_authorization_draft_v1.json"
AUTHORIZATION = OUT / "execution_authorization_v1.json"
REGISTRATION = OUT / "prospective_execution_registration_v1.json"
EXECUTION_AUDIT = OUT / "execution_audit_v1.json"
ANALYSIS = OUT / "analysis_v1.json"
TEST_SOURCE = Path("tests/test_real_persona_chat_sfh_pilot_execution_v1.py")
MATERIAL_CONTROLLER = Path("tools/real_persona_chat_sfh_pilot_v1.py")
BUDGET_SOURCE = Path(
    "docs/validation/p1/persona_dialogue_disjoint_surface_validation_v3/analysis_v3.json")
TOKENIZER_SOURCE = Path("docs/validation/p1d/budget_calibration_v1/frozen_manifest_v2.json")
STYLE_VALIDITY_FILES = (
    Path("docs/validation/p1/real_persona_chat_style_signal_validity_v1/registration_v1.json"),
    Path("docs/validation/p1/real_persona_chat_style_signal_validity_v1/registration_amendment_v1_1.json"),
    Path("docs/validation/p1/real_persona_chat_style_signal_validity_v1/analysis_v1.json"),
    Path("docs/validation/p1/real_persona_chat_style_signal_validity_v1/scientific_report_v1.md"),
)
STYLE_VALIDITY_ANALYSIS_SHA256 = (
    "7778a7857ad9689be9deb3b17867fff92fe6b5f110ea103298ecc49b2b55f5da")
PRIVATE_ROOT = Path(".local/experiments/real_persona_chat_sfh_pilot_v1/execution_v1")
PRIVATE_MATERIAL = Path(".local/experiments/real_persona_chat_sfh_pilot_v1/materials_v1.json")
FROZEN = PRIVATE_ROOT / "frozen_manifest_v1.json"
TOKENIZER_ROOT = PRIVATE_ROOT / "native_tokenizer"
RUN_ROOT = PRIVATE_ROOT / "runs"
CLAIM = PRIVATE_ROOT / "claim_v1.json"
PRIVATE_ANALYSIS = PRIVATE_ROOT / "analysis_private_v1.json"
REMAINING_SUFFIX = PRIVATE_ROOT / "remaining_suffix_manifest_v1.json"

MAX_ATTEMPTS = 64
GENERATION_BASELINE = 508
INFERENCE_BASELINE = 3171.544608799969
GENERATION_LIMIT = 1200
INFERENCE_LIMIT = 72000.0
INFERENCE_CEILING = 1200.0
WALL_CEILING = 1800.0
MIN_PREFLIGHT_RAM = 3 * 1024 ** 3
MIN_READY_RAM = 1024 ** 3
MIN_LIVE_RAM = 512 * 1024 ** 2
MIN_DISK = 1024 ** 3
MAX_INPUT_TOKENS = 1750
CONTEXT_TOKENS = 4096
MAX_NEW_TOKENS = 96
BLOCK_SIZE = 32

MODEL = {
    "model_label": "Qwen3.5-2B-native-chat-Q4_K_M-third-party-development",
    "model_file": "models/gguf/instruct_candidates/lmstudio-bb84e113/Qwen3.5-2B-Q4_K_M.gguf",
    "model_sha256": "0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc",
    "backend_file": "bin/llama.cpp/llama-b11573-bin-win-cpu-x64/llama-server.exe",
    "backend_sha256": "71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846",
    "tokenizer_sha256": "e05dbdef761e577b3d56f3daea7b205a07f68e5d87242ea4e2544382ffdd358e",
    "quantization": "Q4_K_M",
    "artifact_revision": "bb84e11355a036e28f080c7793fa6d22b7c4e344",
    "intended_upstream_revision": "965dcc54bc9c0591873df0e9869c056a54d323d1",
    "conversion_lineage": "PARTIALLY_VERIFIED_DEVELOPMENT_ONLY",
}
RUNTIME = {
    "backend_build": "b11573-0f701c882",
    "chat_template_path": (
        "docs/validation/p1d/development_readiness_v1/official_instruct_metadata/"
        "chat_template.jinja"),
    "chat_template_sha256": "0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6",
    "chat_template_kwargs": {"enable_thinking": False},
    "threads": 4,
    "threads_batch": 4,
    "context_tokens": CONTEXT_TOKENS,
    "gpu_layers": 0,
    "max_new_tokens": MAX_NEW_TOKENS,
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

CONDITIONS = {f"C{index}": {
    "S": (index >> 0) & 1, "F": (index >> 1) & 1, "H": (index >> 2) & 1}
              for index in range(8)}
XOR_MASKS = {"B1": (0, 3, 5, 6), "B2": (1, 2, 4, 7)}
STYLE_FEATURES = (
    "mean_turn_length", "question_turn_rate", "exclamation_turn_rate",
    "ellipsis_turn_rate", "laughter_turn_rate", "polite_ending_rate")
COPY_SOURCES = ("S", "F", "H", "query")
EXPOSED_PROMPT_LABELS = ("[話し方]", "[人物情報]", "[過去の会話]", "[相手の発話]")
FACTORS = {
    "S": ("S",), "F": ("F",), "H": ("H",),
    "SF": ("S", "F"), "SH": ("S", "H"),
    "FH": ("F", "H"), "SFH": ("S", "F", "H"),
}
STARTED = "rpc_sfh_generation_started"
RAW = "rpc_sfh_raw_generation"
DERIVED = "rpc_sfh_result"

SCORER_SPECIFICATION = {
    "version": "personaslm_rpc_sfh_automatic_scorer_v1",
    "normalization": "Unicode NFKC, casefold, remove all whitespace, retain punctuation",
    "response_unit": (
        "boundary-certified nonempty first unit except TRUNCATED and containing none of the "
        "four frozen exposed prompt-section labels; otherwise structurally invalid"),
    "exposed_prompt_section_labels": list(EXPOSED_PROMPT_LABELS),
    "character_trigram": "set-valued contiguous normalized character trigrams",
    "reference_overlap": (
        "set trigram F1; normalized generated strings shorter than three characters score 0; "
        "the materializer guarantees normalized references of at least eight characters"),
    "copying": (
        "for each latent S/F/H/query source in every condition: unique generated-trigram "
        "precision present in the union of source-unit trigram sets, plus maximum per-unit "
        "longest-common-substring length divided by normalized generated length; empty/short "
        "generated text scores 0; empty source scores 0"),
    "style_proxy": {
        "features": list(STYLE_FEATURES),
        "scales": {name: 1.0 for name in STYLE_FEATURES},
        "weights": {name: 1 / len(STYLE_FEATURES) for name in STYLE_FEATURES},
        "mean_length_definition": "characters divided by 50 in source and generated vectors",
        "distance": "equal-weight mean absolute difference; lower is closer",
        "scope": "secondary mixed stylometric proxy; one short response is unstable",
    },
    "missingness": (
        "native/API failure has structural validity 0 and all text-derived outcomes missing; "
        "a successful empty response has structural validity 0, reference-F1/copy/length 0, "
        "and Japanese/style missing; other unassessable text outcomes are missing"),
    "factorial_effects": (
        "with x_j=2*factor_j-1, every nonempty subset A is 2*mean(y*product(x_j)); "
        "a main effect is mean(factor=1)-mean(factor=0), and interactions use the same "
        "Hadamard product coding"),
    "inference": "descriptive speaker-paired estimates only; no confirmatory p-values",
}
SCORER_SPECIFICATION_SHA256 = th(json.dumps(
    SCORER_SPECIFICATION, ensure_ascii=False, sort_keys=True, separators=(",", ":")))

AUTOMATIC_METRICS = (
    "structural_response_validity", "japanese_character_present", "japanese_script_rate",
    "output_length_characters", "reference_character_trigram_f1",
    "source_style_distance", "copy_S_trigram_precision", "copy_S_lcs_ratio",
    "copy_F_trigram_precision", "copy_F_lcs_ratio", "copy_H_trigram_precision",
    "copy_H_lcs_ratio", "copy_query_trigram_precision", "copy_query_lcs_ratio",
    "generated_tokens", "latency_seconds")


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def value_sha256(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _relative(path):
    return Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix()


def write_exclusive(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    b.atomic_json(path, value)


def cfg(plan):
    model = plan["model"]
    return s.Runtime(model["model_file"], model["model_sha256"],
                     model["backend_file"], model_label=model["model_label"])


def normalize_text(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(text)).casefold())


def character_ngrams(text, size=3):
    text = normalize_text(text)
    if len(text) < size:
        return set()
    return {text[index:index + size] for index in range(len(text) - size + 1)}


def character_trigram_f1(generated, reference):
    generated_grams, reference_grams = character_ngrams(generated), character_ngrams(reference)
    require(reference_grams, "Reference must contain character trigrams")
    if not generated_grams:
        return 0.0
    shared = len(generated_grams & reference_grams)
    precision, recall = shared / len(generated_grams), shared / len(reference_grams)
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def _longest_common_substring(left, right):
    left, right = normalize_text(left), normalize_text(right)
    if not left or not right:
        return 0
    previous, best = [0] * (len(right) + 1), 0
    for a in left:
        current = [0]
        for index, b_value in enumerate(right, start=1):
            value = previous[index - 1] + 1 if a == b_value else 0
            current.append(value)
            best = max(best, value)
        previous = current
    return best


def copying_scores(generated, source_units):
    generated_normalized = normalize_text(generated)
    generated_grams = character_ngrams(generated)
    units = [str(value) for value in source_units if normalize_text(value)]
    if not generated_normalized:
        return {"trigram_precision": 0.0, "lcs_ratio": 0.0}
    source_grams = set().union(*(character_ngrams(value) for value in units)) if units else set()
    precision = (len(generated_grams & source_grams) / len(generated_grams)
                 if generated_grams else 0.0)
    longest = max((_longest_common_substring(generated, value) for value in units), default=0)
    return {"trigram_precision": precision,
            "lcs_ratio": longest / len(generated_normalized)}


def source_style_distance(generated, case):
    observed = style_signal.style_vector([{"turns": [generated]}])
    source = case["style_features"]
    expected = {
        "mean_turn_length": source["mean_turn_length_characters"] / 50.0,
        **{name: source[name] for name in STYLE_FEATURES if name != "mean_turn_length"},
    }
    return statistics.fmean(abs(observed[name] - expected[name])
                            for name in STYLE_FEATURES)


def _source_units(case):
    return {
        "S": [case["style_profile"]],
        "F": list(case["facts"]),
        "H": [turn["text"] for turn in case["history"]],
        "query": [case["query"]["text"]],
    }


def score_text(text, case, assessable):
    score = {"structural_response_validity": int(bool(assessable))}
    missing = {metric: None for metric in AUTOMATIC_METRICS
               if metric not in ("structural_response_validity", "generated_tokens",
                                 "latency_seconds")}
    if not assessable:
        score.update(missing)
        if not normalize_text(text):
            score.update({"output_length_characters": 0,
                          "reference_character_trigram_f1": 0.0})
            for name in COPY_SOURCES:
                score[f"copy_{name}_trigram_precision"] = 0.0
                score[f"copy_{name}_lcs_ratio"] = 0.0
        return score
    normalized = normalize_text(text)
    japanese = sum((0x3040 <= ord(char) <= 0x30FF or
                    0x3400 <= ord(char) <= 0x4DBF or
                    0x4E00 <= ord(char) <= 0x9FFF) for char in normalized)
    score.update({
        "japanese_character_present": int(japanese > 0),
        "japanese_script_rate": japanese / len(normalized) if normalized else 0.0,
        "output_length_characters": len(normalized),
        "reference_character_trigram_f1": character_trigram_f1(
            text, case["reference"]["text"]),
        "source_style_distance": source_style_distance(text, case),
    })
    for name, units in _source_units(case).items():
        copying = copying_scores(text, units)
        score[f"copy_{name}_trigram_precision"] = copying["trigram_precision"]
        score[f"copy_{name}_lcs_ratio"] = copying["lcs_ratio"]
    return score


def native_failure_score():
    return {metric: (0 if metric == "structural_response_validity" else None)
            for metric in AUTOMATIC_METRICS}


def pending_human_review():
    return {"status": "PENDING_NOT_COLLECTED", "rating_count": 0, "ratings": []}


def _local_module_candidates(module_name):
    parts, candidates = module_name.split("."), []
    for parent in (Path("tools"), Path("src"), Path(".")):
        module = parent.joinpath(*parts)
        candidates.extend((module.with_suffix(".py"), module / "__init__.py"))
        for depth in range(1, len(parts)):
            candidates.append(parent.joinpath(*parts[:depth], "__init__.py"))
    return [path for path in candidates if path.is_file()]


def runtime_python_dependency_paths(entry_paths=None):
    root = Path.cwd().resolve()
    pending = [Path(path).resolve() for path in (entry_paths or (Path(__file__),))]
    discovered = set()
    while pending:
        path = pending.pop()
        require(path.is_file() and root in path.parents, "Local dependency escaped repository")
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
            pending.extend(candidate.resolve()
                           for candidate in _local_module_candidates(module_name)
                           if candidate.resolve() not in discovered)
    return tuple(sorted((path.relative_to(root) for path in discovered),
                        key=lambda value: value.as_posix()))


def source_hashes():
    paths = [*runtime_python_dependency_paths(), TEST_SOURCE, MATERIAL_CONTROLLER,
             DESIGN, MATERIAL_RECEIPT, AUDIT, AUTHORIZATION, BUDGET_SOURCE,
             TOKENIZER_SOURCE, *STYLE_VALIDITY_FILES]
    unique = {Path(path).resolve() for path in paths}
    return dict(sorted((_relative(path), sha256(path)) for path in unique))


def _validate_xor_schedule(material):
    rows = material["requests"]
    require(len(rows) == MAX_ATTEMPTS, "Request count")
    cases_by_block = {}
    for block in ("B1", "B2"):
        block_rows = [row for row in rows if row["block"] == block]
        case_ids = list(dict.fromkeys(row["case_id"] for row in block_rows))
        require(len(block_rows) == BLOCK_SIZE and len(case_ids) == 4,
                "Each block must be four speakers by eight conditions")
        cases_by_block[block] = case_ids
        for case_index, (case_id, mask) in enumerate(zip(case_ids, XOR_MASKS[block])):
            case_rows = [row for row in block_rows if row["case_id"] == case_id]
            require(len(case_rows) == 8, "Eight conditions per case")
            for position, row in enumerate(case_rows):
                expected = f"C{position ^ mask}"
                require(row["condition"] == expected,
                        f"XOR schedule changed for {block} case {case_index}")
    for position in range(8):
        at_position = []
        for block, case_ids in cases_by_block.items():
            block_rows = [row for row in rows if row["block"] == block]
            for case_id in case_ids:
                case_rows = [row for row in block_rows if row["case_id"] == case_id]
                at_position.append(case_rows[position]["condition"])
            for factor in ("S", "F", "H"):
                values = [CONDITIONS[condition][factor] for condition in at_position[-4:]]
                require(values.count(0) == values.count(1) == 2,
                        "Block-position factor imbalance")
        require(set(at_position) == set(CONDITIONS), "Position lacks all conditions")
    return {"schedule": "XOR_LATIN_8X8", "masks": XOR_MASKS,
            "every_condition_each_position": True,
            "factor_balance_within_block_position": True}


def validate_materials():
    design, receipt, material = load(DESIGN), load(MATERIAL_RECEIPT), load(PRIVATE_MATERIAL)
    require(material["schema_version"] == "personaslm_rpc_sfh_pilot_v1",
            "Private material schema")
    require(material["status"] == "PRIVATE_MATERIALS_FROZEN_NO_INFERENCE",
            "Private materials not frozen")
    require(receipt["status"] == "MATERIALS_FROZEN_MODEL_AND_EXECUTION_NOT_REGISTERED",
            "Material receipt status")
    require(receipt["private_material_sha256"] == sha256(PRIVATE_MATERIAL),
            "Private material hash")
    require(receipt["allocation"]["requests"] == MAX_ATTEMPTS and
            receipt["allocation"]["speakers"] == 8, "Receipt allocation")
    require(len(material["cases"]) == len({row["case_id"] for row in material["cases"]}) == 8,
            "Private case allocation")
    require(material["conditions"] == CONDITIONS, "Condition coding")
    case_ids = {case["case_id"] for case in material["cases"]}
    cases = {case["case_id"]: case for case in material["cases"]}
    require(all(row["case_id"] in case_ids for row in material["requests"]),
            "Request/case binding")
    for index, row in enumerate(material["requests"]):
        require(row["request_id"] == f"RPCSFH{index:03d}", "Request ID/order")
        require({key: row[key] for key in ("S", "F", "H")} ==
                CONDITIONS[row["condition"]], "Request factor coding")
        require(row["prompt_sha256"] == hashlib.sha256(canonical(row["messages"])).hexdigest(),
                "Message hash")
        require(row["reference_sha256"] == hashlib.sha256(
            cases[row["case_id"]]["reference"]["text"].encode("utf-8")).hexdigest(),
            "Reference hash")
    public_rows = [{key: row[key] for key in (
        "request_id", "block", "condition", "latin_mask", "within_case_position",
        "prompt_sha256", "reference_sha256")}
                   for row in material["requests"]]
    require(receipt["request_hashes"] == public_rows, "Public request binding")
    rendered_receipt = json.dumps(receipt, ensure_ascii=False)
    public_keys = set()
    pending = [receipt]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            public_keys.update(value)
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    require(not public_keys.intersection(
        {"speaker_id", "messages", "facts", "history", "query", "reference"}),
        "Private field entered receipt")
    require(all(json.dumps(case["speaker_id"], ensure_ascii=False) not in rendered_receipt
                for case in material["cases"]),
            "Private speaker identifier entered receipt")
    schedule = _validate_xor_schedule(material)
    require(design["allocation"]["maximum_generations"] == MAX_ATTEMPTS,
            "Design allocation")
    require(design["allocation"]["retries"] == 0, "Design retry policy")
    return design, receipt, material, schedule


def audit_requirements():
    return {
        "design_sha256": sha256(DESIGN),
        "material_receipt_sha256": sha256(MATERIAL_RECEIPT),
        "private_material_sha256": sha256(PRIVATE_MATERIAL),
        "controller_sha256": sha256(Path(__file__)),
        "test_sha256": sha256(TEST_SOURCE),
        "scorer_specification_sha256": SCORER_SPECIFICATION_SHA256,
    }


def validate_audit():
    audit = load(AUDIT)
    require(audit.get("status") == "PASS" and
            audit.get("verdict") == "PASS_FOR_EXECUTION_REGISTRATION_ONLY",
            "Independent audit did not pass for registration")
    require(audit.get("auditor_provenance") ==
            "AI independent code/scientific audit; not human review",
            "Audit provenance")
    require(audit.get("bindings") == audit_requirements(), "Audit bindings")
    require(audit.get("blocking_findings") == [] and
            audit.get("blocking_finding_count") == 0, "Blocking audit findings")
    checks = audit.get("checks")
    require(isinstance(checks, dict) and checks and all(value is True for value in checks.values()),
            "Audit checks")
    return audit


def authorization_requirements():
    validate_materials()
    audit = validate_audit()
    return {
        "schema_version": "personaslm_rpc_sfh_pilot_execution_authorization_v1",
        "status": "AUTHORIZED_FOR_EXACT_DEVELOPMENT_PILOT",
        "researcher": "Yaxin ZHENG",
        "authority": (
            "Explicit user directive PersonaSLM — REAL-SPEAKER EXPERIMENTAL ACCELERATION, "
            "sections 7, 8, 13 and 14, plus continuing Autonomous Research Charter"),
        "scientific_level": "DEVELOPMENT_EXPLORATORY_NOT_INDEPENDENT_VALIDATION",
        "bindings": {
            **audit_requirements(),
            "audit_sha256": sha256(AUDIT),
            "budget_source_sha256": sha256(BUDGET_SOURCE),
        },
        "model": {key: MODEL[key] for key in (
            "model_label", "model_sha256", "backend_sha256", "tokenizer_sha256",
            "quantization", "artifact_revision", "intended_upstream_revision",
            "conversion_lineage")},
        "runtime": RUNTIME,
        "resources": {
            "maximum_generation_attempts": MAX_ATTEMPTS,
            "maximum_native_tokenizer_calls": MAX_ATTEMPTS,
            "maximum_live_server_tokenizer_checks": MAX_ATTEMPTS,
            "retries": 0, "hidden_warmups": 0,
            "minimum_prelaunch_available_physical_ram_bytes": MIN_PREFLIGHT_RAM,
            "minimum_after_server_ready_available_physical_ram_bytes": MIN_READY_RAM,
            "minimum_before_each_request_available_physical_ram_bytes": MIN_LIVE_RAM,
            "minimum_free_output_disk_bytes": MIN_DISK,
            "completion_inference_seconds_ceiling": INFERENCE_CEILING,
            "batch_wall_seconds_ceiling": WALL_CEILING,
            "cumulative_baseline": {
                "generations_used": GENERATION_BASELINE,
                "inference_seconds_used": INFERENCE_BASELINE,
                "generations_limit": GENERATION_LIMIT,
                "inference_seconds_limit": INFERENCE_LIMIT,
            },
        },
        "blocks": {
            "B1": "exactly four speakers x eight conditions = 32 requests",
            "B2": "exactly four speakers x eight conditions = 32 requests",
            "stopping": (
                "both blocks execute in one allocation; stop only for registered safety, "
                "integrity, technical, cumulative-budget, inference-time, or wall-time failure; "
                "never stop or continue based on outcomes"),
        },
        "automatic_scorer": SCORER_SPECIFICATION,
        "automatic_scorer_sha256": SCORER_SPECIFICATION_SHA256,
        "semantic_endpoints": "HUMAN_REVIEW_PENDING_NOT_SCORED",
        "prohibitions": [
            "retry", "resume", "hidden completion", "warmup", "terminate unrelated applications",
            "outcome-contingent gate", "validation-speaker access", "public row-level output",
            "fabricated human judgment", "confirmatory p-value"],
    }


def style_validity_binding():
    hashes = {_relative(path): sha256(path) for path in STYLE_VALIDITY_FILES}
    analysis_path = STYLE_VALIDITY_FILES[2]
    require(hashes[_relative(analysis_path)] == STYLE_VALIDITY_ANALYSIS_SHA256,
            "Style-validity analysis changed")
    analysis = load(analysis_path)
    return {
        "role": "INTERPRETIVE_PROVENANCE_NOT_AN_EXECUTION_GATE",
        "files": hashes,
        "status": analysis["status"],
        "supported_claim": analysis["supported_claim"],
        "unsupported_claims": analysis["unsupported_claims"],
        "registered_diagnostic_readout": analysis["registered_diagnostic_readout"],
    }


def write_authorization():
    expected = authorization_requirements()
    write_exclusive(AUTHORIZATION, expected)
    return expected


def validate_authorization():
    value = load(AUTHORIZATION)
    require(value == authorization_requirements(), "Authorization changed")
    return value


def _tokenize_native(tokenizer, text):
    argv = [str(tokenizer.resolve()), "-m", str(Path(MODEL["model_file"]).resolve()),
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
    return ids, {"started_utc": started, "finished_utc": b.utc_now(),
                 "argv_sha256": th("\0".join(argv)), "returncode": completed.returncode,
                 "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
                 "stderr": completed.stderr.decode("utf-8", "replace"),
                 "text_sha256": th(text), "generation_requests": 0}


def _tokenizer_identity():
    source = load(TOKENIZER_SOURCE)["native_tokenizer_identity"]
    tokenizer = Path(MODEL["backend_file"]).with_name("llama-tokenize.exe")
    require(sha256(tokenizer) == MODEL["tokenizer_sha256"] == source["tokenizer_sha256"],
            "Tokenizer changed")
    dll_hashes = {path.name: sha256(path) for path in tokenizer.parent.glob("*.dll")}
    require(dll_hashes == source["dll_hashes"], "Backend DLL set changed")
    return {"path": _relative(tokenizer), "tokenizer_sha256": sha256(tokenizer),
            "dll_hashes": dll_hashes}


def register():
    _, receipt, material, schedule = validate_materials()
    authorization = validate_authorization()
    require(not FROZEN.exists() and not REGISTRATION.exists() and
            not CLAIM.exists() and not list(RUN_ROOT.glob("*")),
            "Registration or execution evidence already exists")
    require(shutil.disk_usage(".").free >= MIN_DISK, "Output disk reserve")
    available = s.memory_observation(os.getpid()).get("system", {}).get("available_physical")
    require(type(available) is int and available >= MIN_PREFLIGHT_RAM,
            "Less than registered 3 GiB available physical RAM for native tokenization")
    require(sha256(Path(MODEL["model_file"])) == MODEL["model_sha256"], "Model changed")
    require(sha256(Path(MODEL["backend_file"])) == MODEL["backend_sha256"], "Backend changed")
    template_path = Path(RUNTIME["chat_template_path"])
    require(sha256(template_path) == RUNTIME["chat_template_sha256"], "Template changed")
    tokenizer_identity = _tokenizer_identity()
    tokenizer = Path(tokenizer_identity["path"])
    template = template_path.read_text(encoding="utf-8")
    cases = {case["case_id"]: case for case in material["cases"]}
    rows, evidence = [], []
    for order, source_row in enumerate(material["requests"]):
        prompt = s.render(template, source_row["messages"])
        ids, token_evidence = _tokenize_native(tokenizer, prompt)
        token_path = TOKENIZER_ROOT / f"{order:04d}.json"
        write_exclusive(token_path, token_evidence)
        evidence.append({"path": _relative(token_path), "sha256": sha256(token_path)})
        require(len(ids) <= MAX_INPUT_TOKENS and len(ids) + MAX_NEW_TOKENS <= CONTEXT_TOKENS,
                "Prompt exceeds registered token recommendation/context")
        case = cases[source_row["case_id"]]
        row = {
            "order": order, **source_row,
            "prompt": prompt, "prompt_sha256": th(prompt),
            "input_token_ids": ids, "input_tokens": len(ids),
            "input_token_ids_sha256": th(str(ids)),
            "latent_case": case,
            "max_new_tokens": MAX_NEW_TOKENS, "seed": 42,
            "temperature": 0.0, "top_p": 1.0, "stop": [],
            "ignore_eos": False, "cache_prompt": False,
        }
        row["request_sha256"] = value_sha256(row)
        rows.append(row)
    plan = {
        "schema_version": "personaslm_rpc_sfh_pilot_private_manifest_v1",
        "status": "FROZEN_PRIVATE_REGISTERED_NOT_EXECUTED",
        "scientific_level": "DEVELOPMENT_EXPLORATORY",
        "design_sha256": sha256(DESIGN),
        "material_receipt_sha256": sha256(MATERIAL_RECEIPT),
        "private_material_sha256": sha256(PRIVATE_MATERIAL),
        "authorization_sha256": sha256(AUTHORIZATION),
        "audit_sha256": sha256(AUDIT),
        "budget_source_sha256": sha256(BUDGET_SOURCE),
        "source_hashes": source_hashes(),
        "model": MODEL,
        "runtime": RUNTIME,
        "template_path": RUNTIME["chat_template_path"],
        "tokenizer_identity": tokenizer_identity,
        "native_tokenizer_evidence": evidence,
        "schedule": schedule,
        "automatic_scorer": SCORER_SPECIFICATION,
        "automatic_scorer_sha256": SCORER_SPECIFICATION_SHA256,
        "style_validity_interpretive_evidence": style_validity_binding(),
        "requests": rows,
        "privacy": "IGNORED_LOCAL_ONLY_DO_NOT_PUBLISH_OR_STAGE",
    }
    write_exclusive(FROZEN, plan)
    registration = {
        "schema_version": "personaslm_rpc_sfh_pilot_execution_registration_v1",
        "status": "PROSPECTIVELY_REGISTERED_TOKENIZED_NOT_EXECUTED",
        "scientific_level": "DEVELOPMENT_EXPLORATORY",
        "bindings": {
            "design_sha256": sha256(DESIGN),
            "material_receipt_sha256": sha256(MATERIAL_RECEIPT),
            "private_material_sha256": sha256(PRIVATE_MATERIAL),
            "authorization_sha256": sha256(AUTHORIZATION),
            "audit_sha256": sha256(AUDIT),
            "private_frozen_manifest_sha256": sha256(FROZEN),
            "source_hashes_sha256": value_sha256(plan["source_hashes"]),
        },
        "allocation": {"requests": MAX_ATTEMPTS, "blocks": 2,
                       "requests_per_block": BLOCK_SIZE, "retries": 0,
                       "outcome_contingent_stopping": False},
        "schedule": schedule,
        "model": authorization["model"], "runtime": RUNTIME,
        "tokenization": {
            "native_calls": MAX_ATTEMPTS,
            "minimum_input_tokens": min(row["input_tokens"] for row in rows),
            "maximum_input_tokens": max(row["input_tokens"] for row in rows),
            "maximum_recommended_input_tokens": MAX_INPUT_TOKENS,
            "all_input_plus_96_within_4096": True,
            "ordered_token_array_hashes_sha256": value_sha256(
                [row["input_token_ids_sha256"] for row in rows]),
        },
        "source_hashes": plan["source_hashes"],
        "automatic_scorer_sha256": SCORER_SPECIFICATION_SHA256,
        "style_validity_interpretive_evidence": style_validity_binding(),
        "semantic_endpoints": "HUMAN_REVIEW_PENDING_NOT_SCORED",
        "privacy": {"prompts_public": False, "token_arrays_public": False,
                    "participant_text_public": False, "row_results_public": False},
        "execution": {"server_launches": 0, "completion_attempts": 0,
                      "generations": 0},
    }
    write_exclusive(REGISTRATION, registration)
    return registration


def validate_plan(plan):
    _, _, material, schedule = validate_materials()
    authorization = validate_authorization()
    require(plan["schema_version"] == "personaslm_rpc_sfh_pilot_private_manifest_v1",
            "Manifest schema")
    require(plan["status"] == "FROZEN_PRIVATE_REGISTERED_NOT_EXECUTED", "Manifest status")
    for key, path in (("design_sha256", DESIGN),
                      ("material_receipt_sha256", MATERIAL_RECEIPT),
                      ("private_material_sha256", PRIVATE_MATERIAL),
                      ("authorization_sha256", AUTHORIZATION),
                      ("audit_sha256", AUDIT), ("budget_source_sha256", BUDGET_SOURCE)):
        require(plan[key] == sha256(path), "Manifest binding changed: " + key)
    require(plan["source_hashes"] == source_hashes(), "Registered source changed")
    require(plan["model"] == MODEL and plan["runtime"] == RUNTIME, "Model/runtime changed")
    require(plan["template_path"] == RUNTIME["chat_template_path"], "Template path changed")
    require(plan["schedule"] == schedule, "Schedule changed")
    require(plan["automatic_scorer"] == SCORER_SPECIFICATION and
            plan["automatic_scorer_sha256"] == SCORER_SPECIFICATION_SHA256,
            "Scorer changed")
    require(plan["style_validity_interpretive_evidence"] == style_validity_binding(),
            "Style-validity interpretive evidence changed")
    require(len(plan["requests"]) == MAX_ATTEMPTS, "Manifest request count")
    template = Path(RUNTIME["chat_template_path"]).read_text(encoding="utf-8")
    source_rows = material["requests"]
    for order, (row, source_row) in enumerate(zip(plan["requests"], source_rows)):
        require(row["order"] == order and row["request_id"] == source_row["request_id"],
                "Request order")
        require(row["messages"] == source_row["messages"] and
                row["prompt"] == s.render(template, source_row["messages"]), "Prompt changed")
        require(row["prompt_sha256"] == th(row["prompt"]) and
                row["input_token_ids_sha256"] == th(str(row["input_token_ids"])) and
                row["input_tokens"] == len(row["input_token_ids"]), "Token binding")
        require(row["input_tokens"] <= MAX_INPUT_TOKENS and
                row["input_tokens"] + MAX_NEW_TOKENS <= CONTEXT_TOKENS,
                "Context bound")
        require(row["request_sha256"] == value_sha256(
            {key: value for key, value in row.items() if key != "request_sha256"}),
            "Request hash")
    require(authorization["resources"]["maximum_generation_attempts"] == MAX_ATTEMPTS,
            "Authorization allocation")
    return {"requests": MAX_ATTEMPTS, "speakers": 8, "conditions": 8,
            "blocks": 2, "schedule": schedule["schedule"]}


def _budget():
    require(sha256(BUDGET_SOURCE) ==
            "0a2d4547a6501991d6b9f1855a4f4081ff885bba5e700f226757ace58d182a44",
            "Cumulative budget source changed")
    value = load(BUDGET_SOURCE)["cumulative_authorization_after"]
    expected = {"generations_limit": GENERATION_LIMIT,
                "generations_used": GENERATION_BASELINE,
                "inference_seconds_limit": INFERENCE_LIMIT,
                "inference_seconds_used": INFERENCE_BASELINE}
    require(value == expected and GENERATION_BASELINE + MAX_ATTEMPTS <= GENERATION_LIMIT and
            INFERENCE_BASELINE + INFERENCE_CEILING <= INFERENCE_LIMIT,
            "Cumulative budget baseline/remaining budget")
    return value


def preflight(check_headroom=True, require_unused=True):
    plan = load(FROZEN)
    checks = validate_plan(plan)
    registration = load(REGISTRATION)
    require(registration["status"] == "PROSPECTIVELY_REGISTERED_TOKENIZED_NOT_EXECUTED" and
            registration["bindings"]["private_frozen_manifest_sha256"] == sha256(FROZEN),
            "Registration binding")
    identity = b.file_preflight(cfg(plan))
    require(identity["status"] == "PASS" and
            identity["model"]["sha256"] == MODEL["model_sha256"] and
            identity["server"]["sha256"] == MODEL["backend_sha256"],
            "Model/backend identity")
    require(sha256(Path(RUNTIME["chat_template_path"])) == RUNTIME["chat_template_sha256"],
            "Chat template changed")
    require(_tokenizer_identity() == plan["tokenizer_identity"], "Tokenizer identity changed")
    budget = _budget()
    if require_unused:
        require(not CLAIM.exists() and not list(RUN_ROOT.glob("*")),
                "Existing allocation: zero retry and zero resume")
    memory = s.memory_observation(os.getpid())
    available = memory.get("system", {}).get("available_physical")
    require(type(available) is int, "Official available physical RAM unavailable")
    if check_headroom:
        require(available >= MIN_PREFLIGHT_RAM,
                "Less than registered 3 GiB available physical RAM")
    disk_free = shutil.disk_usage(".").free
    require(disk_free >= MIN_DISK, "Output disk reserve")
    return {
        "status": "PASS", "scientific_status": "READY_FOR_EXACT_DEVELOPMENT_EXECUTION",
        "checked_utc": b.utc_now(), "checks": checks,
        "bindings": {"private_frozen_manifest_sha256": sha256(FROZEN),
                     "registration_sha256": sha256(REGISTRATION),
                     "authorization_sha256": sha256(AUTHORIZATION),
                     "source_hashes_sha256": value_sha256(plan["source_hashes"]),
                     "server_command_sha256": th("\0".join(s.command(plan)))},
        "identity": {"model_sha256": identity["model"]["sha256"],
                     "model_bytes": identity["model"]["bytes"],
                     "backend_sha256": identity["server"]["sha256"],
                     "tokenizer_sha256": plan["tokenizer_identity"]["tokenizer_sha256"],
                     "chat_template_sha256": RUNTIME["chat_template_sha256"]},
        "resources": {"available_physical_ram_bytes": available,
                      "minimum_prelaunch_available_physical_ram_bytes": MIN_PREFLIGHT_RAM,
                      "free_output_disk_bytes": disk_free,
                      "minimum_free_output_disk_bytes": MIN_DISK,
                      "after_server_ready_minimum_bytes": MIN_READY_RAM,
                      "before_each_request_minimum_bytes": MIN_LIVE_RAM},
        "cumulative_baseline": budget,
        "operations": {"server_launches": 0, "completion_calls": 0,
                       "new_model_generations": 0},
    }


def preflight_receipt():
    try:
        return preflight()
    except BaseException as exc:
        try:
            memory = s.memory_observation(os.getpid())
        except BaseException as observation_error:
            memory = {"observation_error": {"type": type(observation_error).__name__,
                                             "message": str(observation_error)}}
        available = memory.get("system", {}).get("available_physical")
        return {
            "status": "FAIL", "scientific_status": "BLOCKED_RESOURCE_OR_INTEGRITY",
            "checked_utc": b.utc_now(),
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "resources": {"available_physical_ram_bytes": available,
                          "minimum_prelaunch_available_physical_ram_bytes": MIN_PREFLIGHT_RAM,
                          "available_ram_deficit_bytes": (max(0, MIN_PREFLIGHT_RAM - available)
                              if type(available) is int else None),
                          "free_output_disk_bytes": shutil.disk_usage(".").free,
                          "minimum_free_output_disk_bytes": MIN_DISK},
            "operations": {"server_launches": 0, "completion_calls": 0,
                           "new_model_generations": 0},
            "retry_without_material_resource_or_integrity_change": False,
        }


def payload(row):
    return {"prompt": row["input_token_ids"], "n_predict": MAX_NEW_TOKENS,
            "temperature": 0.0, "top_p": 1.0, "seed": 42,
            "cache_prompt": False, "stop": [], "ignore_eos": False,
            "return_tokens": True, "stream": False}


def assessability(boundary):
    span = boundary.get("first_span", {}).get("text", "")
    return bool(boundary.get("unit_identifiable") and span.strip() and
                boundary.get("status") != "TRUNCATED" and
                not any(label in span for label in EXPOSED_PROMPT_LABELS))


def result(row, response, latency):
    token_audit = b.validate_completion(response, row["input_token_ids"])
    normal = b.normalize_result(response)
    count = response.get("tokens_predicted")
    require(type(count) is int and 0 <= count <= MAX_NEW_TOKENS, "Generated token count")
    returned = (len(normal["generated_token_ids"])
                if normal["generated_token_ids"] is not None else None)
    require(returned is None or returned <= count, "Returned tokens exceed native count")
    if normal["stop_reason"] != "stop_sequence" and normal["token_ids_status"] == "returned":
        require(returned == count, "Token count mismatch")
    boundary = b.classify_response(normal["raw_response"], normal["raw_termination"],
                                   declared_stops=())
    span = boundary["first_span"]["text"]
    score = score_text(span, row["latent_case"], assessability(boundary))
    score.update(generated_tokens=count, latency_seconds=latency)
    return {
        "request_id": row["request_id"], "request_sha256": row["request_sha256"],
        "condition": row["condition"], "case_id": row["case_id"], "block": row["block"],
        **normal, "generated_tokens": count, "returned_token_count": returned,
        "latency_seconds": latency, "input_token_audit": token_audit,
        "response_status": boundary, "raw_text_sha256": th(normal["raw_response"]),
        "first_reply_sha256": th(span), "automatic_score": score,
        "automatic_scorer_sha256": SCORER_SPECIFICATION_SHA256,
        "semantic_endpoint_status": "HUMAN_REVIEW_PENDING_NOT_SCORED",
        "human_semantic_review": pending_human_review(),
    }


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


def _run_summary(status, plan, events, inference_seconds, failed_seconds,
                 wall_seconds, run_directory):
    attempted, raw, derived = inventory(plan, events)
    remaining = plan["requests"][len(attempted):]
    return {
        "status": status, "attempted": len(attempted),
        "responses_received": len(raw), "results": len(derived),
        "planned_slots": MAX_ATTEMPTS,
        "completed_by_block": {block: sum(
            row["request_id"] in derived for row in plan["requests"] if row["block"] == block)
                               for block in ("B1", "B2")},
        "native_tokenizer_calls": MAX_ATTEMPTS,
        "live_server_tokenizer_checks": sum(
            event["kind"] == "live_prompt_verified" for event in events),
        "completion_inference_seconds": inference_seconds,
        "failed_completion_seconds": failed_seconds,
        "batch_wall_seconds": wall_seconds,
        "run_directory": _relative(run_directory), "retries": 0, "hidden_warmups": 0,
        "outcome_contingent_stopping": False,
        "attempts_count_toward_cumulative_budget": len(attempted),
        "unattempted_suffix_count": len(remaining),
        "unattempted_suffix_request_hashes_sha256": value_sha256(
            [row["request_sha256"] for row in remaining]),
        "semantic_endpoint_status": "HUMAN_REVIEW_PENDING_NOT_SCORED",
    }


def run(preflight_path):
    preflight_path = Path(preflight_path)
    require(preflight_path.is_file() and preflight_path.parent.resolve() == OUT.resolve(),
            "Preflight must be an immutable public receipt in the study directory")
    fresh, stored, plan = preflight(), load(preflight_path), load(FROZEN)
    require(stored.get("status") == fresh.get("status") == "PASS", "Passing preflight required")
    for key in ("bindings", "identity", "cumulative_baseline"):
        require(stored[key] == fresh[key], "Preflight binding changed: " + key)
    with b.writer_lock(PRIVATE_ROOT):
        require(not CLAIM.exists() and not list(RUN_ROOT.glob("*")),
                "Existing allocation: zero retry and zero resume")
        claim = {"private_frozen_manifest_sha256": sha256(FROZEN),
                 "registration_sha256": sha256(REGISTRATION),
                 "authorization_sha256": sha256(AUTHORIZATION),
                 "preflight_sha256": sha256(preflight_path),
                 "maximum_attempts": MAX_ATTEMPTS, "retries": 0,
                 "hidden_warmups": 0, "resume_permitted": False}
        write_exclusive(CLAIM, claim)
        journal = b.RunJournal(RUN_ROOT, {
            "phase": "P1 real-speaker S/F/H developmental pilot v1",
            "scientific_level": "DEVELOPMENT_EXPLORATORY",
            "claim": claim, "frozen_manifest": plan,
            "authorization": load(AUTHORIZATION), "configuration": cfg(plan).as_dict(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
            "python": platform.python_version(), "platform": platform.platform()})
        for path, digest in plan["source_hashes"].items():
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
                ready = s.memory_observation(server.process.pid)
                journal.write("after_server_ready_memory_gate", ready)
                require(ready.get("system", {}).get("available_physical", 0) >= MIN_READY_RAM,
                        "Less than registered 1 GiB after server ready")
                client = b.LlamaClient(cfg(plan).endpoint, timeout=180, audit=journal.write)
                props = client.request("/props")
                binding = b.validate_server_properties(props, cfg(plan))
                require(RUNTIME["backend_build"].split("-", 1)[1] in binding["build_info"],
                        "Backend build")
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
                live_ready = s.memory_observation(server.process.pid)
                journal.write("post_live_tokenization_memory_gate", live_ready)
                require(live_ready.get("system", {}).get("available_physical", 0) >= MIN_READY_RAM,
                        "Less than registered 1 GiB before completion 1")
                journal.write("live_preflight_pass", {"prompts": MAX_ATTEMPTS,
                                                       "completed_inference": 0})
                for row in plan["requests"]:
                    if row["order"] in (0, BLOCK_SIZE):
                        journal.write("block_started", {"block": row["block"],
                                      "outcome_contingent": False})
                    remaining_wall = WALL_CEILING - (time.monotonic() - started)
                    remaining_inference = INFERENCE_CEILING - inference_seconds
                    require(remaining_wall > 0 and remaining_inference > 0,
                            "Registered time ceiling reached; preserve suffix")
                    server.assert_running()
                    observation = s.memory_observation(server.process.pid)
                    journal.write("before_request_memory_gate", observation)
                    require(observation.get("system", {}).get("available_physical", 0) >=
                            MIN_LIVE_RAM, "Registered 512 MiB live RAM gate reached")
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
                        journal.write("rpc_sfh_completion_failed", {
                            "request_id": active, "elapsed_seconds": elapsed})
                        raise
                    latency = time.monotonic() - tick
                    inference_seconds += latency
                    journal.write(RAW, {"request_id": active, "response": response,
                                        "latency_seconds": latency})
                    journal.write(DERIVED, result(row, response, latency))
                    active = None
                    if row["order"] in (BLOCK_SIZE - 1, MAX_ATTEMPTS - 1):
                        journal.write("block_completed", {"block": row["block"],
                                      "completed_requests": BLOCK_SIZE,
                                      "outcome_contingent": False})
                server.assert_running()
                after = preflight(check_headroom=False, require_unused=False)
                require(after["identity"] == fresh["identity"] and
                        after["bindings"] == fresh["bindings"], "Postflight identity changed")
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
        summary = _run_summary(status, plan, events, inference_seconds, failed_seconds,
                               time.monotonic() - started, journal.directory)
        attempted, raw, derived = inventory(plan, events)
        remaining = plan["requests"][len(attempted):]
        write_exclusive(REMAINING_SUFFIX, {
            "schema_version": "personaslm_rpc_sfh_remaining_suffix_v1",
            "status": "EMPTY_COMPLETE" if not remaining else "PRESERVED_NOT_AUTHORIZED_TO_RESUME",
            "attempted_request_ids": attempted,
            "attempted_unresolved_request_ids": [item for item in attempted if item not in raw],
            "raw_without_derived_request_ids": [item for item in raw if item not in derived],
            "remaining_unattempted": [{"order": row["order"],
                                       "request_id": row["request_id"],
                                       "request_sha256": row["request_sha256"],
                                       "block": row["block"]}
                                      for row in remaining],
            "resume_policy": (
                "This v1 controller hard-refuses a second run. Any separately authorized suffix "
                "controller must exclude every attempted request, including failed attempts."),
        })
        journal.finish(**summary)
        write_exclusive(journal.directory / "summary.json", summary)
        return summary


def _read_only_run():
    folders = [path for path in RUN_ROOT.glob("*") if path.is_dir()]
    require(len(folders) == 1, "Exactly one immutable run required")
    folder = folders[0]
    events = b.read_events(folder)
    summary = load(folder / "summary.json")
    require(events and events[-1]["kind"] == "run_finished" and
            events[-1]["data"] == summary, "Terminal summary")
    return folder, events, summary


def _factor_effect(values, factors):
    require(set(values) == set(CONDITIONS), "Complete condition vector required")
    return 2 * statistics.fmean(
        math.prod(1 if CONDITIONS[condition][factor] else -1
                  for factor in factors) * values[condition]
        for condition in CONDITIONS)


def _summary(values):
    if not values:
        return {"n": 0, "mean": None, "median": None, "minimum": None,
                "maximum": None}
    return {"n": len(values), "mean": statistics.fmean(values),
            "median": statistics.median(values), "minimum": min(values),
            "maximum": max(values)}


def _public_estimates(rows):
    condition_summary, effects, private_effects = {}, {}, {}
    for metric in AUTOMATIC_METRICS:
        condition_summary[metric] = {}
        for condition in CONDITIONS:
            available = [row["automatic_score"].get(metric) for row in rows
                         if row["condition"] == condition and
                         row["automatic_score"].get(metric) is not None]
            condition_summary[metric][condition] = {
                **_summary(available), "planned": 8,
                "missing": 8 - len(available)}
        by_case = defaultdict(dict)
        for row in rows:
            value = row["automatic_score"].get(metric)
            if value is not None:
                by_case[row["case_id"]][row["condition"]] = value
        effects[metric], private_effects[metric] = {}, {}
        for name, factors in FACTORS.items():
            speaker_values = [_factor_effect(values, factors)
                              for values in by_case.values()
                              if set(values) == set(CONDITIONS)]
            leave_one_out = [statistics.fmean(speaker_values[:index] +
                                               speaker_values[index + 1:])
                             for index in range(len(speaker_values))
                             if len(speaker_values) > 1]
            effects[metric][name] = {
                **_summary(speaker_values),
                "complete_speakers": len(speaker_values),
                "incomplete_speakers": 8 - len(speaker_values),
                "leave_one_speaker_out_mean_minimum": (
                    min(leave_one_out) if leave_one_out else None),
                "leave_one_speaker_out_mean_maximum": (
                    max(leave_one_out) if leave_one_out else None),
                "speaker_values_sha256": value_sha256(speaker_values),
            }
            private_effects[metric][name] = speaker_values
    return condition_summary, effects, private_effects


def analyze(write=True):
    plan = load(FROZEN)
    validate_plan(plan)
    folder, events, summary = _read_only_run()
    attempted, raw, derived = inventory(plan, events)
    successful_http = []
    for event in events:
        if event["kind"] != "http_response":
            continue
        data = event["data"]
        if data.get("route") == "/completion" and data.get("status") == 200:
            successful_http.append(json.loads(base64.b64decode(
                data["body_base64"]).decode("utf-8")))
    require(len(successful_http) == len(raw), "Completion HTTP/raw count mismatch")
    raw_in_attempt_order = [raw[request_id]["response"] for request_id in attempted
                            if request_id in raw]
    require(successful_http == raw_in_attempt_order, "Raw generation differs from HTTP body")
    recomputed = []
    rows_by_id = {row["request_id"]: row for row in plan["requests"]}
    for row in plan["requests"]:
        request_id = row["request_id"]
        if request_id not in raw:
            continue
        rebuilt = result(row, raw[request_id]["response"], raw[request_id]["latency_seconds"])
        require(request_id in derived and rebuilt == derived[request_id],
                "Derived row failed independent recomputation")
        recomputed.append(rebuilt)
    for request_id in attempted:
        if request_id in raw:
            continue
        row = rows_by_id[request_id]
        recomputed.append({"request_id": request_id,
                           "request_sha256": row["request_sha256"],
                           "condition": row["condition"], "case_id": row["case_id"],
                           "block": row["block"], "native_failure": True,
                           "automatic_score": native_failure_score(),
                           "automatic_scorer_sha256": SCORER_SPECIFICATION_SHA256,
                           "semantic_endpoint_status": "HUMAN_REVIEW_PENDING_NOT_SCORED",
                           "human_semantic_review": pending_human_review()})
    order_by_id = {row["request_id"]: row["order"] for row in plan["requests"]}
    recomputed.sort(key=lambda row: order_by_id[row["request_id"]])
    condition_summary, effects, private_effects = _public_estimates(recomputed)
    memory = [event["data"] for event in events if event["kind"] in (
        "memory_observation", "after_server_ready_memory_gate",
        "post_live_tokenization_memory_gate", "before_request_memory_gate")]
    available = [item.get("system", {}).get("available_physical") for item in memory]
    available = [value for value in available if type(value) is int]
    peak = max((item.get("process", {}).get("peak_working_set", 0)
                for item in memory), default=0)
    private = {
        "schema_version": "personaslm_rpc_sfh_pilot_private_analysis_v1",
        "run_directory": _relative(folder), "rows": recomputed,
        "speaker_factorial_contrasts": private_effects,
        "privacy": "IGNORED_LOCAL_ONLY_DO_NOT_PUBLISH_OR_STAGE",
    }
    public = {
        "schema_version": "personaslm_rpc_sfh_pilot_analysis_v1",
        "status": ("COMPLETE" if len(raw) == MAX_ATTEMPTS else
                   "COMPLETE_ALLOCATION_WITH_NATIVE_FAILURES"
                   if len(attempted) == MAX_ATTEMPTS else "PARTIAL"),
        "scientific_level": "DEVELOPMENT_EXPLORATORY_NOT_INDEPENDENT_VALIDATION",
        "execution": {"attempted": len(attempted), "responses_received": len(raw),
                      "derived_results": len(derived), "analyzed_slots": len(recomputed),
                      "native_failures": len(attempted) - len(raw),
                      "planned": MAX_ATTEMPTS,
                      "blocks": summary["completed_by_block"], "retries": 0,
                      "outcome_contingent_stopping": False},
        "bindings": {"private_frozen_manifest_sha256": sha256(FROZEN),
                     "registration_sha256": sha256(REGISTRATION),
                     "authorization_sha256": sha256(AUTHORIZATION),
                     "automatic_scorer_sha256": SCORER_SPECIFICATION_SHA256,
                     "journal_terminal_event_sha256": events[-1]["event_hash"]},
        "condition_summary": condition_summary,
        "speaker_paired_factorial_effects": effects,
        "effect_definition": SCORER_SPECIFICATION["factorial_effects"],
        "uncertainty": (
            "Speaker-level range and leave-one-speaker-out mean range are descriptive "
            "influence summaries, not confidence intervals; no confirmatory p-values."),
        "resources": {
            "completion_inference_seconds": summary["completion_inference_seconds"],
            "batch_wall_seconds": summary["batch_wall_seconds"],
            "peak_server_working_set_bytes": peak,
            "minimum_observed_available_physical_bytes": min(available) if available else None,
            "cumulative_after": {
                "generations_used": GENERATION_BASELINE + len(attempted),
                "generations_limit": GENERATION_LIMIT,
                "inference_seconds_used": INFERENCE_BASELINE +
                    summary["completion_inference_seconds"],
                "inference_seconds_limit": INFERENCE_LIMIT,
            },
        },
        "measurement_validity": {
            "automatic": list(AUTOMATIC_METRICS),
            "style_proxy": SCORER_SPECIFICATION["style_proxy"]["scope"],
            "reference_overlap": "lexical resemblance to one observed continuation; not correctness",
            "copying": "surface reuse diagnostic; copying is not Persona Fidelity",
            "human_review_pending": [
                "response relevance", "conversational coherence", "linguistic Persona Fidelity",
                "persona-statement consistency", "history consistency",
                "unsupported personal claims", "answer completeness"],
            "human_semantic_review": pending_human_review(),
            "style_validity_interpretive_evidence": style_validity_binding(),
        },
        "privacy": {"row_level_results_public": False,
                    "private_analysis_sha256": value_sha256(private),
                    "participant_text_public": False},
        "claim_boundary": (
            "Observed effects are exploratory incremental prompt-package effects for eight "
            "development speakers. They are not human-validated Persona Fidelity, semantic "
            "reliability, independent validation, or confirmatory population inference."),
    }
    if write:
        write_exclusive(PRIVATE_ANALYSIS, private)
        public["privacy"]["private_analysis_sha256"] = sha256(PRIVATE_ANALYSIS)
        write_exclusive(ANALYSIS, public)
        execution_audit = {
            "schema_version": "personaslm_rpc_sfh_pilot_execution_audit_v1",
            "status": ("PASS" if len(raw) == MAX_ATTEMPTS else
                       "COMPLETE_ALLOCATION_WITH_NATIVE_FAILURES"
                       if len(attempted) == MAX_ATTEMPTS else "PARTIAL"),
            "attempted_generations": len(attempted), "retries": 0,
            "raw_responses": len(raw), "recomputed_or_missingness_slots": len(recomputed),
            "journal_terminal_event_sha256": events[-1]["event_hash"],
            "private_analysis_sha256": sha256(PRIVATE_ANALYSIS),
            "analysis_sha256": sha256(ANALYSIS),
            "public_contains_row_level_results": False,
            "human_semantic_review": pending_human_review(),
        }
        write_exclusive(EXECUTION_AUDIT, execution_audit)
    return public, private


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=(
        "validate", "authorize", "register", "preflight", "run", "analyze"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preflight", type=Path)
    args = parser.parse_args(argv)
    if args.action == "validate":
        _, _, _, schedule = validate_materials()
        value = {"status": "PASS_OFFLINE_NO_TOKENIZATION_OR_INFERENCE", **schedule}
    elif args.action == "authorize":
        value = write_authorization()
    elif args.action == "register":
        value = register()
    elif args.action == "preflight":
        require(args.output is not None, "--output is required")
        value = preflight_receipt()
        write_exclusive(args.output, value)
    elif args.action == "run":
        require(args.preflight is not None, "--preflight is required")
        value = run(args.preflight)
    else:
        value, _ = analyze()
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
