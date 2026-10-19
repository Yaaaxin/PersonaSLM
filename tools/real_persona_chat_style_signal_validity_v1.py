"""Development-only validity controls for the frozen RealPersonaChat style signal.

This is a post-outcome diagnostic.  It scans every dialogue only through its
structural ``utterances`` key, then parses utterance text solely for dialogues
whose two speakers belong to the frozen development split.
"""

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
import real_persona_chat_style_signal_v1 as original


SCHEMA = "personaslm_rpc_style_signal_validity_v1"
DEFAULT_DATASET = REPO / ".local/datasets/real-persona-chat"
EVIDENCE_DIR = REPO / "docs/validation/p1/real_persona_chat_style_signal_validity_v1"
REGISTRATION = EVIDENCE_DIR / "registration_v1.json"
REGISTRATION_AMENDMENT = EVIDENCE_DIR / "registration_amendment_v1_1.json"
OUTPUT = EVIDENCE_DIR / "analysis_v1.json"
TEST = REPO / "tests/test_real_persona_chat_style_signal_validity_v1.py"
PRIOR_REGISTRATION = REPO / (
    "docs/validation/p1/real_persona_chat_style_signal_v1/registration_v1.json")
PRIOR_ANALYSIS = REPO / (
    "docs/validation/p1/real_persona_chat_style_signal_v1/analysis_v1.json")
PRIOR_CORRECTION = REPO / (
    "docs/validation/p1/real_persona_chat_style_signal_v1/interpretation_correction_v1.json")
PRIOR_REPRODUCTION = REPO / (
    "docs/validation/p1/real_persona_chat_style_signal_v1/analysis_reproduction_v1.json")
INTAKE_RECEIPT = REPO / (
    "docs/validation/p1/real_persona_chat_intake_v1/intake_receipt_v1.json")

HEADER_MARKER = b'"utterances"'
HEADER_LIMIT = 65536
MATCHED_CONTROL_COUNT = 10
TOPIC_NGRAM_N = 3
CORRELATION_FLAG_ABS = 0.30
FEATURE_SETS = {
    "full_frozen": tuple(original.FEATURES),
    "without_length": tuple(
        name for name in original.FEATURES
        if name not in {"mean_turn_length", "sd_turn_length"}),
    "without_explicit_lexical_markers": tuple(
        name for name in original.FEATURES
        if name not in {"laughter_turn_rate", "polite_ending_rate"}),
    "without_length_or_explicit_lexical_markers": tuple(
        name for name in original.FEATURES
        if name not in {"mean_turn_length", "sd_turn_length",
                        "laughter_turn_rate", "polite_ending_rate"}),
}


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True,
        text=True).stdout.strip()


def participants_from_structural_header(path):
    """Read no application-visible bytes beyond the utterances key."""
    header = bytearray()
    with Path(path).open("rb") as handle:
        while len(header) <= HEADER_LIMIT:
            byte = handle.read(1)
            if not byte:
                raise ValueError("Dialogue ended before structural utterances key")
            header.extend(byte)
            if header.endswith(HEADER_MARKER):
                break
        else:
            raise ValueError("Dialogue structural header exceeded frozen limit")
    prefix = bytes(header[:-len(HEADER_MARKER)])
    if b'"text"' in prefix or b'"timestamp"' in prefix:
        raise ValueError("Dialogue content appeared before structural utterances key")
    match = re.search(rb'"interlocutors"\s*:\s*(\[[^\]]*\])', prefix)
    if match is None:
        raise ValueError("Dialogue structural header lacks interlocutors")
    participants = json.loads(match.group(1).decode("utf-8"))
    if (not isinstance(participants, list) or len(participants) != 2 or
            not all(isinstance(value, str) for value in participants)):
        raise ValueError("Dialogue structural interlocutors are invalid")
    return tuple(participants)


