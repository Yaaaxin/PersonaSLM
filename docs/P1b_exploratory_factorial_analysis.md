# P1b Exploratory Factorial Analysis

Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Target: PLOS ONE. Protocol v1.1 remains formal; v1.2 Revised Proposed r1 is unadopted. Exploratory development evidence only. No new inference.

## Estimands and units

The analysis population is 24 paired development cases in 12 synthetic speakers, not 192 independent observations. Conditions retain the frozen S/F/H routing. C1-C0 and C3-C0 are simple added-package contrasts at the other factors zero. S/F/H average four on-minus-off comparisons (weights +/-0.25). Pairwise interactions average difference-in-differences over the third factor (+/-0.5); SxFxH is the third-order difference (+/-1). [Exact specification](validation/p1b/confirmed_analysis_v1/factorial_specification_v2.json) was frozen after source-rating inspection but before this treatment join. No protocol amendment or neutral-adjusted contrast is made.

Categorical label-membership contrasts use the whole eligible category distribution. A zero for the Correct-label indicator means a different observed label, **not automatic factual Incorrect**. The separate Correct-versus-Incorrect sensitivity treats Unverifiable as unknown and uses an evaluable subset. All eligible cases remain in the reported denominators and signed unknown-value bounds. No C0-correct filter or outcome-based exclusion is applied.

## Main numerical inventory

The following first table is the complete **confirmed-span sensitivity**: all 192 adopted labels, with the unresolved BR168 unit explicitly included. It facilitates reproduction of the confirmed set; the conservative table below accounts for boundary uncertainty. Values are proportions for label/task outcomes and descriptive score points for ordinal outcomes. Multiplying a proportion difference by 100 gives percentage points.

| Contrast | factual_correct_label | temporal_correct_label | task_success | response_relevance | conversational_coherence |
| --- | --- | --- | --- | --- | --- |
| C1-C0 | -0.0417 | 0.0000 | -0.0417 | -0.0833 | 0.0000 |
| C3-C0 | -0.0417 | -0.0909 | -0.1250 | -0.3333 | -0.0833 |
| S | -0.1146 | -0.0909 | -0.0625 | -0.1250 | -0.0625 |
| F | 0.0104 | 0.0000 | -0.0625 | -0.2083 | -0.0208 |
| H | -0.1146 | -0.1818 | -0.1875 | -0.4167 | -0.1250 |
| SxF | 0.0208 | 0.0000 | 0.0417 | 0.0000 | 0.0000 |
| SxH | -0.0625 | 0.0000 | -0.0417 | -0.0833 | -0.1250 |
| FxH | 0.0208 | 0.0000 | -0.0417 | -0.0833 | 0.0417 |
| SxFxH | 0.2083 | 0.3636 | 0.0833 | 0.0000 | 0.0000 |


Boundary-conservative point estimates (23/24 evaluable cases for non-temporal semantics; temporal 11/11, because BR168 is temporal N/A):

| Contrast | factual_correct_label | temporal_correct_label | task_success | response_relevance | conversational_coherence |
| --- | --- | --- | --- | --- | --- |
| C1-C0 | -0.0435 | 0.0000 | -0.0435 | -0.0870 | -0.0435 |
| C3-C0 | -0.0435 | -0.0909 | -0.1304 | -0.3478 | -0.1304 |
| S | -0.1196 | -0.0909 | -0.0652 | -0.1304 | -0.0761 |
| F | 0.0109 | 0.0000 | -0.0652 | -0.2174 | -0.0326 |
| H | -0.1196 | -0.1818 | -0.1957 | -0.4348 | -0.1413 |
| SxF | 0.0217 | 0.0000 | 0.0435 | 0.0000 | 0.0217 |
| SxH | -0.0652 | 0.0000 | -0.0435 | -0.0870 | -0.1087 |
| FxH | 0.0217 | 0.0000 | -0.0435 | -0.0870 | 0.0652 |
| SxFxH | 0.2174 | 0.3636 | 0.0870 | 0.0000 | -0.0435 |


The conservative assessed-only mean is a changed coverage subset and is not silently presented as an unbiased full-population estimand. Bounds retain the 24 eligible units. Structural endpoints remain fully evaluable. The full machine record contains all 25 endpoint/sensitivity representations, both boundary policies and all nine contrasts, including every category indicator and ordinal threshold.

## Uncertainty, sign distribution and missingness

Whole-speaker bootstrap:10,000 draws,seed 714005; both cases and all cells move together. The temporal subset has 11 cases/nine speakers. These are empirical exploratory percentile intervals, potentially unstable with 12 purposive clusters, without simultaneous coverage, annotation uncertainty, repeated-model-seed uncertainty or population significance. Intervals excluding zero are not confirmatory discoveries. Degenerate intervals cannot prove absence. No p-values or post-hoc significance selection is used.

Boundary-conservative factual Correct-label incidence:

