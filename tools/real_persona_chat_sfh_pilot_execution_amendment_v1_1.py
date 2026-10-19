"""Apply and execute the RPC S/F/H v1.1 integrity-only schedule amendment.

The v1 registration and its failed preflight are immutable evidence.  This
controller reuses the exact frozen prompts and token arrays, but compares the
schedule through canonical JSON so tuple/list round-tripping cannot create a
false integrity failure.  ``amend`` and ``validate`` do not tokenize, launch a
server, or request a completion.
"""

from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time

import real_persona_chat_sfh_pilot_execution_v1 as base


OUT = base.OUT
AMENDMENT = OUT / "execution_integrity_amendment_v1_1.json"
AMENDMENT_AUDIT = OUT / "independent_integrity_amendment_audit_v1_1.json"
AUTHORIZATION_AMENDMENT_DRAFT = (
    OUT / "execution_authorization_amendment_draft_v1_1.json")
AUTHORIZATION_AMENDMENT = OUT / "execution_authorization_amendment_v1_1.json"
REGISTRATION = OUT / "prospective_execution_registration_v1_1.json"
PREFLIGHT = OUT / "preflight_v1_1.json"
CONTROLLER = Path(__file__)
TEST_SOURCE = Path("tests/test_real_persona_chat_sfh_pilot_execution_amendment_v1_1.py")

ORIGINAL_REGISTRATION = base.REGISTRATION
ORIGINAL_FROZEN = base.FROZEN
ORIGINAL_FAILED_PREFLIGHT = OUT / "preflight_v1.json"
FROZEN = base.PRIVATE_ROOT / "frozen_manifest_v1_1.json"
CLAIM = base.PRIVATE_ROOT / "claim_v1_1.json"
REMAINING_SUFFIX = base.PRIVATE_ROOT / "remaining_suffix_manifest_v1_1.json"
PRIVATE_ANALYSIS = base.PRIVATE_ROOT / "analysis_private_v1_1.json"
ANALYSIS = OUT / "analysis_v1_1.json"
EXECUTION_AUDIT = OUT / "execution_audit_v1_1.json"

HISTORICAL_HASHES = {
    "original_controller_sha256":
        "0a8143ba7a474eadfd303a109dcac5f438e44b14c0ab3e32f82c6f7d0e3d1110",
    "original_test_sha256":
        "7dcc7b8d0b949c43d2fcd6f0ff88fe4cc3baccd4a7c9ba8db2a5efdc45724409",
    "original_registration_sha256":
        "4b0bf22b261e8e1de700e7ac482039cf46f75ba62ff995b598143732a4d1936f",
    "original_frozen_manifest_sha256":
        "67db40afd7d7535cee6b2897b5fc9ba94b5a67a12bd276c6e39c4635407ac909",
    "failed_preflight_sha256":
        "792da63871693c540b19fba3ebf6c8c18b3e1c2d97cdf796af68ecc34ff8a327",
    "authorization_sha256":
        "26be44fe71f16791b2f4815093c8a5c7b2ab93f6092dd9b105300643e7a624fa",
    "original_independent_audit_sha256":
        "76449486daf6f7bc8d0913c1b8151ee4ce257b8df024c918b1385ca812ae5f22",
}


def _relative(path):
    return Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix()


def _historical_paths():
    return {
        "original_controller_sha256": Path(base.__file__),
        "original_test_sha256": base.TEST_SOURCE,
        "original_registration_sha256": ORIGINAL_REGISTRATION,
        "original_frozen_manifest_sha256": ORIGINAL_FROZEN,
        "failed_preflight_sha256": ORIGINAL_FAILED_PREFLIGHT,
        "authorization_sha256": base.AUTHORIZATION,
        "original_independent_audit_sha256": base.AUDIT,
    }


def validate_historical_evidence():
    for name, path in _historical_paths().items():
        base.require(base.sha256(path) == HISTORICAL_HASHES[name],
                     "Historical evidence changed: " + name)
    failed = base.load(ORIGINAL_FAILED_PREFLIGHT)
    base.require(failed.get("status") == "FAIL" and
                 failed.get("error", {}).get("message") == "Schedule changed" and
                 failed.get("operations") == {
                     "server_launches": 0, "completion_calls": 0,
                     "new_model_generations": 0},
                 "Historical failed preflight content changed")
    return failed