def development_manifest(dialogue_dir, expected_split_hash=None):
    headers = []
    speakers = set()
    for path in sorted(Path(dialogue_dir).glob("*.json")):
        participants = participants_from_structural_header(path)
        speakers.update(participants)
        headers.append((path, participants))
    assignments, split_hash = intake.speaker_split(speakers)
    if expected_split_hash is not None and split_hash != expected_split_hash:
        raise ValueError("Frozen speaker split changed")
    manifest = [path for path, pair in headers
                if all(assignments[value] == "DEVELOPMENT" for value in pair)]
    return manifest, assignments, {
        "dialogue_structural_headers_scanned": len(headers),
        "speaker_ids_seen_in_structural_headers": len(speakers),
        "development_dialogues_selected_before_text_parse": len(manifest),
        "excluded_dialogues_not_text_parsed": len(headers) - len(manifest),
        "split_assignment_sha256": split_hash,
    }


def load_development_records(dataset_root, expected_split_hash=None):
    root = Path(dataset_root)
    manifest, assignments, access = development_manifest(
        root / "real_persona_chat/dialogues", expected_split_hash)
    records = defaultdict(list)
    parsed = 0
    for path in manifest:
        value = json.loads(path.read_bytes())
        left, right = value["interlocutors"]
        if not all(assignments[item] == "DEVELOPMENT" for item in (left, right)):
            raise ValueError("Non-development dialogue reached text parser")
        parsed += 1
        for speaker, partner in ((left, right), (right, left)):
            records[speaker].append({
                "dialogue_id": value["dialogue_id"],
                "partner": partner,
                "key": original._dialogue_key(value),
                "turns": [turn["text"] for turn in value["utterances"]
                          if turn["interlocutor_id"] == speaker],
                "partner_turns": [turn["text"] for turn in value["utterances"]
                                  if turn["interlocutor_id"] == partner],
            })
    access.update({
        "development_dialogue_texts_parsed": parsed,
        "exploratory_test_dialogue_texts_parsed": 0,
        "independent_validation_dialogue_texts_parsed": 0,
        "cross_split_dialogue_texts_parsed": 0,
    })
    return records, access


def cohort_binding(selected):
    value = sorted((
        speaker,
        [row["dialogue_id"] for row in profile["source"]],
        [row["dialogue_id"] for row in profile["target"]],
    ) for speaker, profile in selected.items())
    return hashlib.sha256(canonical(value)).hexdigest()


def profile_vector(rows):
    return original.style_vector(rows)


def standardized_vectors(selected, features):
    raw = {speaker: {side: profile_vector(profile[side])
                     for side in ("source", "target")}
           for speaker, profile in selected.items()}
    scales = {}
    for feature in features:
        values = [raw[speaker][side][feature] for speaker in raw
                  for side in ("source", "target")]
        scales[feature] = (statistics.fmean(values),
                           statistics.pstdev(values) or 1.0)
    vectors = {speaker: {side: tuple(
        (raw[speaker][side][feature] - scales[feature][0]) /
        scales[feature][1] for feature in features)
        for side in ("source", "target")} for speaker in raw}
    return vectors, scales


def z_vector(raw, features, scales):
    return tuple((raw[name] - scales[name][0]) / scales[name][1]
                 for name in features)


def controls_for(speaker, selected):
    partners = selected[speaker]["partners"]
    return [other for other, candidate in selected.items()
            if other != speaker and partners.isdisjoint(candidate["partners"])]


def _turns(rows):
    return [text for row in rows for text in row["turns"]]


def length_stats(rows):
    turns = [original._sanitize(text) for text in _turns(rows)]
    return len(turns), sum(len(text) for text in turns)


