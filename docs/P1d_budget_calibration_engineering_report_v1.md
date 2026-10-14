# P1d bounded CPU calibration — engineering report v1

Maintainer: Yaxin ZHENG. Exactly **144 authorized Base requests completed successfully; zero failures, zero retries, zero additional generation requests**. The 1,728 Base and 288 Instruct independent-study targets remain unauthorized.

## Authorization and frozen configuration

The user-authorized manifest is [the original candidate v2](validation/p1d/scientific_validation_v1/budget_calibration_manifest_candidate_v2.json), SHA-256 `510e46b214dda23dea2a3e5462d44982d25b7a9db022626a7a5a1ba504d5e039`. The [frozen byte copy](validation/p1d/budget_calibration_v1/frozen_manifest_v2.json) is identical. Its historical proposal-status fields were preserved; [separate genuine researcher authorization](validation/p1d/budget_calibration_v1/researcher_authorization_v1.json) is operative. Human decision time is null; actual software registration time is recorded.

Model: Qwen3.5-2B-Base Q4_K_M, SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`. Backend: llama.cpp b11573 / commit 0f701c882, server SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`. The tokenizer executable and all 29 DLL hashes are in the frozen manifest and actual preflight. CPU threads/batch 4, context 4,096, GPU layers 0, seed 42, temperature 0, top_p 1, cache_prompt=false, stop=[]; only per-request output cap varies. Effective backend defaults and full payloads are retained, including returned generated token IDs.

## Execution and integrity

Actual software start: `2026-10-14T12:33:47.444197+00:00`. Finish: `2026-10-14T14:00:31.473856+00:00`. Runner elapsed: **86.72 minutes**. Eight registered development cases/speakers, six cells and three caps; no independent candidate ID is included. All 48 prompt/token sequences agree across caps, and live native tokenization verified their saved IDs before the first completion. Input range is 1,633–1,807. No context truncation occurred.

| Output cap | Successful requests | Native stops | Frozen structural status | Identifiable units | Mean wall latency, seconds |
| --- | --- | --- | --- | --- | --- |
| 96 | 48 | {'limit': 48} | {'CROSS_TURN': 48} | 48/48 | 28.68 |
| 192 | 48 | {'limit': 48} | {'CROSS_TURN': 48} | 48/48 | 37.05 |
| 256 | 48 | {'limit': 48} | {'CROSS_TURN': 48} | 48/48 | 42.38 |

Generated tokens: **26,112**. Observed server peak working set: **2,485,653,504 bytes (2.315 GiB)** across 146 observations. This is lifetime process peak, not isolated per-budget RAM. Latencies include prompt processing and response transfer on the actual workstation; concurrent light research/tool activity prevents treating them as clean hardware benchmarks.

All effective server-returned generation settings match after excluding only `n_predict`/`max_tokens`. The engineering JSON separately reports native prompt-processing milliseconds, generation milliseconds and token throughput for each cap. These backend timings are not process CPU-time measurements. No timing extrapolation from these shorter development prompts certifies main-cohort cost.

All 144 write-ahead identities, HTTP completion payloads, raw HTTP response bytes, raw texts, token counts/IDs, order and reconstructed parser results match. Postflight rechecked model/backend/source identities. Native `limit` is normalized to `length`; both are retained, and neither is a semantic failure label.

Raw run directory: `results/p1d_budget_calibration/development_v1/runs/20261014T123347-2ab6ce581f6a46abbdeb83fea75469a2`. Its `events/`, `manifest.json`, `summary.json`, server logs and `source_snapshot/` preserve complete provenance. [Engineering summary](validation/p1d/budget_calibration_v1/engineering_summary_v1.json) and [execution reconstruction](validation/p1d/budget_calibration_v1/measurement_v1/execution_integrity_v1.json) bind these records. Runtime failures: none. Offline engineering corrections and test results are separately documented in the development log and final reproducibility seal.

## Reproduction without new inference

The executed command was `.venv/Scripts/python.exe tools/p1d_budget_calibration.py run --preflight docs/validation/p1d/budget_calibration_v1/preflight_v1.json`. The consumed authorization must not be reused to rerun it.

Read-only reconstruction: `.venv/Scripts/python.exe tools/p1d_budget_calibration.py audit --output results/p1d_budget_calibration/reconstruction_NEW.json` (choose an unused path). Semantic/statistical reconstruction: `.venv/Scripts/python.exe tools/p1d_budget_analysis.py --verify`. New output creation refuses overwrites. No historical protocol, raw experiment, annotation or main candidate bank was modified.
