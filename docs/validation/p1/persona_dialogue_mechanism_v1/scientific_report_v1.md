# Persona-dialogue mechanism study: scientific report v1

## Status and scope

This report covers one completed 42-generation adaptive study on six previously unseen, explicitly synthetic dialogue cases. It used Qwen3.5-2B-Instruct Q4_K_M on CPU and compared seven prompt arms: `H_ONLY`, `S_H`, `S_F_NO_H`, `F_H_RAW`, `S_F_H`, `F_H_STRUCTURE`, and `F_H_REFRESH`. The structure and refresh arms were motivated by an earlier development batch and were prospectively frozen before these six cases were generated. The study is therefore adaptive unseen-case validation, not confirmatory inference, real-speaker evidence, human validation, or a population sample.

The primary question was whether raw dialogue history displaced a current persona-consistent choice, and whether a generic response structure or a names-only recency refresh reduced that failure. Primary endpoints were deliberately narrow exact-parser outcomes. No p-values were computed.

## Execution and integrity

- Exact attempts and completed responses: 42/42.
- Retries: 0.
- Native stop: 42 EOS completions; no request was repeated.
- Generated tokens: 1,236.
- Recorded completion inference time: 252.60805219999565 seconds.
- Batch wall time: 263.6064353999991 seconds.
- Preflight available physical RAM: 4,892,602,368 bytes, above the frozen 3 GiB gate.
- Minimum available physical RAM observed during execution: 2,459,901,952 bytes.
- Peak server working set: 2,439,245,824 bytes.
- Model artifact SHA-256: `0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc`.
- Effective manifest SHA-256: `47f844ed4a65fb8c6742106a2e5f3b2346e8d1cf5231c2a100da182baaf177b5`.
- Execution audit SHA-256: `6f2201716d7d7fbd1356827cd29891a1e1b000e44757fb16f5e7c329036a59e3`; integrity status `PASS` for 42 attempts, 42 HTTP responses, and 42 results.

The first analysis publication attempt failed only during JSON serialization because two frozen categorical `Counter` objects contained both null and string keys. The incomplete file and failure record remain preserved. Analysis v2 changed only those null dictionary keys to the explicit serialization label `BOUNDARY_CENSORED`; all scientific values, denominators, exclusions, parsers, and raw records remained unchanged. The resulting analysis SHA-256 is `0e690501107c8031dd3774a8b7845e9b1cf2dc61d7969404d70738e7bb32cef6`. A fresh replay reproduced it byte-for-byte.

## Registered primary results

The registered primary analysis retained all boundary-censored and unresolved outcomes as missing and reported logical binary bounds. Missingness was too large for most directional claims. For current-preference choice, the arm summaries were:

| Arm | Resolved mean | Resolved / 6 | Logical bounds |
|---|---:|---:|---:|
| `F_H_RAW` | 0.750 | 4 | [0.500, 0.833] |
| `F_H_REFRESH` | 1.000 | 2 | [0.333, 1.000] |
| `F_H_STRUCTURE` | 0.500 | 2 | [0.167, 0.833] |
| `H_ONLY` | 0.750 | 4 | [0.500, 0.833] |
| `S_F_H` | 0.333 | 3 | [0.167, 0.667] |
| `S_F_NO_H` | 1.000 | 3 | [0.500, 1.000] |
| `S_H` | 0.000 | 1 | [0.000, 0.833] |

Every registered primary contrast for current-preference choice or exact historical-target selection had a logical bound spanning zero. The study therefore did not establish that raw history displaced current preference, that explicit style changed this effect, or that either intervention improved choice reliability.

The strict `full_canonical_both` mention-structure endpoint was complete for several comparisons. Relative to `F_H_RAW`, `F_H_REFRESH` reduced responses mentioning both current option names by 1/3 over all six paired cases. This endpoint measures response structure, not correctness, relevance, or Persona Fidelity.

No resolved record selected an exact frozen historical target. This does not prove absence of broader history interference because the exact parser deliberately leaves uncued, ambiguous, and unregistered formulations unresolved.

The registered narrow operational style conjunction was 0 among all eight assessable S-arm responses, with ten of eighteen S-arm responses missing under the primary boundary policy. It is an exact surface-form check, not a validated measure of linguistic or behavioral Persona Fidelity.

## Reproducible measurement failure

The run exposed a deterministic evaluator–persona interaction. Exactly 11 of 42 responses were boundary-censored. All and only these 11 records:

- began with the preregistered Persona-D expression `My pick:`;
- had the sole boundary reason `unrecognized_line_label`;
- contained a nonempty full first span equal to the unchanged raw response;
- ended with native EOS and were not length-truncated; and
- had no removed prefix or excluded tail.

