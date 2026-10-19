"""Verify the pinned RealPersonaChat release without emitting participant text."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess


EXPECTED = {
    "version": "1.0.0",
    "revision": "28d0b6b3865b29cabc26c230a2db37cdf315e937",
    "license_sha256": "e8fb767ba9a496ad5a81d52c6abcd4af6d67a63651b3024ddfd1809f8ad23178",
    "readme_sha256": "9d4d6d01067ada9a6cd754f183b91215794e85901364ea78e0ee5eccca21e27f",
    "version_sha256": "4ca8bbd3c595ee306226c6996b32b8d47a900217c55a7ed0cfc868ee444f34f1",
    "interlocutors_sha256": "35d273f030a5cfd6f77cfb9172277017553737966720bf573baf09afd6e82eb2",
    "dialogue_manifest_sha256": "3ad5430af3d28373d8eed3fe989daa1e8cc192bbc77236afe0226dee706bac9c",
    "dialogues": 13583,
    "utterances": 408619,
    "speakers": 233,
    "pairs": 1572,
}
SPLIT_SEED = "PersonaSLM-RPC-speaker-split-v1"
SPLIT_COUNTS = {
    "DEVELOPMENT": 117,
    "EXPLORATORY_TEST": 58,
    "INDEPENDENT_VALIDATION_RESERVED": 58,
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def revision(root):
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True)
    return result.stdout.strip()


def speaker_split(speakers):
    ranked = sorted(speakers, key=lambda value: hashlib.sha256(
        f"{SPLIT_SEED}\0{value}".encode("utf-8")).hexdigest())
    limits = (SPLIT_COUNTS["DEVELOPMENT"],
              SPLIT_COUNTS["DEVELOPMENT"] + SPLIT_COUNTS["EXPLORATORY_TEST"])
    assigned = {}
    for index, speaker in enumerate(ranked):
        assigned[speaker] = ("DEVELOPMENT" if index < limits[0] else
                             "EXPLORATORY_TEST" if index < limits[1] else
                             "INDEPENDENT_VALIDATION_RESERVED")
    binding = "\n".join(f"{speaker}|{assigned[speaker]}" for speaker in ranked)
    return assigned, hashlib.sha256(binding.encode("utf-8")).hexdigest()


def audit(root, observed_revision=None):
    root = Path(root).resolve()
    dialogue_dir = root / "real_persona_chat" / "dialogues"
    interlocutors_path = root / "real_persona_chat" / "interlocutors.json"
    paths = sorted(dialogue_dir.glob("*.json"))
    speakers_doc = json.loads(interlocutors_path.read_text(encoding="utf-8"))
    assignments, split_hash = speaker_split(speakers_doc)
    utterances = valid_timestamps = unknown_timestamps = schema_errors = 0
    speaker_masks = other_masks = 0
    speakers = set()
    pair_counts = Counter()
    speaker_dialogues = Counter()
    within_split_dialogues = Counter()
    within_split_speakers = {name: set() for name in SPLIT_COUNTS}
    dialogue_manifest = hashlib.sha256()

    for path in paths:
        raw = path.read_bytes()
        file_hash = hashlib.sha256(raw).hexdigest()
        dialogue_manifest.update(
            path.name.encode("utf-8") + b"\0" + file_hash.encode("ascii") + b"\n")
        value = json.loads(raw)
        participants = value.get("interlocutors", [])
        turns = value.get("utterances")
        if len(participants) != 2 or not isinstance(turns, list):
            schema_errors += 1
            continue
        pair_counts[tuple(sorted(participants))] += 1
        for speaker in set(participants):
            speakers.add(speaker)
            speaker_dialogues[speaker] += 1
        left, right = (assignments.get(speaker) for speaker in participants)
        if left == right and left is not None:
            within_split_dialogues[left] += 1
            within_split_speakers[left].update(participants)
        else:
            within_split_dialogues["CROSS_SPLIT_EXCLUDED"] += 1
        for turn in turns:
            utterances += 1
            if turn.get("interlocutor_id") not in participants:
                schema_errors += 1
            timestamp = turn.get("timestamp")
            if timestamp == "NaT":
                unknown_timestamps += 1
            elif isinstance(timestamp, str) and timestamp:
                valid_timestamps += 1
            else:
                schema_errors += 1
            text = turn.get("text")
            if not isinstance(text, str):
                schema_errors += 1
                continue
            speaker_masks += int("<" in text and ">" in text)
            other_masks += int("＊＊" in text)

    persona_counts = Counter(len(value.get("persona", []))
                             for value in speakers_doc.values())
    actual = {
        "version": (root / "VERSION").read_text(encoding="utf-8").strip(),
        "revision": observed_revision or revision(root),
        "license_sha256": sha256(root / "LICENSE"),
        "readme_sha256": sha256(root / "README.md"),
        "version_sha256": sha256(root / "VERSION"),
        "interlocutors_sha256": sha256(interlocutors_path),
        "dialogue_manifest_sha256": dialogue_manifest.hexdigest(),
        "dialogues": len(paths),
        "utterances": utterances,
        "speakers": len(speakers),
        "pairs": len(pair_counts),
    }
    errors = [f"{key}: expected {expected}, observed {actual.get(key)}"
              for key, expected in EXPECTED.items() if actual.get(key) != expected]
    if speakers != set(speakers_doc):
        errors.append("dialogue and interlocutor speaker ID sets differ")
    if persona_counts != {10: 233}:
        errors.append(f"persona sentence counts changed: {dict(persona_counts)}")
    if schema_errors:
        errors.append(f"schema errors: {schema_errors}")

    return {
        "schema_version": "personaslm_real_persona_chat_intake_v1",
        "status": "PASS" if not errors else "FAIL",
        "source": {
            "dataset": "RealPersonaChat",
            "repository": "https://github.com/nu-dialogue/real-persona-chat",
            "paper": "https://aclanthology.org/2023.paclic-1.85/",
            "license": "CC BY-SA 4.0",
            **actual,
        },
        "aggregate_observations": {
            "persona_sentence_count_distribution": dict(persona_counts),
            "dialogues_per_speaker_min": min(speaker_dialogues.values()),
            "dialogues_per_speaker_max": max(speaker_dialogues.values()),
            "dialogues_per_pair_min": min(pair_counts.values()),
            "dialogues_per_pair_max": max(pair_counts.values()),
            "valid_timestamps": valid_timestamps,
            "unknown_timestamps": unknown_timestamps,
            "utterances_with_speaker_mask_marker": speaker_masks,
            "utterances_with_other_mask_marker": other_masks,
        },
        "prospective_split": {
            "algorithm": "sha256(seed + NUL + speaker_id), ascending",
            "seed": SPLIT_SEED,
            "speaker_counts": SPLIT_COUNTS,
            "assignment_sha256": split_hash,
            "within_split_dialogues": dict(within_split_dialogues),
            "speakers_with_within_split_dialogue": {
                key: len(value) for key, value in within_split_speakers.items()},
            "cross_split_rule": "EXCLUDE_DIALOGUE",
            "independent_validation_access": "RESERVED_NOT_FOR_DEVELOPMENT",
        },
        "governance": {
            "allowed_scope": "PSEUDONYMOUS_AGGREGATE_NON_IMPERSONATION_RESEARCH",
            "prohibited": ["REIDENTIFICATION", "SPECIFIC_SPEAKER_IMPERSONATION",
                           "ROW_LEVEL_PUBLIC_GENERATIONS"],
            "excluded_predictors": ["personality", "demographic_information",
                                    "text_chat_experience"],
            "raw_data_location": "IGNORED_LOCAL_ONLY",
            "public_evidence": "AGGREGATES_HASHES_AND_CODE_ONLY",
            "legal_note": "Scientific data-governance assessment; not legal advice.",
        },
        "participant_text_emitted": False,
        "errors": errors,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = audit(args.dataset_root)
    rendered = (json.dumps(report, ensure_ascii=False, indent=2,
                           sort_keys=True) + "\n").encode("utf-8")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as handle:
            handle.write(rendered)
    print(rendered.decode("utf-8"), end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
