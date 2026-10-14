# P1d authorized format diagnostic — engineering v1

Maintainer: Yaxin ZHENG. Exactly **16/16** authorized Base requests succeeded; zero failures, retries or additional completion requests. No Instruct or independent-validation inference was performed.

## Authorization and immutable configuration

The original [candidate](validation/p1d/final_preparation_v1/format_diagnostic_manifest_proposed_v1.json) and its byte-identical [frozen copy](validation/p1d/format_calibration_v1/frozen_manifest_v1.json) have SHA-256 `3f0e68b0fbe4cf5abfeab3bef9f6fbc39460b9219d118500ccc10d6fda121523`. The original proposal's NOT_AUTHORIZED metadata is historical and unchanged; the separate [researcher authorization](validation/p1d/format_calibration_v1/researcher_authorization_v1.json), SHA-256 `73b5ebecb6497ea70e0e7bb8d7ea10b4d5a88d7c75cdd848f92fcdd0328dcded`, records the explicit current user decision. Human decision time is null; software registration time is actual. Initial Git HEAD: `4ac68b2d8ebeb9cd9b13ccdf79a081d0d4f0abf0`, clean working tree.

Model: Qwen3.5-2B-Base Q4_K_M, SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`. Backend: llama.cpp b11573-0f701c882, SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`. CPU only, GPU layers zero, four threads and batch threads, context 4096, greedy temperature 0, top_p 1, seed 42, cache_prompt false, max96. No parameter other than the registered stop lists differs between the two new arms. Full native effective defaults are in [engineering_summary_v1.json](validation/p1d/format_calibration_v1/engineering_summary_v1.json), including sampler order, penalties and ignore_eos=false.

Eight original development identities, H_none, two arms, order seed716708 and exact frozen order were checked. Input lengths are 1635–1758. All eight arrays matched the live pinned backend before the first completion. Evidence, question content, references, fixed context and speaker identities matched source records; held-out overlap is zero. Model, tokenizer, 29 DLLs, sources and configuration passed postflight.

## Execution evidence

Actual UTC start `2026-10-14T14:52:02.926603+00:00`; finish `2026-10-14T14:58:52.382147+00:00`. Runner elapsed 408.878 seconds. Generated tokens: 922. Native termination: eight limit, eight word, zero EOG. All eight word stops are registered strings. Returned IDs, native token counts and possible stop-token suffix differences are retained separately. Frozen structural results: eight CROSS_TURN and eight AMBIGUOUS; all sixteen have unit_identifiable=true.

Observed process peak working set: 2610135040 bytes (2.431 GiB), from 18 observations. This is process lifetime peak, not a per-arm memory effect. No unsupported peak-RAM measurement is invented. Public metadata/download and vocabulary-only preparation overlapped part of execution; the paired latency difference is descriptive and not an isolated machine benchmark.

Raw outputs, HTTP byte bodies, token IDs, prompts, seeds, request order, server logs, memory and immutable source snapshots are under `results/p1d_format_calibration/development_v1/runs/20261014T145202-405aad2fae53417e921cc4f2181a5b17`. Each event is hash-chained. [execution_integrity_v1.json](validation/p1d/format_calibration_v1/execution_integrity_v1.json) reconstructs all sixteen results from original HTTP bodies and verifies actual payloads. Failure log inventory is empty; no failure is retried or hidden.

## Reproduction and validation

` .venv/Scripts/python.exe tools/p1d_format_calibration.py audit --output <NEW_UNUSED_PATH>` reconstructs the execution without generation. `.venv/Scripts/python.exe tools/p1d_format_analysis.py --verify` checks deterministic analysis outputs. Generation command used was `.venv/Scripts/python.exe tools/p1d_format_calibration.py run --preflight docs/validation/p1d/format_calibration_v1/preflight_v1.json`; do not repeat it: the attempt claim is exhausted and the runner refuses reruns.

The initial reconstruction check found only a Python tuple/JSON-array comparison defect. The original assembly source is archived as `analysis_v1/source_snapshot_v1.py`; verification now normalizes JSON representations. No raw data, AI rating or numerical result changed. Two successive reconstructions agreed. Final targeted regression evidence and every source/output digest are indexed by [reproducibility_manifest_v1.json](validation/p1d/format_calibration_v1/reproducibility_manifest_v1.json). Historical protocols/results remain untouched; the development log receives an append only.
