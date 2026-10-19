import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path("tools").resolve()))

import p1_model_feasibility_recovery as recovery
import reproduce_p1_feasibility_analysis_v2 as reproduction


ARTIFACT = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/analysis_reproduction_v2.json"
)


def test_saved_receipt_exactly_matches_fresh_two_candidate_replay():
    assert json.loads(ARTIFACT.read_text(encoding="utf-8")) == reproduction.build_report()


def test_both_raw_journals_have_exactly_eight_attempts_results_and_http_records():
    replay = reproduction.build_report()["local_private_archive_replay"]
    assert replay["status"] == "PASS"
    assert replay["restricted_record_content_exported"] is False
    assert replay["candidates"] == [
        {
            "candidate_id": reproduction.CANDIDATE_1,
            "raw_journal_replay": "PASS",
            "attempts": 8,
            "result_records": 8,
            "completion_http_records": 8,
            "automatic_success": 1,
            "threshold": 7,
            "proceed": False,
            "inference_wall_seconds": 65.87628550000954,
        },
        {
            "candidate_id": reproduction.CANDIDATE_2,
            "raw_journal_replay": "PASS",
            "attempts": 8,
            "result_records": 8,
            "completion_http_records": 8,
            "automatic_success": 2,
            "threshold": 7,
            "proceed": False,
            "inference_wall_seconds": 94.08076140000139,
        },
    ]


def test_selection_and_both_ledgers_are_reconstructed_without_usage():
    result = reproduction.build_report()
    assert result["selection"] == {
        "status": "BOUNDED_SCREEN_NEGATIVE",
        "selected_candidate": None,
        "candidate_1_success": 1,
        "candidate_2_success": 2,
        "qualification_threshold": 7,
    }
    assert result["authorization"]["autonomous"] == {
        "authorization_id": "P1_AUTONOMOUS_MODEL_FEASIBILITY_20261017_V1",
        "consumed_generations": 16,
        "generation_limit": 1200,
        "remaining_generations": 1184,
        "actual_model_inference_wall_seconds": 159.95704690001094,
        "inference_wall_seconds_limit": 72000.0,
        "remaining_inference_wall_seconds": 71840.04295309998,
        "attempts_by_candidate": {
            reproduction.CANDIDATE_1: 8,
            reproduction.CANDIDATE_2: 8,
        },
    }
    assert result["authorization"]["historical"] == {
        "attempted": 80,
        "authorization": 160,
        "remaining": 80,
        "untouched": True,
    }


def test_v4_preflight_run_audit_and_selection_evidence_are_hash_bound():
    assert reproduction.build_report()["evidence_bindings"] == {
        name: {"path": path.as_posix(), "sha256": digest}
        for name, (path, digest) in reproduction.EVIDENCE.items()
    }


def test_reproduction_is_deterministic_public_safe_and_generation_free(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Inference or network-capable action was called")

    for name in ("download", "materialize", "preflight", "run"):
        monkeypatch.setattr(recovery, name, forbidden)
    before = recovery.cumulative()
    first = reproduction.build_report()
    second = reproduction.build_report()
    assert first == second
    assert recovery.cumulative() == before
    serialized = json.dumps(first, ensure_ascii=False, sort_keys=True)
    for forbidden_text in (
        '"raw_response":',
        '"prompt":',
        "server_command",
        "results/p1_model_feasibility",
        str(reproduction.PROJECT_ROOT),
    ):
        assert forbidden_text not in serialized
    assert first["execution_impact"] == {
        "scientific_model_generations": 0,
        "model_inference_wall_seconds": 0,
        "network_calls": 0,
        "authorization_usage_before_equals_after": True,
        "historical_outputs_modified": False,
    }


def test_output_is_exclusive_create_and_leaves_no_temporary_file(tmp_path):
    output = tmp_path / "reproduction.json"
    expected = reproduction.build_report()
    reproduction._write_new_atomic(output, expected)
    assert json.loads(output.read_text(encoding="utf-8")) == expected
    assert not list(tmp_path.glob(".*.tmp"))

    original = output.read_bytes()
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        reproduction._write_new_atomic(output, {"changed": True})
    assert output.read_bytes() == original
