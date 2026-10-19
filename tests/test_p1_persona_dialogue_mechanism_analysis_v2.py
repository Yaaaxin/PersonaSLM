import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "persona_dialogue_mechanism_analysis_v2",
    ROOT / "tools/p1_persona_dialogue_mechanism_analysis_v2.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture():
    return {
        "version": "test_only",
        "primary_arm_summary": {
            "A": {"selection_categories": {None: 2, "CURRENT_A": 1},
                  "scientific_missing_value": None},
            "B": {"selection_categories": {"CURRENT_B": 3}},
        },
        "secondary_only_not_in_primary_effects": {
            "A": {"reason_support_distribution": {None: 2, "SUPPORTED": 1},
                  "task_success": {"mean_resolved": None}},
            "B": {"reason_support_distribution": {"UNRESOLVED": 3}},
        },
        "unrelated": {"missing_value_must_remain_null": None},
    }


def test_sanitizer_changes_only_the_two_authorized_counter_keys():
    original = fixture()
    preserved = copy.deepcopy(original)
    fixed, migrations = MODULE.sanitize_analysis(original)
    expected = copy.deepcopy(original)
    expected["primary_arm_summary"]["A"]["selection_categories"] = {
        "BOUNDARY_CENSORED": 2, "CURRENT_A": 1}
    expected["secondary_only_not_in_primary_effects"]["A"][
        "reason_support_distribution"] = {"BOUNDARY_CENSORED": 2, "SUPPORTED": 1}
    assert original == preserved
    assert fixed == expected
    assert migrations == {
        "primary_arm_summary": {"A": 2},
        "secondary_only_not_in_primary_effects": {"A": 2},
    }
    assert fixed["unrelated"]["missing_value_must_remain_null"] is None
    assert fixed["primary_arm_summary"]["A"]["scientific_missing_value"] is None
    json.dumps(fixed, sort_keys=True)


def test_sanitizer_rejects_a_preexisting_boundary_label_collision():
    value = fixture()
    value["primary_arm_summary"]["A"]["selection_categories"][
        "BOUNDARY_CENSORED"] = 9
    with pytest.raises(RuntimeError, match="ambiguous key merge"):
        MODULE.sanitize_analysis(value)


def test_sanitizer_is_a_noop_when_no_null_counter_keys_exist():
    value = fixture()
    value["primary_arm_summary"]["A"]["selection_categories"].pop(None)
    value["secondary_only_not_in_primary_effects"]["A"][
        "reason_support_distribution"].pop(None)
    fixed, migrations = MODULE.sanitize_analysis(value)
    assert fixed == value
    assert migrations == {
        "primary_arm_summary": {},
        "secondary_only_not_in_primary_effects": {},
    }


def test_exclusive_writer_never_replaces_an_existing_result(tmp_path):
    output = tmp_path / "analysis_v2.json"
    fixed, _ = MODULE.sanitize_analysis(fixture())
    MODULE.write_exclusive(output, fixed)
    before = output.read_bytes()
    assert json.loads(before) == fixed
    assert not list(tmp_path.glob(".*.tmp"))
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        MODULE.write_exclusive(output, {"changed": True})
    assert output.read_bytes() == before


def test_authorization_validator_binds_code_evidence_mapping_and_output(tmp_path):
    authorization = MODULE.authorization_requirements()
    authorization.update({"researcher": "Yaxin ZHENG", "authorized_utc": "TEST_ONLY"})
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps(authorization), encoding="utf-8")
    assert MODULE.validate_authorization(path, MODULE.EXPECTED_OUTPUT) == authorization

    tampered = copy.deepcopy(authorization)
    tampered["permitted_key_mapping"]["target_key"] = "UNAUTHORIZED"
    path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(RuntimeError, match="authorization changed"):
        MODULE.validate_authorization(path, MODULE.EXPECTED_OUTPUT)

    path.write_text(json.dumps(authorization), encoding="utf-8")
    with pytest.raises(RuntimeError, match="output path"):
        MODULE.validate_authorization(path, tmp_path / "wrong.json")
