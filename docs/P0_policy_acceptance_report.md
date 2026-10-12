# P0 Frozen Policy and Holdout Acceptance Report

Recorded 2026-10-12T19:19:43.094673+00:00. Paper: **Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models**. Research Protocol v1.1, English primary language, Real-Speaker Persona Modeling. Maintainer: Yaxin ZHENG. **Overall P0: PARTIAL; P1: BLOCKED.**

## Frozen policies and independent cases

The [response policy](P0_response_status_policy_v1.md), version `response_status_v1`, and [evaluation policy](P0_evaluation_policy_v1.md), version `separate_axes_policy_v1`, were frozen at **2026-10-12T19:09:12.410208+00:00**. Sixteen new development software cases and their checks preceded the freeze. The separate 24-case software holdout and six new real-inference cases were authored after that freeze and sealed at **2026-10-12T19:10:31.766880+00:00**, before evaluation or generation. Sources and policy documents were not edited after holdout access. No prompt or stop optimization reused the previous four development tasks.

The [freeze manifest](validation/P0_response_policy_freeze_v1.json) and [holdout seal](validation/P0_response_holdout_seal_v1.json) preserve versions, hashes, exact inputs, prompt texts and configuration. The local freeze additionally contains exact implementation snapshots and historical inventories. All six real cases use unchanged C0 `transcript_base_v1`, stop=[], 96 maximum new tokens, seed 42, temperature 0, top_p 1, CPU 4/4 and context 4096. Selection is all six predeclared cases, not a subset chosen after observing answers.

## Boundary-classification results

The [software holdout](validation/P0_response_status_holdout_v1.json) yielded **24/24 status matches (100%)** and **24/24 exact first-span matches**, with lossless raw reconstruction in every case. Confusion matrix: each of COMPLETE, TRUNCATED, CROSS_TURN and AMBIGUOUS has six expected examples and six matching predictions; all off-diagonal cells are zero. Six cases remain AMBIGUOUS: hold19–hold24. Decided coverage is **18/24 = 75%**, with 18/18 agreement among decided examples. Uncertain cases remain in the overall denominator.

These are authored software-contract expectations. They are disjoint from development examples but not independently human-labeled or statistically representative model outputs; the same author knows the policy. The six fixture completeness judgments used in COMPLETE examples are explicitly engineered inputs, not human evaluations. This result does not establish human semantic-completeness accuracy.

Real run: **`20261012T191040-7205faad677e426c8838576739d49717`**. Six requests completed, all raw outputs nonempty, all generated 96 tokens and stopped at the limit; no EOS/EOG was reported. The [additive policy analysis](validation/P0_response_policy_real_holdout_v1.json) records **5 CROSS_TURN, 1 AMBIGUOUS, 0 COMPLETE, 0 TRUNCATED**. The cap remains separately recorded even where an earlier role transition supports CROSS_TURN. Cases 001–005 have observed role continuations; 006 has predeclared literal-role content and an inline role reference, so its unit is not automatically certified. No independent real-output labels were supplied: real boundary accuracy is **unavailable**, not 100% or zero.

A stop signal alone is insufficient for semantic completeness. COMPLETE requires a supported boundary plus a separately supplied, raw-hash-bound completeness judgment. Missing judgment remains UNCERTAIN. A model may continue a transcript after supplying a useful first sentence; this is measurable model behavior, not by itself an instrumentation failure. Unknown roles, inline/quoted/fenced delimiters and literal-content collisions remain conservative ambiguity routes. No new generation was run to improve these results.

## Evaluation and controls

The frozen policy scores the identifiable first reply/prefix separately from excluded continuations. New factual accounting is **1 Correct, 0 Incorrect, 5 Unverifiable, 0 Not Applicable**, with all six pre-eligible cases retained. This is not a factual-accuracy estimate. The narrow rule does not certify `resides in`, `is currently in`, arbitrary date constructions or address statements; it therefore abstains on otherwise plausible text rather than silently calling it wrong. No evaluator was modified after these observations. Temporal consistency, relevance and coherence remain separately pending independent annotation; they are never copied from the factual label.

All old v1/v2/v3 scores and raw journals remain unchanged. The runner's legacy evaluation remains identifiable in its original record; the new policy is an explicitly versioned sidecar, not a silent replacement. The prospective rule retains Unverifiable in primary eligible accounting and keeps Not Applicable separate according to frozen applicability. No Persona effect, general factual accuracy or causal interpretation is claimed.

The [English annotation guide](P0_neutral_annotation_form_v3.md) and 40-row form are complete and match the actual original frozen materials. [Readiness check](validation/P0_neutral_review_readiness_v1.json): **0/40 human reviews; OPEN**, no submitted human-review files. The importer is ready and regression-tested; no labels were generated to close this requirement.

## Acceptance checklist

