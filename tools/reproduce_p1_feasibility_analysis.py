"""Reproduce the current P1 feasibility analysis without model inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import p1_evaluator_validity as evaluator
import p1_model_feasibility_recovery as recovery


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_1 = "smollm2_1_7b_instruct_q4_k_m"
CANDIDATE_2 = "qwen2_5_3b_instruct_q4_k_m"
PREFLIGHT = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "candidate2_preflight_attempt_v2.json"
)
PREFLIGHT_SHA256 = "686f92690681b69911643840ff5a30b8b7b07015bc55a293cc0b283b1908d5d9"
EVALUATOR_ARTIFACT = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/evaluator_validity_v1.json"
)
CONDITIONAL_CONTROLLERS = {
    Path("tools/p1_conditional_execution.py"):
        "d51b15dd23bb268bd272bc7f7f4c6f28ee69d8a7027ab18b4019646b28602c65",
    Path("tools/p1_conditional_execution_v2.py"):
        "4d0c776d994ff680852355abe2e0d3df5e59404fa7446afa49f0ade80a354610",
}
LEGACY_FACTORIAL_MANIFESTS = {
    Path("docs/validation/p1/measurement_pilot_v1/B_FACTORIAL_manifest_v1.json"):
        "1fd7ef2d4365119755ca4301779d37c1276c53107d121d0df8dd732aaca6c77b",
    Path(
        "docs/validation/p1/measurement_recovery_2x2_v2/fallback_bank_v1/"
        "fallback_pilot_manifest_candidate_v1.json"
    ): "4be7b1959779371502a0e562a589c942676644ef86897196912677978d4da382",
}
LEGACY_MODEL_SHA256 = "0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc"
LEGACY_AUTHORIZATION = "P1_ACCELERATED_MEASUREMENT_20261015_V1"
ISOLATED_AGGREGATE_FILES = (
    Path("tools/p1_evaluator_validity.py"),
    Path("tools/p1_measurement_scoring.py"),
    *(evaluator.SOURCES[name] for name in sorted(evaluator.SOURCES)),
)
ISOLATED_BOOTSTRAP = (
    "import runpy,sys; sys.path.insert(0,sys.argv[1]); "
    "runpy.run_path(sys.argv[2],run_name='__main__')"
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _isolated_evaluator_reconstruction() -> dict:
    """Rebuild the public-safe aggregate from an explicit temporary allowlist."""
    copied = []
    with tempfile.TemporaryDirectory(prefix="personaslm-p1-analysis-") as directory:
        isolated_root = Path(directory)
        for relative in ISOLATED_AGGREGATE_FILES:
            source = PROJECT_ROOT / relative
            _require(source.is_file(), f"Missing isolated aggregate input: {relative}")
            _require("results" not in relative.parts, f"Raw result path is not public-safe: {relative}")
            target = isolated_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied.append({"path": relative.as_posix(), "sha256": _sha256(source)})

        tool = isolated_root / "tools/p1_evaluator_validity.py"
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                ISOLATED_BOOTSTRAP,
                str(isolated_root / "tools"),
                str(tool),
            ],
            cwd=isolated_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
        _require(
            completed.returncode == 0,
            f"Isolated aggregate reconstruction failed: {completed.stderr.strip()}",
        )
        reconstructed = json.loads(completed.stdout)

    archived_path = PROJECT_ROOT / EVALUATOR_ARTIFACT
    archived = json.loads(archived_path.read_text(encoding="utf-8"))
    _require(reconstructed == archived, "Isolated evaluator aggregate differs from archive")
    return {
        "status": "PASS",
        "exact_archived_equality": True,
        "launcher": {"interpreter": "sys.executable", "flags": ["-I", "-B"]},
        "copied_allowlist": copied,
        "archived_artifact": {
            "path": EVALUATOR_ARTIFACT.as_posix(),
            "sha256": _sha256(archived_path),
        },
        "canonical_evidence_sha256": _canonical_sha256(reconstructed),
        "restricted_or_raw_record_material_copied": False,
    }


def _downstream_execution_boundary() -> dict:
    controllers = []
    for relative, expected in CONDITIONAL_CONTROLLERS.items():
        path = PROJECT_ROOT / relative
        _require(_sha256(path) == expected, f"Legacy controller changed: {relative}")
        controllers.append({"path": relative.as_posix(), "sha256": expected})

    manifests = []
    request_sequences = []
    for relative, expected in LEGACY_FACTORIAL_MANIFESTS.items():
        path = PROJECT_ROOT / relative
        _require(_sha256(path) == expected, f"Legacy factorial manifest changed: {relative}")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        requests = manifest["requests"]
        sequence = [row["request_id"] for row in requests]
        _require(len(sequence) == len(set(sequence)) == 80,
                 f"Legacy factorial inventory changed: {relative}")
        _require(manifest["model"]["model_sha256"] == LEGACY_MODEL_SHA256,
                 f"Legacy factorial model changed: {relative}")
        _require(manifest["authorization_id"] == LEGACY_AUTHORIZATION,
                 f"Legacy factorial authorization changed: {relative}")
        request_sequences.append(sequence)
        manifests.append({
            "path": relative.as_posix(),
            "sha256": expected,
            "request_count": len(sequence),
            "request_order_sha256": _canonical_sha256(sequence),
            "model_sha256": manifest["model"]["model_sha256"],
            "authorization_id": manifest["authorization_id"],
        })
    _require(request_sequences[0] != request_sequences[1],
             "Legacy manifest request sequences unexpectedly match")
    _require(LEGACY_MODEL_SHA256 != recovery.candidates()[CANDIDATE_2]["artifact"]["remote_sha256"],
             "Legacy controller unexpectedly binds Candidate 2")
    return {
        "status": "REQUIRES_NEW_CANDIDATE2_NATIVE_MATERIALIZATION_AND_CONTROLLER",
        "existing_conditional_controller_callable_for_candidate2": False,
        "future_candidate2_gate_policy": "DO_NOT_CALL_EXISTING_P1_CONDITIONAL_EXECUTION_V2",
        "candidate2_model_sha256": recovery.candidates()[CANDIDATE_2]["artifact"]["remote_sha256"],
        "legacy_controller_files": controllers,
        "legacy_80_request_manifests": manifests,
        "manifest_request_sequences_equal": False,
        "positional_slice_reuse_verified": False,
        "reason": (
            "The existing controller and both 80-request manifests bind the historical "
            "Qwen3.5 model and historical authorization. Their request sequences differ; "
            "a positional slice cannot be transferred to Candidate 2 without prospective "
            "native materialization and a new validated controller."
        ),
    }


def build_report() -> dict:
    """Replay saved analyses and verify that authorization usage is unchanged."""
    usage_before = recovery.cumulative()
    candidate1 = recovery.audit(CANDIDATE_1)
    selection = recovery.selection_status()
    isolated = _isolated_evaluator_reconstruction()

    _require(candidate1["integrity_status"] == "PASS", "Candidate 1 integrity failed")
    _require(candidate1["attempted"] == candidate1["replayed_results"] == 8,
             "Candidate 1 inventory changed")
    _require(candidate1["success"] == 1 and candidate1["threshold"] == 7,
             "Candidate 1 frozen gate changed")
    _require(candidate1["proceed"] is False, "Candidate 1 unexpectedly qualifies")
    _require(selection["status"] == "CANDIDATE_1_FAILED_CANDIDATE_2_PENDING",
             "Candidate selection state changed")

    _require(usage_before["new_local_cpu_generations"] == 8, "Autonomous usage changed")
    _require(usage_before["remaining_generations"] == 1192, "Autonomous balance changed")
    _require(usage_before["attempts_by_candidate"] == {CANDIDATE_1: 8, CANDIDATE_2: 0},
             "Candidate attempt inventory changed")
    _require(usage_before["historical_ledger_untouched"] is True,
             "Historical ledger separation changed")

    ledger = recovery.load(recovery.LEDGER)
    historical = ledger["historical_ledger_separation"]
    _require(
        (historical["historical_attempted"], historical["historical_authorization"],
         historical["historical_remaining"]) == (80, 160, 80),
        "Historical ledger changed",
    )

    preflight_path = PROJECT_ROOT / PREFLIGHT
    _require(_sha256(preflight_path) == PREFLIGHT_SHA256, "Candidate 2 preflight hash changed")
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    required = 5 * 1024**3
    gate_available = 4_595_142_656
    _require(preflight["status"] == "BLOCKED", "Candidate 2 preflight is not blocked")
    _require(preflight["candidate_id"] == CANDIDATE_2, "Candidate 2 preflight identity changed")
    _require(preflight["generation_requests_in_failed_action"] == 0,
             "Blocked preflight consumed a generation")
    _require(preflight["required_available_physical_bytes"] == required,
             "Candidate 2 RAM gate changed")
    _require(
        preflight["error_message"]
        == f"RAM preflight failed: available={gate_available} required={required}; no inference",
        "Candidate 2 gate observation changed",
    )
    _require(preflight["authorization_usage_observed"] == usage_before,
             "Preflight usage snapshot differs from current archive")

    usage_after = recovery.cumulative()
    _require(usage_after == usage_before, "Analysis reproduction changed authorization usage")
    return {
        "version": "p1_feasibility_analysis_reproduction_v1",
        "analysis_code": {
            "path": "tools/reproduce_p1_feasibility_analysis.py",
            "sha256": _sha256(Path(__file__)),
        },
        "candidate1_local_private_archive_replay": {
            "status": "PASS",
            "candidate_id": CANDIDATE_1,
            "integrity_status": candidate1["integrity_status"],
            "attempted": candidate1["attempted"],
            "completion_http_records": candidate1["completion_http_records"],
            "replayed_results": candidate1["replayed_results"],
            "automatic_success": candidate1["success"],
            "threshold": candidate1["threshold"],
            "proceed": candidate1["proceed"],
        },
        "selection": {
            "status": selection["status"],
            "selected_candidate": selection["selected_candidate"],
        },
        "authorization": {
            "autonomous": {
                "authorization_id": usage_before["authorization_id"],
                "consumed_generations": usage_before["new_local_cpu_generations"],
                "generation_limit": (
                    usage_before["new_local_cpu_generations"]
                    + usage_before["remaining_generations"]
                ),
                "remaining_generations": usage_before["remaining_generations"],
                "actual_model_inference_wall_seconds": usage_before[
                    "actual_model_inference_wall_seconds"
                ],
                "attempts_by_candidate": usage_before["attempts_by_candidate"],
            },
            "historical": {
                "attempted": historical["historical_attempted"],
                "authorization": historical["historical_authorization"],
                "remaining": historical["historical_remaining"],
                "untouched": usage_before["historical_ledger_untouched"],
            },
        },
        "public_safe_aggregate_isolated_reconstruction": isolated,
        "candidate2_preflight_v2": {
            "status": preflight["status"],
            "candidate_id": preflight["candidate_id"],
            "generation_requests": preflight["generation_requests_in_failed_action"],
            "required_available_physical_bytes": required,
            "gate_available_physical_bytes": gate_available,
            "deficit_bytes": required - gate_available,
            "post_failure_observation_available_physical_bytes": preflight[
                "memory_observation"
            ]["system"]["available_physical"],
            "path": PREFLIGHT.as_posix(),
            "sha256": PREFLIGHT_SHA256,
        },
        "downstream_execution_boundary": _downstream_execution_boundary(),
        "reproduction_boundaries": {
            "local_private_archive_analysis": {
                "status": "PASS",
                "scope": "Candidate 1 journal/raw-output replay from the local results archive.",
            },
            "public_safe_aggregate_isolated_reconstruction": {
                "status": "PASS",
                "scope": "Exact evaluator aggregate rebuilt from the explicit safe allowlist.",
            },
            "generation_reproduction": {
                "status": "NOT_RUN/BLOCKED_RESOURCE",
                "scope": "No generation was repeated; Candidate 2 remains below its frozen RAM gate.",
            },
            "public_clone_only_full_reproduction": {
                "status": "PARTIAL",
                "scope": (
                    "Safe aggregate reconstruction is available, but full Candidate 1 replay "
                    "depends on the local results archive and generation requires model weights."
                ),
            },
        },
        "execution_impact": {
            "scientific_model_generations": 0,
            "model_inference_wall_seconds": 0,
            "authorization_usage_before_equals_after": True,
            "network_calls": 0,
            "historical_outputs_modified": False,
        },
    }


def _write_new_atomic(path: Path, value: dict) -> None:
    """Publish a complete new file without ever replacing an existing path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {path}")
    payload = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = build_report()
    if arguments.output is not None:
        _write_new_atomic(arguments.output, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
