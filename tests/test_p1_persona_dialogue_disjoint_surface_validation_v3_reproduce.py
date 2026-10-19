import ast
from collections import Counter
import copy
import json
from pathlib import Path
import socket
import subprocess
import sys
import urllib.request

import pytest


sys.path.insert(0, str(Path("tools").resolve()))

import p1_persona_dialogue_disjoint_surface_validation_v3_reproduce as reproduction


ARTIFACT = Path(
    "docs/validation/p1/persona_dialogue_disjoint_surface_validation_v3/analysis_reproduction_v1.json"
)
SCRIPT = Path("tools/p1_persona_dialogue_disjoint_surface_validation_v3_reproduce.py")


@pytest.fixture(scope="module")
def report():
    return reproduction.build_report()


def test_script_is_controller_independent_and_has_no_execution_imports():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert not any(
        name.endswith("p1_persona_dialogue_disjoint_surface_validation_v3")
        for name in imports
    )
    assert imports.isdisjoint({"requests", "subprocess", "urllib", "urllib.request", "socket"})


def test_saved_receipt_exactly_matches_fresh_raw_journal_reconstruction(report):
    assert json.loads(ARTIFACT.read_text(encoding="utf-8")) == report
    assert report["status"] == "PASS_ZERO_DIFFERENCES"
    assert report["analysis_code"]["controller_imported"] is False
    assert report["analysis_code"]["archived_analyze_called"] is False
    assert report["execution_impact"] == {
        "model_calls": 0,
        "new_generations": 0,
        "network_calls": 0,
        "human_labels_created": 0,
        "historical_evidence_modified": False,
    }


def test_hash_chain_slot_and_source_accounting_are_exact(report):
    integrity = report["hash_verification"]
    assert integrity["status"] == "PASS_ZERO_HASH_DIFFERENCES"
    assert integrity["tokenizer_dll_hashes_verified"] == 29
    assert integrity["registration_source_hashes_verified_current"] == 35
    assert integrity["registration_source_hashes_verified_snapshot"] == 35
    assert integrity["native_tokenizer_log_hashes_verified"] == 168
    assert integrity["bound_files"]["model"]["sha256"] == (
        "0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc"
    )
    assert integrity["bound_files"]["backend"]["sha256"] == (
        "71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846"
    )
    assert integrity["bound_files"]["chat_template"]["sha256"] == (
        "0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6"
    )
    accounting = report["journal_and_slot_accounting"]
    assert accounting["journal_events"] == 1557
    assert accounting["journal_hash_chain"] == "PASS"
    assert accounting["planned_slots"] == 168
    assert accounting["started"] == accounting["raw_generations"] == 168
    assert accounting["derived_results"] == accounting["live_tokenizer_checks"] == 168
    assert accounting["completion_http_200_bodies_matching_raw_events"] == 168
    assert accounting["native_tokenizer_calls"] == 168
    assert accounting["total_tokenizer_operations"] == 336
    assert accounting["retries"] == accounting["hidden_warmups"] == 0


def test_journal_verifier_rejects_data_gap_and_previous_hash_tampering():
    run = reproduction.PROJECT_ROOT / reproduction.RUN_RELATIVE
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    records = [
        (path.name, json.loads(path.read_text(encoding="utf-8")))
        for path in sorted((run / "events").glob("*.json"))
    ]
    assert len(reproduction._verify_journal_records(manifest, records)) == 1557

    changed_data = copy.deepcopy(records)
    changed_data[10][1]["data"]["tampered"] = True
    with pytest.raises(ValueError, match="Bad event hash"):
        reproduction._verify_journal_records(manifest, changed_data)

    missing_middle = copy.deepcopy(records)
    del missing_middle[10]
    with pytest.raises(ValueError, match="Journal gap"):
        reproduction._verify_journal_records(manifest, missing_middle)

    changed_previous = copy.deepcopy(records)
    changed_previous[10][1]["previous_hash"] = "0" * 64
    with pytest.raises(ValueError, match="Bad chain"):
        reproduction._verify_journal_records(manifest, changed_previous)


