import csv
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import p1_persona_dialogue_disjoint_surface_validation_v2 as module


@pytest.fixture(autouse=True)
def repository_cwd(monkeypatch):
    monkeypatch.chdir(REPO)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fake_plan_and_results():
    design, bank = load(module.DESIGN), load(module.CASE_BANK)
    cases = {case["case_id"]: case for case in bank["cases"]}
    rows, results = [], {}
    for spec in module.request_specs():
        case = cases[spec["case_id"]]
        factors, semantics, surface, messages = module.construction(
            design, bank, case, spec["arm"])
        row = {**spec, "persona_id": case["persona_id"],
               "task_family": case["task_family"], "factors": factors,
               "history_semantics": semantics, "history_surface": surface,
               "messages": messages, "preferred_option": case["preferred_option"],
               "options": case["options"], "anchors": module.anchors(case)}
        rows.append(row)
        side = case["preferred_option"]
        response = (f"Option {side} [{row['anchors']['current'][side]}] — "
                    f"{case['options'][side]['canonical']}. A concise reason.")
        results[row["request_id"]] = {"raw_response": response}
    return {"requests": rows}, results


def csv_rows(value):
    return list(csv.DictReader(io.StringIO(value.decode("utf-8"), newline="")))


def encode_rows(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def unavailable_submission(records, stage="A"):
    copied = [dict(row) for row in records]
    editable = module.STAGE_A_EDITABLE if stage == "A" else module.STAGE_B_EDITABLE
    fields = ((module.STAGE_A_IMMUTABLE + module.STAGE_A_EDITABLE)
              if stage == "A" else
              (module.STAGE_B_IMMUTABLE + module.STAGE_B_EDITABLE))
    for row in copied:
        row.update({field: "" for field in editable})
        row["annotation_status"] = "UNAVAILABLE"
        row["missing_reason"] = "Reviewer did not assess this record."
    return encode_rows(copied, fields)


def provenance(template, submitted, receipt, **updates):
    value = {
        "schema_version": "personaslm_dsv_review_provenance_v2",
        "reviewer_pseudonym": "R1",
        "private_reviewer_identifier": "stored-separately",
        "human_reviewer": True,
        "relationship": "PRINCIPAL_RESEARCHER",
        "independent_of_project": False,
        "prior_rubric_or_item_involvement": "YES",
        "prior_exposure_to_outputs": "NO",
        "condition_mapping_seen_before_lock": "NO",
        "automatic_or_ai_labels_seen_before_lock": "NO",
        "ai_assistance_used_for_judgments": "NO",
        "review_environment": "offline spreadsheet",
        "started_utc": "2026-10-18T21:00:00Z",
        "completed_utc": "2026-10-18T22:00:00Z",
        "template_sha256": module.bytes_sha256(template),
        "instructions_sha256": receipt["instructions_sha256"],
        "schema_sha256": module.sha256(module.REVIEW_SCHEMA),
        "source_receipt_sha256": module.th(json.dumps(
            receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))),
        "completed_csv_sha256": module.bytes_sha256(submitted),
        "notes": "",
    }
    value.update(updates)
    return value


def stage_a_seal():
    return {"status": "VALIDATED_IMMUTABLE_STAGE_A_SEAL",
            "record_count": 168,
            "stage_a_template_sha256": "1" * 64,
            "stage_a_submission_sha256": "2" * 64,
            "stage_a_intake_sha256": "3" * 64,
            "stage_a_order_sha256": "4" * 64}


def test_v2_validates_offline_and_v1_is_preserved_with_zero_operations():
    result = module.validate_design(require_unstarted=True)
    assert result["status"] == "PASS_PROSPECTIVE_NOT_AUTHORIZED_NOT_EXECUTED"
    assert result["requests"] == 168
    assert result["lexical_4gram_overlap_count"] == 1
    withdrawn = load(module.V1_WITHDRAWAL)
    assert withdrawn["status"].endswith("WITHDRAWN_SCIENTIFIC_DESIGN_NO_GO")
    assert set(withdrawn["completed_operations"].values()) == {0}
    assert module.sha256(module.DESIGN) == module.DESIGN_SHA
    assert module.sha256(module.CASE_BANK) == module.CASE_BANK_SHA
    assert module.sha256(module.REVIEW_SCHEMA) == module.REVIEW_SCHEMA_SHA
    assert module.sha256(module.MATERIAL_AUDIT) == module.MATERIAL_AUDIT_SHA


