import ast
import json
from pathlib import Path
import sys
import tempfile

import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools/real_persona_chat_style_signal_v1_reproduce.py"
ARTIFACT = (
    REPO
    / "docs/validation/p1/real_persona_chat_style_signal_v1/analysis_reproduction_v1.json"
)
sys.path.insert(0, str(REPO / "tools"))
import real_persona_chat_style_signal_v1_reproduce as reproduction


@pytest.fixture(scope="module")
def receipt():
    return reproduction.build_receipt()


def test_reproducer_does_not_import_original_analysis_or_intake_controller():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert "real_persona_chat_style_signal_v1" not in imports
    assert "real_persona_chat_intake" not in imports


def test_saved_receipt_matches_fresh_raw_recomputation(receipt):
    assert json.loads(ARTIFACT.read_text(encoding="utf-8")) == receipt
    assert receipt["status"] == (
        "PASS_EXACT_REPRODUCTION_WITH_CHRONOLOGY_LIMITATION"
    )
    assert receipt["verification"]["differences"] == {
        "source": [],
        "registration": [],
        "analysis": [],
    }


def test_exact_frozen_aggregate_values_and_case_hash_reproduce(receipt):
    result = receipt["recomputed"]
    assert result["speaker_units_resolved"] == 76
    assert result["primary"] == {
        "mean_control_percentile_rank": 0.7445236924129356,
        "mean_margin": 0.2004762421353434,
        "mean_other_median_distance": 0.9366385774716032,
        "mean_own_distance": 0.7361623353362599,
        "median_margin": 0.188481584199998,
        "own_closer_than_other_median_proportion": 0.7894736842105263,
        "q25_margin": 0.05966708252430322,
        "q75_margin": 0.3690734047476696,
    }
    assert result["influence"] == {
        "leave_one_speaker_out_mean_margin_max": 0.2050844751282807,
        "leave_one_speaker_out_mean_margin_min": 0.19302901306707262,
    }
    assert result["case_level_values_sha256"] == (
        "6c7081d747d4f39e05729578d262b1de3263e07aa52d1d3a6c949358ca55c4d8"
    )


def test_receipt_emits_no_private_or_row_level_material(receipt):
    privacy = receipt["independence_and_privacy"]
    assert privacy["participant_text_emitted"] is False
    assert privacy["speaker_ids_emitted"] is False
    assert privacy["row_level_results_emitted"] is False
    assert privacy["scientific_report_used_as_numerical_input"] is False
    assert privacy["exploratory_or_validation_dialogue_text_used_for_features"] is False
    assert "margins" not in receipt["recomputed"]
    assert "percentiles" not in receipt["recomputed"]


def test_selected_profile_timestamps_are_parseable_and_strictly_ordered(receipt):
    assert receipt["selected_profile_time_audit"] == {
        "selected_speaker_profiles": 76,
        "selected_speaker_dialogue_records": 304,
        "records_with_parseable_iso_chronology_key": 302,
        "records_with_nat_only_timestamps": 2,
        "records_with_nat_only_timestamps_by_profile_side": {
            "source": 0,
            "target": 2,
        },
        "profiles_with_at_least_one_nat_only_record": 2,
        "records_with_unparseable_chronology_key": 0,
        "profiles_with_all_four_parseable_chronology_keys": 74,
        "profiles_with_strict_source_max_before_target_min": 74,
    }
    assert receipt["verification"][
        "selected_profile_chronology_fully_timestamp_verified"
    ] is False
    assert receipt["runtime"]["python_version"]
    assert receipt["runtime"]["unicodedata_version"]
    assert len(receipt["inputs"]["intake_controller_sha256"]) == 64


def test_receipt_writer_refuses_overwrite():
    with tempfile.TemporaryDirectory(dir=REPO / "results") as directory:
        target = Path(directory) / "receipt.json"
        reproduction._write_exclusive(target, {"status": "first"})
        original = target.read_bytes()
        with pytest.raises(FileExistsError):
            reproduction._write_exclusive(target, {"status": "second"})
        assert target.read_bytes() == original
