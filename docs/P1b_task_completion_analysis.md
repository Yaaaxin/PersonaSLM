# P1b Task Completion and Ordinal Outcomes

Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Target: PLOS ONE. Protocol v1.1 remains formal; v1.2 Revised Proposed r1 is unadopted. Exploratory development evidence only. No new inference.

## Definitions and observed delivery

Answer delivery is not factual consistency. The adopted five-way labels are FULL_ANSWER110, WRONG_ANSWER_DELIVERED33, PARTIAL_ANSWER27, PARTIAL_WITH_FALSE_CLAIM1, NO_FINAL_ANSWER21. Semantic completeness is YES143,PARTIAL28,NO21. The 143 complete responses include 33 wrong delivered answers; complete is not correct.

The exploratory `task_success` diagnostic requires FULL_ANSWER, factual Correct and full source component coverage. All 110 FULL_ANSWER records meet these joint rules:110/192=57.29%. This is a post-generation diagnostic derived from confirmed source labels, not a replacement or newly declared primary factual endpoint. BR168 contributes one success in the confirmed-span sensitivity; conservative boundary accounting retains 109 known successes,82 known nonsuccesses and one unknown on the 192 denominator. Do not report 137/192 as complete-answer accuracy.

Component fractions are adopted annotations, not an independently validated automated scorer. Some partial truthful replies have 0/1 requested endpoints despite a correct intermediate assertion. Three uncommitted promises have 1/1 surface coverage yet no delivered answer. Coverage alone is not a success rule; semantic force, requested components, factual support and delivery matter separately.

## Joint categorical inventory

| Factual consistency | Delivery | Completeness | Structure | Count |
| --- | --- | --- | --- | --- |
| Correct | FULL_ANSWER | YES | AMBIGUOUS | 1 |
| Correct | FULL_ANSWER | YES | CROSS_TURN | 109 |
| Correct | PARTIAL_ANSWER | PARTIAL | CROSS_TURN | 26 |
| Correct | PARTIAL_ANSWER | PARTIAL | TRUNCATED | 1 |
| Incorrect | PARTIAL_WITH_FALSE_CLAIM | PARTIAL | CROSS_TURN | 1 |
| Incorrect | WRONG_ANSWER_DELIVERED | YES | CROSS_TURN | 33 |
| Unverifiable | NO_FINAL_ANSWER | NO | CROSS_TURN | 17 |
| Unverifiable | NO_FINAL_ANSWER | NO | TRUNCATED | 4 |


## Task-family range

Each family has 24 outputs from three paired cases/three speakers; speakers occur again across families and are not independent between families. A=direct retrieval; B=multiple related facts; C=temporal intervals; D=relational chains; E=relevant historical/current residence chains; F=entity identification; G=question-specific past/current validity; H=fixed-context follow-up.

| Family | Cases | Speakers | Factual C | Factual I | Factual U | Full correct | Partial | No answer | Temporal C | Temporal I | Temporal U | Temporal NA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 3 | 3 | 24 | 0 | 0 | 24 | 0 | 0 | 0 | 0 | 0 | 24 |
| B | 3 | 3 | 22 | 0 | 2 | 20 | 2 | 2 | 0 | 0 | 0 | 24 |
| C | 3 | 3 | 10 | 14 | 0 | 10 | 0 | 0 | 10 | 14 | 0 | 0 |
| D | 3 | 3 | 24 | 0 | 0 | 4 | 20 | 0 | 0 | 0 | 0 | 24 |
| E | 3 | 3 | 10 | 14 | 0 | 10 | 1 | 0 | 10 | 14 | 0 | 0 |
| F | 3 | 3 | 21 | 0 | 3 | 21 | 0 | 3 | 0 | 0 | 0 | 24 |
| G | 3 | 3 | 14 | 4 | 6 | 9 | 5 | 6 | 14 | 4 | 6 | 0 |
| H | 3 | 3 | 12 | 2 | 10 | 12 | 0 | 10 | 6 | 2 | 8 | 8 |


D is especially diagnostic:24/24 supported-claim labels but only 4/24 full requested answers. A remains 24/24 full, a valid easy baseline. B's nominally more complex third case is 8/8 full, so designed levels do not order empirical difficulty monotonically. E/C supply 28 of 34 contradictions; H_L2 supplies 8 nonanswers. F explicit identity cues permit simple identification; D's unique terminal entities can allow shortcuts. A correct final value does not prove the stated reasoning path was used.

## Ordinal outcomes and coverage

| Scale | 1 | 2 | 3 | 4 | 5 | Mean | Floor | Ceiling |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| response_relevance | 4 | 14 | 31 | 0 | 143 | 4.3750 | 4/192 (2.08%) | 143/192 (74.48%) |
| conversational_coherence | 0 | 4 | 1 | 18 | 169 | 4.8333 | 0/192 (0.00%) | 169/192 (88.02%) |


All 192 ordinal scores are registered; conservative numerical coverage is 191 because of BR168. Full family/condition score distributions are in [group summaries](validation/p1b/confirmed_analysis_v1/analysis_v1/group_summaries_v1.csv), alongside delivery and completeness. C has 14 wrong replies yet all 24 relevance/coherence scores 5; D has 20 partial replies yet coherence 5 throughout. Coherence, relevance and truth are demonstrably different measurements in these codings. Score-point means are descriptive; all four ordinal thresholds per scale are retained as sensitivity analyses.

## Paired task-success diagnostic

| Contrast | Evaluable/eligible cases | Eligible speakers | Estimate | Empirical 95% interval | Positive/negative/zero | All-eligible unknown bounds | Leave-one-speaker-out range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1-C0 | 24/24 | 12 | -0.0417 | [-0.1667, 0.0833] | 1/2/21 | [-0.0417, -0.0417] | [-0.0909, 0.0000] |
| C3-C0 | 24/24 | 12 | -0.1250 | [-0.3333, 0.0833] | 1/4/19 | [-0.1250, -0.1250] | [-0.1818, -0.0455] |
| S | 24/24 | 12 | -0.0625 | [-0.2188, 0.0833] | 3/6/15 | [-0.0625, -0.0625] | [-0.0909, -0.0114] |
| F | 24/24 | 12 | -0.0625 | [-0.1458, 0.0104] | 2/5/17 | [-0.0625, -0.0625] | [-0.0795, -0.0455] |
| H | 24/24 | 12 | -0.1875 | [-0.3125, -0.0938] | 1/10/13 | [-0.1875, -0.1875] | [-0.2045, -0.1364] |
| SxF | 24/24 | 12 | 0.0417 | [-0.0417, 0.1458] | 3/1/20 | [0.0417, 0.0417] | [0.0000, 0.0682] |
| SxH | 24/24 | 12 | -0.0417 | [-0.1875, 0.1042] | 3/4/17 | [-0.0417, -0.0417] | [-0.0909, 0.0000] |
| FxH | 24/24 | 12 | -0.0417 | [-0.1875, 0.1042] | 2/5/17 | [-0.0417, -0.0417] | [-0.0909, 0.0000] |
| SxFxH | 24/24 | 12 | 0.0833 | [-0.1667, 0.3333] | 4/2/18 | [0.0833, 0.0833] | [0.0000, 0.1818] |


This table includes the adopted ambiguous-span rating; the conservative variant remains in the main analysis. C0 through C7 full-success counts are 17,16,16,14,15,11,11,10, each out of 24. These are paired, heterogeneous development observations, not a dose-response law. The H contrast is distributed across several tasks, not proof of an isolated historical mechanism.
