"""Build the prospective P1 endpoint hierarchy and multiplicity candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from personaslm.conditioning import FACTORIAL  # noqa: E402
from personaslm.human_factorial import CONTRASTS, weights  # noqa: E402


PROTOCOL = Path("docs/research_protocol_v1.1.md")
PRECISION = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/independent_validation_precision_v1.json"
)
MISSINGNESS = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/independent_validation_missingness_policy_v1.json"
)
TOOL = Path("tools/p1_independent_validation_multiplicity.py")
DESTINATION = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_multiplicity_candidate_v1.json"
)
ALPHA = 0.05
CONTROLS = ("N_style", "N_history")
PROTOCOL_SIMPLE_CONTRASTS = ("C1-C0", "C3-C0", "C1-N_style", "C3-N_history")
CONFIRMATORY_FAMILY = PROTOCOL_SIMPLE_CONTRASTS + tuple(
    contrast for contrast in CONTRASTS if contrast not in PROTOCOL_SIMPLE_CONTRASTS
)
DEPENDENCIES = (
    PROTOCOL,
    Path("src/personaslm/conditioning.py"),
    Path("src/personaslm/human_factorial.py"),
    PRECISION,
    MISSINGNESS,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def contrast_registry() -> dict[str, dict[str, float]]:
    conditions = tuple(FACTORIAL) + CONTROLS
    registry = {}
    for name in CONFIRMATORY_FAMILY:
        row = {condition: 0.0 for condition in conditions}
        if name == "C1-N_style":
            row.update({"C1": 1.0, "N_style": -1.0})
        elif name == "C3-N_history":
            row.update({"C3": 1.0, "N_history": -1.0})
        else:
            row.update(weights(name))
        require(math.isclose(sum(row.values()), 0.0, abs_tol=1e-12),
                f"Contrast does not annihilate constants: {name}")
        registry[name] = row
    require(len(registry) == len(CONFIRMATORY_FAMILY) == 11, "Confirmatory family size changed")
    return registry


def holm_adjust(
    pvalues: dict[str, float | None], order: tuple[str, ...], alpha: float = ALPHA
) -> dict:
    """Holm step-down adjustment; unavailable tests remain in-family as non-rejections."""
    require(0.0 < alpha < 1.0, "Alpha must be strictly between zero and one")
    require(len(order) == len(set(order)) and set(pvalues) == set(order),
            "P-value keys must exactly match a unique declared family")
    effective = {}
    for name in order:
        value = pvalues[name]
        require(value is None or (type(value) in (int, float) and not isinstance(value, bool)
                                  and math.isfinite(value) and 0.0 <= value <= 1.0),
                f"Invalid p-value for {name}")
        effective[name] = 1.0 if value is None else float(value)

    declared_rank = {name: index for index, name in enumerate(order)}
    ranked = sorted(order, key=lambda name: (effective[name], declared_rank[name]))
    adjusted = {}
    running = 0.0
    rejection_open = True
    rejected = {}
    thresholds = {}
    count = len(order)
    for index, name in enumerate(ranked):
        remaining = count - index
        threshold = alpha / remaining
        thresholds[name] = threshold
        rejection_open = rejection_open and pvalues[name] is not None and effective[name] <= threshold
        rejected[name] = rejection_open
        running = max(running, min(1.0, remaining * effective[name]))
        adjusted[name] = running
    return {
        "method": "Holm step-down family-wise error control",
        "alpha": alpha,
        "family_size": count,
        "rows": [
            {
                "hypothesis": name,
                "raw_p_value": pvalues[name],
                "effective_p_value_for_ordering": effective[name],
                "rank": ranked.index(name) + 1,
                "step_threshold": thresholds[name],
                "adjusted_p_value": adjusted[name],
                "reject": rejected[name],
                "status": "UNTESTABLE_RETAINED_AS_NONREJECTION" if pvalues[name] is None else "TESTED",
            }
            for name in order
        ],
    }


def validate_inputs() -> tuple[dict, dict, tuple[str, ...]]:
    protocol = (ROOT / PROTOCOL).read_text(encoding="utf-8").replace("–", "-")
    require(all(name in protocol for name in PROTOCOL_SIMPLE_CONTRASTS),
            "Protocol preliminary simple-contrast inventory changed")
    precision = load(PRECISION)
    missingness = load(MISSINGNESS)
    require(precision["design"]["primary_contrast"]
            == "C3_minus_C0_outdated_value_adoption_risk_difference",
            "Precision-planning primary contrast changed")
    require(missingness["scope"]["primary_planning_contrast"]
            == "C3-C0 outdated-value-adoption risk difference.",
            "Missingness primary planning contrast changed")
    registered = tuple(missingness["contrast_registry"])
    require(len(registered) == len(CONTRASTS) and set(registered) == set(CONTRASTS),
            "Missingness contrast registry changed")
    missing_protocol = tuple(name for name in PROTOCOL_SIMPLE_CONTRASTS if name not in registered)
    require(missing_protocol == ("C1-N_style", "C3-N_history"),
            "Protocol/implementation contrast gap changed")
    return precision, missingness, missing_protocol


def build_report() -> dict:
    precision, missingness, missing_protocol = validate_inputs()
    registry = contrast_registry()
    synthetic_pvalues = {
        name: (None if name == "C3-N_history" else 0.004 if name == "C3-C0"
               else 0.011 if name == "H" else 0.5)
        for name in CONFIRMATORY_FAMILY
    }
    return {
        "schema_version": "personaslm_p1_independent_validation_multiplicity_candidate_v1",
        "status": "PROSPECTIVE_CANDIDATE_PENDING_RESEARCHER_ADOPTION_CONTROL_VALIDITY_AND_TEST_CALIBRATION",
        "historical_effect": "No historical output, annotation, score, gate, or estimand is changed.",
        "audit_finding": {
            "protocol_preliminary_simple_contrasts": list(PROTOCOL_SIMPLE_CONTRASTS),
            "existing_registered_contrasts": list(CONTRASTS),
            "protocol_simple_contrasts_absent_from_existing_registry": list(missing_protocol),
            "interpretation": (
                "The two neutral-control contrasts must not be silently dropped or described as "
                "registered confirmatory analyses."
            ),
        },
        "candidate_endpoint_hierarchy": {
            "primary_endpoint": "Binary outdated-value adoption from genuine blinded semantic review.",
            "lead_planning_contrast": "C3-C0",
            "lead_status": "Planning and reporting order only; no privileged unadjusted alpha within the family.",
            "confirmatory_family": list(CONFIRMATORY_FAMILY),
            "family_size": len(CONFIRMATORY_FAMILY),
            "test_sidedness": "Two-sided; effect direction and magnitude are reported regardless of sign.",
            "multiplicity": "Holm step-down family-wise error control at alpha 0.05 across all 11 hypotheses.",
            "neutral_control_condition": (
                "C1-N_style and C3-N_history enter the family only if their exact controls receive "
                "prospective semantic adoption before cohort freeze."
            ),
            "secondary_estimation": [
                "Current-value adoption and the full mutually exclusive semantic-category distribution.",
                "Response Relevance, Factual Consistency, Temporal Consistency, and Conversational Coherence.",
                "Semantic completeness, structural status, Linguistic Fidelity, Behavioral Fidelity, latency, and memory.",
            ],
            "secondary_claim_rule": (
                "Report estimates, denominators, coverage, uncertainty, and missingness; do not convert "
                "unadjusted secondary intervals into confirmatory significance claims."
            ),
        },
        "candidate_contrast_registry": registry,
        "missing_outcome_multiplicity_rule": {
            "rule": (
                "A contrast without its prospectively valid primary-endpoint test remains in the 11-member "
                "family as an untestable non-rejection; it is never removed to reduce the Holm denominator."
            ),
            "compatibility": missingness["analysis_rules"]["no_reweighting"],
        },
        "verified_synthetic_holm_example_not_data": holm_adjust(
            synthetic_pvalues, CONFIRMATORY_FAMILY
        ),
        "adoption_gate": {
            "status": "PENDING_RESEARCHER_ADOPTION",
            "required_before_confirmatory_freeze": [
                "Genuine semantic adoption of the exact N_style and N_history controls.",
                "A versioned missingness-policy extension covering both neutral-control contrasts.",
                "Prospective simulation or validation of the marginal two-way speaker/template test for all family members.",
                "A viable selected model, passed disjoint C0 gate, and interpretable development factorial.",
                "A frozen cohort, applicability matrix, blinded annotation and inter-rater agreement plan.",
            ],
            "cohort_authorized": False,
        },
        "scientific_limits": [
            "Holm controls multiplicity only when the constituent marginal p-values are valid; this artifact does not validate them.",
            "Eight planned template ancestors make template-cluster inference fragile and require the registered sensitivity analyses.",
            "The primary endpoint and family are a proposal, not a Protocol v1.1 amendment or confirmatory freeze.",
            "No neutral-control contrast is estimable unless its exact control is prospectively accepted and executed.",
            "The synthetic Holm values are software examples and contain no observed or simulated PersonaSLM outcome.",
        ],
        "compatibility": {
            "precision_status": precision["status"],
            "missingness_status": missingness["status"],
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
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DESTINATION)
    arguments = parser.parse_args()
    report = build_report()
    write_new(arguments.output, report)
    print(json.dumps({
        "status": report["status"],
        "family_size": len(report["candidate_endpoint_hierarchy"]["confirmatory_family"]),
        "missing_protocol_contrasts": report["audit_finding"]["protocol_simple_contrasts_absent_from_existing_registry"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
