# P1d Instruct feasibility engineering report v1

Maintainer: Yaxin ZHENG. P3/P5, RQ3/4. Exactly eight explicitly authorized development attempts completed; no previous exact run existed. Software execution timestamps: 2026-10-14T16:06:42.075019+00:00 through 2026-10-14T16:09:35.904471+00:00. Researcher decision time is not invented. Authorization is registered separately from the immutable proposed manifest's original zero-authorization field.

## Frozen identity and execution

- Manifest: `docs/validation/p1d/instruct_preparation_v3/minimal_instruct_smoke_manifest_proposed_v1.json`; SHA-256 `ba63c30a9868b94b47f8f79dd774ac0627d56113810ffd4db08eb63af0374b91`. Frozen byte copy: `docs/validation/p1d/instruct_smoke_v1/frozen_manifest_v1.json`.
- Qwen/Qwen3.5-2B candidate: `models/gguf/instruct_candidates/lmstudio-bb84e113/Qwen3.5-2B-Q4_K_M.gguf`; SHA-256 `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`. Intended upstream revision `965dcc54bc9c0591873df0e9869c056a54d323d1`; distributor revision `bb84e11355a036e28f080c7793fa6d22b7c4e344`; reported quantizer b8185. Exact source-weight/conversion-command lineage remains partially verified and accepted only for this development test.
- Pinned llama.cpp b11573-0f701c882; executable SHA-256 `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`. Native tokenizer/DLL identities are in preflight. Official template SHA-256 `0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6`; non-thinking explicit token rendering, special-token parsing enabled.
- CPU-only, 4 generation/batch threads, context 4096, greedy temperature 0/top-p 1, seed 42, 96 output tokens, no stop strings, cache disabled, native EOS enabled. No speculative decoding, vision, hidden warmup or retries. Model-specific template differs from the historical Base text completion.
- All eight development identities, native token arrays (1642–1765 inputs), request hashes, order, parent references and full prompts passed preflight. Full validation-cohort cases were excluded. The 45-minute limit was respected: 173.829 seconds total.

## Actual requests

| Order | Request | Generated tokens | Native stop | Latency seconds |
| --- | --- | ---: | --- | ---: |
| 0 | p1d_instruct_smoke_v1_p1d_dev_04_1 | 22 | eos | 23.664 |
| 1 | p1d_instruct_smoke_v1_p1d_dev_03_0 | 40 | eos | 19.51 |
| 2 | p1d_instruct_smoke_v1_p1d_dev_01_0 | 40 | eos | 19.487 |
| 3 | p1d_instruct_smoke_v1_p1d_dev_07_1 | 32 | eos | 18.641 |
| 4 | p1d_instruct_smoke_v1_p1d_dev_05_1 | 95 | eos | 23.768 |
| 5 | p1d_instruct_smoke_v1_p1d_dev_02_0 | 96 | length | 25.088 |
| 6 | p1d_instruct_smoke_v1_p1d_dev_06_1 | 10 | eos | 18.381 |
| 7 | p1d_instruct_smoke_v1_p1d_dev_00_0 | 6 | eos | 17.924 |

Eight successful responses, zero failures, 341 generated tokens, seven native EOS and one output-budget termination. Mean request wall latency 20.808s. All generated token arrays and native counts are preserved. Observed process lifetime peak working set: 2689376256 bytes (2.505 GiB), from 10 observations; not per-condition peak RAM or total system RAM. No unobserved telemetry is invented.

## Storage, integrity and reproduction

Raw run: `results/p1d_instruct_smoke/development_v1/runs/20261014T160641-ca4d1cf9e0fd433e81d9c9d2bed924b3`. `events/` retains exact payloads, base64 raw HTTP bodies, native stops/timings/token IDs, memory and error/audit events in a hash chain. `server.log`, source snapshot, `manifest.json` and `summary.json` preserve environment and completion status. Manifest hash: `54dec772067faa73b131e94d923174772d84a03a1dfdf71d6292527262b36fda`. `execution_integrity_v1.json` reconstructs all eight results from these records.

Executed once: `.venv/Scripts/python.exe tools/p1d_instruct_smoke.py run --preflight docs/validation/p1d/instruct_smoke_v1/preflight_v1.json`. The exclusive claim prevents a second execution. **Do not rerun this generation command.** Read-only verification: `.venv/Scripts/python.exe tools/p1d_instruct_smoke.py audit --output docs/validation/p1d/instruct_smoke_v1/fresh_integrity_check.json` (choose an unused output path); annotation reconstruction: `.venv/Scripts/python.exe tools/p1d_instruct_measurement.py --verify`. Final reproducibility and scoped regression records are in `docs/validation/p1d/instruct_smoke_v1`.

Original structural statuses remain seven AMBIGUOUS and one TRUNCATED. The pinned parser expects native `eog`, whereas these raw responses say `eos` and end in token 248046. A separately saved alias sensitivity changes interpretation of stop evidence without modifying raw output, text spans or historical labels. Identifiable candidate spans are not independently adjudicated boundary ground truth.
