import json
from collections import Counter
from contextlib import nullcontext
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import p1_persona_dialogue_independent_replication_declarative_repair as module


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_prospective_candidate_is_exactly_48_new_h1_and_preserves_phase_artifacts(monkeypatch):
    monkeypatch.chdir(ROOT)
    result = module.validate_design()
    design = load(module.DESIGN)
    assert result == {
        "status": "PASS_PROSPECTIVE_NOT_AUTHORIZED_NOT_EXECUTED",
        "new_h1_requests": 48,
        "archived_h0_rows": 48,
        "archived_raw_h1_comparators": 48,
        "model_generations": 0,
        "tokenizer_calls": 0,
        "authorization_files_created": 0,
        "preflight_receipts_created": 0,
    }
    assert module.sha256(ROOT / module.DESIGN) == module.DESIGN_SHA
    assert module.sha256(ROOT / module.CASE_TRANSFORM) == module.CASE_TRANSFORM_SHA
    assert design["evidence_level"] == "OUTPUT_INFORMED_SYNTHETIC_DEVELOPMENT"
    assert design["output_informed_status"]["explicit"] is True
    assert design["intervention"]["novelty_status"] == "SIMPLE_NON_NOVEL_BASELINE"
    assert design["authorization"]["execution_authorized"] is False
    assert design["authorization"]["tokenization_authorized"] is False
    assert design["authorization"]["preflight_authorized"] is False
    assert design["authorization"]["maximum_generation_attempts_if_authorized"] == 48
    assert all(value == 0 for value in design["preexecution_state"].values())
    operation_artifacts = {
        ROOT / module.AUTHORIZATION:
            "25fe4ba7dcfa27a518989a416991e856199247dc7140f774fae051af21383ac0",
        ROOT / module.FROZEN:
            "4e7dc5bf4503018fbf9130f49025e4eb7bef31b4e9f9f6ca5ae9cc2987987de0",
        ROOT / module.PREFLIGHT:
            "87be4e7a97c7c9fa7faf29184830233510e49642bfa54a8e0b82caa3beb2eca6",
        ROOT / module.ROOT / "claim.json":
            "a063da5b390cff839e625be2b2213e31306e6b1976b39078bd5903b79d4d7539",
    }
    if (ROOT / module.AUTHORIZATION).exists():
        # The immutable prospective design remains pre-execution evidence. Once the
        # separately authorized run exists, the test verifies rather than rejects it.
        assert all(path.exists() for path in operation_artifacts)
        assert {path: module.sha256(path) for path in operation_artifacts} == \
            operation_artifacts
    else:
        assert not any(path.exists() for path in operation_artifacts)


def test_transform_changes_only_archived_assistant_first_sentence(monkeypatch):
    monkeypatch.chdir(ROOT)
    parent_design = load(module.PARENT_DESIGN)
    bank = load(module.PARENT_CASE_BANK)
    transform = load(module.CASE_TRANSFORM)
    cases = {case["case_id"]: case for case in bank["cases"]}
    mappings = {case["case_id"]: case for case in transform["cases"]}
    assert len(cases) == len(mappings) == 12
    for case_id, case in cases.items():
        mapping = mappings[case_id]
        module._validate_transform(case, mapping)
        for condition in module.H1_CONDITIONS:
            factors, messages, raw = module.declarative_messages(
                case, mapping, condition, parent_design, bank)
            assert factors["H"] == 1
            assert messages[0] == raw[0]
            assert messages[1] == raw[1]
            assert messages[3] == raw[3]
            assert messages[2]["role"] == raw[2]["role"] == "assistant"
            assert messages[2]["content"] == mapping["history_assistant_declarative"]
            assert raw[2]["content"] == mapping["history_assistant_raw"]
            target = case["history_selected_target"]
            assert raw[2]["content"].startswith(f"I recommend the {target}. ")
            assert messages[2]["content"].startswith(f"My choice was {target}. ")
            assert raw[2]["content"].split(". ", 1)[1] == \
                messages[2]["content"].split(". ", 1)[1]


