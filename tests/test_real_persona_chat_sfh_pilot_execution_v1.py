import importlib.util
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "rpc_sfh_execution_v1", TOOLS / "real_persona_chat_sfh_pilot_execution_v1.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_text_normalization_and_set_character_trigram_f1():
    assert MODULE.normalize_text(" Ａ B\n。") == "ab。"
    assert MODULE.character_trigram_f1("短", "これは十分に長い参照です") == 0.0
    assert MODULE.character_trigram_f1("abcdef", "abcdef") == 1.0
    assert MODULE.character_trigram_f1("abcxxx", "abcdef") < 1.0


def test_copying_uses_unique_generated_trigrams_and_max_unit_lcs():
    score = MODULE.copying_scores("abcdef", ["abczzz", "yyydef"])
    assert score["trigram_precision"] == 0.5
    assert score["lcs_ratio"] == 0.5
    assert MODULE.copying_scores("短", ["短い"])["trigram_precision"] == 0.0
    assert MODULE.copying_scores("", ["anything"]) == {
        "trigram_precision": 0.0, "lcs_ratio": 0.0}


def test_style_distance_has_six_equal_weight_response_observable_coordinates():
    text = "これは丁寧です。"
    observed = MODULE.style_signal.style_vector([{"turns": [text]}])
    case = {"style_features": {
        "mean_turn_length_characters": observed["mean_turn_length"] * 50,
        **{name: observed[name] for name in MODULE.STYLE_FEATURES
           if name != "mean_turn_length"},
    }}
    assert MODULE.source_style_distance(text, case) == 0.0
    assert "sd_turn_length" not in MODULE.STYLE_FEATURES


def test_successful_empty_response_uses_frozen_mixed_zero_missingness():
    score = MODULE.score_text("", {}, False)
    assert score["structural_response_validity"] == 0
    assert score["output_length_characters"] == 0
    assert score["reference_character_trigram_f1"] == 0.0
    assert score["japanese_script_rate"] is None
    assert score["source_style_distance"] is None
    for source in MODULE.COPY_SOURCES:
        assert score[f"copy_{source}_trigram_precision"] == 0.0
        assert score[f"copy_{source}_lcs_ratio"] == 0.0


def test_native_failure_is_structural_zero_and_text_outcomes_missing():
    score = MODULE.native_failure_score()
    assert score["structural_response_validity"] == 0
    assert all(value is None for key, value in score.items()
               if key != "structural_response_validity")


def test_exposed_prompt_section_label_is_not_structurally_valid():
    assert (MODULE.SCORER_SPECIFICATION["exposed_prompt_section_labels"] ==
            list(MODULE.EXPOSED_PROMPT_LABELS))
    boundary = {"unit_identifiable": True, "status": "AMBIGUOUS",
                "first_span": {"text": "[人物情報]\nこれは返答です。"}}
    assert MODULE.assessability(boundary) is False


def test_all_latent_sources_are_scored_irrespective_of_condition_bits():
    case = {
        "style_profile": "abc style",
        "style_features": {
            "mean_turn_length_characters": 10,
            "question_turn_rate": 0, "exclamation_turn_rate": 0,
            "ellipsis_turn_rate": 0, "laughter_turn_rate": 0,
            "polite_ending_rate": 0,
        },
        "facts": ["abc fact"],
        "history": [{"text": "abc history"}],
        "query": {"text": "abc query"},
        "reference": {"text": "これは十分に長い参照応答です"},
    }
    score = MODULE.score_text("abc response", case, True)
    for source in MODULE.COPY_SOURCES:
        assert f"copy_{source}_trigram_precision" in score
        assert f"copy_{source}_lcs_ratio" in score


def _scheduled_material():
    rows = []
    order = 0
    for block, masks in MODULE.XOR_MASKS.items():
        for case_index, mask in enumerate(masks):
            case_id = f"{block}_CASE_{case_index}"
            for position in range(8):
                rows.append({"order": order, "request_id": f"R{order:03d}",
                             "block": block, "case_id": case_id,
                             "condition": f"C{position ^ mask}"})
                order += 1
    return {"requests": rows}


def test_xor_schedule_balances_condition_and_factors_by_position():
    result = MODULE._validate_xor_schedule(_scheduled_material())
    assert result["schedule"] == "XOR_LATIN_8X8"
    assert result["every_condition_each_position"] is True
    assert result["factor_balance_within_block_position"] is True


