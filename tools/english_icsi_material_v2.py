"""Prospective v2 material screening, preserving v1 and the reserved corpus split."""
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

import english_icsi_material_v1 as prior


EXPECTED_SPLIT = "cf91921ef55874237d961f0b2c17b916d5122ccff0c08cf6e4a52ba74a30207e"
POLICY = prior.PRIVATE / "icsi_material_policy_v2.json"
NAME_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:'[a-z]+)?\b")


def source_hashes():
    return {name: prior.digest(Path("tools") / name) for name in
            ("english_icsi_material_v2.py", "english_icsi_material_v1.py", "icsi_english_qualification_v1.py")}


def freeze_policy():
    if prior.digest(prior.SPLIT) != EXPECTED_SPLIT:
        raise ValueError("Frozen split mismatch")
    policy = {
        "schema": "icsi_material_policy_v2", "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_hashes": source_hashes(), "split_sha256": EXPECTED_SPLIT,
        "predecessor_negative_sha256": prior.digest(prior.PRIVATE / "icsi_material_candidates_v1.json"),
        "rationale": "V1 zero yield is a restrictive heuristic result, not proof that ICSI has no usable facts. Ordinary capitalization is not reliable name detection; earliest usable prior sources need not be first meetings.",
        "rules": [
            "Bmr development bodies only; Bed reserved bodies remain unread; no model inference",
            "Retain sensitive/contact/foreign/uncertain exclusions; ordinary capitalization allowed; possible names flagged for private audit",
            "Explicit professional first-person self-reports only; reject hypothetical phrases; these are source claims, not world-verified facts",
            "Earliest qualifying source meeting with up to three self-reports and >=100 separate style words and >=10 style turns",
            "Earliest later usable history meeting; first contiguous 4-to-6-turn history with >=1 target turn and 30-to-180 words; prefer 6 then5 then4 at a given position",
            "Natural overlaps retained with timestamps; no removed segment gaps allowed",
            "Four contiguous preceding context turns plus actual15-to100-word target; all context turns must end by target onset",
            "Target meeting strictly later than source and history; at most two nonoverlapping context/reference windows per speaker",
            "Screen every metadata-eligible development speaker (at most12); do not freeze final model-study speaker allocation",
            "No target reference substring may appear in its facts/history/context; candidate raw text and names remain private",
        ],
        "source_privacy_audit_required_before_prompts": True,
        "semantic_review_not_performed": True,
    }
    prior.write_new(POLICY, policy)
    snapshot = prior.PRIVATE / "english_icsi_material_v2.policy_freeze.py"
    with snapshot.open("xb") as output:
        output.write(Path(__file__).read_bytes())
    receipt = {**policy, "private_policy_sha256": prior.digest(POLICY), "snapshot_sha256": prior.digest(snapshot)}
    prior.write_new(prior.PUBLIC / "icsi_material_policy_receipt_v2.json", receipt)
    return receipt


def screened_text(segment):
    if segment.find(".//Foreign") is not None or segment.find(".//Uncertain") is not None:
        return None
    text = re.sub(r"\s+", " ", "".join(segment.itertext())).strip().replace("’", "'")
    if not text or prior.SENSITIVE.search(text) or re.search(r"https?://|www\.|@|\d{4,}", text):
        return None
    if not prior.WORDS.findall(text):
        return None
    names = sorted(set(token for token in NAME_PATTERN.findall(text) if token not in prior.SAFE_CAPITAL))
    return text, names


