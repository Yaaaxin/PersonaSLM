"""Offline reconciliation of existing native-tokenizer evidence and review views."""
import argparse
import base64
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess

from personaslm.control_candidates_v2 import pair
from personaslm.control_candidates import select_match
from personaslm.control_final_review import make_packet, validate_review
from personaslm.control_review_v2 import validate_packet as validate_old
from personaslm.journal import atomic_json, read_events, utc_now
from personaslm.provenance import fingerprint

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "results/p0_final_control_review/20261012T205559"
PUBLIC = ROOT / "docs/validation"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(path, value)


def inspect():
    frozen_path = PUBLIC / "P0_control_candidate_freeze_v2.json"
    validation_path = PUBLIC / "P0_control_tokenizer_validation_v2.json"
    master_path = PUBLIC / "P0_control_development_review_v2.json"
    csv_path = master_path.with_suffix(".csv")
    frozen, validation, master = map(read, (frozen_path, validation_path, master_path))
    if fingerprint({k: v for k, v in frozen.items() if k != "freeze_id"}) != frozen["freeze_id"]:
        raise ValueError("Frozen candidate digest differs")
    if digest(frozen_path) != validation["freeze_sha256"]:
        raise ValueError("Validation refers to different frozen inputs")
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames or [], list(reader)
    if validate_old(master, rows, fields):
        raise ValueError("The source is no longer a blank review master")
    run = ROOT / validation["run_directory"]
    events = read_events(run)
    manifest = read(run / "manifest.json")
    if manifest["candidate_freeze_sha256"] != digest(frozen_path):
        raise ValueError("Native run used a different freeze")
    http, pending, errors = [], None, []
    for e in events:
        d = e["data"]
        if e["kind"] == "http_request" and d["route"] == "/tokenize":
            if pending is not None:
                raise ValueError("Unpaired native tokenizer request")
            pending = e
        elif e["kind"] == "http_response" and d["route"] == "/tokenize":
            if pending is None or d["status"] != 200:
                raise ValueError("Missing request or failed tokenizer response")
            payload = pending["data"]["payload"]
            if {k: payload[k] for k in ("add_special", "parse_special", "with_pieces")} != validation["tokenizer_options"]:
                raise ValueError("Tokenizer options differ")
            raw = base64.b64decode(d["body_base64"], validate=True)
            ids = json.loads(raw)["tokens"]
            if not isinstance(ids, list) or any(type(t) is not int for t in ids):
                raise ValueError("Malformed native token IDs")
            http.append({"prompt": payload["content"], "ids": ids, "request_sequence": pending["sequence"],
                         "response_sequence": e["sequence"], "response_body_sha256": hashlib.sha256(raw).hexdigest()})
            pending = None
        if e["kind"] == "http_response" and d.get("status", 200) >= 400:
            errors.append({"sequence": e["sequence"], "route": d["route"], "status": d["status"], "error": d.get("error")})
    if pending is not None:
        raise ValueError("Unfinished token request")
    if len(http) != 444 or len(events) != validation["journal_events"]:
        raise ValueError("Unexpected native evidence inventory")
    specs = {s["case_id"]: s for s in frozen["case_specs"]}
    observed = {(p["case_id"], p["family"]): p for p in validation["pairs"]}
    old_rows = {(r["case_id"], r["family"]): r for r in rows}
    cursor, candidate_count, per_pair = 0, 0, []
    for f in frozen["pairs"]:
        key = f["case_id"], f["family"]
        if fingerprint(pair(specs[key[0]], key[1])) != fingerprint(f):
            raise ValueError("Current construction differs from frozen inputs")
        p = observed[key]
        ref = http[cursor]
        if ref["prompt"] != p["reference_prompt"]["text"] or ref["ids"] != p["reference_token_ids"]:
            raise ValueError("Reference does not match actual native response")
        cursor += 1
        if select_match(p["attempts"]) != p["matching"]:
            raise ValueError("Candidate selection does not replay")
        chosen = None
        for a in p["attempts"]:
            raw = http[cursor]
            if raw["prompt"] != a["prompt"]["text"] or raw["ids"] != a["token_ids"]:
                raise ValueError("Candidate differs from native request or response")
            if text_hash(raw["prompt"]) != a["prompt_sha256"] or len(raw["ids"]) != a["token_count"]:
                raise ValueError("Candidate hash or count mismatch")
            if a["token_difference"] != len(raw["ids"]) - len(ref["ids"]):
                raise ValueError("Token difference mismatch")
            if a["candidate_index"] == p["matching"]["best_candidate_index"]:
                chosen = {**a, "request_sequence": raw["request_sequence"], "response_sequence": raw["response_sequence"]}
            candidate_count += 1
            cursor += 1
        r = old_rows[key]
        if chosen is None or r["neutral_text"] != chosen["prompt"]["additions"][0] or r["prompt_sha256"] != chosen["prompt_sha256"]:
            raise ValueError("Review record is not the selected actual prompt")
        if chosen["token_difference"] != 0:
            raise ValueError("Selected pair is not an exact match")
        if p["reference_prompt"]["text"].replace(p["reference_prompt"]["additions"][0], "<INTERVENTION>", 1) != chosen["prompt"]["text"].replace(chosen["prompt"]["additions"][0], "<INTERVENTION>", 1):
            raise ValueError("Wrapper or trusted input changed")
        per_pair.append({"case_id": key[0], "family": key[1], "selected_candidate_index": chosen["candidate_index"],
                         "reference_count": len(ref["ids"]), "candidate_count": len(chosen["token_ids"]), "difference": 0,
                         "reference_prompt_sha256": p["reference_prompt_sha256"], "candidate_prompt_sha256": chosen["prompt_sha256"],
                         "trusted_evidence_hash": p["trusted_evidence_hash"], "native_reference_request": ref["request_sequence"],
                         "native_reference_response": ref["response_sequence"], "native_candidate_request": chosen["request_sequence"],
                         "native_candidate_response": chosen["response_sequence"], "review_material_exact": True,
                         "wrapper_evidence_question_exact": True})
    if cursor != len(http):
        raise ValueError("Unused native observations")
    baseline = read(SESSION / "materials/baseline.json")
    unchanged = []
    for name, members in baseline["journals"].items():
        directory = ROOT / name
        paths = [directory / "manifest.json", *sorted((directory / "events").glob("*.json"))]
        if (directory / "server.log").is_file():
            paths.append(directory / "server.log")
        current = {p.relative_to(directory).as_posix(): digest(p) for p in paths}
        if current != members:
            raise ValueError("Historical journal changed")
        unchanged.append(name)
    value = {"created_utc": utc_now(), "scope": "Offline verification of previously observed real tokenizer evidence; no server started",
             "source_hashes": {p.relative_to(ROOT).as_posix(): digest(p) for p in (frozen_path, validation_path, master_path, csv_path)},
             "run_directory": validation["run_directory"], "source_run_manifest_sha256": digest(run / "manifest.json"),
             "source_run_git": manifest["source_snapshot"]["git"], "source_run_configuration": manifest["configuration"],
             "model_sha256": validation["model_sha256"], "backend_sha256": validation["server_sha256"],
             "backend_build": validation["backend_binding"]["build_info"], "tokenizer_options": validation["tokenizer_options"],
             "journal_chain_valid": True, "journal_events": len(events), "native_requests_reconciled": cursor,
             "candidate_prompts_reconciled": candidate_count, "selected_pairs": per_pair,
             "old_run_http_errors_preserved": errors, "historical_journals_unchanged": unchanged,
             "new_tokenizer_requests": 0, "new_completion_requests": 0, "human_reviews_new": 0,
             "current_git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
             "current_git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT, text=True).strip())}
    # Only publish relative configuration paths. The original manifest stays local.
    for key in ("model_file", "server_file"):
        path = Path(value["source_run_configuration"][key])
        if path.is_absolute():
            value["source_run_configuration"][key] = path.relative_to(ROOT).as_posix()
    save(PUBLIC / "P0_final_control_evidence_v3.json", value)
    print(json.dumps({"review_rows": len(rows), "selected_pairs": len(per_pair), "native_requests": cursor,
                      "all_candidate_prompts": candidate_count, "historical_journals_unchanged": len(unchanged), "new_model_requests": 0}))


def package():
    old = PUBLIC / "P0_control_development_review_v2.json"
    frozen = PUBLIC / "P0_control_candidate_freeze_v2.json"
    validation = PUBLIC / "P0_control_tokenizer_validation_v2.json"
    evidence = PUBLIC / "P0_final_control_evidence_v3.json"
    packet = make_packet(read(old), read(frozen), read(validation),
                         {p.name: digest(p) for p in (old, old.with_suffix(".csv"), frozen, validation, evidence)})
    prefix = PUBLIC / "P0_final_control_review_v3"
    save(prefix.with_suffix(".json"), packet)
    with prefix.with_suffix(".csv").open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(packet["items"][0]))
        writer.writeheader()
        writer.writerows(packet["items"])
    with prefix.with_suffix(".csv").open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if validate_review(packet, rows, reader.fieldnames, require_complete=False):
            raise ValueError("Unexpected human judgments")
    print(json.dumps({"version": packet["version"], "rows": len(rows), "columns": len(rows[0]),
                      "human_reviews": 0, "packet_id": packet["packet_id"], "CSV_sha256": digest(prefix.with_suffix(".csv"))}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["inspect", "package"])
    args = parser.parse_args()
    {"inspect": inspect, "package": package}[args.stage]()
