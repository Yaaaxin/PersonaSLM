"""Bounded metadata-only qualification; never deserialize transcript targets."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile


ARCHIVE_SHA256 = "9db98ebdd61a085b4f45f24f46e9c9f6c6f26c3c9cd41643a3b9e74362c85de7"
SOURCE_URL = "https://groups.inf.ed.ac.uk/ami/ICSICorpusAnnotations/ICSI_original_transcripts.zip"


def read_header(stream):
    """Read exactly through Preamble, not a single following target byte."""
    header = bytearray()
    while not header.endswith(b"</Preamble>"):
        byte = stream.read(1)
        if not byte or len(header) >= 131072:
            raise ValueError("Missing or excessive preamble; no transcript fallback")
        header.extend(byte)
    text = header.decode("utf-8")
    text = re.sub(r"<!DOCTYPE[^>]*>", "", text)
    root = ET.fromstring(text + "</Meeting>")
    session = root.attrib["Session"]
    if not re.fullmatch(r"B[a-z]{2}\d{3}", session):
        raise ValueError("Unexpected meeting identifier")
    stamp = root.attrib["DateTimeStamp"]
    date = datetime.strptime(stamp, "%Y-%m-%d-%H%M")
    people = {p.attrib["Name"] for p in root.findall("./Preamble/Participants/Participant")}
    if not people or any(not re.fullmatch(r"[mfux][en]\d{3}", p) for p in people):
        raise ValueError("Unexpected participant identifier; do not guess identity")
    computers = {p for p in people if p.startswith("x")}
    return {"meeting": session, "group": session[:3], "date": date,
            "participants": people - computers, "computer_participant_count": len(computers),
            "header_bytes_read": len(header)}


def summarize(records):
    by_speaker = defaultdict(list)
    neighbors = defaultdict(set)
    for record in records:
        for person in record["participants"]:
            by_speaker[person].append(record)
            neighbors[person].update(record["participants"])
    unseen = set(neighbors)
    components = []
    while unseen:
        pending = {min(unseen)}
        component = set()
        while pending:
            person = pending.pop()
            if person not in component:
                component.add(person)
                pending.update(neighbors[person] - component)
        unseen -= component
        components.append(component)
    distinct_dates = {p: len({r["date"] for r in rs}) for p, rs in by_speaker.items()}
    # Every candidate is metadata-only: 2 earlier meetings and 1 later target.
    windows = []
    for person, person_records in by_speaker.items():
        ordered = sorted(person_records, key=lambda r: (r["date"], r["meeting"]))
        for index in range(len(ordered) - 2):
            triple = ordered[index:index + 3]
            if triple[0]["date"] < triple[1]["date"] < triple[2]["date"]:
                windows.append((person, set().union(*(r["participants"] for r in triple))))
    disjoint_pairs = sum(a[1].isdisjoint(b[1]) for i, a in enumerate(windows) for b in windows[i + 1:])
    component_stats = sorted(({
        "speaker_count": len(c),
        "meeting_count": sum(bool(r["participants"] & c) for r in records),
        "speakers_with_at_least_three_dates": sum(distinct_dates[p] >= 3 for p in c),
    } for c in components), key=lambda c: (-c["speaker_count"], -c["meeting_count"]))
    groups = []
    for group in sorted({r["group"] for r in records}):
        group_records = [r for r in records if r["group"] == group]
        group_people = set().union(*(r["participants"] for r in group_records))
        dates = {p: {r["date"] for r in group_records if p in r["participants"]} for p in group_people}
        groups.append({"group": group, "meetings": len(group_records), "speakers": len(group_people),
                       "speakers_at_least_three_dates": sum(len(d) >= 3 for d in dates.values())})
    split_candidates = []
    for first_group, second_group in itertools.permutations(sorted({r["group"] for r in records}), 2):
        first = [r for r in records if r["group"] == first_group]
        first_people = set().union(*(r["participants"] for r in first))
        second = [r for r in records if r["group"] == second_group and r["participants"].isdisjoint(first_people)]
        if not second:
            continue
        eligible = []
        for subset in (first, second):
            dates_by_person = defaultdict(set)
            for record in subset:
                for person in record["participants"]:
                    dates_by_person[person].add(record["date"])
            eligible.append(sum(len(dates) >= 3 for dates in dates_by_person.values()))
        if min(eligible) > 0:
            split_candidates.append({"first_group_all_meetings": first_group,
                                     "second_group_crossparticipants_excluded": second_group,
                                     "first_meetings": len(first), "second_meetings": len(second),
                                     "first_speakers_at_least_three_dates": eligible[0],
                                     "second_speakers_at_least_three_dates": eligible[1]})
    return {
        "meeting_count": len(records), "unique_speakers": len(by_speaker),
        "meeting_group_counts": groups,
        "distinct_meeting_dates": len({r["date"] for r in records}),
        "date_range_local_timezone_unspecified": [min(r["date"] for r in records).isoformat(), max(r["date"] for r in records).isoformat()],
        "speaker_distinct_date_histogram": dict(sorted(Counter(distinct_dates.values()).items())),
        "speakers_with_at_least_two_dates": sum(n >= 2 for n in distinct_dates.values()),
        "speakers_with_at_least_three_dates": sum(n >= 3 for n in distinct_dates.values()),
        "speakers_with_at_least_four_dates": sum(n >= 4 for n in distinct_dates.values()),
        "full_corpus_coparticipation_components": component_stats,
        "three_meeting_metadata_windows": len(windows),
        "participant_disjoint_window_pairs": disjoint_pairs,
        "participant_disjoint_window_pair_exists": bool(disjoint_pairs),
        "window_pair_is_not_a_frozen_split_or_sufficient_study_sample": True,
        "group_disjoint_feasibility_candidates_not_selected": split_candidates,
        "group_split_limitation": "Speaker separation is also research-group/topic separation; domain transfer and speaker generalization are not isolated",
    }


def qualify(directory):
    archive = directory / "ICSI_original_transcripts.zip"
    with archive.open("rb") as archive_file:
        if hashlib.file_digest(archive_file, "sha256").hexdigest() != ARCHIVE_SHA256:
            raise ValueError("Archive hash mismatch")
    records = []
    with zipfile.ZipFile(archive) as source:
        for name in source.namelist():
            if re.fullmatch(r"transcripts/B[a-z]{2}\d{3}\.mrt", name):
                with source.open(name) as stream:
                    records.append(read_header(stream))
        ignored_mrt = sum(name.endswith(".mrt") and not re.fullmatch(r"transcripts/B[a-z]{2}\d{3}\.mrt", name) for name in source.namelist())
        archive_members = len(source.infolist())
        # Only tag attributes are retained, never personal demographic values.
        speaker_root = ET.fromstring(source.read("doc/icsi1.spk"))
        speaker_ids = {n.attrib["tag"] for n in speaker_root.iter("speaker")}
        header_people = set().union(*(r["participants"] for r in records))
        if header_people - speaker_ids:
            raise ValueError("Transcript-header identities absent from speaker database")
    metadata = [{"meeting": r["meeting"], "date": r["date"].isoformat(), "participants": sorted(r["participants"])} for r in sorted(records, key=lambda r: r["meeting"])]
    artifacts = {p.name: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
                 for p in (archive, directory / "official_license.html", directory / "official_download.html")}
    return {
        "schema": "icsi_english_metadata_qualification_v1",
        "status": "METADATA_QUALIFICATION_ONLY_NOT_EXPERIMENT_AUTHORIZATION",
        "archive_url": SOURCE_URL, "local_artifacts": artifacts,
        "archive_members": archive_members, "ignored_nonmeeting_mrt_files": ignored_mrt,
        "metadata_sha256": hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest(),
        "header_bytes_read": sum(r["header_bytes_read"] for r in records),
        "computer_generated_header_participants_excluded": sum(r["computer_participant_count"] for r in records),
        "speaker_database_header_records": len(speaker_ids),
        "human_header_ids_missing_from_speaker_database": 0,
        "published_vs_actual_speaker_count": "2003 paper/index report 53; this pinned archive has 60 distinct human-format header IDs, all in its speaker database. No identities merged or guessed.",
        "transcript_body_bytes_deserialized": 0,
        "qualification": summarize(records),
        "licence": {
            "official_release": "CC BY 4.0; official download page explicitly includes this original transcript archive",
            "url": "https://groups.inf.ed.ac.uk/ami/icsi/license.shtml",
            "historical_archive_notice": "2004 LDC/ICSI copyright retained; no additional end-user licence in archive index",
            "privacy": "Copyright permission does not comprehensively grant privacy/personality rights",
            "participant_approval_evidence": "Janin et al. 2003 section 4.2; not speaker-simulation-specific consent",
            "primary_paper": "https://www.ee.columbia.edu/~dpwe/pubs/icassp03-janin.pdf",
        },
        "not_established": ["usable utterance quantities", "professional fact yield or truth", "style measurement validity", "sensitive-content exclusion", "final disjoint development/validation cohorts", "temporal changes", "speaker-simulation-specific consent"],
        "new_model_generations": 0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path(".local/datasets/icsi_english_v1"))
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()
    report = qualify(args.data)
    if args.write:
        report["created_utc"] = datetime.now(timezone.utc).isoformat()
        report["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        args.write.parent.mkdir(parents=True, exist_ok=True)
        with args.write.open("x", encoding="utf-8") as output:
            json.dump(report, output, indent=2, sort_keys=True)
            output.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
