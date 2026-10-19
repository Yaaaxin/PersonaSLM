import ast
import json
from pathlib import Path
import socket
import subprocess
import sys
import urllib.request

import pytest


sys.path.insert(0, str(Path("tools").resolve()))

import p1_persona_dialogue_disjoint_surface_validation_v3_reproduce as v1
import p1_persona_dialogue_disjoint_surface_validation_v3_reproduce_v2 as reproduction


ARTIFACT = Path(
    "docs/validation/p1/persona_dialogue_disjoint_surface_validation_v3/analysis_reproduction_v2.json"
)
SCRIPT = Path("tools/p1_persona_dialogue_disjoint_surface_validation_v3_reproduce_v2.py")


@pytest.fixture(scope="module")
def report():
    return reproduction.build_report()


def test_v2_imports_no_controller_or_execution_library():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert "p1_persona_dialogue_disjoint_surface_validation_v3" not in imports
    assert imports.isdisjoint({"requests", "subprocess", "urllib", "urllib.request", "socket"})


def test_v1_receipt_script_and_test_remain_byte_identical():
    assert v1._sha256(reproduction.V1_RECEIPT) == reproduction.V1_RECEIPT_SHA256
    assert v1._sha256(Path(v1.__file__)) == reproduction.V1_SCRIPT_SHA256
    assert v1._sha256(v1.TEST_PATH) == reproduction.V1_TEST_SHA256


def test_saved_v2_receipt_matches_fresh_raw_reconstruction(report):
    assert json.loads(ARTIFACT.read_text(encoding="utf-8")) == report
    assert report["analysis_reproducibility_decision"]["decision"] == "GO"
    assert report["execution_impact"]["model_calls"] == 0
    assert report["execution_impact"]["new_generations"] == 0
    assert report["analysis_code"]["controller_imported"] is False
    assert report["analysis_code"]["archived_analyze_called"] is False


def test_v2_only_corrects_post_hoc_scope_and_keeps_registered_results(report):
    prior = json.loads((v1.PROJECT_ROOT / reproduction.V1_RECEIPT).read_text(encoding="utf-8"))
    correction = report["append_only_correction"]
    assert correction["classification"] == (
        "APPEND_ONLY_POST_HOC_DENOMINATOR_SCOPE_CORRECTION"
    )
    assert correction["registered_estimands_changed"] is False
    assert correction["condition_summaries_changed"] is False
    assert correction["resource_or_budget_accounting_changed"] is False
    assert correction["v1_observation_disposition"]["v1_numerator"] == 23
    assert correction["v1_observation_disposition"]["v1_denominator"] == 23
    assert correction["v1_observation_disposition"]["status"] == (
        "FACTUALLY_TRUE_BUT_DIFFERENT_DENOMINATOR_NOT_USED_FOR_CORRECTED_CLAIM"
    )
    for field in (
        "hash_verification",
        "journal_and_slot_accounting",
        "score_reconstruction",
        "condition_summary",
        "registered_automatic_estimates",
        "task_family_strata",
        "resources",
        "cumulative_authorization_after",
    ):
        assert report[field] == prior[field]


def test_corrected_placeholder_subset_has_exact_source_bytes_and_denominators(report):
    audit = report["post_hoc_exploratory_audit"]
    assert audit["classification"] == (
        "POST_HOC_EXPLORATORY_NOT_PREREGISTERED_NOT_CONFIRMATORY"
    )
    placeholder = audit["literal_anchor_placeholder_subset"]
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
    assert (placeholder["hits"], placeholder["history_conditioned_denominator"]) == (
        24,
        144,
    )
    assert placeholder["selection_category_distribution"] == {
        "CURRENT_PREFERRED": 1,
        "NONE": 23,
    }
    assert placeholder["scorer_none_count"] == 23
    none = placeholder["scorer_none_subset"]
    assert none["preferred_canonical_name"]["denominator"] == 23
    assert none["preferred_canonical_name"]["hits_in_first_sentence"] == 23
    assert none["preferred_canonical_name"]["hits_in_full_response"] == 23
    assert none["nonpreferred_canonical_name"]["denominator"] == 23
    assert none["nonpreferred_canonical_name"]["hits_in_first_sentence"] == 0
    assert none["nonpreferred_canonical_name"]["hits_in_full_response"] == 0
    all_rows = placeholder["all_placeholder_rows"]
    assert all_rows["preferred_canonical_name"]["hits_in_first_sentence"] == 24
    assert all_rows["nonpreferred_canonical_name"]["hits_in_first_sentence"] == 0
    assert placeholder["current_preferred_request_ids"] == [
        "dsv3_097_DSV2_CASE_014_LEON_PLAN_SFH_ALIGNED_DECLARATIVE"
    ]


def test_nonpreferred_post_hoc_concentration_is_unchanged(report):
    audit = report["post_hoc_exploratory_audit"]
    nonpreferred = audit["current_nonpreferred_selection_concentration"]
    assert nonpreferred["count"] == 8
    assert nonpreferred["persona_distribution"] == {"DSV_P02": 8}
    assert nonpreferred["case_distribution"] == {
        "DSV2_CASE_002_JALEN_SUPPORT": 5,
        "DSV2_CASE_010_JALEN_ROUTINE": 3,
    }


def test_v2_reconstruction_has_no_network_or_process_side_effect(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Network or process execution is forbidden")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    assert reproduction.build_report()["execution_impact"]["model_calls"] == 0


def test_v2_receipt_writer_remains_exclusive(tmp_path):
    path = tmp_path / "receipt.json"
    v1._write_exclusive(path, {"status": "first"})
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        v1._write_exclusive(path, {"status": "replacement"})
    assert path.read_bytes() == original
