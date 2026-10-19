# P5 oracle diagnostic — engineering record v1

Maintainer: Yaxin ZHENG. AI-assisted scientific development; human semantic confirmation remains pending. First submission target: PLOS ONE.


Phase P5 / RQ4. Exactly **8 successful CPU requests, 0 failures, 0 retries**. This is development evidence, not P1d independent validation. The originally supplied `p1d` directory was a path typo: the existing `p5` manifest matched the authorized hash exactly. No source was moved or substituted.

- Original manifest: `docs/validation/p5/oracle_evidence_proposed_v1/oracle_evidence_manifest_proposed_v1.json`.
- Frozen byte-identical copy: `docs/validation/p5/oracle_diagnostic_v1/frozen_manifest_v1.json`.
- SHA-256: `894b7f0604f1f4c6121c1aefa1e24ee25c59a12c9e5be687e6403d9066d3c08e`.
- Authorization: `docs/validation/p5/oracle_diagnostic_v1/researcher_authorization_v1.json`; actual registration time is software provenance, human decision time is null.
- Raw run: `results/p5_oracle_diagnostic/development_v1/runs/20261014T190306-2bb3b39e2ce74d1f874237c659d384d5`. `events/` contains append-only hashed HTTP request/response records, base64 native bodies, input/output IDs, process telemetry and every result; `manifest.json` preserves original config, Git state and source snapshots. Logs and `summary.json` remain in this run.

The intended upstream model is Qwen/Qwen3.5-2B, revision `965dcc54bc9c0591873df0e9869c056a54d323d1`; the actual third-party Q4_K_M artifact is the unchanged lmstudio candidate. Conversion-source lineage remains only partially verified, accepted for development only.

| Pinned item | SHA-256 |
| --- | --- |
| GGUF | `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc` |
| llama-server b11573-0f701c882 | `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` |
| llama-tokenize | `e05dbdef761e577b3d56f3daea7b205a07f68e5d87242ea4e2544382ffdd358e` |
| Official chat template | `0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6` |

CPU only, four generation/batch threads, 4,096 context, 96 output tokens, seed 42, temperature 0, top-p 1, cache_prompt false, no custom stops, no ignored EOS, no warmup/speculative/vision generation. Request order is the original manifest order. Live server tokens matched all eight native records before the first completion. Input length 182–303 tokens; no input truncation. All returned generated token IDs were retained.

Initial memory preflights failed the unchanged 3 GiB physical-headroom gate. No completion was sent during those failures. The researcher released memory; final preflight passed. No unrelated process was stopped. Failure records remain beside the successful preflight. System-memory conditions differ from the older Instruct run, so timing is descriptive rather than an isolated evidence-length efficiency effect.

Native terminations: **8 eos**, 0 output-budget stops; last returned token 248046 in each output. Generated tokens total **329**. Mean request wall time **6.0918 s**; run elapsed **55.9518 s** including setup/checks. Observed peak server working set **2,384,363,520 bytes**, based on 10 samples / cumulative process peak telemetry; not a claim of complete system peak RAM. See `engineering_inventory_v1.json` for per-request timings, hashes, counts and order.

The frozen parser labels remain **8 AMBIGUOUS with 8 identifiable candidate spans**. It expects `eog`, while the runtime reports `eos`; even the separately saved alias sensitivity stays AMBIGUOUS because COMPLETE also requires a separate text-bound semantic review. Neither alias normalization nor terminal punctuation creates human boundary truth.

Executed commands: `.venv/Scripts/python.exe tools/p5_oracle_run.py register`, `preflight --output docs/validation/p5/oracle_diagnostic_v1/preflight_v1.json`, then `run --preflight docs/validation/p5/oracle_diagnostic_v1/preflight_v1.json`. The exclusive claim prevents reuse; these are reproduction records, **not permission to rerun**. Safe offline reconstruction: `audit --output <new unused JSON path>`. Measurement source is `tools/p5_oracle_measurement.py`; it refuses changed output text. Tests and preservation results are in this milestone's reproducibility manifest.
