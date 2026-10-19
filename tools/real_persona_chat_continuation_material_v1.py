"""Private-only material for a finite RPC observed-continuation recognition study.

No inference, registration, writes, participant identification, or validation
content access. The endpoint is observed provenance, not semantic acceptability.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import real_persona_chat_sfh_pilot_v1 as material


SELECTION = "RPC-continuation-recognition-v1"
ARMS = ("NONE", "CORRECT", "MISMATCH")
HISTORY_TURNS = 6
MAX_WINDOWS_PER_SOURCE = 8
MAX_SOURCE_TOKEN_DIFFERENCE = 8
OLD_MATERIALS = (
    (Path(".local/experiments/real_persona_chat_sfh_pilot_v1/materials_v1.json"),
     "4f2e57ba05a8784835c0c0108ec10ba18851a28c084b1dc293b4eb4359a1ff4e"),
    (Path(".local/experiments/real_persona_chat_style_specificity_v1/frozen_manifest_v1.json"),
     "7310946d00bf8ac5e4f6bc61336654177202795f86e07a7e124726ac3b5bc4a6"),
)


def order_key(value):
    return hashlib.sha256((SELECTION + "\0" + str(value)).encode()).hexdigest()


def load_development_dialogues(dataset_root):
    """Reuse the strict loader's primitives without decoding persona values."""
    root = Path(dataset_root) / "real_persona_chat"
    ids = material._speaker_ids(root / "interlocutors.json")
    assignments, split_hash = material.intake.speaker_split({key: None for key in ids})
    development = {key for key, value in assignments.items() if value == "DEVELOPMENT"}
    dialogues, excluded = [], 0
    for path in sorted((root / "dialogues").glob("*.json")):
        participants = material._dialogue_participants(path)
        if not all(speaker in development for speaker in participants):
            excluded += 1
            continue
        value = json.loads(path.read_bytes())
        if value["interlocutors"] != participants:
            raise ValueError("Dialogue header changed during development-only load")
        dialogues.append(value)
    return dialogues, split_hash, excluded


def first_target_context(record, speaker):
    turns = record["turns"]
    for index in range(HISTORY_TURNS + 1, len(turns)):
        reference, query = turns[index], turns[index - 1]
        history = turns[index - HISTORY_TURNS - 1:index - 1]
        if reference["interlocutor_id"] != speaker or query["interlocutor_id"] == speaker:
            continue
        texts = [turn["text"] for turn in history] + [query["text"]]
        if any(material.MASK.search(text) for text in texts + [reference["text"]]):
            continue
        if not (4 <= len(query["text"]) <= 240 and 8 <= len(reference["text"]) <= 240):
            continue
        if not all(material.JAPANESE.search(text) for text in (query["text"], reference["text"])):
            continue
        if not material._no_answer_leak(reference["text"], texts):
            continue
        return {"history": history, "query": query, "reference": reference,
                "reference_index": index}
    return None


def source_windows(record, speaker):
    found = []
    for start in range(len(record["turns"]) - HISTORY_TURNS + 1):
        turns = record["turns"][start:start + HISTORY_TURNS]
        if turns[0]["interlocutor_id"] != speaker:
            continue
        if any(not turn["text"].strip() or material.MASK.search(turn["text"]) for turn in turns):
            continue
        if len({turn["interlocutor_id"] for turn in turns}) != 2:
            continue
        found.append({"dialogue_id": record["dialogue_id"], "partner": record["partner"],
                      "start_index": start, "end": record["end"], "turns": turns})
        if len(found) == MAX_WINDOWS_PER_SOURCE:
            break
    return found


def profiles_from_dialogues(dialogues, cohort, excluded_targets):
    by_speaker = defaultdict(list)
    for dialogue in dialogues:
        for speaker in dialogue["interlocutors"]:
            if speaker in cohort:
                record = material._dialogue_record(dialogue, speaker)
                if record is not None:
                    by_speaker[speaker].append(record)
    profiles = []
    for speaker in sorted(cohort, key=order_key):
        records = sorted(by_speaker[speaker], key=lambda row: (row["start"], str(row["dialogue_id"])))
        targets = sorted(records, key=lambda row: order_key(row["dialogue_id"]))
        for target in targets:
            if target["dialogue_id"] in excluded_targets:
                continue
            context = first_target_context(target, speaker)
            if context is None:
                continue
            windows = []
            for source in records:
                if source["end"] < target["start"] and source["partner"] != target["partner"]:
                    windows.extend(source_windows(source, speaker))
            if windows:
                profiles.append({"speaker": speaker, "target": target,
                                 "context": context, "source_windows": windows})
                break
    return profiles


