"""Materialize a private, development-only RealPersonaChat S/F/H pilot.

This controller performs no tokenization or inference.  Participant text and
identifiers are written only to an ignored private file; the public receipt
contains hashes and aggregate counts.
"""

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import real_persona_chat_intake as intake
import real_persona_chat_style_signal_v1 as style_signal


SCHEMA = "personaslm_rpc_sfh_pilot_v1"
SELECTION_SEED = "PersonaSLM-RPC-SFH-pilot-v1"
SPEAKER_COUNT = 8
MIN_SOURCE_TURNS = 20
HISTORY_TURNS = 6
STYLE_FEATURES = (
    "question_turn_rate",
    "exclamation_turn_rate",
    "ellipsis_turn_rate",
    "laughter_turn_rate",
    "polite_ending_rate",
)
STYLE_REGISTRATION = REPO / (
    "docs/validation/p1/real_persona_chat_style_signal_v1/registration_v1.json")
STYLE_ANALYSIS = REPO / (
    "docs/validation/p1/real_persona_chat_style_signal_v1/analysis_v1.json")
PROSPECTIVE_DESIGN = REPO / (
    "docs/validation/p1/real_persona_chat_sfh_pilot_v1/prospective_design_v1.json")
GOVERNANCE_AMENDMENT = REPO / (
    "docs/validation/p1/real_persona_chat_sfh_pilot_v1/data_governance_amendment_v1.json")
CONDITIONS = {
    "C0": (0, 0, 0),
    "C1": (1, 0, 0),
    "C2": (0, 1, 0),
    "C3": (1, 1, 0),
    "C4": (0, 0, 1),
    "C5": (1, 0, 1),
    "C6": (0, 1, 1),
    "C7": (1, 1, 1),
}
BLOCK_MASKS = {"B1": (0, 3, 5, 6), "B2": (1, 2, 4, 7)}
TOP_LEVEL_ID = re.compile(r'^    ("(?:\\.|[^"\\])+"): \{$')
UTTERANCES_FIELD = re.compile(r'^    "utterances": \[$')
MASK = re.compile(r"<[^>]+>|＊＊")
JAPANESE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
HAN_RUN = re.compile(r"[\u3400-\u9fff々]+")
KATAKANA_RUN = re.compile(r"[\u30a0-\u30ffー]+")
LATIN_DIGIT_RUN = re.compile(r"[A-Za-z0-9]+")


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest_file(path):
    return digest_bytes(Path(path).read_bytes())


def verify_live_source(dataset_root):
    """Verify release bytes without deserializing non-development utterances."""
    root = Path(dataset_root).resolve()
    paths = sorted((root / "real_persona_chat" / "dialogues").glob("*.json"))
    manifest = hashlib.sha256()
    for path in paths:
        file_hash = digest_file(path)
        manifest.update(path.name.encode("utf-8") + b"\0" +
                        file_hash.encode("ascii") + b"\n")
    observed = {
        "version": (root / "VERSION").read_text(encoding="utf-8").strip(),
        "revision": intake.revision(root),
        "license_sha256": digest_file(root / "LICENSE"),
        "readme_sha256": digest_file(root / "README.md"),
        "version_sha256": digest_file(root / "VERSION"),
        "interlocutors_sha256": digest_file(
            root / "real_persona_chat" / "interlocutors.json"),
        "dialogue_manifest_sha256": manifest.hexdigest(),
        "dialogues": len(paths),
    }
    expected = {key: intake.EXPECTED[key] for key in observed}
    if observed != expected:
        differences = {key: {"expected": expected[key], "observed": observed[key]}
                       for key in observed if observed[key] != expected[key]}
        raise ValueError(f"Pinned RealPersonaChat source changed: {differences}")
    receipt_path = REPO / (
        "docs/validation/p1/real_persona_chat_intake_v1/intake_receipt_v1.json")
    saved = json.loads(receipt_path.read_text(encoding="utf-8"))
    if saved.get("status") != "PASS" or any(
            saved.get("source", {}).get(key) != value
            for key, value in observed.items()):
        raise ValueError("Saved intake receipt does not bind the live source")
    return observed


def private_output_path(path):
    resolved = Path(path).resolve()
    private_root = (REPO / ".local").resolve()
    if resolved == private_root or private_root not in resolved.parents:
        raise ValueError("Private participant material must remain below REPO/.local")
    return resolved