def test_request_order_is_parent_h1_filter_and_never_contains_h0(monkeypatch):
    monkeypatch.chdir(ROOT)
    parent_plan = load(module.PARENT_FROZEN)
    expected = [row for row in parent_plan["requests"]
                if row["condition"] in module.H1_CONDITIONS]
    specs = module.request_specs()
    assert len(specs) == len(expected) == 48
    assert [row["order"] for row in specs] == list(range(48))
    assert [row["parent_order"] for row in specs] == [row["order"] for row in expected]
    assert [row["parent_request_id"] for row in specs] == [
        row["request_id"] for row in expected]
    assert all(row["request_id"] ==
               row["parent_request_id"] + "__declarative_repair_v1"
               for row in specs)
    assert Counter(row["condition"] for row in specs) == {
        condition: 12 for condition in module.H1_CONDITIONS}
    assert Counter(row["case_id"] for row in specs) == {
        case["case_id"]: 4 for case in load(module.PARENT_CASE_BANK)["cases"]}
    assert not ({row["condition"] for row in specs} & set(module.H0_CONDITIONS))


def test_archived_reuse_indices_bind_all_parent_rows_without_raw_text(monkeypatch):
    monkeypatch.chdir(ROOT)
    parent_audit = load(module.PARENT_AUDIT)
    for conditions in (module.H0_CONDITIONS, module.H1_CONDITIONS):
        index = module.archived_index(conditions)
        expected = [row for row in parent_audit["rows"]
                    if row["condition"] in conditions]
        assert len(index) == len(expected) == 48
        assert all(row["state"] == "COMPLETED" for row in index)
        assert [row["request_id"] for row in index] == [
            row["request_id"] for row in expected]
        assert all(row["raw_text_sha256"] and row["request_sha256"] for row in index)
        assert all("raw_response" not in row for row in index)


def test_factorial_weights_are_complete_centered_and_mutually_orthogonal():
    design = load(module.DESIGN)
    weights = design["estimands"]["repaired_factorial_weights"]
    conditions = [f"C{i}" for i in range(8)]
    assert set(weights) == {"S", "F", "H_DECLARATIVE", "SxF",
                            "SxH_DECLARATIVE", "FxH_DECLARATIVE",
                            "SxFxH_DECLARATIVE"}
    for effect, values in weights.items():
        assert set(values) == set(conditions), effect
        assert sum(values.values()) == pytest.approx(0.0), effect
    effects = list(weights)
    for left_index, left in enumerate(effects):
        for right in effects[left_index + 1:]:
            assert sum(weights[left][condition] * weights[right][condition]
                       for condition in conditions) == pytest.approx(0.0)


def test_added_lexical_diagnostics_are_complete_denominator_only_when_assessable():
    result = {
        "automatic_score": {
            "measurement_state": "ASSESSED_IDENTIFIABLE_UNIT",
            "selection_category": "UNRESOLVED_NO_EXACT_TARGET",
        },
        "response_status": {"first_span": {"text":
            "I recommend the archived target. A reason follows."}},
    }
    score = module._augmented_score(result)
    assert score["selection_resolution"] == 0
    assert score["raw_recommendation_frame_recurrence"] == 1
    result["automatic_score"]["selection_category"] = "CURRENT_A"
    result["response_status"]["first_span"]["text"] = \
        "I recommend Current A. A reason follows."
    score = module._augmented_score(result)
    assert score["selection_resolution"] == 1
    assert score["raw_recommendation_frame_recurrence"] == 0
    result["automatic_score"]["measurement_state"] = "BOUNDARY_CENSORED"
    score = module._augmented_score(result)
    assert score["selection_resolution"] is None
    assert score["raw_recommendation_frame_recurrence"] is None


def test_outdated_endpoint_reports_only_applicable_slots_and_missingness_bounds():
    cases = [f"OUTDATED_{index}" for index in range(4)]
    persona_by_case = {case_id: f"PERSONA_{index}" for index, case_id in enumerate(cases)}
    regime_by_case = {case_id: "OUTDATED_CONFLICTING" for case_id in cases}
    by_case, archived_raw, declarative = {}, {}, {}
    for index, case_id in enumerate(cases):
        by_case[case_id] = {}
        for condition in ("C6", "C7"):
            raw_score = {"outdated_value_adoption": 1,
                         "outdated_value_applicable": True}
            new_value = None if index == 0 and condition == "C6" else 0
            new_score = {"outdated_value_adoption": new_value,
                         "outdated_value_applicable": True}
            archived_raw[(case_id, condition)] = raw_score
            declarative[(case_id, condition)] = new_score
            by_case[case_id][condition] = new_score
    summary = module._outdated_analysis(
        by_case, archived_raw, declarative, persona_by_case, regime_by_case)
    assert summary["eligible_slots"] == 8
    assert summary["inapplicable_slots_included"] == 0
    assert summary["inapplicable_or_missing_recoded_as_zero"] is False
    assert summary["archived_raw_by_condition"]["C6"]["ones"] == 4
    assert summary["declarative_by_condition"]["C6"] == {
        "ones": 0, "zeros": 3, "missing": 1, "total_slots": 4,
        "resolved_denominator": 3, "mean_resolved": 0.0,
        "logical_lower": 0.0, "logical_upper": 0.25}
    effect = summary["declarative_minus_archived_raw"]
    assert effect["eligible_cases"] == 8
    assert effect["complete_cases"] == 7
    assert effect["unresolved_cases"] == 1
    assert effect["complete_case_estimate"] == -1.0
    assert effect["logical_lower"] == -1.0
    assert effect["logical_upper"] == pytest.approx(-0.875)


