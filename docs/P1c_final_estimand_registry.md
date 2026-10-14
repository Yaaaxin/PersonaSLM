# P1c Final Estimand and Evaluation Registry — Proposed v1

Maintainer: Yaxin ZHENG. Prospective and unapproved; no new outcomes analyzed. [Machine-readable registry](validation/p1c/final_review_v1/estimand_registry_proposed_v1.json) and [CSV](validation/p1c/final_review_v1/estimand_registry_proposed_v1.csv) retain every original weight and add scientific interpretation fields.

## Registered candidate contrasts

Cell order is **R0T0, R0T1, R1T0, R1T1, N_history, H_none**. Outcome Y is defined separately for each endpoint. There is no composite reliability score.

| Contrast | Exact weights | Interpretation |
|---|---|---|
| R | −1/2, −1/2, +1/2, +1/2, 0, 0 | Parcel-minus-music replacement averaged over interval/value settings |
| T | −1/2, +1/2, −1/2, +1/2, 0, 0 | Query-valid-minus-expired record replacement averaged over topics |
| RxT | +1, −1, −1, +1, 0, 0 | Unscaled difference in differences |
| R1T0−R0T0 | −1, 0, +1, 0, 0, 0 | Topic replacement at expired status |
| R1T1−R0T1 | 0, −1, 0, +1, 0, 0 | Topic replacement at valid status |
| R0T1−R0T0 | −1, +1, 0, 0, 0, 0 | Interval/value replacement in music records |
| R1T1−R1T0 | 0, 0, −1, +1, 0, 0 | Interval/value replacement in parcel records |
| Each of four active cells−N_history | +1 at active, −1 at neutral | Matched procedural-content comparison, subject to semantic approval |
| Each of four active cells−H_none | +1 at active, −1 at no history | Total content/length/archive package |
| N_history−H_none | 0, 0, 0, 0, +1, −1 | Added procedural dialogue package, including length |

Total: 16 contrasts. Every registry entry lists its cells, all 12 eligible case IDs, assumptions, confounders and prohibited interpretations. Lead the narrative with the four fixed-factor contrasts; report average effects and RxT as exploratory package contrasts. This reporting proposal does not silently adopt a new confirmatory hierarchy or rewrite P1b.

## Evaluation unit and endpoints

The [prospective policy](validation/p1c/final_review_v1/evaluation_policy_proposed_v1.json) applies `response_status_v1` and `separate_axes_policy_v1` without changing historical scores. The [applicability matrix](validation/p1c/final_review_v1/applicability_matrix_v1.json) contains 72 fixed rows: all eight declared axes apply, 12 per condition. Persona Fidelity is N/A because no fidelity target is supplied.

Primary descriptive endpoints remain Response Relevance, Factual Consistency, Temporal Consistency and Conversational Coherence. Separately report Task Success, Required-Component Coverage, Semantic Completeness and Structural Response Status.

Factual/temporal categories remain Correct, Incorrect, Unverifiable and Not Applicable; Missing is a separate administrative state. A demonstrably false answer is Incorrect. Unsupported/absent/unassessable claims are not automatically false. A correct intermediate route does not deliver the requested room. Full task success requires all requested supported components and no incompatible answer; a known partial/no-final reply can fail task delivery while remaining factually Correct or Unverifiable. Unknown reply units remain unknown, not binary failures. Complete wrong answers can be semantically complete.

Assess the frozen first reply. Do not substitute a later correct turn. CROSS_TURN and TRUNCATED are structural statuses, not factual labels. Raw continuation, parser operations, native stopping and any alternative boundary disposition remain separate. Requested date governs temporal truth; neither the newest fact nor the evaluation date is automatically the answer.

Stage A uses the [condition-masked semantic template](validation/p1c/final_review_v1/stage_a_semantic_template_v1.csv), with empty replies and ratings pending generation. It hides treatments, structural results and full continuations. Stage B uses the [separate structural template](validation/p1c/final_review_v1/stage_b_structure_template_v1.csv). The analyst-only mapping is a separate file, not access-control encryption. Presentation seed 715005 is distinct from execution seed 715001. Future response text may reveal treatment cues; do not claim perfect blinding. Source and researcher-confirmed annotations must remain separate if AI assistance is used.

## Denominators and uncertainty

Compute contrasts within paired cases, average each speaker's two case contrasts, then average six speakers equally. Retain all conditions and cases, including failures. There is no C0 condition here and no correctness-based inclusion rule. Task-family summaries contain four cases from only two speakers each.

Report eligible, evaluated, unscorable, Missing, Unverifiable and incomplete counts separately. Correct-label incidence on the frozen eligible denominator is not Correct-versus-Incorrect accuracy. For the latter sensitivity, require assessable outcomes in every nonzero-weight cell and disclose exclusions and possible condition-dependent censoring. Do not renormalize remaining factorial cells. Unknown binary values receive [0,1] identification bounds with signs of original weights retained; these are not sampling confidence intervals.

Keep full 1–5 relevance/coherence distributions, paired higher/equal/lower results and threshold/rank sensitivities. Means are descriptive, without assuming proven interval properties. Proposed uncertainty uses whole-speaker bootstrap seed 715004 with 10,000 draws, plus leave-one-speaker-out and signed case contributions. Six purposive clusters make intervals unstable; no population significance claim is justified.

Development multiplicity policy: disclose all 16 planned contrasts for each separately defined endpoint, without selecting favorable tests. Independent confirmation requires its own approved endpoint hierarchy and adjustment. The earlier proposed six-test temporal Incorrect/task-success × R/T/RxT family remains a candidate for that later freeze.

## Precision and independent validation

The original 135 sensitivity configurations are preserved. They use assumed contrast SDs and ICC 0/.2/.5, not empirical P1c variance. With two cases per speaker, normal half-width is `1.96*s*sqrt((1+ICC)/(2*K))`; six-cluster normal approximation may under-cover.

| Allocation | Main-effect half-width, SD=.25, ICC=.2–.5 | Interaction half-width, SD=.50 | Historical Base decode-time proxy |
|---|---:|---:|---:|
| 6 speakers, 12 development cases, 72 calls | ±15.50–17.32 pp | ±30.99–34.65 pp | 13.10 min |
| 48 new speakers, 96 independent cases, 576 calls | ±5.48–6.13 pp | ±10.96–12.25 pp | 104.81 min |
| 96 new speakers, 192 independent cases, 1,152 calls | ±3.87–4.33 pp | ±7.75–8.66 pp | 209.62 min |

These are planning sensitivities, not power claims or authorization. Doubling SD doubles margins; unknown outcomes and multiplicity can widen uncertainty further. Runtime proxies omit loading, longer-prompt effects and review labor. Independent validation needs new speakers/templates, independently assigned values, date/family balance, semantic review and a useful precision target selected before outcomes. Neither sample expansion nor a null pilot repairs confounding or proves absence of effects.
