import json
from collections import Counter
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import p1_persona_dialogue_history_semantics_surface_factorial_v2 as module


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_candidate_is_exactly_twelve_by_five_balanced_and_unstarted():
    design, bank = load(ROOT / module.DESIGN), load(ROOT / module.CASE_BANK)
    assert module.sha256(ROOT / module.DESIGN) == module.DESIGN_SHA
    assert module.sha256(ROOT / module.CASE_BANK) == module.CASE_BANK_SHA
    assert design["research"]["evidence_level"] == "DEVELOPMENT_MECHANISM_REPLICATION"
    assert design["research"][
        "zero_v2_tokenization_preflight_and_outputs_at_freeze"] is True
    assert design["research"]["prior_v1_native_tokenization_disclosed"].startswith(
        "V1 registered 60 native tokenizer calls")
    assert len(bank["personas"]) == len(bank["cases"]) == 12
    assert Counter(case["persona_id"] for case in bank["cases"]) == Counter(
        {persona_id: 1 for persona_id in bank["personas"]})
    assert Counter(case["preferred_option"] for case in bank["cases"]) == {"A": 6, "B": 6}
    assert Counter(tuple(case["current_option_display_order"]) for case in bank["cases"]) == {
        ("A", "B"): 6, ("B", "A"): 6}
    assert Counter(
        "PREFERRED_FIRST" if case["current_option_display_order"][0] ==
        case["preferred_option"] else "PREFERRED_SECOND"
        for case in bank["cases"]) == {"PREFERRED_FIRST": 6, "PREFERRED_SECOND": 6}
    assert Counter(
        (case["preferred_option"], tuple(case["current_option_display_order"]))
        for case in bank["cases"]) == {
            ("A", ("A", "B")): 3, ("A", ("B", "A")): 3,
            ("B", ("A", "B")): 3, ("B", ("B", "A")): 3}
    for domain in {case["domain"] for case in bank["cases"]}:
        assert Counter(
            "PREFERRED_FIRST" if case["current_option_display_order"][0] ==
            case["preferred_option"] else "PREFERRED_SECOND"
            for case in bank["cases"] if case["domain"] == domain) == {
                "PREFERRED_FIRST": 1, "PREFERRED_SECOND": 1}
    assert Counter(case["aligned_history_option"] for case in bank["cases"]) == {
        "A": 6, "B": 6}
    assert Counter(case["conflict_history_option"] for case in bank["cases"]) == {
        "A": 6, "B": 6}
    assert Counter((case["preferred_option"], case["aligned_history_option"])
                   for case in bank["cases"]) == {
        ("A", "A"): 3, ("A", "B"): 3, ("B", "A"): 3, ("B", "B"): 3}
    rows = design["order"]["requests"]
    assert len(rows) == len({row["request_id"] for row in rows}) == 60
    assert [row["order"] for row in rows] == list(range(60))
    assert Counter(row["arm"] for row in rows) == {arm: 12 for arm in module.ARMS}
    for arm in module.ARMS:
        orders = [row["order"] for row in rows if row["arm"] == arm]
        assert sum(orders) == 354
        assert sum(orders) / len(orders) == 29.5
    assert design["resource_budget"]["requests"] == 60
    assert design["resource_budget"]["actual_completion_inference_seconds_ceiling"] == 3600
    assert design["resource_budget"]["batch_wall_seconds_ceiling"] == 5400
    assert design["resource_budget"]["global_baseline"]["generations_used"] == 232
    assert design["resource_budget"]["global_baseline"][
        "inference_wall_seconds_used"] == pytest.approx(1361.7570141999922)
    assert design["authorization"]["execution_authorized"] is False
    assert design["authorization"]["tokenization_authorized"] is False
    assert design["authorization"]["preflight_authorized"] is False
    assert not (ROOT / module.AUTHORIZATION).exists()
    assert not (ROOT / module.FROZEN).exists()
    assert not (ROOT / module.PREFLIGHT).exists()
    assert not (ROOT / module.ROOT / "claim.json").exists()