def test_inventory_reconstructs_complete_and_partial_zero_retry_prefixes():
    rows = [{"request_id": "r0"}, {"request_id": "r1"}]
    plan = {"requests": rows}
    complete = [
        {"kind": module.STARTED, "data": rows[0]},
        {"kind": module.RAW, "data": {"request_id": "r0", "response": {}}},
        {"kind": module.DERIVED, "data": {"request_id": "r0", "score": 1}},
        {"kind": module.STARTED, "data": rows[1]},
        {"kind": module.RAW, "data": {"request_id": "r1", "response": {}}},
        {"kind": module.DERIVED, "data": {"request_id": "r1", "score": 0}},
    ]
    attempted, raw, derived = module.inventory(plan, complete)
    assert attempted == ["r0", "r1"]
    assert list(raw) == list(derived) == attempted
    partial = complete[:4]
    attempted, raw, derived = module.inventory(plan, partial)
    assert attempted == ["r0", "r1"]
    assert list(raw) == list(derived) == ["r0"]
    with pytest.raises(Exception):
        module.inventory(plan, complete + [complete[1]])


def test_audit_reconstructs_new_rows_without_copying_raw_text(monkeypatch):
    plan = {"requests": []}
    row = {"request_id": "repair-r0", "parent_request_id": "parent-r0",
           "request_sha256": "request-sha", "case_id": "CASE", "condition": "C3"}
    score = {"selection_resolution": 1}
    result = {"raw_text_sha256": "raw-sha", "first_reply_sha256": "reply-sha",
              "generated_tokens": 4, "stop_reason": "eos", "latency_seconds": 1.25,
              "automatic_score": score}
    monkeypatch.setattr(module, "load", lambda path: plan if path == module.FROZEN else {})
    monkeypatch.setattr(module, "validate_plan", lambda _plan: {})
    monkeypatch.setattr(module, "replay", lambda: (
        Path("run"), [{"kind": "run_finished"}], [(row, result, "COMPLETED")], 1))
    monkeypatch.setattr(module, "archived_index", lambda conditions: [
        {"request_id": "parent-h0", "condition": conditions[0]}])
    monkeypatch.setattr(module, "sha256", lambda _path: "manifest-sha")
    value = module.audit()
    assert value["integrity_status"] == "PASS"
    assert value["results"] == value["http_responses_verified"] == 1
    assert value["archived_h0_regenerations"] == 0
    assert value["raw_text_embedded"] is False
    assert value["new_h1_rows"][0]["raw_text_sha256"] == "raw-sha"
    assert "raw_response" not in value["new_h1_rows"][0]


