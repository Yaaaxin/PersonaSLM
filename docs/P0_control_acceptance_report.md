# P0 Control Validity and Human Annotation Acceptance

Recorded **2026-10-12T20:13:26.793933+00:00**. **Overall P0: PARTIAL. Human annotation completion: PASS (40/40). Control validity: PARTIAL, resolution OPEN. P1: NOT STARTED / BLOCKED pending methodological closure and separate researcher approval.**

Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Research Protocol v1.1. Primary language: English. Research target: Real-Speaker Persona Modeling. Maintainer: Yaxin ZHENG. This is a P0 methods/engineering decision, not a scientific comparison or protocol amendment.

## Current acceptance checklist

| Requirement | Status | Evidence | Remaining limitation / action |
|---|---|---|---|
| Frozen objectives, S/F/H, tracks, English scope and Git policy | PASS | Protected files unchanged; no P1, training, unrelated application access or Git mutation | Researcher alone authorizes changes and experiments |
| Real CPU model execution and pinned files | PASS within recorded scope | Existing real inference retained; new tokenizer-only run uses same Qwen3.5-2B-Base Q4_K_M / b11573 | No fresh generation or performance benchmark claimed |
| Input/evidence reconstruction | PASS | 100 original prompts reconstructed byte-for-byte; all 100 token-ID arrays reproduced by real backend | Twenty repeated synthetic cases, one speaker/style |
| Original token matching | PASS | 40/40 exact matches, tolerance zero | Does not prove semantic validity |
| Response/evaluation instrumentation | PASS within frozen scope | `response_status_v1`, `separate_axes_policy_v1`, previous holdout and replay evidence unchanged | Ambiguous units/manual routing, narrow factual coverage; completeness distinct from truth |
| Human annotation completion | PASS | `researcher_verified_annotation_v1`, registration revision 2, Yaxin_ZHENG, 40 unique reviewed rows and 240 core judgments | AI-assisted final review, not blind; original review time unavailable |
| Semantic-control suitability | PARTIAL / OPEN | Researcher overall: PASS 0 / PARTIAL 40 / FAILED 0; all 40 neutrality ratings uncertain | Resolve style contamination, topic/information imbalance and identity/coherence ambiguity |
| Dimension-level repair routing | PARTIAL | Separate software disposition: PASS 0 / PARTIAL 20 / FAILED 20 | Twenty N_style extra-style failures; this does not overwrite the human overall rating |
| Annotation provenance/version comparison | PASS for available files; PARTIAL for earlier lineage | Raw versions archived; 0 judgment changes between available versions; metadata changed in 40 rows | Untouched AI original, initial independent pass and declared intermediate file absent; total earlier changes unknown |
| Candidate controls | PARTIAL / DEVELOPMENT ONLY | Three new cases, 132 attempts; N_history 3/3 matches; N_style 0/3, best +2/-3/-3 | No candidate semantic approval or generation; old controls unchanged |
| Follow-up annotation tooling | PASS | Locked English packet and quote-validating importer; original strict v3 importer unchanged | No fabricated follow-up reviews, second reviewer, consensus or agreement |
| Historical logs/integrity | PASS | 21 original journal inventories unchanged; all 22 current journals chain-verified | Hash integrity is not cryptographic proof of independent authorship |
| Researcher annotation reconstruction | PASS | Re-import reproduces saved content exactly excluding actual registration time | Software validates structure; human authenticity rests on researcher attestation |
| Automated tests | PASS | 263 passed, exit 0 | Software tests are not experimental or human ground truth |
| Model upstream equivalence / unsupported evaluated-ID arrays | PARTIAL, documented limitations | Pinned artifact/backend and supported token accounting | No independently reproduced quantization equivalence or invented missing backend IDs |
| P1 preparation | PARTIAL (proposal only) | Design proposal and nine-study primary-source novelty matrix | No final confirmatory set, power claim, proven novelty or P1 execution |
| Overall P0 research acceptance | PARTIAL | Engineering checks and review completion pass, control-validity findings unresolved | Do not convert reviewed-but-uncertain controls into PASS |

## What still prevents acceptance

The mandatory remaining issue is **valid experimental controls or an explicitly approved, defensible interpretation of their replacement contrasts**. Human review is now complete; requesting another reviewer merely because this review was AI-assisted would be a new requirement and is not used to keep P0 open. The observed unresolved findings themselves keep control validity open.

N_style has a confirmed extra-style cue in all 20 rows. N_history replaces relevant residence dialogue with document descriptions; matching tokens, dates and roles does not separate content relevance from historical formatting. Ten history rows also identify implicit speaker-reference binding. All 40 semantic-neutrality ratings remain uncertain. A future approved revision must preserve the old artifacts, pass exact matching and receive real semantic review. The unsuccessful development candidates are evidence of remaining work, not a reason to relax tolerance or revise old results.

An adequate single-reply policy need not force every Base-model response to end naturally. Existing cap/continuation behavior is a measurable model limitation under the frozen response/evaluation policies. Missing backend interfaces, unverified upstream quantization fidelity, initial AI-review edit history and lack of a second control reviewer qualify claims but are not additional blanket P0 gates. Open-ended scientific output judgments must still follow the protocol's later independent annotation requirements.

## Evidence and test results

**263 passed, 0 failed, 0 warnings reported**, pytest **10.11s**, process **10.638s**, exit **0**. Actual test interval: `2026-10-12T20:08:42.850912+00:00` to `2026-10-12T20:08:53.488847+00:00`.

Initial new-module tests: **29 passed, 1 failed**, due to a test fixture using an out-of-project temporary directory. The fix configured that fixture as a temporary repository; the production path restriction was retained. Targeted rerun: **30 passed**, exit 0. Eight further resolution tests and two provenance/time checks are included in the final 263. The failed test log remains available.

[Neutral diagnostic](P0_neutral_control_diagnostic.md); [human registration report](P0_researcher_annotation_report.md); [latest registration](validation/P0_researcher_verified_annotation_v1_revision2.json); [version differences](validation/P0_researcher_annotation_version_comparison_v1.json); [tokenizer results](validation/P0_control_tokenizer_validation_v1.json); [delivery checks](validation/P0_neutral_validity_delivery_v1.json); [P1 proposal](P1_experimental_design_proposal.md); [related-work matrix](related_work_novelty_matrix.md).

No raw generation, historical score, frozen policy or Protocol v1.1 content was edited. All changes remain uncommitted for researcher review.
