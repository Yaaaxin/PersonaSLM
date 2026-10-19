"""Prospective real-speaker style-signal diagnostic for RealPersonaChat."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import sys
import unicodedata


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import real_persona_chat_intake as intake


SCHEMA = "personaslm_rpc_style_signal_v1"
MIN_CONTROLS = 10
FEATURES = (
    "mean_turn_length", "sd_turn_length", "question_turn_rate",
    "exclamation_turn_rate", "full_stop_turn_rate", "ellipsis_turn_rate",
    "laughter_turn_rate", "polite_ending_rate", "hiragana_rate",
    "katakana_rate", "han_rate", "latin_rate", "digit_rate",
    "punctuation_rate", "symbol_rate")
REGISTRATION = REPO / (
    "docs/validation/p1/real_persona_chat_style_signal_v1/registration_v1.json")
INTAKE_RECEIPT = REPO / (
    "docs/validation/p1/real_persona_chat_intake_v1/intake_receipt_v1.json")


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_head():
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                            check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _dialogue_key(value):
    timestamps = [turn.get("timestamp") for turn in value["utterances"]
                  if turn.get("timestamp") not in (None, "", "NaT")]
    return (min(timestamps) if timestamps else "9999", value["dialogue_id"])


def load_development_records(dataset_root):
    root = Path(dataset_root)
    interlocutors = json.loads((root / "real_persona_chat" /
                                "interlocutors.json").read_text(encoding="utf-8"))
    assignments, assignment_hash = intake.speaker_split(interlocutors)
    records = defaultdict(list)
    for path in sorted((root / "real_persona_chat" / "dialogues").glob("*.json")):
        value = json.loads(path.read_bytes())
        left, right = value["interlocutors"]
        if assignments[left] != "DEVELOPMENT" or assignments[right] != "DEVELOPMENT":
            continue
        for speaker, partner in ((left, right), (right, left)):
            records[speaker].append({
                "dialogue_id": value["dialogue_id"],
                "partner": partner,
                "key": _dialogue_key(value),
                "turns": [turn["text"] for turn in value["utterances"]
                          if turn["interlocutor_id"] == speaker],
            })
    return records, assignment_hash


def select_profiles(records):
    selected = {}
    for speaker, rows in records.items():
        ordered = sorted(rows, key=lambda row: row["key"])
        source, source_partners = [], set()
        for row in ordered:
            if row["partner"] not in source_partners:
                source.append(row)
                source_partners.add(row["partner"])
            if len(source) == 2:
                break
        target, target_partners = [], set()
        for row in reversed(ordered):
            if (row["partner"] not in source_partners and
                    row["partner"] not in target_partners):
                target.append(row)
                target_partners.add(row["partner"])
            if len(target) == 2:
                break
        if len(source) != 2 or len(target) != 2:
            continue
        if max(row["key"] for row in source) >= min(row["key"] for row in target):
            continue
        selected[speaker] = {
            "source": source,
            "target": list(reversed(target)),
            "partners": source_partners | target_partners,
        }
    return selected


def eligible_profiles(selected, minimum_controls=MIN_CONTROLS):
    eligible = dict(selected)
    while True:
        keep = {speaker: value for speaker, value in eligible.items()
                if sum(other != speaker and
                       value["partners"].isdisjoint(candidate["partners"])
                       for other, candidate in eligible.items()) >=
                minimum_controls}
        if set(keep) == set(eligible):
            return keep
        eligible = keep


def _sanitize(text):
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("＊＊", "")


def style_vector(rows):
    turns = [_sanitize(text) for row in rows for text in row["turns"]]
    lengths = [len(text) for text in turns]
    joined = "".join(turns)
    total = max(1, len(joined))
    categories = Counter(unicodedata.category(char)[0] for char in joined)
    script = Counter()
    for char in joined:
        code = ord(char)
        script["hiragana"] += 0x3040 <= code <= 0x309F
        script["katakana"] += 0x30A0 <= code <= 0x30FF
        script["han"] += (0x3400 <= code <= 0x4DBF or
                          0x4E00 <= code <= 0x9FFF)
        script["latin"] += ("A" <= char <= "Z" or "a" <= char <= "z")
        script["digit"] += char.isdigit()
    count = max(1, len(turns))
    return {
        "mean_turn_length": statistics.fmean(lengths) / 50 if lengths else 0,
        "sd_turn_length": statistics.pstdev(lengths) / 50 if len(lengths) > 1 else 0,
        "question_turn_rate": sum("?" in text or "？" in text for text in turns) / count,
        "exclamation_turn_rate": sum("!" in text or "！" in text for text in turns) / count,
        "full_stop_turn_rate": sum("。" in text for text in turns) / count,
        "ellipsis_turn_rate": sum("…" in text or "..." in text for text in turns) / count,
        "laughter_turn_rate": sum("笑" in text or re.search(r"(?i)(^|\W)w+(\W|$)", text)
                                   is not None for text in turns) / count,
        "polite_ending_rate": sum(re.search(
            r"(です|ます|でした|ません)[。！？!?]*$", text) is not None
                                  for text in turns) / count,
        "hiragana_rate": script["hiragana"] / total,
        "katakana_rate": script["katakana"] / total,
        "han_rate": script["han"] / total,
        "latin_rate": script["latin"] / total,
        "digit_rate": script["digit"] / total,
        "punctuation_rate": categories["P"] / total,
        "symbol_rate": categories["S"] / total,
    }


def standardized_vectors(selected):
    raw = {}
    for speaker, value in selected.items():
        raw[speaker] = {side: style_vector(value[side])
                        for side in ("source", "target")}
    scales = {}
    for feature in FEATURES:
        values = [raw[speaker][side][feature] for speaker in raw
                  for side in ("source", "target")]
        scales[feature] = (statistics.fmean(values),
                           statistics.pstdev(values) or 1.0)
    vectors = {speaker: {side: tuple(
        (raw[speaker][side][feature] - scales[feature][0]) /
        scales[feature][1] for feature in FEATURES)
        for side in ("source", "target")} for speaker in raw}
    return vectors


def distance(left, right):
    return statistics.fmean(abs(a - b) for a, b in zip(left, right))


def evaluate(selected, active=None):
    active = set(selected) if active is None else set(active)
    subset = {speaker: selected[speaker] for speaker in active}
    vectors = standardized_vectors(subset)
    margins, percentiles, own_distances, other_medians = [], [], [], []
    for speaker, value in subset.items():
        source = vectors[speaker]["source"]
        own = distance(source, vectors[speaker]["target"])
        controls = [distance(source, vectors[other]["target"])
                    for other, candidate in subset.items()
                    if other != speaker and
                    value["partners"].isdisjoint(candidate["partners"])]
        if len(controls) < MIN_CONTROLS:
            continue
        other = statistics.median(controls)
        own_distances.append(own)
        other_medians.append(other)
        margins.append(other - own)
        percentiles.append(sum(value > own for value in controls) / len(controls))
    return {"margins": margins, "percentiles": percentiles,
            "own_distances": own_distances, "other_medians": other_medians}


def q(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def source_bindings(dataset_root):
    intake_doc = json.loads(INTAKE_RECEIPT.read_text(encoding="utf-8"))
    if intake_doc["status"] != "PASS":
        raise ValueError("RealPersonaChat intake did not pass")
    live = intake.audit(dataset_root)
    if live["status"] != "PASS":
        raise ValueError(f"Pinned RealPersonaChat source changed: {live['errors']}")
    if live["source"] != intake_doc["source"]:
        raise ValueError("Saved intake receipt differs from live source audit")
    return {
        "source_head": git_head(),
        "controller_sha256": sha256(Path(__file__)),
        "intake_receipt_sha256": sha256(INTAKE_RECEIPT),
        "dataset_revision": live["source"]["revision"],
        "dialogue_manifest_sha256":
            live["source"]["dialogue_manifest_sha256"],
        "interlocutors_sha256": live["source"]["interlocutors_sha256"],
        "dataset_root_version": (Path(dataset_root) / "VERSION").read_text(
            encoding="utf-8").strip(),
    }


def registration_document(dataset_root):
    records, assignment_hash = load_development_records(dataset_root)
    selected = eligible_profiles(select_profiles(records))
    cohort_binding = canonical(sorted(
        (speaker,
         [row["dialogue_id"] for row in value["source"]],
         [row["dialogue_id"] for row in value["target"]])
        for speaker, value in selected.items()))
    return {
        "schema_version": SCHEMA,
        "status": "PROSPECTIVELY_REGISTERED_NO_OUTCOMES_COMPUTED",
        "scientific_level": "DEVELOPMENT_MEASUREMENT_DIAGNOSTIC",
        "question": "Does later cross-partner dialogue retain a nonlexical speaker-style signal relative to other speakers?",
        "hypothesis": "Median-other minus own-speaker standardized L1 distance is positive.",
        "falsification": "Mean margin <= 0 or own-closer proportion <= 0.5 weakens practical use of this instrument.",
        "frozen_features": list(FEATURES),
        "unit": "pseudonymous development speaker",
        "profile_rule": "earliest two and latest two chronologically ordered dialogues with four distinct partners",
        "control_rule": "all other eligible targets with disjoint selected partner sets",
        "minimum_controls": MIN_CONTROLS,
        "primary_estimand": "mean(other-speaker median standardized L1 distance - own-speaker distance)",
        "secondary_estimands": ["median margin", "own-closer proportion",
                                 "mean control-percentile rank"],
        "uncertainty": "full leave-one-speaker-out mean-margin range; not a confidence interval",
        "split_assignment_sha256": assignment_hash,
        "eligible_speaker_count": len(selected),
        "cohort_and_dialogue_assignment_sha256": hashlib.sha256(
            cohort_binding).hexdigest(),
        "privacy": "No participant text, IDs, or row-level results may be emitted.",
        "claim_boundary": "A positive result is a stylometric signal, not validated Persona Fidelity or a model-conditioning effect.",
        "source_bindings": source_bindings(dataset_root),
        "outcomes_computed": False,
    }


def verify_registration(dataset_root):
    saved = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    expected = registration_document(dataset_root)
    if saved != expected:
        raise ValueError("Prospective registration or bound source changed")
    return saved


def analysis_document(dataset_root):
    registration = verify_registration(dataset_root)
    records, _ = load_development_records(dataset_root)
    selected = eligible_profiles(select_profiles(records))
    result = evaluate(selected)
    margins = result["margins"]
    if not margins:
        raise ValueError("No evaluable speakers")
    lopo = []
    for omitted in sorted(selected):
        reduced = evaluate(selected, set(selected) - {omitted})["margins"]
        if reduced:
            lopo.append(statistics.fmean(reduced))
    case_values = canonical({
        "margins": sorted(round(value, 12) for value in margins),
        "percentiles": sorted(round(value, 12)
                              for value in result["percentiles"]),
    })
    return {
        "schema_version": f"{SCHEMA}_analysis",
        "status": "COMPLETE",
        "scientific_level": "DEVELOPMENT_MEASUREMENT_DIAGNOSTIC",
        "registration_sha256": sha256(REGISTRATION),
        "speaker_units_planned": registration["eligible_speaker_count"],
        "speaker_units_resolved": len(margins),
        "speaker_units_missing": registration["eligible_speaker_count"] - len(margins),
        "primary": {
            "mean_margin": statistics.fmean(margins),
            "median_margin": statistics.median(margins),
            "q25_margin": q(margins, 0.25),
            "q75_margin": q(margins, 0.75),
            "own_closer_than_other_median_proportion":
                sum(value > 0 for value in margins) / len(margins),
            "mean_control_percentile_rank":
                statistics.fmean(result["percentiles"]),
            "mean_own_distance": statistics.fmean(result["own_distances"]),
            "mean_other_median_distance":
                statistics.fmean(result["other_medians"]),
        },
        "influence": {
            "leave_one_speaker_out_mean_margin_min": min(lopo),
            "leave_one_speaker_out_mean_margin_max": max(lopo),
            "interpretation": "Influence range only; not a confidence interval.",
        },
        "case_level_values_sha256": hashlib.sha256(case_values).hexdigest(),
        "participant_text_emitted": False,
        "speaker_ids_emitted": False,
        "interpretation_rule": registration["claim_boundary"],
    }


def write_exclusive(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(canonical(value))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("register", "analyze"))
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    value = (registration_document(args.dataset_root) if args.action == "register"
             else analysis_document(args.dataset_root))
    write_exclusive(args.output, value)
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