def parse_meeting(raw, meeting, allowed_people):
    root = ET.fromstring(re.sub(br"<!DOCTYPE[^>]*>", b"", raw))
    if root.attrib["Session"] != meeting:
        raise ValueError("Meeting mismatch")
    turns, rejected = [], Counter()
    for index, segment in enumerate(root.findall("./Transcript/Segment")):
        person = segment.get("Participant", "")
        if person not in allowed_people or segment.get("DigitTask", "false").lower() == "true":
            rejected["non_single_human_or_digit_task"] += 1
            continue
        value = screened_text(segment)
        if value is None:
            rejected["sensitive_contact_foreign_uncertain_or_empty"] += 1
            continue
        start, end = float(segment.attrib["StartTime"]), float(segment.attrib["EndTime"])
        if not all(math.isfinite(t) for t in (start, end)) or start < 0 or end < start:
            raise ValueError("Invalid timing")
        turns.append({"speaker": person, "start": start, "end": end, "text": value[0],
                      "possible_name_tokens_for_private_audit": value[1], "source_segment_ids": [index]})
    turns.sort(key=lambda t: (t["start"], t["end"], t["source_segment_ids"]))
    merged = []
    for turn in turns:
        if (merged and merged[-1]["speaker"] == turn["speaker"] and
                0 <= turn["start"] - merged[-1]["end"] <= 1 and
                turn["source_segment_ids"][0] == merged[-1]["source_segment_ids"][-1] + 1):
            merged[-1]["text"] += " " + turn["text"]
            merged[-1]["end"] = turn["end"]
            merged[-1]["source_segment_ids"] += turn["source_segment_ids"]
            merged[-1]["possible_name_tokens_for_private_audit"] = sorted(set(merged[-1]["possible_name_tokens_for_private_audit"] + turn["possible_name_tokens_for_private_audit"]))
        else:
            merged.append(dict(turn))
    return merged, dict(rejected)


def contiguous(turns):
    return (len({t["speaker"] for t in turns}) >= 2 and
            all(a["start"] <= b["start"] and b["source_segment_ids"][0] == a["source_segment_ids"][-1] + 1
                for a, b in zip(turns, turns[1:])) and
            max(t["end"] for t in turns) - turns[0]["start"] <= 180)


def history_window(turns, speaker):
    for index in range(len(turns) - 3):
        for length in (6, 5, 4):
            window = turns[index:index + length]
            if len(window) != length or not contiguous(window) or not any(t["speaker"] == speaker for t in window):
                continue
            if 30 <= sum(len(prior.WORDS.findall(t["text"])) for t in window) <= 180:
                return window
    return None


def targets_for(speaker, meetings, parsed, source_text):
    selected, used = [], set()
    for meeting in meetings:
        turns = parsed[meeting["meeting"]]
        for index in range(4, len(turns)):
            target, context = turns[index], turns[index - 4:index]
            if target["speaker"] != speaker or not 15 <= len(prior.WORDS.findall(target["text"])) <= 100:
                continue
            if not contiguous(context + [target]) or any(t["end"] > target["start"] for t in context):
                continue
            keys = {(meeting["meeting"], sid) for t in context + [target] for sid in t["source_segment_ids"]}
            prompt_text = source_text + " " + " ".join(t["text"] for t in context)
            if keys & used or target["text"].lower() in prompt_text.lower():
                continue
            used |= keys
            selected.append((meeting, context, target))
            if len(selected) == 2:
                return selected
    return selected


def candidates(split, parsed):
    by_speaker = defaultdict(list)
    for meeting in split["development"]:
        for speaker in meeting["participants"]:
            by_speaker[speaker].append(meeting)
    labels = {p: f"D{i:03}" for i, p in enumerate(sorted(split["development_speakers"]), 1)}
    cases, reasons, per_speaker = [], Counter(), []
    def labelled(turn):
        return dict(turn, speaker=labels[turn["speaker"]])
    for speaker, meetings in sorted(by_speaker.items()):
        meetings.sort(key=lambda m: (m["date"], m["meeting"]))
        if len({m["date"] for m in meetings}) < 3:
            reasons["fewer_than_three_dated_meetings"] += 1
            continue
        chosen = None
        for source_index, source in enumerate(meetings[:-2]):
            own = parsed[source["meeting"]]
            facts = [t for t in own if t["speaker"] == speaker and 6 <= len(prior.WORDS.findall(t["text"])) <= 60
                     and prior.SELFREPORT.search(t["text"]) and prior.PROFESSIONAL.search(t["text"])
                     and not prior.HYPOTHETICAL.search(t["text"])] [:3]
            if not facts:
                continue
            style = prior.style_profile(own, speaker, {i for t in facts for i in t["source_segment_ids"]})
            if style is not None:
                chosen = (source_index, source, facts, style)
                break
        if chosen is None:
            reasons["no_prior_source_with_selfreport_and_separate_style"] += 1
            continue
        source_index, source, facts, style = chosen
        history_choice = None
        for history_index in range(source_index + 1, len(meetings) - 1):
            history_meeting = meetings[history_index]
            if source["date"] >= history_meeting["date"]:
                continue
            history = history_window(parsed[history_meeting["meeting"]], speaker)
            if history is not None:
                history_choice = (history_index, history_meeting, history)
                break
        if history_choice is None:
            reasons["no_later_pre_target_contiguous_history"] += 1
            continue
        history_index, history_meeting, history = history_choice
        future = [m for m in meetings[history_index + 1:] if m["date"] > history_meeting["date"]]
        targets = targets_for(speaker, future, parsed, " ".join(t["text"] for t in facts + history))
        if len(targets) < 2:
            reasons["fewer_than_two_qualified_continuation_contexts"] += 1
        per_speaker.append({"speaker": labels[speaker], "candidate_contexts": len(targets)})
        for meeting, context, target in targets:
            cases.append({"speaker": labels[speaker], "first_source_meeting": source["meeting"], "first_source_date": source["date"],
                          "history_meeting": history_meeting["meeting"], "history_date": history_meeting["date"],
                          "target_meeting": meeting["meeting"], "target_date": meeting["date"], "style": style,
                          "facts_source_selfreports_not_world_verified": [labelled(t) for t in facts],
                          "history": [labelled(t) for t in history], "context": [labelled(t) for t in context],
                          "reference_continuation_not_for_prompt": labelled(target)})
    return cases, dict(reasons), per_speaker


