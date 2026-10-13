# P1b Calibration Task Discrimination Audit — v1

Maintainer: Yaxin ZHENG. Formal experimental baseline: Protocol v1.1. Protocol v1.2 Revised Proposed r1 remains prospective and unadopted. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. First submission target: PLOS ONE. Development evidence only; no new inference.

## Capacity versus demonstrated discrimination

The bank provides differing evidence operations and measurable candidate omissions/date mismatches. **It has not yet demonstrated a lower factual ceiling or an empirical difficulty ordering.** All 24 cases and all eight cells remain; no selection depends on C0 or a desired S/F/H direction. Source/query validation establishes answerability, not correctness of model replies or their internal reasoning process.

| Family | Intended demand | Identifiable / 24 | Interpretation limit |
| --- | --- | --- | --- |
| A | factual_retrieval | 24 | Direct lookup baseline; extra distractor records do not establish greater difficulty. |
| B | related_facts | 23 | Two to four requested components; response burden and integration are not separated. |
| C | validity_intervals | 24 | Inclusive date boundaries and prior-day lookup; explicit intervals may permit direct retrieval. |
| D | relational_reasoning | 24 | Relational proof chains have unique terminal entities; correct output does not prove multi-step reasoning. |
| E | relevant_history | 24 | Relevant old residence contrasts with current evidence; task family and history relevance are confounded. |
| F | entity_disambiguation | 24 | Explicit identity or unique role cues can resolve the target without difficult ambiguity. |
| G | historical_vs_current | 24 | Past/current site selection; two-date demand and fixed output budget may interact; no causal budget test. |
| H | context_followup | 24 | H_L1/H_L2 do not establish context necessity; H_L3 retains consecutive User turns. |


## Every case retained

| Case | Components | Facts / query steps | Temporal | Identifiable / 8 | Truncated / 8 |
| --- | --- | --- | --- | --- | --- |
| p1b_A_L1 | 1 | 1 / 1 | False | 8 | 0 |
| p1b_A_L2 | 1 | 2 / 1 | False | 8 | 0 |
| p1b_A_L3 | 1 | 3 / 1 | False | 8 | 0 |
| p1b_B_L1 | 2 | 2 / 2 | False | 8 | 0 |
| p1b_B_L2 | 3 | 3 / 3 | False | 8 | 0 |
| p1b_B_L3 | 4 | 4 / 4 | False | 7 | 0 |
| p1b_C_L1 | 1 | 3 / 1 | True | 8 | 0 |
| p1b_C_L2 | 1 | 3 / 1 | True | 8 | 0 |
| p1b_C_L3 | 2 | 3 / 2 | True | 8 | 0 |
| p1b_D_L1 | 1 | 2 / 2 | False | 8 | 0 |
| p1b_D_L2 | 1 | 3 / 3 | False | 8 | 0 |
| p1b_D_L3 | 1 | 4 / 4 | False | 8 | 0 |
| p1b_E_L1 | 1 | 2 / 1 | True | 8 | 0 |
| p1b_E_L2 | 1 | 4 / 2 | True | 8 | 0 |
| p1b_E_L3 | 1 | 6 / 3 | True | 8 | 0 |
| p1b_F_L1 | 1 | 4 / 1 | False | 8 | 0 |
| p1b_F_L2 | 1 | 4 / 2 | False | 8 | 0 |
| p1b_F_L3 | 1 | 6 / 3 | False | 8 | 0 |
| p1b_G_L1 | 1 | 3 / 1 | True | 8 | 1 |
| p1b_G_L2 | 1 | 3 / 1 | True | 8 | 0 |
| p1b_G_L3 | 2 | 3 / 2 | True | 8 | 4 |
| p1b_H_L1 | 1 | 1 / 1 | False | 8 | 0 |
| p1b_H_L2 | 1 | 3 / 2 | True | 8 | 0 |
| p1b_H_L3 | 1 | 5 / 2 | True | 8 | 0 |


The [24-case inventory](validation/p1b/measurement_audit_v1/task_discrimination_inventory_v1.csv) includes component references, evidence/question/context hashes, proof length, history relevance and structural coverage. Facts and steps are source counts, not complexity scores. Temporal applicability is 11 cases: C/E/G (three each) and H_L2/H_L3. Other facts carry validity metadata, but the predeclared task metric is not retrospectively changed.

## Evidence dependency and shortcuts

A is a valid easy direct-retrieval baseline; more distractors need not make it difficult. B adds required answer components, making brevity/96-token demand a competing explanation for incomplete answers. D's source path has two to four steps but a unique terminal entity permits shortcut selection; a correct building name cannot prove multi-hop reasoning. F often has explicit IDs or a unique archivist and terminal shelf. Keep these as measured lookup tasks rather than claim difficult ambiguity resolution.

C and G require selecting validity intervals at question-specific dates; explicit date tables reduce reasoning demands. C_L3 asks for a preceding-day value, while G_L3 asks two sites. E adds a relevant old residence, but relevance, domain and temporal task demands are not independently crossed. H_L1/H_L2 remain simple follow-up baselines with no demonstrated necessity for context; H_L3 retains consecutive User turns, so a format influence cannot be excluded. No source was edited in this audit.

## Observable review targets, not registered ratings

- The first execution request (C_L1) names Maple Counter whereas its April 5 reference is Birch Counter. This longstanding execution-order example motivates date-sensitive review; it is not a human error count.
- Some B replies omit a requested role; D replies may state crate assignment when a room or building is requested. Supported intermediate facts and complete answers must not share one label by default.
- All eight H_L2 first spans start with a promise to check rather than a declarative desk answer. F_L1 promises sometimes name a shelf, so the literal pattern alone cannot score delivery.
- The five G truncations and one B boundary ambiguity constrain unit coverage; other 186 CROSS_TURN replies still require semantic inspection.

Require source quotations and component-level notes to determine whether date selection, missing requested content or an unsupported statement caused low coverage. Extra gendered pronouns or incidental personal assertions, where unsupported, should be inspected rather than silently treated as attested speaker attributes. Do not award correctness for expected-word occurrence in later turns.

## Identification and next use

Within a case, evidence, question, fixed context, evaluation reference and model settings are identical across C0–C7. S/F/H add intervention packages that also alter length and content. Style is partly nested within speaker, F uses limited fact realization, and history relevance is partly nested within task family. No pure length-independent style, history-presentation or temporal-conflict mechanism is identified. P1 matched controls remain unreviewed; old approvals do not transfer.

Designed L1/L2/L3 outputs show 1/0/4 TRUNCATED responses respectively and one L3 ambiguity. These small, confounded counts do not establish monotonic difficulty. All cases remain development material; future independent tasks need orthogonalized templates/entities/date positions and untouched evaluation examples after an explicit design decision, not selection to manufacture persona effects.

## Algorithmic Opportunity Assessment

The current opportunity is improved measurement of supported-but-undelivered answers. A new reasoning algorithm is unjustified before reviewed errors reproduce. Retrieval or temporal-selection methods would need separate evidence-controlled baselines and independent material; no algorithm or new stimulus is implemented here.
