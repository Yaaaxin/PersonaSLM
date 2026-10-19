"""Calibrate speaker-cluster tests for the finite-template P1 target after v1 failed."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import p1_independent_validation_multiplicity as multiplicity  # noqa: E402
import p1_independent_validation_precision as precision  # noqa: E402
import p1_independent_validation_test_calibration as calibration_v1  # noqa: E402


TOOL = Path("tools/p1_independent_validation_test_calibration_v2.py")
DESTINATION = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_test_calibration_v2.json"
)
V1_ARTIFACT = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_test_calibration_v1.json"
)
REPLICATES = 3_000
SEED = 202610183
DF = precision.SPEAKERS - 1
MAX_FWER_UPPER_95 = 0.06
MAX_MARGINAL_TYPE1_UPPER_95 = 0.065
MAX_UNTESTABLE_FRACTION = 0.02
FAMILY = multiplicity.CONFIRMATORY_FAMILY
REGISTRY = multiplicity.contrast_registry()
ALLOCATION = precision.allocation()
CONDITIONS = tuple(next(iter(REGISTRY.values())))
DEPENDENCIES = (
    Path("tools/p1_independent_validation_precision.py"),
    Path("tools/p1_independent_validation_multiplicity.py"),
    Path("tools/p1_independent_validation_test_calibration.py"),
    V1_ARTIFACT,
)


@dataclass(frozen=True)
class NullScenario:
    name: str
    baseline_probability: float
    speaker_intercept_sd: float
    template_intercept_sd: float
    case_intercept_sd: float
    shared_uniform_probability: float
    condition_template_slope_sd: float


SCENARIOS = (
    NullScenario("central_null", 0.25, 0.60, 0.25, 0.35, 0.50, 0.0),
    NullScenario("high_cluster_dependence_null", 0.25, 0.80, 0.50, 0.45, 0.50, 0.0),
    NullScenario("rare_outcome_null", 0.05, 0.60, 0.25, 0.35, 0.50, 0.0),
    NullScenario("balanced_condition_by_template_null", 0.25, 0.60, 0.25, 0.35, 0.50, 0.45),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def equalizing_shift(
    base_logits: list[float], templates: list[int], slopes: list[float], target: float
) -> float:
    """Set the finite 96-case expected mean to the shared null target."""
    low, high = -20.0, 20.0
    for _ in range(80):
        midpoint = (low + high) / 2.0
        observed = statistics.fmean(
            precision.logistic(logit + slopes[template] + midpoint)
            for logit, template in zip(base_logits, templates)
        )
        if observed < target:
            low = midpoint
        else:
            high = midpoint
    shift = (low + high) / 2.0
    achieved = statistics.fmean(
        precision.logistic(logit + slopes[template] + shift)
        for logit, template in zip(base_logits, templates)
    )
    require(math.isclose(achieved, target, abs_tol=1e-12), "Null mean equalization failed")
    return shift


def simulate_trial(rng: random.Random, scenario: NullScenario) -> dict:
    template_effects = [
        rng.gauss(0.0, scenario.template_intercept_sd)
        for _ in range(precision.TEMPLATE_ANCESTORS)
    ]
    speaker_effects = [
        rng.gauss(0.0, scenario.speaker_intercept_sd)
        for _ in range(precision.SPEAKERS)
    ]
    templates = [row["template_ancestor"] for row in ALLOCATION]
    speakers = [row["speaker"] for row in ALLOCATION]
    base = precision.logit(scenario.baseline_probability)
    base_logits = [
        base + speaker_effects[row["speaker"]] + template_effects[row["template_ancestor"]]
        + rng.gauss(0.0, scenario.case_intercept_sd)
        for row in ALLOCATION
    ]
    target = statistics.fmean(precision.logistic(logit) for logit in base_logits)
    probabilities = {}
    for condition in CONDITIONS:
        if scenario.condition_template_slope_sd == 0.0:
            probabilities[condition] = [precision.logistic(logit) for logit in base_logits]
            continue
        slopes = [
            rng.gauss(0.0, scenario.condition_template_slope_sd)
            for _ in range(precision.TEMPLATE_ANCESTORS)
        ]
        shift = equalizing_shift(base_logits, templates, slopes, target)
        probabilities[condition] = [
            precision.logistic(logit + slopes[template] + shift)
            for logit, template in zip(base_logits, templates)
        ]

    contributions = {name: [] for name in FAMILY}
    for case_index in range(len(ALLOCATION)):
        common_uniform = rng.random()
        outcomes = {
            condition: float(
                (common_uniform if rng.random() < scenario.shared_uniform_probability else rng.random())
                < probabilities[condition][case_index]
            )
            for condition in CONDITIONS
        }
        for name, contrast_weights in REGISTRY.items():
            contributions[name].append(sum(
                contrast_weights[condition] * outcomes[condition]
                for condition in CONDITIONS
            ))

    pvalues = {}
    nonpositive = {}
    for name in FAMILY:
        values = contributions[name]
        estimate = statistics.fmean(values)
        variance = precision.cluster_variance(values, speakers)
        nonpositive[name] = variance <= 0.0
        pvalues[name] = (
            None if variance <= 0.0
            else calibration_v1.student_t_two_sided_p(abs(estimate) / math.sqrt(variance), DF)
        )
    holm = multiplicity.holm_adjust(pvalues, FAMILY)
    return {
        "pvalues": pvalues,
        "holm_rejections": {
            row["hypothesis"]: row["reject"] for row in holm["rows"]
        },
        "nonpositive_variance": nonpositive,
    }


def summarize(scenario: NullScenario, scenario_index: int, replicates: int) -> dict:
    trials = [
        simulate_trial(random.Random(SEED + scenario_index * 1_000_003 + replicate), scenario)
        for replicate in range(replicates)
    ]
    fwer_count = sum(any(trial["holm_rejections"].values()) for trial in trials)
    marginal = {}
    for name in FAMILY:
        tested = [trial["pvalues"][name] for trial in trials if trial["pvalues"][name] is not None]
        raw_rejections = sum(value <= multiplicity.ALPHA for value in tested)
        holm_rejections = sum(trial["holm_rejections"][name] for trial in trials)
        untestable = replicates - len(tested)
        marginal[name] = {
            "raw_type1_count": raw_rejections,
            "raw_type1_fraction_of_all_trials": raw_rejections / replicates,
            "raw_type1_wilson_95_of_all_trials": calibration_v1.wilson(raw_rejections, replicates),
            "holm_rejection_count": holm_rejections,
            "holm_rejection_fraction": holm_rejections / replicates,
            "untestable_nonpositive_variance_count": untestable,
            "untestable_nonpositive_variance_fraction": untestable / replicates,
        }
    return {
        "scenario": asdict(scenario),
        "replicates": replicates,
        "global_null_holm_fwer_count": fwer_count,
        "global_null_holm_fwer_fraction": fwer_count / replicates,
        "global_null_holm_fwer_wilson_95": calibration_v1.wilson(fwer_count, replicates),
        "marginal": marginal,
    }


def calibration_decision(summaries: list[dict]) -> dict:
    fwer_upper = max(row["global_null_holm_fwer_wilson_95"][1] for row in summaries)
    marginal_upper = max(
        result["raw_type1_wilson_95_of_all_trials"][1]
        for row in summaries for result in row["marginal"].values()
    )
    untestable = max(
        result["untestable_nonpositive_variance_fraction"]
        for row in summaries for result in row["marginal"].values()
    )
    passed = (
        fwer_upper <= MAX_FWER_UPPER_95
        and marginal_upper <= MAX_MARGINAL_TYPE1_UPPER_95
        and untestable <= MAX_UNTESTABLE_FRACTION
    )
    return {
        "decision": (
            "MEETS_DECLARED_SYNTHETIC_GLOBAL_NULL_CALIBRATION_RULE"
            if passed else "DOES_NOT_MEET_DECLARED_SYNTHETIC_GLOBAL_NULL_CALIBRATION_RULE"
        ),
        "maximum_global_null_holm_fwer_wilson_upper_95": fwer_upper,
        "maximum_marginal_type1_wilson_upper_95": marginal_upper,
        "maximum_untestable_nonpositive_variance_fraction": untestable,
        "thresholds": {
            "maximum_global_null_holm_fwer_wilson_upper_95": MAX_FWER_UPPER_95,
            "maximum_marginal_type1_wilson_upper_95": MAX_MARGINAL_TYPE1_UPPER_95,
            "maximum_untestable_nonpositive_variance_fraction": MAX_UNTESTABLE_FRACTION,
        },
    }


def build_report(replicates: int = REPLICATES) -> dict:
    require(replicates >= 2, "At least two calibration replicates are required")
    failed = json.loads((ROOT / V1_ARTIFACT).read_text(encoding="utf-8"))
    require(failed["calibration_decision"]["decision"].startswith("DOES_NOT_MEET_"),
            "V1 failed-calibration premise changed")
    summaries = [
        summarize(scenario, index, replicates) for index, scenario in enumerate(SCENARIOS)
    ]
    decision = calibration_decision(summaries)
    passed = decision["decision"].startswith("MEETS_")
    return {
        "schema_version": "personaslm_p1_independent_validation_test_calibration_v2",
        "status": "SYNTHETIC_FINITE_TEMPLATE_TEST_CALIBRATION_COMPLETE_NO_INFERENCE",
        "predecessor_negative_result": {
            "path": V1_ARTIFACT.as_posix(),
            "sha256": sha256(V1_ARTIFACT),
            "decision": failed["calibration_decision"]["decision"],
            "preservation": "UNCHANGED",
        },
        "seed": SEED,
        "replicates_per_scenario": replicates,
        "target_boundary": {
            "primary_target": "Mean contrast over the finite, prospectively frozen eight template ancestors.",
            "sampling_clusters": "48 speakers; two cases stay together within speaker.",
            "template_generalization": "Not claimed by the primary test; template leave-one-out and two-way intervals are sensitivity analyses only.",
        },
        "design": {
            "speakers": precision.SPEAKERS,
            "cases_per_speaker": precision.CASES_PER_SPEAKER,
            "template_ancestors": precision.TEMPLATE_ANCESTORS,
            "degrees_of_freedom": DF,
            "family": list(FAMILY),
            "family_size": len(FAMILY),
            "marginal_test": "two-sided t(47) reference with speaker-cluster sandwich variance",
            "nonpositive_variance_rule": "UNTESTABLE_NONREJECTION; never truncate to zero standard error",
            "multiplicity": "Holm step-down at family alpha 0.05",
        },
        "prospective_calibration_rule": {
            "declared_before_full_v2_simulation": True,
            "maximum_global_null_holm_fwer_wilson_upper_95": MAX_FWER_UPPER_95,
            "maximum_marginal_type1_wilson_upper_95": MAX_MARGINAL_TYPE1_UPPER_95,
            "maximum_untestable_nonpositive_variance_fraction": MAX_UNTESTABLE_FRACTION,
        },
        "summaries": summaries,
        "calibration_decision": decision,
        "prospective_recommendation": (
            "CANDIDATE_PRIMARY_SPEAKER_CLUSTER_TEST_FOR_FINITE_TEMPLATE_TARGET"
            if passed else "NO_CALIBRATED_CONFIRMATORY_TEST_IDENTIFIED"
        ),
        "scientific_limits": [
            "This finite-template target cannot support claims about an unsampled template population.",
            "All outcomes are synthetic null draws from assumed distributions, not fitted PersonaSLM data.",
            "Global-null calibration does not prove strong family-wise control under every partial-null configuration.",
            "The condition-by-template scenario equalizes each condition's expected mean over the exact 96-case allocation; it does not exhaust heterogeneous effects.",
            "Passing cannot validate annotations, controls, missingness inference, power, or authorize the cohort.",
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
    parser.add_argument("--replicates", type=int, default=REPLICATES)
    arguments = parser.parse_args()
    report = build_report(arguments.replicates)
    write_new(arguments.output, report)
    print(json.dumps({
        "status": report["status"],
        "replicates_per_scenario": arguments.replicates,
        "decision": report["calibration_decision"]["decision"],
        "recommendation": report["prospective_recommendation"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