def test_v2_removes_position_confound_and_changes_only_six_mention_orders():
    design, bank = load(ROOT / module.DESIGN), load(ROOT / module.CASE_BANK)
    v1_bank = load(ROOT / module.V1_CASE_BANK)
    cases = {case["case_id"]: case for case in bank["cases"]}
    v1_cases = {case["case_id"]: case for case in v1_bank["cases"]}

    position_cross = Counter()
    absolute_cross = Counter()
    aligned_positions = Counter()
    conflict_positions = Counter()
    for case in cases.values():
        current = ("CURRENT_FIRST" if case["current_option_display_order"][0] ==
                   case["preferred_option"] else "CURRENT_SECOND")
        aligned = ("ALIGNED_FIRST" if case["archived_option_display_order"][0] ==
                   case["aligned_history_option"] else "ALIGNED_SECOND")
        conflict = ("CONFLICT_FIRST" if case["archived_option_display_order"][0] ==
                    case["conflict_history_option"] else "CONFLICT_SECOND")
        position_cross[current + "__" + aligned] += 1
        aligned_positions[aligned] += 1
        conflict_positions[conflict] += 1
        absolute_cross[
            "CURRENT_" + "".join(case["current_option_display_order"]) +
            "__ARCHIVED_" + "".join(case["archived_option_display_order"])] += 1

    assert position_cross == {
        "CURRENT_FIRST__ALIGNED_FIRST": 3,
        "CURRENT_FIRST__ALIGNED_SECOND": 3,
        "CURRENT_SECOND__ALIGNED_FIRST": 3,
        "CURRENT_SECOND__ALIGNED_SECOND": 3}
    assert aligned_positions == {"ALIGNED_FIRST": 6, "ALIGNED_SECOND": 6}
    assert conflict_positions == {"CONFLICT_FIRST": 6, "CONFLICT_SECOND": 6}
    assert absolute_cross == {"CURRENT_AB__ARCHIVED_AB": 4,
                              "CURRENT_AB__ARCHIVED_BA": 2,
                              "CURRENT_BA__ARCHIVED_AB": 2,
                              "CURRENT_BA__ARCHIVED_BA": 4}
    assert design["design"][
        "current_preferred_position_by_aligned_archived_position"] == position_cross
    assert design["design"][
        "current_absolute_order_by_archived_absolute_order"] == absolute_cross

    changed = set()
    for case_id, case in cases.items():
        previous = v1_cases[case_id]
        assert module._history_components(case["history_user"]) == \
            module._history_components(previous["history_user"])
        if case["history_user"] != previous["history_user"]:
            changed.add(case_id)
        comparison = dict(case)
        comparison.pop("archived_option_display_order")
        comparison["history_user"] = previous["history_user"]
        assert comparison == previous
    assert changed == {
        "HSSF_R_FLEXIBLE_FERRY", "HSSF_S_FLEXIBLE_LECTURE",
        "HSSF_X_MILD_NOODLES", "HSSF_Y_MILD_STEW",
        "HSSF_Z_DAYLIGHT_DESK", "HSSF_AA_DAYLIGHT_LOUNGE"}
    changed_cases = [cases[case_id] for case_id in changed]
    assert Counter(case["preferred_option"] for case in changed_cases) == {
        "A": 3, "B": 3}
    assert Counter(
        "PREFERRED_FIRST" if case["current_option_display_order"][0] ==
        case["preferred_option"] else "PREFERRED_SECOND"
        for case in changed_cases) == {"PREFERRED_FIRST": 3, "PREFERRED_SECOND": 3}
    for domain in design["design"]["domains"]:
        domain_cases = [case for case in cases.values() if case["domain"] == domain]
        assert len({tuple(case["archived_option_display_order"])
                    for case in domain_cases}) == 1
        assert Counter(
            "FIRST" if case["archived_option_display_order"][0] ==
            case["aligned_history_option"] else "SECOND"
            for case in domain_cases) == {"FIRST": 1, "SECOND": 1}


def test_withdrawn_v1_is_bound_as_historical_provenance_only():
    design = load(ROOT / module.DESIGN)
    bindings = design["bindings"]
    for key in ("historical_v1_case_bank", "historical_v1_design",
                "historical_v1_authorization", "historical_v1_manifest",
                "historical_v1_withdrawal"):
        binding = bindings[key]
        assert module.sha256(ROOT / binding["path"]) == binding["sha256"]
    withdrawal = load(ROOT / bindings["historical_v1_withdrawal"]["path"])
    assert withdrawal["decision"]["v1_must_not_be_run"] is True
    assert withdrawal["completed_registration"]["native_tokenizer_calls"] == 60
    assert withdrawal["completed_registration"]["model_generations"] == 0
    assert not (ROOT / module.V1_OUT / "preflight_v1.json").exists()
    assert not (ROOT / module.V1_ROOT / "claim.json").exists()
    assert not list((ROOT / module.V1_ROOT / "runs").glob("*"))


