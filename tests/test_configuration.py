import json
import struct
from dataclasses import replace

import pytest

from personaslm.configuration import RuntimeConfig, preflight, verify_gguf
from personaslm.provenance import sha256


@pytest.fixture
def configured(local_tmp):
    # Deliberately NOT a usable model or executable. Unit-test header bytes only.
    model = local_tmp / "unit-only.gguf"
    model.write_bytes(b"GGUF" + struct.pack("<IQQ", 3, 1, 1) + b"not model tensors")
    server = local_tmp / "unit-only-llama-server.exe"
    server.write_bytes(b"not an executable")
    return RuntimeConfig(model_file=str(model), model_sha256=sha256(model), server_file=str(server))


def test_missing_paths_block_without_network():
    report = preflight(RuntimeConfig())
    assert report["status"] == "BLOCKED"
    assert len(report["checks"]) == 2


def test_valid_digest_and_changed_bytes(configured):
    from pathlib import Path
    model = Path(configured.model_file)
    assert preflight(configured)["status"] == "PASS"
    assert verify_gguf(model, configured.model_sha256.upper())["sha256_verified"]
    with model.open("ab") as handle:
        handle.write(b"tampered")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_gguf(model, configured.model_sha256)


@pytest.mark.parametrize("body", [b"", b"not GGUF", b"GGUF" + b"\0" * 20,
                                  b"GGUF" + struct.pack("<IQQ", 99, 1, 1)])
def test_invalid_gguf_headers(local_tmp, body):
    model = local_tmp / "invalid.gguf"
    model.write_bytes(body)
    with pytest.raises(ValueError):
        verify_gguf(model, sha256(model))


@pytest.mark.parametrize("overrides", [
    {"threads": 0}, {"threads": True}, {"max_new_tokens": 4096}, {"seed": -1},
    {"seed": True}, {"token_tolerance": -1}, {"timeout": float("nan")},
    {"startup_timeout": float("inf")}, {"prompt_template": "instruct"},
    {"model_file": 42}, {"endpoint": "http://example.com"},
])
def test_bad_config_rejected(overrides):
    with pytest.raises(ValueError):
        RuntimeConfig(**overrides)


def test_config_unknown_keys_fail_closed(local_tmp):
    config = local_tmp / "config.json"
    config.write_text(json.dumps({"threds": 4}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown"):
        RuntimeConfig.load(config)


def test_digest_not_silently_computed_or_accepted(configured):
    for expected in (None, "", "typo", "0" * 64):
        assert preflight(replace(configured, model_sha256=expected))["status"] == "BLOCKED"
