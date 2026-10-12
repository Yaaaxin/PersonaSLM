"""Append-only tokenizer development, with no completion requests or P1 runs."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess

from personaslm.control_candidates_v2 import CASE_SPECS, FAMILIES, VERSION, PROMPT_VERSION, case_record, pair
from personaslm.control_candidates import select_match
from personaslm.journal import atomic_json, utc_now, RunJournal, read_events
from personaslm.provenance import fingerprint

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "results/p0_control_development_v2/20261012T202741"
PUBLIC = ROOT / "docs/validation"
FREEZE = PUBLIC / "P0_control_candidate_freeze_v2.json"
VALIDATION = PUBLIC / "P0_control_tokenizer_validation_v2.json"
DATA = SESSION / "materials/development_cases_v2.jsonl"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(path, value)


def freeze():
    from personaslm.reproducibility import source_snapshot
    with DATA.open("x", encoding="utf-8", newline="\n") as handle:
        for spec in CASE_SPECS:
            handle.write(json.dumps(case_record(spec), ensure_ascii=False) + "\n")
    value = {"created_utc": utc_now(), "candidate_version": VERSION, "prompt_template_version": PROMPT_VERSION,
             "scope": "DEVELOPMENT ONLY; not approved controls or a P1 dataset", "language": "en",
             "selection": "All three earlier development cases plus three newly authored cases; no outputs consulted",
             "selection_rule": "All frozen candidates evaluated; earliest exact match, otherwise minimum absolute difference then index",
             "token_tolerance": 0, "completion_requests_authorized": 0, "case_specs": CASE_SPECS,
             "dataset_records": [case_record(s) for s in CASE_SPECS], "dataset_sha256": digest(DATA),
             "pairs": [pair(s, family) for s in CASE_SPECS for family in FAMILIES],
             "source_snapshot": source_snapshot(DATA),
             "limitations": ["No claim of semantic neutrality before new human review",
                             "Three earlier development cases are reused for declared engineering repair, not holdout validation",
                             "The original Speaker style profile heading is preserved and can itself cue style",
                             "Generalized old residence is a diagnostic, not a neutral placebo"]}
    value["freeze_id"] = fingerprint(value)
    save(FREEZE, value)
    print(json.dumps({"frozen_utc": value["created_utc"], "freeze_sha256": digest(FREEZE),
                      "pairs": len(value["pairs"]), "candidate_prompts": sum(len(p["candidates"]) for p in value["pairs"])}))


def tokenize():
    from personaslm.configuration import RuntimeConfig, preflight
    from personaslm.inference import LlamaClient
    from personaslm.reproducibility import source_snapshot
    from personaslm.server import ManagedServer, validate_server_properties
    frozen = read(FREEZE)
    if fingerprint({k: v for k, v in frozen.items() if k != "freeze_id"}) != frozen["freeze_id"]:
        raise ValueError("Candidate freeze changed")
    current_source = source_snapshot(DATA)
    if any(current_source[k] != frozen["source_snapshot"][k] for k in ("source_sha256", "tool_sha256", "dataset_utf8")):
        raise ValueError("Source changed after candidate freeze; create a new version")
    config_path = ROOT / "configs/p0_runtime.local.json"
    config = RuntimeConfig.load(config_path)
    checked = preflight(config)
    if checked["status"] != "PASS" or checked["server"]["sha256"] != "71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846":
        raise ValueError("Pinned binary verification failed")
    journal = RunJournal(SESSION / "experiments", {"scope": "P0 tokenizer-only development; no generation",
        "configuration": config.as_dict(), "config_sha256": digest(config_path), "preflight": checked,
        "candidate_freeze_sha256": digest(FREEZE), "candidate_freeze": frozen,
        "source_snapshot": source_snapshot(DATA), "generation_parameters": None,
        "generation_note": "Inherited seed and generation cap are unused; no completions requested"})
    results = []
    try:
        with ManagedServer(config, journal) as server:
            client = LlamaClient(config.endpoint, timeout=config.timeout, audit=journal.write)
            binding = validate_server_properties(client.request("/props"), config)
            journal.write("tokenizer_binding", binding)
            for p in frozen["pairs"]:
                reference = p["reference_prompt"]
                ids_ref = client.tokenize(reference["text"])
                attempts = []
                for candidate in p["candidates"]:
                    built = candidate["prompt"]
                    # Exact single intervention replacement, not a rewritten wrapper.
                    invariant = (reference["text"].replace(reference["additions"][0], "<INTERVENTION>", 1)
                                 == built["text"].replace(built["additions"][0], "<INTERVENTION>", 1)
                                 and reference["evidence_block"] == built["evidence_block"])
                    if not invariant:
                        raise ValueError("Evidence, question, position or wrapper changed")
                    ids = client.tokenize(built["text"])
                    suffix = 0
                    for left, right in zip(reversed(ids_ref), reversed(ids)):
                        if left != right:
                            break
                        suffix += 1
                    row = {**candidate, "prompt_sha256": text_hash(built["text"]), "token_ids": ids,
                           "token_count": len(ids), "token_difference": len(ids) - len(ids_ref),
                           "shared_suffix_tokens": suffix, "wrapper_evidence_question_preserved": invariant}
                    attempts.append(row)
                    journal.write("candidate_tokenized", {"case_id": p["case_id"], "family": p["family"], **row})
                result = {k: p[k] for k in ("case_id", "family", "reference_condition", "render_condition", "reference_prompt", "trusted_evidence", "current_question")}
                result.update({"reference_token_count": len(ids_ref), "reference_token_ids": ids_ref,
                    "reference_prompt_sha256": text_hash(reference["text"]), "trusted_evidence_hash": text_hash(p["trusted_evidence"]),
                    "prompt_template_version": PROMPT_VERSION, "matching": select_match(attempts), "attempts": attempts})
                results.append(result)
                journal.write("pair_result", result)
                print(json.dumps({"case_id": p["case_id"], "family": p["family"], "reference_tokens": len(ids_ref), "matching": result["matching"]}), flush=True)
            server.assert_running()
        after = preflight(config)
        if after != checked:
            raise ValueError("Pinned binary changed")
        journal.write("postflight", after)
        journal.finish("PASS", scope="Tokenizer execution, not semantic acceptance", completion_requests=0)
    except BaseException as exc:
        journal.write("error", {"type": type(exc).__name__, "message": str(exc)})
        raise
    events = read_events(journal.directory)
    http = [e["data"] for e in events if e["kind"] == "http_request"]
    completions = sum(r.get("route") == "/completion" for r in http)
    if completions:
        raise ValueError("Unexpected completion request")
    value = {"created_utc": utc_now(), "run_directory": journal.directory.relative_to(ROOT).as_posix(),
             "candidate_version": VERSION, "freeze_sha256": digest(FREEZE), "model_sha256": checked["model"]["sha256"],
             "server_sha256": checked["server"]["sha256"], "backend_binding": binding,
             "tokenizer_options": {"add_special": True, "parse_special": False, "with_pieces": False},
             "journal_events": len(events), "journal_chain_valid": True, "completion_requests": completions,
             "tokenizer_requests": sum(r.get("route") == "/tokenize" for r in http), "pairs": results,
             "counts_by_family": {f: dict(Counter(p["matching"]["status"] for p in results if p["family"] == f)) for f in FAMILIES},
             "semantic_status": "UNREVIEWED; human judgments for old controls do not apply"}
    save(VALIDATION, value)
    print(json.dumps({k: value[k] for k in ("run_directory", "counts_by_family", "tokenizer_requests", "completion_requests", "journal_events")}, indent=2))


def review_packet():
    from personaslm.control_review_v2 import VERSION as REVIEW_VERSION, EDITABLE, validate_packet
    result = read(VALIDATION)
    items = []
    estimands = {
        "style_generic": "Style profile versus generic discourse text, holding wrapper and total token length fixed",
        "history_format": "Old-residence history versus unrelated coherent dialogue; format and length matched, topic and information differ",
        "history_topic": "Old-residence answer versus residence clarification; question, speaker, date and length matched, pragmatics differ",
        "history_stale_generalized": "Named old residence versus unspecified city residence; a specificity ablation, not a neutral placebo"}
    for p in result["pairs"]:
        if p["matching"]["status"] != "PASS":
            continue
        chosen = p["attempts"][p["matching"]["best_candidate_index"]]
        if not chosen["wrapper_evidence_question_preserved"] or chosen["token_difference"] != 0:
            raise ValueError("Engineering validation must precede new review export")
        item = {"form_version": REVIEW_VERSION, "candidate_version": VERSION, "language": "en",
                "case_id": p["case_id"], "condition_id": p["family"] + "_v2_dev", "family": p["family"],
                "neutral_text": chosen["prompt"]["additions"][0],
                "reference_condition": p["reference_condition"], "reference_conditioning_text": p["reference_prompt"]["additions"][0],
                "trusted_evidence": p["trusted_evidence"], "current_question": p["current_question"],
                "token_count": chosen["token_count"], "reference_token_count": p["reference_token_count"], "token_difference": 0,
                "candidate_index": chosen["candidate_index"], "prompt_template_version": PROMPT_VERSION,
                "prompt_sha256": chosen["prompt_sha256"], "reference_prompt_sha256": p["reference_prompt_sha256"],
                "trusted_evidence_hash": p["trusted_evidence_hash"], "intended_comparison": estimands[p["family"]]}
        item["material_sha256"] = fingerprint(item)
        item.update({field: "" for field in EDITABLE})
        items.append(item)
    packet = {"version": REVIEW_VERSION, "created_utc": utc_now(), "items": items,
              "validation_sha256": digest(VALIDATION), "human_reviews_completed": 0,
              "scope": "New development controls and a clearly labeled non-neutral diagnostic; no inherited annotations",
              "blinding": "Conditions and reference text visible; model outputs absent; not a blind review",
              "excluded_failed_pairs": [{"case_id": p["case_id"], "family": p["family"], "matching": p["matching"]}
                                        for p in result["pairs"] if p["matching"]["status"] != "PASS"]}
    packet["packet_id"] = fingerprint(packet)
    prefix = PUBLIC / "P0_control_development_review_v2"
    save(prefix.with_suffix(".json"), packet)
    with prefix.with_suffix(".csv").open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(items[0]))
        writer.writeheader()
        writer.writerows(items)
    rows = [{k: str(v) for k, v in r.items()} for r in items]
    if validate_packet(packet, rows, list(rows[0])):
        raise ValueError("Blank form unexpectedly contains judgments")
    print(json.dumps({"items": len(items), "human_completed": 0, "failed_pairs_retained": len(packet["excluded_failed_pairs"])}))


def verify():
    baseline = read(SESSION / "materials/baseline.json")
    protected = {n: digest(ROOT / n) == h for n, h in baseline["source_files"].items()
                 if n.startswith(("src/", "tests/", "data/", "docs/validation/")) or n in (
                     "AGENTS.md", "docs/research_protocol_v1.1.md", "docs/research_protocol_v1.1_language_scope_addendum.md")}
    if not all(protected.values()):
        raise ValueError("Historical source/data/annotations changed")
    journals = []
    for name, members in baseline["journals"].items():
        directory = ROOT / name
        current_members = {p.relative_to(directory).as_posix() for p in [directory / "manifest.json", *sorted((directory / "events").glob("*.json"))]}
        if (directory / "server.log").exists():
            current_members.add("server.log")
        if set(members) != current_members or any(digest(directory / p) != h for p, h in members.items()):
            raise ValueError("Historical journal changed")
        events = read_events(directory)
        journals.append({"run_directory": name, "events": len(events), "unchanged": True, "chain_valid": True})
    result = read(VALIDATION)
    new_events = read_events(ROOT / result["run_directory"])
    regenerated = [e["data"] for e in new_events if e["kind"] == "pair_result"]
    if regenerated != result["pairs"]:
        raise ValueError("Published tokenizer observations differ from journal")
    for row in regenerated:
        if select_match(row["attempts"]) != row["matching"]:
            raise ValueError("Matching replay differs")
        for attempt in row["attempts"]:
            if len(attempt["token_ids"]) != attempt["token_count"] or attempt["token_difference"] != attempt["token_count"] - len(row["reference_token_ids"]):
                raise ValueError("Token accounting differs")
            if text_hash(attempt["prompt"]["text"]) != attempt["prompt_sha256"]:
                raise ValueError("Prompt digest differs")
    value = {"created_utc": utc_now(), "protected_files": protected, "historical_journals": journals,
             "new_journal": result["run_directory"], "new_journal_events": len(new_events), "new_journal_chain_valid": True,
             "published_pairs_reconstructed": len(regenerated), "matching_replay_identical": True,
             "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
             "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT, text=True).strip())}
    save(PUBLIC / "P0_control_development_integrity_v2.json", value)
    print(json.dumps({"protected_files_unchanged": len(protected), "historical_journals_unchanged": len(journals), "new_journal_replay": True, "pairs": len(regenerated)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["freeze", "tokenize", "review", "verify"])
    args = parser.parse_args()
    {"freeze": freeze, "tokenize": tokenize, "review": review_packet, "verify": verify}[args.stage]()
