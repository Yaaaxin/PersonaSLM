import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "rpc_sfh_execution_amendment_v1_1",
    TOOLS / "real_persona_chat_sfh_pilot_execution_amendment_v1_1.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _schedules():
    stored = MODULE.base.load(MODULE.ORIGINAL_FROZEN)["schedule"]
    computed = MODULE.base.validate_materials()[3]
    return stored, computed


def test_historical_files_and_zero_operation_failed_preflight_are_exact():
    failed = MODULE.validate_historical_evidence()
    assert failed["error"]["message"] == "Schedule changed"
    assert failed["operations"] == {
        "server_launches": 0, "completion_calls": 0,
        "new_model_generations": 0}
    for name, path in MODULE._historical_paths().items():
        assert MODULE.base.sha256(path) == MODULE.HISTORICAL_HASHES[name]


def test_canonical_comparison_repairs_only_list_tuple_round_trip():
    stored, computed = _schedules()
    assert isinstance(stored["masks"]["B1"], list)
    assert isinstance(computed["masks"]["B1"], tuple)
    normalized, integrity = MODULE.compare_canonical_schedules(stored, computed)
    assert normalized == stored
    assert integrity["stored_schedule_canonical_sha256"] == (
        integrity["computed_schedule_canonical_sha256"])
    assert integrity["values_and_sequence_order_equal"] is True


def test_canonical_comparison_rejects_changed_value():
    stored, computed = _schedules()
    changed = copy.deepcopy(computed)
    changed["masks"]["B1"] = (7, *changed["masks"]["B1"][1:])
    with pytest.raises(ValueError, match="values or sequence order"):
        MODULE.compare_canonical_schedules(stored, changed)


def test_canonical_comparison_rejects_changed_sequence_order():
    stored, computed = _schedules()
    changed = copy.deepcopy(computed)
    values = list(changed["masks"]["B2"])
    values[0], values[1] = values[1], values[0]
    changed["masks"]["B2"] = tuple(values)
    with pytest.raises(ValueError, match="values or sequence order"):
        MODULE.compare_canonical_schedules(stored, changed)


def test_frozen_integrity_amendment_binds_implementation_and_schedule():
    value = MODULE.validate_amendment()
    assert value["status"] == "PROSPECTIVELY_FROZEN_INTEGRITY_ONLY"
    assert value["schedule_integrity"] == MODULE.schedule_integrity()
    assert value["repair"]["retokenization_permitted"] is False


def test_audit_gate_requires_execution_scope_not_preflight_only(monkeypatch):
    audit = {
        "status": "PASS", "verdict": "PASS_FOR_FRESH_PREFLIGHT_ONLY",
        "auditor_provenance": "AI independent code/scientific audit; not human review",
        "bindings": MODULE.amendment_audit_requirements(),
        "blocking_findings": [], "blocking_finding_count": 0,
        "checks": {"dummy": True},
    }
    monkeypatch.setattr(MODULE.base, "load", lambda path: audit)
    with pytest.raises(ValueError, match="did not pass"):
        MODULE.validate_amendment_audit()


def test_build_plan_reuses_frozen_prompts_tokens_and_tokenizer_evidence(monkeypatch,
                                                                        tmp_path):
    original = MODULE.base.load(MODULE.ORIGINAL_FROZEN)
    authority = tmp_path / "authority.json"
    authority.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(MODULE, "AUTHORIZATION_AMENDMENT", authority)
    monkeypatch.setattr(MODULE, "validate_historical_evidence", lambda: None)
    monkeypatch.setattr(MODULE, "amendment_binding", lambda: {"test": "binding"})
    monkeypatch.setattr(MODULE, "source_hashes", lambda: {"test": "hash"})
    monkeypatch.setattr(MODULE.base, "_tokenize_native",
                        lambda *args, **kwargs: pytest.fail("must not retokenize"))
    plan = MODULE.build_amended_plan()
    assert plan["requests"] == original["requests"]
    assert plan["native_tokenizer_evidence"] == original["native_tokenizer_evidence"]
    assert [row["input_token_ids"] for row in plan["requests"]] == [
        row["input_token_ids"] for row in original["requests"]]


def test_source_hash_set_covers_all_effective_integrity_files(monkeypatch):
    monkeypatch.setattr(MODULE, "AMENDMENT_AUDIT", MODULE.AUTHORIZATION_AMENDMENT_DRAFT)
    monkeypatch.setattr(MODULE, "AUTHORIZATION_AMENDMENT",
                        MODULE.AUTHORIZATION_AMENDMENT_DRAFT)
    hashes = MODULE.source_hashes()
    required = (
        MODULE.ORIGINAL_FROZEN, MODULE.ORIGINAL_REGISTRATION,
        MODULE.ORIGINAL_FAILED_PREFLIGHT, MODULE.AMENDMENT,
        MODULE.AUTHORIZATION_AMENDMENT_DRAFT, MODULE.CONTROLLER,
        MODULE.TEST_SOURCE)
    for path in required:
        assert hashes[MODULE._relative(path)] == MODULE.base.sha256(path)