def test_full_validation_proves_disjointness_and_zero_operations():
    assert module.validate_design(require_unstarted=True) == {
        "personas": 12, "cases": 12, "arms": 5, "requests": 60,
        "finite_grammar_probes": 48, "material_disjointness_sources": 8,
        "runtime_python_dependencies": 25,
        "new_model_generations": 0, "tokenizer_operations": 0}


def test_transitive_runtime_dependency_closure_is_bound_and_fails_closed(monkeypatch):
    dependencies = {path.as_posix() for path in module.runtime_python_dependency_paths()}
    required = {
        "tools/p1_persona_dialogue_history_semantics_surface_factorial_v2.py",
        "tools/p1_persona_dialogue_history_template_mechanism.py",
        "tools/p1_persona_dialogue_independent_replication.py",
        "tools/p1_persona_dialogue_mechanism.py",
        "tools/p1_persona_dialogue_mechanism_analysis_v2.py",
        "tools/p1_persona_dialogue_factorial.py",
        "tools/p1d_instruct_smoke.py",
        "tools/p1d_budget_calibration.py",
        "tools/p1d_format_calibration.py",
        "tools/p1d_instruct_template_check.py",
        "src/personaslm/response_status.py",
        "src/personaslm/server.py",
    }
    assert required <= dependencies
    expected = module.source_hashes()
    dependency = "tools/p1_persona_dialogue_mechanism.py"
    assert dependency in expected
    changed = {**expected, dependency: "0" * 64}
    monkeypatch.setattr(module, "source_hashes", lambda: changed)
    with pytest.raises(ValueError, match="dependency closure changed"):
        module.validate_registered_source_hashes(expected)


def test_prompt_factor_isolation_is_exact_within_every_case():
    design, bank = load(ROOT / module.DESIGN), load(ROOT / module.CASE_BANK)
    for case in bank["cases"]:
        built = {arm: module.construction(design, bank, case, arm)[3]
                 for arm in module.ARMS}
        assert len(built["SF_NO_H"]) == 2
        assert all(len(built[arm]) == 4 for arm in module.ARMS[1:])
        assert all(messages[0] == built["SF_NO_H"][0] for messages in built.values())
        assert all(messages[-1] == built["SF_NO_H"][-1] for messages in built.values())
        assert len({built[arm][1]["content"] for arm in module.ARMS[1:]}) == 1
        for semantics in ("ALIGNED", "CONFLICT"):
            raw = built[f"SFH_{semantics}_RAW"]
            declarative = built[f"SFH_{semantics}_DECLARATIVE"]
            assert raw[0] == declarative[0]
            assert raw[1] == declarative[1]
            assert raw[3] == declarative[3]
            raw_first, raw_second = raw[2]["content"].split(". ", 1)
            dec_first, dec_second = declarative[2]["content"].split(". ", 1)
            option = case[f"{semantics.casefold()}_history_option"]
            target = case["archived_options"][option]["canonical"]
            assert raw_first + "." == f"I recommend the {target}."
            assert dec_first + "." == f"{target} was my choice."
            assert raw_second == dec_second
        assert built["SFH_ALIGNED_RAW"][0] == built["SFH_CONFLICT_RAW"][0]
        assert built["SFH_ALIGNED_RAW"][1] == built["SFH_CONFLICT_RAW"][1]
        assert built["SFH_ALIGNED_RAW"][3] == built["SFH_CONFLICT_RAW"][3]


def _row(case):
    return {**case, "options": case["options"],
            "archived_options": case["archived_options"]}


def _style_parts(persona):
    prefix = next(item["value"] for item in persona["operational_style_checks"]
                  if item["check_id"] == "second_sentence_prefix")
    suffix = next(item["value"] for item in persona["operational_style_checks"]
                  if item["check_id"] == "second_sentence_suffix")
    return prefix, suffix


