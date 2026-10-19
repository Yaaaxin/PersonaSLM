"""Deliver sealed English study outputs through the frozen private review adapter."""

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

import english_sfh_reproduce_v1 as reproduction
import english_sfh_review_v1 as review


PUBLIC = Path("docs/validation/p1/english_real_speaker_stage_v1")
PRIVATE = Path(".local/experiments/english_sfh_v1")
DELIVERIES = Path(".local/reviewer-packages")
FROZEN_ADAPTER_SHA256 = "01b29ccb9686f8e9fd65408338da6d99bfc4397f9665aa402c10d9c807b615bd"
FROZEN_RUBRIC_SHA256 = "2c6331e2b076c3b0903170cc159823dcee01d28fc1848b78fa4f887a8388cb14"
LIVE_HELPERS = {
    "english_sfh_review_v1": "tools/english_sfh_review_v1.py",
    "p1_persona_dialogue_disjoint_surface_validation_review_v4": "tools/p1_persona_dialogue_disjoint_surface_validation_review_v4.py",
    "real_persona_chat_sfh_review_v1": "tools/real_persona_chat_sfh_review_v1.py",
    "english_sfh_reproduce_v1": "tools/english_sfh_reproduce_v1.py",
    "personaslm": "src/personaslm/__init__.py",
    "personaslm.journal": "src/personaslm/journal.py",
    "personaslm.provenance": "src/personaslm/provenance.py",
}


def require(value, message):
    if not value:
        raise ValueError(message)


def verify_live_helpers(plan):
    root = Path(__file__).resolve().parents[1]
    for module_name, relative_path in LIVE_HELPERS.items():
        path = Path(sys.modules[module_name].__file__).resolve()
        require(path == (root / relative_path).resolve() and
                hashlib.sha256(path.read_bytes()).hexdigest() == plan["input_hashes"].get(relative_path),
                "Live helper differs from frozen input: " + relative_path)


def dossier(case):
    """Whitelist redacted source fields; never emit source IDs or target answers."""
    dates = [case[key] for key in ("first_source_date", "history_date", "target_date")]
    require(all(isinstance(value, str) for value in dates), "Exact source date strings required")
    parsed = [datetime.fromisoformat(value) for value in dates]
    require(parsed[0] < parsed[1] < parsed[2], "Source chronology changed")
    others = sorted({turn["speaker"] for turn in case["history"] + case["context"]} - {case["speaker"]})
    roles = {speaker: f"Colleague {index + 1}" for index, speaker in enumerate(others)}
    roles[case["speaker"]] = "Participant"

    def text(turn):
        require(isinstance(turn["text"], str) and turn["text"].strip(), "Empty source text")
        return turn["text"]

    lines = ["Evaluate the Participant's next natural turn in this professional conversation.",
             "Many appropriate continuations are possible; no unique reference answer is supplied.",
             "Recording dates below retain their original local ISO form; the source does not establish a timezone.",
             "Earlier self-reports are dated evidence, not externally verified or necessarily current biography.",
             "", "CURRENT CONVERSATION — recorded " + case["target_date"]]
    lines.extend(f"[C{index}] {roles[turn['speaker']]}: {text(turn)}"
                 for index, turn in enumerate(case["context"], 1))
    require(case["style_examples"], "Authentic style examples required")
    lines += ["", "EARLIER PARTICIPANT EXPRESSION EXAMPLES — recorded " + case["first_source_date"]]
    for index, turn in enumerate(case["style_examples"], 1):
        require(turn["speaker"] == case["speaker"], "Style example belongs to another speaker")
        lines.append(f"[S{index}] Participant: {text(turn)}")
    require(case["structured_facts"], "Source-bound professional self-report required")
    lines += ["", "EARLIER PROFESSIONAL SELF-REPORTS"]
    original_quotes = {turn["text"] for turn in case["facts_source_selfreports_not_world_verified"]}
    for index, fact in enumerate(case["structured_facts"], 1):
        require(fact["source_date"] == case["first_source_date"] and fact["source_quote"] in original_quotes,
                "Factual statement lost its exact source binding")
        require(isinstance(fact["statement"], str) and fact["statement"].strip(), "Empty structured fact")
        lines += [f"[F{index}] Recorded {fact['source_date']}; historical self-report: {fact['statement']}",
                  "Exact source excerpt: " + fact["source_quote"]]
    lines += ["", "EARLIER CONVERSATION EVIDENCE — recorded " + case["history_date"]]
    lines.extend(f"[H{index}] {roles[turn['speaker']]}: {text(turn)}"
                 for index, turn in enumerate(case["history"], 1))
    rendered = "\n".join(lines)
    reference = case["reference_continuation_not_for_prompt"]["text"].strip()
    require(reference and reference.casefold() not in rendered.casefold(), "Reference continuation leaked into dossier")
    return rendered


def case_lookup(plan):
    """Match the already-frozen registration's speaker/context sorting exactly."""
    by_speaker = defaultdict(list)
    for case in plan["cases"]:
        by_speaker[case["speaker"]].append(case)
    result = {}
    for speaker in sorted(by_speaker):
        cases = sorted(by_speaker[speaker], key=lambda case: (
            case["target_date"], case["target_meeting"], case["reference_continuation_not_for_prompt"]["start"]))
        require(len(cases) == 2, "Frozen registration requires two contexts per speaker")
        for index, case in enumerate(cases, 1):
            result[f"{speaker}_context{index}"] = case
    require(set(result) == {row["case_id"] for row in plan["requests"]}, "Material/registered case mismatch")
    require(all(result[row["case_id"]]["speaker"] == row["speaker_id"] for row in plan["requests"]),
            "Registered case/speaker mismatch")
    return result


