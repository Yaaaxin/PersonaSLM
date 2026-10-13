# P1 Wave 1 Evaluation Coverage

Maintainer: Yaxin ZHENG. Protocol v1.1; unchanged `separate_axes_policy_v1`, `p1_endpoint_routing_v1`, `english_residence_claim_audit_v3`, and `response_status_v1`.

## Frozen denominators and actual coverage

Eligibility comes from the pre-generation case matrix, never from observed output quality. All structural categories remain in the denominator. Fidelity has no supplied ground truth and stays separate/inapplicable. No overall reliability score is constructed.

| Dimension | Eligible / received | Automatic attempts | Conclusive automatic labels | Unverifiable labels | Minimum unresolved human judgments | Conclusive automatic coverage |
|---|---:|---:|---:|---:|---:|---:|
| Relevance | 96/96 | 0 | 0 | 0; 96 PENDING | 96 | 0% |
| Factual consistency | 72/72 | 48 | 15 | 57 | 57 | 20.83% |
| Temporal consistency | 48/48 | 0 | 0 | 48 human-pending placeholders | 48 | 0% |
| Conversational coherence | 96/96 | 0 | 0 | 0; 96 PENDING | 96 | 0% |

Human-scored coverage is zero for every dimension. The packet requests independent verification of **all** eligible outputs, including the 15 automatically labelled Correct, not only the minimum unresolved set. There are zero missing records and zero empty first spans. Seventeen first spans are boundary-censored, all in family C; they affect relevance/coherence, not factual/temporal eligibility. Semantic incompleteness remains unreviewed for all 96; budget censoring is not automatically semantic failure.

The 48 residence questions were actually passed to the limited city checker: 15 Correct and 33 Unverifiable. The 24 membership questions were deliberately not passed to that checker and received pending-human Unverifiable placeholders. Thus it is inaccurate to say the same evaluator attempted and failed on all 57. Temporal placeholders likewise are not detected temporal errors.

## Why the 57 factual labels are unresolved

The [96-row audit](validation/p1/measurement_audit_v1.json) binds the full first-span sentence to a source fact, speaker and validity interval where its deliberately narrow grammar permits. This is post-output surface-form diagnosis, not a new accuracy result. Every original score and applicability label is preserved.

| Candidate explanation | Observed evidence among the 57 | Limit |
|---|---|---|
| Unsupported answer syntax | 33 date-bearing current-city sentences | Overlaps the date row; do not sum as 66 |
| Date-bearing answer | 33 whole sentences match the source city and exact validity-start suffix | Original evaluator grammar does not recognize the suffix; not proof of human-confirmed correctness |
| Other unsupported task type | 24 membership answers: 23 direct, 1 attributed to the verified record | City-only evaluation intentionally not used; human review required |
| Missing answer | No empty first span; all 57 have one recognized whole-sentence fact form | Does not independently establish semantic completeness |
| Contradictory answers | No contradiction identified within these 57 recognized first-span forms | Does not certify absence of contradictions in later generated turns or a general contradiction detector |
| Multiple answer candidates | No multiple candidates in the complete recognized first-span forms | Additional generated turns remain available, excluded from the frozen unit |
| Incomplete first replies | Zero budget-censored first spans among these 57; all end before a role transition | Human completeness remains unknown |
| Speaker attribution ambiguity | Whole-span subject binds to the case speaker in all 57 | Identity/reference validity still available for human verification |

The comparison is not a city-name substring match. Independent negative tests reject negated claims, wrong subjects, extra conflicting answers, quotations, incompatible dates and unfinished sentences. Those tests validate the diagnostic boundary, not a universal semantic evaluator. The 24 nonfactual outputs are not made factually eligible merely because some mention a city or club. Such unwanted content belongs in relevance/coherence and notes under the existing applicability matrix.

## Per-condition denominators and paired observations

Each condition contains 12 outputs: 9 factual-eligible, 6 temporal-eligible, and 12 relevance/coherence-eligible. There are 3 factual Not Applicable responses per condition. No condition has a human rating yet.

| Condition | Correct | Incorrect | Unverifiable | Conclusive factual coverage |
|---|---:|---:|---:|---:|
| C0 | 0 | 0 | 9 | 0/9 |
| C1 | 1 | 0 | 8 | 1/9 |
| C2 | 0 | 0 | 9 | 0/9 |
| C3 | 2 | 0 | 7 | 2/9 |
| C4 | 1 | 0 | 8 | 1/9 |
| C5 | 3 | 0 | 6 | 3/9 |
| C6 | 4 | 0 | 5 | 4/9 |
| C7 | 4 | 0 | 5 | 4/9 |

C1−C0 has one Unverifiable→Correct label transition (`p1_speaker_01_A`); C3−C0 has two such transitions (see the complete paired inventory in the audit). There are zero paired cases with conclusive factual labels in both the C0 and corresponding treatment cell, because all C0 factual labels are Unverifiable. A difference in recognition coverage is not a factual-accuracy effect. The 9 eligible case pairs remain the denominator; none is silently dropped. Semantic main effects/interactions, temporal effects, and relevance/coherence effects are presently unscorable. Unknown values are not replaced by zeros or treated as Incorrect.

## Human measurement package

The [English CSV](validation/p1/output_human_review_v1.csv) has 96 anonymous response IDs, 12 anonymous case IDs and 41 columns. It includes the question, identical trusted evidence and fixed context, evaluation date, source fact validity ledger, exact first reply, full raw continuation, excluded tail, structural status, hashes and frozen applicability. All 14 human fields are blank. [Instructions](P1_wave1_human_annotation_guide.md) define unit confirmation and separate dimensions; the [schema](validation/p1/output_human_review_schema_v1.json) binds the master hash.

Treatment labels, factor bits, original request/persona IDs and automatic factual labels are absent from the reviewer-facing view. A separate ignored curator mapping links the randomized IDs to original records. The full historical reference ledger is identical across conditions of a case; it does not reveal which history was actually provided to a particular generation. Reviewers must be given only this packet and guide. Names in the synthetic question remain necessary for attribution, and outputs, visible structural categories or prior access may reveal condition clues. This is preparation for condition-masked scoring, not a claim of successful blinding. No reviewer identity, time, agreement or adjudication is fabricated.

The importer rejects missing/invalid judgments, changed material/version/applicability, duplicated/unknown IDs and missing reviewer/masking provenance. It preserves submitted CSV bytes in a new registration directory. Blank input was tested and rejected; unavailable reviewer timestamps may remain blank. Import validation establishes a complete submitted schema, not independent judgment quality or scientific truth. No review has been imported in this audit.