def compare_canonical_schedules(stored, computed):
    """Prove equality of values and sequence order across JSON/list and tuple models."""
    base.require(stored != computed,
                 "Expected historical container-type mismatch is absent")
    stored_bytes = base.canonical(stored)
    computed_bytes = base.canonical(computed)
    base.require(stored_bytes == computed_bytes,
                 "Schedule differs in values or sequence order after canonical JSON encoding")
    normalized = json.loads(computed_bytes)
    digest = hashlib.sha256(stored_bytes).hexdigest()
    return normalized, {
        "comparison": "CANONICAL_JSON_SEQUENCE_COMPARISON_ONLY",
        "stored_schedule_canonical_sha256": digest,
        "computed_schedule_canonical_sha256": hashlib.sha256(computed_bytes).hexdigest(),
        "canonical_bytes_equal": True,
        "values_and_sequence_order_equal": True,
        "stored_mask_container": "JSON_ARRAY",
        "computed_mask_container": "PYTHON_TUPLE",
    }


def schedule_integrity():
    stored = base.load(ORIGINAL_FROZEN)["schedule"]
    _, _, _, computed = base.validate_materials()
    _, integrity = compare_canonical_schedules(stored, computed)
    return integrity


def canonical_schedule():
    """Return the material schedule in its JSON data model (arrays, not tuples)."""
    stored = base.load(ORIGINAL_FROZEN)["schedule"]
    _, _, _, computed = base.validate_materials()
    normalized, _ = compare_canonical_schedules(stored, computed)
    return normalized


def validate_amendment():
    value = base.load(AMENDMENT)
    base.require(value.get("schema_version") ==
                 "personaslm_rpc_sfh_execution_integrity_amendment_v1_1" and
                 value.get("status") == "PROSPECTIVELY_FROZEN_INTEGRITY_ONLY",
                 "Integrity amendment status")
    base.require(value.get("historical_bindings") == HISTORICAL_HASHES,
                 "Integrity amendment historical bindings")
    base.require(value.get("repair", {}).get("permitted_change") ==
                 "CANONICAL_JSON_SEQUENCE_COMPARISON_ONLY",
                 "Integrity amendment scope")
    base.require(value.get("repair", {}).get("generation_configuration_changed") is False and
                 value.get("repair", {}).get("scientific_schedule_changed") is False and
                 value.get("repair", {}).get("retokenization_permitted") is False,
                 "Integrity amendment changes scientific execution")
    base.require(value.get("schedule_integrity") == schedule_integrity(),
                 "Integrity amendment schedule binding")
    base.require(value.get("implementation_bindings") == {
        "controller_path": _relative(CONTROLLER),
        "controller_sha256": base.sha256(CONTROLLER),
        "test_path": _relative(TEST_SOURCE),
        "test_sha256": base.sha256(TEST_SOURCE),
    }, "Integrity amendment implementation binding")
    return value


def amendment_audit_requirements():
    return {
        "amendment_sha256": base.sha256(AMENDMENT),
        "controller_sha256": base.sha256(CONTROLLER),
        "test_sha256": base.sha256(TEST_SOURCE),
        **HISTORICAL_HASHES,
        **schedule_integrity(),
    }


def validate_amendment_audit():
    audit = base.load(AMENDMENT_AUDIT)
    base.require(audit.get("status") == "PASS" and
                 audit.get("verdict") == "PASS_FOR_AMENDED_EXECUTION",
                 "Integrity-amendment audit did not pass")
    base.require(audit.get("auditor_provenance") ==
                 "AI independent code/scientific audit; not human review",
                 "Integrity-amendment audit provenance")
    base.require(audit.get("bindings") == amendment_audit_requirements(),
                 "Integrity-amendment audit binding")
    base.require(audit.get("blocking_findings") == [] and
                 audit.get("blocking_finding_count") == 0,
                 "Integrity-amendment audit blockers")
    checks = audit.get("checks")
    base.require(isinstance(checks, dict) and checks and
                 all(value is True for value in checks.values()),
                 "Integrity-amendment audit checks")
    return audit