def test_opaque_display_position_anchors_and_corrected_case_materials():
    bank = load(module.CASE_BANK)
    assert [case["execution_index"] for case in bank["cases"]] == list(range(24))
    for case in bank["cases"]:
        marks = module.anchors(case)
        assert set(marks["history"].values()) == {
            f"DSV{case['execution_index'] + 1:03d}H1",
            f"DSV{case['execution_index'] + 1:03d}H2",
            f"DSV{case['execution_index'] + 1:03d}H3"}
        for position, semantic in enumerate(case["archived_semantic_display_order"], 1):
            assert marks["history"][semantic].endswith(f"H{position}")
        assert case["irrelevant_control_class"] == "DESIGNED_IRRELEVANT_CONTROL"
        assert case["irrelevant_control_rationale"]
        assert len(case["evidence_spans"]) == 4
    assert bank["cases"][15]["history_targets"]["irrelevant"] == "Ceramic Waybill"
    assert [case["case_id"] for case in bank["cases"][16:]] == [
        "DSV2_CASE_017_ISLA_ROUTINE", "DSV2_CASE_018_BREN_PLAN",
        "DSV2_CASE_019_KAYA_SUPPORT", "DSV2_CASE_020_OREN_ROUTINE",
        "DSV2_CASE_021_ISLA_PLAN", "DSV2_CASE_022_BREN_SUPPORT",
        "DSV2_CASE_023_KAYA_ROUTINE", "DSV2_CASE_024_OREN_PLAN"]


def test_near_williams_schedule_has_exact_first_order_balance():
    rows = module.request_specs()
    assert module.th(json.dumps(module.ARM_INDEX_SCHEDULE,
                                separators=(",", ":"))) == module.SCHEDULE_SHA256
    assert len(rows) == len({row["request_id"] for row in rows}) == 168
    predecessor = Counter()
    for case_id in sorted({row["case_id"] for row in rows}):
        arms = [row["arm"] for row in rows if row["case_id"] == case_id]
        predecessor.update(zip(arms, arms[1:]))
    assert len(predecessor) == 42
    assert Counter(predecessor.values()) == {3: 24, 4: 18}
    for arm in module.ARMS:
        positions = [row["within_case_position"] for row in rows
                     if row["arm"] == arm]
        assert set(Counter(positions).values()) <= {3, 4}
        assert sum(positions) == 72
    for quartile in range(1, 5):
        assert Counter(row["arm"] for row in rows
                       if row["quartile"] == quartile) == {
                           arm: 6 for arm in module.ARMS}


def test_history_package_is_isolated_and_raw_decl_changes_only_sentence_one():
    design, bank = load(module.DESIGN), load(module.CASE_BANK)
    for case in bank["cases"]:
        built = {arm: module.construction(design, bank, case, arm)[3]
                 for arm in module.ARMS}
        assert len({built[arm][1]["content"] for arm in module.ARMS[1:]}) == 1
        assert all(target not in json.dumps(built["SF_NO_H"])
                   for target in case["history_targets"].values())
        for semantic, raw, declarative in (
            ("aligned", "SFH_ALIGNED_RAW", "SFH_ALIGNED_DECLARATIVE"),
            ("conflict", "SFH_CONFLICT_RAW", "SFH_CONFLICT_DECLARATIVE"),
            ("irrelevant", "SFH_IRRELEVANT_RAW", "SFH_IRRELEVANT_DECLARATIVE")):
            raw_parts = built[raw][2]["content"].split(". ", 1)
            declarative_parts = built[declarative][2]["content"].split(". ", 1)
            assert raw_parts[1] == declarative_parts[1]
            assert module.anchors(case)["history"][semantic] in raw_parts[0]


