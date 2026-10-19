"""Publish the frozen mechanism analysis after a key-only JSON repair."""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import tempfile

import p1_persona_dialogue_mechanism as m


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT = Path("docs/validation/p1/persona_dialogue_mechanism_v1")
FAILURE = OUT / "analysis_failure_v1.json"
AUDIT = OUT / "execution_audit_v1.json"
PREFLIGHT = OUT / "preflight_v2.json"
CLAIM = m.ROOT / "claim.json"
TEST_SOURCE = Path("tests/test_p1_persona_dialogue_mechanism_analysis_v2.py")
EXPECTED_OUTPUT = OUT / "analysis_v2.json"

FAILURE_SHA256 = "cd31a657f35bc672827def19cb8c8ea964a6b16ecedf775062a30d47f997ddb0"
CLAIM_SHA256 = "c7e4570be5959c12d26d2360d2cfd73b9c884305a735feb1e502bd50fbaae46a"
RUNNER_SHA256 = "fd3bb9793ca2630d8e2e145d97bfb742ef197e5465346a8a420b38f592274b3f"
BOUNDARY_LABEL = "BOUNDARY_CENSORED"
TARGETS = (
    ("primary_arm_summary", "selection_categories"),
    ("secondary_only_not_in_primary_effects", "reason_support_distribution"),
)
EXPECTED_MIGRATIONS = {
    "primary_arm_summary": {"F_H_STRUCTURE": 2, "S_F_H": 3, "S_F_NO_H": 3, "S_H": 3},
    "secondary_only_not_in_primary_effects": {
        "F_H_STRUCTURE": 2, "S_F_H": 3, "S_F_NO_H": 3, "S_H": 3,
    },
}


def authorization_requirements():
    """Return the exact prospective authorization fields required by this wrapper."""
    failure = load(FAILURE)
    bindings = failure["bindings"]
    run_directory = Path(bindings["run_directory"])
    return {
        "schema_version": "personaslm_persona_dialogue_mechanism_analysis_v2_authorization_v1",
        "status": "AUTHORIZED_BEFORE_ANALYSIS_V2_EXECUTION",
        "authorized_action": "RECOMPUTE_FROZEN_ANALYSIS_WITH_KEY_ONLY_JSON_SERIALIZATION_REPAIR",
        "analysis_wrapper": {
            "path": Path(__file__).resolve().relative_to(PROJECT_ROOT).as_posix(),
            "sha256": m.sha256(Path(__file__)),
        },
        "analysis_test": {"path": TEST_SOURCE.as_posix(), "sha256": sha256(TEST_SOURCE)},
        "evidence": {
            "analysis_failure": {"path": FAILURE.as_posix(), "sha256": FAILURE_SHA256},
            "preserved_partial_output": {
                "path": failure["preserved_partial_file"]["path"],
                "sha256": failure["preserved_partial_file"]["sha256"],
            },
            "effective_manifest": {"path": m.FROZEN.as_posix(),
                                   "sha256": bindings["effective_manifest_sha256"]},
            "effective_authorization": {"path": m.AUTH.as_posix(),
                                        "sha256": bindings["effective_authorization_sha256"]},
            "preflight": {"path": PREFLIGHT.as_posix(),
                          "sha256": bindings["preflight_sha256"]},
            "execution_claim": {"path": CLAIM.as_posix(), "sha256": CLAIM_SHA256},
            "run_manifest": {"path": (run_directory / "manifest.json").as_posix(),
                             "sha256": bindings["run_manifest_sha256"]},
            "run_summary": {"path": (run_directory / "summary.json").as_posix(),
                            "sha256": bindings["run_summary_sha256"]},
            "execution_audit": {"path": AUDIT.as_posix(),
                                "sha256": bindings["execution_audit_sha256"]},
        },
        "permitted_key_mapping": {
            "paths": [f"/{outer}/*/{inner}" for outer, inner in TARGETS],
            "source_key": None,
            "target_key": BOUNDARY_LABEL,
            "recursive_value_replacement": False,
        },
        "output_path": EXPECTED_OUTPUT.as_posix(),
        "maximum_new_model_generations": 0,
    }


def validate_authorization(path, output_path):
    authorization = load(path)
    required = authorization_requirements()
    for key, expected in required.items():
        require(authorization.get(key) == expected, f"Analysis-v2 authorization changed: {key}")
    require(Path(output_path).as_posix() == required["output_path"],
            "Analysis-v2 output path is not the authorized exclusive path")
    require(authorization.get("researcher") == "Yaxin ZHENG",
            "Analysis-v2 researcher authorization missing")
    return authorization


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha256(path):
    return m.sha256(PROJECT_ROOT / path)


def load(path):
    return json.loads((PROJECT_ROOT / path).read_text(encoding="utf-8"))