def authorization_amendment_requirements():
    """Exact post-audit authority; the v1 authorization remains the parent authority."""
    validate_historical_evidence()
    validate_amendment()
    validate_amendment_audit()
    parent = base.validate_authorization()
    return {
        "schema_version": (
            "personaslm_rpc_sfh_execution_authorization_amendment_v1_1"),
        "status": "AUTHORIZED_FOR_V1_1_INTEGRITY_REPAIR_EXECUTION",
        "researcher": parent["researcher"],
        "authority": parent["authority"],
        "scientific_level": parent["scientific_level"],
        "parent_authorization": {
            "path": _relative(base.AUTHORIZATION),
            "sha256": base.sha256(base.AUTHORIZATION),
            "status": parent["status"],
        },
        "bindings": {
            **amendment_audit_requirements(),
            "independent_integrity_amendment_audit_sha256":
                base.sha256(AMENDMENT_AUDIT),
        },
        "permitted_change": "CANONICAL_JSON_SEQUENCE_COMPARISON_ONLY",
        "scientific_schedule_changed": False,
        "generation_configuration_changed": False,
        "frozen_prompts_changed": False,
        "frozen_token_arrays_changed": False,
        "native_retokenization_permitted": False,
        "fresh_preflight_required": _relative(PREFLIGHT),
        "resources": parent["resources"],
        "prohibitions": parent["prohibitions"],
    }


def write_authorization_amendment():
    expected = authorization_amendment_requirements()
    _write_once(AUTHORIZATION_AMENDMENT, expected)
    return expected


def validate_authorization_amendment():
    value = base.load(AUTHORIZATION_AMENDMENT)
    base.require(value == authorization_amendment_requirements(),
                 "Execution authorization amendment changed")
    return value


def amendment_binding():
    validate_historical_evidence()
    validate_amendment()
    validate_amendment_audit()
    validate_authorization_amendment()
    return {
        "amendment_path": _relative(AMENDMENT),
        "amendment_sha256": base.sha256(AMENDMENT),
        "amendment_audit_path": _relative(AMENDMENT_AUDIT),
        "amendment_audit_sha256": base.sha256(AMENDMENT_AUDIT),
        "parent_authorization_path": _relative(base.AUTHORIZATION),
        "parent_authorization_sha256": base.sha256(base.AUTHORIZATION),
        "authorization_amendment_path": _relative(AUTHORIZATION_AMENDMENT),
        "authorization_amendment_sha256": base.sha256(AUTHORIZATION_AMENDMENT),
        "controller_path": _relative(CONTROLLER),
        "controller_sha256": base.sha256(CONTROLLER),
        "test_path": _relative(TEST_SOURCE),
        "test_sha256": base.sha256(TEST_SOURCE),
        "failed_preflight_path": _relative(ORIGINAL_FAILED_PREFLIGHT),
        "failed_preflight_sha256": base.sha256(ORIGINAL_FAILED_PREFLIGHT),
        "schedule_integrity": schedule_integrity(),
        "historical_bindings": HISTORICAL_HASHES,
    }


def source_hashes():
    result = dict(base.load(ORIGINAL_FROZEN)["source_hashes"])
    for path in (ORIGINAL_FROZEN, ORIGINAL_REGISTRATION, ORIGINAL_FAILED_PREFLIGHT,
                 AMENDMENT, AMENDMENT_AUDIT, AUTHORIZATION_AMENDMENT,
                 CONTROLLER, TEST_SOURCE):
        result[_relative(path)] = base.sha256(path)
    return dict(sorted(result.items()))


