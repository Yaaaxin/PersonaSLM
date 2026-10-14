# P1d output-policy calibration — scientific report v1

Maintainer: Yaxin ZHENG. This is development evidence on eight authored cases, not independent P1d validation. All **144 semantic records are AI-assisted proposals; zero researcher adoptions or independent human annotations are registered**.

## Question, controls and primary measurement

Does changing only the output cap from 96 to 192 or 256 improve first-answer delivery and measurement adequacy? Eight development cases × six conditions are paired across caps. Prompts, evidence, requested dates, references, fixed context, model and decoding remain fixed. Budget order is frozen. Main E/V effect signs are neither estimated for policy selection nor used to choose a cap; the original S/F/H research programme remains central.

The [measurement plan](P1d_budget_measurement_plan_v1.md) retains original `response_status_v1` spans and separate relevance, factual, temporal, coherence, task, component, completeness and narrow style outcomes. Reaching the cap is not automatically task failure. Claims, components and ordinal evidence were separately assessed. Exact identical measurement inputs share a documented AI assessment across 22 groups; this is not independent repeat annotation. Review files omit budget/condition labels, but the analyst prepared execution materials and can access the mapping, so complete blinding is not claimed.

## AI-proposed semantic observations, full denominator

| Cap | Factual labels /48 | Temporal labels /48 | Task labels /48 | Semantic completeness /48 |
| --- | --- | --- | --- | --- |
| 96 | {'Correct': 1, 'Unverifiable': 47} | {'Unverifiable': 48} | {'Failure': 48} | {'NO': 48} |
| 192 | {'Correct': 1, 'Unverifiable': 47} | {'Unverifiable': 48} | {'Failure': 48} | {'NO': 48} |
| 256 | {'Correct': 1, 'Unverifiable': 47} | {'Unverifiable': 48} | {'Failure': 48} | {'NO': 48} |

| Cap | Relevance /48 | Coherence /48 | Narrow style fidelity /48 |
| --- | --- | --- | --- |
| 96 | {'2': 5, '3': 43} | {'3': 28, '5': 20} | {'3': 1, '4': 14, '5': 33} |
| 192 | {'2': 5, '3': 43} | {'3': 28, '5': 20} | {'3': 1, '4': 14, '5': 33} |
| 256 | {'2': 5, '3': 43} | {'3': 28, '5': 20} | {'3': 1, '4': 14, '5': 33} |

Required-component slot counts (separate presence and support judgments): `{96: {'required': 84, 'present': 0, 'supported': 0}, 192: {'required': 84, 'present': 0, 'supported': 0}, 256: {'required': 84, 'present': 0, 'supported': 0}}`. Slots within a response/case are not independent observations. No missing component is converted automatically into an incorrect factual claim.

See [all 144 masked item proposals](validation/p1d/budget_calibration_v1/analysis_v1/primary_AI_proposals_UNCONFIRMED_v1.csv), including exact spans, ledger evidence, components, distinct justifications, uncertainty, alternatives and blank researcher fields. The [JSON version](validation/p1d/budget_calibration_v1/analysis_v1/primary_AI_proposals_UNCONFIRMED_v1.json) preserves nested evidence. Case/family distributions and complete paired contributions remain machine-readable.

The dominant observed content is a future promise, question replay or simulated USER RESPONSE, with requested values absent in the primary spans. A changed person in a repeated question is a referential/relevance defect, not automatically an incorrect factual assertion. Generic policy echoes can receive a supported-claim proposal while still failing temporal selection and complete delivery. Their alternative Unverifiable interpretation is explicitly retained. A simulated lack-of-ledger statement has unresolved speaker attribution and a documented Incorrect alternative if adjudicated as the assistant denying supplied evidence.

The no-additional-history arm has these AI-proposed task outcomes (eight cases per cap): `{96: {'Failure': 8}, 192: {'Failure': 8}, 256: {'Failure': 8}}`. A delivery problem also present without additional history cannot be attributed solely to the historical packages. Repetition of a fixed-context commitment motivates a formatting hypothesis, but observational overlap does not prove that commitment or the template caused the failure. The purpose of repairing measurement is to make the original persona-conditioning question testable, not to replace it with a parser-only study.

Unverifiable therefore includes **no evaluable answer claim** and **interpretation/attribution uncertainty**, rather than a common falsehood category. Boundary-unresolved, structurally unscorable, N/A and administrative Missing remain different states. All source applicability flags are retained. Factual Correct-label incidence and Correct/(Correct+Incorrect) are reported separately; an assessable-only rate based on a few policy statements is not task accuracy. No score was changed to manufacture variance.

The [metric-discrimination table](validation/p1d/budget_calibration_v1/analysis_v1/metric_discrimination_v1.json) preserves factual/task/completeness cross-tabs, relevance/coherence pairings, ordinal ceilings and invariant endpoints. Conceptual separation and distinct AI rationales do not establish independent human measurement reliability. A clear, coherent commitment can still fail the task; any endpoint with no observed variation cannot discriminate conditions in this sample and is retained rather than retrospectively dropped.