def _scorer_fixture(text, selected, category, preferred, any_current, count, exact=0):
    started = {
        "request_id": "fixture",
        "case_id": "case",
        "persona_id": "persona",
        "task_family": "family",
        "arm": "SF_NO_H",
        "anchors": {
            "current": {"A": "XA", "B": "XB"},
            "history": {"aligned": "XH1", "conflict": "XH2", "irrelevant": "XH3"},
        },
        "preferred_option": "A",
        "options": {"A": {"canonical": "Alpha"}, "B": {"canonical": "Beta"}},
    }
    raw = {
        "latency_seconds": 1.0,
        "response": {
            "content": text,
            "truncated": False,
            "tokens_predicted": 1,
            "stop_type": "eos",
        },
    }
    unresolved = int(category in {"NONE", "MULTIPLE"})
    archived = {
        "automatic_score": {
            "preferred_current_anchor_selection": preferred,
            "any_current_anchor_selection": any_current,
            "selection_category": category,
            "exact_current_label_name_consistency": exact,
            "first_sentence_anchor_count": count,
            "unresolved_or_multiple": unresolved,
            "selected_anchor": {"A": "XA", "B": "XB"}.get(selected),
            "selected_identity": selected,
            "selected_scope": "CURRENT" if selected in {"A", "B"} else None,
        }
    }
    return reproduction._rescore(started, raw, archived)


@pytest.mark.parametrize(
    "text,selected,category,preferred,any_current,count,exact",
    [
        ("Option A [XA] — Alpha.", "A", "CURRENT_PREFERRED", 1, 1, 1, 1),
        ("Option B [XB] — Beta.", "B", "CURRENT_NONPREFERRED", 0, 1, 1, 1),
        ("No anchor here.", None, "NONE", 0, 0, 0, 0),
        ("Both [XA] and [XB].", None, "MULTIPLE", 0, 0, 2, 0),
        ("No choice. Option A [XA] — Alpha.", None, "NONE", 0, 0, 0, 0),
        ("Alpha is best.", None, "NONE", 0, 0, 0, 0),
        ("Option A [<exact A anchor>] — Alpha.", None, "NONE", 0, 0, 0, 0),
    ],
)
def test_raw_first_sentence_scorer_boundaries(
    text, selected, category, preferred, any_current, count, exact
):
    row = _scorer_fixture(
        text, selected, category, preferred, any_current, count, exact
    )
    assert row["selected_identity"] == selected
    assert row["selection_category"] == category


def test_all_fourteen_registered_points_and_sensitivity_are_independently_fixed(report):
    expected = {
        "theta_A": (1 / 24, 1 / 24),
        "theta_C": (1 / 48, 1 / 24),
        "theta_surface": (0.0, 1 / 72),
        "theta_generic_history": (-3 / 16, -3 / 16),
        "derived_theta_A_minus_theta_C": (1 / 48, 0.0),
        "interaction_surface_aligned_minus_irrelevant": (1 / 12, 1 / 12),
        "interaction_surface_conflict_minus_irrelevant": (1 / 24, 1 / 12),
    }
    estimates = report["registered_automatic_estimates"]
    for name, (preferred, any_current) in expected.items():
        assert estimates[name]["preferred_current_anchor_selection"]["estimate"] == pytest.approx(
            preferred, abs=1e-15
        )
        assert estimates[name]["any_current_anchor_selection"]["estimate"] == pytest.approx(
            any_current, abs=1e-15
        )
        for metric in reproduction.PRIMARY_METRICS:
            result = estimates[name][metric]
            assert result["complete_cases"] == 24
            assert result["unresolved_cases"] == 0
            assert result["logical_bounds"] == pytest.approx(
                [result["estimate"], result["estimate"]], abs=1e-15
            )
            assert len(result["leave_one_persona_out_point_estimate_range"]) == 2

    assert set(report["task_family_strata"]) == {
        "COLLABORATIVE_PLANNING",
        "ROUTINE_NEGOTIATION",
        "SUPPORTIVE_REPLY",
    }
    for family in report["task_family_strata"].values():
        for estimand in family.values():
            for metric in estimand.values():
                assert metric["complete_cases"] == 8
                assert metric["unresolved_cases"] == 0


def test_missing_binary_outcome_is_bounded_and_not_recoded_as_zero():
    rows = [
        {"case_id": "c1", "persona_id": "p1", "arm": "A", "m": 1},
        {"case_id": "c1", "persona_id": "p1", "arm": "B", "m": 0},
        {"case_id": "c2", "persona_id": "p2", "arm": "A", "m": None},
        {"case_id": "c2", "persona_id": "p2", "arm": "B", "m": 1},
    ]
    result = reproduction._estimate(rows, {"A": 1.0, "B": -1.0}, "m")
    assert result["complete_cases"] == 1
    assert result["unresolved_cases"] == 1
    assert result["complete_case_estimate"] == 1.0
    assert result["logical_lower"] == 0.0
    assert result["logical_upper"] == 0.5


