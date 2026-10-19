"""Final bounded source-curation pool; machine retrieval is not semantic approval."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import zipfile

import english_icsi_material_v1 as v1
import english_icsi_material_v2 as v2


POLICY = v1.PRIVATE / "icsi_source_curation_policy_v3.json"
EXTRA_SENSITIVE = re.compile(r"\b(?:kids?|baby|babies|grand\w*|boyfriend|girlfriend|parents?|brother|sister|school|pickup|pick up|drop off|carpool)\b", re.I)
CALIBRATION = re.compile(r"\b(?:your name|my name|say your|read the digits|digit strings?|testing one|test one two|introduc\w*|microphone test|mic test|sound check|soundcheck|what's the number|what is the number)\b", re.I)


def hashes():
    names = ("english_icsi_material_v3.py", "english_icsi_material_v2.py", "english_icsi_material_v1.py", "icsi_english_qualification_v1.py")
    return {name: v1.digest(Path("tools") / name) for name in names}


def freeze():
    if v1.digest(v1.SPLIT) != v2.EXPECTED_SPLIT:
        raise ValueError("Wrong split")
    policy = {"schema": "icsi_source_curation_policy_v3", "created_utc": datetime.now(timezone.utc).isoformat(),
              "source_hashes": hashes(), "split_sha256": v2.EXPECTED_SPLIT,
              "v2_candidate_artifact_sha256": v1.digest(v1.PRIVATE / "icsi_material_candidates_v2.json"),
              "rationale": "Root source inspection found incomplete factual propositions, calibration-like history, target-only backchannels, privacy material and inadequate local context in v2. Candidate count was not qualification. One final bounded pre-inference source-curation pass follows.",
              "rules": [
                  "Bmr bodies only; preserve all v1/v2 files; no reserved Bed body access or inference",
                  "Retain previous sensitive/contact/foreign/uncertain filters; add kids/family/transport expressions; flag possible names for source audit",
                  "Inspect at most two earliest complete source/history/context candidate groups per metadata-eligible speaker, at most12 speakers",
                  "Source self-report retrieval up to6 explicit professional first-person nonhypothetical candidate turns per source meeting; require separate100word10turn style source",
                  "Actual AI-assisted source curation must retain only complete supported propositions; no fabricated human ratings or inferred biography",
                  "History contiguous6to10turns,30to200words,target>=20words,at least one professional term; reject explicit intro/naming/digit calibration indicators; preserve overlaps/timestamps",
                  "Context exactly8 contiguous preceding turns with at most300words; actual target15to100words; all context finishes before target onset",
                  "Source<history<target dates; max2 nonoverlapping contexts per candidate group; no full target quote in any conditioning/context",
                  "Manually redact only names actually present, preserve original private quotations and redaction provenance; do not enrich identities",
                  "No final cohort or GO is asserted by this retrieval artifact; qualified selection requires a separate explicit source-curation record"
              ], "new_model_generations": 0}
    v1.write_new(POLICY, policy)
    snapshot = v1.PRIVATE / "english_icsi_material_v3.policy_freeze.py"
    with snapshot.open("xb") as output:
        output.write(Path(__file__).read_bytes())
    receipt = {**policy, "private_policy_sha256": v1.digest(POLICY), "source_snapshot_sha256": v1.digest(snapshot)}
    v1.write_new(v1.PUBLIC / "icsi_source_curation_policy_receipt_v3.json", receipt)
    return receipt


def screen(turn):
    return not EXTRA_SENSITIVE.search(turn["text"]) and not CALIBRATION.search(turn["text"])


def history(turns, speaker):
    for start in range(len(turns) - 5):
        for size in (10, 9, 8, 7, 6):
            window = turns[start:start + size]
            if len(window) != size or not v2.contiguous(window):
                continue
            words = sum(len(v1.WORDS.findall(t["text"])) for t in window)
            own = " ".join(t["text"] for t in window if t["speaker"] == speaker)
            if 30 <= words <= 200 and len(v1.WORDS.findall(own)) >= 20 and v1.PROFESSIONAL.search(own):
                return window
    return None


def targets(speaker, meetings, parsed, source_text):
    found, used = [], set()
    for meeting in meetings:
        turns = parsed[meeting["meeting"]]
        for index in range(8, len(turns)):
            target, context = turns[index], turns[index - 8:index]
            if target["speaker"] != speaker or not 15 <= len(v1.WORDS.findall(target["text"])) <= 100:
                continue
            if sum(len(v1.WORDS.findall(t["text"])) for t in context) > 300 or not v2.contiguous(context + [target]):
                continue
            if any(t["end"] > target["start"] for t in context):
                continue
            ids = {(meeting["meeting"], i) for t in context + [target] for i in t["source_segment_ids"]}
            if ids & used or target["text"].lower() in (source_text + " " + " ".join(t["text"] for t in context)).lower():
                continue
            used |= ids
            found.append((meeting, context, target))
            if len(found) == 2:
                return found
    return found


def pool(split, parsed):
    by_speaker = defaultdict(list)
    for meeting in split["development"]:
        for speaker in meeting["participants"]:
            by_speaker[speaker].append(meeting)
    labels = {p: f"D{i:03}" for i, p in enumerate(sorted(split["development_speakers"]), 1)}
    groups, failures = [], Counter()
    def labelled(turn):
        return dict(turn, speaker=labels[turn["speaker"]])
    for speaker, meetings in sorted(by_speaker.items()):
        meetings.sort(key=lambda m: (m["date"], m["meeting"]))
        if len({m["date"] for m in meetings}) < 3:
            failures["fewer_than_three_dated_meetings"] += 1
            continue
        selected = 0
        for source_index, source in enumerate(meetings[:-2]):
            first_turns = parsed[source["meeting"]]
            facts = [t for t in first_turns if t["speaker"] == speaker and 6 <= len(v1.WORDS.findall(t["text"])) <= 100
                     and v1.SELFREPORT.search(t["text"]) and v1.PROFESSIONAL.search(t["text"])
                     and not v1.HYPOTHETICAL.search(t["text"])] [:6]
            if not facts:
                continue
            style = v1.style_profile(first_turns, speaker, {i for t in facts for i in t["source_segment_ids"]})
            if style is None:
                continue
            for history_index in range(source_index + 1, len(meetings) - 1):
                middle = meetings[history_index]
                if source["date"] >= middle["date"]:
                    continue
                window = history(parsed[middle["meeting"]], speaker)
                if window is None:
                    continue
                later = [m for m in meetings[history_index + 1:] if middle["date"] < m["date"]]
                continuations = targets(speaker, later, parsed, " ".join(t["text"] for t in facts + window))
                if len(continuations) != 2:
                    continue
                selected += 1
                group = {"candidate_group_id": f"{labels[speaker]}-G{selected}", "speaker": labels[speaker],
                         "first_source_meeting": source["meeting"], "first_source_date": source["date"],
                         "history_meeting": middle["meeting"], "history_date": middle["date"], "style": style,
                         "facts_source_selfreports_not_world_verified": [labelled(t) for t in facts],
                         "history": [labelled(t) for t in window], "continuations": []}
                for meeting, context, target in continuations:
                    group["continuations"].append({"target_meeting": meeting["meeting"], "target_date": meeting["date"],
                                                  "context": [labelled(t) for t in context],
                                                  "reference_continuation_not_for_prompt": labelled(target)})
                groups.append(group)
                break
            if selected == 2:
                break
        if not selected:
            failures["no_complete_bounded_source_history_context_group"] += 1
    return groups, dict(failures)


def retrieve(expected_policy):
    if v1.digest(POLICY) != expected_policy or v1.digest(v1.SPLIT) != v2.EXPECTED_SPLIT:
        raise ValueError("Frozen policy/split mismatch")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    if hashes() != policy["source_hashes"] or v1.digest(v1.DATA) != v1.ARCHIVE_SHA256:
        raise ValueError("Frozen source/archive changed")
    split = json.loads(v1.SPLIT.read_text(encoding="utf-8"))
    parsed, exclusions = {}, Counter()
    with zipfile.ZipFile(v1.DATA) as archive:
        for meeting in split["development"]:
            if not re.fullmatch(r"Bmr\d{3}", meeting["meeting"]):
                raise ValueError("Reserved body access prevented")
            turns, rejected = v2.parse_meeting(archive.read(f"transcripts/{meeting['meeting']}.mrt"), meeting["meeting"], set(meeting["participants"]))
            exclusions.update(rejected)
            parsed[meeting["meeting"]] = [t for t in turns if screen(t)]
            exclusions["additional_sensitive_or_calibration"] += len(turns) - len(parsed[meeting["meeting"]])
    groups, failures = pool(split, parsed)
    artifact = {"schema": "icsi_source_curation_pool_v3", "created_utc": datetime.now(timezone.utc).isoformat(),
                "source_hashes": hashes(), "policy_sha256": expected_policy, "split_sha256": v2.EXPECTED_SPLIT,
                "archive_sha256": v1.ARCHIVE_SHA256, "status": "RETRIEVED_POOL_REQUIRES_ACTUAL_SOURCE_CURATION",
                "groups": groups, "speaker_exclusions": failures, "segment_exclusions": dict(exclusions),
                "reserved_transcript_bodies_read": 0, "development_transcript_bodies_read": len(parsed), "new_model_generations": 0}
    path = v1.PRIVATE / "icsi_source_curation_pool_v3.json"
    v1.write_new(path, artifact)
    report = {k: v for k, v in artifact.items() if k != "groups"}
    report.update({"private_pool_sha256": v1.digest(path), "candidate_groups": len(groups),
                   "candidate_speakers": len({g["speaker"] for g in groups}), "candidate_contexts_including_alternatives": 2 * len(groups)})
    v1.write_new(v1.PUBLIC / "icsi_source_curation_pool_receipt_v3.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze-policy", action="store_true")
    mode.add_argument("--retrieve-pool", action="store_true")
    parser.add_argument("--expected-policy-sha256")
    args = parser.parse_args()
    if args.retrieve_pool and not args.expected_policy_sha256:
        parser.error("Explicit policy hash required")
    print(json.dumps(freeze() if args.freeze_policy else retrieve(args.expected_policy_sha256), indent=2, sort_keys=True))
