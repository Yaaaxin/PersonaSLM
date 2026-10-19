"""Apply explicit private validation-source decisions under the frozen Bed policy."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import zipfile

import english_icsi_material_v1 as v1
import english_icsi_material_v2 as v2
import english_icsi_material_v3 as v3
import english_icsi_source_curation_v3 as original
import english_icsi_validation_material_v1 as validation


POOL = v1.PRIVATE / "icsi_validation_source_pool_v1.json"


def curation_hashes():
    return {Path(__file__).name: v1.digest(Path(__file__)),
            "test_english_icsi_validation_curation_v1.py": v1.digest(Path("tests/test_english_icsi_validation_curation_v1.py"))}


def check_decisions(groups, decisions):
    covered = [item["group"] for item in decisions["selection"] + decisions["exclusions"]]
    if len(covered) != len(set(covered)) or set(covered) != set(groups):
        raise ValueError("Every candidate group needs exactly one explicit decision")
    speakers = [groups[item["group"]]["speaker"] for item in decisions["selection"]]
    if len(speakers) > 8 or len(speakers) != len(set(speakers)):
        raise ValueError("At most one group per speaker and eight speakers")
    for item in decisions["selection"]:
        if any(not item[key].strip() for key in ("statement", "fact_basis", "context_basis")):
            raise ValueError("Complete supported proposition and source audit required")
        indices = item["style_indices"]
        if len(indices) != len(set(indices)) or not 4 <= len(indices) <= 6 or min(indices) < 0:
            raise ValueError("Four to six distinct source-bound style examples required")


def style_candidates(group, split, archive):
    meetings = {m["meeting"]: m for m in split["reserved"]}
    meeting = meetings[group["first_source_meeting"]]
    if not re.fullmatch(r"Bed\d{3}", meeting["meeting"]):
        raise ValueError("Only frozen reserved Bed sources allowed")
    labels = {speaker: f"V{i:03}" for i, speaker in enumerate(sorted(split["reserved_speakers"]), 1)}
    turns, _ = v2.parse_meeting(archive.read(f"transcripts/{meeting['meeting']}.mrt"), meeting["meeting"], set(meeting["participants"]))
    identifiers = set(group["style"]["source_segment_ids"])
    facts = {i for t in group["facts_source_selfreports_not_world_verified"] for i in t["source_segment_ids"]}
    if identifiers & facts:
        raise ValueError("Style/fact source overlap")
    examples = []
    for turn in turns:
        if set(turn["source_segment_ids"]).issubset(identifiers):
            if labels[turn["speaker"]] != group["speaker"]:
                raise ValueError("Style-source speaker mismatch")
            if 10 <= len(v1.WORDS.findall(turn["text"])) <= 60 and v3.screen(turn):
                examples.append(dict(turn, speaker=group["speaker"]))
    return examples


def curate(pool_sha, decisions_path, decisions_sha, authorization_path):
    pool = validation.checked_json(POOL, pool_sha)
    decisions = validation.checked_json(decisions_path, decisions_sha)
    policy = validation.checked_json(validation.POLICY, pool["policy_sha256"])
    authorization = validation.checked_json(authorization_path, pool["authorization_sha256"])
    if (authorization.get("approved_for_reserved_body_access") is not True
            or authorization.get("validation_policy_sha256") != pool["policy_sha256"]
            or authorization.get("development_manifest_sha256") != policy["development_manifest"]["sha256"]):
        raise ValueError("Explicit bound body-access authorization required")
    if authorization.get("curation_source_hashes") != curation_hashes():
        raise ValueError("Curation source must be bound before reserved-body access")
    if decisions["pool_sha256"] != pool_sha or validation.bound_source_hashes() != policy["source_hashes"]:
        raise ValueError("Frozen pool/source changed")
    if v1.digest(v1.DATA) != policy["archive_sha256"]:
        raise ValueError("Archive changed")
    split = validation.checked_json(v1.SPLIT, v2.EXPECTED_SPLIT)
    validation.reserved_metadata(split)
    groups = {g["candidate_group_id"]: copy.deepcopy(g) for g in pool["groups"]}
    check_decisions(groups, decisions)
    with zipfile.ZipFile(v1.DATA) as archive:
        for decision in decisions["selection"]:
            group = groups[decision["group"]]
            examples = style_candidates(group, split, archive)
            group["style_examples"] = [examples[i] for i in decision["style_indices"]]
            if sum(len(v1.WORDS.findall(t["text"])) for t in group["style_examples"]) > 200:
                raise ValueError("Style dossier word bound")
    names = {}
    for decision in decisions["selection"]:
        for span in decision["name_spans"]:
            token = original.flagged(original.locate(groups[decision["group"]], span["path"])["text"])[span["flag_index"]][0]
            if token not in names:
                names[token] = f"Colleague {chr(65 + len(names))}"
    cases = []
    for decision in decisions["selection"]:
        group = groups[decision["group"]]
        if len(group["continuations"]) != 2 or not re.fullmatch(r"V\d{3}", group["speaker"]):
            raise ValueError("Frozen two-context validation group required")
        fact = copy.deepcopy(group["facts_source_selfreports_not_world_verified"][decision["fact_index"]])
        for index, continuation in enumerate(group["continuations"], 1):
            case = {key: copy.deepcopy(group[key]) for key in ("speaker", "first_source_meeting", "first_source_date", "history_meeting", "history_date", "style")}
            case.update(copy.deepcopy(continuation))
            case.update(case_id=f"ICSI-{group['speaker']}-T{index}", source_candidate_group=decision["group"],
                        structured_facts=[{"statement": decision["statement"], "source_quote": fact["text"],
                                           "source_date": group["first_source_date"], "curation_basis": decision["fact_basis"]}],
                        facts_source_selfreports_not_world_verified=[fact],
                        history=[original.redact(t, names) for t in group["history"]],
                        style_examples=[original.redact(t, names) for t in group["style_examples"]],
                        source_curation_basis=decision["context_basis"], reference_is_unique_gold=False,
                        human_semantic_review_status="PENDING_GENUINE_REVIEW")
            case["context"] = [original.redact(t, names) for t in case["context"]]
            target = case["reference_continuation_not_for_prompt"] = original.redact(case["reference_continuation_not_for_prompt"], names)
            if not case["first_source_date"] < case["history_date"] < case["target_date"]:
                raise ValueError("Chronology")
            if len(case["context"]) != 8 or any(t["end"] > target["start"] for t in case["context"]):
                raise ValueError("Current-context source integrity")
            available = " ".join(t["text"] for t in [fact] + case["history"] + case["style_examples"] + case["context"]).lower()
            if target["text"].lower() in available:
                raise ValueError("Within-case full-reference leakage")
            cases.append(case)
    cross_matches = sum(c["reference_continuation_not_for_prompt"]["text"].lower() in " ".join(t["text"] for t in d["history"] + d["context"] + d["style_examples"] + d["facts_source_selfreports_not_world_verified"]).lower()
                        for i, c in enumerate(cases) for j, d in enumerate(cases) if i != j)
    artifact = {"schema": "icsi_validation_curated_material_v1", "created_utc": datetime.now(timezone.utc).isoformat(),
                "status": "AI_SOURCE_CURATED_REQUIRES_ROOT_AND_SEPARATE_SOURCE_AUDIT_NOT_EXECUTION_GO",
                "cases": cases, "pool_sha256": pool_sha, "curation_decisions_sha256": decisions_sha,
                "validation_policy_sha256": pool["policy_sha256"], "authorization_sha256": pool["authorization_sha256"],
                "source_hashes": {**policy["source_hashes"], **curation_hashes()}, "split_sha256": v2.EXPECTED_SPLIT,
                "archive_sha256": policy["archive_sha256"], "name_redaction_mapping_private": names,
                "cross_case_full_reference_matches_requiring_audit": cross_matches,
                "limitations": decisions["limitations"], "new_model_generations": 0}
    path = v1.PRIVATE / "icsi_validation_curated_material_v1.json"
    v1.write_new(path, artifact)
    receipt = {key: value for key, value in artifact.items() if key not in {"cases", "name_redaction_mapping_private"}}
    receipt.update(private_material_sha256=v1.digest(path), speakers=len({c["speaker"] for c in cases}),
                   contexts=len(cases), style_example_counts=[len(c["style_examples"]) for c in cases],
                   existing_person_names_pseudonymized=len(names), unique_gold_references=False)
    v1.write_new(v1.PUBLIC / "icsi_validation_curated_material_receipt_v1.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("pool-sha256", "decisions", "decisions-sha256", "authorization-record"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    print(json.dumps(curate(args.pool_sha256, args.decisions, args.decisions_sha256, args.authorization_record), indent=2, sort_keys=True))
