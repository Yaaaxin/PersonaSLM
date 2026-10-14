# P1c structural boundary analysis v1

Maintainer: Yaxin ZHENG. Exploratory AI-assisted diagnostic; no human boundary adjudication is registered.

## Preserved primary policy

The original response_status_v1 distribution remains CROSS_TURN 64, AMBIGUOUS 8, COMPLETE 0, TRUNCATED 0. All 72 raw continuations and parser traces remain unchanged. The 64 identifiable first replies received substantive Stage A suggestions. The eight ambiguous candidates received Unverifiable and numerical nulls, rather than an invented primary first reply. Native output-limit termination occurred 70 times and EOS twice.

Stage B examined all eight full continuations after Stage A was frozen. Each contains an initial declarative answer followed by `USER QUESTION:` or `RECENT CONVERSATION:`. These section headers are not equivalent to a validated native role boundary. A subsequent generated Assistant span may be incomplete even when the initial sentence is complete.

## Separately versioned alternative spans

The post-output sensitivity takes the literal raw prefix before the first observed section header, preserving leading whitespace, start/end offsets, UTF-8 hashes and all excluded text. It was applied to **all eight**, regardless of correctness. It does not choose the best answer from later turns, change native stop reasons or reclassify any record. The rule is a limited diagnostic fitted to these observed formats, not a validated generic parser.

| ID | Native stop | Prefix content and reference | AI-only secondary suggestion | Boundary alternatives / adjudication |
|---|---|---|---|---|
| PC010 | EOS, 85 tokens | Orchid + Thursday, both requested components | F/T Correct; task 1; coverage 1; complete YES | Subsequent USER QUESTION changes topic to music. Decide whether the initial declarative sentence is an attributable reply rather than part of a generated document. |
| PC023 | EOS, 93 | Orchid + Thursday | F/T Correct; task 1; coverage 1; complete YES | “on a Thursday” is treated as service-day wording, with relevance/coherence 4. Repeated question and later answer remain excluded; adjudicate wording and boundary independently. |
| PC033 | Limit, 96 | Silver + Tuesday; expected Maple + Tuesday | F Incorrect; T Unverifiable; task 0; coverage 0.5; complete YES | Silver belongs to the colleague; Tuesday is supported. Later dialogue cuts inside another answer. Do not use its tail to repair the first answer. |
| PC039 | Limit, 96 | Silver + Friday; expected Maple + Tuesday | F Incorrect; T Unverifiable; task 0; coverage 0; complete YES | Wrong entity/attribute value and unsupported day do not uniquely diagnose a time-selection error. Repeated dialogue ends mid-answer. |
| PC042 | Limit, 96 | Silver + Friday; expected Maple + Tuesday | Same separate labels as PC039 | Later generated answer ends after an unfinished conjunction/quotation. That truncation is in the continuation, not the proposed first sentence. |
| PC044 | Limit, 96 | Maple + Tuesday, supported | F/T Correct; task 1; coverage 1; complete YES | RECENT CONVERSATION replays context and ends at an incomplete later Assistant turn. Decide whether the section heading terminates the attributable first reply. |
| PC054 | Limit, 96 | Nora's June destination Silver; reference Cobalt | F/T Incorrect; task 0; coverage 0; complete YES | Silver corresponds to the earlier route; subsequent context replay does not validate it. Whole-document interpretation remains possible. |
| PC063 | Limit, 96 | Nora's December destination Laurel, supported | F/T Correct; task 1; coverage 1; complete YES | Repeated question/multiple Assistant spans follow; the last cuts off. Preserve all spans but do not score the last one as the first reply. |

The [eight-item review CSV](validation/p1c/calibration_v1/semantic_review_v1/stage_b/ambiguous_boundary_review_UNCONFIRMED_v1.csv) contains the complete raw text, frozen candidate, trace, exact proposed prefix, reference quotations, all seven ratings, confidence, alternatives and blank researcher boundary fields. The [policy](validation/p1c/calibration_v1/semantic_review_v1/stage_b/boundary_sensitivity_policy_v1.json) and [snapshot](validation/p1c/calibration_v1/semantic_review_v1/stage_b/freeze_manifest_v1.json) bind the operation. Recoverability is **proposed 8/8**, not human-validated 8/8.

## Consequences for interpretation

Accepting all eight prefixes would add four proposed correct and four proposed incorrect factual replies. This does not uniformly improve a score. Secondary aggregate suggestions become factual 47 Correct / 24 Incorrect / 1 Unverifiable, temporal 47 / 16 / 9, task success 47 / failure 24 / unknown 1, completeness YES 72. Primary totals are preserved in the [measurement-bias comparison](P1c_measurement_bias_assessment_v1.md).

Both EOS outputs are structurally ambiguous: EOS alone does not certify a usable answer boundary. Conversely, 64 CROSS_TURN spans are proposed semantically complete. Output-limit saturation mainly describes the entire continuation; these logs cannot establish the counterfactual quality under a different output cap or stop policy. Any generation-level boundary intervention remains a new, separately authorized experiment.

## Algorithmic Opportunity Assessment

The reproducible issue is parser coverage for section-heading continuations. Native EOS, official templates, stop sequences and first-span extraction are existing engineering baselines. A boundary detector must also be tested on quoted headers, code blocks and legitimate multi-section replies to measure false splitting. Current recovery examples do not establish a new algorithm; the [bounded validation plan](P1c_algorithmic_opportunity_assessment_v2.md) keeps measurement and generation interventions separate.
