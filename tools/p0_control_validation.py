"""Append-only P0 control investigation; no model generations or P1 execution."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess

from personaslm.journal import atomic_json, utc_now
from personaslm.conditioning import build_prompt, P0_CONDITIONS
from personaslm.control_candidates import (DEVELOPMENT_CASES, VERSION, PROMPT_VERSION,
    candidates, prompt as candidate_prompt, select_match)
from personaslm.fixtures import load_cases
from personaslm.provenance import fingerprint

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "results/p0_neutral_validity/20261012T195226"
SUBMISSION = ROOT / "docs/validation/PersonaSLM_P0_PreReview_Completed.csv"
FREEZE = ROOT / "results/p0_validation/20261012T164648/prompts_frozen_v3.json"
PUBLIC = ROOT / "docs/validation"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(path, value)


def prepare():
    SESSION.mkdir(parents=True, exist_ok=False)
    for name in ("engineering", "materials", "experiments", "literature"):
        (SESSION / name).mkdir()
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    protected = {name: digest(ROOT / name) for name in tracked if name and (ROOT / name).is_file()}
    journals = {}
    for manifest in sorted((ROOT / "results").rglob("manifest.json")):
        if not (manifest.parent / "events").is_dir():
            continue
        files = [manifest, *sorted((manifest.parent / "events").glob("*.json"))]
        if (manifest.parent / "server.log").is_file():
            files.append(manifest.parent / "server.log")
        journals[manifest.parent.relative_to(ROOT).as_posix()] = {
            p.relative_to(manifest.parent).as_posix(): digest(p) for p in files}
    original = SESSION / "materials/researcher_submission_received.csv"
    with original.open("xb") as out:
        out.write(SUBMISSION.read_bytes())
    inventory = {"created_utc": utc_now(), "git_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT, text=True),
        "tracked_files": protected, "historical_journals": journals,
        "submission_path": SUBMISSION.relative_to(ROOT).as_posix(), "submission_sha256": digest(SUBMISSION),
        "history_note": "Earlier read-only inspections used tool transcript timestamps; no per-command timestamps are invented."}
    save(SESSION / "materials/baseline.json", inventory)
    inspect_submission()
    print(json.dumps({"session": SESSION.relative_to(ROOT).as_posix(), "historical_journals": len(journals),
                      "tracked_files": len(protected), "submission_sha256": digest(SUBMISSION)}))


def inspect_submission():
    with SUBMISSION.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    labels = ["answer_leakage", "additional_factual_information", "contradictory_information",
              "temporal_interference", "unintended_linguistic_style", "semantic_neutrality",
              "control_suitability", "speaker_referent_ambiguity", "reviewer_id", "reviewed_utc", "assessment_source"]
    summary = {"created_utc": utc_now(), "extension": SUBMISSION.suffix, "rows": len(rows),
        "counts": {k: dict(Counter(r[k] for r in rows)) for k in labels},
        "all_rows": rows}
    save(SESSION / "materials/submission_inspection.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "all_rows"}, indent=2))


def material_freeze():
    from dataclasses import asdict
    from personaslm.reproducibility import source_snapshot
    cases_path = ROOT / "data/synthetic/p0_cases.jsonl"
    cases = load_cases(cases_path)
    frozen = read(FREEZE)
    audited = {(r["case_id"], r["condition"]): r for r in read(PUBLIC / "P0_case_audit.json")["cases"]}
    reconstructed = []
    for case in cases:
        for condition in P0_CONDITIONS:
            saved = frozen["prompts"][case.case_id].get(condition)
            override = saved.get("neutral_text") if saved and condition.startswith("N_") else None
            built = build_prompt(case, condition, neutral_override=override)
            observed = audited[case.case_id, condition]
            # The full prompt in the audited historical artifact is a string.
            old_prompt = observed["prompt"]
            if isinstance(old_prompt, dict):
                old_prompt = old_prompt["text"]
            if built.text != old_prompt or (saved and asdict(built)["text"] != saved["prompt"]["text"]):
                raise ValueError(f"Historical prompt reconstruction mismatch: {case.case_id} {condition}")
            ids = observed["generation_request"]["prompt"]
            if saved and ids != saved["token_ids"]:
                raise ValueError("Frozen and historical input IDs differ")
            reconstructed.append({"case_id": case.case_id, "condition_id": condition,
                "speaker_identity": case.persona_id, "question": case.question,
                "facts": [asdict(f) for f in case.facts], "evaluation_date": str(case.evaluation_date),
                "style_intervention": case.style_only, "historical_intervention": case.history_dialogue,
                "prompt": asdict(built), "prompt_sha256": text_hash(built.text),
                "trusted_evidence_hash": text_hash(built.evidence_block), "input_token_ids": ids,
                "input_token_count": len(ids), "prompt_template_version": "transcript_base_v1",
                "reconstructed_exactly": True})
    old = {"created_utc": utc_now(), "dataset_sha256": digest(cases_path), "dataset_version": "p0_synthetic_v1",
           "source_freeze_sha256": digest(FREEZE), "audit_source_sha256": digest(PUBLIC / "P0_case_audit.json"),
           "records": reconstructed, "selection": "All 20 historical cases, all five original conditions",
           "scope": "Saved inputs only. No rescoring or generation."}
    save(PUBLIC / "P0_control_reconstruction_v1.json", old)
    pairs = []
    for case in DEVELOPMENT_CASES:
        for reference, neutral in (("C1", "N_style"), ("C3", "N_history")):
            ref = candidate_prompt(case, reference)
            attempts = [{"candidate_index": i, "neutral_text": text,
                "prompt": candidate_prompt(case, neutral, text)} for i, text in enumerate(candidates(case, neutral))]
            pairs.append({"case_id": case["case_id"], "reference_condition": reference,
                "neutral_condition": neutral, "reference_prompt": ref, "candidates": attempts})
    candidate = {"created_utc": utc_now(), "candidate_version": VERSION, "prompt_template_version": PROMPT_VERSION,
        "scope": "DEVELOPMENT ONLY; not approved interventions or a P1 dataset",
        "selection": "All three new invented development cases; all 36 style and 8 history candidates per case",
        "selection_rule": "Enumerate all frozen candidates, choose first exact match or smallest absolute difference; tolerance zero",
        "semantic_limitations": ["Conversation metadiscourse may cue a style even without formatting repetition",
            "History non-disclosure replies may cue abstention; no fact-equated format identification",
            "The header change is a separate template intervention and does not repair old experiments"],
        "token_tolerance": 0, "generation_requests_authorized": 0, "development_cases": list(DEVELOPMENT_CASES), "pairs": pairs}
    candidate["freeze_id"] = fingerprint(candidate)
    save(PUBLIC / "P0_control_candidate_freeze_v1.json", candidate)
    save(SESSION / "materials/source_freeze.json", source_snapshot(cases_path))
    save(SESSION / "materials/input_hashes.json", {"created_utc": utc_now(),
        "files": {p.relative_to(ROOT).as_posix(): digest(p) for p in (SUBMISSION, FREEZE, cases_path,
            PUBLIC / "P0_control_reconstruction_v1.json", PUBLIC / "P0_control_candidate_freeze_v1.json")}})
    print(json.dumps({"historical_prompts_reconstructed": len(reconstructed), "candidate_pairs": len(pairs),
        "candidate_prompts": sum(len(p["candidates"]) for p in pairs), "freeze_id": candidate["freeze_id"]}))


def attestation():
    value = {"version": "researcher_verified_annotation_v1", "recorded_utc": utc_now(),
        "reviewer_id": "Yaxin_ZHENG", "review_type": "researcher_human_review",
        "confirmed_all_records_reviewed": True, "assistance": "AI-assisted human review", "blind_review": False,
        "human_review_time": None, "source": "Researcher instruction in the active task; original review date/time not supplied",
        "statement": "Yaxin ZHENG personally reviewed all 40 neutral-control records and manually corrected some preliminary judgments.",
        "submission_sha256": digest(SUBMISSION),
        "metadata_handling": "Source CSV retained byte-for-byte. Task-level confirmation supplies reviewer identity despite stale/blank per-row metadata. No second reviewer or agreement is inferred."}
    save(SESSION / "materials/researcher_attestation.json", value)
    print(json.dumps(value))


def updated_review():
    from personaslm.researcher_review import import_attested_review, read_submission
    incoming = PUBLIC / "PersonaSLM_P0_Researcher_Reviewed_v3.csv"
    # Preserve the received earlier CSV even if the researcher replaces/removes
    # its original working-copy path while delivering the corrected version.
    prior = SESSION / "materials/researcher_submission_received.csv"
    archived_public = PUBLIC / "P0_received_review_source_v1.csv"
    with archived_public.open("xb") as handle:
        handle.write(prior.read_bytes())
    with (SESSION / "materials/researcher_reviewed_v3_received.csv").open("xb") as handle:
        handle.write(incoming.read_bytes())
    attested = read(SESSION / "materials/researcher_attestation.json")
    attested.update({"recorded_utc": utc_now(), "submission_sha256": digest(incoming),
        "source": "Researcher supplied PersonaSLM_P0_Researcher_Reviewed_v3.csv after confirming personal review of all 40 records",
        "supersedes_submission_sha256": digest(prior), "registration_revision": 2,
        "prior_registration": "docs/validation/P0_researcher_verified_annotation_v1.json",
        "initial_independent_judgment": "Claimed by researcher-supplied metadata; no separate initial-pass artifact supplied",
        "review_process": "Researcher-attested independent first pass, then consultation of preliminary AI judgments and possible revision; final review is not blind"})
    attestation_path = SESSION / "materials/researcher_attestation_revision2.json"
    save(attestation_path, attested)
    result = import_attested_review(PUBLIC / "P0_neutral_annotation_form_v3.json", incoming, FREEZE,
        attestation_path, PUBLIC / "P0_researcher_verified_annotation_v1_revision2.json", archived_public)
    _, old = read_submission(prior)
    _, current = read_submission(incoming)
    old_by_key = {(r["case_id"], r["condition_id"]):r for r in old}
    field_changes = []
    for row in current:
        before = old_by_key[row["case_id"], row["condition_id"]]
        for key in sorted(set(before) | set(row)):
            if before.get(key) != row.get(key):
                field_changes.append({"case_id": row["case_id"], "condition_id": row["condition_id"],
                    "field": key, "before": before.get(key), "after": row.get(key)})
    compared = {"created_utc": utc_now(), "prior_sha256": digest(prior), "reviewed_sha256": digest(incoming),
        "prior_role": "Earlier received source already attested as researcher-verified; not asserted to be untouched AI original",
        "latest_role": "Researcher-supplied final v3 source",
        "judgment_comparison": result["version_comparison"], "all_field_changes": field_changes,
        "changed_fields": dict(Counter(r["field"] for r in field_changes)),
        "records_with_any_field_change": len({(r["case_id"], r["condition_id"]) for r in field_changes}),
        "initial_AI_preliminary_csv_available": False, "initial_independent_human_pass_available": False,
        "initial_AI_to_final_changed_judgments": None,
        "unavailable_intermediate_sha256": sorted({r["source_review_file_sha256"] for r in current}),
        "limitation": "No inference about edits before the earliest saved version; preserve researcher process claims without fabricating missing versions."}
    save(PUBLIC / "P0_researcher_annotation_version_comparison_v1.json", compared)
    print(json.dumps({"annotation_count": result["annotation_count"], "latest_sha256": digest(incoming),
        "changed_judgments_between_available_versions": result["version_comparison"]["changed_judgments"],
        "changed_metadata_records": compared["records_with_any_field_change"],
        "researcher_control_counts": result["researcher_control_counts"], "derived_counts": result["derived_dimension_counts"]}, indent=2))


def resolution_packet():
    from personaslm.control_resolution_review import VERSION as REVIEW_VERSION, EDITABLE, validate_resolution
    material = read(PUBLIC / "P0_neutral_annotation_form_v3.json")
    reconstructed = {(r["case_id"], r["condition_id"]):r for r in read(PUBLIC / "P0_control_reconstruction_v1.json")["records"]}
    items = []
    for source in material["items"]:
        row = {k:v for k,v in source.items() if k not in EDITABLE}
        row["form_version"] = REVIEW_VERSION
        ref = reconstructed[source["case_id"], source["reference_condition"]]
        row["reference_conditioning_text"] = ref["prompt"]["additions"][0]
        row["reference_prompt_sha256"] = ref["prompt_sha256"]
        row["c0_prompt_sha256"] = reconstructed[source["case_id"], "C0"]["prompt_sha256"]
        row.update({k:"" for k in EDITABLE})
        items.append(row)
    packet = {"version": REVIEW_VERSION, "created_utc": utc_now(), "items": items,
        "purpose": "Follow-up resolution or independent replication; original researcher review is already complete",
        "blinding": "Unblinded source conditions and reference material; no model outputs or previous judgments included",
        "language": "en", "human_followup_reviews_completed": 0,
        "source_sha256": digest(PUBLIC / "P0_researcher_verified_annotation_v1_revision2.json")}
    packet["packet_id"] = fingerprint(packet)
    destination = PUBLIC / "P0_neutral_resolution_form_v1"
    save(destination.with_suffix(".json"), packet)
    with destination.with_suffix(".csv").open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(items[0]))
        writer.writeheader()
        writer.writerows(items)
    with destination.with_suffix(".csv").open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames, list(reader)
    assert validate_resolution(packet, rows, fields) == []
    print(json.dumps({"resolution_items": len(rows), "followup_ratings": 0, "original_human_reviews_completed": 40}))


def delivery_audit():
    from personaslm.journal import read_events
    baseline = read(SESSION / "materials/baseline.json")
    prior, chains = [], []
    for name, expected in baseline["historical_journals"].items():
        directory = ROOT / name
        current = {p:digest(directory / p) for p in expected}
        if current != expected:
            raise ValueError("Historical journal changed: " + name)
        prior.append({"run_directory": name, "files_verified": len(current), "unchanged": True})
    for manifest in sorted((ROOT / "results").rglob("manifest.json")):
        if (manifest.parent / "events").is_dir():
            events = read_events(manifest.parent)
            chains.append({"run_directory": manifest.parent.relative_to(ROOT).as_posix(),
                "events": len(events), "chain_valid": True,
                "terminal_event": events[-1]["kind"] if events else None})
    protected = {name: digest(ROOT / name) == expected for name, expected in baseline["tracked_files"].items()
        if name.startswith(("src/", "tests/", "data/", "docs/validation/")) or name in (
            "docs/research_protocol_v1.1.md", "docs/research_protocol_v1.1_language_scope_addendum.md",
            "docs/P0_response_status_policy_v1.md", "docs/P0_evaluation_policy_v1.md", "AGENTS.md")}
    if not all(protected.values()):
        raise ValueError("Frozen source/data/evidence changed")
    assert digest(SESSION / "materials/researcher_submission_received.csv") == baseline["submission_sha256"]
    assert digest(PUBLIC / "P0_received_review_source_v1.csv") == baseline["submission_sha256"]
    latest = PUBLIC / "PersonaSLM_P0_Researcher_Reviewed_v3.csv"
    assert digest(latest) == digest(SESSION / "materials/researcher_reviewed_v3_received.csv")
    # Replay validation only: no reviewer labels, missing times or history are supplied by software.
    from personaslm.researcher_review import import_attested_review
    replay = import_attested_review(PUBLIC / "P0_neutral_annotation_form_v3.json", latest, FREEZE,
        SESSION / "materials/researcher_attestation_revision2.json", SESSION / "engineering/review_reconstruction.json",
        PUBLIC / "P0_received_review_source_v1.csv")
    registered = read(PUBLIC / "P0_researcher_verified_annotation_v1_revision2.json")
    replay_equal = {k:v for k,v in replay.items() if k != "registered_utc"} == {
        k:v for k,v in registered.items() if k != "registered_utc"}
    if not replay_equal:
        raise ValueError("Annotation import reconstruction differs")
    current_names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    needle = "".join(map(chr, (67, 111, 100, 101, 120))).lower()
    bad, inspected, hashes = [], [], {}
    excluded = ("data/private/", "models/", "bin/", ".venv/", "results/", ".git/")
    for name in sorted(set(current_names)):
        path = ROOT / name
        if not name or name.startswith(excluded) or not path.is_file():
            continue
        payload = path.read_bytes()
        if b"\0" in payload:
            continue
        try:
            text = payload.decode("utf-8-sig")
        except UnicodeDecodeError:
            continue
        inspected.append(name)
        hashes[name] = hashlib.sha256(payload).hexdigest()
        if needle in text.lower():
            bad.append(name)
    if bad:
        raise ValueError("Non-neutral development attribution in current text: " + str(bad))
    new_json = [ROOT / n for n in current_names if n.startswith("docs/validation/") and n.endswith(".json")
                and n not in baseline["tracked_files"]]
    for path in new_json:
        read(path)
        if str(ROOT).replace("\\", "/").lower() in path.read_text(encoding="utf-8").replace("\\", "/").lower():
            raise ValueError("Machine path in public JSON")
    value = {"created_utc": utc_now(), "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT, text=True),
        "historical_journals": prior, "all_journal_chains": chains,
        "protected_files_unchanged": protected, "annotation_reconstruction_equal": replay_equal,
        "received_versions_preserved": True, "current_source_files_searched": len(inspected),
        "development_product_reference_matches": bad, "new_json_files_validated": len(new_json),
        "file_hashes_at_audit": hashes,
        "scope": "Read-only integrity and input/annotation replay. No model generations, no historical rescoring.",
        "test_record_sha256": digest(SESSION / "engineering/full_tests.json")}
    save(PUBLIC / "P0_neutral_validity_delivery_v1.json", value)
    print(json.dumps({"historical_journals_unchanged": len(prior), "all_journal_chains_valid": len(chains),
        "protected_files_unchanged": len(protected), "annotation_reconstruction_equal": replay_equal,
        "source_search_matches": len(bad), "new_json_valid": len(new_json)}, indent=2))


def tokenize_development():
    from personaslm.configuration import RuntimeConfig, preflight
    from personaslm.inference import LlamaClient
    from personaslm.journal import RunJournal, read_events
    from personaslm.reproducibility import source_snapshot
    from personaslm.server import ManagedServer, validate_server_properties
    config_path = ROOT / "configs/p0_runtime.local.json"
    config = RuntimeConfig.load(config_path)
    freeze_path = PUBLIC / "P0_control_candidate_freeze_v1.json"
    frozen = read(freeze_path)
    assert fingerprint({k: v for k, v in frozen.items() if k != "freeze_id"}) == frozen["freeze_id"]
    checked = preflight(config)
    expected_server = "71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846"
    if checked["status"] != "PASS" or checked["server"]["sha256"] != expected_server:
        raise ValueError("Pinned files failed preflight")
    journal = RunJournal(SESSION / "experiments", {"scope": "P0 tokenizer-only candidate development; no generation",
        "configuration": config.as_dict(), "config_sha256": digest(config_path), "preflight": checked,
        "candidate_freeze_sha256": digest(freeze_path), "candidate_freeze": frozen,
        "source_snapshot": source_snapshot(ROOT / "data/synthetic/p0_cases.jsonl"),
        "prompt_versions": ["transcript_base_v1", PROMPT_VERSION], "generation_parameters": None,
        "generation_note": "No completion endpoint calls; seed and generation budget are in inherited configuration but unused."})
    historical, pairs = [], []
    try:
        with ManagedServer(config, journal) as server:
            client = LlamaClient(config.endpoint, timeout=config.timeout, audit=journal.write)
            binding = validate_server_properties(client.request("/props"), config)
            journal.write("tokenizer_binding", binding)
            for record in read(PUBLIC / "P0_control_reconstruction_v1.json")["records"]:
                ids = client.tokenize(record["prompt"]["text"])
                row = {"case_id": record["case_id"], "condition_id": record["condition_id"],
                    "prompt_sha256": record["prompt_sha256"], "input_token_count": len(ids),
                    "token_ids": ids, "historical_ids_match": ids == record["input_token_ids"]}
                historical.append(row)
                journal.write("historical_tokenizer_check", row)
            for pair in frozen["pairs"]:
                reference_ids = client.tokenize(pair["reference_prompt"]["text"])
                attempts = []
                for attempt in pair["candidates"]:
                    ids = client.tokenize(attempt["prompt"]["text"])
                    row = {**attempt, "prompt_sha256": text_hash(attempt["prompt"]["text"]),
                        "token_ids": ids, "token_count": len(ids), "token_difference": len(ids)-len(reference_ids)}
                    attempts.append(row)
                    journal.write("candidate_tokenized", {"case_id": pair["case_id"], "neutral_condition": pair["neutral_condition"], **row})
                result = {k: pair[k] for k in ("case_id", "reference_condition", "neutral_condition")}
                result.update({"reference_token_count": len(reference_ids), "reference_token_ids": reference_ids,
                    "reference_prompt_sha256": text_hash(pair["reference_prompt"]["text"]),
                    "trusted_evidence_hash": text_hash(pair["reference_prompt"]["trusted_evidence"]),
                    "prompt_template_version": PROMPT_VERSION, "matching": select_match(attempts), "attempts": attempts})
                pairs.append(result)
                journal.write("pair_result", result)
            server.assert_running()
        after = preflight(config)
        if checked != after:
            raise ValueError("Pinned files changed during tokenizer run")
        journal.write("postflight", after)
        all_ids = all(row["historical_ids_match"] for row in historical)
        journal.finish("PASS" if all_ids else "FAILED", scope="tokenizer execution, not semantic control acceptance",
                       completion_requests=0, historical_ids_match=all_ids)
    except BaseException as exc:
        journal.write("error", {"type": type(exc).__name__, "message": str(exc)})
        raise
    events = read_events(journal.directory)
    completion_calls = sum(e["kind"] == "http_request" and e["data"].get("route") == "/completion" for e in events)
    assert completion_calls == 0
    result = {"created_utc": utc_now(), "run_directory": journal.directory.relative_to(ROOT).as_posix(),
        "candidate_version": VERSION, "freeze_sha256": digest(freeze_path), "model_sha256": checked["model"]["sha256"],
        "server_sha256": checked["server"]["sha256"], "backend_binding": binding,
        "tokenizer_options": {"add_special": True, "parse_special": False, "with_pieces": False},
        "journal_events": len(events), "journal_chain_valid": True, "completion_requests": completion_calls,
        "historical": historical, "pairs": pairs, "matching_counts": dict(Counter(p["matching"]["status"] for p in pairs)),
        "semantic_status": "UNREVIEWED; candidates remain DEVELOPMENT ONLY"}
    save(PUBLIC / "P0_control_tokenizer_validation_v1.json", result)
    print(json.dumps({"run_directory": result["run_directory"], "historical_prompts": len(historical),
        "historical_ids_match": all_ids, "matches": [{k:p[k] for k in ("case_id", "neutral_condition", "matching")} for p in pairs],
        "completion_requests": completion_calls, "journal_events": len(events)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "freeze", "attestation", "tokenize", "updated-review", "resolution-packet", "delivery"])
    args = parser.parse_args()
    if args.stage == "prepare":
        prepare()
    elif args.stage == "freeze":
        material_freeze()
    elif args.stage == "attestation":
        attestation()
    elif args.stage == "tokenize":
        tokenize_development()
    elif args.stage == "updated-review":
        updated_review()
    elif args.stage == "resolution-packet":
        resolution_packet()
    elif args.stage == "delivery":
        delivery_audit()