def _speaker_ids(path):
    """Read only top-level keys; persona values are neither parsed nor kept."""
    found = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            match = TOP_LEVEL_ID.match(line.rstrip("\r\n"))
            if match:
                found.append(json.loads(match.group(1)))
    if len(found) != len(set(found)) or not found:
        raise ValueError("Could not recover unique top-level speaker IDs")
    return found


def _development_people(path, development_ids):
    """Decode only development records from the monolithic persona JSON."""
    selected = {}
    current_id = None
    current_lines = None

    def finish():
        if current_id is None or current_lines is None:
            return
        body = "".join(current_lines).rstrip()
        if body.endswith(","):
            body = body[:-1]
        value = json.loads("{" + body + "}")[current_id]
        selected[current_id] = {
            "interlocutor_id": value["interlocutor_id"],
            "persona": value["persona"],
        }

    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            match = TOP_LEVEL_ID.match(line.rstrip("\r\n"))
            if match:
                finish()
                current_id = json.loads(match.group(1))
                current_lines = [line.lstrip()] if current_id in development_ids else None
            elif line.rstrip("\r\n") == "}":
                finish()
                current_id = None
                current_lines = None
            elif current_lines is not None:
                current_lines.append(line)
    finish()
    if set(selected) != set(development_ids):
        raise ValueError("Development-only persona extraction was incomplete")
    if any(set(value) != {"interlocutor_id", "persona"}
           for value in selected.values()):
        raise ValueError("Excluded participant fields entered the development view")
    return selected


def _dialogue_participants(path):
    """Read a dialogue header and stop before its first utterance."""
    prefix = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if UTTERANCES_FIELD.match(line.rstrip("\r\n")):
                break
            prefix.append(line)
        else:
            raise ValueError(f"Missing utterances field in {Path(path).name}")
    body = "".join(prefix).rstrip()
    if body.endswith(","):
        body = body[:-1]
    header = json.loads(body + "\n}")
    participants = header.get("interlocutors")
    if not isinstance(participants, list) or len(participants) != 2:
        raise ValueError(f"Invalid participant header in {Path(path).name}")
    return participants


def load_development_view(dataset_root):
    root = Path(dataset_root).resolve() / "real_persona_chat"
    people_path = root / "interlocutors.json"
    speaker_ids = _speaker_ids(people_path)
    assignments, assignment_hash = intake.speaker_split(
        {speaker: None for speaker in speaker_ids})
    development_ids = {speaker for speaker, split in assignments.items()
                       if split == "DEVELOPMENT"}
    people = _development_people(people_path, development_ids)
    dialogues = []
    excluded_headers = 0
    for path in sorted((root / "dialogues").glob("*.json")):
        participants = _dialogue_participants(path)
        if not all(speaker in development_ids for speaker in participants):
            excluded_headers += 1
            continue
        value = json.loads(path.read_bytes())
        if value["interlocutors"] != participants:
            raise ValueError("Dialogue header changed during development load")
        dialogues.append(value)
    return people, dialogues, assignment_hash, excluded_headers


def _timestamp(value):
    if not isinstance(value, str) or not value or value == "NaT":
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _dialogue_record(dialogue, speaker):
    turns = dialogue.get("utterances")
    if not isinstance(turns, list) or not turns:
        return None
    times = [_timestamp(turn.get("timestamp")) for turn in turns]
    if any(value is None for value in times):
        return None
    if any(left > right for left, right in zip(times, times[1:])):
        return None
    left, right = dialogue["interlocutors"]
    if speaker not in (left, right):
        return None
    partner = right if speaker == left else left
    return {
        "dialogue_id": dialogue["dialogue_id"],
        "partner": partner,
        "start": times[0],
        "end": times[-1],
        "turns": turns,
        "speaker_turns": [turn["text"] for turn in turns
                          if turn["interlocutor_id"] == speaker],
    }


def _normalized(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text).casefold())


def _content_tokens(text):
    tokens = set()
    for run in HAN_RUN.findall(text):
        tokens.update(run[index:index + 2] for index in range(len(run) - 1))
    for run in KATAKANA_RUN.findall(text):
        tokens.update(run[index:index + 3] for index in range(len(run) - 2))
    for run in LATIN_DIGIT_RUN.findall(text.casefold()):
        if len(run) >= 3:
            tokens.add(run)
    return tokens