| Requirement | Status | Evidence and remaining limitation |
|---|---|---|
| Protocol, English language and Real-Speaker research identity | PASS | Protocol v1.1 and language addendum unchanged; new original-English fictional P0 inputs only |
| Real CPU inference, pinned model and backend | PASS | Six new requests, all received, on the same GGUF/build; no Persona-effect claim |
| Frozen response instrumentation | PASS within declared scope | 24/24 software status/span checks; five real cross-turn observations and one conservatively ambiguous literal-content task; no natural-EOS requirement |
| Independent semantic boundary accuracy on model outputs | PARTIAL | No human ground truth; real-output accuracy unavailable, never replaced with software accuracy |
| Separate evaluation axes and uncertainty accounting | PASS within declared scope | `separate_axes_policy_v1`; four factual categories; separate completeness, relevance, temporal and coherence records; old scores retained |
| General semantic evaluation | PARTIAL | City grammar is narrow; 5/6 new first replies remain Unverifiable; independent annotations remain required for open-ended research |
| Forty real-tokenizer-matched controls | PASS | Original CSV/JSON reconstructed from frozen prompt material, all deltas zero |
| Independent neutral-control validity | PARTIAL / OPEN | 0/40 human reviews, no submitted annotations; sole outstanding mandatory control-validation action for this scoped P0 sign-off |
| Annotation import readiness | PASS | Existing versioned importer tested for missing/invalid labels, missing/duplicate rows, version/material changes, reviewer ID, timestamps and completeness; simulated inputs only |
| Raw records, input reconstruction and failures | PASS | All 20 prior journal inventories unchanged; new journal replayed twice identically; 134 historical plus 6 new responses = 140 |
| Automated tests | PASS | 223 passed, 0 failed, 0 warnings reported, 13.28s pytest, exit 0 |
| Vendor-neutral attribution and maintainer Git policy | PASS | 17 references in 11 files neutralized; no manually-written-code claim; original attribution bytes archived, all commits/pushes remain researcher-managed |
| Overall P0 acceptance | PARTIAL | Neutral-control independent review is OPEN; scoped instrumentation checks do not certify general semantic accuracy |
| P1 execution | BLOCKED | No P1 has started; requires P0 acceptance and separate authorization |


## Mandatory blockers versus limitations

**A — Mandatory:** obtain independent review of the 40 neutral controls; retain six ratings, reviewer identity, version and actual time; resolve FAIL/UNCERTAIN findings transparently. Any revised control needs a new version, zero-tolerance tokenizer matching and renewed review. Do not enter P1 while this remains open.

The previously missing response-status and scoring-unit policies are now implemented, frozen and checked on separate software and real holdouts. This closes the scoped instrumentation/policy-definition actions, not the scientific validation of every semantic judgment. Future use must invoke and log these explicit versions and retain ambiguity/manual routing; legacy substring scores alone remain unsuitable as scientific ground truth.

**B — Measurable limitations:** Base-model continuation, no natural EOS, length censoring, conservative ambiguity, narrow evaluator coverage, pending real-output semantic annotations, unavailable evaluated input-ID arrays, third-party upstream quantization uncertainty, incomplete old C0 metadata, and local raw-archive availability. They qualify claims; they do not require every output to be complete, every tool to expose an unsupported interface, or independently reproduced official-weight equivalence before a scoped pilot. P1 open-ended analysis must still obtain the independent annotations required by the existing protocol.

**C — Future improvements:** richer boundary grammars, more representative independently annotated boundary benchmarks, broader semantic/temporal evaluators, Base/Instruct comparisons, EOS/stop redesign and cross-model performance studies. They require new development/holdout versions where relevant. None was performed by adapting the frozen policy here.

## Preservation, tests and attribution

All 20 existing journal file inventories match the pre-session freeze. The new six-case journal was chain-checked and reconstructed twice identically; prior audited journals retain their original status and hashes. Engineering commands/errors are separate from model experiment journals under `results/p0_acceptance_policy/20261012T190050/`. The new manifest records Git HEAD `1c9bfc3791f7f5cb4b4bda78cd02e2580f0429da`, dirty state, exact source/input snapshots and pinned hashes.

GGUF SHA-256: `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`. Executable SHA-256: `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`; llama.cpp build 11573 / `0f701c882`. Preflight/postflight checks and native server logs are retained. Missing independently evaluated input IDs are not invented. Identical specifications/seeds are not a cross-platform determinism guarantee.

Final tests: **223 passed, 0 failed, 0 warnings reported**, pytest **13.28s**, process **13.894s**, exit **0**. Run time: 2026-10-12T19:14:04.806138+00:00 to 2026-10-12T19:14:18.700372+00:00. Tests overlapped offline auditing, not real generation; timing is not a performance benchmark.

The researcher's vendor-neutral documentation correction replaced 17 product references across 11 files. It changed attribution wording, one diagnostic reviewer label and an equivalent private-directory ignore pattern; AST/payload checks confirm no research logic or measurement changes from that correction. Originals are archived by hash; the edited public evidence JSON differs only in its reviewer attribution. Historical hashes still refer to the preserved originals. See [attribution audit](validation/P0_vendor_neutral_attribution_audit.json). Automated assistance is acknowledged neutrally rather than falsely claiming exclusively manual implementation. Research objectives, protocol, measurements, commands and Git history were not rewritten.

All current-session command captures and early engineering errors are indexed in [command evidence](validation/P0_policy_acceptance_commands.json). Initial patch path and missing capture-directory errors were corrected before freeze; the unrecorded child test result is not claimed. No Git commit/push, P1, LoRA or unrelated application work occurred.
