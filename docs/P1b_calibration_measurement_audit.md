# P1b Calibration Scientific Measurement Audit — v1

Maintainer: Yaxin ZHENG. Formal experimental baseline: Protocol v1.1. Protocol v1.2 Revised Proposed r1 remains prospective and unadopted. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE. Development evidence only; no new inference.

## Audit result and scope

**Instrumentation PASS; semantic measurement OPEN.** Replayed all **192 attempted / 192 completed / 0 failed** requests from run `20261013T172032-271543cb614847e8ae2ef33cca902701`. No responses were regenerated or changed. All saved HTTP response bytes, raw text hashes, prompt/ID/count associations, first spans and parser operations were reconciled; all 192 original review records reconstruct exactly. Current audit baseline Git HEAD is `72d5845c25046a3f6207ccfbf315b1480aa67d8f`; it was clean at the initial inspection. New work is uncommitted. Historical execution Git state remains in its manifest.

The journal has 1781 events and terminal hash `5df2a380ee216979b27cc04048b8c4c3e21c6fdcece849931b4ae8b582bbceef`. [Native transport re-audit](validation/p1b/measurement_audit_v1/native_transport_reaudit_v1.json), [identity re-audit](validation/p1b/measurement_audit_v1/offline_identity_reaudit_v1.json), [summary](validation/p1b/measurement_audit_v1/audit_summary_v1.json) and [all-response audit](validation/p1b/measurement_audit_v1/response_boundary_audit_v1.csv) contain the evidence. The dataset and frozen manifest hashes remain `fb2954ea90950bd9286617e58cff57435f1b6be7b3f775b9d84c9d67ae2e2cf6` and `d73ceb403148b01f7b2c83a51a20165fdd625658e50c04a7ce0caa118ab22869`.

Model hash `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994` and backend hash `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846` were recalculated from the actual local files. The recorded backend is llama.cpp b11573, commit 0f701c882. Native tokenizer response IDs, submitted IDs and evaluated counts match for all 192 prompts. The backend did not return a separate evaluated-input-ID array; this limitation remains explicit. Output IDs are retained. This task replays original real-tokenizer evidence; it does not claim a new live tokenizer observation. Configuration remains CPU 4 threads, context 4096, temperature 0, seed 42, 96-token budget, order seed 714001; inputs 150–434 tokens and no context truncation.

## What boundary inspection adds

Frozen distribution: COMPLETE **0**, TRUNCATED **5**, CROSS_TURN **186**, AMBIGUOUS **1**. Identifiable first spans: **191/192**. Raw and first-span empty counts: **0**. Native stops: length **190**, EOS/EOG **2**. The 186 role-crossing continuations contain multiple visible role markers; marker counts are textual diagnostics, not independently verified discourse turns. Every removed prefix, first span and excluded tail reconstructs the raw text exactly.

COMPLETE under response_status_v1 requires an independent completeness certification that was not supplied during generation. Its zero count does not say all replies failed semantically. Budget termination concerns the full continuation, which may spend most tokens after a completed first reply. EOS likewise does not certify a single response.

| Request / case | Direct observation | Measurement disposition |
|---|---|---|
| 113 / G_L1 C2 | Ends `so it is valid on 2027` at 96 tokens; no excluded tail. Earlier date comparisons and Harbor Lodge are visible | Unfinished date/final clause; assess supported partial content separately. No evidence that the parser removed a completed answer |
| 139 / G_L3 C6 | Unclosed `<think>`; ends `Since March 20` | Reasoning continuation without a separately delivered final answer; human judgment pending |
| 141 / G_L3 C5 | Unclosed `<think>`; ends `The third is for ` | Missing final completion; also inspect the visible date/site assertions independently |
| 143 and 144 / G_L3 C3,C7 | Identical raw prefixes end `2027-03-3`; unclosed `<think>` | Preserve both paired cells, not two independent confirmations; no inferred next tokens |
| 036 / B_L3 C0 | 71-token EOS; first span contains `Factual question:` and a generated question, followed by another Assistant answer in the tail | **Required boundary adjudication.** Frozen AMBIGUOUS / unit_identifiable=false remains. No alternative first reply fabricated |
| 120 / G_L1 C1 | 77-token EOS with another User/Assistant exchange | EOS and CROSS_TURN coexist; judge the first response separately |

All five truncations end at the actual output limit; all retain their complete raw visible prefix with empty excluded tail. Four are the H-present cells of **one** G_L3 case. This supports an observed association in this bank, not a causal claim that history induces reasoning or that a larger budget would solve it. No controlled budget/template comparison was run.