| Contrast | Evaluable/eligible cases | Eligible speakers | Estimate | Empirical 95% interval | Positive/negative/zero | All-eligible unknown bounds | Leave-one-speaker-out range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1-C0 | 23/24 | 12 | -0.0435 | [-0.1818, 0.0909] | 1/2/20 | [-0.0417, 0.0000] | [-0.0952, 0.0000] |
| C3-C0 | 23/24 | 12 | -0.0435 | [-0.2273, 0.1364] | 2/3/18 | [-0.0417, 0.0000] | [-0.0952, 0.0000] |
| S | 23/24 | 12 | -0.1196 | [-0.2727, 0.0119] | 1/6/16 | [-0.1146, -0.1042] | [-0.1548, -0.0714] |
| F | 23/24 | 12 | 0.0109 | [-0.0625, 0.0795] | 3/2/18 | [0.0104, 0.0208] | [-0.0119, 0.0357] |
| H | 23/24 | 12 | -0.1196 | [-0.2188, -0.0312] | 1/6/16 | [-0.1146, -0.1042] | [-0.1429, -0.0833] |
| SxF | 23/24 | 12 | 0.0217 | [-0.0455, 0.0909] | 2/1/20 | [0.0000, 0.0208] | [0.0000, 0.0476] |
| SxH | 23/24 | 12 | -0.0652 | [-0.2273, 0.0952] | 2/4/17 | [-0.0833, -0.0625] | [-0.1190, -0.0238] |
| FxH | 23/24 | 12 | 0.0217 | [-0.0833, 0.1364] | 2/3/18 | [0.0000, 0.0208] | [-0.0238, 0.0476] |
| SxFxH | 23/24 | 12 | 0.2174 | [0.0435, 0.4167] | 4/1/18 | [0.2083, 0.2500] | [0.1429, 0.2381] |


Boundary-conservative temporal Correct-label incidence:

| Contrast | Evaluable/eligible cases | Eligible speakers | Estimate | Empirical 95% interval | Positive/negative/zero | All-eligible unknown bounds | Leave-one-speaker-out range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1-C0 | 11/11 | 9 | 0.0000 | [-0.2500, 0.2500] | 1/1/9 | [0.0000, 0.0000] | [-0.1111, 0.1111] |
| C3-C0 | 11/11 | 9 | -0.0909 | [-0.5556, 0.2500] | 2/3/6 | [-0.0909, -0.0909] | [-0.2222, 0.0000] |
| S | 11/11 | 9 | -0.0909 | [-0.3125, 0.1112] | 1/3/7 | [-0.0909, -0.0909] | [-0.1500, 0.0278] |
| F | 11/11 | 9 | 0.0000 | [-0.1458, 0.1250] | 2/2/7 | [0.0000, 0.0000] | [-0.0556, 0.0500] |
| H | 11/11 | 9 | -0.1818 | [-0.4444, 0.0000] | 1/4/6 | [-0.1818, -0.1818] | [-0.2500, -0.1000] |
| SxF | 11/11 | 9 | 0.0000 | [-0.1500, 0.1154] | 1/1/9 | [0.0000, 0.0000] | [-0.0556, 0.0500] |
| SxH | 11/11 | 9 | 0.0000 | [-0.2308, 0.3333] | 2/2/7 | [0.0000, 0.0000] | [-0.1000, 0.1111] |
| FxH | 11/11 | 9 | 0.0000 | [-0.1818, 0.2500] | 1/2/8 | [0.0000, 0.0000] | [-0.1000, 0.0556] |
| SxFxH | 11/11 | 9 | 0.3636 | [0.0000, 0.6429] | 3/0/8 | [0.3636, 0.3636] | [0.2222, 0.4000] |


Factual Correct-versus-Incorrect evaluable-only sensitivity; Unverifiable stays unknown:

| Contrast | Evaluable/eligible cases | Eligible speakers | Estimate | Empirical 95% interval | Positive/negative/zero | All-eligible unknown bounds | Leave-one-speaker-out range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1-C0 | 21/24 | 12 | 0.0000 | [-0.1364, 0.1364] | 1/1/19 | [-0.0833, 0.0833] | [-0.0526, 0.0526] |
| C3-C0 | 21/24 | 12 | 0.0000 | [-0.1818, 0.1820] | 2/2/17 | [-0.0833, 0.0833] | [-0.0526, 0.0526] |
| S | 17/24 | 12 | 0.0000 | [-0.0667, 0.0735] | 1/2/14 | [-0.1771, 0.0521] | [-0.0333, 0.0167] |
| F | 17/24 | 12 | 0.0000 | [-0.0938, 0.0882] | 2/2/13 | [-0.0938, 0.1354] | [-0.0333, 0.0333] |
| H | 17/24 | 12 | -0.0588 | [-0.1334, 0.0208] | 1/3/13 | [-0.1875, 0.0417] | [-0.0781, -0.0333] |
| SxF | 17/24 | 12 | 0.0000 | [-0.0789, 0.0909] | 1/1/15 | [-0.2083, 0.2500] | [-0.0312, 0.0333] |
| SxH | 17/24 | 12 | 0.0000 | [-0.1875, 0.1750] | 2/2/13 | [-0.2708, 0.1875] | [-0.0667, 0.0667] |
| FxH | 17/24 | 12 | 0.0000 | [-0.1333, 0.1471] | 1/2/14 | [-0.2292, 0.2292] | [-0.0667, 0.0333] |
| SxFxH | 17/24 | 12 | 0.2353 | [0.0000, 0.5000] | 3/0/14 | [-0.2500, 0.6667] | [0.1333, 0.2667] |