def labelled_history(turns, speaker):
    return "\n".join(("匿名話者" if turn["interlocutor_id"] == speaker else "相手") +
                     ": " + turn["text"] for turn in turns)


def source_block(turns, speaker):
    return "[以前の別の会話]\n" + labelled_history(turns, speaker)


def token_count(tokenizer, text):
    value = tokenizer(text)
    count = value if type(value) is int else len(value)
    if count <= 0:
        raise ValueError("Tokenizer must return positive token count or token IDs")
    return count


def paired_windows(left, right, tokenizer, used_people, token_cache):
    candidates = [row["context"]["reference"]["text"] for row in (left, right)]
    lengths = [len(material._normalized(text)) for text in candidates]
    if (not min(lengths) or max(lengths) / min(lengths) > 1.25 or
            abs(lengths[0] - lengths[1]) > 8 or
            material._normalized(candidates[0]) == material._normalized(candidates[1])):
        return None
    base_people = [{row["speaker"], row["target"]["partner"]} for row in (left, right)]
    if base_people[0] & base_people[1] or set.union(*base_people) & used_people:
        return None
    target_start = min(left["target"]["start"], right["target"]["start"])
    local_text = [turn["text"] for row in (left, right)
                  for turn in row["context"]["history"] + [row["context"]["query"]]]
    if any(not material._no_answer_leak(candidate, local_text) for candidate in candidates):
        return None
    for own in left["source_windows"]:
        if own["end"] >= target_start:
            continue
        own_people = base_people[0] | {own["partner"]}
        if own_people & used_people or own_people & base_people[1]:
            continue
        for donor in right["source_windows"]:
            if donor["end"] >= target_start:
                continue
            donor_people = base_people[1] | {donor["partner"]}
            if own_people & donor_people or donor_people & used_people:
                continue
            dialogue_ids = (left["target"]["dialogue_id"], right["target"]["dialogue_id"],
                            own["dialogue_id"], donor["dialogue_id"])
            if len(set(dialogue_ids)) != 4:
                continue
            texts = [turn["text"] for window in (own, donor) for turn in window["turns"]]
            if any(not material._no_answer_leak(candidate, texts) for candidate in candidates):
                continue
            counts = []
            for row, window in ((left, own), (right, donor)):
                block = source_block(window["turns"], row["speaker"])
                if block not in token_cache:
                    token_cache[block] = token_count(tokenizer, block)
                counts.append(token_cache[block])
            if abs(counts[0] - counts[1]) <= MAX_SOURCE_TOKEN_DIFFERENCE:
                return own, donor, counts, own_people | donor_people
    return None


