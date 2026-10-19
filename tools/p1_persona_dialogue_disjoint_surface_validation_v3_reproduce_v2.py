"""Append-only scope correction for the v3 analysis reproduction receipt.

This zero-inference program preserves and verifies the v1 receipt, reruns its
controller-independent reconstruction, and corrects only the denominator used
to describe the post-hoc literal-placeholder name audit.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

import p1_persona_dialogue_disjoint_surface_validation_v3_reproduce as v1


V1_RECEIPT = v1.VALIDATION / "analysis_reproduction_v1.json"
V1_RECEIPT_SHA256 = "8b521427849353497869c0626c946f5e4716f7c7abe1d5f661233dc4f8641cfb"
V1_SCRIPT_SHA256 = "eaa3c4145c19fab46be4e51a46c8b378d65751d8ba8b7506d58c11e99c7dead6"
V1_TEST_SHA256 = "01ceca641b220437800186f15e36a196ce926d5c30b5c2de7e204a88f25339eb"
DEFAULT_OUTPUT = v1.VALIDATION / "analysis_reproduction_v2.json"
TEST_PATH = Path(
    "tests/test_p1_persona_dialogue_disjoint_surface_validation_v3_reproduce_v2.py"
)


def _indexed(events: list[dict], kind: str) -> dict[str, dict]:
    records = [event["data"] for event in events if event["kind"] == kind]
    v1._require(
        len(records) == len({record["request_id"] for record in records}),
        f"Duplicate {kind}",
    )
    return {record["request_id"]: record for record in records}


def _literal_name_summary(rows: list[dict], name_field: str) -> dict:
    return {
        "hits_in_first_sentence": sum(
            row[name_field] in row["first_sentence"] for row in rows
        ),
        "hits_in_full_response": sum(row[name_field] in row["raw_text"] for row in rows),
        "denominator": len(rows),
        "matching_rule": (
            "Case-sensitive exact canonical-name string as a literal substring of "
            "decoded Unicode text; no normalization, fuzzy match, or JSON-escape scan."
        ),
    }


def _corrected_post_hoc_audit() -> dict:
    _, events = v1._read_journal()
    starts = _indexed(events, "disjoint_surface_validation_v3_generation_started")
    raws = _indexed(events, "disjoint_surface_validation_v3_raw_generation")
    derived = _indexed(events, "disjoint_surface_validation_v3_result")
    v1._require(
        len(starts) == len(raws) == len(derived) == 168
        and set(starts) == set(raws) == set(derived),
        "Post-hoc raw-event request accounting changed",
    )

    rows = []
    for request_id in sorted(starts, key=lambda value: starts[value]["order"]):
        started = starts[request_id]
        row = v1._rescore(started, raws[request_id], derived[request_id])
        nonpreferred_option = "B" if started["preferred_option"] == "A" else "A"
        row["nonpreferred_name"] = started["options"][nonpreferred_option]["canonical"]
        v1._require(
            row["preferred_name"]
            and row["nonpreferred_name"]
            and row["preferred_name"] != row["nonpreferred_name"],
            f"Invalid canonical names: {request_id}",
        )
        rows.append(row)

    history_rows = [row for row in rows if row["arm"] != "SF_NO_H"]
    placeholder_rows = [
        row for row in history_rows if v1.ANCHOR_PLACEHOLDER.search(row["raw_text"])
    ]
    none_rows = [
        row for row in placeholder_rows if row["selection_category"] == "NONE"
    ]
    any_exact_rows = [row for row in history_rows if "<exact" in row["raw_text"]]
    category_distribution = dict(
        sorted(Counter(row["selection_category"] for row in placeholder_rows).items())
    )
    preferred_names = _literal_name_summary(none_rows, "preferred_name")
    nonpreferred_names = _literal_name_summary(none_rows, "nonpreferred_name")
    all_preferred_names = _literal_name_summary(placeholder_rows, "preferred_name")
    all_nonpreferred_names = _literal_name_summary(placeholder_rows, "nonpreferred_name")

    v1._require(len(history_rows) == 144, "History-conditioned denominator changed")
    v1._require(len(placeholder_rows) == 24, "Literal placeholder numerator changed")
    v1._require(
        category_distribution == {"CURRENT_PREFERRED": 1, "NONE": 23},
        "Literal placeholder selection-category distribution changed",
    )
    v1._require(len(none_rows) == 23, "Literal placeholder NONE subset changed")
    v1._require(
        preferred_names["hits_in_first_sentence"]
        == preferred_names["hits_in_full_response"]
        == 23
        and nonpreferred_names["hits_in_first_sentence"]
        == nonpreferred_names["hits_in_full_response"]
        == 0,
        "Literal placeholder NONE-subset canonical-name result changed",
    )
    v1._require(
        all_preferred_names["hits_in_first_sentence"]
        == all_preferred_names["hits_in_full_response"]
        == 24
        and all_nonpreferred_names["hits_in_first_sentence"]
        == all_nonpreferred_names["hits_in_full_response"]
        == 0,
        "All-placeholder canonical-name result changed",
    )

    nonpreferred = [
        row for row in rows if row["selection_category"] == "CURRENT_NONPREFERRED"
    ]
    persona_distribution = dict(
        sorted(Counter(row["persona_id"] for row in nonpreferred).items())
    )
    case_distribution = dict(
        sorted(Counter(row["case_id"] for row in nonpreferred).items())
    )
    v1._require(
        len(nonpreferred) == 8 and persona_distribution == {"DSV_P02": 8},
        "Nonpreferred-selection concentration changed",
    )

    return {
        "classification": "POST_HOC_EXPLORATORY_NOT_PREREGISTERED_NOT_CONFIRMATORY",
        "separation_from_registered_estimands": True,
        "literal_anchor_placeholder_subset": {
            "source_event_kind": "disjoint_surface_validation_v3_raw_generation",
            "source_decoded_field": "event.data.response.content",
            "counting_stage": "AFTER_JSON_LOADS_ON_DECODED_UNICODE_TEXT",
            "escaped_json_representation_scanned": False,
            "case_sensitive_regex": v1.ANCHOR_PLACEHOLDER_PATTERN,
            "exact_utf8_literal_hex": {
                "<exact A anchor>": "3c6578616374204120616e63686f723e",
                "<exact B anchor>": "3c6578616374204220616e63686f723e",
            },
            "scope_note": (
                "The 24 numerator contains only decoded response text matching the exact "
                "A/B anchor-placeholder regex; serialized JSON bytes and name-only "
                "placeholders are not counted."
            ),
            "hits": len(placeholder_rows),
            "history_conditioned_denominator": len(history_rows),
            "fraction": len(placeholder_rows) / len(history_rows),
            "any_decoded_less_than_exact_substring_outputs": len(any_exact_rows),
            "selection_category_source": (
                "Independently reconstructed from each decoded raw first sentence and "
                "frozen anchors, then checked against the archived automatic score."
            ),
            "selection_category_distribution": category_distribution,
            "scorer_none_count": len(none_rows),
            "scorer_none_subset": {
                "preferred_canonical_name": preferred_names,
                "nonpreferred_canonical_name": nonpreferred_names,
            },
            "all_placeholder_rows": {
                "preferred_canonical_name": all_preferred_names,
                "nonpreferred_canonical_name": all_nonpreferred_names,
            },
            "current_preferred_request_ids": sorted(
                row["request_id"]
                for row in placeholder_rows
                if row["selection_category"] == "CURRENT_PREFERRED"
            ),
            "arm_distribution": dict(
                sorted(Counter(row["arm"] for row in placeholder_rows).items())
            ),
            "persona_distribution": dict(
                sorted(Counter(row["persona_id"] for row in placeholder_rows).items())
            ),
        },
        "current_nonpreferred_selection_concentration": {
            "count": len(nonpreferred),
            "persona_distribution": persona_distribution,
            "case_distribution": case_distribution,
            "interpretation_limit": (
                "Observed concentration only; it is not a registered persona effect or "
                "causal explanation."
            ),
        },
    }


def build_report() -> dict:
    v1._require(v1._sha256(V1_RECEIPT) == V1_RECEIPT_SHA256, "V1 receipt changed")
    v1._require(v1._sha256(Path(v1.__file__)) == V1_SCRIPT_SHA256, "V1 script changed")
    v1._require(v1._sha256(v1.TEST_PATH) == V1_TEST_SHA256, "V1 test changed")
    prior = v1._load(V1_RECEIPT)
    report = v1.build_report()
    v1._require(report == prior, "Fresh v1 reconstruction differs from preserved receipt")

    report["schema_version"] = "personaslm_disjoint_surface_analysis_reproduction_v2"
    report["status"] = "PASS_ZERO_DIFFERENCES_WITH_APPEND_ONLY_POST_HOC_SCOPE_CORRECTION"
    report["reproduction_type"] = (
        "APPEND_ONLY_SCOPE_CORRECTION_OVER_VERIFIED_V1_INDEPENDENT_RECONSTRUCTION"
    )
    report["analysis_code"] = {
        "path": Path(__file__).resolve().relative_to(v1.PROJECT_ROOT).as_posix(),
        "sha256": v1._sha256(Path(__file__).resolve()),
        "controller_imported": False,
        "archived_analyze_called": False,
        "verified_core_reconstruction_dependency": {
            "path": Path(v1.__file__).resolve().relative_to(v1.PROJECT_ROOT).as_posix(),
            "sha256": V1_SCRIPT_SHA256,
        },
    }
    report["test_code"] = {
        "path": TEST_PATH.as_posix(),
        "sha256": v1._sha256(TEST_PATH),
    }
    report["append_only_correction"] = {
        "classification": "APPEND_ONLY_POST_HOC_DENOMINATOR_SCOPE_CORRECTION",
        "prior_receipt": {
            "path": V1_RECEIPT.as_posix(),
            "sha256": V1_RECEIPT_SHA256,
            "preserved_byte_for_byte": True,
        },
        "registered_estimands_changed": False,
        "condition_summaries_changed": False,
        "resource_or_budget_accounting_changed": False,
        "correction_scope": (
            "V1's 23/23 canonical-name observation used the 23 preferred SF_NO_H "
            "responses. V2 separately answers the intended question for the 23 scorer-NONE "
            "records inside the 24 literal anchor-placeholder history-conditioned outputs."
        ),
        "v1_observation_disposition": {
            "v1_field": (
                "post_hoc_exploratory_audit."
                "no_history_preferred_anchor_with_preferred_name_in_first_sentence"
            ),
            "v1_numerator": 23,
            "v1_denominator": 23,
            "v1_denominator_definition": (
                "SF_NO_H responses independently scored as selecting the preferred "
                "current anchor."
            ),
            "status": "FACTUALLY_TRUE_BUT_DIFFERENT_DENOMINATOR_NOT_USED_FOR_CORRECTED_CLAIM",
        },
    }
    report["post_hoc_exploratory_audit"] = _corrected_post_hoc_audit()
    report["analysis_reproducibility_decision"] = {
        "decision": "GO",
        "basis": (
            "All registered scores, 14 automatic estimands, LOPO/task strata, resources, "
            "and budgets reproduce with zero differences; the post-hoc denominator scope "
            "is corrected append-only and does not alter registered results."
        ),
    }
    report["scientific_limits"] = [
        item
        for item in report["scientific_limits"]
        if not item.startswith("The three explicitly separated post-hoc audits")
    ] + [
        "The corrected literal-placeholder/name and nonpreferred-concentration audits are post-hoc exploratory observations and cannot revise the registered estimands."
    ]
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    report = build_report()
    v1._write_exclusive(arguments.output, report)
    output = (
        arguments.output
        if arguments.output.is_absolute()
        else v1.PROJECT_ROOT / arguments.output
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "output": output.relative_to(v1.PROJECT_ROOT).as_posix(),
                "sha256": v1._sha256(output),
                "model_calls": 0,
                "new_generations": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