def test_xor_schedule_rejects_fixed_c0_to_c7_order():
    material = _scheduled_material()
    for row in material["requests"]:
        row["condition"] = f"C{row['order'] % 8}"
    try:
        MODULE._validate_xor_schedule(material)
    except ValueError as exc:
        assert "XOR schedule" in str(exc)
    else:
        raise AssertionError("Fixed condition order must be rejected")


def test_hadamard_effect_signs_and_scaling():
    values = {}
    for condition, bits in MODULE.CONDITIONS.items():
        z_s, z_f, z_h = (2 * bits[name] - 1 for name in ("S", "F", "H"))
        values[condition] = (10 + 1.5 * z_s - 1.0 * z_f + 0.25 * z_h +
                             0.5 * z_s * z_f - 0.75 * z_s * z_h +
                             1.0 * z_f * z_h + 0.25 * z_s * z_f * z_h)
    expected = {"S": 3.0, "F": -2.0, "H": 0.5, "SF": 1.0,
                "SH": -1.5, "FH": 2.0, "SFH": 0.5}
    for name, factors in MODULE.FACTORS.items():
        assert abs(MODULE._factor_effect(values, factors) - expected[name]) < 1e-12


def test_inventory_counts_failed_started_request_as_attempt():
    plan = {"requests": [{"request_id": "R0"}, {"request_id": "R1"}]}
    events = [{"kind": MODULE.STARTED, "data": plan["requests"][0]}]
    attempted, raw, derived = MODULE.inventory(plan, events)
    assert attempted == ["R0"]
    assert raw == derived == {}


def test_public_estimates_do_not_emit_case_ids_or_row_values():
    rows = []
    for case_index in range(8):
        for condition, bits in MODULE.CONDITIONS.items():
            score = {metric: float(bits["S"]) for metric in MODULE.AUTOMATIC_METRICS}
            rows.append({"case_id": f"SECRET_CASE_{case_index}",
                         "condition": condition, "automatic_score": score})
    conditions, effects, private = MODULE._public_estimates(rows)
    rendered = json.dumps({"conditions": conditions, "effects": effects})
    assert "SECRET_CASE" not in rendered
    assert private["structural_response_validity"]["S"] == [1.0] * 8
    assert effects["structural_response_validity"]["S"]["mean"] == 1.0


def test_frozen_material_receipt_exactly_binds_xor_fields_without_execution():
    _, receipt, material, schedule = MODULE.validate_materials()
    assert schedule["schedule"] == "XOR_LATIN_8X8"
    assert receipt["private_material_sha256"] == MODULE.sha256(MODULE.PRIVATE_MATERIAL)
    assert material["status"] == "PRIVATE_MATERIALS_FROZEN_NO_INFERENCE"
    assert receipt["execution"] == {
        "model": "PENDING_SEPARATE_PROSPECTIVE_EXECUTION_AMENDMENT",
        "tokenization": "NOT_RUN", "preflight": "NOT_RUN",
        "server_launches": 0, "generations": 0}


def test_human_semantic_review_is_an_empty_pending_structure_not_score_zero():
    assert MODULE.pending_human_review() == {
        "status": "PENDING_NOT_COLLECTED", "rating_count": 0, "ratings": []}


def test_style_validity_is_bound_as_interpretive_not_execution_gate():
    binding = MODULE.style_validity_binding()
    assert binding["role"] == "INTERPRETIVE_PROVENANCE_NOT_AN_EXECUTION_GATE"
    assert "validated generative Persona Fidelity" in binding["unsupported_claims"]
    assert (binding["files"][MODULE._relative(MODULE.STYLE_VALIDITY_FILES[2])] ==
            MODULE.STYLE_VALIDITY_ANALYSIS_SHA256)


def test_import_and_validate_paths_do_not_execute_scientific_operations(monkeypatch):
    assert MODULE.MAX_ATTEMPTS == 64
    assert MODULE.GENERATION_BASELINE == 508
    assert MODULE.INFERENCE_BASELINE == 3171.544608799969
    assert MODULE.MIN_PREFLIGHT_RAM == 3 * 1024 ** 3
    assert MODULE.MIN_READY_RAM == 1024 ** 3
    assert MODULE.MIN_LIVE_RAM == 512 * 1024 ** 2
    assert MODULE.RUNTIME["warmup"] is False
    assert MODULE.AUTHORIZATION_DRAFT.name.endswith("draft_v1.json")
