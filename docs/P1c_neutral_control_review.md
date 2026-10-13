# P1c Neutral-Control Review — Proposed v1

Maintainer: Yaxin ZHENG. **All new semantic approvals are OPEN.** Earlier P0 approvals and the unreviewed P1 controls do not transfer to this bank. No control-adjusted P1c outcome exists.

## Roles and candidate bounds

The bank contains no history, four R/T histories and one procedural neutral-history family for each of 12 cases. The finite construction rule was saved before native tokenization: 16 active realizations per R/T cell, 32 neutral realizations and one empty history. A common active variant and common Archivist-question variant are required within a case. Choose the first exact match in declared order, never based on answer generation. Tolerance is zero. Failures and closest differences must remain recorded; no padding or candidate expansion is authorized by a failure.

The native-tokenizer report and full prompt records in [the proposal directory](validation/p1c/proposed_v1/) are engineering evidence only. The standalone pinned GGUF tokenizer is checked against saved P1b native input IDs before new counts are accepted. No completion endpoint or new generation is used. The no-history prompt is intentionally shorter. Evidence is before history, so its absolute prefix position stays fixed; the recent conversation and question follow the history slot.

## Human-review materials and rules

[Stimulus review](validation/p1c/proposed_v1/stimulus_review_v1.csv) provides all 12 cases, evidence, references, dates and context with blank researcher fields. The selected-history review, when matching succeeds, includes every matched active/neutral text, its exact full-prompt count and prompt hash. Do not enter automated judgments into reviewer fields. Save a separately named completed copy and record its source hash. The original master is immutable by workflow and exclusive creation; filesystem ownership does not authenticate a reviewer.

Use PASS / FAIL / UNCERTAIN for each positive criterion, with a quotation and explanation for FAIL or UNCERTAIN:

1. Evidence is sufficient and the required answer is correct at the requested date.
2. Topic relation is appropriately classified as ancillary, not direct answer disclosure.
3. The selected historical statement is true in its stated interval; T correctly records validity at the requested date.
4. The text introduces no requested answer, implication that determines it, or unintended contradiction.
5. The target speaker, archive narrator and present interlocutor are distinguishable.
6. Two turns form a natural, interpretable exchange without unintended style instructions.
7. For neutral text, procedural content does not supply personal facts or imply answers; remaining pragmatic effects are acknowledged.
8. The proposed narrow comparison is scientifically interpretable despite residual content differences.

Use ACCEPT_NARROW / REVISION_REQUIRED / REJECT / UNCERTAIN for the final decision; approval must name the allowed contrast. State reviewer identity only when supplied by the actual reviewer. Record a review time only if known. Initial analytical assistance and subsequent researcher corrections must be preserved separately. No independent blind study, second reviewer or agreement is implied.

## Known confounders requiring explicit acceptance

The active histories contain personal auxiliary facts and interval dates. The neutral archive exchange contains procedural statements and an archive timestamp, but no embedded validity interval. It differs in topic, temporal proposition content and speech act. Both can elicit record-reading behavior. Exact length and format do not make them semantically neutral or equivalent to an empty context.

The selected colors and topic words may carry associations. R is a topical manipulation, not a calibrated measure of psychological relevance. T changes interval/value selection; it does not manipulate truth. The neutral condition cannot isolate temporal conflict alone. The researcher may accept the narrow replacement interpretation, request a versioned correction or reject it. None is presumed here.

## Gate

Generation remains NO-GO until the operational scientific target, cases and selected controls are explicitly approved, all intended exact matches pass, and an execution manifest is frozen. An approval of case ground truth does not approve control semantics. If neutral validity fails, do not silently run a reduced experiment or omit that arm; obtain approval for a narrower revised scope. Review completion and control validity are separate statuses.


## Executed offline preparation and bounded revision

The original finite v1 bank produced 12/12 failed neutral matches. Four active R/T cells matched each other; the nearest permitted neutral differed by one token. All 1,164 candidate prompt measurements and the original bank are retained in [v1 validation](validation/p1c/proposed_v1/tokenizer_validation_v1.json). No tolerance was relaxed.

A separate [v2 revision plan](validation/p1c/proposed_v2/revision_plan_v2.json) was saved before testing its new text. It changes only `its two parts` to `its two distinct parts` in one existing neutral reply, tries the four existing question variants, and permits no further expansion. Evidence, answers and active histories remain byte-identical. The revised neutral passage still requires semantic review: the extra modifier is not automatically harmless.

[Native v2 validation](validation/p1c/proposed_v2/tokenizer_validation_v2.json) reports **12/12 exact matched sets**. Each set has four active histories and one neutral; the no-history cell is intentionally shorter. There are 72 reconstructed proposed prompts. Matched full prompts range from 766 to 938 tokens; all prompts range from 701 to 938, leaving at least 3062 tokens after the 96-token output budget. Evidence-prefix positions and matched fixed-context/question suffix positions are independently checked using native token IDs.

The [60-item history review](validation/p1c/proposed_v2/history_semantic_review_v2.csv) contains four active and one neutral text per case, full evidence/questions/references, exact counts and blank judgments. The [selected proposal configuration](validation/p1c/proposed_v2/configuration_proposal_v2.json) pins these prompt bytes while retaining the original proposed request order. It is not an execution authorization.

Three saved P1b prompts from distinct task families reproduced their original backend token-ID lists exactly through the pinned standalone tokenizer. The model and server hashes match their pins. Native stderr includes `n_ctx_seq (512) > n_ctx_train (0)` warnings during vocabulary tokenization; these are preserved, not interpreted as an observed inference-context overflow. No response was generated. The pinned tokenizer source webpage could not be retrieved; binary identity and empirical token-ID agreement were checked instead.

The complete non-generation suite reported **751 passed**, 0 failed, no warnings in pytest output, exit 0; final pytest output 751 passed in 29.95s, capture wall time 30.443 seconds. The [final integrity record](validation/p1c/proposed_v2/final_integrity_v1.json) separately checks historical hashes, two independent rechecks of P1b case contrasts, JSON/CSV validity and new prompt reconstruction. These results do not approve semantic controls.