def sealed_records(batch, manifest_sha256, execution_receipt_sha256):
    """Full existing raw/HTTP audit precedes any review-package construction."""
    require(batch in ("development", "validation"), "Unknown batch")
    receipt_path = PUBLIC / f"{batch}_execution_receipt_v1.json"
    manifest_path = PRIVATE / batch / "frozen_manifest_v1.json"
    manifest_bytes = manifest_path.read_bytes()
    require(hashlib.sha256(manifest_bytes).hexdigest() == manifest_sha256, "Frozen manifest changed")
    verify_live_helpers(json.loads(manifest_bytes))
    require(receipt_path.is_file() and review.prior.sha256(receipt_path) == execution_receipt_sha256,
            "A sealed execution receipt with an externally verified hash is required")
    receipt = review.prior.load_json_bytes(receipt_path.read_bytes())
    require(receipt["batch"] == batch and receipt["manifest_sha256"] == manifest_sha256 and
            receipt["status"] in ("PASS", "PARTIAL", "BLOCKED"), "Execution receipt scope/hash mismatch")
    require(review.prior.sha256(manifest_path) == manifest_sha256, "Frozen manifest changed")
    plan, audited_receipt, _, _, _ = reproduction.audit_run(batch)
    require(audited_receipt == receipt and plan["batch"] == batch and
            plan == review.prior.load_json_bytes(manifest_path.read_bytes()), "Independent source audit binding mismatch")
    require(review.prior.sha256(Path(review.__file__)) == FROZEN_ADAPTER_SHA256 and
            review.prior.sha256(review.RUBRIC) == FROZEN_RUBRIC_SHA256, "Frozen review adapter/rubric changed")
    require(plan["input_hashes"].get("tools/english_sfh_review_v1.py") == FROZEN_ADAPTER_SHA256 and
            plan["input_hashes"].get("docs/validation/p1/english_real_speaker_stage_v1/human_review_rubric_v1.json") == FROZEN_RUBRIC_SHA256,
            "Review instrument was not prospectively bound")
    folder = Path(receipt["run_directory"]).resolve()
    require(folder.is_relative_to((PRIVATE / batch / "runs").resolve()), "Run directory escaped this batch")
    events = reproduction.read_events(folder)
    require(events and events[-1]["kind"] == "run_finished" and
            events[-1]["event_hash"] == receipt["terminal_event_sha256"], "Journal is not sealed at the bound tail")
    raw = [event["data"] for event in events if event["kind"] == "english_sfh_raw"]
    by_id = {row["request_id"]: row["response"]["content"] for row in raw}
    allocated = {row["request_id"] for row in plan["requests"]}
    require(len(raw) == len(by_id) == receipt["responses"] and set(by_id) <= allocated and
            len(allocated) == len(plan["requests"]), "Raw response count/identity mismatch")
    require(all(isinstance(value, str) for value in by_id.values()), "Raw response content must remain text")
    cases = case_lookup(plan)
    dossiers = {key: dossier(case) for key, case in cases.items()}
    records = [{"request_id": row["request_id"], "case_id": row["case_id"],
                "dossier": dossiers[row["case_id"]], "response": by_id.get(row["request_id"])}
               for row in plan["requests"]]
    require(review.prior.sha256(receipt_path) == execution_receipt_sha256, "Receipt changed during audit")
    return records, receipt


def prepare(batch, manifest_sha256, execution_receipt_sha256):
    public_receipt = PUBLIC / f"{batch}_review_delivery_receipt_v1.json"
    require(not public_receipt.exists(), "Delivery already recorded; no rebuild or overwrite")
    records, execution = sealed_records(batch, manifest_sha256, execution_receipt_sha256)
    delivery = DELIVERIES / f"english_sfh_{batch}_v1"
    analyst = PRIVATE / "review" / batch
    receipt_path = analyst / "package_receipt_v1.json"
    review.build_package(records, delivery, analyst / "protected_mapping_v1.json", receipt_path,
                         sealed_source_sha256=execution_receipt_sha256, dossiers_redacted=True)
    package = review.load_package(delivery, receipt_path)
    blank = review.validate_submission(package, (delivery / "REVIEW.csv").read_bytes())
    require(not blank["errors"] and blank["counts"]["not_started"] == len(records), "Delivery is not entirely blank")
    report = {"schema": "english_sfh_review_delivery_v1", "batch": batch,
              "status": "BLANK_FIXED_PACKAGE_NOT_HUMAN_REVIEWED", "records": len(records),
              "generated_outcomes": sum(row["response"] is not None for row in records),
              "missing_outcomes": sum(row["response"] is None for row in records),
              "human_labels_created": 0, "mapping_in_delivery": False,
              "source_manifest_sha256": manifest_sha256, "execution_receipt_sha256": execution_receipt_sha256,
              "terminal_event_sha256": execution["terminal_event_sha256"],
              "adapter_sha256": FROZEN_ADAPTER_SHA256, "rubric_sha256": FROZEN_RUBRIC_SHA256,
              "bridge_sha256": review.prior.sha256(Path(__file__)),
              "bridge_test_sha256": review.prior.sha256(Path("tests/test_english_sfh_review_delivery_v1.py")),
              "private_package_receipt_sha256": review.prior.sha256(receipt_path),
              "fixed_delivery_file_sha256": package["receipt"]["files"],
              "limits": "Source-relative PI review remains pending; no independent reviewer, double-blind, inter-rater, semantic benefit or validated fidelity claim. No response is rewritten or excluded. Private mappings and participant material are not public artifacts."}
    review.prior.write_exclusive(public_receipt, review.json_bytes(report))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", choices=("development", "validation"), required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--execution-receipt-sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.batch, args.manifest_sha256, args.execution_receipt_sha256), indent=2))
