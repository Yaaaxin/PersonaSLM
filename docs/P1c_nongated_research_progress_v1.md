# P1c nongated research: measurement baseline and statistical implementation

Maintainer: Yaxin ZHENG. This work uses existing development records only. No P1c generation, new annotation or scientific-policy adoption occurred. The [three-item approval packet](P1c_final_consolidated_approval_v1.md) remains the sole execution gate.

## Implemented statistical support

`tools/p1c_paired_statistics.py` implements original signed cell weights, case-level contrasts, equal speaker means, whole-speaker percentile bootstrap, leave-one-speaker-out sensitivity, and unknown-outcome identification bounds. Unknown cells are not reweighted away. The all-eligible point estimate remains unavailable if required observations are unknown; a separately labeled assessed-only sensitivity discloses its selection. Binary ranges and ordinal 1–5 ranges remain distinct. Tests check all 16 registered weights, interaction scale, missingness bounds, equal-speaker weighting, replay and invalid values using synthetic numerical fixtures only. No fixture is a P1c observation.

This is scalar statistical infrastructure, not an annotation importer or a completed P1c analysis. Full category distributions, applicability and ordinal sensitivities must accompany its eventual use under the approved policy. Six speaker clusters cannot yield stable population-level claims. No empirical ICC is estimated. Policy definitions were verified without changing their source versions.

## Bounded answer-component baseline

The [frozen baseline policy](validation/method_development/component_baseline_v1/baseline_policy_v1.json) defines a single rule: all required component values must appear as contiguous case-insensitive word-token sequences in the frozen first reply. The rule was saved before its evaluation; this is still a retrospective development diagnostic because P1b outcomes and aggregate labels were already known. It is not an independent or preregistered validation study.

All 192 original responses, 24 paired cases and 12 speakers were retained. Source and first-reply hashes were verified. No output was changed, and no human rating was added. Reference components are oracle evaluation metadata; this baseline is not a deployable evidence-grounding verifier.

| Predictor of researcher-confirmed FULL_ANSWER | True positives | False positives | False negatives | True negatives |
|---|---:|---:|---:|---:|
| Always predicts full | 110 | 82 | 0 | 0 |
| Never predicts full | 0 | 0 | 110 | 82 |
| Literal component presence | 110 | 5 | 0 | 77 |

These are response-level diagnostic counts, not 192 independent validation observations or factual-accuracy estimates. The reference is researcher-confirmed AI-assisted coding, not independently replicated annotation. The literal baseline's zero observed false negatives does not establish general sensitivity to paraphrases.

The five false positives are retained in [per-response diagnostics](validation/method_development/component_baseline_v1/case_response_diagnostics_v1.csv):

| Response | Existing case | Preserved delivery label | Observable limitation |
|---|---|---|---|
| BR001 | p1b_G_L2 | PARTIAL_ANSWER | Lists several sites and date ranges instead of selecting the requested answer |
| BR096 | p1b_G_L1 | PARTIAL_ANSWER | Contains the target site but ends in an unfinished date phrase |
| BR002 | p1b_F_L1 | NO_FINAL_ANSWER | Says it will check the named shelf; a promise is not an answer |
| BR004 | p1b_F_L1 | NO_FINAL_ANSWER | Same observable promise-to-check pattern |
| BR183 | p1b_F_L1 | NO_FINAL_ANSWER | Same observable promise-to-check pattern |

These five records represent three cases and two families, not five independent mechanisms. No output-dependent lexical exception was added to improve these scores. Evaluation reconstructed twice with identical rows and confusion counts. Actual local execution time and source hashes are in [reproducibility metadata](validation/method_development/component_baseline_v1/reproducibility_v1.json); peak RAM was not measured. No inference latency or generation improvement is claimed.

## Algorithmic Opportunity Assessment

### 1. Observed Failure Modes

Answer mentions can coexist with promises, lists of alternatives and incomplete user-facing delivery. P1b also retains factual/temporal errors and cross-turn continuations; those observations alone do not isolate persona interference or retrieval failure. No P1c effects have been observed.

### 2. Existing Methods and Published Prior Art

Literal checklists and word-boundary matching are known engineering. [Chain-of-Verification](https://aclanthology.org/2024.findings-acl.212/) already uses separate verification questions and revision; [RARR](https://aclanthology.org/2023.acl-long.910/) studies attribution-oriented revision. These are required future comparison families, not implemented or beaten baselines here. The [versioned literature monitor](related_work_novelty_matrix_monitor_v1.md) also identifies direct overlap in temporal memory and admission methods.

### 3. Potential Algorithmic Improvements

An answer-act/component detector that distinguishes assertions from promises and alternatives is an incremental candidate. A detector with access to gold answer strings is not an original deployable algorithm. Reject the idea of replacing human task-success labels with this literal rule. Do not retrofit hand-picked exceptions to the five observed failures.

### 4. Validation Feasibility

Before improving a detector, freeze separate development rules, collect independent templates containing assertions, negations, promises, paraphrases and alternative lists, and obtain valid semantic references. Compare the simple baseline, structured-answer requirements and published verification approaches under declared information access and compute. Ablate answer-act detection versus component coverage; evaluate false alarms and missed completion separately. Generation-based repair, fidelity trade-offs and independent effectiveness remain untested and require a separately authorized experiment.

### 5. Publication Value

This is **Level 0: engineering diagnostic**, supporting measurement caution. It is not a replicated finding, identified new mechanism or validated algorithm. The empirical path remains viable independently of algorithm success. A useful PLOS ONE contribution still needs stronger independent evidence, credible measurement and transparent uncertainty; a successful import or test suite does not establish readiness.
