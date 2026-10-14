# P1c researcher-confirmed exploratory analysis v1

Maintainer: Yaxin ZHENG. Official working title: Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models. First submission target: PLOS ONE. This is development evidence, not independent confirmatory research.

## Registration and scope

Yaxin ZHENG explicitly adopted Option 1 for packet SHA-256 `4989e36d8d862c5995221b470adb8c9620ba7023ffc8ebf9d492cda18f6fc817`. The [actual source statement](validation/p1c/confirmed_semantic_v1/approval/researcher_confirmation_source_v1.txt), [decision](validation/p1c/confirmed_semantic_v1/approval/actual_researcher_decision_v1.json) and [immutable registration](validation/p1c/confirmed_semantic_v1/registration/registration_manifest_v1.json) preserve the approval. No human review timestamp, second reviewer or agreement statistic is fabricated. Software registration time is separately labeled. Historical pending fields remain unchanged as evidence of the earlier state; this new registration establishes 72 confirmed decisions in each approved view, not 144 independent responses.

The reviewed primary 72 ratings include exactly six ordinal field changes in five records; the sensitivity view additionally adopts two PC023 ordinal changes. [The exact audit](validation/p1c/calibration_v1/annotation_gate_v1/six_field_revision_audit_v1.csv) preserves originals, evidence and reasons. No new categorical scoring was introduced during analysis. The eight prefixes remain sensitivity only, with original AMBIGUOUS status and non-unique boundaries. The original coupled scoring implementation remains a disclosed limitation despite subsequent item-level review and researcher adoption.

## Measurement and denominators

| Endpoint | Primary, all 72 | Accepted boundary sensitivity, same 72 |
| --- | --- | --- |
| Factual consistency | 43 Correct; 20 Incorrect; 9 Unverifiable | 47 Correct; 24 Incorrect; 1 Unverifiable |
| Temporal consistency | 43 Correct; 15 Incorrect; 14 Unverifiable | 47 Correct; 16 Incorrect; 9 Unverifiable |
| Task success | 43 success; 20 failure; 9 uncertain | 47 success; 24 failure; 1 uncertain |
| Component coverage | 44 at 1; 20 at 0; 8 unscorable | 48 at 1; 1 at .5; 23 at 0 |
| Semantic completeness | 64 YES; 8 UNCERTAIN | 72 YES |
| Response relevance | 60 at 5; 4 at 4; 8 unscorable | 68 at 5; 4 at 4 |
| Conversational coherence | 64 at 5; 8 unscorable | 72 at 5 |

All seven semantic endpoints are eligible for 72 requests. There are **zero missing researcher decisions** and no semantic N/A records; Persona Fidelity is not applicable because no authorized fidelity target exists. Primary categorical labels have 72 recorded values, but factual C/I assessment covers 63 and temporal C/I assessment 58. Eight boundary-unresolved units and PC006 interpretation uncertainty are not equivalent to evidence-based falsehood. Five additional entity/time ambiguities affect temporal assessability. The derived state retains boundary, interpretation and structural uncertainty separately without replacing the approved label.

43/72 = 59.72% is factual Correct-label incidence, not complete-answer accuracy or C/I accuracy. Pooled C/I descriptive accuracy is 43/63 = 68.25% factual and 43/58 = 74.14% temporal; these are selected-subset summaries, not paired factorial effects. Primary task success is bounded by 43/72 to 52/72 (59.72–72.22%) if its nine unknown outcomes were resolved. Factual unknown-outcome bounds have the same endpoints; temporal correctness bounds are 43/72 to 57/72 (59.72–79.17%). These are identification bounds, not confidence intervals. All 72 records remain present.

The legacy analysis JSON displays null scores as `Missing` in categorical tables. It does not mean an absent annotation: the [new explicit export](validation/p1c/confirmed_semantic_v1/exports/category_distributions_v1.csv) names this `UNSCORABLE_OR_UNCERTAIN_NULL` and preserves reason metadata. Existing analysis bytes and endpoint values are not rewritten.

## Construct discrimination

Factual C/I/U and task success/failure/uncertain agree on all 72 records. Their names do not establish scoring independence. The inspected content supports complete wrong answers (20 identifiable replies) and complete supported answers (43), with no correct-but-partial primary example. This dataset supplies little separation of these constructs. P1b separately has 27 factually correct partial replies among 137 Correct labels and only 110 full correct answers; the waves are not pooled.

