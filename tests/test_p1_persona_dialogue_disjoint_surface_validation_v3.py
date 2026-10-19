import csv
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import p1_persona_dialogue_disjoint_surface_validation_v3 as module


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


def provenance(template, submitted, receipt_path, stage="A", **updates):
    receipt = load(receipt_path)
    value = {
        "schema_version": "personaslm_dsv_review_provenance_v3",
        "reviewer_pseudonym": "R1",
        "private_reviewer_identifier": "stored-separately",
        "human_reviewer": True,
        "relationship": "PRINCIPAL_RESEARCHER",
        "independent_of_project": False,
        "prior_rubric_or_item_involvement": "NO",
        "prior_exposure_to_outputs": "NO",
        "condition_mapping_seen_before_lock": "NO",
        "automatic_or_ai_labels_seen_before_lock": "NO",
        "ai_assistance_used_for_judgments": "NO",
        "stage_b_material_seen_before_stage_a_lock": "NO",
        "review_environment": "offline spreadsheet",
        "started_utc": "2026-10-18T21:00:00Z",
        "completed_utc": "2026-10-18T22:00:00Z",
        "template_sha256": module.bytes_sha256(template),
        "instructions_sha256": receipt["instructions_sha256"],
        "schema_sha256": module.sha256(module.REVIEW_SCHEMA),
        "source_receipt_sha256": module.sha256(receipt_path),
        "completed_csv_sha256": module.bytes_sha256(submitted),
        "notes": "",
    }
    if stage == "B":
        stage_a_attempt = module._validated_attempt_files("A")
        value.update({"stage_a_intake_sha256": module.sha256(
                          stage_a_attempt["intake"]),
                      "stage_a_seal_sha256": module.sha256(module.STAGE_A_SEAL)})
    value.update(updates)
    return module._canonical_pretty_json_bytes(value)


def configure_official_review(monkeypatch, tmp_path):
    delivery_a, delivery_b = tmp_path / "delivery_a", tmp_path / "delivery_b"
    protected = tmp_path / "protected"
    paths = {
        "FROZEN": tmp_path / "frozen.json", "AUDIT": tmp_path / "audit.json",
        "STAGE_A_TEMPLATE": delivery_a / "template.csv",
        "STAGE_A_INSTRUCTIONS": delivery_a / "instructions.json",
        "STAGE_A_RECEIPT": delivery_a / "receipt.json",
        "STAGE_A_MAPPING": protected / "a_mapping.json",
        "STAGE_A_ATTEMPTS": protected / "a_attempts",
        "STAGE_A_VALIDATED_POINTER": protected / "a_validated_pointer.json",
        "STAGE_A_SEAL": protected / "a_seal.json",
        "STAGE_B_TEMPLATE": delivery_b / "template.csv",
        "STAGE_B_INSTRUCTIONS": delivery_b / "instructions.json",
        "STAGE_B_RECEIPT": delivery_b / "receipt.json",
        "STAGE_B_MAPPING": protected / "b_mapping.json",
        "STAGE_B_ATTEMPTS": protected / "b_attempts",
        "STAGE_B_VALIDATED_POINTER": protected / "b_validated_pointer.json",
        "STAGE_B_SEAL": protected / "b_seal.json",
        "UNBLINDED_DERIVATIVE": protected / "unblinded.json",
    }
    for name, path in paths.items():
        monkeypatch.setattr(module, name, path)
    paths["FROZEN"].write_text('{"fake":"manifest"}\n', encoding="utf-8")
    paths["AUDIT"].write_text('{"fake":"audit"}\n', encoding="utf-8")
    plan, results = fake_plan_and_results()
    replay_rows = [(row, results[row["request_id"]], "COMPLETED")
                   for row in plan["requests"]]
    run_folder = tmp_path / "run"
    run_folder.mkdir()
    monkeypatch.setattr(module, "_official_review_replay",
                        lambda: (plan, run_folder, replay_rows))
    return paths, plan, results, replay_rows


def test_v3_validates_offline_and_v2_is_preserved_with_zero_operations():
    result = module.validate_design(require_unstarted=True)
    assert result["status"] == "PASS_PROSPECTIVE_NOT_AUTHORIZED_NOT_EXECUTED"
    assert result["requests"] == 168
    assert result["lexical_4gram_overlap_count"] == 1
    withdrawn = load(module.V2_WITHDRAWAL)
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


