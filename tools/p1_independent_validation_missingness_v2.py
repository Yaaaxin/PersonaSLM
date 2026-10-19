"""Extend prospective missing-outcome bounds to the 11-contrast candidate family."""

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

import p1_independent_validation_missingness as missingness_v1  # noqa: E402
import p1_independent_validation_multiplicity as multiplicity  # noqa: E402
import p1c_paired_statistics as paired  # noqa: E402


TOOL = Path("tools/p1_independent_validation_missingness_v2.py")
DESTINATION = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_missingness_policy_v2.json"
)
V1_ARTIFACT = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_missingness_policy_v1.json"
)
CALIBRATION_V1 = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_test_calibration_v1.json"
)
CALIBRATION_V2 = Path(
    "docs/validation/p1/model_feasibility_recovery_v1/"
    "independent_validation_test_calibration_v2.json"
)
DEPENDENCIES = (
    Path("tools/p1c_paired_statistics.py"),
    Path("tools/p1_independent_validation_missingness.py"),
    Path("tools/p1_independent_validation_multiplicity.py"),
    V1_ARTIFACT,
    CALIBRATION_V1,
    CALIBRATION_V2,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def registry() -> dict[str, dict[str, float]]:
    value = multiplicity.contrast_registry()
    require(tuple(value) == multiplicity.CONFIRMATORY_FAMILY, "Candidate contrast order changed")
    for name, contrast_weights in value.items():
        require(math.isclose(sum(contrast_weights.values()), 0.0, abs_tol=1e-12),
                f"Contrast does not annihilate constants: {name}")
    return value


def build_report() -> dict:
    predecessor = load(V1_ARTIFACT)
    require(predecessor == missingness_v1.build_report(), "V1 missingness policy no longer reproduces")
    failed_calibrations = [load(CALIBRATION_V1), load(CALIBRATION_V2)]
    require(all(
        row["calibration_decision"]["decision"].startswith("DOES_NOT_MEET_")
        for row in failed_calibrations
    ), "Failed-calibration boundary changed")
    contrasts = registry()
    neutral_example = {
        "complete_pair": paired.case_contrast(
            {"C1": 1.0, "N_style": 0.0}, contrasts["C1-N_style"]
        ),
        "unknown_neutral_control": paired.case_contrast(
            {"C1": 1.0, "N_style": None}, contrasts["C1-N_style"]
        ),
        "unknown_active_history": paired.case_contrast(
            {"C3": None, "N_history": 0.0}, contrasts["C3-N_history"]
        ),
    }
    return {
        "schema_version": "personaslm_p1_independent_validation_missingness_policy_v2",
        "status": "PROSPECTIVE_11_CONTRAST_EXTENSION_PENDING_RESEARCHER_AND_CONTROL_ADOPTION",
        "predecessor": {
            "path": V1_ARTIFACT.as_posix(),
            "sha256": sha256(V1_ARTIFACT),
            "status": predecessor["status"],
            "preservation": "UNCHANGED",
        },
        "scope": {
            "extension": "Adds C1-N_style and C3-N_history to the nine V1 signed-bound contrasts.",
            "condition": "The two contrasts activate only if their exact neutral controls receive prospective semantic adoption.",
            "historical_effect": "No historical output, label, gate, score, eligibility decision, or estimand is changed.",
        },
        "state_classification": predecessor["state_classification"],
        "endpoint_rules": predecessor["endpoint_rules"],
        "analysis_rules": {
            **predecessor["analysis_rules"],
            "identified_point": (
                "Report the all-eligible point only when every active cell is known. No confirmatory "
                "p-value is authorized because both prospective marginal-test calibrations failed."
            ),
            "cluster_sensitivity": (
                "Speaker-cluster and two-way speaker/template intervals remain labeled sensitivity "
                "analyses; neither is a calibrated confirmatory test at this checkpoint."
            ),
        },
        "reporting_requirements": predecessor["reporting_requirements"] + [
            "Report N_style and N_history execution/review missingness separately from factorial cells.",
            "Do not activate a neutral-control contrast merely because its mathematical weights are available.",
        ],
        "contrast_registry": contrasts,
        "verified_neutral_contrast_examples": neutral_example,
        "inferential_boundary": {
            "status": "NO_CALIBRATED_CONFIRMATORY_TEST_IDENTIFIED",
            "failed_artifacts": [
                {"path": path.as_posix(), "sha256": sha256(path)}
                for path in (CALIBRATION_V1, CALIBRATION_V2)
            ],
            "effect": "Signed identification bounds remain valid; hypothesis-test adoption remains blocked.",
        },
        "adoption_gate": {
            "status": "PENDING_RESEARCHER_ADOPTION",
            "required": [
                "Genuine semantic adoption of the exact N_style and N_history controls.",
                "A separately justified and prospectively calibrated inferential procedure, or an explicitly estimation-only confirmatory freeze.",
                "A viable selected model, passed disjoint C0 gate, interpretable development factorial, and frozen independent cohort.",
            ],
            "cohort_authorized": False,
        },
        "compatibility": {
            "constant_contrasts_verified_zero": len(contrasts),
            "conditions": list(next(iter(contrasts.values()))),
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
        "contrasts": len(report["contrast_registry"]),
        "inferential_boundary": report["inferential_boundary"]["status"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
