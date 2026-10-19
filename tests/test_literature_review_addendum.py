import json
from pathlib import Path


PATH = Path(
    "docs/validation/literature_monitor_v1/"
    "primary_source_review_addendum_2026-10-18_v1.json"
)


def review():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_review_delta_is_structured_unique_and_not_misrepresented_as_human_review():
    value = review()
    assert value["reviewer_type"] == "AI_ASSISTED_PRIMARY_SOURCE_REVIEW"
    assert value["human_confirmation"] == "NOT_RECORDED"
    records = value["records"]
    assert len(records) == 3
    assert {row["stable_id"] for row in records} == {
        "arxiv:2610.08513",
        "arxiv:2610.11948",
        "arxiv:2610.17763",
    }
    assert all(row["source_url"].startswith("https://arxiv.org/abs/") for row in records)
    assert all(row["full_text_url"].startswith("https://arxiv.org/html/") for row in records)


def test_review_delta_records_required_scientific_fields():
    required = {
        "title",
        "authors",
        "venue_or_status",
        "publication_date",
        "identifiers",
        "source_url",
        "verified_summary",
        "research_methodology",
        "relevant_experimental_factors",
        "relevant_benchmarks",
        "overlap_with_personaslm",
        "difference_from_personaslm",
        "potential_novelty_threat",
        "potential_useful_baselines",
        "potential_methodological_improvements",
        "relevance_assessment",
        "date_last_checked",
    }
    for record in review()["records"]:
        assert required <= record.keys()
        assert record["date_last_checked"] == review()["date_last_checked"]


def test_fpa_collision_and_return_design_adaptation_are_explicit():
    records = {row["stable_id"]: row for row in review()["records"]}
    fpa = records["arxiv:2610.17763"]
    assert fpa["relevance_assessment"]["classification"] == "DIRECT_COMPETITOR_FOR_P6"
    assert fpa["potential_novelty_threat"]["level"] == "HIGH_DIRECT_ALGORITHMIC_COLLISION"
    assert "FPA" in fpa["potential_useful_baselines"]
    return_review = records["arxiv:2610.11948"]
    assert return_review["relevance_assessment"]["classification"] == "EVALUATION_IMPROVEMENT"
    assert "matched direct/single-turn answerability reference" in (
        return_review["potential_methodological_improvements"]
    )


def test_review_changes_no_protocol_and_consumes_no_generation_budget():
    value = review()
    assert value["research_impact"]["p6_status"] == "PAUSED_NO_RENAMED_FPA_IMPLEMENTATION"
    assert value["research_impact"]["protocol_changed"] is False
    assert value["research_impact"]["historical_experiment_reinterpreted"] is False
    assert value["execution_impact"] == {
        "scientific_model_generations": 0,
        "paid_resources": 0,
        "paper_systems_reproduced": 0,
        "human_reviews_fabricated": 0,
    }
