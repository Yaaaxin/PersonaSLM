# P0 C3 Evaluation Audit, Version 2

Date: 2026-10-12. Scope: the **14 C3 responses originally marked incorrect** by `current_city_legacy_v1`. This is a diagnostic audit of synthetic English city questions, not a new scientific endpoint or a Persona effect estimate.

The [original results](validation/P0_case_audit.json) and original evaluator remain unchanged. The supplemental [versioned audit](validation/P0_evaluation_audit_v2.json) preserves every raw response, old verdict/reason, run ID, source hash and new claim-level assessment. It uses `english_city_temporal_audit_v2` in a separate module. No historical result is silently rescored.

## Findings

The initial answer in all 14 responses supplies the evidence-supported current city. The legacy reason `incompatible_city_also_asserted` does not distinguish that answer from past claims in model-authored subsequent turns. This reason is unsupported as an allegation of a *current-city* conflict in all 14. That does **not** establish that all 14 complete outputs are factually correct.

| Nonexclusive diagnostic category | Responses | Interpretation |
|---|---:|---|
| Verifiable city/time contradiction | 2 | 008 and 018 repeatedly answer Nancy for “back then,” although the dated history identifies Metz |
| Generation stopped at the length limit | 14 | Native `stop_type=limit`, 96 generated tokens; this alone does not prove an incomplete initial answer |
| Temporal confusion supported by the contradictory claim | 2 | Same 008 and 018, under the explicit fixed-history interpretation below |
| Legacy current-conflict reason not supported | 14 | Correct first current-city answer followed by historical or unsupported claims |
| Undetermined claims or unfinished material | 11 | Mostly claims about 2023 or earlier, outside the supplied fact-validity intervals |

The whole-output **city-claim** audit returns 2 contradicted, 11 unverifiable, and 1 supported. These are bounded rule outputs with agent inspection, not independent human ground truth or an accuracy score. Categories overlap and must not be added together.

## Case-level inspection

All IDs below have prefix `synthetic_`. The complete text is retained in the linked JSON. “Cut tail” is an agent's structural inspection of the saved output, distinct from the native length-limit flag and from an independent human completeness rating.

| Case | Supplemental city status | Observable issue | Tail inspection |
|---|---|---|---|
| 002 | unverifiable | Nantes in 2023 is not established by the evidence | Last proposition has a city and year; no terminal punctuation |
| 003 | unverifiable | Lille in 2023 is unsupported | Cut model-authored question: `User: Where did` |
| 005 | unverifiable | Nice in 2023 is unsupported | Cut question: `User: Where did Alice` |
| 006 | unverifiable | Tours in 2023/2022 is unsupported | Cut question: `User: Where did the person live` |
| 008 | contradicted | Nancy asserted for the historical date; evidence says Metz | Cut question: `User: Where did` |
| 009 | unverifiable | Reims in 2023 is unsupported | Dangling `User:` header |
| 011 | unverifiable | Lyon in 2023 is unsupported | Cut question: `User: Where did Alice` |
| 012 | unverifiable | Nantes in 2023 is unsupported | Last proposition has a city and year; no terminal punctuation |
| 014 | unverifiable | Bordeaux in 2023/2022 is unsupported | Cut question: `User: Where did the person live in` |
| 015 | unverifiable | Nice in 2023 is unsupported | Cut question: `User: Where did Alice` |
| 017 | unverifiable | Caen in 2023 is unsupported | Incomplete role label `User` |
| 018 | contradicted | Same historical Nancy/Metz conflict as 008 | Cut question: `User: Where did` |
| 019 | supported | Orleans now and Reims then agree with supplied intervals; clear legacy false positive within this narrow scope | Last proposition has the current city; no terminal punctuation |
| 020 | unverifiable | Last answer concerns unsupported 2023 and is unfinished | Cut answer: `The person lived in Angers in` |

Thus 11/14 have visibly dangling questions, role labels or answer syntax at the end; the other 3 end on a recognizable city proposition without punctuation. All 14 hit the limit. These observations do not certify semantic completeness, and the first answers are separate from the generated continuations.

## Rules, regressions and limitations

The new audit splits actual generated `User:` / `Assistant:` boundaries, retains the first reply separately, resolves explicit dates/years, and checks claims against the existing fact-validity intervals. A year claim requires evidence covering that entire year. No fact supplied for 2023 is interpreted as **unverifiable**, not false. Model-authored follow-up questions are examined to interpret the continuation; they never become new benchmark inputs or change the fixed context.

For “back then,” the audit uses the unique dated synthetic history header. This is an explicit contextual interpretation, not a recovered hidden timestamp. Ambiguous temporal anchoring still warrants human review. Negation, quoted/conditional language, invalid dates, non-residence mentions, missing information and predeclared inapplicability have regression coverage. The original legacy evaluator is deliberately retained so saved-run reconstruction remains possible.

During development, a conservative residence-claim guard caused the short answer `Not Paris, Lyon.` to become unverifiable. A regression test caught this (1 failed, 146 passed). The implementation now recognizes that explicit contrast; the same test then passes. The failing test record remains in the command archive. No expected assertion was weakened.

This small English rule audit is not a general semantic parser. Non-city facts, unsupported personal details, fluency, dialogue coherence and persona fidelity require their existing separate procedures. Independent human adjudications completed: **0**. Evaluation acceptance remains **PARTIAL**, despite completion of this engineering audit.
