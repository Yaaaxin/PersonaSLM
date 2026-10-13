# P1c Statistical Precision Plan — Proposed v1

Maintainer: Yaxin ZHENG. This plan contains assumption-based calculations, not model results, achieved precision or a confirmatory power claim. Approval and a later confirmatory freeze are required.

## Unit, estimands and weighting

The paired unit is a case. Cases share speakers: six development speakers have two requested-date cases each. All six conditions are retained; 72 responses would not be 72 independent cases. Estimate a contrast within each case, then average the two cases within each speaker and average speakers equally. Family summaries are descriptive with only two development speakers per family. The proposed independent allocations balance three families and two requested-date strata.

With cell order (R0T0,R0T1,R1T0,R1T1), the weights are:

| Estimand | Weights | Meaning |
|---|---|---|
| R | (−1/2,−1/2,+1/2,+1/2) | Relevance averaged equally over temporal status |
| T | (−1/2,+1/2,−1/2,+1/2) | Validity averaged equally over relevance |
| R×T | (+1,−1,−1,+1) | Difference in differences, not divided by two |

Simple effects compare two cells at a fixed other factor. Each active−neutral contrast has (+1,−1) weights. No-history contrasts retain length confounding. [Machine-readable weights](validation/p1c/proposed_v1/condition_definitions_v1.json) are distinct from S/F/H weights; a new R or T coefficient is not the prior H effect.

## Outcomes and denominators

All 12 development cases are eligible for factual, temporal, relevance, coherence, task success, component coverage, semantic completeness and structural status. With six cells, each has 72 pre-eligible observations and 12 paired cases per contrast, before missingness. Fidelity is not scored: it requires separately justified style/behavioral ground truth. The [applicability matrix](validation/p1c/proposed_v1/applicability_v1.csv) is prospective, not an annotation result.

Factual and temporal outcomes retain Correct, Incorrect, Unverifiable and Not Applicable. Missing ratings are a fifth administrative state. On an all-eligible denominator, report each observed category incidence separately; its Correct indicator is not an assessed-only accuracy metric. Report eligible, observed, unscorable, incomplete and missing counts by condition. Unverifiable is never relabelled Incorrect. A case can have supported claims but incomplete requested components.

Task success requires all requested components supported, a delivered final answer and no incompatible final answer. Component coverage is the number of supported required components divided by the fixed required count. Failure to deliver is distinct from falsehood. The four reliability axes remain separate; there is no composite score. Relevance/coherence retain the established 1–5 ordinal rubric, with category tables and paired higher/equal/lower rates; means are descriptive. Threshold/rank summaries are secondary sensitivities, not independent discoveries.

Keep `response_status_v1` and first-reply extraction. Score identifiable first replies even when additional turns follow. Do not seek a correct later turn. If no defensible first unit exists, retain the structural label and mark the semantic measurement unavailable with an explicit reason. Report conservative unknown-unit results and any separately versioned, researcher-confirmed span sensitivity. No condition is excluded for C0 failure.

For Correct-versus-Incorrect sensitivity, use only cases whose required contrast cells are assessable and disclose the condition-dependent selection. For all-eligible correctness uncertainty bounds, replace unknown cell values by [0,1] and choose endpoints according to each contrast weight's sign. These are identification bounds, not confidence intervals and not hidden imputations. Missing annotation and structural unscorability remain distinguishable from a human Unverifiable label. No post-hoc change of weights is permitted.

## Assumption-based simulation

[Simulation output](validation/p1c/proposed_v1/precision_simulation_v1.json) and [CSV](validation/p1c/proposed_v1/precision_simulation_v1.csv) use seed 715003, 1,000 repetitions per scenario, 135 scenarios. The grid covers 6/48/96 speakers, two cases per speaker, paired-contrast ICC 0/.2/.5, effects 0/.05/.10 and contrast SD .25/.50 for main effects and .50/1.00 for interactions. T at SD .25 is separately represented. High-variance R cases also describe an analogous high-variance T assumption.