def test_audited_authorize_amend_validate_flow_has_zero_scientific_operations(
        monkeypatch, tmp_path):
    def relative(path):
        resolved = Path(path).resolve()
        try:
            return resolved.relative_to(REPO).as_posix()
        except ValueError:
            return "external-test/" + resolved.name

    out = tmp_path / "amended"
    monkeypatch.setattr(MODULE, "_relative", relative)
    monkeypatch.setattr(MODULE, "AMENDMENT_AUDIT", out / "audit.json")
    monkeypatch.setattr(MODULE, "AUTHORIZATION_AMENDMENT", out / "authorization.json")
    monkeypatch.setattr(MODULE, "REGISTRATION", out / "registration.json")
    monkeypatch.setattr(MODULE, "PREFLIGHT", out / "preflight.json")
    monkeypatch.setattr(MODULE, "FROZEN", out / "frozen.json")
    monkeypatch.setattr(MODULE, "CLAIM", out / "claim.json")
    monkeypatch.setattr(MODULE.base, "CLAIM", out / "old-claim.json")
    monkeypatch.setattr(MODULE.base, "RUN_ROOT", out / "runs")
    monkeypatch.setattr(MODULE.base, "_tokenize_native",
                        lambda *args, **kwargs: pytest.fail("must not retokenize"))
    monkeypatch.setattr(MODULE.base.s, "Server",
                        lambda *args, **kwargs: pytest.fail("must not launch server"))

    audit = {
        "schema_version": "personaslm_rpc_sfh_integrity_amendment_audit_v1_1",
        "status": "PASS", "verdict": "PASS_FOR_AMENDED_EXECUTION",
        "auditor_provenance": "AI independent code/scientific audit; not human review",
        "bindings": MODULE.amendment_audit_requirements(),
        "blocking_findings": [], "blocking_finding_count": 0,
        "checks": {"independent_test_fixture": True},
    }
    MODULE._write_once(MODULE.AMENDMENT_AUDIT, audit)
    MODULE.write_authorization_amendment()
    receipt = MODULE.amend()
    validated = MODULE.validate()
    assert receipt["operations"] == {
        "native_tokenizer_calls": 0, "server_launches": 0,
        "completion_calls": 0, "new_model_generations": 0}
    assert validated["status"] == "PASS_OFFLINE_NO_TOKENIZATION_SERVER_OR_INFERENCE"
    amended = MODULE.base.load(MODULE.FROZEN)
    original = MODULE.base.load(MODULE.ORIGINAL_FROZEN)
    assert amended["requests"] == original["requests"]
    assert amended["native_tokenizer_evidence"] == original["native_tokenizer_evidence"]


def test_claim_and_first_event_require_all_integrity_bindings(monkeypatch):
    integrity = MODULE.schedule_integrity()
    binding = {
        "controller_sha256": "wrapper", "amendment_sha256": "amendment",
        "amendment_audit_sha256": "audit",
        "authorization_amendment_sha256": "authorization",
        "failed_preflight_sha256": "failed", "schedule_integrity": integrity,
    }
    monkeypatch.setattr(MODULE, "amendment_binding", lambda: binding)
    claim = {"source_hashes_sha256": "sources", "schedule_integrity": integrity}
    event = MODULE.first_integrity_event(claim)
    assert event["execution_integrity_bindings"] == binding
    assert event["claim"] == claim
    assert event["schedule_integrity"] == integrity
    for key in ("controller_sha256", "amendment_sha256",
                "amendment_audit_sha256", "authorization_amendment_sha256",
                "failed_preflight_sha256"):
        assert key in event["execution_integrity_bindings"]


def test_paths_force_new_preflight_and_separate_authorization_amendment():
    assert MODULE.PREFLIGHT.name == "preflight_v1_1.json"
    assert MODULE.PREFLIGHT != MODULE.ORIGINAL_FAILED_PREFLIGHT
    assert MODULE.AUTHORIZATION_AMENDMENT != MODULE.base.AUTHORIZATION
    assert MODULE.AUTHORIZATION_AMENDMENT_DRAFT.name.endswith("draft_v1_1.json")


def test_import_and_offline_helpers_do_not_execute_scientific_operations():
    assert MODULE.canonical_schedule() == MODULE.base.load(
        MODULE.ORIGINAL_FROZEN)["schedule"]
    assert MODULE.validate_historical_evidence()["operations"] == {
        "server_launches": 0, "completion_calls": 0,
        "new_model_generations": 0}