def _source_files(tmp_path, stage, submitted, provenance_bytes):
    submission_path = tmp_path / f"source_{stage}.csv"
    provenance_path = tmp_path / f"source_{stage}.json"
    submission_path.write_bytes(submitted)
    provenance_path.write_bytes(provenance_bytes)
    return submission_path, provenance_path


def _prepare_and_seal_a(monkeypatch, tmp_path, **provenance_updates):
    paths, plan, results, replay_rows = configure_official_review(
        monkeypatch, tmp_path)
    receipt = module.prepare_stage_a_review_package()
    template = module.STAGE_A_TEMPLATE.read_bytes()
    submitted = unavailable_submission(csv_rows(template), "A")
    provenance_bytes = provenance(
        template, submitted, module.STAGE_A_RECEIPT, **provenance_updates)
    submission_path, provenance_path = _source_files(
        tmp_path, "a", submitted, provenance_bytes)
    seal = module.seal_stage_a(submission_path, provenance_path)
    return paths, plan, results, replay_rows, receipt, seal


def test_fake_stage_a_seal_is_rejected(monkeypatch, tmp_path):
    configure_official_review(monkeypatch, tmp_path)
    module.STAGE_A_SEAL.parent.mkdir(parents=True, exist_ok=True)
    module.STAGE_A_SEAL.write_text(json.dumps({
        "schema_version": "personaslm_dsv_stage_a_seal_v3",
        "status": "VALIDATED_IMMUTABLE_STAGE_A_SEAL", "stage": "A",
        "record_count": 168, "files": {}}), encoding="utf-8")
    with pytest.raises(Exception):
        module.verify_stage_a_seal()
    with pytest.raises(Exception):
        module.prepare_stage_b_review_package()


def test_official_a_b_finalize_and_unblind_happy_path(monkeypatch, tmp_path):
    paths, plan, _, _, receipt_a, seal_a = _prepare_and_seal_a(
        monkeypatch, tmp_path)
    assert receipt_a["mapping_file_sha256"] == module.sha256(
        module.STAGE_A_MAPPING)
    assert module.verify_stage_a_seal() == seal_a
    receipt_b = module.prepare_stage_b_review_package()
    template_b = module.STAGE_B_TEMPLATE.read_bytes()
    rows_b = csv_rows(template_b)
    assert len(rows_b) == 72
    mapping_b = load(module.STAGE_B_MAPPING)["rows"]
    family = {row["case_id"]: row["task_family"] for row in plan["requests"]}
    strata = Counter((row["history_semantics"], family[row["case_id"]])
                     for row in mapping_b if row["left_surface"] ==
                     "RAW_RECOMMENDATION")
    assert len(strata) == 9 and set(strata.values()) == {4}
    assert receipt_b["aggregate_balance"]["raw_left"] == 36
    assert receipt_b["mapping_file_sha256"] == module.sha256(
        module.STAGE_B_MAPPING)
    submitted_b = unavailable_submission(rows_b, "B")
    provenance_b = provenance(
        template_b, submitted_b, module.STAGE_B_RECEIPT, stage="B")
    source_b, source_prov_b = _source_files(
        tmp_path, "b", submitted_b, provenance_b)
    seal_b = module.seal_stage_b(source_b, source_prov_b)
    assert module.verify_stage_b_seal() == seal_b
    derivative = module.unblind_human_review()
    assert len(derivative["stage_a"]) == 168
    assert len(derivative["stage_b"]) == 72
    assert module.UNBLINDED_DERIVATIVE.is_file()
    delivery_text = (module.STAGE_A_TEMPLATE.read_text(encoding="utf-8") +
                     module.STAGE_B_TEMPLATE.read_text(encoding="utf-8"))
    assert mapping_b[0]["left_request_id"] not in delivery_text


