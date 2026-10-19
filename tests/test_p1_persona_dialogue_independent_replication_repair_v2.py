import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "persona_dialogue_independent_replication_repair_v2",
    ROOT / "tools/p1_persona_dialogue_independent_replication_repair_v2.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_repair_is_additive_and_preserves_all_v1_evidence():
    assert MODULE.validate_repair_evidence() is True
    assert MODULE.sha256(ROOT / MODULE.REPAIR_AMENDMENT) == \
        MODULE.REPAIR_AMENDMENT_SHA
    assert MODULE.sha256(ROOT / MODULE.FROZEN) == MODULE.FROZEN_SHA
    assert MODULE.sha256(ROOT / MODULE.ORIGINAL_AUTHORIZATION) == \
        MODULE.ORIGINAL_AUTHORIZATION_SHA
    assert MODULE.sha256(ROOT / MODULE.FAILED_PREFLIGHT_V1) == \
        MODULE.FAILED_PREFLIGHT_V1_SHA
    assert MODULE.sha256(Path(MODULE.original.__file__)) == \
        MODULE.ORIGINAL_RUNNER_SHA
    assert MODULE.sha256(ROOT / MODULE.original.TEST_SOURCE) == \
        MODULE.ORIGINAL_TEST_SHA
    assert not (ROOT / MODULE.PREFLIGHT_V2).exists()


def test_nested_authoritative_baseline_is_exact_and_not_reinterpreted():
    document = json.loads((ROOT / MODULE.BASELINE).read_text(encoding="utf-8"))
    assert "cumulative_authorization_after" not in document
    assert MODULE.cumulative_baseline() == \
        document["analysis"]["cumulative_authorization_after"] == {
            "generations_limit": 1200,
            "generations_used": 106,
            "inference_seconds_limit": 72000.0,
            "inference_seconds_used": 668.7530845000028,
        }


def test_repair_authorization_binds_wrapper_test_amendment_and_failed_receipt(tmp_path):
    required = MODULE.repair_authorization_requirements()
    paths = required["source_hashes"]
    expected = {
        MODULE.REPAIR_AMENDMENT.as_posix(): MODULE.REPAIR_AMENDMENT_SHA,
        MODULE.FAILED_PREFLIGHT_V1.as_posix(): MODULE.FAILED_PREFLIGHT_V1_SHA,
        MODULE.FROZEN.as_posix(): MODULE.FROZEN_SHA,
        MODULE.ORIGINAL_AUTHORIZATION.as_posix(): MODULE.ORIGINAL_AUTHORIZATION_SHA,
        "tools/p1_persona_dialogue_independent_replication_repair_v2.py":
            MODULE.sha256(Path(MODULE.__file__)),
        MODULE.REPAIR_TEST_SOURCE.as_posix():
            MODULE.sha256(ROOT / MODULE.REPAIR_TEST_SOURCE),
    }
    for path, digest in expected.items():
        assert paths[path] == digest
    assert required["maximum_new_tokenizer_calls"] == 0
    assert required["maximum_generation_attempts"] == 96
    assert required["generation_allocation"] == \
        "PRESERVED_ORIGINAL_ALLOCATION_NOT_ADDITIONAL"
    authorization = {**required, "researcher": "Yaxin ZHENG"}
    path = tmp_path / "repair_authorization.json"
    path.write_text(json.dumps(authorization), encoding="utf-8")
    assert MODULE.validate_repair_authorization(path) == authorization
    authorization["maximum_new_tokenizer_calls"] = 1
    path.write_text(json.dumps(authorization), encoding="utf-8")
    with pytest.raises(ValueError, match="Repair authorization changed"):
        MODULE.validate_repair_authorization(path)


def test_failed_v2_receipt_remains_zero_generation_evidence(monkeypatch):
    def fail():
        raise ValueError("synthetic preflight failure")

    monkeypatch.setattr(MODULE, "corrected_preflight", fail)
    monkeypatch.setattr(MODULE.original.s, "memory_observation",
                        lambda _pid: {"system": {"available_physical": 123}})
    monkeypatch.setattr(MODULE.shutil, "disk_usage",
                        lambda _path: type("Disk", (), {"free": 456})())
    receipt = MODULE.preflight_receipt()
    assert receipt["status"] == "FAIL"
    assert receipt["error"] == {"type": "ValueError",
                                 "message": "synthetic preflight failure"}
    assert receipt["memory_observation"]["system"]["available_physical"] == 123
    assert receipt["free_output_disk_bytes"] == 456
    assert receipt["model_server_launches"] == receipt["completion_calls"] == \
        receipt["new_model_generations"] == 0


def test_run_delegates_once_with_corrected_preflight_and_restores_original(
        tmp_path, monkeypatch):
    repair_authorization = tmp_path / "execution_repair_authorization_v2.json"
    preflight = tmp_path / "preflight_v2.json"
    monkeypatch.setattr(MODULE, "REPAIR_AUTHORIZATION", repair_authorization)
    monkeypatch.setattr(MODULE, "PREFLIGHT_V2", preflight)
    required = MODULE.repair_authorization_requirements()
    repair_authorization.write_text(
        json.dumps({**required, "researcher": "Yaxin ZHENG"}), encoding="utf-8")
    preflight.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    prior = MODULE.original.preflight
    calls = []

    def fake_run(path):
        calls.append(Path(path))
        assert MODULE.original.preflight is MODULE.corrected_preflight
        return {"status": "DELEGATED_WITHOUT_EXECUTION"}

    monkeypatch.setattr(MODULE.original, "run", fake_run)
    result = MODULE.run_original_once(preflight)
    assert result == {"status": "DELEGATED_WITHOUT_EXECUTION"}
    assert calls == [preflight]
    assert MODULE.original.preflight is prior


def test_exclusive_v2_receipt_cannot_be_overwritten(tmp_path):
    path = tmp_path / "preflight_v2.json"
    receipt = {"status": "FAIL", "new_model_generations": 0}
    MODULE.original.write_exclusive(path, receipt)
    assert json.loads(path.read_text(encoding="utf-8")) == receipt
    with pytest.raises(FileExistsError):
        MODULE.original.write_exclusive(path, receipt)
