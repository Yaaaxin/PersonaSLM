"""Build the prospective P1 independent-validation missing-outcome policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from personaslm.conditioning import FACTORIAL  # noqa: E402
from personaslm.human_factorial import CONTRASTS, weights  # noqa: E402
import p1c_paired_statistics as paired  # noqa: E402


DEPENDENCIES = (
    Path("src/personaslm/conditioning.py"),
    Path("src/personaslm/human_factorial.py"),
    Path("tools/p1c_paired_statistics.py"),
    Path("tools/p1_independent_validation_precision.py"),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registry() -> dict[str, dict[str, float]]:
    return {
        contrast: {condition: weights(contrast).get(condition, 0.0) for condition in FACTORIAL}
        for contrast in CONTRASTS
    }


def validate_registry(contrasts: dict[str, dict[str, float]]) -> None:
    if tuple(contrasts) != CONTRASTS:
        raise ValueError("Contrast registry order changed")
    for name, contrast_weights in contrasts.items():
        if set(contrast_weights) != set(FACTORIAL):
            raise ValueError(f"Factorial cells changed for {name}")
        if not math.isclose(sum(contrast_weights.values()), 0.0, abs_tol=1e-12):
            raise ValueError(f"Contrast does not annihilate constants: {name}")
        result = paired.case_contrast(
            {condition: 0.5 for condition in FACTORIAL}, contrast_weights
        )
        if not math.isclose(result["estimate"], 0.0, abs_tol=1e-12):
            raise ValueError(f"Constant contrast is nonzero: {name}")


def build_report() -> dict[str, object]:
    contrasts = registry()
    validate_registry(contrasts)
    examples = {
        "complete_pair": paired.case_contrast(
            {"C0": 0.0, "C3": 1.0}, weights("C3-C0")
        ),
        "unknown_c3": paired.case_contrast(
            {"C0": 0.0, "C3": None}, weights("C3-C0")
        ),
        "unknown_c0": paired.case_contrast(
            {"C0": None, "C3": 1.0}, weights("C3-C0")
        ),
        "both_unknown": paired.case_contrast(
            {"C0": None, "C3": None}, weights("C3-C0")
        ),
    }
    return {
        "schema_version": "personaslm_p1_independent_validation_missingness_policy_v1",
        "status": "PROSPECTIVE_POLICY_READY_FOR_RESEARCHER_ADOPTION_NOT_AUTHORIZED",
        "scope": {
            "design": "Proposed 48-speaker, 96-case, eight-factorial-cell plus two-control independent validation cohort.",
            "primary_planning_contrast": "C3-C0 outdated-value-adoption risk difference.",
            "historical_effect": "No historical output, label, gate, score, or estimand is changed.",
        },
        "frozen_eligibility": {
            "population": "Every prospectively frozen case-condition request, regardless of execution or review outcome.",
            "denominator_changes_after_outcomes": "PROHIBITED",
            "technical_retry_policy": "Must be frozen before execution; absent such a policy, a failed request remains missing and is not silently regenerated.",
        },
        "state_classification": {
            "completed_generation_with_empty_or_nonanswer_text": "Observed model outcome; semantically label NO_REQUESTED_VALUE when supported by genuine review, not administrative missingness.",
            "completed_generation_with_uncertain_semantic_interpretation": "Observed UNCERTAIN category; unknown for latent current/outdated binary indicators.",
            "infrastructure_or_resource_failure_without_a_completion": "Administrative missing outcome; never a model failure, success, or semantic nonanswer.",
            "lost_or_hash_invalid_raw_output": "Integrity missingness; retain the incident and do not score reconstructed text.",
            "unreviewed_or_unresolved_response": "Measurement missingness; retain model text but treat the semantic endpoint as unknown.",
            "not_applicable": "Allowed only when applicability was frozen before outcomes; report separately and never use it for an applicable failed assessment.",
        },
        "endpoint_rules": {
            "full_distribution": "Primary descriptive accounting reports every semantic category, including UNCERTAIN and NO_REQUESTED_VALUE, on the frozen eligible denominator.",
            "outdated_value_adoption": "OUTDATED_VALUE_ADOPTION=1; every determinate mutually exclusive non-outdated semantic state=0; UNCERTAIN or missing review=unknown.",
            "current_value_adoption": "CURRENT_VALUE_ADOPTION=1; every determinate mutually exclusive non-current semantic state=0; UNCERTAIN or missing review=unknown.",
            "semantic_completeness": "COMPLETE and INCOMPLETE remain observed categories; UNCERTAIN or unavailable review remains unknown for a binary completeness estimand.",
            "automatic_parser": "Automatic aliases and structural status remain separate diagnostics and cannot impute a missing human semantic endpoint.",
        },
        "analysis_rules": {
            "primary_missingness_analysis": "Apply original signed contrast weights over all eligible cases with endpoint range [0,1]; unknown cells contribute logical lower and upper limits according to weight sign.",
            "aggregation": "Average the two case contributions within each speaker, then weight the 48 speakers equally. Preserve template identifiers for crossed-cluster sensitivity.",
            "identified_point": "Report the all-eligible point estimate and its crossed speaker/template interval only when every required cell is known.",
            "identification_bounds": "Always report all-eligible logical bounds when required cells are unknown. Bounds are not confidence intervals.",
            "cluster_sensitivity": "If outcomes are incomplete, resample bound endpoints by whole speaker and template only as sensitivity; do not describe them as a confidence interval for an identified effect.",
            "complete_pair": "Report complete-pair estimates, their case/speaker/template coverage, and missingness by condition as secondary selected-subset sensitivity only.",
            "no_reweighting": "Never drop unknown cells and renormalize surviving factorial weights.",
            "no_single_imputation": "Do not replace unknowns with failure, success, parser output, reviewer consensus, or a model prediction.",
        },
        "reporting_requirements": [
            "Counts for execution failure, integrity failure, review missingness, semantic UNCERTAIN, and each observed semantic category by condition.",
            "Required-cell, complete-case, speaker, and template coverage for every contrast.",
            "All-eligible logical bounds beside any complete-pair sensitivity estimate.",
            "Reasons and hashes for any preregistered retry; original failed attempts remain preserved.",
            "Separate sampling uncertainty, identification uncertainty, annotation disagreement, and model stochasticity.",
        ],
        "contrast_registry": contrasts,
        "verified_binary_examples": examples,
        "compatibility": {
            "constant_contrasts_verified_zero": len(contrasts),
            "factorial_cells": list(FACTORIAL),
            "dependency_sha256": {path.as_posix(): sha256_file(ROOT / path) for path in DEPENDENCIES},
            "source_sha256": sha256_file(Path(__file__)),
        },
        "adoption_gate": {
            "status": "PENDING_RESEARCHER_ADOPTION",
            "reason": "This prospectively narrows analysis behavior and must not silently amend Protocol v1.1 or authorize the 960-request cohort.",
            "separate_unresolved_items": [
                "Endpoint hierarchy and confirmatory multiplicity family.",
                "Exact technical retry allowance before execution.",
                "Genuine blinded semantic review and independent agreement plan.",
                "Viable model, disjoint-C0 gate, and interpretable development factorial.",
            ],
        },
        "execution_impact": {
            "scientific_model_generations": 0,
            "inference_seconds": 0.0,
            "human_annotations": 0,
            "cohort_authorized": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Missingness policy evidence already exists; never overwrite it")
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "contrasts": len(report["contrast_registry"])}))


if __name__ == "__main__":
    main()
