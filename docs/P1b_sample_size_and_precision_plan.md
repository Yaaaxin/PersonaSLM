# P1b Sample Size and Precision Plan — Proposed v1

Maintainer: Yaxin ZHENG. PLOS ONE planning, not a confirmatory sample-size declaration. Protocol v1.1 remains formal. **Do not execute either larger allocation now.** Empirical discrimination and semantic coverage must first pass a separately authorized bounded calibration.

## Units and estimands

Conditions are paired within case; cases are clustered within speaker. More generated cells do not create more independent speakers. Future allocations below assign eight task families per speaker, with complexity levels rotated across speakers so each family has balanced levels (24 and48 are divisible by3). Independently counterbalance style realization against task/date/answer assignments. Template-family dependence remains; use multiple independent realizations and report sensitivity by family. No purposive synthetic allocation is a probability sample of real speakers.

Primary provisional simple comparisons remain C1−C0 and C3−C0. Average S/F/H effects use four on−off differences; pair interactions average two differences-in-differences; the triple interaction has eight signed terms. They are separate estimands and uncertainty calculations. Report four reliability dimensions separately, with structural status and semantic completeness separately. Neither 96 Wave 1 outputs nor future eight-cell repeats count as independent observations.

## Assumptions and reproducible calculation

For a **fully assessable** binary paired endpoint, let D=Y1−Y0, delta=E(D), and q=P(Y1 differs from Y0). Then Var(D)=q−delta². With n speakers, m cases per speaker, and ICC rho of **case-level paired differences**, use the planning approximation:

`DE = 1 + (m - 1) * rho`

`half_width ≈ z * sqrt((q - delta²) * DE / (n*m))`.

This is a large-sample normal approximation, not a validated power result, an observed confidence interval, or an assumption that all outputs are binary/evaluable. Small numbers of clusters, template dependence, unequal eligibility, and estimated variance can make it optimistic. Final sizing requires cluster-aware simulation and sensitivity after independent calibration; confidence interval computation must resample whole speakers with all paired cells, or use a justified small-cluster method. The old Wave 1 bootstrap that assumes one case per speaker cannot be reused unchanged.

The [machine-readable grid](validation/p1b/precision_plan_v1.json) includes q=0.10/0.30/0.50, rho=0/0.20/0.50 and one versus eight comparisons. These are **assumption ranges**, not estimates from 72 perfect answers. Illustrative effects of ±5 and±10 percentage points would use delta=0.05/0.10; at q=0.30 they reduce variance from0.30 to0.2975/0.29, but do not cure insufficient precision. Direction is never a design target. No observed Wave 1 ceiling is used to set q=0 as a planning certainty.

## Two candidate allocations

| Allocation | Speakers | Cases / speaker | Paired cases | Factorial requests / arm | Meaning |
|---|---:|---:|---:|---:|---|
| A | 24 | 8 | 192 | 1,536 | Moderate exploratory expansion; likely too imprecise for small effects |
| B | 48 | 8 | 384 | 3,072 | Better precision and replication across speakers; not automatically adequate for interactions or subgroup claims |

The new **24-case,12-speaker prototype bank is neither allocation A nor B**. It can support a bounded 192-request calibration only after approval. Larger allocations require new independently authored cases; they have not been generated or authorized. For the calculation below all eight families are factual-eligible. Four families per speaker (C/E/G/H) are assumed temporal-eligible in a *future balanced allocation*. That requires explicitly dated H items; the current prototype H_L1 is temporal N/A, so its actual 11/24 eligibility is not silently replaced by this planning assumption.

At q=0.30, delta=0, rho=0.20:

| Allocation / endpoint | Eligible paired cases | Effective case count | Approximate 95% half-width | Half-width using an eight-comparison Bonferroni critical value |
|---|---:|---:|---:|---:|
| A factual | 192 | 80 | 12.00 pp | 16.74 pp |
| A temporal | 96 | 60 | 13.86 pp | 19.33 pp |
| B factual | 384 | 160 | 8.49 pp | 11.84 pp |
| B temporal | 192 | 120 | 9.80 pp | 13.67 pp |

Sensitivity matters: factual A spans7.75–16.43pp as rho varies0–0.50; B spans5.48–11.62pp. Temporal A spans10.96–17.32pp and B7.75–12.25pp. At fixed rho0.20, changing q from0.10 to0.50 changes widths by factors sqrt(1/3) to sqrt(5/3) relative to the middle scenario. These ranges precede further uncertainty from unscorable items.

