"""Post-hoc six-coordinate decomposition; never replaces frozen pilot scores."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import statistics

from personaslm.journal import atomic_json
from real_persona_chat_sfh_independent_reproduction_v1 import (
    ANALYSIS, FROZEN, PRIVATE, PUBLIC, check, close, effect, load, sha, summarize)

OUTPUT = PUBLIC / "posthoc_style_coordinate_decomposition_v1.json"
COORDINATES = ("length", "question", "exclamation", "ellipsis", "laughter", "polite_ending")


def distances(text, source):
    text = re.sub(r"<[^>]+>", "", text).replace("＊＊", "")
    observed = [len(text) / 50, int("?" in text or "？" in text),
                int("!" in text or "！" in text), int("…" in text or "..." in text),
                int("笑" in text or bool(re.search(r"(?i)(^|\W)w+(\W|$)", text))),
                int(bool(re.search(r"(です|ます|でした|ません)[。！？!?]*$", text)))]
    expected = [source["mean_turn_length_characters"] / 50,
                *[source[key] for key in ("question_turn_rate", "exclamation_turn_rate",
                  "ellipsis_turn_rate", "laughter_turn_rate", "polite_ending_rate")]]
    return [abs(left - right) for left, right in zip(observed, expected)]


def contrast_summary(values):
    result = summarize(values)
    loo = [statistics.fmean(values[:i] + values[i + 1:]) for i in range(len(values))]
    result.update(leave_one_speaker_out_mean_minimum=min(loo),
                  leave_one_speaker_out_mean_maximum=max(loo))
    return result


def calculate():
    public = load(ANALYSIS)
    private_path = PRIVATE / "analysis_private_v1_1.json"
    check(sha(private_path) == public["privacy"]["private_analysis_sha256"], "Private analysis binding")
    plan, data = load(FROZEN), load(private_path)
    requests = {row["request_id"]: row for row in plan["requests"]}
    groups, censor_conditions, affected = defaultdict(dict), Counter(), set()
    for row in data["rows"]:
        boundary = row["response_status"]
        if boundary["status"] == "TRUNCATED":
            censor_conditions[row["condition"]] += 1
            affected.add(row["case_id"])
        if row["automatic_score"]["source_style_distance"] is None:
            continue
        case = requests[row["request_id"]]["latent_case"]
        components = distances(boundary["first_span"]["text"], case["style_features"])
        check(close(statistics.fmean(components), row["automatic_score"]["source_style_distance"]),
              "Exact frozen distance decomposition")
        groups[row["case_id"]][row["condition"]] = components
    complete = [value for value in groups.values() if len(value) == 8]
    check(len(complete) == public["speaker_paired_factorial_effects"]["source_style_distance"]["S"]["complete_speakers"],
          "Identical complete-speaker subset")
    contributions = {}
    for coordinate, name in enumerate(COORDINATES):
        values = [effect({condition: distances[coordinate] / 6
                          for condition, distances in case.items()}, 1) for case in complete]
        contributions[name] = contrast_summary(values)
    total = sum(value["mean"] for value in contributions.values())
    check(close(total, public["speaker_paired_factorial_effects"]["source_style_distance"]["S"]["mean"]),
          "Coordinate effects sum to frozen S effect")
    markers = [effect({condition: statistics.fmean(distances[1:])
                       for condition, distances in case.items()}, 1) for case in complete]
    return {
        "schema_version": "personaslm_rpc_sfh_posthoc_style_coordinate_decomposition_v1",
        "status": "COMPLETE_POST_HOC_DIAGNOSTIC_NOT_A_NEW_PRIMARY_ENDPOINT",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_level": "DEVELOPMENT_EXPLORATORY",
        "question": "How much of the frozen S effect on six-coordinate surface distance is arithmetic length compliance?",
        "selection": "Same five complete speaker-contexts as the frozen style-distance factorial analysis; no new inclusion/exclusion",
        "bindings": {"analysis_sha256": sha(ANALYSIS), "private_analysis_sha256": sha(private_path),
                     "frozen_manifest_sha256": sha(FROZEN), "script_sha256": sha(__file__),
                     "independent_reproduction_script_sha256": sha("tools/real_persona_chat_sfh_independent_reproduction_v1.py")},
        "formula": "Each coordinate contributes abs(observed - source)/6 to the frozen distance; S effect is its paired S=1 minus S=0 mean. Marker-only diagnostic averages the remaining five absolute differences with weight1/5.",
        "coordinate_contributions_to_S_effect": contributions,
        "frozen_S_effect_sum": total,
        "length_contribution_divided_by_total_effect": contributions["length"]["mean"] / total,
        "marker_only_S_effect_posthoc": contrast_summary(markers),
        "censoring": {"native_limit_responses": sum(censor_conditions.values()),
                      "by_condition": {f"C{i}": censor_conditions[f"C{i}"] for i in range(8)},
                      "affected_speakers": len(affected), "complete_speakers": len(complete)},
        "interpretation_limits": [
            "S explicitly supplies length and marker rates, so compliance with these descriptors is expected and does not establish distinctive speaker identity",
            "The length/total ratio is an arithmetic decomposition, not causal mediation or variance explained",
            "Marker-only diagnostic was not prospectively primary and is not validated Persona Fidelity",
            "Complete-case estimates exclude three speakers affected by four truncations; selection may distort conditioning effects",
            "No human semantic judgments or independent validation speakers were used"],
        "privacy": {"participant_text_public": False, "row_identifiers_public": False},
    }


if __name__ == "__main__":
    value = calculate()
    atomic_json(OUTPUT, value)
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