## Boundaries and truncation

The original structural classifications remain unchanged. Paired first-span/token-prefix counts are `{'96-192': {'blocks': 48, 'same_first_span': 48, 'lower_token_prefix': 48}, '96-256': {'blocks': 48, 'same_first_span': 48, 'lower_token_prefix': 48}, '192-256': {'blocks': 48, 'same_first_span': 48, 'lower_token_prefix': 48}}`. The [continuation diagnostics](validation/p1d/budget_calibration_v1/boundary_diagnostics_v1/summary_v1.json) compare seven extraction views, preserving all candidate offsets and original text. Native EOS, literal stops, role/section and fence-aware baselines are known techniques; the new locality and header diagnostics are adaptations, not independent ground truth.

The [content-comparability supplement](validation/p1d/budget_calibration_v1/boundary_diagnostics_v1/boundary_text_comparability_v1.json) distinguishes whitespace-only offset differences from non-whitespace content changes. The existing literal-stop baseline is case-sensitive and can abstain when only uppercase role transitions occur. Its candidate count is not an independent accuracy score; the prospective stopping proposal explicitly lists title-case and uppercase variants rather than hiding this baseline limitation.

Reference-value literal checks in full raw continuations are reported separately from semantic scores. They do not recognize paraphrases or certify boundary correctness. Longer tails can repeat dialogue without delivering an answer. A heading cut can shorten a promise but cannot establish that an omitted answer was present. No primary span was replaced, and no generation-time stop/template effect is inferred from offline cutting.

## Paired uncertainty and qualification

All three budget differences are reported across all metrics. Six condition-block contributions are averaged within each of eight case/speaker clusters; 10,000 whole-speaker draws use seed 716707. [Cluster/LOSO results and unknown bounds](validation/p1d/budget_calibration_v1/analysis_v1/cluster_sensitivity_v1.json) preserve complete-case alternatives separately and never renormalize missing factorial cells. Ordinal means are descriptive; full categories and paired signs remain available. There are no confirmatory p-values. Degenerate intervals for invariant delivery outcomes describe this sample and are not evidence of population certainty.

| Paired cap difference | Mean added wall seconds | 95% speaker-bootstrap sensitivity interval |
| --- | --- | --- |
| 192 minus 96 | 8.38 | 7.91, 8.88 |
| 256 minus 96 | 13.70 | 13.43, 13.98 |
| 256 minus 192 | 5.33 | 4.71, 5.88 |

The unchanged rule requires at least 44/48 semantically complete replies and at most 2/48 unresolved boundaries. **None of the three caps provisionally qualifies under the AI proposals. No adequate primary output policy is selected.** Human adoption is pending, but automatic main-study execution is not warranted. The 96-token setting remains only the preserved reference, not an endorsed adequate validation policy.

The minimal next hypothesis is that explicit current-user turn framing, with and without conventional stops, may improve task delivery. It is untested and requires a separate bounded authorization. A prospective 16-request candidate uses only the same eight development cases and reuses existing original-baseline results; it does not alter the 144 completed requests or authorize any main-study generation.

The [frozen prompt-format comparison](validation/p1d/final_preparation_v1/frozen_prompt_format_comparison_v1.json) verifies a concrete difference: all 72 P1c prompts mark the current question with `User:`, whereas these 144 P1d prompts place an unmarked question below `CURRENT QUESTION`. Their fixed-context assistant utterances also differ (an invitation to specify an assignment versus a ledger-use commitment). Evidence length and task composition differ as well. This is a rationale for a controlled framing diagnostic, not an isolated between-wave causal explanation or permission to change completed prompts.

## Scientific scope and next independent validation

These eight cases share ledger construction and shorter prompts than the candidate bank. They do not estimate independent-template, real-speaker or population effects, nor establish that Base models generally cannot answer. The main 288-case bank remains unfrozen and AI-proposed VALID_WITH_LIMITATIONS, with diagnostic controls, template dependencies and independent-annotation gaps. A task-delivery floor makes an independent history-effect test scientifically uninformative until measurement adequacy is resolved. This is a validity safeguard, not selection for positive persona effects.

## Algorithmic Opportunity Assessment

1. **Observed Failure Modes:** repeated commitments and role/question continuations warrant delivery and boundary diagnosis; causal attribution remains untested.
2. **Existing Methods and Published Prior Art:** native termination, conventional stops/templates, grammar constraints, CoVe, RARR, DCCD, temporal retrieval and FPPS are relevant existing baselines.
3. **Potential Algorithmic Improvements:** no original gap has been established; first test the smallest known format/stopping repair and uncertainty-preserving verification.
4. **Validation Feasibility:** offline locality adds no P1c recoveries; fair supplied-date retrieval succeeds on the curated development pool. Independent span/claim labels, equal compute and persona fidelity remain required.
5. **Publication Value:** preserve this negative development result and the empirical S/F/H path. See [the detailed update](P1d_algorithmic_development_update_v2.md); no algorithm originality or PLOS ONE readiness follows from this calibration.
