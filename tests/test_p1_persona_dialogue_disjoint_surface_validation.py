import json
from collections import Counter
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import p1_persona_dialogue_disjoint_surface_validation as module


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_candidate_validates_offline_and_has_no_operational_evidence(monkeypatch):
    monkeypatch.chdir(ROOT)
    result = module.validate_design(require_unstarted=True)
    assert result == {
        "status": "PASS_PROSPECTIVE_NOT_AUTHORIZED_NOT_EXECUTED",
        "synthetic_personas": 12,
        "cases": 24,
        "task_families": 3,
        "arms": 7,
        "requests": 168,
        "counterbalance_cells": 24,
        "material_audit_sha256": module.MATERIAL_AUDIT_SHA,
        "lexical_4gram_overlap_count": 2,
        "model_generations": 0,
        "tokenizer_operations": 0,
        "human_labels": 0,
    }
    assert module.sha256(module.DESIGN) == module.DESIGN_SHA
    assert module.sha256(module.CASE_BANK) == module.CASE_BANK_SHA
    assert module.sha256(module.REVIEW_SCHEMA) == module.REVIEW_SCHEMA_SHA
    assert module.sha256(module.MATERIAL_AUDIT) == module.MATERIAL_AUDIT_SHA
    for path in (module.AUTHORIZATION, module.FROZEN, module.PREFLIGHT,
                 module.AUDIT, module.ANALYSIS, module.ROOT / "claim.json"):
        assert not path.exists()
    assert not list((module.ROOT / "runs").glob("*"))


def test_24_cell_case_counterbalance_and_unique_entities():
    bank = load(module.CASE_BANK)
    cases = bank["cases"]
    assert len(bank["personas"]) == 12
    assert Counter(case["persona_id"] for case in cases) == {
        persona_id: 2 for persona_id in bank["personas"]}
    assert Counter(case["task_family"] for case in cases) == {
        family: 8 for family in bank["template_family"]["families"]}
    cells = Counter((tuple(case["archived_semantic_display_order"]),
                     case["preferred_option"],
                     "FIRST" if case["current_option_display_order"][0] ==
                     case["preferred_option"] else "SECOND") for case in cases)
    assert len(cells) == 24
    assert set(cells.values()) == {1}
    targets, marks = [], []
    for case in cases:
        targets.extend(option["canonical"] for option in case["options"].values())
        targets.extend(case["history_targets"].values())
        value = module.anchors(case)
        marks.extend(value["current"].values())
        marks.extend(value["history"].values())
    assert len(targets) == len(set(value.casefold() for value in targets)) == 120
    assert len(marks) == len(set(marks)) == 120


def test_augmented_latin_order_has_pairing_quartile_and_position_balance():
    rows = module.request_specs()
    assert len(rows) == len({row["request_id"] for row in rows}) == 168
    assert [row["order"] for row in rows] == list(range(168))
    assert Counter(row["arm"] for row in rows) == {
        arm: 24 for arm in module.ARMS}
    for quartile in range(1, 5):
        assert Counter(row["arm"] for row in rows if row["quartile"] == quartile) == {
            arm: 6 for arm in module.ARMS}
    for arm in module.ARMS:
        positions = [row["within_case_position"] for row in rows if row["arm"] == arm]
        orders = [row["order"] for row in rows if row["arm"] == arm]
        assert set(Counter(positions)) == set(range(7))
        assert set(Counter(positions).values()) <= {3, 4}
        assert sum(positions) == 72
        assert sum(orders) == 2004


def test_history_user_is_fixed_no_h_is_clean_and_surface_only_changes_sentence_one():
    design, bank = load(module.DESIGN), load(module.CASE_BANK)
    for case in bank["cases"]:
        built = {arm: module.construction(design, bank, case, arm)[3]
                 for arm in module.ARMS}
        assert len(built["SF_NO_H"]) == 2
        assert all(len(built[arm]) == 4 for arm in module.ARMS[1:])
        assert len({built[arm][1]["content"] for arm in module.ARMS[1:]}) == 1
        no_h = json.dumps(built["SF_NO_H"])
        assert all(target not in no_h for target in case["history_targets"].values())
        for semantic, raw, declarative in (
            ("aligned", "SFH_ALIGNED_RAW", "SFH_ALIGNED_DECLARATIVE"),
            ("conflict", "SFH_CONFLICT_RAW", "SFH_CONFLICT_DECLARATIVE"),
            ("irrelevant", "SFH_IRRELEVANT_RAW", "SFH_IRRELEVANT_DECLARATIVE")):
            raw_text = built[raw][2]["content"].split(". ", 1)
            declarative_text = built[declarative][2]["content"].split(". ", 1)
            assert raw_text[1] == declarative_text[1]
            assert case["history_targets"][semantic] in raw_text[0]
            assert module.anchors(case)["history"][semantic] in raw_text[0]


