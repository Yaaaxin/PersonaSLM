"""Apply explicit private source-curation decisions; never assert experiment GO."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import zipfile

import english_icsi_material_v1 as v1
import english_icsi_material_v2 as v2
import english_icsi_material_v3 as v3


POOL = v1.PRIVATE / "icsi_source_curation_pool_v3.json"
DECISIONS = v1.PRIVATE / "icsi_source_curation_decisions_v3.json"


def locate(group, path):
    node = group
    for part in path.split("."):
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def flagged(text):
    return [m for m in v2.NAME_PATTERN.finditer(text) if m[0] not in v1.SAFE_CAPITAL]


def redact(turn, names):
    result = copy.deepcopy(turn)
    matches = []
    for name, alias in names.items():
        for match in re.finditer(r"(?<![A-Za-z])" + re.escape(name) + r"(?![A-Za-z])", turn["text"]):
            matches.append({"start": match.start(), "end": match.end(), "original": name, "replacement": alias})
    text = turn["text"]
    for item in sorted(matches, key=lambda item: item["start"], reverse=True):
        text = text[:item["start"]] + item["replacement"] + text[item["end"]:]
    if matches:
        result.update(text=text, original_text_before_name_redaction=turn["text"], name_redactions=matches)
    return result


def style_candidates(group, split, archive):
    meeting = next(m for m in split["development"] if m["meeting"] == group["first_source_meeting"])
    if not re.fullmatch(r"Bmr\d{3}", meeting["meeting"]):
        raise ValueError("Reserved transcript access forbidden")
    turns, _ = v2.parse_meeting(archive.read(f"transcripts/{meeting['meeting']}.mrt"), meeting["meeting"], set(meeting["participants"]))
    identifiers = set(group["style"]["source_segment_ids"])
    facts = {i for t in group["facts_source_selfreports_not_world_verified"] for i in t["source_segment_ids"]}
    if identifiers & facts:
        raise ValueError("Style/fact source overlap")
    return [dict(t, speaker=group["speaker"]) for t in turns
            if set(t["source_segment_ids"]).issubset(identifiers)
            and 10 <= len(v1.WORDS.findall(t["text"])) <= 60 and v3.screen(t)]


def curate():
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    if v1.digest(POOL) != decisions["pool_sha256"] or v1.digest(v1.SPLIT) != v2.EXPECTED_SPLIT:
        raise ValueError("Pool/split changed")
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    if pool["source_hashes"] != v3.hashes() or v1.digest(v1.DATA) != v1.ARCHIVE_SHA256:
        raise ValueError("Frozen source/archive changed")
    split = json.loads(v1.SPLIT.read_text(encoding="utf-8"))
    groups = {g["candidate_group_id"]: g for g in pool["groups"]}
    covered = [d["group"] for d in decisions["selection"] + decisions["exclusions"]]
    if len(covered) != len(set(covered)) or set(covered) != set(groups):
        raise ValueError("Every retrieved group needs one curation decision")
    names = {}
    for decision in decisions["selection"]:
        for span in decision["name_spans"]:
            name = flagged(locate(groups[decision["group"]], span["path"])["text"])[span["flag_index"]][0]
            if name not in names:
                names[name] = f"Colleague {chr(65 + len(names))}"
    cases = []
    with zipfile.ZipFile(v1.DATA) as archive:
        for decision in decisions["selection"]:
            group = groups[decision["group"]]
            fact = copy.deepcopy(group["facts_source_selfreports_not_world_verified"][decision["fact_index"]])
            examples = style_candidates(group, split, archive)
            examples = [redact(examples[i], names) for i in decision["style_indices"]]
            if not 4 <= len(examples) <= 6 or sum(len(v1.WORDS.findall(t["text"])) for t in examples) > 200:
                raise ValueError("Style dossier bounds")
            history = [redact(t, names) for t in group["history"]]
            for index, continuation in enumerate(group["continuations"], 1):
                case = {k: copy.deepcopy(group[k]) for k in ("speaker", "first_source_meeting", "first_source_date", "history_meeting", "history_date", "style")}
                case.update(copy.deepcopy(continuation))
                case.update(case_id=f"ICSI-{group['speaker']}-T{index}", source_candidate_group=decision["group"],
                            structured_facts=[{"statement": decision["statement"], "source_quote": fact["text"],
                                               "source_date": group["first_source_date"], "curation_basis": decision["fact_basis"]}],
                            facts_source_selfreports_not_world_verified=[fact], history=history,
                            style_examples=examples, source_curation_basis=decision["context_basis"],
                            reference_is_unique_gold=False, human_semantic_review_status="PENDING_GENUINE_REVIEW")
                case["context"] = [redact(t, names) for t in case["context"]]
                case["reference_continuation_not_for_prompt"] = redact(case["reference_continuation_not_for_prompt"], names)
                target = case["reference_continuation_not_for_prompt"]
                if not case["first_source_date"] < case["history_date"] < case["target_date"]:
                    raise ValueError("Chronology")
                if any(t["end"] > target["start"] for t in case["context"]):
                    raise ValueError("Future context")
                available = " ".join(t["text"] for t in [fact] + history + examples + case["context"]).lower()
                if target["text"].lower() in available:
                    raise ValueError("Full-reference leakage")
                cases.append(case)
    artifact = {"schema": "icsi_curated_material_v3", "created_utc": datetime.now(timezone.utc).isoformat(),
                "status": "AI_SOURCE_CURATED_REQUIRES_ROOT_SOURCE_REVIEW_NOT_EXECUTION_GO", "cases": cases,
                "pool_sha256": v1.digest(POOL), "curation_decisions_sha256": v1.digest(DECISIONS),
                "source_hashes": {**v3.hashes(), Path(__file__).name: v1.digest(Path(__file__))},
                "archive_sha256": v1.ARCHIVE_SHA256, "split_sha256": v2.EXPECTED_SPLIT,
                "name_redaction_mapping_private": names, "limitations": decisions["limitations"],
                "reserved_transcript_bodies_read": 0, "new_model_generations": 0}
    path = v1.PRIVATE / "icsi_curated_material_v3.json"
    v1.write_new(path, artifact)
    receipt = {k: v for k, v in artifact.items() if k not in {"cases", "name_redaction_mapping_private"}}
    receipt.update(private_material_sha256=v1.digest(path), speakers=len({c["speaker"] for c in cases}),
                   contexts=len(cases), history_turns=[len(c["history"]) for c in cases],
                   style_example_counts=[len(c["style_examples"]) for c in cases],
                   existing_person_names_pseudonymized=len(names), unique_gold_references=False)
    v1.write_new(v1.PUBLIC / "icsi_curated_material_receipt_v3.json", receipt)
    return receipt


if __name__ == "__main__":
    print(json.dumps(curate(), indent=2, sort_keys=True))