Temporal Correct-versus-Incorrect evaluable-only sensitivity:

| Contrast | Evaluable/eligible cases | Eligible speakers | Estimate | Empirical 95% interval | Positive/negative/zero | All-eligible unknown bounds | Leave-one-speaker-out range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1-C0 | 10/11 | 9 | 0.0000 | [-0.2500, 0.2500] | 1/1/8 | [-0.0909, 0.0909] | [-0.1250, 0.1250] |
| C3-C0 | 9/11 | 9 | 0.0000 | [-0.5556, 0.3333] | 2/2/5 | [-0.1818, 0.0909] | [-0.1429, 0.1250] |
| S | 8/11 | 9 | 0.0000 | [-0.1429, 0.1786] | 1/2/5 | [-0.2273, 0.0909] | [-0.0714, 0.0357] |
| F | 8/11 | 9 | 0.0000 | [-0.2222, 0.1667] | 2/2/4 | [-0.1364, 0.1818] | [-0.0833, 0.0714] |
| H | 8/11 | 9 | -0.1250 | [-0.3333, 0.0417] | 1/3/4 | [-0.2955, 0.0227] | [-0.1786, -0.0714] |
| SxF | 8/11 | 9 | 0.0000 | [-0.1875, 0.1875] | 1/1/6 | [-0.2727, 0.3636] | [-0.0714, 0.0714] |
| SxH | 8/11 | 9 | 0.0000 | [-0.3333, 0.4375] | 2/2/4 | [-0.3182, 0.3182] | [-0.1429, 0.1667] |
| FxH | 8/11 | 9 | 0.0000 | [-0.2857, 0.3333] | 1/2/5 | [-0.3182, 0.3182] | [-0.1429, 0.0714] |
| SxFxH | 8/11 | 9 | 0.5000 | [0.0000, 0.8571] | 3/0/5 | [-0.2727, 1.0000] | [0.3333, 0.5714] |


Unknown bounds use sign-aware worst/best assignments within each case before averaging; they are not confidence intervals. Changing a condition's number of Unverifiable replies can change Correct-label prevalence without demonstrating more false statements. In fact, simple factual assessed-only contrasts are both 0 here, while full-label incidence decreases by one case in each. This discrepancy must remain visible.

## Heterogeneity and cancellation

Temporal SxH averages 0, but contributions are C_L1:+0.5,C_L3:-0.5,G_L1:-1,H_L3:+1. Removing one speaker changes the estimate across negative and positive values. A zero marginal interaction is not evidence that every case has zero interaction. The positive triple categorical contrast likewise does not establish a stable higher-order mechanism; compare its signed bounds, small effective samples and sensitivity to how Unverifiable is represented.

The confirmed-span H task-success average is-0.1875; leave-one-speaker-out estimates range-0.2045 to-0.1364. Contributions include both signs and span multiple families; history content, length, topic relevance and date status remain bundled. The raw C0 already has four factual/temporal errors. Neither these errors nor a history difference proves an isolated stale-memory mechanism.

Relevance/coherence are ordinal. Full category distributions, floor/ceiling frequencies and thresholds >=2,3,4,5 are retained. Threshold contrasts provide an ordinal sensitivity without assuming equal distances between adjacent ratings; threshold-specific results must not be selected for favorable signs. Family analyses have only three cases and are descriptive. Persona Fidelity remains unmeasured and separate.

## Full case and speaker evidence

- [All case-level contrasts](validation/p1b/confirmed_analysis_v1/analysis_v1/case_contrasts_v1.csv):10,800 rows, including explicitly inapplicable cases, cell values, analysis states and bounds.
- [Effect summaries](validation/p1b/confirmed_analysis_v1/analysis_v1/effect_summary_v1.csv):4,050 rows, all contrasts/policies/families.
- [Leave-one-speaker-out diagnostics](validation/p1b/confirmed_analysis_v1/analysis_v1/speaker_sensitivity_v1.csv):5,400 rows.
- [Metric coverage](validation/p1b/confirmed_analysis_v1/analysis_v1/metric_coverage_v1.csv):2,050 rows.
- [Full deterministic analysis](validation/p1b/confirmed_analysis_v1/analysis_v1/analysis_v1.json) and [input/output manifest](validation/p1b/confirmed_analysis_v1/analysis_v1/analysis_reproducibility_manifest_v1.json).

Results are development observations under one Base/GGUF/backend/template configuration. No pure style mechanism, independent interaction law, general factual accuracy, confirmed null, natural-person generalization or novelty claim follows.