def _longest_common_substring(left, right):
    if not left or not right:
        return 0
    previous = [0] * (len(right) + 1)
    best = 0
    for a in left:
        current = [0]
        for index, b in enumerate(right, start=1):
            value = previous[index - 1] + 1 if a == b else 0
            current.append(value)
            best = max(best, value)
        previous = current
    return best


def _no_answer_leak(reference, values, facts=()):
    reference = _normalized(reference)
    if len(reference) < 8:
        return False
    for value in values:
        value = _normalized(value)
        if not value:
            continue
        if reference in value or (len(value) >= 8 and value in reference):
            return False
        if _longest_common_substring(reference, value) / len(reference) >= 0.80:
            return False
    reference_tokens = _content_tokens(reference)
    for fact in facts:
        normalized_fact = _normalized(fact)
        if _longest_common_substring(reference, normalized_fact) >= 4:
            return False
        if reference_tokens & _content_tokens(normalized_fact):
            return False
    return True


def _target_turn(record, speaker, facts):
    turns = record["turns"]
    for index in range(HISTORY_TURNS + 1, len(turns)):
        response = turns[index]
        query = turns[index - 1]
        if response["interlocutor_id"] != speaker:
            continue
        if query["interlocutor_id"] == speaker:
            continue
        history = turns[index - HISTORY_TURNS - 1:index - 1]
        if len(history) != HISTORY_TURNS:
            continue
        if not any(turn["interlocutor_id"] == speaker for turn in history):
            continue
        texts = [turn["text"] for turn in history] + [query["text"]]
        reference = response["text"]
        if any(MASK.search(value) for value in texts + [reference]):
            continue
        if not (4 <= len(query["text"]) <= 240 and
                8 <= len(reference) <= 240):
            continue
        if not JAPANESE.search(query["text"]) or not JAPANESE.search(reference):
            continue
        if not _no_answer_leak(reference, texts, facts):
            continue
        return {
            "history": history,
            "query": query,
            "reference": response,
        }
    return None


def _profile_for_speaker(speaker, facts, records):
    ordered = sorted(records, key=lambda row: (
        row["start"], row["end"], str(row["dialogue_id"])))
    for target in reversed(ordered):
        target_turn = _target_turn(target, speaker, facts)
        if target_turn is None:
            continue
        sources = []
        source_partners = set()
        for row in ordered:
            if row["end"] >= target["start"]:
                continue
            if row["partner"] == target["partner"] or row["partner"] in source_partners:
                continue
            if not row["speaker_turns"]:
                continue
            sources.append(row)
            source_partners.add(row["partner"])
            if len(sources) == 2:
                break
        if len(sources) != 2:
            continue
        if sum(len(row["speaker_turns"]) for row in sources) < MIN_SOURCE_TURNS:
            continue
        return {"speaker": speaker, "facts": facts, "sources": sources,
                "target": target, **target_turn}
    return None


def _style_profile(profile):
    rows = [{"turns": row["speaker_turns"]} for row in profile["sources"]]
    features = style_signal.style_vector(rows)
    mean_chars = features["mean_turn_length"] * 50.0
    sd_chars = features["sd_turn_length"] * 50.0
    sentences = [
        f"一発話の長さは平均約{mean_chars:.1f}文字で、標準偏差は約{sd_chars:.1f}文字。",
        f"疑問符を含む発話は約{features['question_turn_rate'] * 100:.1f}%。",
        f"感嘆符を含む発話は約{features['exclamation_turn_rate'] * 100:.1f}%。",
        f"省略表現を含む発話は約{features['ellipsis_turn_rate'] * 100:.1f}%。",
        f"笑い表現を含む発話は約{features['laughter_turn_rate'] * 100:.1f}%。",
        f"丁寧語で終わる発話は約{features['polite_ending_rate'] * 100:.1f}%。",
    ]
    stored = {
        "mean_turn_length_characters": mean_chars,
        "sd_turn_length_characters": sd_chars,
        **{key: features[key] for key in STYLE_FEATURES},
    }
    return "\n".join(sentences), stored


def _history_text(profile):
    lines = []
    for turn in profile["history"]:
        role = "匿名話者" if turn["interlocutor_id"] == profile["speaker"] else "相手"
        lines.append(f"{role}: {turn['text']}")
    return "\n".join(lines)


