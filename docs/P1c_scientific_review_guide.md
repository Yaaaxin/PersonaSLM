# P1c Scientific Review Guide — v1

Maintainer and final decision authority: Yaxin ZHENG. These are **stimulus reviews**, not model-output ratings. No new human judgment has been supplied. Recommendations are AI-assisted analytical material, not independently authored human annotations.

## Files and workflow

1. [12-case form](validation/p1c/scientific_review_v1/case_review_v1.csv): one row per original case, full trusted ledger, question, both dates, fixed context, answer, source quotes and specific risks.
2. [60-text master](validation/p1c/scientific_review_v1/history_text_review_v1.csv): four active histories and one neutral per case, exact text, factor assignment, source quote, token evidence and scope.
3. [12-neutral subset](validation/p1c/scientific_review_v1/neutral_review_v1.csv): convenience view of the same neutral item_ids. It is not an additional independent sample.

Save separately named completed copies. Preserve case_id/item_id, source text, hashes, question and reference fields exactly. Fill only `researcher_*` fields and the actual `reviewer_id`; no timestamp is required if not known. If a source field is wrong, leave it intact, describe the exact problem, and choose REVISION_REQUIRED rather than editing the master. A substantive correction requires a new stimulus version and dependent token/hash validation.

## Positive criteria

Use PASS / FAIL / UNCERTAIN for each criterion; PASS always means the stated requirement is satisfied. Do not reverse a label to fit an overall decision.

| Field | Positive criterion |
|---|---|
| researcher_evidence_and_answer | Identical trusted evidence uniquely supports every requested answer component at the requested date |
| researcher_topic_definition | Parcel versus music is a defensible auxiliary-topic comparison for this exact question; neither history supplies the answer |
| researcher_time_interpretation | Interval truth, requested-date validity and retrospective archive framing are coherent |
| researcher_narrow_scope | The stated package-level interpretation is scientifically useful despite the explicit limitations |
| researcher_no_answer_leakage | This historical/control text gives no required answer or unintended competing target-property value |
| researcher_topic_and_time | The assigned active R/T meaning is coherent; for neutral, the absence of a personal validity assertion and remaining archive cues are accurately disclosed |
| researcher_speaker_and_coherence | Speaker roles and the two-turn exchange are understandable, with any stylistic/artificiality issue acceptable for the stated role |
| researcher_narrow_comparison | The text supports its limited comparison; no claim of pure mechanism or complete semantic neutrality is being approved |

For `researcher_decision` use ACCEPT_NARROW / REVISION_REQUIRED / REJECT / UNCERTAIN. An acceptance must refer to the stated scope; it does not approve inference. Record evidence quotations and explanation in `researcher_notes` for FAIL, UNCERTAIN or a qualified acceptance. These judgments may acknowledge limitations without pretending they are absent. Conflicting labels/decisions must be reported for clarification, not silently repaired.

Review case definitions first, then the four active texts as a set, then the procedural neutral. Pay particular attention to requested-date versus archive date, cyclic colors, interval/value changes, and whether “parcel” is actually related to desk/service questions. Relevant does not mean answer-supporting; music remains about the same person. A correct ground-truth derivation does not validate semantic orthogonality.

## Later independent outcome review, if execution is authorized

Stage A must hide treatment IDs, factor labels, structural status, stop reasons and AI suggestions. Provide the question, common evidence, requested/evaluation dates, required components, fixed context and frozen first reply. Rate relevance/coherence on the existing 1–5 scales; factual/temporal Correct / Incorrect / Unverifiable / Not Applicable; record delivery, component support and completeness separately. Missing ratings are not N/A. A supported partial answer is not full task success.

Stage B reviews native termination, raw full continuation, extracted/excluded spans and unchanged response_status_v1. Additional turns do not invalidate a correct first reply automatically; no defensible first unit means unknown semantic measurement, not an invented reply. Do not substitute a later answer. Corrections require a new annotation version preserving Stage A.

The existing [independent reviewer plan](P1c_annotation_reliability_plan.md) proposes a prospectively selected 36-output subset. No second reviewer or agreement exists. If such review is unavailable, disclose single-authority/assistance provenance and conduct label/unit sensitivity analyses; do not call that independent agreement. Responses may reveal cues despite masked columns. This stimulus packet itself exposes factor assignments intentionally and must not be described as blinded outcome evaluation.