def test_anchor_scorer_uses_complete_denominator_for_valid_responses():
    bank = load(module.CASE_BANK)
    case = bank["cases"][0]
    row = {"anchors": module.anchors(case),
           "preferred_option": case["preferred_option"],
           "options": case["options"]}
    preferred = (f"Option A [{row['anchors']['current']['A']}] — "
                 f"{case['options']['A']['canonical']}. For me, this fits without fuss.")
    score = module.automatic_score(row, preferred)
    assert score["selection_category"] == "CURRENT_PREFERRED"
    assert score["preferred_current_anchor_selection"] == 1
    assert score["any_current_anchor_selection"] == 1
    assert score["exact_current_label_name_consistency"] == 1
    nonpreferred = f"Option B [{row['anchors']['current']['B']}] — other. Reason."
    score = module.automatic_score(row, nonpreferred)
    assert score["selection_category"] == "CURRENT_NONPREFERRED"
    assert score["preferred_current_anchor_selection"] == 0
    assert score["any_current_anchor_selection"] == 1
    multiple = (f"Option A [{row['anchors']['current']['A']}] or Option B "
                f"[{row['anchors']['current']['B']}]. Reason.")
    score = module.automatic_score(row, multiple)
    assert score["selection_category"] == "MULTIPLE"
    assert score["preferred_current_anchor_selection"] == 0
    assert score["any_current_anchor_selection"] == 0
    none = module.automatic_score(row, "I cannot decide. There is not enough context.")
    assert none["selection_category"] == "NONE"
    assert none["preferred_current_anchor_selection"] == 0
    assert none["any_current_anchor_selection"] == 0
    archived_anchor = row["anchors"]["history"]["aligned"]
    archived = module.automatic_score(row, f"[{archived_anchor}] was selected. Reason.")
    assert archived["selection_category"] == "ARCHIVED_ALIGNED"
    assert archived["exact_archived_intrusion"] == 1
    missing = module.automatic_score(row, "", valid_returned_response=False)
    assert missing["preferred_current_anchor_selection"] is None
    assert missing["any_current_anchor_selection"] is None


def test_registered_estimands_match_frozen_reference_and_are_centered():
    design = load(module.DESIGN)
    weights = module.registered_estimand_weights()
    assert set(weights) == {
        "theta_A", "theta_C", "theta_surface", "theta_generic_history",
        "derived_theta_A_minus_theta_C",
        "interaction_surface_aligned_minus_irrelevant",
        "interaction_surface_conflict_minus_irrelevant"}
    assert all(sum(values.values()) == pytest.approx(0.0)
               for values in weights.values())
    assert weights["theta_A"] == {
        "SFH_ALIGNED_RAW": 0.5, "SFH_ALIGNED_DECLARATIVE": 0.5,
        "SFH_IRRELEVANT_RAW": -0.5, "SFH_IRRELEVANT_DECLARATIVE": -0.5}
    assert weights["theta_generic_history"] == {
        "SF_NO_H": -1.0, "SFH_IRRELEVANT_RAW": 0.5,
        "SFH_IRRELEVANT_DECLARATIVE": 0.5}
    assert set(design["estimands"]["primary"]) == {
        "theta_A", "theta_C", "theta_surface", "theta_generic_history"}
    assert set(design["estimands"]["derived_contrast"]) == {
        "theta_A_minus_theta_C"}
    assert set(design["estimands"]["secondary_interactions"]) == {
        "theta_surface_aligned_minus_irrelevant",
        "theta_surface_conflict_minus_irrelevant"}


def test_material_audit_and_blank_two_stage_human_schema_are_frozen():
    assert module.material_overlap_audit() == load(module.MATERIAL_AUDIT)
    audit, review = load(module.MATERIAL_AUDIT), load(module.REVIEW_SCHEMA)
    assert audit["status"] == "PASS"
    assert audit["exact_entity_overlap"] == audit["exact_template_overlap"] == []
    assert audit["lexical_4gram_overlap_count"] == 2
    assert set(review["stages"]) == {"stage_a", "stage_b"}
    assert all(value in (0, False) for value in review["label_state"].values())


def test_inventory_enforces_frozen_prefix_and_zero_duplicates():
    rows = [{"request_id": "r0"}, {"request_id": "r1"}]
    plan = {"requests": rows}
    events = [
        {"kind": module.STARTED, "data": rows[0]},
        {"kind": module.RAW, "data": {"request_id": "r0", "response": {}}},
        {"kind": module.DERIVED, "data": {"request_id": "r0", "score": 1}},
        {"kind": module.STARTED, "data": rows[1]},
    ]
    attempted, raw, derived = module.inventory(plan, events)
    assert attempted == ["r0", "r1"]
    assert list(raw) == list(derived) == ["r0"]
    with pytest.raises(Exception):
        module.inventory(plan, events + [events[1]])


def test_authorization_requirements_are_offline_and_do_not_create_artifacts(monkeypatch):
    monkeypatch.chdir(ROOT)
    before = {path: path.exists() for path in (
        module.AUTHORIZATION, module.FROZEN, module.PREFLIGHT,
        module.ROOT / "claim.json")}
    result = module.authorization_requirements()
    after = {path: path.exists() for path in before}
    assert before == after == {path: False for path in before}
    assert result["maximum_generation_attempts"] == 168
    assert result["maximum_tokenizer_operations_total"] == 336
    assert result["retries"] == result["hidden_warmups"] == 0
    assert result["minimum_available_physical_ram_bytes"] == 3 * 1024 ** 3
    assert result["global_baseline"]["generations_used"] == 340
    assert result["global_baseline"]["inference_wall_seconds_used"] == \
        1968.0195239999766