def _messages(profile, bits, style_text):
    style_on, facts_on, history_on = bits
    facts = "\n".join(f"- {value}" for value in profile["facts"]) if facts_on else ""
    history = _history_text(profile) if history_on else ""
    user = (
        "次の匿名プロフィールと会話を参考に、最後の相手の発話に続く自然な返答を一つ生成してください。\n"
        "参考情報がある欄だけを利用し、個人情報を推測で補わないでください。\n\n"
        "[話し方]\n" + (style_text if style_on else "") + "\n\n"
        "[人物情報]\n" + facts + "\n\n"
        "[過去の会話]\n" + history + "\n\n"
        "[相手の発話]\n" + profile["query"]["text"])
    return [
        {"role": "system", "content": (
            "あなたは匿名化された研究用対話の応答を生成します。特定の実在人物を名乗ったり"
            "特定しようとせず、説明やラベルを付けずに自然な日本語の返答だけを書いてください。")},
        {"role": "user", "content": user},
    ]


def condition_schedule(mask):
    if mask not in range(8):
        raise ValueError("Latin mask must be in 0..7")
    return [f"C{position ^ mask}" for position in range(8)]


def _frozen_style_cohort(dialogues, assignment_hash):
    registration = json.loads(STYLE_REGISTRATION.read_text(encoding="utf-8"))
    if registration["split_assignment_sha256"] != assignment_hash:
        raise ValueError("Style-signal cohort uses a different speaker split")
    records = defaultdict(list)
    for dialogue in dialogues:
        left, right = dialogue["interlocutors"]
        for speaker, partner in ((left, right), (right, left)):
            records[speaker].append({
                "dialogue_id": dialogue["dialogue_id"],
                "partner": partner,
                "key": style_signal._dialogue_key(dialogue),
                "turns": [turn["text"] for turn in dialogue["utterances"]
                          if turn["interlocutor_id"] == speaker],
            })
    cohort = style_signal.eligible_profiles(style_signal.select_profiles(records))
    binding = canonical(sorted(
        (speaker,
         [row["dialogue_id"] for row in value["source"]],
         [row["dialogue_id"] for row in value["target"]])
        for speaker, value in cohort.items()))
    observed = digest_bytes(binding)
    if (len(cohort) != registration["eligible_speaker_count"] or
            observed != registration["cohort_and_dialogue_assignment_sha256"]):
        raise ValueError("Frozen 76-speaker style-signal cohort did not reproduce")
    return set(cohort), observed