def test_post_hoc_exploratory_findings_are_explicitly_separated_and_byte_defined(report):
    audit = report["post_hoc_exploratory_audit"]
    assert audit["classification"] == (
        "POST_HOC_EXPLORATORY_NOT_PREREGISTERED_NOT_CONFIRMATORY"
    )
    assert audit["separation_from_registered_estimands"] is True
    placeholder = audit["literal_anchor_placeholder_in_history_conditioned_outputs"]
    assert placeholder["source_event_kind"] == (
        "disjoint_surface_validation_v3_raw_generation"
    )
    assert placeholder["source_decoded_field"] == "event.data.response.content"
    assert placeholder["counting_stage"] == "AFTER_JSON_LOADS_ON_DECODED_UNICODE_TEXT"
    assert placeholder["escaped_json_representation_scanned"] is False
    assert placeholder["case_sensitive_regex"] == r"<exact [AB] anchor>"
    assert placeholder["exact_utf8_literal_hex"] == {
        "<exact A anchor>": "3c6578616374204120616e63686f723e",
        "<exact B anchor>": "3c6578616374204220616e63686f723e",
    }
    assert (placeholder["hits"], placeholder["denominator"]) == (24, 144)
    assert placeholder["any_decoded_less_than_exact_substring_outputs"] == 28
    assert placeholder["arm_distribution"] == {
        "SFH_ALIGNED_DECLARATIVE": 4,
        "SFH_ALIGNED_RAW": 4,
        "SFH_CONFLICT_DECLARATIVE": 3,
        "SFH_CONFLICT_RAW": 4,
        "SFH_IRRELEVANT_DECLARATIVE": 5,
        "SFH_IRRELEVANT_RAW": 4,
    }
    preferred_name = audit[
        "no_history_preferred_anchor_with_preferred_name_in_first_sentence"
    ]
    assert (preferred_name["hits"], preferred_name["denominator"]) == (23, 23)
    nonpreferred = audit["current_nonpreferred_selection_concentration"]
    assert nonpreferred["count"] == 8
    assert nonpreferred["persona_distribution"] == {"DSV_P02": 8}
    assert nonpreferred["case_distribution"] == {
        "DSV2_CASE_002_JALEN_SUPPORT": 5,
        "DSV2_CASE_010_JALEN_ROUTINE": 3,
    }


def test_condition_resource_and_cumulative_budget_reconstruction(report):
    conditions = report["condition_summary"]
    categories = sum(
        (Counter(value["selection_categories"]) for value in conditions.values()),
        Counter(),
    )
    assert categories == Counter(
        {"CURRENT_PREFERRED": 137, "CURRENT_NONPREFERRED": 8, "NONE": 23}
    )
    assert sum(
        value["preferred_current_anchor_selection"]["ones"]
        for value in conditions.values()
    ) == 137
    assert sum(
        value["any_current_anchor_selection"]["ones"] for value in conditions.values()
    ) == 145
    resources = report["resources"]
    assert resources == {
        "generated_tokens": 8691,
        "inference_wall_seconds": 1203.5250847999923,
        "mean_response_latency_seconds": 7.163839790476144,
        "batch_wall_seconds": 1242.346822200001,
        "native_stop_reason_distribution": {"eos": 168},
        "server_peak_working_set_bytes": 3591196672,
        "minimum_observed_available_physical_bytes": 289243136,
    }
    assert report["cumulative_authorization_after"] == {
        "generations_used": 508,
        "generations_limit": 1200,
        "generations_remaining": 692,
        "inference_seconds_used": 3171.544608799969,
        "inference_seconds_limit": 72000,
        "inference_seconds_remaining": 68828.45539120003,
    }


def test_reconstruction_has_no_network_or_process_side_effect(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Network or process execution is forbidden")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    assert reproduction.build_report()["execution_impact"]["model_calls"] == 0


def test_receipt_writer_is_exclusive_and_preserves_existing_content(tmp_path):
    path = tmp_path / "receipt.json"
    reproduction._write_exclusive(path, {"status": "first"})
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        reproduction._write_exclusive(path, {"status": "replacement"})
    assert path.read_bytes() == original
