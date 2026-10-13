# P1b Calibration Measurement Report

Maintainer: Yaxin ZHENG. Version 1. Formal Protocol v1.1; proposed v1.2 r1 remains unchanged and unadopted. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE.

## Coverage and scientific status

All 192 continuations are available. There are **zero human outcome annotations** and no approved automatic semantic scorer for this bank. Therefore factual accuracy, temporal accuracy, semantic completeness rates and semantic S/F/H effects are **not yet estimated**. Zero scored Unverifiable labels means no semantic assessment has been imported, not that every output is verifiable.

| Outcome | Eligible | N/A | Automatically scored | Human scored | Pending |
|---|---|---|---|---|---|
| conversational_coherence | 192 | 0 | 0 | 0 | 192 |
| factual_consistency | 192 | 0 | 0 | 0 | 192 |
| response_relevance | 192 | 0 | 0 | 0 | 192 |
| temporal_consistency | 88 | 104 | 0 | 0 | 88 |

Structural labels: **COMPLETE: 0, TRUNCATED: 5, CROSS_TURN: 186, AMBIGUOUS: 1**. The frozen parser identifies a unit in 191/192 outputs; 0 extracted first replies are empty and 0 raw continuations are empty. Identifiability and visible text do not establish semantic completeness. Each record retains native termination, full raw continuation, first span, removed prefix, excluded tail and token counts.

## Evaluation contract and masked packet

Use [the 192-row outcome form](validation/p1b/calibration_v1/analysis_v1/output_human_review_v1.csv) and [review guide](P1b_calibration_output_review_guide.md). All human fields are blank. The separate local treatment mapping was frozen before observing outputs. Generated text and prior researcher knowledge may compromise perfect masking; record actual access and assistance rather than claiming independent blinded annotation.

Factual and temporal outcomes use Correct, Incorrect, Unverifiable and predeclared Not Applicable. A supported partial statement can be Correct while the requested answer remains incomplete. Unsupported attribution is not automatically a verified contradiction. Relevance and coherence retain separate 1–5 ratings. Every eligible missing/unscorable output stays in its denominator with its reason. Neither CROSS_TURN nor TRUNCATED is a factual error rule. Do not use the P0 city checker, substring occurrence or the source oracle as a free-text scorer.

The first request, `P1B-CAL1-001`, is retained as an execution-order-selected illustration: its first reply names “Maple Counter”, whereas the frozen April 5 reference component is “Birch Counter”. This source/output discrepancy is a review target, not a registered human judgment or an estimated error rate. It does not identify a persona mechanism. No stimulus or generation setting was changed after seeing it.

## Ceiling effects and Wave 1 comparison

Wave 1's researcher-confirmed 72/72 factual and 48/48 temporal Correct results remain unchanged. This calibration's ceiling status is **unresolved until valid semantic scoring**. A few conspicuous discrepancies cannot demonstrate bank-level discrimination, while syntactically smooth replies do not prove a remaining ceiling. Different task content, global date exposure and prompt realization prevent attributing a between-wave difference solely to difficulty.

Family and designed-level structural tables are in [the structural report](P1b_calibration_structural_analysis.md). They describe output form, not empirical cognitive difficulty. Future analysis must separate factual support from component completion, temporal date selection, relevance and extraction agreement. Keep 24 paired cases and 12 speaker clusters; no C0-correct filtering.

## Scientific limitations and Algorithmic Opportunity Assessment

- H_L1/H_L2 are simple follow-up baselines; context necessity is not demonstrated. H_L3 retains consecutive User turns, with possible Base continuation effects.
- Unique terminal entities, explicit identity cues and repeated answer patterns allow shortcuts. Designed levels are not validated difficulty rankings or evidence of internal multi-step reasoning.
- Style is partially nested in 12 synthetic speakers. Two cases per speaker are not independent speaker replications. F uses a limited supplementary-fact realization.
- Task family, history relevance and temporal content are not disentangled. Eight cells estimate intervention packages, not isolated history mechanisms.
- S/F/H additions also change context length and inserted content. Without reviewed matched controls, these eight-cell estimates do not isolate effects independent of length, wrapper or semantic content.
- The fixed 96-token budget can censor longer answers. Censorship, first-reply completeness, relevance and factual support remain distinct.
- No independent confirmatory set, model-configuration replication, authentic-speaker validation or neutral-adjusted effect is established. No case is removed based on C0 performance.

The immediate information gain comes from reviewing existing responses. No corrective verifier is justified merely by lack of automated coverage. The [algorithmic assessment](P1b_calibration_algorithmic_opportunity.md) separates an instrumentation problem from a demonstrated semantic failure. [Machine-readable analysis](validation/p1b/calibration_v1/analysis_v1/analysis_v1.json), [request measurements](validation/p1b/calibration_v1/analysis_v1/request_measurements_v1.csv), [native transport reconciliation](validation/p1b/calibration_v1/analysis_v1/transport_integrity_v1.json), and [hash inventory](validation/p1b/calibration_v1/analysis_v1/execution_inventory_v1.json).