def build_material(dataset_root):
    live_source = verify_live_source(dataset_root)
    people, dialogues, assignment_hash, excluded_headers = load_development_view(
        dataset_root)
    by_speaker = defaultdict(list)
    for dialogue in dialogues:
        for speaker in dialogue["interlocutors"]:
            record = _dialogue_record(dialogue, speaker)
            if record is not None:
                by_speaker[speaker].append(record)

    style_cohort, style_cohort_hash = _frozen_style_cohort(
        dialogues, assignment_hash)

    eligible = []
    for speaker in style_cohort:
        person = people[speaker]
        facts = person["persona"]
        if len(facts) != 10 or any(not isinstance(value, str) or not value.strip()
                                   or MASK.search(value) for value in facts):
            continue
        profile = _profile_for_speaker(speaker, facts, by_speaker[speaker])
        if profile is not None:
            eligible.append(profile)
    eligible.sort(key=lambda value: digest_bytes(
        f"{SELECTION_SEED}\0{value['speaker']}".encode("utf-8")))
    selected = eligible[:SPEAKER_COUNT]
    if len(selected) != SPEAKER_COUNT:
        raise ValueError(f"Needed {SPEAKER_COUNT} eligible speakers; found {len(selected)}")

    cases = []
    for index, profile in enumerate(selected):
        style_text, style_features = _style_profile(profile)
        case_id = f"RPCDEV{index + 1:02d}"
        cases.append({
            "case_id": case_id,
            "speaker_id": profile["speaker"],
            "source_dialogue_ids": [row["dialogue_id"] for row in profile["sources"]],
            "source_partner_ids": [row["partner"] for row in profile["sources"]],
            "source_period": [min(row["start"] for row in profile["sources"]).isoformat(),
                              max(row["end"] for row in profile["sources"]).isoformat()],
            "target_dialogue_id": profile["target"]["dialogue_id"],
            "target_partner_id": profile["target"]["partner"],
            "target_period": [profile["target"]["start"].isoformat(),
                              profile["target"]["end"].isoformat()],
            "style_source_turn_count": sum(
                len(row["speaker_turns"]) for row in profile["sources"]),
            "style_profile": style_text,
            "style_features": style_features,
            "facts": profile["facts"],
            "history": profile["history"],
            "query": profile["query"],
            "reference": profile["reference"],
        })

    requests = []
    case_lookup = {case["case_id"]: case for case in cases}
    profile_lookup = {f"RPCDEV{i + 1:02d}": profile
                      for i, profile in enumerate(selected)}
    request_index = 0
    case_ids = sorted(case_lookup)
    for block_index, block_cases in enumerate((case_ids[:4], case_ids[4:]), start=1):
        block = f"B{block_index}"
        for case_id, latin_mask in zip(block_cases, BLOCK_MASKS[block]):
            for position, condition in enumerate(condition_schedule(latin_mask)):
                bits = CONDITIONS[condition]
                case = case_lookup[case_id]
                profile = profile_lookup[case_id]
                messages = _messages(profile, bits, case["style_profile"])
                requests.append({
                    "request_id": f"RPCSFH{request_index:03d}",
                    "block": block,
                    "latin_mask": latin_mask,
                    "within_case_position": position,
                    "case_id": case_id,
                    "condition": condition,
                    "S": bits[0], "F": bits[1], "H": bits[2],
                    "messages": messages,
                    "prompt_sha256": digest_bytes(canonical(messages)),
                    "reference_sha256": digest_bytes(
                        profile["reference"]["text"].encode("utf-8")),
                })
                request_index += 1

    binding = [{
        "speaker": case["speaker_id"],
        "source": case["source_dialogue_ids"],
        "target": case["target_dialogue_id"],
        "reference": next(request["reference_sha256"] for request in requests
                          if request["case_id"] == case["case_id"]),
    } for case in cases]
    return {
        "schema_version": SCHEMA,
        "status": "PRIVATE_MATERIALS_FROZEN_NO_INFERENCE",
        "scientific_level": "DEVELOPMENT_EXPLORATORY",
        "dataset_root": str(Path(dataset_root).resolve()),
        "live_source": live_source,
        "split_assignment_sha256": assignment_hash,
        "selection_seed": SELECTION_SEED,
        "eligible_speaker_count": len(eligible),
        "excluded_nondevelopment_dialogue_headers": excluded_headers,
        "frozen_style_cohort_sha256": style_cohort_hash,
        "frozen_style_cohort_count": len(style_cohort),
        "selection_binding_sha256": digest_bytes(canonical(binding)),
        "conditions": {key: {"S": value[0], "F": value[1], "H": value[2]}
                       for key, value in CONDITIONS.items()},
        "cases": cases,
        "requests": requests,
        "privacy": "IGNORED_LOCAL_ONLY_DO_NOT_PUBLISH_OR_STAGE",
    }


