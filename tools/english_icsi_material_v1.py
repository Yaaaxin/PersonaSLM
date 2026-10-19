"""Local-only ICSI material qualification; reserved transcript bodies stay unread."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from icsi_english_qualification_v1 import ARCHIVE_SHA256, read_header


DATA = Path(".local/datasets/icsi_english_v1/ICSI_original_transcripts.zip")
PRIVATE = Path(".local/experiments/english_sfh_v1")
SPLIT = PRIVATE / "icsi_metadata_split_v1.json"
PUBLIC = Path("docs/validation/p1/english_real_speaker_stage_v1")
WORDS = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
SENSITIVE = re.compile(r"\b(?:wife|husband|mother|father|daughter|son|children|family|married|divorce|sex|sexual|gender|religion|church|politic\w*|salary|income|password|secret|address|email|phone|cancer|diabet\w*|illness|sick|disease|medical|hospital|suicide|depress\w*|drunk|drug\w*|race|ethnic\w*)\b", re.I)
SAFE_CAPITAL = {"I", "I'm", "I've", "I'd", "I'll", "OK", "Okay", "Yeah", "Yes", "No", "Well", "Um", "Uh", "So", "Right", "Actually", "Basically", "And", "But", "Now", "Also", "The", "A", "An", "We", "We're", "That's", "That", "This", "It's", "It", "You", "If", "What", "How", "Is", "Are", "Do", "Did", "Can", "Could", "Would", "Should", "For", "In", "On", "At", "To", "There", "Then", "Maybe", "Because", "Or", "Not", "Just", "As", "All", "They", "He", "She"}
PROFESSIONAL = re.compile(r"\b(?:code|coding|program\w*|implement\w*|transcri\w*|record\w*|microphone\w*|corpus|corpora|data|database|model\w*|recogn\w*|speech|experiment\w*|software|system\w*|algorithm\w*|script\w*|server\w*|annotation\w*|file\w*|tool\w*|interface\w*|paper|project|test\w*|train\w*)\b", re.I)
SELFREPORT = re.compile(r"\bI (?:have |had |recently |already |just |actually )?(?:wrote|write|built|build|implemented|implement|tested|test|tried|try|use|used|worked|work|recorded|record|ran|run|developed|develop|annotated|annotate|transcribed|transcribe|prefer|finished|finish|started|start)\b|\bI(?:'m| am|'ve been| have been) (?:working|using|developing|implementing|testing|recording|transcribing|writing)\b")
HYPOTHETICAL = re.compile(r"\b(?:if|would|could|might|maybe|suppose|pretend|hypothetical)\b", re.I)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def metadata_split(records):
    development = [r for r in records if r["group"] == "Bmr"]
    development_people = set().union(*(r["participants"] for r in development))
    reserved = [r for r in records if r["group"] == "Bed" and r["participants"].isdisjoint(development_people)]
    reserved_people = set().union(*(r["participants"] for r in reserved))
    assert development_people.isdisjoint(reserved_people)
    def compact(rows):
        return [{"meeting": r["meeting"], "date": r["date"].isoformat(), "participants": sorted(r["participants"])}
                for r in sorted(rows, key=lambda r: (r["date"], r["meeting"]))]
    return {"development": compact(development), "reserved": compact(reserved),
            "development_speakers": sorted(development_people), "reserved_speakers": sorted(reserved_people),
            "excluded_meetings": sorted(r["meeting"] for r in records if r not in development and r not in reserved)}


def freeze_split():
    if digest(DATA) != ARCHIVE_SHA256:
        raise ValueError("Wrong archive")
    records = []
    with zipfile.ZipFile(DATA) as archive:
        for name in archive.namelist():
            if re.fullmatch(r"transcripts/B[a-z]{2}\d{3}\.mrt", name):
                with archive.open(name) as stream:
                    records.append(read_header(stream))
    split = metadata_split(records)
    split.update({"schema": "icsi_metadata_split_v1", "created_utc": datetime.now(timezone.utc).isoformat(),
                  "archive_sha256": ARCHIVE_SHA256, "source_sha256": digest(__file__),
                  "selection": "All Bmr development; Bed excluding any Bmr participant reserved; metadata-only",
                  "reserved_transcript_body_bytes_deserialized": 0,
                  "scope": "Prospective corpus split, not an experiment or inference authorization"})
    write_new(SPLIT, split)
    receipt = {"schema": "icsi_metadata_split_receipt_v1", "created_utc": split["created_utc"],
               "private_split_sha256": digest(SPLIT), "archive_sha256": ARCHIVE_SHA256,
               "development_meetings": len(split["development"]), "development_participants": len(split["development_speakers"]),
               "reserved_meetings": len(split["reserved"]), "reserved_participants": len(split["reserved_speakers"]),
               "participant_intersection": 0, "reserved_transcript_body_bytes_deserialized": 0,
               "source_sha256": digest(__file__), "group_topic_shift_is_a_limit": True}
    write_new(PUBLIC / "icsi_metadata_split_receipt_v1.json", receipt)
    return receipt


def clean_text(segment):
    if segment.find(".//Foreign") is not None or segment.find(".//Uncertain") is not None:
        return None
    text = re.sub(r"\s+", " ", "".join(segment.itertext())).strip()
    text = text.replace("’", "'")
    if not text or SENSITIVE.search(text) or re.search(r"https?://|www\.|@|\d{4,}", text):
        return None
    words = WORDS.findall(text)
    if not words or any(w[0].isupper() and w not in SAFE_CAPITAL for w in words):
        return None
    return text


def parse_development_meeting(raw, meeting, allowed_people):
    root = ET.fromstring(re.sub(br"<!DOCTYPE[^>]*>", b"", raw))
    if root.attrib["Session"] != meeting:
        raise ValueError("Meeting identity mismatch")
    turns, exclusions = [], Counter()
    for index, segment in enumerate(root.findall("./Transcript/Segment")):
        person = segment.get("Participant", "")
        if person not in allowed_people or segment.get("DigitTask", "false").lower() == "true":
            exclusions["non_single_human_or_digit_task"] += 1
            continue
        text = clean_text(segment)
        if text is None:
            exclusions["privacy_language_or_transcription_filter"] += 1
            continue
        start, end = float(segment.attrib["StartTime"]), float(segment.attrib["EndTime"])
        if not all(math.isfinite(t) for t in (start, end)) or start < 0 or end < start:
            raise ValueError("Invalid transcript timing")
        turns.append({"speaker": person, "start": start, "end": end, "text": text,
                      "source_segment_ids": [index]})
    turns.sort(key=lambda t: (t["start"], t["end"], t["source_segment_ids"]))
    merged = []
    for turn in turns:
        if (merged and merged[-1]["speaker"] == turn["speaker"] and
                0 <= turn["start"] - merged[-1]["end"] <= 1 and
                turn["source_segment_ids"][0] == merged[-1]["source_segment_ids"][-1] + 1):
            merged[-1]["text"] += " " + turn["text"]
            merged[-1]["end"] = turn["end"]
            merged[-1]["source_segment_ids"] += turn["source_segment_ids"]
        else:
            merged.append(dict(turn))
    return merged, dict(exclusions)


def natural_window(turns, start, length):
    window = turns[start:start + length]
    return (len(window) == length and len({t["speaker"] for t in window}) >= 2 and
            all(a["end"] <= b["start"] and b["source_segment_ids"][0] == a["source_segment_ids"][-1] + 1
                for a, b in zip(window, window[1:])) and
            window[-1]["end"] - window[0]["start"] <= 180)


def style_profile(turns, speaker, excluded_segments):
    source = [t for t in turns if t["speaker"] == speaker and not (set(t["source_segment_ids"]) & excluded_segments)]
    words = [word.lower() for t in source for word in WORDS.findall(t["text"])]
    if len(words) < 100 or len(source) < 10:
        return None
    text = " ".join(t["text"].lower() for t in source)
    counts = {"contractions": sum("'" in word for word in words),
              "fillers": sum(word in {"um", "uh", "er", "erm", "hmm"} for word in words),
              "hedges": len(re.findall(r"\b(?:maybe|perhaps|probably|possibly|kind of|sort of|i think|i guess)\b", text))}
    return {"construct": "descriptive source-language rates, not a validated Persona Fidelity score",
            "words": len(words), "turns": len(source), "per_100_words": {k: 100 * v / len(words) for k, v in counts.items()},
            "questions_per_100_turns": 100 * sum("?" in t["text"] for t in source) / len(source),
            "source_segment_ids": [i for t in source for i in t["source_segment_ids"]]}


def material_candidates(split, parsed):
    by_speaker = defaultdict(list)
    for meeting in split["development"]:
        for speaker in meeting["participants"]:
            by_speaker[speaker].append(meeting)
    labels = {p: f"D{index:03}" for index, p in enumerate(sorted(split["development_speakers"]), 1)}
    cases, reasons, speaker_material = [], Counter(), []
    def labelled(turn):
        return dict(turn, speaker=labels[turn["speaker"]])
    for speaker, meetings in sorted(by_speaker.items()):
        meetings.sort(key=lambda m: (m["date"], m["meeting"]))
        if len({m["date"] for m in meetings}) < 3:
            reasons["fewer_than_three_dated_meetings"] += 1
            continue
        first, second = meetings[:2]
        earlier = parsed[first["meeting"]]
        facts = [t for t in earlier if t["speaker"] == speaker and 6 <= len(WORDS.findall(t["text"])) <= 60
                 and SELFREPORT.search(t["text"]) and PROFESSIONAL.search(t["text"])
                 and not HYPOTHETICAL.search(t["text"])] [:3]
        if not facts:
            reasons["no_screened_first_meeting_professional_selfreport"] += 1
            continue
        style = style_profile(earlier, speaker, {i for t in facts for i in t["source_segment_ids"]})
        if style is None:
            reasons["insufficient_separate_style_source"] += 1
            continue
        history_turns = parsed[second["meeting"]]
        history = next((history_turns[i:i + 6] for i in range(len(history_turns) - 5)
                        if natural_window(history_turns, i, 6) and sum(t["speaker"] == speaker for t in history_turns[i:i + 6]) >= 2
                        and 35 <= sum(len(WORDS.findall(t["text"])) for t in history_turns[i:i + 6]) <= 180), None)
        if history is None:
            reasons["no_contiguous_six_turn_second_meeting_history"] += 1
            continue
        selected, used = [], set()
        for target_meeting in meetings[2:]:
            if not first["date"] < second["date"] < target_meeting["date"]:
                continue
            turns = parsed[target_meeting["meeting"]]
            for index in range(6, len(turns)):
                target = turns[index]
                if target["speaker"] != speaker or not 15 <= len(WORDS.findall(target["text"])) <= 70:
                    continue
                if not natural_window(turns, index - 6, 7):
                    continue
                segment_keys = {(target_meeting["meeting"], sid) for t in turns[index - 6:index + 1] for sid in t["source_segment_ids"]}
                if segment_keys & used:
                    continue
                source_text = " ".join(t["text"] for t in facts + history + turns[index - 6:index])
                if target["text"].lower() in source_text.lower():
                    continue
                used.update(segment_keys)
                selected.append({"speaker": labels[speaker], "first_source_meeting": first["meeting"],
                                 "first_source_date": first["date"], "history_meeting": second["meeting"],
                                 "history_date": second["date"], "target_meeting": target_meeting["meeting"],
                                 "target_date": target_meeting["date"], "style": style,
                                 "facts_source_selfreports_not_world_verified": [labelled(t) for t in facts],
                                 "history": [labelled(t) for t in history],
                                 "context": [labelled(t) for t in turns[index - 6:index]],
                                 "reference_continuation_not_for_prompt": labelled(target)})
                if len(selected) == 2:
                    break
            if len(selected) == 2:
                break
        if len(selected) < 2:
            reasons["fewer_than_two_qualified_continuation_contexts"] += 1
        speaker_material.append({"speaker": labels[speaker], "candidate_contexts": len(selected)})
        cases.extend(selected)
    return cases, dict(reasons), speaker_material


def qualify_material(expected_split_sha256):
    if digest(SPLIT) != expected_split_sha256 or digest(DATA) != ARCHIVE_SHA256:
        raise ValueError("Frozen split/archive hash mismatch")
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    assert set(split["development_speakers"]).isdisjoint(split["reserved_speakers"])
    parsed, exclusions = {}, Counter()
    with zipfile.ZipFile(DATA) as archive:
        for meeting in split["development"]:
            if not meeting["meeting"].startswith("Bmr"):
                raise ValueError("Development-only body boundary violated")
            raw = archive.read(f"transcripts/{meeting['meeting']}.mrt")
            turns, rejected = parse_development_meeting(raw, meeting["meeting"], set(meeting["participants"]))
            parsed[meeting["meeting"]] = turns
            exclusions.update(rejected)
    cases, reasons, speakers = material_candidates(split, parsed)
    artifact = {"schema": "icsi_material_candidates_v1", "created_utc": datetime.now(timezone.utc).isoformat(),
                "archive_sha256": ARCHIVE_SHA256, "split_sha256": expected_split_sha256,
                "source_sha256": digest(__file__), "status": "SCREENED_CANDIDATES_NOT_SEMANTICALLY_VALIDATED_OR_PROMPT_FROZEN",
                "reserved_transcript_bodies_read": 0, "development_transcript_bodies_read": len(parsed),
                "cases": cases, "speaker_material": speakers, "speaker_exclusions": reasons,
                "segment_exclusions": dict(exclusions)}
    private_path = PRIVATE / "icsi_material_candidates_v1.json"
    write_new(private_path, artifact)
    report = {k: v for k, v in artifact.items() if k not in {"cases", "speaker_material"}}
    report.update({"private_material_sha256": digest(private_path), "candidate_contexts": len(cases),
                   "speakers_with_two_contexts": sum(s["candidate_contexts"] == 2 for s in speakers),
                   "speakers_with_one_context": sum(s["candidate_contexts"] == 1 for s in speakers),
                   "privacy_filter_is_not_a_guarantee": True, "new_model_generations": 0})
    write_new(PUBLIC / "icsi_material_qualification_v1.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze-split", action="store_true")
    mode.add_argument("--qualify-material", action="store_true")
    parser.add_argument("--expected-split-sha256")
    args = parser.parse_args()
    if args.qualify_material and not args.expected_split_sha256:
        parser.error("Explicit frozen split hash required before body access")
    print(json.dumps(freeze_split() if args.freeze_split else qualify_material(args.expected_split_sha256), indent=2, sort_keys=True))