def sanitize_analysis(value):
    """Rename null Counter keys at the two authorized paths, and nothing else."""
    original = copy.deepcopy(value)
    fixed = copy.deepcopy(value)
    migrations = {outer: {} for outer, _ in TARGETS}
    for outer, inner in TARGETS:
        for arm, summary in fixed[outer].items():
            distribution = summary[inner]
            if None not in distribution:
                continue
            require(BOUNDARY_LABEL not in distribution,
                    f"Refusing ambiguous key merge at {outer}/{arm}/{inner}")
            migrations[outer][arm] = distribution.pop(None)
            distribution[BOUNDARY_LABEL] = migrations[outer][arm]

    before, after = copy.deepcopy(original), copy.deepcopy(fixed)
    marker = {"authorized_distribution_replaced_for_comparison": True}
    for outer, inner in TARGETS:
        require(set(before[outer]) == set(after[outer]), f"Arm set changed at {outer}")
        for arm in before[outer]:
            source = before[outer][arm][inner]
            expected = dict(source)
            if None in expected:
                require(BOUNDARY_LABEL not in expected,
                        f"Pre-existing repair label at {outer}/{arm}/{inner}")
                expected[BOUNDARY_LABEL] = expected.pop(None)
            require(after[outer][arm][inner] == expected,
                    f"Unauthorized distribution change at {outer}/{arm}/{inner}")
            before[outer][arm][inner] = marker
            after[outer][arm][inner] = marker
    require(before == after, "Analysis changed outside the two authorized key maps")
    return fixed, migrations


def bound_evidence():
    require(sha256(FAILURE) == FAILURE_SHA256, "Analysis failure record changed")
    failure = load(FAILURE)
    bindings = failure["bindings"]
    run_directory = Path(bindings["run_directory"])
    paths = {
        "effective_manifest_sha256": m.FROZEN,
        "effective_authorization_sha256": m.AUTH,
        "preflight_sha256": PREFLIGHT,
        "run_summary_sha256": run_directory / "summary.json",
        "run_manifest_sha256": run_directory / "manifest.json",
        "execution_audit_sha256": AUDIT,
    }
    for key, path in paths.items():
        require(sha256(path) == bindings[key], f"Bound evidence changed: {path}")
    partial = failure["preserved_partial_file"]
    require(sha256(Path(partial["path"])) == partial["sha256"],
            "Preserved failed partial output changed")
    require(sha256(CLAIM) == CLAIM_SHA256, "Execution claim changed")

    plan, authorization = load(m.FROZEN), load(m.AUTH)
    claim, run_manifest = load(CLAIM), load(run_directory / "manifest.json")
    audit, summary = load(AUDIT), load(run_directory / "summary.json")
    m.validate_plan(plan)
    sources = m.source_hashes()
    require(plan["registration_source_hashes"] == claim["source_hashes"] == sources,
            "Frozen/live/claimed source hashes differ")
    runner_path = Path(m.__file__).resolve().relative_to(PROJECT_ROOT).as_posix()
    require(runner_path == "tools/p1_persona_dialogue_mechanism.py" and
            sources[runner_path] == RUNNER_SHA256, "Frozen runner changed")
    require(run_manifest["frozen_manifest"] == plan and
            run_manifest["authorization"] == authorization and
            run_manifest["claim"] == claim, "Run manifest bindings changed")
    require(audit["integrity_status"] == "PASS" and
            audit["attempted"] == audit["results"] == audit["http_responses_verified"] == 42,
            "Execution audit is not PASS 42/42/42")
    require(summary["status"] == "PASS" and
            summary["attempted"] == summary["responses_received"] == summary["results"] == 42,
            "Run summary is not PASS 42/42/42")
    return failure, plan, bindings


def build_report(authorization_path, output_path):
    authorization = validate_authorization(authorization_path, output_path)
    failure, plan, bindings = bound_evidence()
    analysis, migrations = sanitize_analysis(m.analyze())
    require(migrations == EXPECTED_MIGRATIONS, "Boundary-censored migration counts changed")
    require(analysis["manifest_sha256"] == bindings["effective_manifest_sha256"] and
            analysis["generations"] == 42 and analysis["new_generations_during_analysis"] == 0,
            "Recomputed analysis binding or generation count changed")
    return {
        "version": "p1_persona_dialogue_mechanism_analysis_v2",
        "status": "PASS_KEY_ONLY_SERIALIZATION_REPAIR",
        "analysis_v2_authorization": {
            "path": Path(authorization_path).as_posix(),
            "sha256": sha256(Path(authorization_path)),
            "researcher": authorization["researcher"],
            "status": authorization["status"],
        },
        "original_failure": failure,
        "evidence_bindings": copy.deepcopy(bindings),
        "source_bindings": {
            "frozen_registration_sources": copy.deepcopy(plan["registration_source_hashes"]),
            "frozen_runner": {"path": "tools/p1_persona_dialogue_mechanism.py",
                              "sha256": RUNNER_SHA256},
            "analysis_v2": {"path": Path(__file__).resolve().relative_to(PROJECT_ROOT).as_posix(),
                            "sha256": m.sha256(Path(__file__))},
            "analysis_v2_test": {"path": TEST_SOURCE.as_posix(),
                                 "sha256": sha256(TEST_SOURCE)},
        },
        "repair": {
            "authorized_paths": [f"/{outer}/*/{inner}" for outer, inner in TARGETS],
            "key_mapping": {"null": BOUNDARY_LABEL},
            "migrated_counts": migrations,
            "all_other_structure_and_values_equal": True,
            "numerical_scores_changed": False,
        },
        "analysis": analysis,
        "execution_impact": {"new_model_generations": 0, "network_calls": 0,
                             "raw_outputs_modified": False,
                             "failed_partial_output_modified": False},
    }


def write_exclusive(path, value):
    """Atomically create a JSON result without replacing any existing evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {path}")
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    args = parser.parse_args()
    report = build_report(args.authorization, args.output)
    write_exclusive(args.output, report)
    print(json.dumps({"status": report["status"], "output": args.output.as_posix(),
                      "new_model_generations": 0}, indent=2))


if __name__ == "__main__":
    main()
