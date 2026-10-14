# P1c final annotation verification and construct discrimination v1

Maintainer: Yaxin ZHENG. AI-assisted verification; human annotation adoption remains pending. No new inference or official semantic effects.

## Exact pending snapshot

The existing [confirmation packet](P1c_final_annotation_confirmation_packet_v1.md) is unchanged. SHA-256: `4989e36d8d862c5995221b470adb8c9620ba7023ffc8ebf9d492cda18f6fc817`, exactly matching the researcher's supplied fingerprint. This supplement does not replace that packet, revise scores or create another approval gate.

| Object | Exact repository path | SHA-256 |
| --- | --- | --- |
| 72 reviewed primary rows | docs/validation/p1c/calibration_v1/semantic_integrity_v1/reviewed_primary_proposals_UNCONFIRMED_v1.csv | 276a67c7a47994f6149834261b488a93399b100ac8fc1e2253f764f1d90d9285 |
| Canonical primary JSON | docs/validation/p1c/calibration_v1/semantic_integrity_v1/reviewed_primary_proposals_UNCONFIRMED_v1.json | 144a63679d2267b725dacb90294d7b72cbfbb9a5c724f4ed1312e099c78f5068 |
| Eight boundary assessments | docs/validation/p1c/calibration_v1/semantic_integrity_v1/boundary_sensitivity_table_v1.csv | d1d4318acfa298a45591c6b186ea17e3ede8f7c631f2a858538ef4613e219f4c |
| Canonical all-72 sensitivity view | docs/validation/p1c/calibration_v1/semantic_integrity_v1/reviewed_boundary_sensitivity_UNCONFIRMED_v2.json | 790e9f6210f3e0b465703911988343f89680a0650c83d51009c23be442f62a77 |

The updated check verifies all original proposal fields, first-reply hashes, the eight literal prefixes, previous artifact seals and approved source pins. The separate execution reconstruction checks all 72 original HTTP outputs, token arrays, model/backend identity and 5,798 historical artifacts. Source files and the old approval packet have not been rewritten. The newly supplied targeted AI audit is preserved and treated as analytical advice, not human confirmation or a second independent reviewer.

## Exact six-field revision audit

The [item-level audit](validation/p1c/calibration_v1/annotation_gate_v1/six_field_revision_audit_v1.csv) contains original explanations, exact reply/question/context/evidence quotations, revised interpretation, rubric reference/hash, alternatives and blank researcher decisions.

| ID | Endpoint | Original → proposed | Rubric-specific reason |
| --- | --- | --- | --- |
| PC004 | Coherence | 4 → 5 | The named collection assignment continues the fixed schedule dialogue; desk/room alias uncertainty belongs to the claim/attribute reading. |
| PC006 | Relevance | 4 → 5 | Both requested desk and service-day fields are directly attempted; calendar ambiguity does not make the reply off-topic. |
| PC006 | Coherence | 4 → 5 | The complete assignment sentence integrates with the generic schedule context despite an unresolved calendar assertion. |
| PC011 | Coherence | 4 → 5 | An incorrect Laurel assignment still follows the requested assignment conversation. |
| PC027 | Coherence | 4 → 5 | Wrong entity/attribute content does not establish a missing reference or discourse discontinuity. |
| PC030 | Coherence | 4 → 5 | The concise wrong assignment is conversationally integrated; falsity remains separately scored. |

These are consistent applications of the existing rubric, not automatic correctness guarantees. PC023 has two **secondary-only** 4-to-5 ordinal revisions for the same relevance/coherence separation; its primary scores remain unresolved. No additional rating revision was made.

## Three different meanings of independence

**Conceptual separation:** truth, task completion, component support, relevance, coherence and semantic completeness ask different questions. **Implementation independence:** original group defaults jointly assigned factual/task and ordinal scores; separate column names and subsequent explanations do not establish independent scoring passes. Reinspection is still the same AI analytical process. **Empirical discrimination:** the current proposals distinguish some constructs but leave others numerically redundant.

The new item table and full pairwise joint distributions record all 72 rows without pooling missingness into failure. Factual C/I/U maps pointwise to task 1/0/unknown in 72/72 rows, including 63 decided and nine unresolved pairs. This is compatible with this sample's simple complete assignment answers, but original shared coding remains a limitation. All 20 factual Incorrect primary replies are semantically complete. PC006 has component coverage 1 under the service-attribute reading but unresolved task success. Secondary PC033 has component coverage 0.5 and task failure. No correct-but-incomplete primary reply was found; none was invented.