def build_amended_plan():
    validate_historical_evidence()
    binding = amendment_binding()
    original = base.load(ORIGINAL_FROZEN)
    plan = copy.deepcopy(original)
    plan["schema_version"] = "personaslm_rpc_sfh_pilot_private_manifest_v1_1"
    plan["status"] = "FROZEN_PRIVATE_REGISTERED_NOT_EXECUTED_V1_1_INTEGRITY_ONLY"
    plan["schedule"] = canonical_schedule()
    plan["source_hashes"] = source_hashes()
    plan["integrity_amendment"] = binding
    plan["authorization_amendment_sha256"] = base.sha256(AUTHORIZATION_AMENDMENT)
    plan["schedule_integrity"] = schedule_integrity()
    base.require(plan["requests"] == original["requests"] and
                 plan["native_tokenizer_evidence"] == original["native_tokenizer_evidence"],
                 "Frozen prompts, token arrays, or tokenizer evidence changed")
    return plan


def build_amended_registration(plan):
    registration = copy.deepcopy(base.load(ORIGINAL_REGISTRATION))
    registration["schema_version"] = (
        "personaslm_rpc_sfh_pilot_execution_registration_v1_1")
    registration["bindings"]["private_frozen_manifest_sha256"] = base.value_sha256(plan)
    registration["bindings"]["source_hashes_sha256"] = base.value_sha256(
        plan["source_hashes"])
    registration["bindings"]["authorization_amendment_sha256"] = (
        base.sha256(AUTHORIZATION_AMENDMENT))
    registration["schedule"] = plan["schedule"]
    registration["source_hashes"] = plan["source_hashes"]
    registration["integrity_amendment"] = plan["integrity_amendment"]
    registration["schedule_integrity"] = plan["schedule_integrity"]
    registration["execution"] = {
        "server_launches": 0, "completion_attempts": 0, "generations": 0,
        "native_tokenizer_calls_added_by_amendment": 0,
    }
    return registration


