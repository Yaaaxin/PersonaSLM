# P1 Wave 1 Exploratory Factorial Analysis

Maintainer: Yaxin ZHENG. Protocol v1.1. Analysis version: `p1_researcher_annotation_analysis_v1`. All results use the separately frozen researcher-confirmed annotations; original automatic evaluations and experimental inputs remain unchanged. This is exploratory analysis, not confirmatory preregistration or a population causal-effect claim.

## Analysis population and estimands

Twelve paired cases, one per fictional speaker, provide eight cells each (96 outputs). Three speakers belong to each scenario family. All 96 outputs remain, including TRUNCATED, CROSS_TURN and AMBIGUOUS; none is selected because C0 was correct. There are no missing generated records or unscorable confirmed labels. There are nine factually eligible case units and six temporally eligible units, not 72 or48 independent speakers.

C0=(0,0,0), C1=(1,0,0), C2=(0,1,0), C3=(0,0,1), C4=(1,1,0), C5=(1,0,1), C6=(0,1,1), C7=(1,1,1), ordered S/F/H. C1−C0 is a simple style-package contrast at F=H=0; C3−C0 is a simple history-package contrast at S=F=0. Main effects average on−off differences over the four settings of the other factors. Pairwise interactions average differences-in-differences over the remaining factor. The triple interaction is a difference-in-differences-in-differences. The weighting divisors are4,2,1 respectively, and exact weights are saved. These are not interchangeable estimands or isolated mechanisms.

The [specification](validation/p1/researcher_analysis_specification_v1.json) was fixed before this registration/unblinding, **after generation and after prior historical analyses were known**. It must not be described as pre-generation preregistration. The original wave's averaged interactions are retained; proposed v1.2 fixed-F hypotheses are not substituted.

For factual/temporal outcomes, Correct=1 and Incorrect=0 within frozen eligibility; Unverifiable would remain unscorable, not zero. Human labels here are all Correct on applicable records. Ordinal 1–5 relevance/coherence means are descriptive score-point summaries, not a validated interval scale or clinical/practical effect threshold. There is no composite reliability/fidelity score; Persona Fidelity remains unmeasured.

## Coverage and distributions

| Metric | Eligible responses | Evaluated | Missing/unscorable | Frozen N/A | Eligible paired cases |
|---|---:|---:|---:|---:|---:|
| Response relevance | 96 | 96 | 0 | 0 | 12 |
| Factual consistency | 72 | 72 | 0 | 24 | 9 |
| Temporal consistency | 48 | 48 | 0 | 48 | 6 |
| Conversational coherence | 96 | 96 | 0 | 0 | 12 |
| Semantic completeness / each structural indicator | 96 | 96 | 0 | 0 | 12 |

Relevance scores:72×5,11×3,13×2 (mean4.3646); coherence:79×5,17×2 (mean4.4688). Scores1/4 are absent. Semantic completeness is79/96. All72 factual and48 temporal labels are Correct; these are confirmed pilot annotations, not general accuracy estimates.

| Condition (12 outputs each) | Relevance mean | Coherence mean | Factual Correct / eligible | Temporal Correct / eligible | Semantically complete |
|---|---:|---:|---:|---:|---:|
| C0 | 4.3333 | 4.5000 | 9/9 | 6/6 | 10/12 |
| C1 | 4.3333 | 4.5000 | 9/9 | 6/6 | 10/12 |
| C2 | 4.3333 | 4.5000 | 9/9 | 6/6 | 10/12 |
| C3 | 4.4167 | 4.2500 | 9/9 | 6/6 | 9/12 |
| C4 | 4.3333 | 4.5000 | 9/9 | 6/6 | 10/12 |
| C5 | 4.3333 | 4.5000 | 9/9 | 6/6 | 10/12 |
| C6 | 4.5000 | 4.7500 | 9/9 | 6/6 | 11/12 |
| C7 | 4.3333 | 4.2500 | 9/9 | 6/6 | 9/12 |

Each condition has three factual N/A records and six temporal N/A records. All metrics have complete assessment coverage within frozen applicability. Complete assessment does not establish independent annotation validity; one researcher confirmed AI-assisted coding of their own narrative review.

## Paired effect estimates and uncertainty