def test_boundary_policy_eos_truncated_cross_turn_empty_and_suspicious():
    bank = load(module.CASE_BANK)
    case = bank["cases"][0]
    row = {"anchors": module.anchors(case),
           "preferred_option": case["preferred_option"], "options": case["options"]}
    first = (f"Option A [{row['anchors']['current']['A']}] — "
             f"{case['options']['A']['canonical']}. Reason.")
    eos = module.b.classify_response(first, {"stop_type": "eog", "stopped_eos": True})
    assert eos["status"] == "AMBIGUOUS"
    assert module.assessability(eos)["assessable"] is True
    truncated = module.b.classify_response(first, {"stop_type": "limit",
                                                   "stopped_limit": True})
    assert module.assessability(truncated)["assessable"] is False
    cross = module.b.classify_response(first + "\nuser: choose again",
                                       {"stop_type": "unknown"})
    assert cross["status"] == "CROSS_TURN"
    assert module.assessability(cross)["assessable"] is True
    score = module.automatic_score(row, cross["first_span"]["text"], True)
    assert score["preferred_current_anchor_selection"] == 1
    assert score["raw_tail_inspected"] is False
    empty = module.b.classify_response("", {"stop_type": "eog", "stopped_eos": True})
    suspicious = module.b.classify_response("Critic: " + first,
                                            {"stop_type": "eog", "stopped_eos": True})
    assert module.assessability(empty)["assessable"] is False
    assert module.assessability(suspicious)["assessable"] is False


def test_primary_complete_denominator_multiple_none_and_archived_are_zero():
    case = load(module.CASE_BANK)["cases"][0]
    row = {"anchors": module.anchors(case),
           "preferred_option": case["preferred_option"], "options": case["options"]}
    current = row["anchors"]["current"]
    multiple = module.automatic_score(
        row, f"[{current['A']}] or [{current['B']}].", True)
    none = module.automatic_score(row, "I cannot decide.", True)
    archived = module.automatic_score(
        row, f"[{row['anchors']['history']['aligned']}] was selected.", True)
    assert (multiple["preferred_current_anchor_selection"],
            multiple["any_current_anchor_selection"]) == (0, 0)
    assert (none["preferred_current_anchor_selection"],
            none["any_current_anchor_selection"]) == (0, 0)
    assert archived["preferred_current_anchor_selection"] == 0
    assert archived["selection_category"] == "ARCHIVED_ALIGNED"
    missing = module.automatic_score(row, "", False)
    assert missing["preferred_current_anchor_selection"] is None


def test_all_168_slots_survive_failure_at_first_middle_last_and_raw_recovery():
    plan = {"requests": [{"request_id": f"r{i}"}
                         for i in range(module.MAX_ATTEMPTS)]}
    for failure in (0, 84, 167):
        attempted = [f"r{i}" for i in range(failure + 1)]
        raw = {f"r{i}": {} for i in range(failure)}
        derived = {f"r{i}": {} for i in range(failure)}
        slots = module.planned_slot_states(plan, attempted, raw, derived)
        assert len(slots) == 168
        assert slots[failure]["state"] == "ATTEMPTED_UNRESOLVED"
        if failure + 1 < 168:
            assert slots[failure + 1]["state"] == "UNATTEMPTED"
    attempted = ["r0", "r1"]
    slots = module.planned_slot_states(plan, attempted, {"r0": {}}, {})
    assert slots[0]["state"] == "RAW_RECOVERABLE"


def test_partial_binary_and_paired_analysis_keep_none_and_logical_bounds():
    metric = module.PRIMARY_METRICS[0]
    summary = module._binary_summary(
        [{metric: 1}, {metric: 0}, {metric: None}], metric)
    assert summary == {"ones": 1, "zeros": 1, "missing": 1,
                       "total_slots": 3, "resolved_denominator": 2,
                       "mean_resolved": .5, "logical_lower": 1 / 3,
                       "logical_upper": 2 / 3}
    weights = module.registered_estimand_weights()["theta_generic_history"]
    by_case = {"c": {arm: {metric: None} for arm in module.ARMS}}
    contrast = module._contrast(by_case, ["c"], weights, metric, {"c": "p"})
    assert contrast["complete_case_estimate"] is None
    assert contrast["unresolved_cases"] == 1
    assert contrast["logical_lower"] == -1.0
    assert contrast["logical_upper"] == 1.0