def normalized_turn(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def content_ngrams(rows, size=TOPIC_NGRAM_N):
    grams = set()
    for text in _turns(rows):
        normalized = "".join(
            char for char in unicodedata.normalize("NFKC", text).casefold()
            if unicodedata.category(char)[0] in {"L", "N"})
        grams.update(normalized[index:index + size]
                     for index in range(max(0, len(normalized) - size + 1)))
    return grams


def jaccard(left, right):
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def length_match_score(focal, candidate):
    focal_turns, focal_chars = focal
    other_turns, other_chars = candidate
    return (abs(math.log1p(focal_turns) - math.log1p(other_turns)) +
            abs(math.log1p(focal_chars) - math.log1p(other_chars)))


def summarize(values):
    if not values:
        raise ValueError("Cannot summarize an empty diagnostic")
    return {
        "n": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "q25": original.q(values, 0.25),
        "q75": original.q(values, 0.75),
        "positive_proportion": sum(value > 0 for value in values) / len(values),
    }


def evaluate_style(selected, features, matching=None):
    vectors, scales = standardized_vectors(selected, features)
    topic = {speaker: {side: content_ngrams(profile[side])
                       for side in ("source", "target")}
             for speaker, profile in selected.items()}
    lengths = {speaker: {side: length_stats(profile[side])
                         for side in ("source", "target")}
               for speaker, profile in selected.items()}
    rows = {}
    for speaker in selected:
        own = original.distance(vectors[speaker]["source"],
                                vectors[speaker]["target"])
        candidates = []
        own_topic = jaccard(topic[speaker]["source"], topic[speaker]["target"])
        for other in controls_for(speaker, selected):
            style_distance = original.distance(
                vectors[speaker]["source"], vectors[other]["target"])
            if matching == "length":
                key = length_match_score(lengths[speaker]["target"],
                                         lengths[other]["target"])
            elif matching == "topic":
                candidate_topic = jaccard(topic[speaker]["source"],
                                           topic[other]["target"])
                key = abs(candidate_topic - own_topic)
            else:
                key = 0.0
            candidates.append((key, hashlib.sha256(other.encode()).hexdigest(),
                               style_distance))
        if len(candidates) < original.MIN_CONTROLS:
            continue
        if matching:
            candidates = sorted(candidates)[:MATCHED_CONTROL_COUNT]
        distances = [value[2] for value in candidates]
        rows[speaker] = {
            "own_distance": own,
            "other_median_distance": statistics.median(distances),
            "margin": statistics.median(distances) - own,
        }
    return rows, scales


def exact_turn_decontamination(selected):
    cleaned = {}
    profiles_with_overlap = unique_shared = removed_source = removed_target = 0
    for speaker, profile in selected.items():
        source_values = {normalized_turn(text) for text in _turns(profile["source"])}
        target_values = {normalized_turn(text) for text in _turns(profile["target"])}
        shared = (source_values & target_values) - {""}
        profiles_with_overlap += bool(shared)
        unique_shared += len(shared)
        sides = {}
        for side in ("source", "target"):
            sides[side] = []
            for row in profile[side]:
                kept = [text for text in row["turns"]
                        if normalized_turn(text) not in shared]
                removed = len(row["turns"]) - len(kept)
                if side == "source":
                    removed_source += removed
                else:
                    removed_target += removed
                sides[side].append({**row, "turns": kept})
        cleaned[speaker] = {**profile, **sides}
    return cleaned, {
        "profiles_with_any_exact_normalized_turn_overlap": profiles_with_overlap,
        "unique_exact_normalized_turns_shared_sum": unique_shared,
        "source_turn_occurrences_removed": removed_source,
        "target_turn_occurrences_removed": removed_target,
    }


def rankdata(values):
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        rank = (cursor + end - 1) / 2 + 1
        for index in order[cursor:end]:
            ranks[index] = rank
        cursor = end
    return ranks


def spearman(left, right):
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("Spearman inputs must have equal nontrivial length")
    left_ranks, right_ranks = rankdata(left), rankdata(right)
    left_mean, right_mean = statistics.fmean(left_ranks), statistics.fmean(right_ranks)
    numerator = sum((a - left_mean) * (b - right_mean)
                    for a, b in zip(left_ranks, right_ranks))
    denominator = math.sqrt(
        sum((a - left_mean) ** 2 for a in left_ranks) *
        sum((b - right_mean) ** 2 for b in right_ranks))
    return numerator / denominator if denominator else 0.0


def source_integrity(dataset_root):
    receipt = json.loads(INTAKE_RECEIPT.read_text(encoding="utf-8"))
    root = Path(dataset_root)
    head = _git(root, "rev-parse", "HEAD")
    dirty = _git(root, "status", "--porcelain", "--untracked-files=no")
    if head != receipt["source"]["revision"] or dirty:
        raise ValueError("Pinned dataset Git state differs from verified intake")
    return {
        "dataset_revision": head,
        "dialogue_manifest_sha256": receipt["source"]["dialogue_manifest_sha256"],
        "interlocutors_sha256": receipt["source"]["interlocutors_sha256"],
        "intake_receipt_sha256": sha256(INTAKE_RECEIPT),
        "tracked_dataset_worktree_clean": True,
    }


def validate_registration():
    registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    amendment = json.loads(REGISTRATION_AMENDMENT.read_text(encoding="utf-8"))
    expected_hashes = {
        "analysis_controller_sha256": amendment["original_controller_sha256"],
        "analysis_test_sha256": sha256(TEST),
        "prior_registration_sha256": sha256(PRIOR_REGISTRATION),
        "prior_analysis_sha256": sha256(PRIOR_ANALYSIS),
        "prior_interpretation_correction_sha256": sha256(PRIOR_CORRECTION),
        "prior_independent_reproduction_sha256": sha256(PRIOR_REPRODUCTION),
        "intake_receipt_sha256": sha256(INTAKE_RECEIPT),
    }
    if registration.get("source_bindings") != expected_hashes:
        raise ValueError("Validity registration source bindings changed")
    if registration.get("frozen_parameters") != {
            "feature_sets": {key: list(value) for key, value in FEATURE_SETS.items()},
            "topic_character_ngram_n": TOPIC_NGRAM_N,
            "matched_control_count": MATCHED_CONTROL_COUNT,
            "correlation_flag_absolute_rho": CORRELATION_FLAG_ABS}:
        raise ValueError("Validity registration parameters changed")
    if (registration.get("status") != "POST_OUTCOME_PROSPECTIVE_CONTROLS_FROZEN" or
            registration.get("outcomes_computed_before_freeze") is not False):
        raise ValueError("Validity registration status is invalid")
    expected_amendment = {
        "schema_version": "personaslm_rpc_style_signal_validity_v1_registration_amendment_1",
        "status": "PROSPECTIVE_IMPLEMENTATION_CORRECTION_BEFORE_DATA_ACCESS",
        "parent_registration_sha256": sha256(REGISTRATION),
        "original_controller_sha256": registration["source_bindings"][
            "analysis_controller_sha256"],
        "corrected_controller_sha256": sha256(Path(__file__)),
        "correction": (
            "Read split_assignment_sha256 from the registered split_policy "
            "object rather than the registration root."),
        "failed_attempt": "KeyError before development manifest construction",
        "control_outcomes_computed_before_amendment": False,
        "participant_text_parsed_before_amendment": False,
    }
    if amendment != expected_amendment:
        raise ValueError("Validity registration amendment changed")
    return registration


def build_analysis(dataset_root):
    registration = validate_registration()
    integrity = source_integrity(dataset_root)
    records, access = load_development_records(
        dataset_root, registration["split_policy"]["split_assignment_sha256"])
    selected = original.eligible_profiles(original.select_profiles(records))
    if (len(selected) != registration["eligible_speaker_count"] or
            cohort_binding(selected) != registration[
                "cohort_and_dialogue_assignment_sha256"]):
        raise ValueError("Frozen development cohort changed")

    full_rows, full_scales = evaluate_style(
        selected, FEATURE_SETS["full_frozen"])
    archived = json.loads(PRIOR_ANALYSIS.read_text(encoding="utf-8"))["primary"]
    full_margins = [row["margin"] for row in full_rows.values()]
    if (abs(statistics.fmean(full_margins) - archived["mean_margin"]) > 1e-12 or
            len(full_rows) != 76):
        raise ValueError("Original frozen aggregate did not reproduce")

    ablations = {}
    case_values = {"full": full_rows}
    for name, features in FEATURE_SETS.items():
        rows = full_rows if name == "full_frozen" else evaluate_style(
            selected, features)[0]
        ablations[name] = summarize([row["margin"] for row in rows.values()])
        case_values[name] = rows

    length_matched, _ = evaluate_style(
        selected, FEATURE_SETS["full_frozen"], matching="length")
    topic_matched, _ = evaluate_style(
        selected, FEATURE_SETS["full_frozen"], matching="topic")

    topic_sets = {speaker: {side: content_ngrams(profile[side])
                            for side in ("source", "target")}
                  for speaker, profile in selected.items()}
    topic_margins = {}
    for speaker in selected:
        own = jaccard(topic_sets[speaker]["source"],
                      topic_sets[speaker]["target"])
        others = [jaccard(topic_sets[speaker]["source"],
                          topic_sets[other]["target"])
                  for other in controls_for(speaker, selected)]
        topic_margins[speaker] = own - statistics.median(others)

    cleaned, duplicate_audit = exact_turn_decontamination(selected)
    cleaned_rows, _ = evaluate_style(cleaned, FEATURE_SETS["full_frozen"])

    partner_margins = {}
    for speaker, profile in selected.items():
        partner_rows = [{"turns": row["partner_turns"]}
                        for row in profile["source"]]
        partner = z_vector(profile_vector(partner_rows),
                           FEATURE_SETS["full_frozen"], full_scales)
        source = z_vector(profile_vector(profile["source"]),
                          FEATURE_SETS["full_frozen"], full_scales)
        target = z_vector(profile_vector(profile["target"]),
                          FEATURE_SETS["full_frozen"], full_scales)
        partner_margins[speaker] = (
            original.distance(partner, target) - original.distance(source, target))

    frequency = []
    selected_turns = []
    selected_chars = []
    char_imbalance = []
    turn_imbalance = []
    margins = []
    for speaker, profile in selected.items():
        source_length = length_stats(profile["source"])
        target_length = length_stats(profile["target"])
        frequency.append(len(records[speaker]))
        selected_turns.append(source_length[0] + target_length[0])
        selected_chars.append(source_length[1] + target_length[1])
        turn_imbalance.append(abs(math.log1p(source_length[0]) -
                                  math.log1p(target_length[0])))
        char_imbalance.append(abs(math.log1p(source_length[1]) -
                                  math.log1p(target_length[1])))
        margins.append(full_rows[speaker]["margin"])
    correlations = {
        "available_development_dialogue_count": spearman(frequency, margins),
        "selected_turn_count": spearman(selected_turns, margins),
        "selected_character_count": spearman(selected_chars, margins),
        "source_target_turn_count_imbalance": spearman(turn_imbalance, margins),
        "source_target_character_count_imbalance": spearman(char_imbalance, margins),
    }
    ordered = sorted(range(len(frequency)), key=lambda i: (frequency[i], i))
    frequency_tertiles = []
    for group in (ordered[:25], ordered[25:50], ordered[50:]):
        frequency_tertiles.append({
            "n": len(group),
            "available_dialogues_min": min(frequency[i] for i in group),
            "available_dialogues_max": max(frequency[i] for i in group),
            "mean_style_margin": statistics.fmean(margins[i] for i in group),
        })

    dialogue_overlap_violations = sum(
        bool({row["dialogue_id"] for row in profile["source"]} &
             {row["dialogue_id"] for row in profile["target"]})
        for profile in selected.values())
    partner_cardinality_violations = sum(
        len(profile["partners"]) != 4 for profile in selected.values())
    exact_clean_margins = [row["margin"] for row in cleaned_rows.values()]
    length_matched_margins = [row["margin"] for row in length_matched.values()]
    topic_matched_margins = [row["margin"] for row in topic_matched.values()]

    compact_cases = {
        "ablations": {name: sorted(round(row["margin"], 12)
                                   for row in rows.values())
                      for name, rows in case_values.items()},
        "length_matched": sorted(round(value, 12)
                                 for value in length_matched_margins),
        "topic_matched": sorted(round(value, 12)
                                for value in topic_matched_margins),
        "topic_overlap": sorted(round(value, 12)
                                for value in topic_margins.values()),
        "exact_turn_decontaminated": sorted(round(value, 12)
                                            for value in exact_clean_margins),
        "partner_negative": sorted(round(value, 12)
                                   for value in partner_margins.values()),
    }
    all_correlations_below_flag = all(
        abs(value) < CORRELATION_FLAG_ABS for value in correlations.values())
    combined = ablations["without_length_or_explicit_lexical_markers"]
    return {
        "schema_version": f"{SCHEMA}_analysis",
        "status": "COMPLETE_POST_OUTCOME_DEVELOPMENT_VALIDITY_DIAGNOSTIC",
        "scientific_level": "POST_OUTCOME_DEVELOPMENT_DIAGNOSTIC_NOT_CONFIRMATORY",
        "registration_sha256": sha256(REGISTRATION),
        "source_integrity": integrity,
        "privacy_and_split_access": {
            **access,
            "participant_text_emitted": False,
            "speaker_ids_emitted": False,
            "row_level_results_emitted": False,
        },
        "cohort": {
            "eligible_development_speakers": len(selected),
            "cohort_and_dialogue_assignment_sha256": cohort_binding(selected),
            "original_frozen_mean_margin_reproduced": statistics.fmean(full_margins),
        },
        "feature_ablation_style_margins": ablations,
        "length_controls": {
            "ten_nearest_target_length_matched_controls":
                summarize(length_matched_margins),
            "margin_correlations": correlations,
            "absolute_spearman_flag_threshold": CORRELATION_FLAG_ABS,
            "all_absolute_correlations_below_flag_threshold":
                all_correlations_below_flag,
            "frequency_tertiles": frequency_tertiles,
        },
        "topic_and_lexical_controls": {
            "character_trigram_overlap_own_minus_other_median":
                summarize(list(topic_margins.values())),
            "ten_nearest_trigram_overlap_matched_style_controls":
                summarize(topic_matched_margins),
            "interpretation": (
                "Character trigrams are a lexical/topic negative control, not a "
                "semantic topic model or Persona Fidelity metric."),
        },
        "formulaic_and_direct_leakage_controls": {
            **duplicate_audit,
            "exact_turn_decontaminated_full_feature_style_margin":
                summarize(exact_clean_margins),
            "source_target_dialogue_id_overlap_profile_count":
                dialogue_overlap_violations,
            "profiles_without_four_distinct_selected_partners":
                partner_cardinality_violations,
        },
        "partner_behavior_negative_control": {
            "partner_source_to_target_minus_own_source_to_target_distance":
                summarize(list(partner_margins.values())),
            "interpretation": (
                "A positive value means the focal target is closer to its own "
                "source profile than to the aggregate language of the two source "
                "partners; this does not eliminate broader accommodation."),
        },
        "registered_diagnostic_readout": {
            "signal_positive_after_joint_length_and_marker_ablation":
                combined["mean"] > 0 and combined["positive_proportion"] > 0.5,
            "signal_positive_with_length_matched_controls":
                statistics.fmean(length_matched_margins) > 0 and
                sum(value > 0 for value in length_matched_margins) / 76 > 0.5,
            "signal_positive_with_topic_overlap_matched_controls":
                statistics.fmean(topic_matched_margins) > 0 and
                sum(value > 0 for value in topic_matched_margins) / 76 > 0.5,
            "exact_turn_overlap_detected":
                duplicate_audit[
                    "profiles_with_any_exact_normalized_turn_overlap"] > 0,
            "imbalance_association_flagged": not all_correlations_below_flag,
            "own_source_closer_than_immediate_source_partners":
                statistics.fmean(partner_margins.values()) > 0 and
                sum(value > 0 for value in partner_margins.values()) / 76 > 0.5,
        },
        "case_level_values_sha256": hashlib.sha256(
            canonical(compact_cases)).hexdigest(),
        "supported_claim": (
            "Development-only evidence about whether the observed mixed "
            "surface/stylometric signal survives finite confounding controls."),
        "unsupported_claims": [
            "validated generative Persona Fidelity",
            "model conditioning effect",
            "stable speaker identity independent of topic",
            "population generalization",
            "independent validation",
        ],
        "model_calls": 0,
        "new_generations": 0,
    }


def write_exclusive(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(canonical(value))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    result = build_analysis(args.dataset_root)
    write_exclusive(args.output, result)
    print(json.dumps({
        "status": result["status"],
        "analysis_sha256": sha256(args.output),
        "development_speakers": result["cohort"][
            "eligible_development_speakers"],
        "nondevelopment_dialogue_texts_parsed": 0,
        "participant_text_emitted": False,
        "new_generations": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
