# P1c scientific closeout — v1

Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE. This is an additive scientific closeout, not a new analysis or a replacement of historical records.

## Completed evidence and source identity

The completed study contains 12 paired cases, six synthetic speakers, 72 successful real CPU requests and 72 researcher-adopted AI-assisted primary annotations. Sixteen exploratory contrasts were registered. The eight alternative prefixes are sensitivity-only, not independently certified boundaries. No independent second human annotation or inter-rater reliability was established.

The confirmed-analysis reproducibility manifest's 67 artifact hashes were checked against the current files. The approved annotation packet remains SHA-256 `4989e36d8d862c5995221b470adb8c9620ba7023ffc8ebf9d492cda18f6fc817`; the confirmed snapshot remains `e29bf9d5176e88bac2a74073254173bd992ff2b07eba3363086bd5f016afa915`. The actual approved prospective addendum is `p1c_addendum_proposed_v2`, SHA-256 `51d1987e2e91e2f4e72735304380e3f4442f418b731e972828677d24b7b96f55`, adopted through the later authorization record. Historical pending labels in its proposal are not silently rewritten. Protocol v1.1 remains unchanged; proposed v1.2 is not adopted.

Entry Git HEAD was `2fc0d6f58b484108e33205452832ceed9c33a7f7`, with a clean tracked tree. The existing [confirmed analysis](P1c_researcher_confirmed_exploratory_analysis_v1.md), [robustness report](P1c_confirmed_measurement_robustness_v1.md) and their machine-readable sources agree. The closeout does not repeat historical inference or the whole historical engineering suite.

## Observations and limits

| Outcome | Primary, denominator 72 | Interpretation |
| --- | --- | --- |
| Factual | 43 Correct, 20 Incorrect, 9 Unverifiable | Correct-label incidence is not evaluated-only accuracy |
| Temporal | 43 Correct, 15 Incorrect, 14 Unverifiable | Wrong entity, interval and semantic ambiguity remain distinguishable |
| Task | 43 Success, 20 Failure, 9 Uncertain | Item-level agreement with factual labels limits construct discrimination |
| Boundary | 64 CROSS_TURN, 8 AMBIGUOUS | 64 identifiable, semantically complete first replies; raw continuation is separate |
| Termination | 70 budget, 2 EOS | Termination does not determine factual correctness |
| Coherence | All 64 assessed ratings are 5 | Zero observed assessed variance; no ability to discriminate conditions here |

Primary Correct-label incidence contrasts are R −4.17, T +4.17 and R×T −8.33 percentage points. Speaker-bootstrap sensitivity intervals are respectively [−29.17, +20.83], [−12.50, +25.00], and [−50.00, +25.00]. All three means become zero in the approved alternative-boundary view, with nonzero case contributions capable of cancellation. This demonstrates measurement sensitivity, not that the parser caused every difference or that the alternative boundary is correct. Six purposively selected clusters do not justify guaranteed population coverage. Neither a stable average effect nor absence of interaction is established.

R changes topic, predicates, names and lexical cues; T changes intervals, dates and values. These are text-package contrasts. Procedural controls remain DIAGNOSTIC_ONLY, and no-history prompts are shorter. Pure relevance, pure temporal mechanisms and stale-answer competition are not identified. Earlier shared scoring, researcher adoption of AI suggestions, and response-text treatment cues limit independent measurement claims. P1b's 137 factual-Correct versus 110 full answers supports keeping constructs separate, but datasets are not pooled.

## Prioritized validity gaps

| Priority / limitation | Internal | Measurement | External | Precision | P1d response |
| --- | --- | --- | --- | --- | --- |
| 1: F boundary ambiguity | Yes, condition-dependent assessability | High | Template dependent | Unknown outcomes | Independent raw-span annotation and abstention |
| 1: C shared scoring; J no independent reviewer | Yes, assessment bias | High | Reviewer transfer | Agreement unknown | Separate scoring passes and independent subset |
| 1: G semantic bundles; H unvalidated controls | High | Manipulation validity | Real-world meaning | Not solved by larger N | Narrow source-selection estimands; separately test non-answer topical content |
| 2: B task discrimination; D coherence ceiling; E factual/task coincidence | Conditional | High | Task transfer | Low observed variance | Multi-component tasks and rubric challenge fixtures |
| 2: A six speakers | Limited stimulus sampling | — | High | High | Independent speakers and balanced task/date allocation |
| 2: I one Base configuration | Configuration confounding | Boundary coverage | High | Model interaction uncertain | Separate same-family instruction arm |

## Algorithmic Opportunity Assessment

**Observed Failure Modes:** inspectable boundary ambiguity and entity/time errors; an internal history-interference mechanism is unresolved. **Existing Methods and Published Prior Art:** the [updated comparison](P1d_published_baseline_comparison.md) covers temporal retrieval, admission, steering and verification. **Potential Algorithmic Improvements:** independent entity/date checks and boundary abstention deserve baseline evaluation. **Validation Feasibility:** existing heading and fence-aware parsing recover identical P1c candidates; authored fixtures are not independent accuracy. **Publication Value:** measurement validity and independent replication are the defensible next contribution; P1c alone is not submission-ready.

P1c is scientifically closed as development evidence. P1d is a new prospective proposal, not a retrospective upgrade of these observations to confirmation.