@pytest.mark.parametrize("status", ["PASS", "PARTIAL", "BLOCKED",
                                     "COMPLETE_DATA_POSTFLIGHT_FAILED"])
def test_terminal_accounting_accepts_every_registered_status(status):
    plan = {"requests": []}
    report = module.build_run_summary(status, plan, [], 0.0, 0.0, 0.1, "run")
    assert report["status"] == status
    assert report["attempted"] == 0


def test_run_summary_uses_maintained_time_when_raw_journal_write_is_absent(monkeypatch):
    plan = {"requests": [{"request_id": "r0"}]}
    events = [{"kind": module.STARTED, "data": plan["requests"][0]}]
    summary = module.build_run_summary(
        "PARTIAL", plan, events, inference_seconds=2.75,
        failed_seconds=0.0, batch_wall_seconds=3.0, run_directory="run")
    assert summary["attempted"] == 1
    assert summary["responses_received"] == 0
    assert summary["inference_wall_seconds"] == 2.75
    assert summary["retries"] == 0
    monkeypatch.setattr(module, "run", lambda _: {"status": "PARTIAL"})
    assert module.main(["run"]) == 3


def test_registered_estimands_match_science_review_exactly():
    weights = module.registered_estimand_weights()
    assert weights["theta_A"] == {
        "SFH_ALIGNED_RAW": .5, "SFH_ALIGNED_DECLARATIVE": .5,
        "SFH_IRRELEVANT_RAW": -.5, "SFH_IRRELEVANT_DECLARATIVE": -.5}
    assert weights["theta_C"] == {
        "SFH_CONFLICT_RAW": .5, "SFH_CONFLICT_DECLARATIVE": .5,
        "SFH_IRRELEVANT_RAW": -.5, "SFH_IRRELEVANT_DECLARATIVE": -.5}
    assert weights["theta_generic_history"] == {
        "SF_NO_H": -1.0, "SFH_IRRELEVANT_RAW": .5,
        "SFH_IRRELEVANT_DECLARATIVE": .5}
    assert all(sum(values.values()) == pytest.approx(0)
               for values in weights.values())


def test_stage_a_is_deterministic_current_only_168_blank_records():
    plan, results = fake_plan_and_results()
    records, mapping, receipt = module.build_stage_a_review(plan, results)
    records2, mapping2, receipt2 = module.build_stage_a_review(plan, results)
    assert (records, mapping, receipt) == (records2, mapping2, receipt2)
    assert len(records) == len(mapping) == 168
    assert all(not row[field] for row in records
               for field in module.STAGE_A_EDITABLE)
    assert all(tuple(row) == module.STAGE_A_IMMUTABLE + module.STAGE_A_EDITABLE
               for row in records)
    assert not ({"request_id", "case_id", "arm", "history_semantics",
                 "history_surface", "response_sha256"} & set(records[0]))
    by_case_panels = defaultdict(set)
    immutable_panel = module.STAGE_A_IMMUTABLE[1:5]
    by_id = {row["blind_record_id"]: row for row in records}
    for item in mapping:
        by_case_panels[item["case_id"]].add(tuple(
            by_id[item["blind_record_id"]][field] for field in immutable_panel))
    assert all(len(values) == 1 for values in by_case_panels.values())
    assert receipt["history_fields_in_delivery"] is False
    assert receipt["mapping_in_delivery"] is False
    public = json.dumps(receipt)
    assert mapping[0]["request_id"] not in public
    assert records[0]["model_response"] not in public
    frozen = load(module.REVIEW_SCHEMA)["deterministic_construction"]
    assert receipt["ordered_id_sha256"] == frozen["ordered_id_sha256"]["stage_a"]
    assert receipt["ordered_source_assignment_sha256"] == \
        frozen["ordered_source_assignment_sha256"]["stage_a"]
    instructions = module.reviewer_instructions("A")
    assert "protected_mapping" not in json.dumps(instructions)
    assert receipt["instructions_sha256"] == module.bytes_sha256(
        module._canonical_pretty_json_bytes(instructions))


