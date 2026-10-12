"""Manage only the explicitly configured, independent CPU llama-server child."""
import os
from pathlib import Path
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

from .inference import LlamaClient
from .provenance import repository_root, require_local_path
from .observations import memory_observation


def server_command(config) -> list[str]:
    if not config.server_file or not config.model_file:
        raise ValueError("Explicit server_file and model_file are required")
    uri = urlsplit(config.endpoint)
    host = "127.0.0.1" if uri.hostname == "localhost" else uri.hostname
    return [str(require_local_path(Path(config.server_file))),
            "--model", str(require_local_path(Path(config.model_file))),
            "--host", host, "--port", str(uri.port or 80),
            "--threads", str(config.threads), "--threads-batch", str(config.threads),
            "--ctx-size", str(config.n_ctx), "--parallel", "1",
            "--n-gpu-layers", "0", "--device", "none", "--no-kv-offload", "--no-op-offload",
            "--no-context-shift", "--offline", "--verbosity", "4"]


def validate_server_properties(props: dict, config) -> dict:
    reported = props.get("model_path")
    if not isinstance(reported, str) or not reported:
        raise ValueError("Server /props did not report model_path; cannot bind tokenizer to GGUF")
    expected = require_local_path(Path(config.model_file))
    if require_local_path(Path(reported)) != expected:
        raise ValueError("Server model_path does not match configured GGUF")
    observed_ctx = props.get("default_generation_settings", {}).get("n_ctx")
    if type(observed_ctx) is not int or observed_ctx != config.n_ctx:
        raise ValueError(f"Server context mismatch: configured={config.n_ctx} observed={observed_ctx}")
    build_info = props.get("build_info")
    if config.engine_revision != "unprovided" and (
        not isinstance(build_info, str) or config.engine_revision not in build_info
    ):
        raise ValueError("Server build_info does not match declared engine_revision")
    return {"model_path_matches": True, "n_ctx": observed_ctx, "build_info": build_info,
            "cpu_status": "launch_arguments_recorded; hardware observation still required",
            "model_identity_limit": "Path plus local digest and owned process, not a server-side tensor hash"}


class ManagedServer:
    def __init__(self, config, journal):
        self.config = config
        self.journal = journal
        self.process = None
        self.log_handle = None

    def __enter__(self):
        command = server_command(self.config)
        uri = urlsplit(self.config.endpoint)
        host = "127.0.0.1" if uri.hostname == "localhost" else uri.hostname
        family = socket.AF_INET6 if host == "::1" else socket.AF_INET
        # Never attach to, stop or replace an unrelated existing local service.
        with socket.socket(family, socket.SOCK_STREAM) as probe:
            probe.bind((host, uri.port or 80))
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("LLAMA_ARG_")}
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        version = subprocess.run([command[0], "--version"], capture_output=True,
                                 timeout=15, env=env, creationflags=flags, cwd=repository_root())
        self.journal.write("engine_version", {"returncode": version.returncode,
                           "stdout": version.stdout.decode("utf-8", errors="replace"),
                           "stderr": version.stderr.decode("utf-8", errors="replace")})
        if version.returncode:
            raise RuntimeError("llama-server --version failed; see engine_version event")
        self.journal.write("server_launch", {"argv": command, "environment_policy": "remove LLAMA_ARG_* overrides"})
        try:
            self.log_handle = (self.journal.directory / "server.log").open("xb")
            self.process = subprocess.Popen(command, stdout=self.log_handle, stderr=subprocess.STDOUT,
                                            stdin=subprocess.DEVNULL, env=env, cwd=repository_root(),
                                            creationflags=flags)
            self.journal.write("server_process", {"pid": self.process.pid})
            deadline = time.monotonic() + self.config.startup_timeout
            health = LlamaClient(self.config.endpoint, timeout=min(2, self.config.startup_timeout), audit=self.journal.write)
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise RuntimeError(f"llama-server exited during startup: {self.process.returncode}; see server.log")
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
            raise TimeoutError("llama-server startup deadline exceeded; see server.log")
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, exc_type, exc, tb):
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
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("Owned llama-server process is no longer running")
        self.journal.write("memory_observation", memory_observation(self.process.pid))
