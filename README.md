# PersonaSLM-Lab — P0 Research Engineering

**Working paper:** *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*

Official repository: <https://github.com/Yaaaxin/PersonaSLM>.

**Current status (2026-10-12): PARTIAL research acceptance.** The researcher's first real C0 run has been audited. Qwen3.5-2B-Base Q4_K_M and llama.cpp b11573 execute on CPU; real tokenizer matching and staged synthetic control validation are documented in the [final validation report](docs/P0_final_validation_report.md). Adapter execution success does not complete semantic review, upstream lineage verification or research sign-off. No P1 work or LoRA training is included.

Historical state before independent model files were supplied: real inference was BLOCKED. The original missing-configuration run and earlier engineering failures remain preserved in the reports and development log.

This is an independent research project. It does not read, reuse or link MimooPet code, data, binaries, models or history. Only the 20 fictional P0 cases in `data/synthetic/p0_cases.jsonl` are used.

## Evidence and design

- [P0 real inference report](docs/P0_real_inference_report.md) — environment, changes, actual results, failures and limits.
- [P0 acceptance checklist](docs/P0_acceptance_checklist.md) — PASS / PARTIAL / BLOCKED.
- [Model provenance](docs/P0_model_provenance_report.md), [reproducibility audit](docs/P0_reproducibility_report.md), and [neutral-control blinded review packet](docs/validation/P0_neutral_blinded_review.jsonl).
- [Command output evidence](docs/validation/P0_command_results.json) and [initial environment record](docs/validation/P0_environment_transcript.txt).
- [Research protocol](docs/research_protocol_v1.1.md) and [annotation guidelines](docs/annotation_guidelines.md).

Research Design Freeze: YES. Confirmatory Experiment Freeze: NO. Overall P0 acceptance: PARTIAL; P1 remains blocked pending acceptance.

## Windows environment and offline checks

The existing project virtual environment works. On this machine the global WindowsApps `python` and `py` aliases fail; invoke the project interpreter explicitly:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m personaslm validate
.\.venv\Scripts\python.exe -m personaslm smoke
.\.venv\Scripts\python.exe -m personaslm preflight
```

The earlier offline suite passed **113 tests**; the latest test counts and exact outputs are in the final validation report. Test doubles and hand-written smoke replies are software checks, not real model observations. The old `.pytest_cache` is unreadable; pytest now uses ignored `results/.pytest_cache`. Full directory audit reports PARTIAL and exit 2 while that original directory remains unreadable.

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

The adapter follows the native [llama.cpp server API](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md). Actual compatibility is now checked against b11573 / 0f701c882, with explicit limitations for absent evaluated input IDs. P0 supports the Base transcript template only; chat-tuned models require later model-specific handling.

Optional CLI overrides include `--model-file`, `--model-sha256`, `--server-file`, `--endpoint`, `--threads`, `--n-ctx`, `--max-new-tokens`, `--seed`, and `--token-tolerance`. Every effective setting is frozen into that run's manifest.

## Results and parser audit

Each invocation gets a separate ignored `results/p0/<run-id>/` directory:

- `manifest.json`: configuration, source/case digests, environment and pre-generation applicability.
- `events/*.json`: ordered request/response bytes, prepared prompts and token IDs, raw generation, parser transformations, scoring and failure events.
- `server.log`: owned process stdout/stderr, when a process was actually launched.

Raw HTTP bytes are stored as base64 before JSON decoding. Native generation responses are saved before parser/scoring work. Generated token IDs that are missing or empty are flagged rather than invented. Run manifests and event files are written once; completed events are atomically published and fsynced, with a hash chain that includes the manifest.

```powershell
.\.venv\Scripts\python.exe -m personaslm audit-run --run-dir results/p0/YOUR_RUN_ID
.\.venv\Scripts\python.exe -m personaslm replay-run --run-dir results/p0/YOUR_RUN_ID --output results/NEW_UNIQUE_REPLAY.json
```

Audit is offline and preserves the original artifacts. `replay-run` also reconstructs inputs and compares saved parser/scorer results, writing only to a new file outside the original run. It does not replay model generation. New run manifests retain exact dataset/source snapshots and read-only Git state. Missing terminal events mean interruption. There is no automatic generation retry, concurrent-writer support or automatic resume. A hash chain detects inconsistent edits; it is not signed or tamper-proof storage.

CLI exit 0 indicates success within that command's scope; exit 2 indicates BLOCKED/PARTIAL. A successful adapter run is not complete P0 sign-off: independently review real CPU behavior, model identity, actual tokenizer behavior and logs. The synthetic city scorer is not a general factuality metric.

## Version control

**First GitHub synchronization completed on 2026-10-12 by the human researcher.** Initial commit: [`4a538570c77666009a609c1218a435ac52a6187a`](https://github.com/Yaaaxin/PersonaSLM/commit/4a538570c77666009a609c1218a435ac52a6187a), authored and committed by **Yaxin ZHENG** at `2026-10-12T17:52:42+02:00` with message `Initialize PersonaSLM research infrastructure`. The researcher confirmed the push; the local `main` and `origin/main` references both point to this commit. The push's exact time was not recorded here.

Commits and pushes remain exclusively researcher-managed under [AGENTS.md](AGENTS.md). All changes are reviewed and committed by the repository maintainer, Yaxin ZHENG. The [development log](docs/research_development_log.md) records synchronization provenance and the preparation for real P0 validation. GitHub synchronization does not complete real-model P0 acceptance.

**Historical snapshot before the researcher's first commit/push (retained):**

`origin` is configured for `Yaaaxin/PersonaSLM`. Work is currently local, with no commit or push. Ignore rules exclude environments, models, binaries, private/chat data, experiment outputs, credentials and machine-specific runtime config. Only the explicitly named synthetic case file is allowlisted under `data/`.

Do not interpret passing parser or synthetic tests as evidence that persona conditioning changes dialogue reliability.
