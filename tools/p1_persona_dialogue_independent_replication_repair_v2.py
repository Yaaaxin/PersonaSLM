"""Versioned preflight adapter for the frozen independent replication.

This wrapper preserves the registered v1 runner and fixes only the nested
cumulative-budget lookup documented by prospective repair amendment v6.
It performs no registration or tokenization and cannot create a second
generation allocation.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import shutil

import p1_persona_dialogue_independent_replication as original


BASELINE = original.BASELINE
FROZEN = original.FROZEN
ORIGINAL_AUTHORIZATION = original.AUTHORIZATION
FAILED_PREFLIGHT_V1 = original.PREFLIGHT
REPAIR_AMENDMENT = original.DESIGN.with_name(
    "prospective_preflight_repair_amendment_v6.json")
REPAIR_AUTHORIZATION = original.DESIGN.with_name(
    "execution_repair_authorization_v2.json")
PREFLIGHT_V2 = original.DESIGN.with_name("preflight_v2.json")
REPAIR_TEST_SOURCE = Path(
    "tests/test_p1_persona_dialogue_independent_replication_repair_v2.py")

ORIGINAL_RUNNER_SHA = "0f1d52c64845e70e9abc33782847c5a46c86dd47d205df52df85aed24993edec"
ORIGINAL_TEST_SHA = "7a68fa58774ab0b9c89371ca6867a9c759ddf5c1da2bb3a7663f8491b853f1f3"
FROZEN_SHA = "55673bc8f9a802fe22f9d4234cd0bea32e806a4d9f3386cd0e483fa1cc716485"
ORIGINAL_AUTHORIZATION_SHA = \
    "79997cd2e021c92cfa77192311677f0b429ef34c496892d6875c068b02df2c62"
FAILED_PREFLIGHT_V1_SHA = \
    "2de0d11f9d7d9ec2062fd39c4df0cb690a1ee1dfd5fc277f873be79a7160c031"
REPAIR_AMENDMENT_SHA = \
    "f95ae3030deac01863ef64409d30c54a2eb904d428ec8e108113df37ca6749b1"


load, sha256, require = original.load, original.sha256, original.require


def _relative(path):
    return Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix()


def cumulative_baseline():
    """Read the unchanged authoritative baseline through its actual schema."""
    document = load(BASELINE)
    require("analysis" in document and
            "cumulative_authorization_after" in document["analysis"],
            "Authoritative cumulative baseline schema changed")
    baseline = document["analysis"]["cumulative_authorization_after"]
    expected = {"generations_limit": 1200, "generations_used": 106,
                "inference_seconds_limit": 72000.0,
                "inference_seconds_used": 668.7530845000028}
    require(baseline == expected, "Authoritative cumulative baseline changed")
    return copy.deepcopy(baseline)


def validate_repair_evidence():
    """Verify that every artifact repaired around remains byte-identical."""
    bindings = {
        original.Path(original.__file__): ORIGINAL_RUNNER_SHA,
        original.TEST_SOURCE: ORIGINAL_TEST_SHA,
        FROZEN: FROZEN_SHA,
        ORIGINAL_AUTHORIZATION: ORIGINAL_AUTHORIZATION_SHA,
        FAILED_PREFLIGHT_V1: FAILED_PREFLIGHT_V1_SHA,
        REPAIR_AMENDMENT: REPAIR_AMENDMENT_SHA,
        BASELINE: original.BASELINE_SHA,
    }
    for path, expected in bindings.items():
        require(Path(path).is_file() and sha256(Path(path)) == expected,
                "Preserved repair evidence changed: " + Path(path).as_posix())
    failed = load(FAILED_PREFLIGHT_V1)
    require(failed["status"] == "FAIL" and
            failed["error"] == {"type": "KeyError",
                                 "message": "'cumulative_authorization_after'"} and
            failed["model_server_launches"] == 0 and
            failed["completion_calls"] == 0 and
            failed["new_model_generations"] == 0,
            "Failed preflight-v1 evidence changed")
    amendment = load(REPAIR_AMENDMENT)
    require(amendment["status"] ==
            "FROZEN_PROSPECTIVE_REPAIR_NOT_YET_AUTHORIZED_NOT_EXECUTED" and
            amendment["observed_failure"]["sha256"] == FAILED_PREFLIGHT_V1_SHA and
            amendment["preserved_evidence"]["original_runner"]["sha256"] ==
            ORIGINAL_RUNNER_SHA and
            amendment["preserved_evidence"]["original_test"]["sha256"] ==
            ORIGINAL_TEST_SHA and
            amendment["preserved_evidence"]["frozen_manifest"]["sha256"] ==
            FROZEN_SHA and
            amendment["preserved_evidence"]["original_execution_authorization"][
                "sha256"] == ORIGINAL_AUTHORIZATION_SHA and
            amendment["root_cause"]["baseline_sha256"] == original.BASELINE_SHA and
            amendment["repair_policy"]["maximum_new_tokenizer_calls"] == 0 and
            amendment["repair_policy"]["maximum_generation_attempts"] ==
            original.MAX_ATTEMPTS and amendment["repair_policy"]["retries"] == 0,
            "Repair amendment changed")
    cumulative_baseline()
    return True


def repair_source_hashes(include_repair_authorization=False):
    """Extend the registered sources without mutating the v1 manifest."""
    validate_repair_evidence()
    paths = {
        **original.source_hashes(),
        _relative(FROZEN): sha256(FROZEN),
        _relative(ORIGINAL_AUTHORIZATION): sha256(ORIGINAL_AUTHORIZATION),
        _relative(FAILED_PREFLIGHT_V1): sha256(FAILED_PREFLIGHT_V1),
        _relative(REPAIR_AMENDMENT): sha256(REPAIR_AMENDMENT),
        _relative(Path(__file__)): sha256(Path(__file__)),
        _relative(REPAIR_TEST_SOURCE): sha256(REPAIR_TEST_SOURCE),
    }
    if include_repair_authorization:
        require(REPAIR_AUTHORIZATION.is_file(), "Repair authorization missing")
        paths[_relative(REPAIR_AUTHORIZATION)] = sha256(REPAIR_AUTHORIZATION)
    return dict(sorted(paths.items()))


def repair_authorization_requirements():
    validate_repair_evidence()
    return {
        "schema_version":
            "personaslm_independent_replication_preflight_repair_authorization_v2",
        "status": "AUTHORIZED_VERSIONED_PREFLIGHT_REPAIR_BEFORE_MODEL_EXECUTION",
        "authorization_path": REPAIR_AUTHORIZATION.as_posix(),
        "repair_amendment": {"path": REPAIR_AMENDMENT.as_posix(),
                             "sha256": REPAIR_AMENDMENT_SHA},
        "preserved_frozen_manifest": {"path": FROZEN.as_posix(),
                                      "sha256": FROZEN_SHA},
        "preserved_execution_authorization": {
            "path": ORIGINAL_AUTHORIZATION.as_posix(),
            "sha256": ORIGINAL_AUTHORIZATION_SHA},
        "failed_preflight_v1": {"path": FAILED_PREFLIGHT_V1.as_posix(),
                                "sha256": FAILED_PREFLIGHT_V1_SHA,
                                "model_server_launches": 0,
                                "new_model_generations": 0},
        "corrected_preflight_output": PREFLIGHT_V2.as_posix(),
        "source_hashes": repair_source_hashes(False),
        "maximum_new_tokenizer_calls": 0,
        "maximum_generation_attempts": original.MAX_ATTEMPTS,
        "generation_allocation": "PRESERVED_ORIGINAL_ALLOCATION_NOT_ADDITIONAL",
        "retries": 0,
        "hidden_warmups": 0,
        "minimum_available_physical_ram_bytes": 3 * 1024 ** 3,
        "minimum_free_output_disk_bytes": 1024 ** 3,
        "actual_completion_inference_seconds_ceiling": 5760,
        "batch_wall_seconds_ceiling": 8640,
        "global_baseline": cumulative_baseline(),
        "allowed_change":
            "Read analysis_v2['analysis']['cumulative_authorization_after']; no other execution or scientific setting changes."
    }


def validate_repair_authorization(path=REPAIR_AUTHORIZATION):
    authorization = load(path)
    required = repair_authorization_requirements()
    for key, expected in required.items():
        require(authorization.get(key) == expected,
                "Repair authorization changed: " + key)
    require(authorization.get("researcher") == "Yaxin ZHENG",
            "Researcher repair authorization missing")
    allowed = set(required) | {"researcher", "authorized_utc",
                               "authorization_statement"}
    require(set(authorization) <= allowed, "Unexpected repair authorization field")
    return authorization


def corrected_preflight(check_headroom=True, require_unused=True):
    """Equivalent v1 gate with only the registered schema-path correction."""
    validate_repair_evidence()
    require(REPAIR_AUTHORIZATION.resolve() == Path(
        repair_authorization_requirements()["authorization_path"]).resolve(),
        "Official repair authorization path changed")
    repair_authorization = validate_repair_authorization(REPAIR_AUTHORIZATION)
    plan = load(FROZEN)
    checks = original.validate_plan(plan)
    authorization = original.validate_authorization(Path(plan["authorization_path"]))
    require(plan["authorization_sha256"] == sha256(Path(plan["authorization_path"])),
            "Original authorization changed")
    config = original.cfg(plan)
    identity = original.b.file_preflight(config)
    require(identity["status"] == "PASS" and
            identity["model"]["sha256"] == plan["model"]["model_sha256"] and
            identity["server"]["sha256"] == plan["model"]["backend_sha256"],
            "Model/backend identity")
    native = plan["native_tokenizer_identity"]
    tokenizer = Path(native["path"])
    require(sha256(tokenizer) == native["tokenizer_sha256"] == original.TOKENIZER_SHA,
            "Tokenizer identity")
    require({path.name: sha256(path) for path in tokenizer.parent.glob("*.dll")} ==
            native["dll_hashes"], "Backend DLL set changed")
    for record in plan["native_tokenizer_logs"]:
        require(sha256(Path(record["path"])) == record["sha256"],
                "Tokenizer log changed")
    baseline = cumulative_baseline()
    require(baseline["generations_limit"] - original.GENERATION_BASELINE >=
            original.MAX_ATTEMPTS and
            baseline["inference_seconds_limit"] - original.INFERENCE_BASELINE >=
            plan["resource_budget"]["actual_completion_inference_seconds_ceiling"],
            "Cumulative budget insufficient")
    if require_unused:
        require(not (original.ROOT / "claim.json").exists() and
                not list((original.ROOT / "runs").glob("*")),
                "Existing allocation: no repeat")
    memory = original.s.memory_observation(os.getpid())
    if check_headroom:
        require(memory.get("system", {}).get("available_physical", 0) >=
                plan["resource_budget"]["minimum_available_physical_ram_bytes"],
                "Less than 3 GiB available RAM")
    require(shutil.disk_usage(".").free >=
            plan["resource_budget"]["minimum_free_output_disk_bytes"],
            "Output disk reserve")
    return {"status": "PASS", "checked_utc": original.b.utc_now(),
        "repair_version": "preflight_schema_adapter_v2",
        "checks": checks, "identity": identity,
        "manifest_sha256": sha256(FROZEN),
        "authorization_sha256": sha256(Path(plan["authorization_path"])),
        "repair_authorization_sha256": sha256(REPAIR_AUTHORIZATION),
        "failed_preflight_v1_sha256": FAILED_PREFLIGHT_V1_SHA,
        "repair_amendment_sha256": REPAIR_AMENDMENT_SHA,
        "design_sha256": original.DESIGN_SHA,
        "prospective_amendment_sha256": original.AMENDMENT_SHA,
        "wording_clarification_sha256": original.WORDING_SHA,
        "analysis_completion_amendment_sha256": original.ANALYSIS_AMENDMENT_SHA,
        "case_bank_sha256": original.CASE_BANK_SHA,
        "source_hashes": repair_source_hashes(True),
        "configuration": config.as_dict(), "server_command": original.s.command(plan),
        "memory_before_run": memory, "cumulative_baseline": baseline,
        "baseline_lookup": "analysis.cumulative_authorization_after",
        "live_gate":
            "All 96 parse_special=true token arrays must match before any completion.",
        "deactivated_controls": {"N_STYLE": "NOT_EXECUTED",
                                 "N_HISTORY": "NOT_EXECUTED"},
        "authorization": {"researcher": authorization["researcher"],
                          "repair_researcher": repair_authorization["researcher"],
                          "maximum_attempts": original.MAX_ATTEMPTS, "retries": 0},
        "model_server_launches": 0, "completion_calls": 0,
        "new_model_generations": 0}


def preflight_receipt():
    """Return persistent-safe v2 PASS/FAIL evidence without model launch."""
    try:
        return corrected_preflight()
    except BaseException as exc:
        try:
            memory = original.s.memory_observation(os.getpid())
        except BaseException as observation_error:
            memory = {"observation_error": {
                "type": type(observation_error).__name__,
                "message": str(observation_error)}}
        try:
            disk_free = shutil.disk_usage(".").free
        except BaseException:
            disk_free = None
        observed = {}
        paths = (("original_runner", Path(original.__file__)),
                 ("original_test", original.TEST_SOURCE), ("manifest", FROZEN),
                 ("original_authorization", ORIGINAL_AUTHORIZATION),
                 ("failed_preflight_v1", FAILED_PREFLIGHT_V1),
                 ("repair_amendment", REPAIR_AMENDMENT),
                 ("repair_wrapper", Path(__file__)),
                 ("repair_test", REPAIR_TEST_SOURCE), ("baseline", BASELINE),
                 ("repair_authorization", REPAIR_AUTHORIZATION))
        for name, path in paths:
            observed[name] = sha256(path) if Path(path).is_file() else None
        return {"status": "FAIL", "checked_utc": original.b.utc_now(),
            "repair_version": "preflight_schema_adapter_v2",
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "expected_bindings": {
                "original_runner_sha256": ORIGINAL_RUNNER_SHA,
                "original_test_sha256": ORIGINAL_TEST_SHA,
                "manifest_sha256": FROZEN_SHA,
                "original_authorization_sha256": ORIGINAL_AUTHORIZATION_SHA,
                "failed_preflight_v1_sha256": FAILED_PREFLIGHT_V1_SHA,
                "repair_amendment_sha256": REPAIR_AMENDMENT_SHA,
                "baseline_sha256": original.BASELINE_SHA},
            "observed_sha256": observed, "memory_observation": memory,
            "free_output_disk_bytes": disk_free,
            "minimum_available_physical_ram_bytes": 3 * 1024 ** 3,
            "minimum_free_output_disk_bytes": 1024 ** 3,
            "model_server_launches": 0, "completion_calls": 0,
            "new_model_generations": 0}


def run_original_once(preflight_path=PREFLIGHT_V2):
    """Run the preserved generator with the corrected gate injected in-process."""
    preflight_path = Path(preflight_path)
    require(preflight_path.resolve() == PREFLIGHT_V2.resolve(),
            "Only the official versioned preflight-v2 is accepted")
    stored = load(preflight_path)
    require(stored.get("status") == "PASS", "Stored preflight-v2 is not PASS")
    validate_repair_authorization(REPAIR_AUTHORIZATION)
    preserved_preflight = original.preflight
    try:
        original.preflight = corrected_preflight
        return original.run(preflight_path)
    finally:
        original.preflight = preserved_preflight


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("authorization-requirements", "preflight", "run"))
    parser.add_argument("--preflight", type=Path, default=PREFLIGHT_V2)
    args = parser.parse_args(argv)
    if args.action == "authorization-requirements":
        print(json.dumps(repair_authorization_requirements(), ensure_ascii=False,
                         indent=2, sort_keys=True))
    elif args.action == "preflight":
        require(args.preflight.resolve() == PREFLIGHT_V2.resolve(),
                "Preflight output must be the official versioned path")
        report = preflight_receipt()
        original.write_exclusive(PREFLIGHT_V2, report)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        if report["status"] != "PASS":
            return 2
    else:
        print(json.dumps(run_original_once(args.preflight), ensure_ascii=False,
                         indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
