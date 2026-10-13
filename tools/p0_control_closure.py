"""One frozen tokenizer-only cycle; evidence extraction remains offline."""
import argparse
import base64
import csv
import json
from pathlib import Path

from personaslm.control_closure import (
    VERSION, PROMPT_VERSION, STYLE_POOL, frozen_pairs, make_style_review,
    history_evidence, annotation_audit, replacement_preserved, text_hash,
)
from personaslm.control_candidates import select_match
from personaslm.control_decisions import read_csv
from personaslm.control_final_review import validate_review
from personaslm.configuration import RuntimeConfig, preflight
from personaslm.inference import LlamaClient
from personaslm.journal import atomic_json, RunJournal, read_events, utc_now
from personaslm.provenance import fingerprint, sha256
from personaslm.reproducibility import source_snapshot
from personaslm.server import ManagedServer, validate_server_properties

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "results/p0_control_closure/closure_v1"
PUBLIC = ROOT / "docs/validation"
FREEZE = PUBLIC / "P0_style_closure_freeze_v1.json"
VALIDATION = PUBLIC / "P0_style_closure_tokenizer_v1.json"
DATA = SESSION / "materials/development_cases.jsonl"
REG = PUBLIC / "P0_final_control_researcher_registration_v1/registration.json"
MASTER = PUBLIC / "P0_final_control_review_v3.json"
MODEL_SHA = "ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994"
SERVER_SHA = "71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_csv(path, rows, fields=None):
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def freeze():
    old = read(PUBLIC / "P0_control_candidate_freeze_v2.json")
    pairs = frozen_pairs(old, read(MASTER), read(REG))
    with DATA.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(old["source_snapshot"]["dataset_utf8"])
    snapshot = source_snapshot(DATA)
    atomic_json(SESSION / "materials/frozen_source_snapshot.json", snapshot)
    config_file = ROOT / "configs/p0_runtime.local.json"
    value = {"version": VERSION, "created_utc": utc_now(), "prompt_template_version": PROMPT_VERSION,
             "dataset_version": "unchanged_six_control_v2_development_cases", "dataset_sha256": sha256(DATA),
             "dataset_records": old["dataset_records"], "source_registration_sha256": sha256(REG),
             "source_master_sha256": sha256(MASTER), "source_candidate_freeze_sha256": sha256(PUBLIC / "P0_control_candidate_freeze_v2.json"),
             "source_sha256": snapshot["source_sha256"], "tool_sha256": snapshot["tool_sha256"], "git": snapshot["git"],
             "config_file_sha256": sha256(config_file), "configuration": read(config_file),
             "model_sha256": MODEL_SHA, "server_sha256": SERVER_SHA, "token_tolerance": 0,
             "candidate_pool": STYLE_POOL, "candidates_per_case": 12, "case_count": 6,
             "maximum_candidate_requests": 72, "maximum_reference_requests": 6, "completion_requests_authorized": 0,
             "selection": "Evaluate the12 frozen alternatives per case once; earliest exact match. If none, report the smallest absolute difference then earliest index, mark FAILED and do not expand.",
             "rationale": "Replace generic discourse definitions with declarative absence-of-style-metadata statements. Preserve heading and all task input. No specified style preference or personal fact is added.",
             "limitations": ["Header and style-related vocabulary still cue a profile frame", "Explicit absence can influence default behavior; neutrality requires review", "Declarative register is not proven stylistically inert", "This reuses six development cases, not a holdout"],
             "pairs": pairs}
    value["freeze_id"] = fingerprint(value)
    atomic_json(FREEZE, value)
    print(json.dumps({"frozen_candidates": 72, "references": 6, "freeze_sha256": sha256(FREEZE), "model_requests": 0}))


