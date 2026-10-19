import json
from pathlib import Path


PATH = Path(
    "docs/validation/literature_monitor_v1/"
    "primary_source_review_addendum_2026-10-18_v2.json"
)


def review():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_pers_eval_review_is_versioned_and_not_human_or_reproduction_evidence():
    value = review()
    assert value["reviewer_type"] == "AI_ASSISTED_PRIMARY_SOURCE_REVIEW"
    assert value["human_confirmation"] == "NOT_RECORDED"
    assert [row["stable_id"] for row in value["records"]] == ["arxiv:2610.19314"]
    assert value["execution_impact"] == {
        "scientific_model_generations": 0,
        "paid_resources": 0,
        "paper_systems_reproduced": 0,
        "human_reviews_fabricated": 0,
    }


def test_pers_eval_review_preserves_frozen_sources_and_measurement_boundary():
    value = review()
    assert all(row["preservation"].startswith("UNCHANGED") for row in value["predecessors"])
    assert value["discovery_evidence"]["failed_sandbox_snapshot"]["source_requests_failed"] == 13
    assert value["discovery_evidence"]["successful_snapshot"]["source_requests_succeeded"] == 13
    assert value["research_impact"]["frozen_gate_changed"] is False
    assert "LLM-as-judge" in value["research_impact"]["prospective_design_adaptations"][0]
