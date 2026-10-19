"""Build a prospective estimation-first P1 analysis candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import p1c_paired_statistics as paired  # noqa: E402


TOOL = Path("tools/p1_independent_validation_estimation_candidate.py")
DESTINATION = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_estimation_candidate_v1.json"
)
PROTOCOL = Path("docs/research_protocol_v1.1.md")
MULTIPLICITY = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_multiplicity_candidate_v1.json"
)
PRECISION = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_precision_v1.json"
)
MISSINGNESS = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_missingness_policy_v2.json"
)
CALIBRATIONS = (
    Path(
        "docs/validation/p1/model_feasibility_recovery_v1/"
        "independent_validation_test_calibration_v1.json"
    ),
    Path(
        "docs/validation/p1/model_feasibility_recovery_v1/"
        "independent_validation_test_calibration_v2.json"
    ),
)
PAIRED_TOOL = Path("tools/p1c_paired_statistics.py")
DEPENDENCIES = (
    PROTOCOL, MULTIPLICITY, PRECISION, MISSINGNESS, *CALIBRATIONS, PAIRED_TOOL
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def validated_inputs() -> tuple[dict, dict, dict, list[dict]]:
    multiplicity = load(MULTIPLICITY)
    precision = load(PRECISION)
    missingness = load(MISSINGNESS)
    calibrations = [load(path) for path in CALIBRATIONS]

    family = multiplicity["candidate_endpoint_hierarchy"]["confirmatory_family"]
    require(len(family) == len(set(family)) == 11, "Eleven-contrast family changed")
    require(set(missingness["contrast_registry"]) == set(family),
            "Missingness and multiplicity contrast families differ")
    require(missingness["contrast_registry"] == multiplicity["candidate_contrast_registry"],
            "Contrast weights differ between predecessor artifacts")
    require(missingness["inferential_boundary"]["status"]
            == "NO_CALIBRATED_CONFIRMATORY_TEST_IDENTIFIED",
            "Missingness inferential boundary changed")
    require(all(
        row["calibration_decision"]["decision"].startswith("DOES_NOT_MEET_")
        for row in calibrations
    ), "A predecessor calibration no longer records a negative decision")

    design = precision["design"]
    require(
        (design["speakers"], design["cases"], design["cases_per_speaker"],
         design["template_ancestors"])
        == (48, 96, 2, 8),
        "Prospective finite-cohort design changed",
    )
    require(design["primary_contrast"]
            == "C3_minus_C0_outdated_value_adoption_risk_difference",
            "Lead planning contrast changed")
    return multiplicity, precision, missingness, calibrations


def aggregate_finite_cohort(
    cases: list[dict],
    contrast_weights: dict[str, float],
    *,
    expected_speakers: int = 48,
    cases_per_speaker: int = 2,
) -> dict:
    """Apply signed case bounds, then equal speaker weighting, without deletion."""
    require(cases and cases_per_speaker > 0, "Cases and cases_per_speaker are required")
    case_ids = [row.get("case_id") for row in cases]
    require(all(isinstance(value, str) and value for value in case_ids),
            "Every case requires a nonempty case_id")
    require(len(case_ids) == len(set(case_ids)), "Case IDs must be unique")

    grouped: dict[str, list[dict]] = {}
    unknown_active_cells = 0
    for row in cases:
        speaker = row.get("speaker_id")
        require(isinstance(speaker, str) and speaker, "Every case requires a speaker_id")
        outcomes = row.get("outcomes")
        require(isinstance(outcomes, dict), "Every case requires an outcomes mapping")
        bounded = paired.case_contrast(outcomes, contrast_weights)
        unknown_active_cells += len(bounded["unknown_cells"])
        grouped.setdefault(speaker, []).append(bounded)

    require(all(len(rows) == cases_per_speaker for rows in grouped.values()),
            "Every speaker must have the prospectively fixed number of cases")
    require(expected_speakers > 0, "Expected speaker count must be positive")
    require(len(grouped) == expected_speakers, "Speaker count changed")

    speaker_rows = []
    for speaker, rows in sorted(grouped.items()):
        speaker_rows.append({
            "speaker_id": speaker,
            "estimate": (
                None if any(row["estimate"] is None for row in rows)
                else statistics.mean(row["estimate"] for row in rows)
            ),
            "lower_bound": statistics.mean(row["lower_bound"] for row in rows),
            "upper_bound": statistics.mean(row["upper_bound"] for row in rows),
        })
    all_known = all(row["estimate"] is not None for row in speaker_rows)
    return {
        "eligible_cases": len(cases),
        "speakers": len(speaker_rows),
        "cases_per_speaker": cases_per_speaker,
        "unknown_active_cells": unknown_active_cells,
        "estimate": (
            statistics.mean(row["estimate"] for row in speaker_rows)
            if all_known else None
        ),
        "lower_bound": statistics.mean(row["lower_bound"] for row in speaker_rows),
        "upper_bound": statistics.mean(row["upper_bound"] for row in speaker_rows),
        "speaker_rows": speaker_rows,
    }


def build_report() -> dict:
    multiplicity, precision, missingness, calibrations = validated_inputs()
    family = multiplicity["candidate_endpoint_hierarchy"]["confirmatory_family"]
    registry = {
        name: multiplicity["candidate_contrast_registry"][name] for name in family
    }
    precision_by_name = {
        row["scenario"]["name"]: row for row in precision["summaries"]
    }
    return {
        "schema_version": "personaslm_p1_independent_validation_estimation_candidate_v1",
        "status": "PROSPECTIVE_ESTIMATION_FIRST_CANDIDATE_PENDING_PILOT_AND_RESEARCHER_ADOPTION",
        "historical_effect": (
            "No historical output, annotation, score, gate, estimand, threshold, or negative "
            "calibration result is changed."
        ),
        "scope": {
            "purpose": (
                "Prospective outcome-blind candidate for reporting the independent finite cohort "
                "when no calibrated confirmatory test has been identified."
            ),
            "not_a_protocol_amendment": True,
            "not_a_confirmatory_freeze": True,
            "cohort_authorized": False,
            "target": (
                "Conditional target if adopted: the realized cohort after its exact inventory is "
                "prospectively frozen, using 96 cases, 48 purposively selected speakers, two cases "
                "per speaker, and eight fixed template ancestors; no broad speaker or new-template "
                "population generalization."
            ),
        },
        "endpoint_and_estimands": {
            "primary_endpoint": (
                "Binary outdated-value adoption from genuine blinded semantic review; unavailable "
                "review is missing and is never recoded as zero or UNCERTAIN."
            ),
            "lead_reporting_estimand": "C3-C0",
            "lead_status": (
                "Designated lead reporting estimand; it receives no privileged test, alpha, or claim."
            ),
            "fixed_contrast_order": family,
            "contrast_registry": registry,
            "neutral_control_rule": (
                "C1-N_style and C3-N_history remain inactive unless the exact controls receive "
                "prospective semantic adoption before cohort freeze."
            ),
            "aggregation": [
                "For every eligible case, apply the candidate-specified signed contrast weights to the active cell outcomes; unknown cells contribute endpoint-range lower and upper bounds by weight sign.",
                "Average the two case-level points or bounds within each speaker without deleting an unknown case.",
                "Average the 48 speaker-level points or bounds with equal speaker weight and no data-dependent reweighting.",
            ],
            "reference_implementation": "aggregate_finite_cohort in the hash-bound source tool.",
        },
        "primary_reporting": {
            "required_for_every_active_contrast": [
                "Point estimate when the all-eligible contrast is identified.",
                "Signed logical lower and upper identification bounds when any active cell is unknown.",
                "All assigned, eligible, reviewed, missing, and category-specific denominators.",
                "The full mutually exclusive semantic outcome distribution, not only the binary endpoint.",
                "Direction and magnitude regardless of whether they match an expectation.",
            ],
            "missingness_policy": {
                **missingness["analysis_rules"],
                "cluster_sensitivity": (
                    "The predecessor's speaker-cluster and two-way interval sensitivities are "
                    "not activated by this candidate because no interval-like procedure is "
                    "prospectively specified and calibrated here."
                ),
            },
            "no_decision_rule": (
                "No p-value, rejection, significance, equivalence, non-inferiority, success/failure, "
                "or no-effect decision is authorized by this candidate."
            ),
        },
        "sensitivity_reporting": {
            "allowed": [
                "Complete-pair estimates, which are selected-subset estimands, with their exact changing denominators.",
                "Template leave-one-ancestor-out estimate ranges labeled finite-template sensitivity only.",
            ],
            "forbidden_interpretation": [
                "Do not call a sensitivity range a calibrated confidence interval.",
                "Do not infer a p-value, rejection, significance, equivalence, or absence of effect.",
                "Do not analyze another outcome-defined subset unless it was separately justified and frozen before outputs or labels were inspected.",
                "No interval-like sensitivity procedure is authorized here; any future formula, reference distribution, seed, and replicate count must be prospectively frozen and all registered variants reported.",
            ],
        },
        "calibration_evidence": {
            "boundary": "NO_CALIBRATED_CONFIRMATORY_TEST_IDENTIFIED",
            "negative_results": [
                {
                    "path": path.as_posix(),
                    "sha256": sha256(path),
                    "decision": report["calibration_decision"]["decision"],
                }
                for path, report in zip(CALIBRATIONS, calibrations)
            ],
            "precision_context_not_acceptance_evidence": {
                "central_median_two_way_halfwidth": precision_by_name["central"][
                    "median_two_way_cluster_95_halfwidth"
                ],
                "high_template_median_two_way_halfwidth": precision_by_name[
                    "high_template_dependence"
                ]["median_two_way_cluster_95_halfwidth"],
                "outcome_dependent_missingness_mean_complete_pair_bias": precision_by_name[
                    "outcome_dependent_missingness"
                ]["mean_bias_for_conditional_template_target"],
                "interpretation": (
                    "These synthetic planning summaries motivate transparent estimation and signed "
                    "bounds; they do not calibrate hypothesis tests or establish empirical effects."
                ),
            },
        },
        "prospective_lock": {
            "must_precede": "Any inspection of independent-cohort model outputs or human outcome labels.",
            "required_before_adoption": [
                "A viable selected model and passed disjoint C0 gate.",
                "An interpretable development factorial pilot.",
                "Genuine semantic adoption or explicit exclusion of each neutral control.",
                "A frozen cohort, applicability matrix, blinded annotation plan, and inter-rater calibration plan.",
                "Researcher review and explicit adoption of this estimation-only policy.",
            ],
            "anti_shopping": [
                "Do not search additional tests merely because both recorded candidates failed.",
                "Do not relax calibration thresholds, discard unfavorable contrasts, or rerun seeds until passing.",
                "Any future inferential candidate requires a separately frozen one-shot validation bank.",
            ],
            "researcher_adopted": False,
            "cohort_authorized": False,
        },
        "scientific_limits": [
            "Estimation-first reporting does not create calibrated frequentist coverage or a confirmatory test.",
            "Purposive speakers and eight authored template ancestors limit generalization to the finite cohort.",
            "Signed bounds can be wide and may not identify the direction of an effect.",
            "The endpoint remains dependent on genuine blinded human review and inter-rater calibration.",
            "No algorithmic novelty, model superiority, or Persona Fidelity validity follows from this artifact.",
        ],
        "compatibility": {
            "dependency_sha256": {path.as_posix(): sha256(path) for path in DEPENDENCIES},
            "source_sha256": sha256(TOOL),
        },
        "execution_impact": {
            "scientific_model_generations": 0,
            "inference_seconds": 0.0,
            "human_annotations": 0,
            "cohort_authorized": False,
        },
    }


def write_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), f"Refusing to overwrite existing evidence: {path}")
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DESTINATION)
    arguments = parser.parse_args()
    report = build_report()
    write_new(arguments.output, report)
    print(json.dumps({
        "status": report["status"],
        "contrasts": len(report["endpoint_and_estimands"]["fixed_contrast_order"]),
        "inferential_boundary": report["calibration_evidence"]["boundary"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
