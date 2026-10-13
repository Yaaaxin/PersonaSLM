# P1 Wave 1 Structural–Semantic Comparison

Maintainer: Yaxin ZHENG. Protocol v1.1. Analysis version: `p1_researcher_annotation_analysis_v1`. Structural policy `response_status_v1` and all original automatic scores remain unchanged.

## Two different measurements

| Original structural status | Human complete first reply | Human incomplete first reply | Total |
|---|---:|---:|---:|
| COMPLETE | 0 | 0 | 0 |
| TRUNCATED | 0 | 17 | 17 |
| CROSS_TURN | 78 | 0 | 78 |
| AMBIGUOUS | 1 | 0 | 1 |
| Total | 79 | 17 | 96 |

All 96 first-reply units are researcher-confirmed. Structural non-COMPLETE prevalence is 96/96 under the **frozen automatic** policy, while semantic first-reply completeness is 79/96 (82.29%). These are not interchangeable failure rates. The original policy did not receive human completeness labels when it ran. Its zero COMPLETE count is not evidence that all first replies were unusable.

All 72 factual-eligible replies are among the CROSS_TURN group, and all 72 are now researcher-confirmed Correct. The remaining six CROSS_TURN replies are complete greetings with explicit constraint violations. The sole AMBIGUOUS reply is the seventh complete greeting. Every TRUNCATED reply is unfinished reasoning without a delivered answer and is predeclared factual/temporal N/A. Treating CROSS_TURN or TRUNCATED as factual errors would alter the construct and corrupt the eligibility denominator.

## Native termination and the first reply

There are 95 native output-budget stops and one native EOS. The cap governs the whole model continuation, so 78 capped continuations nevertheless contain a human-confirmed complete first reply before subsequent role-labelled turns. The 17 remaining capped replies are incomplete. The native EOS output is also judged complete.

MR069 maps to `p1_speaker_11_C`, C1, with 28 generated tokens and the saved EOS token 248044. Its frozen AMBIGUOUS classification and original reason remain untouched. The prior additive eos/eog enum diagnostic establishes a native boundary but does not itself supply completeness; this new human judgment is a separate evidence source. No new generation, stop rule, token budget or production policy was introduced.

The results demonstrate a **measurement distinction on these saved outputs**, not a causal effect of termination policy. No stop-policy intervention was randomized. A first-reply analysis measures that unit; it cannot claim the complete continuation would be safe or appropriate to show a user. Later fabricated turns remain preserved, but their factuality was not independently scored in this registration.

## Constraint and deliberation diagnostic

The separately versioned [constraint diagnostic](validation/p1/researcher_constraint_diagnostic_v1.json), `p1_constraint_following_diagnostic_v1`, retains the supplied, confirmed narrative categories. It does not redefine the four primary metrics or add a post-output factual denominator. Its labels describe the reported constraint violation or lack of a delivered answer; they are not a new independent human rating.

| Condition | Family-C records | Complete greeting with prohibited personal information | Unfinished reasoning without delivered answer |
|---|---:|---:|---:|
| C0 | 3 | 1 | 2 |
| C1 | 3 | 1 | 2 |
| C2 | 3 | 1 | 2 |
| C3 | 3 | 0 | 3 |
| C4 | 3 | 1 | 2 |
| C5 | 3 | 1 | 2 |
| C6 | 3 | 2 | 1 |
| C7 | 3 | 0 | 3 |
| Total | 24 | 7 | 17 |

The seven complete greetings introduce city/club information despite the request to avoid biographical claims. This is an instruction/relevance problem, not automatically a contradiction of trusted facts. The other seventeen do not supply a delivered answer; they are not silently counted as constraint-following successes. No family-C reply is registered as both delivered and satisfying that explicit constraint. This observation is restricted to three fictional speakers and the confirmed notes, with a separate prospective constraint rubric still advisable for future material.

## Consequences for condition contrasts

C1−C0 reduces CROSS_TURN by 8.33 percentage points, yet semantic completeness, relevance and coherence each have an observed paired difference of zero. The apparent structural improvement arises from MR069's different termination/classification, not an observed better first reply.

C3−C0 also reduces CROSS_TURN by 8.33 percentage points, but semantic completeness falls by 8.33 points and coherence by 0.25 score points, both in speaker11_C. Meanwhile relevance rises by 0.0833 points because speaker03_C changes from 2 to 3 despite remaining incomplete. The three constructs therefore support different descriptive statements. This is not evidence of a general persona effect; it shows why a structural proxy or a single composite score would be misleading here.

Average S×H is zero for CROSS_TURN but −4.17 percentage points for semantic completeness, −0.125 relevance points and −0.125 coherence points. Full case-level contrasts and uncertainty are in the [factorial report](P1_wave1_exploratory_factorial_analysis.md). These differences are concentrated in the nonfactual family, with three speakers; they do not identify a population interaction or a mechanism.

All 79 complete replies received coherence 5 and all 17 incomplete replies coherence 2 in the confirmed coding. This exact association makes those coherence contrasts algebraically tied to completeness in this sample; it is not independent evidence for two mechanisms. Numerical labels were assisted interpretations of narrative notes and then confirmed, not independently calibrated repeated ratings. Persona Fidelity was not measured.