def test_combined_analysis_mock_reuses_48_h0_and_reports_temporal_missingness(
        monkeypatch, tmp_path):
    design = load(module.DESIGN)
    bank = load(module.PARENT_CASE_BANK)
    parent_rows, new_rows = [], []

    def base_score(case, condition, declarative=False):
        applicable = (case["history_regime"] == "OUTDATED_CONFLICTING" and
                      condition in ("C6", "C7"))
        outdated = 0 if applicable else None
        if declarative and applicable and condition == "C6" and \
                case["case_id"] == next(item["case_id"] for item in bank["cases"]
                                        if item["history_regime"] ==
                                        "OUTDATED_CONFLICTING"):
            outdated = None
        score = {
            "measurement_state": "ASSESSED_IDENTIFIABLE_UNIT",
            "selection_category": "CURRENT_A",
            "current_named_selection": 1,
            "current_preference_choice": 1,
            "history_target_selection": 0,
            "surface_style_uptake": 1,
            "full_canonical_both": 0,
            "exact_current_note_support": "SUPPORTED",
            "outdated_value_adoption": outdated,
            "outdated_value_applicable": applicable,
        }
        if declarative:
            score.update(selection_resolution=1,
                         raw_recommendation_frame_recurrence=0)
        return score

    def result(score, raw_frame=False):
        return {
            "automatic_score": score,
            "response_status": {"first_span": {"text":
                ("I recommend the archived target. Reason."
                 if raw_frame else "I recommend Current Target. Reason.")}},
            "latency_seconds": 1.0,
            "generated_tokens": 4,
            "stop_reason": "eos",
        }

    for case in bank["cases"]:
        for condition in module.H0_CONDITIONS + module.H1_CONDITIONS:
            row = {"case_id": case["case_id"], "condition": condition,
                   "persona_id": case["persona_id"],
                   "history_regime": case["history_regime"]}
            parent_rows.append((row, result(base_score(case, condition),
                                              condition in module.H1_CONDITIONS),
                                "COMPLETED"))
        for condition in module.H1_CONDITIONS:
            row = {"case_id": case["case_id"], "condition": condition,
                   "persona_id": case["persona_id"],
                   "history_regime": case["history_regime"]}
            new_rows.append((row, result(base_score(case, condition, True)),
                             "COMPLETED"))

    fake_audit = {"audit": "repair"}
    fake_parent_audit = {"audit": "parent"}
    audit_path = tmp_path / "audit.json"
    audit_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(module, "AUDIT", audit_path)
    real_load = module.load

    def fake_load(path):
        path = Path(path)
        if path == module.DESIGN:
            return design
        if path == module.PARENT_CASE_BANK:
            return bank
        if path == module.FROZEN:
            return {"requests": []}
        if path == audit_path:
            return fake_audit
        if path == module.PARENT_AUDIT:
            return fake_parent_audit
        return real_load(path)

    monkeypatch.setattr(module, "load", fake_load)
    monkeypatch.setattr(module, "validate_plan", lambda _plan: {})
    monkeypatch.setattr(module, "audit", lambda: fake_audit)
    monkeypatch.setattr(module.parent, "audit", lambda: fake_parent_audit)
    monkeypatch.setattr(module, "replay", lambda: (
        Path("repair-run"), [], new_rows, len(new_rows)))
    monkeypatch.setattr(module.parent, "replay", lambda: (
        Path("parent-run"), [], parent_rows, len(parent_rows)))
    monkeypatch.setattr(module, "sha256", lambda _path: "sha")
    analysis = module.analyze()
    assert analysis["new_generations"] == 48
    assert analysis["archived_h0_rows_reused"] == 48
    assert analysis["archived_h0_regenerations"] == 0
    assert analysis["combined_factorial_rows"] == 96
    assert analysis["outdated_value_adoption"]["eligible_slots"] == 8
    assert analysis["outdated_value_adoption"][
        "declarative_minus_archived_raw"]["unresolved_cases"] == 1
    assert analysis["inferential_policy"]["p_values"] == "NOT_COMPUTED"
    assert analysis["semantic_and_persona_endpoints"] == \
        "PENDING_GENUINE_BLINDED_HUMAN_REVIEW"


