"""Explicit, project-local P0 configuration; never searches for model weights."""
from dataclasses import asdict, dataclass, fields
import json
import math
from pathlib import Path
import re
import struct

from .inference import _localhost_endpoint
from .provenance import require_local_path, sha256


@dataclass(frozen=True)
class RuntimeConfig:
    model_file: str | None = None
    model_sha256: str | None = None
    server_file: str | None = None
    model_label: str = "unconfigured-base-model"
    engine_revision: str = "unprovided"
    endpoint: str = "http://127.0.0.1:8080"
    threads: int = 4
    n_ctx: int = 4096
    max_new_tokens: int = 96
    seed: int = 42
    timeout: float = 180.0
    startup_timeout: float = 120.0
    token_tolerance: int = 0
    max_match_candidates: int = 256
    prompt_template: str = "transcript_base_v1"

    def __post_init__(self):
        _localhost_endpoint(self.endpoint)
        for name in ("threads", "n_ctx", "max_new_tokens", "max_match_candidates"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.max_new_tokens >= self.n_ctx:
            raise ValueError("max_new_tokens must be smaller than n_ctx")
        if type(self.seed) is not int or not 0 <= self.seed < 2**32 - 1:
            raise ValueError("seed must be an explicit non-random uint32")
        if type(self.token_tolerance) is not int or self.token_tolerance < 0:
            raise ValueError("token_tolerance must be a nonnegative integer")
        for name in ("timeout", "startup_timeout"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if self.prompt_template != "transcript_base_v1":
            raise ValueError("P0 supports only transcript_base_v1 for Base models")
        for name in ("model_label", "engine_revision"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be a nonempty string")
        for name in ("model_file", "server_file", "model_sha256"):
            if getattr(self, name) is not None and not isinstance(getattr(self, name), str):
                raise ValueError(f"{name} must be a string or null")

    @classmethod
    def load(cls, path: Path) -> "RuntimeConfig":
        obj = json.loads(require_local_path(path).read_text(encoding="utf-8-sig"))
        if not isinstance(obj, dict):
            raise ValueError("Runtime configuration must be a JSON object")
        unknown = set(obj) - {field.name for field in fields(cls)}
        if unknown:
            raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")
        return cls(**obj)

    def as_dict(self) -> dict:
        return asdict(self)


def verify_gguf(path: Path, expected_sha256: str) -> dict:
    path = require_local_path(path)
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("An independently recorded 64-hex model_sha256 is required")
    if not path.is_file() or path.suffix.lower() != ".gguf":
        raise ValueError("Configured GGUF file does not exist or has the wrong suffix")
    if re.search(r"-\d{5}-of-\d{5}\.gguf$", path.name, re.IGNORECASE):
        raise ValueError("P0 supports a single GGUF file; split-shard manifests are not implemented")
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:4] != b"GGUF":
        raise ValueError("Invalid or incomplete GGUF header")
    version, tensors, metadata = struct.unpack("<IQQ", header[4:])
    if version not in (2, 3) or tensors == 0 or metadata == 0:
        raise ValueError("Unsupported GGUF version or empty GGUF header")
    actual = sha256(path)
    if actual != expected_sha256.lower():
        raise ValueError(f"GGUF SHA-256 mismatch: expected={expected_sha256.lower()} actual={actual}")
    return {"path": str(path), "sha256": actual, "bytes": path.stat().st_size,
            "gguf_version": version, "sha256_verified": True,
            "limitation": "Header and file digest checked; tensor loading and model identity require llama.cpp."}


def preflight(config: RuntimeConfig) -> dict:
    checks = []
    model = server = None
    if not config.model_file or not config.model_sha256:
        checks.append({"check": "gguf", "status": "BLOCKED", "reason": "model_file and model_sha256 are required"})
    else:
        try:
            model = verify_gguf(Path(config.model_file), config.model_sha256)
            checks.append({"check": "gguf", "status": "PASS", "evidence": model})
        except (ValueError, OSError) as exc:
            checks.append({"check": "gguf", "status": "BLOCKED", "reason": str(exc)})
    try:
        if not config.server_file:
            raise ValueError("server_file is required; no executable is auto-discovered")
        path = require_local_path(Path(config.server_file))
        if not path.is_file():
            raise ValueError("Configured llama-server executable does not exist")
        server = {"path": str(path), "sha256": sha256(path)}
        checks.append({"check": "server_executable", "status": "PASS", "evidence": server})
    except (ValueError, OSError) as exc:
        checks.append({"check": "server_executable", "status": "BLOCKED", "reason": str(exc)})
    return {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "BLOCKED",
            "scope": "offline file preflight only; no real inference verified", "checks": checks,
            "model": model, "server": server}