Revised relevance and coherence agree in 60/64 jointly scorable rows; PC004/011/027/030 differ. Eight additional pairs are jointly null. Coherence has only score 5 on 64 scorable primary replies. Semantic completeness has only YES on those same replies; UNCERTAIN on the other eight represents unavailable boundaries, not a second observed completeness level. Neither known coherence nor known completeness can discriminate conditions in this sample. Their eligible denominators and registered endpoints remain intact. Relevance has only two adjacent categories and limited resolution.

Historical P1b data were checked separately: 137 factual Correct, 110 FULL_ANSWER and 27 factual Correct/PARTIAL_ANSWER. That calibration did discriminate factual support from delivery; it does not supply missing P1c discrimination, independent raters or a causal between-wave comparison. No historical rows or labels were changed or pooled.

## Temporal and entity interpretation

The [eight-item interpretation table](validation/p1c/calibration_v1/annotation_gate_v1/temporal_entity_interpretations_v1.csv) records the complete ledger, query date, exact reply and competing readings.

- PC004: route 53 supports destination room Cobalt. Calling it a collection desk is accepted only as a loose destination alias; a strict attribute reading remains disputed. Existing Correct recommendations are preserved.
- PC006: the literal phrase `on Thursday, 2042-12-15` permits a calendar assertion. Python's proleptic Gregorian calculation gives **Monday** for 2042-12-15. The ledger separately assigns recurring service day **Thursday** during that interval. Calendar falsity is not ignored, but external calendar knowledge is not silently inserted into the trusted answer reference. Primary F/T remain Unverifiable and task unknown pending adoption/adjudication.
- PC023: `on a Thursday` more naturally permits a recurring service-day reading, under which its alternative prefix remains proposed Correct. A literal query-date weekday reading would be false. Its primary boundary remains unresolved; the eight-prefix view is sensitivity only. The wording uncertainty previously present in prose is now also explicit in derived metadata.
- PC011/027/030/035/040: the response gives Laurel for Idris when route 52 requires Silver. Laurel is the colleague's desk **in the same requested interval**. Wrong target/attribute is demonstrable, but a wrong-interval mechanism is not. Existing factual Incorrect/temporal Unverifiable proposals are preserved. A broader false-date-bound-claim temporal interpretation remains disputed; it must not be selected based on condition effects.

No additional primary label was silently changed. Interpretive alternatives are disclosed for researcher adjudication, not promoted into a new endpoint or automatically executed policy sensitivity.

## Derived uncertainty metadata

[Measurement-state v2](validation/p1c/calibration_v1/annotation_gate_v1/derived_measurement_state_v2.json) retains the original metadata alongside a descriptive alias `INTERPRETATION_UNCERTAIN` for `ANNOTATION_UNCERTAIN`. It explicitly flags PC023 secondary wording, correcting a metadata omission without altering a score. BOUNDARY_UNRESOLVED, STRUCTURALLY_UNSCORABLE, EVIDENCE_UNVERIFIABLE, MISSING and NOT_APPLICABLE remain different and may overlap at different levels. Primary factual U remains eight unresolved units plus PC006; official human confirmation remains missing on all 72, while the AI proposals themselves are present.

## One researcher decision, then automatic analysis

Recommended: adopt the specified reviewed 72 primary rows and eight alternative prefixes strictly as sensitivity, with the six primary and two PC023 secondary ordinal revisions and all disclosed interpretation limitations. Alternatively provide explicit per-view/ID/metric corrections or retain the original ordinal proposals. The existing importer supports those decisions and refuses blank confirmation. The current instruction is not approval.

After actual confirmation, freeze a new annotation snapshot and automatically run the exact approved 16 contrasts, with twelve paired cases, six speaker clusters, signed unknown bounds, whole-speaker bootstrap and leave-one-speaker-out diagnostics. No fresh inference or ordinary analysis approval is needed. Package-level interpretation, DIAGNOSTIC_ONLY procedural controls and the shorter no-history prompt remain mandatory. Six purposive clusters do not justify population significance or guaranteed bootstrap coverage.

## Algorithmic Opportunity Assessment

The real boundary problem justifies an offline baseline investigation, not a claimed original parser. The companion baseline report will distinguish candidate-span recovery from independent boundary accuracy. Current annotation agreement cannot serve as independent ground truth for a method developed from the same outputs. Independent measurement validation and empirical replication remain separate requirements for a defensible PLOS ONE study.