def tokenizer_replay(events, pairs):
    pending, observed = None, []
    for event in events:
        data = event["data"]
        if event["kind"] == "http_request" and data["route"] == "/completion":
            raise ValueError("Answer generation is forbidden")
        if event["kind"] == "http_request" and data["route"] == "/tokenize":
            if pending is not None:
                raise ValueError("Unpaired tokenizer request")
            pending = (event["sequence"], data["payload"])
        if event["kind"] == "http_response" and data["route"] == "/tokenize":
            if pending is None or data["status"] != 200:
                raise ValueError("Invalid tokenizer response")
            native = json.loads(base64.b64decode(data["body_base64"]).decode("utf-8"))
            observed.append((pending[1], native["tokens"], pending[0], event["sequence"]))
            pending = None
    expected = []
    for pair in pairs:
        expected.append((pair["reference_prompt"]["text"], pair["reference_token_ids"]))
        expected.extend((a["prompt"]["text"], a["token_ids"]) for a in pair["attempts"])
    if pending is not None or len(observed) != len(expected) or len(expected) != 78:
        raise ValueError("Unexpected tokenizer request count")
    bindings = []
    for (payload, ids, req, res), (text, expected_ids) in zip(observed, expected):
        if payload != {"content": text, "add_special": True, "parse_special": False, "with_pieces": False} or ids != expected_ids:
            raise ValueError("Published tokens differ from raw native response")
        bindings.append({"prompt_sha256": text_hash(text), "request_event": req, "response_event": res, "token_count": len(ids)})
    return bindings


def tokenize():
    if VALIDATION.exists() or any((SESSION / "experiments").iterdir()):
        raise FileExistsError("This bounded cycle was already attempted; retain it and do not restart automatically")
    frozen = read(FREEZE)
    if fingerprint({k: v for k, v in frozen.items() if k != "freeze_id"}) != frozen["freeze_id"]:
        raise ValueError("Freeze digest differs")
    snapshot = source_snapshot(DATA)
    if any(snapshot[k] != frozen[k] for k in ("source_sha256", "tool_sha256")) or sha256(DATA) != frozen["dataset_sha256"]:
        raise ValueError("Implementation or data changed after freeze")
    config_path = ROOT / "configs/p0_runtime.local.json"
    if sha256(config_path) != frozen["config_file_sha256"]:
        raise ValueError("Runtime configuration changed after freeze")
    config = RuntimeConfig.load(config_path)
    checked = preflight(config)
    if checked["status"] != "PASS" or checked["model"]["sha256"] != MODEL_SHA or checked["server"]["sha256"] != SERVER_SHA:
        raise ValueError("Pinned binary identity check failed")
    journal = RunJournal(SESSION / "experiments", {"scope": "P0 six-style closure; tokenizer only; no answer generation",
        "configuration": config.as_dict(), "config_sha256": sha256(config_path), "preflight": checked,
        "freeze_sha256": sha256(FREEZE), "candidate_freeze": frozen, "source_snapshot": snapshot,
        "generation_parameters": None, "generation_note": "Seed and generation cap are unused configuration, not executed parameters"})
    results = []
    try:
        with ManagedServer(config, journal) as server:
            client = LlamaClient(config.endpoint, timeout=config.timeout, audit=journal.write)
            binding = validate_server_properties(client.request("/props"), config)
            journal.write("tokenizer_binding", binding)
            for pair in frozen["pairs"]:
                reference_ids = client.tokenize(pair["reference_prompt"]["text"])
                attempts = []
                for candidate in pair["candidates"]:
                    if not replacement_preserved(pair["reference_prompt"], candidate["prompt"]):
                        raise ValueError("Frozen input invariant failed")
                    ids = client.tokenize(candidate["prompt"]["text"])
                    attempt = {**candidate, "token_ids": ids, "token_count": len(ids),
                               "token_difference": len(ids)-len(reference_ids), "input_invariants_preserved": True}
                    attempts.append(attempt)
                    journal.write("candidate_tokenized", {"case_id": pair["case_id"], **attempt})
                result = {k: v for k, v in pair.items() if k != "candidates"}
                result.update({"reference_token_ids": reference_ids, "reference_token_count": len(reference_ids),
                               "attempts": attempts, "matching": select_match(attempts)})
                results.append(result)
                journal.write("pair_result", result)
                print(json.dumps({"case_id": pair["case_id"], "reference_tokens": len(reference_ids), "matching": result["matching"]}), flush=True)
            server.assert_running()
        after = preflight(config)
        if after != checked:
            raise ValueError("Binary identity changed during tokenization")
        journal.write("postflight", after)
        journal.finish("PASS", scope="Tokenizer execution only; failed exact matching remains failed", completion_requests=0)
    except BaseException as exc:
        journal.write("error", {"type": type(exc).__name__, "message": str(exc)})
        journal.finish("BLOCKED", scope="Tokenizer-only attempt incomplete", completion_requests=0)
        raise
    events = read_events(journal.directory)
    pairs = [e["data"] for e in events if e["kind"] == "pair_result"]
    if pairs != results:
        raise ValueError("Journal result reconstruction differs")
    bindings = tokenizer_replay(events, pairs)
    passed = sum(p["matching"]["status"] == "PASS" for p in pairs)
    value = {"version": VERSION, "created_utc": utc_now(), "run_directory": journal.directory.relative_to(ROOT).as_posix(),
             "freeze_sha256": sha256(FREEZE), "model_sha256": MODEL_SHA, "backend_sha256": SERVER_SHA,
             "backend_binding": binding, "tokenizer_options": {"add_special": True, "parse_special": False, "with_pieces": False},
             "native_pairs": bindings, "journal_events": len(events), "chain_valid": True,
             "tokenizer_requests": 78, "completion_requests": 0, "exact_matches": passed, "failed_matches": 6-passed,
             "pairs": pairs, "semantic_status": "UNREVIEWED", "P0": "PARTIAL"}
    atomic_json(VALIDATION, value)
    print(json.dumps({"exact_matches": passed, "failed_matches": 6-passed, "tokenizations": 78, "completions": 0, "journal_events": len(events)}))


