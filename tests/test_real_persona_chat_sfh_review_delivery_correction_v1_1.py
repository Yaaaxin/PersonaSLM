import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import real_persona_chat_sfh_review_delivery_correction_v1_1 as correction


def test_projection_omits_analyst_construction_and_preserves_rubric():
    source = correction.original.protocol()
    safe = correction.sanitized_protocol(source)
    assert safe["schema"] == source["schema"]
    assert safe["records_required"] == 64
    assert "construction" not in safe and "bindings" not in safe
    assert source["construction"]["order_seed"] not in json.dumps(safe, ensure_ascii=False)
    assert source["construction"]["order_algorithm"] not in json.dumps(safe, ensure_ascii=False)
    assert "cannot undo previous exposure" in safe["exposure_warning"]


def test_public_protocol_exactly_matches_safe_projection():
    expected = correction.original.json_bytes(correction.sanitized_protocol(correction.original.protocol()))
    assert correction.PUBLIC.read_bytes() == expected


def test_questionnaire_does_not_supply_human_attestations():
    questionnaire = correction.blank_questionnaire()
    for key in ("human_reviewer", "independent_of_project", "japanese_competence_attested",
                "prior_assignment_key_material_exposure", "prior_exposure_to_outputs",
                "ai_assistance_used_for_judgments", "review_started_utc", "attestation_recorded_utc"):
        assert questionnaire[key] is None
    assert questionnaire["japanese_competence_description"] == ""
    assert questionnaire["reviewer_pseudonym"] == ""
