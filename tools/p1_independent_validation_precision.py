"""Crossed-cluster precision planning for the proposed P1 validation cohort.

This is synthetic planning only. It does not create prompts, call a model, or
authorize the proposed 48-speaker experiment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path


SEED = 202610181
SPEAKERS = 48
CASES_PER_SPEAKER = 2
TEMPLATE_ANCESTORS = 8
CONDITIONS = 10
REQUESTS = SPEAKERS * CASES_PER_SPEAKER * CONDITIONS
Z_975 = statistics.NormalDist().inv_cdf(0.975)
T7_975 = 2.364624251
CENTRAL_MAX_HALFWIDTH = 0.15
CENTRAL_MIN_COVERAGE = 0.93


@dataclass(frozen=True)
class Scenario:
    name: str
    baseline_probability: float
    c3_log_odds_effect: float
    speaker_intercept_sd: float
    template_intercept_sd: float
    template_slope_sd: float
    case_intercept_sd: float
    paired_shared_uniform_probability: float
    missingness: str


SCENARIOS = (
    Scenario("null_calibration", 0.25, 0.0, 0.60, 0.25, 0.15, 0.35, 0.50, "none"),
    Scenario("central", 0.25, 0.60, 0.60, 0.25, 0.15, 0.35, 0.50, "none"),
    Scenario("high_template_dependence", 0.25, 0.60, 0.80, 0.50, 0.45, 0.45, 0.50, "none"),
    Scenario("outcome_dependent_missingness", 0.25, 0.60, 0.60, 0.25, 0.15, 0.35, 0.50, "outcome_dependent"),
)


def allocation() -> list[dict[str, int]]:
    rows = []
    for speaker in range(SPEAKERS):
        for case in range(CASES_PER_SPEAKER):
            rows.append(
                {
                    "speaker": speaker,
                    "case": case,
                    "template_ancestor": (speaker + 3 * case) % TEMPLATE_ANCESTORS,
                }
            )
    return rows


def logistic(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def logit(probability: float) -> float:
    return math.log(probability / (1.0 - probability))


def cluster_variance(values: list[float], groups: list[int]) -> float:
    mean = statistics.fmean(values)
    grouped: dict[int, float] = {}
    for value, group in zip(values, groups):
        grouped[group] = grouped.get(group, 0.0) + value - mean
    count = len(values)
    clusters = len(grouped)
    if count < 2 or clusters < 2:
        return float("nan")
    return clusters / (clusters - 1) * sum(value * value for value in grouped.values()) / (count * count)


def simulate_trial(rng: random.Random, scenario: Scenario) -> dict[str, float | bool]:
    base = logit(scenario.baseline_probability)
    template_intercepts = [rng.gauss(0.0, scenario.template_intercept_sd) for _ in range(TEMPLATE_ANCESTORS)]
    template_slopes = [rng.gauss(0.0, scenario.template_slope_sd) for _ in range(TEMPLATE_ANCESTORS)]
    speaker_intercepts = [rng.gauss(0.0, scenario.speaker_intercept_sd) for _ in range(SPEAKERS)]

    observed_values: list[float] = []
    observed_speakers: list[int] = []
    observed_templates: list[int] = []
    expected_differences: list[float] = []
    full_data_differences: list[float] = []
    lower_contributions: list[float] = []
    upper_contributions: list[float] = []

    for row in allocation():
        speaker = row["speaker"]
        template = row["template_ancestor"]
        shared = (
            base
            + speaker_intercepts[speaker]
            + template_intercepts[template]
            + rng.gauss(0.0, scenario.case_intercept_sd)
        )
        p0 = logistic(shared)
        p3 = logistic(shared + scenario.c3_log_odds_effect + template_slopes[template])
        expected_differences.append(p3 - p0)

        uniform0 = rng.random()
        uniform3 = uniform0 if rng.random() < scenario.paired_shared_uniform_probability else rng.random()
        y0 = float(uniform0 < p0)
        y3 = float(uniform3 < p3)
        full_data_differences.append(y3 - y0)
        missing0 = False
        missing3 = False
        if scenario.missingness == "outcome_dependent":
            missing0 = rng.random() < 0.03
            missing3 = rng.random() < (0.18 if y3 else 0.03)

        if not missing0 and not missing3:
            observed_values.append(y3 - y0)
            observed_speakers.append(speaker)
            observed_templates.append(template)

        if missing0 and missing3:
            lower_contributions.append(-1.0)
            upper_contributions.append(1.0)
        elif missing0:
            lower_contributions.append(y3 - 1.0)
            upper_contributions.append(y3)
        elif missing3:
            lower_contributions.append(-y0)
            upper_contributions.append(1.0 - y0)
        else:
            lower_contributions.append(y3 - y0)
            upper_contributions.append(y3 - y0)

    estimate = statistics.fmean(observed_values)
    conditional_target = statistics.fmean(expected_differences)
    full_data_realized_estimand = statistics.fmean(full_data_differences)
    speaker_variance = cluster_variance(observed_values, observed_speakers)
    template_variance = cluster_variance(observed_values, observed_templates)
    case_variance = cluster_variance(observed_values, list(range(len(observed_values))))
    two_way_variance_raw = speaker_variance + template_variance - case_variance
    two_way_variance = max(0.0, two_way_variance_raw)
    speaker_halfwidth = Z_975 * math.sqrt(speaker_variance)
    two_way_halfwidth = T7_975 * math.sqrt(two_way_variance)
    lower_bound = statistics.fmean(lower_contributions)
    upper_bound = statistics.fmean(upper_contributions)
    return {
        "estimate": estimate,
        "conditional_target": conditional_target,
        "speaker_halfwidth": speaker_halfwidth,
        "two_way_halfwidth": two_way_halfwidth,
        "speaker_coverage": abs(estimate - conditional_target) <= speaker_halfwidth,
        "two_way_coverage": abs(estimate - conditional_target) <= two_way_halfwidth,
        "two_way_nonpositive_variance": two_way_variance_raw <= 0.0,
        "complete_pair_fraction": len(observed_values) / len(expected_differences),
        "missingness_bound_width": upper_bound - lower_bound,
        "missingness_bound_covers_full_data_realized_estimand": (
            lower_bound <= full_data_realized_estimand <= upper_bound
        ),
    }


def summarize(scenario: Scenario, index: int, replicates: int) -> dict[str, object]:
    trials = [
        simulate_trial(random.Random(SEED + index * 1_000_003 + replicate), scenario)
        for replicate in range(replicates)
    ]
    estimates = [float(row["estimate"]) for row in trials]
    targets = [float(row["conditional_target"]) for row in trials]
    return {
        "scenario": asdict(scenario),
        "replicates": replicates,
        "mean_conditional_template_target": statistics.fmean(targets),
        "mean_estimate": statistics.fmean(estimates),
        "mean_bias_for_conditional_template_target": statistics.fmean(
            estimate - target for estimate, target in zip(estimates, targets)
        ),
        "empirical_estimate_sd": statistics.stdev(estimates),
        "median_speaker_only_95_halfwidth": statistics.median(
            float(row["speaker_halfwidth"]) for row in trials
        ),
        "speaker_only_conditional_target_coverage": statistics.fmean(
            bool(row["speaker_coverage"]) for row in trials
        ),
        "median_two_way_cluster_95_halfwidth": statistics.median(
            float(row["two_way_halfwidth"]) for row in trials
        ),
        "two_way_cluster_conditional_target_coverage": statistics.fmean(
            bool(row["two_way_coverage"]) for row in trials
        ),
        "two_way_nonpositive_variance_fraction": statistics.fmean(
            bool(row["two_way_nonpositive_variance"]) for row in trials
        ),
        "median_complete_pair_fraction": statistics.median(
            float(row["complete_pair_fraction"]) for row in trials
        ),
        "mean_worst_case_missingness_bound_width": statistics.fmean(
            float(row["missingness_bound_width"]) for row in trials
        ),
        "worst_case_missingness_bound_full_data_coverage": statistics.fmean(
            bool(row["missingness_bound_covers_full_data_realized_estimand"]) for row in trials
        ),
    }


def source_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def build_report(replicates: int = 2_000) -> dict[str, object]:
    if replicates < 2:
        raise ValueError("replicates must be at least 2")
    summaries = [summarize(scenario, index, replicates) for index, scenario in enumerate(SCENARIOS)]
    central = next(row for row in summaries if row["scenario"]["name"] == "central")
    central_pass = (
        central["median_two_way_cluster_95_halfwidth"] <= CENTRAL_MAX_HALFWIDTH
        and central["two_way_cluster_conditional_target_coverage"] >= CENTRAL_MIN_COVERAGE
    )
    return {
        "schema_version": "personaslm_p1_independent_validation_precision_v1",
        "status": "SYNTHETIC_PLANNING_COMPLETE_NO_INFERENCE",
        "source_sha256": source_sha256(),
        "seed": SEED,
        "design": {
            "speakers": SPEAKERS,
            "cases_per_speaker": CASES_PER_SPEAKER,
            "cases": SPEAKERS * CASES_PER_SPEAKER,
            "template_ancestors": TEMPLATE_ANCESTORS,
            "conditions": CONDITIONS,
            "condition_ids": ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "N_style", "N_history"],
            "requests": REQUESTS,
            "primary_contrast": "C3_minus_C0_outdated_value_adoption_risk_difference",
            "balanced_template_cases": {
                str(template): sum(row["template_ancestor"] == template for row in allocation())
                for template in range(TEMPLATE_ANCESTORS)
            },
        },
        "prospective_acceptance_rule": {
            "scenario": "central",
            "maximum_median_two_way_cluster_95_halfwidth": CENTRAL_MAX_HALFWIDTH,
            "minimum_two_way_cluster_conditional_target_coverage": CENTRAL_MIN_COVERAGE,
            "interpretation": "Planning gate only. Passing does not freeze or authorize a cohort; failing requires redesign rather than post-hoc relaxation.",
        },
        "estimator": {
            "point": "mean paired binary difference across complete C3/C0 case pairs",
            "speaker_only_interval": "normal 95% speaker-cluster sandwich",
            "two_way_interval": "speaker plus template minus case sandwich with t(7) critical value",
            "missingness": "all-case logical worst-case bounds for the realized finite-cohort contrast; no unknown outcome is recoded as false",
            "target": "conditional mean effect over the eight sampled new template ancestors",
        },
        "summaries": summaries,
        "central_planning_decision": (
            "MEETS_DECLARED_SIMULATED_CENTRAL_PRECISION_AND_COVERAGE_RULE"
            if central_pass
            else "DOES_NOT_MEET_DECLARED_SIMULATED_CENTRAL_PRECISION_AND_COVERAGE_RULE"
        ),
        "scientific_limits": [
            "All probabilities, dependence parameters, and missingness mechanisms are assumptions, not fitted PersonaSLM estimates.",
            "Eight authored template ancestors do not identify a broad new-template population; the coverage target is conditional on the sampled templates.",
            "Only the primary C3-C0 binary contrast is simulated. The remaining conditions consume budget but do not improve its paired precision, and high-order interactions can be much less precise.",
            "The normal and small-template-cluster sandwich approximations may still miscover with 48 purposive speakers and eight templates.",
            "Condition-dependent missingness can bias complete-pair estimates; worst-case bounds, genuine review coverage, and a missingness policy remain mandatory.",
            "No cohort, prompt, endpoint, multiplicity policy, or experiment is frozen or authorized by this artifact.",
        ],
        "execution_impact": {
            "scientific_model_generations": 0,
            "inference_seconds": 0.0,
            "human_annotations": 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=2_000)
    args = parser.parse_args()
    report = build_report(args.replicates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "requests_planned_not_executed": REQUESTS,
                "replicates": args.replicates,
                "decision": report["central_planning_decision"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