There are **17 first spans literally starting `I will check`**, across B_L2, F_L1, G_L2, H_L1 and H_L2. Some mention a candidate location; do not equate the pattern with 17 confirmed missing answers. D-family first replies often give a crate/locker statement where the question requests a room/building. These observations show why grammatical or factually supported text can still fail to deliver the requested answer. [Diagnostic observations](validation/p1b/measurement_audit_v1/diagnostic_observations_v1.json) retain the complete ID list. No semantic scores were inserted.

## Semantic coverage and denominator policy

| Outcome | Eligible | Automatic semantic scores | Human scores | Pending | Frozen N/A |
| --- | --- | --- | --- | --- | --- |
| conversational_coherence | 192 | 0 | 0 | 192 | 0 |
| factual_consistency | 192 | 0 | 0 | 192 | 0 |
| response_relevance | 192 | 0 | 0 | 192 | 0 |
| temporal_consistency | 88 | 0 | 0 | 88 | 104 |


No assessed Unverifiable count or factual/temporal accuracy can yet be estimated. Missing judgments are 192/88/192/192 as appropriate; they are not failed answers. One unit needs boundary adjudication, five raw prefixes are structurally censored, and human completeness for all 192 is pending. The incomplete/ambiguous units remain eligible. Automatic scorer coverage is zero by design: the city scorer is not used outside its scope.

The split [review guide](P1b_calibration_semantic_review_guide.md) and two review views are ready. Preserve partial factual support independently of answer delivery, temporal attribution, relevance and coherence. False assertions differ from unsupported assertions; missing answers differ from false answers; extra turns differ from first-reply content. Ceiling reduction remains **unverified** until review.

## Structural pairing and uncertainty

| Contrast | CROSS_TURN change (pp) | Exploratory cluster percentile interval (pp) |
| --- | --- | --- |
| C1-C0 | 4.167 | [0.000, 12.500] |
| C3-C0 | 0.000 | [-12.500, 12.500] |
| S | 2.083 | [0.000, 5.208] |
| F | 0.000 | [-3.125, 3.125] |
| H | -2.083 | [-12.500, 4.167] |
| SxF | 0.000 | [-6.250, 6.250] |
| SxH | -4.167 | [-10.417, 0.000] |
| FxH | 0.000 | [-6.250, 6.250] |
| SxFxH | 0.000 | [-12.500, 12.500] |


Each contrast uses all 24 cases nested in 12 speakers. Weights remain the frozen simple/average-main/averaged-interaction definitions; [paired values](validation/p1b/measurement_audit_v1/structural_case_contrasts_v1.csv) retain zeros and failures. C1−C0's +4.167pp comes from B_L3's ambiguous-to-cross-turn transition alone. C3−C0's zero nets that transition against G_L3's cross-turn-to-truncated transition. Neither is a semantic effect or proof of a population null.

Intervals are a **new, post-output exploratory sensitivity analysis**, seed 714004, 10,000 whole-speaker resamples, with all of each sampled speaker's cases/cells. They are percentile intervals for resampling this purposive bank, not guaranteed population confidence, simultaneous intervals or significance tests. Sparse/zero outcomes can produce misleadingly narrow or degenerate intervals. The prior leave-one-speaker-out analysis remains unchanged. The full four-status results are in [the uncertainty file](validation/p1b/measurement_audit_v1/structural_uncertainty_v1.json).

For eventual semantic analysis, [the pre-review contract](validation/p1b/measurement_audit_v1/future_semantic_analysis_contract_v1.json) retains 24 factual paired cases/12 clusters, 11 temporal cases/9 clusters, each condition's factual24/temporal11 denominators, four distinct endpoints, and no C0-correct filtering. Show Correct/Incorrect/Unverifiable/missing/N/A separately. Unknown-outcome bounds propagate within-case signed weights before aggregation; assessed-only descriptions cannot replace the eligible denominator. Ordinal distributions and paired changes accompany descriptive means. No final semantic contrasts are computed now.

## Remaining gates and Algorithmic Opportunity Assessment

Human semantic scoring, unit adjudication and truthful review provenance are required before outcome claims. Neutral controls remain OPEN and no neutral-adjusted comparison is available. Statistical precision, independent material and model/generalization checks remain publication work, not reasons to regenerate this bank. The strongest immediate action is to score existing outputs; [publication readiness](P1b_calibration_publication_readiness.md) and [algorithmic assessment](P1b_calibration_algorithmic_opportunity.md) explain the next gates.

Reproducibility commands, test results, preservation checks and file hashes are retained in [delivery evidence](validation/p1b/measurement_audit_v1/delivery_v1.json). The audit code is [p1b_measurement_audit.py](../tools/p1b_measurement_audit.py). The complete original run remains local; public derivatives alone are not a substitute for archiving native journals and the protected mapping for controlled later unblinding.
