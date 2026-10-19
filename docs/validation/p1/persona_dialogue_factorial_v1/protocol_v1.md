# Persona Dialogue S/F/H Factorial Development Protocol v1

Maintainer: Yaxin ZHENG. This protocol was frozen prospectively on 2026-10-18. It defines a synthetic, exploratory P1 development experiment; it does not modify or repeat the completed temporal-QA feasibility screen.

## Scientific question

For two constructed personas, how do an explicit style profile (S), a dated current preference fact (F), and role-native archived dialogue (H) individually and jointly affect a small language model's next-turn persona expression and dialogue reliability? History is prospectively assigned as aligned/helpful, outdated/conflicting, or irrelevant. The experiment asks whether useful history can cue behavior, whether obsolete history can override current persona facts, and whether irrelevant history distracts task delivery.

## Design and materials

The frozen machine-readable specification is `prospective_design_v1.json`. It contains two explicitly synthetic profiles, PF_B and PF_C, and three newly authored natural choice cases per profile. Every case is rendered under C0-C7, yielding exactly 48 unique requests. Within a case, current option notes and the current user turn are byte-identical across conditions. H is represented as native user/assistant turns and contains no current option name. Current-preferred choices are balanced A/B globally and within each history regime.

Both current options satisfy the request. F therefore identifies a persona-congruent choice without redefining external factual truth. S supplies a surface and conversational target; H supplies an independently dated behavioral example. These are operational prompt packages, not pure latent mechanisms.

## Frozen execution

Use the exact local Qwen3.5-2B Q4_K_M artifact, pinned llama.cpp backend and official non-thinking native chat template recorded in the JSON. The batch is CPU-only with four threads, context 4096, greedy decoding, seed 42 and at most 96 generated tokens. Cache, warmup, GPU offload and retries are disabled. Execute the 48 requests once in the frozen SHA-256 order.

Preflight must verify every file hash, rendered prompt, native token sequence, context fit, exclusive allocation, cumulative budget, at least 3 GiB available physical RAM and 1 GiB free output space. The batch ceiling is 45 minutes. A safety or integrity failure stops before the next request and preserves the partial journal; it never authorizes a retry or termination of unrelated applications.

The cumulative baseline is 16/1200 autonomous generations and 159.95704690001094/72000 inference seconds, bound to post-Candidate-2 state SHA-256 `1489732ce936860d46fa0001bf1edc2328b65c3f7b5cde386563644558fbba65`.

## Outcomes and analysis

Aliases, reason cues and applicability are frozen before outputs. Deterministic scoring distinguishes resolved choice, supported/contradicted/unresolved reason, answer completeness, narrow task success, current-preference choice, history-favored choice, C6/C7 outdated adoption in conflicting cases, and persona-specific surface/order checks. Unresolved or unavailable outcomes are not zeros. Broad conversational coherence is not automatically scored, and the surface checks are not validated general Linguistic or Behavioral Persona Fidelity.

Report finite-development paired S/F/H effects, all interactions, history-regime strata, case contributions, speaker blocks, joint reliability/fidelity states, logical missing-outcome bounds, native stopping, tokens, latency and memory. No p-values, confirmatory threshold, population generalization, real-speaker claim, outcome-based case selection or automatic expansion is permitted.

## Reproducibility and limits

Archive exact rendered messages, token IDs, prompt hashes, model/runtime identities, attempt-before-call records, raw HTTP bytes, raw text, native stopping, latency, memory observations, derived scores, scorer source and an analysis-reproduction receipt. Preserve all negative and partial results.

Only synthetic data are available in the repository. No consented real-speaker cohort or P4 permission package was found, so this experiment cannot establish real-speaker external validity. Two profiles, six purposive cases, unmatched prompt lengths and a partially verified third-party conversion also limit inference. Any independent validation, human semantic/fidelity study, new model arm or algorithm comparison requires a separate prospective freeze.
