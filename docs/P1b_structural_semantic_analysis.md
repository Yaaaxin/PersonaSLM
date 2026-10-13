# P1b Structural and Semantic Measurement Comparison

Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Target: PLOS ONE. Protocol v1.1 remains formal; v1.2 Revised Proposed r1 is unadopted. Exploratory development evidence only. No new inference.

## Frozen structure versus adopted semantics

Original response_status_v1 remains COMPLETE0,TRUNCATED5,CROSS_TURN186,AMBIGUOUS1. No span or raw byte was changed. Semantic completeness is YES143,PARTIAL28,NO21. These describe different units: full continuation boundaries versus the supplied first reply. Neither categorical system replaces the other.

### semantic_completeness

| Structure | NO | PARTIAL | YES |
| --- | --- | --- | --- |
| COMPLETE | 0 | 0 | 0 |
| TRUNCATED | 4 | 1 | 0 |
| CROSS_TURN | 17 | 27 | 142 |
| AMBIGUOUS | 0 | 0 | 1 |

### answer_delivery

| Structure | FULL_ANSWER | NO_FINAL_ANSWER | PARTIAL_ANSWER | PARTIAL_WITH_FALSE_CLAIM | WRONG_ANSWER_DELIVERED |
| --- | --- | --- | --- | --- | --- |
| COMPLETE | 0 | 0 | 0 | 0 | 0 |
| TRUNCATED | 0 | 4 | 1 | 0 | 0 |
| CROSS_TURN | 109 | 17 | 26 | 1 | 33 |
| AMBIGUOUS | 1 | 0 | 0 | 0 | 0 |

### factual_consistency

| Structure | Correct | Incorrect | Unverifiable |
| --- | --- | --- | --- |
| COMPLETE | 0 | 0 | 0 |
| TRUNCATED | 1 | 0 | 4 |
| CROSS_TURN | 135 | 34 | 17 |
| AMBIGUOUS | 1 | 0 | 0 |

### temporal_consistency

| Structure | Correct | Incorrect | Not Applicable | Unverifiable |
| --- | --- | --- | --- | --- |
| COMPLETE | 0 | 0 | 0 | 0 |
| TRUNCATED | 1 | 0 | 0 | 4 |
| CROSS_TURN | 39 | 34 | 103 | 10 |
| AMBIGUOUS | 0 | 0 | 1 | 0 |

## Observable cases and causal limits

Of 186 CROSS_TURN outputs,109 contain full correct first replies,33 contain wrong delivered answers,26 partial supported replies,one partial false reply and 17 nonanswers. Thus rejecting every CROSS_TURN as factually wrong would invalidate measurement. Of five TRUNCATED outputs,one is a supported partial answer and four are Unverifiable unfinished reasoning; truncation is not equivalent to contradiction. The five remain in family G. Their native length termination is consistent with censoring but no controlled budget comparison here identifies its causal effect.

BR168 is the one AMBIGUOUS record. Its frozen span contains a complete four-component answer followed by `Factual question:`. The source explicitly flags EXTRA_GENERATED_QUESTION_IN_FIRST_REPLY and assigns coherence 4. Researcher semantic adoption is retained, but no human reply-boundary PASS is invented. Conservative numerical analyses mark this single unit unknown; confirmed-span sensitivity preserves all adopted labels. Neither silently truncates the span or changes response_status_v1.

Native termination remains 190 length/2EOS, versus 95 length/1EOS in Wave 1. Automatic extraction identifies 191/192 units here versus 96/96 there. Native termination, parser extraction, first-reply completeness and truth remain distinct. Subsequent generated turns are preserved for audit but not credited as answers to the first question.

## Descriptive cross-wave comparison

| Measure | Wave 1 | P1b | Interpretation |
| --- | --- | --- | --- |
| Cases / speakers | 12 / 12 | 24 / 12 | Do not pool responses as independent |
| Complete/Truncated/Cross-turn/Ambiguous | 0/17/78/1 | 0/5/186/1 | Different tasks and prompt construction |
| Human complete first reply | 79/96 | 143/192 | Binary Wave 1 versus explicit partial category here; preserve versions |
| Factual labels | 72C/0I/0U;24NA | 137C/34I/21U;0NA | Different eligibility/task mix |
| Temporal labels | 48C/0I/0U;48NA | 40C/34I/14U;104NA | Not an isolated difficulty effect |
| Full task success | No directly equivalent five-way code | 110/192 | Do not retrofit old annotations |
| Native budget stop | 95/96 | 190/192 | Both 98.96%; denominator differs |


The confirmed-span C1-C0 coherence mean is 0; boundary-conservative assessed-only mean is-0.0435 because removing BR168's numerical value removes a positive C0/C1 difference in that case. The semantic labels remain present. This illustrates measurement-unit sensitivity, not evidence to select the more favorable analysis. Complete case and speaker tables show structural and semantic contrasts side by side.

## Next measurement action

Seek an independently scored, condition-masked subset spanning all families and delivery categories, including BR168, before concluding high annotation reliability. A new unit interpretation must be separately versioned. No reinterpretation or new generation was executed here.
