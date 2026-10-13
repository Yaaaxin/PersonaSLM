# P1 Wave 1 versus P1b — Measurement Comparison

Maintainer: Yaxin ZHENG. Formal experimental baseline: Protocol v1.1. Protocol v1.2 Revised Proposed r1 remains prospective and unadopted. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE. Development evidence only; no new inference.

## Verified descriptive comparison

Wave 1 confirmed labels and all immutable review fields were checked against its original masked master and saved SHA-256. P1b was reconstructed from its native journal. [Wave 1 comparison inputs](validation/p1b/measurement_audit_v1/wave1_verified_comparison_inputs_v1.json) retain the checks; historical annotations and automatic scores are untouched.

| Dimension | P1 Wave 1 | P1b calibration |
|---|---:|---:|
| Real responses / paired cases / speakers | 96 / 12 / 12 | 192 / 24 / 12 |
| COMPLETE / TRUNCATED / CROSS_TURN / AMBIGUOUS | 0 / 17 / 78 / 1 | 0 / 5 / 186 / 1 |
| CROSS_TURN rate | 81.25% | 96.875% |
| TRUNCATED rate | 17.708% | 2.604% |
| Frozen identifiable first units | 96/96 (including ambiguous MR069) | 191/192 |
| Human completeness | 79 COMPLETE, 17 INCOMPLETE | All 192 pending |
| Factual eligible / human scored | 72 / 72 | 192 / 0 |
| Temporal eligible / human scored | 48 / 48 | 88 / 0 |
| Relevance and coherence human scored | 96 each | 0 each |
| Confirmed factual / temporal Correct | 72/72 and 48/48 | Not estimated |
| Budget termination / EOS | **95 / 1** | **190 / 2** |
| Budget termination proportion | 98.958% | 98.958% |
| Task families | Four, including nonfactual greeting | Eight evidence-grounded families |

Wave 1 MR069 was AMBIGUOUS despite unit_identifiable=true and a subsequently confirmed complete reply. P1b's B_L3 ambiguity instead has unit_identifiable=false. These flags have different meanings; ambiguous counts alone cannot measure extraction coverage. Wave 1's 28-token EOS response prevents an inaccurate statement that all 96 outputs exhausted their budget.

The +15.625pp CROSS_TURN and −15.104pp TRUNCATED differences are descriptive across different banks. They cannot show improved or worsened semantic reliability. No comparable P1b human completeness or correctness rate exists yet. Historical Wave 1 automatic factual coding (15 Correct/57 Unverifiable) is scorer coverage under its limited grammar, not evidence to subtract from P1b's pending annotations.

## Why this is not a difficulty experiment

Task content, applicability, component counts, persona assignments, prompt construction and explicit fictional evaluation-date exposure differ. Both arms use the same Base model/backend and 96-token budget, but one changes task demands as a package. Relevance/history, evidence length and fixed context are not equal across waves. There are two P1b cases per synthetic speaker, versus one Wave 1 case; treating the extra responses as independent would overstate precision.

A future controlled test would hold speaker/style realization, S/F/H content, answerable evidence, template/date exposure, question family, inference and scoring unit constant, while prospectively manipulating one justified demand. Difficulty and answer length must be disentangled where possible. Independently constructed examples, all paired cells, explicit budget treatment and unit adjudication are needed. That proposal is not executed or silently added to Protocol v1.1.

## Algorithmic Opportunity Assessment

Equal budget-saturation proportions across different banks do not prove an invariant model mechanism. Persistent continuation motivates an operational model/template comparison, while confirmed first-reply annotations are needed to establish what it would improve. No boundary algorithm or extra generation is required to complete the current review.