def select_cases(profiles, tokenizer, pair_count=4):
    if pair_count != 4:
        raise ValueError("The prospective allocation is exactly four reciprocal pairs")
    cases, used_people, cache = [], set(), {}
    for index, left in enumerate(profiles):
        if left["speaker"] in used_people:
            continue
        for right in profiles[index + 1:]:
            if right["speaker"] in used_people:
                continue
            selected = paired_windows(left, right, tokenizer, used_people, cache)
            if selected is None:
                continue
            own, donor, counts, members = selected
            pair_index = len(cases) // 2
            for side, (focal, other, source, mismatch) in enumerate(
                    ((left, right, own, donor), (right, left, donor, own))):
                cases.append({
                    "case_id": f"PAIR{pair_index:02d}SIDE{side}",
                    "pair_index": pair_index, "side": side, "speaker_index": len(cases),
                    "speaker_id": focal["speaker"], "donor_speaker_id": other["speaker"],
                    "target_dialogue_id": focal["target"]["dialogue_id"],
                    "target_partner_id": focal["target"]["partner"],
                    "target_start": focal["target"]["start"].isoformat(),
                    "source_dialogue_id": source["dialogue_id"],
                    "source_partner_id": source["partner"], "source_start_index": source["start_index"],
                    "source_end": source["end"].isoformat(), "source_history": source["turns"],
                    "correct_external_history": source_block(source["turns"], focal["speaker"]),
                    "donor_source_dialogue_id": mismatch["dialogue_id"],
                    "donor_source_partner_id": mismatch["partner"],
                    "donor_source_start_index": mismatch["start_index"],
                    "donor_source_end": mismatch["end"].isoformat(),
                    "donor_source_history": mismatch["turns"],
                    "mismatched_external_history": source_block(mismatch["turns"], other["speaker"]),
                    "source_block_tokens": counts[side], "donor_source_block_tokens": counts[1 - side],
                    "candidate_texts": [left["context"]["reference"]["text"], right["context"]["reference"]["text"]],
                    "candidate_source_speaker_ids": [left["speaker"], right["speaker"]],
                    "target_candidate_index": side, **focal["context"],
                })
            used_people.update(members)
            break
        if len(cases) == pair_count * 2:
            return cases, {"selected_speakers": len(cases), "reciprocal_pairs": pair_count,
                           "disjoint_participants_in_selected_material": len(used_people),
                           "maximum_observed_source_token_difference": max(
                               abs(c["source_block_tokens"] - c["donor_source_block_tokens"]) for c in cases),
                           "source_blocks_tokenized": len(cache)}
    raise ValueError(f"Only {len(cases) // 2}/4 feasible reciprocal pairs; no rule relaxation")


def options(case, order):
    if type(order) is not int or order not in (0, 1):
        raise ValueError("Option order must be zero or one")
    indices = (0, 1) if order == 0 else (1, 0)
    return {"A": case["candidate_texts"][indices[0]], "B": case["candidate_texts"][indices[1]]}, \
        "AB"[indices.index(case["target_candidate_index"])]


def trigram_jaccard(left, right):
    def grams(text):
        text = material._normalized(text)
        return {text[index:index + 3] for index in range(len(text) - 2)}
    a, b = grams(left), grams(right)
    return len(a & b) / len(a | b) if a | b else 0.0


def lexical_baseline(case, arm):
    if arm not in ARMS:
        raise ValueError("Unknown history arm")
    evidence = [turn["text"] for turn in case["history"]] + [case["query"]["text"]]
    if arm != "NONE":
        evidence += [turn["text"] for turn in case[
            "source_history" if arm == "CORRECT" else "donor_source_history"]]
    scores = [trigram_jaccard("\n".join(evidence), candidate) for candidate in case["candidate_texts"]]
    target = case["target_candidate_index"]
    return {"candidate_scores": scores, "accuracy": 0.5 if scores[0] == scores[1]
            else float(scores[target] > scores[1 - target])}


def build_cases(tokenizer, dataset_root=Path(".local/datasets/real-persona-chat")):
    source = material.verify_live_source(dataset_root)
    excluded_targets, historical_bindings = set(), {}
    for path, expected in OLD_MATERIALS:
        if material.digest_file(path) != expected:
            raise ValueError("Historical material integrity changed")
        historical_bindings[path.as_posix()] = expected
        excluded_targets.update(row["target_dialogue_id"] for row in json.loads(path.read_bytes())["cases"])
    dialogues, split_hash, excluded_headers = load_development_dialogues(dataset_root)
    cohort, cohort_hash = material._frozen_style_cohort(dialogues, split_hash)
    profiles = profiles_from_dialogues(dialogues, cohort, excluded_targets)
    cases, selection = select_cases(profiles, tokenizer)
    return cases, {"source": source, "split_assignment_sha256": split_hash,
                   "cohort_sha256": cohort_hash, "selection_seed": SELECTION,
                   "eligible_initial_profiles": len(profiles), **selection,
                   "excluded_historical_target_dialogues": len(excluded_targets),
                   "historical_material_bindings": historical_bindings,
                   "excluded_nondevelopment_headers": excluded_headers,
                   "reserved_validation_content_deserialized": False,
                   "persona_values_deserialized": False, "maximum_main_requests": 48,
                   "endpoint": "OBSERVED_CONTINUATION_RECOGNITION_NOT_SEMANTIC_QUALITY"}
