"""Deliver the unchanged 100-request English grid from its two sealed journals."""

import argparse
import json
from pathlib import Path
import sys

import english_sfh_combined_v1 as combined
import english_sfh_review_delivery_v1 as delivery

review = delivery.review
resume = combined.resume
PUBLIC, PRIVATE = delivery.PUBLIC, delivery.PRIVATE
DELIVERY_BRIDGE_SHA = "08a9c443d8a03c08cf7a78e4de3d1a9cb70b1b2eeef0bc93746e93c3f427dc04"
require, sha = delivery.require, review.prior.sha256


def verify_helpers(parent, suffix):
    """Check the actual imported source closure before calling its audit helpers."""
    root = Path(__file__).resolve().parents[1]
    expected = {}
    for plan in (parent, suffix):
        for field in ("source_hashes", "input_hashes"):
            for name, digest in plan[field].items():
                require(name not in expected or expected[name] == digest, "Conflicting frozen helper binding")
                expected[name] = digest
    bridge_path = "tools/english_sfh_review_delivery_v1.py"
    require(bridge_path not in expected or expected[bridge_path] == DELIVERY_BRIDGE_SHA,
            "Conflicting delivery bridge binding")
    expected[bridge_path] = DELIVERY_BRIDGE_SHA
    loader = Path(combined.original.shared.__file__).resolve()
    loader_relative = loader.relative_to(root).as_posix()
    require(sha(loader) == expected.get(loader_relative), "Changed source-closure helper")
    paths = combined.original.shared.runtime_python_dependency_paths(
        [Path(combined.__file__), Path(delivery.__file__)])
    for path in paths:
        path = path.resolve()
        relative = path.relative_to(root)
        require(sha(path) == expected.get(relative.as_posix()), "Changed live helper: " + relative.as_posix())
        parts = relative.with_suffix("").parts
        module_name = parts[-1] if parts[0] == "tools" else ".".join(parts[1:])
        if module_name.endswith(".__init__"):
            module_name = module_name[:-9]
        module = sys.modules.get(module_name)
        require(module is None or Path(module.__file__).resolve() == path,
                "Imported helper path differs from frozen source")
    delivery.verify_live_helpers(parent)
    require(sha(review.RUBRIC) == delivery.FROZEN_RUBRIC_SHA256, "Frozen rubric changed")


def checked_json(path, expected_sha):
    content = Path(path).read_bytes()
    require(review.prior.sha256_bytes(content) == expected_sha, "Externally bound artifact changed")
    return review.prior.load_json_bytes(content)