The three sets were identical with zero cross-cell exceptions. This demonstrates that the generic response-boundary instrument treated a legitimate persona expression as an unknown structural label and created differential missingness. It does not show that explicit S conditioning alone caused the phrase: two affected records were in `F_H_STRUCTURE`, where history could also carry that expression.

This is a reproducible measurement mechanism, not evidence of an internal model mechanism. It shows why persona evaluation must test whether generic output sanitizers systematically censor style-bearing language.

## Explicitly post-hoc sensitivity

Before executing a sensitivity analysis, an output-informed registration froze an all-conditions predicate for the exact 11-record set. A preserved amendment corrected one manually transcribed request identifier before implementation or execution. The sensitivity changed no raw text, token, stop field, alias, parser, or primary analysis; it only treated those complete spans as assessable and reapplied the already frozen v3 exact parser.

The sensitivity output SHA-256 is `e5585887f1ed951fd0a6e488a2b73d6d60774710559028e7b09172c809a56909`, and a fresh replay reproduced it byte-for-byte. It remains secondary and cannot unlock or replace independent validation.

For current-preference choice, sensitivity estimates were:

| Arm | Sensitivity mean | Resolved / 6 | Logical bounds |
|---|---:|---:|---:|
| `F_H_RAW` | 0.750 | 4 | [0.500, 0.833] |
| `F_H_REFRESH` | 1.000 | 2 | [0.333, 1.000] |
| `F_H_STRUCTURE` | 0.750 | 4 | [0.500, 0.833] |
| `H_ONLY` | 0.750 | 4 | [0.500, 0.833] |
| `S_F_H` | 0.667 | 6 | [0.667, 0.667] |
| `S_F_NO_H` | 1.000 | 4 | [0.667, 1.000] |
| `S_H` | 0.667 | 3 | [0.333, 0.833] |

The narrowed paired results still did not support a reliability advantage for either proposed intervention:

| Contrast | Endpoint | Complete-case estimate | Complete pairs | Logical bounds |
|---|---|---:|---:|---:|
| `F_H_STRUCTURE - F_H_RAW` | current-preference choice | 0.000 | 4 | [-0.333, 0.333] |
| `F_H_REFRESH - F_H_RAW` | current-preference choice | 0.000 | 1 | [-0.500, 0.500] |
| `F_H_RAW - S_F_NO_H` | current-preference choice | -0.500 | 2 | [-0.500, 0.167] |
| `S_F_H - F_H_RAW` | current-preference choice | 0.000 | 4 | [-0.167, 0.167] |
| `S_H - H_ONLY` | current-preference choice | 0.000 | 3 | [-0.500, 0.333] |

For `full_canonical_both`, the sensitivity gave exact full-denominator reductions relative to `F_H_RAW` of 1/6 for structure and 1/3 for refresh and `S_F_H`; `S_H` was 1/3 lower than `H_ONLY`. These are reductions in dual-name mention, not demonstrated improvements in semantic correctness.

## Scientific interpretation

Supported by this study:

1. The exact Qwen3.5-2B configuration can complete a bounded persona-conditioned dialogue batch safely on the current CPU host.
2. A generic response-boundary detector can differentially censor legitimate persona-style text; the failure is exactly reproducible in this batch.
3. The generic structure and names-only refresh baselines reduced dual-option mention in these six synthetic cases.
4. Under both the registered analysis and the narrowly defined sensitivity, the data do not establish that either baseline improves current-preference choice.

Not supported:

- a causal internal memory-conflict mechanism;
- reliable raw-history displacement across a population;
- validated linguistic or behavioral Persona Fidelity;
- real-speaker generalization;
- human semantic validity;
- a novel or effective algorithm;
- calibrated confirmatory significance; or
- publication readiness.

`F_H_STRUCTURE` and `F_H_REFRESH` are simple adaptive baselines and overlap generic response-constraint and recency-refresh ideas in prior work. They are not claimed as original algorithms. A fully disjoint synthetic S/F/H replication with a boundary-safe prospective instrument is required before treating any conditioning pattern as independently replicated. Genuine human review and lawfully governed real-speaker data remain separate indispensable dependencies for broad Persona Fidelity and external-validity claims.

## Reproducibility boundary

The private local archive supports analysis reproduction from all raw request and response events, prompt/token hashes, source hashes, model configuration, native stops, timestamps, latency, and memory observations. Public-clone reproduction is partial because the ignored raw journal and local model artifact are not embedded in repository documentation. Generation reproduction is configuration-reconstructable but is not guaranteed bit-identical across environments.