def test_target_selection_is_surface_independent_and_complete():
    bank = load(ROOT / module.CASE_BANK)
    case = bank["cases"][0]
    persona = bank["personas"][case["persona_id"]]
    prefix, suffix = _style_parts(persona)
    preferred = case["options"][case["preferred_option"]]
    strict = (f"I recommend {preferred['canonical']}. {prefix} "
              f"{preferred['reason_cues'][0]}, {suffix}")
    score = module.automatic_score(_row(case), persona, strict)
    assert score["current_preferred_selection"] == 1
    assert score["current_target_selection"] == 1
    assert score["strict_format_adherence"] == 1
    assert score["raw_recommendation_frame_occurrence"] == 0
    assert score["finite_contract_grammar_adherence"] == 1
    assert score["exact_current_reason_cue_secondary"] == 1

    article = (f"I recommend the {preferred['canonical']}. {prefix} detail, {suffix}")
    score = module.automatic_score(_row(case), persona, article)
    assert score["current_preferred_selection"] == 1
    assert score["current_target_selection"] == 1
    assert score["strict_format_adherence"] == 0
    assert score["raw_recommendation_frame_occurrence"] == 1
    assert score["finite_contract_grammar_adherence"] == 1

    labeled = (f"I recommend Option {case['preferred_option']} — {preferred['canonical']}. "
               f"{prefix} detail, {suffix}")
    score = module.automatic_score(_row(case), persona, labeled)
    assert score["current_preferred_selection"] == 1
    assert score["current_target_selection"] == 1
    assert score["strict_format_adherence"] == 0
    assert score["finite_contract_grammar_adherence"] == 1

    for declarative in (
            f"{preferred['canonical']} was my choice. {prefix} detail, {suffix}",
            f"My choice is {preferred['canonical']}. {prefix} detail, {suffix}"):
        score = module.automatic_score(_row(case), persona, declarative)
        assert score["selection_category"] == "CURRENT_PREFERRED"
        assert score["current_preferred_selection"] == 1
        assert score["current_target_selection"] == 1
        assert score["strict_format_adherence"] == 0
        assert score["finite_contract_grammar_adherence"] == 0

    score = module.automatic_score(
        _row(case), persona, f"I would choose something else. {prefix} detail, {suffix}")
    assert score["selection_category"] == "NONE"
    assert score["current_preferred_selection"] == 0
    assert score["current_target_selection"] == 0
    assert score["strict_format_adherence"] == 0
    assert score["semantic_reason_correctness"] is None
    assert score["semantic_reason_review_status"] == "PENDING_BLINDED_HUMAN_REVIEW"

    other = "B" if case["preferred_option"] == "A" else "A"
    multiple = (f"I choose {preferred['canonical']} or "
                f"{case['options'][other]['canonical']}. {prefix} detail, {suffix}")
    score = module.automatic_score(_row(case), persona, multiple)
    assert score["selection_category"] == "MULTIPLE"
    assert score["current_preferred_selection"] == 0
    assert score["current_target_selection"] == 0


def test_current_nonpreferred_and_archived_targets_remain_distinct():
    bank = load(ROOT / module.CASE_BANK)
    case = bank["cases"][0]
    persona = bank["personas"][case["persona_id"]]
    prefix, suffix = _style_parts(persona)
    other = "B" if case["preferred_option"] == "A" else "A"
    current = case["options"][other]["canonical"]
    score = module.automatic_score(
        _row(case), persona, f"I recommend the {current}. {prefix} detail, {suffix}")
    assert score["selection_category"] == "CURRENT_NONPREFERRED"
    assert score["current_preferred_selection"] == 0
    assert score["current_target_selection"] == 1
    assert score["raw_recommendation_frame_occurrence"] == 1

    archived_option = case["aligned_history_option"]
    archived = case["archived_options"][archived_option]["canonical"]
    score = module.automatic_score(
        _row(case), persona, f"I recommend {archived}. {prefix} detail, {suffix}")
    assert score["selection_category"] == "ARCHIVED_ALIGNED"
    assert score["current_preferred_selection"] == 0
    assert score["current_target_selection"] == 0
    assert score["exact_history_intrusion"] == 1


