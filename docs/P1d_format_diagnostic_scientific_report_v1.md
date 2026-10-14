# P1d format diagnostic — scientific v1

Maintainer: Yaxin ZHENG. First submission target: PLOS ONE. **No configuration qualified for main validation.** This is an eight-case development diagnostic, not independent replication or an E/V effect study. All sixteen semantic assessments below are AI proposals, unconfirmed. The previous 144 proposals also remain unconfirmed.

## Question and identified intervention

The failed 96/192/256-token sweep motivated a predeclared test of current-question role framing and conventional stops. Both new arms add `User:` immediately before the current question and preserve the terminal `Assistant:` prefix. Between the two new arms only the four frozen newline User/Assistant stop strings change. Compared with the historical original H_none/96 outputs, role markers, length/salience and optionally stops change, in a different run. The reference is preserved rather than regenerated. No pure cognitive framing mechanism is identified.

## Observations

| Arm | Requests | Native termination | Frozen structure | Recoverable first span | Complete task answers, AI | Mean wall s |
| --- | --- | --- | --- | --- | --- | --- |
| F_user_marker | 8 | {'length': 8} | {'CROSS_TURN': 8} | 8/8 | 0/8 | 28.336 |
| F_user_marker_stops | 8 | {'stop_sequence': 8} | {'AMBIGUOUS': 8} | 8/8 | 0/8 | 21.819 |

All sixteen raw outputs and evidence were read item by item. Every first response promises ledger use and ends with USER RESPONSE or CURRENT QUESTION. Neither arm delivers any of its **14 required components**. Full continuations repeat promises or simulated user questions; they do not deliver hidden final answers. Arlo's no-stop continuation changes the simulated question to Arwen: this is outside the primary answer span and is not automatically an assistant factual assertion.

The stop arm produces 154 tokens versus 768 without stops. Its first-span content equals the no-stop first span after whitespace normalization in 8/8 pairs; exact text equality is 0/8 because the delimiter newline is removed. Conventional offline stop shadows reproduce the eight actual stop outputs exactly. This is implementation agreement, **not independent boundary accuracy**. First-span recoverability stays 8/8 in both arms. Visible cross-turn continuation is suppressed; actual native EOG remains 0/16.

Frozen AMBIGUOUS in the stop arm means `bounded_reply_semantics_not_certified`, with identifiable=true. It must not be confused with an unresolved first-span boundary or counted as a factual error. The retained section headings still pose discourse-scope uncertainty. A separately recorded heading-excluded prefix is also only a promise and does not rescue delivery; it does not replace primary text.

## Separate semantic endpoints and measurement limits

Per arm: factual Correct4/Unverifiable4/Incorrect0; temporal Unverifiable8; task Failure8; semantic completeness NO8; relevance3×8; coherence3×8; narrow persona-style fidelity4×8. Correct here refers only to four generic policy echoes about historical intervals, not correct requested answers. If these echoes are excluded from material factual claims, factual Unverifiable becomes8/8. Both interpretations leave delivery at0/8. There is no unsupported inference of temporal correctness from the generic rule.

Thus eight responses can be factual Correct while task Failure; the constructs are not copied. Relevance, coherence and fidelity have separate evidence, but each has zero observed variance. They cannot discriminate the two configurations in this sample. They are retained without altering scores to force variation. Generic-policy scope, ordinal anchors and section-heading ownership remain explicit adjudication issues.

The [16-item proposals](validation/p1d/format_calibration_v1/analysis_v1/primary_AI_proposals_UNCONFIRMED_v1.csv) contain evidence, alternatives, applicability and blank human fields. Initial AI review had configuration visibility; it is not claimed as blinded. The [independent-review form](validation/p1d/format_calibration_v1/analysis_v1/independent_review_without_AI_scores_v1.csv) hides assignments and AI scores for a future reviewer; linguistic/whitespace cues remain. No second human or agreement score exists.

## Paired uncertainty and historical comparison

Eight paired cases equal eight purposively chosen speaker clusters. Whole-speaker bootstrap sensitivity uses10000 draws, seed716710; leave-one-speaker-out values and all case contributions are retained. Stop-minus-no-stop mean latency is -6.517s, percentile interval [-7.297, -5.683]s. Concurrent non-generation preparation and system load limit timing generalization. These intervals do not guarantee population coverage.

All paired proposed task differences and their leave-one-out values are zero. Degenerate bootstrap intervals do not prove equivalence or absence of a population effect. Full-eight-case unknown-correctness difference bounds are [-.5,.5] factual and [-1,1] temporal under unrestricted unresolved labels, conditional on the generic-policy primary convention. Categorical incidence and assessable-case accuracy are different; there are no temporally assessable answers. Missing annotations0, but factual/temporal Unverifiable remain separate. There is no available-cell renormalization or confirmatory significance testing.

Exact historical request IDs/hashes are joined in [historical comparison](validation/p1d/format_calibration_v1/analysis_v1/historical_exact_id_comparison_v1.csv). Historical task completion was also0/8. New role labels move simulated user content outside the first span, while three additional cases now echo a supported generic policy. A rise in factual Correct-label incidence from1/8 to4/8 is therefore **not demonstrated requested-answer improvement**. Neither this comparison nor the eight paired stops is independent replication. Each of four task families has only two cases; all have zero proposed complete answers.

## Decision and Algorithmic Opportunity Assessment

This is closest to **Case B**, specifically continuation/measurement control without improved answer delivery; it also triggers the Case C operational constraint against expanding an unsuitable Base configuration. No arm meets the frozen8/8 complete-identifiable-answer qualification. Adding a User marker is insufficient here; larger budgets already failed to change the earlier first replies. Neither finding proves all Base prompts or models are incapable.

1. **Observed Failure Modes:** promise repetition, empty answer content and policy echoes surviving cleaner stopping.
2. **Existing Methods and Published Prior Art:** native EOG, standard stops, deterministic role extraction, official templates, structured checking and generation-time verification are established methods; see [algorithm update](P1d_algorithmic_development_update_v3.md).
3. **Potential Algorithmic Improvements:** no evidence justifies a novel boundary algorithm when conventional stops reproduce these cuts. Study model/template adequacy before inventing a repair method.
4. **Validation Feasibility:** an exact eight-request Instruct feasibility proposal is prepared separately, with no automatic main-policy change. Independent boundary annotation and all-condition coverage remain necessary.
5. **Publication Value:** the defensible development contribution is a separation of termination, recoverability, claim support and actual task delivery. It is not a new mechanism or publication-ready finding.

The empirical S/F/H programme remains intact. P1d history packages refine its history branch; P3 configuration sensitivity and P5 localization support rather than replace that question. No P4 real-person data or P6 generation/training was started.