Relevance and coherence agree for 60/64 scored replies; four route replies have relevance 4 and coherence 5. Coherence has zero observed score variance among identifiable replies and cannot discriminate conditions on that subset. All 64 identifiable replies are semantically complete, including wrong answers. Boundary-driven changes in YES-label incidence must not be presented as evidence of incomplete semantic content. Ordinal thresholds and paired signs are reported; descriptive mean differences do not validate an interval scale.

PC004 retains qualified room/desk alias acceptance. PC006's service-day versus Gregorian-weekday wording remains Unverifiable/uncertain. PC023 is scored only in the accepted sensitivity prefix, with the explicitly adopted interpretation limitation. The five route entity/time cases remain factual Incorrect and temporal Unverifiable: wrong entity does not prove wrong validity interval. These qualifications are preserved in the confirmed source records.

## Registered design and all 16 comparisons

The analysis units are 12 paired cases nested within six synthetic speakers, two cases per speaker. R compares parcel-related versus music-related auxiliary packages; T compares query-valid versus expired interval/value packages. R also changes lexical/predicate cues; T changes dates and some values. N_history is a length-matched **DIAGNOSTIC_ONLY** procedural control, not established semantic neutrality. H_none is shorter. These are restricted package interventions, not pure relevance, temporal cognition or stale-answer competition.

Using cell order R0T0, R0T1, R1T0, R1T1: R has weights (-.5,-.5,.5,.5), T (-.5,.5,-.5,.5), and RxT (1,-1,-1,1), an unscaled difference in differences. Other contrasts are the registered signed cell differences. Original weights, cell identities and policy hashes are preserved. No case is selected by baseline correctness; unknown cells are never renormalized away.

All values below are percentage points. F-C is factual Correct-label incidence; temporal Correct incidence is identical item-by-item here. T-I is temporal Incorrect-label incidence. Brackets for F-C are 95% percentile **speaker-resampling sensitivity intervals**, not guaranteed population coverage; task brackets are all-eligible **identification bounds**, a different object. Task n counts cases with every required nonzero-weight cell assessed. All detailed endpoint representations, categorical distributions, cases and speakers are in the [exports](validation/p1c/confirmed_semantic_v1/exports/factorial_effect_summary_v1.csv).

| Registered contrast | Primary F-C | F-C resampling interval | Primary T-I | Primary task bounds | Task n | Secondary F-C |
| --- | ---: | --- | ---: | --- | ---: | ---: |
| R | -4.17 | [-29.17, +20.83] | -12.50 | [-12.50, +16.67] | 8/12 | +0.00 |
| RxT | -8.33 | [-50.00, +25.00] | +25.00 | [-41.67, +16.67] | 8/12 | +0.00 |
| T | +4.17 | [-12.50, +25.00] | -4.17 | [-12.50, +16.67] | 8/12 | +0.00 |
| R1T0-R0T0 | +0.00 | [-33.33, +33.33] | -25.00 | [-8.33, +25.00] | 8/12 | +0.00 |
| R1T1-R0T1 | -8.33 | [-33.33, +16.67] | +0.00 | [-16.67, +8.33] | 10/12 | +0.00 |
| R0T1-R0T0 | +8.33 | [-16.67, +33.33] | -16.67 | [+0.00, +16.67] | 10/12 | +0.00 |
| R1T1-R1T0 | +0.00 | [-25.00, +25.00] | +8.33 | [-25.00, +16.67] | 8/12 | +0.00 |
| R0T0-N_history | +0.00 | [-25.00, +25.00] | +8.33 | [-8.33, +8.33] | 10/12 | +0.00 |
| R0T1-N_history | +8.33 | [+0.00, +25.00] | -8.33 | [+0.00, +16.67] | 11/12 | +0.00 |
| R1T0-N_history | +0.00 | [-25.00, +25.00] | -16.67 | [-8.33, +25.00] | 9/12 | +0.00 |
| R1T1-N_history | +0.00 | [-25.00, +25.00] | -8.33 | [-8.33, +16.67] | 10/12 | +0.00 |
| R0T0-H_none | +0.00 | [-25.00, +25.00] | +8.33 | [-8.33, +8.33] | 11/12 | +8.33 |
| R0T1-H_none | +8.33 | [-16.67, +33.33] | -8.33 | [+0.00, +16.67] | 10/12 | +8.33 |
| R1T0-H_none | +0.00 | [-25.00, +25.00] | -16.67 | [-8.33, +25.00] | 8/12 | +8.33 |
| R1T1-H_none | +0.00 | [+0.00, +0.00] | -8.33 | [-8.33, +16.67] | 10/12 | +8.33 |
| N_history-H_none | +0.00 | [-25.00, +25.00] | +0.00 | [-8.33, +8.33] | 10/12 | +8.33 |

