"""Prospectively frozen P1 model-feasibility screen.

The screen is intentionally finite: eight already-observed DEVELOPMENT cases
for SmolLM2, followed by the same eight cases for Qwen2.5-3B only when the
first candidate completes and fails the frozen 7/8 gate.  Preparation actions
perform no completion request.  Raw execution records live under ignored
``results/`` and never modify the historical 160-request ledger.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
import platform
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.request
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit


sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path("tools").resolve()))

import p1_temporal_fallback as fallback
from personaslm.inference import LlamaClient, normalize_result
from personaslm.journal import RunJournal, atomic_json, read_events, utc_now
from personaslm.observations import memory_observation
from personaslm.server import server_command, validate_server_properties


OUT = Path("docs/validation/p1/model_feasibility_recovery_v1")
FREEZE = OUT / "prospective_freeze_v1.json"
FREEZE_SHA256 = "5ce53ae8fba0cd5acb4fe303b7bd1b5a81600de68230d770a53e497fdb6483a9"
LEDGER = OUT / "autonomous_authorization_ledger_v1.json"
ROOT = Path("results/p1_model_feasibility/v1")
SOURCE_MANIFEST = Path(
    "docs/validation/p1/measurement_recovery_2x2_v2/fallback_bank_v1/"
    "fallback_calibration_manifest_candidate_v1.json"
)
BANK = Path(
    "docs/validation/p1/measurement_recovery_2x2_v2/fallback_bank_v1/"
    "bank_frozen_v1.json"
)
TOOL = Path("tools/p1_model_feasibility_recovery.py")
TEMPLATE_RUNTIME = Path("results/p1d_scientific_validation/v1/template_runtime")
TEMPLATE_RUNTIME_PROVENANCE = Path(
    "docs/validation/p1d/scientific_validation_v1/official_template_rendering_verification_v1.json"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path | str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_sha256(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text_sha256(raw)


def candidates(plan: dict | None = None) -> dict[str, dict]:
    plan = plan or load(FREEZE)
    return {row["candidate_id"]: row for row in plan["candidate_order"]}


def source_requests() -> dict[str, dict]:
    return {row["case_id"]: row for row in load(SOURCE_MANIFEST)["requests"]}


def case_bank() -> dict[str, dict]:
    return {row["case_id"]: row for row in load(BANK)["cases"]}


def validate_freeze() -> dict:
    require(sha256(FREEZE) == FREEZE_SHA256, "Prospective freeze changed")
    plan = load(FREEZE)
    require(
        plan["version"] == "p1_model_feasibility_recovery_prospective_freeze_v1"
        and plan["status"]
        == "FROZEN_PROSPECTIVE_NO_CHALLENGER_DOWNLOAD_OR_INFERENCE_EXECUTED",
        "Wrong freeze identity/status",
    )
    require(sha256(LEDGER) == plan["authorization"]["ledger_sha256"], "Authorization ledger changed")
    ledger = load(LEDGER)
    require(
        ledger["hard_limits"]
        == {"actual_model_inference_wall_seconds": 72000.0,
            "new_local_cpu_generations": 1200,
            "rule": "Whichever limit is reached first"},
        "Authorization ceilings changed",
    )
    require(
        ledger["consumption_at_freeze"]
        == {"actual_model_inference_wall_seconds": 0.0, "new_local_cpu_generations": 0},
        "Nonzero consumption was retroactively inserted at freeze",
    )
    for path, expected in plan["source_bindings"].items():
        require(Path(path).is_file(), f"Missing bound source: {path}")
        require(sha256(path) == expected, f"Bound source changed: {path}")

    ordered = plan["candidate_order"]
    require(len(ordered) == 2, "Initial screen must contain exactly two frozen challengers")
    require([row["order"] for row in ordered] == [1, 2], "Candidate order changed")
    require(len({row["candidate_id"] for row in ordered}) == 2, "Duplicate candidate")
    expected = {
        "smollm2_1_7b_instruct_q4_k_m": (
            1, "decd2598bc2c8ed08c19adc3c8fdd461ee19ed5708679d1c54ef54a5a30d4f33", 3221225472
        ),
        "qwen2_5_3b_instruct_q4_k_m": (
            2, "626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d", 5368709120
        ),
    }
    for row in ordered:
        order, digest, ram = expected[row["candidate_id"]]
        require(row["order"] == order, "Candidate priority changed")
        require(row["artifact"]["remote_sha256"] == digest, "Candidate artifact hash changed")
        require(row["minimum_available_physical_bytes_before_load"] == ram, "Candidate RAM gate changed")
        local = Path(row["artifact"]["local_path"])
        require(local.suffix.lower() == ".gguf" and "models/gguf/feasibility_candidates" in local.as_posix(),
                "Candidate path escaped ignored model storage")

    settings = plan["execution_policy"]["generation"]
    require(settings == {
        "cache_prompt": False, "context_tokens": 4096, "gpu_layers": 0,
        "ignore_eos": False, "max_new_tokens": 96, "mtp": False, "seed": 42,
        "stop": [], "temperature": 0.0, "threads": 4, "threads_batch": 4,
        "top_p": 1.0, "vision": False,
    }, "Generation settings changed")
    require(plan["measurement"]["qualification_threshold"] == 7, "Qualification threshold changed")
    require(plan["frozen_development_screen"]["independent_validation"] is False,
            "Development screen mislabeled independent")

    rows = plan["frozen_development_screen"]["cases"]
    source = source_requests()
    require(len(rows) == len({row["case_id"] for row in rows}) == 8, "Development case inventory")
    require([row["order"] for row in rows] == list(range(8)), "Development order changed")
    for frozen in rows:
        actual = source[frozen["case_id"]]
        for key in ("source_request_id", "source_request_sha256", "question_sha256",
                    "context_sha256", "evidence_sha256", "reference_sha256", "speaker_id", "family"):
            source_key = "request_id" if key == "source_request_id" else "request_sha256" if key == "source_request_sha256" else key
            require(frozen[key] == actual[source_key], f"Frozen case binding changed: {frozen['case_id']} {key}")
        require(actual["condition"] == "C0" and actual["factors"] == [0, 0, 0], "Screen is not C0")
    pilot = set(plan["post_screen_boundary"]["disjoint_pilot_c0_case_ids"])
    require(len(pilot) == 8 and pilot.isdisjoint(source), "Pilot C0 is not disjoint from model screen")

    evidence = load("docs/validation/p1/stage_b_v1/stage_b_execution_evidence_v1.json")
    require(evidence["calibration_gate"]["automatic_success"] == 6, "Historical 6/8 result changed")
    require(evidence["calibration_gate"]["threshold"] == 7 and not evidence["calibration_gate"]["proceed"],
            "Historical Stage B gate changed")
    require(evidence["authorization"]["ledger"]["total_attempted"] == 80
            and evidence["authorization"]["ledger"]["total_remaining"] == 80,
            "Historical ledger changed")
    return plan


def _completion_seconds(events: list[dict]) -> float:
    return sum(
        float(event["data"].get("elapsed_seconds", 0.0))
        for event in events
        if event["kind"] in ("http_response", "http_error")
        and event["data"].get("route") == "/completion"
    )


def _unresolved_completion_requests(events: list[dict]) -> int:
    requests = sum(
        event["kind"] == "http_request" and event["data"].get("route") == "/completion"
        for event in events
    )
    terminals = sum(
        event["kind"] in ("http_response", "http_error")
        and event["data"].get("route") == "/completion"
        for event in events
    )
    require(terminals <= requests, "Completion terminal record has no request")
    return requests - terminals


def cumulative() -> dict:
    plan = validate_freeze()
    attempts = sorted((ROOT / "attempts").glob("*.json")) if (ROOT / "attempts").exists() else []
    records = [load(path) for path in attempts]
    request_ids = [row["request_id"] for row in records]
    require(len(request_ids) == len(set(request_ids)), "Duplicate feasibility attempt")
    allowed_candidates = set(candidates(plan))
    require(all(row["authorization_id"] == load(LEDGER)["authorization_id"] for row in records),
            "Attempt belongs to another authorization")
    require(all(row["candidate_id"] in allowed_candidates for row in records), "Unknown attempted candidate")
    seconds = 0.0
    unresolved = 0
    run_count = 0
    if (ROOT / "runs").exists():
        for folder in sorted((ROOT / "runs").iterdir()):
            if not folder.is_dir():
                continue
            events = read_events(folder)
            seconds += _completion_seconds(events)
            unresolved += _unresolved_completion_requests(events)
            run_count += 1
    hard = load(LEDGER)["hard_limits"]
    require(len(records) <= hard["new_local_cpu_generations"], "Generation ceiling exceeded")
    require(seconds <= hard["actual_model_inference_wall_seconds"] + 1e-6, "Inference-time ceiling exceeded")
    by_candidate = {candidate_id: sum(row["candidate_id"] == candidate_id for row in records)
                    for candidate_id in allowed_candidates}
    return {
        "authorization_id": load(LEDGER)["authorization_id"],
        "new_local_cpu_generations": len(records),
        "actual_model_inference_wall_seconds": seconds,
        "actual_model_inference_wall_seconds_status": (
            "KNOWN_COMPLETED_OR_FAILED_HTTP_INTERVALS"
            if unresolved == 0 else "LOWER_BOUND_WITH_INTERRUPTED_IN_FLIGHT_REQUEST"
        ),
        "unresolved_in_flight_completion_requests": unresolved,
        "remaining_generations": hard["new_local_cpu_generations"] - len(records),
        "remaining_inference_wall_seconds": (
            hard["actual_model_inference_wall_seconds"] - seconds if unresolved == 0 else None
        ),
        "attempts_by_candidate": by_candidate,
        "run_count": run_count,
        "historical_ledger_untouched": True,
    }


def _run_folders(candidate_id: str) -> list[Path]:
    folders = []
    if (ROOT / "runs").exists():
        for folder in sorted((ROOT / "runs").iterdir()):
            manifest = folder / "manifest.json"
            if folder.is_dir() and manifest.is_file() and load(manifest).get("candidate_id") == candidate_id:
                folders.append(folder)
    return folders


def outcome(candidate_id: str) -> dict | None:
    folders = _run_folders(candidate_id)
    require(len(folders) <= 1, f"Repeated run for candidate: {candidate_id}")
    if not folders:
        return None
    summary = folders[0] / "summary.json"
    if not summary.exists():
        return {"candidate_id": candidate_id, "complete": False, "status": "INTERRUPTED_NO_SUMMARY"}
    integrity = _audit_folder(candidate_id, folders[0])
    require(integrity["integrity_status"] == "PASS", "Candidate run integrity did not pass")
    value = load(summary)
    value["run_directory"] = folders[0].as_posix()
    value["integrity_status"] = integrity["integrity_status"]
    return value


def selection_status() -> dict:
    plan = validate_freeze()
    first, second = [row["candidate_id"] for row in plan["candidate_order"]]
    one, two = outcome(first), outcome(second)
    if one is None:
        return {"status": "PENDING_CANDIDATE_1", "selected_candidate": None}
    if one.get("status") != "PASS" or not one.get("complete"):
        return {"status": "STOPPED_INCOMPLETE_CANDIDATE_1", "selected_candidate": None}
    if one["automatic_success"] >= 7:
        require(two is None, "Candidate 2 ran after Candidate 1 qualified")
        return {"status": "QUALIFIED", "selected_candidate": first, "gate": one}
    if two is None:
        return {"status": "CANDIDATE_1_FAILED_CANDIDATE_2_PENDING", "selected_candidate": None, "gate": one}
    if two.get("status") != "PASS" or not two.get("complete"):
        return {"status": "STOPPED_INCOMPLETE_CANDIDATE_2", "selected_candidate": None, "gate": two}
    if two["automatic_success"] >= 7:
        return {"status": "QUALIFIED", "selected_candidate": second, "gate": two}
    return {"status": "BOUNDED_SCREEN_NEGATIVE", "selected_candidate": None,
            "candidate_1": one, "candidate_2": two}


def candidate_allowed(candidate_id: str) -> dict:
    plan = validate_freeze()
    rows = candidates(plan)
    require(candidate_id in rows, "Unknown candidate")
    selected = rows[candidate_id]
    status = selection_status()["status"]
    if selected["order"] == 1:
        require(status == "PENDING_CANDIDATE_1", "Candidate 1 already attempted or screen stopped")
    else:
        require(status == "CANDIDATE_1_FAILED_CANDIDATE_2_PENDING",
                "Candidate 2 is not activated by a complete Candidate 1 gate failure")
    return selected


def download(candidate_id: str) -> dict:
    candidate = candidate_allowed(candidate_id)
    artifact = candidate["artifact"]
    target = Path(artifact["local_path"])
    if target.exists():
        require(sha256(target) == artifact["remote_sha256"], "Existing model has wrong hash")
        if "bytes" in artifact:
            require(target.stat().st_size == artifact["bytes"], "Existing model has wrong size")
        return {"status": "ALREADY_PRESENT_VERIFIED", "candidate_id": candidate_id,
                "path": target.as_posix(), "sha256": sha256(target), "generation_requests": 0}
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".partial")
    require(not partial.exists(), f"Preserve and inspect incomplete download: {partial}")
    digest = hashlib.sha256()
    count = 0
    try:
        with urllib.request.urlopen(artifact["resolved_url"], timeout=120) as response, partial.open("xb") as handle:
            while True:
                block = response.read(4 * 1024 * 1024)
                if not block:
                    break
                count += len(block)
                require(count <= 4 * 1024**3, "Unexpected model download size")
                digest.update(block)
                handle.write(block)
            handle.flush()
            os.fsync(handle.fileno())
        require(digest.hexdigest() == artifact["remote_sha256"], "Downloaded model hash mismatch")
        if "bytes" in artifact:
            require(count == artifact["bytes"], "Downloaded model size mismatch")
        os.replace(partial, target)
    except BaseException:
        # A partial download is evidence of the failed operation and is never
        # silently deleted or promoted.
        raise
    return {"status": "DOWNLOADED_VERIFIED", "candidate_id": candidate_id,
            "path": target.as_posix(), "bytes": count, "sha256": digest.hexdigest(),
            "generation_requests": 0}


def gguf_metadata(path: Path) -> tuple[dict, dict]:
    scalar = {0: "B", 1: "b", 2: "H", 3: "h", 4: "I", 5: "i", 6: "f", 7: "?", 10: "Q", 11: "q", 12: "d"}
    with path.open("rb") as handle:
        def unpack(fmt: str):
            size = struct.calcsize("<" + fmt)
            raw = handle.read(size)
            require(len(raw) == size, "Short GGUF metadata")
            return struct.unpack("<" + fmt, raw)[0]

        def string() -> str:
            length = unpack("Q")
            require(length <= 32 * 1024**2, "Unbounded GGUF metadata string")
            raw = handle.read(length)
            require(len(raw) == length, "Short GGUF string")
            return raw.decode("utf-8")

        def value(kind: int):
            require(handle.tell() <= 64 * 1024**2, "GGUF metadata exceeds 64 MiB cap")
            if kind in scalar:
                return unpack(scalar[kind])
            if kind == 8:
                return string()
            if kind == 9:
                subkind, length = unpack("I"), unpack("Q")
                require(length <= 1_000_000 and subkind != 9, "Invalid/unbounded GGUF array")
                return [value(subkind) for _ in range(length)]
            raise ValueError(f"Unknown GGUF metadata type: {kind}")

        require(handle.read(4) == b"GGUF", "Not a GGUF artifact")
        version = unpack("I")
        require(version in (2, 3), "Unsupported GGUF version")
        tensors, keys = unpack("Q"), unpack("Q")
        require(keys <= 10_000, "Too many GGUF metadata keys")
        result = {}
        for _ in range(keys):
            # Assignment evaluates the right-hand side before a subscript
            # target in Python.  Read the serialized key first explicitly;
            # otherwise the key length is misread as the value-type code.
            key = string()
            kind = unpack("I")
            result[key] = value(kind)
        return result, {"gguf_version": version, "tensor_count": tensors,
                        "metadata_keys": keys, "metadata_bytes_read": handle.tell(),
                        "tensor_data_read": False}


def verified_template_runtime() -> dict:
    """Bind reuse of the existing project-local Jinja runtime to recorded bytes."""
    provenance = load(TEMPLATE_RUNTIME_PROVENANCE)
    require(provenance.get("packages") == {"Jinja2": "3.1.6", "MarkupSafe": "3.0.4"},
            "Unexpected native-template renderer versions")
    hashes = provenance.get("package_file_sha256")
    require(isinstance(hashes, dict) and hashes, "Template runtime provenance lacks file hashes")
    runtime = TEMPLATE_RUNTIME.resolve()
    for name, digest in hashes.items():
        path = Path(name)
        require(path.is_file() and path.resolve().is_relative_to(runtime),
                f"Missing or escaped template runtime file: {name}")
        require(sha256(path) == digest, f"Template runtime file changed: {name}")
    resolved = str(runtime)
    if resolved not in sys.path:
        sys.path.insert(0, resolved)
    return {
        "package_file_count": len(hashes),
        "packages": provenance["packages"],
        "provenance_path": TEMPLATE_RUNTIME_PROVENANCE.as_posix(),
        "provenance_sha256": sha256(TEMPLATE_RUNTIME_PROVENANCE),
        "runtime_path": TEMPLATE_RUNTIME.as_posix(),
    }


def render_native_template(template: str, messages: list[dict]) -> str:
    verified_template_runtime()
    try:
        from jinja2.sandbox import ImmutableSandboxedEnvironment
    except ImportError as exc:
        raise RuntimeError("Jinja2 is required for offline native-template materialization") from exc
    environment = ImmutableSandboxedEnvironment(
        trim_blocks=True, lstrip_blocks=True, extensions=["jinja2.ext.loopcontrols"]
    )
    environment.globals["raise_exception"] = lambda message: (_ for _ in ()).throw(ValueError(message))
    return environment.from_string(template).render(
        messages=messages, tools=None, add_generation_prompt=True,
        enable_thinking=False, add_vision_id=False,
    )


def _native_tokens(prompt: str, candidate_id: str, order: int, plan: dict) -> tuple[list[int], dict]:
    tokenizer = plan["execution_policy"]["native_tokenizer"]
    require(sha256(tokenizer["path"]) == tokenizer["sha256"], "Native tokenizer changed")
    candidate = candidates(plan)[candidate_id]
    argv = [str(Path(tokenizer["path"]).resolve()), "-m", str(Path(candidate["artifact"]["local_path"]).resolve()),
            "--stdin", "--ids", "--offline"]
    process = subprocess.run(
        argv, input=prompt.encode("utf-8"), capture_output=True, timeout=120,
        env={key: value for key, value in os.environ.items() if not key.upper().startswith("LLAMA_ARG_")},
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    log = {
        "argv": argv, "candidate_id": candidate_id, "generation_requests": 0,
        "order": order, "prompt_sha256": text_sha256(prompt), "returncode": process.returncode,
        "stdout": process.stdout.decode("utf-8", "replace"),
        "stderr": process.stderr.decode("utf-8", "replace"), "software_recorded_utc": utc_now(),
    }
    path = ROOT / "materialization" / candidate_id / f"tokenizer_{order:03d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = load(path)
        comparable = {**log, "software_recorded_utc": existing["software_recorded_utc"]}
        require(existing == comparable, "Existing native-tokenizer log differs")
        log = existing
    else:
        atomic_json(path, log)
    require(process.returncode == 0, "Native tokenizer failed")
    ids = ast.literal_eval(log["stdout"].strip())
    require(isinstance(ids, list) and ids and all(type(value) is int and value >= 0 for value in ids),
            "Invalid native token IDs")
    return ids, {"path": path.as_posix(), "sha256": sha256(path)}


def materialized_path(candidate_id: str) -> Path:
    return OUT / f"materialized_{candidate_id}_v1.json"


def materialize(candidate_id: str) -> dict:
    plan = validate_freeze()
    candidate_allowed(candidate_id)
    candidate = candidates(plan)[candidate_id]
    model = Path(candidate["artifact"]["local_path"])
    require(model.is_file(), "Verified candidate model is not locally available")
    require(sha256(model) == candidate["artifact"]["remote_sha256"], "Candidate model hash mismatch")
    if "bytes" in candidate["artifact"]:
        require(model.stat().st_size == candidate["artifact"]["bytes"], "Candidate model size mismatch")
    metadata, read_info = gguf_metadata(model)
    template = metadata.get("tokenizer.chat_template")
    require(isinstance(template, str) and template.strip(), "Candidate GGUF lacks a nonempty native chat template")
    source = source_requests()
    renderer = verified_template_runtime()
    rows = []
    logs = []
    settings = plan["execution_policy"]["generation"]
    for frozen in plan["frozen_development_screen"]["cases"]:
        original = source[frozen["case_id"]]
        messages = original["messages"]
        require(len(messages) == 1 and messages[0]["role"] == "user", "Unexpected source message mapping")
        prompt = render_native_template(template, messages)
        require(prompt.count(messages[0]["content"]) == 1, "Native template changed or duplicated task content")
        ids, token_log = _native_tokens(prompt, candidate_id, frozen["order"], plan)
        require(len(ids) + settings["max_new_tokens"] <= settings["context_tokens"], "Candidate prompt exceeds context")
        row = {
            "candidate_id": candidate_id,
            "case_id": frozen["case_id"],
            "input_token_ids": ids,
            "input_token_ids_sha256": text_sha256(str(ids)),
            "input_tokens": len(ids),
            "messages": messages,
            "messages_sha256": canonical_sha256(messages),
            "order": frozen["order"],
            "prompt": prompt,
            "prompt_sha256": text_sha256(prompt),
            "request_id": f"p1_model_feasibility_{candidate_id}_{frozen['case_id']}",
            "source_request_id": frozen["source_request_id"],
            "source_request_sha256": frozen["source_request_sha256"],
        }
        row["request_sha256"] = canonical_sha256(row)
        rows.append(row)
        logs.append(token_log)
    value = {
        "candidate_id": candidate_id,
        "candidate_model_sha256": candidate["artifact"]["remote_sha256"],
        "freeze_path": FREEZE.as_posix(),
        "freeze_sha256": FREEZE_SHA256,
        "generation_requests": 0,
        "gguf_metadata_read": read_info,
        "native_template_sha256": text_sha256(template),
        "native_template_renderer": renderer,
        "native_tokenizer_logs": logs,
        "requests": rows,
        "source_manifest_sha256": sha256(SOURCE_MANIFEST),
        "status": "MATERIALIZED_AND_NATIVE_TOKENIZED_NO_COMPLETIONS",
        "tool_sha256": sha256(TOOL),
        "version": "p1_model_feasibility_materialized_v1",
    }
    destination = materialized_path(candidate_id)
    if destination.exists():
        require(load(destination) == value, "Existing materialized manifest differs")
    else:
        atomic_json(destination, value)
    return value


def validate_materialized(candidate_id: str) -> dict:
    plan = validate_freeze()
    path = materialized_path(candidate_id)
    require(path.is_file(), "Candidate has not been materialized")
    value = load(path)
    candidate = candidates(plan)[candidate_id]
    require(value["candidate_id"] == candidate_id and value["freeze_sha256"] == FREEZE_SHA256,
            "Materialized manifest identity mismatch")
    require(value["candidate_model_sha256"] == candidate["artifact"]["remote_sha256"],
            "Materialized model mismatch")
    require(value["source_manifest_sha256"] == sha256(SOURCE_MANIFEST), "Materialized source changed")
    require(value["tool_sha256"] == sha256(TOOL), "Execution tool changed after materialization")
    require(value["native_template_renderer"] == verified_template_runtime(),
            "Native-template renderer provenance changed")
    source = source_requests()
    require(len(value["requests"]) == 8, "Materialized request count")
    for order, row in enumerate(value["requests"]):
        require(row["order"] == order and row["case_id"] in source, "Materialized order/case")
        original = source[row["case_id"]]
        require(row["messages"] == original["messages"], "Materialized messages changed")
        require(row["source_request_sha256"] == original["request_sha256"], "Source request changed")
        require(row["messages_sha256"] == canonical_sha256(row["messages"]), "Messages hash mismatch")
        require(row["prompt_sha256"] == text_sha256(row["prompt"]), "Prompt hash mismatch")
        require(row["input_token_ids_sha256"] == text_sha256(str(row["input_token_ids"])), "Token hash mismatch")
        require(row["input_tokens"] == len(row["input_token_ids"]), "Token count mismatch")
        require(row["request_sha256"] == canonical_sha256({k: v for k, v in row.items() if k != "request_sha256"}),
                "Materialized request hash mismatch")
        require(row["input_tokens"] + 96 <= 4096, "Materialized context overflow")
    for log in value["native_tokenizer_logs"]:
        require(sha256(log["path"]) == log["sha256"], "Native-tokenizer log changed")
    return value


@dataclass(frozen=True)
class Runtime:
    model_file: str
    model_sha256: str
    server_file: str
    model_label: str
    engine_revision: str = "0f701c882"
    endpoint: str = "http://127.0.0.1:8080"
    threads: int = 4
    n_ctx: int = 4096
    max_new_tokens: int = 96
    seed: int = 42
    timeout: float = 180.0
    startup_timeout: float = 120.0

    def as_dict(self):
        return asdict(self)


def runtime(candidate_id: str, plan: dict | None = None) -> Runtime:
    plan = plan or validate_freeze()
    candidate = candidates(plan)[candidate_id]
    backend = plan["execution_policy"]["backend"]
    return Runtime(candidate["artifact"]["local_path"], candidate["artifact"]["remote_sha256"],
                   backend["path"], candidate_id)


def command(candidate_id: str, plan: dict | None = None) -> list[str]:
    return server_command(runtime(candidate_id, plan)) + [
        "--no-warmup", "--no-mmproj", "--spec-type", "none"
    ]


class Server:
    def __init__(self, candidate_id: str, journal: RunJournal, plan: dict):
        self.candidate_id = candidate_id
        self.journal = journal
        self.plan = plan
        self.config = runtime(candidate_id, plan)
        self.process = None
        self.log_handle = None

    def __enter__(self):
        argv = command(self.candidate_id, self.plan)
        uri = urlsplit(self.config.endpoint)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((uri.hostname, uri.port))
        environment = {key: value for key, value in os.environ.items()
                       if not key.upper().startswith("LLAMA_ARG_")}
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.journal.write("server_launch", {
            "argv": argv, "environment_policy": "remove LLAMA_ARG_* overrides", "warmup": False
        })
        try:
            self.log_handle = (self.journal.directory / "server.log").open("xb")
            self.process = subprocess.Popen(
                argv, stdout=self.log_handle, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                env=environment, cwd=Path.cwd(), creationflags=flags,
            )
            self.journal.write("server_process", {"pid": self.process.pid})
            deadline = time.monotonic() + self.config.startup_timeout
            health = LlamaClient(self.config.endpoint, timeout=2, audit=self.journal.write)
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise RuntimeError("Server exited during startup; preserve server.log")
                try:
                    if health.request("/health").get("status") == "ok":
                        self.journal.write("memory_observation", memory_observation(self.process.pid))
                        return self
                except HTTPError as exc:
                    if exc.code != 503:
                        raise
                except (URLError, TimeoutError, ConnectionError):
                    pass
                time.sleep(0.1)
            raise TimeoutError("Server startup deadline exceeded")
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, exc_type, exc, traceback):
        try:
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
        finally:
            if self.log_handle is not None:
                self.log_handle.close()
                self.log_handle = None

    def assert_running(self):
        require(self.process is not None and self.process.poll() is None, "Owned server is not running")
        self.journal.write("memory_observation", memory_observation(self.process.pid))


def _source_hashes() -> dict[str, str]:
    paths = [TOOL, FREEZE, LEDGER, SOURCE_MANIFEST, BANK,
             Path("tools/p1_temporal_fallback.py"), TEMPLATE_RUNTIME_PROVENANCE]
    paths += sorted(Path("src/personaslm").glob("*.py"))
    return {path.as_posix(): sha256(path) for path in paths}


def preflight(candidate_id: str) -> dict:
    plan = validate_freeze()
    candidate_allowed(candidate_id)
    materialized = validate_materialized(candidate_id)
    candidate = candidates(plan)[candidate_id]
    model = Path(candidate["artifact"]["local_path"])
    backend = plan["execution_policy"]["backend"]
    tokenizer = plan["execution_policy"]["native_tokenizer"]
    require(model.is_file() and sha256(model) == candidate["artifact"]["remote_sha256"], "Model identity mismatch")
    require(sha256(backend["path"]) == backend["sha256"], "Backend identity mismatch")
    require(sha256(tokenizer["path"]) == tokenizer["sha256"], "Tokenizer identity mismatch")
    memory = memory_observation(os.getpid())
    available = memory.get("system", {}).get("available_physical", 0)
    required = max(plan["execution_policy"]["global_ram_floor_bytes"],
                   candidate["minimum_available_physical_bytes_before_load"])
    require(available >= required,
            f"RAM preflight failed: available={available} required={required}; no inference")
    require(shutil.disk_usage(".").free >= 1024**3, "Less than 1 GiB output reserve")
    usage = cumulative()
    require(usage["unresolved_in_flight_completion_requests"] == 0,
            "Interrupted completion has unknown wall time; stop feasibility inference")
    require(usage["remaining_generations"] >= 8 and usage["remaining_inference_wall_seconds"] > 1.0,
            "Autonomous authorization exhausted")
    require(not (ROOT / "claims" / f"{candidate_id}.json").exists(), "Candidate already claimed")
    return {
        "authorization_ledger_sha256": sha256(LEDGER),
        "candidate_id": candidate_id,
        "checked_software_utc": utc_now(),
        "configuration": runtime(candidate_id, plan).as_dict(),
        "freeze_sha256": FREEZE_SHA256,
        "ledger_before": usage,
        "materialized_manifest_path": materialized_path(candidate_id).as_posix(),
        "materialized_manifest_sha256": sha256(materialized_path(candidate_id)),
        "memory_before": memory,
        "model_sha256": sha256(model),
        "required_available_physical_bytes": required,
        "server_command": command(candidate_id, plan),
        "source_hashes": _source_hashes(),
        "status": "PASS",
    }


def _payload(row: dict, settings: dict) -> dict:
    return {
        "prompt": row["input_token_ids"], "n_predict": settings["max_new_tokens"],
        "temperature": settings["temperature"], "top_p": settings["top_p"],
        "seed": settings["seed"], "cache_prompt": settings["cache_prompt"],
        "stop": settings["stop"], "return_tokens": True, "stream": False,
    }


def automatic_task_label(answer_state: str) -> str:
    """Map the frozen exact/alias endpoint without collapsing uncertainty.

    Only CURRENT_VALUE_ADOPTION is counted as gate success.  Definite
    incorrect/empty outcomes are failures, while missing and semantically
    unresolved outputs retain their own task-success labels for later human
    review.
    """
    mapping = {
        "CURRENT_VALUE_ADOPTION": "Success",
        "OUTDATED_VALUE_ADOPTION": "Failure",
        "WRONG_ENTITY_ANSWER": "Failure",
        "EMPTY_RESPONSE": "Failure",
        "MISSING_RECORD": "Missing",
        "UNVERIFIABLE_ANSWER": "Uncertain",
        "CONTRADICTORY_ANSWER_REQUIRES_REVIEW": "Uncertain",
    }
    require(answer_state in mapping, f"Unknown frozen endpoint state: {answer_state}")
    return mapping[answer_state]


def run(candidate_id: str, preflight_path: Path) -> dict:
    plan = validate_freeze()
    candidate_allowed(candidate_id)
    fresh = preflight(candidate_id)
    stored = load(preflight_path)
    for key in ("authorization_ledger_sha256", "candidate_id", "configuration", "freeze_sha256",
                "ledger_before", "materialized_manifest_sha256", "model_sha256",
                "required_available_physical_bytes", "server_command", "source_hashes", "status"):
        require(stored[key] == fresh[key], f"Preflight binding changed: {key}")
    materialized = validate_materialized(candidate_id)
    settings = plan["execution_policy"]["generation"]
    claim_path = ROOT / "claims" / f"{candidate_id}.json"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    require(not claim_path.exists(), "Existing candidate claim; no repeat/retry")
    claim = {
        "authorization_id": load(LEDGER)["authorization_id"],
        "candidate_id": candidate_id,
        "freeze_sha256": FREEZE_SHA256,
        "materialized_manifest_sha256": sha256(materialized_path(candidate_id)),
        "maximum_actual_completion_wall_seconds": 2700.0,
        "maximum_attempts": 8,
        "preflight_path": preflight_path.as_posix(),
        "preflight_sha256": sha256(preflight_path),
        "source_hashes": fresh["source_hashes"],
    }
    atomic_json(claim_path, claim)
    journal = RunJournal(ROOT / "runs", {
        "authorization": load(LEDGER), "candidate_id": candidate_id, "claim": claim,
        "configuration": runtime(candidate_id, plan).as_dict(), "freeze": plan,
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
        "materialized_manifest": materialized, "phase": "P1 model-feasibility recovery",
        "platform": platform.platform(), "python": platform.python_version(),
        "scientific_purpose": "Bounded new-model task-validity screen; developmental, not confirmatory or P3.",
    })
    for path, digest in claim["source_hashes"].items():
        destination = journal.directory / "source_snapshot" / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as handle:
            handle.write(Path(path).read_bytes())
        require(sha256(destination) == digest, "Source snapshot mismatch")
    bank = case_bank()
    completed = 0
    active = None
    completion_seconds = 0.0
    results = []
    status = "BLOCKED"
    try:
        journal.write("preflight", fresh)
        with Server(candidate_id, journal, plan) as server:
            client = LlamaClient(runtime(candidate_id, plan).endpoint, timeout=180, audit=journal.write)
            properties = client.request("/props")
            validation = validate_server_properties(properties, runtime(candidate_id, plan))
            require("0f701c882" in validation["build_info"], "Wrong backend build")
            journal.write("effective_server_defaults", {"props": properties, "validation": validation})
            for row in materialized["requests"]:
                tokens = client.request("/tokenize", {
                    "content": row["prompt"], "add_special": True,
                    "parse_special": True, "with_pieces": False,
                })["tokens"]
                require(tokens == row["input_token_ids"], "Live native tokenization differs")
                journal.write("live_prompt_verified", {
                    "request_id": row["request_id"], "token_ids_sha256": text_sha256(str(tokens))
                })
            journal.write("live_preflight_pass", {"prompts": 8, "completed_inference": 0})
            for row in materialized["requests"]:
                usage = cumulative()
                remaining_global = usage["remaining_inference_wall_seconds"]
                remaining_batch = 2700.0 - completion_seconds
                remaining = min(remaining_global, remaining_batch)
                require(remaining > 1.0, "Inference wall-time ceiling reached")
                client.timeout = min(180.0, remaining - 0.5)
                server.assert_running()
                active = row["request_id"]
                attempt_path = ROOT / "attempts" / f"{active}.json"
                attempt_path.parent.mkdir(parents=True, exist_ok=True)
                atomic_json(attempt_path, {
                    "authorization_id": load(LEDGER)["authorization_id"],
                    "candidate_id": candidate_id, "order": row["order"],
                    "request_id": active, "request_sha256": row["request_sha256"],
                    "run_id": journal.run_id, "started_utc": utc_now(),
                })
                journal.write("feasibility_generation_started", row)
                started = time.monotonic()
                response = client.request("/completion", _payload(row, settings))
                elapsed = time.monotonic() - started
                completion_seconds += elapsed
                journal.write("feasibility_raw_generation", {
                    "latency_seconds": elapsed, "request_id": active, "response": response,
                    "raw_output_sha256": text_sha256(response.get("content", "")),
                })
                normalized = normalize_result(response)
                answer_state = fallback.endpoint(normalized["raw_response"], bank[row["case_id"]])
                task_label = automatic_task_label(answer_state)
                automatic_success = task_label == "Success"
                structural = "EMPTY" if not normalized["raw_response"].strip() else (
                    "TRUNCATED" if normalized["stop_reason"] == "length" else "AMBIGUOUS"
                )
                result = {
                    "answer_state": answer_state,
                    "automatic_task_success": task_label,
                    "case_id": row["case_id"],
                    "candidate_id": candidate_id,
                    "component_exact_coverage": 1 if automatic_success else 0,
                    "generated_tokens": len(normalized["generated_token_ids"] or []),
                    "latency_seconds": elapsed,
                    "native_stop_reason": normalized["stop_reason"],
                    "persona_fidelity": "NOT_APPLICABLE",
                    "raw_output_sha256": text_sha256(normalized["raw_response"]),
                    "request_id": active,
                    "semantic_completeness": "NOT_INDEPENDENTLY_ADJUDICATED",
                    "structural_status": structural,
                }
                result_path = ROOT / "results" / f"{active}.json"
                result_path.parent.mkdir(parents=True, exist_ok=True)
                atomic_json(result_path, result)
                journal.write("feasibility_result", result)
                results.append(result)
                completed += 1
                active = None
            server.assert_running()
        require(completed == 8, "Incomplete candidate result")
        for path, digest in claim["source_hashes"].items():
            require(sha256(path) == digest, f"Postflight source changed: {path}")
        journal.write("postflight", {
            "completed_results": completed,
            "source_hashes_verified": len(claim["source_hashes"]),
            "status": "PASS",
        })
        status = "PASS"
    except BaseException as exc:
        status = "PARTIAL" if active is not None or completed else "BLOCKED"
        journal.write("failure", {
            "attempt_consumed": active is not None, "message": str(exc),
            "request_id": active, "type": type(exc).__name__,
        })
    success = sum(row["automatic_task_success"] == "Success" for row in results)
    states = {}
    for row in results:
        states[row["answer_state"]] = states.get(row["answer_state"], 0) + 1
    summary = {
        "answer_states": states,
        "attempted": cumulative()["attempts_by_candidate"][candidate_id],
        "authorization_usage_after_run": cumulative(),
        "automatic_success": success,
        "candidate_id": candidate_id,
        "complete": status == "PASS" and completed == 8,
        "completed_results": completed,
        "inference_wall_seconds_observed": _completion_seconds(read_events(journal.directory)),
        "proceed": status == "PASS" and completed == 8 and success >= 7,
        "status": status,
        "threshold": 7,
    }
    journal.finish(status=status, **{key: value for key, value in summary.items() if key != "status"})
    atomic_json(journal.directory / "summary.json", summary)
    return summary


def _audit_folder(candidate_id: str, folder: Path) -> dict:
    """Replay one immutable run before it can influence model selection."""
    manifest = load(folder / "manifest.json")
    require(manifest.get("candidate_id") == candidate_id, "Run manifest candidate mismatch")
    claim = manifest.get("claim")
    require(isinstance(claim, dict), "Run manifest lacks its claim")
    claim_path = ROOT / "claims" / f"{candidate_id}.json"
    require(claim_path.is_file() and load(claim_path) == claim, "Run claim mismatch")
    require(claim["freeze_sha256"] == FREEZE_SHA256, "Run claim freeze mismatch")
    require(claim["maximum_attempts"] == 8, "Run claim attempt ceiling changed")
    require(claim["maximum_actual_completion_wall_seconds"] == 2700.0,
            "Run claim wall-time ceiling changed")
    require(claim["materialized_manifest_sha256"] == sha256(materialized_path(candidate_id)),
            "Run claim materialized manifest mismatch")
    preflight_path = Path(claim["preflight_path"])
    require(preflight_path.is_file() and sha256(preflight_path) == claim["preflight_sha256"],
            "Run preflight artifact mismatch")

    events = read_events(folder)
    require(events and events[-1]["kind"] == "run_finished", "Run has no valid terminal event")
    summary_path = folder / "summary.json"
    require(summary_path.is_file(), "Run has no summary")
    summary = load(summary_path)
    require(events[-1]["data"] == summary, "Terminal event and standalone summary differ")

    materialized = validate_materialized(candidate_id)
    started = [event["data"] for event in events if event["kind"] == "feasibility_generation_started"]
    raw_rows = [event["data"] for event in events if event["kind"] == "feasibility_raw_generation"]
    result_rows = [event["data"] for event in events if event["kind"] == "feasibility_result"]
    require(len({row["request_id"] for row in started}) == len(started), "Duplicate generation-start event")
    require(len({row["request_id"] for row in raw_rows}) == len(raw_rows), "Duplicate raw-generation event")
    require(len({row["request_id"] for row in result_rows}) == len(result_rows), "Duplicate result event")
    require(started == materialized["requests"][:len(started)], "Attempt order/content changed")
    raw = {row["request_id"]: row for row in raw_rows}
    recorded = {row["request_id"]: row for row in result_rows}

    attempt_files = []
    if (ROOT / "attempts").exists():
        attempt_files = [load(path) for path in sorted((ROOT / "attempts").glob("*.json"))
                         if load(path).get("candidate_id") == candidate_id]
    attempt_by_id = {row["request_id"]: row for row in attempt_files}
    require(len(attempt_by_id) == len(attempt_files), "Duplicate candidate attempt files")
    for row in started:
        attempt = attempt_by_id.get(row["request_id"])
        require(attempt is not None, "Generation event lacks immutable attempt file")
        require(attempt["run_id"] == manifest["run_id"], "Attempt belongs to another run")
        require(attempt["request_sha256"] == row["request_sha256"], "Attempt request hash mismatch")

    bank = case_bank()
    replayed = []
    for row in started:
        request_id = row["request_id"]
        if request_id not in raw or request_id not in recorded:
            continue
        normalized = normalize_result(raw[request_id]["response"])
        state = fallback.endpoint(normalized["raw_response"], bank[row["case_id"]])
        expected = recorded[request_id]
        require(expected["answer_state"] == state, "Recorded score differs on replay")
        require(expected["automatic_task_success"] == automatic_task_label(state),
                "Recorded task-success label differs on replay")
        require(expected["raw_output_sha256"] == text_sha256(normalized["raw_response"]),
                "Recorded raw-output hash differs on replay")
        result_path = ROOT / "results" / f"{request_id}.json"
        require(result_path.is_file() and load(result_path) == expected,
                "Result file differs from journal result")
        replayed.append(state)

    run_status = summary.get("status")
    complete = (run_status == "PASS" and len(started) == len(raw_rows) == len(result_rows)
                == len(attempt_files) == len(replayed) == 8)
    success = sum(state == "CURRENT_VALUE_ADOPTION" for state in replayed)
    require(summary.get("completed_results") == len(result_rows), "Summary result count differs")
    require(summary.get("attempted") == len(attempt_files), "Summary attempt count differs")
    require(summary.get("automatic_success") == success, "Summary success count differs")
    require(summary.get("complete") is complete, "Summary completeness differs")
    require(summary.get("proceed") is (complete and success >= 7), "Summary gate decision differs")
    require(summary.get("threshold") == 7, "Summary threshold changed")
    require(summary.get("candidate_id") == candidate_id, "Summary candidate mismatch")
    usage_after = summary.get("authorization_usage_after_run")
    require(isinstance(usage_after, dict), "Summary lacks authorization usage snapshot")
    ledger = load(LEDGER)
    require(usage_after.get("authorization_id") == ledger["authorization_id"],
            "Authorization snapshot identity mismatch")
    require(usage_after.get("historical_ledger_untouched") is True,
            "Historical ledger separation missing")
    require(usage_after.get("attempts_by_candidate", {}).get(candidate_id) == len(attempt_files),
            "Authorization snapshot candidate count differs")
    require(usage_after.get("new_local_cpu_generations", -1) >= len(attempt_files),
            "Authorization snapshot generation count differs")
    require(usage_after.get("actual_model_inference_wall_seconds", -1.0) + 1e-6
            >= _completion_seconds(events), "Authorization snapshot wall time differs")
    require(usage_after.get("new_local_cpu_generations", 0)
            + usage_after.get("remaining_generations", -1)
            == ledger["hard_limits"]["new_local_cpu_generations"],
            "Authorization snapshot generation ceiling differs")
    require(usage_after.get("unresolved_in_flight_completion_requests") == 0,
            "Completed run authorization snapshot has unresolved wall time")
    require(abs(usage_after.get("actual_model_inference_wall_seconds", 0.0)
                + usage_after.get("remaining_inference_wall_seconds", -1.0)
                - ledger["hard_limits"]["actual_model_inference_wall_seconds"]) <= 1e-6,
            "Authorization snapshot wall-time ceiling differs")

    completion_http = [event for event in events if event["kind"] == "http_response"
                       and event["data"].get("route") == "/completion"]
    inference_seconds = _completion_seconds(events)
    require(inference_seconds <= 2700.0 + 1e-6, "Candidate inference-time ceiling exceeded")
    if run_status == "PASS":
        require(complete, "PASS run is not a complete eight-record run")
        require(len(completion_http) == 8, "PASS run lacks eight completion HTTP records")
        require(not any(event["kind"] == "failure" for event in events), "PASS run contains a failure")
        postflight = [event["data"] for event in events if event["kind"] == "postflight"]
        require(len(postflight) == 1 and postflight[0]["status"] == "PASS",
                "PASS run lacks its postflight")
        require(sum(event["kind"] == "live_prompt_verified" for event in events) == 8,
                "PASS run lacks eight live prompt checks")

    for path, digest in claim["source_hashes"].items():
        require(Path(path).is_file() and sha256(path) == digest,
                f"Current audit dependency differs from run source: {path}")
        snapshot = folder / "source_snapshot" / path
        require(snapshot.is_file() and sha256(snapshot) == digest,
                f"Run source snapshot mismatch: {path}")

    return {
        "attempted": len(attempt_files),
        "candidate_id": candidate_id,
        "complete": complete,
        "completion_http_records": len(completion_http),
        "inference_wall_seconds": inference_seconds,
        "integrity_status": "PASS",
        "proceed": complete and success >= 7,
        "replayed_results": len(replayed),
        "run_status": run_status,
        "success": success,
        "threshold": 7,
    }


def audit(candidate_id: str) -> dict:
    folders = _run_folders(candidate_id)
    require(len(folders) == 1, "Candidate must have exactly one run")
    value = _audit_folder(candidate_id, folders[0])
    return {
        **value,
        "status": "PASS" if value["complete"] else "INTEGRITY_PASS_RUN_INCOMPLETE",
    }


def _write_output(path: Path | None, value: dict) -> None:
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_json(path, value)


def _failure_receipt(action: str, candidate_id: str | None, exc: BaseException) -> dict:
    """Preserve a failed operation without claiming scientific completion."""
    action_attempts = 0
    if action == "run" and candidate_id and (ROOT / "attempts").exists():
        action_attempts = sum(
            load(path).get("candidate_id") == candidate_id
            for path in (ROOT / "attempts").glob("*.json")
        )
    value = {
        "action": action,
        "candidate_id": candidate_id,
        "error_message": str(exc),
        "error_type": type(exc).__name__,
        "generation_requests_in_failed_action": action_attempts,
        "software_recorded_utc": utc_now(),
        "status": "BLOCKED",
    }
    try:
        value["authorization_usage_observed"] = cumulative()
    except BaseException as ledger_exc:
        value["authorization_usage_error"] = {
            "message": str(ledger_exc), "type": type(ledger_exc).__name__
        }
    if action == "preflight":
        value["memory_observation"] = memory_observation(os.getpid())
        try:
            plan = validate_freeze()
            if candidate_id in candidates(plan):
                candidate = candidates(plan)[candidate_id]
                value["required_available_physical_bytes"] = max(
                    plan["execution_policy"]["global_ram_floor_bytes"],
                    candidate["minimum_available_physical_bytes_before_load"],
                )
        except BaseException as validation_exc:
            value["secondary_validation_error"] = {
                "message": str(validation_exc), "type": type(validation_exc).__name__
            }
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["validate", "ledger", "selection", "download", "materialize", "preflight", "run", "audit"])
    parser.add_argument("--candidate", choices=[
        "smollm2_1_7b_instruct_q4_k_m", "qwen2_5_3b_instruct_q4_k_m"
    ])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preflight", type=Path)
    arguments = parser.parse_args()
    try:
        if arguments.action == "validate":
            value = {"candidates": len(validate_freeze()["candidate_order"]), "generation_requests": 0,
                     "status": "PASS", "freeze_sha256": FREEZE_SHA256}
        elif arguments.action == "ledger":
            value = cumulative()
        elif arguments.action == "selection":
            value = selection_status()
        else:
            if not arguments.candidate:
                parser.error("--candidate is required")
            if arguments.action == "download":
                value = download(arguments.candidate)
            elif arguments.action == "materialize":
                value = materialize(arguments.candidate)
            elif arguments.action == "preflight":
                value = preflight(arguments.candidate)
            elif arguments.action == "run":
                if not arguments.preflight:
                    parser.error("--preflight is required for run")
                value = run(arguments.candidate, arguments.preflight)
            else:
                value = audit(arguments.candidate)
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        value = _failure_receipt(arguments.action, arguments.candidate, exc)
    _write_output(arguments.output, value)
    hidden = {"memory_before", "source_hashes"}
    print(json.dumps({key: val for key, val in value.items() if key not in hidden}, indent=2))
    if value.get("status") in ("PARTIAL", "BLOCKED", "INTEGRITY_PASS_RUN_INCOMPLETE"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
