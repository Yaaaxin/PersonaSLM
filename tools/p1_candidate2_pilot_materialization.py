"""Materialize the frozen 80-request pilot for Candidate 2 without inference."""

from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import subprocess
import sys


sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path("tools").resolve()))

import p1_conditional_materials as materials  # noqa: E402
import p1_model_feasibility_recovery as recovery  # noqa: E402
from personaslm.journal import atomic_json, utc_now  # noqa: E402


CANDIDATE = "qwen2_5_3b_instruct_q4_k_m"
SOURCE = Path(
    "docs/validation/p1/measurement_recovery_2x2_v2/fallback_bank_v1/"
    "fallback_pilot_manifest_candidate_v1.json"
)
SOURCE_SHA256 = "4be7b1959779371502a0e562a589c942676644ef86897196912677978d4da382"
OUT = Path("docs/validation/p1/model_feasibility_recovery_v1")
DESTINATION = OUT / "materialized_candidate2_disjoint_pilot_v1.json"
LOCAL = Path("results/p1_model_feasibility/v1/pilot_materialization") / CANDIDATE
TOOL = Path("tools/p1_candidate2_pilot_materialization.py")
NAMESPACE = "P1_AUTONOMOUS_CANDIDATE2_DISJOINT_PILOT_V1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def ordered_source(plan: dict) -> list[dict]:
    rows = plan["requests"]
    require(len(rows) == len({row["request_id"] for row in rows}) == 80, "Source pilot inventory changed")
    require(all(materials.request_hash(row) == row["request_sha256"] for row in rows), "Source request hash changed")
    c0 = [row for row in rows if row["condition"] == "C0"]
    remaining = [row for row in rows if row["condition"] != "C0"]
    require(len(c0) == 8 and len(remaining) == 72, "Source C0/continuation inventory changed")
    return c0 + remaining


def preparation_gate() -> tuple[dict, dict, list[dict]]:
    freeze = recovery.validate_freeze()
    recovery.candidate_allowed(CANDIDATE)
    usage = recovery.cumulative()
    require(usage["attempts_by_candidate"][CANDIDATE] == 0, "Candidate 2 is no longer prospective")
    require(usage["historical_ledger_untouched"] is True, "Historical ledger separation changed")
    require(recovery.sha256(SOURCE) == SOURCE_SHA256, "Frozen disjoint pilot source changed")
    require(
        freeze["post_screen_boundary"]["disjoint_pilot_manifest_sha256"] == SOURCE_SHA256,
        "Prospective freeze does not bind the source pilot",
    )
    materials.validate_all()
    source = recovery.load(SOURCE)
    rows = ordered_source(source)
    expected_c0 = set(freeze["post_screen_boundary"]["disjoint_pilot_c0_case_ids"])
    require({row["case_id"] for row in rows[:8]} == expected_c0, "Disjoint C0 identities changed")
    require(not all(row["condition"] == "C0" for row in source["requests"][:8]),
            "Legacy positional-slice hazard unexpectedly disappeared")
    return freeze, source, rows


