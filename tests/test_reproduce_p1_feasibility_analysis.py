import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path("tools").resolve()))

import p1_model_feasibility_recovery as recovery
import reproduce_p1_feasibility_analysis as reproduction


ARTIFACT = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/analysis_reproduction_v1.json"
)


REGRESSION = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/analysis_reproduction_regression_v1.json"
)


def archived_report():
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_saved_v1_reproduction_receipt_and_bound_sources_remain_immutable():
    regression = json.loads(REGRESSION.read_text(encoding="utf-8"))
    assert reproduction._sha256(Path(reproduction.__file__)) == (
        "2bf7ce8a85762cbb5887a7732bf158a1cf096d1ef6dcd3ad72404ad506be479d"
    )
    assert reproduction._sha256(ARTIFACT) == (
        "4d0570e78106abf1b19113fe616c5b11e4fb59cc87868c646951e22e65bad352"
    )
    assert regression["artifacts"]["tools/reproduce_p1_feasibility_analysis.py"] == (
        reproduction._sha256(Path(reproduction.__file__))
    )
    assert regression["artifacts"][ARTIFACT.as_posix()] == reproduction._sha256(ARTIFACT)


def test_v1_reproduction_fails_closed_after_candidate_two_state_advanced():
    with pytest.raises(ValueError, match="Candidate selection state changed"):
        reproduction.build_report()


def test_replays_candidate_one_and_preserves_both_authorization_ledgers():
    result = archived_report()
    assert result["analysis_code"] == {
        "path": "tools/reproduce_p1_feasibility_analysis.py",
        "sha256": reproduction._sha256(Path(reproduction.__file__)),
    }
    assert result["candidate1_local_private_archive_replay"] == {
        "status": "PASS",
        "candidate_id": reproduction.CANDIDATE_1,
        "integrity_status": "PASS",
        "attempted": 8,
        "completion_http_records": 8,
        "replayed_results": 8,
        "automatic_success": 1,
        "threshold": 7,
        "proceed": False,
    }
    assert result["selection"] == {
        "status": "CANDIDATE_1_FAILED_CANDIDATE_2_PENDING",
        "selected_candidate": None,
    }
    assert result["authorization"]["autonomous"]["consumed_generations"] == 8
    assert result["authorization"]["autonomous"]["generation_limit"] == 1200
    assert result["authorization"]["autonomous"]["attempts_by_candidate"] == {
        reproduction.CANDIDATE_1: 8,
        reproduction.CANDIDATE_2: 0,
    }
    assert result["authorization"]["historical"] == {
        "attempted": 80,
        "authorization": 160,
        "remaining": 80,
        "untouched": True,
    }


def test_public_safe_evaluator_is_rebuilt_in_isolation_from_exact_allowlist():
    isolated = reproduction._isolated_evaluator_reconstruction()
    assert isolated["status"] == "PASS"
    assert isolated["exact_archived_equality"] is True
    assert isolated["launcher"] == {
        "interpreter": "sys.executable",
        "flags": ["-I", "-B"],
    }
    assert [row["path"] for row in isolated["copied_allowlist"]] == [
        path.as_posix() for path in reproduction.ISOLATED_AGGREGATE_FILES
    ]
    assert len(isolated["copied_allowlist"]) == 8
    assert all("results" not in Path(row["path"]).parts for row in isolated["copied_allowlist"])
    assert isolated["restricted_or_raw_record_material_copied"] is False


def test_candidate_two_preflight_v2_is_hash_bound_and_generation_free():
    preflight = archived_report()["candidate2_preflight_v2"]
    assert preflight == {
        "status": "BLOCKED",
        "candidate_id": reproduction.CANDIDATE_2,
        "generation_requests": 0,
        "required_available_physical_bytes": 5 * 1024**3,
        "gate_available_physical_bytes": 4_595_142_656,
        "deficit_bytes": 773_566_464,
        "post_failure_observation_available_physical_bytes": 4_584_386_560,
        "path": reproduction.PREFLIGHT.as_posix(),
        "sha256": reproduction.PREFLIGHT_SHA256,
    }


def test_candidate_two_cannot_reuse_legacy_controller_or_positional_slices():
    boundary = archived_report()["downstream_execution_boundary"]
    assert boundary["status"] == (
        "REQUIRES_NEW_CANDIDATE2_NATIVE_MATERIALIZATION_AND_CONTROLLER"
    )
    assert boundary["existing_conditional_controller_callable_for_candidate2"] is False
    assert boundary["future_candidate2_gate_policy"] == (
        "DO_NOT_CALL_EXISTING_P1_CONDITIONAL_EXECUTION_V2"
    )
    assert boundary["candidate2_model_sha256"] == (
        "626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d"
    )
    assert len(boundary["legacy_controller_files"]) == 2
    assert len(boundary["legacy_80_request_manifests"]) == 2
    assert all(row["request_count"] == 80 for row in boundary["legacy_80_request_manifests"])
    assert all(
        row["model_sha256"] == reproduction.LEGACY_MODEL_SHA256
        and row["authorization_id"] == reproduction.LEGACY_AUTHORIZATION
        for row in boundary["legacy_80_request_manifests"]
    )
    assert len({
        row["request_order_sha256"]
        for row in boundary["legacy_80_request_manifests"]
    }) == 2
    assert boundary["manifest_request_sequences_equal"] is False
    assert boundary["positional_slice_reuse_verified"] is False


def test_reproduction_boundaries_and_zero_execution_impact_are_explicit(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Inference or network-capable action was called")

    for name in ("download", "materialize", "preflight", "run"):
        monkeypatch.setattr(recovery, name, forbidden)
    before = recovery.cumulative()
    result = archived_report()
    after = recovery.cumulative()
    assert before == after
    assert {name: row["status"] for name, row in result["reproduction_boundaries"].items()} == {
        "local_private_archive_analysis": "PASS",
        "public_safe_aggregate_isolated_reconstruction": "PASS",
        "generation_reproduction": "NOT_RUN/BLOCKED_RESOURCE",
        "public_clone_only_full_reproduction": "PARTIAL",
    }
    assert result["execution_impact"] == {
        "scientific_model_generations": 0,
        "model_inference_wall_seconds": 0,
        "authorization_usage_before_equals_after": True,
        "network_calls": 0,
        "historical_outputs_modified": False,
    }


def test_report_is_deterministic_and_contains_no_temporary_path(tmp_path):
    first = archived_report()
    second = archived_report()
    assert first == second
    serialized = json.dumps(first, sort_keys=True)
    assert str(tmp_path) not in serialized
    assert "software_recorded_utc" not in serialized
    assert "observed_utc" not in serialized


def test_output_is_new_only_complete_json_and_leaves_no_temporary_file(tmp_path):
    output = tmp_path / "reproduction.json"
    expected = archived_report()
    reproduction._write_new_atomic(output, expected)
    assert json.loads(output.read_text(encoding="utf-8")) == expected
    assert not list(tmp_path.glob(".*.tmp"))

    original = output.read_bytes()
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        reproduction._write_new_atomic(output, {"changed": True})
    assert output.read_bytes() == original


def test_isolated_programs_have_no_network_or_model_inference_imports():
    combined = "\n".join(
        (reproduction.PROJECT_ROOT / path).read_text(encoding="utf-8")
        for path in reproduction.ISOLATED_AGGREGATE_FILES
        if path.suffix == ".py"
    )
    for forbidden in (
        "import requests",
        "import socket",
        "import urllib",
        "http.client",
        "personaslm.inference",
        "LlamaClient",
    ):
        assert forbidden not in combined
