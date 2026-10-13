# P1b Calibration Execution Report

Maintainer: Yaxin ZHENG. Version 1. Formal Protocol v1.1; proposed v1.2 r1 remains unchanged and unadopted. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE.

## Execution decision and result

The explicitly authorized bounded calibration completed **192/192 real local CPU requests**, with **192 responses, 192 persisted results and zero failed requests**. No extra wave, model switch, answer retry or neutral-control generation occurred. This is adapter execution PASS, not acceptance of scientific hypotheses or publication readiness. Human semantic output review remains pending.

Run ID: `20261013T172032-271543cb614847e8ae2ef33cca902701`. Local raw journal: `results/p1b_calibration/development_v1/runs/20261013T172032-271543cb614847e8ae2ef33cca902701`. Original events and timestamps remain immutable. The run started from Git `863c3ab4721c0857ea0f7fa1804f7369df91cda3` with dirty state `True` because the new approval records and registration helper were uncommitted. Frozen inference source hashes matched the mandatory preflight.

| Check | Result | Evidence / limit |
|---|---|---|
| Researcher stimulus review | PASS | 24 cases; 312 preserved positive-criterion judgments; explicit message confirmation of AI-assisted assessment |
| Frozen data / manifest | PASS | Exact byte hashes; no assignments or input edits |
| Pinned files / native backend | PASS | Model/executable hashes before and after; owned b11573-0f701c882 process |
| Live GGUF tokenization | PASS | 192 actual /tokenize responses; exact input IDs match freeze before first completion |
| Input capacity | PASS | 150–434 tokens; plus 96 output tokens = at most 530, below 4096 |
| Native requests and decoding | PASS | 192 serial requests in frozen order; temperature 0, seed 42, cache_prompt false |
| Executed / raw / parsed results | PASS | 192 unique request IDs; no retry or additional generation |
| Response policy | PASS | response_status_v1 and separate_axes_policy_v1 preserved |
| Semantic outcome review | PENDING | Stimulus acceptance does not label generated outputs |
| Neutral comparisons | OPEN / NOT EXECUTED | The 24 prior Wave 1 candidates remain unreviewed; no transfer to P1b |

## Researcher approval provenance

[Registration](validation/p1b/calibration_v1/researcher_review_registration_v1.json) records `reviewer_id=Yaxin_ZHENG`, `review_status=RESEARCHER_CONFIRMED`, `final_decision_authority=researcher`, and `review_method=Researcher confirmation of AI-assisted case-level assessment`. The original 24-row proposal, 312 judgments, master CSV, source quotations and limitations remain unchanged. The completed source copy and official 41-column import are separate artifacts. Approval came from the actual researcher message, not independently hand-entered CSV values or a blinded outcome questionnaire. No review timestamp, second reviewer or agreement statistic was invented; registration times are actual logging times.

The preparation-time `authorized=false`, `executed=false` and pending review flags in frozen inputs were not rewritten. The separate hash-bound authorization, write-ahead events, native responses and result events establish the actual current state. A copied plan flag in a raw result is not evidence that a request was unexecuted.

## Fixed configuration and identities

- Qwen3.5-2B-Base Q4_K_M; llama.cpp `b11573-0f701c882`.
- Model SHA-256: `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`.
- Backend executable SHA-256: `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`.
- Dataset SHA-256: `fb2954ea90950bd9286617e58cff57435f1b6be7b3f775b9d84c9d67ae2e2cf6`.
- Frozen manifest SHA-256: `d73ceb403148b01f7b2c83a51a20165fdd625658e50c04a7ce0caa118ab22869`.
- Base prompt `p1b_transcript_proposed_v1`; condition order seed 714001; decoding seed 42; temperature 0; top_p 1; output budget 96; no declared stop strings; return_tokens true; cache_prompt false.
- CPU threads 4 / batch threads 4; one server slot; context 4096. Native log reports `offloaded 0/25 layers to GPU`, qwen35 architecture and a 2B model. File identity does not independently prove fidelity of upstream third-party quantization.
- The live native endpoint receives integer input IDs. Input evaluated counts agree, all reported cache_n values are zero, and no context truncation occurred. Output IDs were returned and retained. A separate backend array of evaluated input IDs is unavailable; no such observation is invented.

The optional CIM hardware query returned access-denied errors despite PowerShell exit code 0. Its empty CPU/RAM/OS values are **unavailable**, not valid observations. Previous Ryzen hardware attribution remains historical; current thread/offload/slot observations come from this run's server log. Per-request process-memory observations remain in the local journal. Concurrency with lightweight read-only development checks means latency is not an isolated hardware benchmark.

## Logging, interruption and reconstruction

An exclusive claim and writer lock bind the wave to one authorization. Each attempt is journaled before transmission; raw HTTP bytes precede parsing. Failed or uncertain sends are never silently retried. This run required no interruption or resume. The documented resume adapter remains available for a separately authorized continuation of unattempted IDs, not re-generation of successful outputs.

[Machine-readable analysis](validation/p1b/calibration_v1/analysis_v1/analysis_v1.json), [request measurements](validation/p1b/calibration_v1/analysis_v1/request_measurements_v1.csv), [native transport reconciliation](validation/p1b/calibration_v1/analysis_v1/transport_integrity_v1.json), and [hash inventory](validation/p1b/calibration_v1/analysis_v1/execution_inventory_v1.json).

The [command register](validation/p1b/calibration_v1/command_register_v1.json) points to full local captures. Full final suite: `644 passed in 38.27s`; exit code 0; process duration 39.051 seconds. The original pre-generation suite passed 631 tests; 13 new offline accounting tests were added. Final preservation checks are recorded separately in the [integrity report](validation/p1b/calibration_v1/final_integrity_v1.json).

## Errors and retained limitations

An initial inspection helper passed a string to a Path API and raised AttributeError before mandatory preflight. Correcting that helper did not change any experimental source or configuration. The failure record is retained. Mandatory preflight and execution had no failures. One optional literature fetch returned a cache miss; it was not repeatedly retried. The optional denied hardware query remains an explicit observation gap.

- H_L1/H_L2 are simple follow-up baselines; context necessity is not demonstrated. H_L3 retains consecutive User turns, with possible Base continuation effects.
- Unique terminal entities, explicit identity cues and repeated answer patterns allow shortcuts. Designed levels are not validated difficulty rankings or evidence of internal multi-step reasoning.
- Style is partially nested in 12 synthetic speakers. Two cases per speaker are not independent speaker replications. F uses a limited supplementary-fact realization.
- Task family, history relevance and temporal content are not disentangled. Eight cells estimate intervention packages, not isolated history mechanisms.
- S/F/H additions also change context length and inserted content. Without reviewed matched controls, these eight-cell estimates do not isolate effects independent of length, wrapper or semantic content.
- The fixed 96-token budget can censor longer answers. Censorship, first-reply completeness, relevance and factual support remain distinct.
- No independent confirmatory set, model-configuration replication, authentic-speaker validation or neutral-adjusted effect is established. No case is removed based on C0 performance.

## Algorithmic Opportunity Assessment

Execution integrity demonstrates instrumentation, not a new algorithm. Structural observations and pending semantic coverage are assessed separately in [the algorithmic report](P1b_calibration_algorithmic_opportunity.md). No algorithm, model training or extra generation was initiated.