def test_replay_mock_reconstructs_complete_and_partial_journals(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "MAX_ATTEMPTS", 1)
    run_root = tmp_path / "root"
    folder = run_root / "runs" / "run-1"
    folder.mkdir(parents=True)
    monkeypatch.setattr(module, "ROOT", run_root)
    row = {"request_id": "r0", "request_sha256": "request-sha",
           "persona_id": "SYN_REP_F", "input_token_ids": [1, 2],
           "max_new_tokens": 3, "temperature": 0.0, "top_p": 1.0, "seed": 42,
           "stop": [], "cache_prompt": False, "ignore_eos": False}
    plan = {"requests": [row]}
    response = {"content": "mock"}
    derived = {"request_id": "r0", "derived": True}
    summary = {"status": "PASS"}
    claim = {"source_hashes": {}}
    authorization = {"researcher": "Yaxin ZHENG"}
    run_manifest = {"claim": claim, "frozen_manifest": plan,
                    "authorization": authorization}
    events = [
        {"kind": "live_prompt_verified", "data": {"request_id": "r0"}},
        {"kind": module.STARTED, "data": row},
        {"kind": "http_request", "data": {"route": "/completion",
                                              "payload": module.parent.payload(row)}},
        {"kind": "http_response", "data": {"route": "/completion", "status": 200,
            "body_base64": module.base64.b64encode(
                json.dumps(response).encode("utf-8")).decode("ascii")}},
        {"kind": module.RAW, "data": {"request_id": "r0", "response": response,
                                        "latency_seconds": 1.0}},
        {"kind": module.DERIVED, "data": derived},
        {"kind": "run_finished", "data": summary},
    ]
    real_load = module.load

    def fake_load(path):
        path = Path(path)
        if path == module.FROZEN:
            return plan
        if path == run_root / "claim.json":
            return claim
        if path == folder / "manifest.json":
            return run_manifest
        if path == folder / "summary.json":
            return summary
        if path == module.AUTHORIZATION:
            return authorization
        if path == module.PARENT_CASE_BANK:
            return real_load(path)
        raise AssertionError(path)

    monkeypatch.setattr(module, "load", fake_load)
    monkeypatch.setattr(module, "validate_plan", lambda _plan: {})
    monkeypatch.setattr(module, "validate_run_bindings",
                        lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.b, "read_events", lambda _folder: events)
    monkeypatch.setattr(module, "result", lambda *_args, **_kwargs: derived)
    replayed = module.replay()
    assert replayed[0] == folder
    assert replayed[2][0][2] == "COMPLETED"
    assert replayed[3] == 1
    partial_events = [events[0], events[1], events[2],
                      {"kind": "run_finished", "data": {"status": "PARTIAL"}}]
    summary.clear()
    summary.update(status="PARTIAL")
    monkeypatch.setattr(module.b, "read_events", lambda _folder: partial_events)
    replayed = module.replay()
    assert replayed[2][0][1] is None
    assert replayed[2][0][2] == "ATTEMPTED_UNRESOLVED"
    assert replayed[3] == 0


def test_run_mock_exercises_one_pass_live_gate_without_real_model(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "MAX_ATTEMPTS", 1)
    run_root = tmp_path / "run-root"
    run_root.mkdir()
    preflight_path = tmp_path / "preflight.json"
    monkeypatch.setattr(module, "ROOT", run_root)
    monkeypatch.setattr(module, "PREFLIGHT", preflight_path)
    row = {"order": 0, "request_id": "r0", "request_sha256": "request-sha",
           "persona_id": "SYN_REP_F", "input_token_ids": [1, 2], "prompt": "prompt",
           "max_new_tokens": 3, "temperature": 0.0, "top_p": 1.0, "seed": 42,
           "stop": [], "cache_prompt": False, "ignore_eos": False}
    plan = {"requests": [row], "resource_budget": {
        "batch_wall_seconds_ceiling": 60.0,
        "actual_completion_inference_seconds_ceiling": 60.0}}
    authorization = {"researcher": "Yaxin ZHENG"}
    fresh = {"status": "PASS", "manifest_sha256": "manifest",
             "authorization_sha256": "authorization", "design_sha256": "design",
             "case_transform_sha256": "transform",
             "parent_frozen_manifest_sha256": "parent-manifest",
             "parent_execution_audit_sha256": "parent-audit",
             "current_budget_evidence_sha256": "budget", "source_hashes": {},
             "configuration": {}, "server_command": ["mock"], "identity": {"ok": True}}
    preflight_path.write_text(json.dumps(fresh), encoding="utf-8")
    real_load = module.load

    def fake_load(path):
        path = Path(path)
        if path == preflight_path:
            return fresh
        if path == module.FROZEN:
            return plan
        if path == module.AUTHORIZATION:
            return authorization
        if path == module.PARENT_CASE_BANK:
            return real_load(path)
        raise AssertionError(path)

    class Config:
        endpoint = "mock-endpoint"

        @staticmethod
        def as_dict():
            return {}

    class FakeJournal:
        latest = None

        def __init__(self, root, _manifest):
            self.directory = Path(root) / "run-1"
            self.directory.mkdir(parents=True)
            self.events = []
            FakeJournal.latest = self

        def write(self, kind, data):
            self.events.append({"kind": kind, "data": data})

        def finish(self, **summary):
            self.events.append({"kind": "run_finished", "data": summary})

    class FakeServer:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        @staticmethod
        def assert_running():
            return None

    calls = Counter()

    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            self.timeout = 180

        def request(self, route, payload=None):
            calls[route] += 1
            if route == "/props":
                return {}
            if route == "/tokenize":
                return {"tokens": [1, 2]}
            if route == "/completion":
                return {"content": "mock response"}
            raise AssertionError(route)

    monkeypatch.setattr(module, "load", fake_load)
    monkeypatch.setattr(module, "preflight", lambda **_kwargs: fresh)
    monkeypatch.setattr(module.parent, "cfg", lambda _plan: Config())
    monkeypatch.setattr(module.b, "writer_lock", lambda _root: nullcontext())
    monkeypatch.setattr(module.b, "RunJournal", FakeJournal)
    monkeypatch.setattr(module.b, "read_events",
                        lambda _folder: FakeJournal.latest.events)
    monkeypatch.setattr(module.b, "LlamaClient", FakeClient)
    monkeypatch.setattr(module.b, "validate_server_properties",
                        lambda *_args, **_kwargs: {"build_info": "b11573-0f701c882"})
    monkeypatch.setattr(module.s, "Server", FakeServer)
    monkeypatch.setattr(module.subprocess, "check_output", lambda *args, **kwargs:
                        "research/autonomous-personaslm\n"
                        if "branch" in args[0] else "")
    monkeypatch.setattr(module, "result", lambda row, *_args, **_kwargs:
                        {"request_id": row["request_id"], "mock": True})
    summary = module.run(preflight_path)
    assert summary["status"] == "PASS"
    assert summary["attempted"] == summary["responses_received"] == \
        summary["results"] == 1
    assert summary["retries"] == summary["archived_h0_regenerations"] == 0
    assert calls["/tokenize"] == calls["/completion"] == 1
    assert calls["/props"] == 2