def test_invalid_first_then_valid_correction_is_preserved_for_both_stages(
        monkeypatch, tmp_path):
    configure_official_review(monkeypatch, tmp_path)
    module.prepare_stage_a_review_package()
    template_a = module.STAGE_A_TEMPLATE.read_bytes()
    valid_a = unavailable_submission(csv_rows(template_a), "A")
    invalid_lines = valid_a.splitlines()
    invalid_lines[1] += b",EXTRA_CELL"
    invalid_a = b"\n".join(invalid_lines) + b"\n"
    invalid_a_prov = provenance(
        template_a, invalid_a, module.STAGE_A_RECEIPT)
    bad_a, bad_a_prov = _source_files(
        tmp_path, "a_invalid", invalid_a, invalid_a_prov)
    with pytest.raises(Exception):
        module.seal_stage_a(bad_a, bad_a_prov)
    a1 = module._review_attempt_locations("A", "attempt_001")
    assert a1["submission"].read_bytes() == invalid_a
    assert load(a1["validation_report"])["status"] == \
        "INVALID_PRESERVED_REVIEW_ATTEMPT"
    assert not module.STAGE_A_VALIDATED_POINTER.exists()

    valid_a_prov = provenance(template_a, valid_a, module.STAGE_A_RECEIPT)
    good_a, good_a_prov = _source_files(
        tmp_path, "a_valid", valid_a, valid_a_prov)
    seal_a = module.seal_stage_a(good_a, good_a_prov)
    assert seal_a["validated_attempt_id"] == "attempt_002"
    assert load(module.STAGE_A_VALIDATED_POINTER)["attempt_id"] == "attempt_002"
    assert a1["submission"].read_bytes() == invalid_a

    module.prepare_stage_b_review_package()
    template_b = module.STAGE_B_TEMPLATE.read_bytes()
    valid_b = unavailable_submission(csv_rows(template_b), "B")
    invalid_lines = valid_b.splitlines()
    invalid_lines[-1] += b",EXTRA_CELL"
    invalid_b = b"\n".join(invalid_lines) + b"\n"
    invalid_b_prov = provenance(
        template_b, invalid_b, module.STAGE_B_RECEIPT, stage="B")
    bad_b, bad_b_prov = _source_files(
        tmp_path, "b_invalid", invalid_b, invalid_b_prov)
    with pytest.raises(Exception):
        module.seal_stage_b(bad_b, bad_b_prov)
    b1 = module._review_attempt_locations("B", "attempt_001")
    assert b1["submission"].read_bytes() == invalid_b
    assert load(b1["validation_report"])["status"] == \
        "INVALID_PRESERVED_REVIEW_ATTEMPT"
    assert not module.STAGE_B_VALIDATED_POINTER.exists()

    valid_b_prov = provenance(
        template_b, valid_b, module.STAGE_B_RECEIPT, stage="B")
    good_b, good_b_prov = _source_files(
        tmp_path, "b_valid", valid_b, valid_b_prov)
    seal_b = module.seal_stage_b(good_b, good_b_prov)
    assert seal_b["validated_attempt_id"] == "attempt_002"
    assert load(module.STAGE_B_VALIDATED_POINTER)["attempt_id"] == "attempt_002"
    assert b1["submission"].read_bytes() == invalid_b


def test_pointer_written_seal_missing_recovers_idempotently_for_both_stages(
        monkeypatch, tmp_path):
    configure_official_review(monkeypatch, tmp_path)
    module.prepare_stage_a_review_package()
    template_a = module.STAGE_A_TEMPLATE.read_bytes()
    submitted_a = unavailable_submission(csv_rows(template_a), "A")
    provenance_a = provenance(
        template_a, submitted_a, module.STAGE_A_RECEIPT)
    source_a, source_prov_a = _source_files(
        tmp_path, "a_crash", submitted_a, provenance_a)

    original_write = module.write_exclusive
    def fail_a_seal(path, value):
        if Path(path) == module.STAGE_A_SEAL:
            raise OSError("injected after Stage-A pointer")
        return original_write(path, value)
    monkeypatch.setattr(module, "write_exclusive", fail_a_seal)
    with pytest.raises(OSError, match="after Stage-A pointer"):
        module.seal_stage_a(source_a, source_prov_a)
    assert module.STAGE_A_VALIDATED_POINTER.is_file()
    assert not module.STAGE_A_SEAL.exists()
    assert len(list(module.STAGE_A_ATTEMPTS.iterdir())) == 1
    monkeypatch.setattr(module, "write_exclusive", original_write)
    seal_a = module.seal_stage_a(source_a, source_prov_a)
    assert seal_a["validated_attempt_id"] == "attempt_001"
    assert len(list(module.STAGE_A_ATTEMPTS.iterdir())) == 1
    assert module.seal_stage_a(source_a, source_prov_a) == seal_a

    module.prepare_stage_b_review_package()
    template_b = module.STAGE_B_TEMPLATE.read_bytes()
    submitted_b = unavailable_submission(csv_rows(template_b), "B")
    provenance_b = provenance(
        template_b, submitted_b, module.STAGE_B_RECEIPT, stage="B")
    source_b, source_prov_b = _source_files(
        tmp_path, "b_crash", submitted_b, provenance_b)

    def fail_b_seal(path, value):
        if Path(path) == module.STAGE_B_SEAL:
            raise OSError("injected after Stage-B pointer")
        return original_write(path, value)
    monkeypatch.setattr(module, "write_exclusive", fail_b_seal)
    with pytest.raises(OSError, match="after Stage-B pointer"):
        module.seal_stage_b(source_b, source_prov_b)
    assert module.STAGE_B_VALIDATED_POINTER.is_file()
    assert not module.STAGE_B_SEAL.exists()
    assert len(list(module.STAGE_B_ATTEMPTS.iterdir())) == 1
    monkeypatch.setattr(module, "write_exclusive", original_write)
    seal_b = module.seal_stage_b(source_b, source_prov_b)
    assert seal_b["validated_attempt_id"] == "attempt_001"
    assert len(list(module.STAGE_B_ATTEMPTS.iterdir())) == 1
    assert module.seal_stage_b(source_b, source_prov_b) == seal_b