def test_full_response_history_intrusion_is_not_first_sentence_only():
    bank = load(ROOT / module.CASE_BANK)
    case = bank["cases"][0]
    persona = bank["personas"][case["persona_id"]]
    prefix, suffix = _style_parts(persona)
    preferred = case["options"][case["preferred_option"]]["canonical"]
    archived = case["archived_options"][case["aligned_history_option"]]["canonical"]
    response = (f"I recommend {preferred}. {prefix} {archived} remains archived, {suffix}")
    score = module.automatic_score(_row(case), persona, response)
    assert score["current_preferred_selection"] == 1
    assert score["current_target_selection"] == 1
    assert score["exact_history_intrusion"] == 1
    assert score["exact_history_targets_in_full_response"] == [archived]
    assert score["strict_format_adherence"] == 0


def test_factorial_weights_bounds_and_lopo_preserve_missingness():
    bank = load(ROOT / module.CASE_BANK)
    design = load(ROOT / module.DESIGN)
    cases = [case["case_id"] for case in bank["cases"]]
    personas = {case["case_id"]: case["persona_id"] for case in bank["cases"]}
    by_case = {}
    for index, case_id in enumerate(cases):
        by_case[case_id] = {
            "SFH_ALIGNED_RAW": {"current_preferred_selection": 1},
            "SFH_ALIGNED_DECLARATIVE": {"current_preferred_selection": 1},
            "SFH_CONFLICT_RAW": {"current_preferred_selection": 0},
            "SFH_CONFLICT_DECLARATIVE": {
                "current_preferred_selection": None if index == 0 else 0},
        }
    weights = design["estimands"]["factorial_weights"][
        "H_SEMANTICS_ALIGNED_MINUS_CONFLICT"]
    summary = module.base.weighted_contrast(
        by_case, cases, weights, "current_preferred_selection", personas)
    assert summary["eligible_cases"] == 12
    assert summary["complete_cases"] == 11
    assert summary["unresolved_cases"] == 1
    assert summary["complete_case_estimate"] == 1.0
    assert summary["logical_lower"] < summary["logical_upper"]
    assert len(summary["leave_one_persona_out"]) == 12


def test_partial_analysis_materializes_every_absent_planned_cell_as_null():
    design, bank = load(ROOT / module.DESIGN), load(ROOT / module.CASE_BANK)
    persona_by_case = {case["case_id"]: case["persona_id"] for case in bank["cases"]}
    rows = [({**item, "persona_id": persona_by_case[item["case_id"]]}, None,
             "UNATTEMPTED", None) for item in design["order"]["requests"]]
    by_arm, by_case, latency, personas, results = module._analysis_inputs(rows)
    assert len(by_case) == 12
    assert all(len(cells) == 5 for cells in by_case.values())
    assert all(len(by_arm[arm]) == 12 for arm in module.ARMS)
    assert all(value is None for case in latency.values() for value in case.values())
    assert personas == persona_by_case
    assert results == []
    weights = design["estimands"]["factorial_weights"][
        "H_SEMANTICS_ALIGNED_MINUS_CONFLICT"]
    bounds = module.base.weighted_contrast(
        by_case, sorted(by_case), weights, "current_preferred_selection", personas)
    assert bounds["complete_cases"] == 0
    assert bounds["unresolved_cases"] == 12
    assert bounds["logical_lower"] == -1.0
    assert bounds["logical_upper"] == 1.0