def test_authorization_requirements_bind_exact_budget_sources_and_code(monkeypatch):
    monkeypatch.chdir(ROOT)
    required = module.authorization_requirements()
    assert required["maximum_native_tokenizer_calls"] == 48
    assert required["maximum_live_server_tokenizer_checks"] == 48
    assert required["maximum_generation_attempts"] == 48
    assert required["retries"] == required["hidden_warmups"] == 0
    assert required["minimum_available_physical_ram_bytes"] == 3 * 1024 ** 3
    assert required["global_baseline"] == {
        "generations_limit": 1200,
        "generations_used": 292,
        "inference_seconds_limit": 72000,
        "inference_seconds_used": pytest.approx(1701.0952766999717),
    }
    assert required["design"]["sha256"] == module.DESIGN_SHA
    assert required["case_transform"]["sha256"] == module.CASE_TRANSFORM_SHA
    for path, digest in required["source_hashes"].items():
        assert module.sha256(ROOT / path) == digest
    assert "must not be regenerated" in required["scope"]


def test_nonoperational_actions_do_not_touch_tokenizer_or_model(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)

    original_run = module.subprocess.run

    def guarded_run(*args, **kwargs):
        command = args[0] if args else kwargs.get("args", [])
        if command and "llama-tokenize" in str(command[0]).casefold():
            raise AssertionError("native tokenizer operation was attempted")
        return original_run(*args, **kwargs)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("tokenizer/model operation was attempted")

    monkeypatch.setattr(module.subprocess, "run", guarded_run)
    monkeypatch.setattr(module.s, "Server", forbidden)
    monkeypatch.setattr(module.b, "LlamaClient", forbidden)
    assert module.main(["validate"]) == 0
    assert module.main(["materialization-summary"]) == 0
    captured = capsys.readouterr().out
    assert "PASS_PROSPECTIVE_NOT_AUTHORIZED_NOT_EXECUTED" in captured
    assert "new_model_generations" in captured


def test_human_semantics_novelty_and_inference_boundaries_are_explicit():
    design = load(module.DESIGN)
    measurement = design["registered_measurement"]
    assert measurement["human_only_endpoints"] == [
        "semantic response relevance",
        "semantic factual support",
        "conversational coherence",
        "broad linguistic Persona Fidelity",
        "behavioral Persona Fidelity",
        "semantic answer completeness",
    ]
    assert "No AI-generated" in measurement["human_label_policy"]
    assert "Never recode" in measurement["missingness"]
    assert design["estimands"]["inference"].startswith("No p-values")
    forbidden = set(design["output_informed_status"]["forbidden_claims"])
    assert {"independent validation", "algorithmic novelty", "validated algorithm",
            "broad Persona Fidelity"} <= forbidden