def export():
    master, registration = read(MASTER), read(REG)
    validation = read(VALIDATION)
    packet = make_style_review(master, validation)
    fields, _ = read_csv(PUBLIC / "P0_final_control_review_v3.csv")
    if validate_review(packet, packet["items"], fields, require_complete=False):
        raise ValueError("New style master is not blank")
    atomic_json(PUBLIC / "P0_style_closure_review_v1.json", packet)
    save_csv(PUBLIC / "P0_style_closure_review_v1.csv", packet["items"], fields)
    evidence = history_evidence(master, registration)
    atomic_json(PUBLIC / "P0_history_a_evidence_v1.json", {"version": "history_a_source_evidence_v1", "created_utc": utc_now(),
                "source_master_sha256": sha256(MASTER), "source_registration_sha256": sha256(REG), "items": evidence,
                "human_confirmations": 0, "scope": "Extracted proposed evidence associations; original judgments unchanged"})
    flat = []
    for row in evidence:
        item = {k: v for k, v in row.items() if k not in {"active_excerpt", "candidate_excerpt"}}
        for arm in ("active", "candidate"):
            item.update({arm + "_" + k: v for k, v in row[arm + "_excerpt"].items()})
        flat.append(item)
    save_csv(PUBLIC / "P0_history_a_evidence_v1.csv", flat)
    _, converted = read_csv(REG.parent / "annotation_65_columns.csv")
    audit = annotation_audit(registration, converted)
    atomic_json(PUBLIC / "P0_closure_annotation_audit_v1.json", {"created_utc": utc_now(), "source_sha256": sha256(REG.parent / "annotation_65_columns.csv"), **audit})
    # Six rows only. The18 evidence links are reviewed in their dedicated table;
    # do not demand repair of discarded historical style/B/C annotations.
    save_csv(PUBLIC / "P0_closure_correction_form_v1.csv", audit["derived_labels_requiring_explicit_confirmation"])
    print(json.dumps({"new_style_review_items": 6, "history_evidence_items": len(evidence),
                      "short_correction_rows": 6, "old_gap_counts_verified": audit["historical_counts_verified"], "human_judgments_created": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["freeze", "tokenize", "export"])
    args = parser.parse_args()
    {"freeze": freeze, "tokenize": tokenize, "export": export}[args.stage]()