def _write_once(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(base.canonical(value))


def amend():
    base.require(not FROZEN.exists() and not REGISTRATION.exists(),
                 "v1.1 amendment artifacts already exist")
    base.require(not base.CLAIM.exists() and not CLAIM.exists() and
                 not list(base.RUN_ROOT.glob("*")),
                 "Execution evidence exists; amendment is no longer prospective")
    plan = build_amended_plan()
    registration = build_amended_registration(plan)
    _write_once(FROZEN, plan)
    base.require(base.sha256(FROZEN) ==
                 registration["bindings"]["private_frozen_manifest_sha256"],
                 "Amended private manifest write")
    _write_once(REGISTRATION, registration)
    return {
        "status": "AMENDED_WITHOUT_RETOKENIZATION_OR_INFERENCE",
        "private_frozen_manifest_sha256": base.sha256(FROZEN),
        "registration_sha256": base.sha256(REGISTRATION),
        "integrity_amendment": amendment_binding(),
        "operations": {"native_tokenizer_calls": 0, "server_launches": 0,
                       "completion_calls": 0, "new_model_generations": 0},
    }


def validate_plan(plan):
    expected = build_amended_plan()
    base.require(plan == expected, "Amended private manifest changed")
    base.require(base.value_sha256(plan["schedule"]) ==
                 base.value_sha256(canonical_schedule()),
                 "Canonical schedule changed")
    base.require(plan["schedule_integrity"] == schedule_integrity(),
                 "Canonical schedule integrity changed")
    registration = base.load(REGISTRATION)
    base.require(registration == build_amended_registration(plan),
                 "Amended public registration changed")
    base.require(registration["bindings"]["private_frozen_manifest_sha256"] ==
                 base.sha256(FROZEN), "Amended registration/manifest binding")
    base.validate_authorization()
    validate_authorization_amendment()
    return {"requests": base.MAX_ATTEMPTS, "speakers": 8, "conditions": 8,
            "blocks": 2, "schedule": plan["schedule"]["schedule"],
            "schedule_comparison": "CANONICAL_JSON_SEQUENCE_COMPARISON"}


def validate():
    plan = base.load(FROZEN)
    checks = validate_plan(plan)
    return {"status": "PASS_OFFLINE_NO_TOKENIZATION_SERVER_OR_INFERENCE",
            "checks": checks, "integrity_amendment": amendment_binding()}


def preflight(check_headroom=True, require_unused=True):
    plan = base.load(FROZEN)
    checks = validate_plan(plan)
    identity = base.b.file_preflight(base.cfg(plan))
    base.require(identity["status"] == "PASS" and
                 identity["model"]["sha256"] == base.MODEL["model_sha256"] and
                 identity["server"]["sha256"] == base.MODEL["backend_sha256"],
                 "Model/backend identity")
    base.require(base.sha256(Path(base.RUNTIME["chat_template_path"])) ==
                 base.RUNTIME["chat_template_sha256"], "Chat template changed")
    base.require(base._tokenizer_identity() == plan["tokenizer_identity"],
                 "Tokenizer identity changed")
    budget = base._budget()
    if require_unused:
        base.require(not base.CLAIM.exists() and not CLAIM.exists() and
                     not list(base.RUN_ROOT.glob("*")),
                     "Existing allocation: zero retry and zero resume")
    memory = base.s.memory_observation(os.getpid())
    available = memory.get("system", {}).get("available_physical")
    base.require(type(available) is int, "Official available physical RAM unavailable")
    if check_headroom:
        base.require(available >= base.MIN_PREFLIGHT_RAM,
                     "Less than registered 3 GiB available physical RAM")
    disk_free = shutil.disk_usage(".").free
    base.require(disk_free >= base.MIN_DISK, "Output disk reserve")
    return {
        "status": "PASS", "scientific_status": "READY_FOR_EXACT_DEVELOPMENT_EXECUTION",
        "checked_utc": base.b.utc_now(), "checks": checks,
        "integrity_amendment": amendment_binding(),
        "bindings": {
            "private_frozen_manifest_sha256": base.sha256(FROZEN),
            "registration_sha256": base.sha256(REGISTRATION),
            "authorization_sha256": base.sha256(base.AUTHORIZATION),
            "authorization_amendment_sha256": base.sha256(AUTHORIZATION_AMENDMENT),
            "integrity_amendment_sha256": base.sha256(AMENDMENT),
            "integrity_amendment_audit_sha256": base.sha256(AMENDMENT_AUDIT),
            "failed_preflight_sha256": base.sha256(ORIGINAL_FAILED_PREFLIGHT),
            **schedule_integrity(),
            "source_hashes_sha256": base.value_sha256(plan["source_hashes"]),
            "server_command_sha256": base.th("\0".join(base.s.command(plan))),
        },
        "identity": {
            "model_sha256": identity["model"]["sha256"],
            "model_bytes": identity["model"]["bytes"],
            "backend_sha256": identity["server"]["sha256"],
            "tokenizer_sha256": plan["tokenizer_identity"]["tokenizer_sha256"],
            "chat_template_sha256": base.RUNTIME["chat_template_sha256"],
        },
        "resources": {
            "available_physical_ram_bytes": available,
            "minimum_prelaunch_available_physical_ram_bytes": base.MIN_PREFLIGHT_RAM,
            "free_output_disk_bytes": disk_free,
            "minimum_free_output_disk_bytes": base.MIN_DISK,
            "after_server_ready_minimum_bytes": base.MIN_READY_RAM,
            "before_each_request_minimum_bytes": base.MIN_LIVE_RAM,
        },
        "cumulative_baseline": budget,
        "operations": {"server_launches": 0, "completion_calls": 0,
                       "new_model_generations": 0,
                       "native_tokenizer_calls_added_by_amendment": 0},
    }


def preflight_receipt():
    try:
        return preflight()
    except BaseException as exc:
        try:
            memory = base.s.memory_observation(os.getpid())
        except BaseException as observation_error:
            memory = {"observation_error": {
                "type": type(observation_error).__name__, "message": str(observation_error)}}
        available = memory.get("system", {}).get("available_physical")
        return {
            "status": "FAIL", "scientific_status": "BLOCKED_RESOURCE_OR_INTEGRITY",
            "checked_utc": base.b.utc_now(),
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "integrity_amendment": {
                "path": _relative(AMENDMENT),
                "sha256": base.sha256(AMENDMENT) if AMENDMENT.is_file() else None,
                "failed_preflight_sha256": HISTORICAL_HASHES["failed_preflight_sha256"],
            },
            "resources": {
                "available_physical_ram_bytes": available,
                "minimum_prelaunch_available_physical_ram_bytes": base.MIN_PREFLIGHT_RAM,
                "available_ram_deficit_bytes": (
                    max(0, base.MIN_PREFLIGHT_RAM - available)
                    if type(available) is int else None),
                "free_output_disk_bytes": shutil.disk_usage(".").free,
                "minimum_free_output_disk_bytes": base.MIN_DISK,
            },
            "operations": {"server_launches": 0, "completion_calls": 0,
                           "new_model_generations": 0,
                           "native_tokenizer_calls_added_by_amendment": 0},
            "retry_without_material_resource_or_integrity_change": False,
        }


def execution_claim(preflight_path):
    return {
        "private_frozen_manifest_sha256": base.sha256(FROZEN),
        "registration_sha256": base.sha256(REGISTRATION),
        "authorization_sha256": base.sha256(base.AUTHORIZATION),
        "authorization_amendment_path": _relative(AUTHORIZATION_AMENDMENT),
        "authorization_amendment_sha256": base.sha256(AUTHORIZATION_AMENDMENT),
        "preflight_sha256": base.sha256(preflight_path),
        "integrity_amendment_path": _relative(AMENDMENT),
        "integrity_amendment_sha256": base.sha256(AMENDMENT),
        "integrity_amendment_audit_sha256": base.sha256(AMENDMENT_AUDIT),
        "amendment_controller_sha256": base.sha256(CONTROLLER),
        "amendment_test_sha256": base.sha256(TEST_SOURCE),
        "failed_preflight_sha256": base.sha256(ORIGINAL_FAILED_PREFLIGHT),
        "source_hashes_sha256": base.value_sha256(
            base.load(FROZEN)["source_hashes"]),
        "schedule_integrity": schedule_integrity(),
        "maximum_attempts": base.MAX_ATTEMPTS, "retries": 0,
        "hidden_warmups": 0, "resume_permitted": False,
    }


def first_integrity_event(claim):
    """First journal event: all effective integrity bindings precede model startup."""
    return {
        "execution_integrity_bindings": amendment_binding(),
        "claim": claim,
        "source_hashes_sha256": claim["source_hashes_sha256"],
        "schedule_integrity": schedule_integrity(),
        "scientific_schedule_changed": False,
        "retokenization_calls_added": 0,
    }


def _snapshot_bound_files(journal, plan):
    for path, digest in plan["source_hashes"].items():
        destination = journal.directory / "source_snapshot" / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as handle:
            handle.write(Path(path).read_bytes())
        base.require(base.sha256(destination) == digest, "Source snapshot changed")
    # The effective hash manifest and public registration are claim-bound, not self-hashed.
    for label, path in (("effective_frozen_manifest", FROZEN),
                        ("effective_registration", REGISTRATION)):
        destination = journal.directory / "execution_bindings" / f"{label}.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as handle:
            handle.write(path.read_bytes())
        base.require(base.sha256(destination) == base.sha256(path),
                     "Execution binding snapshot changed")


def run(preflight_path):
    preflight_path = Path(preflight_path)
    base.require(preflight_path.resolve() == PREFLIGHT.resolve() and preflight_path.is_file(),
                 "The immutable v1.1 public preflight receipt is required")
    fresh, stored, plan = preflight(), base.load(preflight_path), base.load(FROZEN)
    base.require(stored.get("status") == fresh.get("status") == "PASS",
                 "Passing preflight required")
    for key in ("bindings", "identity", "cumulative_baseline", "integrity_amendment"):
        base.require(stored[key] == fresh[key], "Preflight binding changed: " + key)
    with base.b.writer_lock(base.PRIVATE_ROOT):
        base.require(not base.CLAIM.exists() and not CLAIM.exists() and
                     not list(base.RUN_ROOT.glob("*")),
                     "Existing allocation: zero retry and zero resume")
        claim = execution_claim(preflight_path)
        _write_once(CLAIM, claim)
        journal = base.b.RunJournal(base.RUN_ROOT, {
            "phase": "P1 real-speaker S/F/H developmental pilot v1.1 integrity amendment",
            "scientific_level": "DEVELOPMENT_EXPLORATORY",
            "integrity_amendment": amendment_binding(),
            "claim": claim, "frozen_manifest": plan,
            "authorization": base.load(base.AUTHORIZATION),
            "authorization_amendment": base.load(AUTHORIZATION_AMENDMENT),
            "schedule_integrity": schedule_integrity(),
            "configuration": base.cfg(plan).as_dict(),
            "git_head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True).strip(),
            "git_status": subprocess.check_output(
                ["git", "status", "--short"], text=True),
            "python": platform.python_version(), "platform": platform.platform(),
        })
        _snapshot_bound_files(journal, plan)
        started, active, status = time.monotonic(), None, "BLOCKED"
        inference_seconds = failed_seconds = 0.0
        try:
            journal.write("integrity_amendment_applied_before_inference",
                          first_integrity_event(claim))
            journal.write("preflight", fresh)
            with base.s.Server(plan, journal) as server:
                ready = base.s.memory_observation(server.process.pid)
                journal.write("after_server_ready_memory_gate", ready)
                base.require(ready.get("system", {}).get("available_physical", 0) >=
                             base.MIN_READY_RAM,
                             "Less than registered 1 GiB after server ready")
                client = base.b.LlamaClient(base.cfg(plan).endpoint, timeout=180,
                                            audit=journal.write)
                props = client.request("/props")
                binding = base.b.validate_server_properties(props, base.cfg(plan))
                base.require(base.RUNTIME["backend_build"].split("-", 1)[1] in
                             binding["build_info"], "Backend build")
                journal.write("effective_server_defaults", {
                    "props": props, "validation": binding})
                for row in plan["requests"]:
                    tokens = client.request("/tokenize", {
                        "content": row["prompt"], "add_special": True,
                        "parse_special": True, "with_pieces": False})["tokens"]
                    base.require(tokens == row["input_token_ids"], "Live tokenizer changed")
                    journal.write("live_prompt_verified", {
                        "request_id": row["request_id"],
                        "token_ids_sha256": base.th(str(tokens))})
                live_ready = base.s.memory_observation(server.process.pid)
                journal.write("post_live_tokenization_memory_gate", live_ready)
                base.require(live_ready.get("system", {}).get("available_physical", 0) >=
                             base.MIN_READY_RAM,
                             "Less than registered 1 GiB before completion 1")
                journal.write("live_preflight_pass", {
                    "prompts": base.MAX_ATTEMPTS, "completed_inference": 0})
                for row in plan["requests"]:
                    if row["order"] in (0, base.BLOCK_SIZE):
                        journal.write("block_started", {
                            "block": row["block"], "outcome_contingent": False})
                    remaining_wall = base.WALL_CEILING - (time.monotonic() - started)
                    remaining_inference = base.INFERENCE_CEILING - inference_seconds
                    base.require(remaining_wall > 0 and remaining_inference > 0,
                                 "Registered time ceiling reached; preserve suffix")
                    server.assert_running()
                    observation = base.s.memory_observation(server.process.pid)
                    journal.write("before_request_memory_gate", observation)
                    base.require(observation.get("system", {}).get(
                        "available_physical", 0) >= base.MIN_LIVE_RAM,
                        "Registered 512 MiB live RAM gate reached")
                    client.timeout = min(180, remaining_wall, remaining_inference)
                    active = row["request_id"]
                    journal.write(base.STARTED, row)
                    tick = time.monotonic()
                    try:
                        response = client.request("/completion", base.payload(row))
                    except BaseException:
                        elapsed = time.monotonic() - tick
                        inference_seconds += elapsed
                        failed_seconds += elapsed
                        journal.write("rpc_sfh_completion_failed", {
                            "request_id": active, "elapsed_seconds": elapsed})
                        raise
                    latency = time.monotonic() - tick
                    inference_seconds += latency
                    journal.write(base.RAW, {"request_id": active, "response": response,
                                             "latency_seconds": latency})
                    journal.write(base.DERIVED, base.result(row, response, latency))
                    active = None
                    if row["order"] in (base.BLOCK_SIZE - 1, base.MAX_ATTEMPTS - 1):
                        journal.write("block_completed", {
                            "block": row["block"], "completed_requests": base.BLOCK_SIZE,
                            "outcome_contingent": False})
                server.assert_running()
                after = preflight(check_headroom=False, require_unused=False)
                base.require(after["identity"] == fresh["identity"] and
                             after["bindings"] == fresh["bindings"],
                             "Postflight identity changed")
                journal.write("postflight", after)
            status = "PASS"
        except BaseException as exc:
            status = "PARTIAL" if active or inference_seconds else "BLOCKED"
            journal.write("failure", {"type": type(exc).__name__, "message": str(exc),
                                      "request_id": active})
        events = base.b.read_events(journal.directory)
        _, _, derived = base.inventory(plan, events)
        if status != "PASS" and len(derived) == base.MAX_ATTEMPTS:
            status = "COMPLETE_DATA_POSTFLIGHT_FAILED"
        summary = base._run_summary(
            status, plan, events, inference_seconds, failed_seconds,
            time.monotonic() - started, journal.directory)
        attempted, raw, derived = base.inventory(plan, events)
        remaining = plan["requests"][len(attempted):]
        _write_once(REMAINING_SUFFIX, {
            "schema_version": "personaslm_rpc_sfh_remaining_suffix_v1_1",
            "status": ("EMPTY_COMPLETE" if not remaining else
                       "PRESERVED_NOT_AUTHORIZED_TO_RESUME"),
            "attempted_request_ids": attempted,
            "attempted_unresolved_request_ids": [item for item in attempted if item not in raw],
            "raw_without_derived_request_ids": [item for item in raw if item not in derived],
            "remaining_unattempted": [{
                "order": row["order"], "request_id": row["request_id"],
                "request_sha256": row["request_sha256"], "block": row["block"]}
                for row in remaining],
            "resume_policy": (
                "This v1.1 amendment controller hard-refuses a second run. Any separately "
                "authorized suffix controller must exclude every attempted request, including "
                "failed attempts."),
            "integrity_amendment": amendment_binding(),
        })
        journal.finish(**summary)
        base.write_exclusive(journal.directory / "summary.json", summary)
        return summary


@contextmanager
def _analysis_paths():
    replacements = {
        "FROZEN": FROZEN, "REGISTRATION": REGISTRATION, "CLAIM": CLAIM,
        "REMAINING_SUFFIX": REMAINING_SUFFIX, "PRIVATE_ANALYSIS": PRIVATE_ANALYSIS,
        "ANALYSIS": ANALYSIS, "EXECUTION_AUDIT": EXECUTION_AUDIT,
        "validate_plan": validate_plan,
    }
    original = {name: getattr(base, name) for name in replacements}
    try:
        for name, value in replacements.items():
            setattr(base, name, value)
        yield
    finally:
        for name, value in original.items():
            setattr(base, name, value)


def analyze():
    # Explicit rebinding keeps the frozen v1 analysis implementation/scorer unchanged.
    with _analysis_paths():
        return base.analyze()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=(
        "authorize", "amend", "validate", "preflight", "run", "analyze"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preflight", type=Path)
    args = parser.parse_args(argv)
    if args.action == "authorize":
        value = write_authorization_amendment()
    elif args.action == "amend":
        value = amend()
    elif args.action == "validate":
        value = validate()
    elif args.action == "preflight":
        base.require(args.output is not None and args.output.resolve() == PREFLIGHT.resolve(),
                     "--output must be the registered v1.1 preflight path")
        value = preflight_receipt()
        _write_once(args.output, value)
    elif args.action == "run":
        base.require(args.preflight is not None, "--preflight is required")
        value = run(args.preflight)
    else:
        value, _ = analyze()
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
