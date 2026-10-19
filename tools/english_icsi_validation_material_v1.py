"""Hash-bound reserved-cohort wrapper around unchanged development retrieval rules."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import zipfile

import english_icsi_material_v1 as v1
import english_icsi_material_v2 as v2
import english_icsi_material_v3 as v3


POLICY = v1.PRIVATE / "icsi_validation_source_policy_v1.json"
RUBRIC = v1.PUBLIC / "human_review_rubric_v1.json"


def reserved_metadata(split):
    development = set(split["development_speakers"])
    reserved = set(split["reserved_speakers"])
    meetings = split["reserved"]
    if development & reserved or len(reserved) != 12 or len(meetings) != 11:
        raise ValueError("Frozen participant-disjoint reserved cohort changed")
    actual = set()
    dates = {speaker: set() for speaker in reserved}
    for meeting in meetings:
        if not re.fullmatch(r"Bed\d{3}", meeting["meeting"]):
            raise ValueError("Unexpected validation meeting")
        people = set(meeting["participants"])
        if people & development or not people <= reserved:
            raise ValueError("Participant leakage")
        actual |= people
        for speaker in people:
            dates[speaker].add(meeting["date"])
    if actual != reserved or sum(len(values) >= 3 for values in dates.values()) != 8:
        raise ValueError("Reserved metadata eligibility differs from freeze")
    return {"development": meetings, "development_speakers": sorted(reserved)}


def validation_labels(groups):
    # The unchanged pool function labels its input cohort D; only labels change.
    def visit(value):
        if isinstance(value, list):
            return [visit(item) for item in value]
        if isinstance(value, dict):
            return {key: "V" + item[1:] if key in {"speaker", "candidate_group_id"}
                    and isinstance(item, str) and re.fullmatch(r"D\d{3}(?:-G[12])?", item)
                    else visit(item) for key, item in value.items()}
        return value
    return visit(groups)


def bound_source_hashes():
    return {**v3.hashes(), "english_icsi_source_curation_v3.py": v1.digest(Path("tools/english_icsi_source_curation_v3.py")),
            Path(__file__).name: v1.digest(Path(__file__)),
            "test_english_icsi_validation_material_v1.py": v1.digest(Path("tests/test_english_icsi_validation_material_v1.py"))}


def checked_json(path, expected):
    path = Path(path)
    if v1.digest(path) != expected:
        raise ValueError(f"Bound input changed: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def freeze(manifest_path, manifest_sha, protocol_path, protocol_sha):
    manifest = checked_json(manifest_path, manifest_sha)
    protocol = checked_json(protocol_path, protocol_sha)
    split = checked_json(v1.SPLIT, v2.EXPECTED_SPLIT)
    reserved_metadata(split)
    if manifest["batch"] != "development" or manifest["language"] != "en":
        raise ValueError("Frozen English development manifest required")
    inputs = manifest["input_hashes"]
    if inputs.get(Path(protocol_path).as_posix()) != protocol_sha or inputs.get(RUBRIC.as_posix()) != v1.digest(RUBRIC):
        raise ValueError("Protocol/rubric not bound by development manifest")
    hashes = bound_source_hashes()
    for name, digest in hashes.items():
        if name not in {Path(__file__).name, "test_english_icsi_validation_material_v1.py"}:
            if protocol["input_hashes"].get("tools/" + name) != digest:
                raise ValueError("Source-selection rule changed since development freeze")
    policy = {"schema": "icsi_validation_source_policy_v1", "created_utc": datetime.now(timezone.utc).isoformat(),
              "status": "FROZEN_METADATA_ONLY_REQUIRES_EXPLICIT_ROOT_BODY_ACCESS_GO",
              "development_manifest": {"path": Path(manifest_path).as_posix(), "sha256": manifest_sha},
              "development_protocol": {"path": Path(protocol_path).as_posix(), "sha256": protocol_sha},
              "rubric_sha256": v1.digest(RUBRIC), "split_sha256": v2.EXPECTED_SPLIT,
              "archive_sha256": v1.ARCHIVE_SHA256, "source_hashes": hashes,
              "development_source_policy_sha256": v1.digest(v3.POLICY),
              "development_curation_decisions_sha256": v1.digest(v1.PRIVATE / "icsi_source_curation_decisions_v3.json"),
              "frozen_generation_configuration": {key: manifest[key] for key in ("model", "runtime", "template_sha256", "tokenizer_identity")},
              "next_stage_rule": protocol["next_stage_rule"],
              "rules": [
                  "Only11 reserved Bed meetings and12 frozen original participant IDs; none may occur in development",
                  "Reuse unmodified v2.parse_meeting, v3.screen and v3.pool; only pseudonym prefix becomes V",
                  "At most8 speakers with3datedmeetings; at most2 earliest candidate groups per person and2 contexts per group",
                  "Same complete dated professional self-report, separate style sources,6to10turn history and8turn current-context criteria",
                  "Root and separate AI source audit must curate complete supported F propositions and interpretable contexts; unfinished authentic references are not unique gold and are not an automatic exclusion",
                  "Same source-bound4to6style examples up to200words, private name pseudonymization and privacy exclusions; examples dossier-only, never S prompts",
                  "No outcome-informed prompt, model, style-feature, source-criteria or rubric changes; no threshold tuning on reserved cases",
                  "At most160 eventual requests if8 speakers qualify; actual source yield is not a quota; this tool authorizes no inference"
              ], "reserved_transcript_bodies_read": 0, "new_model_generations": 0}
    v1.write_new(POLICY, policy)
    snapshot = v1.PRIVATE / "english_icsi_validation_material_v1.policy_freeze.py"
    with snapshot.open("xb") as stream:
        stream.write(Path(__file__).read_bytes())
    receipt = {**policy, "private_policy_sha256": v1.digest(POLICY), "source_snapshot_sha256": v1.digest(snapshot)}
    v1.write_new(v1.PUBLIC / "icsi_validation_source_policy_receipt_v1.json", receipt)
    return receipt


def retrieve(policy_sha, authorization_path, authorization_sha):
    policy = checked_json(POLICY, policy_sha)
    authorization = checked_json(authorization_path, authorization_sha)
    if (authorization.get("approved_for_reserved_body_access") is not True
            or authorization.get("validation_policy_sha256") != policy_sha
            or authorization.get("development_manifest_sha256") != policy["development_manifest"]["sha256"]):
        raise ValueError("Explicit hash-bound root body-access GO required")
    if bound_source_hashes() != policy["source_hashes"] or v1.digest(v1.DATA) != policy["archive_sha256"]:
        raise ValueError("Frozen source/archive changed")
    for key in ("development_manifest", "development_protocol"):
        checked_json(policy[key]["path"], policy[key]["sha256"])
    if (v1.digest(RUBRIC) != policy["rubric_sha256"]
            or v1.digest(v3.POLICY) != policy["development_source_policy_sha256"]
            or v1.digest(v1.PRIVATE / "icsi_source_curation_decisions_v3.json") != policy["development_curation_decisions_sha256"]):
        raise ValueError("Frozen rubric/source policy changed")
    split = reserved_metadata(checked_json(v1.SPLIT, v2.EXPECTED_SPLIT))
    parsed, exclusions = {}, Counter()
    with zipfile.ZipFile(v1.DATA) as archive:
        for meeting in split["development"]:
            turns, rejected = v2.parse_meeting(archive.read(f"transcripts/{meeting['meeting']}.mrt"), meeting["meeting"], set(meeting["participants"]))
            exclusions.update(rejected)
            parsed[meeting["meeting"]] = [turn for turn in turns if v3.screen(turn)]
            exclusions["additional_sensitive_or_calibration"] += len(turns) - len(parsed[meeting["meeting"]])
    groups, failures = v3.pool(split, parsed)
    groups = validation_labels(groups)
    if len(groups) > 16 or len({g["speaker"] for g in groups}) > 8:
        raise ValueError("Validation source allocation exceeded")
    artifact = {"schema": "icsi_validation_source_pool_v1", "created_utc": datetime.now(timezone.utc).isoformat(),
                "status": "RESERVED_POOL_REQUIRES_SOURCE_CURATION_NOT_EXECUTION_GO", "groups": groups,
                "policy_sha256": policy_sha, "authorization_sha256": authorization_sha,
                "source_hashes": policy["source_hashes"], "split_sha256": v2.EXPECTED_SPLIT,
                "speaker_exclusions": failures, "segment_exclusions": dict(exclusions),
                "reserved_transcript_bodies_read": len(parsed), "new_model_generations": 0}
    path = v1.PRIVATE / "icsi_validation_source_pool_v1.json"
    v1.write_new(path, artifact)
    report = {key: value for key, value in artifact.items() if key != "groups"}
    report.update(private_pool_sha256=v1.digest(path), candidate_groups=len(groups),
                  candidate_speakers=len({g["speaker"] for g in groups}), candidate_contexts_including_alternatives=2 * len(groups))
    v1.write_new(v1.PUBLIC / "icsi_validation_source_pool_receipt_v1.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze-policy", action="store_true")
    mode.add_argument("--retrieve-pool", action="store_true")
    for name in ("development-manifest", "development-manifest-sha256", "protocol", "protocol-sha256",
                 "expected-policy-sha256", "authorization-record", "authorization-sha256"):
        parser.add_argument("--" + name)
    args = parser.parse_args()
    required = [args.development_manifest, args.development_manifest_sha256, args.protocol, args.protocol_sha256] if args.freeze_policy else [args.expected_policy_sha256, args.authorization_record, args.authorization_sha256]
    if not all(required):
        parser.error("All explicit path/hash bindings for the selected mode are required")
    print(json.dumps(freeze(*required) if args.freeze_policy else retrieve(*required), indent=2, sort_keys=True))
