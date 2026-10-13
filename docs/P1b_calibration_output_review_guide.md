# P1b Calibration Outcome Review Guide — v1

Maintainer: Yaxin ZHENG. Formal Protocol v1.1; development calibration only. Stimulus approval is separate from outcome annotation. No output judgments, reviewer identities, review dates or agreement statistics are supplied by this packet.

## Materials and masking

Use [the outcome form](validation/p1b/calibration_v1/analysis_v1/output_human_review_v1.csv) after execution and integrity auditing. It contains 192 response records in a separately shuffled order, anonymous response and case identifiers, original first-reply text, complete continuation, excluded continuation, hashes, evidence, question, fixed context, reference date, expected components and frozen applicability. The 41 original Wave 1 field names are retained, with two new reference-guidance columns; this is a distinct P1b review version, not a Wave 1 annotation import.

Condition assignments, S/F/H flags, execution order, full treatment prompts and original request identifiers are withheld from the scoring CSV. The mapping is retained separately under `results/p1b_execution/v1/protected/review_mapping_v1.json`; its hash is recorded in the execution inventory. This is local separation, not an encrypted access-control system. Avoid opening it or treatment-specific analyses before scoring if condition masking is desired. The mapping order was generated with seed 714002 before observing responses and never changes experimental order seed 714001.

The same case-level historical source is displayed for every condition. Its presence in this form does not mean the model saw it. Generated text may reveal cues, and previous researcher knowledge cannot be erased. Record actual assistance and prior access; do not call the review fully independent or blind without evidence. Expected answers are evidence-derived references, not supplied judgments about model responses.

## Unit and completeness

Inspect the full raw continuation before deciding whether the frozen first-reply span captures the intended response. Record `human_reply_unit_confirmed` as `PASS`, `FAIL` or `UNCERTAIN`; quote any boundary disagreement in `human_continuation_notes`. Do not edit raw text, offsets, hashes or the frozen structural label. A disputed extraction remains retained and its semantic applicability must be documented; do not silently substitute a later generated speaker's answer.

Record `human_semantic_completeness` as `COMPLETE`, `INCOMPLETE` or `UNCERTAIN`. It describes delivery of the requested reply, separately from correctness of assertions. A correct partial clause may omit requested components. A CROSS_TURN continuation may start with a complete answer. TRUNCATED indicates budget censorship under the structural policy, not necessarily semantic incompleteness. Missing EOS alone is not a semantic judgment. Do not score generated later user/assistant turns as the first reply's assertions.

## Four separate outcomes

The [frozen routing](validation/p1b/final_v1/evaluation_routing_v1.json) remains authoritative; its historical pending flag is superseded only by the separate researcher approval registration, not rewritten. Every record retains the pre-generation applicability flags.

| Field | Allowed judgments and interpretation |
|---|---|
| `human_factual_consistency` | `Correct`, `Incorrect`, `Unverifiable`, `Not Applicable`. Assess delivered factual propositions against sufficient common evidence. A verified contradictory assertion supports Incorrect; an unsupported claim or unresolved attribution requires Unverifiable with a reason. A supported partial answer can be Correct while incomplete or irrelevant. Missing an answer is not automatically Incorrect. Use Not Applicable only where predeclared. |
| `human_temporal_consistency` | The same four categories. Use the date of the question/proposition and inclusive intervals, not automatically the global reference date. A true past statement is not a current factual contradiction merely because it is old. Explain mixed or unresolved temporal attribution. |
| `human_response_relevance_1_to_5` | Integer 1–5 under the existing annotation guidelines: relevance to the actual question, requested components and constraints. Empty or unfinished reasoning must remain represented rather than discarded. |
| `human_conversational_coherence_1_to_5` | Integer 1–5 under the existing annotation guidelines: coherence with the fixed preceding context and within the first reply. Do not reward an internally fluent but unrelated continuation automatically. |

Retain the existing [annotation guidelines](annotation_guidelines.md), [separate-axis policy](P0_policy_acceptance_report.md) and [frozen P1b routing explanations](P1b_inference_readiness_report.md). Do not combine outcomes into one score or invent Persona Fidelity ground truth. An unavailable assessment may remain blank with an explicit measurement/attribution reason; a blank is missing, not zero or automatically Unverifiable. When a reply can be assessed but its factual/temporal claim cannot be verified, use Unverifiable with its reason. Never convert an eligible missing/unscorable item to retrospective N/A. If frozen eligibility itself is disputed, flag the issue without changing it.

## Evidence and provenance

Use `human_evidence_quotations` for verbatim model/source passages and explain date/entity/component associations. Use `human_unverifiable_reason` for missing answer, unsupported proposition, boundary ambiguity, speaker attribution or other specific limitation. Notes should distinguish instruction violations from false assertions. Multiple supported/contradictory claims must be considered together; substring occurrence is insufficient.

Save a completed copy under a new filename. Keep the original blank master intact. Fill your actual `reviewer_id`, `review_assistance` and `prior_access_to_treatments_or_scores`; enter `reviewed_utc` only if actually recorded. No second reviewer or inter-annotator agreement is presumed. Registration must compare all immutable fields, unique IDs, hashes, labels, applicability and mapping before unblinding a new analysis version. The Wave 1 importer must not be applied blindly to this new packet.

## Denominators and next decision

All 192 requests remain in the structural denominator; all 192 are factual, relevance and coherence eligible. Temporal eligibility is 88, with 104 predeclared N/A. Pending workflow labels are neither correct nor incorrect and are not a fifth factual category. Report scored coverage and missingness explicitly; never filter on C0 correctness. Pair conditions within 24 cases and retain 12 speaker clusters. Semantic factorial estimates must await valid outcome review. No additional inference or neutral-control use follows automatically from annotation.

## Algorithmic Opportunity Assessment

First establish boundary agreement and semantic coverage. Persistent continuation may justify a separately authorized response-boundary diagnostic; it does not by itself justify a new algorithm. Existing role extraction and task-specific evidence review are measurement tools. Any learned verifier or corrective generation method would need independent validation and appropriate existing baselines. No such method is implemented by this review packet.
