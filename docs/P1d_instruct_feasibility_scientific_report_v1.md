# P1d Instruct feasibility scientific report v1

Maintainer: Yaxin ZHENG. Phase P3/P5; RQ3/4. All semantic judgments below are **AI-assisted proposals, not human-confirmed ratings**. Exactly eight H_none development cases were assessed individually against their full trusted ledger, requested date, question, context and required components. No persona-conditioning effect is estimated.

## Decision and outcome separation

The registered criterion was eight identifiable and semantically complete task answers with no answer-losing cut, followed by separate factual/temporal/fidelity assessment. It was not a rule to maximize factual accuracy. It is **not met**: five replies have complete requested-answer form, two are nonanswers and one is partial. Seven discourse utterances are syntactically finished, which is different from complete task answers. Only two tasks are correctly completed. Main P1d validation and the conditional all-cell S/F/H follow-up remain **NO-GO**.

| Development case | Factual | Temporal | Task | Answer completeness | Supported components | Required |
| --- | --- | --- | --- | --- | ---: | ---: |
| p1d_dev_04_1 | Incorrect | Incorrect | Failure | YES | 0 | 2 |
| p1d_dev_03_0 | Correct | Correct | Success | YES | 2 | 2 |
| p1d_dev_01_0 | Incorrect | Incorrect | Failure | YES | 0 | 2 |
| p1d_dev_07_1 | Correct | Correct | Success | YES | 1 | 1 |
| p1d_dev_05_1 | Incorrect | Incorrect | Failure | NO | 0 | 2 |
| p1d_dev_02_0 | Incorrect | Incorrect | Failure | PARTIAL | 0 | 2 |
| p1d_dev_06_1 | Incorrect | Unverifiable | Failure | NO | 0 | 2 |
| p1d_dev_00_0 | Incorrect | Incorrect | Failure | YES | 0 | 1 |

Factual proposals: 2 Correct, 6 Incorrect. Temporal: 2 Correct, 5 Incorrect, 1 Unverifiable. Task: 2 Success, 6 Failure. Required components: 8/14 explicitly present, 3/14 supported. Three complete wrong answers demonstrate that factual consistency and completeness need not coincide. Relevance: five 5, two 3, one 2; coherence: five 5, two 3, one 2. Identical marginal counts do not imply joint label assignment; item-specific explanations are retained.

Mira, Owen and Vera use January values for May/November requests. Arlo denies evidence and claims November lies outside January–December; this is contradicted, not merely absent support. Tessa describes October–December records as applicable in May and ends mid-statement. Cleo denies the stipulated volunteer role; factual Incorrect uses the persona/context role evidence, while Unverifiable is retained as an alternative if adjudication restricts factual scope to ledger attributes alone. No temporal assertion is supplied by that denial, so temporal Unverifiable remains separate. Nolan's response correctly resolves the context target Quinn, and Ellis supplies the correct November locker.

## Structure, uncertainty and comparison

All eight primary spans are identifiable as candidates; none contains a generated extra role transition. Seven terminate natively at EOS and one at the token budget. Original parser statuses are preserved as seven AMBIGUOUS and one TRUNCATED. `boundary_alias_sensitivity_v1.json` documents the `eos`/`eog` interface mismatch; no alternate text is substituted and no independent boundary accuracy is claimed. Truncation is not the reason for labeling Tessa's explicit date claims incorrect.

Matching uses the exact eight historical Base H_none/96 request IDs and hashes. AI-proposed task success changes from 0/8 to 2/8, descriptively +25 percentage points; this is a noncontemporaneous model/template/quantization configuration comparison. Whole-speaker bootstrap sensitivity (8 purposive clusters, 10,000 draws, seed 716802) is [0, 62.5] percentage points; leave-one-speaker-out differences are 14.29–28.57 points. These are neither population coverage guarantees nor official human-confirmed semantic effects. Historical Base latency has different run conditions; no causal speed claim is made.

The original narrow brief/calm style proposals remain available but do not establish broad linguistic or behavioral fidelity. Behavioral fidelity was not predefined and is not retroactively scored. The new prospective fidelity protocol treats short-answer opportunity and independent review explicitly. Review was model-aware AI analysis, not a blind human study. A condition-masked, score-free human form is supplied; output content can still reveal model or configuration.

## Algorithmic Opportunity Assessment

1. **Observed Failure Modes:** Wrong intervals, false evidence-absence claims, incomplete relation-chain delivery and role denial occur under H_none. Historical persona override is not identified.
2. **Existing Methods and Published Prior Art:** Entity/time filtering, component checks, LongMemEval, FPPS, CoVe, RARR, typed admission and temporal graphs are relevant; see the v7 matrix.
3. **Potential Algorithmic Improvements:** Typed support/uncertainty witnesses and persona-preserving channels are a candidate scaffold only. The new offline rules tie a simple declarative baseline; no original algorithm or model improvement is established.
4. **Validation Feasibility:** A separately proposed eight-request P5 oracle-evidence test can estimate generation headroom before any new selector experiment. It changes evidence length, selection and positions jointly and cannot allocate unique causal blame.
5. **Publication Value:** These failures inform measurement and model adequacy for the core S/F/H study. They are not independent validation, a pure post-training effect or manuscript readiness.

## Review and next step

Full proposals: `docs/validation/p1d/instruct_smoke_v1/measurement_v1/AI_proposals_UNCONFIRMED_v1.csv` and JSON; raw text/evidence/reasons/alternatives/provenance are included. Human fields are blank. `independent_review_without_scores_v1.csv` supports review before exposure to proposals. No new administrative adoption is inferred. The consolidated next decision packet binds the optional future P5 scope and preserves all previous approvals.