For primary R/T/RxT task success, only eight cases from four speakers support complete required-cell comparisons. Their assessed-only contrasts are +6.25, -6.25 and +12.50 points, respectively; they are selected-subset sensitivities, not replacements for the unidentified all-eligible effects. Temporal C/I sensitivity uses seven cases/four speakers for these contrasts: +12.50, 0 and 0 points, with broad unknown-outcome bounds retained in the machine-readable results. No claim of unbiased complete-case selection is made.

## Uncertainty, heterogeneity and robustness

Each case contrast is averaged within speaker and the six speaker means receive equal weight. The unchanged procedure uses whole-speaker bootstrap seed 715004 and 10,000 draws, preserves both cases and all cells, and reports leave-one-speaker-out diagnostics. For factual Correct incidence, R's leave-one-speaker-out estimates span -15 to +5 points; T spans -5 to +10; RxT spans -20 to +10. The primary RxT has two positive, two negative and eight zero case contributions. Secondary R, T and RxT Correct-incidence means are all zero, with nonzero opposing contributions still present. Zero average is not proof of no interaction.

Only six purposively designed clusters exist. Resampling intervals can be unstable or degenerate, and endpoints/contrasts are numerous. All 16 comparisons and all outcome representations are disclosed without significance selection or confirmatory p-values. Bounds for unknown outcomes are distinct from sampling uncertainty; resampled bound endpoints are supplied as sensitivity only. Missingness can depend on condition. Complete-case point estimates and unscorable-category incidences answer different questions.

Each task family contains four cases/two speakers/24 outputs. Primary factual C/I/U counts are single retrieval 18/6/0, multiple components 12/5/7 and route integration 13/9/2. Corresponding temporal counts are 18/6/0, 12/5/7 and 13/4/7. Six ambiguous outputs occur in multiple-component tasks and two in route tasks. Family and speaker are nested, so these differences do not identify a complexity effect. [Family contrast contributions](validation/p1c/confirmed_semantic_v1/exports/task_family_contrasts_v1.csv) retain opposing case values and unidentified bounds.

The eight alternative prefixes change factual labels from Unverifiable to four Correct/four Incorrect, and temporal labels to four Correct/one Incorrect/three still Unverifiable. This changes R/T/RxT Correct-incidence point estimates to zero. The resulting within-output, then within-case measurement-effect contrasts are separately computed with the same weights; they do not replace the primary policy. Any apparent effect whose magnitude changes under these non-unique spans is measurement-sensitive, not a demonstrated cognitive mechanism.

## Algorithmic Opportunity Assessment

Observed failures include boundary uncertainty, wrong-entity answers and temporal mistakes. Existing role parsing, native stops, time/entity filtering, memory admission, verification and persona separation are mandatory baselines. The completed [offline investigation](P1c_offline_boundary_baseline_assessment_v1.md) finds no extra real-output recovery from fence awareness over a simple heading rule, and preserves false splits in authored fixtures. This is known engineering, not an original algorithm. Independent span truth, fair published-method comparisons, useful-history/persona retention and matched computational budgets are necessary before a stronger method claim.

## Reproducibility and next scientific step

Both full semantic analyses were reconstructed twice from frozen inputs with exact numerical equality. The snapshot precedes treatment joining; original masked files, raw outputs, tokenizer data, structural statuses and historical protocol remain unchanged. Human confirmation is complete for this exact snapshot, not for future annotations. New generation count is zero.

Recommend independent measurement validation first, then prospectively frozen independent empirical replication with stronger entity/date assignment and family balance. The [separate proposal](P1c_independent_validation_proposal_v1.md) distinguishes these goals and gives assumption-dependent precision and runtime ranges. A separate model-specific Instruct arm could test configuration sensitivity; it would not isolate post-training alone. Neither future inference nor a protocol change is authorized here. The current small development sample, shared coding lineage and absence of independent annotation/replication preclude publication-readiness or originality claims.
