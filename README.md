# PersonaSLM-Lab — P0 Research Engineering

**Working paper:** *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*

Official repository: <https://github.com/Yaaaxin/PersonaSLM>.

**Current status (2026-10-12): PARTIAL.** Offline implementation tests pass. Real inference is **BLOCKED** because no independent Qwen GGUF, expected checksum or llama-server executable has been supplied. No experimental effect claims, P1 work or LoRA training are included.

This is an independent research project. It does not read, reuse or link MimooPet code, data, binaries, models or history. Only the 20 fictional P0 cases in `data/synthetic/p0_cases.jsonl` are used.

## Evidence and design

- [P0 real inference report](docs/P0_real_inference_report.md) — environment, changes, actual results, failures and limits.
- [P0 acceptance checklist](docs/P0_acceptance_checklist.md) — PASS / PARTIAL / BLOCKED.
- [Command output evidence](docs/validation/P0_command_results.json) and [initial environment record](docs/validation/P0_environment_transcript.txt).
- [Research protocol](docs/research_protocol_v1.1.md) and [annotation guidelines](docs/annotation_guidelines.md).

Research Design Freeze: YES. Confirmatory Experiment Freeze: NO. Real P0 sign-off: BLOCKED.

## Windows environment and offline checks

The existing project virtual environment works. On this machine the global WindowsApps `python` and `py` aliases fail; invoke the project interpreter explicitly:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m personaslm validate
.\.venv\Scripts\python.exe -m personaslm smoke
.\.venv\Scripts\python.exe -m personaslm preflight
```

The final suite passed **113 tests**. Test doubles and hand-written smoke replies are software checks, not real model observations. The old `.pytest_cache` is unreadable; pytest now uses ignored `results/.pytest_cache`. Full directory audit reports PARTIAL and exit 2 while that original directory remains unreadable.

For a fresh environment, use an independently installed Python 3.10+ to create `.venv`, then run `python -m pip install -e ".[test]"`. Installation may require network access or local wheels; inference has no cloud API or automatic model download.

## Explicit model configuration

`configs/experiment_registry.yaml` remains the design declaration. P0 runtime reads JSON:

```powershell
Copy-Item configs/p0_runtime.example.json configs/p0_runtime.local.json
```

Fill these fields in the ignored local file:

| Field | Required value |
|---|---|
| `model_file` | Independent single-file GGUF, e.g. `models/gguf/YOUR_BASE_MODEL.gguf` |
| `model_sha256` | Trusted, independently recorded 64-character SHA-256 |
| `server_file` | Independent executable, e.g. `bin/llama.cpp/llama-server.exe` |
| `model_label` | Actual model identity and quantization description |
| `engine_revision` | Known revision substring to check against the server's build information |

All managed paths must stay inside this research root; relative paths resolve against that root, regardless of the calling directory. Symlinks/junctions and split GGUF shards are rejected. No existing models or services are auto-discovered.

To display a local digest for comparison:

```powershell
.\.venv\Scripts\python.exe -m personaslm hash-model --model-file models/gguf/YOUR_BASE_MODEL.gguf
```

Computing a digest alone does not verify a model's trusted origin. Runtime requires the expected digest and rejects a mismatch before starting a process.

## Real P0 run, after supplying the independent files

```powershell
.\.venv\Scripts\python.exe -m personaslm preflight --config configs/p0_runtime.local.json
.\.venv\Scripts\python.exe -m personaslm run-local --config configs/p0_runtime.local.json --condition C0
```

`preflight` is offline. `run-local` starts and owns the configured CPU llama-server, records its command/version/hash/PID/log, and stops that child on exit. An occupied port is refused. This entry point supersedes the starter's manually attached server mode. The CPU deployment setting and research design remain unchanged.

The adapter checks server model path/context, tokenizes full Base transcript prompts through that same server, sends exact token IDs to generation, and rejects prompt-count mismatch or truncation. N_style and N_history use bounded neutral candidate matching against C1 and C3 respectively, with predeclared token tolerance (default 0). Failure to match stops before generation. Human semantic review is still required before research comparisons.

The adapter follows the native [llama.cpp server API](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md). Compatibility with the actual independent binary remains unverified. P0 supports the Base transcript template only; chat-tuned models require later model-specific handling.

Optional CLI overrides include `--model-file`, `--model-sha256`, `--server-file`, `--endpoint`, `--threads`, `--n-ctx`, `--max-new-tokens`, `--seed`, and `--token-tolerance`. Every effective setting is frozen into that run's manifest.

## Results and parser audit

Each invocation gets a separate ignored `results/p0/<run-id>/` directory:

- `manifest.json`: configuration, source/case digests, environment and pre-generation applicability.
- `events/*.json`: ordered request/response bytes, prepared prompts and token IDs, raw generation, parser transformations, scoring and failure events.
- `server.log`: owned process stdout/stderr, when a process was actually launched.

Raw HTTP bytes are stored as base64 before JSON decoding. Native generation responses are saved before parser/scoring work. Generated token IDs that are missing or empty are flagged rather than invented. Run manifests and event files are written once; completed events are atomically published and fsynced, with a hash chain that includes the manifest.

```powershell
.\.venv\Scripts\python.exe -m personaslm audit-run --run-dir results/p0/YOUR_RUN_ID
```

Audit is offline and preserves the original artifacts. It validates the event chain and replays the parser. Missing terminal events mean interruption. There is no automatic generation retry, concurrent-writer support or automatic resume. A hash chain detects inconsistent edits; it is not signed or tamper-proof storage.

CLI exit 0 indicates success within that command's scope; exit 2 indicates BLOCKED/PARTIAL. A successful adapter run is not complete P0 sign-off: independently review real CPU behavior, model identity, actual tokenizer behavior and logs. The synthetic city scorer is not a general factuality metric.

## Version control

`origin` is configured for `Yaaaxin/PersonaSLM`. Work is currently local, with no commit or push. Ignore rules exclude environments, models, binaries, private/chat data, experiment outputs, credentials and machine-specific runtime config. Only the explicitly named synthetic case file is allowlisted under `data/`.

Do not interpret passing parser or synthetic tests as evidence that persona conditioning changes dialogue reliability.