Brackets below contain **95% empirical percentile bootstrap intervals** from10,000 resamples, seed713113. Whole case/speaker units are resampled within scenario family, preserving the observed three-per-family allocation and all eight cells. They describe sensitivity to empirical resampling, not representative population uncertainty, annotation uncertainty or new-seed/model variation. With only three speakers per family and purposive development material they can be highly discrete and optimistic. No significance tests, p-values, discovery selection or multiplicity-adjusted confirmatory conclusions are reported.

For every row: relevance/coherence have12 eligible/evaluable case units, factual9, temporal6; missing/unscorable0. Factual has3 inapplicable cases and temporal6. Exact paired values, case ranges and leave-one-case-out ranges for **all nine contrasts and nine outcomes** are retained in the [case CSV](validation/p1/researcher_case_contrasts_v1.csv), [summary CSV](validation/p1/researcher_contrast_summary_v1.csv) and [full JSON](validation/p1/researcher_factorial_analysis_v1.json).

| Contrast | Relevance points [empirical interval] | Coherence points [empirical interval] | Factual Correct proportion | Temporal Correct proportion |
|---|---|---|---|---|
| C1-C0 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0 [0, 0] | 0 [0, 0] |
| C3-C0 | 0.0833 [0.0000, 0.2500] | -0.2500 [-0.7500, 0.0000] | 0 [0, 0] | 0 [0, 0] |
| S | -0.0625 [-0.1250, 0.0000] | -0.0625 [-0.1875, 0.0000] | 0 [0, 0] | 0 [0, 0] |
| F | 0.0208 [0.0000, 0.0625] | 0.0625 [0.0000, 0.1875] | 0 [0, 0] | 0 [0, 0] |
| H | 0.0625 [0.0000, 0.1250] | -0.0625 [-0.3750, 0.1875] | 0 [0, 0] | 0 [0, 0] |
| SxF | -0.0417 [-0.1250, 0.0000] | -0.3750 [-0.7500, 0.0000] | 0 [0, 0] | 0 [0, 0] |
| SxH | -0.1250 [-0.2500, 0.0000] | -0.1250 [-0.3750, 0.0000] | 0 [0, 0] | 0 [0, 0] |
| FxH | 0.0417 [0.0000, 0.1250] | 0.1250 [0.0000, 0.3750] | 0 [0, 0] | 0 [0, 0] |
| SxFxH | -0.0833 [-0.2500, 0.0000] | -0.7500 [-1.5000, 0.0000] | 0 [0, 0] | 0 [0, 0] |

The [0,0] intervals for ceiling outcomes or identical observed paired scores are **degenerate empirical intervals**, not proof of zero population uncertainty, equivalence or no persona effect. The resampling distribution cannot invent unobserved errors. Factual/temporal contrasts have no observed within-metric variation; a general null is not identifiable with these tasks and this evidence.

| Contrast | Semantic completeness percentage points [empirical interval] | CROSS_TURN percentage points [empirical interval] |
|---|---|---|
| C1-C0 | 0.0000 [0.0000, 0.0000] | -8.3333 [-25.0000, 0.0000] |
| C3-C0 | -8.3333 [-25.0000, 0.0000] | -8.3333 [-25.0000, 0.0000] |
| S | -2.0833 [-6.2500, 0.0000] | -4.1667 [-6.2500, 0.0000] |
| F | 2.0833 [0.0000, 6.2500] | 4.1667 [0.0000, 6.2500] |
| H | -2.0833 [-12.5000, 6.2500] | 0.0000 [-6.2500, 6.2500] |
| SxF | -12.5000 [-25.0000, 0.0000] | -8.3333 [-12.5000, 0.0000] |
| SxH | -4.1667 [-12.5000, 0.0000] | 0.0000 [-12.5000, 12.5000] |
| FxH | 4.1667 [0.0000, 12.5000] | 0.0000 [-12.5000, 12.5000] |
| SxFxH | -25.0000 [-50.0000, 0.0000] | -33.3333 [-75.0000, 0.0000] |

All other structural indicators are in the full machine-readable results, with the same12-case denominator, exact case outcomes and uncertainty. Frozen structural COMPLETE is always0, with an explicitly degenerate empirical distribution. No historical label was replaced by the human completeness judgment.

