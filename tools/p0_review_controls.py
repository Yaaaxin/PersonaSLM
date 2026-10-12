"""Prepare mechanical checks and a condition-blinded human review packet.

This program never supplies human semantic judgments.
"""
import argparse
import json
from pathlib import Path
import random
import re

from personaslm.fixtures import load_cases
from personaslm.journal import atomic_json, utc_now
from personaslm.run_audit import text_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--freeze-name", default="prompts_frozen_v3.json")
    args = parser.parse_args()
    frozen = json.loads((args.session / args.freeze_name).read_text(encoding="utf-8"))
    cases = {c.case_id: c for c in load_cases(Path("data/synthetic/p0_cases.jsonl"))}
    cities = sorted({f.value for c in cases.values() for f in c.facts})
    rows, packet, mapping = [], [], []
    matched = list(frozen["rows"])
    random.Random(42).shuffle(matched)
    for number, row in enumerate(matched, 1):
        cid, neutral, reference = row["case_id"], row["neutral_condition"], row["reference_condition"]
        p = frozen["prompts"][cid][neutral]["prompt"]
        target = frozen["prompts"][cid][reference]["prompt"]
        text = row["neutral_text"]
        known_cities = [city for city in cities if re.search(r"\b"+re.escape(city)+r"\b", text, re.I)]
        issues = []
        if neutral == "N_style":
            issues = ["Repeated sentence may prime repetition", "Shared 'Speaker style profile' heading may prime style interpretation"]
        if neutral == "N_history":
            issues = ["Dated dialogue wrapper intentionally retained; semantic equivalence requires independent review"]
        checks = {"known_city_absent": not known_cities,
                  "evidence_identical": p["evidence_block"] == target["evidence_block"],
                  "question_identical": p["text"].endswith(f"User: {cases[cid].question}\nAssistant:") and target["text"].endswith(f"User: {cases[cid].question}\nAssistant:"),
                  "dates_match_reference": re.findall(r"\d{4}-\d{2}-\d{2}", p["additions"][0]) == re.findall(r"\d{4}-\d{2}-\d{2}", target["additions"][0])}
        rows.append({**row, "conditioning_text": p["additions"][0], "mechanical_checks": checks,
            "assistant_review": "PARTIAL" if all(checks.values()) else "FAILED", "issues": issues,
            "human_judgment": None, "independent_semantic_review_complete": False})
        rid = f"review_{number:03d}"
        packet.append({"review_id": rid, "trusted_evidence": cases[cid].trusted_evidence,
            "current_question": cases[cid].question, "additional_context": p["additions"][0],
            "introduces_answer": None, "contradictory_personal_fact": None, "strong_style_instruction": None,
            "unintended_temporal_information": None, "repetition_or_priming_concern": None,
            "verdict_PASS_PARTIAL_FAILED": None, "notes": None, "annotator_id": None, "reviewed_utc": None})
        mapping.append({"review_id": rid, "case_id": cid, "condition": neutral, "text_sha256": text_hash(text)})
    atomic_json(args.session / "neutral_semantic_audit.json", {"created_utc": utc_now(),
        "status": "PARTIAL", "reviewer": "Automated technical inspection; no human judgments", "rows": rows})
    atomic_json(args.session / "neutral_review_mapping.json", {"mapping": mapping})
    destination = Path("docs/validation/P0_neutral_blinded_review.jsonl")
    with destination.open("x", encoding="utf-8", newline="\n") as handle:
        for entry in packet:
            handle.write(json.dumps(entry, ensure_ascii=False)+"\n")
    print(json.dumps({"created_utc": utc_now(), "review_items": len(packet), "human_judgments": 0,
        "semantic_status": "PARTIAL", "packet": destination.as_posix(),
        "blinding_limit": "Condition IDs/model outputs hidden; text form can still reveal treatment type."}))


if __name__ == "__main__":
    main()