def sealed_records(analysis_sha, reproduction_sha):
    analysis_path = PUBLIC / "development_combined_analysis_v1.json"
    reproduction_path = PUBLIC / "development_combined_independent_reproduction_v1.json"
    analysis = checked_json(analysis_path, analysis_sha)
    reproduced = checked_json(reproduction_path, reproduction_sha)
    bindings = analysis["bindings"]
    require(bindings["original_manifest_sha256"] == resume.PARENT_SHA and
            bindings["original_partial_receipt_sha256"] == resume.RECEIPT_SHA,
            "Original prefix binding changed")
    parent = checked_json(resume.PARENT_MANIFEST, resume.PARENT_SHA)
    suffix = checked_json(resume.MANIFEST, bindings["suffix_manifest_sha256"])
    verify_helpers(parent, suffix)
    require(reproduced["status"] == "PASS" and reproduced["analysis_sha256"] == analysis_sha and
            reproduced["bindings"] == bindings and reproduced["human_labels_created"] == 0,
            "Independent arithmetic receipt binding changed")
    require(sha(PRIVATE / "development_combined_analysis_private_v1.json") == reproduced["private_file_sha256"],
            "Bound private arithmetic rows changed")
    # analyze calls resume.audit_parent and combined.audit_suffix, including raw
    # HTTP equivalence, source snapshots, disjoint attempts and both sealed tails.
    audited = combined.analyze(write=False)
    combined.independent.compare(analysis, audited, "Sealed combined analysis")
    require(analysis["status"] == "COMPLETE_OBSERVATIONS" and
            analysis["allocated"] == analysis["attempts"] == analysis["responses"] == 100 and
            analysis["missing_responses"] == analysis["failed_suffix_calls"] == 0 and
            analysis["new_generation_retries"] == analysis["human_labels_created"] == 0,
            "This delivery requires the complete unchanged 100-response allocation")
    for key in ("responses", "attempts", "cumulative_generations", "cumulative_inference_seconds"):
        combined.independent.compare(reproduced[key], analysis[key], "Reproduction " + key)
    require(suffix["requests"] == parent["requests"][92:] and len(parent["requests"]) == 100,
            "Exact eight-request original suffix required")
    receipts = analysis["run_receipts"]
    require(len(receipts) == 2, "Exactly two sealed run receipts required")
    raw, starts = {}, set()
    for receipt, receipt_name, receipt_hash, tail_key, expected_ids in (
        (receipts[0], "development_execution_receipt_v1.json", resume.RECEIPT_SHA,
         "original_terminal_sha256", {r["request_id"] for r in parent["requests"][:92]}),
        (receipts[1], resume.BATCH + "_execution_receipt_v1.json", bindings["suffix_receipt_sha256"],
         "suffix_terminal_sha256", {r["request_id"] for r in parent["requests"][92:]}),
    ):
        require(checked_json(PUBLIC / receipt_name, receipt_hash) == receipt, "Execution receipt changed")
        events = combined.independent.read_events(Path(receipt["run_directory"]))
        require(events and events[-1]["kind"] == "run_finished" and
                events[-1]["event_hash"] == receipt["terminal_event_sha256"] == bindings[tail_key],
                "Unsealed or changed journal tail")
        run_starts, run_raw = set(), set()
        for event in events:
            if event["kind"] == "english_sfh_started":
                request_id = event["data"]["request_id"]
                require(request_id not in starts, "Repeated cross-journal attempt")
                starts.add(request_id)
                run_starts.add(request_id)
            elif event["kind"] == "english_sfh_raw":
                request_id = event["data"]["request_id"]
                require(request_id not in raw, "Repeated cross-journal response")
                response = event["data"]["response"]["content"]
                require(isinstance(response, str), "Raw response must remain unchanged text")
                raw[request_id] = response
                run_raw.add(request_id)
        require(run_starts == run_raw == expected_ids, "Journal does not match its exact allocation")
    require(len(raw) == len(starts) == 100, "Incomplete combined observations")
    dossiers = {key: delivery.dossier(case) for key, case in delivery.case_lookup(parent).items()}
    records = [{"request_id": row["request_id"], "case_id": row["case_id"],
                "dossier": dossiers[row["case_id"]], "response": raw[row["request_id"]]}
               for row in parent["requests"]]
    require(sha(analysis_path) == analysis_sha and sha(reproduction_path) == reproduction_sha,
            "Evidence changed during delivery audit")
    return records, analysis


def prepare(analysis_sha, reproduction_sha):
    public_path = PUBLIC / "development_review_delivery_receipt_v1.json"
    require(not public_path.exists(), "Delivery already recorded; no overwrite")
    records, analysis = sealed_records(analysis_sha, reproduction_sha)
    directory = delivery.DELIVERIES / "english_sfh_development_v1"
    analyst = PRIVATE / "review" / "development"
    receipt_path = analyst / "package_receipt_v1.json"
    review.build_package(records, directory, analyst / "protected_mapping_v1.json", receipt_path,
                         sealed_source_sha256=analysis_sha, dossiers_redacted=True)
    package = review.load_package(directory, receipt_path)
    blank = review.validate_submission(package, (directory / "REVIEW.csv").read_bytes())
    require(not blank["errors"] and blank["counts"]["not_started"] == 100, "Review is not entirely blank")
    report = {"schema": "english_sfh_combined_review_delivery_v1", "batch": "development",
              "status": "BLANK_FIXED_PACKAGE_NOT_HUMAN_REVIEWED", "records": 100,
              "generated_outcomes": 100, "missing_outcomes": 0, "human_labels_created": 0,
              "mapping_in_delivery": False, "combined_analysis_sha256": analysis_sha,
              "independent_reproduction_receipt_sha256": reproduction_sha,
              "source_bindings": analysis["bindings"],
              "adapter_sha256": delivery.FROZEN_ADAPTER_SHA256, "rubric_sha256": delivery.FROZEN_RUBRIC_SHA256,
              "single_run_delivery_helper_sha256": DELIVERY_BRIDGE_SHA,
              "combined_bridge_sha256": sha(Path(__file__)),
              "combined_bridge_test_sha256": sha(Path("tests/test_english_sfh_combined_review_v1.py")),
              "private_package_receipt_sha256": sha(receipt_path),
              "fixed_delivery_file_sha256": package["receipt"]["files"],
              "limits": "Genuine condition-masked PI review pending; prior exposure must be declared. No independent reviewer, double-blind, inter-rater reliability or semantic benefit is established. Both original journals and their distinct receipts remain unchanged."}
    review.prior.write_exclusive(public_path, review.json_bytes(report))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-sha256", required=True)
    parser.add_argument("--reproduction-sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.analysis_sha256, args.reproduction_sha256), indent=2))
