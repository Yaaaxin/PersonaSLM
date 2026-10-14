# P1c measurement-bias assessment v1

Maintainer: Yaxin ZHENG. All semantic values below are unconfirmed AI proposals. There are no official semantic treatment effects.

## Primary versus boundary sensitivity

Both views retain all 72 eligible records. The secondary view changes only eight explicitly recorded spans and requires researcher adoption as a sensitivity analysis; it never replaces the primary extraction policy.

| Outcome | Frozen primary spans | Proposed prefix sensitivity |
|---|---|---|
| Identifiable/evaluable text units | 64; 8 unresolved | 72 proposed; 0 independently validated new recoveries |
| Factual Correct / Incorrect / Unverifiable | 43 / 20 / 9 | 47 / 24 / 1 |
| Temporal Correct / Incorrect / Unverifiable | 43 / 15 / 14 | 47 / 16 / 9 |
| Task success / failure / unknown | 43 / 20 / 9 | 47 / 24 / 1 |
| Component coverage full / half / zero / unknown | 44 / 0 / 20 / 8 | 48 / 1 / 23 / 0 |
| Semantically complete YES / UNCERTAIN | 64 / 8 | 72 / 0 |
| Relevance or coherence: 5 / 4 / null | 59 / 5 / 8 | 66 / 6 / 0 |
| Frozen structural COMPLETE / TRUNCATED / CROSS_TURN / AMBIGUOUS | 0 / 0 / 64 / 8 | 0 / 0 / 64 / 8, unchanged |

Primary factual Correct-label incidence is 43/72 (59.72%); assessed-only C/(C+I) is 43/63 (68.25%). These are different quantities. Treating all nine Unverifiable items as unknown binary outcomes yields all-eligible bounds [43/72, 52/72], **not** a confidence interval and not an instruction to label them Incorrect. Temporal equivalents are 43/72, assessed-only 43/58 (74.14%), and bounds [43/72, 57/72]. These are annotation-conditional descriptive sensitivity quantities only.

Secondary factual bounds are [47/72, 48/72], and temporal bounds [47/72, 56/72]. Their narrower unknown range does not prove that the alternative boundary policy is correct. Neither view has received independent human validity assessment.

## Structural, stopping and semantic cross-tabulation

| Frozen structure | N | Primary completeness | Primary factual C/I/U | Primary task success/failure/unknown |
|---|---:|---|---|---|
| CROSS_TURN | 64 | YES 64 | 43/20/1 | 43/20/1 |
| AMBIGUOUS | 8 | UNCERTAIN 8 | 0/0/8 | 0/0/8 |

All 64 CROSS_TURN responses reached the output budget. Of the eight AMBIGUOUS responses, six reached the budget and two ended at EOS. Under the proposed sensitivity the six budget-ended ambiguous records contain two correct and four incorrect first prefixes; both EOS prefixes are proposed correct. The resulting secondary task delivery counts are 45 success / 24 failure / 1 unknown among 70 limit stops, and 2 success among 2 EOS stops. These small, selected cells do not identify effects of termination policy.

Using structural COMPLETE as successful-answer count would produce zero, erasing 43 proposed successful primary replies. Counting CROSS_TURN or AMBIGUOUS as factual Incorrect would likewise conflate format, extraction and correctness. Conversely, calling every recoverable prefix a successful answer would conceal four proposed false answers. The full continuation remains available for auditing model behavior beyond the scored reply.

## Missingness and sources of bias

There are three distinct uncertainty sources: eight unidentifiable primary evaluation units; five identifiable wrong-entity/attribute replies whose temporal interpretation is uncertain; one service-day/calendar wording ambiguity. Missing human confirmation applies to all 72 records, separately from these semantic causes. Original applicability is 72 on each semantic axis, N/A 72 for Persona Fidelity.

Previous structural analysis found ambiguity concentrated in two speakers and in multi-component/route families. Therefore complete-case semantic comparisons may be selected by task and condition. No condition-specific semantic estimates were computed here. The prepared analysis retains original signed weights, separate label incidences, unknown-outcome bounds and complete-case sensitivities; it never drops a cell and renormalizes its contrast.

Relevance and coherence show identical proposed ordinal distributions and high ceiling frequency, but were assessed separately. The factual label is not inserted into their scoring rules. The current narrow factual requests may not discriminate those discourse outcomes well. This is a measurement limitation, not proof of identical latent constructs.

## Algorithmic Opportunity Assessment

The candidate empirical contribution is showing whether valid boundary definitions materially alter interpretation of package contrasts. That requires confirmed primary/sensitivity annotations and independent boundary cases; current aggregate differences alone do not establish mechanism or novelty. Existing extraction, verification and structured-reading methods are mandatory comparators, as detailed in the [opportunity report](P1c_algorithmic_opportunity_assessment_v2.md).
