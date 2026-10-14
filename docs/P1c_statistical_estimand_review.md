# P1c Statistical Estimand Review — v1

Maintainer: Yaxin ZHENG. All proposed P1c effects remain unobserved. This review checks identification and planning assumptions without changing the original configuration or protocols.

## Exact contrasts and interpretation

Order: (R0T0, R0T1, R1T0, R1T1, N_history, H_none). [Versioned specification](validation/p1c/scientific_review_v1/factorial_contrast_specification_v1.json) contains all 16 contrasts, including every active-minus-neutral and active-minus-no-history comparison.

| Contrast | Weights | Interpretation |
|---|---|---|
| R | (−.5,−.5,+.5,+.5,0,0) | Mean auxiliary-topic replacement over two interval/value selections |
| T | (−.5,+.5,−.5,+.5,0,0) | Mean valid/expired record replacement over two predicates |
| R×T | (+1,−1,−1,+1,0,0) | Difference in differences, not divided by two |
| R at T0 | (−1,0,+1,0,0,0) | Expired parcel versus expired music |
| R at T1 | (0,−1,0,+1,0,0) | Valid parcel versus valid music |
| T at R0 | (−1,+1,0,0,0,0) | Valid versus expired music |
| T at R1 | (0,0,−1,+1,0,0) | Valid versus expired parcel |
| Any active−neutral | +1 at active; −1 at N_history | Approved limited content replacement, not pure mechanism |
| Any active−no-history | +1 at active; −1 at H_none | Total history package including length |
| Neutral−no-history | (0,0,0,0,+1,−1) | Added procedural dialogue/length package |

These are not previous H effects. Lead interpretation with fixed-factor simple contrasts because their changes are easier to state; retain average effects and the interaction without claiming that averaging removes lexical confounding. No contrast was chosen using P1c outcomes. The original proposed future six-test family (temporal Incorrect and task success × R/T/R×T) remains unapproved. The researcher must resolve the reporting hierarchy prospectively; this document does not silently replace it.

## Units, applicability and missingness

Compute each contrast per case, average the two cases within speaker, then average six speakers equally. Preserve both requested-date strata and every assigned cell. Each condition has 12 pre-eligible records; each applicable outcome has 72. Twelve cases sharing ledgers do not provide twelve fully independent clusters. Family comparisons have only two speakers each and remain descriptive.

Keep four reliability axes, task success, component coverage, semantic completeness and structure separate. Fidelity has no ground truth and is N/A. Factual and temporal categories are Correct, Incorrect, Unverifiable and Not Applicable; missing annotation is separate. Record first-reply unscorability, incomplete delivery and absent outputs independently. Preserve frozen structural status even when the first reply is correct. No C0-correct filtering or favorable-case deletion is permitted.

Correct-label and Incorrect-label incidences use frozen eligible denominators, with other observed categories reported separately. A zero Correct-label indicator does not assert Incorrect. Missing/unidentifiable units are unknown, not assigned category labels. Complete-case Correct-versus-Incorrect sensitivity needs all nonzero-weight cells assessable; report lost cases/speakers and condition-dependent selection bias. Do not renormalize factorial weights around missing cells.

For unknown binary outcomes, use [0,1] cell bounds, multiplying each endpoint according to the sign of its original weight before aggregation. These identification bounds are distinct from sampling intervals. Fully unknown main effects span [−1,+1]; R×T spans [−2,+2]. At unknown fraction q in every cell, the worst-case width is 2q for a main effect and 4q for R×T, even with arbitrarily many observations. Relevance/coherence retain 1–5 category tables and paired higher/equal/lower rates; score means are descriptive, with threshold/rank sensitivities instead of an assumed interval scale.

## Review of all 135 planning configurations

The saved simulation covers 6/48/96 speakers, two cases per speaker; ICC 0/.2/.5; effects 0/.05/.10; five contrast/SD combinations; 1,000 replicates each, seed 715003. This task checked every scenario's saved parameters and analytical precision formula against source; it did not rerun the 135,000 simulated datasets or misrepresent them as generations.

The construction is a bounded paired-contrast Rademacher sensitivity model, not fitted cell-level responses. No empirical ICC or P1c variance has been estimated. P1b H magnitudes are not guaranteed future R/T effects. Normal intervals with six clusters can undercover. Simulation coverage estimates have Monte Carlo error up to approximately .016. The precise stored coverage values remain in the [original simulation](validation/p1c/proposed_v1/precision_simulation_v1.json), including poor coverage; none is selected to justify GO.

With K clusters, two cases, case-contrast SD s and ICC ρ, normal half-width is `1.96*s*sqrt((1+ρ)/(2K))`.

| Allocation | Main effect, s=.25, ρ=.2–.5 | Interaction, s=.50, same ρ | Base response-time proxy |
|---|---:|---:|---:|
| Development: 6 speakers / 12 cases / 72 calls | ±15.50–17.32 pp | ±30.99–34.65 pp | 13.10 min |
| Independent option A: 48 / 96 / 576 | ±5.48–6.13 pp | ±10.96–12.25 pp | 104.81 min |
| Independent option B: 96 / 192 / 1,152 | ±3.87–4.33 pp | ±7.75–8.66 pp | 209.62 min |

Doubling s doubles the margin. For illustration, ±10 pp interaction precision at s=.50 and ρ=.2–.5 requires approximately 58–73 independent speakers before stratification, multiplicity or unknown outcomes; ±5 pp requires 231–289. These are algebraic sensitivity values, not recruitment recommendations. Interaction variance may be larger because its four signed weights have a wider range; covariance can also reduce it, so no universal fourfold sample requirement follows. Ordinal endpoints require their own variance assumptions.

Future whole-speaker bootstrap uses proposed seed 715004 and 10,000 draws, retaining both cases and all cells; also report leave-one-speaker-out ranges and signed case contributions. Six purposive clusters cannot justify population significance. No p-value or effect is calculated here. Development reports must show all planned results without multiplicity-based discovery selection. An independent confirmatory freeze must approve primary endpoints, useful margins, multiplicity family (e.g. Holm), missingness policy and sample size before outputs.

Independent validation should use fresh speakers, withheld templates and independently assigned values, balancing task families and requested-date strata before evaluation. Do not convert these 12 reviewed development cases into confirmation. Increased sample size cannot repair proposition/date coupling, invalid controls or unreliable annotation. Independent annotation and manipulation validity precede scale expansion.
