from dataclasses import replace
import socket
import subprocess
from types import SimpleNamespace
from urllib.error import URLError

import pytest

from personaslm.journal import RunJournal, read_events
from personaslm.server import ManagedServer, server_command, validate_server_properties
from test_configuration import configured


def test_cpu_command_is_explicit_and_uses_argument_array(configured):
    command = server_command(configured)
    for flag, value in (("--device", "none"), ("--n-gpu-layers", "0"), ("--parallel", "1"),
                        ("--threads", "4"), ("--ctx-size", "4096")):
        assert command[command.index(flag) + 1] == value
    for flag in ("--no-kv-offload", "--no-op-offload", "--offline", "--no-context-shift"):
        assert flag in command
    assert command[command.index("--model") + 1] == configured.model_file


def test_server_identity_checks_path_context_revision(configured):
    props = {"model_path": configured.model_file, "default_generation_settings": {"n_ctx": 4096}, "build_info": "b123-testrev"}
    assert validate_server_properties(props, configured)["model_path_matches"]
    for wrong in ({**props, "model_path": None}, {**props, "model_path": "models/other.gguf"},
                  {**props, "default_generation_settings": {"n_ctx": 2048}}):
        with pytest.raises(ValueError):
            validate_server_properties(wrong, configured)
    with pytest.raises(ValueError, match="engine_revision"):
        validate_server_properties(props, replace(configured, engine_revision="different"))


def test_existing_port_is_never_attached_or_terminated(configured, local_tmp, monkeypatch):
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        config = replace(configured, endpoint=f"http://127.0.0.1:{occupied.getsockname()[1]}")
        def forbidden(*args, **kwargs):
            pytest.fail("Must refuse the existing service before launching anything")
        monkeypatch.setattr("personaslm.server.subprocess.run", forbidden)
        with pytest.raises(OSError):
            with ManagedServer(config, RunJournal(local_tmp, {"unit_test_only": True})):
                pass


def test_startup_timeout_cleans_owned_child_and_environment(configured, local_tmp, monkeypatch):
    with socket.socket() as free:
        free.bind(("127.0.0.1", 0))
        port = free.getsockname()[1]
    config = replace(configured, endpoint=f"http://127.0.0.1:{port}", startup_timeout=0.01)
    monkeypatch.setenv("LLAMA_ARG_N_GPU_LAYERS", "999")
    child = SimpleNamespace(pid=123, terminated=False, returncode=None)
    child.poll = lambda: None
    child.wait = lambda timeout: 0
    child.terminate = lambda: setattr(child, "terminated", True)
    def version(*args, **kwargs):
        assert "LLAMA_ARG_N_GPU_LAYERS" not in kwargs["env"]
        return SimpleNamespace(returncode=0, stdout=b"unit-test-version", stderr=b"")
    def unavailable(*args, **kwargs):
        raise URLError("unit-test connection refusal")
    monkeypatch.setattr("personaslm.server.subprocess.run", version)
    monkeypatch.setattr("personaslm.server.subprocess.Popen", lambda *args, **kwargs: child)
    monkeypatch.setattr("personaslm.server.LlamaClient.request", unavailable)
    journal = RunJournal(local_tmp, {"unit_test_only": True})
    with pytest.raises(TimeoutError):
        with ManagedServer(config, journal):
            pytest.fail("Unhealthy test double must never become ready")
    assert child.terminated
    assert any(e["kind"] == "server_launch" for e in read_events(journal.directory))