def qualify(expected_policy_sha256):
    if prior.digest(POLICY) != expected_policy_sha256 or prior.digest(prior.SPLIT) != EXPECTED_SPLIT:
        raise ValueError("Policy/split hash mismatch")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    if source_hashes() != policy["source_hashes"] or prior.digest(prior.DATA) != prior.ARCHIVE_SHA256:
        raise ValueError("Frozen source/archive changed")
    split = json.loads(prior.SPLIT.read_text(encoding="utf-8"))
    parsed, exclusions = {}, Counter()
    with zipfile.ZipFile(prior.DATA) as archive:
        for meeting in split["development"]:
            if not re.fullmatch(r"Bmr\d{3}", meeting["meeting"]):
                raise ValueError("Reserved body boundary violation")
            parsed[meeting["meeting"]], excluded = parse_meeting(archive.read(f"transcripts/{meeting['meeting']}.mrt"), meeting["meeting"], set(meeting["participants"]))
            exclusions.update(excluded)
    cases, reasons, per_speaker = candidates(split, parsed)
    artifact = {"schema": "icsi_material_candidates_v2", "created_utc": datetime.now(timezone.utc).isoformat(),
                "source_hashes": source_hashes(), "policy_sha256": expected_policy_sha256, "split_sha256": EXPECTED_SPLIT,
                "archive_sha256": prior.ARCHIVE_SHA256, "status": "SCREENED_CANDIDATES_PRIVATE_SOURCE_AUDIT_REQUIRED",
                "development_transcript_bodies_read": len(parsed), "reserved_transcript_bodies_read": 0,
                "cases": cases, "speaker_material": per_speaker, "speaker_exclusions": reasons,
                "segment_exclusions": dict(exclusions), "new_model_generations": 0}
    private_path = prior.PRIVATE / "icsi_material_candidates_v2.json"
    prior.write_new(private_path, artifact)
    report = {k: v for k, v in artifact.items() if k not in {"cases", "speaker_material"}}
    report.update({"private_material_sha256": prior.digest(private_path), "candidate_contexts": len(cases),
                   "speakers_with_two_contexts": sum(s["candidate_contexts"] == 2 for s in per_speaker),
                   "speakers_with_one_context": sum(s["candidate_contexts"] == 1 for s in per_speaker),
                   "private_case_records_with_possible_name_flags": sum(any(t.get("possible_name_tokens_for_private_audit") for t in c["facts_source_selfreports_not_world_verified"] + c["history"] + c["context"] + [c["reference_continuation_not_for_prompt"]]) for c in cases),
                   "privacy_filter_is_not_a_guarantee": True})
    prior.write_new(prior.PUBLIC / "icsi_material_qualification_v2.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze-policy", action="store_true")
    mode.add_argument("--qualify-material", action="store_true")
    parser.add_argument("--expected-policy-sha256")
    args = parser.parse_args()
    if args.qualify_material and not args.expected_policy_sha256:
        parser.error("Explicit frozen policy hash required")
    print(json.dumps(freeze_policy() if args.freeze_policy else qualify(args.expected_policy_sha256), indent=2, sort_keys=True))