def test_stage_b_is_seal_gated_exact_72_and_lr_balanced():
    plan, results = fake_plan_and_results()
    with pytest.raises(Exception):
        module.build_stage_b_review(plan, results, {})
    records, mapping, receipt = module.build_stage_b_review(
        plan, results, stage_a_seal())
    assert len(records) == len(mapping) == 72
    assert all(not row[field] for row in records for field in module.STAGE_B_EDITABLE)
    assert set(row["blind_pair_id"] for row in records).isdisjoint(
        {f"DSV1-A-{index:03d}" for index in range(1, 169)})
    family = {row["case_id"]: row["task_family"] for row in plan["requests"]}
    strata = Counter((row["history_semantics"], family[row["case_id"]])
                     for row in mapping if row["left_surface"] ==
                     "RAW_RECOMMENDATION")
    assert set(strata.values()) == {4}
    assert sum(strata.values()) == 36
    assert receipt["aggregate_balance"]["raw_left"] == 36
    assert receipt["surface_blinding"] == "LABEL_MASKED_NOT_INTERVENTION_BLIND"
    frozen = load(module.REVIEW_SCHEMA)["deterministic_construction"]
    assert receipt["ordered_id_sha256"] == frozen["ordered_id_sha256"]["stage_b"]
    assert module.th("\n".join(f"{row['case_id']}|{row['history_semantics']}"
                               for row in mapping)) == frozen[
        "ordered_source_assignment_sha256"]["stage_b_case_semantics"]
    forbidden = set(load(module.REVIEW_SCHEMA)["protected_mapping"][
        "forbidden_in_delivery"])
    assert not forbidden.intersection(records[0])


def test_stage_b_intake_is_bound_to_stage_a_seal():
    plan, results = fake_plan_and_results()
    seal = stage_a_seal()
    records, _, receipt = module.build_stage_b_review(plan, results, seal)
    template = module.review_csv_bytes(records, "B")
    submitted = unavailable_submission(records, "B")
    seal_sha = module.th(json.dumps(seal, sort_keys=True, separators=(",", ":")))
    prov = provenance(template, submitted, receipt,
        stage_a_intake_sha256=seal["stage_a_intake_sha256"],
        stage_a_seal_sha256=seal_sha,
        stage_b_material_seen_before_stage_a_lock="NO")
    report = module.validate_review_intake(
        "B", template, submitted, prov, receipt, seal)
    assert report["records_assigned"] == 72
    assert report["records_unavailable"] == 72
    with pytest.raises(Exception):
        module.validate_review_intake(
            "B", template, submitted, prov, receipt, {})


def test_review_intake_unavailable_uncertain_and_provenance_classification(tmp_path):
    plan, results = fake_plan_and_results()
    records, _, receipt = module.build_stage_a_review(plan, results)
    template = module.review_csv_bytes(records, "A")
    submitted = unavailable_submission(records)
    prov = provenance(template, submitted, receipt)
    report = module.validate_review_intake("A", template, submitted, prov, receipt)
    assert report["records_unavailable"] == 168
    assert report["provenance_classification"] == "CLEAN_BLINDED_HUMAN"
    completed = csv_rows(submitted)
    row = completed[0]
    row.update({"annotation_status": "COMPLETED", "missing_reason": "",
        "selected_entity": "UNCERTAIN", "reason_support": "SUPPORTED",
        "current_fact_consistency": "CONSISTENT",
        "behavioral_persona_fidelity": "3", "response_relevance": "5",
        "conversational_coherence": "5", "answer_completeness": "COMPLETE",
        "linguistic_prefix_match": "PARTIAL", "linguistic_suffix_match": "PARTIAL",
        "global_linguistic_persona_fidelity": "3",
        "material_unverifiable_claim": "NO",
        "evidence_span": row["model_response"].split(".", 1)[0],
        "reviewer_rationale": "The selected identity is not fully clear.",
        "reviewer_confidence": "LOW"})
    mixed = encode_rows(completed, module.STAGE_A_IMMUTABLE + module.STAGE_A_EDITABLE)
    mixed_prov = provenance(template, mixed, receipt,
                            prior_exposure_to_outputs="YES")
    report = module.archive_and_validate_review_intake(
        "A", template, mixed, mixed_prov, receipt, tmp_path, 1)
    assert report["records_with_uncertain"] == 1
    assert report["provenance_classification"] == "HUMAN_EXPOSURE_LIMITED"
    with pytest.raises(FileExistsError):
        module.archive_and_validate_review_intake(
            "A", template, mixed, mixed_prov, receipt, tmp_path, 1)