These are bounded **contrast-level** simulations, not fabricated answers or a fitted joint Bernoulli model. With probability ICC, a speaker's two residuals share one Rademacher sign; otherwise they are independent. Residual SD and within-speaker contrast correlation are therefore specified exactly. This establishes planning sensitivity without inventing empirical variance. It does not model all endpoint-cell covariances, nonresponse or unequal family variance. Effects of 0/.05/.10 are planning values, not effects assumed to exist.

For K speakers, m=2 cases, case-contrast SD s and ICC ρ, the normal planning half-width is `1.96*s*sqrt((1+(m−1)*ρ)/(K*m))`. The outputs include Monte Carlo normal-interval coverage and an illustrative Bonferroni-six normal margin. Normal coverage at six clusters is unreliable. The Monte Carlo error of a coverage estimate is itself up to about .016 at 1,000 repetitions. No sample size is universally sufficient.

| Independent speakers / cases / calls | Main-effect half-width, SD .25, ICC .2–.5 | R×T half-width, SD .50, ICC .2–.5 | Base response-time proxy |
|---|---:|---:|---:|
| Development: 6 / 12 / 72 | ±15.50–17.32 pp | ±30.99–34.65 pp | 13.10 minutes |
| Validation option A: 48 / 96 / 576 | ±5.48–6.13 pp | ±10.96–12.25 pp | 104.81 minutes |
| Validation option B: 96 / 192 / 1,152 | ±3.87–4.33 pp | ±7.75–8.66 pp | 209.62 minutes |

The high-variance assumptions double these margins. For a five-point ordinal contrast these probability-unit assumptions are not transferable: specify ordinal distributions and correlations separately at the future freeze. Thus even 96 speakers may be insufficient for a small interaction. Cost is not an argument for claiming adequate precision.

The cost proxy uses **192 actual P1b latency records**, total 2,096.152 seconds, mean 10.917 seconds/request. It excludes model loading, annotation, token matching, retries and idle time. New prompts are longer, so the transfer is uncertain. At .5×/1×/2× that runtime, the 72-call arm is approximately 6.55/13.10/26.20 response minutes. Instruct runtime is unmeasured. These are forecasts, not elapsed experiments.

## Uncertainty, multiplicity and independent validation

For eventual data, resample whole speaker clusters with both cases and all cells, fixed seed 715004, 10,000 bootstrap replicates; retain cluster and case contrasts plus leave-one-speaker-out estimates. With six development clusters, emphasize ranges and individual contributions rather than significance. Use studentized/hierarchical alternatives only under a separately frozen specification and report sensitivity. Do not interpret a zero aggregate as absence of interaction when contributions cancel.

Proposed primary family for a future approved R/T study: temporal Incorrect-label incidence and task success, each for R/T/R×T (six contrasts). Factual categories, ordinal metrics, structure, query-date strata and neutral comparisons remain secondary exploratory summaries unless prospectively promoted. At an independent confirmatory freeze, approve this hierarchy, useful precision target and Holm family before any outputs. Report all prespecified results, with no pilot significance claims. A normal Bonferroni planning margin is conservative planning support, not an analysis already performed.

Before selecting 48 or 96 speakers, the researcher must state a useful interval width and accept or revise plausible variance/ICC/missingness assumptions. Unknown fractions should be stress-tested at 0/10/25%: even infinite sample size cannot collapse worst-case unknown-outcome bounds without measurement assumptions. Plan annotation effort to reduce unresolved measurement, rather than increasing inference alone.

Independent validation must use new speakers, values and withheld wording templates, generated before any evaluation; separate development and validation manifests; blinded labels; fixed sample and analysis; no tuning after inspection. No confirmatory material is created here. If development shows unreliable manipulation or outcome measurement, fix the development design under a new version rather than recycling tested items into a validation claim.
