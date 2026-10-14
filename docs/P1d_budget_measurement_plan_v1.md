# P1d development budget measurement plan — v1

Maintainer: Yaxin ZHENG. This operational plan implements the authorized development diagnostic and the adopted P1d rubric. It does not amend the main-study estimands or authorize any further inference.

The exact authorized manifest is `510e46b214dda23dea2a3e5462d44982d25b7a9db022626a7a5a1ba504d5e039`. Each of eight development cases has six condition blocks observed at 96, 192 and 256 output tokens. Compare budgets on all 48 blocks, aggregate six block contributions within each of eight speakers, and retain failed or unresolved requests on the fixed denominator. These are eight purposively constructed development clusters, not 144 independent participants. No E/V contrast sign will enter output-policy selection.

## Primary measurement and AI assistance

Keep `response_status_v1`, its exact first span, full raw continuation and native termination unchanged. If `unit_identifiable` is false, primary semantic scoring is boundary-unresolved, with blank ordinal scores, Unverifiable claim/temporal proposals, Uncertain task/completeness and unscorable components. This records a measurement state, not evidence that the output made unverifiable claims. An identifiable budget-censored span can still contain a complete answer. COMPLETE is not automatically assigned from punctuation or a semantic proposal.

Score relevance from responsiveness to the requested action; coherence from organization and continuity with fixed context; factual consistency from material claim support; temporal consistency from asserted dates and requested-time selection; task success from complete supported delivery without material false claims. Independently list present and supported components. A complete wrong answer may be semantically complete, relevant and coherent. A correct partial answer is not task success. Narrow style fidelity is separate. No common score assignment or composite reliability endpoint is allowed.

For every AI proposal preserve the exact span, claim/evidence references, component evidence, ordinal justifications, uncertainty and plausible alternative. Human adoption fields remain blank. Exact duplicate spans may share an AI assessment only when question, evidence, date, fixed context and style are also identical; record every copied assessment link. This is deduplication of identical measurement inputs, not independent review. The semantic CSV hides conditions and caps, but the analyst prepared execution materials and can access the mapping; no independent or perfect blinding is claimed.

## Budget decision and uncertainty

Apply the existing thresholds unchanged: at least 44/48 semantically complete first replies and no more than 2/48 unresolved boundaries; prefer the smallest qualifying cap. Completion is assessed separately from factual accuracy and supported task success. Report both, plus required components, possible answer truncation, native EOS, cap termination and additional dialogue. If unresolved completeness can change qualification, report qualification bounds and require scientific adjudication. AI-only qualification is provisional until researcher adoption. No qualifying cap means NO-GO for a claimed adequate output policy.

Report paired changes for 192−96, 256−96 and 256−192, case/family contributions, leave-one-speaker-out ranges and 10,000 whole-speaker bootstrap sensitivity draws (seed 716707). These are descriptive diagnostics; no confirmatory p-values or guaranteed population coverage. For unknown binary outcomes retain [0,1] and signed paired-difference bounds, without renormalizing cells. Report all three comparisons and all outcomes, not a selected favorable contrast. This calibration does not replace the main 16-contrast registry or its primary multiplicity family.

## Boundary baselines and robustness

Compare the previously implemented frozen parser, native-EOS-only extraction, literal role-stop shadow, anchored role/section extraction and fence-aware extraction on identical saved strings. The new prefix-locality diagnostic asks whether a later suspicious label affects recognition of an earlier role-delimited span. It uses no answer key or treatment assignment and is an engineering adaptation, not a novel algorithm. Preserve all candidate offsets; do not certify them or replace primary spans. Template/stop/constrained-generation methods cannot be evaluated causally by offline text cutting.

Compare generated token prefixes and primary span equality across caps, distinguishing actual output divergence from parser changes induced by a longer tail. Candidate agreement is not independent boundary accuracy. Independent human boundary judgments and semantic answer-loss assessment remain necessary. Microbenchmarks exclude model inference and I/O; record process CPU and wall time separately and disclose concurrent calibration load.

The development prompts are shorter than the future candidate bank and share authored ledger construction. Even a passing development result does not validate unseen templates, longer prompts, Instruct operation or the main 2,016-request cohort. Any new main budget or stopping policy must be explicitly included in the prospective execution decision.