@pytest.mark.parametrize("mutation", ["immutable", "duplicate", "drop", "header",
                                       "span", "enum", "provenance_hash"])
def test_review_intake_rejects_structural_and_provenance_mutations(mutation):
    plan, results = fake_plan_and_results()
    records, _, receipt = module.build_stage_a_review(plan, results)
    template = module.review_csv_bytes(records, "A")
    rows = csv_rows(unavailable_submission(records))
    fields = list(module.STAGE_A_IMMUTABLE + module.STAGE_A_EDITABLE)
    if mutation == "immutable":
        rows[0]["current_user_turn"] += " changed"
    elif mutation == "duplicate":
        rows[1]["blind_record_id"] = rows[0]["blind_record_id"]
    elif mutation == "drop":
        rows.pop()
    elif mutation == "header":
        fields[0], fields[1] = fields[1], fields[0]
    elif mutation in ("span", "enum"):
        row = rows[0]
        row.update({field: "x" for field in module.STAGE_A_EDITABLE})
        row.update({"annotation_status": "COMPLETED", "missing_reason": "",
            "selected_entity": "CURRENT_OPTION_A", "reason_support": "SUPPORTED",
            "current_fact_consistency": "CONSISTENT",
            "behavioral_persona_fidelity": "3", "response_relevance": "5",
            "conversational_coherence": "5", "answer_completeness": "COMPLETE",
            "linguistic_prefix_match": "PARTIAL", "linguistic_suffix_match": "PARTIAL",
            "global_linguistic_persona_fidelity": "3",
            "material_unverifiable_claim": "NO", "reviewer_confidence": "HIGH",
            "reviewer_rationale": "Reviewed."})
        row["evidence_span"] = ("not a substring" if mutation == "span" else
                                row["model_response"].split(".", 1)[0])
        if mutation == "enum":
            row["response_relevance"] = "6"
    submitted = encode_rows(rows, fields)
    prov = provenance(template, submitted, receipt)
    if mutation == "provenance_hash":
        prov["completed_csv_sha256"] = "f" * 64
    with pytest.raises(Exception):
        module.validate_review_intake("A", template, submitted, prov, receipt)


def test_authorization_utc_must_be_nonblank_zoned_utc():
    assert module._parse_zoned_utc("2026-10-18T21:00:00Z").utcoffset().total_seconds() == 0
    for value in ("", "2026-10-18T21:00:00", "2026-10-18T21:00:00+02:00"):
        with pytest.raises(Exception):
            module._parse_zoned_utc(value)


def test_material_audit_and_protocol_freeze_have_no_labels():
    assert module.material_overlap_audit() == load(module.MATERIAL_AUDIT)
    protocol = load(module.REVIEW_SCHEMA)
    assert protocol["deterministic_construction"]["seeds"] == module.REVIEW_SEEDS
    assert protocol["stage_a"]["record_count"] == 168
    assert protocol["stage_b"]["pair_count"] == 72
    assert set(protocol["label_state"].values()) <= {0, False}
    assert protocol["claim_limits"]