Under the same middle assumptions and individual 95% intervals, the formula requires approximately **35 speakers for factual ±10pp and47 for temporal ±10pp**. For ±5pp, it gives139 and185 speakers respectively. These are illustrative lower planning requirements before small-cluster correction, missingness, template dependence and multiplicity; they are not recommendations to generate that many cases. If scientific utility requires ±5pp, neither A nor B is sufficient under those assumptions. A meaningful precision margin must be agreed before scale-up.

## Interactions, ordinal outcomes and multiplicity

For any within-case contrast vector w, estimate its variance from `w' Sigma w`, not eight independent binomial variances. An averaged pair interaction is a difference-in-differences (range−2 to2 for binary outcomes); the triple interaction has range−4 to4. Their covariance structure is unknown from the ceiling pilot. For illustration, if the per-case interaction SD were0.5 and rho0.20, factual allocation A would give a normal half-width1.96×0.5/sqrt(80)=0.110; B0.0775. SD1 doubles those widths. These assumptions must be calibrated; a narrow main-effect interval does not establish interaction precision.

Ordinal relevance/coherence require full distributions and case-paired transitions. Means are descriptive, not a proven interval scale. Plan ordinal or rank-based sensitivity with speaker clustering; do not create a composite score. Do not use the seven possible factorial effects across every task, metric and model as uncorrected confirmatory discoveries.

For later confirmation, specify primary endpoints and contrast hierarchy with the researcher. Eight individual tests (two simple comparisons × four axes) illustrate a conservative Bonferroni precision penalty in the table; this is **not** adoption of an eight-test confirmatory family. Holm is a possible family-wise testing procedure after endpoint choice. Pilot interactions remain exploratory, with estimates and intervals, no significance claim. An equivalence claim needs a scientifically justified margin and appropriate interval/test fixed before independent data.

## Structural missingness and annotation uncertainty

Keep all pre-eligible outputs. Correct/Incorrect/Unverifiable/N/A are not silently recoded. For each condition, report category proportions on the eligible denominator and separately the assessed-only descriptive proportion. Treat missing/Unverifiable as unknown in sensitivity bounds: factual success lies between `Correct/N` and `(Correct+unknown)/N`; paired contrast bounds propagate case-level unknowns before speaker aggregation. Supported incomplete assertions are not forced to Incorrect. Score semantic completeness independently.

If assessment is unavailable in fraction u, a crude random-missingness precision calculation would inflate sample size by1/(1−u). This does **not** repair condition-dependent structural censoring or selection bias. A proposed ≥95% per-condition/metric assessment gate is about measurement feasibility; semantic incompleteness can still be fully assessed and must be reported. With small cells show exact counts; do not weaken the gate after seeing effects.

Use a condition-masked rubric calibration and, where feasible, a second genuine reviewer on a prospectively stratified subset or the full calibration. Save independent decisions before adjudication; report actual agreement only then. Future rater disagreement sensitivity is distinct from case-sampling uncertainty. The confirmed Wave 1 labels and their assisted provenance stay unchanged.

## CPU and annotation cost

Wave 1 observed mean response latency was9.427759seconds under the pinned Base/96-token configuration. Applying that historical rate gives **4.02 CPU wall-hours for A,8.05 for B**, one arm, excluding startup, tokenization, failures, annotation and analysis. New longer evidence may cost more: a declared1–3× latency sensitivity gives4.02–12.07 and8.05–24.14hours. These are cost scenarios, not measured P1b timings or a throughput guarantee.

The recommended bounded calibration is192 requests: approximately30.2minutes at the historical rate, or30.2–90.5minutes in that sensitivity range. An additional Instruct arm costs its own192 requests, with unknown measured throughput; do not assume equal speed. Two reviewed neutral conditions would add25% to an eight-cell factorial budget, but are not included or authorized. Deterministic repeats add cost without independent-case information. Human scoring cost has not been measured;1,536/3,072 replies across four axes may dominate the workload. No invented reviewer-hours estimate is provided.

## Scale-up gate

Do not choose A or B solely because either is affordable. First verify independent ground truth, real-tokenizer context fit, rubric coverage and task discrimination. Then agree on a useful interval width, a narrow scientific claim, sampling/realization plan and multiplicity policy. Choose the smallest allocation that plausibly meets that goal under conservative clustered assumptions. Retain an inconclusive or ceiling result when it occurs; do not expand until a desired effect appears.