def native_tokens(prompt: str, order: int, plan: dict) -> tuple[list[int], dict]:
    tokenizer = plan["execution_policy"]["native_tokenizer"]
    candidate = recovery.candidates(plan)[CANDIDATE]
    require(recovery.sha256(tokenizer["path"]) == tokenizer["sha256"], "Native tokenizer changed")
    argv = [
        str(Path(tokenizer["path"]).resolve()),
        "-m",
        str(Path(candidate["artifact"]["local_path"]).resolve()),
        "--stdin",
        "--ids",
        "--offline",
    ]
    completed = subprocess.run(
        argv,
        input=prompt.encode("utf-8"),
        capture_output=True,
        timeout=120,
        env={key: value for key, value in os.environ.items() if not key.upper().startswith("LLAMA_ARG_")},
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    log = {
        "argv": argv,
        "candidate_id": CANDIDATE,
        "generation_requests": 0,
        "order": order,
        "prompt_sha256": recovery.text_sha256(prompt),
        "returncode": completed.returncode,
        "stdout": completed.stdout.decode("utf-8", "replace"),
        "stderr": completed.stderr.decode("utf-8", "replace"),
        "software_recorded_utc": utc_now(),
    }
    path = LOCAL / f"tokenizer_{order:03d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = recovery.load(path)
        require(existing == {**log, "software_recorded_utc": existing["software_recorded_utc"]},
                "Existing pilot tokenizer log differs")
        log = existing
    else:
        atomic_json(path, log)
    require(log["returncode"] == 0, "Candidate 2 native tokenizer failed")
    ids = ast.literal_eval(log["stdout"].strip())
    require(isinstance(ids, list) and ids and all(type(value) is int and value >= 0 for value in ids),
            "Invalid Candidate 2 pilot token IDs")
    return ids, {"path": path.as_posix(), "sha256": recovery.sha256(path)}


def materialize() -> dict:
    freeze, source, sources = preparation_gate()
    plan = recovery.validate_freeze()
    candidate = recovery.candidates(plan)[CANDIDATE]
    model = Path(candidate["artifact"]["local_path"])
    require(model.is_file() and recovery.sha256(model) == candidate["artifact"]["remote_sha256"],
            "Candidate 2 model identity mismatch")
    metadata, metadata_read = recovery.gguf_metadata(model)
    template = metadata.get("tokenizer.chat_template")
    require(isinstance(template, str) and template.strip(), "Candidate 2 lacks a native template")
    feasibility = recovery.validate_materialized(CANDIDATE)
    require(recovery.text_sha256(template) == feasibility["native_template_sha256"],
            "Candidate 2 template differs from feasibility materialization")
    renderer = recovery.verified_template_runtime()
    settings = plan["execution_policy"]["generation"]
    requests = []
    logs = []
    for order, original in enumerate(sources):
        messages = original["messages"]
        require(len(messages) == 1 and messages[0]["role"] == "user", "Unexpected source message mapping")
        prompt = recovery.render_native_template(template, messages)
        require(prompt.count(messages[0]["content"]) == 1, "Native template duplicated task content")
        ids, log = native_tokens(prompt, order, plan)
        require(len(ids) + settings["max_new_tokens"] <= settings["context_tokens"], "Pilot context overflow")
        row = {
            "applicability": original["applicability"],
            "candidate_id": CANDIDATE,
            "case_id": original["case_id"],
            "condition": original["condition"],
            "context_sha256": original["context_sha256"],
            "evaluation_date": original["evaluation_date"],
            "evidence_sha256": original["evidence_sha256"],
            "factors": original["factors"],
            "family": original["family"],
            "input_token_ids": ids,
            "input_token_ids_sha256": recovery.text_sha256(str(ids)),
            "input_tokens": len(ids),
            "messages": messages,
            "messages_sha256": recovery.canonical_sha256(messages),
            "order": order,
            "prompt": prompt,
            "prompt_sha256": recovery.text_sha256(prompt),
            "question_sha256": original["question_sha256"],
            "reference": original["reference"],
            "reference_sha256": original["reference_sha256"],
            "request_id": f"p1_candidate2_pilot_{original['case_id']}_{original['condition']}",
            "source_request_id": original["request_id"],
            "source_request_sha256": original["request_sha256"],
            "speaker_id": original["speaker_id"],
            "split": original["split"],
        }
        row["request_sha256"] = recovery.canonical_sha256(row)
        requests.append(row)
        logs.append(log)

    c0_ids = [row["request_id"] for row in requests if row["condition"] == "C0"]
    continuation_ids = [row["request_id"] for row in requests if row["condition"] != "C0"]
    require(c0_ids == [row["request_id"] for row in requests[:8]], "C0 gate is not the explicit first block")
    return {
        "schema_version": "personaslm_candidate2_disjoint_pilot_materialization_v1",
        "status": "MATERIALIZED_NATIVE_TOKENS_NO_INFERENCE_NOT_EXECUTION_AUTHORIZATION",
        "candidate": {
            "candidate_id": CANDIDATE,
            "model_sha256": candidate["artifact"]["remote_sha256"],
            "model_bytes": candidate["artifact"].get("bytes"),
            "native_template_sha256": recovery.text_sha256(template),
            "native_template_renderer": renderer,
            "feasibility_materialization_sha256": recovery.sha256(recovery.materialized_path(CANDIDATE)),
            "gguf_metadata_read": metadata_read,
        },
        "scientific_source": {
            "path": SOURCE.as_posix(),
            "sha256": SOURCE_SHA256,
            "legacy_model_sha256_not_inherited": source["model"]["model_sha256"],
            "legacy_authorization_not_consumed": source["authorization_id"],
            "bound_sources": source["bound_sources"],
        },
        "authorization_subledger": {
            "namespace": NAMESPACE,
            "parent_authorization_id": recovery.load(recovery.LEDGER)["authorization_id"],
            "parent_ledger_path": recovery.LEDGER.as_posix(),
            "parent_ledger_sha256": recovery.sha256(recovery.LEDGER),
            "maximum_attempts": 80,
            "c0_gate_attempts": 8,
            "conditional_continuation_attempts": 72,
            "attempts_at_materialization": 0,
            "historical_160_request_ledger_consumed": 0,
        },
        "generation_settings": settings,
        "execution_blocks": {
            "c0_gate": {
                "request_ids": c0_ids,
                "condition": "C0",
                "denominator": 8,
                "automatic_current_value_threshold": 6,
                "prerequisite": "Candidate 2 complete integrity-valid feasibility screen with >=7/8 frozen successes and selected configuration.",
            },
            "conditional_continuation": {
                "request_ids": continuation_ids,
                "count": 72,
                "conditions": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "N_style", "N_history"],
                "prerequisites": [
                    "C0 automatic development gate passes >=6/8.",
                    "Genuine semantic review and endpoint-validity decision are registered.",
                    "A separately validated controller selects these explicit IDs; no positional legacy slice.",
                ],
            },
        },
        "native_tokenizer_logs": logs,
        "requests": requests,
        "tool": {"path": TOOL.as_posix(), "sha256": recovery.sha256(TOOL)},
        "execution_impact": {"scientific_model_generations": 0, "inference_seconds": 0.0},
        "limitations": [
            "Candidate 2 is resource-blocked and scientifically unevaluated; this materialization does not select it.",
            "The eight pilot cases are development material, not independent validation.",
            "Native model/template differences prevent attributing configuration differences to weights alone.",
            "The remaining 72 requests stay blocked even if the future automatic C0 gate passes until semantic validity is resolved.",
        ],
    }