def test_raw_without_derived_can_be_preserved_as_unscorable(monkeypatch):
    def fail(*_args, **_kwargs):
        raise ValueError("synthetic reconstruction failure")

    monkeypatch.setattr(module, "result", fail)
    archived_raw = {"response": {"content": "preserved",
                                  "tokens_predicted": 7,
                                  "stop_type": "eos", "stop": True},
                    "latency_seconds": 1.25}
    reconstructed, error = module._reconstruct_result(
        {"request_id": "offline-only"}, {}, archived_raw)
    assert reconstructed is None
    assert error == {"type": "ValueError",
                     "message": "synthetic reconstruction failure"}
    with pytest.raises(ValueError, match="no longer reproducible"):
        module._reconstruct_result(
            {"request_id": "offline-only"}, {},
            {"response": {"content": "preserved"}, "latency_seconds": 1.25},
            archived_derived={"already": "frozen"})

    plan = {"requests": [
        {"request_id": "offline-only", "max_new_tokens": 96},
        {"request_id": "invalid-native-fields", "max_new_tokens": 96},
        {"request_id": "absent-raw", "max_new_tokens": 96}]}
    raw = {"offline-only": archived_raw,
           "invalid-native-fields": {
               "response": {"content": "also preserved", "tokens_predicted": "7",
                            "stop_type": 9, "stop": "true"},
               "latency_seconds": -1}}
    resources = module._raw_resource_observations(plan, raw)
    assert resources["scorer_eligibility_independent"] is True
    assert resources["raw_completion_records"] == 2
    assert resources["missing_raw_completion_records"] == 1
    assert resources["generated_tokens"] is None
    assert resources["generated_tokens_observed_sum"] == 7
    assert resources["native_tokens_predicted"] == {
        "coverage_status": "PARTIAL", "valid_records": 1,
        "missing_records": 1, "invalid_records": 1}
    assert resources["native_stop_type_distribution"] == {"eos": 1}
    assert resources["native_stop_type_coverage"] == {
        "coverage_status": "PARTIAL", "valid_records": 1,
        "missing_records": 1, "invalid_records": 1}
    assert resources["native_stop_flag_distribution"] == {"True": 1}
    assert resources["completion_latency_seconds_observed_sum"] == 1.25
    assert resources["completion_latency_coverage"] == {
        "coverage_status": "PARTIAL", "valid_records": 1,
        "missing_records": 1, "invalid_records": 1}
    offline_row = {"request_id": "offline-only", "case_id": "case-1",
                   "arm": "SF_NO_H", "persona_id": "persona-1"}
    _, _, latency, _, scorable = module._analysis_inputs(
        [(offline_row, None, "RAW_UNSCORABLE", error)],
        {"offline-only": archived_raw})
    assert latency["case-1"]["SF_NO_H"] == 1.25
    assert scorable == []


def test_authorization_requirements_are_read_only_and_exactly_bounded():
    paths = (ROOT / module.AUTHORIZATION, ROOT / module.FROZEN,
             ROOT / module.PREFLIGHT, ROOT / module.ROOT / "claim.json",
             ROOT / module.ROOT / "native_tokenizer")
    before = {path: path.exists() for path in paths}
    required = module.authorization_requirements()
    assert required["maximum_native_tokenizer_calls"] == 60
    assert required["maximum_live_server_tokenizer_checks"] == 60
    assert required["maximum_tokenizer_operations_total"] == 120
    assert required["maximum_generation_attempts"] == 60
    assert required["retries"] == required["hidden_warmups"] == 0
    assert required["minimum_available_physical_ram_bytes"] == 3 * 1024**3
    assert required["actual_completion_inference_seconds_ceiling"] == 3600
    assert required["batch_wall_seconds_ceiling"] == 5400
    assert required["design"]["sha256"] == module.DESIGN_SHA
    assert required["case_bank"]["sha256"] == module.CASE_BANK_SHA
    assert required["validated_design"]["new_model_generations"] == 0
    assert {path: path.exists() for path in paths} == before


def test_failed_preflight_receipt_records_zero_execution(monkeypatch):
    def fail():
        raise ValueError("Less than 3 GiB available RAM")

    monkeypatch.setattr(module, "preflight", fail)
    monkeypatch.setattr(module.s, "memory_observation",
                        lambda _pid: {"system": {"available_physical": 123}})
    monkeypatch.setattr(module.shutil, "disk_usage",
                        lambda _path: type("Disk", (), {"free": 456})())
    receipt = module.preflight_receipt()
    assert receipt["status"] == "FAIL"
    assert receipt["error"]["message"] == "Less than 3 GiB available RAM"
    assert receipt["memory_observation"]["system"]["available_physical"] == 123
    assert receipt["free_output_disk_bytes"] == 456
    assert receipt["model_server_launches"] == 0
    assert receipt["completion_calls"] == 0
    assert receipt["new_model_generations"] == 0


def test_no_human_semantic_substitute_or_algorithm_claim_is_registered():
    design = load(ROOT / module.DESIGN)
    policy = design["evaluation_policy"]
    assert policy["semantic_reason_correctness"].startswith(
        "PENDING_BLINDED_HUMAN_REVIEW")
    assert "semantic reason correctness" in policy["human_only"]
    assert "No p-values" in design["estimands"]["inference"]
    assert "algorithm claim" in design["estimands"]["inference"]
    assert design["stopping_and_reporting"]["outcome_based_stopping"] is False

