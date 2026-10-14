# P1d sample size and precision — proposed v1

Maintainer: Yaxin ZHENG. All results below are synthetic planning simulations, not model outputs or empirical ICC estimates.

## Simulation and selection rationale

`tools/p1d_precision.py` completed 216 configurations, 128 replicates each, producing 648 contrast summaries. The fixed base seed is 716101 plus scenario index. Candidate allocations are 48, 96 and 144 speakers with two cases each. Baseline prevalence is .25/.50/.75; four task-family offsets are balanced; main effects are zero or ±.05 and interaction zero or .10. Shared uniforms model paired cells and speaker dependence. Speaker-sharing parameters 0/.4 and paired-cell sharing .25/.75 are **not empirical ICC estimates**. They induce correlated binary outcomes and correlated contrasts; outcome ICC and contrast ICC need not coincide.

Missingness is absent, independently balanced at .10, or condition-dependent (.20 versus .05 by E). It is independent of the latent correctness conditional on the declared simulation variables; this is an assumption, not an established property of real unscorability. Outcome-dependent censoring can be worse. Bounds allow all unresolved binary outcomes without assuming missing at random. A supplementary 512-replicate stress run compares 96/144 speakers with sharing .7 and zero paired-cell sharing. Its 12 summaries were independently reconstructed exactly using `tools/p1d_precision_stress.py`.

| Speakers / cases / Base requests | Worst median ordinary 95% half-width, main effect | Interaction | Worst median six-comparison half-width, main / interaction |
| --- | ---: | ---: | ---: |
| 48 / 96 / 576 | 10.26 pp | 20.59 pp | 13.80 / 27.72 pp |
| 96 / 192 / 1,152 | 7.25 pp | 14.39 pp | 9.76 / 19.37 pp |
| 144 / 288 / 1,728 | 5.96 pp | 11.93 pp | 8.02 / 16.05 pp |

These maxima are across the primary grid's no-missingness configurations, not guaranteed future bounds. Under the stronger 512-replicate stress assumption, 144 speakers give simultaneous median half-widths about 9.22 pp for main effects and 18.38 pp for interaction; 96 speakers give 11.23 and 22.53 pp. Simulated complete-data coverage in that selected 144-speaker stress setting is approximately .941–.949. Only 128 replicates in the wide grid leave substantial Monte Carlo uncertainty (coverage SE around .02 at .95). No significance or guaranteed coverage is promised.

Recommend **144 speakers**, the smallest tested candidate meeting the proposed approximate simultaneous half-width targets of 10 pp main and 20 pp interaction even under this stress scenario. Practical effect thresholds of 10 pp main/20 pp interaction are prospective value judgments for researcher approval, not estimates borrowed from P1c. This design still cannot establish tight equivalence around small effects. Precision for each family and the 24-speaker model subset is substantially lower; those are secondary heterogeneity analyses.

## The limiting role of unresolved observations

At 96 speakers with .10 independent missingness, only about .655 of cases have all four active cells observed. Unknown-outcome identification width is approximately 19.5–20.4 pp for main effects and 39.1–40.9 pp for interactions. With .20/.05 condition dependence, about .577 of cases remain complete and widths are roughly 24.2–25.4 and 48.4–50.8 pp. More speakers reduce sampling noise but not a persistent unknown-outcome identification region. The grid's bounds contained every realized complete-data mean; this is an algebraic check, not empirical validity.

Interactions have weights ±1, compared with ±.5 for averaged main effects. For similar covariance, their standard errors are roughly twice as large, implying approximately four times as many units for equal absolute precision. The actual covariance matters. Reporting an assessed-only subset cannot rescue identification if assessability depends on condition. Never silently rescale remaining factorial cells.

## Planned estimation and cost

Compute all 16 registered P1d comparisons on whole cases. Average the two case contributions per speaker, then speakers equally. Retain categorical distributions, missingness, unknown bounds, case contributions, family/date strata and leave-one-speaker-out diagnostics. Whole-speaker bootstrap uses 10,000 draws, seed 716201, retaining both cases and all cells. Six primary endpoint-by-contrast comparisons receive conservative Bonferroni intervals in addition to ordinary intervals. Remaining comparisons are exploratory; no endpoint switching or outcome-based stopping. A simulation interval is a planning approximation, not a promise of confirmatory significance.

The actual P1c latency total was 1,156.563682 seconds for 72 requests: mean 16.06338447 seconds. At that reference speed, 576/1,152/1,728 calls cost 2.57/5.14/7.71 hours. The 288-call Instruct subset adds 1.29 Base-equivalent hours; this is **not measured Instruct runtime**. With 1–3× future prefill/generation cost, the full 2,016-call scope would take about 9–27 hours. Larger P1d prompts and independent templates invalidate a precise extrapolation. Peak RAM and Instruct latency must be measured during separately authorized preflight/development diagnostics.

At a planning assumption of 2–4 minutes per response, one pass over 2,016 outputs takes 67–134 human hours; a 25% second-review subset adds 17–34 hours before adjudication. These are workload assumptions, not observed annotation times. Independent review is likely the practical bottleneck. Fix cohort size before outputs; do not increase N until a preferred sign appears.

The separate analytic model-pair sensitivity uses a hypothetical within-speaker contrast ICC of .16 and between-model contrast correlations 0/.5/.9. With 24 paired speakers, ordinary main-effect-difference half-widths span 6.81–21.54 pp and interaction-difference half-widths 13.63–43.09 pp. These are declared covariance assumptions, not estimated ICCs. They reinforce that the small Instruct arm can diagnose gross coverage/configuration differences but cannot establish small model-specific mechanisms. `model_pair_precision_sensitivity_v1.json` preserves the formula inputs and outputs.
