# P1b Calibration Structural Analysis

Maintainer: Yaxin ZHENG. Version 1. Formal Protocol v1.1; proposed v1.2 r1 remains unchanged and unadopted. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE.

## Observed output structure

**COMPLETE: 0, TRUNCATED: 5, CROSS_TURN: 186, AMBIGUOUS: 1** across 192 real requests. Native termination counts: `{"eos": 2, "length": 190}`. Generated tokens: 71–96 per response, 18388 total. Latency: median 10.909s, range 8.900–14.643s; summed request latency 2096.152s. These are recorded execution observations, not a controlled hardware comparison.

Native output-budget termination applies to the full continuation. `response_status_v1` independently identifies first-reply structure; a continuation containing another role can be CROSS_TURN even though the backend stops at the budget. Frozen labels and excluded text are preserved. Semantic first-reply completeness remains unknown pending review.

Under this frozen policy, COMPLETE additionally requires a separate hash-bound completeness judgment. No such judgment was supplied during generation. Consequently, a zero COMPLETE count is not evidence that every first reply is semantically incomplete; do not reinterpret the policy's certification requirement as a model-performance statistic. Later human completeness labels remain separate from these frozen original statuses.

## Factorial condition

| Factorial condition | Requests | COMPLETE | TRUNCATED | CROSS_TURN | AMBIGUOUS |
|---|---|---|---|---|---|
| C0 | 24 | 0 | 0 | 23 | 1 |
| C1 | 24 | 0 | 0 | 24 | 0 |
| C2 | 24 | 0 | 1 | 23 | 0 |
| C3 | 24 | 0 | 1 | 23 | 0 |
| C4 | 24 | 0 | 0 | 24 | 0 |
| C5 | 24 | 0 | 1 | 23 | 0 |
| C6 | 24 | 0 | 1 | 23 | 0 |
| C7 | 24 | 0 | 1 | 23 | 0 |
## Task family

| Task family | Requests | COMPLETE | TRUNCATED | CROSS_TURN | AMBIGUOUS |
|---|---|---|---|---|---|
| A | 24 | 0 | 0 | 24 | 0 |
| B | 24 | 0 | 0 | 23 | 1 |
| C | 24 | 0 | 0 | 24 | 0 |
| D | 24 | 0 | 0 | 24 | 0 |
| E | 24 | 0 | 0 | 24 | 0 |
| F | 24 | 0 | 0 | 24 | 0 |
| G | 24 | 0 | 5 | 19 | 0 |
| H | 24 | 0 | 0 | 24 | 0 |
## Designed level

| Designed level | Requests | COMPLETE | TRUNCATED | CROSS_TURN | AMBIGUOUS |
|---|---|---|---|---|---|
| 1 | 64 | 0 | 1 | 63 | 0 |
| 2 | 64 | 0 | 0 | 64 | 0 |
| 3 | 64 | 0 | 4 | 59 | 1 |

Families A–H retain their frozen labels: retrieval, multi-fact integration, validity intervals, relational chains, relevant historical distractors, entity disambiguation, current/past distinction and context follow-up. L1–L3 are designed levels, not observed difficulty. Each family has three cases; style/persona and task/history associations limit causal interpretation of differences between families.

## Concentration and boundary inspection

All five TRUNCATED records are in family G: G_L1/C2 (`P1B-CAL1-113`) and G_L3/C3/C5/C6/C7 (`143`, `141`, `139`, `144` respectively, with the same request prefix). The four G_L3 continuations visibly start with a `<think>` block and end mid-continuation at 96 tokens. This is an observed text/termination pattern, not a human factuality score. These four H-present cells belong to one case, so they do not provide four independent replications of a general history effect.

The single AMBIGUOUS result is B_L3/C0 (`P1B-CAL1-036`): it reaches EOG after 71 tokens, but its extracted span includes an unrecognized `Factual question:` label and generated question before another Assistant turn. It requires extraction adjudication; retain the frozen span and status. G_L1/C1 (`P1B-CAL1-120`) also reaches EOG, after 77 tokens, with an additional generated user/assistant exchange and is CROSS_TURN. EOG therefore neither guarantees one turn nor resolves semantic completeness.

C1−C0's CROSS_TURN increase is entirely B_L3's AMBIGUOUS-to-CROSS_TURN transition. C3−C0's net zero combines the B_L3 increase with G_L3's CROSS_TURN-to-TRUNCATED change. A lower CROSS_TURN rate is not automatically an improvement: it can represent unfinished continuation without an observed next-turn boundary. These sparse transitions are why raw paired values and separate semantic measurements matter.

## Paired exploratory contrasts

| Contrast | CROSS_TURN difference (pp) | Nonzero cases | Leave-one-speaker-out range (pp) |
|---|---|---|---|
| C1-C0 | 4.167 | 1 | [0.000, 4.545] |
| C3-C0 | 0.000 | 2 | [-4.545, 4.545] |
| S | 2.083 | 2 | [1.136, 2.273] |
| F | 0.000 | 2 | [-1.136, 1.136] |
| H | -2.083 | 3 | [-3.409, 2.273] |
| SxF | 0.000 | 2 | [-2.273, 2.273] |
| SxH | -4.167 | 2 | [-4.545, -2.273] |
| FxH | 0.000 | 2 | [-2.273, 2.273] |
| SxFxH | 0.000 | 2 | [-4.545, 4.545] |

Every contrast above uses 24 case-level paired units, nested in 12 synthetic speakers. Exact case-level values, including zeros, are in [the contrast CSV](validation/p1b/calibration_v1/analysis_v1/structural_case_contrasts_v1.csv); summaries for all four structural outcomes and weights are in the analysis JSON. C1−C0 and C3−C0 are simple package contrasts. Main effects average four matched differences across the other factors. Two-way interactions are difference-in-differences averaged over the third factor; the three-way contrast differences those interactions. These scales are deliberately distinct and can have different numerical ranges.

The interval shown is **leave-one-speaker-out descriptive sensitivity**, not a confidence interval. No p value, population causal claim, significant effect or independent 192-observation inference is made. Finite-bank equality is not proof of a population null. Analysis code was prepared during execution after early raw responses were inspected; the weights came from the existing prospective precision plan, but these summaries are exploratory rather than confirmatory preregistration.

## Interpretation and Algorithmic Opportunity Assessment

Structural variation may affect measurement coverage, but cannot establish corresponding factual or temporal effects without semantic review. The existing Wave 1 labels (78 CROSS_TURN, 17 TRUNCATED, 1 AMBIGUOUS, 0 COMPLETE) remain historical; the banks and prompt configurations differ. Raw continuation rates alone do not establish a novel failure mode. A separately controlled boundary/template comparison may later test usable first-reply coverage, with false-cut and latency assessment, if review demonstrates a concrete need. No such comparison is executed here.

[Machine-readable analysis](validation/p1b/calibration_v1/analysis_v1/analysis_v1.json), [request measurements](validation/p1b/calibration_v1/analysis_v1/request_measurements_v1.csv), [native transport reconciliation](validation/p1b/calibration_v1/analysis_v1/transport_integrity_v1.json), and [hash inventory](validation/p1b/calibration_v1/analysis_v1/execution_inventory_v1.json).