def test_stage_b_prelock_exposure_downgrades_stage_a_provenance(monkeypatch,
                                                                tmp_path):
    *_, seal = _prepare_and_seal_a(
        monkeypatch, tmp_path,
        stage_b_material_seen_before_stage_a_lock="UNCERTAIN")
    assert seal["provenance_classification"] == "HUMAN_EXPOSURE_LIMITED"
    assert module.verify_stage_a_seal()["provenance_classification"] == \
        "HUMAN_EXPOSURE_LIMITED"


def test_joint_substitution_mapping_run_binding_and_extra_cells_rejected(
        monkeypatch, tmp_path):
    paths, _, _, replay_rows = configure_official_review(monkeypatch, tmp_path)
    module.prepare_stage_a_review_package()
    template = module.STAGE_A_TEMPLATE.read_bytes()
    submitted = unavailable_submission(csv_rows(template), "A")
    provenance_bytes = provenance(
        template, submitted, module.STAGE_A_RECEIPT)
    receipt = load(module.STAGE_A_RECEIPT)
    receipt["_actual_file_sha256"] = module.sha256(module.STAGE_A_RECEIPT)
    mapping = load(module.STAGE_A_MAPPING)

    substituted_rows = csv_rows(template)
    substituted_rows[0]["current_user_turn"] += " substituted"
    substituted = encode_rows(
        substituted_rows, module.STAGE_A_IMMUTABLE + module.STAGE_A_EDITABLE)
    substituted_submission = unavailable_submission(substituted_rows, "A")
    substituted_provenance = provenance(
        substituted, substituted_submission, module.STAGE_A_RECEIPT)
    fake_receipt = dict(receipt)
    fake_receipt["template_sha256"] = module.bytes_sha256(substituted)
    with pytest.raises(Exception):
        module.validate_review_intake(
            "A", substituted, substituted_submission, substituted_provenance,
            fake_receipt, mapping, replay_rows,
            run_directory=mapping["run_directory"])

    bad_mapping = json.loads(json.dumps(mapping))
    bad_mapping["rows"][0]["request_id"] = "substituted-request"
    with pytest.raises(Exception):
        module.validate_review_intake(
            "A", template, submitted, provenance_bytes, receipt,
            bad_mapping, replay_rows, run_directory=mapping["run_directory"])
    bad_run = json.loads(json.dumps(mapping))
    bad_run["run_directory"] = (tmp_path / "substituted-run").as_posix()
    with pytest.raises(Exception):
        module.validate_review_intake(
            "A", template, submitted, provenance_bytes, receipt,
            bad_run, replay_rows, run_directory=mapping["run_directory"])

    extra = submitted.splitlines()
    extra[1] += b",EXTRA"
    with pytest.raises(Exception):
        module.validate_review_intake(
            "A", b"\n".join(template.splitlines()) + b"\n",
            b"\n".join(extra) + b"\n", provenance_bytes, receipt,
            mapping, replay_rows, run_directory=mapping["run_directory"])


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

