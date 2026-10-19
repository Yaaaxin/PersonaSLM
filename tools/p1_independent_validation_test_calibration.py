"""Calibrate the proposed P1 two-way marginal tests under synthetic global nulls."""

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


TOOL = Path("tools/p1_independent_validation_test_calibration.py")
DESTINATION = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_test_calibration_v1.json"
)
MULTIPLICITY_ARTIFACT = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_multiplicity_candidate_v1.json"
)
REPLICATES = 3_000
SEED = 202610182
DF = precision.TEMPLATE_ANCESTORS - 1
MAX_FWER_UPPER_95 = 0.06
MAX_MARGINAL_TYPE1_UPPER_95 = 0.065
MAX_UNTESTABLE_FRACTION = 0.02
DEPENDENCIES = (
    Path("tools/p1_independent_validation_precision.py"),
    Path("tools/p1_independent_validation_multiplicity.py"),
    MULTIPLICITY_ARTIFACT,
)


@dataclass(frozen=True)
class NullScenario:
    name: str
    baseline_probability: float
    speaker_intercept_sd: float
    template_intercept_sd: float
    case_intercept_sd: float
    shared_uniform_probability: float


SCENARIOS = (
    NullScenario("central_null", 0.25, 0.60, 0.25, 0.35, 0.50),
    NullScenario("high_cluster_dependence_null", 0.25, 0.80, 0.50, 0.45, 0.50),
    NullScenario("rare_outcome_null", 0.05, 0.60, 0.25, 0.35, 0.50),
)
REGISTRY = multiplicity.contrast_registry()
FAMILY = multiplicity.CONFIRMATORY_FAMILY
ALLOCATION = precision.allocation()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def beta_continued_fraction(a: float, b: float, x: float) -> float:
    """Numerical Recipes continued fraction for the regularized incomplete beta."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    d = 1e-300 if abs(d) < 1e-300 else d
    d = 1.0 / d
    value = d
    for step in range(1, 201):
        doubled = 2 * step
        coefficient = step * (b - step) * x / ((qam + doubled) * (a + doubled))
        d = 1.0 + coefficient * d
        d = 1e-300 if abs(d) < 1e-300 else d
        c = 1.0 + coefficient / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        value *= d * c
        coefficient = -(a + step) * (qab + step) * x / (
            (a + doubled) * (qap + doubled)
        )
        d = 1.0 + coefficient * d
        d = 1e-300 if abs(d) < 1e-300 else d
        c = 1.0 + coefficient / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        delta = d * c
        value *= delta
        if abs(delta - 1.0) <= 3e-14:
            return value
    raise ArithmeticError("Incomplete-beta continued fraction did not converge")


def regularized_beta(x: float, a: float, b: float) -> float:
    require(0.0 <= x <= 1.0 and a > 0.0 and b > 0.0, "Invalid beta arguments")
    if x in (0.0, 1.0):
        return x
    factor = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return factor * beta_continued_fraction(a, b, x) / a
    return 1.0 - factor * beta_continued_fraction(b, a, 1.0 - x) / b


def student_t_two_sided_p(statistic: float, degrees_of_freedom: int = DF) -> float:
    require(degrees_of_freedom >= 1 and math.isfinite(statistic), "Invalid t statistic")
    x = degrees_of_freedom / (degrees_of_freedom + statistic * statistic)
    return regularized_beta(x, degrees_of_freedom / 2.0, 0.5)


def wilson(successes: int, total: int) -> list[float]:
    require(0 <= successes <= total and total > 0, "Invalid binomial count")
    z = precision.Z_975
    probability = successes / total
    denominator = 1.0 + z * z / total
    center = (probability + z * z / (2 * total)) / denominator
    halfwidth = z / denominator * math.sqrt(
        probability * (1.0 - probability) / total + z * z / (4 * total * total)
    )
    return [max(0.0, center - halfwidth), min(1.0, center + halfwidth)]


def simulate_trial(rng: random.Random, scenario: NullScenario) -> dict:
    template_effects = [
        rng.gauss(0.0, scenario.template_intercept_sd)
        for _ in range(precision.TEMPLATE_ANCESTORS)
    ]
    speaker_effects = [
        rng.gauss(0.0, scenario.speaker_intercept_sd)
        for _ in range(precision.SPEAKERS)
    ]
    contributions = {name: [] for name in FAMILY}
    speakers = []
    templates = []
    cases = []
    base = precision.logit(scenario.baseline_probability)
    for case_index, row in enumerate(ALLOCATION):
        probability = precision.logistic(
            base + speaker_effects[row["speaker"]]
            + template_effects[row["template_ancestor"]]
            + rng.gauss(0.0, scenario.case_intercept_sd)
        )
        common_uniform = rng.random()
        outcomes = {
            condition: float(
                (common_uniform if rng.random() < scenario.shared_uniform_probability else rng.random())
                < probability
            )
            for condition in next(iter(REGISTRY.values()))
        }
        for name, contrast_weights in REGISTRY.items():
            contributions[name].append(sum(
                contrast_weights[condition] * outcomes[condition]
                for condition in contrast_weights
            ))
        speakers.append(row["speaker"])
        templates.append(row["template_ancestor"])
        cases.append(case_index)

    pvalues = {}
    nonpositive = {}
    for name in FAMILY:
        values = contributions[name]
        estimate = statistics.fmean(values)
        variance = (
            precision.cluster_variance(values, speakers)
            + precision.cluster_variance(values, templates)
            - precision.cluster_variance(values, cases)
        )
        nonpositive[name] = variance <= 0.0
        pvalues[name] = (
            None if variance <= 0.0
            else student_t_two_sided_p(abs(estimate) / math.sqrt(variance))
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
            "raw_type1_wilson_95_of_all_trials": wilson(raw_rejections, replicates),
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
        "global_null_holm_fwer_wilson_95": wilson(fwer_count, replicates),
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
    candidate = json.loads((ROOT / MULTIPLICITY_ARTIFACT).read_text(encoding="utf-8"))
    require(candidate["candidate_endpoint_hierarchy"]["confirmatory_family"] == list(FAMILY),
            "Multiplicity candidate family changed")
    summaries = [
        summarize(scenario, index, replicates) for index, scenario in enumerate(SCENARIOS)
    ]
    return {
        "schema_version": "personaslm_p1_independent_validation_test_calibration_v1",
        "status": "SYNTHETIC_GLOBAL_NULL_CALIBRATION_COMPLETE_NO_INFERENCE",
        "seed": SEED,
        "replicates_per_scenario": replicates,
        "design": {
            "speakers": precision.SPEAKERS,
            "cases_per_speaker": precision.CASES_PER_SPEAKER,
            "template_ancestors": precision.TEMPLATE_ANCESTORS,
            "degrees_of_freedom": DF,
            "family": list(FAMILY),
            "family_size": len(FAMILY),
            "marginal_test": "two-sided t(7) reference with speaker + template - case sandwich variance",
            "nonpositive_variance_rule": "UNTESTABLE_NONREJECTION; never truncate to zero standard error",
            "multiplicity": "Holm step-down at family alpha 0.05",
        },
        "prospective_calibration_rule": {
            "declared_before_full_simulation": True,
            "maximum_global_null_holm_fwer_wilson_upper_95": MAX_FWER_UPPER_95,
            "maximum_marginal_type1_wilson_upper_95": MAX_MARGINAL_TYPE1_UPPER_95,
            "maximum_untestable_nonpositive_variance_fraction": MAX_UNTESTABLE_FRACTION,
            "interpretation": "Planning diagnostic only; passing cannot validate unsimulated outcome mechanisms or authorize the cohort.",
        },
        "summaries": summaries,
        "calibration_decision": calibration_decision(summaries),
        "scientific_limits": [
            "All outcomes are synthetic global-null Bernoulli draws from assumed random-effect distributions, not fitted PersonaSLM data.",
            "Global-null family-wise calibration does not prove strong control under every partial-null configuration.",
            "The simulation does not validate blinded annotation, neutral controls, missing-outcome inference, effect power, or population generalization.",
            "Only eight template ancestors determine the t(7) reference; small-cluster sensitivity remains mandatory.",
            "The declared tolerances are planning diagnostics rather than a theorem or confirmatory freeze.",
        ],
        "compatibility": {
            "multiplicity_artifact_sha256": sha256(MULTIPLICITY_ARTIFACT),
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
    }, sort_keys=True))


if __name__ == "__main__":
    main()