def validate_materialized() -> dict:
    require(DESTINATION.is_file(), "Candidate 2 pilot has not been materialized")
    value = recovery.load(DESTINATION)
    require(value["tool"]["sha256"] == recovery.sha256(TOOL), "Materialization tool changed")
    require(value["scientific_source"]["sha256"] == recovery.sha256(SOURCE) == SOURCE_SHA256,
            "Scientific source changed")
    require(value["candidate"]["model_sha256"] == recovery.candidates()[CANDIDATE]["artifact"]["remote_sha256"],
            "Candidate model binding changed")
    model = Path(recovery.candidates()[CANDIDATE]["artifact"]["local_path"])
    require(model.is_file() and recovery.sha256(model) == value["candidate"]["model_sha256"],
            "Candidate model file changed")
    require(value["candidate"]["feasibility_materialization_sha256"] == recovery.sha256(recovery.materialized_path(CANDIDATE)),
            "Feasibility materialization changed")
    require(value["candidate"]["native_template_sha256"] == recovery.validate_materialized(CANDIDATE)["native_template_sha256"],
            "Candidate native template binding changed")
    for path, digest in value["scientific_source"]["bound_sources"].items():
        require(recovery.sha256(path) == digest, f"Bound scientific source changed: {path}")
    rows = value["requests"]
    require(len(rows) == len({row["request_id"] for row in rows}) == 80, "Materialized pilot inventory")
    require(all(row["condition"] == "C0" for row in rows[:8]), "Explicit C0 block changed")
    require(all(row["condition"] != "C0" for row in rows[8:]), "Continuation contains C0")
    require(value["execution_blocks"]["c0_gate"]["request_ids"] == [row["request_id"] for row in rows[:8]],
            "C0 execution IDs changed")
    require(value["execution_blocks"]["conditional_continuation"]["request_ids"] == [row["request_id"] for row in rows[8:]],
            "Continuation execution IDs changed")
    source = {row["request_id"]: row for row in recovery.load(SOURCE)["requests"]}
    scientific_fields = (
        "applicability", "case_id", "condition", "context_sha256", "evaluation_date",
        "evidence_sha256", "factors", "family", "messages", "question_sha256", "reference",
        "reference_sha256", "speaker_id", "split",
    )
    for row, log in zip(rows, value["native_tokenizer_logs"]):
        original = source[row["source_request_id"]]
        require(all(row[field] == original[field] for field in scientific_fields), "Scientific request content changed")
        require(row["source_request_sha256"] == original["request_sha256"], "Source request binding changed")
        require(row["messages_sha256"] == recovery.canonical_sha256(row["messages"]), "Message hash mismatch")
        require(row["prompt_sha256"] == recovery.text_sha256(row["prompt"]), "Prompt hash mismatch")
        require(row["prompt"].count(row["messages"][0]["content"]) == 1, "Prompt task content mismatch")
        require(row["input_token_ids_sha256"] == recovery.text_sha256(str(row["input_token_ids"])), "Token hash mismatch")
        require(row["input_tokens"] == len(row["input_token_ids"]), "Token count mismatch")
        require(row["input_tokens"] + value["generation_settings"]["max_new_tokens"]
                <= value["generation_settings"]["context_tokens"], "Materialized context overflow")
        require(row["request_sha256"] == recovery.canonical_sha256({k: v for k, v in row.items() if k != "request_sha256"}),
                "Request hash mismatch")
        require(recovery.sha256(log["path"]) == log["sha256"], "Tokenizer log changed")
        recorded = recovery.load(log["path"])
        require(recorded["generation_requests"] == 0 and ast.literal_eval(recorded["stdout"].strip()) == row["input_token_ids"],
                "Tokenizer evidence mismatch")
    return {
        "status": "PASS_MATERIALIZED_NO_INFERENCE_NOT_EXECUTION_AUTHORIZATION",
        "requests": 80,
        "c0_gate_requests": 8,
        "conditional_continuation_requests": 72,
        "namespace": value["authorization_subledger"]["namespace"],
        "scientific_model_generations": 0,
    }


def write_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), f"Refusing to overwrite existing evidence: {path}")
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("materialize", "validate"))
    arguments = parser.parse_args()
    if arguments.action == "materialize":
        write_new(DESTINATION, materialize())
    print(json.dumps(validate_materialized(), indent=2))


if __name__ == "__main__":
    main()