## Complete case-level rating inventory

Each vector lists C0,C1,C2,C3,C4,C5,C6,C7. Full case contrasts are exported including frozen inapplicable cells, which remain blank with an explicit N/A reason rather than zero.

| Paired case | Relevance vector | Coherence vector |
|---|---|---|
| p1_speaker_01_A | 5, 5, 5, 5, 5, 5, 5, 5 | 5, 5, 5, 5, 5, 5, 5, 5 |
| p1_speaker_02_B | 5, 5, 5, 5, 5, 5, 5, 5 | 5, 5, 5, 5, 5, 5, 5, 5 |
| p1_speaker_03_C | 2, 2, 2, 3, 2, 2, 3, 2 | 2, 2, 2, 2, 2, 2, 5, 2 |
| p1_speaker_04_D | 5, 5, 5, 5, 5, 5, 5, 5 | 5, 5, 5, 5, 5, 5, 5, 5 |
| p1_speaker_05_A | 5, 5, 5, 5, 5, 5, 5, 5 | 5, 5, 5, 5, 5, 5, 5, 5 |
| p1_speaker_06_B | 5, 5, 5, 5, 5, 5, 5, 5 | 5, 5, 5, 5, 5, 5, 5, 5 |
| p1_speaker_07_C | 2, 2, 2, 2, 2, 2, 3, 2 | 2, 2, 2, 2, 2, 2, 2, 2 |
| p1_speaker_08_D | 5, 5, 5, 5, 5, 5, 5, 5 | 5, 5, 5, 5, 5, 5, 5, 5 |
| p1_speaker_09_A | 5, 5, 5, 5, 5, 5, 5, 5 | 5, 5, 5, 5, 5, 5, 5, 5 |
| p1_speaker_10_B | 5, 5, 5, 5, 5, 5, 5, 5 | 5, 5, 5, 5, 5, 5, 5, 5 |
| p1_speaker_11_C | 3, 3, 3, 3, 3, 3, 3, 3 | 5, 5, 5, 2, 5, 5, 5, 2 |
| p1_speaker_12_D | 5, 5, 5, 5, 5, 5, 5, 5 | 5, 5, 5, 5, 5, 5, 5, 5 |

All nonzero relevance or coherence changes occur in the three C-family speakers. C3−C0 relevance +1 in03_C gives +1/12 overall; C3−C0 coherence −3 in11_C gives −3/12. Removing those respective single cases yields zero for those contrasts. Relevance S×H is nonzero in03_C and07_C; coherence S×H only in03_C. Relevance triple interaction arises in07_C, coherence triple interaction in03_C and11_C. Nine factual-task speakers show no score variation. Family, style and speaker are not independently crossed in this wave.

The source categories explain the scale distribution: seven complete greetings violate the no-biographical-claims request and receive relevance3/coherence5; seventeen unfinished reasoning replies receive relevance2 or3/coherence2. The association between completeness and coherence is exact in these codings. It is not two independent confirmations of a mechanism. Distinctions between ordinal values2 and3 were assisted interpretations subsequently accepted by the researcher, not independently selected in the original narrative questionnaire.

## Ceiling and identification limits

The factual/temporal ceiling is consistent with directly visible sufficient evidence, simple current-city/membership questions, repeated answer predicates, short contexts and limited temporal reasoning demands. Existing history is genuinely dated past information, not necessarily a difficult contradiction. These explanations are plausible task properties, not experimentally separated causes of the ceiling. Do not create artificial errors, alter the old questions, or interpret the pilot as generally reliable.

S/F/H are operational packages with residual wording, length, content and relevance differences. H does not independently randomize relevance, temporal status and format. New neutral controls remain0/24 reviewed, OPEN; no neutral response exists and no control-adjusted contrast is estimated. Broad factual interference, pure style mechanisms, post-training effects and real-speaker fidelity remain unestablished.

The defensible conclusion is a small, fully traceable exploratory comparison with factual/temporal ceilings and concentrated nonfactual structure/score variation. See the [structural–semantic report](P1_wave1_structural_semantic_comparison.md), [publication assessment](P1_wave1_publication_readiness.md) and [next-step recommendation](P1_wave1_next_experiment_recommendation.md). No new model response was generated.