def public_receipt(material, private_path, dataset_root):
    intake_receipt = REPO / "docs/validation/p1/real_persona_chat_intake_v1/intake_receipt_v1.json"
    live_source = verify_live_source(dataset_root)
    if live_source != material["live_source"]:
        raise ValueError("Dataset source changed after private materialization")
    request_hashes = [{"request_id": value["request_id"],
                       "block": value["block"],
                       "latin_mask": value["latin_mask"],
                       "within_case_position": value["within_case_position"],
                       "condition": value["condition"],
                       "prompt_sha256": value["prompt_sha256"],
                       "reference_sha256": value["reference_sha256"]}
                      for value in material["requests"]]
    case_hashes = []
    for case in material["cases"]:
        case_hashes.append({
            "case_id": case["case_id"],
            "private_case_sha256": digest_bytes(canonical(case)),
            "style_source_turn_count": case["style_source_turn_count"],
        })
    return {
        "schema_version": f"{SCHEMA}_materialization_receipt",
        "status": "MATERIALS_FROZEN_MODEL_AND_EXECUTION_NOT_REGISTERED",
        "scientific_level": "DEVELOPMENT_EXPLORATORY",
        "private_material_sha256": digest_file(private_path),
        "source_bindings": {
            "controller_sha256": digest_file(Path(__file__)),
            "intake_receipt_sha256": digest_file(intake_receipt),
            "style_registration_sha256": digest_file(STYLE_REGISTRATION),
            "style_analysis_sha256": digest_file(STYLE_ANALYSIS),
            "prospective_design_sha256": digest_file(PROSPECTIVE_DESIGN),
            "governance_amendment_sha256": digest_file(GOVERNANCE_AMENDMENT),
            "style_cohort_and_dialogue_assignment_sha256":
                material["frozen_style_cohort_sha256"],
            "dataset_revision": live_source["revision"],
            "dataset_version": live_source["version"],
            "dataset_version_sha256": live_source["version_sha256"],
            "dataset_license_sha256": live_source["license_sha256"],
            "dataset_readme_sha256": live_source["readme_sha256"],
            "dataset_dialogue_count": live_source["dialogues"],
            "dialogue_manifest_sha256": live_source["dialogue_manifest_sha256"],
            "interlocutors_sha256": live_source["interlocutors_sha256"],
            "split_assignment_sha256": material["split_assignment_sha256"],
        },
        "allocation": {
            "speakers": len(material["cases"]),
            "contexts_per_speaker": 1,
            "conditions_per_context": len(CONDITIONS),
            "requests": len(material["requests"]),
            "blocks": {
                "B1": {"allocation": "4 speakers x all 8 conditions = 32 requests",
                       "xor_latin_masks": list(BLOCK_MASKS["B1"])},
                "B2": {"allocation": "remaining 4 speakers x all 8 conditions = 32 requests",
                       "xor_latin_masks": list(BLOCK_MASKS["B2"])},
            },
            "within_block_order": "case_id ascending; within case, position p=0..7 uses condition index p XOR its fixed mask",
            "outcome_contingent_stopping": False,
        },
        "factor_definition": {
            "S": "numeric surface/stylometric profile from two earlier, distinct-partner dialogues",
            "F": "ten participant-authored persona statements of unknown temporal truth; not temporally verified facts; no demographics/personality/chat-experience",
            "H": f"{HISTORY_TURNS} real turns before the fixed current partner query in the target dialogue",
        },
        "chronology": {
            "all_selected_timestamps": "PARSEABLE_NONDECREASING",
            "style_source_end_strictly_before_target_start": True,
            "NaT_allowed": False,
            "reference_after_history_and_query": True,
        },
        "separation": {
            "reference_in_prompt": False,
            "exact_or_80pct_contiguous_reference_leakage": 0,
            "fact_reference_four_character_or_content_token_overlap": 0,
            "style_contains_raw_dialogue_text": False,
            "target_dialogue_used_for_style": False,
            "source_and_target_partners_distinct": True,
            "nondevelopment_utterances_deserialized": False,
            "all_speaker_ids_and_dialogue_participant_headers_scanned_for_split_enforcement": True,
            "nondevelopment_persona_values_deserialized_or_retained": False,
        },
        "case_hashes": case_hashes,
        "request_hashes": request_hashes,
        "selection_binding_sha256": material["selection_binding_sha256"],
        "privacy": {
            "participant_text_in_receipt": False,
            "speaker_ids_in_receipt": False,
            "row_level_public_generations": False,
            "private_material_location": "IGNORED_LOCAL_ONLY",
        },
        "execution": {
            "model": "PENDING_SEPARATE_PROSPECTIVE_EXECUTION_AMENDMENT",
            "tokenization": "NOT_RUN",
            "preflight": "NOT_RUN",
            "server_launches": 0,
            "generations": 0,
        },
        "claim_boundary": (
            "Materials support a paired developmental model pilot only. H naturally carries surface and "
            "content cues, so factorial effects are incremental conditioning-package effects, not pure "
            "orthogonal psychological constructs. Automatic style and reference metrics remain proxies; "
            "semantic Persona Fidelity, factual consistency, and history consistency require blinded human review."),
        "dataset_root_recorded_privately": str(Path(dataset_root).resolve()) == material["dataset_root"],
    }


def write_exclusive(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(canonical(value))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--private-output", required=True, type=Path)
    parser.add_argument("--public-output", required=True, type=Path)
    args = parser.parse_args(argv)
    private_path = private_output_path(args.private_output)
    public_path = args.public_output.resolve()
    if private_path.exists() or public_path.exists():
        raise FileExistsError("Refusing to overwrite frozen pilot material")
    material = build_material(args.dataset_root)
    write_exclusive(private_path, material)
    try:
        receipt = public_receipt(material, private_path, args.dataset_root)
        write_exclusive(public_path, receipt)
    except Exception:
        private_path.unlink(missing_ok=True)
        raise
    print(json.dumps({
        "status": receipt["status"],
        "speakers": receipt["allocation"]["speakers"],
        "requests": receipt["allocation"]["requests"],
        "private_material_sha256": receipt["private_material_sha256"],
        "public_output": str(public_path),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
