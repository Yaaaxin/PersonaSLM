"""Independently reproduce the frozen RealPersonaChat style-signal result.

This zero-inference implementation reads the pinned raw JSON directly.  It
does not import the original intake or style-signal controller and emits only
aggregate values and hashes.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import statistics
import subprocess
import unicodedata


REPO = Path(__file__).resolve().parents[1]
VALIDATION = REPO / "docs/validation/p1/real_persona_chat_style_signal_v1"
REGISTRATION = VALIDATION / "registration_v1.json"
ARCHIVED_ANALYSIS = VALIDATION / "analysis_v1.json"
ORIGINAL_CONTROLLER = REPO / "tools/real_persona_chat_style_signal_v1.py"
INTAKE_CONTROLLER = REPO / "tools/real_persona_chat_intake.py"
REPRODUCTION_TEST = REPO / "tests/test_real_persona_chat_style_signal_v1_reproduce.py"
INTAKE_RECEIPT = (
    REPO / "docs/validation/p1/real_persona_chat_intake_v1/intake_receipt_v1.json"
)
DEFAULT_DATASET = REPO / ".local/datasets/real-persona-chat"
DEFAULT_OUTPUT = VALIDATION / "analysis_reproduction_v1.json"
SPLIT_SEED = "PersonaSLM-RPC-speaker-split-v1"
SPLIT_COUNTS = (117, 58, 58)
MIN_CONTROLS = 10
FEATURES = (
    "mean_turn_length",
    "sd_turn_length",
    "question_turn_rate",
    "exclamation_turn_rate",
    "full_stop_turn_rate",
    "ellipsis_turn_rate",
    "laughter_turn_rate",
    "polite_ending_rate",
    "hiragana_rate",
    "katakana_rate",
    "han_rate",
    "latin_rate",
    "digit_rate",
    "punctuation_rate",
    "symbol_rate",
)


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _split_assignments(speaker_keys: list[str]) -> tuple[dict[str, str], str]:
    _require(len(speaker_keys) == sum(SPLIT_COUNTS), "Unexpected speaker count")
    ranked = sorted(
        speaker_keys,
        key=lambda value: hashlib.sha256(
            f"{SPLIT_SEED}\0{value}".encode("utf-8")
        ).hexdigest(),
    )
    first, second = SPLIT_COUNTS[0], SPLIT_COUNTS[0] + SPLIT_COUNTS[1]
    assigned = {
        speaker: (
            "DEVELOPMENT"
            if index < first
            else "EXPLORATORY_TEST"
            if index < second
            else "INDEPENDENT_VALIDATION_RESERVED"
        )
        for index, speaker in enumerate(ranked)
    }
    binding = "\n".join(f"{speaker}|{assigned[speaker]}" for speaker in ranked)
    return assigned, hashlib.sha256(binding.encode("utf-8")).hexdigest()


def _raw_development_records(
    dataset_root: Path,
) -> tuple[dict[str, list[dict]], dict[str, object]]:
    data = dataset_root / "real_persona_chat"
    interlocutors_path = data / "interlocutors.json"
    interlocutors = json.loads(interlocutors_path.read_text(encoding="utf-8"))
    assignments, assignment_hash = _split_assignments(list(interlocutors))
    records: dict[str, list[dict]] = defaultdict(list)
    manifest = hashlib.sha256()
    dialogue_count = 0

    for path in sorted((data / "dialogues").glob("*.json")):
        raw = path.read_bytes()
        manifest.update(
            path.name.encode("utf-8")
            + b"\0"
            + hashlib.sha256(raw).hexdigest().encode("ascii")
            + b"\n"
        )
        dialogue_count += 1
        dialogue = json.loads(raw)
        left, right = dialogue["interlocutors"]
        if not (
            assignments[left] == "DEVELOPMENT"
            and assignments[right] == "DEVELOPMENT"
        ):
            continue
        timestamps = [
            turn.get("timestamp")
            for turn in dialogue["utterances"]
            if turn.get("timestamp") not in (None, "", "NaT")
        ]
        chronological_key = (
            min(timestamps) if timestamps else "9999",
            dialogue["dialogue_id"],
        )
        for speaker, partner in ((left, right), (right, left)):
            records[speaker].append(
                {
                    "dialogue_id": dialogue["dialogue_id"],
                    "partner": partner,
                    "key": chronological_key,
                    "turns": [
                        turn["text"]
                        for turn in dialogue["utterances"]
                        if turn["interlocutor_id"] == speaker
                    ],
                }
            )
    return records, {
        "split_assignment_sha256": assignment_hash,
        "interlocutors_sha256": _sha256(interlocutors_path),
        "dialogue_manifest_sha256": manifest.hexdigest(),
        "dialogue_file_count": dialogue_count,
    }


def _profiles(records: dict[str, list[dict]]) -> dict[str, dict]:
    candidates = {}
    for speaker, rows in records.items():
        ordered = sorted(rows, key=lambda row: row["key"])
        early, early_partners = [], set()
        for row in ordered:
            if row["partner"] not in early_partners:
                early.append(row)
                early_partners.add(row["partner"])
            if len(early) == 2:
                break
        late, late_partners = [], set()
        for row in reversed(ordered):
            if row["partner"] not in early_partners | late_partners:
                late.append(row)
                late_partners.add(row["partner"])
            if len(late) == 2:
                break
        if (
            len(early) == len(late) == 2
            and max(row["key"] for row in early) < min(row["key"] for row in late)
        ):
            candidates[speaker] = {
                "source": early,
                "target": list(reversed(late)),
                "partners": early_partners | late_partners,
            }

    while True:
        retained = {
            speaker: profile
            for speaker, profile in candidates.items()
            if sum(
                other != speaker
                and profile["partners"].isdisjoint(other_profile["partners"])
                for other, other_profile in candidates.items()
            )
            >= MIN_CONTROLS
        }
        if retained.keys() == candidates.keys():
            return retained
        candidates = retained


def _surface_features(rows: list[dict]) -> dict[str, float]:
    turns = [
        re.sub(r"<[^>]+>", "", text).replace("＊＊", "")
        for row in rows
        for text in row["turns"]
    ]
    lengths = [len(text) for text in turns]
    joined = "".join(turns)
    denominator = max(1, len(joined))
    turn_count = max(1, len(turns))
    unicode_classes = Counter(unicodedata.category(char)[0] for char in joined)
    character_classes = Counter()
    for char in joined:
        code = ord(char)
        character_classes["hiragana"] += 0x3040 <= code <= 0x309F
        character_classes["katakana"] += 0x30A0 <= code <= 0x30FF
        character_classes["han"] += 0x3400 <= code <= 0x4DBF or 0x4E00 <= code <= 0x9FFF
        character_classes["latin"] += "A" <= char <= "Z" or "a" <= char <= "z"
        character_classes["digit"] += char.isdigit()
    return {
        "mean_turn_length": statistics.fmean(lengths) / 50 if lengths else 0.0,
        "sd_turn_length": (
            statistics.pstdev(lengths) / 50 if len(lengths) > 1 else 0.0
        ),
        "question_turn_rate": sum("?" in text or "？" in text for text in turns)
        / turn_count,
        "exclamation_turn_rate": sum("!" in text or "！" in text for text in turns)
        / turn_count,
        "full_stop_turn_rate": sum("。" in text for text in turns) / turn_count,
        "ellipsis_turn_rate": sum("…" in text or "..." in text for text in turns)
        / turn_count,
        "laughter_turn_rate": sum(
            "笑" in text or re.search(r"(?i)(^|\W)w+(\W|$)", text) is not None
            for text in turns
        )
        / turn_count,
        "polite_ending_rate": sum(
            re.search(r"(です|ます|でした|ません)[。！？!?]*$", text) is not None
            for text in turns
        )
        / turn_count,
        "hiragana_rate": character_classes["hiragana"] / denominator,
        "katakana_rate": character_classes["katakana"] / denominator,
        "han_rate": character_classes["han"] / denominator,
        "latin_rate": character_classes["latin"] / denominator,
        "digit_rate": character_classes["digit"] / denominator,
        "punctuation_rate": unicode_classes["P"] / denominator,
        "symbol_rate": unicode_classes["S"] / denominator,
    }


def _measure(profiles: dict[str, dict], active: set[str] | None = None) -> dict:
    active = set(profiles) if active is None else active
    subset = {speaker: profiles[speaker] for speaker in active}
    raw = {
        speaker: {
            side: _surface_features(profile[side]) for side in ("source", "target")
        }
        for speaker, profile in subset.items()
    }
    scales = {}
    for feature in FEATURES:
        values = [
            raw[speaker][side][feature]
            for speaker in raw
            for side in ("source", "target")
        ]
        scales[feature] = (statistics.fmean(values), statistics.pstdev(values) or 1.0)
    vectors = {
        speaker: {
            side: tuple(
                (raw[speaker][side][feature] - scales[feature][0])
                / scales[feature][1]
                for feature in FEATURES
            )
            for side in ("source", "target")
        }
        for speaker in raw
    }

    def distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
        return statistics.fmean(abs(a - b) for a, b in zip(left, right))

    margins, percentiles, own_distances, other_medians = [], [], [], []
    for speaker, profile in subset.items():
        source = vectors[speaker]["source"]
        own = distance(source, vectors[speaker]["target"])
        controls = [
            distance(source, vectors[other]["target"])
            for other, other_profile in subset.items()
            if other != speaker
            and profile["partners"].isdisjoint(other_profile["partners"])
        ]
        if len(controls) < MIN_CONTROLS:
            continue
        other = statistics.median(controls)
        own_distances.append(own)
        other_medians.append(other)
        margins.append(other - own)
        percentiles.append(sum(value > own for value in controls) / len(controls))
    return {
        "margins": margins,
        "percentiles": percentiles,
        "own_distances": own_distances,
        "other_medians": other_medians,
    }


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def _computed_analysis(profiles: dict[str, dict], registration_hash: str) -> dict:
    result = _measure(profiles)
    margins = result["margins"]
    _require(bool(margins), "No evaluable development speakers")
    leave_one_out = []
    for omitted in sorted(profiles):
        reduced = _measure(profiles, set(profiles) - {omitted})["margins"]
        if reduced:
            leave_one_out.append(statistics.fmean(reduced))
    private_case_binding = _canonical(
        {
            "margins": sorted(round(value, 12) for value in margins),
            "percentiles": sorted(round(value, 12) for value in result["percentiles"]),
        }
    )
    return {
        "registration_sha256": registration_hash,
        "speaker_units_resolved": len(margins),
        "primary": {
            "mean_margin": statistics.fmean(margins),
            "median_margin": statistics.median(margins),
            "q25_margin": _quantile(margins, 0.25),
            "q75_margin": _quantile(margins, 0.75),
            "own_closer_than_other_median_proportion": sum(
                value > 0 for value in margins
            )
            / len(margins),
            "mean_control_percentile_rank": statistics.fmean(result["percentiles"]),
            "mean_own_distance": statistics.fmean(result["own_distances"]),
            "mean_other_median_distance": statistics.fmean(result["other_medians"]),
        },
        "influence": {
            "leave_one_speaker_out_mean_margin_min": min(leave_one_out),
            "leave_one_speaker_out_mean_margin_max": max(leave_one_out),
        },
        "case_level_values_sha256": hashlib.sha256(private_case_binding).hexdigest(),
    }


def _profile_time_audit(profiles: dict[str, dict]) -> dict[str, object]:
    records = parseable = nat_only = unparseable = strict_profiles = 0
    nat_only_by_side = Counter()
    affected_profiles = 0
    for profile in profiles.values():
        parsed = {"source": [], "target": []}
        profile_has_nat_only = False
        for side in ("source", "target"):
            for row in profile[side]:
                records += 1
                value = row["key"][0]
                if value == "9999":
                    nat_only += 1
                    nat_only_by_side[side] += 1
                    profile_has_nat_only = True
                    continue
                try:
                    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except (TypeError, ValueError):
                    unparseable += 1
                    continue
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                else:
                    timestamp = timestamp.astimezone(timezone.utc)
                parsed[side].append(timestamp)
                parseable += 1
        affected_profiles += profile_has_nat_only
        if (
            len(parsed["source"]) == len(parsed["target"]) == 2
            and max(parsed["source"]) < min(parsed["target"])
        ):
            strict_profiles += 1
    return {
        "selected_speaker_profiles": len(profiles),
        "selected_speaker_dialogue_records": records,
        "records_with_parseable_iso_chronology_key": parseable,
        "records_with_nat_only_timestamps": nat_only,
        "records_with_nat_only_timestamps_by_profile_side": {
            "source": nat_only_by_side["source"],
            "target": nat_only_by_side["target"],
        },
        "profiles_with_at_least_one_nat_only_record": affected_profiles,
        "records_with_unparseable_chronology_key": unparseable,
        "profiles_with_all_four_parseable_chronology_keys": len(profiles)
        - affected_profiles,
        "profiles_with_strict_source_max_before_target_min": strict_profiles,
    }


def _differences(expected: object, observed: object, path: str = "") -> list[str]:
    if isinstance(expected, dict) and isinstance(observed, dict):
        differences = []
        for key in sorted(set(expected) | set(observed)):
            child = f"{path}.{key}" if path else key
            if key not in expected or key not in observed:
                differences.append(child)
            else:
                differences.extend(_differences(expected[key], observed[key], child))
        return differences
    return [] if expected == observed else [path]


def build_receipt(dataset_root: Path = DEFAULT_DATASET) -> dict:
    dataset_root = dataset_root.resolve()
    registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    archived = json.loads(ARCHIVED_ANALYSIS.read_text(encoding="utf-8"))
    intake = json.loads(INTAKE_RECEIPT.read_text(encoding="utf-8"))
    records, raw_bindings = _raw_development_records(dataset_root)
    profiles = _profiles(records)

    version_path = dataset_root / "VERSION"
    license_path = dataset_root / "LICENSE"
    readme_path = dataset_root / "README.md"
    revision = subprocess.run(
        ["git", "-C", str(dataset_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    observed_source = {
        "version": version_path.read_text(encoding="utf-8").strip(),
        "revision": revision,
        "license_sha256": _sha256(license_path),
        "readme_sha256": _sha256(readme_path),
        "version_sha256": _sha256(version_path),
        "interlocutors_sha256": raw_bindings["interlocutors_sha256"],
        "dialogue_manifest_sha256": raw_bindings["dialogue_manifest_sha256"],
        "dialogues": raw_bindings["dialogue_file_count"],
    }
    expected_source = {
        key: intake["source"][key]
        for key in observed_source
    }
    source_differences = _differences(expected_source, observed_source)

    cohort_binding = _canonical(
        sorted(
            (
                speaker,
                [row["dialogue_id"] for row in profile["source"]],
                [row["dialogue_id"] for row in profile["target"]],
            )
            for speaker, profile in profiles.items()
        )
    )
    registration_checks = {
        "registration_sha256": _sha256(REGISTRATION),
        "intake_receipt_sha256": _sha256(INTAKE_RECEIPT),
        "split_assignment_sha256": raw_bindings["split_assignment_sha256"],
        "cohort_and_dialogue_assignment_sha256": hashlib.sha256(
            cohort_binding
        ).hexdigest(),
        "eligible_speaker_count": len(profiles),
        "frozen_features": list(FEATURES),
        "original_controller_sha256": _sha256(ORIGINAL_CONTROLLER),
    }
    expected_registration_checks = {
        "registration_sha256": archived["registration_sha256"],
        "intake_receipt_sha256": registration["source_bindings"][
            "intake_receipt_sha256"
        ],
        "split_assignment_sha256": registration["split_assignment_sha256"],
        "cohort_and_dialogue_assignment_sha256": registration[
            "cohort_and_dialogue_assignment_sha256"
        ],
        "eligible_speaker_count": registration["eligible_speaker_count"],
        "frozen_features": registration["frozen_features"],
        "original_controller_sha256": registration["source_bindings"][
            "controller_sha256"
        ],
    }
    registration_differences = _differences(
        expected_registration_checks, registration_checks
    )

    recomputed = _computed_analysis(profiles, registration_checks["registration_sha256"])
    expected = {
        "registration_sha256": archived["registration_sha256"],
        "speaker_units_resolved": archived["speaker_units_resolved"],
        "primary": archived["primary"],
        "influence": {
            key: value
            for key, value in archived["influence"].items()
            if key != "interpretation"
        },
        "case_level_values_sha256": archived["case_level_values_sha256"],
    }
    analysis_differences = _differences(expected, recomputed)
    profile_time_audit = _profile_time_audit(profiles)
    all_differences = {
        "source": source_differences,
        "registration": registration_differences,
        "analysis": analysis_differences,
    }
    passed = not any(all_differences.values())
    chronology_fully_verified = (
        profile_time_audit["records_with_parseable_iso_chronology_key"]
        == profile_time_audit["selected_speaker_dialogue_records"]
        and profile_time_audit["profiles_with_strict_source_max_before_target_min"]
        == profile_time_audit["selected_speaker_profiles"]
    )
    return {
        "schema_version": "personaslm_rpc_style_signal_v1_analysis_reproduction",
        "status": (
            "PASS_EXACT_REPRODUCTION"
            if passed and chronology_fully_verified
            else "PASS_EXACT_REPRODUCTION_WITH_CHRONOLOGY_LIMITATION"
            if passed
            else "FAIL_DIVERGENCE"
        ),
        "reproduction_type": "CONTROLLER_INDEPENDENT_RAW_JSON_RECOMPUTATION",
        "scientific_level": "DEVELOPMENT_MEASUREMENT_DIAGNOSTIC",
        "inputs": {
            "registration_sha256": _sha256(REGISTRATION),
            "intake_receipt_sha256": _sha256(INTAKE_RECEIPT),
            "archived_analysis_sha256": _sha256(ARCHIVED_ANALYSIS),
            "dataset_revision": revision,
            "dialogue_manifest_sha256": raw_bindings["dialogue_manifest_sha256"],
            "interlocutors_sha256": raw_bindings["interlocutors_sha256"],
            "registered_source_head": registration["source_bindings"]["source_head"],
            "original_controller_sha256": _sha256(ORIGINAL_CONTROLLER),
            "intake_controller_sha256": _sha256(INTAKE_CONTROLLER),
            "reproduction_script_sha256": _sha256(Path(__file__).resolve()),
            "reproduction_test_sha256": _sha256(REPRODUCTION_TEST),
        },
        "runtime": {
            "python_version": platform.python_version(),
            "unicodedata_version": unicodedata.unidata_version,
        },
        "verification": {
            "source_bindings_match": not source_differences,
            "registration_bindings_match": not registration_differences,
            "all_reported_aggregate_values_match_exactly": not analysis_differences,
            "selected_profile_chronology_fully_timestamp_verified": (
                chronology_fully_verified
            ),
            "differences": all_differences,
        },
        "selected_profile_time_audit": profile_time_audit,
        "methodological_limitation": (
            "Two selected target-side speaker-dialogue records are NaT-only. "
            "The frozen selector placed their sentinel chronology keys last, so the "
            "source-before-target relation is timestamp-verifiable for 74/76 profiles, "
            "not all 76. Aggregate style-signal values still reproduce exactly."
            if not chronology_fully_verified
            else None
        ),
        "recomputed": recomputed,
        "independence_and_privacy": {
            "original_analysis_controller_imported_or_called": False,
            "original_intake_module_imported_or_called": False,
            "scientific_report_used_as_numerical_input": False,
            "model_calls": 0,
            "new_generations": 0,
            "development_dialogue_text_used_for_features": True,
            "exploratory_or_validation_dialogue_text_used_for_features": False,
            "participant_text_emitted": False,
            "speaker_ids_emitted": False,
            "row_level_results_emitted": False,
        },
        "claim_boundary": registration["claim_boundary"],
    }


def _write_exclusive(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(_canonical(value))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    receipt = build_receipt(args.dataset_root)
    _write_exclusive(args.output, receipt)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "receipt_sha256": _sha256(args.output),
                "participant_text_emitted": False,
                "speaker_ids_emitted": False,
                "model_calls": 0,
            },
            sort_keys=True,
        )
    )
    return 0 if receipt["status"].startswith("PASS_EXACT_REPRODUCTION") else 1


if __name__ == "__main__":
    raise SystemExit(main())
